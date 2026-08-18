# A skill that reconciles the written record with the repo

Status: Draft

## Problem / Intent

The committed prose drifts from the repo and nothing detects it. `docs/lessons.md` cites
`assign_split`, an embedding cache and an MCP `add_pairs` tool, none of which exist. Eight
process rules are each stated in three to seven files, so changing one means finding all of
them. Afterwards `/reconcile` finds dangling citations, contradictions and duplicated sources
of truth, fixes what is mechanical, and reports what needs a decision.

Objections: none.

## Criteria

- [ ] A1 `.claude/skills/reconcile/SKILL.md` exists, with a description stating when to run it.
- [ ] A2 The skill carries a scan command; run against the repo as it stands it names
      `assign_split`, `add_pairs` and `derived_values`, and nothing else.
- [ ] A3 The skill states the precedence ladder that picks the canonical home for a duplicated
      rule, and replaces the other copies with a pointer rather than deleting them.
- [ ] A4 The skill states what not to flag, and that it never edits a `work/<slug>/` directory.
- [ ] A5 The skill states the scan's blind spot: a citation with no identifier in it.
- [ ] A6 `/reconcile` is named in `CLAUDE.md` and `README.md`.
- [ ] A7 `make check` passes.

## Not doing

- Applying the fixes to the current drift. The skill lands here; running it is its own change,
  separately reviewable.
- Turning the scan into a gate in `scripts/gates/`. That follows the first finding it catches
  that a gate could have caught, which is what `/compound` prescribes.
- Any schedule or hook that runs it unprompted.

## Research

- `scripts/gates/45-doc-links.sh:23` already resolves `docs/`, `scripts/` and `work/` paths
  cited from markdown outside `work/`, so file paths are covered and symbols are not.
- A scan for backticked snake_case tokens absent from the repo reports 16 in
  `docs/architecture.md` and 5 in `docs/lessons.md`, because nothing is built yet and both
  files name unbuilt things. Subtracting the vocabulary of `docs/architecture.md` and
  `docs/vision.md` leaves 3 tokens on 2 lines, all of them dead: `docs/lessons.md:26` and `:48`.
- The embedding-cache citation at `docs/lessons.md:31` carries no identifier, so no scan
  reaches it.
- Rules stated in three or more files: claims audited apart (7 files), `Status: Approved` (6),
  `make check` as the definition of done (5), the compound ladder (4), narration (4), the
  changelog line (4).
- `docs/lessons.md:14` states the single-source rule for product docs; the process files do not
  follow it.
- `work/README.md:11` states that slug directories stay after merge as the record of intent,
  which is what makes them unsafe to rewrite.

## Approach

A skill in three checks, each running a command first and judging second: dangling citations,
contradictions, duplicated sources of truth. The scan narrows candidates mechanically; the
agent adjudicates each against a stated rule, so a wrong verdict is traceable to the rule
rather than to taste. Canonical homes are picked by a fixed ladder — an executable check, then
`docs/decisions/` or `docs/architecture.md` or `docs/vision.md`, then `AGENTS.md`, then a skill,
then `docs/lessons.md` — and losing copies become pointers. `work/` is never edited.

Rejected — a gate instead of a skill: contradiction and canonical-home choices need judgment,
and a gate that guesses them fails the build on opinion. Rejected — an agent with no scan: it
would re-read the whole repo each run and report a different set each time, which is what makes
drift checks get ignored. Rejected — folding this into `/compound`: compounding turns one
finding into one check, and this sweeps a whole class, so merging them buries both.

## Steps

1. Write the skill: the three checks with their commands, the precedence ladder, the not-to-flag
   list, the `work/` rule, the blind spot, the output format, and the handoff to `/compound` —
   files: `.claude/skills/reconcile/SKILL.md` — proves it:
   `grep -q 'work/' .claude/skills/reconcile/SKILL.md && grep -q 'Do not flag'
   .claude/skills/reconcile/SKILL.md` (A1, A3, A4, A5)
2. Verify the scan on the repo as it stands — files: none — proves it: the command from the
   skill prints exactly `assign_split`, `add_pairs`, `derived_values` (A2)
3. Name the skill where the others are named — files: `CLAUDE.md`, `README.md` — proves it:
   `grep -q reconcile CLAUDE.md README.md` (A6)
4. Run the whole check — proves it: `make check` (A7)

## Risks & open

- The scan over-reports once code exists, since a token can be absent from the repo and still
  correct in a design document. Visible as candidate count per run; the vocabulary subtraction
  is what holds it down, and `docs/architecture.md` is its source.
- Deduplication removes a clause that only the losing copy carried. The pointer rule makes it
  visible in the diff; the skill forbids a silent delete.
- Open: whether `/reconcile` may edit `AGENTS.md`, which is capped at 120 lines and where a
  merge can push it over. Assumption taken: it may, and the budget gate refuses the result if
  the merge overflows. Reversible by forbidding the file in the skill.
