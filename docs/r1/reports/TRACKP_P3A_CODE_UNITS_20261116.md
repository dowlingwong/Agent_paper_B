# Track P P.3a attempt-2 — code units (A3-short delta and probes-only runner), 16 November 2026

**Status: implementation record for re-review (revision 3). ENGINEERING_ONLY; AI-assisted.** No GPU job, no model,
no experiment and no host was run or touched; no push, no merge of `main`, no deletion. Revision 3 responds to the
independent round-2 review of the round-1 fixes (`7c9e8b08` code + `9071f5b2` delivery pin), which found **1
BLOCKING + 1 MAJOR + 5 MINOR**; the round-2 review file is
`docs/r1/reviews/TRACKP_P3A_RUNNER_REVIEW_R2_20261116.md` (reviewer artifact, read-only). The A3-short commit
`3833d93e` and every unrelated file are unchanged.

**Commits under review / to be recorded after review.**

| | |
|---|---|
| **C** (reviewed code commit) | `5b7ad0cb7fedd083bad457968dc3dd3e920ac154` — `fix(r1): Track P P.3a probes-only runner review fixes (round 2)`, touches only `r1/scripts/trackp_p3a_guarded.py` and `r1/tests/test_trackp_p3a_probes_only.py` |
| **D** (mechanical delivery-pin child) | direct child of `C`; its only runner change is the single canonical `EXPECTED_PAPER_HEAD = "5b7ad0cb…"` assignment and it rewrites this record. **D cannot contain its own sha** (a commit sha covers the file with the pin, a hash cycle), so D's exact sha is recorded after the commit exists / after review. |

Author and committer of both: `Dowling Wong <wangdowling@gmail.com>`. **The host checks out exactly D** (detached
HEAD or on branch `trackp-p3a-code-20261116`), **clean** — see §5.5. C alone is refused by C's own script (its
constant still names the previous reviewed code commit `7c9e8b08`; self-pin cycle); `3833d93e` and `8a3d3eaf` are
refused (they predate the runner/fixes).

## 0. Commits and exact diff scope

| Commit | Subject | Files |
|---|---|---|
| `3833d93e` | `feat(r1): Track P P.3a A3-short execution flag (option 3)` | `r1/c3/train/exam_run.py` (+21/−8), `r1/scripts/trackp.py` (+16/−1), `r1/tests/test_trackp_p3a_a3_short.py` (new, 139 lines) |
| `7ae4d2ea` | `feat(r1): Track P P.3a probes-only runner/preflight/journal/budget unit` | `r1/scripts/trackp_p3a_guarded.py` (+772/−15), `r1/tests/test_trackp_p3a_probes_only.py` (new, 528 lines) |
| `8a3d3eaf` | round-1 record | this record only |
| `7c9e8b08` | round-1 review fixes | runner + its test file |
| `9071f5b2` | round-1 record + delivery pin | one `EXPECTED_PAPER_HEAD` line in the runner and this record |
| **`C` = `5b7ad0cb`** | **round-2 review fixes** | runner (+`253/−58`), tests (+`243/−62`) |
| **D** (this commit) | round-2 record + delivery pin | one `EXPECTED_PAPER_HEAD` line in the runner and this record |

`git diff 7ae4d2ea..D --name-status` therefore touches exactly this record (`A` in `8a3d3eaf`, rewritten in
`9071f5b2` and D), `r1/scripts/trackp_p3a_guarded.py` (`M`) and `r1/tests/test_trackp_p3a_probes_only.py` (`M`) —
no A3-short file, no W2-3/v3/v2/M13/order change, no config/rule/E0/data/model change, no `main` merge, no script
outside `r1/`, no deletion. `git diff 7c9e8b08..D -- r1/` is the round-2 runner fixes plus the single delivery-pin
line. `git diff 3833d93e..D -- r1/c3/train/exam_run.py r1/scripts/trackp.py r1/tests/test_trackp_p3a_a3_short.py`
is empty.

**Why a delivery-pin commit exists (self-reference cycle).** A commit cannot name its own sha: `EXPECTED_PAPER_HEAD`
in C would have to contain C, which changes the bytes that produce C. C therefore keeps the previous reviewed
commit's sha in that line, and D changes exactly that one canonical line to C. D is byte-checked (§2.2), not merely
shape-checked. The preflight accepts exactly C, a docs-only child of C with a byte-identical `r1/` tree, and D —
nothing else (§2.2).

## 0.1 Point-by-point response to the round-2 review

