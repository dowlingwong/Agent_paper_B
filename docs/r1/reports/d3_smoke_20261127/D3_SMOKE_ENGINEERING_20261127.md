# D.3 per-arm ENGINEERING smoke (`compute/20261127-27`)

**Status: ENGINEERING_ONLY. No campaign, label, evaluation, test or sealed value is evidence.** This record runs the
real G1 adapter (node, `gemma4_31b` manager, worker), the real G1 snapshot/record writers and the real G6 audit on one
reserved smoke instance per D.3a arm. It writes no outcome table.

- **Task:** `compute/20261127-27` (with the inherited takeover card `compute/20261126-00`).
- **Base:** `origin/main` `d669b0bf` (the branch merged `a3c8284d` before delivery).
- **Deliverable branch:** `compute-d3-smoke-20261127` @ `546be763` (base `d669b0bf`, merges `280c0015`); this report and its captures are in that commit.
- **Review branch:** `compute-d3-smoke-review-20261127` @ `936b2c58`; review
  `docs/r1/reviews/D3_SMOKE_ENGINEERING_REVIEW_20261127.md` sha256 `30657df4…`; **Verdict: ACCEPTED**.
- **Run:** `d3-smoke-engineering-20261127-a`, run root `/home/dowling/r1_tracks/work/d3smoke_20261127/run-d` on TASL-2.

## 1. Placement and what ran

The task card named Ada (`zli538`) with `gemma4_31b`. On Ada, `/data1/dowling/models` is mode 0700 and unreadable to
`zli538`; the model is not available to that account. TASL-2 has the same pinned GGUF
(`/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf`, sha256
`2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`), the llama.cpp build and a free RTX 4090. The job
was placed there under R1-HOST-FREE (compute decides the host); no signed note binds this engineering smoke to Ada.
The card lease was held by the llama-server in `~/r1_locks/gpu0.lock`; the CPU set was `16-31` under
`~/r1_locks/cpus-16-31.lock`. The other user processes on the card at start: 0 (count and memory only).

| Field | Value |
|---|---|
| Host / GPU | TASL-2 / NVIDIA GeForce RTX 4090, 24,564 MiB, driver 535.309.01 |
| GPU UUID | `GPU-4d623e76-7587-ee15-a633-46f60d220d94` |
| Memory at start / at server load | 23,825 MiB free / 21,591 MiB used, 2,592 MiB free |
| Proposer | `gemma4_31b` Q4_K_M through llama-server `--reasoning off`; alias `gemma4_31b` |
| Harness | `9bb416805175149eb87b71f28d77530572aa4bce`, clean |
| Python / packages | `/home/dowling/r1_tracks/venv` (3.11.17) |
| Node / seed | `digits_mlp` / `6301` (reserved engineering seed) |
| W / LLM cap | 20 / 80 (unchanged) |

**Design deviation, recorded not hidden.** The signed D.3 pre-declaration fixes the engineering smoke to
`openml_climate` and says it is never audited for Y; the task card asks for one instance per arm and a G6 audit. The
TASL-2 `openml_climate` data cache is empty and the OpenML cache rebuild is on deepthought, so the smoke ran on
`digits_mlp` and the G6 audit is labelled an engineering check only. This is a level-2 conflict between the task card
and the signed pre-declaration; the coordinator must obtain a signed amendment or re-scope before any Y value is
used. No Y value here enters an outcome table.

## 2. Campaigns

One instance per arm; every D.3a arm the adapter allows (A0, A0R, A1, A2, FIXR3, EGATE, LADDER). A3/A5/A6 were refused
by the adapter (no frozen learned artefact; A6 always refuses).

| Arm | Worker runs | LLM calls | Rule skips | Value skips | Keeps | Ended on | Wall s |
|---|---:|---:|---:|---:|---:|---|---:|
| A0 | 20 | 20 | 0 | 0 | 2 | worker_runs | 132.7 |
| A0R | 20 | 20 | 0 | 0 | 2 | worker_runs | 132.2 |
| A1 | 20 | 20 | 0 | 0 | 2 | worker_runs | 132.1 |
| A2 | 20 | 20 | 0 | 0 | 2 | worker_runs | 132.4 |
| FIXR3 | 18 | 7 | 0 | 0 | 1 | no_fundable_candidate | 53.3 |
| EGATE | 20 | 3 | 0 | 0 | 1 | worker_runs | 38.0 |
| LADDER | 20 | 20 | 0 | 0 | 19 | worker_runs | 126.1 |

The manager proposed a distinct configuration on every trial in this run, so **no rule skip occurred**; the
"rule skip charges no worker run and counts the manager call" accounting is exercised by the G8 unit test, but the
live smoke did not produce an instance of it. FIXR3 ended on `no_fundable_candidate` after 18 charged runs, which
exercises the replicate-arm budget end; EGATE used 3 manager calls and 20 runs. LADDER kept most candidates, as its
margin rule allows. Repeated training is charged in the replicate arms (G8); the per-arm `runs.jsonl`/`ledger.jsonl`
was checked for the charged counts.

## 3. G6 audit (engineering check, not Y evidence)

All seven campaigns were audited on the reserved smoke audit block 6391-6400 of instance 6301: terminal, every w
point reached, and every kept incumbent. The audit used the same environment as the campaign (Python 3.11.17,
scikit-learn 1.9.1) and sigma `0.006613322803772441` from `d3_constants.json` for `digits_mlp`.

