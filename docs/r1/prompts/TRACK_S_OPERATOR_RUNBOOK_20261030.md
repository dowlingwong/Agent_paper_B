# Track S — operator runbook for TASL-2 (zhixu portal) and TASL-7 (revision 2)

**Written 30 Oct 2026 by the chat session (Claude) at the author's request; AI-assisted.** One operator agent (Claude Code), started by the author on the Mac with SSH access to both hosts, carries out this runbook phase by phase. Every phase ends with a **STOP**, an independent review and, where marked, an author decision. Do not skip a STOP.

Revision 2 addresses the independent review `docs/r1/reviews/TRACKS_OPERATOR_RUNBOOK_REVIEW_20261030.md` (REVISE: 5 BLOCKING, 8 MAJOR, 7 MINOR). The code was extended for it in paper commit `9bb64ba`. The mapping is in §12.

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
| Everything for `digits_mlp` (llama-servers, collectors, worker runs, audits) | **TASL-2**, `ssh portal_zhixu`, user `dowling`, 32 CPUs, 1 × RTX 4090, driver 535 / CUDA 12.2. Track X evidence has priority |
| Everything for `tabular_mlp` | **TASL-7**, Tailscale `tasl-7` (100.106.74.51), user `dowling`, 24 CPUs, 1 × RTX 4090, driver 580 / CUDA 13.0, **no sudo**, a pending reboot may happen. Track P evidence has priority. Record your SSH alias in Phase 0 |
| S0.6 synthetic calibration, `breast_w` S1.1 | Mac or the container (CPU, no LLM) |
| Author | Commits the pre-declaration (S0.8) and the authorization note (S0.9); decides where marked |

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
- **injects the pinned LLM flags** (`--manager llamacpp --manager-model llamacpp/r1-manager --proposal-schema manager_proposal/v1 --gguf … --llama-build 620d2225… --llama-server-bin … --host-label … --gpu …`) into every `collect` call of an LLM phase.

Use only `trks collect …` and `trks analyze …` on the hosts. Never call `python -m r1.tracks.collect` directly for an LLM phase. (The code also refuses EVIDENCE without the llama.cpp manager and its pins.)

### 0.4 GPU lease, priority and pauses

- **Servers hold the lease for their whole life.** Start them only as `tmux new -d -s trks_llm /home/dowling/r1_tracks/bin/trks-servers <k>` (template §11.2). The script runs `flock -n ~/r1_locks/gpu0.lock`. **Inside the tmux pane**, it starts k servers and `wait`s, so the lock is held exactly as long as the servers live. If the lock is taken, the script exits at once and nothing starts.
- **Before starting the servers,** check:
  1. On TASL-2, that `~/r1_locks/trackx_evidence.active` is absent.
  2. On TASL-7, that `~/r1_locks/trackp_evidence.active` is absent. This marker must be created by Track P for its evidence runs; the author arranges it in Phase 0. Also check that no `r1p_*` tmux session is running a GPU job.
  3. That `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` lists no compute process.
- **Watcher.** `tmux new -d -s trks_watch /home/dowling/r1_tracks/bin/trks-watch` (template §11.3). It polls every 60 s. If a priority marker appears, it touches every running collector's `STOP` file. When those collectors have exited (status "paused", exit 0), it stops our servers, which releases the lock. **A pause is not a failure.** Resume later with the same commands; every unit is resumable.
- **Ownership.** Never kill or signal a process you did not start.

### 0.5 Shards

- **Choosing k.** After S0.1, each host gets **k = 2** servers (ports 18101 and 18102) if setting (b) passed 100 % within-server identity, else **k = 1** (port 18101). k is **fixed for the node from then on**.
- **Running.** Every LLM phase except S0.4, S0.5 and the exact placebo runs as k processes: `TRKS_PORT=1810<i+1> trks collect … --shard <i>/<k> --out <OUT>/<phase>_s<i> --work <WORK>/<phase>_s<i>`. Each process runs in its own tmux session `trks_<phase>_s<i>`.
- **Pairing.** The shard map (instance index mod k) is the same in every phase, so all policies of an instance use the same server. Pairing does not require the two servers to be identical to each other.

