# Decisions

Append-only. One line each. Everything here is settled — do not re-ask it, do not re-derive it, do not quietly build against a different answer.

Admission test: would a different answer have changed what gets built? If not, it is not a decision and does not belong here. To reverse one, append a line naming what it supersedes.

- 2026-08-14 — Execution model: full platform. Extractors are defined in ExtractLayer and we run them — not an SDK wrapping the user's own inference, not a proxy in front of it. Scoped to execution; how runs first reach us for read-only observability is open.
- 2026-08-14 — Core wedge: observability. Versioning and auto-improvement rank below it and build on the run record.
- 2026-08-14 — First user: platform and AI teams at mid-size companies. Not solo developers, not non-technical operators.
- 2026-08-14 — Ambiguity policy: stop and ask. Agents do not resolve ambiguity by guessing when the readings would produce different artifacts.
