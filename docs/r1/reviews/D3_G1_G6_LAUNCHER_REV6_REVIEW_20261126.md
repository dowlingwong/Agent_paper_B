# D.3 G1/G6 launcher revision 6: independent design review

**AI-assisted independent review (fresh session, Claude; 27 November 2026, of the 26 November revision). Tier E; design only.**
I did not write revision 6, the accepted D.3 G1/G6 design, or the R1–R6 review chain, and I did not
participate in the G1/G6 work. I read the revision, the accepted design, the two task cards, PLAN §10 and
`canon/COMPUTE.md` read-only. I changed nothing except writing this review file.

## 1. Inputs

| Input | Revision / location | sha256 |
|---|---|---|
| **R6** = launcher revision under review | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, branch `compute-d3-launcher-design-20261126` @ `40c64f5f` | `41b88061e95f2af7806b0ede3442044b872b6186c0014ca168155a2411120117` |
| **D5b** = accepted base design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, revision 5b, accepted by R6R | `4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23` |
| **R6R** = base-design acceptance | `docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R6_20261126.md` | `497b54d8f24a60542ca5719a2213c33b05771ba9e87e4b9f6304d2d590140cc8` |
| **T-COMPUTE** = task card | `tasks/compute/20261126-02-d3-launcher.md` at `origin/coord/coordinator` `e13b2ddc` | `6a27ea1a7b97ef6d8492ba2f2b625408036e320aada1d2fe298793547f6ccaba` |
| **T-CLUSTER** = task card | `tasks/cluster/20261126-02-d3-g1-g6-code.md` at `origin/coord/coordinator` `e13b2ddc` | `303fbe69f29c3d1269ead04bb437610244762fb7cd834086c545e8d5d6aa173b` |
| **PLAN** | `docs/r1/PLAN.md` at the checkout; R1-HOST-FREE (PLAN:1579), R1-CARD-SHARE (PLAN:1585), R1-NO-TIMEOUT (PLAN:1586) | `4f476a8246c0442a8d02a8f63fdf71e961e46ec0e07a070b2f81114950e67c80` |
| **CARD** | `canon/COMPUTE.md` at the checkout | `3b0237ebefd211b0d608429b45b30f9ff494bb9d87e0559a19352a4d400d2024` |

`origin/main` is `166db0eb`. The branch adds exactly one file, 89 lines, and no other path:
`git diff 166db0eb..40c64f5f --stat` is one insertion. That matches the revision's claim (R6:3–9) that this
is a design-only launcher amendment.

## 2. Verification method

Read-only. I compared:

- R6 line by line against D5b, especially D5b §1 (D5b:11–24), §2.1 (D5b:28–41), §2.3 (D5b:74–87), G6
  (D5b:89–123), the G1→G6→G7→S path (D5b:126–141), and the fixed settings (D5b:143–187);
- R6 against R6R's acceptance basis and its three non-blocking notes (R6R:52–64);
- R6 against the two task cards, the three governing PLAN rows, and CARD's host/lease/sharing statements
  (CARD:15, 20, 42, 81);
- the existing lease/foreign-process conventions in the repository (read-only) so that I would not mistake a
  house convention for a design defect (`r1/tests/test_t1_tasl_g1b.py:208–215`, `r1/tests/test_t1_tasl_g1b_x.py:285`,
  `r1/tests/test_t1_tasl_g1b.py:324–325`).

I ran no code, test, job, campaign, audit, label or evaluation. I opened no label, split, sweep-table or sealed
file. The only shell commands were `git show`/`git diff`/`git log`/`git status`, `shasum`, `read`, `grep` and
`find`. The revision's status block ("no code, no job, no campaign, no audit, no data read", R6:3) is accurate
for the revision itself.

## 3. Findings

### BLOCKING

None. This is a design-only amendment and it does not start any run or touch any record.

### MAJOR

