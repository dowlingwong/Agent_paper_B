# Track S — independent review of operator Phase 1 (S0.1) and Phase 2 (S1.1), STOP 1

**Reviewer.** Fresh independent reviewer: I did not see the operator's work in progress and did not accept
the operator's conclusions before checking them. I read the runbook, the design, the report, the pinned
probe code and the hosts, and re-derived the numbers from the raw result files and the hosts' originals.

**Artifacts under review.**
- Operator worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackS-ops-20261030`,
  branch `trackS-ops-20261030`, head **`51984467`**. The worktree was clean at the start of the review;
  during the review (`12:06:57` local) a concurrent operator action modified `r1/tracks/ops/trks-servers`
  and `r1/tracks/ops/trks-watch` (uncommitted, rev 3.3 drill-marker change) and copied the new files to
  TASL-2. This is outside the reviewed commit and outside my changes; see the workspace note in §2.1.
- Runbook `docs/trackS-decisions-30oct:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, revision
  **3.2**, sha256 `1789c000dbeaaa96202e00d72714d6b5df4e87733ca8f5823b9afd01ac7091ab`. The copy at
  `/Users/wongdowling/Documents/agent_paper_B/docs/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` is
  revision **3.3**, sha256 `a93fb84b…2a53` (mtime `2026-10-30T11:24:55+01:00`); see P2. The operator's
  report cites 3.2 and the sha of the docs-branch copy, and the installed host scripts were the 3.2
  versions during the phase (TASL-2's two were replaced by 3.3 during this review; §2.1). Phase 1/2 were
  therefore run under 3.2.
- Design `docs/trackS-decisions-30oct:docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`
  (rev 7.4), §2 (S0.1/S1.1) and §10 (STOPs).
- Deliverables: `docs/r1/reports/TRACKS_PHASE1_20261030.md` (194 lines), the top `docs/r1/STATUS.md`
  entry, `docs/r1/reports/TRACKS_HOST_FACTS_20261030.md` (Phase 0), `results/r1/tracks/*`,
  `r1/tracks/ops/launch/tasl{2,7}_s01.sh`.

All times UTC unless stated. The hosts' raw logs are local PDT (UTC−7); report stamps are UTC.

## 1. Scope

In scope: (i) the S0.1 determinism/latency/CPU census on both hosts at k = 2 servers; (ii) the S1.1
interaction check on both hosts and on the Mac for `openml_breast_w`; (iii) the Phase 1 "Done when" rule
and the operator's STOP-1 disposition; (iv) provenance, copy-back fidelity, projection arithmetic, the
Mac run's provenance, host pin/safety state and the launch scripts; (v) the three items the operator
flagged to the author. Out of scope: interpreting the S0.1 outcome, choosing k, and any later phase.

I did **not** start a GPU server, change a pin, the GGUF, a server flag or any file other than this
review. I did not touch the main working tree (its pre-existing `docs/r1/*` → `docs/*` move is untouched).

## 2. What I re-verified and how

### 2.1 Repository, pins and host state

```
git -C .claude-worktrees/trackS-ops-20261030 rev-parse HEAD        # 51984467
git -C .claude-worktrees/trackS-ops-20261030 status --porcelain    # only this review file at review start
ssh portal_zhixu 'trks-status' ; ssh tasl7 'trks-status'
```

Both hosts, at review time (`2026-10-30T11:04Z`):

| Check | TASL-2 | TASL-7 |
|---|---|---|
| paper (detached) | `9bb64ba6712668c4bab4a66720cf7f2645e1c672` | same |
| harness (detached) | `115df37d2b4581487eb2d911dc4d6a903afcc76a` | same |
| llama.cpp | `620d2225cc436ab0b001e3200e590e3b286ef9ab` | same |
| paper tracked-file modifications | 0 | 0 |
| GGUF sha256 | `509287f7…4d3c` (pin) | `509287f7…4d3c` (pin) |
| `llama-server --version` | `0.7.0-dev (build 11669, commit 620d2225c)` | same |
| compute apps | none | none |
| `flock -n ~/r1_locks/gpu0.lock true` | free | free |
| `trks_watch` | running (pid 2803053; watch log `01:14:12Z`) | running (pids 1268145/1268146, since 01:13:42Z) |
| `trks_llm` | absent | absent |
| `~/r1_locks` | only `gpu0.lock`; no marker | only `gpu0.lock`; no marker |
| pre-existing TASL-2 processes | Track P `llama-server` pids 2945752/3747685, started 26 Oct, still alive, no GPU memory; tmux `12` and `r1p_agent` still alive | — |

The installed `trks-run`, `trks-servers`, `trks-watch` and `trks-status` were byte-identical to the
committed `r1/tracks/ops/*` when checked (TASL-2 at `11:04Z`: `b53bc811…`, `47dcf336…`, `3108566d…`,
`a217f6b8…`; TASL-7 still had the 3.2 `trks-servers`/`trks-watch` at `12:07Z`); the installed `trks` is
the host-filled copy (label/UUID), as intended. The installed `trks-servers`/`trks-watch` were the 3.2
versions (no `trks_drill.active`) during the phase; 3.3 says to reinstall them **before Phase 3**, which
has not started — correct for this phase.

**Workspace note (concurrent action during the review, outside the reviewed commit).** At `12:06:57`
local the operator worktree's `r1/tracks/ops/trks-servers` and `trks-watch` changed (uncommitted; adding
the rev 3.3 `$R/trks_drill.active` marker), and by `12:07Z` TASL-2's installed copies matched them
(`124316b5…` / `cf68843e…`), while TASL-7 still had the 3.2 copies (`47dcf336…` / `3108566d…`). The
running `trks_watch` on TASL-2 is still the process started on 29 Oct (same pid, one `watch started`
line); replacing the file does not restart it. This is the rev 3.3 "reinstall before Phase 3" step in
progress. It is not part of commit `51984467`, it does not touch any Phase 1/2 artefact, and it does not
affect this review's evidence or verdict; I did not make or revert these edits.

