# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- The product design: vision, the implementation description (entities, storage, API,
  workflows, layer map), and decision records (`docs/`).
- The development process: `make check` as the executable definition of done
  (`scripts/gates/`), the spec → plan → build → compound loop as skills, independent
  claim auditing and adversarial review, enforcement hooks, and CI running the same
  command as local.

### Fixed

- `make check` covers markdown prose and unowned TODOs again, resolves doc references in
  files git does not track yet, stops reading words like `framework/` as broken paths, and
  ignores a Python virtualenv at the repository root.