**M1 — Refusal (a) is not implementable as written and contradicts the allowed second host.**
R6:58 refuses "a chunk whose detected GPU `model`/`uuid`/`driver family` is not the `campaign_model` declared
for that instance". But R6:54 defines `campaign_model` as "the model declared for the instance/arm" — a model
identifier, not a UUID and not a driver family. Taken literally, a UUID can never equal a model string and the
predicate is type-incoherent; taken as a composite hardware identity (model + UUID + driver), it refuses the
very case R6:64 explicitly allows ("The same GPU model on a second host is allowed") because the UUID changes.
That also cuts against R1-HOST-FREE (1) ("a job runs on any host and card that fits it") and (2)(c) (one GPU
*model*, not one UUID). The refusal must be split: refuse on `gpu.model != campaign_model`; record UUID, driver
and host and disclose them; if a driver-family change is meant to be a separate refusal, state it separately
and reconcile it with the second-host allowance.

**M2 — The model check is not anchored to an independent instance/campaign declaration, and the record lacks
the state refusals (b) and (c) need.**
R6:47–55 lists `campaign_model` but not `stage`, `arm`, `instance_id` or `repetition`; it lists no expected or
observed `proposer_model`; and it does not name the source or pin of the declared model. Refusal (b) (R6:59)
compares "another arm of an instance" and refusal (c) (R6:60–61) compares "the proposer server record", but
neither is a field in the per-chunk record. Worse, `campaign_model` is in the same `launch.json` the chunk runs
with, so a chunk can self-declare the card's model and pass refusal (a). R6:88 says the measured model remains
the reviewed note's model, but the record does not cite the note/PD sha and the rule does not say the comparison
is against that independent declaration. There is also no instance-level model claim shared across arms, so
refusal (b) is not race-free if two arms of one instance start together. The design should name the source of
truth (reviewed note/PD pin or a campaign spec), add the identity and proposer fields, and state where the
instance-level claim lives and which component evaluates it. This is design-level, not merely schema: without
an independent declaration the one-model refusal is self-referential.

**M3 — Shared-card execution is not reconciled with the accepted design's chunk-walltime/1.5× STOP, and that
is a governing-row conflict, not an implementation detail.**
R6:37–40 permits a shared card and checks free memory. R6:9 and R6:20 say STOP classes are unchanged. D5b:79
lists `chunk walltime` in the §10 STOP list, and D5b:156/160 fixes the smoke's measured chunk time as the
1.5× walltime. R1-CARD-SHARE (2) says speed is not a result; (3) says an attempt lost to the card or host is an
infrastructure failure, never an outcome and never a STOP; R1-NO-TIMEOUT (2) says a run that reaches its budget
or runs out of memory while another process was on its card is repeated, and (1) withdraws job and campaign
deadlines. The revision never says whether the walltime/1.5× check applies to a shared-card attempt. As written,
a slow chunk on a shared card can be a STOP or an outcome, contrary to the rows that the revision itself cites
for sharing. The amendment should state that no shared-card attempt is a STOP; the 1.5× bound is descriptive or
applies only to an exclusive-card attempt; and if the accepted design's `chunk walltime` STOP is withdrawn under
R1-NO-TIMEOUT, that withdrawal must be recorded (it is a design line, not a silent launcher change).

**M4 — The revision adopts R1-HOST-FREE (2)(c) but leaves D5b's "one GPU model for both stages" sentence
unamended.**
D5b:13 says "One GPU model for both stages, a model with a measured D.3 chunk time." PLAN R1-HOST-FREE (1)
explicitly names that D.3 sentence as replaced; R6:13–14 adopts the narrower (2)(c) rule (all arms of one
instance; one proposer model per campaign). But R6:21–22 says the revision changes §2.1's HTCondor sentence and
per-chunk record, not §1. The combined design therefore contains two hardware-binding rules. An implementer can
enforce a cross-stage model binding that the governing row removed, or cannot tell whether D.3a and D.3b may use
different models. The fix is small but necessary: explicitly replace D5b:13 with (2)(c), and say whether
D.3a/D.3b are one campaign for (2)(c).

### MINOR

