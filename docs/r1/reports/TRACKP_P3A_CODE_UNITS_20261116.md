# Track P P.3a attempt-2 — code units (A3-short delta and probes-only runner), 16 November 2026

**Status: implementation record for review. ENGINEERING_ONLY; AI-assisted.** No GPU job, no model, no experiment
and no host was run or touched; no push, no merge of `main`, no deletion. Two reviewed code commits plus this record
sit on branch `trackp-p3a-code-20261116` in worktree `.claude-worktrees/trackp-p3a-code-20261116`, based on
**`b9ad6f8f` (`origin/trackp-20261026`)**. The attempt-1 code path is preserved: without `--probes-only` the
supervisor's multi-base campaign is unchanged.

Inputs read (read-only): plan rev2 `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md`; accepted Unit A review
`docs/r1/reviews/TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md`; M13 order record
`docs/r1/reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md`; attempt-1 inventory
`docs/r1/reports/trackp_p3a_attempt1_inventory_20261116/`; pinned code at `b9ad6f8f`.

## 0. Commits and exact diff scope

| Commit | Subject | Files |
|---|---|---|
| `3833d93e` | `feat(r1): Track P P.3a A3-short execution flag (option 3)` | `r1/c3/train/exam_run.py` (+21/−8), `r1/scripts/trackp.py` (+16/−1), `r1/tests/test_trackp_p3a_a3_short.py` (new, 139 lines) |
| `7ae4d2ea` | `feat(r1): Track P P.3a probes-only runner/preflight/journal/budget unit` | `r1/scripts/trackp_p3a_guarded.py` (+772/−15), `r1/tests/test_trackp_p3a_probes_only.py` (new, 528 lines) |
| this record | docs | `docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md` |

Author/committer both `Dowling Wong <wangdowling@gmail.com>`. `git diff b9ad6f8f..HEAD --name-status`:

```
M	r1/c3/train/exam_run.py
M	r1/scripts/trackp.py
M	r1/scripts/trackp_p3a_guarded.py
A	r1/tests/test_trackp_p3a_a3_short.py
A	r1/tests/test_trackp_p3a_probes_only.py
A	docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md
```

No other file is touched: no W2-3/v3/v2/M13/order change, no config/rule/E0/data/harness change, no `main` merge,
no script outside `r1/`, no deletion of the pinned non-finite STOPs. Both code commits' `git show --stat` are the
three and two files above. **Reviewed commit shas: A3 delta `3833d93e`, probes-only runner `7ae4d2ea`.**

## 1. Commit 1 — A3-short execution delta (`R1-P3A-OOM-OPTION3`)

`exam_run.probes(model, run_dir, n=..., seed=..., counters=..., a3_short: bool = False)`. In the ``counters is not
None`` (A3 budget-v2) branch:

- `a3_short=True`: the descriptive block at the pin's `exam_run.py:290–295` (`E.a3_probe(tok, n=n,
  lengths=(0,)+E.A3_DESCRIPTIVE, …)` and `_a3_rps(…, f"descriptive_{L_}")`) is **not called**. Instead
  `out["A3_descriptive"] = {"skipped": "R1-P3A-OOM-OPTION3", "levels": list(E.A3_DESCRIPTIVE), "pass": None}`.
  The A3 budget-v2 rows (0/25/50/100 % at 1,024 tokens), `A3_errors`, A4, A5 and A1/A2 are unchanged.
- `a3_short=False`: byte-identical behaviour to `b9ad6f8f` (same calls, same `A3_descriptive`, same `pass: None`).
- `a3_short=True` with `counters=None` raises `ValueError` **before any probe runs**, so the v1 A3 0/2k/8k path can
  never be silently shortened.

`r1/scripts/trackp.py`: `--a3-short` is added **only to the `probes` subparser**; `cmd_probes` forwards
`a3_short=args.a3_short` to `X.probes`. The flag is refused (TrackPStop, rc 2) unless `--budget` is present and the
run is not `--tiny` (tiny never takes the budget-v2 counters); the refusal happens in `main` before any config/env/GPU
work and again in `cmd_probes` as defence in depth. No manifest field was added — the run-time record of the flag is
the attempt-2 runner's journal/sidecar (commit 2) and the child report's skipped marker.

Tests (`r1/tests/test_trackp_p3a_a3_short.py`, CPU, stubbed probes, no model/tokenizer/GPU):

- flag-on with counters never calls the descriptive `E.a3_probe`/`_a3_rps` (patched to fail if called) and produces
  exactly the skipped marker; the A3 budget-v2 path still ran;
- flag-off calls `E.a3_probe(lengths=(0,2000,8000))` and both descriptive `_a3_rps` keys as before;
- flag-on changes no other output key and no other value (`set` and value equality against flag-off);
- `probes(..., counters=None, a3_short=True)` is refused; CLI refuses `--a3-short` without `--budget`, refuses
  `--a3-short --budget --tiny`, and `--a3-short` is not accepted by the `e0` subparser;
- `cmd_probes` forwards the flag (True and False).

## 2. Commit 2 — probes-only runner / preflight / journal / budget (same file as the attempt-1 supervisor)

`r1/scripts/trackp_p3a_guarded.py` is extended, not replaced: `verify_pins`, `verify_live_pins`, `read_json_finite`,
`emit`, the watchdog (`start_watchdog`), `worker_parent_death_guard`, `stop_group`/`stop_group` safety and the
`run_base` multi-base path are preserved. `run_unit` gained keyword-only attempt-2 hooks
(`template_id`, `attempt1_input`, `projection_seconds`, `lease_mirror`, `sidecar_builder`); with none of them the
attempt-1 path emits the same journal events as before.

### 2.1 Args and mode contract (`parse_args`, `validate_probes_only_args`)

New args: `--probes-only`, `--base` (required, must be `qwen3.5-4b-base`), `--attempt1-root` (required),
`--a3-short` (required in this mode), `--authorization-amend-sha256` (required, must equal the reviewed
`cd867e95ddab0525827a48d68ea570743977bbf1b6ea819fefb98b3cf460f32d`), and the new root via `--root` (absolute, must
not exist, must be named `p3a_attempt2_<UTC>`). The attempt-1 root, or any path containing/nested in it, is refused;
the attempt-1 root name is refused. Supplying any probes-only flag without `--probes-only` is a STOP (the old
multi-base campaign cannot be silently switched), and probes-only never iterates `BASES` — it runs the two units in
§2.6 only.

### 2.2 Preflight (`verify_probes_only_pins`, fail-closed)

- paper: branch `trackp-20261026`, clean, and `b9ad6f8f` is an ancestor of HEAD (the A3-short commit is on top; the
  actual HEAD commit is recorded in `campaign_start.pins.paper`), harness `897d83c8` clean;
- `r1/c3/train/data/e0_v1.jsonl.gz` sha256 `4f4db29b…`; `r1/c3/rules/p3_rule_v2.yaml` sha256 `8c0ef908…`;
  `r1/scripts/configs/trackp_portal.json` identical to `607e85e:…`; venv freeze equal to
  `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt`; `registry.reverify` clean;
- host `TASL-7`, boot id + NVIDIA driver snapshot (`580.178.04` required), disk free ≥ 10 GiB;
- `flock ~/r1_locks/gpu0.lock` is free (taken and released in the check), empty GPU-compute census
  (`foreign_compute_processes`), no other experiment process (host `ps` census; own pid/ppid excluded), no
  `*.active` marker, installed marker helper `~/r1_locks/bin/trackp-evidence` sha256 `f457a04e…`, and the 4 Nov
  amendment sha gate (`--authorization-amend-sha256`, additionally re-hashed if the file is present in the checkout).
- The attempt-1 environment is set if absent and recorded: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`,
  `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `PYTHONUNBUFFERED=1`.

### 2.3 Marker (`evidence_marker`)

Uses the helper's actual interface only — `trackp-evidence begin p3a` before GPU work and `trackp-evidence end p3a`
in a `finally` on success or STOP. The job runs directly (`trackp.py` takes its own `flock`); `trackp-evidence run`
is deliberately never used (nested `flock`). `marker_begin`/`marker_end` journal events record the exact command,
rc, stdout/stderr and UTC. A failed begin is a STOP before any unit; a failed end is a STOP after the session.

### 2.4 Attempt-1 provenance (`build_attempt1_provenance`, `assert_attempt1_pins`, `attempt1_input`)

Read-only, fail-closed: `--attempt1-root` must contain `journal.jsonl` and `<root>/../gpu_lease_log.jsonl`; the
journal must start with `campaign_start` and contain exactly one `STOP` with a finite `gpu_seconds_total`. The
provenance block records root, journal sha256, lease-log sha256, paper commit/branch/dirty, the STOP
`gpu_seconds_total` and hours, `derived_prompt_version: trackp_prompt/v1`,
`derived_order: history_first`, the derived template ids per family, `recorded_at_run_time: false`,
`label: "derived"`, and the M13 derivation doc + sha256. The hashes and the 130745.3789889291 s STOP total are
pinned to the reviewed values. For each loaded `EVIDENCE/<base>/final/saved` directory: `saved/manifest.json["files"]`
must equal `EVIDENCE/<base>/final/manifest.json["model_files_sha256"]`, every recorded file is re-hashed from disk
(extra files refused), and the block records every relative path + sha256 + a composite hash (symlinks recorded, never
followed). This is the plan §1c.2 attempt-1 input binding that attempt 1's probes manifests (empty
`model_files_sha256`) lacked. Attempt 1 is never edited or re-labelled.

### 2.5 Template/version and per-unit sidecar (`template_block`, `make_sidecar_builder`)

`<unit>/runner_manifest.json`, schema `trackp_p3a_unit_manifest/v1`, is written by the runner after the child exits 0
and after the child `manifest.json`/`report.json` pass the finite-JSON re-read, before `unit_complete`:

- `attempt2_template`: `version` imported from `r1.c3.train.types.PROMPT_VERSION` (must be `trackp_prompt/v1`),
  `version_source: r1/c3/train/types.py:26`, `family`, declared `frame` (`kev_pointer_v1` / `qwen_bintoken_v1`),
  `order: history_first`, declared `field_order` (`state,proposal,question,options,decide` /
  `state,proposal,question,bins,belief,action`), `readout`, `encoder` (Kev commit + `kev/model.py` sha256 from the
  installed Kev dist-info; Qwen transformers version + tokenizer repo/revision from the manifest),
  `wrapper_config` (`kev_hybrid`/`pointer_temperature`/`released_temperature` or canonical
  `list_bins`/`bin_order`), and the composite `template_id`
  `trackp_prompt/v1/<frame>/history_first/<encoder id>` — exactly the M13 §3.2 block and ids §3.5.
- `attempt1_provenance` (§2.4), `attempt1_input` for this unit, `inputs.child_manifest_sha256`,
  `inputs.child_report_sha256`, `inputs.authorization_amend_sha256`, `cost.gpu_seconds`, `created_utc`.
- The per-unit template is recomputed from the child manifest and must equal the campaign-level declaration, which in
  turn must equal the M13 derived attempt-1 `template_id`; any drift (PROMPT_VERSION, Kev commit, transformers
  version, wrapper config, frame/order) is a STOP. The child's own `manifest.json`/`report.json` are never modified.
- `journal.jsonl` `campaign_start` records `serialisation_schema`, `templates` (both families),
  `attempt1_provenance`, `attempt1_inputs`, authorization, marker, environment, budget and argv. Every
  `unit_start`/`unit_complete` records `template_id` (unit_start also `attempt1_input`; unit_complete also
  `runner_manifest_sha256` and `gpu_seconds_unit`); `STOP` records `template_id` and the marker end.

### 2.6 Budget (`Attempt2Budget`) and the two-unit sequence

- `used = attempt-1 journal gpu_seconds_total (130745.3789889291 s = 36.318161 h) + time recorded in this run's own
  `gpu_lease_log.jsonl`*. The global lease log is still what the child writes and the watchdog tails; the runner
  mirrors the observed lease start/end into the new root's log. `require_available(projection)` refreshes and refuses
  a unit **before it starts** if `used + projection >= 45 h`; the 60-h P.3a cap is recorded and checked (it includes
  attempt 1; it is not extra time). Conservative per-unit projections: DRYRUN 600 s, EVIDENCE 1,800 s.
