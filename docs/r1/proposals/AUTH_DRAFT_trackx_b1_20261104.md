# DRAFT — Authorization: Track X Stage B1 under `x5_rule_v2` (4 November 2026)

**This is a draft prepared by the Mac-local agent (Claude; AI-assisted) at the author's request of 4 Nov 17:54 ("起草 B1 授权说明，绑定 `rule_sha256`、`nodes`、`stage_a_table_sha256`（两张表）、`llm_call_cap`，由我审定后提交"). It authorizes nothing.** The author reviews it, fills the open values, sets `"approved": true`, and commits the final note under `docs/r1/authorizations/` (the path the B1 config's `authorizations.b1` names). The machine-readable block below has the fields `r1.exam.runtime.author_gate` checks for phase `b1` (plus `host` and `workers`, recorded for the operator; the gate at `8eae4f84` does not check them); the gate refuses to run unless the committed bytes match and PLAN carries the R1-EXAM-RULE row with the same rule sha.

## Preconditions before the author commits the final note

1. M2 (`mac-x5v2-20261104`) accepted by its independent reviewer, and the reviewed commit is the paper pin. *(M2 is being fixed after review round 1; the rule file and its sha are not changed by those fixes.)*
2. PLAN §10 row **R1-EXAM-RULE-X5V2** committed by the author with the rule sha below.
3. R1-EXAM-STAGEA-ACCEPT (Stage A accepted; B1 candidates = `t7h8`'s 8 PASS + `t7j10`'s 7 PASS + 3 anchors) is in PLAN; the related row and draft review was accepted within its stated scope. M5 found code defects; its fix does not revalidate the historical measurements.
4. Host: **TASL-7** (R1-EXAM-HOST-B1B2-TASL7, 18:10): B1 and B2 on TASL-7, the whole exam on one host; P.3a pauses while B1 or B2 runs. M2 makes the exam worker follow the configured host (it was hard-pinned to TASL-2).
5. *(open)* The existing B1/B2 hard STOPs in `exam_runner.py`, `ExamRunner.start` and `campaign.collect` must be resolved through the owning task, with the reviewed harness pin and observer cache evidence implemented and independently reviewed. The current M2 head `75134796` cannot launch B1. Do not remove the guards without satisfying and reviewing their conditions. The final note and paper pin must be re-checked after that work; this draft authorizes no launch.

## Bound values

| Field | Value | Source |
|---|---|---|
| `rule_sha256` | `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20` (`r1/exam/rules/x5_rule_v2.yaml`) | M2 hand-off; recomputed by the M2 reviewer. Final only with R1-EXAM-RULE-X5V2. |
| `nodes` | `["digits_mlp", "openml_credit_approval", "openml_ionosphere"]` | RUNBOOK X.4: "`digits_mlp` if D28 passes, else `tabular_mlp`"; `digits_mlp` passed the repaired D28 on 27 Oct and is one of sweep 1's eight nodes (`authorizations/c3_sweep1_20261027.md`). The gate accepts only this set or the `tabular_mlp` variant. Author selected the proposed `digits_mlp` variant (PLAN R1-EXAM-B1-DRAFT-VALUES); this does not authorize the run. |
| `stage_a_table_sha256` | `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c` (`t7h8`) | R1-EXAM-STAGEA-COMPLETE report; `reports/OPS_O1_20261104.md` |
| `stage_a_amendment_table_sha256` | `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103` (`t7j10`) | `reports/OPS_O1_20261104.md` (Identity and custody) |
| `stage_a_amendment_acceptance_sha256` | *TODO — depends on M2's acceptance-record format.* Candidate: `reports/OPS_O1_20261104.md` blob sha256 `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e` (as merged from `ops-20261104` @ `f52db28e`). | M2 is checking which file its loader binds as the acceptance record. |
| `llm_call_cap` | **80** | Author selected the proposed value (PLAN R1-EXAM-B1-DRAFT-VALUES). |
| host / `gpu_uuid` | `TASL-7` / `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` | R1-EXAM-HOST-B1B2-TASL7; the TASL-7 GPU UUID already in `exam_b1_v2.json` (same card as Stage A `t7h8`/`t7j10`) |
| `workers` | **20** — see below | Author selected the proposed value (PLAN R1-EXAM-B1-DRAFT-VALUES). |

The author asked for "two tables" under `stage_a_table_sha256`. The gate and M2's config bind them as two fields: `stage_a_table_sha256` (`t7h8`) and `stage_a_amendment_table_sha256` (`t7j10`), plus the operator acceptance record. Both tables are listed above.

