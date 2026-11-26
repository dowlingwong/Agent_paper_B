# C3 label sweep 1 on deepthought — readiness report, 26/27 October 2026

AI-assisted (Claude, implementation agent on deepthought). **ENGINEERING_ONLY.** This report
proposes nothing and authorizes nothing. Phase 7 (B.1) starts only when
`docs/r1/authorizations/c3_sweep1_<date>.md` exists on `origin/main`, committed by the author, and
matches the pinned set below. **The agent never writes that note.**

## Headline: the machinery is ready; the node pool is not, and that is the author's decision

Phases 2, 4 and 5 are complete and pass. **Phase 6 does not:** 4 of the 8 D21 nodes fail D28 under
llama.cpp (`openml_breast_w`, `openml_sonar`, `openml_blood_transfusion`, `openml_wdbc` — all on
`keep_after_trial_1`; `openml_wdbc` also on a boundary `invalid_rate` of exactly 0.30). The
diagnosis is `docs/r1/reports/LIVENESS_LLAMACPP_20261026.md`: on those four nodes **no proposal in
20 trials produced a positive delta**, because `max_iter` edits are exactly inert on an already
converged model and `C` edits mostly hurt, with little or no headroom above a baseline `val_auc` of
0.99 on two of them. The manager itself is healthy — all eight nodes pass `active_novelty_fraction`,
161 of 161 trials parsed under the schema, and `digits_mlp`, the known 19 Oct risk, is now the
strongest node in the pool (10 keeps after trial 1).

Consequently **the pinned set below cannot be authorized as it stands**: it names the pool of 8, and
the runner's `min_live_nodes = 8` would STOP at its own liveness phase. The author decides first —
repair, substitute the reserve, run with fewer nodes, or re-read the criterion (options, with their
costs, are in the liveness report). Whatever is chosen changes the `nodes` line, `min_live_nodes`,
the sweep size and the runtime estimate below; a corrected config and readiness report would follow.
Everything else in the pinned set is measured and holds.

## The pinned set

