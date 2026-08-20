@AGENTS.md

Claude-specific notes on top of the operating rules above.

- `/plan`, `/build` and `/compound` are the skills that run the loop above; `/vision` writes `docs/vision.md` before it starts.
- `/reconcile` sits outside the loop: run it when the written record has drifted from the repo.
- `/tune` sits outside it too: run it after the human has had to steer by hand, so the correction lands in the prompt that made it necessary.
- Delegate codebase search to the `codebase-researcher` subagent so its output never enters this context raw.
- Before asking for plan approval, run the `plan-reviewer` subagent on the design.
- After any change, run the `claim-auditor` subagent on what you assert, then the `adversarial-reviewer` subagent on the code. The three are different jobs; do not merge them.
- Hooks enforce what these instructions only request. A rule that matters belongs in `scripts/gates/` or `.claude/hooks/`, not here.
