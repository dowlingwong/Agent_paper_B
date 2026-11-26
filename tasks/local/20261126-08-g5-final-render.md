# local/20261126-08 — G.5 final note render (starts after two inputs; prepare now)

Main: `95249de3`. The coordinator's signing sheet is `sheets/G5_SIGNING_SHEET_S1_S14_20261126.md` on this branch.

**Start the render only when both exist:**
(1) the author's signing reply to that sheet, which the coordinator records as a PLAN row and names in a later task file; and
(2) the reviewed seven-node REL-T1-G1B copy on `main` (task `compute/20261126-05`).

**Prepare now (level 0, no spec change pushed):** read §11 and §11.1 of the draft (revision 13). List every spec field the
signature fills (`decisions.<id>.signed`, `key_values.freeze_wait_release_date`, `cuda_ipc.mode`, `noise_floor.seven.*`,
`tails` from P10, `run_id`, `paper_commit`, `spec_sha256`), with the source of each value. Then dry-run the sheet's
recommended values (S6 = 2027-12-31, S4 = acceptance line) through `validate_spec` and `key-lines` in a scratch copy of the
spec, and report any refusal. Report this as a short note on `coord/local`.

**After both inputs:** fill the spec, run `g5_tasl.py key-lines`, write the final note as
`docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md` (`approved: false` until the coordinator publishes it with the row), run
`g5_tasl.py check-note <spec> --note <note> --draft`, then get a fresh review of the render (tier E). Push a branch.

The houseprice fix (`local/20261126-01`) keeps its pass criterion as written: the sheet recommends S14 = A, so 9.486 s
stays, under R1-HOST-FREE (3).

Done when: the branch is pushed with the review verdict and the draft check's output.
