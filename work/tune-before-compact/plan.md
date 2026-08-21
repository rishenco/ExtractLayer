# Keep the steering a compaction would bury

Status: Draft

## TL;DR
- Afterwards: every compaction leaves the human turns of the segment it buried in a small capped
  file, and the session is asked to tune from it once the work in flight closes.
- Decided: one hook on `SessionStart` matched to `compact`, which both kinds of compaction reach;
  the transcript survives on disk, so nothing is copied and no `PreCompact` hook exists.
- Decided: one log per boundary holding that segment only — keyed by session it would overwrite the
  compaction before it, and holding the whole session it would re-present encoded moments.
- Decided: the log is capped and keeps the turns nearest the boundary, because a human turn can
  carry pasted output of any size and the reader truncates from the wrong end.
- Decided: an unreadable transcript, a segment with no human turn, and a payload with no session
  each say a different thing, because the way this dies must not read like a quiet success.
- Shape:
  - `.claude/hooks/`: + `steering-due.sh` writes the steering log and names it
  - `.claude/skills/tune/`: + reading a named steering log as the conversation
  - `scripts/gates/06-hooks.sh`: + the hook over fixture transcripts, + the event it binds to

## Problem / Intent

`/tune` reads the conversation for the moments a human had to steer. Compaction replaces that
conversation with a summary, so the session that most needs tuning — long, and full of the
corrections length produces — is the one whose evidence goes first. A tune run afterwards reads a
summary that already dropped the moments, and the next session earns the same corrections again.

Afterwards: the steering outlives the compaction in a form the next context can hold. The
transcript is one cumulative file per session and a compaction only appends a boundary to it, so
what the model can no longer see is still on disk; the fix is to draw the human turns of the buried
segment out of it, not to stop the thing that buried them.

Objections: firing `/tune` on context pressure rather than on the presence of a correction invites
the failure its own skill names, encoding a decision as a rule nobody made. Decided: fire anyway,
and carry the skill's bar into the instruction so a null result is a first-class outcome.

Two earlier shapes were dropped. Deferring the first manual `/compact` never covered automatic
compaction, and pressing the key twice bypassed it. Copying the transcript aside handed a context
window the file that had just overflowed it. A merge-time trigger was argued down separately.

## Criteria

- [ ] C1 A `compact` payload writes `.local/steering-<session>-<n>.md` holding every human turn
      recorded since the previous compact boundary, or since the start of the transcript when there
      is none, with the opening of the assistant turn each answered and no tool output.
- [ ] C2 A transcript carrying two boundaries yields a log of the later segment and leaves the
      earlier log standing.
- [ ] C3 A segment larger than the cap yields a log holding the turns nearest the boundary, whose
      head names how many went.
- [ ] C4 The payload names the log on stdout, with stderr discarded, and asks for the tune once the
      work in flight reaches a close rather than on the turn the compaction resumed.
- [ ] C5 A transcript that cannot be read writes no log and says so.
- [ ] C6 A transcript that reads but holds no human turn in the segment says that, in words C5 does
      not use.
- [ ] C7 A payload carrying no `session_id` writes no log and says so, rather than naming one every
      such session shares.
- [ ] C8 A `SessionStart` payload with any other source writes nothing and says nothing of tuning.
- [ ] C9 A transcript whose final line is a half-written record still yields a log of every
      complete record before it.
- [ ] C10 `.claude/skills/tune/SKILL.md` carries the path the hook wrote at a scratch root, with
      the session and ordinal removed; moving the directory in either alone fails the gate.
- [ ] C11 A fixture `settings.json` carrying `steering-due.sh` under another event fails the gate,
      and the real file passes.
- [ ] C12 A log past thirty days is removed when the next is written in the same tree.
- [ ] C13 A log past thirty days at the repository root survives a gate run, so the sweep cannot
      reach a tree the cases did not create.

## Not doing

- Blocking, deferring or delaying any compaction.
- The pull request merge trigger.
- Copying the transcript, or reading it anywhere but through the log.
- Judging whether a tune improved anything. Nothing here measures that.
- Reading Claude Code's auto memory. No memory directory exists in this environment after a session
  carrying several corrections.

## Research

- Claude Code 2.1.238 gives every hook payload `session_id` and `transcript_path`, the latter a
  pure function of the session id. `SessionStart` accepts `hookSpecificOutput.additionalContext`
  and its `source` enum includes `compact`.
- The compaction routine runs for `trigger:"auto"` and for manual alike and fires the same
  `SessionStart` with source `compact`, guarded only against subagent contexts, so both kinds are
  covered by one hook. The same routine can be blocked by a `PreCompact` hook even when automatic.
- Compaction appends `{type:"system",subtype:"compact_boundary",compactMetadata,logicalParentUuid}`
  to that file. Nothing truncates or rotates it, so a session that compacts twice carries two
  boundaries and the turns before each remain readable.
- `PostCompact` exists but its hook output becomes a `userDisplayMessage`, and it is absent from
  the union of events accepting `additionalContext`. It cannot instruct Claude.
- Entries are one JSON object per line carrying `type` and `timestamp`, with `isMeta`,
  `isCompactSummary` and tool results distinguishing bookkeeping from conversation.
