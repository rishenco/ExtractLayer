# Tune before a compaction

Status: Draft

## TL;DR
- Afterwards: a manual compaction is deferred once, `/tune` runs against the conversation while it
  is still whole, and the next compaction proceeds.
- Decided: the deferral is one-shot per cycle. A hook cannot see whether a tune happened, and a
  hook that can block twice can block forever.
- Decided: an automatic compaction is never deferred, because blocking at the context limit risks
  the session. The hook reads the payload's `trigger` itself, so a matcher is not what holds it.
- Decided: the instruction rides `UserPromptSubmit`, because `PreCompact` output never reaches
  Claude. No hook can hand Claude a turn, so a tune costs one message.
- Shape:
  - `.claude/hooks/`: + `compact-defer.sh` defers the first manual compaction, + `tune-due.sh`
    says once that a tune is owed; the marker between them lands in the ignored `.local/`
  - `scripts/gates/06-hooks.sh`: + the deferral cycle on real payloads, + which event each hook
    is registered under

## Problem / Intent

`/tune` reads the conversation for the moments a human had to steer. Compaction replaces that
conversation with a summary, so the session that most needs tuning — long, and full of the
corrections length produces — is the one whose evidence goes first. A tune run afterwards reads a
summary that already dropped the moments, and the next session earns the same corrections again.

Afterwards: a manual `/compact` no longer discards an untuned conversation silently. The first one
is deferred, the tune runs against the whole transcript, and the second compacts.

Objections: firing `/tune` on context pressure rather than on the presence of a correction invites
the failure its own skill names, encoding a decision as a rule nobody made. Decided: fire anyway,
and carry the skill's bar into the instruction so a null result is a first-class outcome. A
merge-time trigger was argued down and dropped: a merge usually lands after the session that
earned it, when the conversation is already gone.

## Criteria

- [ ] A1 A `manual` payload with no marker present exits 2 and names `/tune`.
- [ ] A2 A `manual` payload with the marker present exits 0 and removes it, so one compaction is
      deferred at most once.
- [ ] A3 An `auto` payload exits 0 and writes no marker.
- [ ] A4 `tune-due.sh` names `/tune` on stdout while the marker is pending, and prints nothing on
      the next prompt.
- [ ] A5 `.claude/settings.json` maps `compact-defer.sh` to `PreCompact` and `tune-due.sh` to
      `UserPromptSubmit`; either name moved to another event fails `make check`.
- [ ] A6 A full defer, announce and compact cycle leaves `git status --porcelain` empty.
- [ ] A7 Writing a deferral removes any marker older than a day, so a session that ends deferred
      does not leave one behind for good.

## Not doing

- The pull request merge trigger.
- Deferring an automatic compaction.
- Verifying a tune actually ran. The deferral is one-shot, so re-running `/compact` at once
  compacts untuned.
- Any change to what `/tune` does, how it routes, or what it may edit.
- Tuning from a compaction summary, which is the outcome this exists to prevent.
- The positional `$?` fragility in the existing pull request cases at `06-hooks.sh:36`. The new
  cases capture status inside a helper; the old ones read correctly today.

## Research

- Claude Code 2.1.238 builds the `PreCompact` payload as `{hook_event_name, trigger,
  custom_instructions}`, `trigger` being `manual` or `auto`, and matches a `PreCompact` matcher
  against that same `trigger`. The hooks reference names the field `compaction_trigger`, a string
  this build does not contain.
- Every hook payload carries `session_id`, `transcript_path`, `cwd` and `permission_mode`, so a
  marker keyed on the session is reachable from both events.
- `UserPromptSubmit` accepts `hookSpecificOutput.additionalContext` and renders it as a
  `hook_additional_context` message, which is how an instruction reaches Claude.
- The build carries the string `compaction blocked by PreCompact hook`, so exit 2 blocks there.
- `scripts/gates/06-hooks.sh:59-68` requires every `.claude/hooks/*.sh` to be executable and its
  basename to appear anywhere in `.claude/settings.json`. The event key is not checked.
- `scripts/gates/06-hooks.sh:31` feeds a hook by `printf '%s' "$1" | bash <hook> 2>&1`, and reads
  `$?` in the statement after the call — correct only while nothing sits between them.
- `scripts/gates/05-selftest.sh:26-30` captures `got=$?` inside its `expect` helper.
- `.gitignore:1` ignores `.local`, and no file in the repo writes to it.
- `scripts/lib/files.sh:11-12` lists untracked files but honours `.gitignore`, so an ignored marker
  is invisible to every gate.
