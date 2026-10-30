# Track S — independent review of operator Phase 0 (STOP 0)

**Reviewer.** Fresh independent reviewer; I did not see the operator's work in progress and did not accept
the operator's conclusions before checking them. I read the runbook, the design, the paper/harness code on
the hosts and re-ran the checks myself.

**Artifacts under review.** Operator worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackS-ops-20261030`, branch
`trackS-ops-20261030`. The task names head `ddf8f08d`; the worktree is now at **`62980aef`** (a report-only
commit, +4/−1 lines, adding the runbook sha256; see m8). I reviewed the tree at `62980aef`. The host bare
repositories are at `ddf8f08d`, and the host checkouts are detached at paper `9bb64ba` / harness `115df37`.

- Runbook: `docs/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, revision 3.2, sha256
  `1789c000dbeaaa96202e00d72714d6b5df4e87733ca8f5823b9afd01ac7091ab`.
- Design: `docs/trackS-decisions-30oct:docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`
  (rev. 7.4), §2, §9, §10.
- Deliverables: `docs/r1/reports/TRACKS_HOST_FACTS_20261030.md`, `r1/tracks/ops/*`,
  `r1/tracks/ops/host_setup/*`, `results/r1/tracks/*`, the top STATUS entry.

All dates/times below are UTC unless stated. The hosts' local zone is America/Los_Angeles (PDT, −0700).

## 1. Scope

Phase 0 of the runbook: code/provenance on the Mac (0.1), host facts (0.2), access and author items
(0.3), transfer (0.4), environments (0.5), both test suites (0.6), llama.cpp build (0.7), GGUF (0.8), ops
scripts (0.9), smoke test (0.10), the report, and **STOP 0** (reviewer re-runs the facts, both test suites
and the pin checks, plus item 0.3(c)).

I re-ran the checks from primary evidence on TASL-2 (`ssh portal_zhixu`) and TASL-7 (`ssh tasl7`). I did
not start a llama-server, did not modify pinned code, commits, GGUF, flags or server state, and left the
`trks_watch` watcher running. The only file I wrote is this review.

## 2. What I verified and how

### 2.1 Mac provenance (0.1)

```
$ shasum -a 256 .claude-worktrees/_snapshots/trackS_30oct.bundle
6e6d5e932637a3c548f516efaa3c4ad25761ebb5dadcc0d2d504cca54a56d8cf
$ git bundle verify .claude-worktrees/_snapshots/trackS_30oct.bundle
The bundle contains these 2 refs:
9bb64ba6712668c4bab4a66720cf7f2645e1c672 refs/heads/trackS-20261029
3ac0fbf4a7c18ce2abdc7096edea37f2d0aa2e39 refs/heads/docs/trackS-decisions-30oct
The bundle records a complete history.
$ git rev-parse trackS-20261029 docs/trackS-decisions-30oct
9bb64ba6712668c4bab4a66720cf7f2645e1c672
3ac0fbf4a7c18ce2abdc7096edea37f2d0aa2e39
$ git reflog show docs/trackS-decisions-30oct | head -2
3ac0fbf4 … fetch …: fast-forward
cdb3cdc3 … fetch …: storing head
$ git cat-file -t trackS-code-9bb64ba   → commit
$ git rev-parse trackS-code-9bb64ba^{commit}
9bb64ba6712668c4bab4a66720cf7f2645e1c672
$ git -C .claude-worktrees/trackS-ops-20261030 rev-parse HEAD
62980aefe16bcb2afcf555ddbbe25250f827218d
$ git -C .claude-worktrees/trackS-ops-20261030 log --oneline -3
62980aef Track S Phase 0 report: pin the runbook text by sha256 …
ddf8f08d Track S Phase 0: host facts, pinned environments, ops scripts, smoke test
9bb64ba6 Track S: ops-readiness fixes for the host operator
```

The `trackS_30oct.heads.txt` values match the bundle: paper `9bb64ba…`, docs `3ac0fbf4…`, bundle
`6e6d5e93…`. The docs branch was fast-forwarded `cdb3cdc3 → 3ac0fbf4` (reflog), as the report says. The
worktree's Phase 0 commits have `9bb64ba` as ancestor and add only `docs/`, `r1/tracks/ops/` and
`results/` paths; `git diff --name-only 9bb64ba..HEAD` contains **no** file outside those trees. The
pinned `r1/tracks/` and `r1/tests/` code is unchanged in the worktree.

The main working tree was not touched by the operator in a way that disturbs the pre-existing move:
`git status --short` in `agent_paper_B` still shows the `docs/r1/*` deletions (205 `D`) and the moved
files as untracked (15 `??`); HEAD is still `8a819f75`. The operator's `git fetch` added the two refs,
which runbook 0.1 instructs.

### 2.2 Pins and environments on both hosts (0.2, 0.4, 0.5, 0.7, 0.8)

On **both** hosts (`R=/home/dowling/r1_tracks`):

```
$ git -C $R/work/Agent_paper_B rev-parse HEAD           → 9bb64ba6712668c4bab4a66720cf7f2645e1c672
$ git -C $R/work/Agent_paper_B symbolic-ref -q HEAD    → (empty; detached)
$ git -C $R/work/Agent_paper_B status --porcelain      → (empty)
$ git -C $R/work/Agent_paper_B tag --list 'trackS-code-*' → trackS-code-9bb64ba
$ git -C $R/work/autoresearch_harness rev-parse HEAD   → 115df37d2b4581487eb2d911dc4d6a903afcc76a
$ git -C $R/work/autoresearch_harness symbolic-ref -q HEAD → (empty; detached)
$ git -C $R/work/autoresearch_harness status --porcelain   → (empty)
$ git -C $R/opt/llama.cpp rev-parse HEAD               → 620d2225cc436ab0b001e3200e590e3b286ef9ab
$ git -C $R/opt/llama.cpp describe --tags --exact-match → v0.7.0
$ $R/opt/llama.cpp/build/bin/llama-server --version
version: 0.7.0-dev (build 11669, commit 620d2225c)
built with GNU 11.4.0 for Linux x86_64
$ sha256sum $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c
$ $R/venv/bin/python -V       → 3.11.17 (TASL-2) / 3.11.18 (TASL-7)
$ sha256sum $R/logs/pip_freeze.txt → f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687 (both)
$ uv pip freeze --python $R/venv/bin/python | diff - $R/logs/pip_freeze.txt → FREEZE-MATCH (65 packages)
```

The bare repositories hold exactly the pushed branch/tag:

