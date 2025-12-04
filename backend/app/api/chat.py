from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.core.llm import LLM
from app.db.vector_store import VectorStore
from app.core.rag import build_prompt
from app.core.settings import settings

router = APIRouter()
llm = LLM()
vs = VectorStore()

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]

@router.post("/")
def chat(req: ChatRequest):
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty question")

    # embed query, retrieve docs
    q_emb = llm.embed_texts([q])[0]
    hits = vs.search(q_emb, top_k=settings.TOP_K)

    # extract contexts
    contexts = [h["payload"]["text"] for h in hits]
    sources = [{"id": h["id"], "score": h["score"], "meta": h["payload"]} for h in hits]

    # build prompt and ask LLM
    prompt = build_prompt(contexts, q)
    answer = llm.generate(prompt)

    return ChatResponse(answer=answer, sources=sources)