| Finding | Status | Where |
|---|---|---|
| **BLOCKING-1** M4 unit-start check re-hashed the *live global* attempt-1 lease log that attempt 2 appends to, so the EVIDENCE unit could never start | **Fixed.** At campaign start the attempt-1 lease-log bytes are copied read-only into `<root>/attempt1_provenance/gpu_lease_log.jsonl` (mode `0444`), and `attempt1_provenance.lease_log_snapshot` records `sha256`, byte count, line count, source, read-only flag and mode. The unit-start verifier re-hashes **that immutable snapshot** (bytes + size + equality with the campaign-start pin) plus the pinned attempt-1 journal / loaded files / template, and never reads the live log. The live global log is read exactly once at campaign start, where it must equal the pinned sha256, and is documented to grow afterwards. CPU test with a **host-shaped** attempt-1 root (parent is the runs dir): DRYRUN start passes, a fake lease pair is appended to the live global log, EVIDENCE start still passes, and a tampered snapshot STOPs. | §2.4, §2.5, §3 |
| **MAJOR-1** `_delivery_pin_child` accepted any one-line child whose changed line merely *contained* `EXPECTED_PAPER_HEAD = ` (a crafted `__import__("os").system(…)` child passed) | **Fixed, byte-exact.** The expected pin blob is computed in memory: the reviewed code commit's runner blob with its single canonical `EXPECTED_PAPER_HEAD = "<40 hex>"` line replaced by the same canonical line naming the reviewed code commit. D is accepted only if it has exactly one parent (== C), its runner blob is byte-identical to that blob, and no other file under `r1/` changed (changes outside `r1/` must be under `docs/`). A crafted one-line child with injected code is REFUSED; a genuine pin child in a throwaway repo is accepted. | §2.2, §3 |
| **MAJOR-1/§3.2 (MINOR-3)** the pin was on the checkout, not on the executing bytes (`R.git_commit` ignores untracked/assume-unchanged differences) | **Fixed.** `verify_executing_files` requires the executing runner to be the checkout's tracked runner and 12 executing files (runner, child `trackp.py`, watchdog, gate, `run.py`, `types.py`, `model.py`, `exam_run.py`, `trainer.py`, `registry.py`, `serialize.py`, `labels.py`) to be byte-identical to their `HEAD:` blobs; their sha256 are recorded in the preflight return and `campaign_start`. Dirty, `assume-unchanged`/ignored and out-of-checkout copies are refused (tests). | §2.2, §2.7, §3 |
| **MINOR-1/§3.3** the stale docs-child constant `8a3d3eaf` is an ancestor with a different `r1/` tree and could never be accepted; the record implied otherwise | **Fixed.** `EXPECTED_PAPER_HEAD_DOCS_CHILD` is removed. The docs-only-child acceptance is re-based generically on `EXPECTED_PAPER_HEAD`: a descendant of C with a byte-identical `r1/` tree. The record (§2.2, §5) now states exactly what is accepted and that a clean checkout runs only D; no stale constant remains. | §2.2, §5.5 |
| **MINOR-2** delivery wording did not name the commit the host must check out | **Fixed.** §5.5 names the reviewed code commit C plus its mechanical delivery-pin child D and says the host checks out **exactly D**, detached or on branch, clean; C alone is refused and any docs-only child of D (e.g. a review record committed on top) would make the branch HEAD unacceptable, so post-review records go to the ops branch while this branch stays at D. Commits are "under review / to be recorded after review". | §5.5, §6 |
| **MINOR-3** pin on the checkout, not the executing bytes | Fixed together with the MAJOR-1/§3.2 line above: `verify_executing_files` compares bytes to `HEAD:` blobs (not `git diff --quiet`) and records sha256. | §2.2, §2.7 |
| **MINOR-4** DRYRUN `--n-probe 8` deviated from the accepted-plan review's attempt-1-style 32 without a recorded rationale | **Fixed (recorded reading; keeps 8).** Attempt-1 probe leases at n=100 were 67.8–148.4 s; the DRYRUN is a short path-exercising run (`--a3-short` changed path, its `A3.protocol == v2_budget` and `A3_descriptive` skipped marker asserted by `verify_a3_short_report`; the real A3/A4/A5 rows are exercised by that path, not by the sample count); the EVIDENCE unit keeps n=100. Rationale is in the runner comment and §2.6. | §2.6 |
| **MINOR-5** `attempt1_boot_id_match` was a literal `True` | **Fixed.** `campaign_start` writes `pins["boot_id"] == provenance["attempt1_boot_id"]` (computed). | §2.7 |