### `llm_call_cap` — earlier options (the author selected 80)

B1 runs each campaign with W = 20 worker runs, and after each executed proposal one charged A4 side query (RUNBOOK X.4; `r1/exam/observer.py`: one LLM call per observation). In `r1/exam/campaign.py` the cap is both the campaign's trial budget and `max_llm_calls`; the gate requires an integer ≥ 2 ("paired" cap).

| Option | Value | What it means |
|---|---|---|
| A | 80 | Room for up to 40 proposal/A4 pairs, i.e. twice W. Mirrors the E1b collector's trial budget of 2 × runs (`r1/headroom/e1b_collect.py`). W, not the cap, normally ends a campaign. *(Agent's recommendation; derivation only, not measured.)* |
| B | 40 | Exactly one pair per worker run. Any skipped, inert or duplicate proposal (no worker run) still costs calls, so campaigns with many non-executed proposals end before W. |
| C | other | Author's value. |

### `workers` on TASL-7 (24 logical CPUs) — selected value and limitations

TASL-7 has 24 logical CPUs (AMD Ryzen 9 7900X, 12 cores × 2 threads) and 62 GiB RAM (`reports/PORTAL_TRACKP_HOST_FACTS_TASL7_20261026.md`). **The author selected `workers = 20`** (R1-EXAM-B1-DRAFT-VALUES). At M2 `75134796`, `workers` controls the process pool for paired audit configurations after collection; roots and seeds are run sequentially, and the worker setup limits BLAS/OpenMP threads. It is not the number of parallel campaigns. The practical CPU and memory headroom for 20 audit processes is not measured here; M2's final reviewed handoff must confirm the behavior and disclose the unmeasured headroom before execution.

## Pins carried from the B1 config (`r1/scripts/configs/exam_b1_v2.json` on `mac-x5v2-20261104`)

- Paper: the M2 commit accepted by review (*TODO*); harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (R1-EXAM-B1-HARNESS-PIN); `cache_prompt: false` on every call.
- llama.cpp `version: 0.7.0-dev (build 1, commit 620d222)`, binary sha `b70f488248ba6c77…`; prompt set `70872a7702a36dc1…`; registry `r1/exam/registry.yaml`.
- Repair templates carried into B1 (R1-EXAM-A1-M1-REQUIREMENTS (1)): `olmo31_32b` `5d275f78…`, `devstral_small2_24b` `a0c0ed8a…`, `ministral3_14b` `2f545122…`.
- Instance seeds 9001–9004, audit seeds 9101–9104, W = 20, temperature 0.2, `manager_proposal/v1`, schema-sensitivity node `openml_credit_approval` (all as the gate and RUNBOOK X.4 require).

## Scope and STOPs (from RUNBOOK X.4, R1-MAIN-PROPOSER and the rows cited)

- Authorizes B1 only, on TASL-7 (R1-EXAM-HOST-B1B2-TASL7), for the 18 candidates of R1-EXAM-STAGEA-ACCEPT (`t7h8`'s 8 PASS, `t7j10`'s 7 PASS, 3 anchors). Always-thinking models skip B1 (R1-EXAM-ALWAYS-ON-SKIP; none of the 18 is always-on). `x5_rule_v2`'s finalist eligibility (D28 pass, measured in B1, and thinking-off capable) applies at finalist selection, not at B1 entry.
- Not authorized: B2, any sweep, any change to the rule file, the frozen prompt set, the registry or the repair templates, any other host.
- STOP: any pin mismatch; a template-repair digest mismatch; a request without `cache_prompt: false`; an LLM-call cap reached before W on more than *(author to set, if wanted)* of campaigns; OOM or CPU fallback; a non-finite metric.

## Machine-readable block (the final note must contain exactly one such block)

```json
{
  "author": "Dowling Wong",
  "phase": "b1",
  "approved": false,
  "rule_sha256": "79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20",
  "nodes": ["digits_mlp", "openml_credit_approval", "openml_ionosphere"],
  "stage_a_table_sha256": "00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c",
  "stage_a_amendment_table_sha256": "71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103",
  "stage_a_amendment_acceptance_sha256": "TODO_AFTER_M2_ACCEPTANCE_FORMAT",
  "llm_call_cap": 80,
  "host": "TASL-7",
  "workers": 20
}
```

`approved` stays `false` and the unresolved acceptance SHA stays a TODO string, so the gate cannot accept this draft by accident.
