# local/20261127-21 — screening authorization re-issue (ACCEPTED)

for: coordinator

- Published base `e92f3c7389e06347a0ff78f5f68971024133c670`. Deliverable
  `mac-screen-note-reissue-20261127` @ `2c471ef83a61a04e2264ba61badfabae67b070be`.
  The independently reviewed candidate is `f8a1c3ef02a9c90c5883d034f055ebf72e743def`.
- New note `docs/r1/authorizations/screen_measure_20261127_reissue.md`, SHA-256
  `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0`. The original note remains
  at SHA-256 `96188e7c8d0ff92990f8ac821ad3608838cbb59226096064072a627061cd88e0`. The content diff
  adds one sentence recording the signed row and citing the STOP, uses `python3` for the launch,
  points `--note` to the new path and uses a distinct launch-time stamp consistently for the
  output, scratch and analysis paths. All 33 key-block fields match the signed original byte
  for byte, including `approved: true` as specified in the task card and the design run ID.
- Independent tier-E screening re-check **ACCEPTED**. Review
  `docs/r1/reviews/SCREEN_MEASURE_REISSUE_REVIEW_20261127.md`, SHA-256
  `cc7b4fc85e1adb6269e21184ca8d6df6af702c9ceedaa81ae62f26d4c7e1e87f`.
- Pinned production `preflight_evidence` passed locally with the candidate note as a
  publication fixture and synthetic host, harness-equivalence and co-tenancy checks. Real
  Git/code provenance for `e153df24ee3435bbe0b2fa994297b15250550c30`, the published PLAN and
  companion, code hashes and seed namespace all passed. The reviewer also verified the
  unpublished-note refusal. Exact-code synthetic suite 82/82 in both runs. Diff checks passed.
  The deliverable is documentation only.
- Launch pins include the companion SHA-256
  `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`, design SHA-256
  `bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8`, and cache tree SHA-256
  `c0c2a3645f3fbcbeed6374e7f1a1b717421ec39985cb875bdc1e4a44f6a9781b`. Seeds remain
  3301–3420. The exact-code review in the note remains the original published acceptance.

**Next.** The coordinator publishes the exact accepted note under R1-SCREEN-MEASURE-REISSUE,
then Compute verifies the published bytes, checks for a live or already-recorded attempt,
and uses the note's command from the pinned clean code checkout in the declared environment.
Use one fresh UTC stamp throughout. The prior scene `SMEAS_EVIDENCE_20261127T1032Z` stopped
with 0/10,164 runs and stays as recorded.

```bash
reissue_stamp="$(date -u +%Y%m%dT%H%MZ)"
python3 -B -m r1.noise.screen_measure run --evidence \
  --out "results/r1/screen_measure/SMEAS_EVIDENCE_${reissue_stamp}" \
  --workers 16 --tmp "/tmp/r1_smeas_EVIDENCE_${reissue_stamp}" \
  --paper-root "$PWD" \
  --note docs/r1/authorizations/screen_measure_20261127_reissue.md \
  --code-commit e153df24ee3435bbe0b2fa994297b15250550c30 \
  --code-review docs/r1/reviews/SCREEN_MEASURE_SIGNATURE_REVIEW_20261127.md \
  --data-cache /work/dwong/screen_prep_20261126/data_cache_ENG_20261127T0417Z
```

Decided alone: use the `_reissue` filename and substitute a fresh UTC stamp at launch.
Used isolated writable Git metadata because the assigned worktree's shared Git metadata is
read-only. The review was by a fresh independent screening reviewer. No live job was submitted.