1. **The new record is not stated to be additive.** R6:47 says "Every chunk's `launch.json` and `chunk.json`
   carry:" and then lists only hardware fields. D5b:39–41's `chunk.json` also carries pins, image, model sha,
   server flags, walltime and status, and D5b §2.3 uses those in preflight. Say "in addition to D5b §2.1's
   fields" so the revision does not appear to replace the scientific record.
2. **"Same `launch.json`" needs a parity rule.** R6:33 and R6:36 say the two launchers use the same
   `launch.json`; but `launcher`, `request`/`scope` and `lease_path` necessarily differ. R6:78–80's "same
   fields and the same argv" is the right parity test; state there that only those launcher-specific values may
   differ and that both launchers emit the field (the inapplicable one as null), not omit it.
3. **`gpu0.lock` is one card, not one host.** R6:37 names `~/r1_locks/gpu0.lock` on a GPU host. Ada has eight
   cards (CARD:20), and R1-HOST-FREE allows any fitting card. The lease must correspond to the card actually
   used (`gpu<index>.lock` or a per-UUID lease) and be recorded with the UUID; a fixed `gpu0.lock` either
   serialises the wrong card or claims the wrong device.
4. **The free-memory check has no required-memory threshold in the record.** R6:38 says "checks free memory",
   and R6:50 records `memory_total_mib`/`memory_free_mib_at_start`, but not the job's required memory or a
   `memory_check` result. Define `required_memory_mib` (or equivalent) and record PASS/fail. Insufficient free
   memory is a placement decision (wait/re-place), not a model refusal and not a STOP.
5. **"A lease held by another job" versus our-own-job sharing.** R6:62 refuses a lease held by another job.
   R1-CARD-SHARE (1) allows another of our jobs on the card when memory fits, while the existing reviewed G1b
   lease is exclusive (the repository tests above). State which convention D.3 uses: an exclusive lease among
   our own jobs (existing G1b/G.5 behaviour) while foreign processes are admitted when memory fits, or a
   per-job lease that permits our own jobs to share. The row's (5) preserves the reviewed lease check, so this
   needs a sentence, not an assumption.
6. **G6's default launcher is outside the recorded enum.** R6:42 says `chunk.json.launcher ∈ {htcondor, ssh}`;
   R6:72 says G6's default is "a direct deepthought process", which is neither. Either scope the enum to G1
   chunks or add a `direct` value (and define its record). G6's "same launcher-neutral manifest" (R6:22) makes
   this a real field question.
7. **The G6 "CPU-set/co-tenancy lease" on deepthought is undefined.** R6:73 says a CPU-set/co-tenancy lease is
   recorded. CARD:15/81 gives deepthought audits 16 workers with at least 10 of 40 cores free (co-tenancy
   sampled); CARD:42 documents `cpus-<set>.lock` for TASL CPU jobs, not deepthought. Either say the deepthought
   record is the co-tenancy sample/cores-free check (no lock file), or define the CPU lease path and owner. Do
   not invent a TASL-style lock on deepthought.
8. **"The analysis read the chunk files" is loose against D5b §3.2.** R6:42–43 says "the scientific record and
   the analysis read the chunk files". D5b:126–131 fixes the primary path as G1 → G6 → G7 outcome-table builder
   → the pinned `d3_analysis.py`, and says `d3_analysis.py` is not changed to read `summary.json`/`Y_final.jsonl`
   directly. Say that `chunk.json.launcher` is provenance only, that the G7 builder may read the chunk records,
   and that the pinned analysis input path is unchanged. Otherwise this reads as an analysis change.
9. **"Refusal before execution (a STOP)" is ambiguous against the design's stage-wide STOP.** R6:57 calls the
   four cases "a STOP, no output directory"; D5b:80–83 says a STOP stops new submissions, lets in-flight chunks
   finish and exits 3, and R6:9/20 says STOP classes are unchanged. Clarify that a wrong-model chunk is refused
   and re-placed (or, if the campaign has already moved model, is a campaign-level STOP), so a single bad
   placement does not silently become a new §10 class.
10. **The record does not name the environment freeze required by R1-HOST-FREE (1).** R6:49–55 names host,
    model, UUID, driver and memory, but not the environment freeze/image. The SSH path can run the same script
    on a host with a different Python/CUDA/Apptainer environment. Add the environment-freeze/image field (or
    cite the pinned image and its preflight check) and require the same environment check on both launchers.
