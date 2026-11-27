# Report — D.3 per-arm ENGINEERING smoke (`compute/20261127-27`)

**Result: ENGINEERING PASS for the G1/G6 chain; STOP for the G7/analysis sub-item and for the signed smoke
definition.** All seven D.3a arms ran one reserved smoke instance each through the real adapter, worker and manager;
the G1 snapshots/final and the G6 terminal/w/keep audit ran; G7/build_row refused the reserved smoke seed, and the
signed pre-declaration fixes a different smoke node and says the smoke is never audited for Y. No outcome table was
written. No label, evaluation, test or sealed value was read. No campaign result is claimed.

## 1. Deliverable

| Object | Value |
|---|---|
| Task | `compute/20261127-27` (with `compute/20261126-00` takeover) |
| Base | `origin/main` `d669b0bf`; merged `280c0015` |
| Deliverable branch | `compute-d3-smoke-20261127` @ `7ecc3594` (report/captures at `546be763`; full-suite captures added at `b662c718`; P5 blocker note at `7ecc3594`) |
| Review branch | `compute-d3-smoke-review-20261127` @ `936b2c58` |
| Review | `docs/r1/reviews/D3_SMOKE_ENGINEERING_REVIEW_20261127.md` sha256 `30657df4f3d7e702c82360ebfb970f1235db9977fe6d18384aa9102a21e25b45`; **ACCEPTED** |
| Run | `d3-smoke-engineering-20261127-a`, root `/home/dowling/r1_tracks/work/d3smoke_20261127/run-d` on TASL-2 |
| Manifest / observed | sha256 `946ee1df…` / `86c0508b…` |
| `smoke.json` / `audit.json` | sha256 `60af2df7…` / `6caec2c1…` |
| `table.json` | REFUSED record, sha256 `aef3eb28…` |
| Captures | `docs/r1/reports/d3_smoke_20261127/captures/`; top-level `SHA256SUMS` sha256 `172b2e65…` |

## 2. Placement and scope

The task card named Ada (`zli538`) with `gemma4_31b`. On Ada `/data1/dowling/models` is mode 0700 and unreadable to
`zli538`; the model is not available to that account. TASL-2 has the same GGUF (sha256 `2959c1b0…`), the llama.cpp
build and a free RTX 4090; the smoke was placed there under R1-HOST-FREE (compute decides the host). The card lease
was held by the llama-server in `~/r1_locks/gpu0.lock`; CPU set 16-31 under `~/r1_locks/cpus-16-31.lock`. Observed:
`NVIDIA GeForce RTX 4090`, 24,564 MiB, driver 535.309.01, UUID `GPU-4d623e76…`; 23,825 MiB free at probe, 21,591 MiB
used / 2,592 MiB free after the model loaded; other processes 0. Harness `9bb41680…` clean; Python 3.11.17.

**Signed-design conflict (STOP).** The pre-declaration fixes the engineering smoke to `openml_climate`, seeds
6301-6302, and says it is never audited for Y; the task card asks one instance per arm and a G6 audit. TASL-2's
`openml_climate` data cache is empty, so the run used `digits_mlp`; the deviation and the engineering-only label are
recorded in `smoke.json`. The coordinator needs a signed amendment or a re-scope before any Y value is used.

## 3. Campaigns and audit (engineering only)

One instance, seed 6301, W = 20, LLM cap = 80, harness `9bb41680`, `verify_seed_base = 20000`.

| Arm | Runs | Calls | Rule skips | Keeps | Ended on | Y (eng.) | w | Keeps audited |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| A0 | 20 | 20 | 0 | 2 | worker_runs | 1.7269 | 20 | 2 |
| A0R | 20 | 20 | 0 | 2 | worker_runs | 1.7269 | 20 | 2 |
| A1 | 20 | 20 | 0 | 2 | worker_runs | 1.7269 | 20 | 2 |
| A2 | 20 | 20 | 0 | 2 | worker_runs | 1.7269 | 20 | 2 |
| FIXR3 | 18 | 7 | 0 | 1 | no_fundable_candidate | 1.2636 | 18 | 1 |
| EGATE | 20 | 3 | 0 | 1 | worker_runs | 1.2636 | 20 | 1 |
| LADDER | 20 | 20 | 0 | 19 | worker_runs | 1.8532 | 20 | 19 |