### 2.2 Copy-back fidelity

`sha256sum` on the Mac copies and on the hosts' `$R/out/<node>/{s01,s11}/` originals:

| file | sha256 (Mac = host) | report |
|---|---|---|
| `digits_mlp/s01/serial.json` | `65388dfaa60cc5380733dd15befec4b39c873872b01d4d5088b7ac3068d7b56a` | matches §1 |
| `digits_mlp/s01/concurrent.json` | `005cadb3a2b37cb5c7ed6d5136bcced23847fea4fd6815233a1caaf3c6a9b182` | matches §1 |
| `tabular_mlp/s01/serial.json` | `31d463c4a190cf2c9fd18ef77ccca452a3a49bb647fd35f66499423883bc54c8` | matches §1 |
| `tabular_mlp/s01/concurrent.json` | `d65c4c815cd57715dfc805b57d176b447b4807d88b8d99aed561a1d051554328` | matches §1 |
| `digits_mlp/s11/digits.json` | `b4e364811dd9bf8ccbd2f4f6d011bf084bb01352a77ccc8520518b5e3a4c6174` | not tabulated |
| `tabular_mlp/s11/tabular.json` | `5ac5154bf5aca6cbe84a9ed3f901b383b38b04f6ccc0ae47826964da4ac90eaa` | not tabulated |
| `openml_breast_w/s11/breast_w.json` | `f9b9c7e879853f3ef8549bf4f98b0b98ef46356b8ebd6340560d1ca0cb4d7000` | matches §5 |

The copy-back is faithful. The hosts' `trks_s01_*`/`trks_s11` logs print the same `per_url` dictionaries
and the same S1.1 summary lines as the copied-back files, and the `.exit` files are `rc=0` at the times
the report states (10:20:24Z/10:20:21Z serial; 10:45:44Z/10:46:36Z concurrent; 10:52:40Z/10:52:39Z S1.1).

### 2.3 S0.1 arithmetic from the raw files

I recomputed every report value from `results/r1/tracks/*/s01/*.json`; exact integers are in parentheses.

| | digits_mlp (TASL-2) | tabular_mlp (TASL-7) |
|---|---|---|
| serial within-server identity | **0.930** (186/200) | **0.870** (174/200) |
| serial mean / p95 latency | 0.644596 / 0.691548 s | 0.658160 / 0.716086 s |
| serial errors / latency n | 0 / 600 | 0 / 600 |
| concurrent 18101 identity (per-client; cross-client) | **1.000** (1.000/1.000; 1.000) | **1.000** (1.000/1.000; 1.000) |
| concurrent 18102 identity (per-client; cross-client) | **0.925** (0.970/0.955; 0.925) | **0.855** (0.925/0.930; 0.855) |
| `cross_server_identity` | **0.915** (183/200) | **0.875** (175/200) |
| concurrent 18101 mean / p95 | 2.521700 / 2.670175 s | 2.602933 / 2.795111 s |
| concurrent 18102 mean / p95 | 2.527256 / 2.675937 s | 2.606604 / 2.795419 s |
| concurrent errors / latency n per URL | 0 / 1200 | 0 / 1200 |
| CPU cores / `cores_free_est` after serial | 32 / 29.7832 | 24 / 22.8916 |
| CPU cores / `cores_free_est` after concurrent | 32 / 28.7456 | 24 / 22.0767 |

Every number in report §2.1–§2.2 is the raw value (the report rounds 2.521700→2.5217 etc.). The CPU
census is reproducible as `cores_free_est = cpus − load1`: e.g. TASL-2 concurrent after,
`32 − 3.2543945 = 28.745605`, exactly the stored field; likewise all eight census records. The counts are
internally consistent: on digits 18102 the 15 non-identical prompts are exactly the disjoint union of the
9 bad prompts of client 0 and the 6 of client 1 (194/200 + 191/200 → 185/200); on tabular 18102 the 29
are the union of 15 + 14 (185/200 + 186/200 → 171/200). `cross_client_identity` equals the within-server
rate on 18102 in both nodes; this is consistent with the per-client counts and the probe's definitions
(`cross_identity` compares first contents, `identity_rate` requires every repeat of every client).

