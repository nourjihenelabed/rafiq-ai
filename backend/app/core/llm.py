import os
import requests
from typing import List
from sentence_transformers import SentenceTransformer
from app.core.settings import settings

class LLM:
    def __init__(self):
        # embedding model
        model_name = os.getenv("EMBEDDING_MODEL", settings.EMBEDDING_MODEL)
        self.embedder = SentenceTransformer(model_name)

        # HF config
        self.hf_token = os.getenv("HF_TOKEN", settings.HF_TOKEN)
        self.hf_model = os.getenv("HF_MODEL", settings.HF_MODEL)
        # Ollama config (e.g., http://localhost:11434)
        self.ollama_url = os.getenv("OLLAMA_URL", settings.OLLAMA_URL)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # returns list of vectors
        embeddings = self.embedder.encode(texts, show_progress_bar=False)
        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # Prefer Ollama (local) if configured
        if self.ollama_url:
            try:
                payload = {"prompt": prompt, "max_tokens": max_tokens}
                r = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                # expected { "text": "..." } or similar; adapt if different
                if isinstance(data, dict):
                    return data.get("text") or data.get("result") or str(data)
                return str(data)
            except Exception as e:
                # fallback to HF if available
                print("Ollama call failed:", e)

        # Hugging Face Inference fallback
        if self.hf_token and self.hf_model:
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            body = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
            resp = requests.post(f"https://api-inference.huggingface.co/models/{self.hf_model}",
                                 headers=headers, json=body, timeout=60)
            resp.raise_for_status()
            out = resp.json()
            # HF sometimes returns [{"generated_text": "..."}] or string
            if isinstance(out, list) and "generated_text" in out[0]:
                return out[0]["generated_text"]
            if isinstance(out, dict) and "generated_text" in out:
                return out["generated_text"]
            if isinstance(out, str):
                return out
            # try to extract text field
            return str(out)
        # final fallback: return the prompt truncated (safe)
        return "Désolé, impossible de générer la réponse (LLM non configuré)."
