# local/20261128-11 — G.5 tests independent of the repository spec's state (unblocks publication)

Your render (`local-20261128-10-g5-final-render` @ `6466e044`, review ACCEPTED) fills `sweep2/t1_tasl/g5_tasl_spec.json`, and 79 focused tests that read
that file in its draft state now fail (IDs in your report, sha256 `b385a976…`). Fix the tests, not the spec or the note: each affected test builds its
own spec state (draft or filled) from a fixture, so both the draft-state coverage and the published-state coverage stay, and no signed choice or
render value changes. On a branch based on the render tip: focused G.5 suite base (`a70c8872`) vs render vs render+fix (render+fix must have zero new
failures against base), full suite base vs tip, tier-E review of the test change. Report the tip; the coordinator then merges render + fix together after
its own full-suite check and publishes the note with `approved: true` under R1-G5-SIGNATURE. Priority: first.
