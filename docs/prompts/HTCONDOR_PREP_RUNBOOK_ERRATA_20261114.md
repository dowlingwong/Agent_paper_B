# ERRATA and operating notes — ETP HTCondor preparation, night of 13/14 Nov 2026

**Status.** Written by the cluster agent after the pre-execution review `docs/r1/reviews/HTCONDOR_PREP_RUNBOOK_REVIEW_20261114.md` (`VERDICT: NOT ACCEPTED`, 2 BLOCKING + 5 MAJOR + 17 MINOR/NIT). The reviewed runbook text is **not modified** (provenance: `69b3576b`); where this file and the runbook differ, **this file is the operative procedure**. Execution = runbook + this errata, and the same fresh reviewer must accept the combination before any cluster action. The review is `ACCEPTED AS THE REVIEW` by the Lead; its BLOCKING/MAJOR fixes are applied below, as its own verdict section requires.

**Applies from:** 14 Nov 2026 00:00 CET. **Hard stop:** 05:30 CET (VPN-dependent work), per runbook L229. Author asleep; open questions go to `docs/r1/reports/HTCONDOR_QUESTIONS_20261114.md`, never wait.

---

## A. Fixes that make the BLOCKING/MAJOR findings executable

### A1 (F1, F17, F20) — W2 exact invocation and STOP semantics

The runbook §5 line is replaced by this procedure. The script's own CLI is `python -m r1.scripts.w2_execute_all_identity_check <ledgers…> --runs-total W` (argparse `--runs-total` is required; the script imports `r1.c3.features` and `r1.c3.analysis_guard`, so it must run as a module from the repository root, not as a script path).

1. **Checkout (clean, detached):**
   `git -C /work/dwong/htcondor_prep_20261114/w2 clone --no-checkout <local bare or /ceph/dwong git dir of Agent_paper_B>` then fetch `origin/mac-w2-budget-20261109` (`0b62fb03df5480faf558cddd8f715cbb5310416e`) and `git checkout --detach 0b62fb03…`. Read-only: no commit, no branch, no worktree.
2. **Interpreter:** use a Python environment that has the r1 dependencies. Discover read-only in this order and record `python -VV` + the environment path in the W2 log: (i) the sweep-1 harness venv recorded by the deepthought sweep manifests; (ii) any `*/venv/bin/python` under `/ceph/dwong` or `/work/dwong` whose `python -c "import numpy, sklearn"` succeeds; (iii) the system `python3` only if (i)–(ii) absent, and then record the missing-dependency risk. No package installation.
3. **W:** `W = 20`, from `r1/scripts/configs/c3_sweep_deepthought.json` (`"runs": 20`, SHA-256 `2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b`) — not from any label table. Command includes `--runs-total 20`.
4. **Inputs (read-only):** the sweep-1 output directories named by the deepthought sweep manifests / `docs/r1/authorizations/c3_sweep1_20261027.md`; glob exactly `**/provenance/ledgers/roots/*/root_trials.jsonl` and `root_trials.jsonl.gz` (both memory modes). Record the directory list and the count of ledgers before running.
5. **Exact run:** `cd <checkout> && "$PY" -m r1.scripts.w2_execute_all_identity_check <ledger…> --runs-total 20`, capture exit code and stdout JSON verbatim to `w2/w2_check.<UTC>.json`.
6. **Semantics (start message: 如有差异 STOP):** exit **0** `IDENTICAL` → record; exit **3** `STOP_DIFFERENCE` → **STOP the W2 part immediately**, write the summary JSON into the report and question list, hand it to the author, do **not** adopt, recompute or edit anything; exit **2** `BAD_INPUT` → STOP and report. Never open a label table, seed-labelled analysis output, sealed path or metric field.
7. **§0.2 carve-out (F20):** this field-limited read (`budget_index`, `decision`, `worker_mode`, `extra.control` only) is the **only** Paper B data read on the cluster tonight, exactly as the W2 start-message line authorizes.

