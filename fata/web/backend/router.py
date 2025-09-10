from flask import Flask, send_from_directory
from pathlib import Path

# Path to Vite build directory
BUILD_DIR = Path(__file__).resolve().parent.parent / "frontend" / "build"

app = Flask(__name__, static_folder=str(BUILD_DIR), static_url_path="/")

@app.route("/api/stats")
def stats():
    return {
        "blocked_ads": 123,
        "total_requests": 456,
        "unique_domains": 42
    }

# Serve Vite frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path: str):
    file_path = BUILD_DIR / path
    if path and file_path.exists():
        return send_from_directory(BUILD_DIR, path)
    else:
        # Fallback to index.html for React Router / SPA routes
        return send_from_directory(BUILD_DIR, "index.html")
