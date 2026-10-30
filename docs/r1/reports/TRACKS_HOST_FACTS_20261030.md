# Track S — Phase 0 host facts, environments, pins and smoke test (TASL-2, TASL-7)

**Written 30 Oct 2026 by the Track S operator agent; AI-assisted.** Phase 0 of
`docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` (revision 3.2,
sha256 `1789c000dbeaaa96202e00d72714d6b5df4e87733ca8f5823b9afd01ac7091ab`; the copy in the Mac's
main tree and the one on `docs/trackS-decisions-30oct` are byte-identical, and the document is read
from that branch per runbook §0.1 — it is not part of the pinned paper commit). Every output below is
**ENGINEERING_ONLY**: it feeds the pre-declaration and is never quoted as a result.

Operator worktree: `.claude-worktrees/trackS-ops-20261030`, branch **`trackS-ops-20261030`**, from paper
commit **`9bb64ba6712668c4bab4a66720cf7f2645e1c672`**. Hosts: TASL-2 (`ssh portal_zhixu`) and TASL-7
(`ssh tasl7`).

**Timestamps.** Report timestamps are UTC. Raw log excerpts are stamped by the hosts in their local
zone (America/Los_Angeles, PDT, −0700, i.e. 7 h behind UTC), so a local `18:17` in a log line is
`01:17Z`. TASL-2's clock is not NTP-synchronised (`timedatectl`: "System clock synchronized: no"),
TASL-7's is; the offset between the two is constant.

## 0. Provenance of the code and documents

| Item | Expected (runbook §0.1) | Observed | Verdict |
|---|---|---|---|
| bundle `trackS_30oct.bundle` sha256 | `6e6d5e932637a3c548f516efaa3c4ad25761ebb5dadcc0d2d504cca54a56d8cf` | same | OK |
| `git bundle verify` | complete history, 2 refs | "okay", complete history, 2 refs | OK |
| `trackS-20261029` | `9bb64ba…` | `9bb64ba6712668c4bab4a66720cf7f2645e1c672` | OK |
| `docs/trackS-decisions-30oct` | `3ac0fbf4…` (`trackS_30oct.heads.txt`) | `3ac0fbf4a7c18ce2abdc7096edea37f2d0aa2e39` | OK |
| ops tag | — | `trackS-code-9bb64ba` → `9bb64ba…` created | OK |

The local `docs/trackS-decisions-30oct` branch was one commit behind the bundle head
(`cdb3cdc3`); the bundle fetch fast-forwarded it to `3ac0fbf4` ("operator runbook rev 3.2: SSH aliases
… work dir approved"). No force, no conflict. The main working tree (`exam-x-20261026`, with its
uncommitted `docs/r1/*` → `docs/*` move) was not touched.

## 1. Host facts (runbook 0.2)