### A2 (F2) — I2 commits corrected

I2 uses the commits the reviewed command itself binds and asserts: **paper `60ecf1dae299ee424aa1bdfe078eab02a881b87e`** and **harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`**. Source: `docs/r1/proposals/B1_TASL7_WORKER_ONCE_60EC_20261107.sh` on `origin/mac-b1-20261107`, SHA-256 `1be4ae335cd8e22d123b3253617aa1612fcb0f7ea7076900addc5d0cacf1a5b3`; reviews `docs/r1/reviews/B1_TASL7_REAL_WORKER_RESULT_REVIEW_20261107.md` and `B1_TASL7_WORKER_ONCE_60EC_REVIEW_20261107.md`. **`e5dc8c67…` is dropped** (unreachable from every fetched ref; not used). Before writing the I2 job: confirm both commits are present in the deepthought clone of the paper repo (I2 needs a harness clone too — the harness is the separate public repo `dowlingwong/autoresearch_harness`; fetch `a3fedbb` if absent, record the source). If either commit cannot be obtained tonight, **I2 is not executed** and goes to the question list — it is not written against other commits.

### A3 (F3, F21) — image delivery defined; I1–I4 explicitly deferred unless a pullable image exists

1. **First a gate, before any image work:** `docker info` on deepthought (not a credential read). If the daemon is unreachable, §3 stops at the gate; record it; the image becomes a question, and the night continues with §1/§2/§4.1.
2. **Build and test locally only:** build tag `r1-htc:20261114-<Dockerfile sha short>`; smoke it with `docker run <tag> …`; `docker save` to `/work/dwong/htcondor_prep_20261114/images/r1-htc-20261114.tar` and record its SHA-256. That archive is **not** a pullable image reference; it is kept for tomorrow.
3. **Registry:** none is documented in the repo and the only login record is `~/.docker/config.json`, a credential file that §0.4 B forbids reading. **No `docker login`, no credential read, no registry guess.** A registry/namespace and the pullable-image path become question Q3.
4. **Consequence, stated now (F3):** because no pullable image can be produced tonight, **I1–I4 are not submitted tonight**. The report records "I1–I4 not executed: no pullable image / registry unknown" and the local build+smoke result instead. This is the explicit fallback the reviewer required, not a late discovery. The pinned image on the batch system remains a goal for the next window.

### A4 (F4, F23) — night timetable, priority and cut-offs (CET)

Priority when time is short: **W2 + pool facts > probe wave 1 > moves > image build > I-probes**. Never trade the 05:30 stop for a lower priority item.

| Window | Work | Hard cut-off |
|---|---|---|
| 00:00–00:20 | ssh master; W2 (A1); §2 pool facts | W2 result recorded even if later steps slip |
| 00:20–00:50 | §1.1 inventory, §1.2 pinned paths, MOVE_PLAN draft; §4.1 JDL dry-runs written | inventory capped at 25 min; if not done, inventory the largest entries only and record the cap |
| 00:30–00:50 | fresh review of the 7 JDLs (one unit) | review accepted before any submission |
| 00:50–01:10 | submit P1, read result, then P2–P7 | all wave-1 jobs submitted by 01:15 |
| 01:00–02:30 | MOVE_PLAN review, then moves (one entry at a time); image build in the background only if the docker gate passes | **stop starting new moves at 03:30**; image build aborted at 02:30 if not finished |
| 02:50–03:10 | wave-2 resubmission P1, P3, P4, P6 (+3 h sample) | P6 dropped if the GPU-hour register is above 3.5 GPU-h |
| 03:00–04:00 | §4.4 I-probes **only if** a pullable image exists (A3; normally not tonight) | not started after 04:00 |
| 04:00–04:40 | report draft + question list + TSVs committed | report exists by 04:40 |
| 04:40–05:10 | fresh review of the report; fixes | reviewer verdict by 05:15 |
| 05:10–05:25 | final commit, push or bundle + `READY.txt`, SHA list | done by 05:25 |
| 05:25–05:30 | short Chinese message; **no further VPN-dependent command** | 05:30 hard stop |

**+6 h wave (runbook §4.3): cannot happen before 05:30 — dropped tonight and said so in the report.** The queue-time goal is still covered by wave 1 (all resource classes) and the +3 h sample.

**Deliverables to commit (F23):** `docs/r1/reports/HTCONDOR_PREP_20261114.md`, `docs/r1/reports/HTCONDOR_QUESTIONS_20261114.md`, and under `docs/r1/reports/htcondor_prep_20261114/`: `inventory.tsv`, `MOVE_PLAN.md`, `MOVE_LOG.tsv`, `POOL_FACTS.md`, `pinned_paths.txt`, `queue_times.tsv`, `gpu_register.tsv`, `w2/` summary JSON, image build log + image id + archive SHA, and the review files. Bundle + `READY.txt` under `~/Documents/agent_paper_B/Claude outputs/` if push is impossible.

### A5 (F5, F9) — disk gate wired into the move loop; no-deletion on failure

Before **each** entry: record `du -sb` of the source, `df -h` and `quota -s` of `/work`; require **post-copy free ≥ max(15 % of the `/work` quota, entry bytes + 5 GiB)**; write the numbers into `MOVE_LOG.tsv`; if the floor would be breached, **stop the move programme** and report (runbook §0.5 STOP). `mkdir -p /ceph/dwong/_to_delete` before the first move; before `mv`/`ln -s` check the destination does not exist and use a unique suffix (`…moved_20261114_<n>`), abort the entry otherwise. **Failed verification:** leave the source untouched, move the partial `/work` copy to `/work/dwong/_to_delete/<X>.failed_<UTC>` (a move, never a delete), record it, go to the next entry. Nothing is ever `rm`'d.

### A6 (F6, F8) — GPU-hour and 10-job accounting

Maintain `gpu_register.tsv` from the job event logs / `condor_history -af RemoteWallClockTime ExitCode`: one row per job with `gpu_hours = run_s/3600`, **restarts and evictions count**. Stop submitting GPU probes at **5.0 GPU-h** (margin under the author's 6 GPU-h cap); wave-1 P4–P7 are mandatory, the +3 h resubmissions are droppable, I4 (if ever run) is droppable — never exceed the register. Before any resubmission, ensure **≤ 6 of our own jobs are active** (`condor_q`); only our own idle duplicates may be removed (`condor_rm`), and they are recorded as `>4h (removed)` in `queue_times.tsv`. `condor_rm` is used only on tonight's own job IDs.

### A7 (F7, F10–F16, F18, F19, F22, F24–F26) — corrected details

- **F10:** run the in-use process check on **every login host where `/ceph/dwong` is mounted** that is reachable from deepthought's SSH config (`deepthought`, `portal1`, `bms1`, `bms3`; `bms2` unverified). If a host is unreachable, record "not checked: <host>" in `MOVE_LOG.tsv`. `condor_q` is pool-wide.
- **F11:** pinned-path grep adds the sweep-1 authorization/manifests and `origin/dt-sweep1-20261026`; the deepthought sweep manifests are the authoritative pinned-path list (read-only).
- **F12:** P3 stays "remote CPU, best effort": it carries `+RemoteJob = True` only; record the actual site and report the class **only if** a remote execution is observed.
- **F13:** finished rows take `ExitCode` from `condor_history`; queued/held/removed rows take `JobStatus`/`HoldReason` from `condor_q`; the row records which source was used.
- **F14:** the Track P env uses the freeze pins (`torch==2.14.1+cpu` in the freeze) with the matching CUDA build if it exists; the exact CUDA wheel is recorded as `proposed:`; R1-ENV-PIN's `2.6.0+cu124` is **not** mixed in.
- **F15:** llama.cpp build flags from `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md` §2.1 and `TRACKS_HOST_FACTS_20261030` §2 (`-DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release`), with `CMAKE_CUDA_ARCHITECTURES="70;80;89;90"`; CUDA 12.2 fallback tag is `12.2.2-cudnn8-devel-rockylinux9`.
- **F16:** accounting-group fallback is the documented `belle`, or no group; `cms.higgs` is unverified and becomes an author question. Author's own past jobs (`condor_history -limit 50 dwong -af AcctGroup AccountingGroup`) still come first.
- **F18:** §2 adds a read-only `/ceph/srv/dwong` discovery and records the XRootD endpoint actually reachable; I3 (if ever run) verifies the GGUF SHA-256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` before loading.
- **F19:** pre-flight `tailscale status` if a CLI exists on the Mac (record result; never kill Tailscale processes) and record VPN-up/VPN-down times in the report.
- **F22:** `condor_userprio -allusers` (and `-long` if needed); record if `-all` would be rejected.
- **F24:** `bms2` unverified — author question only; submission works from any one host.
- **F25:** review paths prefixed `docs/r1/reviews/`.
- **F26:** reading non-secret `Host`/`HostName`/`User`/`Port` lines in `~/.ssh/config` is allowed; key files and `~/.config/r1/secrets.env` stay forbidden.

