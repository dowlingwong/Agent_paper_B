# Track S — Phase 1 (S0.1 determinism/latency/census) and Phase 2 (S1.1 interaction) — STOP 1

**Written 30 Oct 2026 by the Track S operator agent; AI-assisted.** Runbook
`docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` revision 3.2
(sha256 `1789c000dbeaaa96202e00d72714d6b5df4e87733ca8f5823b9afd01ac7091ab`), Phases 1 and 2. Every
number here is **ENGINEERING_ONLY**: S0.1 and S1.1 feed the pre-declaration and are never quoted as
results. Code at paper `9bb64ba`, harness `115df37`; llama.cpp `620d2225` (v0.7.0); GGUF sha256
`509287f7…4d3c`. Hosts TASL-2 (`digits_mlp`) and TASL-7 (`tabular_mlp`). All report times UTC; raw log
lines keep the hosts' local PDT stamps (7 h behind UTC).

## 0. What was run, and the headline

- **Phase 1 (S0.1)** ran on both hosts with **k = 2** servers (ports 18101, 18102), serial then
  concurrent, each probe as the command of its own tmux session via `trks-run` (launch scripts
  `r1/tracks/ops/launch/tasl{2,7}_s01.sh`, committed). All four probes exited **rc=0** with **0 errors**.
- **Phase 2 (S1.1)** ran on both hosts (CPU, no LLM) and on the Mac for `openml_breast_w`. All three
  completed.
- **Headline: S0.1 does not reach 100 % identity in either setting on either host.** Under the
  runbook's Phase 1 "Done when" rule that is the **STOP** branch. **STOP 1 is therefore raised for the
  author**, not a k choice. Details in §2–§3.

## 1. Provenance of this phase

| Item | Value |
|---|---|
| launch scripts (committed) | `r1/tracks/ops/launch/tasl2_s01.sh`, `tasl7_s01.sh` |
| probe command (per host) | `$R/bin/trks-run trks_s01_serial - probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 --order-seed 1 --proposal-schema manager_proposal/v1 --node <node> --server-args "<exact server cmd>" --out $OUT/s01/serial.json` |
| concurrent command | same with `--url 18101 --url 18102 --mode concurrent --clients-per-url 2 --order-seed 2`, `--out $OUT/s01/concurrent.json` |
| out layout | `$OUT/s01/` with `OUT=$R/out/<node>` (§0.1 node-scoped layout) |
| servers | `bin/trks-servers 2` under `flock`; both ports `29/29 layers` offloaded, `5.2 GiB` each |
| session exit codes | serial `rc=0` (10:20:24Z TASL-2 / 10:20:21Z TASL-7), concurrent `rc=0` (10:45:44Z / 10:46:36Z) |
| probe request body | carries a fixed per-prompt `seed` (e.g. `1332422715`), `temperature 0.2`, `manager_proposal/v1` `response_format`; recorded under `request_example` |
| GPU lease | released after the phase: `flock -n ~/r1_locks/gpu0.lock` succeeds, `nvidia-smi --query-compute-apps` empty on both |

Result files (copied back to `results/r1/tracks/<node>/s01/`), sha256:

| file | sha256 |
|---|---|
| `digits_mlp/s01/serial.json` | `65388dfaa60cc5380733dd15befec4b39c873872b01d4d5088b7ac3068d7b56a` |
| `digits_mlp/s01/concurrent.json` | `005cadb3a2b37cb5c7ed6d5136bcced23847fea4fd6815233a1caaf3c6a9b182` |
| `tabular_mlp/s01/serial.json` | `31d463c4a190cf2c9fd18ef77ccca452a3a49bb647fd35f66499423883bc54c8` |
| `tabular_mlp/s01/concurrent.json` | `d65c4c815cd57715dfc805b57d176b447b4807d88b8d99aed561a1d051554328` |

## 2. S0.1 results

`n = 200` distinct manager prompts, `repeats = 3`, 0 transport errors in every run. "Identity" is the
share of prompts whose every repeat returned identical content.

### 2.1 Serial (one server, port 18101, 1 client)

| | digits_mlp (TASL-2) | tabular_mlp (TASL-7) |
|---|---|---|
| **within-server identity** | **0.930** (0.93) | **0.870** (0.87) |
| errors | 0 | 0 |
| latency mean / p95 | 0.6446 s / 0.6915 s | 0.6582 s / 0.7161 s |
| CPU cores / cores free (end) | 32 / 29.78 | 24 / 22.89 |

### 2.2 Concurrent (two servers, 2 clients per server)