- Exactly two GPU commands, in this order, both `--a3-short` and loading attempt-1 `EVIDENCE/<base>/final/saved`:
  1. DRYRUN `kev-0.8b` probes, `--n-probe 8`;
  2. EVIDENCE `qwen3.5-4b-base` probes, `--n-probe 100`.
  No other base or unit, new directories only, no retry (an existing unit directory is a STOP).
- After each child report the runner asserts the changed path ran: `A3.protocol == "v2_budget"` and
  `A3_descriptive == {"skipped": "R1-P3A-OOM-OPTION3", "levels": [2000, 8000], "pass": null}` exactly. If the DRYRUN
  report does not show it, the campaign STOPs and the EVIDENCE unit never starts.
- Outputs are preserved; nothing is deleted or moved aside.

## 3. Exact test commands and results (local, CPU, no GPU/model)

Local environment (temporary venv, not the TASL-7 env): Python 3.13.4, pytest 9.2.0, numpy 2.5.5, scipy 1.18.1,
torch 2.15.0 (CPU/MPS build), PyYAML 6.0.3. No transformers/tokenizers, no pool model, no CUDA.

```
$ python -m py_compile r1/c3/train/exam_run.py r1/scripts/trackp.py r1/scripts/trackp_p3a_guarded.py \
      r1/tests/test_trackp_p3a_a3_short.py r1/tests/test_trackp_p3a_probes_only.py
py_compile OK (5 files)

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_a3_short.py -q
8 passed

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_probes_only.py -q
25 passed

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_guarded.py -q     # pre-existing suite
5 passed, 4 failed

$ PYTHONPATH=. pytest r1/tests/test_trackp_cli.py -q
9 skipped
```

