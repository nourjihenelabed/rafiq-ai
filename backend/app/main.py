from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, ingest

app = FastAPI(title="Rafiq-AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during dev; lock down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/")
def root():
    return {"service": "rafiq-ai backend", "status": "ok"}
