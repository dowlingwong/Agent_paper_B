Reviewed base: `2b3ff75e` (branch `mac-sweep2-b2-draft-20261117`; accepted in round 2)

# Independent review record — sweep-2 B.2 addendum draft (R1-SWEEP2-B2-DRAFT)

**Unit.** `docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261117.md`, a draft supplementary authorization for the
sweep-2 B.2 fresh-seed audits (`approved: false`; the author commits it after sweep-2 collection). Authority:
`author-decisions-20261117b` @ `45fb94cc`, row R1-SWEEP2-B2-DRAFT. Base: `main` `26177d82`.

**Process.** One independent reviewer (a separate agent that did not write the draft), two rounds. The reviewer edited
nothing. The round texts are reproduced below as delivered (headings shifted down two levels).

| Round | Commit reviewed | Verdict |
|---|---|---|
| 1 | `857c52af` (diff from `26177d82`) | NOT ACCEPTED (1 blocking, 11 should-fix, 6 minor, 4 notes) |
| 2 | `2b3ff75e` (diff from `857c52af`) | ACCEPTED (4 minor, 2 notes) |
| — | `0d9068e4`: the round-2 minors, applied after acceptance | not re-reviewed |

---

## Round 1 (commit `857c52af`)

### Review: sweep-2 B.2 addendum draft (R1-SWEEP2-B2-DRAFT), round 1

- Unit: commit `857c52af` on `mac-sweep2-b2-draft-20261117` (parent `main` @ `26177d82`), one file
  `docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261117.md` (145 lines). The worktree is clean and only this file was added.
- Authority: `gh/author-decisions-20261117b` @ `45fb94cc` (PLAN.md; `main` is an ancestor), row R1-SWEEP2-B2-DRAFT (PLAN line 1278).
- Compared with: the sweep-1 B.2 addendum (`mac-e2-code-20261117`, `AUTH_DRAFT_b2_20261104.md` Part 3) and the sweep-2 authorization note draft
  (`C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md` on `main`).
- Code checked:
  - `r1/c3/audit.py` and `r1/c3/dataset.py` @ `26177d82`;
  - `sweep2/s2_c2_lib.py`, `render_jdl.py`, `spec.example.json` and the smoke and S2-C4 job records @ `gh/sweep2-main-20261116` (`d9b31a30`);
  - `r1/scripts/HARNESS_PIN_C3`;
  - harness `6adf385` vs `a3fedbb` (local harness clone);
  - `mac-trackp-sft-dev-20261117` (note 4).
- Reviewer: independent AI reviewer (Claude). Nothing in the repository was modified. Scratch files are in `/tmp/rv_s2b2/`.

#### Verdict: NOT ACCEPTED

The draft does what the row asks:
- K = 10, with 7001–7005 for labels and 7006–7010 for evaluation;
- one pinned HTCondor CPU class;
- the sweep-2 image digest and harness pin, each as a placeholder plus a proposed value;
- `approved: false`, kept;
- the author commits it after collection.

It is clearly marked as a draft. Placeholders are consistently `<…>` and proposals are marked *(proposed)*. Most citations are accurate.

It is not accepted because of the following:
- One internal contradiction would leave the operator with conflicting instructions: a stopped job is "rerun whole" in one place, and `NumJobStarts > 1` is a STOP in another.
- One technical claim is false: the collection job records do not carry Python or library versions.
- One claim about the CPU-class constant misleads.
- The relationship to R1-B2-DECOUPLE's "does not start" is not stated. R1-B2-GO lifted it for sweep 1 only.
- The publication requirement that sweep-1 B.2 had (B1 (a)) is missing.
- The proposed job layout would duplicate audit runs.
- Several cited rows are missing from the Authority list.

All of these are text fixes. The verdict can change to ACCEPTED once findings 1–8 are addressed.

#### What was verified as correct

