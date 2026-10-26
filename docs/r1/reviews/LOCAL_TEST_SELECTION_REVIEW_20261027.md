# Independent local test selection review — 27 October 2026

AI-assisted, static inspection only. **Verdict: reject the selection audit for revision; its matched-comparison framework is sound as a proposal, but the identified exclusion list misses two directly relevant harness tests.** This is not a safe-suite certification, execution authorization, or a review of scientific readiness. No test, collection, inference, training, model script, SSH, or network operation was performed for this review.

## Finding

The audit lists real `lr_synthetic` campaign attempts and proposes excluding them (`docs/r1/reports/LOCAL_TEST_SELECTION_AUDIT_20261027.md:18-19,24`), but omits these two harness selectors at pinned `897d83c8efa364ec2fdd37288241cc42e01d7274`:

- `tests/stage2/test_r1_l12.py::TestControllerLlmCharging::test_side_query_calls_exhaust_the_llm_cap`
- `tests/stage2/test_r1_l12.py::TestControllerLlmCharging::test_uncharged_decisions_leave_the_cap_alone`

Both call `_run` (`tests/stage2/test_r1_l12.py:48-54`), which copies `nodes/lr_synthetic` and invokes `run_real_campaign` with `LocalWorker` (`:33-45`). The node's training function performs gradient descent (`nodes/lr_synthetic/train.py:105-124`) and its entry point calls it (`:142-147`). These are node subprocess **attempts** under the same exclusion rationale; the source does not establish that either reached training in any historical run. Add both to the known exclusions and retain their precise scope: the third method in the class, `test_decision_rejects_negative_llm_calls` (`:56-58`), does not call `_run`, so excluding the whole class is unnecessary without another reason. This finding does not assert that the table claims exhaustive coverage: it explicitly disclaims that at audit line 30, and its allowlist rule mitigates the risk. It does show that the current concrete inventory misses material counterparts of an already identified path.

## Assessment and limits

The audit correctly distinguishes the confirmed eight in-process OpenML fits from other attempted subprocesses of unknown progress, the interrupted paper run from a complete result, and baseline-record fidelity from scope adherence (audit `:7-9`; incident `docs/r1/reports/LOCAL_TEST_SCOPE_INCIDENT_20261027.md:5-17`; `docs/r1/reviews/LOCAL_L0_REVIEW_20261027.md`, scope-incident re-check). PLAN `docs/r1/PLAN.md:507` states the CPU tiny-model exception, real-weight and approximate ten-minute limits. The audit's more conservative exclusion of other fitted models is a selection judgment, not a change to that boundary.

The comparison proposal requires an individually inspected complete-node-ID allowlist, both-revision transitive and fixture inspection, matched identities and outcome categories, and an empty fallback when inspection is incomplete (audit `:32-36`). It expressly says restricted matched results cannot establish original full-suite acceptance or historical scope compliance (`:37`). That is the correct limitation; a passing intersection must not be represented as the original acceptance criterion. No actual allowlist, selection safety, runtime bound, offline enforcement, or result has been verified here. Further indirect paths may exist, so adding the two omissions alone does not make the exclusion table exhaustive or authorize a run.

The audit identifies paper source at `94b7396a05265dde7c45a683481f4b437ddc783d` (`:3`); the shared worktree HEAD had advanced during this review. The harness checkout resolved to the stated pin and was clean when inspected. Any future selection must recheck the exact paper revisions and working-tree contents as the audit itself requires; this review does not attest to an unchanged paper tree or certify transitive behavior.
