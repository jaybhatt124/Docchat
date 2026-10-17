# DocChat Backend (Render)

Flask JSON API for the DocChat RAG chatbot. Deployed on **Render** as a
**Docker** service (Docker is required so the native OpenCV/libGL libraries
for RapidOCR are present).

## Endpoints

| Method | Path          | Purpose                              |
|--------|---------------|--------------------------------------|
| GET    | `/`           | Service info                         |
| GET    | `/api/health` | Health check + whether GROQ key set  |
| POST   | `/api/upload` | Upload + index a document            |
| POST   | `/api/ask`    | Ask a question about the document    |
| GET    | `/api/status` | Is a document indexed for this user? |

Sessions are tracked with an `X-Session-Id` header sent by the frontend
(stored in `localStorage`). This avoids cross-site cookie issues.

## Environment variables (Render → Environment)

| Key                | Required | Example / Notes                             |
|--------------------|----------|---------------------------------------------|
| `GROQ_API_KEY`     | Yes      | `gsk_...` from console.groq.com             |
| `FLASK_SECRET_KEY` | No       | any random string                           |
| `ALLOWED_ORIGINS`  | No       | `*` or `https://your-app.vercel.app`        |
| `PORT`             | Auto     | Render sets this automatically              |

## Deploy on Render

1. Push this folder (or the whole repo) to GitHub.
2. Render → **New → Web Service** → connect the repo.
3. **Root Directory**: `backend` (if using the whole repo).
4. **Environment**: `Docker` (Render auto-detects the `Dockerfile`).
5. Add the environment variables above (`GROQ_API_KEY` is required).
6. Deploy. Copy the service URL, e.g.
   `https://docchat-backend.onrender.com`.
7. Put that URL into `frontend/config.js` (`PRODUCTION_API_BASE`).

> Note: the in-memory session store means the service runs with a single
> gunicorn worker. On Render's free tier the service sleeps after inactivity,
> so the first request can take ~30s to wake up. Scanned-PDF OCR can take
> 60–120s for large files (the timeout is set to 300s).

## Run locally

```bash
pip install -r requirements.txt
# create .env from .env.example and set GROQ_API_KEY
python app.py
# -> http://localhost:5000
```
