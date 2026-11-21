# Sweep-2 audit unit: batch extraction, the audit's sweep-2 mode, the sweep-2 integrity check

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, on `mac-s2-audit-20261121` over published `main`
`985dd45d`, for item 1 of the queue of 21 Nov 2026 (22:44). This is desk work: synthetic sealed chunks only. No real
sweep ledger, table, label, audit or evaluation file was opened.

The authorization draft is `docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261121.md`, with decisions D1–D6.

## Why three pieces

The audit and release code on `main` know only sweep 1:
- the classification sidecar `R1-SWEEP1-CLASSIFY`;
- the sweep-1 index;
- the sweep-1 authorization and addendum names.

Sweep 2 exists only as 16 sealed chunks in `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/`. Before any audit can be
authorized:
- a reviewed step must copy those chunks out into something the table builder can read;
- the audit needs a sweep-2 mode;
- the release step needs a registered sweep-2 integrity check.

## What changed

- **`r1/c3/sweep2_batch.py` (new).** It provides three commands:
  - `extract`: copies the chunks out (layout and refusals in the module docstring);
  - `verify`: re-derives the per-mode manifests and the index from the copied chunk manifests and `EXTRACT.json`,
    re-hashes every file, and checks each chunk's job-record sha256 against the collection counts published on
    `main`. This is internal consistency only. A ledger edited together with `EXTRACT.json` and the index passes it,
    and a test pins that boundary. What binds the batch to the seal is the addendum's four sha256 pins (below) and
    `verify --sealed`, which re-derives the whole batch from the sealed tree without writing;
  - `counts`: prints the B.2 plan counts from table fields only.

  The index uses sweep 1's schema `r1.c3_sweep_index/1`, so `dataset build-sweep --index … --paper-root …` builds the
  sweep-2 table without code changes; there is no classification sidecar. The pins are taken from `main`:
  - the run id, launch commit `4aac5209`, harness `a3fedbbd`, image digest and authorization sha256 from
    `c3_sweep2_20261119.md`;
  - the collection counts sha256 `3e29382b…` (the published `collection_counts.json`);
  - the D28 noise summary.

  The layout follows `sweep2/s2_c2_lib.py`: `seal` extracts `out/` and `work/` into the sealed chunk and writes
  `SHA256SUMS` over every file. It also follows `r1/headroom/e1b_collect.py`: the manifest fields, `out/roots/<inst>.json`
  start files and `work/roots/<inst>/root_trials.jsonl`.
- **`r1/c3/audit.py`.** `evidence-run --source sweep2` and `verify_evidence_completion(..., source='sweep2')` add:
  - the sweep-2 addendum (`c3_sweep2_b2_addendum_*.md`):
    - it names R1-SWEEP2-B2-GO, the code commit, harness `6adf3859` and K = 10;
    - its key block reads exactly `approved: true`, `label: EVIDENCE`, the run id and the start ruling, with no
      duplicate keys;
    - it pins the index, `EXTRACT.json`, `proposals.jsonl` and `configs.json` sha256s, checked at the audit start and
      again on consumption;
    - the start row must be exactly one author row in a dated §10 table on `origin/main` (`release.author_rows`),
      naming the run id, R1-SWEEP-HOST-HTC, R1-B2-DECOUPLE and B6 (a), B4 (a), B1 (a);
  - the harness-equivalence check: `nodes`, `configs`, `harness`, `uv.lock`, `src/autoresearch/worker`, `nodes`
    registry, `common` and `manager/base.py` are equal at `6adf3859` and `a3fedbbd`. The full list of files changed
    elsewhere is recorded, and the verifier re-runs the check where the harness is present;
  - the sweep-2 plan: `sweep2_batch.verify`, the table bound to the index, a full replay rebuild, the same partition;
  - the completion schema `r1.c3_audit_completion/4`, carrying `source: sweep2` and `extract_sha256`, and binding the
    sweep-2 authorization.

  The sweep-1 path is unchanged: the completion's keys, order and values are tested against the old list, and the
  existing evidence tests pass unchanged.
- **`r1/c3/release_checks.py`.** `sweep2_integrity` is registered, and `COMPLETION_KEEP` gains `source` and
  `extract_sha256`. Because `release.py` is pinned by R1-S2-LABELS-TRAINDEV-RELEASE (`a9d8ff5e`), it is not edited:
  - the check itself verifies that `r1/c3/sweep2_batch.py` is the plain module beside it and equals `origin/main`;
  - the release CLI already passes `--paper-root` and `--index` through, without `--classification`.
