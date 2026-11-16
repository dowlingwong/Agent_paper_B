# Track P P.3a attempt-2 — code units (A3-short delta and probes-only runner), 16 November 2026

**Status: implementation record for re-review (revision 2). ENGINEERING_ONLY; AI-assisted.** No GPU job, no model,
no experiment and no host was run or touched; no push, no merge of `main`, no deletion. Revision 2 responds to the
independent review of the round-1 code units `7ae4d2ea` (runner) and `8a3d3eaf` (record): verdict NOT ACCEPTED, no
BLOCKING, **2 MAJOR + 8 MINOR**. The code changes are the fix commit **`7c9e8b08`** plus one mechanical
delivery-pin/docs commit; the A3-short commit `3833d93e` and every unrelated file are unchanged. **The commits under
review are `7c9e8b08` (code) and the delivery-pin/docs child that updates `EXPECTED_PAPER_HEAD` and this record;
their final shas are recorded after review.** No claim of acceptance is made.

Inputs read (read-only): plan rev2 `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md`; accepted Unit A review
`docs/r1/reviews/TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md`; M13 order record
`docs/r1/reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md`; attempt-1 inventory
`docs/r1/reports/trackp_p3a_attempt1_inventory_20261116/`; pinned code at `b9ad6f8f`; the round-1 review of the two
code units (2 MAJOR + 8 MINOR, findings quoted in §0.1).

## 0. Commits and exact diff scope

| Commit | Subject | Files |
|---|---|---|
| `3833d93e` | `feat(r1): Track P P.3a A3-short execution flag (option 3)` | `r1/c3/train/exam_run.py` (+21/−8), `r1/scripts/trackp.py` (+16/−1), `r1/tests/test_trackp_p3a_a3_short.py` (new, 139 lines) |
| `7ae4d2ea` | `feat(r1): Track P P.3a probes-only runner/preflight/journal/budget unit` | `r1/scripts/trackp_p3a_guarded.py` (+772/−15), `r1/tests/test_trackp_p3a_probes_only.py` (new, 528 lines) |
| `8a3d3eaf` | `docs(r1): record Track P P.3a attempt-2 code units` (round-1 record) | this record only |
| `7c9e8b08` | `fix(r1): Track P P.3a probes-only runner review fixes (round 1)` | `r1/scripts/trackp_p3a_guarded.py`, `r1/tests/test_trackp_p3a_probes_only.py` |
| delivery-pin/docs child | `docs(r1): P.3a runner review fixes record + delivery pin` | one `EXPECTED_PAPER_HEAD` line in `r1/scripts/trackp_p3a_guarded.py` and this record |

Author/committer both `Dowling Wong <wangdowling@gmail.com>`. `git diff 7ae4d2ea..HEAD --name-status` after the
delivery-pin commit:

```
A	docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md
M	r1/scripts/trackp_p3a_guarded.py
M	r1/tests/test_trackp_p3a_probes_only.py
```

(`git diff 7ae4d2ea..7c9e8b08 --numstat` = runner `+216/−18` and tests `+586/−28`; the delivery-pin/docs
child changes one code line plus this record.)

Only those three files are touched after `7ae4d2ea`: no A3-short file (`3833d93e`), no W2-3/v3/v2/M13/order change,
no config/rule/E0/data/harness change, no `main` merge, no script outside `r1/`, no deletion of the pinned
non-finite STOPs.

**Why a delivery-pin commit exists.** An exact-commit pin cannot name the very commit that contains it (git's
commit sha covers the file with the pin, a hash cycle). `EXPECTED_PAPER_HEAD` therefore names the reviewed *code*
commit `7c9e8b08`; the delivery-pin commit is its direct child and changes **exactly one code line** (that
assignment) plus this record. The preflight accepts precisely: the reviewed code commit, its docs-only child when
the `r1/` tree is byte-identical, or this single mechanical delivery-pin child — and refuses every other commit,
including arbitrary descendants. The actual paper HEAD (kind, sha, branch), the sha256 of the executing runner
script and of the child `trackp.py` are recorded in `campaign_start` (§2.7).