- `scripts/gates/10-comments.sh:20` scans `sh` for comments; `scripts/gates/30-slop.sh:31` greps
  `.claude/` for filler, so hook message text is held to the same prose bar as docs.
- `scripts/gates/20-budgets.sh:8` caps shell at 400 lines; `06-hooks.sh` is 73.
- `docs/architecture.md:69-75` scopes its layer map to `extractlayer/` and names nothing under
  `.claude/`, so no boundary changes and no ADR is owed.
- No shellcheck or shfmt exists in the repo; `make check` has no shell lint step.

## Approach

The trigger is harness enforcement, so it lands in `.claude/hooks/` beside the four hooks already
there rather than in skill prose, which `AGENTS.md` puts last because prose cannot fail a build.
`compact-defer.sh` runs on `PreCompact`: on a manual compaction with no marker it writes
`.local/compact-deferred-<session>` and exits 2, which blocks the compaction and prints what to do;
on a manual compaction with the marker present it removes it and exits 0. Writing one also drops
any marker over a day old, because a session that ends deferred leaves its own behind and
`docs/lessons.md` does not allow an unbounded store. `tune-due.sh` runs on
`UserPromptSubmit`: while the marker reads `pending` it returns the instruction to tune as
`hookSpecificOutput.additionalContext` and rewrites the marker to `announced`, so it speaks once
and the next compaction still passes. The marker takes
the slot `.gitignore` already reserves, which keeps session state out of every gate's file list for
free. The two hooks compute the marker path independently rather than sharing a library, because
`06-hooks.sh` requires every file in `.claude/hooks/` to be a registered hook, and the end-to-end
case is what catches drift between them.

Rejected:

- A `SessionStart` hook matched on `compact`. The only mechanism that reaches Claude cleanly, and
  it reaches it after the summary has replaced the conversation — it tunes from the input this
  change exists to protect.
- A `Stop` hook that tunes once the transcript passes a size watermark. It needs no extra message
  and it would cover automatic compaction, but the watermark guesses where the limit is and the
  tune lands on an arbitrary turn mid-build. A threshold meant to be corrected later is a stopgap.
- `PreCompact` running the tune itself in a nested non-interactive session. It removes the extra
  message and puts an unbounded agent inside a hook timeout, with no conversation to read.
- Blocking until a tune is observed, recorded by a `PostToolUse` hook on the skill call. It buys
  enforcement for a hook that models which tool call counts as a tune, and a block clearing only on
  success can wedge a session at the context limit.

## Steps

1. `compact-defer.sh`, registered under `PreCompact`, with the marker in `.local/` — files:
   `.claude/hooks/compact-defer.sh`, `.claude/settings.json`, `scripts/gates/06-hooks.sh`,
   `CHANGELOG.md`, `CLAUDE.md` — proves it: three cases driving the hook with `manual` and `auto`
   payloads, plus a marker aged past a day that the next deferral removes (A1, A2, A3, A7)
2. `tune-due.sh`, registered under `UserPromptSubmit` — files: `.claude/hooks/tune-due.sh`,
   `.claude/settings.json`, `scripts/gates/06-hooks.sh` — proves it: a case asserting the
   instruction on the first prompt and silence on the second (A4)
3. The event map each hook is registered under — files: `scripts/gates/06-hooks.sh` — proves it:
   moving either basename to another event key fails the gate, and the real file passes (A5)
4. The cycle end to end — files: `scripts/gates/06-hooks.sh` — proves it: defer, announce, compact
   against a scratch clone, asserting the second compaction exits 0 and the tree stays clean (A6)

## Risks & open

- A tune costs one message. Between the deferred `/compact` and the real one the human has to send
  something; the block message says so. If that reads as friction, the fallback is the rejected
  `Stop` watermark, and removing the two hooks reverts cleanly.
- A human who re-runs `/compact` immediately compacts untuned, by design, because A2 is what stops
  the deferral looping. If that happens often, the successor is recording that a tune ran, not
  blocking twice.
- An automatic compaction never tunes. Open: whether a watermark should tune ahead of the limit.
  Assumption meanwhile: manual only, which is what was asked for. Reversible either way.
- The payload shape is read out of Claude Code 2.1.238. A later build that renames `trigger` makes
  every manual compaction look automatic, and the deferral becomes a silent no-op. Visible the
  first time `/compact` compacts with no message; no gate can see it, because `06-hooks.sh` drives
  the hook with a payload this repo writes rather than one the CLI produced.
- Both hooks build the marker path from `session_id` independently. If they ever disagree the
  deferral never announces, which the end-to-end case is there to catch.
- Raised and declined: fixing the positional `$?` in the existing pull request cases. It is
  unrequested scope, and those two reads are correct as written.