**The 4 `test_trackp_p3a_guarded.py` failures are pre-existing and environmental, not caused by this work.** They
are the real-subprocess tests, which reach the pin's `worker_parent_death_guard` `preexec_fn`
(`ctypes.CDLL(None).prctl(PR_SET_PDEATHSIG)`); macOS has no `prctl`. Verified by running the same suite on an
unmodified `b9ad6f8f+3833d93e` baseline worktree: identical `5 passed, 4 failed`. The 5 CPU-only safety tests pass
on both. `test_trackp_cli.py` skips because the pool tokenizers are not in the local HF cache (no transformers).

**What could not run locally:** the real probes (they need the TASL-7 venv, the four-base pool tokenizers/model
files and a GPU), the DRYRUN/EVIDENCE children (stubbed in the tests), the live preflight/marker/lease/`nvidia-smi`
paths (they are TASL-7-only and were not exercised by design), and the tokenizer-dependent Track P CLI dry-run suite.
The parser/mode/budget/provenance/template/sequence logic is covered by the 33 new CPU tests; every changed file is
`py_compile` clean.

## 4. Fail-closed STOP list

A3-short delta: `a3_short` with `counters=None` (ValueError); CLI `--a3-short` without `--budget`; CLI
`--a3-short` with `--tiny`; `--a3-short` on any non-`probes` subcommand (argparse error).

Probes-only runner: missing/invalid `--probes-only` args; wrong `--base`; amendment-sha mismatch (and amendment file
hash mismatch if present); relative/existing/mis-named root; attempt-1 root reused or nested; non-`TASL-7` host;
paper branch/dirtiness/ancestor pin; harness pin/dirtiness; E0/rule/config/freeze/registry mismatch; driver/boot
mismatch; low disk; held lease; non-empty GPU census; another experiment process; another `*.active` marker; missing
or wrong marker helper; attempt-1 journal/lease-log missing, wrong sha256, no/duplicate STOP, non-finite or changed
GPU total; attempt-1 loaded directory missing/unrecorded/tampered/symlinked; family/frame/wrapper-config/PROMPT_VERSION/
Kev-encoder/transformers template drift; per-unit template disagreement with the campaign declaration; 45-h
projection crossing or 45-h/60-h reached; unit directory already existing (no retry); child failure rc≠0; missing or
incomplete lease record; label/boot mismatch; non-finite child report/manifest; DRYRUN report not showing the budget-v2
path / the skipped marker; failed marker begin or end; any unexpected unit/base in the sequence. Every STOP preserves
outputs and emits a STOP journal record; there is no bare `trackp.py probes` fallback.

## 5. What the reviewer must check