## 0.1 Point-by-point response to the round-1 review

| Finding | Status | Where |
|---|---|---|
| **MAJOR-1** boot id never compared to attempt-1 boot id | fixed: `EXPECTED_ATTEMPT1_BOOT_ID = 2c9bb104-…` pinned, read from the attempt-1 journal `campaign_start` into provenance, asserted, and enforced in the live preflight and again against the journal before root creation; expected+actual recorded in provenance and `campaign_start`; CPU tests added | §2.2, §2.4 |
| **MAJOR-2** any descendant passed; delivery record named `3833d93e` (no runner) | fixed: `EXPECTED_PAPER_HEAD = 7ae4d2ea…`→`7c9e8b08` with docs-child and mechanical delivery-pin child only; branch `trackp-p3a-code-20261116` or detached HEAD; `b9ad6f8f` ancestor/clean kept; `git ls-files --error-unmatch` folded in; paper HEAD + runner/child script sha256 recorded; §5.5 delivery wording corrected; wrong-HEAD/wrong-branch CPU tests added | §2.2, §2.7, §5.5 |
| **M1** no golden token-stream test | fixed: source-level golden vector (Qwen `prefix`/`segments`, Kev record layout) always runs; the pool-tokenizer/Qwen and installed-Kev token-id vectors run when available and **skip with an explicit reason** when absent; limitation recorded | §2.8, §3, §6 |
| **M2** `derived_template_id` was always the Qwen id | fixed: campaign provenance carries `derived_template_ids_by_family`; each sidecar's `attempt1_provenance.derived_template_id` is that unit's family id and must equal its `attempt2_template.template_id` and the M13 §3.5 id (fail-closed) | §2.4, §2.5 |
| **M3** missing preflight-internals tests | fixed: monkeypatched CPU tests for dirty/detached/wrong-HEAD paper, harness pin/dirt, e0/rule/config/freeze/registry, hostname/driver/disk, GPU census, lease, `*.active`, experiment processes, marker helper, amendment file, tracked scripts, and the boot/HEAD pins | §3 |
| **M4** template/provenance hashes only checked after child exit | fixed: `unit_start_verifier` re-reads the attempt-1 journal/lease hashes, re-hashes every loaded attempt-1 file and recomputes the declared template **before** the child is spawned; `unit_start` records the verification; drift is a STOP | §2.5 |
| **M6** sidecar write not atomic | fixed: `write_json_atomic` (same-directory temp file + fsync + `os.replace`) used for `runner_manifest.json`; CPU test asserts the replace and no temp remains | §2.5 |
| **M7** root/attempt-1-root argument checks | fixed: `--attempt1-root` must be absolute; `--root` must be absolute, absent (`l-exists`, so a dangling symlink also refuses), `p3a_attempt2_YYYYmmddTHHMMSSZ` UTC, directly under the runs directory; explicit tests | §2.1 |
| **M8** record wording / symlink statement | fixed: this record says "commits under review / to be recorded after review", does not imply pre-acceptance, and states exactly what the code does: extra *regular* files in a loaded `final/saved` are refused; symlinks are recorded (and a symlink where a recorded model file is expected fails the hash comparison) but an extra symlink is not itself refused | §2.4, §5.5 |
| **M5** SIGTERM/`kill -9` marker-left behaviour | documented: the marker `end` runs in a `finally` (`begin`/`end` on success or STOP), so a SIGTERM/SIGKILL to the supervisor can leave the `p3a.active` marker and no STOP record; the next preflight refuses via the `*.active` STOP, and the manual recovery is `trackp-evidence end p3a` after inspection (documented, no code change) | §6 |

## 1. Commit 1 — A3-short execution delta (`R1-P3A-OOM-OPTION3`, unchanged)

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
run is not `--tiny`. No manifest field was added — the run-time record of the flag is the attempt-2 runner's
journal/sidecar and the child report's skipped marker. **This commit is not touched by revision 2.**

## 2. Probes-only runner / preflight / journal / budget (same file as the attempt-1 supervisor)

