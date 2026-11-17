# DRAFT — B.2 start ruling and authorization addendum (packet e2)

**Draft by the Mac-local worker (Claude), MAC_LOCAL_RUNBOOK_20261104 M3 step 5; AI-assisted, 4 November 2026. This is not a ruling and not an authorization.** R1-B2-REPLAY-GO: after the replay shows zero differences, the author gives e2 as a separate later ruling that lifts R1-B2-DECOUPLE's "does not start", together with the B.2 authorization addendum. Placeholders are in `<angle brackets>`.

**Update 17 Nov 2026 (Mac-desk agent, AI-assisted).** The author signed **R1-B2-GO** (`author-decisions-20261117b` @ `33c82351`) and chose B6 (a), B4 (a) and B1 (a) in Part 1, so Part 2 is superseded by the signed row. The code for those choices is the e2 code unit, branch `mac-e2-code-20261117`, report `reports/E2_CODE_UNIT_20261117.md`. **Part 3 is now filled in** for the author to commit as `docs/r1/authorizations/c3_b2_addendum_20261117.md` on `main`; only the `<author: …>` items are left. The text above the Part 3 heading is the 4 November draft, kept as it was.

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

## Part 3 — authorization addendum (filled 17 Nov 2026 for the author; commit as `docs/r1/authorizations/c3_b2_addendum_20261117.md`)

# Addendum to `c3_sweep1_20261027.md`: B.2 fresh-seed audits of sweep 1

Committed on the author's instruction of `<author: date, time>`: "`<author: words>`". The original note already covers "B.1 sweep 1 and B.2 audits". This addendum binds the B.2 run to the e2 code and to the e2 ruling **R1-B2-GO** (17 Nov 2026), which lifts R1-B2-DECOUPLE's "does not start" for the sweep-1 fresh-seed audits only.

**Scope.** One complete EVIDENCE audit of the classified sweep-1 batch: every eligible proposal of both memory modes, with K = 10 fresh joint seeds, run by the operator (O4 step 2). Not authorized:
- retraining, C3 or Track P training, or tuning or selection on 7006–7010;
- any resume of a stopped audit;
- any other batch.

**Pins.**