All round-1 fixes are retained: boot-id gate, exact code-commit identity, per-family provenance ids, preflight
internals tests, unit-start verification of the journal/loaded files/template, atomic sidecar write, root/attempt-1
argument contract, M1 golden tests with explicit skips, the marker-left document and the symlink wording.

**A6 authority (resolved).** Round 2 noted that Unit B still needed an A6 disposition. The author decided
`R1-TRACKP-A6-DEFER` (branch `author-decisions-20261116c` @ `65d8d5bb`, already merged into the ops branch), which
defers A6 for attempt 2 and requires disclosure: attempt 2 runs no A6 work; the P.3a report must disclose the A6
deferral and the 2k/8k descriptive-level omission; any P.3b serialization-order change requires a separately
reviewed A6 unit. The authority rows are on the ops branch, not in this code checkout; only their identity is cited.

## 1. Commit `3833d93e` — A3-short execution delta (`R1-P3A-OOM-OPTION3`, unchanged by revision 3)

`exam_run.probes(model, run_dir, n=..., seed=..., counters=..., a3_short: bool = False)`. In the `counters is not
None` (A3 budget-v2) branch:

- `a3_short=True`: the descriptive block at the pin's `exam_run.py:290–295` (`E.a3_probe(tok, n=n,
  lengths=(0,)+E.A3_DESCRIPTIVE, …)` and `_a3_rps(…, f"descriptive_{L_}")`) is **not called**. Instead
  `out["A3_descriptive"] = {"skipped": "R1-P3A-OOM-OPTION3", "levels": list(E.A3_DESCRIPTIVE), "pass": None}`.
  The A3 budget-v2 rows (0/25/50/100 % at 1,024 tokens), `A3_errors`, A4, A5 and A1/A2 are unchanged.
- `a3_short=False`: byte-identical behaviour to `b9ad6f8f` (same calls, same `A3_descriptive`, same `pass: None`).
- `a3_short=True` with `counters=None` raises `ValueError` **before any probe runs**, so the v1 A3 0/2k/8k path
  can never be silently shortened.

`r1/scripts/trackp.py`: `--a3-short` is added **only to the `probes` subparser**; `cmd_probes` forwards
`a3_short=args.a3_short` to `X.probes`. The flag is refused (TrackPStop, rc 2) unless `--budget` is present and the
run is not `--tiny`. **Not touched by revision 3.**

## 2. Probes-only runner / preflight / journal / budget

`r1/scripts/trackp_p3a_guarded.py` is extended, not replaced; the attempt-1 multi-base path is unchanged (without
the attempt-2 keyword arguments `run_unit` behaves as before).

### 2.1 Args and mode contract (`parse_args`, `validate_probes_only_args`)

New args: `--probes-only`, `--base` (required, must be `qwen3.5-4b-base`), `--attempt1-root` (required, **absolute**),
`--a3-short` (required in this mode), `--authorization-amend-sha256` (required, must equal the reviewed
`cd867e95ddab0525827a48d68ea570743977bbf1b6ea819fefb98b3cf460f32d`), and `--root`: absolute, **absent** (checked
with `l-exists`, so a dangling symlink is refused), named `p3a_attempt2_YYYYmmddTHHMMSSZ` (a real UTC calendar
timestamp, parsed and re-rendered), and located **directly under the runs directory** (`$R1_RUNS`, default
`<LEASE_LOG parent>`, i.e. `~/r1_trackp/runs` on TASL-7). The attempt-1 root may not equal/contain/be nested in the
new root and its name is refused. Supplying any probes-only flag without `--probes-only` is a STOP; probes-only
never iterates `BASES`.

### 2.2 Preflight (`verify_probes_only_pins`, fail-closed)

- **Exact paper HEAD (MAJOR-1/MAJOR-2, byte-exact).** `verify_paper_head` accepts exactly three identities, branch
  `trackp-p3a-code-20261116` or a detached HEAD (`"HEAD"`), with `b9ad6f8f` still an ancestor:
  1. **C**, the reviewed code commit (`EXPECTED_PAPER_HEAD`; kind `exact_reviewed_runner_commit`);
  2. a **docs-only child of C** whose `r1/` tree is byte-identical (any descendant of C with an identical `r1/`
     tree; kind `docs_child_r1_identical`);
  3. **D**, the mechanical delivery-pin child (kind `delivery_pin_child`): exactly one parent equal to C, the
     runner blob at `r1/scripts/trackp_p3a_guarded.py` **byte-identical** to C's runner blob with the single
     canonical `EXPECTED_PAPER_HEAD = "<C>"` assignment substituted, and no other file under `r1/` changed
     (changes outside `r1/` are allowed only under `docs/`, e.g. this record).
  Nothing else is accepted — not an arbitrary descendant, not an ancestor, not a crafted one-line child, not a
  child that edits another `r1/` file. The old shape rule (one added/one removed line containing the assignment)
  and the stale `8a3d3eaf` docs-child constant are gone.
- **Executing bytes (MAJOR-1/round 2, MINOR-3).** `verify_executing_files` requires the executing runner to be the
  checkout's tracked `r1/scripts/trackp_p3a_guarded.py`, requires C to be an ancestor of HEAD, and requires the 12
  files in `EXECUTING_FILES` (runner, child `r1/scripts/trackp.py`, `trackp_p3a_watchdog.py`, `trackp_p3a_gate.py`,
  `r1/c3/train/run.py`, `types.py`, `model.py`, `exam_run.py`, `trainer.py`, `registry.py`, `serialize.py`,
  `r1/c3/labels.py`) to be **byte-identical to their `HEAD:` blobs**. `git status --porcelain
  --untracked-files=no` is not sufficient, so an `assume-unchanged`/`skip-worktree`/ignored edit or an executing
  copy outside the checkout is refused. Each file's path, sha256 and byte count are recorded.
- **Boot id (MAJOR-1/round 1)**: the current `boot_id` is compared to `EXPECTED_ATTEMPT1_BOOT_ID =
  2c9bb104-…` before root creation/marker/GPU; expected and actual are recorded.
- harness `897d83c8` clean; `r1/c3/train/data/e0_v1.jsonl.gz` sha256 `4f4db29b…`; `r1/c3/rules/p3_rule_v2.yaml`
  sha256 `8c0ef908…`; `r1/scripts/configs/trackp_portal.json` identical to `607e85e:…`; venv freeze equal to
  `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt`; `registry.reverify` clean; tracked
  runner/watchdog/gate/child (`git ls-files --error-unmatch`).
- host `TASL-7`, NVIDIA driver `580.178.04` (kernel/user/package consistency via `tasl7_driver_snapshot`), disk
  free ≥ 10 GiB; `flock ~/r1_locks/gpu0.lock` free; empty GPU-compute census; no other experiment process; no
  `*.active` marker; installed marker helper `~/r1_locks/bin/trackp-evidence` sha256 `f457a04e…`; the 4 Nov
  amendment sha gate (`--authorization-amend-sha256`, additionally re-hashed if the file is present).
- The attempt-1 environment is set if absent and recorded: `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`,
  `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `PYTHONUNBUFFERED=1`.

