"""Speech-to-text with a Whisper model through an OpenAI-compatible API (Groq by default)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from .errors import SummarizerError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Transcript:
    """Transcribed text and what the API tells us about the audio."""

    text: str
    language: str | None
    duration_sec: float | None


def transcribe(
    client: OpenAI,
    audio_path: Path,
    model: str,
    language: str | None = None,
) -> Transcript:
    """Send an audio file to the Whisper endpoint and return the transcript.

    Args:
        client: API client (already pointed at Groq or OpenAI).
        audio_path: MP3 file to transcribe (max 25 MB).
        model: Whisper model name, e.g. ``whisper-large-v3-turbo``.
        language: Optional ISO-639-1 code (``"ar"``, ``"en"``). Giving it
            improves accuracy; leave it empty to auto-detect.

    Raises:
        SummarizerError: if the API returns no text.
    """
    options: dict = {"model": model, "response_format": "verbose_json", "temperature": 0.0}
    if language:
        options["language"] = language

    with audio_path.open("rb") as audio:
        result = client.audio.transcriptions.create(file=audio, **options)

    text = (result.text or "").strip()
    if not text:
        raise SummarizerError("The transcript is empty. Does the video contain speech?")

    return Transcript(
        text=text,
        language=getattr(result, "language", None),
        duration_sec=getattr(result, "duration", None),
    )