11. **The test plan should name the parity/privacy cases and the ENGINEERING label.** R6:78–82 covers the
    hardware record, the four refusals, launcher parity, a CPU-only dry run, per-unit tier-E reviews and the
    full `r1/tests` base/tip run. Add: a test that the two launchers contain no duplicated chunk logic and
    invoke the same argv; a test that the HTCondor request is not rewritten; a test that the other-process
    record contains count/memory only; and label the CPU-only dry run `ENGINEERING_ONLY` per T-CLUSTER.
12. **The G6 paragraph relies on "existing §3.1 conditions" but does not restate the seal point or the
    16-worker/10-core condition.** R6:70–74 is otherwise consistent with D5b:118–120 and D5b:110–113. State
    "after campaign seal, 16 workers, ≥10 of 40 cores free" so the launcher-neutral rewrite cannot be read as
    dropping them; also say the direct deepthought process is sealed/attempt-recorded like a job.
13. **The §2.1 amendment is asserted, not quoted.** R6:21 says it changes §2.1's "One HTCondor job" sentence;
    the replacement should be written once: "one chunk per launch; when HTCondor is the launcher, one HTCondor
    job per `(stage,node,arm,repetition)` chunk; when SSH is the launcher, one process per chunk." D5b:29 and
    D5b:32 are otherwise compatible.
14. **R6R's non-blocking notes.** R6R:54–58 (G6 audit-job scheduling) is addressed by R6:70–74. R6R:59–62
    (§3.2 refusal wording) and R6R:63–64 (revision label) remain unit-level/editorial; say so in the unit
    report rather than implying this revision settles them.

## 4. Compatibility verdict

**With the accepted design (D5b).** The launcher amendment is structurally compatible: it keeps one chunk
record and one chunk script, it preserves arms, budgets, seeds, snapshots, Y/Y(w), the G1→G6→G7→S path,
pins, the H200 non-prerequisite and the STOP list in principle. It is not yet a clean amendment because M4
leaves D5b:13's "one GPU model for both stages" standing beside R6:13–14, and M3 leaves D5b:79/156/160's
walltime STOP unreconciled with the shared-card rule. M1/M2 make the hardware/refusal part incomplete.

**With `compute/20261126-02`.** The card's core requirements are present: one `campaign_chunk.py` (R6:26–29),
HTCondor as one of two launchers (R6:31–34), the other starting the same script over SSH under a lease
(R6:35–40), the launcher recorded (R6:42–43), no request edited to get a slot (R6:34), host/model/driver per
chunk (R6:47–55), and refusals for both one-model rules (R6:57–66). The card is not yet fully satisfiable
because refusal (a) is incoherent and refusal (b)/(c) lack an independent model source and cross-arm state
(M1/M2), and because the card's "runs wherever a card is free" now has to coexist with the walltime STOP (M3).

**With `cluster/20261126-02`.** The two-unit split, per-unit tier-E review, full `r1/tests` base/tip with zero
new failures, no GPU job and no evidence run, and CPU-only engineering dry runs are all named in R6:76–82. The
card's "list by test id" and "labelled" dry run are unit-report details (MINOR 11); the card's instruction to
settle R6R's non-blocking notes is only partly reflected (MINOR 14). No GPU/evidence run is proposed.

## 5. Limits of this review

This is a design review only. I did not test whether the proposed `campaign_chunk.py` or launchers are
implementable, did not run the `r1/tests` suite, and did not inspect any GPU host. The implementation remains
subject to the G1/G6 tier-E unit reviews, the pre-code pin/environment checks, the D.3 pre-declaration revision,
and the author gates already in D5b. I did not read any label, evaluation, split, sweep-table or sealed file.

I changed nothing except writing this review file. `git status --porcelain` shows the pre-existing untracked
`reports/` directory (created before this session, left untouched) and this new review file; no tracked file,
design, code, spec, pin or record was modified, staged or committed.

verdict: CHANGES REQUIRED
