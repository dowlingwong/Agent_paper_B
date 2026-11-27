# Round-2 review — corrected Expansion G.1b four-node result (`compute/20261126-10`)

**Verdict: ACCEPTED.** Round-1 finding B1 is fixed correctly, the newly captured seal receipts match the report
table and the live tree, and the correction introduces no new overclaim or contradiction.

- Round 1: `docs/r1/reviews/G1B_X_RESULT_REVIEW_20261127.md` (NOT ACCEPTED at `2ef8e436`), sha256
  `35f262664d5fac213615856385787d1b6a4f4cd56598da23df7c61b51006bb0b`; its findings stand as history.
- Round-2 deliverable: branch `compute-expansion-g1b-20261127` @ `50fc9cbc96147ed2dd28ff9826915167810eb292`
  (one commit over `2ef8e436`), base `origin/main` `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`.
- Delta (`git diff --name-status 2ef8e436 50fc9cbc`): one modified report and three added receipts
  (`SEAL_RECEIPT_mlgym_metamaze.json`, `SEAL_RECEIPT_gc7rc_forestcover.json`, `SEAL_RECEIPT_gc7rc_etth1.json`);
  `summary.json`, `ASSEMBLY.json`, `edits.json` and `SEAL_RECEIPT_titanic.json` are byte-unchanged.

## (a) The corrected G.5 consequence

The report now says all four nodes completed G.1b with determinism PASS and are eligible to join G.5 by addendum;
D21 is reported as the funnel reading and does not select T1 nodes. That matches, verbatim in substance:

- **R1-T1-D21-SCOPE**: every T1 node that passed U2, G.1b fixed-seed determinism and, where run, the cross-host
  check enters G.5 "regardless of its D21 value; no other threshold is introduced."
- **R1-T1-NODE-EXPANSION**: "A candidate whose G.1b completes with determinism PASS … enters G.5 under
  R1-T1-D21-SCOPE."
- **R1-STEP-ORDER (2)(a)** and **R1-G5-S9 (3)**: the candidate joins by addendum once its G.1b completes with
  determinism PASS.
- The note's `cutoff:` line: `stop: null` + determinism PASS + finished before the cutoff → G.5 addendum. All four
  job records read `stop: null`, all four finished 27 Nov, determinism PASS.
- The report's `R1-G5-S9 (2)` split is right: `mlgym_metamaze`/`mlgym_titanic` enter the arms and primary gate;
  `gc7rc_etth1`/`gc7rc_forestcover` are labelled only and reported as descriptive extra tasks (R1-1GC-FALLBACK).
- "T0" is corrected to T1, and the "no further author decision" statement is consistent with the publication rows:
  the coordinator publishes the addendum; an independent review of it is still required, but that is not an author
  decision.

The determinism section now states the gate explicitly and matches `summary.json` (repeat = first outcome metric,
`divergent` 0 in every configuration). The D21 table, funnel line, `gc7rc_etth1` 0.0073 miss and Titanic NaN are
unchanged and still reported; the negative result is not hidden.

## (b) Captured seal receipts

All four files hash exactly to the report's table and to the live sealed tree (`ssh tasl2`, read-only):

| File | sha256 | Report table | Live receipt |
|---|---|---|---|
| `SEAL_RECEIPT_mlgym_metamaze.json` | `897fadbaceef595386554cf4f4aef05dac5cf83cbf1a705264f53cb8f3e5de10` | same | same |
| `SEAL_RECEIPT_gc7rc_forestcover.json` | `2940254a01b7136d76eb2ed310536a7bf92cf5b03b373cffa8408ca285433506` | same | same |
| `SEAL_RECEIPT_gc7rc_etth1.json` | `96dad194c74b5dafb790ea3451cb7c6dd7763efd2c5e28737fe9306dd2bd02d7` | same | same |
| `SEAL_RECEIPT_titanic.json` | `13773f1541b2d84cb5545fb80601babf6e087ae9b535cc50849870c03de00207` | same | same |

Each receipt's `job_record_sha256` equals the report's job-record column (`e1bc3229…`, `6d9a0ad8…`, `2c50d59a…`,
`ac23a7c1…`), each `sealed_utc` matches the report's ordering (27 Nov 00:37, 07:05, 15:29, 18:31), and each
receipt's `node_log_sha256` matches the live `node.log`. Three are new captures; Titanic's is the round-1 file,
unchanged.

## (c) No new overclaim or contradiction

- No numeric claim changed; the D21 values, funnel, hashes and timing are identical to round 1.
- New base/branch line is correct (`c80f83bc`, `compute-expansion-g1b-20261127`).
- The pre-attempt refusal disclosure is accurate: four run-root logs at `22:52:49Z` stopped with exit 2 on the
  origin-path check, and the attempt directories carry `attempt.json` from the successful `22:53:26Z` launch, so
  "created no attempt directory and are not attempts" holds. It consumes no attempt and does not weaken "Attempt 1".
- The NaN/strict-JSON sentence is accurate: the file is Python `json.dump` output with a bare `NaN`; strict parsers
  may reject it. The report now says so instead of implying universal JSON.
- The "bit for bit" wording is gone; "reproduces the first run's outcome metric" is exact.
- The "R1-STEP-ORDER step 1" line is gone; the citation is now (2)(a).

Residual, non-blocking (round-1 minors only partly closed):

1. The 460/460 and start-time claims are still not checkable from the branch: the receipts bind the
   `job_record.json` digests, but the job records themselves are not captured. This was verified live in round 1
   and again here; capturing the four job records would close it.
2. The report now gives the base commit and branch but still has no checker/AI-assisted line and no checkout path.
3. `G5_EXPANSION_ADDENDUM_TEMPLATE_20261127.md` is still a draft and states the G.5 switch has no addendum reader
   yet. The report's "join" is the entitlement under the rows, not an executed join; a half-sentence naming that
   engineering prerequisite would keep a later reader from over-reading the present tense. This is a caveat, not a
   contradiction.

## Scope

I re-fetched `50fc9cbc`, read the full corrected report, re-hashed the four receipts and their job-record/log
bindings, and re-checked the affected PLAN rows, the note's `cutoff:` line and the addendum template. I did not
write to the deliverable branch or the TASL-2 sealed/assembly roots, and I opened no label or evaluation row.