- The transcript at `~/.claude/projects/<project>/<session>.jsonl` measured 1.35 MB over 626
  entries before any compaction: 14 human turns totalling 43 KB against 105 tool results and 688 KB
  of assistant turns. Dropping tool output removes a fraction, not a bound: `.claude/hooks/
  stop-gate.sh:23-27` feeds a whole `scripts/check.sh` run back into the conversation on every stop
  while the tree is red, and that arrives inside a turn no filter of this kind drops.
- Claude Code refuses to read a file past its token ceiling and returns its head, so an uncapped
  log loses its newest steering first.
- Stderr from a hook that exits 0 reaches the debug log only.
- `.claude/skills/tune/SKILL.md:11` assumes the conversation is in context; `:16` counts a repeated
  instruction as a steering moment; `:24-30` route an edit into `.claude/`, `AGENTS.md` or
  `docs/lessons.md`, and `:43` runs `make check` and shows the diff.
- `scripts/gates/06-hooks.sh:59-68` requires every `.claude/hooks/*.sh` to be executable with its
  basename somewhere in `.claude/settings.json`; the event it binds to is not checked, and the path
  is read literally. `06-hooks.sh:3` cds to the repository root and `:16` passes
  `CLAUDE_PROJECT_DIR` to a hook as an environment variable.
- `.gitignore:1` ignores `.local`, which nothing writes to yet; `scripts/lib/files.sh:12` passes
  `--exclude-standard`, so a log there is invisible to every gate.

## Approach

One hook, on the one event both kinds of compaction reach and from which the model can be told
anything. `steering-due.sh` runs on `SessionStart` matched to `compact`. It walks the transcript
named by the payload a line at a time, counts the `compact_boundary` entries, and writes the human
turns lying after the second-to-last one into `.local/steering-<session>-<n>.md`, each with the
opening of the assistant turn it answered so a short correction keeps its referent. The ordinal in
the name is what stops one compaction erasing the record of the one before it.

Tool results and bookkeeping are dropped, and the log is capped: past the cap the turns nearest the
boundary are the ones kept, and the head of the log says how many went, because a human turn can
carry a pasted gate run of any size and the reader discards the tail. A line that does not parse is
skipped, so a record still being written costs one turn rather than the log. Writing sweeps logs
past thirty days from the tree it wrote into, matching the retention Claude Code applies to the
transcripts they are drawn from.

The hook names the log and asks for the tune at the close of the work in flight. Automatic
compaction fires when the context fills, which is mid-task by construction, and `/tune` edits
harness files and runs `make check` — landing that inside a build puts unrequested scope in its
diff. Nothing enforces the timing but the sentence; a hook cannot see whether work is in flight.

`/tune` gains one line: a named steering log is the conversation to read. Without it the skill
rereads a context compaction just emptied. A gate case runs the hook, takes the path it created,
and requires the skill to carry it.

Rejected:

- Deferring the compaction until a tune runs. Manual only, bypassed by pressing the key twice, and
  it starts the tune when the context is fullest.
- Copying the transcript aside. A compacted session is by definition one whose transcript did not
  fit the context window, and the copy carries every tool result into a file that persists.
- Extracting at `PreCompact`. The transcript survives, so the earlier event buys nothing and cannot
  see the boundary that marks what was lost.
- One log per session. The second compaction overwrites the first log, and the first segment is the
  one most likely never read.
- Leaving it to auto memory, or reading its notes. It writes nothing in this environment.

## Steps

1. `steering-due.sh`, bound to `SessionStart` matched on `compact` — files:
   `.claude/hooks/steering-due.sh`, `.claude/settings.json`, `scripts/gates/06-hooks.sh`,
   `CHANGELOG.md` — proves it: cases over fixture transcripts for one boundary, two boundaries, an
   oversized segment, an unreadable transcript, a segment with no human turn, a payload with no
   session, another source, a half-written final line, and an aged log, each at a scratch
   `CLAUDE_PROJECT_DIR`, plus an aged log at the real root that survives (C1-C9, C12, C13)
2. `/tune` reads a named steering log — files: `.claude/skills/tune/SKILL.md`, `CLAUDE.md`,
   `scripts/gates/06-hooks.sh` — proves it: a case running the hook and requiring the skill to
   carry the path it created (C10)
3. The event the hook binds to, read through an `EL_SETTINGS` seam — files:
   `scripts/gates/06-hooks.sh` — proves it: a fixture settings file carrying the basename under
   another event fails, and the real file passes (C11)

## Risks & open

- The timing in C4 is a sentence, not a gate. A tune that runs on the resumed turn anyway lands
  harness edits in whatever diff is open. Visible in that diff, and the fallback is to drop the
  instruction and leave the log for a human to name.
- The log depends on a vendor's internal file shape: one JSON object per line, `type` telling a
  human turn from an assistant turn, and `compact_boundary` marking the segment. A build that
  changes those yields an empty log, which C6 turns into a sentence, or a wrong one, which only a
  human reading the log will catch.
- Reversing the hook does not reverse what a tune wrote from a wrong log. `AGENTS.md` is capped, so
  a rule added there merges or deletes another, and that deletion outlives the hook. Every such
  edit reaches a pull request, which is where it can still be caught.
- The opening of the answered assistant turn is a fixed prefix, so a correction answering something
  long keeps its referent only in part.
- Nothing here shows that tuning from a steering log improves a later session. The mechanism
  preserves evidence a human-invoked skill already uses; the value of the skill is not claimed by
  this change.
- Raised and declined: pruning on `SessionEnd`, a third event for a bound the sweep gives; and
  fixing the positional `$?` in the existing pull request cases, as unrequested scope.