**Limitation (P3).** The pinned probe writes only aggregates: `determinism.py:313` drops `contents` from
`per_url`. The identity rates therefore cannot be recomputed from raw per-call responses; I verified them
by exact reproduction of the stored aggregates, by re-deriving the call schedule (below), and by the
report's definitions matching the probe's code. This is a property of the pinned probe, not an operator
error.

### 2.4 Probe provenance

All four S0.1 files carry:

- `provenance.gguf_sha256 = 509287f7…4d3c` (pin), `gguf_path` the pinned GGUF,
  `llama_build = 620d2225cc436ab0b001e3200e590e3b286ef9ab`, and `server_args` the exact
  `llama-server -m … --alias r1-manager --host 127.0.0.1 --port 18101 -ngl 999 -c 8192 --parallel 1
  --verbose` (serial), or both command lines joined by `" | "` (concurrent; P4).
- `order.seed = 1` (serial) / `2` (concurrent), matching Phase 1.
- `request_example` with `seed = 1332422715`, `temperature = 0.2`, no `max_tokens`, and
  `response_format` = the `manager_proposal/v1` JSON schema. `1332422715` is exactly
  `manager_seed("tracks_s01", 2, 0, 0)` under harness `115df37` (`sha256(...).digest()[:4]`).
- `server_props` for each URL: `n_ctx = 8192`, `total_slots = 1`, `model_alias = r1-manager`,
  `model_path` the pinned GGUF, `build_info = b11669-620d2225c`, and the full generation defaults.

I independently re-derived each `order_head` with the probe's own rule
`random.Random(f"{order_seed}|{url_index}|{client}").shuffle(items)` for `items = [(i,r) for r in
range(3) for i in range(200)]`. All 1 + 4 + 1 + 4 = 10 recorded heads match exactly. This is direct
evidence that the recorded order seeds were the ones used and that the 200×3 schedule is the intended
interleaved one.

The server logs confirm the actual servers: two `llama-server` logs per host, `build 11669
(620d2225c)`, `offloaded 29/29 layers to GPU`, `CUDA0 model buffer size = 4168.09 MiB`,
`CUDA0 KV buffer size = 448.00 MiB`, `n_ctx = 8192`, `n_slots = 1`. The report's "29/29 layers" is
verified; its "5.2 GiB each" is not independently reproducible from the copied-back evidence (the log
shows 4.5 GiB model+KV; the balance is plausibly compute buffers measured by `nvidia-smi` and not
recorded). No impact on the phase.

### 2.5 The Phase 1 "Done when" rule, re-applied verbatim

The runbook (3.2, lines 207–211) says:

> **k = 2** if, in the concurrent run, within-server identity is **100 %** on both URLs **and**
> `cross_server_identity` is **100 %** (§0.5).
> Else **k = 1** if identity is 100 % in the serial run. Restart the servers with k = 1 for all later
> phases.
> Else **STOP** for the author.

Applying it to the observed numbers:

| tier | digits_mlp | tabular_mlp |
|---|---|---|
| k = 2 (both URLs 100 % **and** cross-server 100 %) | fails (1.000 / 0.925; cross 0.915) | fails (1.000 / 0.855; cross 0.875) |
| k = 1 (serial 100 %) | fails (0.930) | fails (0.870) |
| else | **STOP** | **STOP** |