### 2.3 Marker (`evidence_marker`)

Uses the helper's interface only: `trackp-evidence begin p3a` before GPU work and `trackp-evidence end p3a` in a
`finally` on success or STOP. The job runs directly (`trackp.py` takes its own `flock`); `trackp-evidence run` is
never used (nested `flock`). `marker_begin`/`marker_end` journal events record the exact command, rc, stdout/stderr
and UTC. A failed begin is a STOP before any unit; a failed end is a STOP after the session.

### 2.4 Attempt-1 provenance and the read-only lease-log snapshot (BLOCKING-1)

`build_attempt1_provenance` is called **once at campaign start, before the new root exists**, and reads:

- the pinned attempt-1 journal (`attempt1_journal_facts`): hash, exactly one STOP with a finite
  `gpu_seconds_total`, paper commit/branch/dirty, and `attempt1_boot_id` from `campaign_start` (missing/empty is a
  STOP);
- the **live** attempt-1 lease log `<attempt1-root>/../gpu_lease_log.jsonl` (on TASL-7 exactly `R.LEASE_LOG`) as
  provenance metadata only: `lease_log` path and `lease_log_sha256` are recorded and pinned to
  `EXPECTED_ATTEMPT1_LEASE_LOG_SHA256 = 695050…` by `assert_attempt1_pins`.

**After** `args.root.mkdir()` and **before** any journal/marker/child, `snapshot_attempt1_lease_log` copies those
bytes to `<root>/attempt1_provenance/gpu_lease_log.jsonl` with `O_EXCL`, fsync and mode `0444`, re-hashes the copy,
and records `attempt1_provenance.lease_log_snapshot` (schema `trackp_p3a_attempt1_lease_log_snapshot/v1`):
`path`, `sha256`, `bytes`, `lines`, `source`, `source_sha256_at_snapshot`, `read_only: true`, `mode: "0444"`,
`created_utc`, and the note that the live global log grows during attempt 2 and is never re-hashed at unit starts.
The copy must equal the campaign-start `lease_log_sha256`; a change between campaign start and the snapshot is a
STOP. **Nothing is written into attempt 1.** The only attempt-2 lease-log write is the existing global log via the
child `trackp.py` (unchanged config) and this run's own mirror under the new root.

