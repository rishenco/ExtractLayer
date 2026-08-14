# ExtractLayer

A runtime for LLM extractors, sold on observability.

`docs/vision.md` is what we are building and for whom. `docs/decisions.md` is what is already settled. Read both before non-trivial work, and trust them over your own inference.

## Before code

**Name the check that proves it is done** — a command, an observable behavior, a falsifiable claim — before you start. If you cannot name one, you do not understand the task yet. Run it before you say you are finished; "it should work" is not a result.

**Stop and ask when the request has more than one reasonable reading.** Guessing is not efficiency; a wrong guess costs more than a question. Ask one question, take the answer, keep going.

**Say when the request conflicts with the goal.** If what was asked for works against `docs/vision.md`, or would be better solved differently, say so before building it. Obeying a bad instruction is a bug, not politeness.

Answers are durable — append one line to `docs/decisions.md` so nothing is decided twice.

## Building

Small scope, permanent decisions. Ship the smallest thing that works end to end, then build on top of something that already works — but decide as though the decision stays. Never a stopgap meant to be replaced later.

Fix causes at the layer that owns the concept. Name the layer before editing. If the fix needs knowledge that layer should not have, you are at the wrong layer — say where it belongs.

Everything you add needs a caller today. No speculative abstraction, no unrequested options, no handling for failures that cannot happen yet. If you think something extra is needed, say it instead of building it.

Read what is already here — the code, the dependency's docs and types — before reimplementing it or adding a package.

## Voice

Write as the author of the codebase, not as a narrator explaining it. No comment restates its code. No reasoning survives into the product. Exceptions: directives like `//nolint`, and algorithms that are genuinely non-obvious.

Prose short, plain, specific. Cut recaps of what you just did. Cut "comprehensive", "robust", "seamless", "powerful".

## Finishing

Run an adversarial review sub-agent. Fix what is real; say what you dismissed and why.

Update `CHANGELOG.md`.

If the user corrected you this session, run `/retro` — it decides what, if anything, becomes permanent.
