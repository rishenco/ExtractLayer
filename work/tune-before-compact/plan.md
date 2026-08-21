# Keep the steering a compaction would bury

Status: Draft

## TL;DR
- Afterwards: every compaction, automatic or manual, leaves the human turns that preceded it in a
  small file, and the session that resumes is told to tune from it. Nothing is blocked or deferred.
- Decided: one hook on `SessionStart` matched to `compact`. The transcript survives compaction on
  disk, so there is nothing to copy and no `PreCompact` hook; `PostCompact` cannot instruct Claude.
- Decided: the log holds human turns and the opening of what each answered, never tool output. The
  transcript is the serialization of a conversation that just failed to fit in the context window.
- Decided: a compaction that produces no log says so, because a feature that never fires and one
  that finds nothing must not look alike.
- Shape:
  - `.claude/hooks/`: + `steering-due.sh` writes the steering log and names it to the resumed
    session
  - `.claude/skills/tune/`: + reading a named steering log as the conversation
  - `scripts/gates/06-hooks.sh`: + the hook on fixture transcripts, + the event it binds to

## Problem / Intent

`/tune` reads the conversation for the moments a human had to steer. Compaction replaces that
conversation with a summary, so the session that most needs tuning — long, and full of the
corrections length produces — is the one whose evidence goes first. A tune run afterwards reads a
summary that already dropped the moments, and the next session earns the same corrections again.

Afterwards: the steering outlives the compaction in a form the next context can actually hold. The
transcript is one cumulative file per session and a compaction only appends a boundary to it, so
what the model can no longer see is still on disk — the fix is to draw the human turns out of it,
not to stop the thing that buried them.

Objections: firing `/tune` on context pressure rather than on the presence of a correction invites
the failure its own skill names, encoding a decision as a rule nobody made. Decided: fire anyway,
and carry the skill's bar into the instruction so a null result is a first-class outcome.

Two earlier shapes were dropped on review. Deferring the first manual `/compact` never covered
automatic compaction, which is what a long session hits, and `/compact` pressed twice bypassed it
in one keystroke. Copying the whole transcript aside handed a context window the file that had just
overflowed it. A merge-time trigger was argued down separately: a merge usually lands after the
session that earned it.

## Criteria

- [ ] C1 A `compact` payload writes `.local/steering-<session>.md` holding every human turn
      recorded before the compact boundary, and no tool output.
- [ ] C2 The same payload names that file and `/tune` on stdout, with stderr discarded.
- [ ] C3 A payload whose transcript is absent or unreadable writes no log and says on stdout that
      the compaction left none, so absence is reported rather than silent.
- [ ] C4 A transcript whose final line is a half-written record still yields a log of every
      complete record before it.
- [ ] C5 A `SessionStart` payload with any other source writes nothing and says nothing of tuning.
- [ ] C6 `.claude/skills/tune/SKILL.md` names the same path the hook writes; changing either alone
      fails the gate.
- [ ] C7 A fixture `settings.json` binding the hook to another event fails the gate, and the real
      file passes.
- [ ] C8 A log older than thirty days is removed when the next is written.
- [ ] C9 Running the gate while a log exists at the repository root leaves it untouched, so
      `make check` cannot destroy a live one.

## Not doing

- Blocking, deferring or delaying any compaction.
- The pull request merge trigger.
- Copying the transcript, or reading it anywhere but through the log.
- Judging whether a tune improved anything. Nothing here measures that.
- Reading Claude Code's auto memory. No memory directory exists in this environment after a session
  carrying several corrections, so there are no notes to read.

## Research

- Claude Code 2.1.238 gives every hook payload `session_id` and `transcript_path`, the latter a
  pure function of the session id. `SessionStart` accepts `hookSpecificOutput.additionalContext`
  and its `source` enum includes `compact`; the post-compaction `SessionStart` carries the same
  session, so the path is unchanged.
- Compaction appends `{type:"system",subtype:"compact_boundary",compactMetadata,logicalParentUuid}`
  to that file. Nothing truncates or rotates it, so the turns before the boundary remain readable.
- `PostCompact` exists but its hook output becomes a `userDisplayMessage`, and it is absent from
  the union of events accepting `additionalContext`. It cannot instruct Claude.
- Entries are one JSON object per line carrying `type` and `timestamp`, with `isMeta`,
  `isCompactSummary` and tool results distinguishing bookkeeping from conversation. A measured
  transcript runs 1.35 MB over 626 entries before any compaction: 14 human turns totalling 43 KB
  against 105 tool results and 688 KB of assistant turns.