- R1-SWEEP2-B2-DRAFT: the quote in lines 4–7 is a faithful translation of PLAN line 1278. The section is "17 November 2026 (night, 2)" and the commit is `45fb94cc`.
- R1-SWEEP-HOST-HTC: "CPU-only audits run on one fixed HTCondor CPU node type; one host type per table" is accurate.
- R1-SWEEP2-SETTINGS (2) is accurate: the sweep-2 note holds no B.2, a later addendum adds it, and DECOUPLE and REPLAY-GO are unchanged.
- R1-SWEEP2-ANY-GPU is accurate: collection may run on any GPU with ≥ 24 GB and compute capability ≥ 7.0, and the CPU model is recorded per campaign. In code, `cpu_identity()` returns `"recorded_only": True`, and `validate_spec` rejects `cpu_family`, `cpu_model_number` and `cpu_model_contains` in the requirements.
- R1-MAIN-PROPOSER (b) and (e) are accurate: K = 10 under the CLASSIFY/DECOUPLE rules, plus the twin-campaign and one-assignment rules.
- R1-BX-PROPOSED-CONFIRM D3 is accurate: T0 stays at K = 10.
- R1-B1-CORPUS-FREEZE is accurate: soft-label tables are frozen separately after the audit.
- R1-B2-GO is accurate: B6 (a) and B4 (a) are sweep-1 substitutions on deepthought, and the sweep-1 plan was 4,660 seed runs.
- `audit.py` @ `26177d82`:
  - `DEFAULT_SEEDS = tuple(range(7001, 7011))`;
  - joint seeds (train seed = split seed = s);
  - `evidence_blocks` gives no label to duplicates and labels no-ops by rule;
  - the evidence path hard-codes `docs/r1/authorizations/c3_sweep1_20261027.md` and the sweep-1 classification sidecar.

  So precondition 3's statements that "the sweep-1 path binds `c3_sweep1_20261027.md` and the sweep-1 classification" and that the sweep-2 audit code does not exist yet are correct.
- `r1/scripts/HARNESS_PIN_C3` is `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` on both `main` and `sweep2-main`. That matches the proposed harness.
- The harness has `LocalWorker.run_trial_at_seed` at `a3fedbb`. `src/autoresearch/worker/` is byte-identical between `6adf385` and `a3fedbb`; this is useful for finding 21.
- Note 4 checks out: `trackp.py --label-sweep {sweep1,sweep2}` exists, and `LabelBlockSource(sweep="sweep2")` reads only `label_block.jsonl` plus the completion's label-block hash.

#### Findings

##### 1. Blocking: rerun vs STOP contradiction for stopped or restarted jobs
**Location:**
- Scope, lines 54–55: "a stopped job is rerun whole in a new directory … as for sweep-2 collection under R1-SWEEP2-LAYOUT-AMEND".
- STOPs, line 126: "there is no automatic resume".
- STOPs, line 130: "a job that started more than once (`NumJobStarts > 1`)" is listed as a STOP.

**Problem:** For collection, R1-SWEEP2-LAYOUT-AMEND and R1-SWEEP2-STOP-PRECEDENCE (PLAN line 1245, not cited) handle these cases differently:
- `NumJobStarts > 1` and evictions or infrastructure interruptions are **whole-job reruns**, not STOPs;
- a cause on the STOP list takes precedence and is a STOP;
- going over walltime is a STOP.

The draft says both that a stopped job is rerun and that `NumJobStarts > 1` is a STOP, so it is not clear what the operator does.

**Fix:** Pick one rule and state it once. Either:
- (a) follow collection: eviction or `NumJobStarts > 1` with no STOP cause → rerun the whole job as a fresh submission in a new directory, move the old directory aside and disclose it; a cause on the STOP list (including walltime, OOM, or any guard or seed-run failure) → STOP, which takes precedence (cite R1-SWEEP2-STOP-PRECEDENCE); or
- (b) for audits, every anomaly including `NumJobStarts > 1` is a STOP for the author, and a rerun happens only on the author's word. In that case remove the rerun clause from Scope.

Also say how the merge step treats a rerun job: the rerun replaces the moved-aside output as a whole and is never merged with it.

##### 2. Should-fix: start ruling, i.e. R1-B2-DECOUPLE's "does not start", is not addressed
**Location:** Authority (lines 15–27) and the addendum's opening paragraph placeholder (line 37).

**Problem:** R1-B2-DECOUPLE says B.2 "does not start". R1-B2-GO lifted that **for the sweep-1 fresh-seed audits only** ("仅限 sweep 1"), and R1-SWEEP2-SETTINGS (2) keeps DECOUPLE unchanged.

For sweep 2, the only basis for starting is R1-SWEEP2-B2-DRAFT's "审计随即开始" ("the audits start right after"). The sweep-1 addendum stated its start basis explicitly ("binds … to the e2 ruling R1-B2-GO, which lifts R1-B2-DECOUPLE's 'does not start' for the sweep-1 fresh-seed audits only").

The draft also makes the code require the string `R1-SWEEP2-B2-DRAFT` (line 82), which is a drafting row and not a start ruling.

**Fix:** Add a sentence to the addendum, for the author to confirm, saying that this addendum together with R1-SWEEP2-B2-DRAFT lifts R1-B2-DECOUPLE's "does not start" for the sweep-2 fresh-seed audits only. Offer the alternative: the author adds a one-line start row (for example `R1-SWEEP2-B2-GO`) when committing, and the guard keys on that row ID. List R1-B2-DECOUPLE and R1-B2-GO under Authority.

