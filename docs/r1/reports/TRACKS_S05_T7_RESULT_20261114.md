# Track S `digits_mlp` S0.5 pilot on TASL-7 — resumed run result (14 November 2026)

**S0.5 complete; S0.5b complete; descriptive report; L1 pause. STOP 4 / the S0.5 summary still wait for
`tabular_mlp`.** Engineering only; no run-quality claim. The TASL-2 S0.5 scene was not touched.

## 1. Run
- Pause: 2026-11-13T13:03:00Z (watch-triggered STOP on the B1 `_d` marker), scene `out/digits_mlp/s05_t7_20261113`
  with `sessions[0].done` = 22 roots / 6 forks / 0 leaves / 0 failed / 0 exhausted, `status=paused`.
- Resume under the reviewed rev-5 unit: STOP renamed (not deleted) to
  `_to_delete/STOP.retired.20261114T103527Z` (0 B, inode 57048847, sha `e3b0c442…`); launcher sha `f823b86a…`
  (the `LIVE` guard fix) started k=2 servers (18101/18102) and the collector `trks_s05_t7`; `trks_s05_t7.cmd` was
  byte-identical to the paused run (sha `fe9fae36…`, 786 B). **First attempt** with the previous launcher revision
  `3e957464…` aborted rc=1 before starting anything (the `pgrep|pipefail` guard bug); that attempt is recorded in the
  resume unit; nothing was started and the STOP had already been renamed.
- S0.5 exit: `2026-11-14T12:34:03Z rc=0`; `sessions[1].done` = 28 roots / 18 forks / 71 leaves / 0 failed /
  0 exhausted / `deadline_hit=false` / `status=complete`.
- Servers stopped (`tmux kill-session trks_llm`, own `llama-server .*--port 1810[12]` gone; `gpu0.lock` free). S0.5b:
  `2026-11-14T13:00:39Z` start → `13:00:54Z rc=0` (CPU; manifest complete and no servers as required).
- Ledger totals across both sessions: roots **50** (all `ok`, 0 errors), forks **24** (5 A/A), leaves **71** (all `ok`),
  0 failed/exhausted, deadline not hit.

## 2. Calibration summary (`s05_calibration.jsonl`, 298 rows, level 0.8, k=5 audit seeds)
Overall coverage 231/298 = **0.7752** (nominal 0.8). Notable strata (covered/total): GOOD `HIDDEN_UNITS +, stratum 0`
0/20; `BATCH_SIZE +, 1-2` 20/40; `HIDDEN_UNITS +, 1-2` 31/40; `HIDDEN_UNITS +, >=3` 75/75;
`LEARNING_RATE_INIT -, stratum 0` 5/11. `delta_audit` mean −0.0074 (min −0.4123, max 0.1922). Descriptive only; the
aggregate gate is a Phase-4 decision with `tabular_mlp`, not inferred here.

## 3. Truncation summary (`s05b_truncated.jsonl`, 200 rows)
W ∈ {8, 10, 12, 20}, binding true/false, policies `a2u` and `static:0.00198,0`, reps 0/1. Cap binding is visible at the
higher W: `runs_used / trials` = 8/8 (W8), 10/12 (W10), 12/22 (W12), 16/40 (W20); mean `y_terminal` by W =
0.963097 / 0.968334 / 0.970830 / 0.972802.

## 4. Copy-back (this commit)
`results/r1/tracks/digits_mlp/s05_t7_20261113/`: `roots.jsonl`, `forks.jsonl`, `leaves.jsonl`, `audit_runs.jsonl`,
`manifest.json`, `s05_calibration.jsonl`, `s05b_truncated.jsonl`, `_to_delete/STOP.retired.20261114T103527Z`, run logs
(`logs/`: collector `.log`/`.cmd`/`.exit`, S0.5b logs, launcher stdout/rc for both attempts), the two reviewed launch
scripts (`scripts/`), and `SHA256SUMS`. Key shas: roots `039b6955…`, forks `bf638fa6…`, leaves `427faff6…`,
calibration `2e4c9a8c…`, truncated `cd296fd8…`, manifest `68a0d6e0…`; the collector log is 1,617,214 B (uncompressed;
not truncated).

## 5. Limits
One host, ENGINEERING_ONLY, descriptive calibration/truncation only; the S0.5 summary and STOP 4 are deferred until
`tabular_mlp`; B2/X.7/sweep 2 are not started; TASL-2 was not reachable and its scene is preserved (read-only census
only, no resume). L1: pause after this report and wait for instructions.