### 0.6 Sessions, health and failures

- **Deadline and stop file.** Every collector call carries `--deadline 28800` (8 h), so it stops scheduling new units after 8 h, and `--stop-file <its OUT>/STOP`. Restart a stopped or paused session with the identical command: it resumes.
- **Exit codes.**
  - **3** ("STOP: server unhealthy", after 3 consecutive transport or health failures): check the server log. Restart the servers once through `trks-servers`. If the next session also exits 3, **STOP** for the author.
  - Any other non-zero exit is a STOP. Read the manifest and `failed_units.jsonl`.
- **Retries.** A unit that fails `--max-retries` times stays in `failed_units.jsonl` and is never counted as done. More than **2 %** failed units in a phase is a STOP.
- **Checks.** At every working session, check `tmux ls`, each manifest's progress and status, `failed_units.jsonl`, `nvidia-smi` and the server logs. `trks-status` (§11.4) prints all of this.

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
- **Copy-back after every phase.** `rsync -a` the whole `<OUT>/<phase>*` trees (not `<WORK>`) from the host to the Mac under `results/r1/tracks/<node>/<phase>/`. Commit JSON, manifests and `.jsonl` files up to 20 MB; gzip larger `.jsonl` files (`assemble` reads `.jsonl.gz`) and record their sha256 in a `SHA256SUMS` file. `<WORK>` stays on the host until Track S is closed. S0.5b needs it.
- **Reports.** `docs/r1/reports/TRACKS_<phase>_<date>.md`, a STATUS entry, and a message to the author with what was done, the commits, the checks, the verdict and any questions.
- **Commits.** Author `Dowling Wong <wangdowling@gmail.com>`, with each message ending in the attribution lines the coordinating session gives you. Push `trackS-ops-*` to the hosts' bare repositories and, where the Mac has credentials, to GitHub. Never push `main`, `r1` or `exam-x-*`. Never force-push.

## Phase 0 — Code, host facts, environments, build (both hosts; ½–1 day)

**0.1 Code on the Mac.**
- In the author's checkout: `git fetch .claude-worktrees/_snapshots/trackS_30oct.bundle trackS-20261029:trackS-20261029 docs/trackS-decisions-30oct:docs/trackS-decisions-30oct`.
- Verify `trackS-20261029` = `9bb64ba` and the docs head recorded in PLAN R1-REPO-ACCESS.
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

**0.3 Author items (STOP 0 cannot pass without them).**
- (a) Approve the work directory `/home/dowling/r1_tracks/` on both hosts.
- (b) Arrange that Track P creates and removes `~/r1_locks/trackp_evidence.active` around its evidence runs on TASL-7.
- (c) Confirm the SSH aliases.

**0.4 Transfer (R1-EXAM-TRANSFER).**
- On each host, create `/home/dowling/r1_tracks/{remotes,work,opt,models,bin,logs}`, with `git init --bare remotes/Agent_paper_B.git`.
- From the Mac, push `trackS-ops-<date>` and the tag `trackS-code-9bb64ba` to it.
- Clone into `work/Agent_paper_B` and `git checkout --detach 9bb64ba`.
- Harness: clone `https://github.com/dowlingwong/autoresearch_harness` into `work/autoresearch_harness` and `git checkout --detach 115df37`.

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

**0.9 Scripts.** Install `trks`, `trks-servers`, `trks-watch` and `trks-status` from §11 into `bin/`, filling the paths and pins.

**0.10 Smoke test (ENGINEERING_ONLY).**
1. Start `trks-servers 1` (under the lease) and confirm full offload in the log (`offloaded N/N layers`).
2. `trks collect --phase S0.4 --node <node> --instances 1 --dry-run --out <OUT>/smoke --work <WORK>/smoke --label ENGINEERING_ONLY`.
3. Then one real instance without `--dry-run`.
4. Stop the servers.

**Output:** `docs/r1/reports/TRACKS_HOST_FACTS_<date>.md`.

