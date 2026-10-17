# DocChat Frontend (Vercel)

Static frontend (HTML + CSS + vanilla JS) for the DocChat RAG chatbot.
Deployed on **Vercel** as a static site. It talks to the Flask backend
(Render) over CORS.

## Files

```
frontend/
├── index.html          # the UI
├── config.js           # backend API base URL (edit this!)
├── vercel.json         # Vercel static config
└── static/
    ├── css/style.css
    └── js/app.js
```

## Point it at your backend

Open `config.js` and set `PRODUCTION_API_BASE` to your Render URL:

```js
var PRODUCTION_API_BASE = "https://docchat-backend.onrender.com";
```

`localhost` automatically uses `http://localhost:5000`, so local dev needs
no changes.

## Deploy on Vercel

1. Push this folder (or the whole repo) to GitHub.
2. Vercel → **Add New → Project** → import the repo.
3. **Root Directory**: `frontend` (if using the whole repo).
4. **Framework Preset**: `Other` (no build step — pure static).
5. Deploy. Vercel serves `index.html` as the site root.
6. Make sure the backend's `ALLOWED_ORIGINS` includes your Vercel URL
   (or keep `*`).

## Run locally

Serve the folder with any static server, e.g.:

```bash
python -m http.server 8000
# open http://localhost:8000
```

(Opening `index.html` directly with `file://` also works, but a tiny static
server is cleaner.)
