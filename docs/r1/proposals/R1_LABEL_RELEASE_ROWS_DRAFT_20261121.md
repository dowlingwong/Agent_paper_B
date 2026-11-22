# Draft release rows of the sweep-2 analysis preregistration §8 (PRE-STAGE A) — approved: false

Drafted by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, for the signed preregistration
(`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, R1-SWEEP2-PREREG) §8. **Not author decisions.** Each row,
once the placeholders are filled and it is added to a dated author table of PLAN §10, is what `r1/c3/release.py`
(`release_row`) requires before it writes or opens a partition. The text must match exactly (`release.row_pattern`;
`release.row_text` fills it in).

Placeholders:

- `<PREREG_SHA256_AT_FREEZE>`: the sha256 of the committed preregistration after the coordinating chat freezes it. The release
  step reads only the preregistration's decision block. Comments are ignored, exactly one fenced block may hold a
  `frozen:` line, and that block must end the document. Every line is `key: value`, and the keys are exactly the signed
  block's, each once: `frozen`, `split_file`, the thirteen `pre_*` decisions with their signed values, `gate_sha256`,
  `gate_input_builder_sha256`, `signed_by` and `frozen_utc`. Among them, exactly:
  - `frozen: true`
  - `split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`
  - `pre_stage: A`
  - `gate_sha256:` the committed gate's sha256
  - `gate_input_builder_sha256:` the committed builder's sha256 (the reviewed value is
    `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808`)
  - `frozen_utc: YYYY-MM-DDTHH:MM[:SS]Z`

  An unfrozen or otherwise different block is refused.
- `<RELEASE_CODE_COMMIT>`: the published commit (an ancestor of `origin/main` and of the running checkout) whose
  `r1/c3/release.py` is the reviewed release step. The release step that writes a partition must run exactly that file.
  Readers check the row and the receipt's commit, not HEAD's bytes, so a later reviewed edit does not void earlier
  receipts.
- `<ARMS_FROZEN_RECORD_PATH>` and `<ARMS_FROZEN_RECORD_SHA256>` (test rows only): the committed arms-frozen record (§4
  step 4); the release step checks its bytes.
- `<T1_NODE>`, `<G1B_SUMMARY_PATH>`, `<G1B_SUMMARY_SHA256>` (T1 train/dev row only; one item per T1 node, joined by
  `; `): each T1 node's G.1b noise summary, committed in the repository, as PRE-DELTA requires ("path and sha256 recorded in
  the T1 train/dev release row, before any training"). The release step checks each file's bytes.

The P3 split-file sha256 is filled in: `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`.

## T0 (both sources: sweep 1 and sweep 2)

| ID | Decision |
|---|---|
| R1-S2-LABELS-TRAINDEV-RELEASE | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`): the train and dev label blocks of both sources (sweep 1 and sweep 2), partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. No test label and no evaluation value is released by this row. |
| R1-S2-LABELS-TEST-RELEASE | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`), after the arms-frozen record `<ARMS_FROZEN_RECORD_PATH>` (sha256 `<ARMS_FROZEN_RECORD_SHA256>`): the test label blocks and every evaluation block of both sources (sweep 1 and sweep 2), partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. |

## T1 (the G.5 tables; for the G.5 note, citing this preregistration)

| ID | Decision |
|---|---|
| R1-T1-LABELS-UNSEAL | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`): the train and dev label blocks of the G.5 T1 tables, with the T1 nodes' G.1b noise summaries `<T1_NODE>`: `<G1B_SUMMARY_PATH>` (sha256 `<G1B_SUMMARY_SHA256>`), partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. No test label and no evaluation value is released by this row. |
| R1-T1-LABELS-TEST-RELEASE | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`), after the arms-frozen record `<ARMS_FROZEN_RECORD_PATH>` (sha256 `<ARMS_FROZEN_RECORD_SHA256>`): the test label blocks and every evaluation block of the G.5 T1 tables, partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. |

## What each row lets the release step do

- **Train/dev rows** (R1-S2-LABELS-TRAINDEV-RELEASE, R1-T1-LABELS-UNSEAL):
  - The step writes `label_block.traindev.jsonl` (the label rows of P3 train and dev instances, byte-identical lines) and its
    receipt, after the source's integrity check passes.
  - No test label and no evaluation value leaves the release step. The evaluation block is opened only by the integrity
    check, which returns pass/fail, counts and hashes (§6 carve-out).
- **Test rows** (R1-S2-LABELS-TEST-RELEASE, R1-T1-LABELS-TEST-RELEASE):
  - After the arms-frozen record, the step writes `label_block.test.jsonl` and `evaluation_block.all.jsonl` and their
    receipt, from the same label block and table as the traindev release.
  - From then on the raw-block locks of the tier open (`release.test_released`). A reader that does not know its tier
    needs both tiers' test rows.

## Points for the author (proposed decisions; options and a recommendation)

**REL-SCOPE: what the test rows open.**
- A (recommended, implemented): PRE-STAGE A as signed. Until the test row exists, readers get train/dev labels only. After
  it, the tier's raw blocks may be read, for example by `offline_eval` for descriptive work. A reader that cannot tell its
  tier (`offline_eval`, `env`, `ni_masking`) needs both tiers' test rows, so it stays locked for good if no T1 test row is
  ever written (fail closed).
- B: only the gate-input builder and the fold module read test partitions, and raw readers stay locked for good. This
  matches the G.5 draft's "test partition … to the gate run only", which concerns T1.

  Under B a PLAN row is needed, and the T1 rows would differ.

**REL-CODE: how later code changes interact with the rows.**
- A (recommended, implemented): integrity checks live in `r1/c3/release_checks.py`. Registering the sweep-2 or G.5 check
  changes that file, not `release.py`. Readers bind each receipt to its own release-code commit. The release step requires
  the committed, published `release_checks.py`.

  Limit: any edit of `release.py` itself makes a new write under the same row impossible (the writer must run the cited
  file). Amending the row to a new commit changes its text and commit, which voids every earlier receipt under it. So
  `release.py` should be final before the first T0 row, or the T0 rows must be split per source.
- B: every integrity check is registered before the first row.
- C: one row per source.

**REL-T1-G1B: the G.1b host.** PRE-DELTA says the T1 σ_node and δ_n come from "each node's sealed G.1b summary on H200".
R1-T1-HOST-TASL moved G.1b to the TASL pair (RTX 4090). The T1 train/dev row binds whichever summaries the author
designates. Proposed: an author note that "on H200" reads "on the T1 host of R1-T1-HOST-TASL".

PRE-DELTA also calls the summaries "sealed". The release step checks committed files only and refuses sealed paths, so a
reviewed copy-out of each summary into the repository, with its sha256, must come first.

## Before the rows can be used (conditions, not decisions)

- **Integrity checks.** A reviewed integrity check per source is registered in `r1/c3/release_checks.py`. Today only
  `sweep1` is registered (the sweep-1 B.2 audit, `audit.verify_evidence_completion`). Sweep 2 and the G.5 tables have no
  labelled audit yet (sweep 2's B.2 needs its own authorization, R1-SWEEP2-SETTINGS (2)), so their release STOPs until their
  check is reviewed and registered.
- **G.5 completion schema.** A G.5 evidence writer must use its own completion schema, not the B.2 audit's
  `r1.c3_audit_completion/`. `audit.RunCache` infers T0 from that prefix and would otherwise open a G.5 run log under the T0
  test row alone.
- **G.5 outputs.** The G.5 outputs are sealed (a tar under the sealed tree), and the release step refuses sealed paths. A
  reviewed extraction step must first place the G.5 label and evaluation blocks, with their completion record, in an
  unsealed audit directory, with its own hashes.
- **Where the step runs.** The release step runs where the audit outputs live (the cluster). It refuses a checkout with
  tracked changes, and a checkout whose PLAN, preregistration, `release.py`, `release_checks.py`, gate, builder, split file,
  `p3_split`, `audit`, `dataset` or `analysis_guard` differ from `origin/main`.