**STOP 0:** the review loop (the reviewer re-runs the facts, both test suites and the pin checks), plus the author items in 0.3.

## Phase 1 — S0.1 determinism, latency, CPU census (each host; < 1 GPU-h)

Start `trks-servers 2` (ports 18101 and 18102). Then:

```
trks probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --node <node> --server-args "<exact server command>" --out <OUT>/s01/serial.json
trks probe --url http://127.0.0.1:18101/v1 --url http://127.0.0.1:18102/v1 --mode concurrent --clients-per-url 2 \
  --n 200 --repeats 3 --order-seed 2 --proposal-schema manager_proposal/v1 --node <node> --server-args "…" --out <OUT>/s01/concurrent.json
```

`trks probe` is the wrapper around `python -m r1.tracks.probes.determinism`. It injects the GGUF, build and host flags.

**Done when:**
- **k = 2** if within-server identity is **100 %** in the concurrent run.
- Else **k = 1** if identity is 100 % in the serial run.
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
trks s11 --node digits_mlp --out <OUT>/s11/digits.json          # TASL-2
trks s11 --node tabular_mlp --out <OUT>/s11/tabular.json        # TASL-7
python -m r1.tracks.probes.s1_factorial --node openml_breast_w --pair max_iter:C --out s11_breast_w.json   # Mac / container
```

This is reported with the result. It is not a gate. It is reviewed together with Phase 3.

## Phase 3 — S0.4 dev campaigns, D28 liveness, A2-U prior (each node on its host; k servers may run, but S0.4 uses one process)

```
TRKS_PORT=18101 trks collect --phase S0.4 --node <node> --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file <OUT>/s04/STOP --out <OUT>/s04 --work <WORK>/s04
trks collect --phase liveness --node <node> --out <OUT>/s04          # exit 3 = STOP (node fails D28)
trks collect --phase fit_prior --node <node> --out <OUT>/s04 --sigma-node <σ_node> --obs-inflation 1.0 --prior <OUT>/a2u_prior.json
```

Here σ_node = 0.0066 for digits and 0.0019 for tabular (PLAN D18 table).

**Done when:**
- liveness passes;
- `a2u_prior.json` and its sha256 are recorded;
- failed units are ≤ 2 % and were retried.

**STOP 3:** the review loop, covering Phases 2 and 3.

## Phase 4 — S0.5 pilot, S0.5b truncation, summary

The declared price is g = 0.1 σ_node: digits **0.00066**, tabular **0.00019**. A2-U runs at g0 = g by default.

```
TRKS_PORT=18101 trks collect --phase S0.5 --node <node> --prior <OUT>/a2u_prior.json --prior-sha256 <sha> --obs-inflation 1.0 \
  --W 40 --instances 20 --policy "static:<0.3·σ_node>,0" --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 \
  --label ENGINEERING_ONLY --deadline 28800 --stop-file <OUT>/s05/STOP --out <OUT>/s05 --work <WORK>/s05
