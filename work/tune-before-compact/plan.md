# Tune before a compaction

Status: Draft

## TL;DR
- Afterwards: a manual compaction is deferred once, `/tune` runs against the conversation while it
  is still whole, and the next compaction proceeds.
- Decided: one deferral per cycle, recorded in an ADR, because the successor — blocking until a
  tune is observed — replaces this shape rather than extending it.
- Decided: an automatic compaction is never deferred and clears a pending one, because blocking a
  compaction raised by a context-limit error surfaces that error and fails the request.
- Decided: a payload whose trigger cannot be read defers nothing.
- Decided: the instruction rides `UserPromptSubmit` as `additionalContext`, because `PreCompact`
  output never reaches Claude and stderr from a hook that exits 0 reaches nobody.
- Shape:
  - `.claude/hooks/`: + `compact-defer.sh` defers, + `tune-due.sh` says once that a tune is owed
  - `scripts/lib/`: + the marker state both hooks read and write
  - `scripts/gates/06-hooks.sh`: + the cycle on fixture payloads, + the event each hook binds to
  - `docs/decisions/`: + why the deferral fires once

## Problem / Intent

`/tune` reads the conversation for the moments a human had to steer. Compaction replaces that
conversation with a summary, so the session that most needs tuning — long, and full of the
corrections length produces — is the one whose evidence goes first. A tune run afterwards reads a
summary that already dropped the moments, and the next session earns the same corrections again.

Afterwards: a manual `/compact` no longer discards an untuned conversation silently. One is
deferred, the tune runs against the whole transcript, and the next compacts. A deferral is owed
again once one is spent, so a session that compacts repeatedly tunes before each.

Objections: firing `/tune` on context pressure rather than on the presence of a correction invites
the failure its own skill names, encoding a decision as a rule nobody made. Decided: fire anyway,
and carry the skill's bar into the instruction so a null result is a first-class outcome. A
merge-time trigger was argued down and dropped: a merge usually lands after the session that
earned it, when the conversation is already gone.

## Criteria

- [ ] A1 A `manual` payload with no marker exits 2 and names `/tune`.
- [ ] A2 A `manual` payload with a marker exits 0 and removes it, so one compaction is deferred at
      most once.
- [ ] A3 An `auto` payload exits 0 and removes a marker it finds; a payload whose trigger is
      missing or unreadable exits 0 and writes none.
- [ ] A4 `tune-due.sh` names `/tune` on stdout, with stderr discarded, while the marker is pending,
      and prints nothing on the next prompt.
- [ ] A5 A fixture `settings.json` binding either hook to another event fails the gate, and the
      real file passes.
- [ ] A6 After defer, announce and compact, no `compact-deferred-*` marker is left.
- [ ] A7 Writing a deferral removes any marker older than a day.
- [ ] A8 Running the gate while a marker exists at the repository root leaves that marker
      untouched, so `make check` on every Stop cannot disarm a live deferral.

## Not doing

- The pull request merge trigger.
- Deferring an automatic compaction, or tuning before one.
- Verifying a tune actually ran; ADR 0013 carries why.
- Any change to what `/tune` reads or may edit.
- Preserving the transcript for a later tune, which is a different feature and is rejected below.
- The positional `$?` in the existing pull request cases at `06-hooks.sh:36`. The new cases capture
  status inside a helper; the old ones read correctly today.

## Research

- Claude Code 2.1.238 builds the `PreCompact` payload as `{hook_event_name, trigger,
  custom_instructions}`, `trigger` being `manual` or `auto`, and matches a `PreCompact` matcher
  against that same `trigger`. The hooks reference names the field `compaction_trigger`, a string
  this build does not contain.
- Every hook payload carries `session_id`, `transcript_path`, `cwd` and `permission_mode`.
- `UserPromptSubmit` accepts `hookSpecificOutput.additionalContext` and renders it as a
  `hook_additional_context` message. Stderr from a hook that exits 0 reaches the debug log only.
- The build carries the string `compaction blocked by PreCompact hook`, so exit 2 blocks. Where the
  compaction was raised by a context-limit error, blocking surfaces that error and fails the
  request.
- `UserPromptSubmit` fires on a submitted prompt; `UserPromptExpansion` covers skill and custom
  commands. A built-in command such as `/compact` is neither.
- `.claude/hooks/stop-gate.sh:10` runs `scripts/check.sh` on every Stop, so every gate case runs
  against the live repository several times a session.
- `scripts/gates/06-hooks.sh:59-68` requires every `.claude/hooks/*.sh` to be executable and its
  basename to appear anywhere in `.claude/settings.json`; the event it binds to is not checked, and
  the path is read literally with no seam for a fixture.
- `06-hooks.sh:16` already drives a hook against a scratch tree through `CLAUDE_PROJECT_DIR`;
  `06-hooks.sh:31` merges stderr into stdout and reads `$?` in the next statement.
- `06-hooks.sh:59` globs `.claude/hooks/*.sh` only, so a helper under `scripts/lib/` is not caught
  by it; `stop-gate.sh:8` already sources one.
