# Keep the conversation a compaction would destroy

Status: Draft

## TL;DR
- Afterwards: every compaction, automatic or manual, leaves the conversation it replaced on disk,
  and the session that resumes is told to tune from it. Nothing is blocked or deferred.
- Decided: `SessionStart` matched on `compact` carries the instruction, because `PostCompact`
  output is shown to the human and never reaches Claude.
- Decided: `/tune` learns to read a named transcript. Without that the snapshot has no reader, and
  a tune after a compaction reads the summary this exists to get past.
- Decided: one snapshot per session, replaced at each compaction and swept by age; a payload with
  no readable transcript writes nothing, so a hook that cannot find its input is silent, not wrong.
- Shape:
  - `.claude/hooks/`: + `transcript-keep.sh` copies the transcript aside, + `tune-due.sh` names it
    to the resumed session
  - `.claude/skills/tune/`: + reading a named transcript as the conversation
  - `scripts/gates/06-hooks.sh`: + both hooks on fixture payloads, + the event each binds to

## Problem / Intent

`/tune` reads the conversation for the moments a human had to steer. Compaction replaces that
conversation with a summary, so the session that most needs tuning — long, and full of the
corrections length produces — is the one whose evidence goes first. A tune run afterwards reads a
summary that already dropped the moments, and the next session earns the same corrections again.

Afterwards: the evidence outlives the compaction. `PreCompact` carries `transcript_path` while the
conversation is still whole, so the fix is to keep it rather than to stop the thing that destroys
it. The tune then runs on a fresh context with the full record in a file.

Objections: firing `/tune` on context pressure rather than on the presence of a correction invites
the failure its own skill names, encoding a decision as a rule nobody made. Decided: fire anyway,
and carry the skill's bar into the instruction so a null result is a first-class outcome.

An earlier shape deferred the first manual `/compact` and asked for a tune before allowing the
next. It was dropped on review: automatic compaction — what a long session actually hits — was
never covered, `/compact` pressed twice bypassed it in one keystroke, and it ran the tune when the
context was fullest. A merge-time trigger was argued down separately: a merge usually lands after
the session that earned it, when the conversation is already gone.

## Criteria

- [ ] B1 A `PreCompact` payload exits 0 for both `manual` and `auto`, so no compaction is ever
      blocked.
- [ ] B2 A `PreCompact` payload copies the file named by `transcript_path` to the session's
      snapshot, and the copy matches the original byte for byte.
- [ ] B3 A `PreCompact` payload whose `transcript_path` is absent, empty or unreadable exits 0 and
      writes no snapshot.
- [ ] B4 `tune-due.sh` names both the snapshot path and `/tune` on stdout, with stderr discarded,
      when a snapshot exists for the session.
- [ ] B5 `tune-due.sh` prints nothing when no snapshot exists for the session.
- [ ] B6 A snapshot older than the sweep age is removed when the next one is written.
- [ ] B7 A fixture `settings.json` binding either hook to another event fails the gate, and the
      real file passes.
- [ ] B8 Running the gate while a snapshot exists at the repository root leaves it untouched, so
      `make check` on every Stop cannot destroy a live one.

## Not doing

- Blocking, deferring or delaying any compaction.
- The pull request merge trigger.
- Reading the snapshot anywhere but `/tune`.
- Judging whether a tune improved anything. Nothing here measures that, and saying otherwise would
  be a claim no gate can settle.
- Disabling or duplicating Claude Code's own auto memory, which records corrections continuously
  and is on by default in this build.

## Research

- Claude Code 2.1.238 sends `PreCompact` `{hook_event_name, trigger, custom_instructions}` with
  `trigger` one of `manual` or `auto`, and every payload carries `session_id` and
  `transcript_path`. The hooks reference names the trigger field `compaction_trigger`, a string
  this build does not contain.
- `PostCompact` exists, carries `{trigger, compact_summary}`, and its hook output is folded into a
  `userDisplayMessage`. It is absent from the union of events accepting
  `hookSpecificOutput.additionalContext`, so it cannot instruct Claude.
- `SessionStart` accepts `additionalContext` and its `source` enum includes `compact`;
  `.claude/hooks/session-start.sh` already proves its stdout reaches the model.
- Stderr from a hook that exits 0 reaches the debug log only.
- `autoMemoryEnabled` defaults to true when unset, and `.claude/settings.json` does not set it.
  Auto memory records `feedback`, described in the build as guidance the user has given on how to
  work, corrections included.
- `.claude/hooks/stop-gate.sh:10` runs `scripts/check.sh` on every Stop, so every gate case runs
  against the live repository several times a session.
