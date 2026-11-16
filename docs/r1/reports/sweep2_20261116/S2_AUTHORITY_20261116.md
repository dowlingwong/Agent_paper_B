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
