# backend/app/db/vector_store.py
import os
import json
import sqlite3
import uuid
from typing import List, Tuple, Dict, Any

import numpy as np
import faiss

from app.core.settings import settings

class VectorStore:
    """
    Simple FAISS + SQLite vector store.
    - Index file:        {dir}/faiss.index
    - Metadata DB (sqlite): {dir}/meta.db
    """

    def __init__(self):
        self.dir = os.getenv("VECTOR_STORE_DIR", settings.VECTOR_STORE_DIR)
        os.makedirs(self.dir, exist_ok=True)
        self.index_path = os.path.join(self.dir, "faiss.index")
        self.meta_db_path = os.path.join(self.dir, "meta.db")
        self.dimension = settings.EMBED_DIM  # must match embedder output
        # use IndexFlatIP after normalizing vectors -> cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self._load_index()
        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.meta_db_path, check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS docs (
                id TEXT PRIMARY KEY,
                document TEXT,
                metadata TEXT
            )
        """)
        self.conn.commit()

    def _load_index(self):
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
            except Exception:
                # fallback to new empty index
                self.index = faiss.IndexFlatIP(self.dimension)

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)

    @staticmethod
    def _normalize_embeddings(embs: List[List[float]]) -> np.ndarray:
        arr = np.array(embs, dtype='float32')
        # normalize rows to unit length for cosine similarity
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms
        return arr

    def upsert(self, records: List[Tuple[str, List[float], Dict[str,Any]]]):
        """
        records: list of tuples (id:str, vector:list[float], metadata:dict)
        """
        if not records:
            return
        ids = [r[0] for r in records]
        embs = [r[1] for r in records]
        metas = [r[2] for r in records]
        docs = [m.get("text","") for m in metas]
        # normalize embeddings
        emb_matrix = self._normalize_embeddings(embs)
        # add to faiss index
        self.index.add(emb_matrix)
        self._save_index()
        # store metadata in sqlite (id -> json metadata + document)
        cur = self.conn.cursor()
        for id_, doc, meta in zip(ids, docs, metas):
            meta_json = json.dumps(meta, ensure_ascii=False)
            cur.execute("INSERT OR REPLACE INTO docs (id, document, metadata) VALUES (?, ?, ?)",
                        (id_, doc, meta_json))
        self.conn.commit()

    def search(self, query_vector: List[float], top_k: int = 5):
        """
        Returns list of dicts: {id, score, payload, document}
        Score is cosine similarity in [ -1, 1 ] (higher better)
        """
        q = np.array(query_vector, dtype='float32').reshape(1, -1)
        # normalize
        norm = np.linalg.norm(q)
        if norm == 0:
            norm = 1.0
        q = q / norm
        if self.index.ntotal == 0:
            return []
        scores, indices = self.index.search(q, top_k)
        scores = scores[0].tolist()
        indices = indices[0].tolist()
        results = []
        cur = self.conn.cursor()
        for idx, score in zip(indices, scores):
            # FAISS indices are 0..n-1 in insertion order; we stored IDs in insertion order
            # But we need to map the position -> id. We'll store IDs in sqlite rows in insertion order,
            # so fetch the id at row number (idx).
            cur.execute("SELECT id, document, metadata FROM docs LIMIT 1 OFFSET ?", (idx,))
            row = cur.fetchone()
            if not row:
                continue
            id_, document, meta_json = row
            meta = json.loads(meta_json) if meta_json else {}
            results.append({
                "id": id_,
                "score": float(score),
                "payload": meta,
                "document": document
            })
        return results

    def get_all(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, document, metadata FROM docs")
        rows = cur.fetchall()
        out = []
        for id_, doc, meta_json in rows:
            meta = json.loads(meta_json) if meta_json else {}
            out.append({"id": id_, "document": doc, "meta": meta})
        return out

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
        # save index
        try:
            self._save_index()
        except Exception:
            pass
