# Unit (revision 2) — Track G G.0 U2 raw-cost census, node `autoresearch_fixedtokens` (17 Nov 2026)

**Status: proposal for fresh independent review; one node only.** Revision 2 answers the round-1 review
(`reviews/TRACKG_U2_RAWCOST_REVIEW_20261117.md`, sha `…`, NOT ACCEPTED: BLOCKING-1 unit granularity — one
unit per node; MAJORs env-not-created, memory cap unenforced, undefined pre-run footprint, whole-smoke
raw-cost attribution, House-Prices path). Scope: **exactly `autoresearch_fixedtokens`**; each of the other
seven nodes runs under its **own** reviewed unit with the same per-node procedure; U4 compiles the rows.
Authority: `R1-TRACKG-G0-GO` (main **`50176481`**), `R1-TRACKG-PORT-OWNER`, `R1-TRACKG-LICENCES`,
`R1-TRACKG-PORT-DECISIONS` (main `50176481`), `R1-TRACKG-G1B-HOST`. ENGINEERING_ONLY; no noise
floor/D21/D28 (G.1b on L40S), no T1 label/sweep, no evidence.

## 1. Deployment / environment (torch env now created; fix MAJOR-1)

- Harness worktree `harness_ar` = `mac-trackg-port-ar-20261117b` @ **`08d065077d40087114452697d5d596e66a0578be`**
  (base `717ad835`, only adds nodes/configs/tests; clean); paper `main` `50176481` has the kit report/review
  (`TRACKG_U3_PORT_AUTORESEARCH_20261117.md`, blob/per the main commit `0ea061d1`).
- Ada Python **3.12.16** via uv; torch env `envs/torch312` created from the union of the suite requirements
  with the CUDA 12.4 build of torch 2.6.0 (+pytest, PyYAML): recorded versions `torch 2.6.0+cu124`,
  `numpy 2.5.4`, `transformers 4.49.0`, `datasets 5.0.1`, `sklearn 1.9.1`, `pandas 3.1.1`,
  `tiktoken 0.14.0`, `pyarrow 26.0.1`; `torch.cuda.is_available() == True`, 8 devices; the `uv pip freeze`
  sha256, interpreter path/version, driver 545.23.08 and the CUDA 12.x minor-version-compatibility note are
  recorded in the result. (The JAX env is only needed for the Breakout node's own unit; not this one.)
- Static test: from `harness_ar`, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
  envs/torch312/bin/python -m pytest tests/trackg/test_port_autoresearch.py -k "not smoke"`; record the
  result. (Each worktree has only its own suite test file.)
- Data: `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repo); from
  `harness_ar/nodes/autoresearch_fixedtokens`, `envs/torch312/bin/python prepare_data.py --out
  "$AR_TRACKG_DATA_ROOT/autoresearch_fixedtokens"` (the node's setup_command with that interpreter);
  record the setup log, `data_manifest.json` sha256 and data sizes, and `du`/`df` before/after.

## 2. Per-node procedure (this node only)

1. **Paper-A-first + co-tenancy:** re-run the U0 three-check gate immediately before launch (newest
   `results/paper_a/replay_panel_v4/live_*` == configured run dir; self-excluded `pgrep` empty; status
   `clear_*`, key false, `unidentified_apps: 0`); capture JSON path/sha/UTC. Choose a GPU with **≥24 GiB
   free** (run-1 floor, since no measured footprint exists yet; for later units use measured peak + 2 GiB),
   record `nvidia-smi --query-gpu=uuid,index,memory.free,memory.used` immediately before launch; a full
   card → wait/re-check every 15 min or choose another free card; do not disturb others.
2. **Memory cap (fixed):** wrap the smoke in a real user cgroup cap:
   `systemd-run --user --scope -p MemoryMax=64G -p MemorySwapMax=0 -- bash -lc '… port_smoke_gpu …
   --memory-limit "systemd-run --user --scope -p MemoryMax=64G (whole unit)"'`; verify enforcement once
   (small overshoot probe) and record the command/result; if the cap cannot be enforced → STOP.
3. **Smoke/raw-cost:** from `harness_ar` with `PYTHONPATH=src` and the node's interpreter,
   `python -m tests.trackg.port_smoke_gpu --node autoresearch_fixedtokens --gpu-uuid GPU-… --cpus <list>
   --memory-limit "…" --runs-root <outside repo>/u2_autoresearch_fixedtokens_<UTC>
   --provisional-timeout <s>`. The smoke executes **7–9 full-budget runs** (baseline, refused frozen
   diff, broken diff, first edit, all 3–5 edits, repeat baseline) at seeds 8001/8001; require
   `CHECKLIST_E_PASSED autoresearch_fixedtokens` and the per-run JSON lines.
   - **Baseline time** = `elapsed_seconds_info_only` from `<runs-root>/runs_smoke/s000_baseline/run_record.json`
     (record path/run id; B1 is the timeout basis; B2 is a determinism check only, both values recorded).
   - **VRAM:** sample `nvidia-smi --query-compute-apps=pid,used_memory` at 1 s and filter to the baseline
     run's process tree (run-dir/`run_record.json` mtimes delimit the window); if attribution is not
     possible, record the whole-smoke maximum **labelled "max over all smoke runs / card total (upper
     bound, includes co-tenants)"** — never call it the baseline footprint.
   - **CPU/RAM:** `/usr/bin/time -v` on the smoke is whole-smoke aggregate (label it); an extra dedicated
     baseline run is allowed inside this one-node unit and its `/usr/bin/time -v` is the baseline CPU/RAM;
     record the sampler/commands/intervals and co-tenant baseline.
