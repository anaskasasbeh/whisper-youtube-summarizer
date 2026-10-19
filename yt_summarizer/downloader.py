"""Download the audio track of a YouTube video as a small MP3 file."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

from .errors import SummarizerError

logger = logging.getLogger(__name__)

# Speech does not need music quality: 64 kbps mono keeps files small.
# Whisper APIs accept files up to 25 MB -> roughly 50 minutes at this bitrate.
AUDIO_BITRATE_KBPS = 64
MAX_UPLOAD_MB = 25.0


@dataclass(frozen=True)
class AudioFile:
    """A downloaded audio file plus the video metadata we keep."""

    path: Path
    video_id: str
    title: str
    url: str
    duration_sec: float | None
    size_mb: float


class _YtDlpLogger:
    """Route yt-dlp messages into Python logging instead of printing them."""

    def debug(self, msg: str) -> None:
        logger.debug(msg)

    def info(self, msg: str) -> None:
        logger.debug(msg)

    def warning(self, msg: str) -> None:
        logger.warning(msg)

    def error(self, msg: str) -> None:
        # yt-dlp raises DownloadError right after this; we report it there.
        logger.debug(msg)


def check_ffmpeg() -> None:
    """Fail early with a clear message if ffmpeg is not installed."""
    if shutil.which("ffmpeg") is None:
        raise SummarizerError(
            "ffmpeg was not found. Install it, then close and reopen VS Code / the terminal "
            "(Windows: winget install --id=Gyan.FFmpeg -e)."
        )


def download_audio(url: str, out_root: Path) -> AudioFile:
    """Download a video's audio to ``out_root/<video_id>/audio.mp3``.

    Args:
        url: YouTube video URL.
        out_root: Folder that will contain one sub-folder per video.

    Raises:
        SummarizerError: if the download fails or the file is too large.
    """
    check_ffmpeg()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_root / "%(id)s" / "audio.%(ext)s"),
        "noplaylist": True,  # a URL with &list=... downloads only this video
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(AUDIO_BITRATE_KBPS),
            }
        ],
        # ffmpeg options: 1 channel (mono), 16 kHz (Whisper's native sample rate)
        "postprocessor_args": {"extractaudio": ["-ac", "1", "-ar", "16000"]},
        "logger": _YtDlpLogger(),
        "noprogress": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc).removeprefix("ERROR: ")
        raise SummarizerError(f"Could not download the audio: {message}") from exc

    video_id = info["id"]
    path = out_root / video_id / "audio.mp3"
    if not path.exists():
        raise SummarizerError(f"Download finished but {path} was not created.")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise SummarizerError(
            f"The audio is {size_mb:.1f} MB, above the {MAX_UPLOAD_MB:.0f} MB API limit "
            f"(about 50 minutes of speech). Try a shorter video."
        )

    return AudioFile(
        path=path,
        video_id=video_id,
        title=info.get("title") or video_id,
        url=info.get("webpage_url") or url,
        duration_sec=info.get("duration"),
        size_mb=round(size_mb, 2),
    )
