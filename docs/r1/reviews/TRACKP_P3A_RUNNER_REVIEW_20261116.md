# Independent review — Track P P.3a probes-only runner (`7ae4d2ea`, round 1)

Independent reviewer (fresh subagent, read-only; CPU-only checks; transcribed by the operator because the
reviewer did not write a file). Reviewed bytes: branch `trackp-p3a-code-20261116`, runner commit
`7ae4d2ea` (parent `3833d93e`; `git diff 3833d93e..7ae4d2ea` = `r1/scripts/trackp_p3a_guarded.py` +787/−15
and new `r1/tests/test_trackp_p3a_probes_only.py` +528); docs child `8a3d3eaf` (+259 docs only). Not pushed;
author/committer Dowling Wong. Authority: accepted Unit A plan rev 2 + `TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md`,
M13 record, OOM diagnosis, authorizations.

## Verdict: NOT ACCEPTED — no BLOCKING, 2 MAJOR, 8 MINOR

- **MAJOR-1:** current boot id recorded and in-session stability checked, but never compared to the
  reviewed attempt-1 boot id `2c9bb104-cc3c-4c60-be67-c1c8f0287fe4`; an unplanned reboot between the
  16 Nov preflight and the run would pass (27 Oct authorization makes a reboot a STOP).
- **MAJOR-2:** preflight requires branch `trackp-20261026` and `b9ad6f8f` ancestor only, so any descendant
  passes; the delivery record points at `3833d93e` (which lacks the runner) — reviewed identity not pinned
  and the documented delivery would fail closed. Fix: exact reviewed commit pin, accepted delivery shape,
  actual HEAD + runner/child sha256 recorded, old-path `git ls-files` check.
- **MINOR:** M1 golden-token test (M13 deliverable); M2 sidecar `derived_template_id` always the Qwen id;
  M3 preflight internals untested; M4 re-verify template/provenance at `unit_start`; M5 marker kill -9 doc;
  M6 atomic sidecar write; M7 root/attempt-1 absolute/UTC/absent validation; M8 record wording and
  extra-file/symlink statement.

**Correct in this commit:** two-command sequence (DRYRUN kev-0.8b n=8 → EVIDENCE qwen3.5-4b-base n=100,
both `--a3-short --budget`, attempt-1 `final/saved`), new-root/attempt-1-reuse refusal, marker begin/end on
STOP, 45-h budget seed (130745.3789889291 s) and projection, attempt-1 provenance hashing, M13 template
block/ids, fail-closed preflight before root/marker/GPU; tests reproduced (25 passed, A3-short 8 passed,
guarded 5 passed/4 pre-existing macOS prctl failures, CLI 9 skipped).
