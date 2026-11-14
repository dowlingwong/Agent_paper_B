# DRAFT — B.2 start ruling and authorization addendum (packet e2)

**Draft by the Mac-local worker (Claude), MAC_LOCAL_RUNBOOK_20261104 M3 step 5; AI-assisted, 4 November 2026. This is not a ruling and not an authorization.** R1-B2-REPLAY-GO: after the replay shows zero differences, the author gives e2 as a separate later ruling that lifts R1-B2-DECOUPLE's "does not start", together with the B.2 authorization addendum. Placeholders are in `<angle brackets>`.

**Read first:** `reports/MAC_B2_GATES_20261104.md`. Even with e2, the B.2 code on this branch **stops by design** at three gates:
- **B4:** no task-native runtime attestation; `_require_task_native_runtime_attestation` stops every EVIDENCE run and every EVIDENCE consumption.
- **B6:** no published report bound to a pre-launch full freeze; `original_sweep_environment`.
- **B1:** the classification, PLAN row and review must be byte-identical on `origin/main`; `_verify_published`.

These STOPs were written on purpose after the BLOCK reviews (`C3_AUDIT_SPLIT_PACKAGE_REVIEW_20261028`, `C3_EVIDENCE_GUARDS_REVIEW_20261028`, `C3_SWEEP1_ENVIRONMENT_INVESTIGATION_20261028`). e2 has to say what replaces each of them. The options below are for the author; **the Mac agent has not chosen any of them and has not changed that code.** Once the author picks, the code change and its review are a follow-up task (Q1–Q2 in `reports/MAC_M3_HANDOFF_20261104.md`).

---

## Part 1 — choices the author makes in e2

**(i) B6: the environment basis for B.2.** No launch-bound freeze exists, and the investigation found none.
- (a) A passed 16-case replay (e1) plus the current-environment checks of the replay (same wrapper target, versions, `uv.lock`, freeze + narwhals, dist-info mtimes) replace the bound freeze for B.2. The code then accepts a published replay report in place of `prepare.json:sweep_environment_sha256`, with the replay's disclosure carried into every B.2 record.
- (b) Keep B.2 stopped until some other historical record is found.
- (c) Another, independently reviewed exception the author defines.

**(ii) B4: the per-run runtime record.**
- (a) Accept the existing per-run probe record (`worker_runtime` from a separate probe process, recorded per seed run), with the limitation disclosed: it does not attest the task process itself ([AS]: NOT CHECKABLE).
- (b) Require a task-native attestation first. A reviewed design is needed that keeps the frozen harness `6adf385`, its arguments, working directory, import behaviour and numerics unchanged, as [AS] requires. That is code not yet written, and it may need a harness-side hook, which R1-HARNESS-NEXT-PIN keeps off the sweep-1 pin.
- (c) Another, independently reviewed exception.

**(iii) B1: the publication target.** The guards check `origin/main`.
- (a) Publish the classification row, sidecar, index, authorization note, this addendum and the accepted review to `main`. This needs the author's push; the runbook forbids the agents to push `main`.
- (b) Change the guards to a named, author-pinned branch and commit. That is a code change plus review.

## Part 2 — paste-ready ruling row (fill after choosing)

```
| R1-B2-GO (<date>) | **B.2 starts.** Lifts R1-B2-DECOUPLE's "does not start" for the sweep-1 fresh-seed audits only. Preconditions met: the environment replay `<report path>` passed 16/16 at zero tolerance and was independently reviewed (`<review path>`); the M3 gate table `reports/MAC_B2_GATES_20261104.md` is closed or ruled here. Rulings on the open gates: B6 <(i)(a|b|c) text>; B4 <(ii)(a|b|c) text>; B1 <(iii)(a|b) text>. Labels use 7001–7005, evaluation 7006–7010 (R1-SWEEP1-CLASSIFY clarification); the label table is frozen separately after review (R1-B1-CORPUS-FREEZE). Addendum: `docs/r1/authorizations/c3_b2_addendum_<date>.md`. |
```

## Part 3 — authorization addendum (draft)

# Addendum to `c3_sweep1_20261027.md`: B.2 fresh-seed audits of sweep 1

Committed on the author's instruction of `<date, time>`: "`<author's words>`". The original note already covers "B.1 sweep 1 and B.2 audits". This addendum binds the B.2 run to the post-classification code and to the e2 ruling R1-B2-GO.

**Scope.** One complete EVIDENCE audit of the classified sweep-1 batch: every eligible proposal of both memory modes, with K = 10 fresh joint seeds, run by the operator (O4 step 2). Not authorized: retraining, C3 or Track P training, tuning or selection on 7006–7010, any resume of a stopped audit, and any other batch.

**Pins.**

| Item | Value | Source |
|---|---|---|
| Paper code | `<accepted commit carrying the e2 code changes>` | its independent review (`Code-Commit:` / `Verdict: ACCEPTED`) |
| Harness | `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, clean | R1-SWEEP1-CLASSIFY; R1-HARNESS-NEXT-PIN |
| Interpreter and versions | as in the e1 note (batch wrappers → shared venv; Python 3.13.15; sklearn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1; `uv.lock` `dd42d018…`) | replay draft; e1 |
| Classification | sidecar `bb6d891c…`; index `812468e2…`; authorization `563374f6…` | R1-SWEEP1-CLASSIFY |
| Table | built by `python -m r1.c3.dataset build-sweep --classification …`. The dry run on the frozen corpus gives 4,999 proposals, `proposals.jsonl` `b713c42338c4…` and `configs.json` `b585b7275866…` in this workspace; the host build is expected to give the same counts and hashes (byte identity across the two Python environments is expected but not verified); any difference is a STOP to report before the audit | `reports/MAC_M3_DRYRUNS_20261104.md` §2 |
| Audit design | K = 10; label 7001–7005, evaluation 7006–7010, in separate blocks; duplicates get no label; no-ops are labelled by rule | authorization; R1-SWEEP1-CLASSIFY |
| Expected population | 1,725 eligible (466 unique configurations, 4,660 seed runs), 3,274 duplicates, 0 no-ops | dry run |

**Host and workers.**
- Host: deepthought, CPUs only.
- **Workers: 16** (authorization `c3_sweep1_20261027.md`; the code caps workers at 16 and below the CPU count).
- At least 10 cores are left free for other users (operator O4). If 16 workers would break that, use fewer and record the number.
- Scratch: a new local `/tmp/r1_c3_audit_EVIDENCE_<stamp>`.
- Output: a new `results/r1/evidence/C3_audit_EVIDENCE_<stamp>`.
- Ceph: at least 50 GiB free, and the file-count reserve the operator states.
- Estimate: about 2.5 CPU-h, from recorded trial times. The authorization's provisional estimate is 2–3 h.

**Pass rule.** The audit is complete when:
- every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and its incumbent;
- `label_block.jsonl` and `evaluation_block.jsonl` are written and match the raw runs on recomputation;
- `evidence_completion.json` binds all hashes;
- the counts by kind equal the plan's.

Labels count only after an independent review and the author's separate label-table freeze (R1-B1-CORPUS-FREEZE).

**STOPs (retain everything; no automatic resume).**
- Any guard failure: classification, publication, paper provenance, environment, worker runtime, resources, output path.
- The host table differs from the dry run's.
- Any failed, missing, non-finite or file-changing seed run.
- The deadline is passed or a resource floor is reached.
- An interruption, or another user's load leaving fewer than 10 free cores.
- Any use of 7006–7010 outside the evaluation block.
