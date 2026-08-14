# How to run development here

1. Spend your attention on the plan, not the diff. A wrong line in a plan becomes hundreds of
   wrong lines of code; a wrong line of code is one line. Read `work/<slug>/plan.md` carefully
   and skim the pull request.
2. Keep a change small enough that its spec fits on one screen. If the acceptance criteria do
   not fit, it is two changes.
3. Answer the questions `/spec` asks. Every unanswered one becomes an assumption you will find
   in the PR later, when it is expensive.
4. Reject a plan freely. It costs a minute there and an afternoon after `/build`.
5. Approve a plan by setting `Status: Approved` yourself. If an agent set it, the gate is
   decorative.
6. Run background work only on approved plans. An agent with an approved plan is autonomous;
   an agent without one is guessing, which is the failure mode this repo exists to prevent.
7. Do not argue with an agent about quality. Make the standard executable and let `make check`
   be the referee — an agent will concede to a failing command and negotiate with an opinion.
8. Run several approved plans in parallel in separate worktrees. The gate makes their output
   comparable without you reading every diff.
9. When a defect reaches you, run `/compound` before fixing it. Fixing costs one incident;
   closing the hole costs one change and ends the class.
10. When a gate annoys you, decide out loud: the code is wrong, or the gate is. Never weaken a
    gate quietly — that is how the standard erodes without anyone choosing it.
11. Let the floor recede. Every real linter you configure retires a hand-written gate; see
    `docs/decisions/0003-repo-gates-are-a-floor.md`.
12. Re-read `docs/vision.md` when a request feels wrong. Usually the vision is out of date
    rather than the request, and updating it is the higher-leverage fix.
