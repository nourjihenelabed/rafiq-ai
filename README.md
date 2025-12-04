# Rafiq-AI — Secrétaire virtuel (prototype)

## Structure
- backend/ : FastAPI backend (ingest + chat + vector store)
- frontend/ : static frontend (HTML/CSS/JS)
- docker-compose.yml : dev compose

## Quick start (dev)
1. Copy `.env` and fill HF_TOKEN/HF_MODEL or OLLAMA_URL if you plan to use an LLM.
2. Build & run:
   ***** bash ********* 
   docker-compose up --build