| Arm | Y (engineering) | y_raw | w | Keeps audited |
|---|---:|---:|---:|---:|
| A0 | 1.7269 | 0.011420 | 20 | 2 |
| A0R | 1.7269 | 0.011420 | 20 | 2 |
| A1 | 1.7269 | 0.011420 | 20 | 2 |
| A2 | 1.7269 | 0.011420 | 20 | 2 |
| FIXR3 | 1.2636 | 0.008356 | 18 | 1 |
| EGATE | 1.2636 | 0.008356 | 20 | 1 |
| LADDER | 1.8532 | 0.012256 | 20 | 19 |

The audit record (`audit.json`) is self-hashed; the per-arm `Y_final.jsonl`, `Y_w.jsonl`, `Y_keep.jsonl` and
`g7_rows.jsonl` are captured with `SHA256SUMS`.

## 4. G7 and the pinned analysis — STOP

`table_check` builds the seven rows with G7's `build_row`, but `d3_outcome_table.build_row` calls
`d3_analysis.audit_seeds`, which accepts only the deployment seeds 6201-6218. Seed 6301 raises
`D3InputError: not a declared D.3 instance seed`. The pinned analysis is hash-bound in revision 4 and was not changed
here; no `r1_d3_outcome/v2` table was written, and no synthetic full-design expansion was substituted. This is a
**STOP of the "G7 assembles the table and the pinned analysis accepts it" sub-item**; it needs a signed amendment or a
re-scope (for example, an engineering-only analysis path, which is not in the signed text).

## 5. Tests

`AR_HARNESS_ROOT=…/harness_9bb_20261127 python -m pytest -q r1/tests/test_d3_audit_g6.py r1/tests/test_d3_smoke_engineering.py`
→ **16 passed** at `66f13e1c` (17 after the final self-hash test on the delivered tip). Full `r1/tests` with the two
torch-only modules excluded (this TASL-2 venv has no torch; the same exclusion is applied to both runs):

| Run | Passed | Failed | Skipped | Errors | Failure/error IDs |
|---|---:|---:|---:|---:|---|
| base `d669b0bf` | 4,788 | 57 | 162 | 3 | 60, sha256 `c8e7b55a…` |
| tip `66f13e1c` | 4,793 | 57 | 162 | 3 | 60, sha256 `c8e7b55a…` |

The tip's failure/error ID list is identical to the base's (zero new failures; +5 passed from the new tests). The two
excluded modules are `test_trackp_p4_runner.py` and `test_trackp_sft_select_stop.py`, both `ModuleNotFoundError: torch`;
they fail at collection on both base and tip in this venv.

## 6. Captures and hashes

Capture tree: `docs/r1/reports/d3_smoke_20261127/captures/` (152 files; top-level `SHA256SUMS` sha256 `172b2e65f3dbadad61b5775f970ec50326a1e0c75c50b584bc3805eedfdd9435`). The full run
trees stay on TASL-2 under `/home/dowling/r1_tracks/work/d3smoke_20261127/run-d/`.

| Object | sha256 |
|---|---|
| `manifest.json` | `946ee1df19b7e75ac155cfc23b6cb32850775eaec4245694646266fc9831bb13` |
| `observed.json` | `86c0508b3f2fd7e29d61080d96312a82669292a1479f2bb4f320569db41d391f` |
| `run-d/smoke.json` | `60af2df7b0947289ab78aff5fe47a0547f2204c9d6be43017789f634396deb3d` |
| `run-d/audit.json` | `6caec2c1718072bcf7fc35496006d31bde04ba10a33497b4d3c7fefeced98a7e` |
| `run-d/table.json` | `aef3eb28e41c84f03e41dd7dcaa0d01e19d928c092c7cad6049e54cc3d790aa6` |
| chunk A0 / A0R / A1 / A2 | `1c4c84e3…` / `6c223d4e…` / `a6c28642…` / `05eed52c…` |
| chunk FIXR3 / EGATE / LADDER | `93ee6eab…` / `32027253…` / `62e10319…` |
| per-campaign summaries A0/A0R/A1/A2 | `4c7737b9…` / `31e3cebe…` / `a658e96f…` / `9d78a5c0…` |
| per-campaign summaries FIXR3/EGATE/LADDER | `84c44031…` / `702f2bab…` / `d1345b43…` |
| full-suite tip / base logs | `236c673a…` / `a5766966…` |
| review file | `30657df4f3d7e702c82360ebfb970f1235db9977fe6d18384aa9102a21e25b45` |

The campaign `SHA256SUMS` and the audit `SHA256SUMS` files are in the capture tree; the run record's `record_sha256`
is the self-hash of `smoke.json` (`3e69073a…`), and the audit record's is `b713b5fa…`. The table record is a
**REFUSED** record (`74392786…`), not an outcome table.

## 7. What happens next

- The coordinator merges the deliverable and its review after its own checks.
- The signed smoke definition conflicts with the task card on node and on auditing the smoke for Y; a signed
  amendment or a re-scope is needed before the G7/analysis sub-item can pass.
- The engineering result says the G1 adapter, all seven arms, the replicate budget end, the G1 snapshots/final and
  the G6 terminal/w/keep audit all run; it does not say anything about the campaign outcome.
- `compute/20261127-29` (Ada P5 records) was attempted: Ada cards 0 and 2 are empty, but the Track P `gpu_lease`
  helper checks all GPUs and refused because another user holds cards 1/3-7; no GPU work started. Needs a reviewed
  per-card lease route. `compute/20261127-28` (E-INT census) needs its signed spec, staged data and smoke.
