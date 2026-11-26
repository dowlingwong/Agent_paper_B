# compute/20261126-10 — launch the four expansion nodes (the task file compute/20261126-04 item 5 waits for)

Owner: compute. Runbook §2 order 2B; PLAN R1-T1-NODE-EXPANSION, R1-STEP-ORDER (2)(a). **Ready now.**

The note is published: `docs/r1/authorizations/g1b_x_t1_tasl_20261126.md` on `main` `166db0eb`, sha256
`16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539`, `approved: true`. The coordinator ran the strict
`check-note-x` on `166db0eb`: PASS. The P4 review binds the spec `d0dce058…cfd238` (ACCEPTED), and `check_gate_x` passes for
all four nodes against `main`. Your c1 record and your REL-T1-G1B copy are on `main` in the same merge.

On TASL-2, from a checkout of `7d0279d8a677582f4f6e5892461bf7138e78fd66` holding the published note byte-identical (copy it
from `origin/main`; an untracked file under `docs/` is allowed by `verify_launch_tasl`), one call per node, all four at once
(disjoint CPU sets):

    G1B_TASL_ENABLE_REAL=1 sweep2/t1_tasl/t1_tasl_node.sh g1b sweep2/t1_tasl/g1b_tasl_x_spec.json <node> docs/r1/authorizations/g1b_x_t1_tasl_20261126.md --enable

Nodes and CPU sets: `mlgym_metamaze` 0-3, `gc7rc_forestcover` 4-7, `mlgym_titanic` 12-15, `gc7rc_etth1` 16-31, each with its
`~/r1_locks/cpus-<set>.lock`. No GPU lease. Start before 30 Nov 20:33 CET, so the `cutoff` line has no case (now is well
before that). Everything in `compute/20261126-04` items 6–7 applies: a node-deadline STOP is not an outcome (keep the scene,
report, wait for a task), and a determinism failure is a STOP. `launch` runs the strict check and the publication-row check
itself; if either refuses, that is a STOP. Report it and do not work around it.

Report per node: start UTC, attempt directory, and then seal and verdict. Then `assemble` and `summarise` as the note says,
with the summary and its sha256.