| Pin | Value |
|---|---|
| Paper commit | **`origin/main` head at launch.** At the moment Phase 4 completed it was `fc3e0dab0e38256e8ce77d2040fb23138ceeb947`; it has since moved to `8ba81b68c70c58d40612c7a316e8d1669ff5ca33`. See the caveat below. |
| This branch | `dt-sweep1-20261026`, head `c409a2618c826585cc017f84517047fd552040c0` (plus the commit carrying this report) |
| Harness commit | **`897d83c8efa364ec2fdd37288241cc42e01d7274`**, branch `r1`; equals `r1/scripts/HARNESS_PIN_C3` on `main` |
| llama.cpp build line | **`version: 0.7.0-dev (build 1, commit 620d222)`**; `built with GNU 13.3.1 for Linux x86_64`; release tag `v0.7.0`, source commit `620d2225cc436ab0b001e3200e590e3b286ef9ab`; binary `/ceph/dwong/opt/llama.cpp/build-gcc13/bin/llama-server` |
| Build recipe | CUDA 11.8 (`/usr/local/cuda-11.8`, nvcc 11.8.89) for `-DCMAKE_CUDA_ARCHITECTURES=52`, GCC Toolset 13.3.1 for C/C++, `/usr/bin/g++` (GCC 8.5) as the CUDA host compiler, `-DCMAKE_CXX_FLAGS=-include iomanip`; runtime `LD_LIBRARY_PATH` with `/usr/local/cuda-11.8/lib64` and `/opt/rh/gcc-toolset-13/root/usr/lib64` |
| GGUF | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` @ revision `13fb94bfda8c8cf22497dc57b78f391a9acb426a`, file `qwen2.5-coder-7b-instruct-q4_k_m.gguf` (**Q4_K_M**, R1-PROPOSER-QUANT), 4,683,073,536 bytes, at `/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf` |
| GGUF sha256 | **`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`** (re-verified twice on 26 Oct: Phase 4 probe 53.7 s, Phase 6 run 18.6 s) |
| Config | `r1/scripts/configs/c3_sweep_deepthought.json`, sha256 **`85431afc775803de885a362dbfb1797323ae907a626a35f4bc871f2bae374d70`**; `--check-config` passes with no placeholders |
| Schema version | **`manager_proposal/v1`** (`proposal_schema` in the config; R1-SCHEMA, structure only: six string fields, `rationale` first, `additionalProperties: false`, `strict: true`) |
| Node list | the D21 pool of 8: `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_blood_transfusion` — **4 of which currently fail D28**; `openml_climate` remains the reserve, used only if the author substitutes it |
| Memory modes | `append_only_summary` (primary) and `none` (declared contrast) |
| Verify split | `"vary"` |
| Instances, W, seeds | **18 instances per node per memory mode**, **W = 20** worker runs per campaign, D26 per-request seeds derived as `manager_seed(campaign_id, budget_index, repetition, revision_attempt)`; transport retry 3 attempts |
| Audit seeds (Phase 8) | K = 10: **7001–7005 label, 7006–7010 evaluation**, never mixed |
| GPU plan | **One manager per TITAN, and sweep 1 is one batch on one TITAN:** `gpu_uuid = GPU-2516f262-6a75-eee3-26ee-b2e8d908c07d` (index 1), port 18083, `-ngl 999 -c 8192 -np 1`, `footprint_mib` **5253**, co-tenancy margin 5253 + 2048 = 7,301 MiB. See the GPU-plan note below. |
| Workers | 16 of 40 CPUs |
| Watchdog / resume | watchdog on (poll 5 s, health timeout 10 s, 3 unresponsive checks, 3 model checks, **max 3** restarts); resume on, **max 5** restarts; `min_live_nodes` 8; `max_parse_failure_rate` 0.20; `max_collect_sessions` 12 |
| Paper A check | "not applicable" on this host (`paper_a_status.py --not-applicable`), which refuses on `ucrtasl` |
| Host | `deepthought` (`deepthought.etp.kit.edu`), RHEL 8.10, 4 × GTX TITAN X 12 GB, compute 5.2, driver 525.147.05, 40 CPUs; `allowed_hosts = ["deepthought"]` |
| Environment | `/ceph/dwong/r1_prepare_20261025/venv`, CPython **3.13.15**, scikit-learn **1.8.0**, numpy **2.4.4**, pandas **3.0.3**, scipy **1.17.1**; harness lock sha256 `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090` |

## Estimated runtime (measured, not guessed)

From the Phase 6 run: 161 LLM calls, **mean latency 7.46 s** (median 7.02, min 4.09, max 14.97) at a
mean prompt of **827 tokens** (max 1,232) and mean completion of 102 tokens; worker runs averaged
2.47 s per trial.

The server has one slot (`-np 1`), so LLM calls serialise and the sweep is inference-bound; worker
runs on the other 16 cores overlap other roots' waiting.

| Quantity | Value |
|---|---|
| Sweep size, pool of 8 | 8 nodes × 18 instances × 2 memory modes × W = 20 = **5,760 proposals** |
| Inference at the measured mean | 5,760 × 7.46 s ≈ **11.9 h** |
| With longer memory-on prompts at W = 20 | prompts grow beyond the W = 10 measurement (827 → ~1.1 k tokens on the memory-on half); ≈ **13 h** |
| Plus liveness, preconditions, archives, commits, co-tenancy contention | **≈ 14–20 h wall on one TITAN** |
| If the pool were the 4 currently passing nodes | 2,880 proposals, ≈ **7–10 h** |
| Phase 8 audits (CPU, K = 10) | from the Phase 6 mix, roughly 55–65 % of proposals are neither inert nor duplicates → ≈ 3.2–3.7 k eligible × 10 seeds ≈ 32–37 k worker runs × ≈ 2.5 s ≈ **22–26 CPU-hours**, i.e. ≈ **2–3 h wall on 16 workers**. Wider uncertainty than the sweep estimate: the eligible fraction is measured at W = 10 on 161 trials. |

Phase 1's independent projection was 11.70 h for ≈ 5,800 calls from a 7.26 s mean latency, which
agrees with the 11.9 h above.

## What has been verified on this host

| Phase | Result |
|---|---|
| Branches | `dt-sweep1-20261026` from `origin/main`, six 25 Oct doc commits cherry-picked (report blobs byte-identical), pushed; `dt-sweep1-20261025` untouched; harness `r1` fast-forwarded to `897d83c` and verified |
| PLAN §10 | R1-DT-RESTART, R1-DT-TESTGATE, R1-DT-SCRATCH, R1-DT-PIN recorded in the author's terms |
| Phase 2 | nine of nine data caches `ok` (climate included); harness suite **454 passed / 8 failed / 1 collection error** = the accepted 26 Oct baseline; paper suite at baseline plus the accepted items; two environment defects found and fixed (`narwhals`, `PATH`) — `docs/r1/reports/DT_PHASE2_RECHECK_20261026.md` |
| R1-DT-TESTGATE (a) | met: `retry` 93.1 s / **107.3 s**, `permanent` 44.2 / 48.0 s, `watchdog` **101.1 s**, `interrupt` **123.5 s**, all passing standalone at `--deadline 300`; only the hardcoded 75 s limit fails |
| R1-DT-TESTGATE (b) | **resolved in one attempt**: the interrupt scenario passes on both backends, archive assertion included; the 25 Oct failure is explained by pre-batch-B code (batch B handoff, deviation 5) |
| Phase 4 (A.6) | config completed from host measurements, schema on, `--check-config` passes, no placeholders |
| Phase 5 (A.8) | both host-smoke scenarios **pass** with the real `llama-server`, real GGUF and the schema on: server killed mid-request → watchdog recorded the loss, restarted, re-ran the affected roots whole, batch completed; runner killed mid-campaign → completed root kept byte for byte, interrupted root re-run whole — `docs/r1/reports/WATCHDOG_SMOKE_DT_20261026.md` |
| Full GPU offload | proven at every load and after every collection, by route (ii) against the pinned footprint; the server pid held **exactly 5253 MiB** on the card in every start measured (Phase 4 probe, both smoke scenarios, Phase 6) |
| R1-SCHEMA | the build enforces per-request `response_format: json_schema` (same prompt: prose without it, strict six-field JSON with it); **161 of 161** Phase 6 trials parsed, zero parse failures, schema recorded per trial, in the run manifest and in the sweep index |
| Phase 6 (A.7) | **4 of 8 nodes pass D28** — STOP for the author; `docs/r1/reports/LIVENESS_LLAMACPP_20261026.md` |
| Disk and quota | `/ceph` 303 TiB free (floor 50 GiB); Ceph file count 275,960 of 500,000 = **45 % headroom** (floor 10 %); scratch on local disk per R1-DT-SCRATCH, `/` 119 GiB free |

## Four things the author should decide or know before authorizing

1. **The node pool (blocking).** See the headline and the liveness report. Nothing else can be
   settled until this is.
2. **The paper pin cannot be a frozen commit as written.** The runner's `preconditions` phase refuses
   to launch unless the paper checkout is *exactly* at the remote `main` head. `main` moved three
   times during this work (`7611338` → `fc3e0da` → `8ba81b6`). So the sweep-1 paper pin can only be
   "the `main` head at launch", and the authorization note must either name that commit (written
   immediately before the launch) or say so explicitly. The coordinator must also merge this
   branch's config into `main` first: the launch reads the config from the batch's own fresh clone of
   `main`, not from this branch.
3. **"One manager per TITAN" has two readings.** The runner drives one dedicated `llama-server` on
   one card per batch; the config comment and the batch B handoff record a per-card split as open
   question 3, **not built**. Read as a placement rule — no card ever hosts two managers — sweep 1 is
   one batch on one TITAN, which is what is pinned here. Read as "use all four cards", it needs four
   batches, which produce four sweep indexes; `r1.c3.dataset build-sweep` does not accept those as
   one sweep (Phase 9 would refuse). If the author wants the ~4× speed-up, that is a code change and
   a PLAN row, not a config change.
4. **The host is not exclusive in practice.** Three to four other users ran on it throughout:
   ~12.4 of 40 cores, 6,377 MiB on TITAN index 0, and 1,170 MiB on *all four* TITANs. The selected
   card had 11,111 MiB free against a 7,301 MiB need, so there is room, but a co-tenant's job growing
   during a 14–20 h sweep would trip the runner's co-tenancy STOP. `workers` was set to 16 rather
   than the runbook's starting suggestion of 24 for the same reason. Also open from the batch B
   handoff: whether to pin a `footprint_mib` slightly below the measured 5253 for margin (it
   reproduced exactly on every start measured here, so no margin was needed).

## Launch procedure, when and if authorized

```bash
# 1. the config must be on main (coordinator merges this branch), then, in a clean clone at main:
#    (the launcher clones main itself; this checkout only provides the launcher and the config)
export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:/opt/rh/gcc-toolset-13/root/usr/lib64:$LD_LIBRARY_PATH
export R1_C3_BATCH_ROOT=<batch root>          # durable; the runner's own output location
export R1_C3_CONFIG=<paper>/r1/scripts/configs/c3_sweep_deepthought.json
export R1_GIT_NAME=... R1_GIT_EMAIL=... R1_COAUTHOR=...
export TMPDIR=/tmp/<local scratch>            # R1-DT-SCRATCH: never Ceph
bash r1/scripts/c3_label_sweep_launch.sh --prepare          # clones main + the pin, syncs the venv, runs both suites
bash r1/scripts/c3_label_sweep_launch.sh --start <batch>    # tmux session r1_c3_sweep
```

`--prepare` refuses unless `prepare.json` is clean. The five Track-P/sidecar tests that need `torch`
would have made it refuse on this host; they now skip where `torch` is absent (committed on this
branch), and the five desktop dry-run integration tests, including the two with the 75 s deadline,
skip inside a batch (`R1_DRYRUN_CHILD=1`). The accepted-failure list in `c3_prepare_check.py` was
**not** changed.

## Labels

Everything in this phase is ENGINEERING_ONLY. The Phase 5 smoke outputs and the Phase 6 liveness
campaigns are ENGINEERING_ONLY and are not labels. Sweep 1 (Phase 7) and its audits (Phase 8) are
the EVIDENCE runs and have not started. The 25 Oct climate noise floor remains PILOT. The climate
pilot raw records `E1_CLIMATE_DT_20261025_ATTEMPT02` are on the author's Mac, untracked, and were
neither regenerated nor re-run.