| Item | Value | Source |
|---|---|---|
| Paper code | `<author: the full 40-character e2 commit accepted by its review, see reviews/E2_CODE_UNIT_REVIEW_20261117.md>`. The operator checks out exactly this commit, which must be an ancestor of the published `main`; `main` is fast-forwarded to it and `docs/r1/PLAN.md` is not changed on `main` until the audit has started (the classification guard compares the checkout's `PLAN.md` with the published one) | the review's `Code-Commit:` / `Verdict: ACCEPTED` lines, published on `main` |
| Harness | `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, tracked-clean, at the path the e1 replay checked (`…/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness`). Its only untracked files are those the e1 record names: the six OpenML data caches, whose tree digests must equal the e1 post-run record, and `paper/tables/artifact_completeness_report.txt` | R1-SWEEP1-CLASSIFY; R1-HARNESS-NEXT-PIN; e1 `pins.json` |
| Environment basis (R1-B2-GO **B6 (a)**) | The published, independently reviewed e1 replay report `docs/r1/reports/e1_replay_20261117/`: 16/16 cases at tolerance 0, under the R1-E1-OPENML-AMEND identity basis; review `docs/r1/reviews/E1_AMEND_RUN_REVIEW_20261117.md` (ACCEPTED); branch `ops-e1-replay-amend-20261117` @ `52992b22`, whose files the code reads at that commit (an ancestor of `main`); corrections the e1 review asks for go into a separate erratum file, never into the pinned files. At audit start the code re-runs the replay's current-environment checks and requires the recorded values: wrapper target, Python 3.13.15, sklearn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1, `uv.lock` `dd42d018…`, the 25 Oct freeze plus narwhals 2.27.1, package list `c09242ac…`, and newest dist-info mtime `2026-10-26T22:09:12Z`. This replaces `prepare.json:sweep_environment_sha256`. It is a current-state observation, not a launch-bound freeze, and every record says so | R1-B2-GO; R1-E1-OPENML-AMEND |
| Worker runtime (R1-B2-GO **B4 (a)**) | The existing per-run `worker_runtime` probe record, from a separate probe process using the worker's `PATH` and `python3`. Its limitation is disclosed in `environment.json` and `evidence_completion.json`: **it does not attest the task process itself** | R1-B2-GO |
| Publication (R1-B2-GO **B1 (a)**) | This addendum, the R1-B2-GO row, the e1 replay report and its review, the e2 code review, the classification row, sidecar, index and authorization note must all be on `main`. The guards read them from `origin/main` | R1-B2-GO |
| Classification | sidecar `bb6d891c…`; index `812468e2…`; authorization `c3_sweep1_20261027.md` `563374f6…` | R1-SWEEP1-CLASSIFY |
| Table | Built by `python -m r1.c3.dataset build-sweep --classification …`. The dry run on the frozen corpus gives 4,999 proposals, `proposals.jsonl` `b713c42338c4…` and `configs.json` `b585b7275866…`. The host build must give the same counts and hashes; any difference is a STOP to report before the audit | `reports/MAC_M3_DRYRUNS_20261104.md` §2 |
| Audit design | K = 10; label seeds 7001–7005 and evaluation seeds 7006–7010, in separate blocks; duplicates get no label; no-ops are labelled by rule | authorization; R1-SWEEP1-CLASSIFY |
| Expected population | 1,725 eligible (466 unique configurations, 4,660 seed runs), 3,274 duplicates, 0 no-ops | dry run; R1-B2-GO |

**Host and workers** (R1-B2-GO; this revises the "fixed HTCondor CPU class" wording of R1-SWEEP2-SETTINGS (3) for this audit).
- Host: **deepthought, CPUs only**: the same host and environment as e1.
- **Workers: 16** (authorization `c3_sweep1_20261027.md`). The code refuses more than 16, or a number at or above the CPU count.
- **At least 10 of deepthought's 40 cores stay free for other users** (operator O4).
  - The operator checks this immediately before launch, as e1 did (`logs/cotenancy.log`).
  - If 16 workers would leave fewer than 10 free cores, the operator uses fewer workers and records the number.
  - If other users' load during the run leaves fewer than 10 free cores, that is a STOP.
- Scratch: a new local `/tmp/r1_c3_audit_EVIDENCE_<stamp>`.
- Output: a new `results/r1/evidence/C3_audit_EVIDENCE_<stamp>`.
- Ceph: at least 50 GiB free, and the file-count reserve the operator states.
- Estimate: about 2.5 CPU-h from recorded trial times, so about 10 min wall time at 16 workers plus overhead. The authorization's provisional estimate is 2–3 h.
- Command (on deepthought, from the paper checkout at the accepted e2 commit, in the batch venv, with `AR_HARNESS_ROOT` set to the batch harness and the batch wrappers first on `PATH`, as for e1; with `PYTHONDONTWRITEBYTECODE=1`, so the shared venv stays unchanged as in e1; without the batch `env.sh` `PYTHONPATH`, which the provenance guard refuses):
  ```
  PYTHONDONTWRITEBYTECODE=1 python -B -m r1.c3.audit evidence-run --table <host table> --paper-root <checkout> \
      --index results/r1/pilot/C3_sweep_index_20261028T033315Z.json \
      --classification results/r1/evidence/C3_sweep_classification_20261028.json \
      --out results/r1/evidence/C3_audit_EVIDENCE_<stamp> --workers 16 --deadline <operator> \
      --code-commit <accepted e2 commit> --code-review docs/r1/reviews/E2_CODE_UNIT_REVIEW_20261117.md \
      --addendum docs/r1/authorizations/c3_b2_addendum_20261117.md \
      --scratch-root /tmp/r1_c3_audit_EVIDENCE_<stamp> --required-scratch-bytes <operator> \
      --ceph-reserve-files <operator>
  ```
  The code reads this file from `origin/main`. It requires the file to contain `R1-B2-GO`, the paper code commit above, the harness pin, and `K = 10`.

**Pass rule.** The audit is complete when all of the following hold:
- every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and its incumbent;
- `label_block.jsonl` and `evaluation_block.jsonl` are written and match the raw runs on recomputation;
- `evidence_completion.json` (schema `/3`) binds all hashes, this addendum, the environment basis and the worker-runtime limitation;
- the counts by kind equal the plan's.

Labels count only after an independent review and the author's separate label-table freeze (R1-B1-CORPUS-FREEZE).

**STOPs.** Retain everything; there is no automatic resume.
- Any guard failure:
  - classification, publication or paper provenance;
  - environment: the e1 replay basis, or the current-environment checks differing from the replay;
  - a host other than deepthought; an untracked harness file outside the e1 record, or an OpenML cache tree differing from the e1 post-run digest;
  - worker runtime record, resources or output path.
- The host table differs from the dry run's.
- Any failed, missing, non-finite or file-changing seed run.
- The deadline is passed, or a resource floor is reached.
- An interruption, or other users' load leaving fewer than 10 free cores.
- Any use of 7006–7010 outside the evaluation block.
