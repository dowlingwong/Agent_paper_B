# G.4 — T1 pilot on NEMO2 H200 (HTCondor): job design and the R1-BX-D14 recompute

**Status: PREPARED — NOT SUBMITTED, NOT AUTHORIZED.** ENGINEERING_ONLY. The pilot's proposals are measurements of
the T1 loop, not labels. Submission needs:
- the author-signed note `docs/r1/authorizations/g4_t1_pilot_<YYYYMMDD>.md` on published `main`;
- `--enable` and `G4_ENABLE_REAL=1`;
- P1–P5 recorded as PASS (§4).

Written by the Mac-desk agent (Claude), AI-assisted. Revision 2, after round 1 of the independent review
(B1, M1–M4, m1–m13, n1–n6).

**Authority (published `main` `94db94bb`).**

| Row | What it fixes here |
|---|---|
| R1-TRACKG-G3-EARLY | The pilot runs on three nodes: `mlab_cifar10`, `mlgym_fmnist`, and `autoresearch_fixedtokens`, or `mlgym_breakout_minatar` if autoresearch is not ready. G.4 starts without the U4 census report. |
| R1-T1-HOST-H200 | NEMO2 H200, the same GPU model as the G.1b noise floors and the G.5 labels. |
| R1-MAIN-PROPOSER, R1-EXAM-X7 | Main proposer `gemma4_31b` (bartowski Q4_K_M, sha256 `2959c1b0…`), with thinking off and the exam flags. |
| R1-SWEEP2-SETTINGS (1) | Server setting: context 32,768, `-ngl 999`, `-np 1`, `--jinja`, `{"enable_thinking":false}`, q8_0 K/V, `--no-webui`; `cache_prompt` false. |
| R1-BX-PROPOSED-CONFIRM D4 | Schema `manager_proposal/v2-diff`. If the pick fails diff liveness on a T1 node, that is a STOP and the author decides. |
| R1-BX-D14, R1-BX-PROPOSED-CONFIRM (B.7 timing) | The dates are recomputed after G.4. |
| R1-HARNESS-ISOLATION | The unisolated-run gate applies to every run. |
| D15, D26 | Manager temperature 0.2; every call carries a seed derived from (instance, trial index, repetition). |
| R1-EXAM-B1-TRUNCATION-INVALID | Completion cap on every call (4,096); a truncated reply is invalid. |

**Code.**
- Paper `sweep2/g4/`:
  - `g4_lib.py` (spec, job, stage/render, switch, dates)
  - `g4_job.sh`
  - `g4_spec.json`
  - `g4_dates_params.json`
  - tests in `r1/tests/htcondor/test_g4_h200.py`
- Harness `mac-trackg-t1-20261120`:
  - `src/autoresearch/trackg/pilot_g4.py`
  - the `record_gate` parameter of `campaign_v2_diff.run_v2_diff_campaign`
  - tests in `tests/trackg/test_trackg_pilot_g4.py` and one new test in `test_trackg_campaign_v2_diff.py`
  - `V2DiffManager` gains `temperature` (default 0.0, unchanged for earlier callers) and `include_history`
    (default True; False is the `none` memory mode)
- Harness pin `24935be3` (the same in `g1b_spec.json`; `g4_spec.json` must equal it, and the validator checks it).

## 1. Shape (sweep-2-shaped)

Per node there are **3 campaign instances × W = 20 manager calls**, each campaign a root v2-diff campaign from the
node's baseline. That gives **60 proposals per node and 180 in all**. The W = 20 campaign length is the one the T1 label
campaigns use (G.5).

**Manager settings, and how they differ from sweep 2.** Both the spec and the harness validator pin them:
- completion cap 4,096 tokens; context 32,768; `cache_prompt` false;
- temperature **0.2** (D15, as sweep 2). The v2-diff manager's own default was 0.0; the pilot passes 0.2 so that
  its shares are measured at the temperature G.5 is expected to use (author item G5-TEMP in the G.5 draft);
- seed per call `sha256("<manager seed>:<step>")[:8]`: deterministic in (instance, trial index), repetition 0 — the
  D26 rule, though not the T0 derivation function;