| | **TASL-2** (`portal_zhixu`) | **TASL-7** (`tasl7`) |
|---|---|---|
| hostname | TASL-2 | TASL-7 |
| user | `uid=1008(dowling)` | `uid=1011(dowling)` |
| nproc | 32 | 24 |
| RAM (`free -g`) | 62 GiB total, 57 available | 62 GiB total, 58 available |
| disk `/home/dowling` | 1.9 T, 269 G avail, 85 % used | 1.9 T, 917 G avail, 49 % used |
| GPU | RTX 4090, 24 564 MiB | RTX 4090, 24 564 MiB |
| GPU UUID | `GPU-4d623e76-7587-ee15-a633-46f60d220d94` | `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` |
| driver / CUDA (nvidia-smi) | 535.309.01 / 12.2 | 580.178.04 / 13.0 |
| CUDA toolkit found | `/usr/local/cuda`, `/usr/local/cuda-12`, `/usr/local/cuda-12.2` → 12.2 (V12.2.140) | `/usr/local/cuda-11.7` (V11.7.64), `/usr/local/cuda-12.2` (V12.2.91); **no `/usr/local/cuda` symlink** |
| nvcc used | `/usr/local/cuda-12.2/bin/nvcc` | `/usr/local/cuda-12.2/bin/nvcc` |
| cmake / gcc / git / tmux / flock | 3.22.1 / 11.4.0 / 2.34.1 / 3.2a / util-linux 2.37.2 | same |
| system python3 | 3.10.12, **no `ensurepip`** | 3.10.12 (`ensurepip` present) |
| `uv` at Phase 0 start | not installed | not installed |
| time zone / clock sync | America/Los_Angeles (PDT) / **synchronized: no** | America/Los_Angeles (PDT) / synchronized: yes |
| network (hf/github/astral) | 200 / 200 / 200 | 200 / 200 / 200 |
| `~/r1_locks` at start | `gpu0.lock` only (no priority marker) | `gpu0.lock` only (no priority marker) |
| pre-existing tmux | `12` (interactive claude, `~/Agent_paper_B`), `r1p_agent` (idle bash, `~/Agent_paper_B`) | none |
| pre-existing llama.cpp / GGUF | none | none |
| GPU compute processes at start | none | none |

**Notable, unowned processes on TASL-2.** Two long-lived idle `llama-server` processes owned by the
Track P environment (`/home/dowling/r1_trackp/venvs/trackp-cpu/bin/python … /tmp/r1_c3_dryrun_retry_*/bin/llama-server
-m … DRYRUN-Q4_K_M.gguf -ngl 999`) were present. They held **no** GPU memory
(`nvidia-smi --query-compute-apps` empty) and are not Track S processes; per §0.4 ownership they were
left untouched. **The author has confirmed (30 Oct) that their presence on TASL-2 is expected.**

## 2. Pins — all verified (runbook §0.2)

| Pin | Expected | Observed | Verdict |
|---|---|---|---|
| llama.cpp commit | `620d2225cc436ab0b001e3200e590e3b286ef9ab` | same on both hosts | OK |
| llama.cpp tag | **v0.7.0** | `git rev-list -n1 v0.7.0` = `620d2225…` on both | OK |
| `llama-server --version` | recorded | `version: 0.7.0-dev (build 11669, commit 620d2225c)` / `built with GNU 11.4.0 for Linux x86_64`, identical both hosts | OK |
| GGUF revision | `13fb94bfda8c8cf22497dc57b78f391a9acb426a` | fetched from the pinned `resolve/<rev>/` URL | OK |
| GGUF file | `qwen2.5-coder-7b-instruct-q4_k_m.gguf` | present in `$R/models/` | OK |
| GGUF sha256 | `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` | **exact match** on both hosts (`sha256sum`), size 4 683 073 536 B identical | OK |
| manager alias | `r1-manager` | `--alias r1-manager` in `trks-servers` | OK |
| schema | `manager_proposal/v1` | injected into every LLM phase; appears in dry-run manifest `manager.proposal_schema` | OK |
| paper code (hosts, detached) | `9bb64ba` | `git rev-parse HEAD` = `9bb64ba6712668c4bab4a66720cf7f2645e1c672`, no tracked-file modifications | OK |
| harness code (hosts, detached) | `115df37` | `git rev-parse HEAD` = `115df37d2b4581487eb2d911dc4d6a903afcc76a` | OK |
| server flags | `-ngl 999 -c 8192 --parallel 1 --verbose --alias r1-manager --host 127.0.0.1 --port <p>` | installed verbatim in `bin/trks-servers` | OK |

The harness `115df37` is reachable from GitHub on both hosts (`refs/heads/trackS-20261029`), so the
bare-repository fallback (§0.4) was not needed for the harness.

## 3. Phase 0 steps

**0.1 Code on the Mac.** Done (see §0); worktree `trackS-ops-20261030` created from `9bb64ba`, branch
of the same name, tag `trackS-code-9bb64ba`.

