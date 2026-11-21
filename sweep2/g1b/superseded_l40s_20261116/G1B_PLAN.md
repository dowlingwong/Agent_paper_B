# G.1b — T1 GPU-node noise floor on NEMO2 L40S (HTCondor): prepared job specification

**Status: PREPARED — NOT RUN, NOT SUBMITTED, NOT AUTHORIZED TO RUN.** This document and the files beside it are a
reviewable design/spec/JDL/test set for the G.1b T1 noise-floor job. No job was submitted, no GPU was used, no
labels were read, no server was started and nothing was pushed to `main`. The job refuses to run until the G.0
census names the candidate nodes and fills every placeholder (see §2 and §12).

**Branch:** `g1b-noise-20261116` (worktree `.claude-worktrees/g1b-noise-20261116`), based on `origin/main`
`9ae6d87783f53f9da27200869085c9ed0e7697e2`. Nothing here depends on files that are not on that base: the reviewed
S2-C2 pattern lives on `sweep2-main-20261116` (not yet on `main`), so the wrapper/renderer are standalone ports of it,
not imports of unpushed code.

## 1. Authority and scope

| Source | Commit / location | What it fixes here |
|---|---|---|
| `R1-TRACKG-G1B-HOST` | `author-decisions-20261116` @ `4da73306` | Track G keeps the **G.0 census on Ada** (R1-ADA-CENSUS); the **G.1b T1 GPU-node noise floor moves to NEMO2 L40S (HTCondor)**, same GPU model as the T1 labels (R1-SWEEP-HOST-HTC, R1-BX-D5); amends the G.1b part of R1-ADA-CENSUS |
| `R1-BX-D5` | PLAN | label runs use a **fixed step or token budget** (not wall clock); **one GPU model per table**; label runs 1–2 min, closed-loop about 5 min |
| `R1-BX-REVISIONS (e)` | PLAN | per candidate task the server agent records run time at the fixed budget **on each GPU model**, VRAM, determinism, a 10-seed noise floor on 3–5 representative edits, the D21 verdict, D28 liveness |
| `R1-BX-REVISIONS (f)` | PLAN | cost model: "about 40 GPU-h per T1 node at 2-minute runs", of which "noise floor about 2" |
| `R1-ADA-CENSUS`, `R1-ADA-OVERFLOW` | PLAN | Ada/`zhixu` is the census host; resumable units; co-tenancy rule (G.1b no longer runs there) |
| `D21 rule (22 Oct)`, `D21 uniform application`, `D21 pool`, `D21 common measurement` | PLAN | 30 seeds per condition; ≥2 material edits (resolved, \|Δ̂_J\| > 2 se, \|Δ̂_J\| ≥ 0.002); mean plug-in P(wrong) ≥ 0.10; σ_joint > 0; seed count fixed at 30; library versions in every manifest; rule applied to every node, no exception after results |
| `R1-SWEEP2-SETTINGS` (1) and (5) | `author-decisions-20261116` @ `4da73306` | shared server setting: **context 32,768** with the exam flags; **a projection above 60 GPU-h or 48 h wall is an author STOP** |
| `R1-SWEEP-HOST-HTC` | `author-sweephost-20261116` @ `4651469a` | sweeps run as HTCondor jobs; LLM label runs only on NEMO2 L40S; job requirements pin the GPU and CPU models; one host type per table |
| Work plan `prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` | `docs/runbooks-16nov` @ `b3289232` | unit pattern and STOP list; this unit follows the later-sweep pattern (S2-C8) adapted to a measurement unit |
| Reviewed S2-C2 wrapper + S2-C4 measured layout | `sweep2-main-20261116` @ `acae9fde`, `docs/r1/reports/sweep2_20261116/S2_C4_RESULTS_20261116.md` | container universe, v1 gpu digest, L40S/CPU-class requirements, `+RemoteJob`, transfer outputs as tars; measured memory/disk/wall layout |

**What this unit is.** The authoritative 30-seed D21 measurement of training/split/joint noise on each G.0-named T1
candidate node, executed on the GPU model that will also run the T1 label table (NEMO2 L40S). Its output is the
per-node σ̂ (σ_joint) and the D21 verdict that a later T1 label table would use, together with the `vary` split term.

