# Review: G.5 final render, c3_t1_labels_20261127 (tier E), round 1

- **Unit:** `local/20261126-08` with `-10`, `-14` and `-15`.
- **Reviewed:** tip `30b2eff1` on `mac-g5-render-20261126`, over base `166db0eb`.
- **Reviewer:** a fresh tier-E reviewer (Claude subagent, AI-assisted) who did not write the unit. It changed, committed and pushed nothing, and opened no credential, label, test or evaluation file; it read only the G.1b `runs.jsonl` engineering copy, for P10. The author of the unit transcribed this record from the hand-back.

## Blocking findings

### B1. P10 (all seven nodes Gaussian) is a choice, not a mechanical fill

- No numeric heavy-tail test is adopted:
  - R1-BX-REVISIONS (c) carries the rule as *(proposed)*.
  - R1-BX-PROPOSED-CONFIRM E5 says "a heavy-tailed node uses a Student-t".
  - R1-NOISE-STUDENT-T was only option 6 of `AUTHOR_DECISIONS_20261104.md`.
- "No node declared, so Gaussian" is circular: the declaration being asked for is that very declaration.
- The data are not benign. mlab_ogbn_arxiv has G2 of +8.45 at c0, +29.79 at c3, and +7.5 to +8.7 on all four paired differences. mlgym_breakout_minatar has +5.92, +3.81 and +7.16. The standard error of G2 at n = 30 is about 0.83.
- **Fix:** the decision goes to the author with the kurtosis table. Under R1-G5-SIGNATURE (2) a render that makes a choice comes back to the author. The report must give the derivation.

### B2. `paper.commit` 166db0eb is already stale

- `main` 47df6f55 changed code outside `docs/`: `dry_run_node.py`, `run_cpuset_check.sh` and a test.
- `verify_launch_tasl` requires the launch checkout to equal `paper.commit` outside `docs/` and the spec, so every job would stop.
- **Fix:** fill it again at publication, after the last code merge. Re-render `paper_commit` and `spec_sha256`, run `check-note --draft` again, and get a short re-check.

### B3. The REL-T1-G1B copy review reads `verdict: ACCEPTED` (lowercase)

- `_review_names` requires `^Verdict: ACCEPTED\s*$`, so `check_seven_copy` against `origin/main` STOPs at every job start.
- With only that line corrected, the same call passes.
- **Fix:** a docs-only correction of the review's verdict line before publication.

### B4. P11 PENDING blocks publication

- No C1–C15 host-test PASS record is on `main`. Partial records exist:
  - the G.4b re-pilot (C3, C8);
  - `g5_pin_check` rc 0 (C13);
  - the engine smoke `G5_TASL2_ENGINE_SMOKE_20261123.md`, with fake engines (partial C2 and C14).
- Some C items cannot pass before signature: C15 needs "both assembly stages with the signed note", and C10 needs "a multi-day span".
- **Fix:** a ruling on the reading of P11, then a reviewed host-test record cited in P11. `P_CITES["P11"]` is empty, so the citation has to be checked by hand.

## Minor findings

- **M1:** the S13 operator-flock schedule is not written into the note.
- **M2:** cite the engine smoke when P11 is rewritten.
- **M3:** mlgym_houseprice is CPU-only, outside the GPU scoping of R1-BX-REVISIONS (c).
- **M4:** state n per configuration (mlab_cifar10 c4 has 29 seeds).

## Nits

- **N1:** the spec's `comment` and `draft.revision` are stale. Leave them; changing them would move `spec_sha256`.
- **N2:** the signed-text lines parse as fields. This is harmless.
- **N3:** the "over 166db0eb" sentence goes stale with B2.

## What checks out

- The spec diff contains only authorised fills, and `key_values.status` is unchanged.
- `validate_spec` passes, plain and with `launch=True`.
- The key block equals the `key-lines` output apart from line 1. Outside the fills, the lines equal the revision-13 render.
- P1–P9 cite real records with correct sha256s, and all eleven P5/P8 reviews read `Verdict: ACCEPTED`.
- A strict `check_note` simulation passes.
- The other switch checks pass against `origin/main`. `check_cpuset_record` STOPs for houseprice only, which is expected after signature.

Verdict: NOT ACCEPTED

## Author's response (render revision on this branch)

- **B1:** P10 now reads PENDING. It states that the declaration is the author's, gives the kurtosis summary, the per-configuration n and the houseprice scoping (M3, M4), and sends the full table to the author with the report. The `tails` line still renders gaussian only because the spec requires a value.
- **M1:** the S13 schedule is added as signed text.
- **N3:** the sentence now says `paper.commit` is filled again at publication.
- **B2, B3 and B4:** these are publication-time or level-1/2 items for the coordinator and the author. They are listed in the report. `check-note --draft` now STOPs on P10 and P11 only.
