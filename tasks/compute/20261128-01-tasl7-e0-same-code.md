# compute/20261128-01 — P.4 E0 reference on TASL-7 at the same code and configuration as the Ada run (R1-P4-E0-SAME-CODE-REFERENCE)

PLAN **R1-P4-E0-SAME-CODE-REFERENCE** (`main` `15fe05b0`). Bind the run to the Ada comparison recorded on `main` (`docs/r1/reports/trackp_p5_ada_20261127/`):
paper `c80f83bc`, `e0_config_ref.json` sha256 `9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054`, the same data, model and seed as
the Ada E0 run `p5_20261127_b/e0e`. On TASL-7 (4090, free): verify the environment and the lease (per-card), run the **complete** E0 reference, then
compare Ada with it using the **existing** comparator and tolerances. Keep the 26 Oct reference as a record. Report: equivalent or not (with the metrics
and tolerances), the timing disposition the phase-1 note needs, captures and hashes on a branch, and a fresh review. Priority: before the P11 items.