The manager proposed a distinct configuration every trial in this run, so **no rule skip occurred**; the
skip-charges-no-run/counts-the-call rule is covered by the G8 unit test but the live smoke did not exercise it.
FIXR3 exercised the replicate-arm `no_fundable_candidate` end; EGATE used 3 manager calls; LADDER kept most candidates.
The G6 audit used the reserved smoke block 6391-6400 and the same environment; `sigma_node` 0.006613… from
`d3_constants.json`. The Y column is an engineering check of the audit path, **not evidence**.

## 4. G7 / pinned analysis — STOP

`table_check` built the seven rows with G7 `build_row` and recorded the refusal:

| Arm | campaign_id | refusal |
|---|---|---|
| all seven | `D.3a__<arm>__digits_mlp__s6301__r0` | `not a declared D.3 instance seed` |

`d3_outcome_table.build_row` calls `d3_analysis.audit_seeds`, which accepts only 6201-6218. The analysis is hash-bound
in pre-declaration revision 4 and was not changed. No `r1_d3_outcome/v2` table and no synthetic expansion was written.
This sub-item needs a signed amendment or a re-scope (e.g. an engineering-only analysis path that is not in the
signed text).

## 5. Tests

- Focused: `AR_HARNESS_ROOT=…/harness_9bb_20261127 python -m pytest -q r1/tests/test_d3_audit_g6.py r1/tests/test_d3_smoke_engineering.py`
  → **17 passed** at `aa28824f`.
- Full `r1/tests` with the two torch-only modules excluded (this TASL-2 venv has no torch; same exclusion on both
  sides): base `280c0015` **45 failed / 4,800 passed / 162 skipped / 3 errors / 71 subtests**; merged tip
  `546be763` **45 failed / 4,805 passed / 162 skipped / 3 errors / 71 subtests**. The 48 failure/error IDs are
  identical (sha256 `c308eb23…`): **zero new failures, +5 passed**. The pre-merge pair (base `d669b0bf` 57/4,788,
  tip `66f13e1c` 57/4,793) had identical 60 IDs (`c8e7b55a…`).

## 6. Running elsewhere / blocked

- **Expansion G.1b (`compute/20261126-10`):** ETTh1, MetaMaze and **Forest Cover** sealed; Forest Cover attempt-1
  `determinism` PASS, `stop: null`, seal receipt `2940254a…`. Titanic was 84/150 joint runs at 15:33Z, still running;
  assemble/summarise wait for its seal.
- **Houseprice CPU-set (`compute/20261127-15`):** **STOP `too_few_attempts`**; two complete deterministic
  reference-identical attempts, the procedure needs three. See `20261127-15-houseprice-cpuset-stop.md`.
- **D.3 HTCondor preflight:** still no batch GPU (pool advertises none); request unchanged.
- **G.5 P11 / campaigns:** unchanged; TASL-7 card free, TASL-2 CPU sets now 0-3/4-7/16-31 free.
- **`compute/20261127-29` (Ada P5): attempted after the D.3 smoke; blocked before any GPU work.** Ada card 0 and
  card 2 are empty (5 MiB used, 48,427 MiB free), but the Track P `gpu_lease` helper in `r1/c3/train/run.py` checks
  compute processes on **all** GPUs and refused because another user holds cards 1/3-7:
  `TrackPStop: another compute process holds the GPU: [...]` (pids 3952132, 3878351-3878353, 3878386-3878388;
  count and memory only). No training, smoke or E0 started; the pre-check log is
  `/data1/zli538/paperb_p4_20261127/p5_smoke_20261127/smoke.log`. Needs a reviewed per-card lease route (or a
  host-owner statement) before P5 can run.
- **`compute/20261127-28` (E-INT census):** ready only after a signed census spec/authorization, the staged
  ClimbMix data/tokenizer and the smoke; not started. It yields to Paper B.

## 7. Decided alone

To move the engineering smoke from Ada to TASL-2 after confirming the model is unreadable to `zli538`; to keep
`digits_mlp` and record the design-node deviation rather than fabricate an OpenML cache; to refuse the G7 table
instead of changing the hash-pinned analysis; to keep `run-b`/`run-c` as sealed pre-check attempts and deliver
`run-d`, produced with the self-hashed record; to run the full suite with the two torch-only modules excluded and
compare the same selection on both sides.

## 8. What happens next

1. Coordinator: merge `compute-d3-smoke-20261127` and its review after its own checks.
2. Coordinator/author: decide the signed smoke conflict and the G7/analysis sub-item (amendment or re-scope).
3. Then `compute/20261127-29`, then `compute/20261127-28`.