`r1/scripts/trackp_p3a_guarded.py` is extended, not replaced. The attempt-1 multi-base path is unchanged: with none
of the attempt-2 keyword arguments, `run_unit` emits the same journal events and performs the same checks as before.

### 2.1 Args and mode contract (`parse_args`, `validate_probes_only_args`)

New args: `--probes-only`, `--base` (required, must be `qwen3.5-4b-base`), `--attempt1-root` (required, **absolute**),
`--a3-short` (required in this mode), `--authorization-amend-sha256` (required, must equal the reviewed
`cd867e95ddab0525827a48d68ea570743977bbf1b6ea819fefb98b3cf460f32d`), and `--root`:
absolute, **absent** (checked with `l-exists`, so a dangling symlink is refused), named
`p3a_attempt2_YYYYmmddTHHMMSSZ` (a real UTC calendar timestamp, parsed with `datetime.strptime` and re-rendered),
and located **directly under the runs directory** (`$R1_RUNS`, default `<LEASE_LOG parent>`, i.e.
`~/r1_trackp/runs` on TASL-7). Also: the attempt-1 root may not equal/contain/be nested in the new root, and the
attempt-1 root name is refused. Supplying any probes-only flag without `--probes-only` is a STOP (the old multi-base
campaign cannot be silently switched), and probes-only never iterates `BASES`.

### 2.2 Preflight (`verify_probes_only_pins`, fail-closed)

- **Exact paper HEAD (MAJOR-2)**: `verify_paper_head` accepts only (i) `EXPECTED_PAPER_HEAD` (the reviewed runner
  commit), (ii) its docs-only child when `git diff --quiet <expected> <head> -- r1/` is empty, or (iii) the single
  mechanical delivery-pin child (direct child, `r1/` diff is exactly the one `EXPECTED_PAPER_HEAD` assignment, other
  changes allowed only in this record). Branch must be `trackp-p3a-code-20261116` or a detached HEAD (`"HEAD"`).
  `b9ad6f8f` must still be an ancestor and the checkout clean. The paper/watches/gate/child scripts must be tracked
  (`git ls-files --error-unmatch`). `campaign_start` records the paper HEAD and the accepted kind.
- **Boot id (MAJOR-1)**: the current `boot_id` is compared to the reviewed
  `EXPECTED_ATTEMPT1_BOOT_ID = 2c9bb104-cc3c-4c60-be67-c1c8f0287fe4` (the attempt-1 `campaign_start.boot_id` and
  the exported attempt-1 manifests); a mismatch is a STOP **before** root creation, marker or GPU work. Expected and
  actual ids are recorded in `campaign_start` and in the provenance block.
- harness `897d83c8` clean; `r1/c3/train/data/e0_v1.jsonl.gz` sha256 `4f4db29b…`; `r1/c3/rules/p3_rule_v2.yaml`
  sha256 `8c0ef908…`; `r1/scripts/configs/trackp_portal.json` identical to `607e85e:…`; venv freeze equal to
  `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt`; `registry.reverify` clean;
- host `TASL-7`, NVIDIA driver `580.178.04` (kernel/user/package consistency via `tasl7_driver_snapshot`), disk
  free ≥ 10 GiB; `flock ~/r1_locks/gpu0.lock` free; empty GPU-compute census; no other experiment process; no
  `*.active` marker; installed marker helper `~/r1_locks/bin/trackp-evidence` sha256 `f457a04e…`; the 4 Nov
  amendment sha gate (`--authorization-amend-sha256`, additionally re-hashed if the file is present in the
  checkout).
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
`gpu_seconds_total` and hours, `attempt1_boot_id` (from the attempt-1 `campaign_start`) plus
`expected_attempt1_boot_id`, `derived_prompt_version: trackp_prompt/v1`, `derived_order: history_first`, the
**per-family** `derived_template_ids_by_family` (M2 — no campaign-level scalar id), `recorded_at_run_time: false`,
`label: "derived"`, and the M13 derivation doc + sha256. The journal/lease hashes, the paper commit, the boot id
and the 130745.3789889291 s STOP total are pinned to the reviewed values (mismatch = STOP). For each loaded
`EVIDENCE/<base>/final/saved` directory: `saved/manifest.json["files"]` must equal
`EVIDENCE/<base>/final/manifest.json["model_files_sha256"]`, every recorded file is re-hashed from disk (**extra
regular files are refused**; a symlink where a recorded model file is expected fails the hash comparison), and the
block records every relative path + sha256 + a composite hash. Symlinks found in the directory are **recorded**
under `symlinks` (never followed), but an extra symlink by itself is not refused — the fail-closed guarantee is the
recorded-file hash equality. Attempt 1 is never edited or re-labelled.

