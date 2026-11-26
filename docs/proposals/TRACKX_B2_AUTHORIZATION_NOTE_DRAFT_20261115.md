# Track X B2 authorization note — DRAFT for the author (15 November 2026)

**Draft, AI-assisted (Claude, Mac-local agent). Not an authorization.** It carries every binding the B2 author gate
reads (`runtime.author_gate`, phase `b2`). To authorize B2, the author:
1. copies this file to `docs/r1/authorizations/trackx_b2_20261115.md`;
2. replaces this preamble with their own prose: name the B1 run `7912_20261113_d`, the reviewed B2 code base, the executable hand-off `proposals/B2_HANDOFF_EXEC_20261115.md` and the two PLAN rows;
3. sets `"approved": true`;
4. commits it on the run HEAD together with the two PLAN §10 rows.

No agent sets `approved: true`.

```json
{
  "author": "Dowling Wong",
  "phase": "b2",
  "approved": false,
  "rule_sha256": "53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad",
  "nodes": ["digits_mlp", "openml_credit_approval", "openml_ionosphere"],
  "stage_a_table_sha256": "00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c",
  "stage_a_amendment_table_sha256": "71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103",
  "stage_a_amendment_acceptance_sha256": "0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e",
  "anchor_duplicate_reference_sha256": "84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd",
  "b1_analysis_sha256": "07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc",
  "instances_per_node": 4,
  "llm_call_cap": 80,
  "host": "TASL-7",
  "gpu_uuid": "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1",
  "workers": 20
}
```

The values are the filled B2 configuration's (`r1/scripts/configs/exam_b2_v2.json` on `mac-b2-handoff-exec-20261115`).
`llm_call_cap`, `workers` and the anchor reference are B1's values, for the author to confirm. Changing any value
means changing it in both files.