- **`r1/tests/test_c3_release.py`.** One test asserted "no release row on the checkout yet". Main `985dd45d` signed
  R1-S2-LABELS-TRAINDEV-RELEASE, so the test now asserts that exactly that row is present and parses as the release
  step reads it. The test failed on `main` before this change.

## Round-1 revisions (review of 21 Nov)

- **M1:** the addendum pins and their checks, `verify` against the published counts, `verify --sealed`, and the
  docstring reworded.
- **M2:** the `approved: true` key block is enforced.
- **M3:** D1 names R1-SWEEP-HOST-HTC and R1-B2-DECOUPLE, and the start-row check requires both.
- **M4:** a pins STOP, and an independent review of the precondition-2 output before signature.
- **Minors 1–14:**
  - `extract` calls `require_d8_confirmation()` first;
  - suffixed root ledgers are refused;
  - the collector harness must be clean;
  - `action_versions` is added to the common keys, and one manager across the modes is required;
  - stopped chunks must be admitted, with matching record sha256s;
  - the extra-file check compares top-level paths;
  - the sealed path is recorded as a constant;
  - the harness paths are widened and re-checked;
  - the start row is found with `author_rows`;
  - D2 and D3 wording corrected;
  - the estimate argument replaced by a counts-based deadline;
  - a new table directory and an unchanged PLAN are required;
  - the tests listed below.

## Round-2 minors (fixed after acceptance)

- D2 wording: `memory/summarizer.py` is imported via `manager/base.py`; its diff is opt-in display modes only.
- `extract` refuses a sealed path other than `SEALED_RUN_DIR`, so a copy elsewhere is not recorded as the source.
- The addendum's `precondition2_review` is required: on `origin/main`, `Verdict: ACCEPTED`, containing the four pins.
  It is recorded with its sha256.

## Tests

`r1/tests/test_c3_sweep2_audit.py`, 28 tests on synthetic sealed chunks (one node, two instances, both modes) in the
seal layout:
- extract, verify, `build-sweep`, counts and the audit's sweep-2 plan;
- fourteen extract refusals:
  - a changed ledger byte, an uncounted record, wrong pins;
  - audit seeds, noise values, root failures;
  - a missing campaign, an unlisted file, the counts file;
  - an unadmitted stop, a suffixed ledger, a dirty collector harness, a manager differing across modes;
  - a sealed path other than the declared one;
- an admitted stopped chunk extracts and verifies, with the admitted-record cross-check;
- `verify` passes a consistently forged batch, which `verify --sealed` refuses (the M1 boundary pinned); a planted
  nested `EXTRACT.json` is caught;
- the pins check (each of the four);
- the mode-manifest merge, including `action_versions`;
- write-once, and tampering caught by `verify` (a changed byte, an extra file, a manifest edited together with its
  `EXTRACT` entry and index binding);
- the sweep-2 addendum and start row: the key block, duplicates, short pins, a missing token, a duplicated row, a
  fenced row, and the precondition-2 review (verdict, pins, path);
- harness equivalence in a scratch git repository;
- the completion records of both profiles;
- the integrity check's registration and wrapping, the shadowing check and its git branch;
- a profile mismatch refused both ways;
- a positive end-to-end `verify_evidence_completion(source='sweep2')`, and its refusal when the index differs from
  the pins.

Targeted runs of the existing evidence, audit, release and dataset tests pass:
- round 1: 97 passed for `test_c3_sweep2_audit`, `release`, `evidence_*` and `attestation`; 45 for `audit`,
  `dataset`, `trackp_p3` and `p3_split`; the e2 environment-basis, authorization, boundary, seed-isolation, table and
  guard modules;
- after the revisions:
  - 28 for `test_c3_sweep2_audit` (after the round-2 minors), with 7 for `evidence_authorization`;
  - 81 for `release`, `evidence_split_blocks`, `evidence_authorization` and `evidence_guards`;
  - 38 for `audit`, `e2_environment_basis` and `dataset`;
  - 42 for `audit_dryrun`, `p3_split` and `trackp_p3`.

## Limits

- The sealed chunk layout and manifest fields are taken from the code that wrote them; no real chunk was read here.
  `extract` refuses on any mismatch. The first run on deepthought (precondition 2 of the draft) is therefore also the
  check of these assumptions.
- The eligible count, and with it the time estimate, comes from `sweep2_batch counts` on the real table. The draft
  carries the sweep-1 scaling (4,660 seed runs in 23 min at 16 workers) until then.