The result is unambiguously the STOP branch on both hosts. The report's §3 table and conclusion are
correct. Design §2 ("100 % within-host identity in the chosen setting; else STOP") and §10 ("the S0.1
identity check fails") agree, as does runbook §10 ("S0.1 identity < 100 % in both settings → STOP
(author)"). The operator did not set k anywhere and did not start a later phase (§2.7 below).

### 2.6 Projection arithmetic

The runbook formula is `(C·L/k + R·t_run/c)/3600` with C = 80 000, R = 60 000,
`c = min(free cores, k×2)`. `t_run` is from the Phase 0 smoke test. I recomputed `t_run` directly from
the hosts' smoke logs (`run_command finished in Xs` lines):

- TASL-2 `trks_smoke.log`: **n = 77, mean 0.909091 s**, median 0.800, max 1.9, min 0.6.
- TASL-7 `trks_smoke_retry.log` (successful campaign only): **n = 155, mean 1.913548 s**, median 1.900,
  max 4.6, min 0.6. The excluded failed-attempt runs are n = 10, mean 0.8200 — exactly as the report
  states (Phase 0 review m7).

I then recomputed the table. `L` is the serial mean for k = 1 and the mean of the two concurrent URL
means for k = 2 (both URLs have n = 1200, so this equals the pooled mean).

| node | k | L (s) | c | LLM h | CPU h | total h | days | report total |
|---|---|---|---|---|---|---|---|---|
| digits_mlp | 1 | 0.644596 | 2 | 14.3244 | 7.5758 | **21.9002** | 0.9125 | 21.90 |
| digits_mlp | 2 | 2.524478 | 4 | 28.0498 | 3.7879 | **31.8377** | 1.3266 | 31.84 |
| tabular_mlp | 1 | 0.658160 | 2 | 14.6258 | 15.9458 | **30.5716** | 1.2738 | 30.57 |
| tabular_mlp | 2 | 2.604769 | 4 | 28.9419 | 7.9729 | **36.9148** | 1.5381 | 36.91 |

Every tabulated number is reproducible. The free-core values at the end of the concurrent probes are
28.7456 (TASL-2) and 22.0767 (TASL-7), so the `k×2` cap binds in every row; `c = 2/4` is correct. No
node exceeds the 4-day fallback threshold (96 h) on either branch.

**On "k = 2 buys no LLM throughput" (P1).** The conclusion is true, but the report's arithmetic mixes two
models. The tabulated LLM term doubles (14.32 → 28.05 h), which is the formula's `C·L/k` with k = 2
streams and L = 2.52 s, i.e. ~0.79 calls/s — half the serial rate (1.551 calls/s). The concurrent probe,
however, ran **two clients per server** (4 client streams); its realised call rate is
4 / 2.5245 = 1.585 calls/s on digits (vs 1.551 serial, +2.1 %) and 4 / 2.6048 = 1.536 on tabular (vs
1.519, +1.1 %) — flat, because L includes queueing behind the second client on each single-slot server.
So "no LLM throughput gain" follows both from the formula's LLM term (indeed a loss) and from the
measured 4-stream call rate (flat), but the sentence "only doubling the number of LLM streams, so ...
the LLM term doubles" conflates the formula's 2-stream model with the probe's 2k-client setting. This is
a presentation issue in a non-decisional paragraph; the operator explicitly labels it "a property of the
projection, not a decision". MINOR.

### 2.7 No later phase was started

Checked on both hosts:

| Check | TASL-2 | TASL-7 |
|---|---|---|
| `find $R/out -maxdepth 3` | `smoke/`, `digits_mlp/{s01,s11}`, empty `digits_mlp/inputs` | `smoke/`, `tabular_mlp/{s01,s11}`, empty `tabular_mlp/inputs` |
| `$R/logs` sessions | smoke, smoke_dry, s01_serial, s01_conc, s11 | smoke, smoke_dry, smoke_retry, s01_serial, s01_conc, s11 |
| manifests | only `out/smoke/manifest.json` (phase `S0.4`, `instances: 1`, created `20261030T011713Z`, Phase 0 smoke) | only `out/smoke/manifest.json` (same, created `20261030T011702Z`) |
| tmux | `12`, `r1p_agent`, `trks_watch` | `trks_watch` |
| `$R/scratch` | only `digits_mlp/smoke` | only `tabular_mlp/smoke` |
| any `trks_s04`/`trks_tune*`/`trks_s3*` session/log | none | none |
| any `$OUT/s04`, `tune*`, `s3a*`, `s3e*`, `EVIDENCE` | none | none |
| branch HEAD / worktree | `51984467`; phase commit only | same |

`out/smoke` is the Phase 0 smoke test required by runbook 0.10 (`--phase S0.4 --instances 1`, manifest
`instances: 1`), not the Phase 3 S0.4 campaign. There is no `$OUT/s04`. The branch is pushed to GitHub
and to both hosts' bare repositories at `51984467`; there is no later commit. **No phase after Phase 2
was started.**

### 2.8 Phase 2 (S1.1): recomputation

I recomputed every contrast from `results/r1/tracks/*/s11/*.json` with
`I_s = y11 − y10 − y01 + y00`, `sd = std(I, ddof=1)`, `t = stats.t.ppf(0.975, n−1)`, `half = t·sd/√n`.
All three files have `seeds = 37001…37030` (30), `split = "vary"`, and four metrics arrays of length 30
with no nulls; cell arrays are aligned by seed.

| node | pair | levels (00/11) | I | 95 % t-CI | report |
|---|---|---|---|---|---|
| digits | HIDDEN_UNITS × BATCH_SIZE | 32/64, 64/128 | +0.005663800 | [+0.002966901, +0.008360699] | +0.005664 [+0.002967, +0.008361] |
| digits | HIDDEN_UNITS × LEARNING_RATE_INIT | 32/64, 1e-3/0.002 | −0.003528400 | [−0.006133097, −0.000923703] | −0.003528 [−0.006133, −0.000924] |
| digits | BATCH_SIZE × LEARNING_RATE_INIT | 64/128, 1e-3/0.002 | +0.008170800 | [+0.005268027, +0.011073573] | +0.008171 [+0.005268, +0.011074] |
| tabular | HIDDEN_UNITS × BATCH_SIZE | 32/64, 64/128 | +0.002646667 | [+0.001755891, +0.003537442] | +0.002647 [+0.001756, +0.003537] |
| tabular | HIDDEN_UNITS × LEARNING_RATE_INIT | 32/64, 1e-3/0.002 | −0.002659167 | [−0.003637191, −0.001681142] | −0.002659 [−0.003637, −0.001681] |
| tabular | BATCH_SIZE × LEARNING_RATE_INIT | 64/128, 1e-3/0.002 | +0.004889167 | [+0.004049136, +0.005729197] | +0.004889 [+0.004049, +0.005730] |
| breast_w | max_iter × C | 100/200, 0.01/0.02 | 0.000000000 | [0.000000000, 0.000000000] | 0.000000 [0, 0] |

The report's values are the same to its rounding. The host `trks_s11.log` files print exactly these
summaries and `trks_s11.exit` is `rc=0` on both. The Mac file has the same 30 seeds and one pair.

**`openml_breast_w` characterisation.** I checked every seed: `00[i] == 10[i]` and `01[i] == 11[i]` for
all 30 seeds, and the cell means are 00 = 10 = 0.9950082, 01 = 11 = 0.9950886. `max_iter` 100 vs 200 is
therefore inert on `val_auc` for this node, the interaction is exactly 0, and only `C` moves the metric
(by +8.0e-5). The report's "degenerate: cells 00≡10 and 01≡11; max_iter is inert; only C moves the
metric; says nothing about a max_iter effect" is correct. The node is `logistic_regression` with
`max_iter` in `ALLOWED_RANGES(100, 3000)` and `C` editable; the code defaults are the levels used.

### 2.9 Mac provenance for `openml_breast_w`

The scratch environment exists at
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/_trks_ops_s11/` (outside the worktree, not
committed). Verified:

- `harness` is a clone of `https://github.com/dowlingwong/autoresearch_harness` at
  **`115df37d2b4581487eb2d911dc4d6a903afcc76a`** (the pin), with one untracked runtime directory
  `nodes/openml_breast_w/data_cache/` (the downloaded OpenML data).
- venv Python **3.11.11**; installed **numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, pandas 3.1.0**.
  These are exactly the versions in the frozen host `pip_freeze.txt` on both hosts, so the Mac and host
  S1.1 numbers are on the same dependency set. `pandas` was installed at `11:19:50` local, after the
  first failed attempt (numpy/scipy/sklearn at `11:14:24–27`), which is consistent with the report's
  "first attempt failed for a missing dependency".
- The node calls `fetch_openml(..., as_frame=True)` (`benchmark.py:176`), so pandas is required; the
  data cache is under the scratch harness.
- The result `breast_w.json` sha256 is `f9b9c7e8…d7000` (matches the report) and its mtime (`11:24:16`)
  follows the scratch env creation (`11:14–11:19`). The paper `r1/tracks/probes/s1_factorial.py` and
  `determinism.py` are unchanged between `9bb64ba` and `51984467` (`git diff` empty), so the effective
  paper code is the pin.

I cannot prove from the artefact alone which `r1` checkout was on `sys.path`; the scratch venv does not
install `r1`, and the run must have used the worktree (code unchanged) or an equivalent checkout. The
harness pin, dependency versions, data cache and mtimes are all consistent with the report.

### 2.10 Safety and propriety

- Pins, GGUF, tracked-file cleanliness: §2.1 — all OK.
- Lease: `flock -n ~/r1_locks/gpu0.lock true` succeeds on both; no `trks_llm`; no compute apps.
- Watcher: running on both with one `watch started` line and no pause/`FORCED` lines; the watch log has
  no priority-marker entry.
- No unowned process killed: the two Track P `llama-server` processes (started 26 Oct) and the TASL-2
  tmux sessions `12` and `r1p_agent` are still alive; I found no evidence of any other process being
  signalled. (I cannot prove a negative for the whole period, but the expected survivors survive.)
- Nothing written outside the approved work directory in Phase 1: `find /home/dowling -maxdepth 2
  -newermt '2026-10-30 09:00:00'` outside `$R` and `~/r1_locks` returns nothing on either host. The
  Phase 0 uv-installer footprints outside `$R` are already recorded in the Phase 0 report.
- `$R/launch` contains only `tasl2_s01.sh` / `tasl7_s01.sh`; `$OUT/inputs` is empty (no later-phase
  `dev_roots.jsonl` or π′).

### 2.11 Committed launch scripts against §0.1

`r1/tracks/ops/launch/tasl{2,7}_s01.sh` are committed in `51984467` and byte-identical to the host copies
(`a8f0d479…` / `a36dd9d0…`). They:

- start with `set -euo pipefail; R=…; OUT=$R/out/<node>; WORK=$R/scratch/<node>; IN=$OUT/inputs;
  PATH=$R/bin:$PATH`;
- run each probe via `trks-run trks_s01_serial - probe …` / `trks_s01_conc`, i.e. the probe is the tmux
  session's command, not an inline `ssh` collector string (the `$R/logs/*.cmd` files record the exact
  argv with `printf %q`);
