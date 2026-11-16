# Sweep-2 HTCondor authority — R1-SWEEP-HOST-HTC signed (16 November 2026)

**Authority read from branch `author-sweephost-20261116` @ `4651469a`** (row commit `fd275c53`, provenance commit
`4651469a`; carries all author rows to date). Row **R1-SWEEP-HOST-HTC**:

- from sweep 2 on, **all C3 label sweeps** (T0 sweep 2, its B.2 audits, later T1 sweeps) run as **HTCondor jobs**;
- **LLM label runs only on NEMO2 L40S** (job requirements pin the GPU model and the CPU model); CPU-only audits run
  on **one fixed HTCondor CPU node type**; **one host type per table**;
- it supersedes the host descriptions of R1-SWEEP-HOST (deepthought-primary) and R1-MAIN-PROPOSER (c)
  (4090 → L40S); **sweep 1 stays frozen** and is not rerun;
- selection host (4090) vs deployment host (L40S) must be disclosed, and an **L40S deployment check is required
  before EVIDENCE**;
- the row does **not** authorize sweep-2 launch: EVIDENCE still needs the author-committed
  `docs/r1/authorizations/c3_sweep2_<date>.md`, and the **R1-BX-D8 analysis lock stands**.

The work plan `prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` (`docs/runbooks-16nov` @ `a2789ea6`) is now active for the
cluster units; status:

| unit | status |
|---|---|
| S2-C1 image freeze proposal (v1 gpu `69b06b35…`) | ready for the author's P7 authorization; v1 remains in use, no digest switch |
| S2-C2 sweep job wrapper (ENGINEERING) | **ACCEPTED** by independent review (round 3); 31 synthetic tests pass |
| S2-C4 timing pilot (1 node × 2 instances × both modes) | **ACCEPTED and EXECUTED** on NEMO2 L40S (2 jobs, rc 0; measured 867/921 s wall, 16 s queue, 75/82 s GGUF, 61/61 offload; layout proposal 8,289 s/full chunk, 16 chunks, ~36.84 GPU-h; disk 42.4M kB / memory 32G; sealed `/ceph` evidence verified) |
| S2-C3 L40S deployment check | next unit: pre-declared criteria + replay of B2's 12 thinking-off roots; will be submitted for review before running |
| S2-C5 real-submission switch / S2-C6 EVIDENCE launch | not started (gated: P2–P7 + author authorization; D8 lock) |

**S2-C3 design note (pre-declaration in progress).** The B2 batch tree (TASL-7) has one `job.json` per root
(`phase=b2`, `mode=off`, node/seed/W/audit seeds/authorization head etc.), which is the exact input of the reviewed
B2 campaign driver (`python -m r1.exam.campaign`). The deployment check will replay the 12 off roots
(3 nodes × seeds 9011–9014) on L40S under the frozen v1 gpu image + B2 harness and compare per-instance `final_y`,
parse failures, invalid/duplicate/no-op rates and server throughput with the B2 EVIDENCE values (B2 hand-back). The
replay is **ENGINEERING**: it must not produce EVIDENCE-labelled data, so the reviewed wrapper will carry the
explicit engineering label/replay marker and the comparison will ignore any label fields; the pre-declared tolerance
criteria will be written **before** the run and the comparison script submitted for review together with the replay
wrapper.

EVIDENCE still gated: `c3_sweep2_<date>` authorization (P3) absent, P2 integration branch absent, P4/P5/P7 not yet
recorded in an authorization; R1-BX-D8 analysis lock unchanged.

## Update — author decisions `author-decisions-20261116b` @ `025bfc16` (16 Nov 2026)

New signed rows and decisions (main will fast-forward to this branch):

- **R1-E1-OPENML:** authorize an independently reviewed e1 offline mechanism wired into
  `r1/scripts/c3_env_replay.py` run path: (a) prove the six OpenML datasets are exactly the sweep-1 datasets by the
  identity sweep 1 recorded; (b) worker subprocesses have no network and cannot download. If sweep 1 recorded no
  usable dataset hashes, report **"identity unprovable"** and STOP for the author (then decide whether the 4
  non-OpenML cases suffice or an exception to R1-MAIN-PROPOSER (g)2). Zero-tolerance pass rule and offline STOP
  unchanged. Basis: e1 STOP at `ops-e1-replay-20261116` @ `fc7d8e4e`, review accepted.
- **R1-S2C3-DRIVER:** authorize a reviewed, declared-input, TASL-independent ENGINEERING replay driver for the
  S2-C3 L40S deployment check; all inputs (B2 handback binding, Stage A tables, OpenML datasets, …) declared and
  sha-verified; ENGINEERING_ONLY; no B.2 audits; no 7001–7010. Corrected criterion 3 (invalid 20 / duplicates 33 /
  noops 20 over 240, ±10 %; parse failure 0/240) accepted.
- **R1-S2C3B-SEEDS:** `liveness_seed_policy = "sweep1_d28_reuse"` accepted (per-node first two sweep instance seeds;
  `r1.liveness` has no seed flag); liveness output never enters a label table/training/selection and touches no
  7001–7010/8001–8010/9001+; the overlap with sweep-2 instance seeds is disclosed in the sweep-2 report. Amends
  R1-SWEEP2-SETTINGS (4)'s disjointness wording.
- **R1-G1B-CAP:** G.1b waits for the G.0 census run time and candidate screening; provisional standalone cap
  **100 GPU-h**; a projection above it is an author STOP. D21 protocol unchanged (552 runs/node).
- **R1-SWEEP2-LAYOUT:** the sweep-2 authorization uses the measured 32k layout: 16 chunks (one per (node, memory
  mode)), ~9,387 s/chunk, ~41.72 GPU-h total (below the 60 GPU-h cap); `request_walltime = 12,203` s,
  `request_disk = 42,460,977` kB, `request_memory = 32,000` MB; supersedes the S2-C4 16k layout. Basis: 32k smoke
  (clusters 759728/759729, `sweep2-main-20261116` @ `f172d299`, sealed under
  `/ceph/srv/dwong/paperb/sweep2/s2smoke-20261116-a/`).

**Proceed in this order:** S2-C3 driver (this row) → S2-C3 run → S2-C3b run → e1 mechanism; G.1b only after the
G.0 census.

## Update — R1-SWEEP2-LAYOUT-AMEND (`author-decisions-20261116c` @ `65d8d5bb`, 17 Nov 2026)

- **The 32k layout numbers are void** (the visible in-campaign worker runs never trained). Fix the worker
  environment, add the worker gates (STOP on a zero-success campaign; STOP if the overall worker failure rate exceeds
  sweep-1's ledger rate + 5 pp, with sweep-1's rate computed first), rerun the 2-instance 32k smoke with real
  training, and re-measure.
- **Walltime = 1.5 × the re-measured single-chunk time**; a chunk that exceeds its walltime is a STOP.
- **No resume path:** a killed/non-clean chunk (`NumJobStarts > 1`) is rerun whole in a **new directory**, the old
  directory is moved aside (never deleted), and the rerun is disclosed in the report.
- **Thinking kwargs byte-identical to the exam** (extra spaces removed); disclosure is not a substitute.
- **S2-C3b liveness pass counts as the pre-launch liveness gate only if** its image digest, paper commit, harness
  pin and server settings are the launch's (the unit now records/validates `launch_binding`).
- R1-SWEEP2-SETTINGS (5)'s 60 GPU-h / 48 h projection cap is unchanged.
