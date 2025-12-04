import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import os
from app.core.settings import settings

class VectorStore:
    def __init__(self):
        # using chroma local persistence
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", settings.CHROMA_PERSIST_DIR)
        self.client = chromadb.Client(ChromaSettings(chroma_db_impl="duckdb+parquet", persist_directory=persist_dir))
        self.collection = None
        self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            self.collection = self.client.get_collection(settings.COLLECTION_NAME)
        except Exception:
            self.collection = self.client.create_collection(name=settings.COLLECTION_NAME)
        return self.collection

    def upsert(self, records):
        """
        records: list of tuples (id:str, vector:list[float], metadata:dict)
        """
        ids = [r[0] for r in records]
        embeddings = [r[1] for r in records]
        metadatas = [r[2] for r in records]
        documents = [r[2].get("text", "") for r in records]
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def search(self, query_vector, top_k=5):
        results = self.collection.query(query_embeddings=[query_vector], n_results=top_k, include=["metadatas","distances","ids","documents"])
        out = []
        if results and "ids" in results:
            ids = results["ids"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0]
            docs = results["documents"][0]
            for i, id_ in enumerate(ids):
                out.append({
                    "id": id_,
                    "score": float(distances[i]),
                    "payload": metadatas[i],
                    "document": docs[i]
                })
        return out
