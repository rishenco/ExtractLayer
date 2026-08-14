# ExtractLayer

Observability, versioning, and auto-improvement for LLM-based extractors.

You define an extractor here, ExtractLayer runs it, and every run is recorded — input, output, prompt version, latency, cost, failure. Versioning and auto-improvement are built on that record.

## Project context

Agents read these before working. So should you.

- `docs/vision.md` — what this is, who it is for, what has to be excellent
- `docs/decisions.md` — settled questions, append-only. Nothing here gets re-litigated
- `CLAUDE.md` — how agents work in this repo, capped at 600 words
- `docs/corrections.md` — a running log of times an agent got it wrong

The loop: when an agent is corrected, the correction is logged. `/retro` reads that log and decides where the missing context belonged — usually `vision.md` or `decisions.md`, rarely `CLAUDE.md`. A rule is earned only by a mistake that has happened twice, and only by evicting something else.