- serialise serial before concurrent (`wait_session`), check each `rc`, and `mkdir -p "$OUT/s01"`;
- use a scalar `$S1`/`$S2` for `--server-args` (a single argument by design) and quoted expansions; no
  policy string is passed, and no quote character is put inside a variable. The two `--url` options are
  literal, not a variable expanded unquoted. This satisfies §0.1's array/quoting intent for this phase.

The only nuance is the concurrent `--server-args "$S1 | $S2"` (P4).

## 3. Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| **P1** | MINOR (framing) | The "k = 2 buys no LLM throughput" sentence is qualitatively right but mixes two models. The tabulated LLM term is the formula's `C·L/k` with k = 2 streams and L = the 4-client latency, and it doubles (14.32 → 28.05 h), i.e. ~0.51× the serial call rate; the concurrent probe's realised 4-client call rate is flat (1.551 → 1.585 calls/s digits; 1.519 → 1.536 tabular). The conclusion "no gain" holds on either reading, but "only doubling the number of LLM streams" is the formula's 2-stream model while the probe ran 2 clients/server. The operator labels the paragraph non-decisional. | Recomputed projection table; `results/.../s01/*.json` latency means; `80000/(28.05·3600)` vs `1/0.6446`; report §4. |
| **P2** | MINOR (provenance) | The report cites runbook rev **3.2** (sha `1789c…`), which is the docs-branch copy and the revision the installed scripts implemented during the phase; the file at the absolute path `/Users/wongdowling/Documents/agent_paper_B/docs/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` is rev **3.3** (sha `a93fb84…`, mtime `2026-10-30T11:24:55+01:00`), whose §0.6 *does* define the failed-units denominator. The §0.6 "no denominator" flag is accurate for 3.2 (the runbook of record) but stale against the 3.3 file now at that path. The operator should state which revision governs and reconcile the two copies. | `sha256sum` of both copies; `diff -u` (only 3.2→3.3 changes); `git show docs/trackS-decisions-30oct:…`; report §5/§6; Phase 0 report §3 0.10. |
| **P3** | MINOR (evidence limitation) | The S0.1 identity rates cannot be recomputed from raw per-call responses because the pinned probe drops `contents` (`determinism.py:313`). I verified the stored aggregates, their integer-count consistency, the report's match to them, and the call schedules from the order seeds; but the central identity claim rests on the pinned probe's computation, not on independently replayable raw responses. | `r1/tracks/probes/determinism.py:305–315`; JSON keys; reproduced `order_head` for all 10 URL/client combinations. |
| **P4** | MINOR (provenance clarity) | The concurrent probe's `provenance.server_args` is two exact command lines joined by a literal `" | "`, not a single exact command line (the serial one is exact). The two commands individually match the installed `trks-servers` command and §0.2 flags, and the runbook's concurrent example is `"…"`, so this is acceptable, but the pipe character could be misread as a shell pipe. | `provenance.server_args` in both concurrent JSONs; `r1/tracks/ops/launch/tasl{2,7}_s01.sh`; installed `bin/trks-servers`. |
| **P5** | MINOR (record) | The Phase 1 commit amended the Phase 0 report's m10 disposition from "the denominator is stated as exhausted/planned" to "flagged as a rule gap", but the Phase 0 review file's operator note still says m10 was fixed by adding the sentence. The Phase 1 report/STATUS do record the flag, so the current position is consistent; the historical Phase 0 record is not. | `git show 51984467 -- docs/r1/reports/TRACKS_HOST_FACTS_20261030.md`; Phase 0 review tail; report §3 0.10 / §8 m10. |
| **P6** | MINOR (process record) | The Phase 1 report does not record the §0.4 pre-start checks (priority markers absent, no compute apps) before `trks-servers 2`; it records the post-phase state. `trks-servers` enforces the marker check and flock, and the GPU was free (the two Track P servers hold no GPU memory), so the risk is low, but the check is part of the runbook. | Report §1/§6; `bin/trks-servers` (3.2); `nvidia-smi` at review time; Phase 0 report §1. |

