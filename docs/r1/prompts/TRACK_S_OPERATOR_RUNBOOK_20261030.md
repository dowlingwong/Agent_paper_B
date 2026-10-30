# Track S — operator runbook for TASL-2 (zhixu portal) and TASL-7 (revision 3.3)

**Written 30 Oct 2026 by the chat session (Claude) at the author's request; AI-assisted.** One operator agent (Claude Code), started by the author on the Mac with SSH access to both hosts, carries out this runbook phase by phase. Every phase ends with a **STOP**, an independent review and, where marked, an author decision. Do not skip a STOP.

Revision 2 addressed the independent review `docs/r1/reviews/TRACKS_OPERATOR_RUNBOOK_REVIEW_20261030.md` (REVISE: 5 BLOCKING, 8 MAJOR, 7 MINOR); the code was extended for it in paper commit `9bb64ba`. Revision 3 addresses that reviewer's re-check of revision 2 (not accepted: 2 BLOCKING quoting bugs, 2 MAJOR, 9 MINOR); it changes only this runbook. The mapping is in §12.

**Authority.** If anything below conflicts with these, they win; stop and report.
- PLAN §10: R1-TRACKS-HOST, R1-TRACKS-HOST-2, R1-TRACKS-ADOPT, R1-TRACKS-S02, R1-TRACKS-FRAMING, R1-REPO-ACCESS, R1-INFER-LLAMACPP, R1-DT-PIN, R1-EXAM-TRANSFER, R1-PORTAL-SCHEDULE, R1-TASL7-TRACKP and R1-COMPUTE.
- The design: `docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`, revision 7.4 ("design §n").
- The code: paper branch `trackS-20261029` at **`9bb64ba`** and harness `trackS-20261029` at **`115df37`**. The paper commit's `r1/tracks/IMPLEMENTATION_NOTES.md` and `r1/tracks/ANALYSIS_NOTES.md` describe every CLI.

## What Track S is (orientation)

Track S is a **one-way screen**. It asks whether a tuned, state-dependent (dynamic) threshold policy π\* beats the tuned static threshold rule m\* on whole campaigns of the governed autoresearch loop.

- **Design.** The comparison is paired by instance, with n = 300 fresh instances per node, on the audited terminal metric in raw units.
- **Outcomes.**
  - **A**: a dynamic gain was found.
  - **A-small**: significant, but below δ_Y.
  - **No gain found**: this bounds π\* only and is never evidence that the loop is one-step.
- **Nodes.** `digits_mlp` runs entirely on TASL-2; `tabular_mlp` runs entirely on TASL-7.
- **Your job.** Run the declared phases faithfully, keep provenance complete, and stop when a rule says stop. Interpreting the results is not your job.

## 0. Ground rules

### 0.1 Roles and places

| Work | Where |
|---|---|
| You, git, review loops, reports, analysis (CPU) | **Mac**, in a **separate worktree** of the author's `agent_paper_B` on branch `trackS-ops-<YYYYMMDD>` (from `trackS-20261029` at `9bb64ba`). The main working tree (`exam-x-20261026`) has an uncommitted move of `docs/r1/*` → `docs/*` made by someone else: **do not touch it** |
| Everything for `digits_mlp` (llama-servers, collectors, worker runs, audits) | **TASL-2**, SSH alias **`portal_zhixu`** (`ssh portal_zhixu`), user `dowling`, 32 CPUs, 1 × RTX 4090, driver 535 / CUDA 12.2. Track X evidence has priority |
| Everything for `tabular_mlp` | **TASL-7**, SSH alias **`tasl7`** (`ssh tasl7`; Tailscale `tasl-7`, 100.106.74.51), user `dowling`, 24 CPUs, 1 × RTX 4090, driver 580 / CUDA 13.0, **no sudo**, a pending reboot may happen. Track P evidence has priority |
| S0.6 synthetic calibration, `breast_w` S1.1 | Mac or the container (CPU, no LLM) |
| Author | Commits the pre-declaration (S0.8) and the authorization note (S0.9); decides where marked |

**Paths on each host** (used in every command below; `<node>` is `digits_mlp` on TASL-2 and `tabular_mlp` on TASL-7):
- `R=/home/dowling/r1_tracks`
- `OUT=$R/out/<node>`: everything that is copied back (manifests, `.jsonl`, `STOP` files). A phase writes `$OUT/<phase>[_s<i>]`.
- `WORK=$R/scratch/<node>`: per-unit working trees; stays on the host until Track S is closed (S0.5b needs it).
- `IN=$OUT/inputs`: files copied from the Mac to the host (centres file, π′), each with its sha256 in `$IN/SHA256SUMS`.

**Shell rules (review N1, N2).**
- Never pass a collector command as an inline `ssh host '…'` string. Write each launch as a small script under `r1/tracks/ops/launch/<host>_<phase>.sh` in your worktree, copy it to `$R/launch/` with `scp`, run it with `ssh <host> bash $R/launch/<file>`, and commit it. The launch script is the provenance of the exact command.
- Policy strings (`static:g,h`, `dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar`) contain only digits, letters, `:`, `,`, `.`, `-` and `e`. **Write them unquoted.** Never put quote characters inside a variable.
- A repeated argument list is a **bash array**, expanded as `"${ARR[@]}"`, never a string expanded as `$VAR`.
- Every collector runs in its own tmux session started by `trks-run` (§11.2), which makes the collector the session's command and records its exit code.
- Every launch script starts with `set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/<node>; WORK=$R/scratch/<node>; IN=$OUT/inputs; PATH=$R/bin:$PATH`.

### 0.2 Pins (a mismatch is a STOP)

