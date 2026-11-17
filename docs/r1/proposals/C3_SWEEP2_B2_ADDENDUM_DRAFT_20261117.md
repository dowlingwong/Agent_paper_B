# Draft addendum: B.2 fresh-seed audits of C3 sweep 2 (HTCondor, one CPU class)

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it for PLAN row
**R1-SWEEP2-B2-DRAFT** (17 Nov 2026, night (2); branch `author-decisions-20261117b` @ `45fb94cc`): "draft now the
supplementary authorization for the sweep-2 B.2 audits (K = 10, 7001–7005 label / 7006–7010 evaluation, one fixed
HTCondor CPU node type, image digest and harness pin the same as sweep 2); the author commits it after sweep-2
collection is complete, and the audits start right after."

**How the author uses it:**
- After sweep-2 collection is complete and accepted, copy the block between the two rules below to
  `docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md` on `main`.
- Fill every `<…>` placeholder. The values marked *(proposed)* are the agent's; change or confirm them.
- Set `approved: true` yourself. This draft keeps `approved: false`, and the agent never sets it.

**Authority.** PLAN §10 rows take precedence over this note wherever they differ. Rows used:
- **R1-SWEEP2-B2-DRAFT** (this draft; K = 10, 7001–7005 / 7006–7010, one HTCondor CPU class, sweep 2's image digest
  and harness pin);
- **R1-SWEEP-HOST-HTC** (CPU-only audits run on one fixed HTCondor CPU node type; one host type per table);
- **R1-SWEEP2-SETTINGS (2)** (the sweep-2 authorization holds no B.2 audit; a later addendum adds it;
  R1-B2-DECOUPLE and R1-B2-REPLAY-GO unchanged);
- **R1-SWEEP2-ANY-GPU** (collection may run on any qualifying GPU; the CPU model of each campaign is recorded only);
- **R1-MAIN-PROPOSER** (b) audits K = 10 under the R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE rules, (e) one instance
  assignment and twin pairs across sources, (f) as amended by R1-SWEEP-HOST-HTC;
- **R1-SWEEP1-CLASSIFY** (labels 7001–7005, evaluation 7006–7010, never mixed);
- **R1-BX-PROPOSED-CONFIRM** D3 (T0 stays at K = 10);
- **R1-B1-CORPUS-FREEZE** (a label table counts only after its separate freeze);
- **R1-BX-D8** and its confirmations (the analysis lock is unchanged by this addendum).

What the sweep-1 B.2 addendum (`proposals/AUTH_DRAFT_b2_20261104.md` Part 3, unit e2) settles for sweep 1 and this
draft does **not** inherit: the deepthought host, the e1 replay as environment basis (R1-B2-GO B6 (a)) and the
probe-based worker-runtime record (B4 (a)). Sweep 2 needs its own basis on its CPU class; see preconditions 4–5.

---

# Addendum to `c3_sweep2_<date>.md`: B.2 fresh-seed audits of sweep 2

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite: sweep 2's
run id and its accepted collection report and review; the sweep-2 table and its review; the accepted sweep-2 audit
code unit; the replay on the pinned CPU class and its review.>

```
approved: false
label: EVIDENCE
run_id: <audit run id, e.g. s2b2-<YYYYMMDD>-a; every job spec and job record carries it>
phase: c3_sweep2_b2
parent_authorization: docs/r1/authorizations/c3_sweep2_<date>.md
```

## Scope

One complete EVIDENCE audit of the completed sweep-2 batch `<sweep-2 run id>`: every eligible proposal of both
memory modes, K = 10 fresh joint seeds (train seed = split seed = s, as sweep-1 B.2). Not authorized:
- any C3, Track P or other training, tuning, threshold choice or selection on 7006–7010;
- any resume of a stopped audit job (a stopped job is rerun whole in a new directory, the old one moved aside and
  disclosed, as for sweep-2 collection under R1-SWEEP2-LAYOUT-AMEND);
- any other batch, and any pooling decision across sweeps (R1-MAIN-PROPOSER (e) fixes it on validation, separately).

