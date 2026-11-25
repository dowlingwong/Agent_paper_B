# Captures — T1 expansion candidate 1, MLGym Titanic kit (25 November 2026)

Evidence for `../TITANIC_KIT_20261125.md`. Kit branch `mac-trackg-titanic-20261125` @
`3a67042ba7e4211feb9681524f3879643c8cf635` (pushed to `origin`; no PR). Host: TASL-2.

| File / dir | What it is |
|---|---|
| `git.txt` | branch, tip, base (`origin/mac-trackg-t1-tasl-20261121` @ `c025f89`), remote ref, committer, the committed `git ls-tree` of the kit |
| `pins_final.txt` | node_spec_sha256, spec-file sha256, committed pin (from `git archive HEAD`), deployed pin, edits/data manifest shas, env freeze sha, budget/isolation fields |
| `pins.txt` | per-frozen-file sha256 table and the committed/deployed pin computation output |
| `kit_files_sha256.txt` | sha256 of every committed kit file (from `git archive HEAD`) |
| `spec/mlgym_titanic.yaml` | the node spec |
| `edits/` | E1–E4 diffs and the declared edits manifest |
| `data_manifest/data_manifest.json` | the setup's hashed data manifest |
| `env/` | `torch312` freeze (sha256 `d2e70fe4…`, 77 packages), its sha and the Python version |
| `test_logs/` | static port tests, full port tests (incl. synthetic smoke), isolation tests, G.1b noise-floor tooling tests |
| `smoke/checklist_e_cpu_smoke.log` | the checklist-E CPU smoke log with `CHECKLIST_E_PASSED mlgym_titanic` |
| `smoke/smoke_summary.json` | compact per-run smoke summary (outcome, elapsed, isolation, pin) |
| `smoke/smoke_ledger.jsonl` | the stub manager's raw ledger (full run records) |
| `smoke/synthetic_smoke_summary.json` + `synthetic_smoke/titanic_run_records/` | the synthetic-data smoke records of this node (random tables, reduced budget) |
| `kit_docs/` | copies of the node's `LICENCES.md` and `README.md` |
| `commands.txt` | the command set used on TASL-2 |
| `SHA256SUMS` | sha256 of every file above |

Evidence roots on TASL-2 (not copied in full): data
`/home/dowling/r1_engineering/titanic_20261125/data/mlgym_titanic` (manifest sha256
`c8ccedd0…`), smoke runs `/home/dowling/r1_engineering/titanic_20261125/cpu_smoke_runs`, kit worktree
`/home/dowling/r1_trackp/wt/titanic-20261125`. The earlier smoke attempt stopped by the E4 draft bug is kept
aside at `/home/dowling/r1_engineering/titanic_20261125/cpu_smoke_runs_attempt2_e4_nonfinite`.
