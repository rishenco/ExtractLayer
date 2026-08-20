# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- A derived column may not be named after one of the extractor's source columns, at creation or at a schema edit, so a row can no longer lose its source value to a column that shadows it.
- Datasets, models and the serve path: give an extractor datasets of rows validated against its source columns and schema, batch-upsert and delete those rows, create models and archive the ones a role no longer needs, point the specimen and serving roles at them, and call `POST /extractors/{id}/serve` to turn one source row into its derived row.
- Extractors over a REST API: create one with source columns and a JSON Schema draft 2020-12 schema, read it, update its name, description and schema, page through them with a cursor, and delete it. `docker compose up` brings up the database and the service.
- The product design: vision, the implementation description (entities, storage, API, workflows, layer map), and decision records (`docs/`).
- The development process: `make check` as the executable definition of done (`scripts/gates/`), the plan → build → compound loop as skills, one approved document per change (`work/<slug>/plan.md`), independent claim auditing and adversarial review, enforcement hooks, and CI running the same command as local.
- A pull request an agent opens gets a listener: the session subscribes to its CI and review activity instead of leaving it unwatched.
- A plan opens with a TL;DR — afterwards, decisions, shape — and approval reads from it; `make check` caps the summary at 15 lines and the plan at 200.
- The development process: `make check` as the executable definition of done (`scripts/gates/`), the plan → build → compound loop as skills, one approved document per change (`work/<slug>/plan.md`), a design review before approval and an adversarial code review after the build, independent claim auditing, enforcement hooks, and CI running the same command as local.
- `/reconcile` checks the written record against the repo — citations naming things that do not exist, prose contradicting an executable, one rule stated in several files — fixes what is mechanical and reports what needs a decision.
- `/tune` reads a session's course corrections back into the harness — the skill, subagent, or rule that would have made each one unnecessary — and hands what a check could catch to `/compound`.

### Fixed

- `make check` covers markdown prose and unowned TODOs again, resolves doc references in files git does not track yet, rejects a doc citation that names a line number, stops reading words like `framework/` as broken paths, and ignores a Python virtualenv at the repository root.
