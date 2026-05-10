# 📖 Basic RAG: Detailed Code Walkthrough

This document provides a detailed, section-by-section breakdown of every file in the Basic RAG project. It is designed to help you understand exactly how the application works under the hood.

---

## 1. `app.py` (The Flask Web Server)
This is the entry point of the application. It serves the frontend UI and handles all API requests.

```python
import os
import glob
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from rag_engine import RAGEngine
```
* **Imports**: We import `Flask` for the server, `CORS` to allow cross-origin requests, `secure_filename` to safely save user uploads, and our custom `RAGEngine` which handles the AI logic.

```python
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

UPLOAD_FOLDER   = "knowledge_base"
ALLOWED_EXT     = {"pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
```
* **App Setup**: We initialize Flask, telling it to serve static files (HTML/CSS/JS) from the `static/` folder. We also define where uploaded PDFs should go (`knowledge_base/`) and ensure the folder exists.

```python
rag: RAGEngine | None = None

def get_rag() -> RAGEngine:
    global rag
    if rag is None:
        rag = RAGEngine()
    return rag
```
* **Lazy Initialization**: This is a singleton pattern. Loading the AI embedding model takes a few seconds and uses memory. We only initialize the `RAGEngine` once, when the first request comes in (or at startup), and reuse it for all future requests.

```python
@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")
```
* **Frontend Route**: When a user visits `http://localhost:5000/`, Flask serves the frontend UI.

```python
@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400
    result = get_rag().generate(question)
    return jsonify(result)
```
* **Query API**: The core endpoint. It receives a JSON payload with a `"question"`, passes it to `rag.generate()`, and returns the LLM's answer and the sources it used.

```python
@app.route("/api/upload", methods=["POST"])
def upload_document():
    # ... validation code ...
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename."}), 400
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    chunk_count = get_rag().reindex()
    return jsonify({"message": f"'{filename}' uploaded and indexed.", "total_chunks": chunk_count})
```
* **Upload API**: Accepts a PDF file, saves it securely to the `knowledge_base/` directory, and immediately calls `rag.reindex()` so the new document is searchable without restarting the server.

---

## 2. `rag_engine.py` (The AI & Vector Logic)
This file does the heavy lifting: reading PDFs, chunking text, generating embeddings, searching FAISS, and calling Gemini/OpenRouter.

```python
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
_gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "inclusionai/ring-2.6-1t:free")
```
* **Configuration**: Safely loads the API keys from the `.env` file. It configures Gemini as the primary provider and OpenRouter as the fallback.

```python
def chunk_text(text: str, chunk_size: int = 400, overlap: int = 60):
```
* **Chunking**: LLMs and vector models can't digest an entire book at once. This function takes a long string of text and slices it into chunks of 400 words, with a 60-word overlap between chunks so context isn't lost at the boundaries.

```python
class RAGEngine:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        # ...
```
* **Initialization**: Loads the embedding model (`all-MiniLM-L6-v2`). This model converts text into an array of 384 numbers (a vector) capturing the semantic meaning of the text.

```python
    def _build_index(self):
        # ... extract text from PDFs ...
        embeddings = self.embedder.encode(texts)
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
```
* **Vector Indexing**: 
    1. It reads all PDFs and chunks them.
    2. It passes all chunks into the `embedder` to get vectors.
    3. It normalises the vectors and creates a **FAISS Index**. FAISS is a library by Meta for ultra-fast similarity search. `IndexFlatIP` combined with normalized vectors gives us "Cosine Similarity" (finding text with the closest meaning).

```python
    def retrieve(self, query: str, top_k: int = 5):
        q_emb = self.embedder.encode([query])
        faiss.normalize_L2(q_emb)
        scores, indices = self.index.search(q_emb, top_k)
```
* **Retrieval**: When a user asks a question, this converts the question into a vector and asks FAISS to find the top 5 closest matching chunks in our database.

```python
    def generate(self, query: str):
        retrieved = self.retrieve(query)
        # ... format context ...
        answer, provider = self._call_gemini(prompt)
        if answer is None:
            answer, provider = self._call_openrouter(system_msg, context, query)
```
* **Generation**: This is where RAG happens. It retrieves the context, pastes it into a prompt string, and asks the LLM to answer the question *only* using that context. If Gemini fails (e.g., rate limits), it automatically falls back to OpenRouter.

---

## 3. `.env` (Environment Variables)
```ini
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=models/gemini-2.0-flash
OPENROUTER_API_KEY=sk-or-v1-...
```
* **Secrets Management**: This file holds sensitive passwords and keys. It is explicitly ignored by Git (via `.gitignore`) so you don't accidentally publish your keys to GitHub. `python-dotenv` loads these into `os.environ` so Python can read them safely.

---

## 4. `create_sample_pdfs.py` (Dummy Data Generator)
```python
from reportlab.platypus import SimpleDocTemplate, Paragraph
```
* **PDF Generation**: This is a developer utility script. It uses the `reportlab` library to programmatically generate 4 sample PDFs (AI Overview, Python Guide, etc.) so you have data to test the RAG engine out-of-the-box without needing to find your own PDFs.

---

## 5. `static/app.js` & `static/index.html` (Frontend)
```javascript
async function askQuestion(text) {
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text })
    });
    // ... display answer in UI ...
}
```
* **Client UI**: The app uses vanilla HTML, CSS, and JavaScript. It listens for user clicks/typing, sends JSON HTTP `POST` requests to our Flask backend, and renders the LLM's Markdown response into HTML using a library called `marked.js`. It also handles drag-and-drop file uploading using `FormData`.
