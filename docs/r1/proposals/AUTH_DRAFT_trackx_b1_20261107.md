# B1 authorization candidate — 7 November 2026

AI-assisted (Codex). This candidate is **not an authorization**: `approved` is false. The author's conditional rule/note approval and all prerequisites are recorded in PLAN §10 and `prompts/MAC_OVERNIGHT_PROMPT_20261107.md` §0. After the other independent prerequisites are ready, the author has allowed an `approved: true` candidate to be committed at the configured authorization path. Then obtain independent review of the exact committed HEAD, run the real committed author gate and host preflight, and complete handover; start B1 only when all launch conditions hold.

Q1 binds the exact O1 report bytes. Q2 uses the independently reviewed fixed-rule reference `reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json`: 99% predictive interval `[0.42386590667728663, 0.5800007633587785]`, no fallback. The author-approved rule SHA and both Stage A table SHAs are below. The actual tables, GPU/lease, 20-worker headroom, remaining test coverage, and TASL-7 handover still require verification.

```json
{
  "author": "Dowling Wong",
  "phase": "b1",
  "approved": false,
  "rule_sha256": "53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad",
  "nodes": ["digits_mlp", "openml_credit_approval", "openml_ionosphere"],
  "stage_a_table_sha256": "00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c",
  "stage_a_amendment_table_sha256": "71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103",
  "stage_a_amendment_acceptance_sha256": "0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e",
  "anchor_duplicate_reference_sha256": "84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd",
  "llm_call_cap": 80,
  "host": "TASL-7",
  "gpu_uuid": "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1",
  "workers": 20
}
```

The 7 November author instruction does not authorize B2, X.7 or sweep 2. Any runner, guardian, author-gate or anchor-gate STOP is preserved for the author; it is not retried or overridden.

## Runtime disclosure and outstanding loader evidence

The proposed B1 runtime includes the paper-side OpenML bootstrap guard at `f63471bf2d0286e11142bf25841cc0485b6bbade`, subject to final integrated review. It keeps harness `a3fedbb` pinned and uses sklearn private OpenML APIs (site capture reported sklearn 1.8.0); detected missing or corrupt caches cause STOP without retry or cache deletion. The added bootstrap and import can affect work near the existing timeout. Numerical equivalence has not been measured. This is a runtime disclosure, not a new author decision or a change to the draft JSON above.

The retained offline loader site capture reports expected loader output, but its SSH exit record and wrapper summary are missing. Its result remains STOP pending independent examination of contemporaneous command/session evidence; the operator must preserve the capture and site destination without automatically rerunning. The reviewer and operator must resolve that evidence gap before relying on the check; effort depends on the available records. This is separate from the other note, gate and launch conditions.
