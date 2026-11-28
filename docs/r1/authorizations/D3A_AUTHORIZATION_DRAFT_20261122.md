**AI-assisted (Claude, 22 and 27 Nov 2026. Codex, revision 5 binding, 28 Nov 2026). Unsigned draft.**

# Authorization: D.3a closed loop on T0, rule arms (EVIDENCE) — DRAFT, NOT SIGNED

Drafted by a subagent of the coordinating chat. Tier E (R1-PROCESS-TIERS). This file authorizes nothing: `approved` stays `false` until the author
signs. Prepared under R1-D3-MIN ("Each stage also needs its authorization note") and R1-MINSUB-CHOICES (4), on branch
`mac-d3-predecl-20261122` over `author-minsub-20261122` @ `d9acb501`. This draft binds the signed revision 5
[pre-declaration](D3_PREDECLARATION_DRAFT_20261128_R5.md), published frozen at `d25938ed`, by the SHA-256 below.
Revision 2 follows `docs/r1/reviews/D3_PREDECLARATION_REVIEW_20261122.md` (findings 1, 8, 10 and NOTE 10:
EGATE pin, smoke seeds, P10/P11, chunk count by repetition, the house layout fields). Revision 3 follows the round-2
review `docs/r1/reviews/D3_PREDECLARATION_REVIEW_R2_20261122.md` (smoke node and replicate seeds, P10 outside the
pinned script, the analysis run once). Revision 4 (27 Nov 2026) aligns it with revision 4 of the pre-declaration
(A0R; one GPU model per instance, R1-HOST-FREE (2)(c); infrastructure failures, R1-CARD-SHARE (3) and R1-NO-TIMEOUT;
the 140 GPU-h figure a reporting threshold; D.3b unconditional, R1-D3B-UNCONDITIONAL).

