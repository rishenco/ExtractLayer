# ExtractLayer

An open-source project that addresses one problem: LLM-based structured data extraction. Product intent lives in `docs/vision.md`; the implementation description in `docs/architecture.md`.

## Working here

Development runs through agents, gated by an executable definition of done.

```
/spec  <idea>    intent and acceptance criteria       work/<slug>/spec.md
/plan  <slug>    research and file-level steps        work/<slug>/plan.md   → you approve
/build <slug>    execute, verify, adversarial review  a green branch        → you approve the PR
/compound        turn findings into gates             tests, gates, hooks
```

`make check` is the definition of done. It runs every gate in `scripts/gates/` plus each workspace's own checks. CI runs the same command — there is no second, weaker standard, and a workspace whose tooling is missing fails rather than skipping, in CI as locally.

A branch that changes source needs a `plan.md` marked `Status: Approved`, or a `Skips-plan-gate: <reason>` trailer on the commit that touches the file. Both markers live in the repo, so an agent can write either one — they make intent traceable. Requiring a human review on the pull request is what makes it binding.

```
make check       run every gate
make gates       list gates and what each enforces
```

`docs/working.md` is how to run this efficiently in practice.

## Layout

```
AGENTS.md         operating rules, capped and enforced
CLAUDE.md         thin Claude-specific layer over AGENTS.md
docs/             vision, architecture, decisions, lessons
work/<slug>/      spec, plan and review for one change
scripts/gates/    the executable definition of done
.claude/          skills, subagents, hooks
```

## Adding a workspace

A workspace is any directory with a `package.json`, `go.mod`, or `pyproject.toml`. Each one must declare its own checks and its own layer boundaries before `make check` will pass — `scripts/gates/60-workspaces.sh` and `50-architecture.sh` say exactly what is missing.