trks collect --phase S0.5b --node <node> --truncate-W 8,10,12,20 --out <OUT>/s05 --work <WORK>/s05
```

- A fork-rebuild mismatch or an A/A mismatch here is a STOP (design §10).
- Copy `<OUT>/s05` from both hosts to the Mac. It must include `s05_calibration.jsonl` and `s05b_truncated.jsonl`.
- Then, on the Mac:
  `python -m r1.tracks.analyze s05-summary --node digits_mlp=<MAC>/s05_digits --node tabular_mlp=<MAC>/s05_tabular --out <MAC>/s05_summary.json`
  It prints `values`: W, σ_cmp,vary, σ_D UCL, the between-repetitions UCL, `between_policy_sd_at_cap`, the near band b, the calibration status and λ.

**Calibration gate.** If coverage is outside [0.70, 0.90] for a node:
1. Set **λ₂ = max(1, (q₉₀ / 1.2816)²)**, where q₉₀ is the 90th percentile of |z| over that node's `s05_calibration.jsonl`, and z = (audited Δ − predictive mean) / predictive sd. Use the documented snippet in §11.5, and record λ₂.
2. `trks collect --phase set_obs_inflation --node <node> --prior <OUT>/a2u_prior.json --obs-inflation <λ₂> --prior-out <OUT>/a2u_prior_l2.json`
3. Re-run S0.5 and S0.5b into **new** `--out` and `--work` (`s05_l2`), with the new prior and `--obs-inflation <λ₂>`. Every later command uses this prior and λ₂. The code refuses a mismatch.
4. A second failure is a **STOP**.

**Fallback.** Using the Phase 1 projection, a node whose projected S0.7 + S3a + S3e exceeds 4 days drops from the decision now. The author confirms. It is never revisited after outcomes exist.

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

1. **Statics: 15 configurations × 20 paired dev instances.** For i in 0…k−1, each in its own tmux session:
   ```
   TRKS_PORT=1810<i+1> trks collect --phase tune --node <node> --prior <P> --prior-sha256 <s> --obs-inflation <λ> --W <W> \
     --tune-grid static --sigma-cmp-vary <σ_cmp,vary> --shard <i>/<k> --label ENGINEERING_ONLY --deadline 28800 \
     --stop-file <OUT>/tune_static_s<i>/STOP --out <OUT>/tune_static_s<i> --work <WORK>/tune_static_s<i>
   ```
   Copy back, then on the Mac:
   ```
   python -m r1.tracks.collect assemble --node <node> --out <ND> --dev <tune_static_s0 … s<k-1>>
   python -m r1.tracks.analyze select --predeclaration <MAC>/predecl_draft.json --node <node>=<ND> --out <MAC>/sel1_<node>.json
   ```
2. **Extension, only if `values.extension_configs` is set.** The same command with `--tune-g-extension-only` in place of `--tune-grid static`, writing to `tune_ext_s<i>`. Re-assemble and select again.
3. **Members: 4 centred members × 40 paired dev instances.**
   ```
   TRKS_PORT=… trks collect --phase tune --node <node> … --tune-grid dynamic --sigma-cmp-vary <σ> --m-star "<m*>" \
     --centres-from <ND>/dev_roots.jsonl --shard <i>/<k> … --out <OUT>/tune_mem_s<i> --work <WORK>/tune_mem_s<i>
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
TRKS_PORT=… trks collect --phase S3 --node <node> --prior … --obs-inflation <λ> --W <W> --root-policy "<m*>" \
  --instances 30 --forks 4 --near-band <b> --p-near 0.5 --aa-fraction 0.1 --reps 2 --reps-ordinary 1 \
  --shard <i>/<k> --label EVIDENCE --deadline 28800 --stop-file <OUT>/s3a_s<i>/STOP --out <OUT>/s3a_s<i> --work <WORK>/s3a_s<i>
```

Copy back, then assemble (all dev dirs plus `--fork` with every `s3a_s*`). On the Mac, freeze π′:

```
python -m r1.tracks.analyze fit-policy --predeclaration <PREDECL_FINAL> --node <node>=<ND> --out-dir <MAC>/pi_prime
```

Record the sha256 of `<node>.pi_prime.json` and copy the file to the host.

**8.2 S3e.** The exact placebo runs **first and alone**, then the shards:

```
S3E="--W <W> --instances 300 --policy '<π*>' --policy '<m*>' --policy '<matched static>' \
     --placebo-policy '<m*>' --exact-placebo-n 10 --descriptive-placebo-n 15"
TRKS_PORT=18101 trks collect --phase campaign --node <node> --prior … --obs-inflation <λ> $S3E --exact-placebo-only \
  --label EVIDENCE --deadline 28800 --stop-file <OUT>/s3e_placebo/STOP --out <OUT>/s3e_placebo --work <WORK>/s3e_placebo
# only after the placebo run finished with no mismatch:
TRKS_PORT=1810<i+1> trks collect --phase campaign --node <node> --prior … --obs-inflation <λ> $S3E --shard <i>/<k> \
  --label EVIDENCE --deadline 28800 --stop-file <OUT>/s3e_s<i>/STOP --out <OUT>/s3e_s<i> --work <WORK>/s3e_s<i>
