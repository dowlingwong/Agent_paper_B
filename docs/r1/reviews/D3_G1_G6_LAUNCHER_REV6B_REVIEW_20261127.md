# D.3 G1/G6 launcher revision 6b: independent design review

**AI-assisted independent review (fresh session, Claude; 27 November 2026, of the 27 November revision 6b). Tier E; design only.**
I did not write revision 6b, revision 6, the accepted D.3 G1/G6 design, the prior launcher review, or the R1–R6 review chain, and I did not participate in the G1/G6 work. I read the revision, the accepted design, the prior review, the two task cards, the governing PLAN rows and `canon/COMPUTE.md` read-only. I changed nothing except writing this review file.

## 1. Inputs

| Input | Revision / location | sha256 |
|---|---|---|
| **R6b** = launcher revision under review | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, branch `compute-d3-launcher-design-20261126` @ `c7b8f60a`, revision 6b | `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d` |
| **R6** = prior launcher review, CHANGES REQUIRED | `docs/r1/reviews/D3_G1_G6_LAUNCHER_REV6_REVIEW_20261126.md` | `644c0383c5649eac1c41818b7128997dca08f61d9f8a569e998f5dd5fe47e3d8` |
| **D5b** = accepted base design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, revision 5b, accepted by R6R | `4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23` |
| **R6R** = base-design acceptance | `docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R6_20261126.md` | `497b54d8f24a60542ca5719a2213c33b05771ba9e87e4b9f6304d2d590140cc8` |
| **T-COMPUTE** = task card | `tasks/compute/20261126-02-d3-launcher.md` at `origin/coord/coordinator` `480d6873` | `6a27ea1a7b97ef6d8492ba2f2b625408036e320aada1d2fe298793547f6ccaba` |
| **T-CLUSTER** = task card | `tasks/cluster/20261126-02-d3-g1-g6-code.md` at `origin/coord/coordinator` `480d6873` | `303fbe69f29c3d1269ead04bb437610244762fb7cd834086c545e8d5d6aa173b` |
| **PLAN** | `docs/r1/PLAN.md` at the checkout; R1-HOST-FREE, R1-CARD-SHARE, R1-NO-TIMEOUT | `4f476a8246c0442a8d02a8f63fdf71e961e46ec0e07a070b2f81114950e67c80` |
| **CARD** | `canon/COMPUTE.md` at the checkout | `3b0237ebefd211b0d608429b45b30f9ff494bb9d87e0559a19352a4d400d2024` |
| **RUNBOOK** | `docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md` (checked only for the A3/A5-versus-A2 statement) | `281ee1fd672e633815aebc501930900639c4ca2d1ce9fc38e7445bbdf6240f3e` |

`origin/main` is `166db0eb`. The branch adds exactly two files and no other path: revision 6b (145 lines) and the prior review (193 lines). `git diff 166db0eb..c7b8f60a --stat` reports 338 insertions, no deletions, and no code, spec, pin or record changed. That matches the revision's claim (R6b:3–11) that this is a design-only launcher/hardware/walltime amendment.

## 2. Verification method

Read-only. I compared:

- R6b line by line against D5b, especially D5b §1 (D5b:11–24), §2.1 (D5b:28–41), §2.3 (D5b:74–87), §3.1/§3.2 (D5b:89–137), and the fixed settings (D5b:143–187);
- R6b against every finding of R6 (M1–M4, MINOR 1–14) and against R6R's acceptance basis and three non-blocking notes;
- R6b against the two task cards, PLAN R1-HOST-FREE (1), (2)(a), (2)(c), R1-CARD-SHARE (1)–(5), R1-NO-TIMEOUT (1)–(2), and CARD's host/lease/sharing statements;
- R6b's A3/A5-versus-A2 sentence against the runbook's existing instruction to "Add A3/A5 versus A2 and A5 versus A3 as specified by D.3b" (RUNBOOK:78), so that I would not mistake an existing contrast for a new scientific claim.

