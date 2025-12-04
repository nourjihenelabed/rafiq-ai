import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_storage")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "rafiq_ai")
    TOP_K: int = int(os.getenv("TOP_K", "5"))

settings = Settings()