TRKS_PORT=… trks collect --phase campaign --node <node> … --W <W> --instances 30 --policy '<best member, other channel 1>' \
  --policy '<best member, other channel 2>' --shard <i>/<k> --label EVIDENCE … --out <OUT>/s3e_other_s<i> --work <WORK>/s3e_other_s<i>
TRKS_PORT=… trks collect --phase campaign --node <node> … --W <W> --instances 30 --policy a2u \
  --policy 'pi_prime:<path>/<node>.pi_prime.json' --shard <i>/<k> --label EVIDENCE … --out <OUT>/s3e_sec_s<i> --work <WORK>/s3e_sec_s<i>
```

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
R=/home/dowling/r1_tracks; . $R/venv/bin/activate
export AR_HARNESS_ROOT=$R/work/autoresearch_harness OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd $R/work/Agent_paper_B
PIN="--manager llamacpp --manager-model llamacpp/r1-manager --proposal-schema manager_proposal/v1 \
 --gguf $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --gguf-sha256 509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c \
 --llama-build 620d2225cc436ab0b001e3200e590e3b286ef9ab --llama-server-bin $R/opt/llama.cpp/build/bin/llama-server \
 --host-label <TASL-2|TASL-7> --gpu 'NVIDIA GeForce RTX 4090'"
sub=$1; shift
case "$sub" in
  collect)
    phase=$(printf '%s\n' "$@" | grep -A1 -x -- --phase | tail -1)
    case "$phase" in
      S0.4|S0.5|S3|tune|campaign)
        : "${TRKS_PORT:?set TRKS_PORT}"; export LLAMACPP_BASE_URL=http://127.0.0.1:$TRKS_PORT/v1
        exec python -m r1.tracks.collect "$@" $PIN ;;
      *) exec python -m r1.tracks.collect "$@" ;;
    esac ;;
  analyze) exec python -m r1.tracks.analyze "$@" ;;
  probe) exec python -m r1.tracks.probes.determinism "$@" --host-label <TASL-x> \
           --gguf $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --gguf-sha256 509287f7…  --llama-build 620d2225… \
           --llama-server-bin $R/opt/llama.cpp/build/bin/llama-server ;;
  s11) exec python -m r1.tracks.probes.s1_factorial "$@" ;;
  *) echo "unknown subcommand" >&2; exit 2 ;;
esac
```
Write the full hashes in place of the "…". Check that the pin flags match `collect --help` and the probe's `--help` exactly. If a flag differs, fix the template, never the code.

### 11.2 `bin/trks-servers <k>`
```bash
#!/usr/bin/env bash
# run as: tmux new -d -s trks_llm /home/dowling/r1_tracks/bin/trks-servers <k>
set -euo pipefail
R=/home/dowling/r1_tracks; k=${1:?k}
for f in ~/r1_locks/trackx_evidence.active ~/r1_locks/trackp_evidence.active; do [ -e "$f" ] && { echo "priority marker $f"; exit 1; }; done
exec flock -n ~/r1_locks/gpu0.lock bash -c '
  R=/home/dowling/r1_tracks
  for i in $(seq 1 '"$k"'); do
    $R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager \
      --host 127.0.0.1 --port 1810$i -ngl 999 -c 8192 --parallel 1 --verbose > $R/logs/llama_1810$i.log 2>&1 &
  done
  wait'
```
`flock -n` holds the lock for as long as the inner bash, and therefore the servers, live. If the lock is taken, it exits at once.

