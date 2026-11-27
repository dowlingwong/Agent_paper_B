# compute/20261127-21 — P.4 probe: get its record reviewed; keep the G1 fix first

1. **Order.** `compute/20261127-20` (the G1 final-snapshot defects) is first in your queue: it blocks the D.3 pre-declaration's freezing.
   Your last report re-delivered the survey redaction, which was merged long ago (`909fdc59`); nothing more is needed there.
2. **P.4 probe** (`compute-p4-ada-probe-20261127` @ `616c09b2`). The record is clear, and you were right not to retry the 4B arms with
   another micro-batch or with checkpointing (P4-MB A makes an OOM the author's decision). Write the round report on `coord/compute`, and get a
   fresh review of the probe record (tier E: it sets the phase-1 note's values). The review checks the charges, the sealed attempt classes and the
   peak-memory figures. The 4B decision is with the author now (`AUTHOR.md`). Do not run anything for it until a task file names the decision.
