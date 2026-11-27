# local/20261127-30 — PRE-SPLIT amendment ready to publish; the addendum switch with its own launch binding

Base: `main` `f43823da` (the four addendum drafts are merged). Two units.

1. **PRE-SPLIT amendment (R1-G5-S9 (1)).** Make `docs/r1/proposals/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_DRAFT_20261127.md` publish-ready as its A§4
   says (status line, final block, the path `docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md`, `approved: true`). Its
   content must say exactly what R1-G5-S9 (1) decides and nothing more; the frozen preregistration's bytes stay unchanged. Run the release check
   that refuses v2 today, to show it accepts the published amendment (in a scratch publication fixture), and get a fresh review. The coordinator
   publishes it under R1-G5-S9 (1).
2. **The addendum switch (coordinator decision, level 1: sequencing).** The main G.5 note does **not** wait for the addenda: it publishes as soon as
   its own conditions hold (P11, houseprice, `paper.commit`, final review) and the eight nodes start. The addendum unit carries **its own reviewed
   launch binding**: its own launch commit and spec digest per addendum note, checked by `verify_launch_tasl` against that note, so a later code
   change for the addenda does not move the main note's pin. Include: the census-override handling the G.5 engine needs for MetaMaze, ETTh1 and
   Forest Cover (as their G.1b used it, reviewed); a G.5 deployment entry per node (CPU set, lease, census environment); the spec/run binding of the
   added jobs and receipts in `g5_job`/`g5_seal` and the assembly; MLGym release integration under split v2; separate 1GC outputs; the same K,
   campaign settings, run budget, host checks and release locks. End-to-end synthetic refusals and routing tests, full suite, tier-E review.
   The four nodes' P10 tail declarations are an author item once their copies exist; list the kurtosis table when the D6 copy lands.