##### 3. Should-fix: false claim about what collection job records carry
**Location:** Pins, Image row (line 66): "The job checks the image identity markers the collection job records carry (`versions_sha256 <value>`, Python and library versions)."

**Problem:** The sweep-2 job records (`smoke_20261116/job_record_*.json` and `s2c4_run_20261116/…`) carry these identity fields:
- `image.versions_sha256`, which is the sha256 of `/opt/r1/VERSIONS.txt`;
- `image.llama_server_sha256`;
- `image.spec_digest`;
- `image_digest`.

There are no Python or library version fields (checked with grep; `image_identity()` in `s2_c2_lib.py` returns only those three values). A guard specified as written cannot be implemented.

**Fix:** Say that the job checks the following:
- the `container_image` digest pinned in the JDL (`docker://<digest>`);
- `versions_sha256` (proposed value `d31e8b2336c1a1a698163ef8c20f2cdf067bed9539e73bb7b545aeffb117dcc2`, as in the smoke records and the sweep-2 note draft);
- `llama_server_sha256` (`f8d35fd3…`), if the audit image check reuses `image_identity`.

Python and library versions come from precondition 5's per-run record, not from the collection records.

##### 4. Should-fix: the CPU-class claim misleads, and 6/207 only stands in for the model string
**Location:** Pins, CPU class row (line 67), and note 1 (line 138).

**Problem:** The draft says the class is "already a constant of the sweep-2 wrapper (`CPU_MODEL_CONTAINS`)" and "the one the sweep-2 wrapper already names".

The constant does exist (`s2_c2_lib.py` lines 39–41). But since R1-SWEEP-HOST-L40S-SITES and R1-SWEEP2-ANY-GPU it is **vestigial**:
- `render_jdl.requirements()` has no CPU term;
- `validate_spec` actively STOPs if any CPU pin is present in `requirements` (lines 234–238);
- `cpu_identity()` is recorded only and checks nothing;
- the test asserts `TARGET.CpuFamily` is absent from the JDL.

The author could read the draft as saying the current wrapper enforces this class. It does not, and the audit wrapper needs new requirement and runtime-check code.

Also, `S2_C2_REVIEW_20261116.md` (around line 511) found that `CpuModelNumber 207` is the Emerald Rapids family/model and not the 8562Y+ SKU. A scheduler requirement on 6/207 can therefore match a host that the `/proc/cpuinfo` model-string check then STOPs on.

The 8562Y+ values come from the 16 Nov L40S hosts g3605, g3608 and g3610 (S2-C4 and the round-5 smoke). Every in-campaign worker run in that smoke failed in ≤ 0.1 s (R1-SWEEP2-LAYOUT-AMEND). The later H200 smoke (`d9b31a30`) has no committed job record that shows its CPU.

**Fix:**
- Reword to say the constant comes from the S2-C2 round-5 L40S pin and is no longer enforced under R1-SWEEP2-ANY-GPU, so the audit code unit must add it back for audit jobs only.
- State which identity is authoritative. Proposed: the `/proc/cpuinfo` model string plus family plus model number, all three at run time, with 6/207 in the requirements as a scheduler pre-filter, and the matching machine set from `condor_status` recorded before launch (precondition 6).
- Note that the known 6/207 hosts are NEMO2 **GPU** nodes, with 16-CPU slots and the `ProvidesEtpCeph` limitation. The author may read R1-SWEEP-HOST-HTC's "CPU 节点类型" ("CPU node type") as meaning CPU-only nodes, so the choice should be explicit.

##### 5. Should-fix: proposed job layout per (node, memory mode) duplicates audit runs
**Location:** Host, jobs and resources (lines 73–76).

**Problem:** Audit work units are unique `(node, config_hash)` pairs across **both** memory modes:
- `audit.py` `evidence_run` schedules `(node, h)` jobs;
- `evidence_cache` raises `duplicate or unexpected evidence cache entry` on a repeated `(node, config_hash, seed)`;
- joint seeds make the run independent of memory mode and instance.

Incumbents, at least each node's initial configuration, and any repeated candidates appear in both memory modes. One job per (node, mode) would therefore run those configurations twice, and the merge would either fail or need a deduplication rule that does not exist. The sweep-1 count was 466 unique configurations across both modes.

**Fix:** Propose sharding by unique `(node, config_hash)` from the dry plan, for example one job per node (8 jobs) or a fixed hash partition. Say the merge requires each key exactly once.

