# ExtractLayer

A runtime for LLM extractors, sold on observability.

`docs/vision.md` is what we are building and for whom. `docs/decisions.md` is what is already settled. Read both before non-trivial work, and trust them over your own inference.

## Before code

**Name the check that proves it is done** — a command to run, or a behavior to observe. If you cannot name one, you do not understand the task yet. Run it before you say you are finished; "it should work" is not a result.

**Name the strongest objection to what was asked**, in one line, before building it. If the request works against `docs/vision.md`, or would be better solved another way, that is the moment to say so — not in review, when it is already built.

**Stop and ask when two readings would produce different artifacts.** Guessing is not efficiency. Ask one question, take the answer, keep going. If nobody is there to answer, take the reading that is cheapest to reverse and say which one you took.

Answers are durable. If a different answer would have changed what got built, append it to `docs/decisions.md` so it is never asked twice.

## Building

**Interfaces are permanent, implementations are disposable.** Names, data shapes, and boundaries are decided as though they stay. An in-memory store behind a settled interface is fine; the same store leaking its shape into callers is not. Ship the smallest thing that works end to end, then build on top of it.

**Fix causes at the layer that owns the concept.** Name the layer before editing. If the fix needs knowledge that layer should not have, you are at the wrong layer — say where it belongs.

**Everything you add needs a caller today.** No speculative abstraction, no unrequested options, no handling for failures that cannot happen yet. If you think something extra is needed, say it instead of building it.

Code no human would write, concretely: a wrapper with one caller, a config struct for two values, a layer that only forwards, error handling for an error the types rule out, an interface with one implementation and no second in sight.

When two implementations both pass the check, prefer the one that deletes more code, then the one a reader understands without scrolling.

## Voice

Write as the author of the codebase, not a narrator explaining it — no comment restates its code, no reasoning survives into the product. Exceptions: directives like `//nolint`, and genuinely non-obvious algorithms.

Prose short, plain, specific. Cut recaps of what you just did.

## Finishing

If you changed code, run an adversarial review sub-agent. Fix what is real; say what you dismissed and why.

Update `CHANGELOG.md`.

When the user corrects you, append one line to `docs/corrections.md` as it happens. Run `/retro` at the end of the session to decide what, if anything, becomes permanent.
