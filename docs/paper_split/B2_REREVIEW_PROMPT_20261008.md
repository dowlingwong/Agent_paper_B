# Paper B B2 re-review prompt — 8 October 2026

Status: prepared, **not dispatched**; no independent review has occurred.
Use a fresh session with no takeover conversation context. This is an
AI-assisted review and must never be described as human or external.

Adapted from execution runbook Appendix A only to apply the author's narrower
scope rule: the source repository and Paper A are off limits. Historical
source-commit claims remain reported provenance. Runbook §2.6 permits either
an author-started fresh session or a reviewer spawned without conversation
context. The review report is advisory to the author's B2-N and B2-BAVAR gates.

## 📋 Copyable prompt

```text
You are an independent reviewer (AI-assisted review; never call it human
review) of Paper B's controller and evaluation core in the B-only repository
(read only; work in a fresh GitHub clone under a scratch directory). The 27 September
review (docs/paper_split/INDEPENDENT_REVIEW_20260927.md) found B "design-ready:
no": C1 (proposed and repeated-myopic controllers identical on the evaluated
path), C2 (constant-reserve ablation identical to myopic), M1 (the max-bias
correction used an in-sample second-stage decision), M2 (its test could not
detect that), N2 (path allowance fed contrast p-values instead of checkpoint
allowances), N3 (population tax applied 2p, not 2·m·p, and with an empty grid),
E2 (a zero-variance contrast read as equivalence), plus C3 and L1. Fixes were
reported as committed on 28 September in the source
(d6b3bd3e…b9b56265); the code was copied into B at S = 4154f153.
Do not access the source repository or Paper A. Use the copied review and
fix records in B. For old-code checks, recreate the described pre-fix
behavior only in scratch, marking this as a reconstruction rather than
verification against a historical source checkout. If exact historical
bytes are necessary, report the evidence gap and request an author-supplied
B-only fixture through GitHub; do not cross the scope boundary. The review's reproduction scripts (identity.py, maxbias.py,
maxbias2.py, eval_semantics.py, the harness run) were never committed: re-create
each from the review's description in your scratch directory, run it against
the current code, and establish, with numbers:
the evaluated controllers can differ (agreement < 1 on a world with V̂_wait
spread); the corrected continuation target removes the max bias (nested
out-of-fold vs naive, paired CI); the max-bias test fails on the old code and
passes on the new; checkpoint-wise p1, p2 feed the path allowance; the reported
population bound uses 2·m·p_path with m = 3 consistently and no tax when p_path
is 0; an equivalence reading requires distinct policies and a non-degenerate
interval; plus C2, C3, L1. Report BLOCKER/MAJOR/MINOR/NIT with file:line,
evidence and a concrete fix, a verdict "design-ready: yes/no", and what you
checked and found correct. Write docs/paper_split/B2_REREVIEW_<date>.md
(untracked) and return it.

Clone only https://github.com/dowlingwong/Agent_paper_B.git; record the exact
reviewed commit. Use the pinned Python and requirements.lock. CPU only; no
GPU, model, paid API, task-realism rerun, authorize command or authorization
record mutation. Do not change scientific definitions, fixtures or source
files. Keep probes and temporary mutations in scratch and preserve the
original reviewed files. Return the report and reproduction scripts with
commands and observed numbers; the takeover agent will commit approved
B-only artifacts later, so do not push from the reviewer session.

Separate the controller/evaluation-core verdict from overall B readiness:
B1, author novelty verdict and author BAVAR reading remain separate gates.
List any reconstruction limit and any claim not actually checked. Cite every
finding by current file and line, quote the relevant code or record before
judging it, and distinguish evidence from interpretation.
```
