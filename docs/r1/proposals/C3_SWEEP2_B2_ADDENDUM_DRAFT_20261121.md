# Draft addendum: B.2 fresh-seed audits of C3 sweep 2 on deepthought (approved: false)

**This is a draft, not an authorization.** The Mac-desk agent (Claude, AI-assisted) prepared it on 21 Nov 2026 for
R1-SWEEP2-SETTINGS (2): "the sweep-2 authorization holds no B.2 audit; a later addendum adds it; R1-B2-DECOUPLE and
R1-B2-REPLAY-GO unchanged". It follows the queue of 21 Nov 2026 (22:44): "on the deepthought CPU like sweep 1's B.2".
For the host and the environment only, it replaces the reviewed HTCondor draft of 17 Nov
(`proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261117.md`, written for R1-SWEEP2-B2-DRAFT).

**What this unit delivers with the draft** (all on `mac-s2-audit-20261121`, independently reviewed):
- `r1/c3/sweep2_batch.py`: it copies the 16 sealed chunks of `s2ev-20261119-a` out of the sealed tree into a sweep
  batch. Every file is checked against the sealed `SHA256SUMS`, every job record against the published collection
  counts (`3e29382b…`), and the pins. It writes an index in sweep 1's schema, so `dataset build-sweep` builds the
  sweep-2 table unchanged. It also provides `verify` (internal consistency, plus `--sealed` for a full
  re-derivation from the sealed tree) and `counts`.
- A sweep-2 mode of `r1/c3/audit.py`: `evidence-run --source sweep2`, with completion schema `/4`.
- The sweep-2 integrity check, registered in `r1/c3/release_checks.py`.

How the author uses this draft:
1. Decide D1–D6.
2. Commit the start row (D1) together with the addendum. The block between the two rules goes to
   `docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md` on `main`, with the `<…>` fields filled.
3. Set `approved: true` yourself. The agent never sets it. The code refuses an addendum whose key block does not
   read exactly `approved: true`, `label: EVIDENCE`, `sweep2_run_id: s2ev-20261119-a` and
   `start_ruling: R1-SWEEP2-B2-GO`, or that lacks the four full sha256 pins (below).

PLAN §10 rows take precedence wherever they differ from this draft.

## Author decisions

**D1. Host, and the start row.** Two signed rows name a different host:
- **R1-SWEEP-HOST-HTC** (16 Nov, PLAN §10) is the most direct conflict. From sweep 2 on, every C3 label sweep,
  explicitly including sweep 2's B.2 audit, runs as an HTCondor job, and a CPU-only audit runs on one fixed
  HTCondor CPU node type. R1-B2-GO amended the host for sweep 1 only.
- **R1-SWEEP2-B2-DRAFT** (17 Nov) repeats it for this audit: "one fixed HTCondor CPU node type, image digest and
  harness pin the same as sweep 2".

R1-MAIN-PROPOSER (f) ("deepthought's CPUs like B.2") is marked *(proposed)* and was superseded by
R1-SWEEP-HOST-HTC, so it gives no authority. The queue asks for deepthought.
- **A (recommended): deepthought, in sweep 1's B.2 environment** (the e1-replayed batch venv and harness, 16 workers,
  ≥ 10 cores left free). It needs one start row that does three things for this audit only:
  - amends R1-SWEEP-HOST-HTC's host rule;
  - amends R1-SWEEP2-B2-DRAFT;
  - lifts R1-B2-DECOUPLE's "B.2 … does not start" for sweep 2.

  The code requires exactly one such author row in a dated §10 table on `origin/main`, naming the run id,
  R1-SWEEP-HOST-HTC, R1-B2-DECOUPLE, and B6 (a), B4 (a) and B1 (a). Proposed text:

  > `| R1-SWEEP2-B2-GO | The sweep-2 fresh-seed audits of s2ev-20261119-a start under the addendum
  > docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md. For this audit only, amends R1-SWEEP-HOST-HTC
  > (sweep 2's B.2 audit as an HTCondor CPU job) and R1-SWEEP2-B2-DRAFT: host deepthought (CPUs), in the
  > environment of the sweep-1 B.2 audit, with R1-B2-GO's substitutions B6 (a) (the e1 replay as the environment
  > basis), B4 (a) (the worker-runtime probe, its limitation disclosed) and B1 (a) (authority files byte-identical on
  > published main), adopted for sweep 2; harness 6adf3859 for the audit, whose node, config, worker and audited
  > library code equals the sweep-2 pin a3fedbbd (checked at run time). Lifts R1-B2-DECOUPLE's "does not start" for
  > sweep 2's B.2; K = 10; seeds 7001–7005 label, 7006–7010 evaluation; R1-B2-DECOUPLE otherwise unchanged; one
  > host for the table, as R1-SWEEP-HOST-HTC requires. |`

