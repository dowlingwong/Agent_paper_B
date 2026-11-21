# T1 on the TASL pair: three PLAN rows for the author (DRAFT, approved: false)

**Status: DRAFT for the author's signature. Nothing here is a decision.** Each section gives the facts, the options,
a recommendation, and a proposed row text for the option recommended. The author chooses an option (or writes
another); the coordinating chat publishes the row to `docs/r1/PLAN.md` on `main`. The T1 jobs
(`sweep2/t1_tasl/g1b_tasl.py`, `g4_tasl.py`) refuse to launch until the spec's `edit_count.authority`,
`timeout_decision.authority` and `host_decision.authority` name these rows and the rows are on published `main`.

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026. Context: R1-T1-HOST-TASL (branch
`author-decisions-20261121` `e5e452a0`, reaching `main`) moves the T1 table (G.1b, G.4, G.5) to the two RTX 4090
hosts; the TASL job code and its plan are `sweep2/t1_tasl/` (`T1_TASL_PLAN.md`). The census numbers are from the U4
census report (`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, `ops-tasl-20261116` @ `76f1d7ba`,
sha256 `146b1114…92d7`), measured on the RTX 6000 Ada.

The three rows replace the H200 author items G1B-EDITS, G1B-TIMEOUT and G1B-IMAGE (`sweep2/g1b/G1B_H200_PLAN.md`
§2–§2b), which never became rows.

---

## 1. R1-G1B-EDITS — the declared edit count (recommendation: A)

**Facts.** G.1b measures each node's baseline and its declared representative edits: (n + 1) configurations × 92
runs (30 train, 30 split, 30 joint seeds, plus the default and its repeat). R1-G1B-CAP says "D21 protocol unchanged
(552 runs per node)", which is (5 + 1) × 92: five edits, as in the CPU E1 measurement. **Every one of the seven passed
T1 nodes declares four edits** (E1–E4; the U3 kit reviews accepted four; `mlgym_houseprice`'s edits manifest
`f26332ff…` also lists four). With four edits a node has 460 runs. The queue of 21 Nov repeats "552"; the two numbers
cannot both hold.

| | A: four edits | B: five edits |
|---|---|---|
| Runs per node | 460 | 552 |
| GPU-h, six GPU nodes (4090/Ada ratio 1.0; 1.5) | 28.3 (41.6) | 33.6 (49.7) |
| Wall per host (TASL-2 / TASL-7, ratio 1.0) | 14.1 h / 14.2 h | 16.7 h / 16.9 h |
| `mlgym_houseprice` (8 CPU cores) | 0.9 h | 1.0 h |
| Kit change | none | a new diff in each of seven nodes; `representative_edits/` is frozen, so every committed pin changes |
| Census | valid as is | committed and deployed pins no longer match: U2 re-smokes on each node (or a census amendment) |

- **A (recommended): measure the four declared edits; 460 runs per node.** The D21 rule is unchanged and applied
  uniformly within T1. Disclosure: D21's "≥ 2 material edits" is applied out of four edits on T1 nodes against five on
  T0 nodes, which makes qualifying slightly harder on T1; the screening funnel (R1-BX-D12) says so.
- **B: add a fifth edit per node before any measurement; 552 runs per node.** About a day of desk work (seven new
  diffs, manifests, composability tests, independent review) plus seven U2 re-smokes, before G.1b can start.

**Proposed row (A):**

> | R1-G1B-EDITS | G.1b measures each T1 node's **four** declared representative edits (E1–E4): (4 + 1) × 92 = **460 runs per node**, uniform across the T1 nodes, on the TASL pair (R1-T1-HOST-TASL). Amends the "552 runs per node" of R1-G1B-CAP, which assumed five edits; the D21 rule and the 100 GPU-h cap are unchanged. The screening funnel (R1-BX-D12) discloses that T1 nodes qualify out of four edits and T0 nodes out of five. Basis: `docs/r1/proposals/T1_TASL_ROWS_DRAFT_20261121.md` §1; U4 census report (four declared edits on every passed node). |

---

## 2. R1-G1B-TIMEOUT — the per-run timeout basis (recommendation: B)

**Facts.** R1-TRACKG-PORT-DECISIONS (4): timeout = 3 × the census baseline run time; a timeout is the proposal's
failure. The census baseline is the B1 record (`c0`) on the RTX 6000 Ada. An edit can make a run slower. On
`mlab_ogbn_arxiv`, E4 took 21.8 s in the census, against 3 × 5.651 = 16.95 s.

On the TASL pair the census times are an estimate (another card), and the task says to STOP if a measured run exceeds
the declared timeout. The TASL code does exactly that: any G.1b run that reaches the timeout is a STOP
(`stop_class: timing`), not a divergent row, and every part records the 4090/Ada ratio of its baseline runs.

| Node | B1 baseline (s) | Slowest executed census record (s) | Timeout under A (s) | Timeout under B (s) |
|---|---|---|---|---|
| `mlab_cifar10` | 12.297 | 13.347 (E2) | 36.89 | 40.04 |
| `mlab_imdb` | 64.142 | 65.156 (E1) | 192.43 | 195.47 |
| `mlab_ogbn_arxiv` | 5.651 | 21.8 (E4) | 16.95 | 65.40 |
| `mlgym_cifar10` | 31.731 | 35.948 (E3) | 95.19 | 107.84 |
| `mlgym_fmnist` | 34.376 | 40.795 (E3) | 103.13 | 122.39 |
| `mlgym_breakout_minatar` | 61.248 | 61.781 (B2) | 183.74 | 185.34 |
| `mlgym_houseprice` (CPU) | 5.059 | 6.794 (E4) | 15.18 | 20.38 |

- **A: keep 3 × the B1 baseline time.** No amendment. On the 4090, ogbn's E4 runs reach 16.95 s unless the 4090 is at
  least 1.29 × faster than the Ada on that edit, so G.1b would most likely STOP on ogbn at its first E4 run and the
  author would decide then.
- **B (recommended): 3 × the slowest executed census record of the node (baseline or declared edit), the same rule
  for all seven nodes.** The timeout stays a guard against hangs, not a filter on edits. Amends
  R1-TRACKG-PORT-DECISIONS (4) for the T1 table only; the G.4 pilot and the G.5 labels use the same basis, so the
  noise floor and the labels share it. The timing STOP still catches a 4090 that is much slower than the Ada.
- **C: as A, but a timeout is a divergent row, not a STOP** (the H200 design). ogbn's E4 would then give 92 divergent
  rows and could not be material, so the node's D21 verdict would reflect the timeout basis, not the noise; and it
  contradicts the task's STOP rule. Not recommended.
- **D: time each node once on the 4090 first** (B1 and E1–E4, one run each, minutes per node) and set the basis to 3 ×
  the slowest 4090 record. Removes the estimate, at the cost of a basis fixed after seeing the 4090. The natural
  fallback if B's timing STOP fires.

**Proposed row (B):**

> | R1-G1B-TIMEOUT | For the T1 table (G.1b, G.4, G.5) the per-run timeout is **3 × the slowest executed census record of the node** (baseline or declared edit; U4 census, RTX 6000 Ada), the same rule for every T1 node. Amends R1-TRACKG-PORT-DECISIONS (4) ("3 × the census baseline") for the T1 table; T0 is unchanged. On the RTX 4090 the census times are an estimate: a G.1b run that reaches the timeout is a STOP for the author, not a divergent row; in G.4 and G.5 a proposal's timeout remains its failure, and a baseline timeout STOPs the campaign. Basis: `docs/r1/proposals/T1_TASL_ROWS_DRAFT_20261121.md` §2 (per-node values). |

---

## 3. R1-T1-TASL-ENV — hosts and environments of the T1 table (in place of the image row; recommendation: A)

**Facts.** On H200 the table's environment was a container image (G1B-IMAGE). The TASL hosts run directly: no image,
so the row must fix what the image fixed. The census ran on Ada in uv environments built from the census freezes
(torch312 `d2e70fe4…`, jax312 `80a455c6…`, Python 3.12.16) under the harness isolation in a delegated user scope. The
Track X Stage A and the exams ran on TASL-7 with the exam `llama-server`:
`/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server`, sha256 `b70f4882…7d8b`, `version: 0.7.0-dev
(build 1, commit 620d222)` (`r1/scripts/configs/exam_portal.json`; RUNBOOK, Track X Stage A row), and the GGUF at
`/home/dowling/exam-x/models/gemma4_31b/`. Image v2's binary is the same llama.cpp commit built elsewhere (`f8d35fd3…`,
build 11669). TASL-2 and TASL-7 are exclusive
to the author's work; the author has no root on TASL-7.

- **A (recommended):**
  - **Hosts.** TASL-2 (G.1b, the G.4 and G.5 workers) and TASL-7 (G.1b; then the proposer server), each identified
    in the spec and the signed note by host name and its RTX 4090's full UUID; the driver version is recorded, not
    pinned.
  - **Environments.** On each host, the node environments are built with `uv` from the census freezes on Python
    3.12.16; at every job start `uv pip freeze` must equal the census freeze byte for byte (after normalisation), else
    STOP. A freeze that does not install on a host is a STOP (no substitute wheels).
  - **Code.** The harness checkout at the reviewed pin, clean; the paper repo at the launch commit.
  - **Isolation.** Non-root; Yama `ptrace_scope` ≥ 1; each job in a delegated user scope (`systemd-run --user
    --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`) with `AR_TEST_CGROUP_PARENT` set to it; the harness
    isolation host checks recorded per host (R1-T1-HOST-TASL's precondition).
  - **One card per job.** An exclusive `flock` on `~/r1_locks/gpu0.lock` for the job's life; no compute process of
    another owner on the card before or after each part.
  - **Proposer.** On TASL-7 the exam `llama-server` binary (sha256 `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`,
    `version: 0.7.0-dev (build 1, commit 620d222)`; checked at start, and its `/props` build checked by the worker), the pinned gemma4_31b GGUF (`2959c1b0…`), the exam
    settings of R1-T1-HOST-TASL, bound to TASL-7's Tailscale address.
  - **Data.** Each node's own `setup_command` on the host; the data manifest must equal the census value.
- **B: as A, but image v2's `llama-server` binary** (`f8d35fd3…`, build 11669, the same commit `620d2225c`; the H200
  G.4 and sweep-2 pin). Aligns the T1 server with the H200 plans, but the binary was built for the container and may
  not run on TASL-7 outside it (shared libraries; untested), and it is not the binary the proposer was examined with.
- **C: copy the Ada census environments to the TASL hosts.** uv environments are not relocatable across paths and
  driver stacks; not recommended.

**Proposed row (A):**

> | R1-T1-TASL-ENV | Hosts and environments of the T1 table on the TASL pair (R1-T1-HOST-TASL), in place of an image row. Hosts: TASL-2 (G.1b; G.4/G.5 workers) and TASL-7 (G.1b; proposer server), each identified by host name and the full UUID of its RTX 4090. Node environments built with uv from the census freezes (torch312, jax312; Python 3.12.16), equal to the freeze at every job start, else STOP. Harness at the reviewed pin, clean. Each job non-root, Yama ptrace_scope ≥ 1, in a delegated user scope (MemoryMax 8G, MemorySwapMax 0) as the census, holding the host's GPU lease (`~/r1_locks/gpu0.lock`) with no other compute process on the card. Proposer: the Track X exam `llama-server` binary on TASL-7 (sha256 `b70f4882…7d8b`, `version: 0.7.0-dev (build 1, commit 620d222)`, checked at start), the pinned gemma4_31b GGUF, the exam settings, on TASL-7's Tailscale address. Node data from each node's setup command, manifest equal to the census. Basis: `docs/r1/proposals/T1_TASL_ROWS_DRAFT_20261121.md` §3; `sweep2/t1_tasl/T1_TASL_PLAN.md`. |

---

## 4. What changes in the code when the author signs

Nothing in the logic. The operator copies the row ids into the spec authorities (`edit_count.authority`,
`timeout_decision.authority`, `host_decision.authority`); under option B of §1 the spec's `n_edits_per_node` becomes 5
after the kit change; under option A of §2 `timeout_decision.basis` becomes `census_baseline_x3`; under option D of §2
a reviewed spec change adds the measured 4090 values. The launch binding checks the rows on published `main`.