| Item | Pin |
|---|---|
| llama.cpp | tag **v0.7.0**, commit **`620d2225cc436ab0b001e3200e590e3b286ef9ab`**, built per host for sm_89. Record the `llama-server --version` string, but pin by commit |
| Manager GGUF | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` @ revision **`13fb94bfda8c8cf22497dc57b78f391a9acb426a`**, file `qwen2.5-coder-7b-instruct-q4_k_m.gguf`, sha256 **`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`**, alias `r1-manager` |
| Server flags | `-ngl 999 -c 8192 --parallel 1 --verbose --alias r1-manager --host 127.0.0.1 --port <p>` (one slot per server) |
| Schema | `manager_proposal/v1` |
| Code | paper `9bb64ba`, harness `115df37`, checked out **detached** on the hosts; the venv is frozen after Phase 0. A newer commit is used only if the coordinating session accepted it and recorded it in STATUS |

You may fix toolchain problems yourself (flags, paths, a missing header include). You may never change the tag, the commit, the GGUF or the flags without an author PLAN row.

### 0.3 The wrapper: no command without pins

In Phase 0 you create `/home/dowling/r1_tracks/bin/trks` on each host (template in §11.1). It:
- activates the venv;
- sets `AR_HARNESS_ROOT` and `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`;
- sets `LLAMACPP_BASE_URL` from `TRKS_PORT`;
- **injects the pinned LLM flags** (`--manager llamacpp --manager-model llamacpp/r1-manager --proposal-schema manager_proposal/v1 --gguf … --llama-build 620d2225… --llama-server-bin … --host-label … --gpu <GPU UUID>`) into every `collect` call of an LLM phase (S0.4, S0.5, S3, tune, campaign), from a bash array;
- refuses an LLM-phase call that already carries one of these flags, and accepts both `--phase X` and `--phase=X`. `collect assemble` and the CPU phases get no pins.

Use only `trks collect …`, `trks analyze …`, `trks probe …` and `trks s11 …` on the hosts, and launch collectors only through `trks-run`. Never call `python -m r1.tracks.collect` directly for an LLM phase. (The code also refuses EVIDENCE without the llama.cpp manager and its pins.)

### 0.4 GPU lease, priority and pauses

- **Servers hold the lease for their whole life.** Start them only as `tmux new -d -s trks_llm /home/dowling/r1_tracks/bin/trks-servers <k>` (template §11.3). The script runs `flock -n ~/r1_locks/gpu0.lock`. **Inside the tmux pane**, it starts k servers and `wait`s, so the lock is held exactly as long as the servers live. If the lock is taken, the script exits at once and nothing starts.
- **Before starting the servers,** check:
  1. On TASL-2, that `~/r1_locks/trackx_evidence.active` is absent.
  2. On TASL-7, that `~/r1_locks/trackp_evidence.active` is absent. This marker must be created by Track P for its evidence runs; the author arranges it in Phase 0. Also check that no `r1p_*` tmux session is running a GPU job.
  3. That `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` lists no compute process.
  4. On both hosts, that the drill marker `$R/trks_drill.active` is absent (`trks-servers` refuses to start otherwise).
- **Watcher.** `tmux new -d -s trks_watch /home/dowling/r1_tracks/bin/trks-watch` (template §11.4). Start it in Phase 0 and keep it running; restart it after a reboot. It polls every 60 s. If a priority marker appears, it:
  1. touches a `STOP` file in **every** directory under `$R/out` that has a `manifest.json` (finished phases ignore it);
  2. waits until no `r1.tracks.collect` process of ours is left (each collector finishes its current unit and exits 0 with status "paused");
  3. stops our servers (`tmux kill-session -t trks_llm`), which releases the lock.

  If collectors are still running after 1 h, it stops the servers anyway (priority wins) and logs `FORCED`. A forced pause is reported to the author before resuming: check `failed_units.jsonl` and the manifests, and do not edit them.
- **Resuming** after the marker is gone: `find $R/out -name STOP -delete`, start the servers, then re-run the same launch scripts. **A pause is not a failure**, and the exit 3 a forced pause can cause does not count towards the "exit 3 twice" STOP. Every unit is resumable.
- **Ownership.** Never kill or signal a process you did not start.

### 0.5 Shards

- **Choosing k.** After S0.1, each host gets **k = 2** servers (ports 18101 and 18102) only if the concurrent run (setting b) shows **100 % within-server identity on both servers and 100 % cross-server identity** (`cross_server_identity` = 1.0). Otherwise it gets **k = 1** (port 18101). k is **fixed for the node from then on**.
- **Why cross-server identity is required for k = 2 (review N3).** The exact placebo runs alone on port 18101 and its m\* rep-0 campaigns on instances 0–9 are the primary m\* campaigns of those instances, while π\* for the odd instances among them runs on shard 1 (port 18102). With identical servers, these 5 pairs are still exact pairs.
- **Running.** Every LLM phase except S0.4, S0.5 and the exact placebo runs as k processes: `trks-run trks_<phase>_s<i> 1810<i+1> collect … --shard <i>/<k> --out $OUT/<phase>_s<i> --work $WORK/<phase>_s<i>`.
- **Pairing.** The shard map (instance index mod k) is the same in every phase, so all policies of an instance use the same server.

### 0.6 Sessions, health and failures

- **Deadline and stop file.** Every collector call carries `--deadline 28800` (8 h), so it stops scheduling new units after 8 h, and `--stop-file $OUT/<its phase dir>/STOP`. Restart a stopped or paused session with the identical command: it resumes.
- **Exit codes.** `trks-run` appends each exit code with a timestamp to `$R/logs/<session>.exit`; the collector's output is in `$R/logs/<session>.log`.
  - **3** ("STOP: server unhealthy", after 3 consecutive transport or health failures): check the server log. Restart the servers once through `trks-servers`. If the next session also exits 3, **STOP** for the author.
  - Any other non-zero exit is a STOP. Read the manifest and `failed_units.jsonl`.
- **Retries.** A unit that fails `--max-retries` times stays in `failed_units.jsonl` and is never counted as done. More than **2 %** failed units in a phase is a STOP.
- **Where the counts are.** The manifest is written at the start and at the end of each session, and each session appends its own record. Read the latest one: `jq '.sessions[-1].done' manifest.json` (status `complete`, `deadline`, `paused` or `STOP: server unhealthy`; a session that died has `interrupted` instead of `done`). Its `roots`, `leaves` and `failed` count **that session only**. Committed units are the distinct ids in `roots.jsonl` (`root_id`) and `leaves.jsonl` (`fork_id`, `arm`, `rep`), across sessions. Forks are not units; they have no retries of their own.
- **How the 2 % is counted (rev 3.3; Phase 0 review m10).**
  - Failed units are **permanently failed units**: units whose retries are used up. Read them as `exhausted` in the latest session's `done`; it is cumulative.
  - The rate is Σ over the phase's shards of `exhausted`, divided by Σ over the shards of (committed roots + committed leaves + `exhausted`).
  - Lines in `failed_units.jsonl` and `done.failed` count **failed attempts**, not failed units. An attempt that a later retry completed does not count.
  - **A phase is finished** when, for every shard, the identical command with `--dry-run` added prints `roots_todo` = 0 and `leaves_todo` = 0. (For a fork phase, leaves are planned only after their root commits, so a dry run before that under-counts them.) Re-run the sessions with the same commands until then, or until the 2 % rule stops the phase.
  - If a report needs any other reading of a STOP rule, do not adopt it in the report. Flag it to the coordinating session, which changes this runbook.
- **Checks.** At every working session, check `tmux ls`, each manifest's progress and status, `failed_units.jsonl`, `nvidia-smi` and the server logs. `trks-status` (§11.5) prints all of this.

### 0.7 Labels and gates

- S0.1, S1.1, S0.4, S0.5, S0.5b, S0.6 and S0.7 are labelled `ENGINEERING_ONLY`. Their outputs feed the pre-declaration and are never quoted as results.
- S3a and S3e are labelled `EVIDENCE`, **only after** the author has committed both the pre-declaration (S0.8; a PLAN §10 row with its sha256) and the authorization note (S0.9, `docs/r1/authorizations/trackS_<date>.md`). Until then, refuse to start them.
- You never write the pre-declaration's PLAN row or an authorization note.

### 0.8 Review loop, reporting, commits

- **Review loop at every STOP.**
  1. Spawn a **fresh** reviewer agent that has not seen your work in progress. Give it the phase goal, this runbook, the design sections, the commits and the host outputs, but not your conclusions.
  2. The reviewer writes `docs/r1/reviews/TRACKS_OPS_<phase>_REVIEW_<date>.md`.
  3. You fix each finding or answer it.
  4. The same reviewer writes "accepted" or "not accepted".

  You never accept your own phase.
- **Copy-back after every phase.** `rsync -a` the whole `$OUT/<phase>*` trees (not `$WORK`) from the host to the Mac under `results/r1/tracks/<node>/<phase>/`. Commit JSON, manifests and `.jsonl` files up to 20 MB; gzip larger `.jsonl` files (`assemble` reads `.jsonl.gz`) and record their sha256 in a `SHA256SUMS` file. `$WORK` stays on the host until Track S is closed. S0.5b needs it.
- **Reports.** `docs/r1/reports/TRACKS_<phase>_<date>.md`, a STATUS entry, and a message to the author with what was done, the commits, the checks, the verdict and any questions.
- **Commits.** Author `Dowling Wong <wangdowling@gmail.com>`, with each message ending in the attribution lines the coordinating session gives you. Push `trackS-ops-*` to the hosts' bare repositories and, where the Mac has credentials, to GitHub. Never push `main`, `r1` or `exam-x-*`. Never force-push.

## Phase 0 — Code, host facts, environments, build (both hosts; ½–1 day)

**0.1 Code on the Mac.**
- In the author's checkout: `git fetch .claude-worktrees/_snapshots/trackS_30oct.bundle trackS-20261029:trackS-20261029 docs/trackS-decisions-30oct:docs/trackS-decisions-30oct`.
- Verify `trackS-20261029` = `9bb64ba…` and `docs/trackS-decisions-30oct` = the docs head recorded in `.claude-worktrees/_snapshots/trackS_30oct.heads.txt` next to the bundle (`git bundle verify` first). A mismatch is a STOP.
- Create your worktree `trackS-ops-<date>` from `9bb64ba`. Read the documents from `docs/trackS-decisions-30oct`.

**0.2 Host facts (read-only).** Per host, record:
- `hostname; id; nproc; free -g; df -h /home/dowling`;
- `nvidia-smi` and the CSV query;
- the CUDA toolkit: `ls -d /usr/local/cuda*`, then `<path>/bin/nvcc --version` (nvcc is not on PATH);
- `cmake --version`, `gcc --version`, `git`, `tmux`, `flock`;
- Python: TASL-2 has 3.10 without ensurepip and no `uv`;
- network: `curl -sI --max-time 10 https://huggingface.co https://github.com https://astral.sh`;
- `ls -la ~/r1_locks; tmux ls`;
- any existing llama.cpp build or GGUF (reuse only if commit and sha256 match).

