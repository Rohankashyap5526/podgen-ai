"""
PodGen AI - Lightweight RAG Service
Chunking + TF-IDF retrieval.

Designed for low-memory/free deployments.
Does not require SentenceTransformers, PyTorch, or FAISS.
"""

import re
import logging
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class RAGService:
    """Lightweight RAG: chunk → TF-IDF → retrieve."""

    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150
    MAX_CHUNKS = 100
    MAX_FEATURES = 5000

    def __init__(self):
        self._chunks: List[str] = []
        self._vectorizer = None
        self._matrix = None

    # ─── Public API ──────────────────────────────────────────────────────────

    def ingest(self, text: str) -> int:
        """
        Chunk text and build a TF-IDF index.

        Returns the number of chunks.
        """

        # Reset previous index
        self._chunks = []
        self._vectorizer = None
        self._matrix = None

        if not text or not text.strip():
            return 0

        # Create chunks
        self._chunks = self._chunk(text)

        # Limit memory usage on free hosting
        self._chunks = self._chunks[:self.MAX_CHUNKS]

        if not self._chunks:
            return 0

        logger.info(
            "Creating TF-IDF index from %d chunks...",
            len(self._chunks)
        )

        try:
            self._vectorizer = TfidfVectorizer(
                max_features=self.MAX_FEATURES,
                stop_words="english",
                ngram_range=(1, 2),
                lowercase=True,
                sublinear_tf=True
            )

            self._matrix = self._vectorizer.fit_transform(
                self._chunks
            )

            logger.info(
                "TF-IDF index ready: %d chunks, %d features",
                self._matrix.shape[0],
                self._matrix.shape[1]
            )

        except Exception:
            logger.exception("Failed to create TF-IDF index")
            self._chunks = []
            self._vectorizer = None
            self._matrix = None
            return 0

        return len(self._chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 6
    ) -> List[str]:
        """
        Return the top-k most relevant chunks.
        """

        if (
            not self._chunks
            or self._vectorizer is None
            or self._matrix is None
            or not query
        ):
            return []

        top_k = min(top_k, len(self._chunks))

        try:
            query_vector = self._vectorizer.transform([query])

            scores = cosine_similarity(
                query_vector,
                self._matrix
            ).flatten()

            # Highest similarity first
            indices = np.argsort(scores)[::-1][:top_k]

            results = [
                self._chunks[i]
                for i in indices
                if scores[i] > 0
            ]

            logger.info(
                "Retrieved %d chunks for query",
                len(results)
            )

            return results

        except Exception:
            logger.exception("TF-IDF retrieval failed")
            return []

    def get_summary_context(
        self,
        max_chars: int = 4000
    ) -> str:
        """
        Return a concatenated sample of chunks for summarization.
        """

        if not self._chunks:
            return ""

        total = 0
        selected = []

        for chunk in self._chunks:

            if total + len(chunk) > max_chars:
                break

            selected.append(chunk)
            total += len(chunk)

        return "\n\n---\n\n".join(selected)

    # ─── Chunking ────────────────────────────────────────────────────────────

    def _chunk(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks on
        paragraph and sentence boundaries.
        """

        text = text.strip()

        if not text:
            return []

        # Normalize excessive whitespace
        text = re.sub(r"[ \t]+", " ", text)

        paragraphs = [
            p.strip()
            for p in re.split(r"\n{2,}", text)
            if p.strip()
        ]

        chunks = []
        current = ""

        for para in paragraphs:

            # Normal paragraph fits in current chunk
            if len(current) + len(para) <= self.CHUNK_SIZE:

                if current:
                    current += "\n\n" + para
                else:
                    current = para

            else:

                if current:
                    chunks.append(current)

                # Paragraph is too large
                if len(para) > self.CHUNK_SIZE:

                    sentences = re.split(
                        r"(?<=[.!?])\s+",
                        para
                    )

                    buf = ""

                    for sentence in sentences:

                        if len(buf) + len(sentence) <= self.CHUNK_SIZE:

                            buf = (
                                buf + " " + sentence
                            ).strip()

                        else:

                            if buf:
                                chunks.append(buf)

                            buf = sentence

                    current = buf

                else:
                    current = para

        if current:
            chunks.append(current)

        # Add overlap
        overlapped = []

        for i, chunk in enumerate(chunks):

            if i > 0 and self.CHUNK_OVERLAP > 0:

                previous_tail = chunks[i - 1][
                    -self.CHUNK_OVERLAP:
                ]

                chunk = (
                    previous_tail
                    + " "
                    + chunk
                )

            overlapped.append(chunk.strip())

        logger.info(
            "Created %d text chunks",
            len(overlapped)
        )

        return overlapped

    # ─── Utility ─────────────────────────────────────────────────────────────

    def clear(self):
        """Release RAG resources after a job."""

        self._chunks = []
        self._vectorizer = None
        self._matrix = None

        logger.info("RAG index cleared")
