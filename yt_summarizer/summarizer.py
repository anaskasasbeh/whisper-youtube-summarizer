"""Summaries with a chat model: English bullet points + an Arabic "life coach" summary.

Long transcripts use a simple map-reduce:
    map    -> split the transcript into chunks and turn each chunk into short notes
    reduce -> write the final summaries from the combined notes
This keeps every request small enough for free-tier tokens-per-minute limits.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from openai import OpenAI

from .errors import SummarizerError

logger = logging.getLogger(__name__)

# Measured on real runs: ~4 characters per token for English, ~3 for Arabic.
# Map chunks of 6,000 characters (~1.5K-2K tokens) and a final (reduce) input of up to
# 10,000 characters (~2.5K-3.3K tokens) keep each request well under Groq's free
# limit of 8K tokens per minute, including the answer.
CHUNK_CHARS = 6_000
REDUCE_MAX_CHARS = 10_000
NOTES_MAX_TOKENS = 1_536
SUMMARY_MAX_TOKENS = 2_048
MAX_CONDENSE_ROUNDS = 3
TEMPERATURE = 0.3

NOTES_SYSTEM = "You extract the key points from parts of long video transcripts."
NOTES_PROMPT = """This is part {index} of {total} of a video transcript.
Write its key points as short bullet notes in {language}.
Keep names, numbers and examples. Do not add anything that is not in the text.

Text:
{text}"""

ENGLISH_SYSTEM = "You are good at creating clear, faithful bullet-point summaries of long texts."
ENGLISH_PROMPT = """Summarize the following {source} in English, in bullet point form.
Use at most 12 bullet points; merge related ideas.
Use only information from the text. Keep names and numbers exactly as they appear;
if a number is unclear in the text, say so instead of guessing.

Text:
{text}"""

ARABIC_SYSTEM = "You are an Arabic life coach who writes motivating but factual summaries."
ARABIC_PROMPT = """Create a summary of the following {source} in Arabic.
- Start with a short title in Arabic.
- Then list the most important ideas as bullet points (at most 12; merge related ideas).
- End with one short concluding sentence.
The summary must be informative and factual: use only information from the text.
Keep names and numbers exactly as they appear; if a number is unclear, say so instead of guessing.
Write the entire summary in Arabic.

Text:
{text}"""

_SENTENCE_END = re.compile(r"(?<=[.!?؟…])\s+")


@dataclass
class TokenUsage:
    """Token counts reported by the API, summed over all requests."""

    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def add(self, usage: object | None) -> None:
        self.requests += 1
        if usage is not None:
            self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0


@dataclass(frozen=True)
class Summaries:
    """The two final summaries, plus the intermediate notes for long transcripts."""

    english: str
    arabic: str
    map_requests: int
    notes: str | None = None  # map-step notes (None when the transcript was short)


def split_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of at most ``max_chars``, cutting at sentence ends when possible."""
    pieces: list[str] = []
    for sentence in _SENTENCE_END.split(text.strip()):
        if len(sentence) <= max_chars:
            pieces.append(sentence)
        else:
            pieces.extend(_pack(sentence.split(), max_chars))  # very long sentence: cut at spaces
    return _pack(pieces, max_chars)


def _pack(parts: list[str], max_chars: int) -> list[str]:
    """Greedily join parts with spaces into chunks no longer than ``max_chars``."""
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current} {part}" if current else part
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


class Summarizer:
    """Writes the English and Arabic summaries, condensing long transcripts first."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        reasoning_effort: str | None = None,
        chunk_chars: int = CHUNK_CHARS,
        reduce_max_chars: int = REDUCE_MAX_CHARS,
    ) -> None:
        self.client = client
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.chunk_chars = chunk_chars
        self.reduce_max_chars = reduce_max_chars
        self.usage = TokenUsage()

    def summarize(self, transcript: str, language: str | None = None) -> Summaries:
        """Return the English and Arabic summaries of a transcript.

        Args:
            transcript: Full transcript text.
            language: Spoken language reported by Whisper (e.g. ``"English"``).
                Map-step notes are written in this language so the model does not drift
                into another one; if unknown, notes follow the language of the text.
        """
        notes_language = language or "the same language as the text"
        text, map_requests = self._condense(transcript, notes_language)
        source = "notes taken from a long video transcript" if map_requests else "video transcript"

        logger.info("Writing the English summary...")
        english = self._chat(
            ENGLISH_SYSTEM, ENGLISH_PROMPT.format(source=source, text=text), SUMMARY_MAX_TOKENS
        )
        logger.info("Writing the Arabic summary...")
        arabic = self._chat(
            ARABIC_SYSTEM, ARABIC_PROMPT.format(source=source, text=text), SUMMARY_MAX_TOKENS
        )
        return Summaries(
            english=english,
            arabic=arabic,
            map_requests=map_requests,
            notes=text if map_requests else None,
        )

    def _condense(self, text: str, language: str) -> tuple[str, int]:
        """Map step: replace a long text with chunk notes until it fits in one request."""
        map_requests = 0
        rounds = 0
        while len(text) > self.reduce_max_chars:
            if rounds == MAX_CONDENSE_ROUNDS:
                raise SummarizerError(
                    "The transcript is too long to summarize. Try a shorter video."
                )
            chunks = split_text(text, self.chunk_chars)
            logger.info(
                "Long text (%d characters): summarizing it in %d chunks first.",
                len(text),
                len(chunks),
            )
            notes = [
                self._chat(
                    NOTES_SYSTEM,
                    NOTES_PROMPT.format(
                        index=i, total=len(chunks), language=language, text=chunk
                    ),
                    NOTES_MAX_TOKENS,
                )
                for i, chunk in enumerate(chunks, start=1)
            ]
            map_requests += len(chunks)
            rounds += 1
            text = "\n\n".join(notes)
        return text, map_requests

    def _chat(self, system: str, prompt: str, max_tokens: int) -> str:
        """Send one chat request and return the answer text."""
        options: dict = {}
        if self.reasoning_effort:
            options["reasoning_effort"] = self.reasoning_effort

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=max_tokens,
            temperature=TEMPERATURE,
            **options,
        )
        self.usage.add(response.usage)

        choice = response.choices[0]
        content = (choice.message.content or "").strip()
        if not content:
            raise SummarizerError(
                f"The model returned an empty answer (finish_reason={choice.finish_reason}). "
                "Try again, or set REASONING_EFFORT=low in .env."
            )
        if choice.finish_reason == "length":
            logger.warning("An answer reached the token limit and may be cut off.")
        return content