- memory mode **`history`**: the prompt shows the campaign's own last 12 steps (summary, decision, metric). This is
  not T0's `append_only_summary` (which keeps a summary file); the v2-diff manager has no such file. `none` shows no
  history. The pilot runs `history` only; whether T1 uses one mode or both (E4: "both memory modes") is author item
  G5-MEM in the G.5 draft. If the author wants both before the pilot, the spec splits the three instances.

Seeds come from a pilot block, 4001–4099, for the training, split and manager seeds:
- instance 1 uses 4001/4001/4001;
- instance 2 uses 4002/4002/4002;
- instance 3 uses 4003/4003/4003.

The block is disjoint from G.1b (1001–3030), the B.2 audit seeds (7001–7010) and the exam seeds (9001+). Both the
paper validator and the harness pilot validator check this.

The third node is `mlgym_breakout_minatar`. `autoresearch_fixedtokens` has no passed isolated U2 yet (condition 7,
option A, pending on 20 Nov), and the spec records this as `third_node_reason`. When autoresearch's U2 passes, the
spec takes its pins: committed pin, data-manifest sha256, census time and environment. The validator accepts either third
node; Breakout needs the stated reason.

## 2. What one job does (`g4_lib.py job`)

It reuses the reviewed steps instead of re-implementing them:
- **From G.1b's `g1b_lib`:**
  - v2 image identity (VERSIONS sha256) plus the `llama-server` sha256;
  - exactly one `NVIDIA H200`;
  - a non-root uid;
  - pinned clones of paper and harness; the staged `g4_lib.py`, `g1b_lib.py` and `s2_c2_lib.py` must equal the
    commit's copies;
  - the census environment rebuilt from the committed freeze;
  - the node's data via its `setup_command` (log kept on failure), with the committed-pin and data-manifest checks
    in the pilot runner (as G.1b, review B1);
  - the delegated cgroup.
- **From sweep-2's `s2_c2_lib`:**
  - the GGUF fetch with a streaming sha256 and size check;
  - the owned `llama-server` with the exam flags;
  - the `--version` build check against `0.7.0-dev (build 11669, commit 620d2225c)`;
  - the full-offload check.