## Pins

| Item | Value | Source |
|---|---|---|
| Sweep-2 batch | `<sweep-2 run id>`, collection report `<path>`, review `<path>` (ACCEPTED); sealed output `<ceph path>` | sweep-2 authorization; collection review |
| Table | built by `python -m r1.c3.dataset build-sweep` from the sweep-2 index `<path, sha256>`; `proposals.jsonl` `<sha256>`, `configs.json` `<sha256>`; table review `<path>`. The audit plan is a pure function of this table; a different table is a STOP | table build record |
| Paper code | `<the sweep-2 audit code commit accepted by its review>`; the review file carries `Code-Commit:` and `Verdict: ACCEPTED`; the commit is an ancestor of the published `main` | precondition 3 |
| Harness | **the sweep-2 pin**: `<as committed in c3_sweep2_<date>.md>` *(proposed: `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, `r1/scripts/HARNESS_PIN_C3`)*, clean. The audit job refuses any other commit | R1-SWEEP2-B2-DRAFT |
| Image | **the sweep-2 digest**: `<as committed in c3_sweep2_<date>.md>`, the same image the collection jobs ran (worker training is CPU-only, so the audit runs that image on a CPU slot, no GPU requested). The job checks the image identity markers the collection job records carry (`versions_sha256 <value>`, Python and library versions) | R1-SWEEP2-B2-DRAFT |
| CPU class (one for the whole audit table) | `<cluster agent: TARGET.CpuFamily / TARGET.CpuModelNumber and the /proc/cpuinfo model string>`. *(Proposed: `CpuFamily` 6 / `CpuModelNumber` 207, `INTEL(R) XEON(R) PLATINUM 8562Y+` — measured on the sweep-2 smoke hosts and already a constant of the sweep-2 wrapper (`CPU_MODEL_CONTAINS`) — provided the cluster's ads show enough CPU-only capacity on it; otherwise the class with the most CPU-only slots, chosen before launch and not changed after.)* Pinned in the job requirements and checked at run time from `/proc/cpuinfo`; a job elsewhere is a STOP | R1-SWEEP-HOST-HTC |
| Audit design | K = 10; label seeds 7001–7005 and evaluation seeds 7006–7010 in separate blocks (`label_block.jsonl`, `evaluation_block.jsonl`); duplicates get no label; no-ops are labelled by rule; the same plan rules as sweep-1 B.2 (`r1.c3.audit evidence_blocks`) | R1-SWEEP1-CLASSIFY; R1-MAIN-PROPOSER (b) |
| Expected population | `<from the audit dry plan on the sweep-2 table: eligible proposals, unique configurations, seed runs (= configurations × 10), duplicates, no-ops>` | dry plan, after collection |

## Host, jobs and resources

- **HTCondor CPU jobs** on the class above, the sweep-2 image, no GPU. *(Proposed layout: one job per (node, memory
  mode), 16 jobs, as in sweep-2 collection; each job runs its configurations' 10 seeds with `<n>` workers on
  `request_cpus = <n>`; the cluster agent states `request_memory`, `request_disk` and `request_walltime` from a
  measured job, walltime = 1.5 × the measured job time, as R1-SWEEP2-LAYOUT-AMEND set for collection.)*
- Estimate *(to be replaced by the dry plan)*: sweep-1 B.2's plan was 4,660 seed runs, about 2.5 CPU-h of recorded
  trial time; sweep 2 has the same nodes, instances and W, so the same order of magnitude.
- Output per job: a new directory under `<ceph root>/sweep2_b2/<run id>/<job>`; a merge step writes one
  `label_block.jsonl`, one `evaluation_block.jsonl` and one `evidence_completion.json` for the table.
- Command: `<the audit code unit's submit command, with --addendum docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md>`.
  The code reads this file from `origin/main` and requires it to contain `R1-SWEEP2-B2-DRAFT`, the sweep-2 run id,
  the paper code commit, the harness pin, the image digest, the CPU class and `K = 10`.

## Preconditions (all before the first audit job)

1. Sweep-2 collection complete, its gates passed, its report independently reviewed and accepted.
2. The sweep-2 table built from the sealed batch and independently reviewed; its hashes entered above.
3. **Sweep-2 audit code unit**, independently reviewed and on `main`: `evidence-run` bound to the sweep-2 table,
   index, authorization and this addendum (the sweep-1 path binds `c3_sweep1_20261027.md` and the sweep-1
   classification); the HTCondor CPU job wrapper with the class, image and harness checks; the merge step; the same
   label/evaluation separation and completion schema as sweep-1 B.2.
4. **Environment basis on the pinned class** *(proposed, by analogy with e1 for sweep 1)*: a replay of `<n>` logged
   sweep-2 in-campaign worker runs (both memory modes, every node) on the pinned CPU class in the sweep-2 image
   reproduces the logged metrics at tolerance `<0 | stated>`, independently reviewed. Collection ran on whatever CPU
   the GPU slots had (R1-SWEEP2-ANY-GPU), so this check is what ties the audit host to the collected campaigns.
5. **Worker-runtime record**: the audit job records, for every seed run, the Python and library versions of the
   process that ran the training (not a separate probe) *(proposed; the alternative is the sweep-1 B4 (a) probe with
   its limitation disclosed — an author choice)*.
6. CPU-class capacity measured from `condor_status` on the day of launch, recorded in the launch record.

## Pass rule

The audit is complete when all of the following hold:
- every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and its incumbent,
  all on the pinned CPU class, image and harness;
- `label_block.jsonl` and `evaluation_block.jsonl` are written and match the raw runs on recomputation;
- `evidence_completion.json` binds the table, the plan, both blocks, the runs, the environment and the job records,
  and this addendum;
- the counts by kind equal the plan's.

Labels count only after an independent review and the author's separate label-table freeze (R1-B1-CORPUS-FREEZE).

## Disclosures (in the sweep-2 B.2 report)

- The audit CPU class differs from the CPUs of the collection campaigns (recorded per campaign under
  R1-SWEEP2-ANY-GPU) and from sweep-1 B.2's host (deepthought). Labels are measured on one class only.
- **Twin pairs across sources.** Sweep 1 and sweep 2 share instance seeds, and audits use joint seeds, so the same
  (node, incumbent, candidate) can appear in both sources. R1-MAIN-PROPOSER (e) expects the same label in both; the
  two audits run on different hosts, harness pins (`6adf385` / the sweep-2 pin) and environments, so equality is not
  guaranteed. *(Proposed: the report compares the label-seed (7001–7005) values of the twin pairs descriptively; no
  gate, no use of 7006–7010.)*

## STOPs

Retain everything; there is no automatic resume.
- Any guard failure: authorization, publication, table, plan, image, harness, CPU class, environment basis.
- A job on another CPU class, image or harness.
- Any failed, missing, non-finite or file-changing seed run.
- A job over its walltime, or a job that started more than once (`NumJobStarts > 1`).
- A resource floor reached.
- Any use of 7006–7010 outside the evaluation block.

---

## Notes for the author (not part of the addendum)

1. **CPU class.** The proposed class (6/207, Xeon Platinum 8562Y+) is the one the sweep-2 wrapper already names; its
   CPU-only capacity has not been measured here. The cluster agent confirms or replaces it before launch.
2. **Environment basis and worker runtime (preconditions 4–5)** are proposals by analogy with R1-B2-GO's B6/B4 for
   sweep 1; for sweep 2 the image is fixed, which makes a task-process record straightforward.
3. **The sweep-2 audit code does not exist yet** (precondition 3); this draft fixes what it must check, not how.
4. **SFT readiness.** The Track P SFT pipeline (`r1/c3/train/sft_data.py`, R1-TRACKP-SFT-DEV; branch `mac-trackp-sft-dev-20261117`, under review) reads only
   `label_block.jsonl` and the completion's label-block hash and seeds; it plugs in sweep 2's labels with
   `--label-sweep sweep2` once this audit's label block exists.