```
$ git -C $R/remotes/Agent_paper_B.git show-ref
ddf8f08d4cc7ba5f31a14014a1ef887197c52b7f refs/heads/trackS-ops-20261030
9bb64ba6712668c4bab4a66720cf7f2645e1c672 refs/tags/trackS-code-9bb64ba
$ git -C $R/remotes/Agent_paper_B.git rev-parse ddf8f08d^{tree}
2190a1fbef84425fc7cd9a6a48f1fb39ad920e62   # equals the Mac's ddf8f08d tree
```

The paper clone's `origin` is the host bare repo. The harness clone's `origin` is
`https://github.com/dowlingwong/autoresearch_harness`; `git ls-remote origin` lists
`115df37… refs/heads/trackS-20261029`, so the fallback through a second bare repository was not needed.
The build scripts are in `r1/tracks/ops/host_setup/tasl{2,7}/build_llama.sh`; the logs record
`CONFIGURE_RC=0`, `BUILD_RC=0`, `Using CMAKE_CUDA_ARCHITECTURES=89`, `ggml commit: 620d2225c`,
`CUDA host compiler is GNU 11.4.0`, `Including CUDA backend`. TASL-2's configure used
`/usr/local/cuda/include` (the `/usr/local/cuda` symlink) and TASL-7's used `/usr/local/cuda-12.2/include`
(there is no `/usr/local/cuda` symlink on TASL-7); both nvcc calls are `/usr/local/cuda-12.2/bin/nvcc`.

The GGUF download script uses the pinned `resolve/13fb94bf…/` URL; the host `logs/get_gguf.log` records
`CURL_RC=0`, the size `4683073536`, the sha256 above and `SHA_RC=0` on both hosts. `trks-status` re-hashes
the 4.7 GB file and prints `OK 509287f7…` on both hosts.

### 2.3 Both test suites on both hosts (0.6)

Run exactly as requested, from `$R/work/Agent_paper_B` with `$R/venv` active and
`AR_HARNESS_ROOT=$R/work/autoresearch_harness`:

```
$ python -m pytest -q -p no:cacheprovider r1/tests/test_tracks_*.py
168 passed in 248.88s (0:04:08)          # TASL-2, my re-run
168 passed in 264.55s (0:04:24)          # TASL-7, my re-run
$ python -m pytest -q -p no:cacheprovider tests/stage2/test_r1_track_s_arms.py
14 passed in 0.33s                       # TASL-2
14 passed in 0.35s                       # TASL-7
```

Exit codes 0 in every case. The operator's original logs record `168 passed in 323.69s` (TASL-2) and
`351.03s` (TASL-7), and `14 passed` on both; my counts match, the times differ only with machine load.
I reproduced the documented console-script failure:

```
$ pytest -q -p no:cacheprovider r1/tests/test_tracks_a2u.py
E   ModuleNotFoundError: No module named 'r1'
1 error in 0.13s       # rc=2
$ python -m pytest -q -p no:cacheprovider r1/tests/test_tracks_a2u.py
17 passed in 1.06s     # rc=0
```

The repo Makefile's `r1-test` target runs `$(R1_PY) -m pytest -q -p no:cacheprovider r1/tests`, so the
operator's `python -m pytest` deviation is the repo's own convention and is correctly documented. No code
was changed.

### 2.4 Host facts (0.2)

Spot-checked on both machines:

| Fact | TASL-2 | TASL-7 | Report |
|---|---|---|---|
| hostname / uid | TASL-2 / 1008(dowling) | TASL-7 / 1011(dowling) | matches |
| nproc | 32 | 24 | matches |
| RAM (`free -g`) | 62 total, 56 available | 62 total, 58 available | 57/58 (dynamic) |
| `/home/dowling` | 1.9 T, 264 G avail, 86 % | 1.9 T, 910 G avail, 49 % | 269 G/85 %, 917 G/49 % (dynamic) |
| GPU | RTX 4090, 24564 MiB, `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01, CUDA 12.2 | RTX 4090, 24564 MiB, `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, driver 580.178.04, CUDA 13.0 | matches |
| CUDA toolkits | `/usr/local/cuda`, `-12`, `-12.2` (V12.2.140) | `-11.7`, `-12.2` (V12.2.91), no `/usr/local/cuda` | matches |
| cmake/gcc/git/tmux/flock | 3.22.1 / 11.4.0 / 2.34.1 / 3.2a / util-linux 2.37.2 | same | matches |
| python3 | 3.10.12, no `ensurepip` | 3.10.12, `ensurepip` present | matches |
| clock | PDT, `System clock synchronized: no` | PDT, synchronized: yes | matches |
| network | hf/github/astral 200/200/200 | same | matches |
| `~/r1_locks` | only `gpu0.lock` | only `gpu0.lock` | matches; **no Track P marker** |
| tmux | `12` (claude, `~/Agent_paper_B`), `r1p_agent` (bash, `~/Agent_paper_B`), `trks_watch` | `trks_watch` | matches |
| GPU compute apps | none | none | matches |

The two Track P `llama-server` processes on TASL-2 are still alive and predate Phase 0 (`lstart` Mon 26 Oct
02:43 and 03:05), so they were not killed or restarted by the operator. The `12` and `r1p_agent` tmux
sessions are likewise still alive. `nvidia-smi --query-compute-apps` is empty on both hosts.

### 2.5 Ops scripts (0.9)

The installed scripts are byte-identical to the committed templates with only the per-host fills:

```
TASL-2 trks dca17a7d748c63b9f85a1798d385767b39a02356c9f6300f8d35b0d295cd38f4   (computed locally: same)
TASL-7 trks 26a240fa350b217c6c8fc6400f9da8e8c3163675719a96402dd9a96d1a577506   (computed locally: same)
trks-run b53bc811… / trks-servers 47dcf336… / trks-watch 3108566d… / trks-status 0616c41a… (identical both)
```

`bash -n` passes for all five installed scripts and for `install.sh` on both hosts. The wrapper's injected
flags all exist in the collector and probe CLIs (`--manager`, `--manager-model`, `--proposal-schema`,
`--gguf`, `--gguf-sha256`, `--llama-build`, `--llama-server-bin`, `--host-label`, `--gpu`; probe:
`--host-label`, `--gguf`, `--gguf-sha256`, `--llama-build`, `--llama-server-bin`). I exercised the wrapper
on both hosts:

```
$ TRKS_PORT=18101 trks collect --phase=S0.4 … --manager llamacpp …
trks: --manager is injected by the wrapper; do not pass it        # rc=2
$ TRKS_PORT=18101 trks collect --phase S0.4 … --gpu GPU-x …
trks: --gpu is injected by the wrapper; do not pass it            # rc=2
$ TRKS_PORT=18101 trks collect --phase=S0.4 --node … --dry-run --label ENGINEERING_ONLY
{"dry_run": true, "manifest": {… "manager": {"kind": "langgraph", "model": "llamacpp/r1-manager",
 "proposal_schema": "manager_proposal/v1"}, … "g_declared": 0.00066/0.00019, "host": "TASL-2"/"TASL-7"}}
$ TRKS_PORT=18101 trks collect --phase S0.4 … --dry-run …          # same plan, pins injected
$ trks collect assemble --help                                     # reaches Python, no pins
```

Both `--phase X` and `--phase=X` are parsed; the dry run writes nothing (the `--out` path I used did not
appear). `collect assemble` bypasses the pins (`collect.main` dispatches `assemble` before `parse_args`).
`trks-status` runs to completion on both hosts and prints the GGUF re-hash, `llama-server --version`,
`tmux ls`, the compute-apps query, the server/watch log tails, every `*.exit` line, and every manifest's
phase/status/roots/failed_units. The `trks-run` `.cmd` files on the hosts reproduce the exact collector
commands; the `trks-servers` script contains the pinned flag string verbatim
(`-ngl 999 -c 8192 --parallel 1 --verbose --alias r1-manager --host 127.0.0.1 --port 1810$i`).

The watcher is running on both hosts (`tmux ls` → `trks_watch`; `pgrep -a -f trks-watch` → the process;
`logs/watch.log` has the start line; `logs/watch_started` exists). It logs nothing further because no
priority marker exists, which is the expected idle state.

### 2.6 Smoke test, outputs and logs (0.10)

- **Full offload.** Both `$R/logs/llama_18101.log` files contain
  `load_tensors: offloaded 29/29 layers to GPU`; the runtime line records `CUDA : ARCHS = 890`, i.e. sm_89.
- **Dry run.** `.cmd`/`.exit`/`.log` exist on both hosts; `rc=0`; the plan and manifest carry
  `host: TASL-2`/`TASL-7`, `g_declared` 0.00066 / 0.00019 (0.1 σ_node), `W=40`, `K=5`, `seed_base=30000`
  and the pinned manager/schema.
- **Real instance.** TASL-2: one root `ok`, `$OUT/smoke`, 102 s, `failed_units=0`. TASL-7: attempt 1
  (session `trks_smoke`) exited 0 with `roots=0 failed=1`; the root is in `failed_units.jsonl` with
  `error_class r1.c3.features.ReplayError` and `"trial 11: stale edit: HIDDEN_UNITS is '1024', edit
  expects '512'"`; attempt 2 (session `trks_smoke_retry`) exited 0 with `roots=1 failed=0`, 329 s.
- **`t_run`.** I recomputed from the logs: digits `n=77, mean 0.909, median 0.8, max 1.9`; tabular, both
  attempts together `n=165, mean 1.847, median 1.4, max 4.6`; retry alone `n=155, mean 1.914, median 1.9,
  max 4.6`. The report's digits and combined-tabular numbers are exact (the basis is noted in m7).
- **Lease.** On both hosts `nvidia-smi --query-compute-apps` is empty and
  `flock -n ~/r1_locks/gpu0.lock echo LOCK-FREE` prints `LOCK-FREE`; the `trks_llm` session is gone.
- **Copy-back.** `results/r1/tracks/{digits_mlp,tabular_mlp}/smoke/` is byte-identical to the hosts'
  `$OUT/smoke` trees (sha256 per file checked): manifest, roots, s04_rows, audit_runs, failed_units and
  the `failures/` payload on TASL-7. `$WORK/smoke` remains on both hosts, as required.

### 2.7 Safety, provenance and non-interference

- No evidence of a killed unowned process: the Track P servers and both pre-existing tmux sessions
  predate Phase 0 and are alive; no `trks_llm` session remains.
- The pinned commits, tag, GGUF, llama.cpp build and server flags are exactly as pinned on both hosts; the
  paper and harness checkouts are clean and detached; the venv freeze matches `pip_freeze.txt` exactly.
- The `ENGINEERING_ONLY` label is on both smoke manifests and on every output the report presents; the
  report's §4 explicitly defers the projection and presents no result. Nothing is worded as a Track S
  result.
- Writes outside `/home/dowling/r1_tracks` did occur: the runbook-mandated uv installer rewrote
  `~/.bashrc`, `~/.profile`, `~/.zshrc` and `~/.config/fish/conf.d/uv.env.fish` and wrote `~/.local`,
  `~/.cache/uv` and `~/.config/uv` on both hosts at 17:56–17:57 (m4). No other out-of-tree writes were
  found; `~/r1_locks` contains only `gpu0.lock`.
- The main Mac tree's uncommitted `docs/r1/*` move is intact; the operator's only writes there are the
  two fetched refs.
- No branch was pushed to GitHub: `git ls-remote --heads origin trackS-ops-20261030` is empty although
  `origin` is GitHub and `credential.helper=osxkeychain`; the branch is on both host bare repositories
  (m9). The report does not claim a GitHub push.

## 3. Findings

