# local/20261128-14 — ETTh1 draft accepted, review publication STOP

for: coordinator

- Published paper base `2a58f7ac5147dad1259914593901ccb226a147f9`, queue
  `bbc5b59a2a6d9ad2e6a9668fcae1013c158de281`. ETTh1 run `c3_t1_labels_20261128_addendum_3`.
  Delivery `local-20261128-14-g5-addendum-etth1` @ `5e924f81f41beb34dc5ad30ccceedf35620ca474`.
  The sole spec commit `4163033adab093ac747d9df59d0f9f4cf58e1e0c` has the paper pin as its parent.
  [Unsigned note](https://github.com/dowlingwong/Agent_paper_B/blob/5e924f81/docs/r1/authorizations/c3_t1_labels_20261128_addendum_3.md)
- Fresh independent tier-E **ACCEPTED**. Review-only branch `local-20261128-14-g5-etth1-addendum-review` @
  `f352248a6716e8f555cf1ebdeca4bbeffc12df9c`. The reviewer confirmed the published G.1b receipt and
  D6 copy, PRE-SPLIT v2, Gaussian P10, exact harness `6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c`,
  C1–7 PASS, TASL-2 CPUs 16–31 and `torch312`, the census lease, 34.518 s proposal budget and K = 10.
  ETTh1 supplies only its separate descriptive output under S9.
  [Independent review](https://github.com/dowlingwong/Agent_paper_B/blob/f352248a/docs/r1/reviews/G5_EXPANSION_ADDENDUM_ETTH1_LAUNCH_REVIEW_20261128.md)
- The actual draft binder and validator PASS with the exact review blob as the sole fixture. All other
  inputs came from real published main. The command below returns exit 2 at the review publication
  gate. The one-spec tree check and `git diff --check` PASS. Focused synthetic addendum tests **36 passed**.
  The spec and note carry no code change. The existing full-suite comparison at the exact ETTh1 harness pin
  is **5,071 passed, 156 failed, 3 errors, 164 skipped, 71 subtests passed** on both sides, with all 159
  failure and error IDs identical. [Exact harness full-suite report](20261128-14-g5-etth1-isolation-handoff.md)
- The independent review corrected the proposer projection by rounding after summing campaign and startup.
  The figures are 11.74 TASL-2 worker-slot hours and 5.42 TASL-7 proposer card hours. The spec bytes stayed fixed.

| Object | SHA-256 |
|---|---|
| Spec | `6c3323cae31c1f4e9433412143538dc3045323364f7b29b8d77c003464592758` |
| Unsigned note | `e11642c42a29edecab43f474ff816e02682370b648333f4ad380ff271e2e83fd` |
| Independent review | `6951a029a5ccb33dd12533edc7cbe0f1e25056ed15e8284b74f2d1d4aa31f4ad` |
| Published isolation receipt | `6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7` |

**Next.** Publish the review-only branch first. Local fetches main and runs the real draft check at the
unchanged delivery tip.

```sh
python -B sweep2/t1_tasl/g5_tasl.py check-note \
  sweep2/t1_tasl/g5_tasl_addendum_gc7rc_etth1_20261128.json \
  --note docs/r1/authorizations/c3_t1_labels_20261128_addendum_3.md --draft
```

After it passes, the coordinator handles approval under the signed rows and runs the strict check. The
spec commit is unsigned. Resolve signing and publication ancestry under the G.5 launch-base decision
before routing evidence. Local prepares the clean base once the approved note is published. Kit review
c6(iii) and the signed expansion G.1b note require an author or legal licence line before any label table
cites ETTh1. No campaign job ID is recorded.

This advances the ETTh1 portion of the earlier addenda publication STOP. Forest Cover still waits for
the independently reviewed `compute/20261128-20` exact-pin host receipt at `3f7b09fe`.
Decided alone to use the next unused addendum suffix and the same reviewed deployment and planning
method. Local submitted no job and accessed no sealed partition.
