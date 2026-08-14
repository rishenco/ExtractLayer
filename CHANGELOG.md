# Changelog

## Unreleased

### Added

- `docs/vision.md`, `docs/decisions.md` — product intent and settled questions, so agents read intent instead of inferring it.
- `docs/corrections.md` — running log of agent corrections, written as they happen. Gives the retro loop something to count.
- `.claude/skills/retro` — routes a correction to the file it belongs in, checks whether an existing rule already covers it, and caps `CLAUDE.md` with eviction.
- `README.md`.

### Changed

- `CLAUDE.md` rewritten so every rule fires on a recognizable action — about to touch an unnamed file, about to write a duplicate guard, about to claim done.
- The scope rule and the layer rule merged into one pair, after a trial agent found a duplicated coercion and then declined to settle it because that meant opening a file the task did not name. Naming the duplicate as a thing that forces the edit fixed both rules at once: across nine trials on one task, layer fixes went 0/3 (diagnostic wording) to 1/3 (action wording) to 3/3 (merged), while the merged wording also produced the smallest diffs.
- Permanence split from scope — interfaces permanent, implementations disposable — replacing the contradiction between "smallest thing that works" and "never a stopgap". Contradictory rules cause both to be ignored.
- Cap lowered to 500 words / 80 lines; selective ignoring sets in around 80 lines.
- Retro's admission gate now requires a rule's trigger to be an action rather than a diagnosis, and routes must-hold rules to hooks or tests instead of a fourth restatement.

### Removed

- Rules that restated default model behavior or had no recognizable trigger: "keep components modular", "read what is already here", the banned-adjective list, and "run your tests" (agents verified unprompted in every trial).