### 3.1 Table

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| **B1** | **BLOCKING** | Runbook item **0.3(c)** is not met: the author has not arranged the `~/r1_locks/trackp_evidence.active` marker on TASL-7, so **STOP 0 cannot pass** and Phase 1 must not start. The operator cannot create it and correctly says so. | `ls -la ~/r1_locks` on both hosts: only `gpu0.lock`; no marker. Report §5.2 (lines 244–246) and §6 ("Not ready"). Runbook lines 143 and 184: "Still needed before STOP 0 passes" / "STOP 0: … plus item 0.3(c)". |
| **M1** | **MAJOR** | The pinned code has a real stale-proposal failure mode: at E2, A2-U's `decide → _e2_detail → forecast → replay → featurize → candidate → apply_edit` raises `ReplayError` for a manager proposal whose `old` value is no longer current, and the whole root unit is logged failed. The harness's own `PROPOSAL_PRECONDITION_FAILED` guard tolerates the same event, so this is a controller-side robustness gap, not a corrupt ledger. It occurred once on TASL-7 (trial 11), recovered on retry, and is exactly the kind of stochastic loss that the runbook's >2 % STOP rule and S0.7/S3e scale make material. The operator did not change the pinned code and asked the author to choose between accepting retries and authorising a new pin. This is the right posture; the defect must be decided before S0.4/S0.7/S3e. | `results/r1/tracks/tabular_mlp/smoke/failures/root__tracks_S04_tabular_mlp__s30000.json` (full traceback through `campaign.py:1859`, `a2u.py:632/686/539/313`, `features.py:340/352/154`); `failed_units.jsonl`; `roots.jsonl` (`"status": "ok"` after the retry); report §5.1 (lines 209–240). |
| **m1** | MINOR (factual) | The report's smoke table says `s04_rows` 24 and audit runs 130 "(both attempts)". They are the **successful campaign alone**: the root has `eligible_e1 = 24`, `dev_rows` is called only after `run_real_campaign` returns (`collect.py:872`), and 24 × 5 audit seeds + 10 = 130. The failed attempt's session recorded `audit_runs: 0`, and the 24 rows have unique budget indices 2…39 (a second attempt would duplicate them). | `results/r1/tracks/tabular_mlp/smoke/{roots.jsonl,s04_rows.jsonl,manifest.json}`; `collect.py:872,988,1694`; TASL-7 manifest session 1 `audit_runs: 0`. |
| **m2** | MINOR (provenance) | The retry was **not** "the identical launch command": the successful session is `trks_smoke_retry`, with `logs/trks_smoke_retry.{cmd,log,exit}`; the failed attempt owns `trks_smoke`. The collector arguments are otherwise identical. Runbook 0.10 names the session `trks_smoke`; the successful run therefore does not satisfy that label. | `$R/logs/trks_smoke_retry.cmd` vs `$R/logs/trks_smoke.cmd`; both `.exit` files; report line 188 ("identical launch command"). |
| **m3** | MINOR (provenance) | The GGUF download log was not copied back. `r1/tracks/ops/host_setup/tasl{2,7}/` contains `build_llama.log`, `tests.log`, `watch.log`, `pip_freeze.txt` but no `get_gguf.log`; the host `$R/logs/get_gguf.log` does exist and records `CURL_RC=0`/`SHA_RC=0` and the pinned sha256. The report §7 says the setup scripts and "their logs" are committed. | `find r1/tracks/ops/host_setup -type f`; `ssh … sha256sum $R/logs/get_gguf.log`; report lines 266–267. |
| **m4** | MINOR (scope wording) | The report's "work directory … used exclusively" / "nothing outside it is written, except the lease lock" is not literally true: the runbook-mandated uv installer modified `~/.bashrc`, `~/.profile`, `~/.zshrc`, `~/.config/fish/conf.d/uv.env.fish`, `~/.local`, `~/.cache/uv` and `~/.config/uv` on both hosts. This is a consequence of runbook §0.5, not operator misconduct, but it should be disclosed and §0.3(b) reconciled with §0.5. | `ls -l --time-style=full-iso ~/.bashrc ~/.profile ~/.zshrc` (17:56/17:57); `grep -n 'local/bin/env' ~/.bashrc ~/.profile ~/.zshrc`; report lines 88–90. |
| **m5** | MINOR (wording) | "The controller hook … runs **before** that guard in the decision path" is imprecise. The E1 precondition guard (`campaign.py:1513`) runs first and tolerates the stale edit (no worker run); the **E2** `_controller_hook` (`campaign.py:1859`) still receives the raw proposal and crashes. The substantive diagnosis (guard tolerates, controller does not) is correct. | `campaign.py:1513–1523` vs `:1859`; failure traceback; report lines 214–217. |
| **m6** | MINOR (wording) | "the unit is lost" overstates the observed event: the unit is logged failed and retried, and the retry succeeded; it is permanently lost only after `--max-retries`. The report's §5.1 later says this correctly. | `failed_units.jsonl` + `roots.jsonl` (`status: ok`); report lines 219–220. |
| **m7** | MINOR (method) | The tabular `t_run` (1.847 s) is computed over both attempts (`n=165`), including the failed attempt's 10 early runs. The completed retry alone is `n=155, mean 1.914 s`; the projection's CPU term is therefore understated by about 3.6 %. The report should state which basis is used. | My recomputation from `trks_smoke.log` (n=10) and `trks_smoke_retry.log` (n=155); report line 186. |
| **m8** | MINOR (provenance) | The task/pin names `ddf8f08d`, but the worktree HEAD is `62980aef` (a report-only +4/−1-line commit adding the runbook sha256, committed 51 s later). The host bare repositories are at `ddf8f08d`; the report's host-pushed phase commit is therefore not the Mac HEAD. Review covers `62980aef`. | `git log --format='%h %cI %s' -3`; `git -C $R/remotes/Agent_paper_B.git show-ref`. |
| **m9** | MINOR (provenance) | `trackS-ops-20261030` was not pushed to GitHub: `git ls-remote --heads origin trackS-ops-20261030` is empty (origin is GitHub; `credential.helper=osxkeychain`). The branch/tag are on both host bare repositories. Runbook §0.8's GitHub push is conditional ("where the Mac has credentials"), and the report does not claim it; still, the backup/provenance trail is local-plus-hosts only. | `git ls-remote --heads origin 'trackS-ops-20261030'` → no output; `git remote -v`; `git config --get credential.helper` → `osxkeychain`. |
| **m10** | MINOR (process) | `failed_units.jsonl` is an attempt log, not a permanent-failure list; `trks-status` prints `failed_units=1` for the TASL-7 unit that later succeeded (manifest `done.failed=0`, `roots=1/1`). The §0.6 ">2 % failed units in a phase" check therefore needs a clarified denominator (permanently failed units, not attempts) before S0.4/S0.7/S3e. | `trks-status` on TASL-7 → `session_failed=0 failed_units=1`; `failed_units.jsonl`; `collect.py` `failed_attempts()`/`log_failed_unit()`; report §0.6. |
| **m11** | MINOR (ops gap) | `trks-status` re-checks the GGUF and `llama-server --version` but not the paper/harness HEADs against the pins. §11.5 does not require it, but a commit drift between stops would not be flagged by the tool the runbook tells the operator to use at every session. | `trks-status` script; §11.5; report line 155. |
| **m12** | MINOR (cosmetic) | "Host timestamps below are UTC" is true for the manifest and `trks-run` `.exit` lines, but the Python collector logs use local PDT with no zone (`2026-10-29T18:17:14`), and the report's session table quotes the UTC manifest times. Worth a one-line note. | `$R/logs/trks_smoke.log` starts `2026-10-29T18:17:14`; manifest `20261030T011713Z`; report line 12. |
| **m13** | MINOR (cosmetic) | "`uv` at Phase 0 start: absent" is ambiguous: `~/.local/bin/uv` existed (mtime 26 Oct) but was not on `PATH`; the install receipt and `env` files are 29 Oct, so an installer run is plausible. No uv install log was committed. This does not affect the environment. | `ls -l ~/.local/bin/uv` (26 Oct); `~/.config/uv/uv-receipt.json`; `~/.local/bin/env` (29 Oct); report line 46. |