**What this unit is not.**

- It is not the G.0 census. The census stays on Ada and is the only source of the candidate node list.
- It reads no labels, no C3 data, no sweep-2 table and no B.2 audit. Nothing downstream may read it as labels; the
  D8 analysis lock is untouched.
- It does not run the proposer. The pick GGUF and the 32,768-context server setting are carried as shared pins of the
  G.1b family (this noise floor + the later D28 liveness sub-unit), but this chunk makes **no LLM call** and downloads
  **no 19.6 GB GGUF** (§5).
- It is ENGINEERING_ONLY. Using σ̂ in a label table needs the separate T1 label authorization and the C3/D8 rules;
  the noise floor is a measurement, not a label table and not evidence.

## 2. The G.0 dependency: the candidate node list does not exist yet

The candidate list is **not known until the experiment agent's G.0 census on Ada names the nodes**. The spec
therefore carries a **validated placeholder list** (`sweep2/g1b/g1b_spec.template.json`: eight
`G0_PENDING_NODE_01…08` slots with placeholder run times, metrics, edit sets and runner) and the job must **refuse to
run with placeholders**. The runtime validator enforces, fail-closed:

1. `g0_census.status` must be `complete` — otherwise STOP "G.0 census incomplete";
2. `g0_census.nodes` must be non-empty (an empty node list is refused as G.0-empty), unique, valid harness node ids,
   and must contain **no placeholder token** (`G0_PENDING…`, `PENDING…`, `PLACEHOLDER…`, `TBD…`, `TODO…`, `FILL…`,
   `<…>`);
3. `g0_census.report_path` must be the committed census report under `docs/r1/reports/` with a real sha256 (an
   all-zero sha256 is refused);
4. `plan.candidate_nodes` must equal the census node set exactly — a node may be neither added nor dropped silently
   (D21 uniform application);
5. every candidate must have a real `run_seconds` (1…300 s), metric, direction, request layout ≥ the measured floor,
   exactly **five** declared edits, and a runner module + sha256; all placeholders are refused.

The G.0 census must therefore deliver, per candidate: the node id, the fixed-budget run time **on L40S** (or a
declared L40S timing probe, §7.4), the metric name and direction, the five declared edits with their patch sha256,
and the request memory/disk from the measured peak. The eight placeholder slots are illustrative; if G.0 names six
nodes, the operator deletes two entries before filling the rest — the validator accepts any census-conformant count.

## 3. Protocol

### 3.1 Runs per node

