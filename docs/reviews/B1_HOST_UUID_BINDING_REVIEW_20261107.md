# B1 host and GPU UUID authorization binding — independent review

AI-assisted (Codex), 7 November 2026. **ACCEPTED for the scoped code and synthetic-test change** at `fde124751be70d96aabbdbbce4ea565ee9735a49`, compared with `71153ec`. This is not approval of the pending note, combined checkout, host preflight, B1 launch, B2, or any experiment.

`r1/exam/runtime.py:346–348` now refuses a v2 B1 note when its `host` or `gpu_uuid` differs from the configuration or either configured field is absent/empty. The clause is nested under `phase == 'b1'` and `x5_rule/v2`; it does not change v1's path or the existing v2 B2 STOP. The surrounding committed-HEAD, clean-checkout, rule, table, worker and anchor bindings remain intact. A repository writer can still forge matching bytes; the stated author instruction and independent review remain the process boundary.

The new comparison establishes **note-to-configuration equality**, not a live hardware census. Prompt §0.3 separately requires the TASL-7 operator to verify the actual GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, the cooperative flock and inherited server descriptor, Python binding, available disk, and reviewed handover. `host_check` and `gpu_sample` are distinct runtime checks; this review did not execute them on a host, and matching note/config alone does not satisfy that condition.

Independent command, using an initially absent isolated pytest base to avoid default shared-root retention:

```text
AR_HARNESS_ROOT=/private/tmp/paper-b-m2-harness-a3fedbb PYTHONDONTWRITEBYTECODE=1 /Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=/private/tmp/paper-b-host-binding-pytest-20261107-r1 r1/tests/test_exam_b1_committed_authority.py r1/tests/test_exam_x5_rule_v2.py
```

Result: **107 passed, 2 skipped** in 3.83 s; the two harness-dependent request checks were skipped and are not asserted. The focused committed-checkout tests cover accepted matching fields, mismatch in each field, changed/missing note authority, and the anchor-reference binding; the legacy tests retain their separate version behavior. No real host, model, GPU, or experiment was used. The uncommitted configuration and draft in the implementer's checkout are outside this review and require their own exact-byte review.