- Claude Code refuses to read a file past its token ceiling and directs the caller to offsets.
- Stderr from a hook that exits 0 reaches the debug log only.
- `autoMemoryEnabled` defaults true, but `autoMemoryDirectory` is unset and the resolver returns
  nothing without it; no memory directory exists on disk here.
- `.claude/hooks/stop-gate.sh:16` runs `scripts/check.sh`, reached whenever the tree is dirty or
  HEAD is ahead of base, so gate cases run against the live repository through a session.
- `scripts/gates/06-hooks.sh:59-68` requires every `.claude/hooks/*.sh` to be executable with its
  basename somewhere in `.claude/settings.json`; the event it binds to is not checked, and the path
  is read literally with no seam for a fixture. `06-hooks.sh:16` already drives a hook against a
  scratch tree through `CLAUDE_PROJECT_DIR`.
- `.gitignore:1` ignores `.local`; `scripts/lib/files.sh:12` passes `--exclude-standard`, so a log
  there is invisible to every gate.

## Approach

One hook, on the one event that both knows a compaction happened and can instruct the model.
`steering-due.sh` runs on `SessionStart` matched to `compact`. It reads the transcript named by the
payload, walks it line by line, and writes `.local/steering-<session>.md`: each human turn before
the compact boundary, in order, with the opening of the assistant turn it answered so a short
correction keeps its referent. Tool results and bookkeeping entries are dropped, which is what
takes the log from megabytes to kilobytes and keeps command output — and anything a command
printed — out of a file that outlives the session. A line that does not parse is skipped, so a
record still being written when the hook runs costs one turn rather than the log. Writing a log
sweeps ones past thirty days, the retention Claude Code applies to the transcripts they are drawn
from, so a log never outlives its source.

The hook then names the log and asks for a tune against it, carrying the skill's own bar so that
finding nothing is a real answer. When there is no readable transcript it writes nothing and says
that instead, because the failure this design is most likely to suffer — a later build renaming a
payload field — otherwise looks exactly like a session with nothing to tune.

`/tune` gains one line: a named steering log is the conversation to read. Without it the skill
rereads a context compaction just emptied, and the log has no reader. Both the hook and the skill
name the same path, and a gate case fails if only one of them changes.

Rejected:

- Deferring the compaction until a tune runs. Manual only, bypassed by pressing the key twice, and
  it starts the tune when the context is fullest.
- Copying the transcript aside for the skill to read. A compacted session is by definition one
  whose transcript did not fit the context window; the copy is unreadable by its reader, and it
  carries every tool result verbatim into a file that persists.
- Extracting at `PreCompact`. The transcript survives the compaction, so the earlier event buys
  nothing and cannot see the boundary that marks what was lost.
- Leaving it to auto memory, or reading its notes. It writes nothing in this environment.
- `PostCompact` for the instruction. Its output is shown to the human, not the model.

## Steps

1. `steering-due.sh`, bound to `SessionStart` matched on `compact` — files:
   `.claude/hooks/steering-due.sh`, `.claude/settings.json`, `scripts/gates/06-hooks.sh`,
   `CHANGELOG.md` — proves it: cases over fixture transcripts for a compaction with human turns, a
   transcript with a half-written final line, an unreadable transcript, another `source`, and an
   aged log, each at a scratch `CLAUDE_PROJECT_DIR` (C1, C2, C3, C4, C5, C8, C9)
2. `/tune` reads a named steering log — files: `.claude/skills/tune/SKILL.md`, `CLAUDE.md`,
   `scripts/gates/06-hooks.sh` — proves it: a case asserting the hook and the skill name one path
   (C6)
3. The event the hook binds to, read through an `EL_SETTINGS` seam — files:
   `scripts/gates/06-hooks.sh` — proves it: a fixture settings file binding it elsewhere fails, and
   the real file passes (C7)

## Risks & open

- The log depends on the shape of a vendor's internal file: one JSON object per line, with `type`
  telling a human turn from an assistant turn and the `compact_boundary` entry marking what was
  lost. A later build that changes those makes the hook write an empty or wrong log, and the reader
  is a prompt, so a wrong log reads as a plausible answer rather than an error. C3 turns the empty
  case into a sentence; a wrong-shaped one only a human reading the log will catch. One hook and
  one skill line to reverse.
- The opening of the answered assistant turn is a fixed prefix, so a correction answering something
  long keeps its referent only in part. Visible in the log itself.
- Nothing here shows that tuning from a steering log improves a later session. The mechanism
  preserves evidence a human-invoked skill already uses; the value of the skill is not measured by
  this change and is not claimed by it.
- Raised and declined: pruning on `SessionEnd`, a third event for a bound the sweep gives; and
  fixing the positional `$?` in the existing pull request cases, as unrequested scope.
