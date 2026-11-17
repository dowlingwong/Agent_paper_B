# Draft addendum: B.2 fresh-seed audits of C3 sweep 2 (HTCondor, one CPU class)

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it for PLAN row
**R1-SWEEP2-B2-DRAFT** (17 Nov 2026, night (2); branch `author-decisions-20261117b` @ `45fb94cc`): "draft now the
supplementary authorization for the sweep-2 B.2 audits (K = 10, 7001–7005 label / 7006–7010 evaluation, one fixed
HTCondor CPU node type, image digest and harness pin the same as sweep 2); the author commits it after sweep-2
collection is complete, and the audits start right after."

**How the author uses it:**
- After sweep-2 collection is complete and accepted, copy the block between the two rules below to
  `docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md` on `main`.
- Fill every `<…>` placeholder. Who fills what is listed in note 6. The values marked *(proposed)* are the agent's;
  change or confirm them.
- Set `approved: true` yourself. This draft keeps `approved: false`, and the agent never sets it.

**Authority.** PLAN §10 rows take precedence over this note wherever they differ. Rows used:
- **R1-SWEEP2-B2-DRAFT** (this draft; K = 10, 7001–7005 / 7006–7010, one HTCondor CPU class, sweep 2's image digest
  and harness pin; audits start right after the author commits it);
- **R1-B2-DECOUPLE** (B.2 "does not start"; labels from 7001–7005, 7006–7010 only for evaluation) and **R1-B2-GO**
  (which lifted "does not start" for the sweep-1 fresh-seed audits only, with the B6 (a) / B4 (a) / B1 (a)
  substitutions for sweep 1 on deepthought);
- **R1-SWEEP1-CLASSIFY** (what "fresh" means; 7006–7010 never used for training, selection or tuning);
- **R1-SWEEP-HOST-HTC** (CPU-only audits run on one fixed HTCondor CPU node type; one host type per table);
- **R1-SWEEP2-SETTINGS (2)** (the sweep-2 authorization holds no B.2 audit; a later addendum adds it;
  R1-B2-DECOUPLE and R1-B2-REPLAY-GO unchanged);
- **R1-SWEEP2-ANY-GPU** (collection may run on any qualifying GPU; the CPU model of each campaign is recorded only);
- **R1-SWEEP2-LAYOUT-AMEND**, **R1-SWEEP2-STOP-PRECEDENCE** and **R1-SWEEP2-RESOURCES** (no resume, whole reruns, STOP
  precedence, walltime and request rules of sweep-2 collection, applied here by analogy where marked *(proposed)*);
- **R1-MAIN-PROPOSER** (b) audits K = 10 under the R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE rules; (e) one instance
  assignment and twin pairs across sources; (f) source as a stratum, and its *(proposed)* "deepthought CPUs" audit
  host, superseded in content by R1-SWEEP-HOST-HTC;
- **R1-BX-PROPOSED-CONFIRM** D3 (T0 stays at K = 10);
- **R1-B1-CORPUS-FREEZE** (a label table counts only after its separate freeze);
- **R1-BX-D8** and **R1-BX-D8-CONFIRM** (on `main` since `14c47777`; this addendum does not change the analysis rules).

What the sweep-1 B.2 addendum (`proposals/AUTH_DRAFT_b2_20261104.md` Part 3, unit e2) settles for sweep 1 and this
draft does **not** inherit: the start ruling (R1-B2-GO is sweep-1 only), the deepthought host, the e1 replay as
environment basis (B6 (a)) and the probe-based worker-runtime record (B4 (a)). It carries over B1 (a)'s publication
rule. Sweep 2 needs its own start sentence (below) and its own basis on its CPU class (preconditions 5–6).

---

# Addendum to `c3_sweep2_<date>.md`: B.2 fresh-seed audits of sweep 2

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite: sweep 2's
run id and its accepted collection report and review; the sweep-2 table and its review; the accepted sweep-2 audit
code unit; the replay on the pinned CPU class and its review.>

**Start.** *(For the author to confirm.)* This addendum, with R1-SWEEP2-B2-DRAFT, lifts R1-B2-DECOUPLE's "does not
start" **for the sweep-2 fresh-seed audits only**. *(Alternative: the author adds a one-line start row, e.g.
`R1-SWEEP2-B2-GO`, when committing this file, and the audit code keys on that row instead.)*

```
approved: false
label: EVIDENCE
run_id: <audit run id, e.g. s2b2-<YYYYMMDD>-a; every job spec and job record carries it>
phase: c3_sweep2_b2
parent_authorization: docs/r1/authorizations/c3_sweep2_<date>.md
start_ruling: <R1-SWEEP2-B2-DRAFT with this addendum | R1-SWEEP2-B2-GO>
```