I ran no code, test, job, campaign, audit, label or evaluation. I opened no label, split, sweep-table, evaluation or sealed file. The only shell commands were read-only inspection commands (`git show`/`git diff`/`git log`/`git status`/`git rev-parse`, `shasum`, `read`, `grep`, `sed`, `find`, `tail`, `ls`). The revision's status block ("no code, no job, no campaign, no audit, no data read", R6b:3) is accurate for the revision itself.

## 3. Findings

### BLOCKING

None. This is a design-only amendment and it starts no run and touches no record.

### MAJOR

None. The four prior MAJOR findings (M1–M4) are substantively answered; see the point-by-point closure in §4.

### MINOR

These are wording/schema precision notes for the G1/G6 unit review. None changes a governing rule or requires another design round.

1. **The withdrawal is stated more narrowly in the summary than in the operative section.** R6b:28 says the revision "withdraws the `chunk walltime` STOP of D5b §2.3/§3.3 **for shared-card attempts**", while R6b:109 says "D5b's `chunk walltime` STOP is **withdrawn** under R1-NO-TIMEOUT (1)" without qualification, and R6b:113–115 says no wall-clock value decides a result and the other STOP classes are unchanged. The operative §4 is the correct reading under R1-NO-TIMEOUT (1), which is not limited to shared cards. Make R6b:28 match §4 (withdrawn for every chunk; the 1.5× is descriptive), so an implementer cannot keep the STOP for an exclusive-card attempt. This is not a reason to withhold acceptance because §4 is unambiguous and R6b:11 says no other scientific choice changes.

2. **`campaign_model` and the manifest's `instance_model` are not tied together explicitly.** R6b:69 and R6b:89 speak of `campaign_model` in `campaign_model_source`/`campaign_manifest.json`, but R6b:83–84 describes the manifest as carrying per-instance `instance_model` and the campaign's `proposer_model` and does not name a manifest `campaign_model` field; R6b:34 also allows different instances to use different "campaign blocks" only as the reviewed note declares. Refusal (a) should say explicitly that it compares the observed model with the source's declared campaign model **and** with the manifest's `instance_model` for that instance (or state that the reviewed note declares one campaign model for every instance, making the two identical). Otherwise an implementer can read (a) and (b) as two different claims if the note ever declares per-instance models. This is schema precision, not a self-reference: the manifest, not `launch.json`, remains the comparator.

3. **"No wall-clock value decides a result" is broader than the chunk walltime.** R6b:114, read alone, could be taken to withdraw the per-run budget that R1-NO-TIMEOUT (2) deliberately keeps ("The run budget of a proposal stays part of the task"), including the rule that a run reaching its budget on an attempt that had its card to itself counts as the proposal's failure. The revision's scope (R6b:5–6, "launcher, hardware-record and walltime parts") and R6b:11 ("scientific choices ... unchanged") make the intended reading the chunk-level walltime only. Say "no chunk wall-clock value" and add that the per-run budget on an exclusive-card attempt is untouched, to prevent a reader from treating this as a science change.

4. **The manifest's `proposer_model` is per instance, but the proposer rule is per campaign.** R6b:83–84 places `instance_model` and "the campaign's `proposer_model`" in one per-instance manifest row. D.3 has multiple arms/campaigns on the same instance, and R1-HOST-FREE (2)(c) binds a campaign's proposer for that campaign's life. If different campaigns could use different proposer models, one row per instance cannot carry them all. State that D.3's proposer model is campaign-wide (one manager model for the run) or key the manifest by campaign. In the expected single-manager case this is only a schema note.

**Other observation, outside the M1–M4 scope.** D5b §3.3's "P7 projection ≤140 GPU-h" preflight line is untouched by this revision. Under R1-NO-TIMEOUT (3) that figure is a reporting threshold, not a STOP; the G1 unit should read it that way rather than preserve a stop at the figure. This is a pre-existing base-design wording point, not a finding against R6b's four corrections, and I do not count it against acceptance.