The job then writes the pilot file and runs `python -m autoresearch.trackg.pilot_g4 run` from the node environment
and the pinned harness. For each instance, the harness:
- runs `run_v2_diff_campaign(enable_v2_diff=True, record_gate=check_effective)`;
- uses the census timeout (3 × census time; a timeout is the proposal's divergent failure) and no waiver;
- sends every manager request with `cache_prompt: false` and records the wall time of each call;
- STOPs on a gate refusal (ledger line `stop_unisolated`), a transport failure, an integrity error or a failed
  baseline.

After the campaigns, a STOP is raised when diff liveness is 0 on the node (no valid proposal ran), per D4. The
server is always killed. Outputs:
- `out.tar`, which holds the pilot file, the campaign ledgers (manager views; no sealed test metric), the run records
  (each `run_record.json` carries the node's `sealed` test block, as every Track G run record does; nothing in G.4
  reads it), `pilot_record.json`, `pilot_summary.json` and the setup and engine logs;
- `job_record.json`;
- `llama-server.log`;
- `SHA256SUMS`.

## 3. What the pilot measures (`pilot_g4.summarise`, per node)

- **Throughput:** proposals per campaign-hour, and LLM versus run seconds (median and total).
- **Diff liveness:** valid proposals per proposal, ran per valid, ok runs per proposal.
- **Shares:**
  - invalid, refused, inert and duplicate proposals per proposal. `refused` covers every diff refusal reason
    (`scope_violation`, `context_mismatch`, `ambiguous_hunk`, `malformed_diff`, `unsafe_path`, …);
    `refusal_reasons` counts them, since a D4 fallback decision depends on whether diffs fail on scope or on hunks;
  - divergent, kept and timeouts per ran proposal, **and** divergent and timeouts per proposal
    (`divergent_of_proposals`, `timeouts_of_proposals`): the G.5 divergence STOP family counts per proposal, so the
    G.5 draft uses the per-proposal rates;
  - ran per proposal, ok per valid, final infrastructure failures per proposal.
- **Prompt and completion lengths:** median, p95 and max of `prompt_tokens`; a `fit` block checks the largest prompt
  plus the completion cap against the 32,768 context, counts calls that reached the cap (truncated, hence invalid),
  and checks that every recorded request had `cache_prompt: false`. A context overflow returns an HTTP error and
  STOPs the campaign as `stop_transport`.
- A STOPped instance keeps its wall time, so the throughput is not inflated.

## 4. Projection, layout, switch

- **Job size.** Walltime per job = 3,600 s + ⌈(3 × 21 campaign steps) × (census run time + 60 s LLM estimate) × 1.5⌉.
  The 21 steps are 20 calls plus the baseline. The GPU-h estimate adds a 1,500 s startup (GGUF fetch, environment,
  data, server).

  | Node | Census run s | Steps | GPU-h (est.) | Walltime request |
  |---|---|---|---|---|
  | mlab_cifar10 | 12.297 | 63 | 1.68 | 10,433 s |
  | mlgym_fmnist | 34.376 | 63 | 2.07 | 12,519 s |
  | mlgym_breakout_minatar | 61.248 | 63 | 2.54 | 15,058 s |
  | **Total** | | 189 | **6.3** | |

- **Pilot cap.** 20 GPU-h is a declared **pilot cap (proposed)**; the note's `gpu_hours` confirms it. A spec may lower
  the cap, never raise it.
- **Layout.** `request_cpus 16`, `request_memory 65536` MB (the 19.6 GB GGUF plus the environment), `request_disk
  104857600` kB, `request_GPUs 1`, requirements `GPUs_DeviceName =?= "NVIDIA H200"`.
- **Cap.** The projection and the requested walltimes (10.6 slot-h) must both be within the cap.
- **Switch** (`g4_lib.py check|submit`). It refuses:
  - a note that is not on `origin/main`;
  - a field that differs from the staged spec (paper commit and spec sha256 included);
  - P3 without `g1b_first_receipt=<path> sha256=<hex>` naming the sealed G.1b first-node receipt, a receipt whose
    sha256 differs, or one with an infrastructure STOP; P4 without a citation of the review file under
    `docs/r1/reviews/`; P5 (the image row, G1B-IMAGE) not PASS;
  - a changed staged file or JDL, or a staged file that differs from the checkout;
  - a preview stage;
  - a submission without both keys, a second submission of a node, or a node outside the note;
  - a failed S2-C5 launch binding (`g1b_lib.verify_launch`).
- **Sealing.** `g4_lib.py seal <job output> --run-id … --node …` verifies the transferred sums and record, copies to
  `/ceph/srv/dwong/paperb/g4_h200/<run_id>/<node>/` (no overwrite) and writes a receipt that binds the record,
  `llama-server.log` and `g4_run.log` (both written after the sums).

  It writes a once-only marker per node.
- **Prerequisites in the note:**
  - P1: R1-T1-HOST-H200 host check;
  - P2: R1-TRACKG-G3-EARLY nodes;
  - P3: the G.1b first node (`mlab_ogbn_arxiv`) ran on H200 without an infrastructure STOP, which proves the
    image, environment, data, cgroup and gate path the pilot shares; the note names its sealed receipt
    (`g1b_first_receipt=<path> sha256=<hex>`) and `check` verifies it;
  - P4: this unit reviewed, citing the review file under `docs/r1/reviews/`;
  - P5: the author row authorizing image v2 for the T1 table (G1B-IMAGE, G.1b plan §2b; one digest for G.1b,
    G.4 and G.5).

## 5. R1-BX-D14 recompute (`g4_lib.py dates`)

After the pilot: `g4_lib.py dates --params g4_dates_params.json --spec <staged g4_spec.json> --sealed <three sealed
node directories> --today <date>`. The recompute:
- reads each pilot summary only from a sealed directory, after checking its receipt, `SHA256SUMS`, run id, spec
  sha256, harness commit, image, H200 and that the job did not STOP; it refuses a summary with a pilot STOP or a
  stop line, with other than 60 proposals, with a missing LLM or run median, of a node outside the pilot, or given
  twice;
- models **the G.5 table as the G.5 draft defines it** (`g5_node`): 12 instances × W = 20 (manager calls; or worker
  runs with an LLM-call cap, G5-W), campaigns + audits of the evaluated non-inert, non-duplicate proposals and their
  parent incumbents (12 baselines + keeps) at K seeds + 1,500 s per job (2 campaign waves + audit chunks under the
  walltime);
- uses, for each **pilot node**, its measured H200 campaign seconds per manager call (`campaign_wall_total /
  proposals`, which includes the LLM, the runs, reruns, timeouts and the baselines), its run median, ran share and
  keep share; for the **other nodes**, the census run time × the median measured H200/census run-time ratio of the
  pilot nodes, the median LLM seconds and the median shares (the output states the ratio);
- computes K = 10 and K = 6; **K = 10 binds** until the K-check row exists (`k_check_passed`);
- turns the binding total into labels-done and B.7 dates from the H200 slots and the stated spans; D.3 and the
  manuscript are B.7 shifted by the R1-BX-D14 target spans (not recomputed separately); it reports the slack per
  milestone, the G.5 total against the G.5 cap (`g5_cap_gpu_hours`, 220 as proposed in the G.5 draft) and `today`.

**Pre-pilot illustration only** (`--today 2026-11-21`; fallbacks: LLM 60 s, ran share 0.6, keep share 0.2, census run
times, × 1.25 inflation on runs and audits):

| K | G.5 GPU-h | Labels done | B.7 | D.3 | Manuscript | Slack |
|---|---|---|---|---|---|---|
| 10 (binding until the K-check row) | 179.6 | 30 Nov | 3 Dec | 29 Dec | 5 Jan | 5 days |
| 6 (only after the K-check PASS row) | 124.1 | 30 Nov | 3 Dec | 29 Dec | 5 Jan | 5 days |

The illustration assumes 4 concurrent H200 slots, 1 queue day, 1 G.1b day, 5 prerequisite days (G.4 run and
reading, the G.5 signature, the K check) and 3 analysis days to B.7. **The binding numbers are the ones recomputed
from the sealed pilot**, reported to the author with the pilot results.

## 6. Needs a cluster test

Everything in G.1b plan §6 applies (items 1–12): isolation inside the container, the v2 VERSIONS sha256, egress for
wheels and data, data bytes, JAX on H200, GitHub egress and pushed commits (the job clones the harness at
`24935be3`, which must be pushed; the launch commit must also descend from the current `main`, which has moved
past `94db94bb`), the exact device name, scratch and memory, the GPU assignment variables, CPU
affinity and walltime enforcement. In addition:
1. **`llama-server` in the v2 image:** its sha256 and the build line (`0.7.0-dev (build 11669, commit 620d2225c)`).
   The sweep-2 pins are for the v1 image.
2. **GGUF egress** from the H200 job to Hugging Face (about 19.6 GB per job; S2-C4 measured 75–82 s on NEMO2).
3. **The server and the isolated runs sharing one H200.** The server holds about 20 GB; each run gets the GPU through
   its UUID. That leaves enough memory headroom, but the time per run while the server is idle is not yet measured.
4. **JAX next to the server:** `mlgym_breakout_minatar` preallocates 75 % of GPU memory by default while
   llama-server holds about 20–25 GB; record `nvidia-smi` memory with both resident.
5. **Output sizes:** `llama-server.log` and `out.tar` (full working copies of about 63 runs per job) against
   `request_disk` and the transfer.
6. **Server load time** from scratch disk against `start_server`'s 300 s health deadline. If it never becomes healthy
   the process is reaped only at job end (inherited from the sweep-2 server code).
7. **`g4_job.sh` after HTCondor renames the executable:** it finds its libraries via `dirname "$0"`.
8. **`+RequestWalltime` enforcement** on NEMO2 (the slot-hour cap relies on it).

## 7. STOPs

The job STOPs on everything G.1b STOPs on (image, host, environment, data, cgroup, gate), and also on:
- the GGUF sha256 or size;
- the `llama-server` build or offload;
- a transport failure;
- `stop_unisolated` or `stop_integrity`;
- `baseline_failed`;
- zero diff liveness (`stop_class: node`; every other STOP is `infrastructure`);
- the deadline (the pilot engine's timeout is the time left to it; its log is kept).

Every STOP, spec validation and unexpected exceptions included, still writes `job_record.json` (with `stop_class`,
`walltime_s` and `cgroup_parent`), `out.tar` when `out/` exists, and `SHA256SUMS` (G.1b review N1). Submission uses the same S2-C5 launch binding as G.1b (`g1b_lib.verify_launch`, with
the PLAN rows R1-T1-HOST-H200 and R1-TRACKG-G3-EARLY), and the note binds `paper_commit` and `spec_sha256`.

There is no retry or deletion, and outputs are always transferred.
