# STOP — screening evidence run: worker-runtime probe rejects the `python`/`python3` alias

**Task:** `compute/20261127-22` (PLAN R1-SCREEN-MEASURE-SIGNATURE). **Result: STOP at the first
worker-runtime probe; 0 of 10,164 runs written.** The scene is kept; nothing was resumed, patched or
retried.

## Launch and scene

- **Note:** `docs/r1/authorizations/screen_measure_20261127.md`, `approved: true`, on `main` `840ad01d`;
  companion `docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_20261127.md`.
- **Code:** `e153df24ee3435bbe0b2fa994297b15250550c30`, clean checkout at
  `/work/dwong/screen_measure_20261127/paper`, ancestor of published `main`.
- **Host:** `deepthought`, 16 workers, CPUs only.
- **Environment:** batch venv `/ceph/dwong/r1_prepare_20261025/venv` (Python 3.13.15, scikit-learn
  1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3); `AR_HARNESS_ROOT` = the e1 batch harness at
  `6adf3859de66c4814fcf376eed59880fbd8eeaf7` (tracked-clean, 5 known untracked files).
- **Launch command (exact note command, via `run_screen.sh`):**

  ```
  python -B -m r1.noise.screen_measure run --evidence \
    --out results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1032Z \
    --workers 16 --tmp /tmp/r1_smeas_EVIDENCE_20261127T1032Z \
    --paper-root <checkout> \
    --note docs/r1/authorizations/screen_measure_20261127.md \
    --code-commit e153df24ee3435bbe0b2fa994297b15250550c30 \
    --code-review docs/r1/reviews/SCREEN_MEASURE_SIGNATURE_REVIEW_20261127.md \
    --data-cache /work/dwong/screen_prep_20261126/data_cache_ENG_20261127T0417Z
  ```

- **Output:** `/work/dwong/screen_measure_20261127/paper/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1032Z/`
  (`design.json`, `lineage_runs.jsonl` 0 bytes, `manifest.json`, `cotenancy.log`).
- **Scratch:** `/tmp/r1_smeas_EVIDENCE_20261127T1032Z` (empty, kept).
- **Copies:** `docs/r1/reports/screen_measure_stop_20261127/` (byte-identical; `SHA256SUMS`).

| File | sha256 |
|---|---|
| `cotenancy.log` | `ca1794717c6429d46d64ad3e4003dd2a73e04bb04003311095b0a6a2c7f272fa` |
| `design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `lineage_runs.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) |
| `manifest.json` | `0e8113898291d6d04b289f84aea8f27b91df96f08d92d1324093dad2f77a7142` |

## The STOP

`manifest.json` records:

```
"stop": "worker_runtime digits_mlp c12 3301: STOP: worker interpreter, versions, or package list mismatch",
"planned_runs": 10164, "written_runs": 0, "failed_runs": 0, "elapsed_seconds": 0.5
```

The strict preflight (published note, pre-declaration, PLAN row, code provenance, environment,
harness equivalence, seed block, co-tenancy) **passed**; the stop came at the first per-run worker
probe, before any run was written.

**Exact mismatch (read-only reproduction of the probe).** The expected vs observed values differ
only in the literal interpreter path:

| Field | Expected (the audit process) | Observed (the worker's `python3`) |
|---|---|---|
| `worker_python` | `/ceph/dwong/r1_prepare_20261025/venv/bin/python` | `/ceph/dwong/r1_prepare_20261025/venv/bin/python3` |
| `prefix` | `/ceph/dwong/r1_prepare_20261025/venv` | same |
| `versions` | sklearn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3 | same |
| `package_list_sha256` | `a089bbf1fc7522a596631f4dd9535a18866336ff18edbbae14932106d94f16d3` | same |

The probe resolves `python3` on `PATH`; the launch process was started with `python`. Both are
symlinks to the same interpreter (`worker_python_realpath`
`/ceph/dwong/r1_prepare_20261025/python/cpython-3.13.15-linux-x86_64-gnu/bin/python3.13`). The probe
compares `sys.executable` literally, so the alias name is the whole difference. This is exactly the
B4 (a) worker-runtime limitation the note discloses; under the note it is a STOP.

## What was not done

- No retry, no alternate `PATH`, no edit to the note, probe, spec or environment, and no output or
  scratch deletion. `lineage_runs.jsonl` is empty; no harness run started.
- No label, evaluation, test-partition, sealed or sweep-evidence file was opened.
- No other task was started on deepthought in this line; the 16 workers were never launched.

## Decision needed (author/coordinator)

The signed note's launch command and the reviewed probe disagree on the interpreter's literal name.
A re-issued note/command that starts the audit with the same name the probe resolves, or a reviewed
probe change that compares `worker_python_realpath` (and keeps the prefix/version/package checks),
would clear this. Either changes a signed document or the code at `code_commit`; it is not an
operator patch. **Recommendation:** a reviewed probe fix to compare the real path (the environment is
identical), then a new note revision and a new `SMEAS_EVIDENCE_<stamp>` run; the kept scene stays as
the STOP record. Screening remains unmeasured, so the seventh-arm decision is not reached.

**Task id:** `compute/20261127-22`. **Branch/tip:** `compute-screen-measure-stop-20261127` @ this
commit. **Tests:** none (the run stopped before a harness run); the strict preflight passed and the
manifest records the stop. **What happens next:** STOP to the author; no retry until a re-issued
note or reviewed probe fix.