### 11.3 `bin/trks-watch`
```bash
#!/usr/bin/env bash
# run as: tmux new -d -s trks_watch /home/dowling/r1_tracks/bin/trks-watch
R=/home/dowling/r1_tracks
while sleep 60; do
  if [ -e ~/r1_locks/trackx_evidence.active ] || [ -e ~/r1_locks/trackp_evidence.active ]; then
    for m in $(find $R/work/out -name manifest.json -newer $R/logs/watch_started 2>/dev/null); do touch "$(dirname "$m")/STOP"; done
    # wait for our collectors (tmux sessions trks_<phase>_*) to exit, then stop our servers
    while tmux ls 2>/dev/null | grep -q '^trks_\(s0\|tune\|s3\|campaign\)'; do sleep 30; done
    tmux kill-session -t trks_llm 2>/dev/null
    echo "$(date -u) paused for priority marker" >> $R/logs/watch.log
  fi
done
```
Create `logs/watch_started` before starting the watcher. Remove the `STOP` files before resuming. Adapt the session-name pattern to the names you use; keep every Track S session prefixed `trks_`.

### 11.4 `bin/trks-status`
A script that prints `tmux ls`, `nvidia-smi` (compute apps), the last lines of each server log, and, for each `<OUT>/*/manifest.json`, the phase, shard, status, units done/total and the `failed_units.jsonl` count.

### 11.5 λ₂ snippet
```python
import json, numpy as np
z = [(r["delta_audit"] - r["pred_mean"]) / r["pred_sd"] for r in map(json.loads, open("s05_calibration.jsonl"))]
q90 = float(np.quantile(np.abs(z), 0.9)); lam2 = max(1.0, (q90 / 1.2816) ** 2); print(q90, lam2)
```
Check the field names against `s05_calibration.jsonl` before use, and record the output.

## 12. Review record

**Revision 1 → 2** (`reviews/TRACKS_OPERATOR_RUNBOOK_REVIEW_20261030.md`, REVISE). Code changes are in `9bb64ba`.

| Finding | Resolution |
|---|---|
| B1: lease not held | `trks-servers` holds `flock` inside the tmux pane for the servers' lifetime (§0.4, §11.2) |
| B2: 2 servers × 2 campaigns not implemented | Code: `--shard i/k`, an own URL per process, `--exact-placebo-only`, assemble checks. Runbook: k per host from S0.1, a fixed map, the placebo run alone and first (§0.5, Phase 8) |
| B3: S0.5 / S0.5b commands | One S0.5 call with `--W 40 --rep 0 --rep 1 --rep-instances 10 --forks 1.5`; S0.5b uses the recorded `--work` and refuses otherwise (code) |
| B4: S3a and π′ | `--instances 30 --forks 4 --near-band b --p-near 0.5`; `--a2-fraction` defaults to 0 (code); `analyze fit-policy` needs no S3e (code) |
| B5: λ not carried | λ recorded in the prior; later phases refuse a mismatch (code); the λ₂ rule and a new `--out` (Phase 4, §11.5) |
| M1: missing manager flags | The `trks` wrapper injects pins; the code requires `--manager` and refuses EVIDENCE without the pins |
| M2: server crashes and priority | Health check, circuit breaker (exit 3) and `--stop-file` (code); 8 h deadline sessions; a watcher with priority markers; the Track P marker arranged by the author (Phase 0.3) |
| M3: extension re-runs everything | `--tune-g-extension-only` (code) |
| M4: S0.6 inputs; controls merge; label | `s05-summary` and `select` print the inputs; `--controls` is repeatable; the decision label comes from S3e only (code) |
| M5: provenance of docs and code | Bundle `trackS_30oct.bundle` with both branches; detached checkouts; design header 7.4; frozen venv |
| M6: copy-back list; gz | Whole `<OUT>` trees are copied back; `assemble` reads `.jsonl.gz` |
| M7: D28; S0.5 STOPs; Phase 5 STOP | `--phase liveness` in Phase 3; S0.5 fork and A/A STOPs; STOP 5 added |
| M8: pre-declaration template; ridge CV | `analyze predecl-template`; ridge λ by inner CV in `fit-policy` (code) |
| Minor | nvcc path and Release target; iomanip; pin by commit; GGUF revision and file; `--verbose`; uv and Python 3.11 user install; BLAS threads; repeatable `--url`; "other members" defined; TASL-7 reboot handling; projection formula |
