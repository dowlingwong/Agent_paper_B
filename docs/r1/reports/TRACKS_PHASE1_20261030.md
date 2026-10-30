# Track S — Phase 1 (S0.1 determinism/latency/census) and Phase 2 (S1.1 interaction) — STOP 1

**Written 30 Oct 2026 by the Track S operator agent; AI-assisted.** Runbook
`docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, Phases 1 and 2.

**Which revision governs.** These phases were **executed under revision 3.2**
(sha256 `1789c000dbeaaa96202e00d72714d6b5df4e87733ca8f5823b9afd01ac7091ab`, the copy on
`docs/trackS-decisions-30oct`). During execution the author revised the file at that path to
**revision 3.3** (sha256 `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`,
mtime 30 Oct 11:24). Revision 3.3 changes §0.6 (the 2 % rule), Phase 3 (adds the 3.0 pause drill and
3.0b), §0.3(c), §11.3/§11.4 (the drill marker) and the session-status wording; it does **not** change
the Phase 1 "Done when" rule or the Phase 2 text. **The STOP 1 outcome below is therefore the same under
3.2 and 3.3.** The operator adopted the 3.3 §11.3/§11.4 scripts and restarted the watcher (§6). Every
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
| servers | `bin/trks-servers 2` under `flock`; both ports `29/29 layers` offloaded; `nvidia-smi` reported **5242 MiB** per server process (the llama log gives the model buffer as 4168.09 MiB, the rest being KV/context) |
| session exit codes | serial `rc=0` (10:20:24Z TASL-2 / 10:20:21Z TASL-7), concurrent `rc=0` (10:45:44Z / 10:46:36Z) |
| probe request body | carries a fixed per-prompt `seed` (e.g. `1332422715`), `temperature 0.2`, `manager_proposal/v1` `response_format`; recorded under `request_example` |
| §0.4 pre-start checks (before `trks-servers 2`) | both hosts: `~/r1_locks` held only `gpu0.lock` (no `trackx_evidence.active`, no `trackp_evidence.active`, no `trks_drill.active`); `nvidia-smi --query-compute-apps` empty; no `r1p_*` session running a GPU job on TASL-7; no `trks_llm` session. Recorded here after the reviewer's P6 |
| GPU lease | released after the phase: `flock -n ~/r1_locks/gpu0.lock` succeeds, `nvidia-smi --query-compute-apps` empty on both |

Result files (copied back to `results/r1/tracks/<node>/s01/`), sha256:

| file | sha256 |
|---|---|
| `digits_mlp/s01/serial.json` | `65388dfaa60cc5380733dd15befec4b39c873872b01d4d5088b7ac3068d7b56a` |
| `digits_mlp/s01/concurrent.json` | `005cadb3a2b37cb5c7ed6d5136bcced23847fea4fd6815233a1caaf3c6a9b182` |
| `tabular_mlp/s01/serial.json` | `31d463c4a190cf2c9fd18ef77ccca452a3a49bb647fd35f66499423883bc54c8` |
| `tabular_mlp/s01/concurrent.json` | `d65c4c815cd57715dfc805b57d176b447b4807d88b8d99aed561a1d051554328` |

One provenance detail (reviewer P4): the **serial** probe's recorded `provenance.server_args` is one exact
server command line, matching the installed `trks-servers` command and §0.2's flags. The **concurrent**
probe's value is the two exact command lines joined by a literal `" | "`; the pipe is a separator in a
provenance string, not a shell pipe (both commands individually match the installed form).

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

**Evidence limitation (reviewer P3).** These identity rates cannot be recomputed from raw per-call
responses: the pinned probe keeps only aggregates and drops `contents` (`determinism.py:313`). The stored
aggregates, their integer-count consistency against `n × repeats`, and the call schedules reproducible
from `--order-seed` were checked, but the identity numbers rest on the pinned probe's own computation,
not on independently replayable responses.

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

**Flag for the runbook owner (no operator reading adopted).** The mixed-server case is **not** ambiguous
and is **not** the flag: the k = 2 tier needs 100 % on both URLs (it fails), and the k = 1 tier is decided
by the serial run alone (it fails), so the rule reaches STOP without needing a judgement about the
18101/18102 split. The genuine gap is narrower: **the rule does not say whether a re-run (or a change of
server/probe setting) is authorised before the STOP becomes final.** The operator has **not** decided
that question and has not re-run.

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

**Consequence worth stating plainly (non-decisional).** Two servers on one 4090 roughly quadruple
per-call latency (0.64 → 2.52 s). In the *formula's* two-stream model that doubles the LLM term
(14.32 → 28.05 h, i.e. ≈0.51× the serial call rate); in the *probe's measured* four-client setting the
realised call rate is essentially flat (1.551 → 1.585 calls/s on digits, 1.519 → 1.536 on tabular).
On either reading there is **no LLM-throughput gain from k = 2** — the LLM term doubles and only the CPU
term improves (c = 4 instead of 2). This is a property of the projection, not a decision; the k choice is
governed by §0.5/Phase 1.

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
- **Revision 3.3 adoption (done at STOP 1, required before Phase 3).** The §11.3 `trks-servers` and
  §11.4 `trks-watch` templates were updated to revision 3.3, reinstalled on both hosts
  (`trks-servers` sha256 `124316b5ce46d13129ff347b92356bb9904b56b025377f16917759f9d38ff22d`,
  `trks-watch` sha256 `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112`, identical on
  both hosts), `bash -n` clean, and `trks_watch` was **restarted** (new `watch started` lines 11:07:39Z
  TASL-7 / 11:08:05Z TASL-2). The new drill gate was exercised safely: with `$R/trks_drill.active`
  present, `trks-servers 1` printed `priority marker …/trks_drill.active` and exited **1** without
  starting a server; the marker was then removed and its absence verified.
- **No later phase was started.** In particular no S0.4 (`digits` prior fit), no tuning, no EVIDENCE.
- Open for the author: (i) the S0.1 STOP itself — re-run, adjust the server/probe setting, or halt;
  (ii) the rule question flagged in §3 (mixed server results / re-run before the STOP is final);
  (iii) the Phase 2 `KeyError` flag. The Phase 0 m10 flag (no defined denominator for the "> 2 % failed
  units" STOP in revision 3.2) is **resolved by runbook revision 3.3 §0.6**, which now defines it as
  `exhausted / (committed roots + committed leaves + exhausted)` over all shards and states that reports
  never re-read a STOP rule; no operator reading was adopted.

## 7. Files

- `docs/r1/reports/TRACKS_PHASE1_20261030.md` (this report)
- `results/r1/tracks/digits_mlp/{s01,s11}/`, `results/r1/tracks/tabular_mlp/{s01,s11}/`,
  `results/r1/tracks/openml_breast_w/s11/`
- `r1/tracks/ops/launch/tasl{2,7}_s01.sh`

## 8. Review record

**Round 1** (`docs/r1/reviews/TRACKS_OPS_PHASE1_REVIEW_20261030.md`, fresh independent reviewer):
**ACCEPTED** on the question put to it — whether the phase correctly reached STOP 1 and stopped — with
**6 MINOR** findings (P1–P6) and no BLOCKING or MAJOR:

| # | Severity | Finding | Disposition |
|---|---|---|---|
| P1 | MINOR (framing) | "k = 2 buys no LLM throughput" mixed the formula's two-stream model with the probe's four-client setting | **Fixed** — §4 now gives both readings (formula doubles the LLM term; the measured 4-client call rate is flat) and keeps the conclusion non-decisional |
| P2 | MINOR (provenance) | The report cited runbook 3.2 while the file at that path is now 3.3, whose §0.6 does define the failed-units denominator | **Fixed** — the header now states which revision governs and that the Phase 1 rule is unchanged; the m10 flag is recorded as resolved by 3.3 §0.6 (§6) |
| P3 | MINOR (evidence limit) | The S0.1 identity rates cannot be re-derived from raw responses because the pinned probe drops `contents` | **Recorded** — §2 states the limitation and what *was* checked |
| P4 | MINOR (provenance clarity) | The concurrent probe's `server_args` is two command lines joined by `" | "` | **Recorded** — §1 notes the pipe is a provenance separator, not a shell pipe |
| P5 | MINOR (record) | The Phase 0 review's operator note says m10 was fixed by adding a denominator sentence; the report now (correctly) flags it instead | **Fixed** — the Phase 0 report's m10 row and the Phase 0 review note were reconciled to "flagged, then resolved by runbook 3.3 §0.6" |
| P6 | MINOR (process record) | The §0.4 pre-start checks were not recorded for Phase 1 | **Fixed** — §1 now records them (markers absent, no compute apps, no GPU Track P session) |

The reviewer also confirmed independently: the copy-back hashes match the hosts, the probes' embedded
provenance (GGUF sha256, llama.cpp build, server command lines, order seeds, fixed per-prompt seed in the
request body) is complete, no phase after Phase 2 was started, both hosts remain at the pins with the
lease free and the watcher running, and the operator correctly flagged rather than re-read the STOP rules.
