# local/20261126-11 — T5 shared-noise: the one correction round (mac-t5-shared-20261122)

Fresh review of your branch `mac-t5-shared-20261122` @ `d0ef5282`: **ACCEPT WITH MINOR** (0 MAJOR, 3 MINOR, 6 NOTE). Record:
`docs/r1/reviews/T5_SHARED_NOISE_REVIEW_20261126.md` on branch `coord-reviews-20261126` @ `a2464ec4`, sha256
`2ac9cde0ed8bb4e52628430f3d5d8278813180aa4777ea51b1886329410a6542`. Tier S: one correction round. The remaining minors are
fixed without a further round.

- **m2:** state the table/known "bracket" of the threshold correction as an empirical ordering (it holds in all 48 cells),
  not as a proven bound (note l.283–286, l.351).
- **m3:** say the "conservative" result is consistent with R1-THEORY-RHO (2), which is conditional; the evidence is
  aggregate over edit types (note l.303).
- **m1:** in the note, label the "+0.47 to +1.84 δ_n" figures as oracle-prior and give A2's own figures beside them. The
  PLAN row R1-D3-CHOICES (1) quotes the same figures. That row is the author's; the coordinator brings it to him. Do not
  edit PLAN.
- The six NOTEs: address them or say why not, one line each (n2: the t ≥ 0 condition in the paraphrase of
  R1-THEORY-RHO (1)).

One commit on your branch. Run the unit's tests and give the counts. Done when: your report gives the new tip.