### 2.5 Template/version and per-unit sidecar (`template_block`, `make_sidecar_builder`, `make_unit_start_verifier`)

`<unit>/runner_manifest.json`, schema `trackp_p3a_unit_manifest/v1`, is written by the runner after the child exits 0
and after the child `manifest.json`/`report.json` pass the finite-JSON re-read, before `unit_complete`. The write is
**atomic** (M6: same-directory temp file, fsync, `os.replace`) and is re-read and compared.

- `attempt2_template`: `version` imported from `r1.c3.train.types.PROMPT_VERSION` (must be `trackp_prompt/v1`),
  `version_source: r1/c3/train/types.py:26`, `family`, declared `frame` (`kev_pointer_v1` / `qwen_bintoken_v1`),
  `order: history_first`, declared `field_order`, `readout`, `encoder`, `wrapper_config`, and the composite
  `template_id` `trackp_prompt/v1/<frame>/history_first/<encoder id>` — exactly the M13 §3.2 block and ids §3.5.
- `attempt1_provenance`: copy of the campaign provenance with a **per-unit** `derived_template_id` (the unit's
  family composite id) and `derived_template_family` (M2); it must equal the unit's `attempt2_template.template_id`,
  the family entry in `derived_template_ids_by_family`, and the reviewed M13 §3.5 id.
- `attempt1_input` for this unit, `inputs.child_manifest_sha256`, `inputs.child_report_sha256`,
  `inputs.authorization_amend_sha256`, `cost.gpu_seconds`, `created_utc`.
- The per-unit template is recomputed from the child manifest and must equal the campaign-level declaration; any
  drift (PROMPT_VERSION, Kev commit, transformers version, wrapper config, frame/order) is a STOP.
- **At each `unit_start`** (M4), *before the child is spawned*, `make_unit_start_verifier` re-reads the attempt-1
  journal and lease log (sha256 + STOP seconds + paper commit + boot id), re-hashes every loaded attempt-1
  `final/saved` file, and recomputes the declared template; any drift is a STOP. The result (template id,
  composite input hash, journal/lease hashes) is recorded in the `unit_start` event. The post-child template check
  remains.
- `journal.jsonl` `campaign_start` records `serialisation_schema`, `templates`, `attempt1_provenance`,
  `attempt1_inputs`, authorization, marker, environment, budget and argv. Every `unit_start`/`unit_complete`
  records `template_id` (unit_start also `attempt1_input` and `unit_start_verification`; unit_complete also
  `runner_manifest_sha256` and `gpu_seconds_unit`); `STOP` records `template_id` and the marker end.

### 2.6 Budget (`Attempt2Budget`) and the two-unit sequence