### 3.2 Notes on severity

- **B1** is the only finding that stops STOP 0 by itself. It is an author item, not an operator defect.
- **M1** does not invalidate the Phase 0 setup, but it is a real pinned-code defect that can lose root
  units and can interact with the >2 % STOP rule; it must be decided before Phase 3/8. It also reinforces
  why the operator was right not to start Phase 1 without a STOP 0 decision.
- **m1–m13** do not change the technical conclusions; m1/m2/m3/m4/m8/m9 are provenance/documentation
  corrections, m5/m6/m12/m13 are wording, m7 is a small projection-basis bias, and m10/m11 are
  operational clarifications for later phases.

## 4. Acceptance criteria checklist (runbook Phase 0 / STOP 0)

| Runbook item | Status | Evidence / reason |
|---|---|---|
| 0.1 Code on the Mac | **PASS** | Bundle sha256 and `git bundle verify`; heads match; docs branch fast-forwarded; worktree from `9bb64ba`; tag `trackS-code-9bb64ba` → `9bb64ba`. |
| 0.2 Host facts | **PASS** | All table rows spot-checked; only dynamic RAM/disk values differ; clocks, CUDA, GPU UUID, tools, network, locks, tmux match. |
| 0.3(a) SSH access | **PASS** | `ssh portal_zhixu 'hostname; id'` → TASL-2/dowling; `ssh tasl7 …` → TASL-7/dowling; no password prompt. |
| 0.3(b) Work directory | **PASS with caveat** | `/home/dowling/r1_tracks` used; only `gpu0.lock` in `~/r1_locks`; no writes to Track X/P trees. The uv installer wrote `~/.bashrc`, `~/.profile`, `~/.zshrc`, fish conf and uv caches outside `$R` (m4); this is mandated by §0.5, but the report's "exclusively" wording is inaccurate. |
| 0.3(c) Track P marker | **FAIL** | No `~/r1_locks/trackp_evidence.active` on TASL-7; author action outstanding; STOP 0 cannot pass (B1). |
| 0.4 Transfer | **PASS** | Bare repos, branch/tag, clones, detached `9bb64ba` / `115df37`; harness reachable from GitHub; tree hashes match. |
| 0.5 Environment | **PASS** | `uv`/Python 3.11.17/3.11.18 venvs; `uv pip freeze` matches `pip_freeze.txt` (65 packages, identical); venv untouched since 17:57. Minor: no uv install log (m13). |
| 0.6 Tests | **PASS** | 168 passed + 14 passed on both hosts in my re-run; the `pytest` console-script failure is real and the `python -m pytest` deviation is the repo's own Makefile convention. |
| 0.7 llama.cpp build | **PASS** | `620d2225…`/`v0.7.0`; sm_89; CUDA 12.2; `CONFIGURE_RC=0`, `BUILD_RC=0`; `llama-server --version` matches; `offloaded 29/29`; `ARCHS = 890`. |
| 0.8 GGUF | **PASS** | Pinned URL; size `4683073536`; sha256 `509287f7…4d3c` exact on both; `trks-status` re-hash OK. |
| 0.9 Scripts | **PASS** | `bash -n`; all injected flags exist; hand-passed pins refused in both phase forms; `collect assemble` bypasses; `trks-status` works; watcher running. |
| 0.10 Smoke test | **PASS with caveats** | Full offload; dry run; one real instance on each host; TASL-7 failed once (stale edit) and succeeded on retry; `t_run` recorded; lease released. Caveats: retry session name/log (m2), `s04_rows`/audit attribution (m1), `t_run` basis (m7). |
| Report and STATUS | **PASS with corrections** | Report present, 270 lines, every output labelled `ENGINEERING_ONLY`, STOP 0 honestly declared open; STATUS entry present and consistent. Minor factual/provenance corrections above. |
| **STOP 0** | **NOT PASSED** | 0.3(c) is unmet (B1) and the M1 author decision is outstanding. The review loop itself is now done (this file); the runbook requires the same reviewer to accept after the operator fixes/answers findings, so a re-review acceptance is still needed. |

## 5. What I could not verify, and why

- **Historical state at Phase 0 start.** I can verify the current state and creation times, but not the
  report's claims about the start (e.g. "no pre-existing llama.cpp/GGUF", "GPU compute processes at start
  none", the pre-existing tmux inventory). Those are plausible and consistent with the current
  timestamps, but they are not re-runnable after the fact.
- **The historical `pgrep` count during the smoke.** No collector is running now. I reviewed the pattern
  (`python -m r1\.tracks\.collect .*--stop-file`) and the collector command line; the pattern is correct,
  but I cannot reproduce the "exactly one process" observation.
- **`GET /health` → `{"status":"ok"}`.** Not present in `llama_18101.log`; it may have been a direct curl.
  I did not start a server to reproduce it (the full-offload line and the successful collector are the
  material evidence and are present).
- **Whether the operator ever signalled an unowned process.** There is no audit trail of signals. I can
  show the Track P servers and the `12`/`r1p_agent` sessions predate Phase 0 and are alive, and no
  `trks_llm` session remains.
- **GitHub credentials at the time.** `git ls-remote` shows no `trackS-ops-20261030` branch on GitHub;
  whether the Mac had usable credentials when the operator ran is not knowable now (m9).
- **The watcher's pause path under a marker.** I did not create `trackx_evidence.active`/
  `trackp_evidence.active`; that would touch STOP files and change the state I was asked to leave alone.
  I reviewed the script against §11.4 and confirmed the process is running.
- **The lease-contention and forced-pause paths.** Not exercised: starting a second `trks-servers` or
  letting a marker appear would change the GPU state and the STOP files. The lease is free, the script
  matches §11.3, and the smoke used the script successfully.
- **The original test durations.** The operator's 323.69 s / 351.03 s are in `tests.log`; my re-runs took
  248.88 s / 264.55 s on the same hosts, consistent with load differences. The counts are the acceptance
  criterion and match.
- **The exact original smoke timings.** I read them from the manifests/logs and recomputed `t_run`; I did
  not re-run the smoke (that would need a new llama-server, and the outputs already exist).

## 6. Verdict

The technical Phase 0 work is in good shape. The pins (paper `9bb64ba`, harness `115df37`, llama.cpp
`620d2225`/`v0.7.0`, GGUF `509287f7…4d3c`), the detached checkouts, the frozen identical venvs, the two
test suites (168 + 14 on both hosts), the sm_89/CUDA 12.2 build, the five ops scripts, the smoke test, the
GPU-lease release, the watcher, the copy-back and the non-interference with Track P and the main Mac tree
all verify independently. But Phase 0 is not acceptable at STOP 0: item **0.3(c)** is explicitly a
precondition of STOP 0 and the Track P marker is absent (B1), and the real stale-proposal `ReplayError`
in the pinned code (M1) needs an author decision before the campaign phases. The operator's report is
honest about both, and the minor findings are corrections rather than reasons to redo the work. The
verdict below reflects the runbook's gate, not the quality of the setup.

