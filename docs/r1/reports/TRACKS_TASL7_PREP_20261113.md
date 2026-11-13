# Track S `digits_mlp` on TASL-7 — prepared launch units (13 November 2026)

**Candidates for independent review; nothing here is executed by this record.** These three units implement the
approved host move (`reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` rev 2, accepted) for `digits_mlp` on TASL-7:
Phase-1 S0.1, Phase-4 S0.5 and Phase-4 S0.5b. They are committed together so the review covers the exact bytes that
will run; they are executed only after B1 `_c` ends normally and the accepted post-run unit
(`proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`) has retired the marker and documented it.

## Shared preconditions (all fail-closed)

1. the `_c` marker retired by the accepted STOP-case unit (the actual STOP path taken); `~/r1_locks/trackx_evidence.active` absent; Track P marker
   absent; `$R/trks_drill.active` absent; no foreign GPU job; lease `~/r1_locks/gpu0.lock` free.
2. TASL-7 paper checkout `$R/work/Agent_paper_B` fetched from the TASL-7 bare repo (branch
   `mac-tracks-a2u-stale-20261111`, which contains `8237fd02`) and checked out **detached at pin
   `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`**, clean; harness `$R/work/autoresearch_harness` at `a3fedbb` clean.
   `trks`/`trks-run`/`trks-servers` inject `HOST_LABEL=TASL-7`, GGUF sha
   `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`, llama build `620d2225…`.
3. Prior `a2u_prior_r2_20261111.json` (sha256 `5c849d15…`) copied to `$OUT/a2u_prior_r2_20261111.json` from the Mac
   copy in `results/r1/tracks/digits_mlp/s04_rerun20261111/`; the S0.5 script refuses any other digest.
4. The S0.1 **result** is independently reviewed before S0.5 (k decision and the host/venv facts are recorded);
   S0.1 failure is STOP for the author.
5. Track P stays paused, Track X is not touched, the TASL-2 `s05` scene is never contacted, resumed or deleted.

## Unit digests

```
c1deee130d8d67b495c4dcf2ad2b46b37153a6ae33224754e7b0e4f1be99c0f8  r1/tracks/ops/launch/tasl7_digits_s01_20261113.sh
# revised 13 Nov (reviewed): accepts S01_SUFFIX so the operator-error re-run uses s01_t7_20261113b and leaves the
# preserved empty s01_t7_20261113/ untouched; the other two digests are unchanged.
3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh
3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a  r1/tracks/ops/launch/tasl7_digits_s05b_20261113.sh
```

## Units (all under `r1/tracks/ops/launch/`)

- `tasl7_digits_s01_20261113.sh` (sha256 below): requires `trks_llm` running **k = 2** (started separately with
  `tmux new -d -s trks_llm $R/bin/trks-servers 2` per rev-3.3 Phase 1), waits for both endpoints, runs the serial and
  concurrent probes in their own `trks-run` sessions (`s01_t7_20261113/serial.json`, `concurrent.json`), and checks
  both rcs. k decision: 2 if within-server identity is 100 % on both URLs and cross-server identity 100 %; else 1 if
  the serial run is 100 %; else STOP.
- `tasl7_digits_s05_20261113.sh`: `K` servers (default **2**, the TASL-7 S0.1 decision) in `trks_llm`
  (`trks-servers $K`); waits for endpoints 18101..1810K; refuses a running `trks_llm` whose live server count != K; `$OUT/digits_mlp/s05_t7_20261113` and `$WORK/digits_mlp/s05_t7_20261113`; session `trks_s05_t7`;
  the same rev-3.3 Phase-4 command (W 40, 20 instances, `--policy static:0.00198,0`, `--obs-inflation 1.0`,
  `--prior-sha256 5c849d15…`, `--deadline 28800`, `--stop-file $RUN/STOP`, `--label ENGINEERING_ONLY`); a
  manifest-less existing `$RUN` refuses (not resumable), a manifest-bearing one is a resume of that directory.
- `tasl7_digits_s05b_20261113.sh`: CPU-only; refuses any `trks_llm`/`llama-server` still running; requires
  `$RUN/manifest.json` with `sessions[-1].done.status == "complete"`; runs the Phase-4 S0.5b collector
  (`--truncate-W 8,10,12,20`) in session `trks_s05b_t7`; waits and checks the exit code.

## After the run (copy-back, report, review, pause)

Copy `$RUN` (calibration/truncation JSONL, manifest, SHA256SUMS) to
`results/r1/tracks/digits_mlp/s05_t7_20261113/` on the Mac (never to the preserved TASL-2 `s05` path), write the
report + STATUS, obtain a fresh independent review, then pause and report per L1. The S0.5 summary and STOP 4 still
wait for `tabular_mlp`.

## STOP conditions (in addition to the Track S runbook §10 and the host-move record)

S0.1 identity < 100 % in both settings; k decision impossible; calibration gate twice; more than 2 % failed units in a
phase; exit 3 twice; A/A or fork-rebuild mismatch; a priority marker appears (watcher pauses, resume later, not a
failure); any pin/host-facts mismatch; any GPU/lease anomaly; any deviation from the reviewed bytes; any request to
touch the TASL-2 scene.