For each loaded `EVIDENCE/<base>/final/saved`: `saved/manifest.json["files"]` must equal
`final/manifest.json["model_files_sha256"]`, every recorded file is re-hashed from disk (extra **regular** files are
refused; a symlink where a recorded model file is expected fails the comparison), and the block records every
relative path + sha256 + a composite hash. Symlinks found in the directory are recorded (never followed) but an
extra symlink by itself is not refused — the fail-closed guarantee is the recorded-file hash equality. Attempt 1 is
never edited or re-labelled.

### 2.5 Template/version, per-unit sidecar and the unit-start verifier

`<unit>/runner_manifest.json`, schema `trackp_p3a_unit_manifest/v1`, is written after the child exits 0 and after
the child `manifest.json`/`report.json` pass the finite-JSON re-read, before `unit_complete`. The write is atomic
(M6: same-directory temp file, fsync, `os.replace`) and re-read/compared.

- `attempt2_template`: `version` imported from `r1.c3.train.types.PROMPT_VERSION` (must be `trackp_prompt/v1`),
  `version_source: r1/c3/train/types.py:26`, `family`, declared `frame`, `order: history_first`, declared
  `field_order`, `readout`, `encoder`, `wrapper_config`, and the composite `template_id`
  `trackp_prompt/v1/<frame>/history_first/<encoder id>` — the M13 §3.2 block and §3.5 ids.