- **B: one HTCondor CPU class in the v1 CPU image**, as the row stands, following the 17 Nov draft. That needs an
  HTCondor CPU job wrapper with its own seal and merge steps, an environment-basis replay on the class, and a
  worker-runtime record decision. None of these exists; this unit's code covers A only.

**D2. The audit harness.**
- **A (recommended): `6adf3859` (sweep 1's audit harness)**, with a run-time check that these paths are identical at
  `6adf3859` and `a3fedbbd`: `nodes`, `configs`, `harness`, `uv.lock`, `src/autoresearch/worker`,
  `src/autoresearch/nodes`, `src/autoresearch/common` and `src/autoresearch/manager/base.py`. The audit imports
  these. The run also records the full list of files changed elsewhere.
  - The agent ran `git diff --stat 6adf385 a3fedbb` on the harness repository. It touches eight files:
    `control_plane/campaign.py` (the cache-prompt record and an opt-in controller ledger view), `control_plane/
    snapshot.py`, `llm/langchain_client.py`, `llm/providers.py`, `manager/langgraph_manager.py`,
    `memory/summarizer.py` and two test files. One of them is imported: `memory/summarizer.py` is imported via
    `manager/base.py`. Its diff adds opt-in memory-display modes (Track S) only, which a no-edit audit run never uses,
    so the labels are not affected. The run-time check covers the listed paths, not what they import.
    `HARNESS_DEFAULTS_CHECK_20261120.md` checked only `configs`, `nodes` and `harness`; the wider list here is this
    unit's.
  - The e1 basis was established at `6adf3859`.
  - Same harness, same environment and same seeds mean twin proposals of the two sources get identical labels, as
    R1-MAIN-PROPOSER (e) expects.
- **B: `a3fedbbd` (the sweep-2 pin).** It needs a new environment-basis replay on deepthought at that pin, and a code
  change (the code pins `6adf3859`).

**D3. Environment basis.**
- **A (recommended): the e1 replay stands for the audit environment** (R1-B2-GO B6 (a), as for sweep 1), plus D2's
  harness-equivalence check. The difference from the collection environment is disclosed:
  - library versions: the v1 image's harness env records Python 3.13.18, NumPy 2.4.4, scikit-learn 1.8.0 and pandas
    3.0.3 (`htcondor_chain_20261114/s5/out/s5_identity.txt`). The e1 basis has Python 3.13.15, so the patch level
    differs. The strongest common fact: the image's `harness_lock_sha256` equals the e1 basis `uv.lock`
    (`dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090`).
  - hosts: collection ran on NEMO2 H200 nodes' CPUs; the audit runs on deepthought.

  Labels are measured in one environment, which is the B.2 design.
- **B:** an additional descriptive replay (for example 16 sealed sweep-2 worker runs on deepthought) of the
  collection metrics. It is report-only, with no tolerance gate: across CPU models a tolerance-0 gate would likely
  STOP on float differences that do not bear on the audit's labels.
- **C:** B as a gate at a stated tolerance. Not recommended without a measured basis for the tolerance.

**D4. Divergent runs.**
- **A (recommended): unchanged from sweep-1 B.2.** A non-finite seed run is a STOP.
- **B:** R1-BX-PROPOSED-CONFIRM REVISIONS (c) (E5: partial labels). The code does not implement it.

**D5. Who extracts and builds, and where.** The extraction reads `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/`.
Recommended:
- the operator runs `extract`, `build-sweep` and `counts` on deepthought (the ETP Ceph mount) before signature, from
  the reviewed code commit;
- the counts and the projection below are entered into the addendum;
- a host where the sealed tree is not readable is a STOP for the author, with no copying by other means.

**D6. Worker runtime.** B4 (a) as for sweep 1: the probe, with its limitation disclosed. Recommended as is.

## Preconditions (all before the first audit seed run)

1. **Code.** This unit (the batch step, the audit's sweep-2 mode, the integrity check) is independently reviewed,
   and its accepted commit is an ancestor of the published `main`. The review file carries `Code-Commit: <sha>` and
   `Verdict: ACCEPTED`.
2. **Batch and table, on deepthought.** Run in the audit's paper checkout at the code commit, with the `docs/`
   overlay from published `main` as for sweep 1:
   ```
   PYTHONDONTWRITEBYTECODE=1 python -B -m r1.c3.sweep2_batch extract --sealed /ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a --paper-root <checkout>
   PYTHONDONTWRITEBYTECODE=1 python -B -m r1.c3.dataset build-sweep --index <checkout>/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json --paper-root <checkout> --out <host table>
   PYTHONDONTWRITEBYTECODE=1 python -B -m r1.c3.sweep2_batch counts --table <host table>
   ```
   `<host table>` must be a new directory (`build-sweep` without a classification does not refuse an existing
   one). Then, as a second-party check:
   ```
   PYTHONDONTWRITEBYTECODE=1 python -B -m r1.c3.sweep2_batch verify --index <index> --paper-root <checkout> --sealed /ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a
   ```
   It re-derives the whole batch from the sealed tree without writing and must report `sealed_rederivation: equal`.

   These four values go into the addendum's key block as full sha256s; the code checks them at the audit start and
   again on consumption:
   - `sweep2_index_sha256`;
   - `sweep2_extract_sha256`;
   - `table_proposals_sha256`;
   - `table_configs_sha256`.

   Also recorded: the counts (eligible, duplicates, no-ops, unique configurations, seed runs).

   **Independent review before signature.** A reviewer who did not run the steps checks the precondition-2 output:
   - the four sha256s, the counts and the `verify --sealed` result;
   - that `build.json` binds the index;
   - that the batch is a new directory.

   The review sees no label. Its file is cited in the addendum as `precondition2_review`. The code requires it on
   `origin/main`, with a `Verdict: ACCEPTED` line and all four pinned sha256 values in it.

   These steps read sweep ledgers and table fields only, never a label or evaluation file. `extract` checks that
   R1-BX-D8-CONFIRM(-V31) is signed before it reads anything.
3. **Harness objects.** Fetch `a3fedbbd` into the batch harness repository (`git fetch origin a3fedbbd…`). This
   writes objects only; the worktree and its untracked state stay as the e1 record requires. The audit checks that
   both commits are present and that the audited paths are equal.
4. **Publication (B1 (a)).** These must be on `main` before the first run; the guards read them from `origin/main`:
   - this addendum and the start row R1-SWEEP2-B2-GO;
   - `c3_sweep2_20261119.md`;
   - the sweep-2 report and its review;
   - the code review;
   - the e1 replay report and review, and R1-B2-GO.
5. **Freshness (R1-SWEEP1-CLASSIFY).** Every sealed chunk shows `b2_audits` none and `audit_seeds` 0; the extraction
   refuses otherwise. No ENGINEERING run on these proposals used 7001–7010.

---

# Addendum to `c3_sweep2_20261119.md`: B.2 fresh-seed audits of sweep 2

<Author's opening paragraph: date, time and instruction.>

```
approved: false
label: EVIDENCE
phase: c3_sweep2_b2
sweep2_run_id: s2ev-20261119-a
start_ruling: R1-SWEEP2-B2-GO
sweep2_index_sha256: <64 hex, precondition 2>
sweep2_extract_sha256: <64 hex, precondition 2>
table_proposals_sha256: <64 hex, precondition 2>
table_configs_sha256: <64 hex, precondition 2>
precondition2_review: docs/r1/reviews/<the precondition-2 review>.md
parent_authorization: docs/r1/authorizations/c3_sweep2_20261119.md (sha256 349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a)
```

**Scope.** One complete EVIDENCE audit of the sweep-2 batch `s2ev-20261119-a`: every eligible proposal of both
memory modes and all eight nodes, with K = 10 fresh joint seeds. The `openml_wdbc` sensitivity row of R1-S2C3B-WDBC
is audited like every node; the analysis scope is the preregistration's. Not authorized:
- training, tuning, threshold choice or selection on 7006–7010;
- any resume of a stopped audit;
- any other batch.

**Pins.**

| Item | Value | Source |
|---|---|---|
| Paper code | `<the accepted commit of mac-s2-audit-20261121>`, checked out detached, with `docs/` overlaid from published `main` as for sweep 1; `r1/` clean | precondition 1 |
| Code review | `docs/r1/reviews/<the unit's review>.md` (`Code-Commit:` / `Verdict: ACCEPTED`) | precondition 1 |
| Harness | `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, tracked-clean, at the e1 path; untracked files only as the e1 record. Node, config, harness and worker code equal to the sweep-2 pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (checked) | D2; R1-B2-GO |
| Environment basis | R1-B2-GO B6 (a): the e1 replay report `docs/r1/reports/e1_replay_20261117/` (16/16 at tolerance 0) and its review, plus the current-environment checks at audit start (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1, `uv.lock` `dd42d018…`) | D3; R1-B2-GO |
| Worker runtime | R1-B2-GO B4 (a): the per-run probe; it does not attest the task process itself (disclosed) | D6 |
| Sweep-2 batch | index `results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json` and `EXTRACT.json`, sha256 as in the key block (enforced); collection counts `3e29382b4d31cef54b92d0cf77a0819b5dedda92aedd528b708f5030b88b6ec7` (each chunk record checked against the copy published on `main`) | precondition 2 |
| Table | `proposals.jsonl` and `configs.json`, sha256 as in the key block (enforced), built from the index (no classification sidecar); the audit also rebuilds the table and refuses any difference | precondition 2 |
| Audit design | K = 10; label seeds 7001–7005 and evaluation seeds 7006–7010 in separate blocks; duplicates get no label; no-ops labelled by rule; completion schema `r1.c3_audit_completion/4`, `source: sweep2` | R1-B2-DECOUPLE; R1-SWEEP1-CLASSIFY |
| Expected population | `<eligible> eligible, <duplicates> duplicates, <noops> no-ops; <unique> unique configurations, <seed runs> seed runs` (from `sweep2_batch counts`) | precondition 2 |

**Host and resources.**
- **deepthought, CPUs only**, in the e1-replayed batch venv.
- **16 workers**, and at least 10 of the 40 cores stay free:
  - checked before launch (`cotenancy.log`);
  - fewer workers if needed, with the number recorded;
  - a breach during the run is a STOP.
- Scratch: a new local `/tmp/r1_c3_audit_EVIDENCE_<stamp>`.
- Output: a new `results/r1/evidence/C3_audit_EVIDENCE_<stamp>`.
- Ceph: ≥ 50 GiB free and the operator's file-count reserve.
- **Estimate.**
  - Sweep-1 B.2 ran 4,660 seed runs in 22 min 44 s at 16 workers (`b2_audit_20261119`: 1,725 eligible, 466 unique
    configurations).
  - Seed runs are 10 × the unique configurations after de-duplication, not a function of the trial count. In sweep 1,
    3,274 of 4,999 proposals were duplicates. The count is bounded by each node's configuration grid, so it can only
    come from `sweep2_batch counts`; no figure is assumed here.
  - Projection: `T = <seed runs> / 4,660 × 23 min` at 16 workers, plus setup and verification. Setup hashes the full
    sealed `work/` trees and rebuilds the table, so allow for tens of minutes rather than a few.
  - Deadline: `max(10,800 s, 2.5 × T)`, entered here once the counts are known. A projection above 2 h at 16 workers
    is reported to the author before launch.
- **Command.** Run on deepthought from the paper checkout at the code commit, in the batch venv, with:
  - `AR_HARNESS_ROOT` set to the e1 batch harness;
  - the batch wrappers first on `PATH`;
  - `PYTHONDONTWRITEBYTECODE=1`;
  - no batch `env.sh` `PYTHONPATH`.
  ```
  PYTHONDONTWRITEBYTECODE=1 python -B -m r1.c3.audit evidence-run --source sweep2 --table <host table> --paper-root <checkout> \
      --index <checkout>/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json \
      --out results/r1/evidence/C3_audit_EVIDENCE_<stamp> --workers 16 --deadline <operator> \
      --code-commit <paper code> --code-review docs/r1/reviews/<review>.md \
      --addendum docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md \
      --scratch-root /tmp/r1_c3_audit_EVIDENCE_<stamp> --required-scratch-bytes <operator> --ceph-reserve-files <operator>
  ```
  The code reads this file from `origin/main`. It refuses unless all of the following hold:
  - the start row is one author row on `main` (as in D1);
  - the file names R1-SWEEP2-B2-GO, the paper code commit, harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7` and
    `K = 10`;
  - the key block reads `approved: true`, `label: EVIDENCE`, `sweep2_run_id: s2ev-20261119-a` and
    `start_ruling: R1-SWEEP2-B2-GO`;
  - the four pins equal the index, `EXTRACT.json` and table the run uses;
  - `precondition2_review` is on `origin/main`, reads `Verdict: ACCEPTED` and contains the four pins.

**Release after the audit.** Once the audit is accepted, the sweep-2 train/dev partition is written under
R1-S2-LABELS-TRAINDEV-RELEASE by:

```
python -m r1.c3.release --stage traindev --source sweep2 --table <host table> --audit <audit dir> --out <release root> --paper-root <checkout> --index <index>
```

Its integrity check (`release_checks.sweep2_integrity`) re-verifies the batch, rebuilds the table, re-derives both
blocks from the raw seed runs, and binds the `/4` completion, this addendum and the start row.

**Pass rule.** The audit is complete when all of the following hold:
- every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and its incumbent;
- both blocks are written and match the raw runs on recomputation;
- `evidence_completion.json` (schema `/4`) binds the batch, the table, the plan, the blocks, the environment, the
  sweep-2 authorization and this addendum;
- the counts by kind equal the plan's.

Labels count only after an independent review of the run and the author's label-table freeze (R1-B1-CORPUS-FREEZE).

**STOPs.** Retain everything; there is no automatic resume.
- The index, `EXTRACT.json`, `proposals.jsonl` or `configs.json` sha256, or the counts, at audit time differ from this
  addendum's values. This matches sweep 1's "host table differs from the dry run's"; the code enforces the four
  sha256s.
- `docs/r1/PLAN.md` changes on `main` while the audit runs.
- Any guard failure:
  - the batch (`sweep2_batch.verify`) or the table rebuild;
  - publication or paper provenance;
  - the environment basis or the current-environment checks;
  - the harness, or its equivalence with `a3fedbbd`;
  - the host, the worker-runtime record, resources or the output path.
- Any failed, missing, non-finite or file-changing seed run.
- The deadline is passed, or a resource floor is reached.
- An interruption, or other users' load leaving fewer than 10 free cores.
- Any use of 7006–7010 outside the evaluation block.

**Disclosures** (in the sweep-2 B.2 report):
- The audit environment (deepthought, e1 basis) differs from the collection environment (v1 image on NEMO2 H200
  nodes' CPUs); the library versions are as in D3.
- Twin pairs across sources are audited in one environment with one harness.
- The R1-S2C3B-WDBC sensitivity row.

---

## Notes for the author (not part of the addendum)

1. **Critical path.**
   1. This unit's review, then `main`.
   2. Precondition 2 on deepthought, including `verify --sealed`.
   3. The counts and sha256s entered into the addendum, and the independent precondition-2 review.
   4. Signature, with R1-SWEEP2-B2-GO.
   5. The audit (duration from the counts), then its review.
   6. The train/dev release.

   The P.3b exam set (R1-P3B-EXAM-DECISIONS: sweep 2's P3 train) waits for that release.
2. **Who fills what.**
   - The author: D1–D6 and the opening paragraph.
   - The operator, on deepthought: the precondition-2 values, the workers, the deadline, the scratch and the reserve.
   - A second party: the precondition-2 review.
   - The code unit's review: the code commit and the review path.
3. The 17 Nov draft remains valid for D1 B.