No BLOCKING or MAJOR findings. All six are report/provenance/process records; none changes the STOP-1
decision or any S0.1/S1.1 number.

## 4. Acceptance checklist

### Phase 1 (S0.1)

| Requirement (runbook Phase 1 / §0.5 / §10) | Status | Evidence |
|---|---|---|
| Servers started with k = 2 on both hosts (ports 18101/18102) | **PASS** | two server logs per host; `n_ctx 8192`, `n_slots 1`, `offloaded 29/29`, `CUDA0 model 4168.09 MiB`; lease free after |
| Serial probe from a launch script, via `trks-run`, before concurrent | **PASS** | `$R/logs/s01_launch.log`; `trks_s01_serial.cmd`; rc=0 |
| Concurrent probe with two URLs and `--clients-per-url 2` | **PASS** | `trks_s01_conc.cmd`; JSON `clients_per_url: 2`; rc=0 |
| `--n 200 --repeats 3 --order-seed 1/2 --proposal-schema manager_proposal/v1` | **PASS** | JSON fields; reproduced `order_head` |
| GGUF sha256, llama build, exact server command, fixed request seed recorded | **PASS** | `provenance`/`request_example`; `1332422715 = manager_seed(…,2,0,0)`; P4 caveat |
| Latency (mean/p95) and free cores recorded | **PASS** | §2.3 table; `cpu_before`/`cpu_after`; P3 caveat on raw identity |
| "Done when" rule applied verbatim | **PASS** | k=2 fails on both; k=1 fails on both; STOP |
| k left unset; no later phase | **PASS** | no k anywhere; §2.7 |
| Projection reported | **PASS** | §2.6; all four totals reproduce; P1 caveat |
| STOP 1 raised for the author | **PASS** | report §3/§6; STATUS |
| Review loop (fresh reviewer) | **PASS** | this file |