Also note that at about 2.5 CPU-h in total (sweep-1 scale), per-job overhead (pulling the GPU image, which is several GB, and the queue) will dominate. Fewer, larger jobs may be better.

##### 6. Should-fix: publication requirement (sweep-1 B1 (a)) is missing
**Location:** Pins table, and lines 29–31.

**Problem:** The draft lists what it does not inherit from sweep-1 B.2 (B6 (a) and B4 (a)), but says nothing about B1 (a). The sweep-1 addendum had an explicit Publication row saying which documents must be on `main` for the guards that read `origin/main`. Here, "publication" appears only as a guard name (line 127), and line 82 says the code reads the addendum from `origin/main`.

**Fix:** Add a Publication row listing what must be on `main` before the first job:
- this addendum;
- the start ruling (finding 2);
- the sweep-2 authorization note;
- the collection report and review;
- the table review;
- the audit-code review;
- the environment-basis report and review (precondition 4).

State that the guards read them from `origin/main`, as R1-B2-GO B1 (a) did for sweep 1.

##### 7. Should-fix: Authority list is incomplete, and one attribution is wrong
**Location:** lines 15–27 and 24.

**Problems:**
- Rows used in the body or needed but not listed: R1-B2-DECOUPLE, R1-B2-GO, R1-SWEEP2-LAYOUT-AMEND (cited in lines 55 and 76), R1-SWEEP2-STOP-PRECEDENCE (finding 1) and R1-SWEEP2-RESOURCES (finding 9).
- Line 24 attributes "labels 7001–7005, evaluation 7006–7010" to R1-SWEEP1-CLASSIFY. That row says "Seeds remain 7001–7010", defines "fresh", and says 7006–7010 are never used for training or selection. The 7001–7005 / 7006–7010 label/evaluation split is stated in **R1-B2-DECOUPLE** ("Labels use seeds 7001–7005; 7006–7010 are limited to B.2 task-level joint-seed retraining and evaluation").
- Line 23, "R1-MAIN-PROPOSER (f) as amended by R1-SWEEP-HOST-HTC": HTC says it amends R1-SWEEP-HOST and R1-MAIN-PROPOSER **(c)**. It supersedes (f)'s *(proposed)* "deepthought CPUs" only by its content. (f) also carries "source as a stratum; within each source, one host" and a 50-proposal two-host check for a fallback case. Neither is mentioned.

**Fix:**
- Add the missing rows.
- Cite R1-B2-DECOUPLE for the seed split and R1-SWEEP1-CLASSIFY for "fresh" and the 7006–7010 use restriction.
- Rephrase (f) as "(f)'s audit-host proposal, superseded by R1-SWEEP-HOST-HTC", and mention source-as-stratum in Disclosures.

##### 8. Should-fix: no freshness precondition
**Location:** Preconditions (lines 85–100).

**Problem:** R1-SWEEP1-CLASSIFY defines "fresh" as seeds not used to generate, filter or select the audited proposals. Sweep 2's collector must run with `--audit-seeds 0` (sweep-2 note draft, Boundaries). The smoke records carry `b2_audits: "none (no B.2 audits; audit seeds 7001-7010 untouched)"`. Nothing in the addendum checks that the sealed collection actually left 7001–7010 untouched.

**Fix:** Add a precondition: every sealed sweep-2 job record shows no B.2 audits (`b2_audits` none, `--audit-seeds 0`), and no ENGINEERING run on these proposals (liveness, S2-C3/C3b, smokes) used 7001–7010.

##### 9. Should-fix: resource floors and resource requests are undefined
**Location:** line 75 and STOP line 131 ("A resource floor reached").

**Problem:** Sweep-1 B.2 defined its floors: Ceph ≥ 50 GiB free, a file-count reserve, and a scratch requirement. Here no floor is defined, so the STOP cannot be applied. The disk and memory requests are "from a measured job", without the sweep-2 rule.

**Fix:**
- Add `<…>` placeholders for the floors: sandbox disk, free space on the submit host or Ceph for sealing, and the file-count reserve.
- State `request_disk` and `request_memory` = measured peak × 1.4, rounded up, *(proposed, by analogy with R1-SWEEP2-RESOURCES)*.

##### 10. Should-fix: output path ignores how NEMO2 transfers and seals output
**Location:** line 79: "Output per job: a new directory under `<ceph root>/sweep2_b2/<run id>/<job>`".

**Problem:** On the proposed (NEMO2) hosts, slots do not advertise `ProvidesEtpCeph`. Sweep-2 jobs write to their sandbox, outputs are transferred `ON_EXIT`, and a reviewed `seal` step copies them under `/ceph/srv/dwong/paperb/sweep2/…` (s2_c2_lib and render_jdl docstrings, and the sweep-2 note draft).

