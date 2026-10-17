"""
app.py — Flask backend (API) for the DocChat document Q&A RAG chatbot.
Powered by Groq. Uses in-memory TF-IDF retrieval + RapidOCR for images
and scanned PDFs.

This backend serves a JSON API only and is meant to be deployed on Render
(Docker). The static frontend is deployed separately on Vercel and talks to
this API over CORS.

Endpoints:
    GET  /            -> service info
    GET  /api/health  -> health check
    POST /api/upload  -> upload + index a document
    POST /api/ask     -> ask a question about the indexed document
    GET  /api/status  -> whether the current session has a document

Run locally:
    python app.py            (http://localhost:5000)
Production (Render):
    gunicorn -b 0.0.0.0:$PORT -t 300 -w 1 --threads 4 app:app
"""

import os
import re

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from rag_engine import extract_text, chunk_text, VectorStore, ask_groq

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Allow the Vercel frontend (or "*" during development) to call this API.
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
    allow_headers=["Content-Type", "X-Session-Id"],
    methods=["GET", "POST", "OPTIONS"],
)

# In-memory store keyed by session id: { session_id: {"store": VectorStore, "doc_name": str} }
# NOTE: simple in-memory approach — fine for a single-user demo.
# Because the store lives in memory, the server must run with ONE worker
# (see the gunicorn command above) so that all requests hit the same process.
SESSIONS = {}

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"}

COVERAGE_PATTERNS = (
    r"\b(?:all|the\s+\d+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|many)\s+types?\b",
    r"\b(?:types?|kinds?|categories)\s+of\b",
    r"\bdifferent\s+(?:types?|kinds?|categories)\b",
    r"\bhow\s+many\s+(?:types?|kinds?|categories)\b",
    r"\b(list|name|enumerate|mention|explain|describe)\s+all\b",
    r"\b(list|name|enumerate)\s+(?:the\s+)?(?:different\s+)?(?:types?|kinds?|categories)\b",
    r"\b(summariz(?:e|ation)|overview|contents)\b",
    r"\b(?:in detail|detailed|explain thoroughly)\b",
    r"\bevery\b",
)


def is_coverage_question(question: str) -> bool:
    """True when the user is asking for a complete list/enumeration of items."""
    lowered = question.lower()
    return any(re.search(pattern, lowered) for pattern in COVERAGE_PATTERNS)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session_id() -> str:
    """Resolve the session id.

    The frontend generates a stable id and sends it as the X-Session-Id
    header (localStorage-backed). This avoids cross-site cookie problems
    between the Vercel frontend and the Render backend. A cookie-based
    fallback is kept so the API still works when called directly (e.g. curl).
    """
    sid = request.headers.get("X-Session-Id")
    if sid:
        return sid
    if "sid" not in session:  # session is a signed cookie; only reachable with secret_key
        session["sid"] = os.urandom(16).hex()
    return session["sid"]


@app.route("/")
def root():
    return jsonify({"service": "DocChat API", "status": "ok"})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "groq_configured": bool(GROQ_API_KEY)})


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PDF, DOCX, TXT, or image files (PNG, JPG, JPEG, WEBP)."}), 400

    if not GROQ_API_KEY:
        return jsonify({"error": "Server configuration is missing GROQ_API_KEY."}), 500

    try:
        file_bytes = file.read()
        text = extract_text(file_bytes, file.filename)

        if not text:
            return jsonify({"error": "Couldn't extract any text from this file."}), 400

        chunks = chunk_text(text)
        store = VectorStore()
        store.build(chunks)

        sid = get_session_id()
        SESSIONS[sid] = {
            "store": store,
            "doc_name": file.filename,
        }

        return jsonify({
            "message": f"Indexed '{file.filename}' — {len(chunks)} chunks.",
            "doc_name": file.filename,
            "chunk_count": len(chunks),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    top_k = max(2, min(int(data.get("top_k", 4)), 8))
    model = data.get("model", "openai/gpt-oss-120b")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    sid = get_session_id()
    sess = SESSIONS.get(sid)

    if not sess:
        return jsonify({"error": "Please upload and process a document first."}), 400

    try:
        store: VectorStore = sess["store"]
        coverage_question = is_coverage_question(question)
        relevant_chunks = store.search(
            question,
            k=20 if coverage_question else top_k,
            neighbor_count=2 if coverage_question else 0,
        )

        answer = ask_groq(
            question=question,
            context_chunks=relevant_chunks,
            api_key=GROQ_API_KEY,
            model=model,
        )

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def status():
    sid = get_session_id()
    sess = SESSIONS.get(sid)
    if sess:
        return jsonify({"active": True, "doc_name": sess["doc_name"]})
    return jsonify({"active": False})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
