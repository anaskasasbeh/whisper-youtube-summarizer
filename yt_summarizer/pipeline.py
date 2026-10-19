"""Run the whole pipeline: download -> transcribe -> summarize -> save results."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from openai import OpenAI

from .config import Settings
from .downloader import AUDIO_BITRATE_KBPS, download_audio
from .summarizer import Summaries, Summarizer
from .transcriber import transcribe

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    """Where the results were saved, the summaries, and the measured run stats."""

    out_dir: Path
    summaries: Summaries
    stats: dict


def create_client(settings: Settings) -> OpenAI:
    """Create an OpenAI-compatible client (Groq by default).

    ``max_retries`` makes the SDK wait and retry on rate limits (HTTP 429)
    and temporary server errors, honouring the API's ``retry-after`` header.
    """
    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        max_retries=5,
        timeout=180.0,
    )


def run_pipeline(
    url: str,
    out_root: Path,
    settings: Settings,
    client: OpenAI | None = None,
    language: str | None = None,
    keep_audio: bool = False,
) -> RunResult:
    """Download, transcribe and summarize one video; save everything in ``out_root/<video_id>/``."""
    client = client or create_client(settings)
    run_start = perf_counter()

    logger.info("Step 1/3: downloading audio...")
    step_start = perf_counter()
    audio = download_audio(url, out_root)
    download_sec = perf_counter() - step_start
    out_dir = audio.path.parent
    logger.info("Downloaded '%s' (%.2f MB) in %.1f s.", audio.title, audio.size_mb, download_sec)

    try:
        logger.info("Step 2/3: transcribing with %s...", settings.transcribe_model)
        step_start = perf_counter()
        transcript = transcribe(client, audio.path, settings.transcribe_model, language)
        transcribe_sec = perf_counter() - step_start
        _write(out_dir / "transcript.txt", transcript.text + "\n")
        logger.info(
            "Transcript: %d words, language=%s, in %.1f s.",
            len(transcript.text.split()),
            transcript.language,
            transcribe_sec,
        )

        logger.info("Step 3/3: summarizing with %s...", settings.summary_model)
        step_start = perf_counter()
        summarizer = Summarizer(client, settings.summary_model, settings.reasoning_effort)
        summaries = summarizer.summarize(transcript.text, transcript.language)
        summarize_sec = perf_counter() - step_start
        logger.info("Summaries ready in %.1f s.", summarize_sec)
    finally:
        if not keep_audio:
            audio.path.unlink(missing_ok=True)

    _write(
        out_dir / "summary_en.md",
        f"# {audio.title}\n\nSource: {audio.url}\n\n{summaries.english}\n",
    )
    _write(out_dir / "summary_ar.md", f"{summaries.arabic}\n\n---\nSource: {audio.url}\n")
    if summaries.notes:  # long videos only: keep the map-step notes for review/debugging
        _write(out_dir / "notes.md", summaries.notes + "\n")

    duration = transcript.duration_sec or audio.duration_sec
    usage = summarizer.usage
    stats = {
        "video": {
            "id": audio.video_id,
            "title": audio.title,
            "url": audio.url,
            "duration_sec": duration,
        },
        "audio": {"size_mb": audio.size_mb, "bitrate_kbps": AUDIO_BITRATE_KBPS},
        "transcript": {
            "language": transcript.language,
            "characters": len(transcript.text),
            "words": len(transcript.text.split()),
        },
        "summary": {
            "map_requests": summaries.map_requests,
            "notes_characters": len(summaries.notes) if summaries.notes else 0,
            "api_requests": usage.requests,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
        },
        "models": {
            "api_base_url": settings.base_url,
            "transcribe": settings.transcribe_model,
            "summary": settings.summary_model,
            "reasoning_effort": settings.reasoning_effort,
        },
        "timings_sec": {
            "download": round(download_sec, 2),
            "transcribe": round(transcribe_sec, 2),
            "summarize": round(summarize_sec, 2),
            "total": round(perf_counter() - run_start, 2),
        },
        "transcription_speed_x_realtime": (
            round(duration / transcribe_sec, 1) if duration and transcribe_sec else None
        ),
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _write(out_dir / "run_stats.json", json.dumps(stats, indent=2, ensure_ascii=False) + "\n")

    return RunResult(out_dir=out_dir, summaries=summaries, stats=stats)


def _write(path: Path, text: str) -> None:
    """Write a UTF-8 text file and log where it went."""
    path.write_text(text, encoding="utf-8")
    logger.info("Saved %s", path)
