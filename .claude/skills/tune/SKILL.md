---
name: tune
description: Read the conversation for the moments the human had to steer by hand, and edit the harness prompt that made the steering necessary. Use toward the end of a session that contained a correction, or name the correction as the argument.
argument-hint: "[correction to encode]"
---

A correction given in conversation fixes one session. The prompts that earned it are unchanged, so the next session earns it again. Steering that would repeat is a defect in the harness — a skill, an agent, or a rule that should have made it unnecessary.

## Collect

Reread the conversation from the top — a skill runs inside it, so all of it is in context. A steering moment is one where the human:

- overruled what was about to happen, or reverted what did;
- restated intent because the first reading missed it;
- answered a question that `docs/` or a skill already answers;
- gave an instruction for the second time.

A decision is not a moment: scope, taste, and priority calls belong to the human every time, and encoding one turns a choice into a rule nobody made. The test is whether the human would have to say it again in the next session — only a yes is a defect.

An argument names one correction to encode; scan for the rest anyway.

## Route

For each moment, the first that fits:

1. A test, gate, or hook could have caught it → run `/compound` and stop. Prompt text about something a program can see is the weaker fix, and this skill never writes it.
2. The skill that was running when the steering arrived → its file under `.claude/skills/`.
3. The subagent whose output caused it → its file under `.claude/agents/`.
4. A rule that governs every change → `CLAUDE.md`, or `AGENTS.md` knowing it is capped.
5. None of these → one line in `docs/lessons.md`, and nothing else.

## Edit

- Write the rule the correction implies, not a transcript of it: general enough to cover the class of mistake, and no wider.
- The line must read as if it had always been there, in the file's own voice. `scripts/gates/35-narration.sh` holds every committed file to exactly that.
- A correction that contradicts an existing line changes that line. An exception appended under a wrong rule leaves the wrong rule standing.
- The best tune deletes the line that caused the behaviour.
- One moment, one edit. A moment that wants a paragraph is a design change — take it to `/plan`.
- Never edit `scripts/gates/` or `.claude/hooks/` from here; enforcement changes go through `/compound`. And never weaken a rule: a correction that relaxes scrutiny is a decision, and decisions get an ADR.

## Report

Apply the edits, run `make check`, and show the diff. Per edit: the moment in one line, and the rule as now written. Per moment dropped: the decision it was. Per moment routed to `/compound`: what would now fail. The edits go through review like any other change — nothing here is exempt from the loop that ships code.
