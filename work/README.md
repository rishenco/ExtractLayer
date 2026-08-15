# work

One directory per change, named for its slug.

```
work/<slug>/spec.md    intent and acceptance criteria   (/spec)
work/<slug>/plan.md    research and steps               (/plan, human approves)
```

`plan.md` carries `Status: Draft` until a human sets `Status: Approved`. `/build` refuses to
run before that — this is where a background loop waits instead of guessing.

Directories stay after merge. They are the record of what was intended, which is what makes a
later review able to tell a bug from a decision.