- `used = attempt-1 journal gpu_seconds_total (130745.3789889291 s = 36.318161 h) + time recorded in this run's own
  `gpu_lease_log.jsonl`*. `require_available(projection)` refreshes and refuses a unit **before it starts** if
  `used + projection >= 45 h`; the 60-h P.3a cap is recorded and checked (it includes attempt 1; it is not extra
  time). Conservative per-unit projections: DRYRUN 600 s, EVIDENCE 1,800 s.
- Exactly two GPU commands, in this order, both `--a3-short` and loading attempt-1 `EVIDENCE/<base>/final/saved`:
  1. DRYRUN `kev-0.8b` probes, `--n-probe 8`;
  2. EVIDENCE `qwen3.5-4b-base` probes, `--n-probe 100`.
  No other base or unit, new directories only, no retry (an existing unit directory is a STOP).
- After each child report the runner asserts the changed path ran: `A3.protocol == "v2_budget"` and
  `A3_descriptive == {"skipped": "R1-P3A-OOM-OPTION3", "levels": [2000, 8000], "pass": null}` exactly. If the
  DRYRUN report does not show it, the campaign STOPs and the EVIDENCE unit never starts.
- Outputs are preserved; nothing is deleted or moved aside.

### 2.7 Delivery identity recorded at run time (MAJOR-1/MAJOR-2)

The preflight return (embedded in `campaign_start.pins` and repeated at the top level) records: paper HEAD commit,
branch and accepted kind (`exact_reviewed_runner_commit` / `docs_child_r1_identical` / `delivery_pin_child`), the
expected commit, the base pin and its ancestor check, the boot id expected/actual/match, the **sha256 of the
executing runner script** (`EXECUTING_RUNNER = <file> resolve`) and of the **child `r1/scripts/trackp.py`**, plus
the existing harness/E0/rule/config/freeze/registry/host/driver/disk/lease/marker/census records. `run_probes_only_campaign`
also re-checks the current boot id against the attempt-1 journal's recorded boot id before creating the root.

### 2.8 Golden template vector (M1)

`test_golden_field_order_from_the_pinned_renderers` always runs: it takes a fixed `DecisionPrompt`, renders the
pinned Qwen `BinTokenWrapper.prefix`/`segments` with a deterministic stub tokenizer, asserts the token positions of
state → proposal → question → bins → belief → action, and compares them to `FRAMES`; it also checks the pinned Kev
`PointerWrapper.records` layout (state before proposal+question before the 12 options) and the declared Kev decide
token. The real **token-id** golden vectors (M13 §3.2) are separate tests: they use the pool tokenizer for
`qwen3.5-4b-base` and the installed Kev encoder, and **skip with an explicit reason** when those are absent locally.
On TASL-7 they must be re-run (they are part of the acceptance check, §5). The local limitation is recorded in §6.

## 3. Exact test commands and results (local, CPU, no GPU/model)

Local environment (temporary venv, not the TASL-7 env): Python 3.13.4, pytest 9.2.0, numpy 2.5.5, scipy 1.18.1,
torch 2.15.0 (CPU/MPS build), PyYAML 6.0.3. No transformers/tokenizers, no pool model, no CUDA, no Kev.

```
$ python -m py_compile r1/c3/train/exam_run.py r1/scripts/trackp.py r1/scripts/trackp_p3a_guarded.py \
      r1/tests/test_trackp_p3a_a3_short.py r1/tests/test_trackp_p3a_probes_only.py
py_compile OK (5 files)

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_a3_short.py -q
8 passed

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_probes_only.py -q
41 passed, 2 skipped

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_guarded.py -q     # pre-existing suite
5 passed, 4 failed

