# HoreKa 2 start-up runbook — HK0 to HK3 before the downtime (9–21 Nov 2026)

**Written 9 Nov 2026 by the chat session (Claude); AI-assisted.** Not independently reviewed yet.

**What this is.** A day-by-day sequence for the **HoreKa agent**, from today to the downtime. It covers only the engineering phases, which do not need the main proposer: HK0 (queue facts), HK1 (environment), HK2 (ports and smoke tests), HK3 (census and noise floors). HK4 and later need X.7 (the Track X exam's pick) and are out of scope.

**Relation to revision 3.** `prompts/HOREKA_RUNBOOK_20261104.md` revision 3 still governs pins, seeds, placement, the GPU-hour ledger, job design (§1), the downtime times and the review loop. **This file replaces its access procedure:** you do not use the `agent`-partition session, the tunnel or the scan prompt's wrappers. You work from the Mac over the author's normal SSH connection, and every job you run is a scripted batch job. Where the two files otherwise conflict, STOP and report.

Report to the author in **Chinese**; write files in **English**.

---

## 0. Access and ground rules

### 0.1 How you reach HoreKa

- The author opens one master connection on the Mac: `ssh -fN hk2` (password + OTP). His `~/.ssh/config` keeps it alive for 8 h. Every command of yours goes over it as `ssh -o BatchMode=yes hk2 '<command>'`. Never open, stop or exit the master; if it is gone, ask him to reopen it.
- **On the login node, run only light commands:** `git` / `rsync` transfers, `sbatch` through `hk2_submit.py`, `squeue` / `sacct` / `ls` / `cat` / `sha256sum` on small files, `module avail`. The submit and status tools already space their Slurm queries at least 60 s apart.
- **Everything heavy runs inside a batch job:** building, installing, downloading datasets or models, any training, any test. Never on the login node.
- Code transfer: create bare repositories under `/hfs2/data/project/hk-project-p0027888/ka_ir7683/r1/git/`, push from the Mac (`git push hk2:/hfs2/…/r1/git/<repo>.git <commit>:refs/heads/<branch>`), check out **detached** at the pinned commits under `…/r1/work/<repo>@<short sha>/`. Gated artefacts are fetched on the Mac and sent with `rsync -e ssh --timeout=300`. No token is ever placed on HoreKa.

### 0.2 What you need from the author (STOP if missing)

| # | Item |
|---|---|
| A | The tool limits confirmed: freeze F, cutoff C, copy-back D; the date GPU-hour accounting starts; the GPU-hour ceiling and STOP threshold; whether he is reachable on 20–21 Nov. Proposed values are in `r1/scripts/hk2/hk2_config.json`; change each key's `status` to the confirmed value in a reviewed commit |
| B | The master connection open when you need HoreKa |
| C | After HK0: the maximum job length T_max and the GPU model (H100 or H200) |
| D | At HK3 step 5: k runs per GPU, the audit placement, and whether campaigns share the GPU with the proposer |

### 0.3 Rules

- **Never touch what you did not start:** no cancel, signal or edit of another user's job or file, or a job the author started. Record every job id you submit; cancel only those.
- **Pins:** jobs run the commits and artefacts of the RUNBOOK §5 pin table; a mismatch is a STOP.
- **Seeds:** noise floors use 8001–8010; C3 seeds 7001–7010 and exam seeds 9001+ are not used in these phases.
- **Submission** only through `hk2_submit.py`, with its guards (budget, F, C, 90 outstanding jobs). Its `real_submission_enabled` switch is turned on once, in a reviewed commit, after the HK1 site checks of §3.
- **Branches:** reports on `hk2-ops-20261109` (from `mac-int-20261107`), ports on `hk2-trackg-20261109`; your own worktrees only; never push `main`, `r1` or `exam-x-*`; never force-push.
- **Deletions:** never delete evidence; retire into `_to_delete/` and say so.
- **Review loop:** at the end of each phase, a **fresh** reviewer gets the phase goal, this file, revision 3, the pins and your outputs (not your conclusions), writes `docs/r1/reviews/HK2_<PHASE>_REVIEW_<date>.md`, and re-checks until *accepted*. You never accept your own phase.
- **Reports:** after each phase, `docs/r1/reports/HK2_<PHASE>_<date>.md`, a STATUS entry, and a short Chinese message: what was done, commits, checks, review verdict, decisions needed, and when you next need the master connection.

## 1. Day plan (targets)

| When | Phase |
|---|---|
| 9–10 Nov | **S0** Mac-side preparation |
| 10 Nov | **HK0** queue facts; **HK1** site checks and code transfer |
| 10–11 Nov | **HK1** jobs: J0 setup, USR1 test, GPU check |
| 11–16 Nov | **HK2** ports on the Mac; one smoke job per port |
| 13–19 Nov | **HK3** census and noise floors, task by task |
| 20 Nov 12:00 | **F**: no new submissions |
| 20 Nov 20:00 | **C**: every job has ended |
| 21 Nov 18:00 | **D**: copy-back done; report |
| 23 Nov – 4 Dec | Downtime |

## 2. S0 — Mac-side preparation (no HoreKa access)

1. Read revision 3 (all but its §0.2 session procedure), `reports/HOREKA_QUEUE_20261104.md`, `reports/HOREKA_SCAN_20261104.md`, `prompts/TRACK_G_RUNBOOK.md`, and the tools in `r1/scripts/hk2/` with their tests. Run `r1/tests/hk2/` on the Mac and record the result.
2. **HK0 table.** The 10 probe jobs are ids **120384–120393** (names `r1q_*`), pending on 4 Nov 18:01, with `--deadline` about 7 Nov 17:26. Prepare a table: did each start, when, how long it waited, which GPU it got.
3. **Pins.** List the pins J0 will use (paper commit, harness commit, llama.cpp commit and build flags of revision 3 §1 J0, modules). Any undecided pin goes on the question list.
4. **Licences and availability (G.0.1)** for the candidates of `TRACK_G_RUNBOOK.md` §1: autoresearch (fixed-step variant); MLGym light tasks (CIFAR-10, Fashion-MNIST, House Price, one MinAtar/MountainCar-type RL task); MLAgentBench light tasks (cifar10, imdb, ogbn-arxiv); the 1GC-7RC public datasets (TinyShakespeare, Forest Cover, ETTh1, AG News, ogbg-molhiv). Repository, licence, dataset licences, download URL and size, container needed or not. Output `reports/HK2_G01_LICENCES_<date>.md` with a proposed port order: cheapest and cleanly licensed first, aiming at 8 or more T1 candidates over at least 3 suites and 5 domains.
5. **Job scripts and manifests:** J0 setup (revision 3 §1), the 15-minute USR1 test (`dev-cpu`), the GPU check (`dev-gpu-h100`); each with its committed `hk2_submit.py --dry-run` output.
6. Ask the author for item A and for the master connection.

## 3. HK0 and HK1 — first contact (10 Nov)

Over `ssh hk2`, light commands only:
1. `sacct -X -u $USER -S 2026-11-04 -n -P -o JobName,JobID,Partition,State,Submit,Start,End,Elapsed,AllocTRES | grep r1q_`; and `ls -l ~/r1_queue_20261104/; cat ~/r1_queue_20261104/*.out` for any job that ran. Fill in the HK0 table.
2. `date +%Z`; which `squeue` / `sacct` fields are visible to this account; whether `sacct` reports elapsed time for the probe jobs (the budget guard reads it); where the submit tool's lock file will live under `$PROJECT`.
3. `module avail` for CUDA 12.9.1 and GCC 14.3.0; record `git --version` and `rsync --version` on the Mac.
4. Create the bare repositories, push the pins, check out detached (§0.1).

**Then on the Mac:**
- `HK2_HK0_<date>.md`: the probe table, and a T_max / partition proposal. If no 1-GPU `gpu-h100` or `gpu-h200` job started within 24 h of submission, say so plainly: the author then chooses between accepting long waits, H200, the Ada fallback, or a smaller scope. Review; send to the author (item C).
- A fresh reviewer checks the site facts of step 2 against what `hk2_submit.py` assumes. After *accepted*, turn on `real_submission_enabled` in a reviewed commit and push that checkout.

## 4. HK1 — setup jobs (10–11 Nov)

1. Submit **J0** on `cpu` (16 cores, ≤ 2 h): venv from pinned wheels, the tested download URLs, llama.cpp built with `-DGGML_NATIVE=OFF -DCMAKE_CUDA_ARCHITECTURES=90`, hashes of everything installed.
2. Submit the **USR1 test** on `dev-cpu` (`--time=00:15:00`, `--signal=B:USR1@600`, the background-runner pattern of revision 3 §1): the stand-in runner must move its open unit to `results/_interrupted/<jobid>/` and exit cleanly.
3. When J0 has finished: the **GPU check** on `dev-gpu-h100` (1 GPU, ≤ 30 min): `nvidia-smi`; the built llama-server starts with a small model the author names; whether `/props` reports the model path (if not, the runner reads `/proc/<pid>/cmdline`).
4. Read results with `cat` / `sha256sum` on the output files; any failure is a STOP with the log.
5. A job submitting its own continuation is not tested in this phase.

**Done when** `HK2_HK1_<date>.md` is accepted.

## 5. HK2 — ports and smoke tests (11–16 Nov)

**Needs** the Mac agent's port kit and diff support at a reviewed commit (`reports/M10_PORTKIT_HANDOFF_<date>.md`, from the Mac overnight runbook of 9 Nov, Task 2). Until it arrives, do G.0.1 and data-preparation scripts only; do not build your own template.

Per task, in the S0 port order, coding on the Mac on `hk2-trackg-20261109`:
1. Data preparation; fixed-step wrapper; metric parser with the divergence class; `NodeSpec`; resource limits; deterministic settings and fixed worker counts; **3–5 representative edits declared as diffs and committed with a hash before any measurement**.
2. A fresh reviewer reviews the port.
3. Submit the **J1 smoke** job on `dev-gpu-h100` (≤ 1 h; the dev QoS allows one job at a time, so queue them one after another, or use `gpu-h100` with ≤ 1 h): one fixed-step run with a stub manager, and a frozen-path edit that must be refused. Record wall time and peak VRAM (this is also the raw cost of G.0.2).
4. Done per task when the frozen-path edit was refused and the smoke manifest is complete.

## 6. HK3 — census and noise floors (13–19 Nov)

Per ported task, in this order, as 1-GPU `gpu-h100` jobs within `-c ≤ 32`, `--mem ≤ 180G`, each with `--deadline` = C and `--signal=B:USR1@600`:
1. Raw cost at the fixed step budget.
2. **Determinism:** the same seed in two jobs on two different compute nodes, one under load (k = 4); compare outputs bitwise.
3. **Concurrency:** k = 1, 2, 4 runs per GPU; throughput, and identity at each k.
4. **Co-location:** baseline × 3 seeds beside an active llama-server, compared bitwise with the same seeds alone.
5. **STOP for the author** (item D).
6. **Noise floor** at that placement: seeds 8001–8010 × (the declared edits + baseline); spread over ≥ 3 jobs on different nodes if step 2 failed. Report σ̂, the largest |z|, the excess kurtosis.
7. D21 verdict per task.

**Output:** `reports/TRACKG_CENSUS_<date>.md`: one row per candidate, the screening funnel per suite, and a GPU-hour projection for HK4–HK7 at K = 6 and K = 10.

**Rough cost of HK1–HK3:** about 2 GPU-h for setup and checks; about 0.5 GPU-h per smoke test; about 2–4 GPU-h per task for census and floors. For 10 tasks, roughly 30–50 GPU-h. Keep the ledger `results/r1/trackg/hk2/gpu_ledger.csv` (revision 3 §0.4).

## 7. The freeze (20–21 Nov)

- From F (20 Nov 12:00) the submit tool refuses every submission; do not work around it.
- Every job carries `--deadline=2026-11-20T20:00:00`; a job that cannot finish by C never starts.
- Between C and D (21 Nov 18:00): copy `engineering/` back to `results/r1/trackg/hk2/` on the Mac, verify `SHA256SUMS`, report.
- After the downtime (from about 5 Dec): check your own state first (`squeue -u`, `sacct -u` since 20 Nov, the `$PROJECT` tree and its checksums), resume nothing automatically, report, wait for the author.

## 8. STOPs

- A missing item of §0.2.
- A pin mismatch, a scope violation, or a frozen-path edit that is not refused.
- A foreign process on a GPU allocated to you.
- A job queued more than 48 h without starting: report it with the `squeue` reason, and ask whether to move to `gpu-h200` or shrink the scope.
- The ledger passing 100 GPU-h before HK3 ends; the budget guard refusing a job.
- Any message from NHR@KIT or Slurm about this account, or a blocked job: stop submitting and report to the author.
- Anything this file and revision 3 do not cover.
