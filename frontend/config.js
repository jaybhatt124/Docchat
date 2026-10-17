/*
 * DocChat frontend configuration
 * ---------------------------------------------------------------------------
 * This file points the static frontend at the Flask backend.
 *
 * Local development:
 *     The backend runs at http://localhost:5000, so localhost is used
 *     automatically — no change needed.
 *
 * Production (Vercel):
 *     Replace the URL below with your deployed Render backend URL,
 *     e.g. "https://docchat-backend.onrender.com".
 */
(function () {
  var PRODUCTION_API_BASE = "https://docchat-m7ob.onrender.com/";

  var host = window.location.hostname;
  var isLocal =
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "0.0.0.0" ||
    host === "" ||
    host.endsWith(".local");

  window.DOCCHAT_API_BASE = isLocal ? "http://localhost:5000" : PRODUCTION_API_BASE;
})();
