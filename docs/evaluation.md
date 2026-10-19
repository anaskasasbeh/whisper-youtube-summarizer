# Evaluation notes

How the pipeline was tested, what went wrong, and what changed.
Every number below comes from `run_stats.json` or the terminal log of a real run
(Windows PC, consumer internet connection in Jordan, Groq free tier, October 2026).
Each configuration was run once, so treat timings as single measurements, not benchmarks.

## Test videos

| Example | Language | Duration | Why it was chosen |
|---|---|---|---|
| [Docker in 5 mins](https://www.youtube.com/watch?v=yRkE-1Lq0qo) | Arabic (Egyptian dialect, many English tech terms) | 3 min 15 s | Short path: no map step |
| [GitHub Actions Tutorial](https://www.youtube.com/watch?v=R8_veQiYBjI) | English | 32 min 30 s | Long path: map-reduce + rate limits |

## Method

1. Run the CLI on each video and keep `transcript.txt`, both summaries and `run_stats.json`.
2. Read the transcript, then check each summary bullet against it (names, numbers, claims).
3. Fix what is wrong, run again, and compare.

## Issues found in the first long-video run, and fixes

| # | Issue | Cause | Fix |
|---|---|---|---|
| 1 | The English summary had a section called *"German/Chinese notes"*, although the transcript is 100% English | The map step asked for notes "in the same language as the text"; the model drifted into another language for one chunk | Notes are now requested in the language detected by Whisper (e.g. "in English"), and saved to `notes.md` so they can be reviewed |
| 2 | A second, unnecessary condense round (5 chunks, then 2 more) | Round-1 notes were 7,220 characters, just above the 6,000-character chunk size that also acted as the reduce limit | Separate limit for the final step: up to 10,000 characters (estimated ~2.5K–3.3K tokens, using ~4 characters/token for English and ~3 for Arabic observed in these runs) |
| 3 | One map answer hit the token limit (`An answer reached the token limit`) | `max_completion_tokens=1024` was tight for notes plus reasoning | Raised to 1,536 |
| 4 | English summary was ~110 lines long | No length guidance in the prompt | "At most 12 bullet points; merge related ideas" |

### Before vs after (same video, identical transcript)

Whisper produced the exact same transcript in both runs, so the differences below come only
from the summarization changes.

| Metric | Before fix | After fix |
|---|---:|---:|
| Map (condense) rounds | 2 | 1 |
| Map requests | 7 | 5 |
| Total chat API requests | 9 | 7 |
| Prompt tokens | 12,175 | 9,868 |
| Completion tokens | 6,123 | 2,953 |
| Rate-limit retries (HTTP 429, handled automatically) | 4 | 2 |
| Summarization time | 76.08 s | 36.40 s |
| Total run time | 266.82 s | 223.98 s |
| English summary length | ~110 lines | 12 bullets |
| Non-English text in notes/summary | yes | none |

Time spent waiting on rate limits varies from run to run; request and token counts are the
more stable comparison.

## Error analysis: where mistakes come from

The LLM never hears the audio — it only reads the transcript. So errors come from two places:

**Speech recognition (Whisper)** — most errors were English technical words inside Arabic
speech (code-switching), not the dialect itself:

| Heard as | Meant |
|---|---|
| ايروز | errors |
| الفاكتج | package |
| نوت 18 | Node 18 |
| البروشيكت | project |
| "daytime" | "date time" (English video) |
| "metrics" | "matrix" (English video) |

One stretch of the Arabic transcript collapsed into a list of English terms
(`Operating System Package Docker Docker Image image container container`).

**Summarization (LLM)**:

- It often *repairs* recognition errors from context (it wrote "matrix strategy" and
  "date-time" correctly), which helps readability but means it uses outside knowledge.
- For the same reason it can add details that were never said: both summaries of the
  English video mention `docker/build-push-action@v2`, but "v2" does not appear in the
  transcript (it was introduced in the map-step notes).

Takeaway: summaries are useful for a quick overview, but names, versions and numbers should be
checked against `transcript.txt`.
