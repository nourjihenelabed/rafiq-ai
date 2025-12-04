# Frontend (static)

Simple static frontend hosting with nginx.

Dev:
- Serve locally: `python -m http.server 3000` from the frontend folder
- Or build a Docker container with `docker build -t rafiq-frontend .` then run it.

The frontend expects backend endpoints at http://localhost:8000/ingest/ and http://localhost:8000/chat/
