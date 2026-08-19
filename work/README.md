# work

One directory per change, named for its slug.

```
work/<slug>/plan.md      intent, criteria, research and steps   (/plan, human approves)
work/<slug>/claims.md    what the build asserts, with verdicts  (/build, the auditor rules)
```

`plan.md` carries `Status: Draft` until a human sets `Status: Approved`. `/build` refuses to run before that — this is where a background loop waits instead of guessing.

Directories stay after merge. They are the record of what was intended, which is what makes a later review able to tell a bug from a decision.
