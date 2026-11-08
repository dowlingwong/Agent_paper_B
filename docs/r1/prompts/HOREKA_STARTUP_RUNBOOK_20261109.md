# HoreKa 2 start-up runbook — HK0 to HK3 before the downtime (9–21 Nov 2026)

**Written 9 Nov 2026 by the chat session (Claude) at the author's request ("horeka准备工作你能不能也写成一个runbook，我让一个能ssh horeka的agent去一步步实验"); AI-assisted.** Not independently reviewed yet.

**What this is.** A day-by-day sequence for the **HoreKa agent** from today to the downtime. The rules come from `prompts/HOREKA_RUNBOOK_20261104.md` revision 3 (adopted as R1-HOREKA-RUNBOOK); read it first. Where this file is shorter, revision 3 governs. Where they conflict, STOP and report. Report to the author in **Chinese**; write files in **English**.

**What it covers.** Only the engineering phases, which do not need the main proposer: HK0 (queue facts), HK1 (environment), HK2 (ports and smoke tests), HK3 (census and noise floors). HK4 and later need X.7 (the Track X exam's pick) and are out of scope here.

---

## 0. Before anything touches HoreKa

### 0.1 What the author must give you (check each; STOP if one is missing)

| # | Item | Where it comes from |
|---|---|---|
| A | Decisions on the tool limits: freeze F, cutoff C, copy-back D; campaign accounting start; GPU-hour ceiling and STOP threshold; his availability for sessions on 20–21 Nov | A dated PLAN §10 row (proposed id `R1-HOREKA-LIMITS`). The values now in `r1/scripts/hk2/hk2_config.json` are proposals until that row exists |
| B | Confirmation that no other HoreKa session of his is open | Chat, before each session |
| C | An open master connection to `hk2` (`ssh -fN hk2`, with his password and OTP) | He runs it; you never open, stop or exit it |
| D | The one-time key setup of the session script (Setup A and B) | Done once by him; you only check that the key file exists (`ls -l`) |

Submission rights are already settled: **R1-HOREKA-AGENT-SUBMIT** ("agent 可以从 agent 节点提交 GPU 作业，包括续作业，同时等 NHR 回复。"). So revision 3 §0.3's interim rule (the author submits every `gpu-*` job himself) no longer applies. An NHR@KIT reply that restricts agent submission or LLM loops in batch jobs is an immediate STOP (revision 3 §5): create the STOP marker file and report.

### 0.2 Sessions, in one paragraph

NHR@KIT forbids AI agents on login nodes. You therefore work on a compute node of the `agent` partition, through a tunnel. A **session** is: you start the documented session script over the author's open master connection (it submits a 1-hour interactive job on a compute node); you add a port forward to his connection; you pass two gates (your config points at the tunnel; the job is running on that node); you work; then you end the session in order (cancel your session job, remove your forward, stop your local client). Follow `prompts/HOREKA_SCAN_PROMPT_20261104.md` revision 5.6, §1 steps 0–5, with the folder `…/_snapshots/hk2_session_<UTC date-time>/` in place of `horeka_scan_20261104` everywhere. One session at a time; at most 1 hour unless HK1 shows the script accepts a longer `--time`; each session at the author's request. Batch jobs keep running after a session ends.

### 0.3 Branches, reports, reviews

- Reports on `hk2-ops-20261109` from `mac-int-20261107`; ports on `hk2-trackg-20261109`; your own worktrees only.
- After each phase: `docs/r1/reports/HK2_<PHASE>_<date>.md`, a STATUS entry, a fresh independent reviewer until *accepted*, then a short Chinese message to the author saying what was done, the decisions needed and **when you need the next session and for how long**.
- Never delete evidence; retire into `_to_delete/`. Never touch a job or file you did not start.

## 1. Day plan

Dates are targets. Each "session" line is one 1-hour session the author opens for you.

| When | Phase | Needs a session? |
|---|---|---|
| 9–10 Nov | **S0** Mac-side preparation | No |
| 10 Nov | **Session 1**: HK0 facts, site checks, repositories | Yes |
| 10 Nov | Review of Session 1; submit switch enabled in a reviewed commit | No |
| 10–11 Nov | **Session 2**: J0 setup job and the USR1 test submitted | Yes |
| 11 Nov | **Session 3**: J0 results, GPU check; HK1 report | Yes |
| 11–16 Nov | **HK2** ports on the Mac; smoke jobs (Sessions 3–5) | Yes, about one per day |
| 13–19 Nov | **HK3** census and floors, node by node (batch, checked in sessions) | Yes, about one per day |
| 20 Nov 12:00 | **F**: no new submissions | — |
| 20 Nov 20:00 | **C**: every job has ended | — |
| 21 Nov 18:00 | **D**: copy-back and sealed copy done; report | Yes |
| 23 Nov – 4 Dec | Downtime | — |

## 2. S0 — Mac-side preparation (no HoreKa access)

1. Read revision 3 in full, the scan prompt rev 5.6 §1, `reports/HOREKA_QUEUE_20261104.md`, `reports/HOREKA_SCAN_20261104.md`, `prompts/TRACK_G_RUNBOOK.md`, and the M10 tools `r1/scripts/hk2/` with their tests.
2. Run the hk2 tool tests on the Mac (`r1/tests/hk2/`); record the result.
3. **HK0 desk part.** From the queue report: the 10 probe jobs are ids **120384–120393** (names `r1q_*`), all pending on 4 Nov 18:01 with `--deadline` about 7 Nov 17:26. Prepare the table you will fill in Session 1: for each job, did it start, when, how long it waited, and the GPU model it got. Draft the T_max and partition proposal rules: if no 1-GPU `gpu-h100` or `gpu-h200` job started within 24 h of submission, that is revision 3 HK0 step 4's STOP for the author.
4. **Pins.** Write down the pins J0 will use: paper commit, harness commit, llama.cpp commit and build flags (revision 3 §1 J0), and the modules. If any pin is undecided, list it as a question.
5. **Licence and availability (G.0.1)** for the candidate tasks of `TRACK_G_RUNBOOK.md` §1: autoresearch (fixed-step variant); MLGym light tasks (CIFAR-10, Fashion-MNIST, House Price, one MinAtar/MountainCar-type RL task); MLAgentBench light tasks (cifar10, imdb, ogbn-arxiv); the 1GC-7RC public datasets (TinyShakespeare, Forest Cover, ETTh1, AG News, ogbg-molhiv). Desk work only: repository, licence, dataset licences, download URL and size, whether it needs a container. Output: `reports/HK2_G01_LICENCES_<date>.md`, with a proposed port order (cheapest, cleanly licensed first; aim for 8 or more T1 candidates across at least 3 suites and 5 domains).
6. **Manifests.** Prepare the J0 manifest and its `hk2_submit.py --dry-run` output (committed), and a 15-minute `dev-cpu` USR1 test job script (revision 3 §1 units).
7. Ask the author for items A–D of §0.1 and for Session 1.

**Done when** the S0 report is reviewed and the author has items A–D.

## 3. Session 1 — HK0 facts, site checks, repositories

All commands on the compute node, through `nodessh`. Nothing is submitted in this session.

1. **Probe history:** `sacct -X -u $USER -S 2026-11-04 -n -P -o JobName,JobID,Partition,State,Submit,Start,End,Elapsed,AllocTRES | grep r1q_`, and `ls -l ~/r1_queue_20261104/; cat ~/r1_queue_20261104/*.out` for jobs that ran (GPU model and memory from `nvidia-smi`). Fill in the S0 table.
2. `date +%Z`; `command -v start-vscode-remote-ssh.sh`, then read the script: does it accept a longer `--time`?
3. Site facts the submit tool relies on: which `squeue`/`sacct` fields are visible under `PrivateData`, whether `sacct` shows the probe jobs' elapsed time (the accounting the budget guard reads), and where the shared lock file of `hk2_submit.py` will live.
4. Create the bare repositories under `/hfs2/data/project/hk-project-p0027888/ka_ir7683/r1/git/`, push the pinned commits from the Mac with `nodessh-raw` (revision 3 §0.2), check out detached under `…/r1/work/<repo>@<short sha>/`.
5. `module avail` for CUDA 12.9.1 and GCC 14.3.0; record `rsync --version` and `git --version` on the Mac.
6. End the session in order.

**After Session 1 (Mac):**
- `HK2_HK0_<date>.md`: the probe table and the T_max / GPU-model proposal. Review, then send to the author; he fixes them in row `R1-HOREKA-TMAX`.
- A fresh reviewer checks the site facts of steps 2–3 against what `hk2_submit.py` assumes. Only after that review, enable `real_submission_enabled` in a reviewed commit (its config status already reads "enable only at HK1 after review") and push that checkout to HoreKa in the next session.

## 4. Sessions 2 and 3 — HK1 jobs

**Session 2.**
1. Push the reviewed checkout with the switch enabled.
2. Submit **J0 setup** on `cpu` (16 cores, ≤ 2 h) through `hk2_submit.py`: venv from pinned wheels, the tested download URLs, llama.cpp built with `-DGGML_NATIVE=OFF -DCMAKE_CUDA_ARCHITECTURES=90`.
3. Submit the **USR1 test** on `dev-cpu` (`--time=00:15:00`, `--signal=B:USR1@600`, the background-runner pattern of revision 3 §1): the stand-in runner must move its open unit to `results/_interrupted/<jobid>/` and exit cleanly.
4. Record both job ids in the ledger; end the session. The jobs run on.

**Session 3.**
1. J0 and USR1 results: logs, hashes, the built llama.cpp version string; any failure is a STOP with the log.
2. **GPU check** on `dev-gpu-h100` (1 GPU, ≤ 30 min): `nvidia-smi`; the built llama-server starts with a small model the author names; whether `/props` reports the model path (if not, the runner checks `/proc/<pid>/cmdline`).
3. Self-submission (a job submitting its own continuation) is **not** tested here; revision 3 HK1 step 6 defers it.
4. End the session. Write `HK2_HK1_<date>.md`; review until accepted.

## 5. HK2 — ports and smoke tests (11–16 Nov)

**Needs** the Mac agent's port kit and diff support at a reviewed commit (`reports/M10_PORTKIT_HANDOFF_<date>.md`; Mac overnight runbook of 9 Nov, Task 2). Until it arrives, do G.0.1 and data preparation scripts only; do not invent your own template.

Per task, in the S0 port order, on `hk2-trackg-20261109`, all coding on the Mac:
1. Data preparation script; fixed-step wrapper; metric parser with the divergence class; `NodeSpec`; resource limits; deterministic settings and fixed worker counts; **3–5 representative edits declared as diffs and committed with a hash before any measurement**.
2. A fresh reviewer reviews the port.
3. In a session: submit the **J1 smoke** job on `dev-gpu-h100` (≤ 1 h, one at a time): one fixed-step run with a stub manager, and a frozen-path edit that must be refused. Record wall time and peak VRAM (this is also G.0.2's raw cost).
4. Done per task when scope enforcement refused the frozen-path edit and the smoke manifest is complete.

Batch several smoke jobs per session where the one-at-a-time `dev` rule allows; otherwise use `gpu-h100` with ≤ 1 h.

## 6. HK3 — census and noise floors (13–19 Nov)

Per ported task, in revision 3's order, as `gpu-h100` 1-GPU jobs within the probed shape (`-c ≤ 32`, `--mem ≤ 180G`), each with `--deadline` = C and `--signal=B:USR1@600`:
1. Raw cost at the fixed step budget.
2. **Determinism:** the same seed in two jobs on two different compute nodes, one under load (k = 4); compare bitwise.
3. **Concurrency:** k = 1, 2, 4 runs per GPU; throughput and identity at each k.
4. **Co-location:** baseline × 3 seeds beside an active llama-server load, compared bitwise with the same seeds alone.
5. **STOP for the author:** he fixes k, the audit placement and whether campaigns co-locate the proposer.
6. **Noise floor** at that placement: seeds 8001–8010 × (the declared edits + baseline); spread over ≥ 3 jobs if step 2 failed. Report σ̂, the largest |z|, the excess kurtosis.
7. D21 verdict per node.

**Output:** `reports/TRACKG_CENSUS_<date>.md`, one row per candidate, the screening funnel per suite, and a GPU-hour projection for HK4–HK7 at K = 6 and K = 10.

**Rough cost of HK1–HK3:** J0 and checks about 2 GPU-h; smoke about 0.5 GPU-h per task; census and floors about 2–4 GPU-h per task. For 10 tasks, roughly 30–50 GPU-h of the ceiling. Keep the ledger `results/r1/trackg/hk2/gpu_ledger.csv` (revision 3 §0.4).

## 7. The freeze (20–21 Nov)

- From F (20 Nov 12:00) the submit tool refuses every submission; do not try to work around it.
- Every job already carries `--deadline=2026-11-20T20:00:00`; jobs that cannot finish by C never start.
- Between C and D (21 Nov 18:00): copy `engineering/` back to `results/r1/trackg/hk2/` on the Mac, make the sealed copy of any `evidence/` (there should be none in these phases), verify `SHA256SUMS`, report.
- After the downtime (from about 5 Dec): check your own state first (`squeue -u`, `sacct -u` since 20 Nov, the `$PROJECT` tree and checksums), resume nothing automatically, report, wait for the author.

## 8. STOPs

Everything in revision 3 §5, plus: a missing item of §0.1; the port kit not reviewed when HK2 would start; any job queued more than 48 h without starting (report it with `squeue` reasons and ask whether to move to `gpu-h200` or shrink the scope); the ledger passing 100 GPU-h before HK3 ends.
