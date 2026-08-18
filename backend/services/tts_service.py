"""
PodGen AI - TTS Service
Converts podcast scripts to multi-speaker audio.
Supports: gTTS (free), ElevenLabs (API), pyttsx3 (local offline).
"""

import os
import re
import uuid
import logging
import asyncio
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)
AUDIO_OUTPUT_DIR = Path("audio_output")
AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)


# ─── Script Parser ────────────────────────────────────────────────────────────

def parse_script(script: str, host_name: str = "HOST", guest_name: str = "GUEST") -> List[Tuple[str, str]]:
    """
    Parse a podcast script into a list of (speaker, text) tuples.
    Handles: HOST:, GUEST:, {host_name}:, {guest_name}:
    Also strips [stage directions].
    """
    segments = []
    pattern = re.compile(
        rf"(?i)^({re.escape(host_name)}|{re.escape(guest_name)}|HOST|GUEST)\s*:\s*(.+)",
        re.MULTILINE
    )

    for match in pattern.finditer(script):
        speaker_raw = match.group(1).upper()
        text = match.group(2).strip()

        # Remove stage directions like [laughs], [pause]
        text = re.sub(r"\[.*?\]", "", text).strip()
        text = re.sub(r"\s{2,}", " ", text)

        if not text:
            continue

        # Normalise speaker to HOST / GUEST
        if speaker_raw in (host_name.upper(), "HOST"):
            speaker = "HOST"
        else:
            speaker = "GUEST"

        # Split long segments at sentence boundaries for more natural pacing
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunk, chunks = "", []
        for sent in sentences:
            if len(chunk) + len(sent) < 400:
                chunk = (chunk + " " + sent).strip()
            else:
                if chunk:
                    chunks.append(chunk)
                chunk = sent
        if chunk:
            chunks.append(chunk)

        for c in chunks:
            segments.append((speaker, c))

    return segments


# ─── TTS Engines ─────────────────────────────────────────────────────────────

class GTTSEngine:
    """Free Google TTS – two different lang/accent combos for host vs guest."""

    def synthesise(self, text: str, speaker: str, output_path: str):
        from gtts import gTTS
        # Host: US English, Guest: UK English (slight accent difference)
        tld = "com" if speaker == "HOST" else "co.uk"
        tts = gTTS(text=text, lang="en", tld=tld, slow=False)
        tts.save(output_path)


class ElevenLabsEngine:
    """ElevenLabs high-quality TTS."""

    HOST_VOICE_ID = os.getenv("ELEVENLABS_HOST_VOICE", "21m00Tcm4TlvDq8ikWAM")   # Rachel
    GUEST_VOICE_ID = os.getenv("ELEVENLABS_GUEST_VOICE", "AZnzlk1XvdvUeBnXmlld")  # Domi

    def synthesise(self, text: str, speaker: str, output_path: str):
        import requests
        voice_id = self.HOST_VOICE_ID if speaker == "HOST" else self.GUEST_VOICE_ID
        api_key = os.getenv("ELEVENLABS_API_KEY", "")
        if not api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not set")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)


# ─── Main TTS Service ─────────────────────────────────────────────────────────

class TTSService:

    def __init__(self):
        self.engine_name = os.getenv("TTS_ENGINE", "gtts").lower()  # gtts | elevenlabs
        self._engine = self._load_engine()

    def _load_engine(self):
        if self.engine_name == "elevenlabs" and os.getenv("ELEVENLABS_API_KEY"):
            logger.info("Using ElevenLabs TTS engine")
            return ElevenLabsEngine()
        logger.info("Using gTTS engine (free)")
        return GTTSEngine()

    def generate_audio(
        self,
        script: str,
        job_id: str,
        host_name: str = "HOST",
        guest_name: str = "GUEST",
        progress_callback=None,
    ) -> Optional[str]:
        """
        Convert a podcast script to a merged MP3 file.
        Returns the file path relative to audio_output/.
        """
        try:
            from pydub import AudioSegment
        except ImportError:
            logger.error("pydub not installed. Cannot merge audio segments.")
            return self._generate_simple_audio(script, job_id, host_name, guest_name, progress_callback)

        segments = parse_script(script, host_name, guest_name)
        if not segments:
            logger.warning("No parseable segments in script.")
            return None

        temp_files = []
        combined = AudioSegment.silent(duration=500)  # 0.5s intro silence

        try:
            for i, (speaker, text) in enumerate(segments):
                if not text.strip():
                    continue

                tmp_path = str(AUDIO_OUTPUT_DIR / f"_tmp_{job_id}_{i}.mp3")
                try:
                    self._engine.synthesise(text, speaker, tmp_path)
                    temp_files.append(tmp_path)

                    seg = AudioSegment.from_mp3(tmp_path)
                    combined += seg + AudioSegment.silent(duration=300)  # natural pause

                    if progress_callback:
                        pct = int((i + 1) / len(segments) * 100)
                        progress_callback(pct)

                except Exception as e:
                    logger.warning("TTS failed for segment %d: %s", i, e)
                    continue

            out_filename = f"podcast_{job_id}.mp3"
            out_path = AUDIO_OUTPUT_DIR / out_filename
            combined.export(str(out_path), format="mp3", bitrate="128k")
            logger.info("Audio saved to %s (%.1f min)", out_path, len(combined) / 60000)

            return out_filename

        finally:
            for f in temp_files:
                try:
                    os.remove(f)
                except OSError:
                    pass

    def _generate_simple_audio(self, script, job_id, host_name, guest_name, progress_callback):
        """Fallback: generate individual segment files without merging."""
        segments = parse_script(script, host_name, guest_name)
        if not segments:
            return None

        out_dir = AUDIO_OUTPUT_DIR / f"podcast_{job_id}_segments"
        out_dir.mkdir(exist_ok=True)

        for i, (speaker, text) in enumerate(segments):
            tmp_path = str(out_dir / f"{i:04d}_{speaker}.mp3")
            try:
                self._engine.synthesise(text, speaker, tmp_path)
                if progress_callback:
                    progress_callback(int((i + 1) / len(segments) * 100))
            except Exception as e:
                logger.warning("Segment %d failed: %s", i, e)

        return f"podcast_{job_id}_segments"