**0.3 Access and author items.**
- (a) **SSH access (confirmed by the author, 30 Oct).** The operator reaches TASL-2 as `ssh portal_zhixu` and TASL-7 as `ssh tasl7`, from the Mac, without a password prompt. Check both with `ssh <alias> 'hostname; id'` at the start of Phase 0. If either fails, STOP and ask.
- (b) **Work directory (approved by the author, 30 Oct).** `/home/dowling/r1_tracks/` on both hosts is the operator's work directory. The operator may create, read and write anything under it without asking; nothing outside it is written, except the lease lock `~/r1_locks/gpu0.lock`, which `flock` uses.
- (c) **Track P marker on TASL-7.** The author arranges that Track P creates and removes `~/r1_locks/trackp_evidence.active` around its evidence runs, through the helper in `docs/r1/proposals/TRACKP_EVIDENCE_MARKER_20261030.md` (PLAN row R1-TASL7-TRACKP-MARKER). For STOP 0, the author's confirmation that this is being arranged is enough. **Gate (rev 3.3):** no Track S phase from Phase 6 on starts on TASL-7 until either the helper is installed and the 3.0b check has passed, or the author has stated in writing (STATUS or the phase report) that no Track P evidence run will start on TASL-7 while that phase runs. Phases 1–5 are short and need neither.

**0.4 Transfer (R1-EXAM-TRANSFER).**
- On each host, create `/home/dowling/r1_tracks/{remotes,work,opt,models,bin,logs,launch,out,scratch}`, with `git init --bare remotes/Agent_paper_B.git`.
- From the Mac, push `trackS-ops-<date>` and the tag `trackS-code-9bb64ba` to it.
- Clone into `work/Agent_paper_B` and `git checkout --detach 9bb64ba`.
- Harness: clone `https://github.com/dowlingwong/autoresearch_harness` into `work/autoresearch_harness` and `git checkout --detach 115df37`. If GitHub is unreachable from the host or the clone needs credentials (not yet verified on TASL-2), transfer the harness through a second bare repository the same way, from the Mac's clone.

**0.5 Environment.**
- Install `uv` user-level: `curl -LsSf https://astral.sh/uv/install.sh | sh`. If astral.sh is unreachable, STOP and ask.
- `uv python install 3.11`; `uv venv /home/dowling/r1_tracks/venv --python 3.11`.
- `uv pip install -e work/autoresearch_harness[dev]`, plus numpy, scipy, scikit-learn, PyYAML and pytest at the versions the tests need.
- `uv pip freeze > logs/pip_freeze.txt`. The venv is frozen from here on.