**Fix:** Describe the same flow: sandbox → transfer on exit → seal into a new directory with `SHA256SUMS` and a receipt, no overwrite. Then merge. Also note what a killed attempt leaves, because of `ON_EXIT` transfer.

##### 11. Should-fix: precondition 4 (environment replay) conflicts with "audits start right after", and tolerance 0 across CPU classes is risky
**Location:** precondition 4 (lines 93–96).

**Problems:**
- Replaying logged sweep-2 in-campaign runs needs the collected campaigns, so it can only run after collection. That adds a replay unit plus an independent review between the commit and the first audit job, against R1-SWEEP2-B2-DRAFT's "audits start right after".
- Collection runs on whatever CPU each GPU slot has. A tolerance-0 replay on a different CPU microarchitecture may fail for numerical reasons that have nothing to do with environment identity, and the draft defines no response to a failure.

**Fix:**
- Tell the author about the timing cost in the notes.
- Propose that replay cases come from campaigns whose recorded CPU is the pinned class, where that is possible, plus a stated number from other classes.
- Pre-declare the response to a non-zero difference: a STOP for the author, or a stated tolerance.
- Optionally allow the replay to start on the first sealed chunks while collection continues.

##### 12. Should-fix: "straightforward" overstates how easy a task-process runtime record is
**Location:** note 2 (lines 140–141) and precondition 5.

**Problem:** Both the image digest and the harness pin are frozen, to the sweep-2 values. A record taken from the training process itself must therefore come from the paper side, for example a `python3` shim on `PATH` or a sandbox `sitecustomize`. That touches the import behaviour and command resolution that the sweep-1 [AS] constraints cared about. A PATH/`python3` resolution problem is also the suspected cause of the sweep-2 worker failure (note 1 of the sweep-2 note draft). This is feasible, but it is not obviously straightforward. Note also that `_require_task_native_runtime_attestation` still STOPs every EVIDENCE run on `main`.

**Fix:** Replace "straightforward" with a one-line statement of the constraint: no change to the harness pin or the image, and the mechanism must not alter the trial's command or imports. Keep B4 (a) as the explicit alternative.

##### 13. Minor: the CPU-difference disclosure overclaims
**Location:** line 116: "The audit CPU class differs from the CPUs of the collection campaigns".

**Problem:** Some collection campaigns may land on 8562Y+ hosts.

**Fix:** "may differ from the CPU of some or all collection campaigns (recorded per campaign); the report lists the per-campaign CPU models."

##### 14. Minor: code statements are written as fact
**Location:** line 82: "The code reads this file from `origin/main` and requires it to contain …".

**Problem:** The code does not exist (note 3).

**Fix:** "The audit code must read … and must refuse unless …".

##### 15. Minor: wrong function named for the plan rules
**Location:** Audit design row (line 68), "the same plan rules as sweep-1 B.2 (`r1.c3.audit evidence_blocks`)".

**Problem:** The plan rules are `partition_population` / `evidence_plan`. `evidence_blocks` builds the label and evaluation blocks.

**Fix:** Cite both.

##### 16. Minor: the sweep-2 table-build path is not part of any code unit
**Location:** Table row (line 63) and preconditions 2–3.

**Problem:** On `main`, `dataset build-sweep` takes `--index` and, for EVIDENCE, a classification sidecar (sweep 1). Sweep 2 has sealed per-chunk tarballs and an authorization labelled EVIDENCE, with no sidecar. Nothing yet turns the sealed chunks into an index, or binds the table to the sweep-2 note instead of a sidecar.

**Fix:** Name this in precondition 2 or 3 as part of a code unit.

##### 17. Minor: worker count vs request_cpus
**Location:** line 74.

**Problem:** `<n>` workers on `request_cpus = <n>`. The sweep-1 path refuses a worker count at or above the CPU count.

**Fix:** State the relation the audit code will enforce, for example workers ≤ `request_cpus`, and how the CPU count is read inside the container.

##### 18. Minor: STOP list is shorter than the sweep-1 and sweep-2 lists
**Location:** STOPs (lines 127–132).

**Problem:** Sweep-1 B.2 listed guard failures for the worker-runtime record and the output path. The sweep-2 note listed "any code path reading labels before R1-BX-D8-CONFIRM" and "pushing `main` without the author's instruction".

**Fix:** Add a worker-runtime record failure, an output-path or overwrite failure, and the two sweep-2-note STOPs, or a reference to them. R1-BX-D8-CONFIRM is already on `main` (`14c47777`); say so as a satisfied precondition.