| | digits_mlp (TASL-2) | tabular_mlp (TASL-7) |
|---|---|---|
| identity, 18101 | **1.000** (clients 1.000 / 1.000; cross-client 1.000) | **1.000** (1.000 / 1.000; 1.000) |
| identity, 18102 | **0.925** (clients 0.970 / 0.955; cross-client 0.925) | **0.855** (0.925 / 0.930; 0.855) |
| **cross_server_identity** | **0.915** | **0.875** |
| errors | 0 | 0 |
| latency mean / p95, 18101 | 2.5217 s / 2.6702 s | 2.6029 s / 2.7951 s |
| latency mean / p95, 18102 | 2.5273 s / 2.6759 s | 2.6066 s / 2.7954 s |
| CPU cores / cores free (end) | 32 / 28.75 | 24 / 22.08 |

**Observation (not a decision).** In the concurrent run the *first* server reached 1.000 on both hosts
while the *second* did not, and cross-server identity is well below 1. The probe deliberately
interleaves the repeats of each prompt with different predecessors so that prompt-cache / KV-order
effects surface as non-identical repeats (its own docstring), and the request body does carry a fixed
seed — so this is not a missing-seed artifact. The operator did not investigate the cause further.

## 3. The Phase 1 decision rule, quoted, and its outcome

Runbook Phase 1, "**Done when**", verbatim:

> - **k = 2** if, in the concurrent run, within-server identity is **100 %** on both URLs **and**
>   `cross_server_identity` is **100 %** (§0.5).
> - Else **k = 1** if identity is 100 % in the serial run. Restart the servers with k = 1 for all later
>   phases.
> - Else **STOP** for the author.

Applying it:

| tier | condition | digits_mlp | tabular_mlp |
|---|---|---|---|
| k = 2 | concurrent identity 100 % on **both** URLs **and** cross-server 100 % | fails (1.000 / 0.925; cross 0.915) | fails (1.000 / 0.855; cross 0.875) |
| k = 1 | serial identity 100 % | fails (0.930) | fails (0.870) |
| else | — | **STOP** | **STOP** |

Design §2/§10 agree: S0.1's gate is "100 % within-host identity in the chosen setting; else STOP", and
design §10 lists "the S0.1 identity check fails" as a STOP. Runbook §10: "S0.1 identity < 100 % in both
settings → STOP (author)".

**Outcome: STOP 1 is raised. k is not set, and no later phase was started.**

**Flag for the runbook owner (no operator reading adopted).** The ordered rule above does not say what to
do when the two servers disagree — here 18101 reached 1.000 in the concurrent run while 18102 did not,
and the serial run reached neither. "Within-server identity is 100 % on both URLs" is unambiguous for the
k = 2 tier (it fails), and the k = 1 tier is also unambiguous (serial fails); but the phrase in §0.5
("each host gets k = 2 only if … 100 % within-server identity on both servers") would benefit from an
explicit statement of what to do with a mixed result, and of whether a re-run is authorised before the
STOP becomes final. The operator has **not** decided either question.

## 4. Projection (reported for the author; formula from §Phase 1)

`projected hours = (C × L / k + R × t_run / c) / 3600`, with `C ≈ 80 000` LLM calls,
`R ≈ 60 000` worker and audit runs, `t_run` from the Phase 0 smoke test (`0.9091 s` digits /
`1.9135 s` tabular), `L` = the mean latency of the setting, `c = min(free cores, k × 2)`.

Because **k is undecided** (STOP), the projection is given for both candidates:

| node | k | L (s) | c | LLM h | CPU h | **total h** | days | > 4-day fallback? |
|---|---|---|---|---|---|---|---|---|
| digits_mlp | 1 | 0.6446 | 2 | 14.32 | 7.58 | **21.90** | 0.91 | no |
| digits_mlp | 2 | 2.5245 | 4 | 28.05 | 3.79 | **31.84** | 1.33 | no |
| tabular_mlp | 1 | 0.6582 | 2 | 14.63 | 15.95 | **30.57** | 1.27 | no |
| tabular_mlp | 2 | 2.6048 | 4 | 28.94 | 7.97 | **36.91** | 1.54 | no |

`L` for k = 2 is the mean over the two concurrent URLs (2.5245 s / 2.6048 s). Free cores at the end of
the concurrent probes were 28.75 (TASL-2) and 22.08 (TASL-7), so the `k × 2` cap binds in every row.

**Consequence worth stating plainly:** two servers on one 4090 roughly quadruple per-call latency
(0.64 → 2.52 s) while only doubling the number of LLM streams, so **k = 2 buys no LLM throughput** — the
LLM term doubles (14.32 → 28.05 h). k = 2 only helps the CPU term (c = 4 instead of 2). This is a
property of the projection, not a decision; the k choice is governed by §0.5/Phase 1.

