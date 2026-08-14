# Changelog

## Unreleased

### Added

- `docs/vision.md`, `docs/decisions.md` — product intent and settled questions, so agents read intent instead of inferring it.
- `docs/corrections.md` — running log of agent corrections, written as they happen. Gives the retro loop something to count.
- `.claude/skills/retro` — routes a correction to the file it belongs in, checks whether an existing rule already covers it, and caps `CLAUDE.md` at 600 words with eviction.
- `README.md`.

### Changed

- `CLAUDE.md` rewritten. Rules now have triggers: name the check and run it, name the strongest objection before building, stop when two readings produce different artifacts, fix at the layer that owns the concept, everything needs a caller today.
- Permanence split from scope — interfaces are permanent, implementations disposable — replacing the contradiction between "smallest thing that works" and "never a stopgap".

### Removed

- Rules that restated default model behavior or had no recognizable trigger: "keep components modular", "read what is already here", the banned-adjective list.
