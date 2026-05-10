# 🔍 Basic RAG — Retrieval-Augmented Generation App

A full-stack **Retrieval-Augmented Generation (RAG)** application that lets you upload PDF documents and ask natural language questions about them. The backend uses **FAISS** for vector search and **OpenRouter** to power LLM-based answers, while the frontend is a clean, single-page web UI served by Flask.

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Browser (UI)                   │
│         static/index.html + app.js              │
└────────────────────┬────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────┐
│              Flask API  (app.py)                │
│  /api/query  /api/upload  /api/documents        │
│  /api/retrieve  /api/status                     │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│             RAG Engine (rag_engine.py)           │
│                                                 │
│  ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │  PyPDF2  │──▶│ Chunker  │──▶│ Sentence    │ │
│  │ (ingest) │   │ (400w,   │   │ Transformer │ │
│  └──────────┘   │  60 ovlp)│   │ (embeddings)│ │
│                 └──────────┘   └──────┬──────┘ │
│                                       │         │
│  ┌────────────────────────────────────▼──────┐  │
│  │         FAISS Vector Index (IndexFlatIP)  │  │
│  │           vector_store/index.faiss        │  │
│  └────────────────────────────────────┬──────┘  │
│                                       │          │
│  ┌────────────────────────────────────▼──────┐  │
│  │       OpenRouter LLM  (Ring 2.6-1T)       │  │
│  │     Grounded answer generation + sources  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
basic rag/
├── app.py                  # Flask server & REST API
├── rag_engine.py           # Core RAG logic (ingest, index, retrieve, generate)
├── create_sample_pdfs.py   # One-time script to generate demo knowledge-base PDFs
│
├── knowledge_base/         # Drop your PDF files here
│   ├── ai_overview.pdf
│   ├── ml_fundamentals.pdf
│   ├── python_guide.pdf
│   └── rag_and_llms.pdf
│
├── vector_store/           # Auto-generated FAISS index (do not edit manually)
│   ├── index.faiss
│   └── chunks.pkl
│
└── static/                 # Frontend (served by Flask)
    ├── index.html
    ├── style.css
    └── app.js