4. **Timeout:** first run is measuring; per R1-TRACKG-PORT-DECISIONS (4) node timeout = B1 runtime × 3.
   A timeout is recorded both as the harness outcome and manually reclassified as a **failed proposal /
   per-node STOP**; no retry. OOM/CPU fallback/non-passing checklist E/kit failure → per-node STOP.
5. **Preserve raw records** (`run_record.json`, `run.log` per run) under `<runs-root>`; never delete;
   record paths/sha256. An interrupted unit re-runs whole from a new `<runs-root>` (old moved aside).
6. **Record** `TRACKG_U2_AR_RESULT_20261117.md` (or the per-node row file): node/suite; env versions
   (`python -V`, freeze sha, torch/cuda, driver 545.23.08, CPU model, OS/kernel); kit/harness tips; static
   test result; gate capture; data provenance/manifest sha/df; GPU UUID/free-used before/after; memory cap;
   runs-root and per-run record paths/sha; B1/B2 times; baseline peak VRAM (or labelled upper bound);
   CPU/RAM; checklist-E result; timeout/reclassification; disk accounting (100 GB unit/total cap, measure
   before/after); one-node statement; no evidence/noise/D21/D28. No deletion.

## 3. STOPs (this node)

Kit static-test failure; env/freeze mismatch; data setup/manifest mismatch or egress/setup timeout (HF/Xet,
PyPI, OGB, Kaggle); Paper-A gate not clear; no card with ≥24 GiB free after re-checks; memory cap not
enforceable; OOM/CPU fallback/timeout; non-passing checklist E; any tracked-file change in the worktree
(untracked data links/`__pycache__` are recorded, not a STOP); any other user's process/files touched;
disk <50 GB or >100 GB unit use. Preserve and record; no retry; stop this node only.

## 4. Must not

No other node, no T1 label/sweep, no noise floor/D21/D28 on Ada, no kit code edits, no MLGym copy for House
Prices (that node's own unit will STOP pending Kaggle data), no other host, no deletion, no main/exam-x
push, nothing counted as evidence.

## 5. Result / U4

This unit yields the `autoresearch_fixedtokens` row only; U4 compiles it with the rows from the other seven
per-node units. Other nodes repeat this procedure under their own reviewed units; no cross-node
authorisation is claimed here.