### Phase 2 (S1.1)

| Requirement (runbook Phase 2 / design §2) | Status | Evidence |
|---|---|---|
| Host runs on the right nodes (digits/TASL-2, tabular/TASL-7) | **PASS** | `trks_s11.cmd`; JSON `node`; rc=0 |
| Mac run for `openml_breast_w` with `--pair max_iter:C` | **PASS** | JSON node/pair; scratch env; result sha |
| 30 S1.1 seeds under the `vary` split | **PASS** | `seeds 37001…37030`; `split: "vary"`; `run_config` train=split=s |
| Factor pairs and levels | **PASS** | JSON `levels`: 32/64, 64/128, 1e-3/0.002; 100/200, 0.01/0.02 |
| Interaction contrasts and t-intervals recomputed | **PASS** | §2.8 table; exact matches |
| `breast_w` correctly characterised | **PASS** | 00≡10 and 01≡11 for all 30 seeds; I=0 exactly; only C moves `val_auc` |
| Mac provenance (harness 115df37, deps) | **PASS** | harness HEAD; venv versions equal host freeze; data cache; pandas install timeline |
| Phase 2 not a gate | **PASS** | report §5 says so; no gate applied |
| All runs rc=0 / all seeds have metrics | **PASS** | host `.exit` rc=0; JSON no nulls; Mac file complete |

### Safety / propriety

| Requirement | Status | Evidence |
|---|---|---|
| Hosts at paper `9bb64ba` / harness `115df37`, no tracked mods | **PASS** | `trks-status`; `git status --porcelain` |
| GGUF unchanged | **PASS** | sha `509287f7…4d3c` on both |
| GPU lease released, no compute apps | **PASS** | `flock -n` succeeds; `nvidia-smi` empty |
| `trks_watch` still running | **PASS** | pids since 29 Oct; watch log clean. TASL-2's script file was replaced by 3.3 during this review, but the running process is still the 29 Oct one (§2.1) |
| No unowned process killed | **PASS** (no evidence of one) | Track P servers/tmux survivors |
| Nothing outside `$R` except recorded | **PASS** | `find … -newermt`; Phase 0 uv footprints recorded |
| Launch scripts comply with §0.1 | **PASS** | committed/copied/run; `set -euo pipefail`; `trks-run`; quoted; P4 note |

## 5. Independent ruling on STOP 1

**STOP 1 is correctly raised.** The Phase 1 rule is ordered and exhaustive for this observation set:

1. k = 2 requires concurrent within-server identity 100 % on **both** URLs **and**
   `cross_server_identity` 100 %. On digits 18101 is 1.000 but 18102 is 0.925 and cross-server is 0.915;
   on tabular 18101 is 1.000 but 18102 is 0.855 and cross-server is 0.875. The tier fails on both hosts.
2. k = 1 requires serial identity 100 %. It is 0.930 on digits and 0.870 on tabular. The tier fails on
   both hosts.
3. The rule's remaining branch is **STOP for the author**. That is what the operator did.

The operator's disposition is correct: STOP raised, k left unset, no later phase started, no attempt to
reinterpret the rule or to pick a server. The S0.1 outcome itself is an engineering finding for the
author, not for the operator; the phase correctly reached its STOP. The two probes and the S1.1 runs are
complete, faithfully copied back, and provenance-complete; the host state is clean. The findings in §3
are MINOR and do not affect the STOP or the recorded numbers.

## 6. The three flagged items

**(a) Mixed server result / re-run before the STOP is final.** The "mixed result" half is **not** a real
gap for this run: the k = 2 tier explicitly requires both URLs, so 1.000 / 0.925 fails it, and the k = 1
tier is decided by the serial run, which fails. The report concedes this. The genuine gap is the absence
of any statement on whether the operator may re-run the concurrent probe (or restart servers) before the
STOP becomes final; the rule says only "Else STOP". The operator correctly **did not decide** this and
flagged it; the runbook owner must clarify. Recorded accurately, with a slight overstatement of the
mixed-result ambiguity. **MINOR.**

