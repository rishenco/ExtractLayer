# Lessons

Rules learned from real defects that could not be made executable. Everything here is debt:
each line is a rule a human has to remember instead of a check that fails the build.

Added by `/compound`, and only after a test, a gate, and a hook were each ruled out.

Format: one line, imperative, with the change that taught it.

## Open

- In-repo approval markers are forgeable by an agent: `Status: Approved` and
  `Skips-plan-gate:` are both writable by whoever writes the code. `70-approved-plan.sh` makes
  intent traceable, not enforced. The non-forgeable gate is the pull request review on GitHub,
  so branch protection requiring a human approval is what actually holds — added while
  bootstrapping the loop.
- `10-comments.sh` matches per line, so a `#` or a URL inside a heredoc, a Go raw string, or a
  Python triple-quoted string reads as a comment and fails the gate. Move comment linting to
  each workspace linter, which parses instead of guessing, as soon as a stack lands — found by
  adversarial review of the gate itself.
