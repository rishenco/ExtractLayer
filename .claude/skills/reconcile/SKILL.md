---
name: reconcile
description: Check the committed prose against the repo — dangling citations, contradictions, one rule stated in many files — and fix what is mechanical. Use when the written record has drifted from the code, or before planning from a document nobody has checked lately.
argument-hint: "[path to narrow to, optional]"
---

The repo is the fact; committed prose is a claim about it. Drift is silent — nothing fails when a document names something that does not exist.

Three checks. Each runs its command first and judges second, so a verdict traces to a stated rule rather than to taste. They share two file lists, which include what is written but not yet committed:

```bash
prose() { { git ls-files '*.md'; git ls-files --others --exclude-standard '*.md'; } | grep -v '^work/' | sort -u; }
code()  { { git ls-files;        git ls-files --others --exclude-standard;        } | grep -v '\.md$'  | sort -u; }
```

## Dangling citations

An identifier cited in prose that exists neither in the code nor in the design vocabulary.

```bash
known="$(
  { code | while IFS= read -r f; do grep -oE '[a-z][a-z0-9]*(_[a-z0-9]+)+' "$f"; done
    grep -hoE '[a-z][a-z0-9]*(_[a-z0-9]+)+' docs/architecture.md docs/vision.md
  } | sort -u
)"
prose | while IFS= read -r f; do
  grep -onE '`[a-z][a-z0-9]*(_[a-z0-9]+)+`' "$f" | tr -d '`' | while IFS=: read -r n t; do
    grep -qxF "$t" <<<"$known" || printf '%s:%s: %s\n' "$f" "$n" "$t"
  done
done
```

Each hit is dead or early. Dead: the thing was never built or no longer is, and the sentence around it describes something that does not exist — cut the sentence, or correct the name to what the code calls it. Early: the design names it and the code has not caught up — leave it, and say so.

The scan reads identifiers only. A citation carrying no identifier — a component named in words alone — is invisible to it and rots the same way. Read the sentences around each hit for the unbackticked neighbours the scan cannot reach.

## Contradictions

Prose that states a magnitude or a name about something executable, where the executable says otherwise.

```bash
prose | while IFS= read -r f; do
  grep -nE '`(scripts/|make )[^`]*`' "$f" | sed "s|^|$f:|"
done | awk '{ rest=$0; sub(/^[^:]*:[0-9]+:/,"",rest); gsub(/`[^`]*`/,"",rest)
              sub(/^[[:space:]]*[0-9]+\.[[:space:]]/,"",rest)
              if (rest ~ /[0-9][0-9]/) print }'
```

Open the file each line names and compare. The executable wins: prose is edited to match it, never the reverse. A number that no file defines is not a contradiction — it is an assertion nothing settles, so it moves to the file that could define it, or goes.

## Duplicated sources of truth

```bash
prose | while IFS= read -r f; do
  grep -oE '`[^`]+`' "$f" | tr -d '`' | sort -u | sed "s|^|$f\t|"
done | awk -F'\t' '{ c[$2]++ } END { for (t in c) if (c[t] >= 3) printf "%2d  %s\n", c[t], t }' | sort -rn
```

A span in three or more files is a candidate, not a finding. It is duplicated only where two files each state the rule; a file that names the rule and points to where it is stated is the end state.

The canonical home is the first of these that can hold the rule:

1. An executable check — a gate in `scripts/gates/`, a workspace linter, a hook. A rule that runs needs no prose.
2. `docs/decisions/`, `docs/architecture.md` or `docs/vision.md` — a decision, a boundary, or product intent.
3. `AGENTS.md` — a rule that governs every change.
4. The skill that does the work — a rule that applies only while doing it.
5. `docs/lessons.md` — what none of the above can hold.

Every losing copy becomes a pointer to the winner. Deleting one outright loses whatever it alone said, so when a copy carries a clause the winner does not, add the clause to the winner before the copy becomes a pointer.

## Do not flag

- A pointer to the canonical home. That is the fix, not the defect.
- A term the design names and the code has not built yet. `docs/architecture.md` and `docs/vision.md` are vocabulary, not claims about what exists.
- A rule restated inside one file for a reader who will not read its other sections.
- The change that taught a line in `docs/lessons.md`. That file's format requires it.
- Two files saying the same thing in different words. A wording difference carrying no difference in meaning is not drift.

## Never edit

Nothing under `work/`. A plan and its claims record what was intended when they were written, so correcting them destroys the only evidence of the intent. A slug directory that contradicts the repo is a finding to report and never one to fix.

## Report

Per finding: path and line, the check that found it, the verdict, and the rule the verdict came from. Two outcomes only — fixed mechanically, or needs a decision.

Apply the mechanical fixes: a dead citation cut, a number corrected to what the executable defines, a losing copy turned into a pointer. Anything that changes what a rule means goes to the human as a question with the option you would take.

Then run `/compound` on any finding a check could have caught, so the next drift of that shape fails the build instead of waiting for this skill to be run again.