**0.3 Access.** `ssh portal_zhixu 'hostname; id'` → TASL-2 / `dowling`; `ssh tasl7 'hostname; id'` →
TASL-7 / `dowling`, both without a password prompt. The work directory `/home/dowling/r1_tracks/` was
created and is the only directory that holds experiment state. Two mandated exceptions exist: `flock`
uses `~/r1_locks/gpu0.lock` (§0.4), and the `uv` installer of §0.5 writes outside `$R` (see 0.5).

**0.4 Transfer.** On each host: `$R/{remotes,work,opt,models,bin,logs,launch,out,scratch}` created and
`git init --bare remotes/Agent_paper_B.git`; branch `trackS-ops-20261030` and tag `trackS-code-9bb64ba`
pushed from the Mac; cloned into `work/Agent_paper_B` and `git checkout --detach 9bb64ba`;
`work/autoresearch_harness` cloned from GitHub and `git checkout --detach 115df37`.

**0.5 Environment.** `uv 0.13.6` installed user-level from astral.sh on both hosts;
`uv python install 3.11`; `uv venv $R/venv --python 3.11`; `uv pip install -e
work/autoresearch_harness[dev]` plus `numpy scipy scikit-learn PyYAML pytest`; `uv pip freeze >
logs/pip_freeze.txt`.

- venv interpreter: **3.11.17** (TASL-2) and **3.11.18** (TASL-7). Only the patch level differs.
- `pip_freeze.txt` is **byte-identical** on both hosts (65 packages,
  sha256 `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687`). The venv is frozen from
  here on.