**(b) §0.6 "> 2 % failed units" denominator.** Under the runbook actually cited and used, **rev 3.2**,
this is a **real gap**: §0.6 says only "More than 2 % failed units in a phase is a STOP", with no
numerator/denominator, while `failed_units.jsonl` counts attempts and the TASL-7 manifest shows
`done.failed: 0`, `roots: 1/1` for a still-logged attempt. The operator correctly **refrained from
adopting a denominator** (the author's instruction; the Phase 0 report's m10 row was amended to a flag)
and recorded it. It is **not** a Phase 1 failure (the probes have zero failed units); it is a runbook gap
for S0.4/S0.7/S3e. Caveat: rev 3.3, now at the main-tree absolute path, resolves it
(`exhausted / (committed + exhausted)`), so the flag is stale against 3.3 and the revision provenance
should be reconciled (P2). **Real gap under 3.2; correctly flagged, not decided; recorded accurately for
3.2.**

**(c) `r1/tracks/probes/s1_factorial.py:139` `KeyError: 'ci95_t'`.** **Real pinned-code bug.** I reproduced
it: `interaction()` returns `{"n": 0, "interaction": None}` when no cell has ≥ 2 usable rows, `run_pair`
merges that into a result that still has `pair`/`levels`, line 138 writes the file, and line 139's
`r[k] for k in ("pair","n","interaction","ci95_t")` raises `KeyError('ci95_t')`. The operator correctly
**did not change pinned code** and flagged it; the report's account (after writing, on a pair with no
data, first `breast_w` attempt, missing dependency) is accurate as to the code path. I cannot
independently verify the first attempt's exact error from an artefact (the output is overwritten by the
successful run), but the pandas install timestamp (`11:19:50`, after the first cells) supports the
"missing dependency" account. **MINOR.**

**Compliance with "do not reinterpret STOP rules".** The operator flagged all three rather than adopting
a reading, and amended the Phase 0 report's earlier adopted denominator to a flag. This complies with the
author's instruction. The only residual is the 3.2/3.3 provenance ambiguity (P2), which is a
documentation matter for the runbook owner.

## 7. What I could not verify

- **Identity rates from raw responses (P3).** The pinned probe stores aggregates only; no per-call
  content is in the result files. I verified the aggregates, their consistency, the report's match and
  the call schedules, but not a replay from raw responses. Replaying would require re-running the GPU
  probes, which is unnecessary for a STOP that is already determined.
- **The exact "5.2 GiB each".** The server log shows 4168.09 MiB model + 448 MiB KV; the remaining
  ~0.7 GiB is plausible compute buffers, but the run-time `nvidia-smi` total was not recorded.
- **The first `breast_w` attempt's exact traceback.** The code bug is reproduced and the pandas install
  timeline is consistent; the overwritten first output is not on disk.
- **The Mac `r1` checkout path.** The scratch venv does not install `r1`; the probe code is unchanged
  from `9bb64ba`, and the harness pin/deps/data cache are verified, but the exact `sys.path` used is not
  recorded.
- **A negative on "no unowned process was ever killed".** The expected Track P/Track X survivors are
  alive; no evidence of a kill was found.
- **The authoritative runbook revision (P2).** Two copies exist: 3.2 on the docs branch (cited, used by
  the installed scripts) and 3.3 at the main-tree absolute path (later, defines the §0.6 denominator).
  Phase 1/2 requirements are identical in both; the difference is the §0.6 flag.

## 8. Verdict and justification

The phase correctly reached STOP 1 and stopped. Every S0.1 number in the report reproduces from the raw
JSON, the copy-back is byte-identical to the hosts, the probes' provenance (GGUF, llama build, server
command, order seeds, fixed request seed) is complete and the order schedules are re-derivable, the four
projection rows reproduce exactly from the runbook formula and the re-derived `t_run`, the Phase 1
three-tier rule unambiguously yields STOP on both hosts, and no later phase was started. The S1.1
contrasts reproduce exactly for all seven pairs, the 30-seed/`vary`/levels setup is correct, the
`openml_breast_w` `max_iter`-inert characterisation is exactly right, and the Mac scratch environment's
harness pin and dependency versions are verified and match the host freeze. The host state is safe:
pins, GGUF, lease, watcher and non-interference all check out. The six findings are MINOR report,
provenance and process records (P1 the throughput framing, P2 the 3.2/3.3 revision provenance, P3 the
lack of replayable per-call identity data, P4 the joined concurrent `--server-args`, P5 the Phase 0 m10
historical record, P6 the unrecorded §0.4 pre-start checks); none changes the STOP decision, any recorded
number, or the safety posture. The three flagged items are real or accurately stated, and the operator
correctly flagged rather than decided them. The correct disposition for the author is to decide the S0.1
STOP (re-run/adjust/halt) and to reconcile the runbook revision and the three rule questions; the
operator should not start any later phase until then.

REVIEW VERDICT: ACCEPTED