##### 19. Note: the estimate is an inference
**Location:** line 78.

**Problem:** "Same nodes, instances and W, so the same order of magnitude" is plausible. But the unique-configuration count depends on the proposer (duplicate and no-op rates differ: X.7(c) Q1), and per-run time depends on the CPU. The line is marked as to be replaced by the dry plan, so this is only a note.

##### 20. Note: a non-finite seed run is a STOP, but E5 has a divergence rule
**Location:** Pass rule (line 105) and STOP line 129.

**Problem:** This is inherited unchanged from sweep-1 B.2, so it is consistent. However, R1-BX-PROPOSED-CONFIRM REVISIONS (c) (E5) defines how divergent proposals are labelled: non-finite loss → divergent, partial labels. A sweep-2 proposer that produces more divergent configurations would STOP the audit instead of going through E5.

**Fix:** The author may want to say which rule applies; no change is needed for consistency with sweep 1.

##### 21. Note: clarifications for the twin-pair disclosure
**Location:** lines 118–122.

**Points:**
- Because audits use joint seeds, the audit value depends only on (node, configuration, seed), not on the instance. The twin key for audit values is (node, incumbent hash, candidate hash). R1-MAIN-PROPOSER (e) uses (instance, incumbent, edit) for grouping. The draft's key is right for comparing values, but it should say why.
- The harness worker code (`src/autoresearch/worker/`) is byte-identical between `6adf385` and `a3fedbb`. Any twin-pair differences therefore come from host and environment, not from the harness. That is worth stating.
- The descriptive comparison needs sweep-1 B.2's label block to exist. It reads labels after R1-BX-D8-CONFIRM, which is satisfied, and before the label freeze. Say it is a report-level descriptive read.

##### 22. Note: how the draft reads for the author
The structure is clear: intro, the block to copy, notes. The "How the author uses it" steps are right. There are exactly two `---` rules around the block, and every author-fillable value is a `<…>` placeholder.

Suggestion: mark which placeholders the author fills and which the cluster agent or code units fill, as the sweep-2 note draft does in its note 3. Today only the CPU class says "cluster agent".

---

## Round 2 (commit `2b3ff75e`)

### Review: sweep-2 B.2 addendum draft (R1-SWEEP2-B2-DRAFT), round 2

- Unit: `mac-sweep2-b2-draft-20261117` @ `2b3ff75e`, parent `857c52af` (round 1).
- File: `docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261117.md`, now 204 lines (+122/−63). The worktree is clean.
- Authority: same as round 1, `gh/author-decisions-20261117b` @ `45fb94cc`.
- New source checked: `gh/sweep2-main-20261116:docs/r1/reports/sweep2_20261116/SWEEP2_LAUNCH_CHECKLIST_20261116.md`.
- Reviewer: independent AI reviewer (Claude). Nothing in the repository was modified; scratch files are in `/tmp/rv_s2b2/`.

#### Verdict: ACCEPTED

The round-1 blocking finding (1) and every should-fix finding (2–12) are resolved. The minors and notes (13–22) are handled.

Round 2 raises no blocking or should-fix problem. Four minor points and two notes remain (R2-1 to R2-6). The author can apply them when filling the draft, or the agent can fold them in without another review round.

The draft still keeps `approved: false`. Placeholders are `<…>` throughout, and proposals are marked *(proposed)*. Note 6 now says who fills each placeholder.

#### Round-1 findings: verification