$ PYTHONPATH=. pytest r1/tests/test_trackp_cli.py -q
9 skipped
```

The 2 skips are the real tokenizer/Kev golden vectors: `test_golden_token_ids_qwen_from_the_pool_tokenizer`
(pool tokenizers not in the local HF cache; skip message names the missing import) and
`test_golden_token_ids_kev_from_the_pinned_encoder` (`pytest.importorskip("kev")`). The source-level golden vector
and every other new test run.

**The 4 `test_trackp_p3a_guarded.py` failures are pre-existing and environmental, not caused by this work.** They
are the real-subprocess tests, which reach the pin's `worker_parent_death_guard` `preexec_fn`
(`ctypes.CDLL(None).prctl(PR_SET_PDEATHSIG)`); macOS has no `prctl`. Verified again this round: identical
`5 passed, 4 failed` on the unmodified baseline and here. The 5 CPU-only safety tests pass. `test_trackp_cli.py`
skips because the pool tokenizers are not in the local HF cache (no transformers).

**What could not run locally:** the real probes (they need the TASL-7 venv, the four-base pool
tokenizers/model files and a GPU), the DRYRUN/EVIDENCE children (stubbed in the tests), the live
preflight/marker/lease/`nvidia-smi` paths (TASL-7-only; every internals branch is now unit-tested with stubs), the
tokenizer/Kev token-id golden vectors (skipped with a reason), and the tokenizer-dependent Track P CLI dry-run
suite. Every changed file is `py_compile` clean.

**Round-2 test coverage added (M3):** `_PreflightStubs` stubs every live dependency and one test per failure
branch: paper dirty / wrong HEAD identity / base pin not an ancestor, harness pin or dirt, e0/rule/config/freeze/
registry, hostname/driver(kernel+empty)/disk, GPU census, lease, `*.active`, foreign experiment process, marker
helper sha, untracked runner scripts, amendment file hash (present + matching), and boot-id mismatch. The exact
HEAD identity (wrong HEAD, wrong branch, detached HEAD, docs child, delivery-pin child, arbitrary descendant) is
tested against a throwaway git repo, as are the boot-id gate, the unit-start re-verifier (input/journal/template
drift), the atomic sidecar write, the root-name/absolute/runs-dir contract, and the source-level golden vector.

## 4. Fail-closed STOP list

A3-short delta: `a3_short` with `counters=None` (ValueError); CLI `--a3-short` without `--budget`; CLI
`--a3-short` with `--tiny`; `--a3-short` on any non-`probes` subcommand (argparse error).

Probes-only runner: missing/invalid `--probes-only` args; wrong `--base`; relative `--attempt1-root`; relative/
existing/dangling-symlink/mis-named/non-UTC root; a root not directly under the runs directory; attempt-1 root
reused or nested; non-`TASL-7` host; **paper HEAD not exactly the reviewed runner commit / its docs-only child /
the mechanical delivery-pin child, or wrong branch**; `git ls-files` untracked scripts; dirty paper; paper base pin
not an ancestor; harness pin/dirtiness; E0/rule/config/freeze/registry mismatch; driver mismatch; **current boot id
≠ attempt-1 boot id**; low disk; held lease; non-empty GPU census; another experiment process; another `*.active`
marker; missing or wrong marker helper; attempt-1 journal/lease-log missing, wrong sha256, no/duplicate STOP,
non-finite or changed GPU total, missing or changed boot id; attempt-1 loaded directory missing/unrecorded/
tampered/extra regular file/symlinked recorded file; family/frame/wrapper-config/PROMPT_VERSION/Kev-encoder/
transformers template drift; **unit-start attempt-1 provenance/journal/lease/input/template drift**; per-unit
template or per-unit provenance template-id disagreement with the campaign declaration; 45-h projection crossing or
45-h/60-h reached; unit directory already existing (no retry); child failure rc≠0; missing or incomplete lease
record; label/boot mismatch; non-finite child report/manifest; DRYRUN report not showing the budget-v2 path / the
skipped marker; failed marker begin or end; any unexpected unit/base in the sequence. Every STOP preserves outputs
and emits a STOP journal record (when the journal exists); there is no bare `trackp.py probes` fallback.

## 5. What the reviewer must check

1. **A3 delta (`3833d93e`)** — unchanged by revision 2. `git diff b9ad6f8f..3833d93e` is flag/tests-only; flag-off
   is call-for-call identical; the flag is probes-only and refused without `--budget`/on `--tiny`.
2. **Runner fixes (`7c9e8b08`).** `git diff 7ae4d2ea..7c9e8b08` is confined to the runner and its test file. Check
   the boot gate (expected/actual recorded, STOP before root/marker), the exact-HEAD acceptance (and refusal of
   arbitrary descendants), the merged `git ls-files` check, the per-unit provenance id, the unit-start verifier,
   the atomic sidecar write, the root/attempt-1-root arg contract, the `campaign_start` delivery-identity fields,
   and the golden-vector test/skip.
3. **Tests.** Re-run the commands in §3 in a full Track P environment (TASL-7 venv); the tokenizer/Kev golden tests
   must run there, and the 4 real-subprocess supervisor tests are Linux-only and must pass there. Confirm the new
   tests need no model/tokenizer/GPU/host.
4. **Boundaries.** Confirm `git diff 7ae4d2ea..HEAD --stat` touches only the three files in §0, no A3-short file,
   no `main` merge, no config/rule/E0/data/model change, no deletion, no push.
5. **Delivery pin / exact commit.** The code commit is `7c9e8b08`; `EXPECTED_PAPER_HEAD` names it, and the
   delivery-pin/docs child differs from it by exactly the one pin assignment plus this record. Confirm the
   preflight accepts the pinned commit and that single pin child only, and records the actual HEAD + executing
   runner/child script sha256. **Commits under review / to be recorded after review** — do not check out
   `3833d93e` (it predates the probes-only runner) or `8a3d3eaf` (it predates these fixes); the run checks out the
   reviewed runner commit/pin child, clean/detached or on branch `trackp-p3a-code-20261116`. Unit B additionally
   still needs Unit A execution, the M13/A6 disposition and the run authorization — none of which this record
   provides.

## 6. Residual risks / interpretation points

- **Exact-commit pin vs. the pin commit (MAJOR-2).** The pin cannot contain its own sha; §0 records the two-commit
  delivery-pin mechanism and the preflight accepts only the reviewed code commit, its docs-only child (r1/
  identical) or that single mechanical pin child. Any later code change requires a new reviewed code commit and a
  new pin child; no other descendant is accepted.
- **Golden token-id test limitation (M1).** Locally only the source-level golden vector runs; the real pool
  tokenizer and installed Kev encoder are absent, so the two token-id tests skip with an explicit reason. They must
  be run on TASL-7 before the run acceptance (§5.3). If neither can produce a vector there either, the M13 §3.2
  golden requirement is unmet and the run must not start.
- **Marker left by SIGTERM/`kill -9` (M5).** The marker end runs in a `finally`, but a SIGTERM/SIGKILL of the
  supervisor (or power loss) can by definition skip it, leaving `~/r1_locks/p3a.active` and no journal STOP. This is
  fail-closed: the next preflight's `*.active` check refuses to start. Recovery is manual after inspection: run
  `~/r1_locks/bin/trackp-evidence end p3a` (the helper's `end <phase>` interface) and verify the lease/journal
  state; outputs are preserved. The runner never removes another marker automatically.
- **M13 derivation sha.** `M13_ORDER_RECORD_SHA256` records the M13 record bytes as delivered on 16 Nov
  (`351611c5…`); it is provenance data (the record is not on the host checkout, so it cannot be re-hashed at run
  time). If the M13 record is amended, regenerate this constant before the run.
- **Derived attempt-1 template ids** are pinned from M13 §3.5 and cross-checked against the live sources: the Qwen
  id requires the installed `transformers` version to be exactly `5.19.0` and the Kev id requires the installed Kev
  commit `2074cc44…`; drift is a STOP, which is intended but means a host venv change must be separately reviewed.
- **Kev encoder hash** is computed from the installed `kev/model.py` (dist-info `direct_url.json` commit): attempt 1
  recorded no such hash, so the attempt-2 sidecar records the current installed hash (M13 R2 limit).
- **Campaign template representation.** The two units are different families (Kev DRYRUN, Qwen EVIDENCE), so the
  journal records `templates` keyed by family and each sidecar carries its own `attempt2_template` and its own
  per-unit `attempt1_provenance.derived_template_id`; both must equal the M13 derived ids.
- **Lease log location.** Attempt 1's lease log is the global `~/r1_trackp/runs/gpu_lease_log.jsonl`; the runner
  requires it there and writes only the new root's `gpu_lease_log.jsonl` (mirror). The child keeps writing the
  global log because `trackp.py`'s lease path comes from the unchanged config.
- **`ps`-based foreign-process census** is heuristic (pattern list, own pid/ppid excluded); it is one of several
  independent STOPs (lease, GPU census, markers) and may need the pattern list widened if the host ever runs
  another clearly-foreign experiment.
- **Local test coverage gap** described in §3: real child execution, live preflight and the marker helper are
  TASL-7-only and were not run by this unit.

**No host was contacted, no GPU command was run, nothing was pushed, `main` was not merged, no deletion was made,
and attempt 1 was only read (through its exported inventory).**
