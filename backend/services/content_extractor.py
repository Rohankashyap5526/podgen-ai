"""
PodGen AI - Content Extractor
Handles extraction from URLs and documents (PDF, DOCX, TXT).
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ContentExtractor:

    # ─── URL Extraction ───────────────────────────────────────────────────────

    def extract_from_url(self, url: str) -> str:
        """Scrape and clean content from a web URL."""
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove boilerplate elements
            for tag in soup(["script", "style", "nav", "footer", "header",
                              "aside", "advertisement", "ads", "cookie"]):
                tag.decompose()

            # Try article / main content first
            article = (
                soup.find("article")
                or soup.find("main")
                or soup.find(class_=re.compile(r"article|content|post|entry", re.I))
                or soup.find("body")
            )

            text = article.get_text(separator="\n") if article else soup.get_text(separator="\n")
            return self._clean_text(text)

        except Exception as exc:
            logger.error("URL extraction failed for %s: %s", url, exc)
            raise ValueError(f"Failed to extract content from URL: {exc}")

    # ─── Document Extraction ─────────────────────────────────────────────────

    def extract_from_document(self, file_bytes: bytes, filename: str) -> str:
        """Extract text from PDF, DOCX, or TXT files."""
        fname = filename.lower()

        if fname.endswith(".pdf"):
            return self._extract_pdf(file_bytes)
        elif fname.endswith(".docx"):
            return self._extract_docx(file_bytes)
        elif fname.endswith(".txt"):
            return self._clean_text(file_bytes.decode("utf-8", errors="ignore"))
        else:
            raise ValueError(f"Unsupported file type: {filename}")

    def _extract_pdf(self, file_bytes: bytes) -> str:
        try:
            import fitz  # PyMuPDF
            import io

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = [page.get_text() for page in doc]
            return self._clean_text("\n\n".join(pages))
        except ImportError:
            # Fallback to pdfplumber
            try:
                import pdfplumber
                import io
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    texts = [page.extract_text() or "" for page in pdf.pages]
                return self._clean_text("\n\n".join(texts))
            except Exception as exc:
                raise ValueError(f"PDF extraction failed: {exc}")

    def _extract_docx(self, file_bytes: bytes) -> str:
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return self._clean_text("\n\n".join(paragraphs))
        except Exception as exc:
            raise ValueError(f"DOCX extraction failed: {exc}")

    # ─── Text Cleaning ────────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """Remove noise and normalize whitespace."""
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove zero-width / invisible characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Normalize spaces
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)
        return text.strip()
