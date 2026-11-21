# Errata to the autoresearch U2 result (`U2_ISO_AUTORESEARCH_RESULT_20261121.md`, sha256 `8f872f2da42ad6256ac037e5aca267be295d4063edd1ae473e74c7ae47be4d86`)

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, on `mac-ar-u2-text-20261121` over `ops-tasl-20261116`
`dc0c559e`, for finding M5 of the G.1b cross-check review (U2 conditions C1–C5). ENGINEERING_ONLY.

The result file is not edited, because its sha256 `8f872f2d…` is bound on `main` by:
- the U4 census (`TRACKG_U4_CENSUS_20261120.md`);
- its acceptance sidecar (`TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md`);
- the delta spot check (`docs/r1/reviews/TRACKG_U4_CENSUS_DELTA_SPOT_CHECK_20261121.md`).

These corrections apply to it. No measured value changes, and the census row is unaffected.

| Where in the result | As written | Correct |
|---|---|---|
| Status line | `R1-TRACKG-AR-U2-TASL2` "reaches main after the sweep-2 launch" | The row is on `main` (PLAN §10). |
| Status line and Record, last bullet | "The T1 labels themselves run on H200 (`R1-T1-HOST-H200`)"; "T1 labels remain H200" | The T1 table (G.1b, G.4, G.5) runs on the TASL pair (`R1-T1-HOST-TASL`, amending `R1-T1-HOST-H200`). |
| Unit provenance (C1) | The executed amended unit "with TASL-2 adaptations" is preserved as `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` (`b83d9159…`) | That file is the Ada-targeted unit, byte-identical to the committed one (Ada, `torch312` Python 3.12.16, the Ada data root, the Paper A gate, ≥ 40 GiB free), as the result's own revision note says. The TASL-2 adaptations are recorded only in the result's prose: host TASL-2, env `ar-cond7a` (Python 3.12.15), data root `/home/dowling/r1_trackp/data`, 20,000 MiB free-floor, no Paper A gate, host difference disclosed. The reviewed unit `3bb015a1…` was not preserved. |
| Raw-cost table, B1 row (C4) | "B1/B2 median 218.7935 s" | The B1/B2 median is **218.697 s** ((218.951 + 218.443) / 2). 218.7935 s is the median of the 8 executed runs. |
| Raw-cost table, whole smoke wall (C4) | "1,791.0 s (29:49)" | 1,791.0 s is 29 min 51 s. 29:49 matches `time -v`'s 1,789.26 s. |

## Errata of the smoke report it cites (`TASL2_AR_COND7A_RESULT_20261121.md`, sha `8814eecc…`; also bound, not edited)

- "median 218.951 s" sits next to "mean 223.547 s" and is meant as the median of the 8 executed runs (the captures'
  `slowdown.json`, `median_executed_run_seconds`, over 8 records). 218.951 s is the upper-middle value
  (`vals[len // 2]`). The true median of the 8 executed runs is **218.7935 s** (review m6). The B1/B2 median, a
  different quantity, is 218.697 s.
- "16.6 KB": the refused `s001` record is 166,300 B.
- "161,531,825 B" cannot be reproduced from the bundle (review m8). The capture bundle content is 152,751,278 B, and its
  apparent size (`du -sb`) is 161,534,003 B. The U2 result's own phrase "the Mac bundle/packaging size" is not a
  verified explanation either.
- The `slowdown.stderr` wording: `slowdown.stderr.txt` is 0 B. The first, false `RESULT_STATUS` STOP is evidenced only
  by `RESULT_STATUS.initial_false_stop.txt` and `DONE.initial_false_stop`; the result attributes it to a parse error
  in the slowdown script. The record is preserved, and the smoke was not re-run.

## Still open

- C3/C4: the executed TASL-2 unit exists only as prose in the result. The executed bytes and the reviewed `3bb015a1…`
  bytes were not preserved.
- This errata file needs a short independent re-review before autoresearch's G.1b spec entry relies on the U2 row.
