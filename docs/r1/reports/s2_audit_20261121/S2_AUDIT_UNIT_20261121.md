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
  - `verify`: re-derives the per-mode manifests and the index from the copied chunk manifests and `EXTRACT.json`, and
    re-hashes every file;
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
  - the sweep-2 addendum (`c3_sweep2_b2_addendum_*.md`, naming R1-SWEEP2-B2-GO, the run id, the code commit, harness
    `6adf3859` and K = 10), with the start row required on `origin/main`;
  - the harness-equivalence check (`nodes`, `configs`, `harness` and `src/autoresearch/worker` equal at `6adf3859`
    and `a3fedbbd`);
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

## Tests

`r1/tests/test_c3_sweep2_audit.py`, 18 tests on synthetic sealed chunks (one node, two instances, both modes) in the
seal layout:
- extract, verify, `build-sweep`, counts and the audit's sweep-2 plan;
- nine extract refusals: a changed ledger byte, an uncounted record, wrong pins, audit seeds, noise values, root
  failures, a missing campaign, an unlisted file, the counts file;
- the mode-manifest merge;
- write-once, and tampering caught by `verify` (a changed byte, an extra file, a manifest edited together with its
  `EXTRACT` entry and index binding);
- the sweep-2 addendum and start row;
- harness equivalence in a scratch git repository;
- the completion records of both profiles;
- the integrity check's registration and wrapping, and the shadowing check;
- a profile mismatch refused both ways.

Targeted runs of the existing evidence, audit, release and dataset tests pass:
- 97 passed for `test_c3_sweep2_audit`, `release`, `evidence_*` and `attestation`;
- 45 passed for `audit`, `dataset`, `trackp_p3` and `p3_split`;
- the e2 environment-basis, authorization, boundary, seed-isolation, table and guard modules pass.

## Limits

- The sealed chunk layout and manifest fields are taken from the code that wrote them; no real chunk was read here.
  `extract` refuses on any mismatch. The first run on deepthought (precondition 2 of the draft) is therefore also the
  check of these assumptions.
- The eligible count, and with it the time estimate, comes from `sweep2_batch counts` on the real table. The draft
  carries the sweep-1 scaling (4,660 seed runs in 23 min at 16 workers) until then.