Neither node crosses the 4-day fallback threshold on either branch, so on the Phase 1 projection **no
node drops from the decision** (design §2 fallback). The runbook leaves that confirmation to the author.

## 5. Phase 2 — S1.1 interaction check (CPU, no LLM; not a gate)

2 × 2 factorial at the 30 S1.1 seeds under the `vary` split; per seed the interaction contrast
`I = y11 − y10 − y01 + y00`; `t` interval reported. All runs `rc=0`, all seeds produced metrics.

**digits_mlp (TASL-2)**, 30 seeds:

| factor pair | interaction I | 95 % t-CI | excludes 0 |
|---|---|---|---|
| HIDDEN_UNITS × BATCH_SIZE | +0.005664 | [+0.002967, +0.008361] | yes |
| HIDDEN_UNITS × LEARNING_RATE_INIT | −0.003528 | [−0.006133, −0.000924] | yes |
| BATCH_SIZE × LEARNING_RATE_INIT | +0.008171 | [+0.005268, +0.011074] | yes |

**tabular_mlp (TASL-7)**, 30 seeds:

| factor pair | interaction I | 95 % t-CI | excludes 0 |
|---|---|---|---|
| HIDDEN_UNITS × BATCH_SIZE | +0.002647 | [+0.001756, +0.003537] | yes |
| HIDDEN_UNITS × LEARNING_RATE_INIT | −0.002659 | [−0.003637, −0.001681] | yes |
| BATCH_SIZE × LEARNING_RATE_INIT | +0.004889 | [+0.004049, +0.005730] | yes |

**openml_breast_w (Mac)**, 30 seeds, `--pair max_iter:C`:

| factor pair | interaction I | 95 % t-CI | note |
|---|---|---|---|
| max_iter × C | +0.000000 | [+0.000000, +0.000000] | degenerate: cells `00`≡`10` and `01`≡`11` (max_iter 100 vs 200 leaves `val_auc` identical); only C moves the metric |

Reading (descriptive only, as the runbook asks — S1.1 "is reported with the result. It is not a gate"):
all three MLP-node pairs show a non-zero interaction whose interval excludes 0, at magnitudes of roughly
0.003–0.008 `val_score`; `breast_w`'s `max_iter` level is inert at 100 vs 200 so its interaction is
exactly 0 and says nothing about a `max_iter` effect.

**Provenance for the Mac run.** `openml_breast_w` is not run on the hosts by the runbook, so it ran on the
Mac against a **pinned** harness clone at `115df37` (scratch env
`.claude-worktrees/_trks_ops_s11/`, outside this worktree and not committed) with Python 3.11,
numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, pandas (needed because the node calls
`fetch_openml(..., as_frame=True)`). Result sha256
`f9b9c7e879853f3ef8549bf4f98b0b98ef46356b8ebd6340560d1ca0cb4d7000`. It downloads the breast-w dataset on
first use.

**Flag for the probe's owner (pinned paper code).** `r1/tracks/probes/s1_factorial.py:139` formats its
summary with `r[k] for k in ("pair","n","interaction","ci95_t")`, but `interaction()` omits `ci95_t` when a
pair yields no usable data, so the run ends in `KeyError: 'ci95_t'` *after* writing the report file. It
was hit on the first `breast_w` attempt (all cells failed for a missing dependency). No code was changed.

## 6. State at STOP 1

- Both hosts at the pins, no tracked modifications; `trks_watch` running; GPU lease **free**; no compute
  apps; no `trks_llm` session; probe sessions finished.
- Phase 1 and 2 outputs copied back to `results/r1/tracks/`; `$WORK` untouched on the hosts.
- **No later phase was started.** In particular no S0.4 (`digits` prior fit), no tuning, no EVIDENCE.
- Open for the author: (i) the S0.1 STOP itself — re-run, adjust the server/probe setting, or halt;
  (ii) the two rule questions flagged in §3 and the m10 denominator flag carried from Phase 0; (iii) the
  Phase 2 `KeyError` flag.

## 7. Files

- `docs/r1/reports/TRACKS_PHASE1_20261030.md` (this report)
- `results/r1/tracks/digits_mlp/{s01,s11}/`, `results/r1/tracks/tabular_mlp/{s01,s11}/`,
  `results/r1/tracks/openml_breast_w/s11/`
- `r1/tracks/ops/launch/tasl{2,7}_s01.sh`
