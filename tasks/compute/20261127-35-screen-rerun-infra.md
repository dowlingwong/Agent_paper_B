# compute/20261127-35 — screening: rerun after the co-tenancy stop (R1-SCREEN-COTENANCY-INFRA), first in your queue

PLAN **R1-SCREEN-COTENANCY-INFRA** (`main` `c80f83bc`). The stopped run `SMEAS_EVIDENCE_20261127T1550Z` stays sealed as a record; none of its rows enters
the analysis. Rerun under the **same** signed note `screen_measure_20261127_reissue_2.md`, code `c12136d6`, the rebuilt cache (tree `3843b53c…`),
with a **new** `SMEAS_EVIDENCE_<stamp>`. Start when the strict preflight finds at least 10 cores free for other users on deepthought; if the
load is high, wait and retry the preflight later. The guard stays on. A later co-tenancy stop: seal, record it, and rerun the same way. Any other
STOP returns to the author. Report per-node verdicts with intervals, CPU-hours and the sealed output; a SHARED decision node at once.
Then continue `compute/20261127-34`.
