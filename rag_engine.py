"""
RAG Engine - handles PDF ingestion, vector indexing, retrieval, and LLM generation.
Providers: Gemini (primary) -> OpenRouter (fallback on quota/error)
"""
import os, glob, pickle
import requests
from dotenv import load_dotenv

load_dotenv()   # reads .env into os.environ

import numpy as np
import faiss
from google import genai
from google.genai import types as genai_types
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

# -- Configuration -------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")

_gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# -- OpenRouter fallback -------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "inclusionai/ring-2.6-1t:free")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

EMBED_MODEL   = "all-MiniLM-L6-v2"        # fast, 384-dim embeddings
CHUNK_SIZE    = 400                         # words per chunk
CHUNK_OVERLAP = 60
TOP_K         = 5                           # retrieved chunks

INDEX_PATH    = "vector_store/index.faiss"
CHUNKS_PATH   = "vector_store/chunks.pkl"
KB_DIR        = "knowledge_base"

# -- Text helpers --------------------------------------------------------------

def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages  = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end   = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# -- Vector store --------------------------------------------------------------

class RAGEngine:
    def __init__(self):
        print("[RAG] Loading embedding model...")
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.index    = None
        self.chunks   = []          # list of {"text": ..., "source": ...}
        os.makedirs("vector_store", exist_ok=True)

        if os.path.exists(INDEX_PATH) and os.path.exists(CHUNKS_PATH):
            self._load_index()
        else:
            self._build_index()

    # -- Build -----------------------------------------------------------------

    def _build_index(self):
        pdf_files = glob.glob(os.path.join(KB_DIR, "*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(
                f"No PDFs found in '{KB_DIR}/'. Run create_sample_pdfs.py first."
            )

        print(f"[RAG] Indexing {len(pdf_files)} PDF(s)...")
        all_chunks = []
        for pdf_path in pdf_files:
            print(f"  Processing: {os.path.basename(pdf_path)}")
            raw = extract_text_from_pdf(pdf_path)
            for chunk in chunk_text(raw):
                all_chunks.append({"text": chunk, "source": os.path.basename(pdf_path)})

        print(f"[RAG] Embedding {len(all_chunks)} chunks...")
        texts      = [c["text"] for c in all_chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=True, batch_size=32)
        embeddings = embeddings.astype(np.float32)

        # L2-normalise -> cosine similarity via inner-product index
        faiss.normalize_L2(embeddings)
        dim         = embeddings.shape[1]
        self.index  = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        self.chunks = all_chunks

        # Persist
        faiss.write_index(self.index, INDEX_PATH)
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)
        print(f"[RAG] Index saved ({len(self.chunks)} chunks).")

    # -- Load ------------------------------------------------------------------

    def _load_index(self):
        print("[RAG] Loading existing vector index...")
        self.index = faiss.read_index(INDEX_PATH)
        with open(CHUNKS_PATH, "rb") as f:
            self.chunks = pickle.load(f)
        print(f"[RAG] Index loaded ({len(self.chunks)} chunks).")

    # -- Retrieve --------------------------------------------------------------

    def retrieve(self, query: str, top_k: int = TOP_K):
        q_emb = self.embedder.encode([query], show_progress_bar=False).astype(np.float32)
        faiss.normalize_L2(q_emb)
        scores, indices = self.index.search(q_emb, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                results.append({
                    "text":   self.chunks[idx]["text"],
                    "source": self.chunks[idx]["source"],
                    "score":  float(score),
                })
        return results

    # -- Generate (with automatic fallback) -----------------------------------

    def generate(self, query: str):
        retrieved = self.retrieve(query)
        if not retrieved:
            return {"answer": "No relevant context found.", "sources": [],
                    "context_used": [], "provider": "none"}

        context_blocks = []
        for i, r in enumerate(retrieved, 1):
            context_blocks.append(f"[Source {i}: {r['source']}]\n{r['text']}")
        context = "\n\n---\n\n".join(context_blocks)

        system_msg = (
            "You are a helpful AI assistant. Answer the user's question based ONLY on the "
            "provided context. If the context does not contain enough information to answer, "
            "say so clearly. Always be concise, accurate, and cite the source document names."
        )
        prompt = f"{system_msg}\n\nContext:\n{context}\n\nQuestion: {query}"

        # Try Gemini first
        answer, provider = self._call_gemini(prompt)

        # Fall back to OpenRouter if Gemini failed / quota exceeded
        if answer is None:
            answer, provider = self._call_openrouter(system_msg, context, query)

        if answer is None:
            answer   = "All LLM providers failed or quota exceeded. Please try again later."
            provider = "error"

        sources = list({r["source"] for r in retrieved})
        return {
            "answer":       answer,
            "sources":      sources,
            "provider":     provider,
            "context_used": [{"text": r["text"][:300] + "...", "source": r["source"],
                              "score": r["score"]} for r in retrieved],
        }

    # -- Gemini call -----------------------------------------------------------

    def _call_gemini(self, prompt: str):
        """Returns (answer_text, 'gemini') or (None, None) on quota/error."""
        if not _gemini_client:
            print("[RAG] WARN No GEMINI_API_KEY set -- falling back to OpenRouter.")
            return None, None
        try:
            resp = _gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )
            print("[RAG] OK  Gemini answered.")
            return resp.text, "gemini"
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                print("[RAG] WARN Gemini quota exceeded -- falling back to OpenRouter.")
            else:
                print(f"[RAG] WARN Gemini error: {err[:120]} -- falling back to OpenRouter.")
            return None, None

    # -- OpenRouter call -------------------------------------------------------

    def _call_openrouter(self, system_msg: str, context: str, query: str):
        """Returns (answer_text, 'openrouter') or (None, None) on error."""
        if not OPENROUTER_API_KEY:
            print("[RAG] FAIL No OPENROUTER_API_KEY set -- cannot fall back.")
            return None, None
        try:
            payload = {
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {query}"},
                ],
                "temperature": 0.3,
                "max_tokens":  1024,
            }
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "http://localhost:5000",
                "X-Title":       "BasicRAG",
            }
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"]
            print(f"[RAG] OK  OpenRouter answered via {OPENROUTER_MODEL}.")
            return answer, "openrouter"
        except Exception as e:
            print(f"[RAG] FAIL OpenRouter error: {str(e)[:120]}")
            return None, None

    # -- Re-index (add new PDFs without restarting) ----------------------------

    def reindex(self):
        if os.path.exists(INDEX_PATH):
            os.remove(INDEX_PATH)
        if os.path.exists(CHUNKS_PATH):
            os.remove(CHUNKS_PATH)
        self.index  = None
        self.chunks = []
        self._build_index()
        return len(self.chunks)
