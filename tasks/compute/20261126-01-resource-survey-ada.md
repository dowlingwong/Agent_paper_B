# compute/20261126-01 — where are free resources now; is Ada ready (R1-HOST-FREE)

Read-only on every host. No `sudo`, nothing of another user touched, no evidence run.

1. **Survey, one table:** for deepthought, deepthought2, the ETP pool, TASL-2, TASL-7 and Ada: CPUs and load, RAM,
   each GPU with model, memory, driver, current compute processes and their users, how many cards are empty now,
   and the free memory on each card that is in use (a card may be shared, R1-CARD-SHARE). Free disk under the work paths. This also fills the *to verify* fields of
   `canon/COMPUTE.md` for Ada.
2. **Ada readiness** (the author reports many Ada cards free):
   - who else uses the server and how (processes over a few samples in two hours);
   - Python environments present; whether `docker` or `apptainer` is usable by the account; CUDA and driver versions;
   - whether the pinned Track P image (v2.2 digest in `r1/scripts/configs/trackp_htcondor_v2.json`) can run there, or
     whether the environment must be built from its lock file; do not build yet, say what it would take;
   - whether a llama.cpp server build for the proposer `gemma4_31b` exists or what building it needs;
   - an **engineering** timing only if it costs under one GPU-hour in total and is clearly labelled
     ENGINEERING_ONLY: tokens per second of the proposer on one card.
3. **A placement proposal for the open steps:** which work goes to which host under R1-HOST-FREE — the P.4
   probe and SFT runs, the D.3 proposer, audit capacity for G.5 beyond the TASL pair, the expansion G.1b (stays on
   TASL-2, its note binds it). State for each what must exist first (a launcher, a host check, a cross-host check, a
   note).

Done when: one report with the table, the readiness findings and the proposal; captures on a branch if you keep any.
