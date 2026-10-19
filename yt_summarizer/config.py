"""Load settings from environment variables and the local .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .errors import SummarizerError

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_TRANSCRIBE_MODEL = "whisper-large-v3-turbo"
DEFAULT_SUMMARY_MODEL = "openai/gpt-oss-120b"


@dataclass(frozen=True)
class Settings:
    """Everything the pipeline needs to talk to the API."""

    api_key: str
    base_url: str
    transcribe_model: str
    summary_model: str
    reasoning_effort: str | None


def load_settings() -> Settings:
    """Read settings from .env / environment variables.

    Raises:
        SummarizerError: if API_KEY is missing.
    """
    load_dotenv()

    api_key = os.getenv("API_KEY", "").strip()
    if not api_key:
        raise SummarizerError(
            "API_KEY is not set. Copy .env.example to .env and paste your key "
            "(free Groq key: https://console.groq.com/keys)."
        )

    return Settings(
        api_key=api_key,
        base_url=os.getenv("API_BASE_URL", "").strip() or DEFAULT_BASE_URL,
        transcribe_model=os.getenv("TRANSCRIBE_MODEL", "").strip() or DEFAULT_TRANSCRIBE_MODEL,
        summary_model=os.getenv("SUMMARY_MODEL", "").strip() or DEFAULT_SUMMARY_MODEL,
        reasoning_effort=os.getenv("REASONING_EFFORT", "").strip() or None,
    )