- **Writes outside `$R`, as mandated by §0.5.** The astral installer put the `uv` binary in
  `~/.local/bin/uv`, its Python and package caches under `~/.local/share/uv` (and `~/.cache/uv`), and
  appended a PATH line to `~/.profile` / `~/.bashrc` (and the fish/zsh equivalents where present).
  These are the documented side effects of `curl … | sh`; they are the only files Phase 0 created
  outside `/home/dowling/r1_tracks/` apart from the §0.4 lease lock. Note that the large
  `~/.local/share/uv` and `~/.cache/uv` trees **pre-date** Phase 0 (25/26 Oct, containing earlier
  Python installs and another track's cache); Phase 0 added to them rather than creating them.

**0.6 Tests.** Byte-for-byte the expected counts, on both hosts:

| Suite | Expected | TASL-2 | TASL-7 |
|---|---|---|---|
| `r1/tests/test_tracks_*.py` | 168 passed | **168 passed** (session 323.69 s) | **168 passed** (session 351.03 s) |
| harness `tests/stage2/test_r1_track_s_arms.py` | 14 passed | **14 passed** | **14 passed** |

The independent reviewer re-ran both suites and reproduced 168 and 14 on both hosts
(TASL-2 248.88 s, TASL-7 264.55 s; the wall time varies with machine load).

*Deviation, recorded.* `pytest -q …` (the console script) fails at collection with
`ModuleNotFoundError: No module named 'r1'`, because with no `r1/tests/__init__.py` pytest inserts
`r1/tests` — not the repo root — into `sys.path`. The repo's own `Makefile` r1-test target runs
`$(R1_PY) -m pytest -q -p no:cacheprovider r1/tests`; `python -m` puts the repo root on `sys.path`.
The suites were therefore run as **`python -m pytest`** from `$R/work/Agent_paper_B`, which is the
wrapper's environment (§0.3) and the repo's own convention. No code was changed.

**0.7 llama.cpp build.** Cloned `https://github.com/ggml-org/llama.cpp` into `opt/llama.cpp`,
checked out `620d2225…`, then

```
cmake -S opt/llama.cpp -B opt/llama.cpp/build -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=89 -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.2/bin/nvcc \
  -DCMAKE_BUILD_TYPE=Release
cmake --build opt/llama.cpp/build -j --target llama-server
```

Both hosts: `CONFIGURE_RC=0`, `BUILD_RC=0`. Configure log confirms
`Using CMAKE_CUDA_ARCHITECTURES=89`, `ggml version: 0.27.0`, `ggml commit: 620d2225c`,
CUDA host compiler GNU 11.4.0, and that the CUDA backend was included. The `<iomanip>` workaround was
**not** needed. The binary is small (17 864 B) because this build uses shared libraries; `libggml-cuda.so`
is present and the runtime loads it (see the smoke test's `offloaded 29/29 layers`).

**0.8 GGUF.** Downloaded from the pinned revision; sha256 equals the pin on both hosts (§2).

**0.9 Scripts.** `bin/trks`, `bin/trks-run`, `bin/trks-servers`, `bin/trks-watch`, `bin/trks-status`
installed from `r1/tracks/ops/` (§11 templates; `trks-status` written to §11.5). Per-host filling is
done at install time by `r1/tracks/ops/install.sh <alias> <label> <uuid>`:
`HOST_LABEL=TASL-2 / GPU_ID=GPU-4d623e76-…` on TASL-2,
`HOST_LABEL=TASL-7 / GPU_ID=GPU-ab72fb4a-…` on TASL-7.

Checks, all passing on both hosts:

- `bash -n` on every installed script (during install).
- `trks collect --help` exposes every injected flag: `--manager --manager-model --proposal-schema
  --gguf --gguf-sha256 --llama-build --llama-server-bin --host-label --gpu`. **They match §11.1 exactly.**
- `trks probe --help` exposes `--host-label --gguf --gguf-sha256 --llama-build --llama-server-bin`.
- `trks collect assemble --help` reaches Python.
- The wrapper plans a phase (and therefore injects the pins) for **both** `--phase=S0.4` and
  `--phase S0.4`: passing a pin flag by hand is refused in both forms
  (`trks: --manager is injected by the wrapper`, `trks: --gpu is injected by the wrapper`).
- `bin/trks-status` runs. Beyond the §11.5 list it also checks the three **pinned HEADs** (paper,
  harness, llama.cpp) and reports tracked-file modifications; on both hosts all three print `OK` and
  paper has 0 modifications. It discovers manifests **recursively** under `$R/out`, so it works with
  both the `$R/out/<phase>` layout used in Phase 0 and the runbook §0.1 `$R/out/<node>/<phase>` layout
  used from Phase 3 on.
- Watcher started on both hosts (`tmux new -d -s trks_watch $R/bin/trks-watch`; `logs/watch_started`
  touched first) and **left running**. It stayed alive across an ~8.5 h gap during which the operator's
  SSH was unavailable (it runs on the hosts, not the Mac).

Installed sha256 (per host; identical for the four host-independent scripts):

| script | TASL-2 | TASL-7 |
|---|---|---|
| `trks` | `dca17a7d…38f4` | `26a240fa…7506` (differs only in the two filled lines) |
| `trks-run` | `b53bc811…64c4` | same |
| `trks-servers` | `47dcf336…257b` | same |
| `trks-watch` | `3108566d…570c` | same |
| `trks-status` | `a217f6b8b14b4c1b68c657e3e02c9c1b4f3ebfdf0a12e326fd5966fbd1c6e644` | same |

**0.10 Smoke test (ENGINEERING_ONLY).**

1. `tmux new -d -s trks_llm $R/bin/trks-servers 1`. Both hosts:
   `load_tensors: offloaded 29/29 layers to GPU`, `CUDA0 model buffer size = 4168.09 MiB`, and an
   explicit `curl -s http://127.0.0.1:18101/health` returned `{"status":"ok"}`. (llama-server does not
   log `/health` requests, so the health result is a direct observation, not a log line.) Full offload
   confirmed.
2. Dry run via `trks-run trks_smoke_dry 18101 collect --phase S0.4 … --dry-run`: rc=0 on both. The
   dry-run manifest shows `host: TASL-2` / `TASL-7`, `g_declared = 0.00066` / `0.00019` (exactly
   0.1 σ_node), `W = 40`, `K = 5`, `seed_base = 30000`, `manager.kind = langgraph` with the pinned
   model and schema — i.e. the wrapper's pin injection works end-to-end.
3. One real instance, `$OUT/smoke`, `$WORK/smoke`:

| | TASL-2 `digits_mlp` | TASL-7 `tabular_mlp` |
|---|---|---|
| session | 01:17:13Z → 01:18:55Z (102 s) | attempt 1 `trks_smoke` 01:17:02Z → 01:17:18Z (**failed unit**); attempt 2 `trks_smoke_retry` 01:19:09Z → 01:24:38Z (329 s, **ok**) |
| result | `roots=1 failed=0 status=complete` | attempt 1: `roots=0 failed=1`; attempt 2: `roots=1 failed=0 status=complete` |
| `s04_rows.jsonl` | 11 | 24 (all from the successful attempt 2) |
| audit runs | 65 | 130 (all from attempt 2; attempt 1 recorded `audit_runs: 0`) |
| worker `run_command` time | n=77, **mean 0.9091 s**, median 0.800 s, max 1.900 s | attempt 2 only: n=155, **mean 1.9135 s**, median 1.900 s, max 4.600 s (attempt 1's 10 runs were faster, mean 0.8200 s, and are excluded) |

   All exit codes 0. The TASL-7 first attempt is a real finding — see §5.1. It was the same argument
   list re-run through `trks-run` under a new session name (`trks_smoke_retry`; `trks-run` refuses a
   name that already has a session), into the same `--out`/`--work`, which is how §0.6 says a stopped
   session resumes. The retry completed the campaign and wrote one `ok` root. `failed_units.jsonl`
   still holds the attempt-1 record: it counts **failure events**, not permanently failed units, and
   the collector does not delete a line when a later attempt succeeds.
4. `tmux kill-session -t trks_llm` on both hosts; afterwards `nvidia-smi --query-compute-apps` is empty
   and `flock -n ~/r1_locks/gpu0.lock` succeeds, i.e. the lease is released.

`pgrep -a -f 'python -m r1\.tracks\.collect .*--stop-file'` during the smoke run matched exactly one
process — our own collector, with the full pin list on its command line — and nothing else (§11.4).

## 4. Inputs for the Phase 1 projection (reported, not yet computed)

The projection formula (§Phase 1) needs `C ≈ 80 000` LLM calls, `L` = mean latency, `R ≈ 60 000`
worker/audit runs, `t_run` = per-run CPU time and `c` = free cores. From this phase:

- `t_run` = **0.9091 s** (digits_mlp, TASL-2, n=77) and **1.9135 s** (tabular_mlp, TASL-7, n=155,
  successful campaign only).
- `c`: 32 cores (TASL-2), 24 cores (TASL-7), capped by `k × 2` concurrent campaigns.
- `L` is **not yet measured** — it is S0.1 (Phase 1). The projection is therefore computed at STOP 1,
  not here.

## 5. Findings and author decisions

### 5.1 A stale manager proposal crashes A2-U's E2 forecast (pinned code; not fixed by me)

At TASL-7 trial 11 the manager proposed `HIDDEN_UNITS: 512 → …`, but trial 9 had been **kept**
(`512 → 1024`), so the proposal's `old` value was stale. A2-U's `decide → _e2_detail → forecast →
replay → featurize → candidate` calls `r1/c3/features.apply_edit`, which raises `ReplayError` on a
stale `old`; nothing in `a2u.py` catches it, so the root unit is logged to `failed_units.jsonl`
(`error_class r1.c3.features.ReplayError`) and retried. Traceback path:
`campaign.py:1859 (_controller_hook)` → `a2u.py:632/686/539/313` → `features.py:340/352/154`.

The same event is **tolerated elsewhere in the system**: the harness has its own precondition guard
(`control_plane/campaign.py`, `FailureCategory.PROPOSAL_PRECONDITION_FAILED`, "structured edit
precondition failed for {symbol}: expected {old_value}, found {current}") which records a failed-invalid
trial and lets the campaign continue. The controller receives the raw `proposal` and replays it, so the
graceful harness path does not cover the controller's forecast. `ReplayError` is a *sanctioned*
consistency check for a malformed ledger (`r1/tests/test_c3_features.py::test_stale_edit_raises`), so
this is a robustness gap on a live-but-stale proposal, not a corrupt-ledger case.

Evidence: `results/r1/tracks/tabular_mlp/smoke/failures/root__tracks_S04_tabular_mlp__s30000.json` and
`failed_units.jsonl`; the ledger decision chain is in `<work>/…/root_trials.jsonl`.

The event is **stochastic** (temperature 0.2): the re-run recovered and finished. It is nevertheless a
systematic risk:

- an instance seed is fixed for exact pairing, so a unit whose manager keeps emitting a stale edit can
  exhaust `--max-retries` (default 2) and stay failed;
- §0.6 makes **> 2 % failed units in a phase a STOP**, and S3e has 300 instances per node, S0.7 has
  460 campaigns per node — so the failure rate must be known before **S0.7/S3e** (S0.4, the phase that
  measures it, is itself Phase 3), not discovered during EVIDENCE.
- **The S0.4 screen is coarse (review n1).** S0.4 runs `--instances 10` per node, i.e. 20 units total.
  A zero-failure result bounds the rate only by the rule of three (≈ 14 % at 95 %), and **one** failure
  in 20 units is already 5 % > the §0.6 STOP threshold. The STOP-3 author decision must therefore treat
  the S0.4 figure as a screen, not an estimate, and may need a larger sample before S0.7/S3e.

I did **not** change the pinned paper code (9bb64ba) or harness (115df37); §0.2 forbids that without an
author PLAN row and §10 sends anything uncovered to a STOP.

**Author decision (30 Oct): accept retries for now and quantify the stale-proposal rate on S0.4.** The
pins stay unchanged; S0.4 is the first real phase and its `failed_units.jsonl` / manifests are the
measurement. The measured rate is reported to the author at STOP 3 and before any EVIDENCE phase; a
second pinned commit remains available if the rate turns out to matter.

### 5.2 Runbook item 0.3(c) — resolved by the author (30 Oct)

The author must arrange that **Track P creates and removes `~/r1_locks/trackp_evidence.active`** around
its evidence runs on TASL-7. The author has confirmed (30 Oct) that **this is arranged and Track P will
handle it**. That satisfies the arrangement required by §0.3(c); the marker file itself was correctly
absent at Phase 0 (Track P creates it only around its own evidence runs). The watcher's handling of a
marker is therefore exercised in the field, not synthesised by the operator — creating a cross-track
marker file by hand could perturb another track's evidence bookkeeping.

### 5.3 Track P processes resident on TASL-2 (§1)

Idle, GPU-free Track P dry-run `llama-server` processes are running on TASL-2, and `r1p_agent` and `12`
tmux sessions are open there. They do not hold the GPU lease and were not touched. **The author has
confirmed (30 Oct) that this is expected.**

## 6. State at the end of Phase 0

Ready: both hosts at the pinned paper/harness commits with a frozen, identical venv; the pinned
llama.cpp built for sm_89 with CUDA; the pinned GGUF verified by sha256; the five ops scripts installed
and self-checked; the watcher running on both hosts (survived the operator's SSH outage); the GPU lease
released; `$OUT` copied back; `trackS-ops-20261030` pushed to both hosts' bare repositories and to
GitHub (`https://github.com/dowlingwong/Agent_paper_B.git`).

STOP 0: **PASSED** — the review loop accepted the phase at round 2 (see §8). Phase 1 may start.

## 7. Files

- `r1/tracks/ops/{trks,trks-run,trks-servers,trks-watch,trks-status,install.sh}` — committed.
- `r1/tracks/ops/host_setup/tasl{2,7}/` — the exact setup scripts (`build_llama.sh`, `run_tests.sh`,
  `get_gguf.sh`), their logs (`build_llama.log`, `tests.log`, `get_gguf.log`, `watch.log`),
  `pip_freeze.txt`.
- `results/r1/tracks/{digits_mlp,tabular_mlp}/smoke/` — manifests, `roots.jsonl`, `s04_rows.jsonl`,
  `audit_runs.jsonl`, `failed_units.jsonl` and `failures/` (the §5.1 evidence).
- `docs/r1/reviews/TRACKS_OPS_PHASE0_REVIEW_20261030.md` — the independent review.
- `$WORK` (`/home/dowling/r1_tracks/scratch/<node>/smoke`) stays on the hosts, as required for S0.5b.

## 8. Review record

**Round 1** (`docs/r1/reviews/TRACKS_OPS_PHASE0_REVIEW_20261030.md`): **NOT ACCEPTED** — 1 BLOCKING,
1 MAJOR, 13 MINOR. The reviewer independently re-verified the bundle/heads provenance, both pinned
commits on both hosts, the llama.cpp tag/commit and `--version`, the GGUF sha256, the frozen 65-package
venv, both test suites (168 and 14 on both hosts), all five ops scripts against §11 (including pin
refusal, both `--phase` forms, the `assemble` bypass and `bash -n`), byte-identity of the copied-back
smoke outputs with the hosts, the free GPU lease and the running watcher.

Disposition of each finding:

| # | Sev | Finding | Disposition |
|---|---|---|---|
| B1 | BLOCKING | 0.3(c) unmet: no Track P marker arrangement on TASL-7 | **Answered** — author confirms (30 Oct) the arrangement is in place and Track P handles it; the marker is Track P's to create around its own evidence runs (§5.2) |
| M1 | MAJOR | pinned-code stale-proposal `ReplayError` loses a root unit | **Answered by author** — accept retries and quantify the rate on S0.4, pins unchanged (§5.1); report already states the operator did not modify the pin |
| m1 | MINOR | `s04_rows 24 / audit_runs 130` misattributed to "both attempts" | **Fixed** — both come from the successful attempt only; attempt 1 recorded 0 rows and `audit_runs: 0` (§3 0.10) |
| m2 | MINOR | retry used `trks_smoke_retry`, not "the identical `trks_smoke` command" | **Fixed** — same argument list; the new session name was a provenance choice (the old tmux session had already ended, so `trks-run` would have accepted the old name); wording corrected (§3 0.10) |
| m3 | MINOR | `get_gguf.log` not copied back though the report says "their logs" | **Fixed** — copied back for both hosts and committed under `r1/tracks/ops/host_setup/` |
| m4 | MINOR | uv installer wrote shell profiles and uv caches outside `$R`, contradicting "exclusively" | **Fixed** — §3 0.5 now lists the mandated writes outside `$R` and scopes the "only experiment directory" claim |
| m5 | MINOR | "controller hook runs before guard" imprecise | **Fixed** — §5.1 now states only what is demonstrable: the controller receives the raw proposal and its replay raises, while the harness's `PROPOSAL_PRECONDITION_FAILED` guard is a separate graceful path |
| m6 | MINOR | "unit is lost" overstates (it was retried) | **Fixed** — §5.1 says the unit is logged and retried, permanent only if retries exhaust |
| m7 | MINOR | tabular `t_run` 1.847 s includes the failed attempt's 10 runs | **Fixed** — retry-only mean 1.9135 s (n=155) reported and used; the excluded 10 runs (0.8200 s) are stated (§3 0.10, §4) |
| m8 | MINOR | worktree HEAD `62980aef` vs task-pinned `ddf8f08d` | **Explained** — `62980aef` was a report-only commit made after the round-1 task text was written; reviewed substance is `ddf8f08d` + report wording. This report is committed on top of `eeb0599d`; the round-2 review records `d7010422`/`eeb0599d` |
| m9 | MINOR | no GitHub push of `trackS-ops-20261030` | **Fixed** — pushed to `origin` (`github.com/dowlingwong/Agent_paper_B.git`) and to both hosts |
| m10 | MINOR | `failed_units` count = attempts, not permanent failures | **Fixed** — stated explicitly in §3 0.10, and the §0.6 denominator is now stated as **permanently failed (`exhausted`) units over planned units** |
| m11 | MINOR | `trks-status` does not check HEAD pins | **Fixed** — it now verifies paper/harness/llama.cpp HEADs, reports tracked-file modifications, and finds manifests recursively (§3 0.9, sha256 `a217f6b8…`) |
| m12 | MINOR | "host timestamps UTC" wording | **Fixed** — §0 now distinguishes UTC report stamps from local-PDT raw log excerpts |
| m13 | MINOR | uv "absent" ambiguous | **Fixed and checked further** — "not installed" (§1) is the right reading, and `stat` settles it: `~/.local/bin/uv` has **birth** time 2026-10-29 17:57:06 (TASL-2) / 17:56:38 (TASL-7) — i.e. created by the §0.5 installer during Phase 0 — while its 2026-10-26 **mtime** is only the downloaded archive's timestamp. An earlier draft of this report briefly misread the mtime as pre-existence; that draft was discarded and never committed. |
| — | — | could not verify: historical start state, historical `pgrep` count, `GET /health` claim, watcher pause path, GitHub credentials at the time, exact original wall times | **Answered** — the start state and the `pgrep` count are historical and not reconstructable; the `/health` result was a direct `curl` observation (llama-server does not log it); the watcher pause path was deliberately not synthesised (see §5.2) though the watcher is alive and its `marker()`/`ours()` predicates were checked; GitHub push is now demonstrated; wall times vary with load while pass counts match |

**Round 2** (`docs/r1/reviews/TRACKS_OPS_PHASE0_REVIEW_20261030.md`, appended by a second independent
reviewer because the round-1 session was not resumable in this harness — a documented deviation from
"the same reviewer"): **ACCEPTED**. Disposition counts: **13 FIXED, 2 SATISFACTORILY ANSWERED (B1, M1),
0 STILL OPEN**, plus 4 new MINOR residuals (n1–n4) which are addressed here:

| # | Sev | Finding | Disposition |
|---|---|---|---|
| n1 | MINOR | "quantify on S0.4" is a coarse screen (20 units) | **Fixed** — §5.1 now states the sample size, the rule-of-three bound and that one failure in 20 already exceeds 2 % |
| n2 | MINOR | smoke wrote to `$R/out/smoke`, not §0.1's `$R/out/<node>/smoke` | **Recorded** — Phase 0 used the flat layout (harmless, one node per host; copy-back is already `results/r1/tracks/<node>/smoke`); `trks-status` now scans recursively, and **Phase 3 onward uses `$R/out/<node>/<phase>` as §0.1 requires** |
| n3 | MINOR | the 0.3(c) arrangement exists only as an operator-relayed confirmation | **Recorded** — the author's confirmation is quoted in §5.2 and STATUS; the marker is correctly absent and the watcher predicate handles it. Track P's own runbook does not mention the marker |
| n4 | MINOR | documentation residuals (HEAD, session-name reason, STOP denominator, uv cache provenance) | **Fixed** — see the m2/m8/m10 rows, §3 0.5 (pre-existing uv caches distinguished) and §3 0.10 |

**STOP 0 is therefore passed.** Phase 1 may start.