One configuration set per node: `c0` (the node's baseline configuration) plus the **standard E1 edit set of five
declared edits** `c1…c5` (D21; five per node, as in the 22 Oct common measurement). Each configuration runs the
three seed conditions plus two default runs:

| condition | seeds | role |
|---|---|---|
| `train` | 1001–1030 (30) | training seed varies, split seed at the node default |
| `split` | 2001–2030 (30) | split seed varies, training seed at the node default |
| `joint` | 3001–3030 (30) | both vary together (paired d_s = m(ck,s) − m(c0,s)) |
| `default`, `default_repeat` | node defaults | fixed-seed **determinism** check (same config twice) |

**Runs per node = 6 configurations × (30 + 30 + 30 + 2) = 552.** The counts are exact coverage requirements: the
offline summariser refuses a run directory with a missing, duplicated or extra `(node, config, condition, seeds)` row.

### 3.2 Split policy and seeds

`"vary"` split is fixed by the authority/D21 and validated (`plan.split_policy == "vary"`). Seed blocks are the E1/D21
convention (train 1001–1030, split 2001–2030, joint 3001–3030), pinned in `measurement.seed_bases`; they are disjoint
from the B.2 audit seeds 7001–7010 and the exam seeds 9001+. **The seed count is fixed at 30 for every node** — the
validator refuses 10 or 29 or 31, and no per-node reduction is expressible.

### 3.3 Fixed budget, not wall clock

Every run uses the node's fixed step (or token) budget, the same budget as the T1 label runs (R1-BX-D5). The budget
is declared by the G.0 census/port and recorded per node in the chunk manifest. The per-run timeout is 3 × the
measured run time (Track G runbook G.1), bounded by `run_seconds ≤ 300`. Wall-clock time never selects or stops a
seed; only the chunk deadline does.

### 3.4 Determinism, engines and workers

`measurement.workers = 1`: **one GPU training run at a time**, so that the D21 fixed-seed determinism premise is not
perturbed by GPU oversubscription. The job runs the node's `default` chunk (two runs per configuration) first; if any
configuration's two metrics differ, the chunk STOPs with the evidence preserved and the node's D21 verdict is forced
to "does not qualify (determinism)" — σ̂ from a non-deterministic node is not published. Parallelising the GPU runs is
a different measurement and would need a reviewed determinism unit; it is refused here.

The T1 measurement engine is a reviewed module in the pinned paper commit (`node.runner.module` /
`runner.entrypoint`, sha256 pinned in the spec). Its required contract, mirroring `r1.noise.e1_noise_floor.run_one`:

```
run_one(*, node, config_id, edit, condition, train_seed, split_seed, node_root,
        artifact_dir, step_budget, timeout_seconds) -> {
            "node", "config", "condition", "train_seed", "split_seed",
            "metric" (float|None), "success" (bool), "failure", "edit_applied", "wall_seconds"}
```

`edit` is one of the node's five declared edit records (`edit_id`, `kind`, `patch_sha256`). The runner applies the
declared edit to a fresh per-run copy of the node (the harness `LocalWorker` path, `editable_paths` / `frozen_paths`
scope), runs at the fixed budget and parses the node's metric, reporting divergence as its own class. The engine is
**pending**: R1-BX-D4's code-diff support and the T1 ports must be reviewed and pinned before G.1b can execute; the
placeholder is refused until then. This is listed in §12.

### 3.5 One GPU model, one host class

NEMO2 `BwForCluster-Nemo2`, GPU **NVIDIA L40S**, CPU class `CpuFamily 6` / `CpuModelNumber 207` and model name
`INTEL(R) XEON(R) PLATINUM 8562Y+`, ≥ 16 CPUs (the S2-C4 measured class), one GPU per job. The JDL requirements encode
exactly this (no broad machine regexp, no `ProvidesEtpCeph`); the runtime re-checks the landed host CPU
(`/proc/cpuinfo` family/model/name), the GPU (name, ≥ 40 GiB, UUID, driver) and the CPU count, and STOPs off-class.
One GPU model per table: if a T1 label table ever ran on a different model, this σ̂ would not apply to it.

## 4. D21 qualification rule (executed exactly as written)

For each edit k and each node, over the 30 **paired joint** seeds:

```
d_s      = m(c_k, s) − m(c0, s)                    (same seed s, same node, joint condition)
Δ̂_J      = mean_s d_s
se       = sd(d_s; ddof=1) / sqrt(30)
resolved = |Δ̂_J| > 2·se        (if se = 0: Δ̂_J ≠ 0, the same inequality)
material = resolved and |Δ̂_J| ≥ 0.002             (raw metric units)
P(wrong) = Φ(−|Δ̂_J| / sd_joint)                   (plug-in error rate of the default keep rule)
```

Node verdict: **qualifies iff** (i) ≥ 2 material edits, (ii) mean plug-in P(wrong) over the material edits ≥ 0.10,
(iii) σ_joint > 0 (σ_joint = sd of the baseline's 30 joint metrics), and (iv) the seed count is exactly 30. The
seed-bootstrap probability of qualifying is reported as a diagnostic but is **not** part of the decision. There is no
post-hoc exception, no threshold change and no node substitution after the results are seen (D21 uniform application).

The rule is executed by the pinned `r1.noise.e1_report` code from the pinned paper commit, and the job verifies at
runtime that this code still carries the same constants (`MIN_EDITS = 2`, `QUALIFY_P = 0.10`, `MIN_EFFECT = 0.002`),
STOPping on drift. The offline summariser double-checks the pinned report's `qualifies_D21` against the local
`d21_qualify` implementation and STOPs if they disagree — two independent implementations of the same frozen rule.

The 10-seed/3–5-edit census floor of R1-BX-REVISIONS (e) is a **screening** measurement on Ada; it is not the D21
verdict. The D21 verdict comes only from this 30-seed L40S measurement on the candidate list the census names.

## 5. Pinned environment (one image, one harness, one library set)

| Item | Pin |
|---|---|
| Image | `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296` (v1 gpu image, tag `20261114-74820315`; S2-C1 freeze proposal / S2-C4 measured layout) |
| Image markers | `/opt/r1/VERSIONS.txt`: `image=r1-htc-gpu`, `build_utc=2026-11-14T23:10:24Z`, `llama_server_sha256=f8d35fd3…`, `llama_cpp_commit=620d2225…`; the job re-checks every marker and the llama-server binary hash |
| Python / libraries | `/opt/r1/envs/trackp/bin/python`; exact pinned versions for `python`, `numpy`, `scikit-learn`, `torch` in `env.libraries`, re-checked at run time and recorded in the manifest (D21: library versions in every measurement manifest) |
| Harness | `autoresearch_harness` at **the T1 label-table pin** (`harness.commit`, 40-hex, no placeholder; the EXAM pin `897d83c8…` is refused). The pin must come from the reviewed T1 port; noise floor and label table must share one harness commit (R1-BX-D5 one environment) — if the label table later changes pin, σ̂ must be re-measured |
| Paper code | `Agent_paper_B` at the commit that carries `sweep2/g1b/` and the T1 runner (`paper.commit`). The job clones it, and verifies that the transferred `g1b_lib.py` is byte-identical to `sweep2/g1b/g1b_lib.py` in that commit (code identity), and the runner module sha256 |
| Proposer/server (shared G.1b-family pin) | pick `gemma4_31b`, GGUF sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` (19,598,489,952 B, revision `619aca75…`, registry `docs/r1/reports/exam_phase2_20261026/gemma4_31b.json` sha256 `a04a0346…`); llama-server `0.7.0-dev (build 11669, commit 620d2225c)`; **context 32,768**, `-ngl 999`, `-np 1`, `--jinja`, `{"enable_thinking": false}`, q8_0 K/V cache, `cache_prompt: false`, `--no-webui` (R1-SWEEP2-SETTINGS (1)) |
| GGUF in this job | **not downloaded, no server started**: `model.use = "declared-only-no-download"`. The noise floor is training-run measurement only; carrying the pin keeps the whole G.1b family on one declared environment and avoids 19.6 GB egress per chunk (S2-C4 measured GGUF fetch 74.7–81.8 s and disclosed 314 GB egress for 16 sweep-2 chunks) |

## 6. How results are recorded

### 6.1 Per chunk (the container job)

The job writes only its HTCondor sandbox; HTCondor transfers `out.tar`, `job_record.json`, `SHA256SUMS`,
`g1b_run.log`. NEMO2 slots do not advertise `ProvidesEtpCeph`, so sealing to `/ceph` is an operator step (§6.3).

`job_record.json` (`g1b_job_record/1`) fields:

- run id, chunk (`chunk_id`, node, condition, seed range), label `ENGINEERING_ONLY`,
  `output_use = "ENGINEERING_ONLY G.1b noise-floor measurement; no labels read; not evidence; not a label table"`;
- spec sha256, plan sha256, projection (per node, total runs, total GPU-h, serial/per-node wall, chunks, max chunk
  wall), caps;
- image identity (digest, `/opt/r1/VERSIONS.txt` sha256, llama-server sha256, markers);
- **host** (hostname, fqdn, logical CPUs), **GPU** (name, UUID, driver, total memory, compute capability, count),
  **CPU** (model, family, model number, logical CPUs), **library versions** (python, numpy, scikit-learn, torch);
- paper commit + checkout identity, harness commit + checkout identity, wrapper sha256 (transfer == pinned tree),
  runner module/entrypoint/sha256;
- D21 rule constants actually found in the pinned `r1.noise.e1_report`;
- the chunk's run counts (expected/written/successful), per-run timeout, failures, determinism result, timings, rc
  and any STOP reason; start/finish UTC.

`out/manifest.json` (E1 `r1.e1_noise_floor/2` shape) carries label, run id, chunk, seed bases, seeds per condition,
split policy, node(s), edit ids, host/GPU/CPU/libraries/image/harness/paper/runner pins, projection and caps.
`out/runs.jsonl` is one E1-schema row per run; `out/edits.json` maps node → the five declared edits.

### 6.2 Assembly and the D21 verdict (offline, operator/Mac side)

Sealed chunks are assembled into `results/r1/g1b/<run_id>/` (merged `runs.jsonl` + `edits.json` + a manifest list +
all job records and SHA256SUMS). `python -m sweep2.g1b.g1b_lib summarise <run-dir> <chunk-spec>` then:

1. verifies **exact coverage** — 552 rows per node, every `(node, config, condition, seeds)` exactly once, no
   duplicates/extras (missing or extra rows STOP);
2. runs the fixed-seed determinism pairing (`default` vs `default_repeat` per configuration) and, on failure, forces
   a "does not qualify (determinism)" verdict without publishing σ̂;
3. applies the **pinned** `r1.noise.e1_report.summarise` to the run directory (rule executed, not re-implemented),
   checks its D21 constants, and double-checks each node's `qualifies_D21` against `g1b_lib.d21_qualify` (STOP on
   disagreement = rule drift);
4. writes `summary.json` (per node: σ_joint, σ_train, σ_split, resolved/material edit counts, mean P(wrong), the
   checks, `vary` split term, median run wall, determinism) and `tables.md` (the E1 report tables), plus the screening
   funnel (measured / qualified / failed determinism) required by R1-BX-D12.

### 6.3 Sealing

`python -m sweep2.g1b.g1b_lib seal <job-output> --run-id <id> --chunk-id <id>` verifies the transferred
`SHA256SUMS` with `sha256sum -c`, the job record identity (label, run/chunk, image digest, host, GPU), refuses
`.`/`..`/symlink path components and an existing target, and copies into
`/ceph/srv/dwong/paperb/g1b/<run_id>/<chunk_id>/` with its own `SHA256SUMS` and `SEAL_RECEIPT.json`. Nothing is
deleted or overwritten; failed attempts stay beside the successful one (the S2-C4 attempt convention).

## 7. Chunking, caps and the pre-declared STOP

### 7.1 Why chunking is required

Runs per node are 552, and the measured S2-C4 wall ceiling for one chunk is **10,776 s**. A chunk is therefore one
`(node, condition, contiguous seed part)` or the node's `default` (12-run) chunk. Seed parts are computed so that a
chunk fits the wall ceiling:

```
walltime_s = 900 (reserved: checks/staging/tars) + ceil(runs_in_chunk × run_seconds × 1.35)
seeds_per_part = floor( ((10776 − 900) / (run_seconds × 1.35)) / 6 )
```

The chunk plan is computed by the validator and the JDL renderer from the spec; a chunk spec that is not one of the
pre-declared chunks is refused, so chunk sizes cannot drift.

| run_seconds | chunks per node | max chunk wall (s) | notes |
|---|---|---|---|
| 30 | 4 | 8,190 | one part per condition |
| 60 | 7 | 10,620 | parts 20 + 10 |
| 90 | 10 | 10,377 | parts 13 + 13 + 4 |
| 120 | 10 | 10,620 | parts 10 + 10 + 10 |
| 300 (ceiling) | 25 | 10,620 | parts of 4 seeds (…+2) |

### 7.2 Pre-declared caps (author STOP)

- `max_total_gpu_hours = 60` and `max_chunk_wall_hours = 48` (R1-SWEEP2-SETTINGS (5)); `max_chunk_wall_seconds =
  10,776` from the S2-C4 layout. A spec may lower these values but **may not raise them**: a raise needs a new author
  row amending R1-SWEEP2-SETTINGS (5). The constants live in the reviewed code, not only in the spec.
- The projection is checked at validation **and again at run time**: if the projected whole-unit GPU-hours exceed 60,
  or a chunk's wall exceeds 10,776 s, or one node's chunk total exceeds 48 h, or the unit would need more than the
  pre-declared 8 concurrent L40S slots to finish inside 48 h, the job STOPs and reports the per-node projection.
- **GPU-hour definition:** one GPU per job and `workers = 1`, so one-slot wall hours equal GPU-hours; the total is
  `Σ_nodes 552 × run_seconds / 3600`. Because chunks are independent jobs, the wall clock can be shorter than the
  total when several jobs run concurrently; the pre-submit slot check (§7.3) keeps the projected wall under 48 h.

### 7.3 Pre-submit checks (operator, no submission here)

1. `condor_status` shows at least `ceil(total_gpu_hours / 48)` (and at most the declared 8) L40S slots on
   `BwForCluster-Nemo2` with the pinned CPU class; otherwise STOP for the author (the wall cap would be breached).
2. The spec validates against the pinned image/harness/paper/library/runner pins and the projection is inside the
   caps; the rendered JDL is the reviewed one.
3. The run is ENGINEERING_ONLY; an independent reviewer has accepted the unit and the author has recorded the cap
   decision (below).

### 7.4 `run_seconds` calibration (declared before measurement)

`run_seconds` comes from the G.0 census's fixed-budget run time **on L40S**. If the census (being on Ada) only has Ada
timings, the operator must obtain the L40S run time from a **declared timing probe** — the node's own `default` chunk
(12 runs) run first under this same layout at the ceiling `run_seconds = 300` — and use the median successful
`wall_seconds × 1.10` (rounded up, ≤ 300) as the condition-chunk `run_seconds`. This probe is declared before any
D21 measurement, is a timing measurement only (the metric values are the protocol's fixed-seed determinism rows, not
noise results), and is disclosed as such. No result-driven tuning is allowed: the D21 verdict data are the 30-seed
condition chunks only.

## 8. Pre-declared decision procedure

1. G.0 census (Ada) names the candidate nodes; the operator fills the spec (no placeholders). If the census cannot
   name a candidate's five declared edits, or names a node the port has not made measurable, that is an author STOP —
   the edit set is not silently reduced.
2. Compute the projection. If it exceeds 60 GPU-h or 48 h (or needs > 8 slots), STOP and report the per-node
   projection to the author. The author may (a) raise the cap with a new row, or (b) narrow the candidate list
   **before any measurement**; the 30-seed rule, the five edits and the D21 thresholds are not negotiable
   (D21 uniform application). The job will not run under a raised cap until the new row and the reviewed constant
   change exist.
3. Run the `default` chunks (determinism + `run_seconds` calibration). A non-deterministic configuration ⇒ the node
   does not qualify (determinism); STOP and preserve.
4. Run the condition chunks; assemble; apply the D21 rule with the pinned report code and the double-entry check.
5. Report the screening funnel and the per-node verdicts. Qualified nodes enter the noise-node pool from which a T1
   label table's σ̂ is taken; non-qualifying nodes stay engineering-only. No substitution, threshold change or
   post-hoc filtering after the results are seen.
6. The noise floor is ENGINEERING_ONLY. Any use of σ̂ in a label table is a separate authorized unit, and the D8
   analysis lock and the B.2 decoupling rules are unchanged.

## 9. Estimated GPU hours (pre-declared formula; measured run times pending)

`per-node GPU-h = 552 × run_seconds / 3600 = 0.15333 × run_seconds`. The projection cannot be finalised before G.0
measures the L40S run time; the sensitivity table below is what the validator computes once `run_seconds` is filled.

| run_seconds | per node | 4 candidates | 6 candidates | 8 candidates | 10 candidates |
|---|---|---|---|---|---|
| 30 | 4.60 | 18.4 | 27.6 | 36.8 | 46.0 |
| 60 | 9.20 | 36.8 | 55.2 | 73.6 | 92.0 |
| 90 | 13.80 | 55.2 | 82.8 | 110.4 | 138.0 |
| 120 | 18.40 | 73.6 | 110.4 | 147.2 | 184.0 |
| 300 (ceiling) | 46.00 | 184.0 | 276.0 | 368.0 | 460.0 |

Largest per-run time that stays inside the 60 GPU-h cap: **97.8 s for 4 candidates, 65.2 s for 6, 48.9 s for 8,
39.1 s for 10**.

**Cost finding (for the author).** R1-BX-REVISIONS (f) budgeted "about 2 GPU-h" for a T1 node's noise floor at
2-minute runs, from 10 training seeds × (5 edits + baseline) = 60 runs. The D21 protocol requires 30 seeds × three
conditions × (5 edits + baseline) + 2 defaults = 552 runs, i.e. **9.2× that line**: at 120 s/run it is 18.4 GPU-h per
node, so the eight-slot placeholder list projects **147.2 GPU-h** — about 2.5× the whole 60 GPU-h cap, and 46 % of the
tight 40 GPU-h/node T1 cost envelope in (f). With R1-BX-D5's 1–2 min label budget, the full 60 GPU-h / 48 h cap is
therefore **very likely to trigger the pre-declared author STOP** for more than about four candidates. This is a
decision for the author, not something this unit may work around: D21 fixes the seeds and the uniform application
forbids dropping nodes silently.

## 10. Files and tests

| File | Role |
|---|---|
| `sweep2/g1b/G1B_PLAN.md` | this document |
| `sweep2/g1b/g1b_spec.template.json` | placeholder spec with the validated placeholder node list (refused until G.0) |
| `sweep2/g1b/g1b_spec.schema.json` | JSON Schema (structure only; the runtime validator is authoritative) |
| `sweep2/g1b/g1b_lib.py` | spec validation (placeholders/G.0-empty/caps/chunk plan), D21 math, chunk run loop, job record + manifest, offline summarise, seal |
| `sweep2/g1b/g1b_job.sh` | container entry point (ENGINEERING_ONLY; pre-creates transferred outputs; tars on the way out) |
| `sweep2/g1b/render_jdl.py` | stages inputs and renders the fixed JDL (normal + `--layout-preview`) |
| `sweep2/g1b/g1b_dryrun/` | rendered layout-preview JDL, staged inputs, and the real `condor_submit -dry-run` ad from deepthought (no submission) |
| `r1/tests/htcondor/test_g1b.py` | 23 synthetic tests: template/placeholder refusal, D21 math (2 material edits, mean P(wrong) ≥ 0.10, σ_joint > 0, 30 seeds fixed), 60 GPU-h/48 h and chunk-wall STOPs, chunk plan/expansion, determinism pairing, JDL requirements, preview-not-submittable |

Run: `python -m pytest r1/tests/htcondor/test_g1b.py -q` (23 passed; no GPU/network/submission).

## 11. STOP / no-retry / no-deletion

Every failure is fail-closed and its evidence is preserved: placeholder or empty G.0 census, plan/census drift,
raised cap or projection over cap, chunk outside the pre-declared plan, wrong image/marker/llama hash, off-class
host/CPU/GPU, pinned-library mismatch, wrong harness/paper commit, wrapper or runner hash mismatch, D21 rule drift,
missing/duplicate/extra run, non-deterministic fixed seed, deadline with unfinished runs, seal SHA mismatch or an
existing sealed target. The transferred sandbox and the sealed attempt are kept, never deleted and never overwritten;
there is no ad-hoc retry (the protocol has no resume inside a chunk: a failed chunk is diagnose-then-resubmit as a new
attempt). No force push, never push `main`, no deletions.

## 12. What is prepared vs what still needs the G.0 census

**Prepared and reviewable now**

- the exact protocol, D21 math and pre-declared decision procedure (§3, §4, §8);
- the fail-closed spec template + JSON Schema + runtime validator (placeholder/empty-census/cap/chunk-plan refusal);
- the container wrapper, the reviewed-pattern JDL renderer/template, the chunking and the 60 GPU-h / 48 h STOP;
- the pinned environment (image digest + markers, harness/paper pin rules, 32,768-context server setting and pick
  GGUF, pinned libraries) and the manifest/recording/sealing design;
- the real `condor_submit -dry-run` ad (layout preview; no submission) and 23 synthetic tests.

**Needs the G.0 census (Ada) and the G.1 porting/pinning before any run**

1. **Node names** — the candidate T1 node list, with the census report path + sha256 (`docs/r1/reports/…`).
2. **Task assets / ports** — the T1 nodes' `NodeSpec`, data, fixed-budget wrapper, metric parser and the reviewed
   code-diff measurement runner module with its sha256 (the engine is a placeholder today; R1-BX-D4 diff support and
   the T1 port review are prerequisites).
3. **Per-node edit sets** — the five declared edits per node (patch assets + sha256), scope paths, frozen evaluator;
   fewer than five is an author STOP, not a reduced set.
4. **Per-node L40S run time** at the fixed budget (census, or the declared timing probe, §7.4), metric name and
   direction, request memory/disk from the measured peak (≥ the S2-C4 floors).
5. **Harness pin** — the reviewed T1 label-table harness commit (placeholder `PENDING_T1_HARNESS_PIN` today).
6. **Paper commit** — the pushed commit carrying `sweep2/g1b/` and the runner (template placeholder today; the job
   verifies the transferred wrapper against the pinned tree).
7. **Author cap decision** — if the projection exceeds 60 GPU-h / 48 h: raise the cap with a new row, or narrow the
   candidate list before measurement (§9 says this is likely). The job refuses to run before that decision.
8. **Independent review** of this unit and the cluster-agent submission hand-off; no submission happens in this unit.

## 13. Residual risks

1. **Cap STOP is likely** (§9): the D21 protocol costs 9.2× the (f) noise-floor line at 2-minute runs. The author
   will have to decide between a raised cap and a smaller candidate list before G.1b can run. No workaround is
   encoded.
2. **The T1 measurement runner does not exist yet.** The job's runner contract is declared and pinned by sha256, but
   it has not executed against a real T1 port. The first execution needs a stub-manager smoke run and a review of the
   node assets; a runner that returns non-E1 rows STOPs the chunk.
3. **Harness/paper pin coupling.** The noise floor must share the T1 label-table harness pin; if the label table later
   changes pin, the σ̂ must be re-measured. The paper pin must be pushed before it can be pinned in the spec.
4. **Run time uncertainty.** `run_seconds` is the biggest projection lever (per-node GPU-h is linear in it). If the
   L40S run time is higher than the G.0/Ada estimate, the cap STOP fires; the calibration procedure (§7.4) must run
   before the spec is filled.
5. **Diff determinism on GPU.** Two identical seeds are expected bit-identical (the E1 common measurement was
   bit-identical on CPU), but GPU kernels can be non-deterministic. The job runs one GPU training run at a time and
   fails the node rather than publishing σ̂ if the fixed-seed pair differs; the first real chunk is the test of this.
6. **Image dependency coverage.** The v1 gpu image was frozen for the LLM label stack; the T1 task dependencies
   (e.g. torchvision/gym/data libraries) may not be in it. If a port needs more, the author must approve a v2 image
   digest **before** the table (one digest per table; S2-C1 process), which changes the pinned environment and needs a
   re-review of this spec.
7. **Container scratch.** Per-run node copies live inside the job sandbox; the measured S2-C4 disk layout
   (42,439,718 kB request) is a floor here and is not yet measured for T1 task data — G.0 must record the peak disk.
8. **No labels/analysis risk declared:** the job reads no labels, so the R1-BX-D8 lock is untouched; the risk is only
   that someone later treats these ENGINEERING rows as labels, which the label and manifest state explicitly.

## 14. Review checklist

- Is the candidate-node refusal complete (empty census, placeholder ids, placeholder run times/edits/runner, plan
  drift) and does no path around it exist (including the preview JDL, which is staged with the placeholder spec and
  STOPs at validation)?
- Are the D21 constants and the 30-seed rule exactly the 22 Oct row, and is the double-entry check (pinned
  `e1_report` vs `d21_qualify`) sound?
- Is one GPU training run at a time the right reading of the D21 determinism premise, and is the determinism gate the
  right response to a mismatch?
- Are the chunk plan and the 60 GPU-h / 48 h / 8-slot STOPs the right pre-declaration, and is the §9 cost finding
  framed as an author decision rather than a silent workaround?
- Are the pinned environment and the manifest/recording fields enough for the D21 requirement (library versions,
  host/GPU/CPU, image/harness/paper/runner hashes), and is the no-GGUF-download decision correct for this chunk?
- Anything in the runner contract that cannot be satisfied by the planned T1 ports / R1-BX-D4 diff support?