| # | Round-1 finding | Status | Where / how checked |
|---|---|---|---|
| 1 | Rerun vs STOP contradiction (blocking) | **Resolved** | "Reruns and STOPs" (lines 110–127) gives one rule. A STOP cause wins even if the job was evicted or restarted. Only an eviction or infrastructure interruption with no STOP cause (`NumJobStarts > 1`) leads to a whole-job rerun: fresh submission, new directory, old one moved aside, disclosed. The merge uses the rerun output as a whole. `NumJobStarts > 1` is gone from the STOP list. Scope line 67 points to this section. This matches R1-SWEEP2-STOP-PRECEDENCE (PLAN line 1245) and R1-SWEEP2-LAYOUT-AMEND. |
| 2 | Start basis vs R1-B2-DECOUPLE | **Resolved** | The Start sentence (lines 49–51) lifts "does not start" for sweep-2 audits only, offers the `R1-SWEEP2-B2-GO` alternative, and adds a `start_ruling` key (line 59). The guard keys on the start ruling (line 107). It is listed in Authority (lines 19–21) and note 2. |
| 3 | False claim that job records carry Python/library versions | **Resolved** | Image row (line 78): JDL digest, `versions_sha256` (proposed `d31e8b23…`, which matches the smoke records), and optionally `llama_server_sha256` `f8d35fd3…`. It now says outright that the collection records do not carry Python or library versions. Consistent with `image_identity()` in `s2_c2_lib.py`. |
| 4 | Misleading CPU-class constant; family/model is only a proxy | **Resolved** | CPU row (line 79): `CPU_MODEL_CONTAINS` is called a leftover that is not enforced under ANY-GPU. The run-time check uses model string + family + model number, with `CpuFamily`/`CpuModelNumber` as a scheduler pre-filter only. 8562Y+ is identified as a GPU-node CPU. Precondition 4 says the CPU check must be added back. The proposal moves to a CPU-only node type; the `n31xx/n32xx/n33xx` observation is accurate (launch checklist, line 68: "H200 `g4401/g4402` and CPU `n31xx/n32xx/n33xx` are present"). |
| 5 | Per-(node, mode) layout duplicates runs | **Resolved** | Lines 87–91: work units are unique (node, configuration hash) pairs, 8 per-node jobs or a hash partition are proposed, the merge requires each key exactly once, and the overhead remark is included. Consistent with `evidence_cache` in `audit.py`. |
| 6 | Publication requirement missing | **Resolved** | Publication row (line 82) lists the required documents on `main` and the `origin/main` guards, citing B1 (a) by analogy. Lines 37–39 say it carries over. |
| 7 | Authority incomplete; wrong attribution of seed split; (f) wording | **Resolved** | DECOUPLE, B2-GO, LAYOUT-AMEND, STOP-PRECEDENCE, RESOURCES and D8-CONFIRM are added. The seed split is attributed to R1-B2-DECOUPLE (line 19, Audit design row). (f) is now "source as a stratum" plus a proposed host "superseded in content by R1-SWEEP-HOST-HTC". A small nit remains in R2-4. |
| 8 | No freshness precondition | **Resolved** | Precondition 2 (lines 132–133). |
| 9 | Resource floors and request rule undefined | **Resolved** | Lines 94–97: ×1.4 and 1.5× marked as proposed by analogy, with floor placeholders. "A resource floor reached" now refers to defined values. |
| 10 | Direct Ceph output | **Resolved** | Outputs (lines 101–105): sandbox, transfer `ON_EXIT`, seal into a new directory with `SHA256SUMS` and a receipt, then merge from sealed outputs only. It also says a killed attempt returns no outputs. |
| 11 | Replay timing and tolerance across CPU classes | **Resolved** | Precondition 5: cases selected by recorded CPU plus `<m>` from other classes, the pass rule declared beforehand, a difference beyond tolerance is a STOP, and the replay can start on early chunks. Note 3 covers timing. |
| 12 | "Straightforward" overclaim | **Resolved**, with a new wording issue | "Straightforward" is gone, and the constraint (no change to harness pin, image, command or imports) is stated. The example given is weak; see R2-1. |
| 13 | CPU disclosure overclaim | Resolved | Line 170, "may differ from … some or all". |
| 14 | Code stated as fact | Resolved | Line 107, "must read … must refuse unless". |
| 15 | Plan rules named wrongly | Resolved | Line 80 names `partition_population` / `evidence_plan` / `evidence_blocks`. |
| 16 | Table-build path for sweep 2 | Resolved | Precondition 3. |
| 17 | Workers vs `request_cpus` | Resolved | Line 92: `request_cpus = n + 1`, so the sweep-1 "workers < CPU count" rule is satisfied. |
| 18 | STOP list shorter than sweep-1 / sweep-2 | Resolved | Lines 120–127 add worker-runtime record, output path or overwrite, start ruling, and pushing `main`. The D8 lock is handled as precondition 8 (D8-CONFIRM on `main` at `14c47777`, verified in round 1). That is acceptable because the analysis-reader guards enforce it. |
| 19 | Estimate is an inference | Resolved | Lines 98–100. |
| 20 | Non-finite STOP vs E5 | Resolved | Audit design row and note 5 leave the choice to the author. |
| 21 | Twin-pair clarifications | Resolved | Lines 173–179: twin key, byte-identical worker code (verified in round 1), and the comparison only once sweep-1 B.2's label block exists, as a report-level read. |
| 22 | Who fills what | Resolved | Note 6. |

Cross-references checked:
- "precondition 3" (Table row), "precondition 4" (Paper code row), "precondition 5" (Publication row), "precondition 6" (Image row) and "preconditions 5–6" (line 39) all point to the right items after renumbering.
- Notes 1, 3 and 5 are referenced correctly.

#### New findings (round 2)

