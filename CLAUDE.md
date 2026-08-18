@AGENTS.md

Claude-specific notes on top of the operating rules above.

- Skills: `/vision`, `/spec`, `/plan`, `/build`, `/compound`. They are the loop, in order.
- Delegate codebase search to the `codebase-researcher` subagent so its output never enters this context raw.
- After any change, run the `claim-auditor` subagent on what you assert, then the `adversarial-reviewer` subagent on the code. They are different jobs; do not merge them.
- Hooks enforce what these instructions only request. A rule that matters belongs in `scripts/gates/` or `.claude/hooks/`, not here.