## 4. Point-by-point closure of R6's M1–M4

### M1 — model refusal compares only the GPU model identifier: **closed**

R6b:87–106 now splits the predicate cleanly. Refusal (a) is "a chunk whose detected GPU `model` (the model identifier, e.g. 'NVIDIA RTX 6000 Ada Generation') differs from the `campaign_model`" (R6b:88–89); UUID, driver and host are "recorded and disclosed, never compared to the model" (R6b:97); "The same GPU model on a second host, with another UUID or driver, is allowed for a chunk that fits; a different model is refused" (R6b:97–98). A note-fixed driver-family rule, if any, is explicitly a separate check named by the note (R6b:98–100). The old composite identity (model/UUID/driver family) is gone. This answers R6 M1 and matches R1-HOST-FREE (1) and (2)(c).

### M2 — independent source, manifest claim, identity and proposer fields, race-free refusals: **closed**

- **Source of truth.** The authority is the reviewed stage note/PD pin (or, before the note, the campaign spec), recorded as `campaign_model_source` with path and sha256; `launch.json` may not self-declare a different model (R6b:80–82).
- **Instance-level claim.** Before the first chunk, G1 writes one `campaign_manifest.json` under the run root with per-instance `instance_model` and the campaign's `proposer_model`, plus the source sha; it is written once, locked, and its sha is in every `chunk.json` (R6b:82–85). The chunk compares the observed card with that manifest, "not with a value the chunk chose" (R6b:84–85).
- **Record fields.** `stage`, `arm`, `instance_id`, `repetition`, `campaign_manifest_sha256`, `proposer_model_expected`, `proposer_model_observed` and `proposer_check` are all required per chunk (R6b:68–74).
- **Refusals (a)/(b)/(c).** (a) compares the observed model with the source/manifest declaration; (b) compares the arm's `instance_model` with the observed model, with the manifest as the race-free claim; (c) compares the observed proposer model with the manifest's `proposer_model` (R6b:88–93). None reads a value the chunk itself chose, and the once-written, locked manifest removes the two-arms-starting-together race. This answers R6 M2. MINOR 2 and MINOR 4 above ask for tighter naming between `campaign_model` and `instance_model` and for the proposer key, but they do not restore the self-reference or the race.

### M3 — shared-card walltime reconciled with the accepted STOP and the governing rows: **closed**

R6b:107–115 explicitly withdraws D5b's `chunk walltime` STOP under R1-NO-TIMEOUT (1), makes the smoke's measured chunk time and its 1.5× "descriptive planning values used for scheduling and reporting, not a pass/fail line", and says an attempt lost to the card or host (including a slow shared-card attempt, OOM or a kill) is sealed, recorded with the other compute processes and their memory, and repeated in a new directory. "No shared-card attempt and no wall-clock value decides a result" (R6b:113–114), and "the other §10 STOP classes are unchanged" (R6b:115). That is the rule R1-CARD-SHARE (2)/(3) and R1-NO-TIMEOUT (1)–(2) require: speed is descriptive, a lost attempt is never an outcome and never a STOP, and the chunk-walltime STOP is recorded as withdrawn rather than silently dropped. The summary qualifier in R6b:28 and the breadth of R6b:114 are the MINOR 1 and MINOR 3 wording points above; the operative rule is correct.

### M4 — D5b:13 replaced, both-stages question answered: **closed**

R6b:26–29 says the revision "replaces D5b:13 ('One GPU model for both stages') with the two R1-HOST-FREE (2)(c) rules and the paired-comparison rule below" and "No other line of D5b changes". R6b:31–35 then answers the question: D.3a and D.3b for one instance are a paired comparison (D.3b's A3/A5 against D.3a's A2 on the same instances), so they use one `instance_model` for that instance across both stages; this is (2)(a)/(2)(c) applied, not a second hardware rule; an arm's own campaign keeps its proposer model for its whole life; the sentence "replaces D5b:13 rather than standing beside it". I checked the A3/A5-versus-A2 statement against the runbook (RUNBOOK:78), which already instructs that contrast, so this is not a new scientific claim. No second hardware-binding rule remains.