1. **A3 delta (`3833d93e`).** `git diff b9ad6f8f..3833d93e` is flag/tests-only: only the descriptive block is
   guarded by `if a3_short`, the budget-v2 A3 rows and A4/A5/A1/A2 are untouched, flag-off is call-for-call identical,
   and the flag is probes-only and refused without `--budget`/on `--tiny`. Confirm no non-finite STOP or spec constant
   changed.
2. **Runner (`7ae4d2ea`).** `git diff 3833d93e..7ae4d2ea` is confined to `r1/scripts/trackp_p3a_guarded.py` and its
   test file; the attempt-1 path's calls/journal keys are unchanged when the new kwargs are absent. Check the
   preflight list against plan §1c.2 and R2 conditions 2/6, the marker ordering (begin before the first unit, end in
   `finally`), the attempt-1 hash walk, the M13 template block/ids, the budget arithmetic
   (`45 h − 36.318161 h = 8.681839 h`; 60-h cap recorded), the exactly-two command sequence (DRYRUN kev-0.8b n=8 then
   EVIDENCE qwen3.5-4b-base n=100, both A3-short loading attempt-1 `final/saved`), and the DRYRUN gate before
   EVIDENCE.
3. **Tests.** Re-run the four commands in §3 in a full Track P environment; the 4 real-subprocess supervisor tests are
   Linux-only and must pass there. Confirm the new tests do not need a model, tokenizer, GPU or host.
4. **Boundaries.** Confirm `git diff b9ad6f8f..HEAD --stat` touches only the six files listed in §0, no `main` merge,
   no W2-3/v3/v2/M13/order change, no config/rule/E0/data/model change, no deletion, no push.
5. **Recorded shas.** Record `3833d93e` (A3 delta) and `7ae4d2ea` (runner) as the reviewed code commits; the run must
   check out exactly the A3-short commit on TASL-7 (clean) and the runner preflight accepts that HEAD because
   `b9ad6f8f` is an ancestor. Unit B additionally still needs Unit A execution, the M13/A6 disposition and the run
   authorization — none of which this record provides.

## 6. Residual risks / interpretation points

- **M13 derivation sha.** `M13_ORDER_RECORD_SHA256` records the M13 record bytes as delivered on 16 Nov
  (`351611c5…`). It is stored as provenance data (the record is not on the host checkout, so it cannot be re-hashed at
  run time); if the M13 record is amended, regenerate this constant before the run.
- **Derived attempt-1 template ids** are pinned from M13 §3.5 and cross-checked against the live sources: the Qwen id
  therefore requires the installed `transformers` version to be exactly `5.19.0` (the recorded freeze/config pin) and
  the Kev id requires the installed Kev commit `2074cc44…`; drift is a STOP, which is intended but means a host venv
  change must be separately reviewed.
- **Kev encoder hash** is computed from the installed `kev/model.py` (dist-info `direct_url.json` commit): attempt 1
  recorded no such hash, so the attempt-2 sidecar records the current installed hash (M13 R2 limit: the upstream git
  object is not available locally).
- **Campaign template representation.** The plan/§1c.2 says "per-unit manifest with a template version"; M13 §3.3
  describes one campaign `template`. Because the two units are different families (Kev DRYRUN, Qwen EVIDENCE), the
  journal records `templates` keyed by family and each sidecar carries its own `attempt2_template`; both must equal
  the M13 derived attempt-1 ids.
- **Lease log location.** Attempt 1's lease log is the global `~/r1_trackp/runs/gpu_lease_log.jsonl` (attempt-1 root
  sibling); the runner requires it there and writes only the new root's `gpu_lease_log.jsonl` (mirror). The child
  keeps writing the global log because `trackp.py`'s lease path comes from the unchanged config.
- **`ps`-based foreign-process census** is heuristic (pattern list, own pid/ppid excluded); it is one of several
  independent STOPs (lease, GPU census, markers) and may need the pattern list widened if the host ever runs another
  clearly-foreign experiment.
- **Local test coverage gap** described in §3: real child execution, live preflight and the marker helper are
  TASL-7-only and were not run by this unit.

**No host was contacted, no GPU command was run, nothing was pushed, `main` was not merged, and attempt 1 was only
read (through its exported inventory).**
