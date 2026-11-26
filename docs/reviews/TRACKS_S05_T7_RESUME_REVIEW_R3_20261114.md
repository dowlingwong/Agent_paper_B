# Independent review, round 3 — Track S `digits_mlp` S0.5 resume unit (rev 3b), 14 November 2026

**Reviewer.** Fresh and independent; I did not write the unit, the reviewed launchers, the pause record or the reports.
I read a `/tmp` clone only. The TASL hosts are unreachable in the author's VPN window and I was told not to attempt
access, so **no host access was made and nothing was executed**; every host-side check below is an execution
precondition. Nothing under `/Users/wongdowling/Documents/agent_paper_B` was modified; only `/tmp` and this file were
written.

## Unit reviewed

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030` (remote head and local
  `origin/trackS-ops-20261030` both at the tip), tip **`5e0cdded41a08daecb803f815bba1cbcc8a10e45`** ("Track S S0.5
  resume unit rev 3b (cleanup of the round-2 text fixes)"), tree `628ba3f6cc69fa2686886328fa81eb7d5b2a90eb`; parents
  `ec80ba2a` (rev 3, review-round-2 fix), `8545f7e5` (B1 `_d` review records), `d7992019` (rev 2, the version round 2
  actually reviewed), `491e1241`, `2c60b300`.
- `docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md`: blob `e330bf63b355669f8b12722be86cbccfb7c8c002`, **73 lines,
  6955 B, sha256 `898039a8b7770a29bf6301ff68e3296957da802cace7aa74659cd4e3e2575a17`** — matches the pinned hash.
- Commit scope: `5e0cdded` changes **one file** (+6/−4, two hunks); `ec80ba2a` one file (+16/−9). No code, pin, STATUS
  or runbook byte change, no secret, non-executing.
- Bytes the unit relies on, re-hashed in the clone: launcher `tasl7_digits_s05_20261113.sh`
  `3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151`; `tasl7_digits_s05b_20261113.sh`
  `3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a`; `r1/tracks/ops/trks-run`
  `b53bc811dc177000c27d33dc43f5f964954c15d7981c5705ad7fcadb851064c4`; `r1/tracks/collect.py`
  `d09cf1f4e1ce6fc6964b4e70a78a968279fa777be839c00c30f1a0f1398364d5`.

## Round-2 findings, checked against rev 3b

| # | round-2 finding | result |
|---|---|---|
| 1 | Major: copy-back `$RUN/sp05*` glob matches nothing, ledgers dropped | **fixed** (rev 3; §2 lines 60–63) |
| 2 | Minor: scene check imprecise — snapshots at `$WORK/roots/<id>/snapshots`, `done.status=paused` unasserted | **partly fixed**: counts/`paused`/dedup fixed, **snapshot path removed again** — F1 |
| 3 | Minor: `.cmd` tolerance not implementable | **fixed**: byte-identical required, any difference = STOP (line 46) |
| 4 | Minor: collector session misnamed | **fixed**: outer session `trks_s05t7resume`, collector `trks_s05_t7` (§1.3) |
| 5 | Minor: only exit 2 triggers cleanup | **fixed**: any non-zero (2, 3, other) → kill own `trks_llm`, pkill own servers, verify lease, report (§1.4) |
| 6 | Minor: rc=0 + non-complete unhandled | **fixed**: report and wait for the author; no S0.5b, no silent restart (§1.6) |
| 7 | Minor: λ/obs-inflation implicit | **fixed in substance**: §0.4 states both fixed by the reviewed launcher; launcher argv (`:77`) passes `--obs-inflation 1.0`; `collect.py` `MANIFEST_KEYS` (`:1275–1280`) + resume refusal (`:2092–2094`) make a changed value a hard `SystemExit` |

## Verification of the four requested items

1. **Copy-back (round-2 MAJOR) — PASS.** §2 names `$RUN/s05_calibration.jsonl` and `$RUN/s05b_truncated.jsonl`
   ("both must exist"), the other run `*.jsonl` ledgers (`roots`/`forks`/`leaves`/`failed_units`/`audit_runs` as
   present — all real filenames, `collect.py:1254,1653,1644,717,910`), the manifest, the run's logs and `SHA256SUMS`, to
   the **new** `results/r1/tracks/digits_mlp/s05_t7_20261113/` (not the TASL-2 scene), with "assert each named file
   exists before copy". The `sp05*` glob survives only as a historical note that it matched nothing; no glob is used.
2. **Minors — PASS except F1.** §0.2 asserts counts 22 roots / 6 forks / 0 leaves / 0 failed / 0 exhausted and
   `done.status=paused`, with the duplicated parenthetical gone; `.cmd` byte-identical; outer-session wording coherent
   (launcher hardcodes `SESSION=trks_s05_t7` at `:13`, and `trks_s05t7resume` is *not* a prefix of `trks_s05_t7`, so it
   cannot collide with the launcher's `has-session` guard); any launcher non-zero has the cleanup clause; rc=0
   non-complete waits for the author; `obs-inflation 1.0`/λ₂ stated as fixed; `trackS-ops-20261030`; TASL-2-return
   census-only; STOP table has exit-3-twice-in-a-row with the forced-pause exception, the 5-day GPU cap, and the
   calibration-gate-twice STOP (the Phase-4 λ gate; λ₂ itself is only in §0.4 — acceptable for a resume); no-deletion
   rename recorded; post-`mv -n` verification; Mac-local capture with `SHA256SUMS`.
3. **Diff scope — PASS.** rev 3 → rev 3b is one file, +6/−4, exactly two hunks: the §0.2 dedup and the §1.4
   exit-2/3 cleanup. rev 2 → rev 3 is one file, the round-2 fixes; `8545f7e5` adds only the two B1 `_d` review
   records. No code/pin/STATUS change, no secret, non-executing.
4. **Runtime — no defect in an executing step.** The one failing item is a precondition-text regression (fail-closed),
   below.

## F1 — Minor, blocking for this confirmation: §0.2 no longer names `$WORK/roots/<id>/snapshots`

Rev 3 had "the per-root snapshots live under `$WORK/roots/<id>/snapshots`" inside a duplicated parenthetical. Rev 3b
deleted that parenthetical **and the path**, leaving "`$WORK=…` (snapshots and `roots/<id>/root_trials.jsonl`; …)".
That reads as if snapshots sit directly under `$WORK`. `collect.py:839` puts them at `root_dir/"snapshots"`, i.e.
`$WORK/roots/<id>/snapshots`; `$WORK` itself contains only `roots/`. This is the exact rev-2 wording that round 2 (F2)
called a false-STOP trap for a literal checker, and the requested fix (`$WORK/roots/<id>/{root_trials.jsonl,snapshots}`)
is absent. The rest of §0.2 (counts, `paused`, no duplication) is correct.

*Fix (one line):* in §0.2 write "`$WORK=…` (`roots/<id>/root_trials.jsonl` and `roots/<id>/snapshots`; the
leaves/S0.5b inputs live under `$WORK`, not `$RUN`)" — or keep rev 3's sentence and drop only the duplicated `done`
clause.

## Notes (not needed for the fix, but worth carrying)

1. The title still says "rev 3" while the commit is rev 3b; bump it on the same edit (the file hash changes, so any
   downstream pin must be updated).
2. §2 "the run's logs (collector `.log`/`.cmd`/`.exit`, launcher log/rc)" does not name the S0.5b records:
   `$R/logs/s05b_t7_20261113_launch.log` and `trks_s05b_t7.{log,cmd,exit}`; the launcher writes its log but not its own
   rc, so "launcher log/rc" has no host path unless the operator tees the rc. Name both in the copy list.
3. Round 2's suggested `len(sessions)==1` assertion is still absent; optional, the counts + `paused` already pin the
   scene.
4. The `$RUN` "mtime <= 13:03:00Z" fallback baseline remains tight (manifest rewritten after `end_utc`); the pause
   capture is the primary evidence, as the unit says.

## Conclusion

The round-2 MAJOR is fixed and every other round-2 minor is fixed or fixed in substance; nothing remaining would fail
in an executing step. One text regression in §0.2 (the fork-snapshot path) is exactly the imprecision round 2 asked to
remove, so the exact bytes are not yet the confirmed unit. After that one-line fix, the unit is ready for execution
after the preconditions.

VERDICT: changes required
