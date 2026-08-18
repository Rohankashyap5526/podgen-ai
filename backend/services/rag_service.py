"""
PodGen AI - RAG Service
Chunking, embedding, and semantic retrieval with FAISS.
"""

import re
import logging
import numpy as np
from typing import List, Tuple

logger = logging.getLogger(__name__)


class RAGService:
    """Lightweight RAG: chunk → embed → store → retrieve."""

    CHUNK_SIZE = 800          # characters
    CHUNK_OVERLAP = 150

    def __init__(self):
        self._embedder = None   # lazy-loaded
        self._index = None
        self._chunks: List[str] = []

    # ─── Public API ───────────────────────────────────────────────────────────

    def ingest(self, text: str) -> int:
        """Chunk text and build a FAISS index. Returns chunk count."""
        self._chunks = self._chunk(text)
        if not self._chunks:
            return 0

        embeddings = self._embed(self._chunks)
        self._build_index(embeddings)
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 6) -> List[str]:
        """Return the top-k most relevant chunks for a query."""
        if not self._chunks or self._index is None:
            return []

        q_emb = self._embed([query])[0]
        top_k = min(top_k, len(self._chunks))

        distances, indices = self._index.search(
            np.array([q_emb], dtype="float32"), top_k
        )
        return [self._chunks[i] for i in indices[0] if i < len(self._chunks)]

    def get_summary_context(self, max_chars: int = 4000) -> str:
        """Return a concatenated sample of chunks for summarization."""
        if not self._chunks:
            return ""
        total, selected = 0, []
        for chunk in self._chunks:
            if total + len(chunk) > max_chars:
                break
            selected.append(chunk)
            total += len(chunk)
        return "\n\n---\n\n".join(selected)

    # ─── Chunking ─────────────────────────────────────────────────────────────

    def _chunk(self, text: str) -> List[str]:
        """Split text into overlapping chunks on sentence / paragraph boundaries."""
        # Try to split on paragraph breaks first
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

        chunks, current = [], ""
        for para in paragraphs:
            if len(current) + len(para) <= self.CHUNK_SIZE:
                current = (current + "\n\n" + para).strip() if current else para
            else:
                if current:
                    chunks.append(current)
                # Para is itself too long → split by sentences
                if len(para) > self.CHUNK_SIZE:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    buf = ""
                    for sent in sentences:
                        if len(buf) + len(sent) <= self.CHUNK_SIZE:
                            buf = (buf + " " + sent).strip()
                        else:
                            if buf:
                                chunks.append(buf)
                            buf = sent
                    if buf:
                        current = buf
                    else:
                        current = ""
                else:
                    current = para

        if current:
            chunks.append(current)

        # Add overlap: prepend tail of previous chunk
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i > 0 and self.CHUNK_OVERLAP > 0:
                tail = chunks[i - 1][-self.CHUNK_OVERLAP:]
                chunk = tail + " " + chunk
            overlapped.append(chunk.strip())

        return overlapped

    # ─── Embedding ────────────────────────────────────────────────────────────

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Embed texts using sentence-transformers (or a simple TF-IDF fallback)."""
        try:
            from sentence_transformers import SentenceTransformer
            if self._embedder is None:
                logger.info("Loading sentence-transformers model…")
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            return self._embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        except ImportError:
            logger.warning("sentence-transformers not installed – using TF-IDF fallback")
            return self._tfidf_embed(texts)

    def _tfidf_embed(self, texts: List[str]) -> np.ndarray:
        """Very simple bag-of-words fallback embedding."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        if not hasattr(self, "_tfidf_vocab"):
            self._tfidf = TfidfVectorizer(max_features=512, stop_words="english")
            all_docs = self._chunks if self._chunks else texts
            self._tfidf.fit(all_docs)
        mat = self._tfidf.transform(texts).toarray().astype("float32")
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
        return mat / norms

    # ─── FAISS Index ──────────────────────────────────────────────────────────

    def _build_index(self, embeddings: np.ndarray):
        try:
            import faiss
            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatIP(dim)
            self._index.add(embeddings.astype("float32"))
        except ImportError:
            logger.warning("faiss not installed – using numpy dot-product search")
            self._fallback_embeddings = embeddings

    def _numpy_search(self, q_emb: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        scores = self._fallback_embeddings @ q_emb
        indices = np.argsort(scores)[::-1][:top_k]
        return scores[indices], indices