```

---

## ✨ Features

| Feature | Details |
|---|---|
| 📄 PDF Ingestion | Upload any PDF via the UI or drop files into `knowledge_base/` |
| ✂️ Smart Chunking | 400-word chunks with 60-word overlap for coherent context |
| 🔢 Vector Embeddings | `all-MiniLM-L6-v2` (384-dim, fast & accurate) |
| ⚡ FAISS Search | Cosine-similarity search via `IndexFlatIP` on L2-normalised vectors |
| 🤖 LLM Generation | `inclusion-ai/ring-2.6-1t` via OpenRouter API |
| 📎 Source Citations | Every answer includes the source PDF filename(s) |
| 🔁 Live Re-indexing | Uploading a new PDF automatically rebuilds the index without a restart |
| 🌐 Web UI | Single-page app — no frontend build step required |

---

## 🚀 Getting Started

### 1. Clone / Download

```bash
git clone <your-repo-url>
cd "basic rag"
```

### 2. Install Dependencies

```bash
pip install flask flask-cors werkzeug PyPDF2 sentence-transformers faiss-cpu numpy requests reportlab
```

> **Windows note:** If `faiss-cpu` fails, try `pip install faiss-cpu --no-cache-dir`.

### 3. Create the Sample Knowledge Base (first run only)

```bash
python create_sample_pdfs.py
```

This generates four demo PDFs inside `knowledge_base/`:
- `ai_overview.pdf` — Artificial Intelligence overview
- `python_guide.pdf` — Python programming guide
- `ml_fundamentals.pdf` — Machine Learning fundamentals
- `rag_and_llms.pdf` — RAG & LLM concepts

### 4. Start the Server

```bash
python app.py
```

The server will:
1. Load the embedding model (`all-MiniLM-L6-v2`)
2. Build or load the FAISS index
3. Start listening on **http://localhost:5000**

### 5. Open the App

Navigate to [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🔌 REST API Reference

### `GET /api/status`
Returns engine health and index statistics.

**Response:**
```json
{
  "status": "ready",
  "total_chunks": 142,
  "model": "inclusion-ai/ring-2.6-1t",
  "embed_model": "all-MiniLM-L6-v2"
}
```

---

### `POST /api/query`
Ask a question against the knowledge base.

**Request:**
```json
{ "question": "What is retrieval-augmented generation?" }
```

**Response:**
```json
{
  "answer": "RAG combines a retrieval system with a generative LLM...",
  "sources": ["rag_and_llms.pdf"],
  "context_used": [
    { "text": "...", "source": "rag_and_llms.pdf", "score": 0.91 }
  ]
}
```

---

### `POST /api/retrieve`
Return raw retrieved chunks without LLM generation (useful for debugging).

**Request:**
```json
{ "query": "FAISS vector search", "top_k": 3 }
```

**Response:**
```json
{
  "results": [
    { "text": "...", "source": "rag_and_llms.pdf", "score": 0.88 }
  ]
}
```

---

### `POST /api/upload`
Upload a new PDF to the knowledge base. Automatically triggers re-indexing.

- **Content-Type:** `multipart/form-data`
- **Field:** `file` (PDF only)

**Response:**
```json
{ "message": "'my_doc.pdf' uploaded and indexed.", "total_chunks": 158 }
```

---

### `GET /api/documents`
List all PDFs currently in the knowledge base.

**Response:**
```json
{ "documents": ["ai_overview.pdf", "python_guide.pdf"], "count": 2 }
```

---

## ⚙️ Configuration

All key parameters are at the top of `rag_engine.py`:

| Parameter | Default | Description |
|---|---|---|
| `OPENROUTER_MODEL` | `inclusion-ai/ring-2.6-1t` | LLM used for answer generation |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer embedding model |
| `CHUNK_SIZE` | `400` | Words per text chunk |
| `CHUNK_OVERLAP` | `60` | Overlap words between chunks |
| `TOP_K` | `5` | Number of retrieved chunks per query |
| `INDEX_PATH` | `vector_store/index.faiss` | FAISS index file path |
| `CHUNKS_PATH` | `vector_store/chunks.pkl` | Serialised chunk metadata |
| `KB_DIR` | `knowledge_base` | Directory scanned for PDF files |

---

## 🔑 API Key

The OpenRouter API key is stored in `rag_engine.py` at `OPENROUTER_API_KEY`. For production use, move it to an environment variable:

```python
import os
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
```

Then set it in your shell:

```bash
# Windows PowerShell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."

# Linux / macOS
export OPENROUTER_API_KEY="sk-or-v1-..."
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web framework & static file serving |
| `flask-cors` | Cross-Origin Resource Sharing |
| `werkzeug` | Secure filename handling for uploads |
| `PyPDF2` | PDF text extraction |
| `sentence-transformers` | `all-MiniLM-L6-v2` embedding model |
| `faiss-cpu` | Efficient vector similarity search |
| `numpy` | Numerical operations & L2 normalisation |
| `requests` | HTTP calls to OpenRouter API |
| `reportlab` | (Dev only) Generate sample PDF documents |

---

## 🧠 How It Works

### Indexing Phase
1. All PDFs in `knowledge_base/` are read with **PyPDF2**.
2. Extracted text is split into overlapping word chunks.
3. Each chunk is encoded into a 384-dimensional vector by **all-MiniLM-L6-v2**.
4. Vectors are L2-normalised and stored in a **FAISS `IndexFlatIP`** (inner-product = cosine similarity on normalised vectors).
5. The index and chunk metadata are persisted to `vector_store/`.

### Query Phase
1. The user's question is encoded with the same embedding model.
2. FAISS performs a similarity search and returns the top-5 most relevant chunks.
3. Retrieved chunks are formatted into a context block and sent to the **OpenRouter LLM**.
4. The LLM generates a grounded answer citing the source documents.
5. The answer, sources, and scored context are returned to the UI.

---

## 🛠️ Development Tips

- **Reset the index:** Delete `vector_store/index.faiss` and `vector_store/chunks.pkl`, then restart the server.
- **Add custom PDFs:** Drop any PDF into `knowledge_base/` and use the `/api/upload` endpoint or restart the server.
- **Switch LLM:** Update `OPENROUTER_MODEL` in `rag_engine.py` to any model available on [openrouter.ai/models](https://openrouter.ai/models).
- **Debug retrieval:** Use the `/api/retrieve` endpoint to inspect raw chunk scores before generation.

---

## 📝 License

This project is open source and free to use for educational and personal projects.