##### R2-1. Minor: the example for precondition 6 does not meet its own requirement
- **Location:** precondition 6, lines 148–150: "the Python and library versions of the process that ran the training … for example a recorded resolution of the worker's `python3` before the run".
- **Problem:** Resolving `python3` before the run is a separate check outside the training process. That is essentially what the sweep-1 B4 (a) probe already does ("a separate probe process using the worker's `PATH` and `python3`"). The author could therefore think the example closes the B4 gap when it does not. The requirement itself is fine and it is marked as proposed, so this is not gating.
- **Fix:** Either drop the example, or give one that runs inside the task process without changing the command or imports, and flag that it must be reviewed against those constraints. One option: a sandbox-only `sitecustomize` that writes `sys.version` and the loaded package versions, which touches import behaviour. Another: a `python3` shim on `PATH` that records versions and then `exec`s the real interpreter, which still is not the training process's own imports. Then say plainly: "if no mechanism records from the training process itself, the honest option is B4 (a) with its limitation disclosed."

##### R2-2. Minor: applying the collection rerun rule to audits is an analogy and should be marked proposed
- **Location:** "Reruns and STOPs", line 112: "*(As in sweep-2 collection: R1-SWEEP2-LAYOUT-AMEND and R1-SWEEP2-STOP-PRECEDENCE.)*"
- **Problem:** Both rows are written for collection chunks. Line 28 says they are "applied here by analogy where marked *(proposed)*", but this section is not marked *(proposed)*. Read alone, it presents the analogy as settled.
- **Fix:** Add *(proposed, by analogy)* to line 112, or have the author confirm it in note 6.

##### R2-3. Minor: the CPU-only node type needs container support confirmed as well as capacity
- **Location:** CPU row (line 79) and precondition 7.
- **Problem:** The launch-checklist snapshot shows only that `n31xx`–`n33xx` ads exist. It gives no CPU model, does not say whether they share one model, and does not say whether they match a `universe = container`, `docker://` job (`HasContainer`, `HasDockerURL`). The image is the GPU image `r1-htc-gpu`. It should run without a GPU, but no record shows it has run on these nodes.
- **Fix:** Precondition 7 should record not just capacity but:
  - the matching set's model string, family and model number;
  - container support (`HasContainer` / `HasDockerURL`);
  - one test job of the sweep-2 image on that node type.

  The test job can be the same job that measures the requests on lines 94–95.

##### R2-4. Minor: "tuning" is attributed to the wrong row
- **Location:** line 22: R1-SWEEP1-CLASSIFY "7006–7010 never used for training, selection or tuning".
- **Problem:** CLASSIFY says "never used for training or selection of any evidence". "Tuning" comes from R1-B2-DECOUPLE ("never C3/Track P training, tuning or selection").
- **Fix:** Drop "or tuning" from the CLASSIFY bullet, or add "tuning" to the DECOUPLE bullet.

##### R2-5. Note: the start sentence and PLAN precedence
- **Location:** lines 16 and 49–51.
- **Problem:** Line 16 says PLAN rows take precedence over this note. A note lifting a PLAN row's "does not start" therefore rests entirely on R1-SWEEP2-B2-DRAFT's "审计随即开始" ("the audits start right after"). The draft says this ("with R1-SWEEP2-B2-DRAFT"), and the start-row alternative is the cleaner route.
- **Fix:** Nothing required. Optionally, note 2 could recommend the start row, so the lift sits in PLAN like R1-B2-GO did for sweep 1.

##### R2-6. Note: a reasoning clause in the twin-pair disclosure
- **Location:** lines 173–174: "Sweep 1 and sweep 2 share instance seeds, and audits use joint seeds, so an audit value depends only on (node, configuration, seed)".
- **Problem:** The conclusion follows from joint seeds alone. Shared instance seeds explain why twin pairs occur, not why the value is independent of the instance.
- **Fix:** Optionally reword to: "Shared instance seeds make twin (node, incumbent, candidate) pairs likely; joint audit seeds make an audit value depend only on (node, configuration, seed)."

---

## After acceptance

`0d9068e4` applies the round-2 minors and notes: the worker-runtime example replaced by the statement that a check
before or beside the trial is a probe, with the B4 (a)-style probe as the honest fallback (R2-1); the rerun rule marked
*(proposed)* (R2-2); the launch-day CPU-class record extended to the CPU model, container support and one test job
(R2-3); "tuning" credited to R1-B2-DECOUPLE (R2-4); the start-row note (R2-5); the twin-pair wording (R2-6). Not
re-reviewed.

---

Accepted commit: `2b3ff75e` (round 2). Final draft commit including the round-2 minors: `0d9068e4`.