## Scope

One complete EVIDENCE audit of the completed sweep-2 batch `<sweep-2 run id>`: every eligible proposal of both
memory modes, K = 10 fresh joint seeds (train seed = split seed = s, as sweep-1 B.2). Not authorized:
- any C3, Track P or other training, tuning, threshold choice or selection on 7006–7010;
- any resume of a job (the rerun rule is under "Reruns and STOPs");
- any other batch, and any pooling decision across sweeps (R1-MAIN-PROPOSER (e) fixes it on validation, separately).

## Pins

| Item | Value | Source |
|---|---|---|
| Sweep-2 batch | `<sweep-2 run id>`, collection report `<path>`, review `<path>` (ACCEPTED); sealed output `<ceph path>` | sweep-2 authorization; collection review |
| Table | built from the sealed batch by the sweep-2 table path (precondition 3); `proposals.jsonl` `<sha256>`, `configs.json` `<sha256>`; table review `<path>`. The audit plan is a pure function of this table; a different table is a STOP | table build record |
| Paper code | `<the full 40-character sweep-2 audit code commit accepted by its review>`; the review file carries `Code-Commit:` and `Verdict: ACCEPTED`; the commit is an ancestor of the published `main` | precondition 4 |
| Harness | **the sweep-2 pin**: `<as committed in c3_sweep2_<date>.md>` *(proposed: `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, `r1/scripts/HARNESS_PIN_C3`)*, clean. The audit job refuses any other commit | R1-SWEEP2-B2-DRAFT |
| Image | **the sweep-2 digest**: `<as committed in c3_sweep2_<date>.md>`, the same image the collection jobs ran (worker training is CPU-only, so the audit runs that image on a CPU slot, no GPU requested). The job checks what the collection job records carry: the JDL's `container_image` digest, `versions_sha256` (the sha256 of `/opt/r1/VERSIONS.txt`; *proposed: `d31e8b2336c1a1a698163ef8c20f2cdf067bed9539e73bb7b545aeffb117dcc2`, as in the smoke records*) and, if the audit reuses `image_identity`, `llama_server_sha256` (`f8d35fd3…`). Python and library versions come from the per-run record of precondition 6, not from the collection records, which do not carry them | R1-SWEEP2-B2-DRAFT |
| CPU class (one for the whole audit table) | `<cluster agent: the /proc/cpuinfo model string, cpu family and model number, and the condor_status machine set that matches them>`. The audit job checks all three at run time; `TARGET.CpuFamily` / `TARGET.CpuModelNumber` in the requirements are only a scheduler pre-filter (one family/model number can cover several SKUs). A job elsewhere is a STOP. *(Proposed: the CPU-only node type with the most free slots in the pool's `condor_status` before launch — the 16 Nov snapshot lists CPU nodes `n31xx`–`n33xx` besides the GPU nodes — chosen before launch and not changed after. The `INTEL(R) XEON(R) PLATINUM 8562Y+` (family 6 / model 207) seen on the 16 Nov NEMO2 L40S hosts is a GPU-node CPU; its constant `CPU_MODEL_CONTAINS` in `sweep2/s2_c2_lib.py` is a leftover of the round-5 L40S pin and is not enforced under R1-SWEEP2-ANY-GPU. Whether "CPU 节点类型" means CPU-only nodes: `<author>`, note 1.)* | R1-SWEEP-HOST-HTC |
| Audit design | K = 10; label seeds 7001–7005 and evaluation seeds 7006–7010 in separate blocks (`label_block.jsonl`, `evaluation_block.jsonl`); duplicates get no label; no-ops are labelled by rule; the same plan rules (`r1.c3.audit` `partition_population` / `evidence_plan`) and block rules (`evidence_blocks`) as sweep-1 B.2; a non-finite seed run is a STOP, as in sweep-1 B.2 (note 5) | R1-B2-DECOUPLE; R1-SWEEP1-CLASSIFY; R1-MAIN-PROPOSER (b) |
| Expected population | `<from the audit dry plan on the sweep-2 table: eligible proposals, unique (node, configuration) pairs, seed runs (= pairs × 10), duplicates, no-ops>` | dry plan, after collection |
| Publication (as R1-B2-GO **B1 (a)** for sweep 1) | Before the first job, all of these are on `main`: this addendum; the start ruling; `c3_sweep2_<date>.md`; the collection report and review; the table review; the audit-code review; the environment-basis report and review (precondition 5). The guards read them from `origin/main` | R1-B2-GO B1 (a), by analogy |

## Host, jobs and resources

- **HTCondor CPU jobs** on the class above, the sweep-2 image, no GPU.
- **Work units are unique (node, configuration hash) pairs across both memory modes**: joint seeds make an audit run
  independent of memory mode and instance, and the sweep-1 cache refuses a repeated (node, configuration, seed).
  *(Proposed layout: one job per node, 8 jobs, each running its node's unique configurations at the 10 seeds; or a
  fixed hash partition of the pairs. The merge requires every (node, configuration, seed) exactly once.)* With about
  2.5 CPU-h at sweep-1 scale, per-job overhead (image pull, queue) dominates, so fewer, larger jobs are preferred.
- Workers per job: `<n>`, with `request_cpus = <n + 1>`; the audit code refuses a worker count at or above the CPU
  count it reads inside the container, as the sweep-1 path does *(proposed)*.
- `request_memory` and `request_disk` = the measured peak of a test job × 1.4, rounded up; `+RequestWalltime` = 1.5 ×
  its measured time *(proposed, by analogy with R1-SWEEP2-RESOURCES and R1-SWEEP2-LAYOUT-AMEND)*: `<values>`.
- **Resource floors** (each a STOP when reached): sandbox disk `<kB>`; free space for sealing on the submit side
  `<GiB>`; file-count reserve `<n>`.
- Estimate *(to be replaced by the dry plan)*: sweep-1 B.2's plan was 4,660 seed runs, about 2.5 CPU-h of recorded
  trial time. Sweep 2 has the same nodes, instances and W, but its unique-configuration count depends on the
  proposer's duplicate and no-op rates (X.7(c) Q1) and its run time on the CPU.
- **Outputs** as in sweep-2 collection: the job writes only into its sandbox; outputs transfer back on exit
  (`ON_EXIT`); a reviewed seal step copies them into a new directory `<ceph root>/sweep2_b2/<run id>/<job>` with
  `SHA256SUMS` and a receipt, never overwriting. A killed attempt returns no outputs; the HTCondor user log and job ad
  are kept. A merge step then writes one `label_block.jsonl`, one `evaluation_block.jsonl` and one
  `evidence_completion.json` for the table, from sealed outputs only.
- Command: `<the audit code unit's submit command, with --addendum docs/r1/authorizations/c3_sweep2_b2_addendum_<date>.md>`.
  The audit code must read this file from `origin/main` and must refuse unless it contains the start ruling, the
  sweep-2 run id, the paper code commit, the harness pin, the image digest, the CPU class and `K = 10`.

## Reruns and STOPs

*(As in sweep-2 collection: R1-SWEEP2-LAYOUT-AMEND and R1-SWEEP2-STOP-PRECEDENCE.)* A job that ends for a reason on
the STOP list below is a STOP, with its state preserved, even if it was also evicted or restarted. Only an eviction or
infrastructure interruption with no STOP cause (`NumJobStarts > 1` and the like, held by `periodic_hold`) leads to a
**whole-job rerun**: a fresh submission into a new directory, the old one moved aside (never deleted) and disclosed.
The merge uses the rerun's sealed output as a whole and never combines it with the moved-aside one. There is no
resume.

STOPs (retain everything):
- any guard failure: authorization, start ruling, publication, table, plan, image, harness, CPU class, environment
  basis, worker-runtime record, output path or overwrite;
- a job on another CPU class, image or harness;
- any failed, missing, non-finite or file-changing seed run;
- a job over its walltime;
- a resource floor reached;
- any use of 7006–7010 outside the evaluation block;
- pushing `main` without the author's explicit instruction.

## Preconditions (all before the first audit job)

1. Sweep-2 collection complete, its gates passed, its report independently reviewed and accepted.
2. **Freshness** (R1-SWEEP1-CLASSIFY): every sealed sweep-2 job record shows no B.2 audit (`b2_audits` none; collector
   `--audit-seeds 0`), and no ENGINEERING run on these proposals (liveness, S2-C3, S2-C3b, smokes) used 7001–7010.
3. The sweep-2 table built from the sealed batch and independently reviewed; its hashes entered above. On `main`,
   `dataset build-sweep` takes an index and, for EVIDENCE, the sweep-1 classification sidecar; the step that turns the
   sealed chunk outputs into an index and binds the table to `c3_sweep2_<date>.md` belongs to a code unit (here or in
   precondition 4).
4. **Sweep-2 audit code unit**, independently reviewed and on `main`: `evidence-run` bound to the sweep-2 table,
   index, authorization and this addendum (the sweep-1 path binds `c3_sweep1_20261027.md` and the sweep-1
   classification sidecar); the HTCondor CPU job wrapper with the CPU-class, image and harness checks (the CPU check
   must be added back for audit jobs; the collection wrapper no longer has it); the seal and merge steps; the same
   label/evaluation separation and completion schema as sweep-1 B.2.
5. **Environment basis on the pinned class** *(proposed, by analogy with e1 for sweep 1)*: a replay of `<n>` logged
   sweep-2 in-campaign worker runs (both memory modes, every node) on the pinned CPU class in the sweep-2 image,
   independently reviewed. Cases come from campaigns whose recorded CPU is the pinned class where possible, plus `<m>`
   from other classes. The pass rule is declared before the run: tolerance `<0 | stated>`; a difference beyond it is a
   STOP for the author. The replay can start on the first sealed chunks while collection continues (note 3).
6. **Worker-runtime record**: the audit job records, for every seed run, the Python and library versions of the process
   that ran the training *(proposed)*, without changing the harness pin, the image, or the trial's command and imports
   (so from the paper side, for example a recorded resolution of the worker's `python3` before the run). The
   alternative is the sweep-1 B4 (a) probe with its limitation disclosed — an author choice. On `main` today
   `_require_task_native_runtime_attestation` still STOPs every EVIDENCE run; the e2 unit replaces it for sweep 1 only.
7. CPU-class capacity measured from `condor_status` on the day of launch, recorded in the launch record.
8. R1-BX-D8-CONFIRM is on `main` (`14c47777`): satisfied.

## Pass rule

The audit is complete when all of the following hold:
- every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and its incumbent,
  all on the pinned CPU class, image and harness;
- `label_block.jsonl` and `evaluation_block.jsonl` are written and match the raw runs on recomputation;
- `evidence_completion.json` binds the table, the plan, both blocks, the runs, the environment, the job and seal
  records, and this addendum;
- the counts by kind equal the plan's.

Labels count only after an independent review and the author's separate label-table freeze (R1-B1-CORPUS-FREEZE).

## Disclosures (in the sweep-2 B.2 report)

- The audit CPU class may differ from the CPU of some or all collection campaigns (recorded per campaign under
  R1-SWEEP2-ANY-GPU) and differs from sweep-1 B.2's host (deepthought); the report lists the per-campaign CPU models.
  Labels are measured on one class only. Sources stay strata (R1-MAIN-PROPOSER (f)).
- **Twin pairs across sources.** Sweep 1 and sweep 2 share instance seeds, and audits use joint seeds, so an audit
  value depends only on (node, configuration, seed): the twin key for comparing values is (node, incumbent hash,
  candidate hash), while R1-MAIN-PROPOSER (e) groups by (instance, incumbent, edit). (e) expects the same label in both
  sources; the two audits run on different hosts and environments. The harness worker code (`src/autoresearch/worker/`)
  is byte-identical between `6adf385` and `a3fedbb`, so differences would come from host and environment, not the
  harness. *(Proposed: the report compares the label-seed (7001–7005) values of the twin pairs descriptively, once
  sweep-1 B.2's label block exists; a report-level read, no gate, no use of 7006–7010.)*

---

## Notes for the author (not part of the addendum)

1. **CPU class.** Whether "one fixed HTCondor CPU node type" means CPU-only nodes is yours to say; the proposal picks
   the CPU-only type with the most slots. The 8562Y+ hosts seen so far are NEMO2 GPU nodes with 16-CPU slots.
2. **Start ruling.** R1-B2-GO lifted "does not start" for sweep 1 only. The block above proposes a sentence; a separate
   start row is the alternative.
3. **Timing.** Preconditions 3–6 add code units and reviews between collection and the first audit job. The replay of
   precondition 5 can begin on the first sealed chunks, and the code units (3, 4, 6) can be written and reviewed
   before collection ends.
4. **Twin comparison** needs sweep-1 B.2's label block; it is descriptive only.
5. **Divergent runs.** Like sweep-1 B.2, a non-finite seed run is a STOP. R1-BX-PROPOSED-CONFIRM REVISIONS (c) (E5)
   defines divergent proposals and partial labels; if sweep 2's proposer yields more divergent configurations, the
   audit would STOP rather than apply E5. Which rule applies: `<author>`.
6. **Who fills what.**
   - The author: the opening paragraph, `run_id`, the start ruling, the CPU-node reading (note 1), the replay
     tolerance (precondition 5), the worker-runtime choice (precondition 6), the divergence rule (note 5).
   - From `c3_sweep2_<date>.md`: the harness pin and the image digest.
   - The cluster agent: the CPU class and its capacity, the measured requests, walltime and floors, the layout.
   - Code and run units: the sweep-2 batch, table and dry-plan values, the audit code commit, the replay report.
7. **SFT readiness.** The Track P SFT pipeline (`r1/c3/train/sft_data.py`, R1-TRACKP-SFT-DEV; branch
   `mac-trackp-sft-dev-20261117`, under review) reads only `label_block.jsonl` and the completion's label-block hash
   and seeds; it plugs in sweep 2's labels with `--label-sweep sweep2` once this audit's label block exists.
