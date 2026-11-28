# local/20261128-10 — G.5 final render (resumes `local/20261126-08`): P11 PASS, paper.commit, check, review

P11 is complete on `main` `a70c8872`: the primary lease matrix and infra STOP (`b70cfa01`, partial record) and the four TASL-7 scenarios determinism, restart,
tar, closeserver (`compute-g5-p11-matrix-complete-20261128` @ `0ce1e664`, review re-check ACCEPTED, 420/420 captures), plus the earlier host-test record and
refusals record. S14 houseprice PASS is published. Resume the final render from `mac-g5-sd-render-20261127` @ `bc968b3e`: write P11 as PASS with the exact
record and review citations (R1-G5-P11), P10 per R1-G5-TAILS, fill `paper.commit` with the full 40-hex launch commit, set the note's run id
(`c3_t1_labels_<YYYYMMDD>`), run `g5_tasl.py key-lines` and `check-note … --draft`, and get the tier-E review of the render. Keep `approved: false` in the
draft; under R1-G5-SIGNATURE the coordinator publishes the reviewed note with `approved: true` and runs the strict `check-note` after publication.
Priority: first (before the D.3 rev 5 freeze work, which waits for the author's signature anyway).
