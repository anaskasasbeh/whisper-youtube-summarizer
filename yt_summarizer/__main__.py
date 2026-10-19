"""Command-line entry point:  python -m yt_summarizer "<YouTube URL>"."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import openai

from .config import load_settings
from .errors import SummarizerError
from .pipeline import RunResult, run_pipeline

logger = logging.getLogger("yt_summarizer")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Define and read the command-line options."""
    parser = argparse.ArgumentParser(
        prog="python -m yt_summarizer",
        description="Transcribe a YouTube video with Whisper and summarize it "
        "in English and Arabic.",
    )
    parser.add_argument("url", help="YouTube video URL (put it in quotes)")
    parser.add_argument(
        "-l", "--language",
        help="spoken language as an ISO-639-1 code, e.g. ar or en (default: auto-detect)",
    )
    parser.add_argument(
        "-o", "--out", type=Path, default=Path("outputs"),
        help="folder for the results (default: outputs)",
    )
    parser.add_argument("--keep-audio", action="store_true", help="keep the downloaded MP3 file")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug logs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return an exit code (0 = success)."""
    args = parse_args(argv)
    _use_utf8_output()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    if not args.verbose:
        # One log line per HTTP request is noise (the openai SDK uses httpx2 under the hood).
        for name in ("httpx", "httpx2"):
            logging.getLogger(name).setLevel(logging.WARNING)

    try:
        settings = load_settings()
        result = run_pipeline(
            url=args.url,
            out_root=args.out,
            settings=settings,
            language=args.language,
            keep_audio=args.keep_audio,
        )
    except SummarizerError as exc:
        logger.error("%s", exc)
        return 1
    except openai.AuthenticationError:
        logger.error("The API key was rejected. Check API_KEY in your .env file.")
        return 1
    except openai.RateLimitError:
        logger.error(
            "Rate limit reached even after retrying. Wait a minute and try again "
            "(daily limits reset after 24 hours)."
        )
        return 1
    except openai.APIConnectionError:
        logger.error("Could not reach the API. Check your internet connection.")
        return 1
    except openai.APIStatusError as exc:
        logger.error("API error %s: %s", exc.status_code, exc.message)
        return 1
    except KeyboardInterrupt:
        logger.warning("Stopped by the user.")
        return 130

    _print_results(result)
    return 0


def _print_results(result: RunResult) -> None:
    """Show both summaries in the terminal."""
    print("\n=== English summary ===\n")
    print(result.summaries.english)
    print("\n=== Arabic summary ===\n")
    print(result.summaries.arabic)
    print(f"\nAll results saved in: {result.out_dir.resolve()}")


def _use_utf8_output() -> None:
    """Print Arabic safely, even when Windows output is redirected to a file."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
