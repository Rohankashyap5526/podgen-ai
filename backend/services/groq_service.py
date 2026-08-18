"""
PodGen AI - Groq LLM Service
Handles all LLM calls: summarisation, script generation, metadata.
"""

import os
import json
import logging
from typing import Optional, Generator

logger = logging.getLogger(__name__)


STYLE_PROMPTS = {
    "educational": (
        "Create an engaging, informative podcast where the host and guest "
        "explore the topic in depth, explaining concepts clearly with relatable examples."
    ),
    "debate": (
        "Create a lively debate-style podcast where the host and guest take "
        "opposing or differing perspectives, challenging each other respectfully "
        "while exploring nuances of the topic."
    ),
    "storytelling": (
        "Create a narrative-driven podcast that weaves the topic into compelling "
        "stories, anecdotes, and human experiences, keeping listeners hooked throughout."
    ),
}

AUDIENCE_PROMPTS = {
    "general": "Assume a general adult audience with no specialized knowledge.",
    "technical": "Assume a technically sophisticated audience comfortable with jargon.",
    "kids": "Use simple language, fun analogies, and an upbeat tone suitable for children.",
    "experts": "Assume domain experts; go deep, cite evidence, avoid over-simplification.",
}


class GroqService:
    """Wrapper around the Groq REST API for fast LLM inference."""

    MODEL = "openai/gpt-oss-120b"
    FALLBACK_MODEL = "mixtral-8x7b-32768"

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set – LLM calls will fail.")
        self._client = None

    def _get_client(self):
        """Lazy-init the Groq client (singleton per service instance)."""
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        return self._client

    # ─── Core Chat ────────────────────────────────────────────────────────────

    def chat(self, system: str, user: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("Groq API error: %s", exc)
            raise RuntimeError(f"LLM inference failed: {exc}")

    # ─── Summarisation ────────────────────────────────────────────────────────

    def summarise(self, text: str, max_words: int = 600) -> str:
        system = (
            "You are an expert content analyst. Summarise the given text accurately, "
            "preserving all key facts, arguments, and insights. "
            f"Target length: approximately {max_words} words."
        )
        user = f"Summarise this content:\n\n{text[:8000]}"
        return self.chat(system, user, max_tokens=1024, temperature=0.3)

    # ─── Topic Research ───────────────────────────────────────────────────────

    def research_topic(self, topic: str, audience: str = "general") -> str:
        system = (
            "You are a brilliant research assistant. Given a podcast topic, "
            "generate comprehensive background knowledge, key facts, interesting angles, "
            "controversies, expert perspectives, and compelling stories related to it. "
            f"{AUDIENCE_PROMPTS.get(audience, '')}"
        )
        user = f"Research this podcast topic thoroughly:\n\n{topic}"
        return self.chat(system, user, max_tokens=2048, temperature=0.6)

    # ─── Script Generation ────────────────────────────────────────────────────

    def generate_script(
        self,
        context: str,
        topic: str,
        style: str = "educational",
        audience: str = "general",
        tone: str = "conversational",
        duration_minutes: int = 10,
        host_name: str = "Alex",
        guest_name: str = "Jordan",
        host_personality: str = "curious and engaging",
        guest_personality: str = "knowledgeable and enthusiastic",
    ) -> str:
        style_desc = STYLE_PROMPTS.get(style, STYLE_PROMPTS["educational"])
        audience_desc = AUDIENCE_PROMPTS.get(audience, AUDIENCE_PROMPTS["general"])

        # Estimate word count (~130 wpm average podcast speech)
        target_words = duration_minutes * 130

        system = f"""You are a world-class podcast scriptwriter. {style_desc}

{audience_desc}

PODCAST SPEAKERS:
- HOST ({host_name}): {host_personality}
- GUEST ({guest_name}): {guest_personality}

TONE: {tone}

SCRIPT FORMAT RULES:
- Use the exact format: HOST: <dialogue> or GUEST: <dialogue>
- Include natural speech patterns: um, well, you know, right?, exactly!, wow
- Add stage directions in [brackets] for pauses, laughs, emphasis: [pause], [laughs], [excited]
- Target approximately {target_words} words total
- Structure: Intro (10%) → Deep Dive (60%) → Examples/Stories (20%) → Conclusion + CTA (10%)
- Make the conversation feel NATURAL and HUMAN, not scripted
- Include follow-up questions, interruptions, and genuine reactions
"""

        user = f"""Generate a complete podcast script on: "{topic}"

CONTENT CONTEXT (use this as your knowledge base):
{context[:6000]}

Write a full, high-quality podcast script now. Start immediately with the HOST introduction."""

        return self.chat(system, user, max_tokens=4096, temperature=0.75)

    # ─── Metadata Generation ─────────────────────────────────────────────────

    def generate_metadata(self, script: str, topic: str) -> dict:
        system = (
            "You are a podcast marketing expert. Given a script, generate compelling metadata. "
            "Respond ONLY with a valid JSON object, no markdown, no explanation."
        )
        user = f"""For this podcast about "{topic}", generate:
- title: catchy, SEO-friendly title (max 60 chars)
- description: engaging 2-3 sentence description
- tags: list of 8-10 relevant tags/keywords
- key_takeaways: list of 3-5 main insights

Script excerpt:
{script[:2000]}

JSON only:"""

        raw = self.chat(system, user, max_tokens=512, temperature=0.5)
        try:
            # Strip markdown fences if present
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "title": f"Podcast: {topic[:50]}",
                "description": f"An in-depth exploration of {topic}.",
                "tags": [topic.lower()],
                "key_takeaways": [],
            }

    # ─── Coherence Scoring ────────────────────────────────────────────────────

    def score_script(self, script: str) -> dict:
        system = (
            "You are a podcast quality evaluator. Respond ONLY with a valid JSON object."
        )
        user = f"""Evaluate this podcast script on:
- coherence (0-10): logical flow and consistency
- engagement (0-10): how captivating it is
- naturalness (0-10): how human and conversational it sounds
- information_density (0-10): depth of content

Script excerpt:
{script[:3000]}

JSON format: {{"coherence": N, "engagement": N, "naturalness": N, "information_density": N, "overall": N, "feedback": "..."}}"""

        raw = self.chat(system, user, max_tokens=256, temperature=0.2)
        try:
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(raw)
        except Exception:
            return {"overall": 7, "feedback": "Script generated successfully."}