**0.6 Tests on each host** (with the wrapper's environment):
- `pytest -q r1/tests/test_tracks_*.py` in the paper checkout: **168 passed**. It takes 5–10 min of CPU and includes the end-to-end test.
- `pytest -q tests/stage2/test_r1_track_s_arms.py` in the harness: **14 passed**.

Any other result is a STOP.

**0.7 Build llama.cpp.**
1. `git clone https://github.com/ggml-org/llama.cpp opt/llama.cpp && git -C opt/llama.cpp checkout 620d2225cc436ab0b001e3200e590e3b286ef9ab`.
2. Build:
   `cmake -S opt/llama.cpp -B opt/llama.cpp/build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89 -DCMAKE_CUDA_COMPILER=<toolkit>/bin/nvcc -DCMAKE_BUILD_TYPE=Release && cmake --build opt/llama.cpp/build -j --target llama-server`
   If the compiler complains about `<iomanip>`, add `-DCMAKE_CXX_FLAGS="-include iomanip"`. This was needed on deepthought.
3. Record every command and `llama-server --version`.

**0.8 GGUF.** Download the pinned file at the pinned revision into `models/`:
`curl -L -o models/qwen2.5-coder-7b-instruct-q4_k_m.gguf https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q4_k_m.gguf`
Then run `sha256sum`. It must equal the pin.

**0.9 Scripts.** Install `trks`, `trks-run`, `trks-servers`, `trks-watch` and `trks-status` from §11 into `bin/`, filling the host label and GPU UUID (`nvidia-smi --query-gpu=uuid --format=csv,noheader`). Then check: `bash -n` on each script; `trks collect --help` and `trks probe --help` list every injected flag; and a dry `trks collect --phase=S0.4 …` and `trks collect assemble --help` reach Python. Start the watcher (`touch $R/logs/watch_started` first).

**0.10 Smoke test (ENGINEERING_ONLY).**
1. `tmux new -d -s trks_llm $R/bin/trks-servers 1` and confirm full offload in `$R/logs/llama_18101.log` (`offloaded N/N layers`).
2. `trks-run trks_smoke_dry 18101 collect --phase S0.4 --node <node> --instances 1 --dry-run --out $OUT/smoke_dry --work $WORK/smoke_dry --label ENGINEERING_ONLY`.
3. Then one real instance without `--dry-run`, into `$OUT/smoke` and `$WORK/smoke` (session `trks_smoke`). Record the per-run CPU time t_run.
4. `tmux kill-session -t trks_llm`.

**Output:** `docs/r1/reports/TRACKS_HOST_FACTS_<date>.md`.

**STOP 0:** the review loop (the reviewer re-runs the facts, both test suites and the pin checks), plus the author's confirmation for item 0.3(c).

## Phase 1 — S0.1 determinism, latency, CPU census (each host; < 1 GPU-h)

Start the servers with k = 2 (`tmux new -d -s trks_llm $R/bin/trks-servers 2`; ports 18101 and 18102). Then, from a launch script, run each probe in its own session (`trks-run trks_s01_serial - probe …`, then `trks-run trks_s01_conc - probe …` after the first has exited), so an ssh drop does not kill it:

```
trks probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --node <node> --server-args "<exact server command>" --out $OUT/s01/serial.json
trks probe --url http://127.0.0.1:18101/v1 --url http://127.0.0.1:18102/v1 --mode concurrent --clients-per-url 2 \
  --n 200 --repeats 3 --order-seed 2 --proposal-schema manager_proposal/v1 --node <node> --server-args "…" --out $OUT/s01/concurrent.json
```

`trks probe` is the wrapper around `python -m r1.tracks.probes.determinism`. It injects the GGUF, build and host flags.

**Done when:**
- **k = 2** if, in the concurrent run, within-server identity is **100 %** on both URLs **and** `cross_server_identity` is **100 %** (§0.5).
- Else **k = 1** if identity is 100 % in the serial run. Restart the servers with k = 1 for all later phases.
- Else **STOP** for the author.
- Latency (mean and p95) and free cores are recorded.

**Projection** (formula, reported for the author). Projected hours for the rest of the node = (C × L / k + R × t_run / c) / 3600, where:
- C ≈ 80 000 LLM calls;
- L is the mean latency;
- R ≈ 60 000 worker and audit runs;
- t_run is the per-run CPU time measured in the smoke test;
- c is the number of free cores, capped by k × 2 concurrent campaigns.

**STOP 1:** the review loop.

## Phase 2 — S1.1 interaction check (CPU, no LLM; can run in parallel with Phase 1)

```
trks s11 --node digits_mlp --out $OUT/s11/digits.json          # TASL-2
trks s11 --node tabular_mlp --out $OUT/s11/tabular.json        # TASL-7
python -m r1.tracks.probes.s1_factorial --node openml_breast_w --pair max_iter:C --out s11_breast_w.json   # Mac / container
```

This is reported with the result. It is not a gate. It is reviewed together with Phase 3.

## Phase 3 — S0.4 dev campaigns, D28 liveness, A2-U prior (each node on its host; k servers may run, but S0.4 uses one process)

**3.0 Pause drill (rev 3.3; both hosts, during S0.4; before any multi-day phase).** The watcher's pause path has not yet run on a real host. Exercise it once per host with Track S's own **drill marker** `$R/trks_drill.active`, which the watcher (§11.4) treats like a priority marker. Never create another track's marker (`trackx_…`, `trackp_…`) by hand.
1. Start S0.4 as below. Once at least one unit has committed (`jq -r .root_id $OUT/s04/roots.jsonl | sort -u | wc -l` ≥ 1; the manifest is not updated during a session), record that count, `tmux ls`, and that the lease is held (`flock -n ~/r1_locks/gpu0.lock true` fails).
2. `touch $R/trks_drill.active` and note the time.
3. **Expected:**
   - within about 1 min, `logs/watch.log` says `priority marker seen ($R/trks_drill.active): pausing`;
   - after the current unit, `trks_s04` exits with `rc=0` in `logs/trks_s04.exit`, and `jq '.sessions[-1].done.status' $OUT/s04/manifest.json` is `"paused"`;
   - then `servers stopped; lease released`; `trks_llm` is gone, `flock -n ~/r1_locks/gpu0.lock true` succeeds, and `nvidia-smi` lists no compute process;
   - no `FORCED` entry.
4. `rm $R/trks_drill.active`. Wait for `marker gone` in the log. Then resume as in §0.4: `find $R/out -name STOP -delete`, start the servers, re-run the S0.4 launch script.
5. **Expected after the resume:**
   - the distinct `root_id` count in `roots.jsonl` keeps growing from the count at the pause (the new session's own `done.roots` starts at 0; that is normal);
   - no unit is committed twice: `jq -r .root_id $OUT/s04/roots.jsonl | sort | uniq -d` prints nothing;
   - `s04_rows.jsonl`, the file `fit_prior` reads, has no duplicate (instance, budget_index) pair;
   - `exhausted` stays 0.
6. Record the timestamps, the pause latency (marker to lease released) and the outputs in the Phase 3 report.

Any deviation is a **STOP**. The drill pause is not a failure, and its exit is not an exit 3.

**3.0b Track P integration check (TASL-7; only when Track P is idle and has installed its marker helper, `docs/r1/proposals/TRACKP_EVIDENCE_MARKER_20261030.md`).** Ask the author first. Then, during a Track S LLM session on TASL-7: `~/r1_locks/bin/trackp-evidence begin drill-trackS`; check that Track S pauses as in step 3 and that `trackp-evidence status` shows the lease free; `trackp-evidence end drill-trackS`; then resume and check as in steps 4–5. This is the only time the operator may create the Track P marker, and only through the helper with the author's permission. If Track P is not ready, record this check as open. It does not block STOP 3, but it gates Phase 6 on TASL-7 (Phase 0.3(c)).

```
trks-run trks_s04 18101 collect --phase S0.4 --node <node> --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file $OUT/s04/STOP --out $OUT/s04 --work $WORK/s04
# after trks_s04 has exited 0 with status "complete" (CPU, no servers needed; short, so run directly):
trks collect --phase liveness --node <node> --out $OUT/s04          # exit 3 = STOP (node fails D28)
trks collect --phase fit_prior --node <node> --out $OUT/s04 --sigma-node <σ_node> --obs-inflation 1.0 --prior $OUT/a2u_prior.json
```

Here σ_node = 0.0066 for digits and 0.0019 for tabular (PLAN D18 table).

**Done when:**
- liveness passes;
- `a2u_prior.json` and its sha256 are recorded;
- failed units are ≤ 2 % (exhausted / planned, §0.6) and were retried;
- the pause drill (3.0 above) passed on both hosts.

**STOP 3:** the review loop, covering Phases 2 and 3 and the drill.

## Phase 4 — S0.5 pilot, S0.5b truncation, summary

The declared price is g = 0.1 σ_node: digits **0.00066**, tabular **0.00019**. A2-U runs at g0 = g by default.

```
trks-run trks_s05 18101 collect --phase S0.5 --node <node> --prior $OUT/a2u_prior.json --prior-sha256 <sha> --obs-inflation 1.0 \
  --W 40 --instances 20 --policy "static:<0.3·σ_node>,0" --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 \
  --label ENGINEERING_ONLY --deadline 28800 --stop-file $OUT/s05/STOP --out $OUT/s05 --work $WORK/s05
# after trks_s05 has exited 0 with status "complete" (CPU; long, so in its own session, which survives an ssh drop):
trks-run trks_s05b - collect --phase S0.5b --node <node> --truncate-W 8,10,12,20 --out $OUT/s05 --work $WORK/s05
```

- **λ at S0.5 (not checked by the code).** The code's λ-mismatch check covers only the phases after S0.5. Pass `--obs-inflation` equal to the `obs_inflation` recorded in the prior's metadata (1.0 for `a2u_prior.json`, λ₂ for `a2u_prior_l2.json`), and check that the S0.5 manifest records the same value. A difference is a STOP.
- A fork-rebuild mismatch or an A/A mismatch here is a STOP (design §10).
- Copy `$OUT/s05` from both hosts to the Mac. It must include `s05_calibration.jsonl` and `s05b_truncated.jsonl`.
- Then, on the Mac:
  `python -m r1.tracks.analyze s05-summary --node digits_mlp=<MAC>/s05_digits --node tabular_mlp=<MAC>/s05_tabular --out <MAC>/s05_summary.json`
  It prints `values`: W, σ_cmp,vary, σ_D UCL, the between-repetitions UCL, `between_policy_sd_at_cap`, the near band b, the calibration status and λ.

**Calibration gate** (design S0.5 (iii)): coverage of the 80 % intervals in [0.70, 0.90] overall and in every stratum with ≥ 20 predictions. If it fails for a node:
- **Coverage too low** (overall, or in stratum `1-2` or `>=3`):
  1. Set **λ₂ = max(1, (q₉₀ / 1.2816)²)**, where q₉₀ is the 90th percentile of |z| over that node's `s05_calibration.jsonl` rows with a non-null `delta_audit`, and z = (`delta_audit` − `mu`) / `sd`. Use the snippet in §11.6 and record its output.
  2. `trks collect --phase set_obs_inflation --node <node> --prior $OUT/a2u_prior.json --obs-inflation <λ₂> --prior-out $OUT/a2u_prior_l2.json --out $OUT/s05_l2`
  3. Re-run S0.5 (session `trks_s05_l2`) and S0.5b into **new** `--out` and `--work` (`s05_l2`), with `--prior $OUT/a2u_prior_l2.json`, its sha256 and `--obs-inflation <λ₂>`. Every later command uses this prior and λ₂; the code refuses a mismatch.
  4. A second failure is a **STOP**.
- **Coverage too high, or a failing stratum `0`:** **STOP** for the author. λ ≥ 1 only widens intervals, and it does not change stratum-0 intervals (they come from the prior alone), so the λ₂ revision cannot fix these.

**Fallback** (design §2, S0.5b). Using the Phase 1 projection, a node whose projected **S0.7 + S3e** time exceeds 4 days drops from the decision now. (S3a is not counted.) The author confirms. It is never revisited after outcomes exist.

**STOP 4:** the review loop. Send the author W, σ_D, b, λ and the projection.

## Phase 5 — S0.6 synthetic calibration, first run (Mac or container; CPU, about 1 h per node)

```
python -m r1.tracks.simulate_controls --out <MAC>/s06_<node>_pre --node <node> --delta-Y <0.0033|0.0020> \
  --sigma-unit <σ_cmp,vary> --sigma-D <σ_D UCL> --between-policy-sd <between_policy_sd_at_cap> --W <W>
python -m r1.tracks.analyze predecl-template --s05 <MAC>/s05_summary.json --sigma-node digits_mlp=0.0066 \
  --sigma-node tabular_mlp=0.0019 --controls <s06 json per node> --out <MAC>/predecl_draft.json
```

n = 300 is the default.

**Done when:** N0's route-A count is **< 19 of 200**. A count of ≥ 19 is a STOP. The calibration table is reported (power with its CI, P(correct member), the achieved oracle gain) under its own label, FIXTURE.

**STOP 5:** the review loop.

## Phase 6 — S0.7 tuning (each node on its host; k shards)

1. **Statics: 15 configurations × 20 paired dev instances.** For i in 0…k−1 (one launch script per host that loops over i):
   ```
   trks-run trks_tune_static_s<i> 1810<i+1> collect --phase tune --node <node> --prior <P> --prior-sha256 <s> --obs-inflation <λ> --W <W> \
     --tune-grid static --sigma-cmp-vary <σ_cmp,vary> --shard <i>/<k> --label ENGINEERING_ONLY --deadline 28800 \
     --stop-file $OUT/tune_static_s<i>/STOP --out $OUT/tune_static_s<i> --work $WORK/tune_static_s<i>
   ```
   Copy back, then on the Mac:
   ```
   python -m r1.tracks.collect assemble --node <node> --out <ND> --dev <tune_static_s0 … s<k-1>>
   python -m r1.tracks.analyze select --predeclaration <MAC>/predecl_draft.json --node <node>=<ND> --out <MAC>/sel1_<node>.json
   ```
2. **Extension, only if `values.extension_configs` is set.** The same command with `--tune-g-extension-only` in place of `--tune-grid static`, writing to `tune_ext_s<i>`. Re-assemble and select again.
3. **Members: 4 centred members × 40 paired dev instances.** First copy the Mac's `<ND>/dev_roots.jsonl` (from the assemble of steps 1–2) to the host as `$IN/dev_roots.jsonl` and append its sha256 to `$IN/SHA256SUMS`. Then:
   ```
   trks-run trks_tune_mem_s<i> 1810<i+1> collect --phase tune --node <node> … --tune-grid dynamic --sigma-cmp-vary <σ> --m-star <m*> \
     --centres-from $IN/dev_roots.jsonl --shard <i>/<k> … --stop-file $OUT/tune_mem_s<i>/STOP --out $OUT/tune_mem_s<i> --work $WORK/tune_mem_s<i>
   ```
   Assemble **all** tune dirs, then `select` → `<MAC>/sel2_<node>.json`. It gives π\*, r̄₁, τ̄, r̄₂, g_eff, h_eff, `dev_between_sd`, the flip rates and the winner's-curse report.
4. **S0.6 re-run** with `--dev-between-sd <dev_between_sd>` (output `s06_<node>_post`). Then:
   ```
   python -m r1.tracks.analyze predecl-template --s05 … --select <node>=<MAC>/sel2_<node>.json --controls <post jsons> --sigma-node … --out <MAC>/predecl_s08.json
   ```

**STOP 6:** the review loop. Send the author m\*, π\* and the S0.6 tables.

## Phase 7 — S0.8 pre-declaration and S0.9 authorization (author)

Fill `predecl_s08.json` in full:
- no TODO left, and the `draft` flag removed;
- W, n = 300, δ_Y and λ;
- the near band b, with `--p-near 0.5`;
- the S3a design: 30 roots per node, `--forks 4` (≈ 120 uniform forks plus the near-threshold oversample, about 150 forks in total);
- the secondaries;
- the sha256 of `r1/tracks/analyze.py` at `9bb64ba`, and the pins.

Commit it as `docs/r1/predeclarations/trackS_<date>.json` on `trackS-ops-<date>` and compute its sha256. Send the author the hash, a one-page summary, and the authorization draft `docs/r1/proposals/AUTH_DRAFT_trackS_20261030.md`, filled with the values.

**STOP 7 (author):** the author commits a PLAN §10 row with the pre-declaration hash, and the note `docs/r1/authorizations/trackS_<date>.md`. **Nothing in Phase 8 starts before both are committed.**

## Phase 8 — S3a forks and S3e decision campaigns (EVIDENCE)

**8.1 S3a.** k shards on each host:

```
trks-run trks_s3a_s<i> 1810<i+1> collect --phase S3 --node <node> --prior … --obs-inflation <λ> --W <W> --root-policy <m*> \
  --instances 30 --forks 4 --near-band <b> --p-near 0.5 --aa-fraction 0.1 --reps 2 --reps-ordinary 1 \
  --shard <i>/<k> --label EVIDENCE --deadline 28800 --stop-file $OUT/s3a_s<i>/STOP --out $OUT/s3a_s<i> --work $WORK/s3a_s<i>
```

Copy back, then assemble (all dev dirs plus `--fork` with every `s3a_s*`). On the Mac, freeze π′:

```
python -m r1.tracks.analyze fit-policy --predeclaration <PREDECL_FINAL> --node <node>=<ND> --out-dir <MAC>/pi_prime
```

Record the sha256 of `<node>.pi_prime.json`, copy the file to the host as `$IN/<node>.pi_prime.json`, and append its sha256 to `$IN/SHA256SUMS`. It is frozen from here on.

**8.2 S3e.** The exact placebo runs **first and alone**, then the shards. The launch script defines the shared arguments as a bash array (policy strings unquoted, §0.1):

```bash
S3E=(--node <node> --prior <P> --prior-sha256 <s> --obs-inflation <λ> --W <W> --instances 300
     --policy <π*> --policy <m*> --policy <matched static>
     --placebo-policy <m*> --exact-placebo-n 10 --descriptive-placebo-n 15 --label EVIDENCE --deadline 28800)
trks-run trks_s3e_placebo 18101 collect --phase campaign "${S3E[@]}" --exact-placebo-only \
  --stop-file $OUT/s3e_placebo/STOP --out $OUT/s3e_placebo --work $WORK/s3e_placebo
```

Only after `trks_s3e_placebo` has exited 0 with status "complete" and no mismatch, run **three separate launch scripts, one after another** (`<host>_s3e_main.sh`, `<host>_s3e_other.sh`, `<host>_s3e_sec.sh`), each looping over i in 0…k−1. Start the next script only after every session of the previous one has exited with rc=0 and status "done" (`trks-status`). Each script defines the arrays it uses:

```bash
# <host>_s3e_main.sh
trks-run trks_s3e_s<i> 1810<i+1> collect --phase campaign "${S3E[@]}" --shard <i>/<k> \
  --stop-file $OUT/s3e_s<i>/STOP --out $OUT/s3e_s<i> --work $WORK/s3e_s<i>
# <host>_s3e_other.sh and <host>_s3e_sec.sh
SEC=(--node <node> --prior <P> --prior-sha256 <s> --obs-inflation <λ> --W <W> --instances 30 --label EVIDENCE --deadline 28800)
trks-run trks_s3e_other_s<i> 1810<i+1> collect --phase campaign "${SEC[@]}" \
  --policy <best member, other channel 1> --policy <best member, other channel 2> --shard <i>/<k> \
  --stop-file $OUT/s3e_other_s<i>/STOP --out $OUT/s3e_other_s<i> --work $WORK/s3e_other_s<i>
trks-run trks_s3e_sec_s<i> 1810<i+1> collect --phase campaign "${SEC[@]}" \
  --policy a2u --policy pi_prime:$IN/<node>.pi_prime.json --shard <i>/<k> \
  --stop-file $OUT/s3e_sec_s<i>/STOP --out $OUT/s3e_sec_s<i> --work $WORK/s3e_sec_s<i>
```

Never run two collectors on one port at the same time: each server has one slot, and S0.1 tested at most two clients per server. The same rule holds in every phase.

- `--instances 30` with the default seed base is the first 30 S3e instances.
- The "other channels" are the best member of each channel other than π\*'s. The exact list is in `sel2_<node>.json`.

**STOP immediately** on any of these:
- an exact-placebo mismatch;
- an A/A mismatch;
- a pin mismatch;
- exit 3 twice;
- more than 2 % failed units;
- any condition in design §10.

**8.3 S4a** (the prompt-level display ablation) has **no runner**. It is a secondary. Report it as not run, and do not improvise it.

**STOP 8:** the review loop. The reviewer checks manifests, pins, counts, shard disjointness, placebos and failed units.

## Phase 9 — Assemble and analyse (Mac, CPU)

```
python -m r1.tracks.collect assemble --node <node> --out <ND> --dev <all tune dirs> \
  --campaign <s3e_placebo> <all s3e_s*, s3e_other_s*, s3e_sec_s*> --fork <all s3a_s*>
python -m r1.tracks.analyze analyze --predeclaration <PREDECL_FINAL> --node digits_mlp=<ND_D> --node tabular_mlp=<ND_T> \
  --controls <s06_digits_post.json> --controls <s06_tabular_post.json> --out-json <R>.json --out-md <R>.md
```

**Done when** the outcome is reported exactly as `analyze` prints it, per node:
- A;
- A-small;
- no gain found, with UB₉₅, the S3e flip rate and P(correct member) side by side;
- Track S not run.

Put it in `docs/r1/reports/TRACKS_RESULT_<date>.md`. **You do not change the framing**; R1-TRACKS-FRAMING maps the outcome.

**STOP 9:** the review loop, then the author reads the result.

## 10. If something fails

| Situation | Action |
|---|---|
| llama.cpp build failure | Fix flags, paths or includes and record them. Never change the commit. If it cannot be built, STOP |
| GGUF sha256 mismatch; pin mismatch | STOP |
| S0.1 identity < 100 % in both settings | STOP (author) |
| D28 liveness fails | STOP (author; design §10) |
| Calibration gate fails twice; N0 ≥ 19/200; an exact placebo D ≠ 0; descriptive placebo \|z\| > 3.5; an A/A or fork-rebuild mismatch | STOP |
| Collector exit 3 twice in a row | STOP |
| More than 2 % failed units in a phase | STOP |
| Priority marker appears | The watcher pauses everything; resume later. Not a failure |
| TASL-7 reboots | Every unit resumes. Restart the watcher and the servers, then the collectors with the same commands |
| GPU time on a host passes 5 days | STOP |
| Anything not covered | STOP and ask |

## 11. Script templates (fill the paths in Phase 0; commit them to `trackS-ops-<date>` under `r1/tracks/ops/`)

### 11.1 `bin/trks`
```bash
#!/usr/bin/env bash
set -euo pipefail
R=/home/dowling/r1_tracks; . "$R/venv/bin/activate"
export AR_HARNESS_ROOT=$R/work/autoresearch_harness OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$R/work/Agent_paper_B"
GGUF=$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
GGUF_SHA=509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c
LLAMA_BUILD=620d2225cc436ab0b001e3200e590e3b286ef9ab
LLAMA_BIN=$R/opt/llama.cpp/build/bin/llama-server
HOST_LABEL=TASL-2                      # TASL-7 on TASL-7
GPU_ID=GPU-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   # nvidia-smi --query-gpu=uuid --format=csv,noheader
PIN=(--manager llamacpp --manager-model llamacpp/r1-manager --proposal-schema manager_proposal/v1
     --gguf "$GGUF" --gguf-sha256 "$GGUF_SHA" --llama-build "$LLAMA_BUILD" --llama-server-bin "$LLAMA_BIN"
     --host-label "$HOST_LABEL" --gpu "$GPU_ID")
PROBE_PIN=(--host-label "$HOST_LABEL" --gguf "$GGUF" --gguf-sha256 "$GGUF_SHA" --llama-build "$LLAMA_BUILD"
           --llama-server-bin "$LLAMA_BIN")
[ $# -ge 1 ] || { echo "usage: trks collect|analyze|probe|s11 ..." >&2; exit 2; }
sub=$1; shift
phase=""; prev=""
for a in "$@"; do
  case "$a" in --phase=*) phase=${a#--phase=} ;; esac
  if [ "$prev" = "--phase" ]; then phase=$a; fi
  prev=$a
done
case "$sub" in
  collect)
    case "$phase" in
      S0.4|S0.5|S3|tune|campaign)
        for a in "$@"; do
          case "$a" in --manager|--manager=*|--manager-model*|--gguf*|--llama-*|--host-label*|--gpu|--gpu=*|--proposal-schema*)
            echo "trks: $a is injected by the wrapper; do not pass it" >&2; exit 2 ;; esac
        done
        : "${TRKS_PORT:?trks: set TRKS_PORT for an LLM phase}"
        export LLAMACPP_BASE_URL=http://127.0.0.1:$TRKS_PORT/v1
        exec python -m r1.tracks.collect "$@" "${PIN[@]}" ;;
      *) exec python -m r1.tracks.collect "$@" ;;      # CPU phases and `collect assemble`
    esac ;;
  analyze) exec python -m r1.tracks.analyze "$@" ;;
  probe)   exec python -m r1.tracks.probes.determinism "$@" "${PROBE_PIN[@]}" ;;
  s11)     exec python -m r1.tracks.probes.s1_factorial "$@" ;;
  *) echo "trks: unknown subcommand $sub" >&2; exit 2 ;;
esac
```
Fill `HOST_LABEL` and `GPU_ID` per host. Check that the pin flags match `collect --help` and the probe's `--help` exactly. If a flag differs, fix the template, never the code. The GPU is recorded by UUID (no spaces); record `nvidia-smi --query-gpu=name,uuid --format=csv` in the host facts.

### 11.2 `bin/trks-run <session> <port|-> <trks arguments…>`
```bash
#!/usr/bin/env bash
# Runs one trks command as the command of its own tmux session; records the command, its output and its exit code.
set -euo pipefail
R=/home/dowling/r1_tracks
[ $# -ge 3 ] || { echo "usage: trks-run trks_<name> <port|-> <trks args...>" >&2; exit 2; }
s=$1; p=$2; shift 2
case "$s" in trks_*) ;; *) echo "trks-run: session name must start with trks_" >&2; exit 2 ;; esac
if tmux has-session -t "$s" 2>/dev/null; then echo "trks-run: session $s already exists" >&2; exit 1; fi
cmdf=$R/logs/$s.cmd
{
  echo '#!/usr/bin/env bash'
  if [ "$p" != "-" ]; then echo "export TRKS_PORT=$p"; fi
  printf '%q ' "$R/bin/trks" "$@"; echo ">> $R/logs/$s.log 2>&1"
  echo "rc=\$?; echo \"\$(date -u +%FT%TZ) rc=\$rc\" >> $R/logs/$s.exit"
} > "$cmdf"
tmux new -d -s "$s" "bash $cmdf"
echo "started $s ($cmdf)"
```
`printf %q` keeps every argument one word, so nothing is re-split. A restart with the same launch script overwrites `<session>.cmd` with the identical command and appends to the log and the exit file.

### 11.3 `bin/trks-servers <k>`
```bash
#!/usr/bin/env bash
# run as: tmux new -d -s trks_llm /home/dowling/r1_tracks/bin/trks-servers <k>
set -euo pipefail
R=/home/dowling/r1_tracks; k=${1:?k}
for f in ~/r1_locks/trackx_evidence.active ~/r1_locks/trackp_evidence.active $R/trks_drill.active; do
  if [ -e "$f" ]; then echo "priority marker $f"; exit 1; fi
done
exec flock -n ~/r1_locks/gpu0.lock bash -c '
  R=/home/dowling/r1_tracks
  for i in $(seq 1 '"$k"'); do
    $R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager \
      --host 127.0.0.1 --port 1810$i -ngl 999 -c 8192 --parallel 1 --verbose >> $R/logs/llama_1810$i.log 2>&1 &
  done
  wait'
```
`flock -n` holds the lock for as long as the inner bash, and therefore the servers, live. If the lock is taken, it exits at once. (The re-check confirmed: a second start exits 1, and `tmux kill-session -t trks_llm` stops both servers and frees the lock.)

### 11.4 `bin/trks-watch`
```bash
#!/usr/bin/env bash
# run as: tmux new -d -s trks_watch /home/dowling/r1_tracks/bin/trks-watch
R=/home/dowling/r1_tracks
log() { echo "$(date -u +%FT%TZ) $*" >> "$R/logs/watch.log"; }
MARKERS="$HOME/r1_locks/trackx_evidence.active $HOME/r1_locks/trackp_evidence.active $R/trks_drill.active"
marker() { for f in $MARKERS; do if [ -e "$f" ]; then seen=$f; return 0; fi; done; return 1; }
ours() { pgrep -u "$(id -u)" -f 'python -m r1\.tracks\.collect .*--stop-file' >/dev/null; }   # LLM collectors only
log "watch started"
while sleep 60; do
  marker || continue
  log "priority marker seen ($seen): pausing"
  find "$R/out" -name manifest.json -print0 2>/dev/null | while IFS= read -r -d '' m; do touch "$(dirname "$m")/STOP"; done
  t=0
  while ours; do
    sleep 30; t=$((t + 30))
    if [ "$t" -ge 3600 ]; then log "FORCED: collectors still running after 1 h; stopping servers anyway"; break; fi
  done
  tmux kill-session -t trks_llm 2>/dev/null && log "servers stopped; lease released"
  while marker; do sleep 60; done
  log "marker gone: resume by hand (delete STOP files, start servers, re-run launch scripts)"
done
```
It touches `STOP` in every phase directory with a manifest, including those of collectors started before the watcher, and it waits on the collector processes themselves rather than on tmux session names. It waits only for collectors with a `--stop-file` (every LLM phase has one, §0.6); CPU-only phases (S0.5b, liveness, fit_prior, assemble) do not use the GPU and keep running. Check on TASL-2 and TASL-7 that the `pgrep` pattern matches only Track S collectors (`pgrep -a -f 'python -m r1\.tracks\.collect .*--stop-file'` during the smoke test).

### 11.5 `bin/trks-status`
A script that prints `sha256sum` of the GGUF compared with the pin (a mismatch is a STOP; the collector records the given sha256 without re-hashing), `tmux ls`, `nvidia-smi` (compute apps), the last lines of each server log and of `logs/watch.log`, every `logs/*.exit` line, and, for each `$OUT/*/manifest.json`, the phase, shard, status, units done/total and the `failed_units.jsonl` count.

### 11.6 λ₂ snippet
```python
import json, sys, numpy as np
rows = [json.loads(l) for l in open(sys.argv[1])]            # <s05 dir>/s05_calibration.jsonl
z = [(r["delta_audit"] - r["mu"]) / r["sd"] for r in rows if r.get("delta_audit") is not None and r["sd"] > 0]
q90 = float(np.quantile(np.abs(z), 0.9)); lam2 = max(1.0, (q90 / 1.2816) ** 2)
print(json.dumps({"n": len(z), "n_null_skipped": len(rows) - len(z), "q90": q90, "lambda2": lam2}))
```
The fields are those written by `collect` S0.5 (`mu`, `sd` = predictive sd with audit noise, `delta_audit`, which is null when the audit is missing). Record the printed line in the Phase 4 report. λ₂ is a declared one-step revision; the re-run checks whether it worked.

## 12. Review record

**Revision 1 → 2** (`reviews/TRACKS_OPERATOR_RUNBOOK_REVIEW_20261030.md`, REVISE). Code changes are in `9bb64ba`.

| Finding | Resolution |
|---|---|
| B1: lease not held | `trks-servers` holds `flock` inside the tmux pane for the servers' lifetime (§0.4, §11.3) |
| B2: 2 servers × 2 campaigns not implemented | Code: `--shard i/k`, an own URL per process, `--exact-placebo-only`, assemble checks. Runbook: k per host from S0.1, a fixed map, the placebo run alone and first (§0.5, Phase 8) |
| B3: S0.5 / S0.5b commands | One S0.5 call with `--W 40 --rep 0 --rep 1 --rep-instances 10 --forks 1.5`; S0.5b uses the recorded `--work` and refuses otherwise (code) |
| B4: S3a and π′ | `--instances 30 --forks 4 --near-band b --p-near 0.5`; `--a2-fraction` defaults to 0 (code); `analyze fit-policy` needs no S3e (code) |
| B5: λ not carried | λ recorded in the prior; later phases refuse a mismatch (code); the λ₂ rule and a new `--out` (Phase 4, §11.6) |
| M1: missing manager flags | The `trks` wrapper injects pins; the code requires `--manager` and refuses EVIDENCE without the pins |
| M2: server crashes and priority | Health check, circuit breaker (exit 3) and `--stop-file` (code); 8 h deadline sessions; a watcher with priority markers; the Track P marker arranged by the author (Phase 0.3) |
| M3: extension re-runs everything | `--tune-g-extension-only` (code) |
| M4: S0.6 inputs; controls merge; label | `s05-summary` and `select` print the inputs; `--controls` is repeatable; the decision label comes from S3e only (code) |
| M5: provenance of docs and code | Bundle `trackS_30oct.bundle` with both branches; detached checkouts; design header 7.4; frozen venv |
| M6: copy-back list; gz | Whole `$OUT` trees are copied back; `assemble` reads `.jsonl.gz` |
| M7: D28; S0.5 STOPs; Phase 5 STOP | `--phase liveness` in Phase 3; S0.5 fork and A/A STOPs; STOP 5 added |
| M8: pre-declaration template; ridge CV | `analyze predecl-template`; ridge λ by inner CV in `fit-policy` (code) |
| Minor | nvcc path and Release target; iomanip; pin by commit; GGUF revision and file; `--verbose`; uv and Python 3.11 user install; BLAS threads; repeatable `--url`; "other members" defined; TASL-7 reboot handling; projection formula |

**Revision 2 → 3** (re-check of revision 2 in the same review file, not accepted). Runbook only; no code change.

| Finding | Resolution |
|---|---|
| N1 (BLOCKING): wrapper word-splits `--gpu '…'` | Pins are bash arrays; the GPU is recorded by UUID; the wrapper refuses pin flags passed by hand (§11.1) |
| N2 (BLOCKING): `$S3E` keeps literal quotes | Shared arguments are bash arrays expanded as `"${S3E[@]}"`; policy strings are unquoted; commands go through launch scripts and `trks-run`, never inline ssh strings (§0.1, Phase 8.2, §11.2) |
| N3 (MAJOR): exact-placebo pairs cross servers at k = 2 | k = 2 requires 100 % cross-server identity in S0.1(b) as well (§0.5, Phase 1) |
| N4 (MAJOR): watcher gaps | `OUT`, `WORK` and `IN` defined (§0.1); the watcher touches `STOP` in every manifest directory under `$R/out`, waits on the collector processes, forces after 1 h, and logs; every collector is its tmux session's command via `trks-run` (§0.4, §11.4) |
| `set_obs_inflation` without `--out` | Added (Phase 4) |
| λ₂ snippet field names; λ limits | `mu`, `sd`, null `delta_audit` skipped (§11.6); over-coverage or a failing stratum 0 is a STOP for the author (Phase 4) |
| S0.5 outside the λ check | Manual check against the prior's metadata and the manifest (Phase 4) |
| Smoke test without `TRKS_PORT` | Runs through `trks-run … 18101` (Phase 0.10) |
| `--centres-from` Mac path | Copied to `$IN` with sha256 (Phase 6); π′ likewise (Phase 8.1) |
| `--phase=X` and `assemble` under `pipefail` | Argument loop instead of `grep` (§11.1); checked in Phase 0.9 |
| Fallback counted S3a | S0.7 + S3e only (Phase 4) |
| Docs head not recorded in PLAN | Recorded in `trackS_30oct.heads.txt` next to the bundle (Phase 0.1) |
| Design §11 without a 7.4 entry | The docs branch carries the 7.4 design with its §11 entry |
| Harness clone on TASL-2 unverified | Fallback through a bare repository (Phase 0.4) |

**Revision 3 → 3.1** (re-check of revision 3: **accepted**, with four MINOR items, all fixed here).

| Finding | Resolution |
|---|---|
| Phase 8.2 block started three collectors on one single-slot server | Three separate launch scripts, started one after another; one collector per port at a time in every phase (Phase 8.2) |
| Watcher waited on CPU-only phases | The watcher matches only collectors with `--stop-file`; S0.5b runs via `trks-run … -` (§11.4, Phase 4) |
| Probes exposed to an ssh drop | Phase 1 probes run via `trks-run … - probe` |
| GGUF never re-hashed after Phase 0 | `trks-status` re-hashes it against the pin (§11.5) |

**Revision 3.1 → 3.2** (author, 30 Oct; no review needed: facts only). SSH aliases `portal_zhixu` (TASL-2) and `tasl7` (TASL-7) recorded; the work directory `/home/dowling/r1_tracks/` approved, so the operator needs no further approval for it (§0.1, Phase 0.3).

**Revision 3.2 → 3.3** (30 Oct, after the Phase 0 review; at the author's request).
- §0.6: the 2 % rule's denominator is stated: exhausted units / planned units, over all shards (Phase 0 review m10; the operator had stated it only in its report). Reports never re-read a STOP rule; the runbook does.
- Phase 3.0: a **pause drill** on both hosts during S0.4, with Track S's own drill marker `$R/trks_drill.active` (Phase 0 review n3: the pause path was unexercised). 3.0b: an optional Track P integration check through Track P's marker helper, with the author's permission.
- §11.4: the watcher also reacts to `$R/trks_drill.active` and logs which marker it saw; §11.3 and §0.4: the servers refuse to start while it exists. **Re-install `bin/trks-watch` and `bin/trks-servers` on both hosts and restart `trks_watch` before Phase 3.**
- §0.6: where the counts are (per-session manifest records; committed ids in `roots.jsonl` / `leaves.jsonl`); a phase is finished when a `--dry-run` shows nothing left to do. The collector's final status is `complete`, not `done`.
- Phase 0.3(c): a gate for Phase 6 and later on TASL-7 (the Track P helper and check 3.0b, or the author's written statement).
- Independent review of 3.3 (30 Oct): no BLOCKING; 3 MAJOR and 9 MINOR, all addressed here or in the helper (rev 2 of `proposals/trackp-evidence.sh`).
