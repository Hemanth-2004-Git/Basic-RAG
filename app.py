"""
Flask API server for the Basic RAG application.
"""
import os
import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from rag_engine import RAGEngine

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

UPLOAD_FOLDER   = "knowledge_base"
ALLOWED_EXT     = {"pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Lazy-initialise the RAG engine (loads/builds index once)
rag: RAGEngine | None = None


def get_rag() -> RAGEngine:
    global rag
    if rag is None:
        rag = RAGEngine()
    return rag


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")


@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400
    result = get_rag().generate(question)
    return jsonify(result)


@app.route("/api/documents", methods=["GET"])
def list_documents():
    pdfs = [os.path.basename(p) for p in glob.glob(f"{UPLOAD_FOLDER}/*.pdf")]
    return jsonify({"documents": pdfs, "count": len(pdfs)})


@app.route("/api/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename."}), 400
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    # Re-build the index to include the new document
    chunk_count = get_rag().reindex()
    return jsonify({"message": f"'{filename}' uploaded and indexed.", "total_chunks": chunk_count})


@app.route("/api/retrieve", methods=["POST"])
def retrieve_only():
    """Return raw retrieved chunks without LLM generation."""
    data = request.get_json(silent=True) or {}
    query_text = (data.get("query") or "").strip()
    top_k = int(data.get("top_k", 5))
    if not query_text:
        return jsonify({"error": "Query is required."}), 400
    results = get_rag().retrieve(query_text, top_k=min(top_k, 10))
    return jsonify({"results": results})


@app.route("/api/status", methods=["GET"])
def status():
    engine = get_rag()
    return jsonify({
        "status":       "ready",
        "total_chunks": len(engine.chunks),
        "model":        "gemini-2.0-flash",
        "embed_model":  "all-MiniLM-L6-v2",
    })


if __name__ == "__main__":
    print("\n[RAG] Basic RAG Server starting...")
    print("   Visit http://localhost:5000\n")
    # Warm up (builds or loads the index before first request)
    get_rag()
    app.run(host="0.0.0.0", port=5000, debug=False)