- `attempt1_provenance`: copy of the campaign provenance (including `lease_log_snapshot`) with a **per-unit**
  `derived_template_id` (the unit's family composite id) and `derived_template_family`; it must equal the unit's
  `attempt2_template.template_id`, the family entry in `derived_template_ids_by_family`, and the reviewed M13 §3.5
  id.
- `attempt1_input` for this unit, `inputs.child_manifest_sha256`, `child_report_sha256`,
  `authorization_amend_sha256`, `cost.gpu_seconds`, `created_utc`; the per-unit template is recomputed from the
  child manifest and must equal the campaign declaration.
- **At each `unit_start`** (M4, BLOCKING-1), *before the child is spawned*, `make_unit_start_verifier` re-reads the
  pinned attempt-1 journal facts (hash, paper commit, boot id, STOP seconds), re-hashes the **immutable read-only
  lease-log snapshot** (sha256 + byte count, and equality with the campaign-start pin), re-hashes every loaded
  attempt-1 `final/saved` file and recomputes the declared template; any drift is a STOP. It never reads or
  re-hashes the live global lease log. The result (template id, composite input hash, journal hash, snapshot
  path/sha256/bytes and an explicit `lease_log_source` note) is recorded in the `unit_start` event.

### 2.6 Budget (`Attempt2Budget`) and the two-unit sequence

- `used = attempt-1 journal gpu_seconds_total (130745.3789889291 s = 36.318161 h) + time recorded in this run's own
  gpu_lease_log.jsonl`. `require_available(projection)` refreshes and refuses a unit **before it starts** if
  `used + projection >= 45 h`; the 60-h P.3a cap is recorded and checked (it includes attempt 1; not extra time).
  Conservative per-unit projections: DRYRUN 600 s, EVIDENCE 1,800 s.
- Exactly two GPU commands, in this order, both `--a3-short` and loading attempt-1 `EVIDENCE/<base>/final/saved`:
  1. DRYRUN `kev-0.8b` probes, `--n-probe 8`;
  2. EVIDENCE `qwen3.5-4b-base` probes, `--n-probe 100`.
  No other base or unit, new directories only, no retry (an existing unit directory is a STOP).
- **DRYRUN `--n-probe 8` rationale (MINOR-4, recorded deviation from the attempt-1-style 32).** The DRYRUN is a
  short path-exercising run, not a replication of the attempt-1 probe sample: attempt-1 probe leases at n=100 were
  67.8–148.4 s, n=8 exercises the same changed argv/A3 path, and the changed path is asserted from the DRYRUN child
  report (`A3.protocol == "v2_budget"` and the exact `A3_descriptive` skipped marker), not from the sample count;
  the real A3/A4/A5 rows are exercised by that same protocol. EVIDENCE keeps the planned n=100. Recorded before
  Unit B as the review requires.
- After each child report `verify_a3_short_report` asserts `A3.protocol == "v2_budget"` and
  `A3_descriptive == {"skipped": "R1-P3A-OOM-OPTION3", "levels": [2000, 8000], "pass": null}` exactly. If the
  DRYRUN report fails, the campaign STOPs and the EVIDENCE unit never starts.

### 2.7 Delivery identity recorded at run time (MAJOR-1/MAJOR-2)

The preflight return (embedded in `campaign_start.pins` and repeated at top level) records: paper HEAD commit,
branch and accepted kind (`exact_reviewed_runner_commit` / `docs_child_r1_identical` / `delivery_pin_child`), the
expected commit C, the base pin and its ancestor check, the boot id expected/actual/match, the executing files block
(paths + sha256 + byte counts, including the runner and the child `trackp.py`), plus the
harness/E0/rule/config/freeze/registry/host/driver/disk/lease/marker/census records. `campaign_start` also records
`attempt1_boot_id_match` as the **computed** comparison `pins["boot_id"] == provenance["attempt1_boot_id"]`
(MINOR-5). `run_probes_only_campaign` re-checks the current boot id against the attempt-1 journal's recorded boot id
before creating the root.

### 2.8 Golden template vector (M1)

`test_golden_field_order_from_the_pinned_renderers` always runs: it renders the pinned Qwen
`BinTokenWrapper.prefix`/`segments` with a deterministic stub tokenizer, asserts the token positions of state →
proposal → question → bins → belief → action, and compares them to `FRAMES`; it also checks the pinned Kev
`PointerWrapper.records` layout and the declared Kev decide token. The real **token-id** golden vectors (M13 §3.2)
are separate tests: they use the pool tokenizer for `qwen3.5-4b-base` and the installed Kev encoder, and **skip
with an explicit reason** when absent locally. On TASL-7 they must be re-run (part of acceptance, §5). The local
limitation is recorded in §6.

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
45 passed, 2 skipped

$ PYTHONPATH=. pytest r1/tests/test_trackp_p3a_guarded.py -q     # pre-existing suite
5 passed, 4 failed

$ PYTHONPATH=. pytest r1/tests/test_trackp_cli.py -q
9 skipped
```

The 2 skips are the real tokenizer/Kev golden vectors: `test_golden_token_ids_qwen_from_the_pool_tokenizer` (pool
tokenizers not in the local HF cache; skip message names the missing import) and
`test_golden_token_ids_kev_from_the_pinned_encoder` (`pytest.importorskip("kev")`). The source-level golden vector
and every other new test run.

**The 4 `test_trackp_p3a_guarded.py` failures are pre-existing and environmental, not caused by this work.** They
are the real-subprocess tests, which reach the pin's `worker_parent_death_guard` `preexec_fn`
(`ctypes.CDLL(None).prctl(PR_SET_PDEATHSIG)`); macOS has no `prctl`. Identical `5 passed, 4 failed` on the
unmodified baseline. `test_trackp_cli.py` skips because the pool tokenizers are not in the local HF cache.

**Round-2 test coverage added.** `test_blocking1_unit_start_verifies_the_immutable_snapshot_not_the_live_global_log`
builds a host-shaped synthetic attempt-1 root (root directly under the runs directory, so its parent lease log is
the live global log), snapshots it, passes the DRYRUN start, appends a fake lease pair to the live log, and passes
the EVIDENCE start; then tampers the snapshot and asserts a STOP, and asserts the attempt-1 tree's content hash is
unchanged (no writes into attempt 1).
`test_snapshot_refuses_a_live_lease_log_that_changed_since_campaign_start`, the end-to-end
`test_campaign_runs_exactly_dryrun_then_evidence` (which now has the fake DRYRUN append its lease pair to the live
log before the EVIDENCE verifier runs and asserts the snapshot block + both unit-start snapshot hashes),
`test_verify_paper_head_accepts_only_the_three_reviewed_identities` (genuine pin accepted byte-exactly; crafted
injected-code child refused; pin-shaped child with an `r1/` code edit refused; ancestor and descendant refused), and
`test_verify_executing_files_pins_the_executing_bytes_to_head` (dirty edit, `assume-unchanged` edit invisible to
`git status`, foreign copy and missing file all refused) are new/changed this round.

**What could not run locally:** the real probes (TASL-7 venv, pool tokenizers/model files, GPU), the
DRYRUN/EVIDENCE children (stubbed), the live preflight/marker/lease/`nvidia-smi` paths (TASL-7-only; internals are
stubbed and unit-tested), the tokenizer/Kev token-id golden vectors (skipped with a reason), and the
tokenizer-dependent Track P CLI dry-run suite. Every changed file is `py_compile` clean.

## 4. Fail-closed STOP list

A3-short delta: `a3_short` with `counters=None` (ValueError); CLI `--a3-short` without `--budget`; CLI
`--a3-short` with `--tiny`; `--a3-short` on any non-`probes` subcommand (argparse error).

Probes-only runner: missing/invalid `--probes-only` args; wrong `--base`; relative `--attempt1-root`; relative/
existing/dangling-symlink/mis-named/non-UTC root; a root not directly under the runs directory; attempt-1 root
reused or nested; non-`TASL-7` host; **paper HEAD not exactly one of {C, a docs-only child of C with identical
r1/, the byte-exact delivery-pin child D}, wrong branch, or arbitrary descendant/crafted child**; **executing
runner outside the checkout or any executing file differing from its `HEAD:` blob (dirty/untracked/ignored)**;
`git ls-files` untracked scripts; dirty paper; paper base pin not an ancestor; harness pin/dirtiness;
E0/rule/config/freeze/registry mismatch; driver mismatch; **current boot id ≠ attempt-1 boot id**; low disk; held
lease; non-empty GPU census; another experiment process; another `*.active` marker; missing or wrong marker helper;
attempt-1 journal/lease-log missing, wrong sha256, no/duplicate STOP, non-finite or changed GPU total, missing or
changed boot id; **a lease log that changed between campaign start and the snapshot; a missing, resized or tampered
lease-log snapshot at unit start**; attempt-1 loaded directory missing/unrecorded/tampered/extra regular
file/symlinked recorded file; family/frame/wrapper-config/PROMPT_VERSION/Kev-encoder/transformers template drift;
**unit-start attempt-1 journal/input/template drift**; per-unit template or per-unit provenance template-id
disagreement with the campaign declaration; 45-h projection crossing or 45-h/60-h reached; unit directory already
existing (no retry); child failure rc≠0; missing or incomplete lease record; label/boot mismatch; non-finite child
report/manifest; DRYRUN report not showing the budget-v2 path / skipped marker; failed marker begin or end; any
unexpected unit/base in the sequence. Every STOP preserves outputs and emits a STOP journal record (when the
journal exists); there is no bare `trackp.py probes` fallback.

## 5. What the reviewer must check

1. **A3 delta (`3833d93e`)** — unchanged. `git diff b9ad6f8f..3833d93e` is flag/tests-only; flag-off is
   call-for-call identical; the flag is probes-only and refused without `--budget`/on `--tiny`.
2. **Runner fixes (C).** `git diff 7c9e8b08..C -- r1/` is confined to the runner; check the byte-exact pin child
   (`_delivery_pin_child`/`expected_pin_runner_blob`), the executing-bytes check, the docs-only-child rule, the
   read-only lease-log snapshot and the unit-start verifier that reads only the snapshot/journal, the computed
   boot-id match, and the `attempt1_provenance.lease_log_snapshot`/`executing_files` records.
3. **Tests.** Re-run §3 in a full TASL-7 environment; the tokenizer/Kev golden tests must run there, and the 4
   real-subprocess supervisor tests are Linux-only and must pass there. Confirm the new tests need no
   model/tokenizer/GPU/host.
4. **Boundaries.** Confirm `git diff 7ae4d2ea..D --stat` touches only the three files in §0, no A3-short file, no
   `main` merge, no config/rule/E0/data/model change, no deletion, no push.
5. **Delivery pin / exact commit (MINOR-2/MINOR-1).** 
   - The **reviewed code commit is C = `5b7ad0cb7fedd083bad457968dc3dd3e920ac154`**; **D** is its direct child and
     the **only runnable delivery**: the host checks out **exactly D** — detached HEAD or on branch
     `trackp-p3a-code-20261116`, clean — and nothing else. D differs from C by exactly the one canonical
     `EXPECTED_PAPER_HEAD` assignment to C plus this record.
   - C alone is refused: C's own script still names `7c9e8b08` in `EXPECTED_PAPER_HEAD` (self-pin cycle). Do not
     check out `3833d93e` (predates the runner) or `8a3d3eaf` (predates the fixes).
   - Accepted set: exactly {C; a docs-only child of C whose `r1/` tree is byte-identical; D byte-exact}. The
     docs-only-child branch is a function-level identity only: because the executing files must equal the `HEAD:`
     blobs and the pin lives in those bytes, a clean checkout can only run D. Any commit made on top of D (for
     example a review record) changes `HEAD` and makes the branch HEAD unacceptable while D remains runnable; review
     records therefore go to the ops branch, and this branch stays at D.
   - The branch is local/unpushed; delivery also needs it transferred to TASL-7 (push/fetch/bundle). The host paper
     checkout moves off `trackp-20261026`/`b9ad6f8f` to D (no merge of `main`), with `b9ad6f8f` still the ancestor
     pin.
   - **Commits under review / to be recorded after review.** The preflight records the actual HEAD + accepted kind
     and the executing-file sha256.
6. **A6 / run authorization.** `R1-TRACKP-A6-DEFER` (author decisions @ `65d8d5bb`) defers A6 for attempt 2 and
   requires the P.3a report to disclose the A6 deferral and the 2k/8k descriptive-level omission; attempt 2 does no
   A6 work, and any P.3b serialization-order change needs a separately reviewed A6 unit. A green preflight is **not**
   a run authorization: Unit B still needs the Unit A execution record and the delivery/run authorization per the
   accepted plan.

## 6. Residual risks / interpretation points

- **Exact-commit pin vs. the pin commit (MAJOR-2).** The pin cannot contain its own sha; §0/§5.5 record the
  two-commit delivery mechanism (C then D), the byte-exact acceptance rule and the exact checkout (D). Any later
  code change requires a new reviewed code commit and a new pin child; no other descendant is accepted.
- **Docs-only-child acceptance is theoretical only (MINOR-1).** The stale `8a3d3eaf` constant is gone and the rule
  is re-based on C, but a clean checkout cannot satisfy both "executing files == `HEAD:` blobs" and "pin line names
  C" except at D. The record states this rather than implying a docs-only child can be run; post-review records go
  to the ops branch.
- **Lease log location (BLOCKING-1).** Attempt 1's lease log is the global `~/r1_trackp/runs/gpu_lease_log.jsonl`
  (= `<attempt1-root>/../gpu_lease_log.jsonl`); the child keeps writing it (unchanged config), so the runner reads
  it once at campaign start (hash + read-only snapshot) and then only ever re-hashes the snapshot. The new root's
  own `gpu_lease_log.jsonl` is the attempt-2 budget mirror, not the attempt-1 provenance. The snapshot is
  read-only (`0444`) and inside the new root; nothing is written into attempt 1.
- **Golden token-id test limitation (M1).** Locally only the source-level golden vector runs; the real pool
  tokenizer and installed Kev encoder are absent, so the two token-id tests skip with an explicit reason. They must
  be run on TASL-7 before run acceptance (§5.3). If neither can produce a vector there either, the M13 §3.2 golden
  requirement is unmet and the run must not start.
- **Marker left by SIGTERM/`kill -9` (M5).** The marker end runs in a `finally`, but a SIGTERM/SIGKILL of the
  supervisor (or power loss) can by definition skip it, leaving `~/r1_locks/p3a.active` and no journal STOP. This is
  fail-closed: the next preflight's `*.active` check refuses to start. Recovery is manual after inspection: run
  `~/r1_locks/bin/trackp-evidence end p3a` and verify the lease/journal state; outputs are preserved. The runner
  never removes another marker automatically.
- **M13 derivation sha.** `M13_ORDER_RECORD_SHA256` records the M13 record bytes as delivered on 16 Nov
  (`351611c5…`); it is provenance data (the record is not on the host checkout, so it cannot be re-hashed at run
  time). If the M13 record is amended, regenerate this constant before the run.
- **Derived attempt-1 template ids** are pinned from M13 §3.5 and cross-checked against the live sources: the Qwen
  id requires the installed `transformers` version to be exactly `5.19.0` and the Kev id requires the installed Kev
  commit `2074cc44…`; drift is a STOP, which is intended.
- **Kev encoder hash** is computed from the installed `kev/model.py` (dist-info `direct_url.json` commit): attempt 1
  recorded no such hash, so the attempt-2 sidecar records the current installed hash (M13 R2 limit).
- **`ps`-based foreign-process census** is heuristic (pattern list, own pid/ppid excluded); it is one of several
  independent STOPs (lease, GPU census, markers).
- **Local test coverage gap** described in §3: real child execution, live preflight and the marker helper are
  TASL-7-only and were not run by this unit. The `v2_budget`/A4/A5 path is locally covered by the stubbed tests and
  is re-asserted at run time from the child reports.

**No host was contacted, no GPU command was run, nothing was pushed, `main` was not merged, no deletion was made,
and attempt 1 was only read (through its exported inventory).**
