# local/20261128-02 — G.5 P11: an engineering smoke path for the note-gated host tests (correction of my 28 Nov disposition)

Your report `20261128-08-g5-render-p11-stop.md` is right: R1-G5-P11 needs **reviewed pre-publication** coverage, and the strict `check-note` after
publication does not execute host tests. My disposition in `compute/20261128-05` item 1 ("checked at publication") is withdrawn for C2, C4, C5, the
G.5 seal path, C9, C14, C10's short span (restart = infrastructure STOP), the C11 chunk side and C16.

Build a reviewed **ENGINEERING_ONLY** smoke path that runs those checks on TASL-2/TASL-7 without a published note: a synthetic smoke spec and run id the
launch gate accepts only in an explicit engineering mode (never `c3_t1_labels_*`, never evidence; label tables and receipts written under an
engineering root and refused by the release path), following the 24 Nov smoke (`main-t1-g5-smoke-20261124`). Targeted tests, full suite base vs tip,
tier-E review; report the exact compute commands per item. If any item genuinely cannot run before publication, name it with the reason: moving a
P11 item past publication is the author's (a change to R1-G5-P11), and I will take it to the author with that list.
Priority: first in your queue.