## 5. Point-by-point closure of R6's MINOR 1–14

| # | Prior point | Status | Where / reason |
|---|---|---|---|
| 1 | Record must be additive to D5b §2.1 | **closed** | R6b:65–66: "in addition to D5b §2.1's `chunk.json` (pins, image, model sha, server flags, walltime, status); nothing is replaced." |
| 2 | Launcher parity rule: only launcher-specific values differ; inapplicable field emitted as null | **closed** | R6b:56–59: "only `launcher`, `request`/`scope` and `lease_path` differ, and each launcher emits the inapplicable field as `null`, never omitting it." |
| 3 | Lease must be per card actually used, not a fixed `gpu0.lock` | **closed** | R6b:103–105: `gpu<index>.lock` or a per-UUID lease; "never a fixed `gpu0.lock` on a multi-GPU host"; UUID recorded beside it. |
| 4 | Required memory and `memory_check` PASS/fail; insufficient memory is a placement decision | **closed** | R6b:71–72 records `required_memory_mib` and `memory_check`; R6b:94–95 says a memory-check fail is "wait or re-place; not a STOP". |
| 5 | Say which lease convention D.3 uses versus our own jobs | **closed** | R6b:102–104 chooses "an exclusive own-job lease, as the existing G1b/G.5 code uses", while foreign processes may share when memory fits. That is one of the two options R6 named; it preserves the reviewed lease check in R1-CARD-SHARE (5) and makes no shared-card attempt a STOP. The alternative (own jobs may share) would also be permitted by R1-CARD-SHARE (1), so this is a placement convention, not a contradiction. |
| 6 | G6's `direct` launcher must be in the recorded enum or scoped out | **closed** | R6b:56–58 adds `direct` and defines it as the G6 deepthought CPU default; R6b:121–124 defines its record. |
| 7 | Deepthought CPU lease must not be an invented TASL-style lock | **closed** | R6b:122–125: the record carries `host`, `workers: 16`, `cores_free_at_start` and `lease_path: null`; "deepthought has no TASL-style CPU lock file and none is invented." |
| 8 | Analysis path must stay G1 → G6 → G7 → pinned `d3_analysis.py` | **closed** | R6b:59–61: `chunk.json.launcher` is provenance only; the G7 builder may read chunk records; `d3_analysis.py` still reads the `r1_d3_outcome/v1` table exactly as D5b §3.2 says. |
| 9 | Refusal must be a placement refusal, with a campaign-level STOP only on model drift | **closed** | R6b:87: "a placement refusal, not a §10 STOP"; R6b:100–102: a model-mismatch chunk is re-placed, and only a campaign that has already moved model is a campaign-level STOP with no outcome table from the partial design. |
| 10 | Record the environment freeze and require the same check on both launchers | **closed** | R6b:76–77: `environment_freeze` (pinned image/venv freeze and preflight check); "both launchers run the same check." |
| 11 | Test plan must name parity/no-duplication, request-not-rewritten, count/memory-only and `ENGINEERING_ONLY` | **closed** | R6b:130–137 covers the hardware record and refusals, launcher parity with the same argv and no duplicated chunk logic, the HTCondor request not rewritten, the other-process record count/memory only, the G6 `direct` record, the CPU-only `ENGINEERING_ONLY` dry run, and the full suite base/tip listed by test id. |
| 12 | G6 must restate seal, 16 workers, ≥10 of 40 cores, and seal the direct process | **closed** | R6b:119–124: "after campaign seal, 16 workers, ≥10 of 40 cores free (co-tenancy sampled)"; a direct process is attempt-recorded and sealed like a job (stdout/stderr, host, start/end, exit). |
| 13 | Quote the §2.1 replacement once | **closed** | R6b:44–46 quotes: "one chunk per launch; when HTCondor is the launcher, one HTCondor job per `(stage, node, arm, repetition)` chunk; when SSH is the launcher, one process per chunk on the leased host." |
| 14 | R6R's non-blocking notes: settle level-0 items, leave §3.2 wording and revision labels unit-level | **closed** | R6b:144–145 says the R6R notes on §3.2 refusal wording and revision labels "remain unit-level/editorial and are not settled here"; the G6 scheduling note is addressed by R6b:117–126. The unit report should still record the two remaining notes, as R6 asked; that is a unit-report task, not a design gap. |

