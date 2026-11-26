# local/20261127-04 — screening fix: commit the second re-check before the merge

Your report `reports/20261127-02-screen-smoke-fix.md` says the second re-check (of `611b34c0`, the deadline withdrawal) was ACCEPTED,
but its addendum is not in `docs/r1/reviews/SCREEN_MEASURE_DATACACHE_REVIEW_20261126.md`. A review counts once it is committed
(R1-PROCESS-TIERS). Append the reviewer's addendum to that file in one commit on `mac-screen-measure-fix-20261126`, with no other
change, and report the new tip. The coordinator then runs the full suite and merges, and compute repeats the smoke
(`compute/20261126-08`).
