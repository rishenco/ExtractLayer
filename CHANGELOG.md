# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Extractors over a REST API: create one with source columns and a JSON Schema draft 2020-12 schema, read it, update its name, description and schema, page through them with a cursor, and delete it. `docker compose up` brings up the database and the service.
- The product design: vision, the implementation description (entities, storage, API, workflows, layer map), and decision records (`docs/`).
- The development process: `make check` as the executable definition of done (`scripts/gates/`), the plan → build → compound loop as skills, one approved document per change (`work/<slug>/plan.md`), independent claim auditing and adversarial review, enforcement hooks, and CI running the same command as local.
- A pull request an agent opens gets a listener: the session subscribes to its CI and review activity instead of leaving it unwatched.
- `/reconcile` checks the written record against the repo — citations naming things that do not exist, prose contradicting an executable, one rule stated in several files — fixes what is mechanical and reports what needs a decision.

### Fixed

- `make check` covers markdown prose and unowned TODOs again, resolves doc references in files git does not track yet, rejects a doc citation that names a line number, stops reading words like `framework/` as broken paths, and ignores a Python virtualenv at the repository root.
