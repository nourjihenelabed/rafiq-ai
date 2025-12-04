from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup

from app.utils.text_splitter import naive_chunker
from app.core.llm import LLM
from app.db.vector_store import VectorStore
from app.core.settings import settings

router = APIRouter()

class IngestPayload(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    source_name: Optional[str] = "user-paste"

llm = LLM()
vs = VectorStore()

@router.post("/")
def ingest(payload: IngestPayload):
    if not payload.url and not payload.text:
        raise HTTPException(status_code=400, detail="Provide url or text")
    texts = []
    source = payload.source_name or payload.url or "unknown"
    if payload.url:
        try:
            r = requests.get(payload.url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            # naive: collect visible paragraphs & headings
            paras = []
            for tag in soup.find_all(["h1","h2","h3","p","li"]):
                t = tag.get_text(strip=True)
                if t:
                    paras.append(t)
            texts = paras
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch url: {e}")
    else:
        # text provided directly: split into paragraphs by newlines
        raw = payload.text.strip()
        texts = [p.strip() for p in raw.split("\n\n") if p.strip()]

    # chunk paragraphs into smaller docs
    chunks = []
    for i, p in enumerate(texts):
        c = naive_chunker(p, max_chars=800)
        for j, piece in enumerate(c):
            chunks.append({
                "source": source,
                "source_url": payload.url,
                "para_index": i,
                "chunk_index": j,
                "text": piece
            })

    # embed & upsert
    if not chunks:
        raise HTTPException(status_code=400, detail="No textual content found to index.")
    texts_for_emb = [c["text"] for c in chunks]
    embeddings = llm.embed_texts(texts_for_emb)
    records = []
    for idx, emb in enumerate(embeddings):
        meta = {
            "source": chunks[idx]["source"],
            "source_url": chunks[idx]["source_url"],
            "para_index": chunks[idx]["para_index"],
            "chunk_index": chunks[idx]["chunk_index"],
            "text": chunks[idx]["text"]
        }
        records.append((f"{source}-{idx}", emb, meta))

    vs.upsert(records)
    return {"indexed": len(records), "source": source}
