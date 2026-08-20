# 0004. Claims are audited separately from code review

Date: 2026-08-14 Status: Accepted

## Context

"Review" means code review, and code review asks whether the code is good. The failure that actually costs most with agents is different: the confident unverified assertion. "Tests pass." "I verified this." "This handles that case." Each is cheap to write, expensive to disbelieve, and indistinguishable from the truth in a transcript.

A code reviewer will not catch it. It reads the diff, and the diff does not record what the author said about it. Folding claim-checking into the reviewer dilutes both: the audit becomes one item on a quality checklist and gets answered with an opinion.

Verification is asymmetric. Reproducing a claim is far cheaper than making one, and an agent with a fresh context has no investment in the claim being true.

## Decision

Claims are a separate artifact with a separate auditor.

`/build` writes `work/<slug>/claims.md`: one block per claim, each with the evidence and the exact command that settles it. A claim is a sentence that can be false. Anything that cannot be settled by a command is not a claim and does not belong in the ledger.

The `claim-auditor` subagent reproduces every claim from scratch and writes a verdict of `SUPPORTED`, `UNSUPPORTED` or `FALSE`. Its rules of evidence are explicit: the transcript is not evidence, another agent's report of a command is not evidence, and a citation counts only if the cited line says what was claimed. Where a claim rests on a test, it breaks the behaviour and confirms the test fails — a test that passes both ways is how a true sentence hides a false one.

`scripts/gates/75-claims.sh` fails while any verdict is `UNSUPPORTED`, `FALSE` or missing, and when a ledger contains no claims at all. A ledger is claim blocks and verdicts and nothing else: a line outside one fails, so no preamble announces an outcome no verdict states, and evidence pointing at the ledger rather than at the tree fails with it.

The `adversarial-reviewer` keeps code quality, layering and shape, and is told the audit is not its job.

## Consequences

Assertions become enumerable, which is what makes them attackable. An agent that would have buried "tests pass" in prose has to state it as a claim with a command attached.

The ledger is forgeable like every in-repo marker: an agent can write `SUPPORTED` itself. What the gate removes is the ability to be vague — a skipped audit is now a visible absence rather than an invisible one.

Two subagents run per change instead of one. That is the cost, and it is small against a false claim reaching a pull request and being believed.