- `.gitignore:1` ignores `.local`, and no file in the repo writes to it. `scripts/lib/files.sh:11`
  honours `.gitignore`, so a marker there is invisible to every gate.
- `docs/decisions/` numbers to 0012, and `0001`, `0003` and `0004` are harness decisions.

## Approach

The trigger is harness enforcement, so it lands in `.claude/hooks/` beside the four hooks already
there rather than in skill prose, which `AGENTS.md` puts last because prose cannot fail a build.
Both hooks root themselves at `CLAUDE_PROJECT_DIR` and read `session_id` from the payload, so the
marker is `.local/compact-deferred-<session>` under whichever tree the caller names — which is what
lets the gate drive them against a scratch tree while a live marker sits untouched in the real one.
`scripts/lib/tune-marker.sh` holds the path and the two states, because both hooks are real callers
and a format duplicated across them drifts silently.

`compact-defer.sh` runs on `PreCompact`. Only a payload that positively reads `manual` can defer;
anything else, `auto` included, exits 0. On `manual` with no marker it writes `pending`, exits 2 to
block the compaction, and tells the human to run `/tune` and then compact again. On `manual` with a
marker it removes it and exits 0. An `auto` payload removes a marker too: the compaction it
precedes destroys the conversation either way, and a marker left behind would silently spend the
next manual deferral. Writing a deferral drops markers over a day old, since a session that ends
deferred leaves its own and `docs/lessons.md` does not allow an unbounded store.

`tune-due.sh` runs on `UserPromptSubmit`. While the marker reads `pending` it returns the
instruction as `hookSpecificOutput.additionalContext` and rewrites the marker to `announced`, so it
speaks once and the following compaction still passes.

Rejected:

- A `SessionStart` hook matched on `compact`. The only mechanism that reaches Claude cleanly, and
  it reaches it after the summary has replaced the conversation — it tunes from the input this
  change exists to protect.
- A `Stop` hook that tunes once the transcript passes a size watermark. It needs no extra message
  and would cover automatic compaction, but the watermark guesses where the limit is and the tune
  lands on an arbitrary turn mid-build. A threshold meant to be corrected later is a stopgap.
- `PreCompact` running the tune itself in a nested non-interactive session: an unbounded agent
  inside a hook timeout, with no conversation to read.
- Blocking until a tune is observed. It is the stronger guarantee, and a block that clears only on
  success can wedge a session at the context limit. ADR 0013 records the choice.
- Copying `transcript_path` aside on `PreCompact` so a later tune reads it. It blocks nothing,
  needs no marker and covers `auto`, and it preserves evidence rather than triggering a tune: it
  buys a different feature, and one that changes what `/tune` reads against a transcript the
  reference says may lag the live conversation.
- Pruning on `SessionEnd`. A third hook for a bound the age sweep already gives.

## Steps

1. `scripts/lib/tune-marker.sh` — files: `scripts/lib/tune-marker.sh` — proves it: sourced by a
   case that writes and reads a marker under a scratch root (A8)
2. `compact-defer.sh`, bound to `PreCompact` — files: `.claude/hooks/compact-defer.sh`,
   `.claude/settings.json`, `scripts/gates/06-hooks.sh`, `CHANGELOG.md`, `CLAUDE.md` — proves it:
   cases for `manual` first, `manual` second, `auto` over a marker, an unreadable trigger, and a
   marker aged past a day, each at a scratch `CLAUDE_PROJECT_DIR` with a fixture session
   (A1, A2, A3, A7, A8)
3. `tune-due.sh`, bound to `UserPromptSubmit` — files: `.claude/hooks/tune-due.sh`,
   `.claude/settings.json`, `scripts/gates/06-hooks.sh` — proves it: a case capturing stdout with
   stderr discarded, asserting the instruction on the first prompt and silence on the second (A4)
4. The event each hook binds to, read through an `EL_SETTINGS` seam — files:
   `scripts/gates/06-hooks.sh` — proves it: a fixture settings file with either name under the
   wrong event fails, and the real file passes (A5)
5. Why the deferral fires once — files: `docs/decisions/0013-one-shot-compaction-deferral.md` —
   proves it: the cycle end to end, leaving no marker behind (A6)

## Risks & open

- `/compact` pressed twice runs no tune. It is the natural reaction to a blocked keypress, and
  `UserPromptSubmit` does not fire for a built-in command, so nothing announces between the two.
  The block message asks for `/tune` by name rather than for any message, which is the whole
  mitigation; the human can always spend the keystroke instead. No gate can tell the two paths
  apart.
- The payload shape is read out of Claude Code 2.1.238. A later build that renames `trigger` makes
  every compaction unreadable and the deferral a silent no-op. That direction is the safe one — the
  hook defers nothing rather than blocking an automatic compaction — and it is visible the first
  time `/compact` compacts with no message.
- An automatic compaction still tunes nothing, and clears a pending deferral on its way past. Open:
  whether a watermark should tune ahead of the limit. Assumption meanwhile: manual only, which is
  what was asked for. Reversible either way.
- Raised and declined: fixing the positional `$?` in the existing pull request cases, as
  unrequested scope, and pruning on `SessionEnd`.
