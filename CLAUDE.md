@AGENTS.md

Claude-specific notes on top of the operating rules above.

- Skills: `/vision`, `/spec`, `/plan`, `/build`, `/compound`. They are the loop, in order.
- Delegate codebase search to the `codebase-researcher` subagent so its output never enters
  this context raw.
- After any change, run the `adversarial-reviewer` subagent. Fix what is significant.
- Hooks enforce what these instructions only request. A rule that matters belongs in
  `scripts/gates/` or `.claude/hooks/`, not here.