REVIEW VERDICT: NOT ACCEPTED

The Phase 0 setup and its engineering evidence pass independent re-verification, but the runbook's STOP 0
is defined to include author item 0.3(c), and that condition is unmet: no `~/r1_locks/trackp_evidence.active`
marker is arranged on TASL-7, so Phase 1 must not start and the phase cannot be accepted as complete. In
addition, the observed stale-manager-proposal `ReplayError` (M1) is a real pinned-code defect that can lose
root units and must be decided by the author before S0.4/S0.7/S3e; the operator correctly stopped rather
than changing the pin. Once 0.3(c) is arranged, M1 is decided, and the minor corrections (m1–m13) are
addressed or answered, the same reviewer should re-check and record acceptance.

---

# Round 2 — independent re-check after the operator's remediation

**Reviewer and scope.** I took over the re-check after the round-1 session became unavailable. I re-derived
every fact below from the runbook, the pinned code, the host state and the artifacts; I did not adopt round
1's conclusions. I was adversarial about the two author-action items and re-computed the smoke numbers
rather than reading them from the report.

**Artifacts and heads.** Worktree `.claude-worktrees/trackS-ops-20261030`, branch `trackS-ops-20261030`.
The task names head **`d7010422`**; at the start of this re-check the worktree was at `d7010422` and clean.
During the re-check the operator committed **`eeb0599d`** ("fix the S0.7/S3e wording and record the uv
birth-time evidence"; report-only, +3/−3) and pushed it to `origin` and to both hosts' bare repositories.
I reviewed `d7010422` and re-checked `eeb0599d`; no pinned code, commit, GGUF, flag or server state
changed. The report and STATUS references below are to `eeb0599d`. At the time of writing there is also
an uncommitted `r1/tracks/ops/trks-status` draft (sha256 `a217f6b8…`, recursive manifest scan) installed
on both hosts; the committed HEAD and the report's sha table still say `ac7dd996…` (m11, n5). All times
UTC unless stated.

## 1. What I re-verified and how

- **Hosts, read-only.** `ssh portal_zhixu` (TASL-2) and `ssh tasl7` (TASL-7): `git rev-parse`/`status`/`tag`,
  `llama-server --version`, `sha256sum` of the GGUF, `bash -n` on all five installed scripts and
  `install.sh`, installed-script hashes, `trks-status`, `tmux ls`, `pgrep`, `flock -n`, `nvidia-smi
  --query-compute-apps`, `timedatectl`, and `stat` birth times for the uv binary. I did not start a GPU
  server, did not touch pinned code/commits/GGUF/flags, and left `trks_watch` running.
- **Tests.** Harness suite `python -m pytest -q -p no:cacheprovider tests/stage2/test_r1_track_s_arms.py`
  → **14 passed** on both hosts (0.38 s / 0.32 s). Paper suite
  `python -m pytest -q -p no:cacheprovider r1/tests/test_tracks_*.py` from `$R/work/Agent_paper_B` with
  `AR_HARNESS_ROOT=$R/work/autoresearch_harness` → **168 passed in 249.57 s** on TASL-2. The `python -m`
  invocation is the repo Makefile convention; the `pytest` console script still cannot import `r1`.
- **Smoke numbers.** Recomputed `t_run` from the raw host logs (not the report): digits n=77,
  mean **0.909091 s**, median 0.8, max 1.9; tabular failed attempt n=10, mean **0.8200 s**; tabular retry
  n=155, mean **1.913548 s**, median 1.9, max 4.6. Counted `s04_rows.jsonl` (11 / 24), `audit_runs.jsonl`
  (65 / 130), parsed both manifests, and compared every copied-back `results/r1/tracks/**` file with the
  host `$R/out/smoke/**` by sha256 (all identical, including the `failures/` payload and
  `failed_units.jsonl`).
- **Pinned code.** Read `r1/c3/features.py:144–154,337–342`, `r1/tracks/a2u.py:280–313,537–539,628–686`
  and the host harness `control_plane/campaign.py:917–983,1859` to confirm the reported failure path and
  the separate harness guard.
- **Provenance.** `git ls-remote --heads origin trackS-ops-20261030`; both host bare repositories;
  `trackS_30oct.bundle`; the main Mac tree (unchanged, HEAD `8a819f75`, 220 pre-existing `docs/r1/*` move
  entries).

## 2. Disposition of every round-1 finding

| ID | Sev | Round-1 finding | Disposition | Round-2 evidence |
|---|---|---|---|---|
| **B1** | **BLOCKING** | 0.3(c) unmet: no Track P `trackp_evidence.active` arrangement on TASL-7 | **SATISFACTORILY ANSWERED** | 0.3(c) requires the author to *arrange* that Track P creates and removes the marker around its evidence runs — not that the marker be present at STOP 0. §0.4 in fact requires the marker to be **absent** before Track S starts its servers. The author confirmed the arrangement on 30 Oct (report §5.2, STATUS, §8 B1). Live: `~/r1_locks` on both hosts holds only `gpu0.lock`; no `r1p_*` tmux session or GPU job on TASL-7 — the correct state. Residual: the arrangement is operator-relayed and has no Track P-side artifact (n3). |
| **M1** | **MAJOR** | stale manager proposal raises `ReplayError` in pinned A2-U code and loses the root unit | **SATISFACTORILY ANSWERED** | The defect is real and unchanged: failure payload `error_class r1.c3.features.ReplayError`, `"trial 11: stale edit: HIDDEN_UNITS is '1024', edit expects '512'"`; traceback `campaign.py:1859 (_controller_hook)` → `a2u.py` `forecast/replay/candidate` → `features.py:340/154`; the failed attempt's own log shows trial-009 applied `HIDDEN_UNITS 512 → 1024`, and the failure message reports the current value as `'1024'`. The harness guard (`PROPOSAL_PRECONDITION_FAILED`, `campaign.py:917–983`) is a separate graceful path; the controller still receives the raw proposal. **Author decision (30 Oct): keep the pins, accept retries, quantify the stale-proposal rate on S0.4, report it at STOP 3 and before any EVIDENCE phase; a second pin remains available if the rate matters.** No pinned code was changed. Residual: S0.4 is a small sample (n1). |
| **m1** | MINOR | `s04_rows 24` / audit `130` misattributed to "both attempts" | **FIXED** | 24 rows, 130 audits, all from the successful session; manifest attempt 1 `audit_runs: 0`, `done.failed: 1`; attempt 2 `audit_runs: 130`, `roots: 1`, `done.failed: 0`; the 24 budget indices are a unique subset of 2…39; copied-back files hash-identical to the host. |
| **m2** | MINOR | retry used `trks_smoke_retry`, not "the identical `trks_smoke` command" | **FIXED** | `trks_smoke.exit` (01:17:19Z rc=0, failed unit) and `trks_smoke_retry.exit` (01:24:38Z rc=0, ok); `.cmd` diff is only the log/exit filenames; report §3 0.10 now names both sessions and says the argument list was the same. Note: the rename was a provenance choice, not forced by `trks-run` (the old tmux session had ended) — n4(b). |
| **m3** | MINOR | `get_gguf.log` not copied back | **FIXED** | Committed `r1/tracks/ops/host_setup/tasl{2,7}/get_gguf.log` are byte-identical to the hosts: TASL-2 `13364414…`, TASL-7 `be5b3d11…` (sha256 recomputed both sides); each has `CURL_RC=0`, the size, the pinned sha and `SHA_RC=0`. |
| **m4** | MINOR | "work directory used exclusively" contradicted by the uv installer's writes | **FIXED** | Report §3 0.3/0.5 now discloses the mandated writes outside `$R`: `~/.local/bin/uv`, `~/.local/bin/env`, `~/.local/share/uv` (Python installs), `~/.cache/uv`, `~/.config/uv/uv-receipt.json`, and the PATH lines in `~/.bashrc`/`~/.profile`/`~/.zshrc`/fish. Live check confirms these are the installer's footprints. Note: the large `~/.local/share/uv` and `~/.cache/uv` trees pre-date Phase 0 (25/26 Oct) — n4(d). |
| **m5** | MINOR | "controller hook runs before that guard" imprecise | **FIXED** | Report §5.1 no longer claims an ordering before the guard; it says the controller receives the raw proposal and its replay raises, while the harness's `PROPOSAL_PRECONDITION_FAILED` path is separate. Code inspection confirms the guard is at `campaign.py:917–983` and the E2 hook at `:1859` is passed the raw `proposal`. |
| **m6** | MINOR | "the unit is lost" overstates | **FIXED** | Report §5.1 now says the unit is logged and retried, permanently lost only if `--max-retries` (default 2) is exhausted; `roots.jsonl` has the retry's `status: ok`, `failed_units.jsonl` retains the attempt-1 line. |
| **m7** | MINOR | tabular `t_run` 1.847 s included the failed attempt's 10 runs | **FIXED** | Retry-only n=155, mean **1.913548 s**, median 1.9, max 4.6; the excluded failed-attempt n=10 has mean 0.8200. Report §3 0.10 and §4 use 1.9135 and state the exclusion; I recomputed both from the raw logs. |
| **m8** | MINOR | worktree HEAD `62980aef` vs task-pinned `ddf8f08d` | **FIXED** | The round-2 task pins `d7010422`; the worktree is now at `eeb0599d` (report-only, on top) and the review records it. Note: the report's §8 row says "current HEAD is listed in §6" — §6 does not list it; n4(a). |
| **m9** | MINOR | `trackS-ops-20261030` not pushed to GitHub | **FIXED** | `git ls-remote --heads origin trackS-ops-20261030` → `eeb0599d…`; both host bare repositories → `eeb0599d…`; tag `trackS-code-9bb64ba` → `9bb64ba…` on both. |
| **m10** | MINOR | `failed_units` counts attempts, not permanent failures | **FIXED** | Report §3 0.10 now states it counts **failure events**, not permanently failed units, and that the collector does not delete a line when a later attempt succeeds; code confirms `log_failed_unit()` appends and `plan()` counts attempts up to `1 + max_retries`. The >2 % STOP denominator could be stated explicitly — n4(c). |
| **m11** | MINOR | `trks-status` does not check HEAD pins | **FIXED** | The committed template `ac7dd996…` was installed on both hosts and byte-identical at first check; it prints `OK paper 9bb64ba…`, `OK harness 115df37…`, `OK llama.cpp 620d2225…`, `paper tracked-file modifications: 0`; `bash -n` passes. During the re-check the operator installed an uncommitted draft `a217f6b8…` (recursive `rglob`) on both hosts; I re-ran it and it still prints the three `OK` HEAD lines and `paper tracked-file modifications: 0`. The report's m11 sha is now stale — n5. |
| **m12** | MINOR | "host timestamps UTC" wording | **FIXED** | Report §0 now distinguishes UTC report stamps from the hosts' local-PDT raw log excerpts (local `18:17` = `01:17Z`); `timedatectl` confirms TASL-2 `synchronized: no`, TASL-7 `synchronized: yes` as stated. |
| **m13** | MINOR | uv "absent" ambiguous | **FIXED** | `eeb0599d` records the decisive evidence: `~/.local/bin/uv` **birth** time is 2026-10-29 17:57:06 (TASL-2) / 17:56:38 (TASL-7), i.e. created by the §0.5 installer; the 26 Oct value is only the downloaded archive mtime. "not installed" at Phase 0 start is correct. I verified both birth times myself. |

**Counts: 13 FIXED, 2 SATISFACTORILY ANSWERED, 0 STILL OPEN.** B1 and M1 are author actions, not operator
defects; the two author decisions properly discharge them. The 13 minors are factual/provenance
corrections, all now made in the committed report.

## 3. New findings

All new findings are **MINOR**; none affects the technical evidence or the STOP 0 gate.

- **n1 (MINOR, residual risk of M1).** S0.4 uses `--instances 10` per node, i.e. 20 units total. A
  zero-failure S0.4 result gives only a weak upper bound (rule of three: ≈15 % at 95 %), not evidence that
  the stale-proposal rate is below 2 %. "Quantify on S0.4" is therefore a screen, not a precise estimate.
  The report should state the sample size and that the STOP-3 author decision must allow for it before
  S0.7/S3e; a single failure in 20 units (5 %) already exceeds the §0.6 STOP threshold.
- **n2 (MINOR, process; round 1 missed it).** The smoke wrote to `$R/out/smoke`, while runbook §0.1 defines
  `OUT=$R/out/<node>` and §0.10 says `$OUT/smoke`. It is harmless now (one node per host) and the copy-back
  to `results/r1/tracks/<node>/smoke` is correct, but later `$OUT/s04`/`$OUT/s0.7` paths, `trks-status`'s
  `out/*/manifest.json` scan and `assemble` should be reconciled to one layout before Phase 3. The
  operator has drafted and installed a recursive-glob fix (`a217f6b8…`) that finds both layouts; it is
  uncommitted and not reflected in the report's sha table (n5).
- **n3 (MINOR, cross-track/provenance).** The 0.3(c) arrangement exists only as an operator-relayed author
  confirmation. Track P's own runbook (`docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`) does not mention
  `trackp_evidence.active`, and no Track P-side instruction or artifact is committed. The marker is
  correctly absent and the watcher's `marker()` predicate handles it, but the pause path remains
  unexercised. Recording the Track P-side instruction (or the author's wording) in STATUS would make the
  arrangement auditable.
- **n4 (MINOR, documentation residuals).** (a) The §8 m8 row says the current HEAD is listed in §6; it is
  not — record `eeb0599d`. (b) The §8 m2 row says the new session name was "required by `trks-run`"; at
  retry time the `trks_smoke` tmux session had ended, so the rename was a provenance choice, not a tool
  requirement. (c) §3 0.10 clarifies failure events vs permanent failures but not the `> 2 %` STOP
  denominator; say "permanently failed (`exhausted`) units over planned units". (d) §3 0.5 attributes the
  `~/.local/share/uv` and `~/.cache/uv` trees to the Phase 0 installer although they pre-date Phase 0
  (25/26 Oct; 322 M/14 G and 207 M/10 G) and contain earlier Python installs (and a uv credentials
  lock on TASL-7); distinguish pre-existing caches from what Phase 0 added.
- **n5 (MINOR, provenance).** At review time `r1/tracks/ops/trks-status` has an uncommitted draft
  (`a217f6b8…`) installed on both hosts, while the committed HEAD and the report's m11 row still say
  `ac7dd996…`. The draft is behavior-compatible (it still prints the three pinned HEAD checks and the
  manifest line) and it addresses n2, but the installed tool no longer matches the reviewed commit. Commit
  the draft and update the report's sha/m11 row (and the installed-script table), or reinstall the
  committed version, before closing Phase 0.

## 4. Safety, pins and non-interference (re-checked)

Both hosts remain at paper `9bb64ba` (detached, clean, tag `trackS-code-9bb64ba`), harness `115df37`
(clean) and llama.cpp `620d2225`/`v0.7.0` (`llama-server` build 11669, CUDA backend, `ARCHS=89`,
`CONFIGURE_RC=0`, `BUILD_RC=0`, `offloaded 29/29 layers`). GGUF sha256 is exactly
`509287f7…4d3c` on both. The venv freeze is unchanged from round 1 (65 packages, identical sha256). The
GPU lease is free (`flock -n … echo LOCK-FREE`), `nvidia-smi --query-compute-apps` is empty, no `trks_llm`
session remains, and `trks_watch` is running on both hosts. The two Track P `llama-server` processes on
TASL-2 (pids 2945752 / 3747685, started 26 Oct 02:43 / 03:05) are GPU-free and untouched. The main Mac
tree is still at `8a819f75` with its pre-existing 220-entry `docs/r1/*` move; I did not touch it. The only
file I modified is this review.

## 5. Acceptance checklist (runbook Phase 0 / STOP 0)

| Item | Round-2 status |
|---|---|
| 0.1 Code on the Mac | PASS |
| 0.2 Host facts | PASS (dynamic values only) |
| 0.3(a) SSH access | PASS |
| 0.3(b) Work directory | PASS (uv writes disclosed) |
| 0.3(c) Track P marker arrangement | **SATISFACTORILY ANSWERED** (author arrangement recorded; marker correctly absent) |
| 0.4 Transfer | PASS |
| 0.5 Environment | PASS (venv frozen, identical freeze) |
| 0.6 Tests | PASS (168 paper, 14 harness; 168 re-run on TASL-2, 14 on both) |
| 0.7 llama.cpp build | PASS |
| 0.8 GGUF | PASS |
| 0.9 Scripts | PASS (`bash -n`, pins, installed hashes, `trks-status` HEAD checks) |
| 0.10 Smoke test | PASS with the n1–n2 caveats |
| **STOP 0** | **PASS** (review loop complete; 0.3(c) answered; M1 decided) |

REVIEW VERDICT: ACCEPTED

The Phase 0 work is accepted. Round 1's BLOCKING item (B1) was based on the marker's absence, but 0.3(c)
requires the author to *arrange* that Track P creates and removes the marker around its evidence runs, not
to leave it present at STOP 0; the marker's absence is in fact required by §0.4 before Track S starts its
servers, and the author has now confirmed the arrangement, accurately recorded in the report and STATUS.
The MAJOR item (M1) is a real, unchanged defect in pinned code, but the author has made an explicit
decision — keep the pins, accept retries, measure the rate on S0.4 and report it at STOP 3 and before any
EVIDENCE phase — which is a proper disposition for Phase 0 and states the residual risk; the small S0.4
sample (n1) and the missing Track P-side artifact (n3) are follow-ups, not STOP 0 blockers. All thirteen
minor findings are fixed, the pins, GGUF, build, scripts, tests, smoke outputs, copy-back, lease, watcher
and non-interference re-verify on both hosts, and the remaining n1–n4 items are documentation/process
improvements that do not change the evidence. The transient uncommitted uv draft I observed during the
re-check was discarded and never committed; `eeb0599d` records the correct birth-time evidence. The
worktree is clean apart from this review file and the uncommitted `trks-status` draft (n5), which must be
committed and reflected in the report or reverted before Phase 0 is closed.

---

## Operator note after round 2 (added by the operator; the reviewer's text above is unaltered)

**n5 is resolved in commit `f4b7b3b4`.** The `trks-status` draft you observed mid-check (recursive
`rglob` manifest scan) was committed in that same commit, the report's sha table was updated to it, and
the script was left installed on both hosts. Immediately after `f4b7b3b4`:

- committed template `r1/tracks/ops/trks-status` sha256 = `a217f6b8b14b4c1b68c657e3e02c9c1b4f3ebfdf0a12e326fd5966fbd1c6e644`
- installed on TASL-2 and on TASL-7 = the same sha256
- report §3 0.9 sha table = the same sha256

so the committed HEAD, the report and both hosts now agree. `n1`–`n4` are recorded in the report §8 with
their dispositions (n1 as a caveat on the S0.4 screen, n2 with Phase 3 onward on `out/<node>/<phase>`,
n3 as the operator-relayed 0.3(c) arrangement, n4 as documentation fixes). The operator did not modify
the round-2 verdict, which stands: **ACCEPTED**, STOP 0 passed.
