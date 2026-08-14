# ExtractLayer — a runtime for LLM extractors, sold on observability.

`docs/vision.md` is the intent. `docs/decisions.md` is what is settled. Read both before non-trivial work, and trust them over your own inference.

## Before code

**When two readings of the request would produce different artifacts, stop and ask.** One question, then keep going. If nobody is there to answer, take the reading that is cheapest to reverse and say which one you took.

**Say the strongest objection to the request, in one line, before building it.** If it works against the vision, or has a better solution, that is the moment to say so — not after it exists.

**Say what would prove it done** — a command to run, or a behavior to observe.

## While building

**Before touching a file the task did not name, say what forces it.** Test scaffolding, a version bump, a refactor, a new config file. If nothing forces it, propose it instead of building it.

**When you are about to write the same guard, coercion, or fallback a second time, stop.** The first site was already the wrong place. Say which layer owns the value and settle it there.

**Everything you add needs a caller today.** No speculative abstraction, no unrequested options, no error paths the types rule out. The shapes to notice: a wrapper with one caller, a config struct for two values, a layer that only forwards.

**Never let a command write outside the project directory.** Global installs, machine-level config — use the project-local form, or ask.

When two versions both pass, keep the one that deletes more code.

## When writing anything

**Claim only what a check you actually ran covers.** "Every case", "now works", coverage claims in a changelog — name the command that shows it, or weaken the sentence. Evidence against you goes in too.

No comment restates its code. No reasoning survives into the product. Exceptions: directives like `//nolint`, and genuinely non-obvious algorithms.

Prose short, plain, specific. No recaps of what you just did.

## Finishing

If you changed code, run an adversarial review sub-agent. Fix what is real; say what you dismissed and why.

Update `CHANGELOG.md`.

Log each correction to `docs/corrections.md` as it happens. Run `/retro` to decide what becomes permanent.