Under [R1-D3-STEP8-HOLD (3)](../PLAN.md#27-november-2026-f--d3-step-8-waits-for-the-screening-result-author),
the [deepthought2 screening record](../reports/screen_measure_20261128/dt2/SCREEN_MEASURE_DT2_20261128.md)
and its [accepted re-check](../reviews/SCREEN_MEASURE_DT2_ANALYSIS_REVIEW_20261128_RECHECK.md), published at
`bf4e0083`, release step (8). All 10,164 runs completed with zero failures, no node returned
`SHARED`, and the recorded decision is `R1_THEORY_RHO_2_FINAL`. R1-D3-PREDECL-R5 carries that receipt forward.

**On signature** the author (or the coordinating chat under an explicit author row) copies this file to
`docs/r1/authorizations/d3a_<YYYYMMDD>.md`, retains the bound `predeclaration_sha256`, sets `approved: true`,
fills every `<pending>` and records P1–P11 as PASS with their citations. The signed file is then published byte-identically
on `main` before any D.3a campaign starts.

**28 Nov P7 re-read and launch hold.** The accepted exact-runtime receipt records 50 failures in 276 charged
worker runs. P7 passes at revision 5's threshold of 18.53%. The engineering receipt establishes that the pinned
server fits on the TASL-2 RTX 4090. Evidence launch binding still requires the production manifest and reservation
proof on the selected route, the direct campaign environment comparison and image disposition under §§2 and 7.2,
the resource request basis and a run ID verified against Compute's ledger.

## Key block

```
approved: false
label: EVIDENCE
phase: d3a_closed_loop
run_id: <pending: fresh D.3a evidence ID verified against Compute's ledger>
predeclaration: docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md
predeclaration_sha256: 700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad
analysis_script: r1/c3/d3_analysis.py
analysis_sha256: c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce
constants_file_sha256: 4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93
arms: A0, A0R, A1, A2, FIXR3, EGATE, LADDER
fixr3: r = 3, one-sided Welch, alpha 0.05
egate: r1/baselines/responses.py PaceStyleGate, alpha 0.1, clip 0.05, max_pairs 8 (as on main)
nodes: digits_mlp, openml_breast_w, openml_climate, openml_credit_approval, openml_ionosphere, openml_sonar, tabular_mlp
instances: 6201-6218 per node (126)
smoke_seeds: 6301-6302 on openml_climate, smoke replicate seeds 6311-6319 and 6321-6329 (ENGINEERING_ONLY, P7)
replicate_seeds: 6500 + 10 i + j, j = 1..9 (6501-6679)
memory_mode: append_only_summary
W: 20
llm_call_cap: 80 (R1-D3-CHOICES (2)); a call issued again after an infrastructure failure is not counted
repetitions: 1 (R1-D3-CHOICES (2))
audit: K = 10, seeds 6700 + 10 i + k (6701-6880), host deepthought CPUs
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296 (proposed; pre-declaration §2)
model_gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
llama_server_sha256: 646caa007c99a5c9e644dac1c1a6a75f84ed78c5ca08da39a2fb690073d61e5b
server: -c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs {"enable_thinking":false} q8_0 K/V; cache_prompt false on every call
harness_commit: 9bb416805175149eb87b71f28d77530572aa4bce
paper_commit: <pending: exact launch commit after the runtime binding is verified>
gpu_model: RTX 4090 for each of the seven nodes (R1-HOST-FREE (2)(c))
layout_chunks: 49 (one chunk per node and arm at one repetition)
layout_request_walltime_s: <pending: bind the selected route and any scheduler requests using the exact-runtime P7 basis>
layout_request_disk_kb: <pending: full-chunk scratch basis x 1.4 if a scheduler requests disk>
layout_request_memory_mb: <pending: complete host RAM basis x 1.4 if a scheduler requests memory>
layout_gpu_hours_projection: 28.85 GPU-h (exact-runtime P7 engineering projection, A0R sensitivity 32.91 GPU-h)
layout_wall_hours: <pending: report elapsed hours for the bound placement and serial or concurrent schedule>
projection_reporting_threshold_gpu_hours: 140 (R1-NO-TIMEOUT (3): reported against, reaching it reported to the author; not a STOP)
P1: PASS — s2ev-20261119-a, B.2 attempt 3, ACCEPTED at 6c5ba97b; registered in R1-SWEEP2-LABELS-FREEZE (f93264fc)
P2: PASS — R1-S2-LABELS-TRAINDEV-RELEASE, release.py receipt v2 (dc9ad88a), sha256 de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c
P3: PASS — reviewed fit of A1, A2 and LADDER on receipted sweep-2 P3 dev instances; artifact sha256 above equals frozen rev 5 §§5.0 and 14
P4: PASS — independently accepted (docs/r1/reviews/D3_PREDECL_R5_REVIEW_20261128.md), signed and frozen under R1-D3-PREDECL-R5, published at d25938ed, and bound above with the screening record at bf4e0083 carried forward
P5: PASS — reviewed code units and reservation/retry accounting are merged; see Code-Commit and review inventory below. Live reservation binding is checked at deployment.
P6: PASS — frozen rev 5 harness pin above; sweep-2 defaults comparison and R1-D3-VERIFY-SEED review below
P7: PASS — accepted exact-runtime P7 at a70c8872, 14/14 engineering campaigns, 50/276 = 18.12% against the 18.53% stage STOP in frozen rev 5 §10
P8: PASS — deepthought host preparation, e1 basis, clean shared harness pin and co-tenancy load check ACCEPTED at b70cfa01; recheck the audit conditions at runtime
P9: PENDING — the author's signature of this note
P10: PENDING — the separate reviewed verify-seed disjointness check of the pre-declaration §4.1 (outside `r1/c3/d3_analysis.py`; its result entered in the pre-declaration before its review) re-run at the launch commit with the same verdict
P11: PENDING — `r1/c3/d3_analysis.py` at the launch commit has the sha256 of the pre-declaration's §14, and `r1/tests/test_d3_analysis.py` passes there (recorded output)
```

## Scope and pins

- **What runs.** Seven arms × seven nodes × 18 instances × the signed number of repetitions, memory
  `append_only_summary`, W = 20, the signed LLM-call cap, trial budget equal to the cap; seeds, arms, outcome and
  analysis exactly as the pre-declaration fixes them (§2–§9). The harness `campaign_id` of every campaign is its
  instance id, so all arms of an instance share the D26 seed stream; each (arm, repetition) has its own ledger root
  (pre-declaration §4.1).
- **Proposer host.** The selected model is RTX 4090 for all seven nodes, initially on TASL-2 using CPUs 16–31.
  TASL-7 is eligible after its own checks on an empty RTX 4090. All arms of each instance, including D.3b,
  share that model (R1-HOST-FREE (2)(c)). Every campaign records host, GPU model and UUID, driver, CPU
  model, environment freeze and the other compute processes on its card at start and end (R1-CARD-SHARE).
- **Infrastructure failures** (pre-declaration §3.1): never an outcome, never a STOP, attempts unlimited; a lost chunk
  is rerun whole in a new directory on the same GPU model, nothing of the lost attempt charged.
- **Audit host.** deepthought CPUs (R1-MINSUB-CHOICES (4)), under the four conditions of R1-SWEEP2-B2-GO as the
  pre-declaration §7.2 applies them; 16 workers, at least 10 of 40 cores free, `cotenancy.log`.
- **Data read.** The constants file (from the sweep-2 dev label block) and the pinned noise source; no test label, no
  evaluation value, no T1 label; no D.3a output trains, tunes or selects any arm (R1-D3-MIN).
- **Outputs.** Sealed per chunk with `SHA256SUMS` as sweep 2; the outcome table (`r1_d3_outcome/v2`) is built only from a
  complete design and carries the exact `predeclaration_sha256` above in its §8 header, as do the separately authorized
  D.3b and HPO-REF tables. The analysis runs **once** by `r1/c3/d3_analysis.py` with `--d3b-not-run not_started`. A later D.3b analysis recomputes the D.3a family only as a reproduction check that must equal this
  run exactly (pre-declaration §9); the D.3a result is this run's.
- **Compute (pre-declaration §11).** Exact-runtime P7 projects 28.85 proposer GPU-h for the seven-node layout,
  or 32.91 GPU-h with the reported A0R latency sensitivity, against the 140 GPU-h reporting threshold.
  The primary audit projects at most 10,080 seed runs, ≈ 13.1 worker-hours and ≈ 49 min at 16 workers,
  plus the Y(w) and kept-incumbent audits of the secondary outcomes.
- **Not authorized.** D.3b (runs whether or not the gate passes, R1-D3B-UNCONDITIONAL, but needs the arms-frozen record and its own note); the HPO-REF rows (their own note); D.3c; `openml_wdbc`; any T1 node; any other memory
  mode; any resume of a stopped or lost chunk (a lost chunk is rerun whole); any change to the arms after launch.

## Precondition records

- **P1.** [B.2 attempt-3 report](../reports/sweep2_20261116/S2_B2_AUDIT_REPORT_20261122.md) and
  [ACCEPTED review](../reviews/S2_B2_AUDIT_RUN_REVIEW_20261122.md), 10,640/10,640 finite runs. The author's
  freeze names audit stamp `20261122T164726Z` and seal SHA-256
  `55fdb2252588c8e2ec1392e480b5862227c2337ed105d11fea111c6d0a2c3eb5`.
- **P2.** [Release report](../reports/release_20261122/S2_TRAINDEV_RELEASE_20261122.md),
  [receipt v2](../reports/release_20261122/RECEIPT_sweep2_traindev_v2.json) and
  [ACCEPTED round-2 review](../reviews/RELEASE_TRAINDEV_20261122_REVIEW.md). PRE-STAGE A covers 850 train
  and 422 dev rows and zero evaluation rows. Rev 5 §13 item 9 leaves any further confirming row to the author.
- **P3–P4.** [G2 fit](../reports/d3_g2_20261127/D3_G2_CONSTANTS_FIT_20261127.md),
  [fitter review](../reviews/D3_G2_CONSTANTS_REVIEW_20261127.md) and
  [artifact review](../reviews/D3_G2_CONSTANTS_FIT_REVIEW_20261127.md). The fit repeated byte-identically.
  Rev 5 is frozen at `85943ba0` and published at `d25938ed` after its
  [independent review](../reviews/D3_PREDECL_R5_REVIEW_20261128.md). The rev 4 step (8) record is at `474c998d`.
- **P5.** [Code-Commit and review inventory](https://github.com/dowlingwong/Agent_paper_B/blob/25157781/reports/20261128-07-d3-evidence-accounting.md#p5-code-commit-and-review-set)
  covers the G1 runner and launchers, A0 and A0R, G2, FIXR3, EGATE, LADDER, G6, G7, G8 and the
  [accepted reservation and retry changes](../reviews/D3_EVIDENCE_ACCOUNTING_REVIEW_20261128.md) merged at
  `c674e051`. At deployment verify the pinned endpoint and GGUF on the same UUID as the lease and timing record.
- **P6.** The sweep-2 comparator is `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`. The cross-pin Git diff
  touches only harness `campaign.py`, `snapshot.py` and one stage-2 test. Node configs match. The
  [verify-seed review](../reviews/D3_VERIFY_SEED_REVIEW_20261127.md) accepted default-1000 replay behavior
  and the [step (5) review](../reviews/D3_PREDECL_R4_STEP5_THIRD_REVIEW_20261127.md) checked the node defaults.
- **P7.** [Exact-runtime receipt](../reports/d3a_p7_exact_20261128/D3A_P7_EXACT_RUNTIME_20261128.md) and
  [ACCEPTED re-check](../reviews/D3A_P7_EXACT_REVIEW_20261128.md) at `a70c8872`.
  `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d` completed 14/14 engineering campaigns on
  `openml_climate`. The pooled gate counts 200 harness and 76 replicate worker runs. The 50 charged failures
  include two admitted `ParserError` cases. The observed 18.12% passes at 18.53%, with 0.41 percentage points
  of headroom. The captured server used `-c 32768` and `--cache-type-k q8_0 --cache-type-v q8_0`, with the
  GGUF and binary digests above. The receipt records the contemporaneous rev 4 STOP at 12.99%. P7 ran no G6
  audit or G7 build.
- **P8.** [Deepthought readiness](../reports/d3a_p8_host_20261128/D3A_P8_HOST_20261128.md) and
  [ACCEPTED re-check](../reviews/D3A_P8_HOST_RECHECK2_20261128.md) at `b70cfa01`. The e1 audit environment
  and clean `9bb41680` harness passed. The 16-worker check left at least 34.07 cores at the pre-launch
  check and 40 during the observed load. Rev 5 §7.2's environment comparison cites campaign Python
  3.13.18 in the v1 image and audit Python 3.13.15. Complete the direct campaign environment comparison
  before author signoff.

### RTX 4090 engineering sizing basis

Exact-runtime P7 §5 extrapolates each 18-campaign chunk from the largest observed campaign mean call latency (5.764 s)
and the highest observed call count for that arm across the two seeds. It reports the following values
for a single proposer slot. Elapsed scheduling time also depends on the number of ready cards and gaps
between chunks. Reaching a scheduler request is an infrastructure failure under R1-NO-TIMEOUT.

| Arm | 18-campaign basis (s) | 1.5× scheduler request (s) |
|---|---:|---:|
| A0 | 2,179 | 3,268 |
| A0R | 2,283 | 3,424 |
| A1 | 2,283 | 3,424 |
| A2 | 4,980 | 7,470 |
| FIXR3 | 726 | 1,089 |
| EGATE | 311 | 467 |
| LADDER | 2,075 | 3,113 |

Exact-runtime P7 observed 21,999 MiB peak GPU memory. The host sampler measured 14.27 GB peak RAM used after
its delayed start. The scratch samples cover one campaign per arm per seed (3.95 MB and 3.52 MB for the two run
roots plus a 0.12 MB cache). Complete the production resource basis and verify the pinned endpoint and GPU UUID
against the lease held over the full server and chunk lifetime before binding the launch.

### Candidate code checks

On published commit `8fbad26ac68236bbf47d2f099851a906cb4f8427`, the checker
`python -B -m r1.c3.d3_verify_namespaces` returned PASS for 160 verify seeds, 20010–20801. The checker
SHA-256 matches frozen rev 5 (`62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2`).
`python -B -m pytest -q -p no:cacheprovider -rfE r1/tests/test_d3_analysis.py` passed 53 tests. The
analysis SHA-256 equals the key block above and the test SHA-256 is
`c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` as in frozen rev 5 §14. Re-run both
checks after the exact launch commit is bound to complete P10 and P11.

## Boundaries and STOPs

All STOPs of the pre-declaration §10 apply. In addition: no EVIDENCE launch before `approved: true`, P1–P11 all PASS and
this note published byte-identically on `main`; a launch commit whose authority files (PLAN, `authorizations/`) differ
from published `main`; a pin of the key block differing from the job record. On a STOP the stage is reported as
stopped, with no contrast computed from a partial design (pre-declaration §10).