---

## B. §0.3 fact-status ledger (F7, F16, and the review's §3)

The official ETP wiki, the tutorial GitLab and the newer Indico tutorial are **login/access gated from this machine**; the report says so. Operative fact policy: the reviewer's ledger in `docs/r1/reviews/HTCONDOR_PREP_RUNBOOK_REVIEW_20261114.md` §3 is authoritative tonight.

- **VERIFIED from reachable public sources** (2022 ETP Batch System Tutorial `indico.kit.edu/event/2951`; HEPiX 2024 KIT deck): submission/monitoring tools; `Universe=docker` + `docker_image` + `mschnepf/slc7-condocker` and "any image the pool can pull"; `RequestCPUs/RequestMemory/request_disk/+RequestWalltime`; `+RemoteJob` semantics (remote jobs get no `/home`/`/work`/`/ceph`); `/ceph/srv` readable from ETP and TOpAS; CloudSite ClassAd; CUDA 12.4 needs driver ≥ 550.54.14; the `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` tag exists.
- **UNVERIFIED tonight — treat as questions, not facts:** `ProvidesETPResources` / `ProvidesEtpCeph` exact ClassAd names; `request_GPUs` "up to 8"; `GPUs_DeviceName` selection and the exact device strings; NEMO2 L40S/H200 counts and the `CloudSite` string; `NVIDIA_VISIBLE_DEVICES` short-UUID warning; `+RequestGPUMemoryMB`; the 6-start hold rule; multi-core optimisation; the 100 MB transfer limit; `bms2`; the other accounting-group names.
- **CONTRADICTED by reachable public source — question list:** XRootD endpoint (public deck: `root://ceph-node-a.etp.kit.edu`; runbook says `ceph-node-j`); "the tutorial uses `cms.higgs`" (both public sources use `belle`). **POSSIBLE MISMATCH:** V100S count 16 (runbook) vs 24 (HEPiX 2024).
- None of these is silently adopted; every mismatch becomes a numbered question with a paste-ready answer in §7 of the report.

---

## C. Explicitly not done tonight (so the report can state it)

1. I1–I4 probes: **not submitted** without a pullable image (A3).
2. §4.3 +6 h resubmission wave: **cannot fit before 05:30** (A4).
3. Registry push / `docker login`: **never** without the author (A3).
4. No Paper B experiment, label, sweep, exam or model work; the only Paper B read is W2 (A1.7).
5. No deletion of anything, anywhere; moved originals become `_to_delete/` + symlink (A5).

---

## D. Acceptance rule

The runbook's own opening rule stands: execution begins only after a fresh independent reviewer *accepts* the review of the runbook. This errata is submitted to the same reviewer for re-check; if it is accepted, execution of runbook + errata may begin immediately (the night has already started, so the timetable in A4 is applied with the clock shifted, keeping every cut-off relative to 05:30).
