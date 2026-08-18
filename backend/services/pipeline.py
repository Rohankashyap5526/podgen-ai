"""
PodGen AI - Podcast Generation Pipeline
Orchestrates the full flow: ingest → RAG → LLM → TTS
Uses an agent-based design: PlannerAgent, ScriptAgent, VoiceAgent
"""

import logging
import asyncio
from typing import Optional

from services.job_manager import JobManager, JobStatus
from services.content_extractor import ContentExtractor
from services.rag_service import RAGService
from services.groq_service import GroqService
from services.tts_service import TTSService

logger = logging.getLogger(__name__)


# ─── Agent Definitions ────────────────────────────────────────────────────────

class PlannerAgent:
    """Decides what context to extract and how to structure the podcast."""

    def __init__(self, rag: RAGService, groq: GroqService):
        self.rag = rag
        self.groq = groq

    def plan(self, topic: str, context: str, config: dict) -> str:
        """Retrieve relevant chunks and prepare enriched context for script generation."""
        # Retrieve most relevant chunks
        queries = [
            topic,
            f"key facts and statistics about {topic}",
            f"interesting stories and examples of {topic}",
            f"expert opinions on {topic}",
        ]
        all_chunks = []
        for q in queries:
            chunks = self.rag.retrieve(q, top_k=3)
            all_chunks.extend(chunks)

        # Deduplicate
        seen, unique = set(), []
        for c in all_chunks:
            key = c[:100]
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return "\n\n---\n\n".join(unique[:12])


class ScriptAgent:
    """Generates the podcast script from context."""

    def __init__(self, groq: GroqService):
        self.groq = groq

    def write(self, context: str, topic: str, config: dict) -> str:
        return self.groq.generate_script(
            context=context,
            topic=topic,
            style=config.get("style", "educational"),
            audience=config.get("audience", "general"),
            tone=config.get("tone", "conversational"),
            duration_minutes=config.get("duration_minutes", 10),
            host_name=config.get("host_name", "Alex"),
            guest_name=config.get("guest_name", "Jordan"),
            host_personality=config.get("host_personality", "curious and engaging"),
            guest_personality=config.get("guest_personality", "knowledgeable and enthusiastic"),
        )


class VoiceAgent:
    """Converts scripts to audio."""

    def __init__(self, tts: TTSService):
        self.tts = tts

    def speak(self, script: str, job_id: str, config: dict, progress_cb=None) -> Optional[str]:
        return self.tts.generate_audio(
            script=script,
            job_id=job_id,
            host_name=config.get("host_name", "HOST"),
            guest_name=config.get("guest_name", "GUEST"),
            progress_callback=progress_cb,
        )


# ─── Main Pipeline ────────────────────────────────────────────────────────────

class PodcastPipeline:

    def __init__(self, job_manager: JobManager):
        self.job_manager = job_manager
        self.extractor = ContentExtractor()
        self.rag = RAGService()
        self.groq = GroqService()
        self.tts = TTSService()

        # Agents
        self.planner = PlannerAgent(self.rag, self.groq)
        self.scripter = ScriptAgent(self.groq)
        self.voice = VoiceAgent(self.tts)

    async def run(
        self,
        job_id: str,
        input_type: str,
        content,
        config: dict,
        filename: Optional[str] = None,
    ):
        """Full async pipeline execution."""
        jm = self.job_manager

        def _check():
            if jm.is_cancelled(job_id):
                raise InterruptedError("Job cancelled by user")

        try:
            # ── Stage 1: Ingest ─────────────────────────────────────────────
            jm.update_job(job_id, status=JobStatus.PROCESSING, stage="extracting", progress=5)
            _check()

            raw_text = await asyncio.get_event_loop().run_in_executor(
                None, self._extract, input_type, content, filename, config
            )
            logger.info("[%s] Extracted %d chars", job_id, len(raw_text))
            jm.update_job(job_id, stage="extracted", progress=15)
            _check()

            # ── Stage 2: Chunking + Embedding ───────────────────────────────
            jm.update_job(job_id, stage="indexing", progress=20)
            chunk_count = await asyncio.get_event_loop().run_in_executor(
                None, self.rag.ingest, raw_text
            )
            logger.info("[%s] Indexed %d chunks", job_id, chunk_count)
            jm.update_job(job_id, stage="indexed", progress=35)
            _check()

            # ── Stage 3: Planning / Context Retrieval ───────────────────────
            jm.update_job(job_id, stage="planning", progress=40)
            topic = self._derive_topic(input_type, content, config)
            enriched_ctx = await asyncio.get_event_loop().run_in_executor(
                None, self.planner.plan, topic, raw_text, config
            )
            jm.update_job(job_id, stage="planned", progress=50)
            _check()

            # ── Stage 4: Script Generation ──────────────────────────────────
            jm.update_job(job_id, stage="scripting", progress=55)
            script = await asyncio.get_event_loop().run_in_executor(
                None, self.scripter.write, enriched_ctx, topic, config
            )
            jm.update_job(job_id, script=script, stage="scripted", progress=70)
            logger.info("[%s] Script generated (%d chars)", job_id, len(script))
            _check()

            # ── Stage 5: Metadata ───────────────────────────────────────────
            jm.update_job(job_id, stage="metadata", progress=72)
            metadata = await asyncio.get_event_loop().run_in_executor(
                None, self.groq.generate_metadata, script, topic
            )
            jm.update_job(
                job_id,
                title=metadata.get("title"),
                description=metadata.get("description"),
                tags=metadata.get("tags", []),
                stage="metadata_done",
                progress=75,
            )
            _check()

            # ── Stage 6: Audio Generation ───────────────────────────────────
            jm.update_job(job_id, stage="generating_audio", progress=78)

            # Re-read script in case user edited it
            current_script = jm.get_job(job_id).get("script", script)

            def tts_progress(pct):
                overall = 78 + int(pct * 0.20)
                jm.update_job(job_id, progress=overall)

            audio_filename = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.voice.speak(current_script, job_id, config, tts_progress),
            )

            audio_url = f"/audio/{audio_filename}" if audio_filename else None

            # ── Stage 7: Quality Score ──────────────────────────────────────
            _check()
            score = await asyncio.get_event_loop().run_in_executor(
                None, self.groq.score_script, current_script
            )

            jm.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                stage="completed",
                progress=100,
                audio_url=audio_url,
                quality_score=score,
            )
            logger.info("[%s] ✅ Podcast generated successfully", job_id)

        except InterruptedError:
            logger.info("[%s] Job cancelled", job_id)

        except Exception as exc:
            logger.exception("[%s] Pipeline failed: %s", job_id, exc)
            jm.update_job(
                job_id,
                status=JobStatus.FAILED,
                stage="failed",
                error=str(exc),
            )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _extract(self, input_type, content, filename, config):
        if input_type == "topic":
            # Research the topic via LLM
            return self.groq.research_topic(content, config.get("audience", "general"))
        elif input_type == "url":
            return self.extractor.extract_from_url(content)
        elif input_type == "document":
            return self.extractor.extract_from_document(content, filename or "file.txt")
        else:
            raise ValueError(f"Unknown input type: {input_type}")

    def _derive_topic(self, input_type, content, config):
        if input_type == "topic":
            return content
        elif input_type == "url":
            # Extract title from URL
            from urllib.parse import urlparse
            path = urlparse(content).path
            parts = [p for p in path.split("/") if p]
            if parts:
                return parts[-1].replace("-", " ").replace("_", " ").title()
            return content
        elif input_type == "document":
            return config.get("filename", "Document")
        return "podcast topic"
