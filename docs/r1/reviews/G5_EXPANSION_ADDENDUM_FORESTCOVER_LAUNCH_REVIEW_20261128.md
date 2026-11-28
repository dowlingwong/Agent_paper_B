Verdict: ACCEPTED

# Independent tier-E review of the unsigned Forest Cover G.5 addendum

Task `local/20261128-16`. The reviewer was independent of the spec and note drafts.

- Run ID `c3_t1_labels_20261128_addendum_4`.
- Paper pin `f532176f3f0241909c9fb8df63a58e6fbefaefbd`.
- Spec-only commit `b9268a2a9ad9406b33de03b41804d2c2626df93f`.
- Spec SHA-256 `2834327aac53e5172cef3dce4aafd4f646903c0c3f4af7dc86adfbc7551b1a78`.
- Unsigned note commit `10efc822341eafecb0eaa919b91b806d20a4b4fd`.
- Reviewed unsigned note body SHA-256 with `approved: false` and `review: PENDING`,
  `3437e2f360d87d7e89ddb584fdf999f0ac3a1974dc4ad82d5324e970b13d8910`.

The spec commit's tree is the paper pin plus the one Forest Cover JSON spec. The next
commit adds only the unsigned note. Both additions match their committed bytes.
Published main at verification was `4ceb5099b65245f10b4c10eab22c7201325799c9`.
The pin is its ancestor and the advance adds five unrelated D.3 preflight report files.
The published inputs and prose citation hashes match the pinned objects.

The actual `g5_addendum.bind(..., draft=True)` and `g5_tasl.validate_spec(..., launch=True)`
passed. The review fixture supplied one blob at the intended review path and replaced
only the pending citation in a temporary copy of the note at its canonical path suffix.
All other inputs came from published main and the exact desk tree. The draft binder
refused the original pending citation and the temporary citation without its published
review. The strict binder refused the unsigned note even with the fixture.

The published expansion G.1b note, spec, receipt and reviewed D6 copy bind
`g1b-x-tasl-20261126-a`, Forest Cover attempt 1, TASL-2 CPU, and the same job recorded in
the assembly. The copy contains 460 Forest Cover runs, zero divergences and determinism
PASS. D21 remains a funnel disclosure under R1-T1-D21-SCOPE. The independently accepted
harness comparison binds census kit `85851664679d10889c5af406843c4a3fc38f7a49` to G.5 harness
`3f7b09febf401a83f3aa881f00eecdd032024416`. Published TASL-2 isolation passes C1–7 at
that exact G.5 pin. Its accepted review has documentation and evidence-coverage minors,
which the draft acknowledges.

Both waves and their audits use the determinism-checked 4–7 replacement set, `torch312`,
and the census interpreter on TASL-2. The inherited worker-slot lease is
`~/r1_locks/gpu0.lock`. The S13 leases are `~/r1_locks/cpus-0-3.lock` and
`~/r1_locks/cpus-4-7.lock`. The second also covers the census deployment. The proposer
uses TASL-7 under this addendum's own run ID and digest. The derived runtime inherits
the signed base settings, including W = 20 manager calls, history, 12 instances,
K = 10, the signed seed blocks and STOP rules. The proposal budget is
3 × 255.723 s = 767.169 s.

R1-G5-TAILS-EXPANSION signs Gaussian for Forest Cover before label assembly. The
published split v2 regenerates byte-identically, preserves T0 and the original eight
T1 assignments, and routes Forest Cover as `g5_addendum_extra_task`. The approved,
frozen PRE-SPLIT amendment binds the same v2. Under R1-G5-S9 the descriptive output
is separate from SFT, arms training and the primary gate.

The existing planning formula gives 62.08 worker-slot hours and 9.81 TASL-7 proposer
card hours including startup, with a 93.406 s CPU census baseline, 60 s manager calls,
0.60 run share, no duplicate discount and 1.25 inflation. This is consistent with the
signed 425 worker-card GPU-hour reporting threshold and R1-NO-TIMEOUT (3). The draft
records the port baseline and evaluator, CPU noise floor, validation selection, sealed
test partition, UCI Covertype CC BY 4.0 attribution and exclusion of data from repository
and bundles. It carries forward the pinned kit review's appendix and funnel disclosures.

This acceptance covers the one-spec commit and exact unsigned note. Publication requires
the coordinator's real draft check with this review on main, approval under the signed
workflow, and the strict check after publication. This was a desk review of published
engineering metadata.
