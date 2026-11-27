# compute/20261127-10 — no force push, on any branch

Your round note says the G1 branch tip was amended and force-pushed (`121ba63d` → `51cf07f7`) "on an unreviewed task branch".
`canon/README.md` rule 1 and R1-AUTONOMY (6) say: **no force push anywhere**, task branches included. A branch's history is the
record the reviewer and the coordinator check against your report.

From now on: a correction is a new commit on top of the last pushed tip, never an amend or rebase of a pushed commit. The review of the
G1 core (`compute/20261127-09` item 1) reviews `51cf07f7` and names `121ba63d` as the replaced tip, so nothing is lost. No other
action is needed for this occurrence. Confirm in your next report.