No prior MINOR is left open as a substantive gap. The four new MINOR notes in §3 are wording/schema items for the G1/G6 unit review.

## 6. Compatibility with the accepted design and the task cards

**With D5b.** There is no contradiction with §2.1, §2.3, §3.1 or §3.2:

- §2.1: the HTCondor-only sentence is replaced by the quoted launcher-neutral sentence, and the per-chunk record is additive; layout, ledger roots, outputs, seeds, snapshots and the G1→G6→G7→S path are untouched.
- §2.3: the `chunk walltime` STOP is explicitly withdrawn and recorded; the other §10 STOP classes are unchanged; a wrong-model chunk is a placement refusal/re-placement, not a new STOP class; the campaign-level STOP on model drift is the clarification R6 MINOR 9 asked for.
- §3.1/§3.2: the audit remains CPU-only on deepthought after seal with 16 workers and ≥10 of 40 cores free; the direct process is sealed/attempt-recorded; `d3_analysis.py` still reads the `r1_d3_outcome/v1` table and the launcher is provenance only. No audit value enters a campaign or controller.

**With `compute/20261126-02`.** The card's requirements are present: one `campaign_chunk.py` (R6b:39–42); HTCondor as one of two launchers and SSH as the other, both invoking the same script with the same `launch.json` (R6b:44–54); the SSH launcher takes a lease and checks free memory rather than requiring an empty card (R6b:50–53); host, GPU model and driver are recorded per chunk (R6b:68–74); and both one-model rules are enforced by refusals (b) and (c), with the independent source/manifest making them non-self-referential (R6b:80–93). The card's "refuses a chunk that would break either rule" is satisfied.

**With `cluster/20261126-02`.** The two-unit split, per-unit tier-E review, full `r1/tests` suite on base and tip listed by test id, no GPU job and no evidence run, and CPU-only `ENGINEERING_ONLY` dry runs are all named (R6b:128–137). The card's pre-declaration constants and the two remaining R6R notes are unit-report items, not design changes.

**Science and authority.** The revision changes no arm, budget, seed, snapshot, Y/Y(w) definition, analysis input or table. The only rule changes are the four corrections R6 required and the withdrawal of the chunk-walltime STOP that R1-NO-TIMEOUT (1) authorises. The A3/A5-versus-A2 pairing is already in the runbook. No new author-level decision is introduced; the exact script names, schema version, HTCondor request values and direct-wrapper remain unit-level (R6b:139–145), as the task cards intend.

## 7. Limits of this review

This is a design review only. I did not test whether `campaign_chunk.py`, `launch_htcondor.py`, `launch_ssh.py` or `campaign_manifest.json` are implementable, did not run the `r1/tests` suite, and did not inspect any GPU host. Implementation remains subject to the G1/G6 tier-E unit reviews, the pre-code pin/environment checks, the D.3 pre-declaration revision, and the author gates already in D5b. I did not read any label, evaluation, split, sweep-table or sealed file.

I changed nothing except writing this review file. `git status --porcelain` shows the pre-existing untracked `reports/` directory (created before this session, left untouched) and this new review file; no tracked file, design, code, spec, pin or record was modified, staged or committed.

verdict: ACCEPTED FOR CODE