- `scripts/gates/06-hooks.sh:59-68` requires every `.claude/hooks/*.sh` to be executable with its
  basename somewhere in `.claude/settings.json`; the event it binds to is not checked, and the path
  is read literally with no seam for a fixture.
- `06-hooks.sh:16` already drives a hook against a scratch tree through `CLAUDE_PROJECT_DIR`;
  `06-hooks.sh:31` merges stderr into stdout and reads `$?` in the next statement.
- `.gitignore:1` ignores `.local`, and no file in the repo writes to it. `scripts/lib/files.sh:11`
  honours `.gitignore`, so a snapshot there is invisible to every gate.

## Approach

`PreCompact` is the last moment the whole conversation exists, and it hands the hook a path to it.
`transcript-keep.sh` copies that file to `.local/tune-transcript-<session>.jsonl` and exits 0,
whatever the trigger — so an automatic compaction is covered on the same path as a manual one, and
no compaction is ever delayed. Writing a snapshot sweeps ones past the age bound first, since a
transcript is large and a session that never resumes leaves its own behind.

`tune-due.sh` runs on `SessionStart` matched to `compact`. It names the snapshot and asks for a
tune against it, carrying the skill's own bar so that finding nothing is a real answer. The
instruction reaches Claude through `additionalContext`, which `SessionStart` accepts and
`PostCompact` does not.

`/tune` gains one line: a named transcript is the conversation to read. That is the whole reason
the snapshot exists — without it the skill rereads a context that compaction just emptied. Both
hooks root at `CLAUDE_PROJECT_DIR` and key on `session_id`, which is what lets `06-hooks.sh` drive
them against a scratch tree while a live snapshot sits untouched in the real one.

Rejected:

- Deferring the compaction until a tune runs. It covers manual compaction only, `/compact` pressed
  twice bypasses it with no announcement in between, and it starts the tune when the context is
  fullest. The shape this replaces.
- `PostCompact` for the instruction. Its output is shown to the human, not the model.
- A `Stop` hook that tunes once the transcript passes a size watermark. The watermark guesses where
  the limit is and the tune lands on an arbitrary turn mid-build.
- Leaving it to auto memory. It records corrections into memory notes; it does not edit the
  checked-in skills, agents and rules that made the steering necessary, and it does not route what
  a program could catch to `/compound`. It reduces the loss this addresses; it does not close it.
- Keeping every snapshot a session produces. The transcript at each compaction already carries what
  came before it, so the last one is the one worth reading, and the others are megabytes.

## Steps

1. `transcript-keep.sh`, bound to `PreCompact` — files: `.claude/hooks/transcript-keep.sh`,
   `.claude/settings.json`, `scripts/gates/06-hooks.sh`, `CHANGELOG.md` — proves it: cases for
   `manual`, `auto`, an absent transcript and an aged snapshot, each at a scratch
   `CLAUDE_PROJECT_DIR` with a fixture session (B1, B2, B3, B6, B8)
2. `tune-due.sh`, bound to `SessionStart` matched on `compact` — files:
   `.claude/hooks/tune-due.sh`, `.claude/settings.json`, `scripts/gates/06-hooks.sh` — proves it: a
   case capturing stdout with stderr discarded, with and without a snapshot present (B4, B5)
3. `/tune` reads a named transcript — files: `.claude/skills/tune/SKILL.md`, `CLAUDE.md` — proves
   it: `make check`, which holds the skill to the same prose gates as every other committed file
4. The event each hook binds to, read through an `EL_SETTINGS` seam — files:
   `scripts/gates/06-hooks.sh` — proves it: a fixture settings file with either name under the
   wrong event fails, and the real file passes (B7)

## Risks & open

- Whether a transcript stays cumulative across compactions is not settled here. If a later one is
  truncated rather than appended to, the last snapshot is not a superset and an early correction is
  lost. Visible by reading two snapshots from one session; the fallback is keeping each compaction's
  snapshot under a count bound instead of one per session.
- Whether `session_id` survives a compaction into the resumed session is assumed, not proven. If it
  changes, `tune-due.sh` finds no snapshot and stays silent — the safe direction, and visible the
  first time a compaction produces no instruction.
- The payload shape is read out of Claude Code 2.1.238. A later build that renames
  `transcript_path` makes the hook write nothing, which B3 already defines as silence rather than
  error.
- Snapshots are session transcripts sitting in the working tree under `.local`. They are ignored by
  git and by every gate, and they hold whatever the conversation held.
- Nothing here shows that tuning from a transcript improves a later session. The mechanism
  preserves evidence a human-invoked skill already uses; the value of the skill itself is not
  measured by this change and is not claimed by it.
- Raised and declined: pruning on `SessionEnd`, a third hook for a bound the age sweep gives; and
  fixing the positional `$?` in the existing pull request cases, as unrequested scope.
