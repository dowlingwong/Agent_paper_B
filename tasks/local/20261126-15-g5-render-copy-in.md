# local/20261126-15 — G.5 final render: the second input is on main (start local/20261126-08's render)

The seven-node REL-T1-G1B copy and its independent review (ACCEPTED) are on `main` `166db0eb` (merge of
`compute-rel-t1-g1b-copy-20261126` @ `0c1525d4`): `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/` with `COPY_RECORD.json`, the
step's `stdout.txt`, and `docs/r1/reviews/REL_T1_G1B_COPY_REVIEW_20261126.md`. Copy hashes: summary `945abc0a…`, ASSEMBLY
`e4056710…`, runs `1f56c068…`, gate `00ee68c2…`. The coordinator checked that summary, ASSEMBLY and gate are byte-identical to
`docs/r1/reports/tasl_chain_20261122/G1B_TASL_SEVEN_NODE_ASSEMBLY_20261125/` on `main`, that runs.jsonl matches the gate's
`runs_jsonl_sha256`, and that no record has a seed in 7001–7010.

Both inputs of `local/20261126-08` now exist: the signature (`ef06a65c`) and the copy. Render as -08 says, with P10 recorded in
the unit (`local/20261126-14`). Fill `noise_floor.seven.*` from the step's stdout, set `run_id` to the note's date, render,
`check-note --draft`, fresh review (tier E), push. Do not change any signed choice.
