# G.4 — T1 pilot on NEMO2 H200 (HTCondor): job design and the R1-BX-D14 recompute

**Status: PREPARED — NOT SUBMITTED, NOT AUTHORIZED.** ENGINEERING_ONLY. The pilot's proposals are measurements of
the T1 loop, not labels. Submission needs:
- the author-signed note `docs/r1/authorizations/g4_t1_pilot_<YYYYMMDD>.md` on published `main`;
- `--enable` and `G4_ENABLE_REAL=1`;
- P1–P4 recorded as PASS (§4).

Written by the Mac-desk agent (Claude), AI-assisted.

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

## 1. Shape (sweep-2-shaped)

Per node there are **3 campaign instances × W = 20 manager calls**, each campaign a root v2-diff campaign from the
node's baseline. That gives **60 proposals per node and 180 in all**. The W = 20 campaign length is the one the T1 label
campaigns use (G.5).

Seeds come from a pilot block, 4001–4099, for the training, split and manager seeds:
- instance 1 uses 4001/4001/4001;
- instance 2 uses 4002/4002/4002;
- instance 3 uses 4003/4003/4003.

The block is disjoint from G.1b (1001–3030), the B.2 audit seeds (7001–7010) and the exam seeds (9001+). Both the
paper validator and the harness pilot validator check this.

The third node is `mlgym_breakout_minatar`. `autoresearch_fixedtokens` has no passed isolated U2 yet (condition 7,
option A, pending on 20 Nov), and the spec records this as `third_node_reason`. When autoresearch's U2 passes, the
spec takes its pins: committed and deployed pins, census time and environment. The validator accepts either third
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
  - the node's data via its `setup_command`, with the deployed-pin check in the pilot runner;
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
- `out.tar`, which holds the pilot file, the campaign ledgers (manager views; no sealed test metric), the run records,
  `pilot_record.json`, `pilot_summary.json` and the setup and engine logs;
- `job_record.json`;
- `llama-server.log`;
- `SHA256SUMS`.

## 3. What the pilot measures (`pilot_g4.summarise`, per node)

- **Throughput:** proposals per campaign-hour, and LLM versus run seconds (median and total).
- **Diff liveness:** valid proposals per proposal, ran per valid, ok runs per proposal.
- **Shares:**
  - invalid, refused (scope), inert and duplicate proposals per proposal;
  - divergent and kept per ran proposal;
  - timeouts per ran proposal;
  - final infrastructure failures per proposal.
- **Prompt and completion lengths:** median, p95 and max of `prompt_tokens`, against the 32,768 context.
- **Divergence against the census:** the ratio to a census divergence rate, if one is given. This prepares the G.5
  STOP; see the G.5 draft for the reference rate.

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
- **Switch** (`g4_lib.py check|submit`). It refuses:
  - a note that is not on `origin/main`;
  - a field that differs from the staged spec;
  - a changed staged file or JDL;
  - a preview stage;
  - a submission without both keys.

  It writes a once-only marker per node.
- **Prerequisites in the note:**
  - P1: R1-T1-HOST-H200 host check;
  - P2: R1-TRACKG-G3-EARLY nodes;
  - P3: the G.1b first node (`mlab_ogbn_arxiv`) ran clean on H200, which proves the image, environment, data,
    cgroup and gate path the pilot shares;
  - P4: this unit reviewed.

## 5. R1-BX-D14 recompute (`g4_lib.py dates`)

After the pilot, run `g4_lib.py dates --params g4_dates_params.json --summaries <three pilot_summary.json>
--today <date>`. The calculation:
- takes the median LLM seconds per call and the executed share (ran-of-valid × valid-of-proposals) from the pilot;
- projects G.5 per T1 node: the proposals needed for about 150 audited (executed) proposals, the campaign time (LLM
  plus runs), and the audits at K seeds × census run time;
- turns that into labels-done, B.7, D.3 and manuscript dates, from the H200 slots and the stated spans.

**Pre-pilot illustration only** (the pilot medians replaced by the fallbacks LLM = 60 s and executed share = 0.6):

| K | G.5 GPU-h | Labels done | B.7 | D.3 | Manuscript |
|---|---|---|---|---|---|
| 6 (R1-BX-PROPOSED-CONFIRM D3, if its check passes) | 86 | 29 Nov | 2 Dec | 28 Dec | 4 Jan |
| 10 (if the K check fails) | 121 | 30 Nov | 3 Dec | 29 Dec | 5 Jan |

The illustration assumes:
- 4 concurrent H200 slots;
- 1 queue day;
- 1 G.1b day;
- 5 prerequisite days (G.4 run and reading, the G.5 signature, the K check);
- 3 analysis days to B.7;
- the R1-BX-D14 target spans B.7 → D.3 (26 days) and D.3 → manuscript (7 days).

Against the targets (B.7 ≈ 8 Dec, D.3 ≈ 3 Jan, manuscript 10 Jan) this leaves about 6 days of slack, but every
input except the census run times is an assumption. **The binding numbers are the ones recomputed from the pilot**,
and the recompute will be reported to the author with the pilot results.

## 6. Needs a cluster test

Everything in G.1b plan §6 applies: isolation inside the container, the v2 VERSIONS sha256, egress for wheels and
data, data bytes, JAX on H200. In addition:
1. **`llama-server` in the v2 image:** its sha256 and the build line (`0.7.0-dev (build 11669, commit 620d2225c)`).
   The sweep-2 pins are for the v1 image.
2. **GGUF egress** from the H200 job to Hugging Face (about 19.6 GB per job; S2-C4 measured 75–82 s on NEMO2).
3. **The server and the isolated runs sharing one H200.** The server holds about 20 GB; each run gets the GPU through
   its UUID. That leaves enough memory headroom, but the time per run while the server is idle is not yet measured.

## 7. STOPs

The job STOPs on everything G.1b STOPs on (image, host, environment, data, cgroup, gate), and also on:
- the GGUF sha256 or size;
- the `llama-server` build or offload;
- a transport failure;
- `stop_unisolated` or `stop_integrity`;
- `baseline_failed`;
- zero diff liveness;
- the deadline.

There is no retry or deletion, and outputs are always transferred.
