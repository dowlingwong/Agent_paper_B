**AI-assisted independent design review (Claude, fresh reviewer session, 26 Nov 2026). Tier E; design only.**
I did not write the design or any code, and I ran no campaign, audit, test or job. I opened no label,
test-partition, evaluation-value, sweep-table or sealed file. Everything below was read with `git show`.

Under review: **D** = `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, branch
`mac-d3-design-20261126` @ `e16235b3` (118 lines). Authoritative text: **PD** =
`docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, branch `mac-d3-predecl-20261122` @ `a24a55bf`,
§§2, 4, 7 and 12 (and §§8–11 where they fix the interfaces G6 has to feed); **PLAN** = `docs/r1/PLAN.md` at
`e16235b3`, row `R1-D3-OUTCOMES2` (PLAN:1562) and `R1-D3-ORDER` (PLAN:1564); **S** = `r1/c3/d3_analysis.py`,
**A** = `r1/c3/audit.py`, **C** = `r1/c3/control.py`, all at `a24a55bf`.

# D.3 G1 campaign runner and G6 Y / Y(w) audit: independent design review

**VERDICT: ACCEPT WITH CHANGES (3 MAJOR, 12 MINOR, 4 NOTE).**
The direction and most fixed values are right, and the design is close to codeable. It is **not** accepted
for code until MAJOR 1–3 are settled. MAJOR 1 and 2 are decisions the design text must state before the
runner is written; MAJOR 3 is either a pre-declaration amendment (with the S re-pin that implies) or a
separately reviewed descriptive unit — either way the design must name it before any Y(w) code exists.

## What is right (checked and not re-litigated)

- **T0 set / WDBC.** D:10–12 names exactly the seven nodes of PD:53 and excludes `openml_wdbc`; matches.
- **W and cap.** D:37 applies `W=20` and an 80-call cap to every arm including A0, and D:37–38 counts
  replicate and verify runs against W and proposals/revisions/controller calls against the cap: matches
  PD:55–56 and PD:157–162. The 80 and the repetition count are **proposed** (PD:56, PD:526–527); see MINOR 12.
- **Seeds.** D:40–41, 63–64 and 72 reproduce PD:116, 120–121. Recomputed: replicate `6500+10i+j` for
  i = 0…17, j = 1…9 gives 6501–6679; audit `6700+10i+k` for k = 1…10 gives 6701–6880; smoke replicates
  6311–6319 / 6321–6329; smoke 6301–6302. Arithmetic and ranges are correct.
- **`campaign_id`.** D:26–29 correctly separates the harness `campaign_id` (= instance id, PD:119) from the
  D.3 record name (`<stage>__<arm>__<instance_id>__r<rep>`), and the ledger root
  `<run_root>/<stage>/<arm>/r<rep>/<instance_id>/` matches PD:119 exactly.
- **Chunk granularity.** D:24–25 (one HTCondor job per `(stage,node,arm,repetition)`, 18 instances, one GPU,
  16 workers, no per-instance job) matches PD §12 G1 (PD:498) and §11's layout basis.
- **K and audit conditions.** D:14–15, 72–82: K = 10, seeds 6701–6880, train seed = split seed = audit seed,
  deepthought CPUs, 16 workers, ≥10 of 40 cores free, e1-replay environment, harness-path equality, disclosed
  host difference. Matches PD:121 and PD:339–351. The audit cache keys in D:77 follow PD:335; the extension
  to repetitions and w points is reasonable (see MINOR 11 for naming).
- **No test/evaluation label, no T1 label, no use of D.3 output for training/tuning/selection, no resume**
  (D:16) matches PD:45–46 and PD:441, 454–455. A killed chunk is correctly rerun whole in a new directory
  with the old scene moved aside and disclosed (D:30–31 vs PD:452–453) — but see MINOR 3 on its STOP
  classification.
- **Snapshot at actual w / no imputation.** D:51–52 and D:89–90 state the right rule for the early end;
  the conflict is only with the primary-Y rule (MAJOR 1).

## MAJOR findings

**MAJOR 1 — The primary Y rule contradicts PD §7.1/§8 and the pinned S, and its "complete w=20 sets" rule
drops exactly the campaigns the paired design needs.**
D:75 says "**Y = Y(20)** is the primary outcome" and D:90 says "The analysis of the primary Y uses only
complete instance sets at w=20". PD's Y is not defined at w=20: "the final incumbent is the configuration of
the campaign's last kept trial (the start configuration if none). y_raw = (1/10) Σ_k [m(final,a_k) −
m(start,a_k)]" (PD:329–335). PD §8 has one row per campaign, `status: complete`, and explicitly permits
`ended_on: llm_call_cap` below W (PD:399–407); S rejects a non-complete row but accepts a cap-ended complete
row (S:273–277), computes Y from that row's `y_raw` (S:386–397), and requires the table to cover the declared
design exactly, i.e. every `(arm, node, seed, repetition)` once (S:310–312). Early endings are expected, not
exceptions: A1's constant screen can end at the cap with no run and Y = 0 (PD:213–216), any arm can end at
the 80-call cap below W (PD:166), and FIXR3/EGATE can end `no_fundable_candidate` (PD:167, 240–242, 286–287).
Dropping those campaigns from the primary contrasts (a) violates §8/S's exact-design requirement, (b) changes
the 126 paired instances of PD:362–369 and 371–375, and (c) biases any arm that ends on the cap — an analysis
that looks correct only if every campaign happens to reach w=20, which the design itself says is not so.
*Settle before code:* adopt the PD/S-consistent rule — primary Y = the final snapshot's incumbent at
`w_final` (the last charged count), which equals Y(20) when the campaign reaches 20; keep Y(20) as the
primary curve point where it exists; use `missing_w` only for the descriptive Y(w) points and never for the
campaign's primary Y. If the author instead wants Y(20) alone as the primary estimand, that is a change to
PD §7.1/§8 (and S, hence the §9/§14 sha pins) with an explicit, pre-declared missingness rule that does not
drop cap-ended campaigns — it cannot be a G6-only analysis rule introduced here. The design must choose and
say which; the current text is internally inconsistent (D:75 vs D:89–90) and inconsistent with PD/S.

**MAJOR 2 — The snapshot w counter is not defined precisely enough to exist for the arms that use
multi-run decisions, so the "exactly w = 5,10,15,20" points and the audit work list are undefined.**
D:46–47 writes a snapshot "after every cumulative worker-run count reaching w ∈ {5,10,15,20}" and D:110–111
asks whether cumulative worker runs including replicates is the intended "worker-run budget" reading. The
answer must be yes, but it needs precision the design does not give: PD:55 counts replicate **and verify**
runs against W; PD:157–162 defines the count as trials whose worker ran **plus 2r per verify** (A1/A2 verify
r = 2 costs 4 runs, PD:208–209); FIXR3's step is 3 runs (PD:232–247); an EGATE pair is a candidate run plus
an incumbent run when the incumbent has none (PD:258–261); and PD:162–164 says it is not yet settled whether
the harness `ComputeBudget` sees controller-issued runs, i.e. G8 (PD:510) must provide the counter. With those
jumps a declared w can fall **inside** a decision: what is "the incumbent" at that point, is the snapshot
taken mid-step with a serializable `controller_state_sha256`, or only at a decision boundary (in which case
the exact declared w may not exist and cannot be imputed)? D:48–49 lists `incumbent_config`,
`last_kept_trial_index` and `controller_state_sha256` as a decision-boundary snapshot, while D:46 describes
an exact-count trigger; the two do not yet meet. The design must also say whether snapshots are written live
or deterministically reconstructed from the sealed ledger at campaign seal (the latter would make
`controller_state_sha256` a ledger-prefix hash instead), and where/how the final-at-actual-w snapshot is named
(e.g. `snapshots/w18.final.json`) and how G6 recognises it (see MAJOR 1 and MINOR 4). *Settle before code:*
pin (i) the counter to `accounting.campaign_usage` (G8) charged runs including 2r verify and replicate runs;
(ii) snapshot timing (after each completed decision, recording the actual charged count, or via a
per-charged-run hook if one exists); (iii) live vs reconstructed; (iv) the final snapshot's path and role.
Without this the implementer cannot guarantee the four declared points or tell G6 which incumbent to audit.

**MAJOR 3 — G6's Y(w) outputs and the analysis interface are outside the signed pre-declaration and the
pinned analysis script; D:92–97 claims an interface S does not have.**
PD §7 has no Y(w), no w = 5/10/15/20 and no Y(20)-primary rule: §7.1 defines Y on the final incumbent
(PD:329–335), §7.3 the paired contrasts on that Y (PD:353–369). The only source of Y(w) is PLAN row
`R1-D3-OUTCOMES2`, which says these outcomes are "**written into the pre-declaration before any run**" and
defines Y(w) as "the incumbent after the w-th charged worker run, audited as Y is" (PLAN:1562). D:104 then
attributes Y(w) to §7 ("§7: … Y(w) secondary"), which misstates the authority, and D:105–106 lists the
missing author items as only "LLM cap, sidedness, repetitions, σ_node, A6" — omitting the Y(w)/snapshot/
schema/script changes, which are larger than any of those. D:92–97 says "`d3_analysis.py` receives `Y_w.jsonl`
and the campaign `summary.json`s … builds primary contrasts at Y(20) (§7.3 exact tests/intervals)". S does
not read either: it reads only one or two `r1_d3_outcome/v1` tables, the pre-declaration, the D.3b note and
the pinned noise summary (S:9–16, 513–527); §8's table has only the per-campaign `y_raw` and has no Y(w) rows
(PD:385–419); S validates that exact schema and computes Y from `y_raw` (S:223–330, 386–397). "Exact tests"
is also wrong: §7.3 is two-sided Student t with Holm within each family plus a stratified percentile
bootstrap (PD:362–379; S:56–76, 399–445), not an exact test.
*Settle before signing/code:* either (a) amend PD §7/§8 to declare Y(w) and give it a defined input (and
re-pin S's sha and tests in §9/§14, because S must change), with G7's outcome-table builder (PD:509) writing
the added data; or (b) define Y(w) as a separately reviewed descriptive unit with its own declared inputs,
schema and no verdict, still written into the pre-declaration before any run (per the PLAN row), and state
that it does not enter S's primary family. In both cases name G7 and G8 as dependencies of G1/G6 in the design
(see NOTE 3) and add Y(w)/snapshot/schema/script to the missing-author-items list. Option (a) is the cleanest
because PLAN:1562 already describes Y(w) as "audited as Y is"; option (b) keeps S frozen but needs a new
reviewed script and schema. Either way, do not make D:92–97's `Y_w.jsonl`/`summary.json` interface a wrapper
around S without re-pinning S.

## MINOR findings

1. **`ended_on` labels and precedence (D:38–39 vs PD:405–407, S:193, 285–286).** D uses
   `runs`/`llm_cap`/`stop`/`error`; PD §8 and S use exactly `worker_runs`/`llm_call_cap`/
   `no_fundable_candidate`, and `stop`/`error` are not table values (a STOP is reported as a STOP, PD:458–461;
   a campaign table row must be `complete`). The runner's internal status must be mapped to the three schema
   labels; `no_fundable_candidate` (FIXR3/EGATE only) is missing from D. Also state the precedence when the
   run budget and the call cap are reached by the same action (S's check `(runs == W) iff worker_runs` makes
   `worker_runs` win at 20 runs). G7's `ended_on` mapping must be specified.

2. **Preflight/STOP list is incomplete against PD §10 (D:55–62 vs PD:439–456).** Missing: the constants
   file's sha256 vs §14; the arms-frozen record's per-node A1/A2 constants (checked before D.3b); S's
   sha256 vs §14 and its tests passing at the launch commit; "any precondition of the stage's note missing";
   the measured D.3 GPU chunk time / walltime basis (see MINOR 9); `cache_prompt: false` and
   `enable_thinking:false` flag mismatches (§10 names them separately from "server flags"); >1 % of A5/A6
   forecasts answered by the fallback prior; any read of an evaluation value or a T1 label (D says only
   "test"); and any use of a D.3 output to train/tune/select an arm (D:16 states the rule but not the STOP).
   The §10 list should be reproduced item-for-item or the design should say the runner enforces §10 wholesale.

3. **Killed/non-clean chunk is a recovery rule, not a stage STOP (D:30–31 vs D:59–62; PD:452–453).**
   D:30–31 correctly says a killed chunk is rerun whole in a new directory with the old scene moved aside and
   disclosed. D:60 then lists "killed/non-clean chunk" in the campaign STOP list, which would end the stage
   instead of recovering. Fix the classification. Also define stage-wide STOP coordination across the ~42
   concurrent chunks: "A STOP stops submitting" (D:61) must say what stops (the chunk, the arm, the whole
   stage), how queued chunks are drained, how the STOP flag is published, and how in-flight chunks are
   recorded (PD:458–461 requires the stage reported as stopped with completed campaigns per arm/node).

4. **Output/ledger/audit path namespaces are underspecified and collide (D:26–34, 83–90).** D:30 checks the
   "output directory" absent before launch, but the ledger root of D:26–27 is shared by the seven node chunks
   of one `(stage,arm,rep)`; define the per-chunk directory vs the shared root, and whether the absence check
   is per chunk or per root (otherwise later node chunks fail the check). The G6 record
   `audit/w<w>/<instance_id>.json` (D:83) has no stage/arm/repetition and collides when two arms have snapshots
   at the same w for the same instance (different incumbent configs); the record path must be per campaign or
   the cache record must be explicitly per `(node, config_sha, seed)`. There is also no defined path for the
   final-at-actual-w snapshot/audit (MAJOR 1/2), which the primary Y needs.

5. **G6 job layout and cache are under-specified (D:77–78, 86–88 vs PD:339–351 and PD:508).** "One per
   stage/arm/repetition" with a cache "shared across arms, repetitions and w points" is a cross-job shared
   state problem: define the audit job's seal point (after all seven node chunks of an arm? after the stage?),
   which process owns a cache entry, the atomic write/lock protocol, and how a cached run records its
   provenance (which job/record) so "reused only if its record sha matches" is checkable. "deepthought direct"
   vs "separate HTCondor CPU chunks" (D:86–87) are two different scheduling models; pick one, and note that
   one host with 16 workers means the per-arm jobs must run serially or share the 16 workers (not 16 workers
   each). PD:339–351 says one host and the sweep-2 operator protocol; D should include `cotenancy.log`.

6. **G6 audit must not write label/evaluation blocks, and its failure/no-resume rule needs reconciling with
   `audit.py` (D:72–73, 96 vs PD:339–340; A:1–38, 92).** PD §7.2 says "no label/evaluation split, because Y
   trains nothing", but A's B.2 path writes separate label and evaluation blocks and defaults to seeds
   7001–7010 (`A:92`, A:25–38); G6 needs a mode that runs only the raw per-seed metrics on seeds 6701–6880,
   writes no label/evaluation block (a "no evaluation value" STOP), and treats a failed/non-finite seed run
   as a STOP with no retry (D:88) — while A's cache can resume an interrupted call, which is a different
   situation. Specify that the cache only reuses completed successful runs. Also D:96's "test-label read" is
   narrower than PD §8/§9/S: the refusal must cover any input whose name is a label, evaluation, split,
   sweep-table or `r1_sealed` path (PD:410–419; S:196–200).

7. **Smoke and verify-seed details (D:63–66 vs PD:120–122, 484–487).** The smoke count "(12 campaigns)" is
   six D.3a arms × two instances; it does not cover D.3b's A3/A5 (and A6); state the per-stage smoke rule and
   count. D:64 says smoke outputs "may set walltimes only", narrower than PD:120 ("walltimes and the compute
   projection"), which is exactly how §11's P7 projection is replaced — do not block that use. The verify-seed
   result must also be re-run by the D.3a note's P10 at the launch commit and the separate check must import
   `declared_d3_seeds`/`RESERVED_SEED_NAMESPACES` without changing them (PD:122, 548–551); D:65–66 omits the
   launch re-run. State the `vary` split policy (PD:59) explicitly. (The seed arithmetic itself is correct.)

8. **Runner fixed-design settings are missing from the G1 text (D:32–45 vs PD:54–67).** The design does not
   state `append_only_summary` memory mode, the structure-only `manager_proposal/v1` proposal schema and
   temperature 0.2 with the D26 seed, the server string with `enable_thinking:false` and `cache_prompt` false,
   or the `one_line/v1` skip display recorded in every manifest. PD:498's G1 spec explicitly requires
   "manifests with pins, skip display, seeds"; D:32's `chunk.json` lists pins/image/model/server/host/walltime/
   status but not skip display, seeds or memory mode. These are fixed by PD §2 and are STOP-checkable items;
   put them in the runner/preflight text.

9. **The GPU-model statement is outdated and the measured-chunk-time precondition is absent (D:12–13, 101 vs
   PD:65, 484–492; PLAN:1564).** D says launch "waits for [the H200] or for an author row that changes the
   measured model". PD §2 only requires "a GPU model with a measured D.3 chunk time"; §11 requires the
   2-instance smoke on the GPU model to be used, with walltime = 1.5 × the measured chunk time, and the
   proposed P7 projection STOP above 140 GPU-h (PD:484–492, 547). PLAN:1564 says that if the NEMO2 H200 is
   still out, another GPU model of the pool is measured instead — no author row is needed for that. Replace
   "H200 prerequisite" with the actual precondition (measured D.3 chunk time from the 2-instance smoke on the
   pinned model, 1.5× walltime, P7 projection and STOP) and add it to the pre-launch checks.

10. **No G6 compute projection (D:86–90; PD:489–492).** PD §11's audit estimate is for one Y audit per
    campaign: 126 × (10 start + 6 × 10) = 8,820 runs, 11.5 worker-h, ≈43 min at 16 workers. Four w points
    multiply it: with the design's `(node,c0,audit_seed)` cache the upper bound is ≈31,500 runs (≈41
    worker-h, ≈2.6 h at 16 workers); with no c0 reuse it is ≈60,500 runs (≈79 worker-h, ≈4.9 h). The design
    must state the G6 projection, the cache assumption behind it, and whether any new STOP or budget applies;
    §11's audit sentence should be updated (or the design should say it is superseded) before the note cites
    it.

11. **Cache key / record naming (D:77–78, 83–85).** The second key `(node, c0, audit_seed)` should identify
    `c0` by its config sha, not by the symbol; define the canonical `config_sha256` (which harness/config
    digest and version) so the runner's snapshot, the audit cache and G7's table agree. "Reused only if its
    record sha matches" is undefined (record of what?); a cached run needs provenance (source record path,
    w, arm) recorded for the disclosure D:78 promises. In `audit/Y_w.jsonl` (D:84) define rows for the
    declared `missing_w` points and for the final-at-actual-w snapshot, and say whether the row carries
    `y_raw`, `Y`, both, and the `σ_node` (the §8 table carries σ per node; do not duplicate it in a way that
    can disagree).

12. **The design targets pre-declaration revision 3, while the 26 Nov PLAN rows on its own branch require
    revision 4 before signing (D:101, 105–106; PLAN:1560–1564).** `R1-D3B-UNCONDITIONAL` (A5 − A3, D.3b
    unconditional) and `R1-D3-DECOMP` (adds A0R to D.3a) are in PLAN at the design commit, and
    `R1-D3-ORDER` step (2) says the pre-declaration is revised to include that section's rows, reviewed and
    signed before any D.3 run. The design's fixed arm list (six D.3a arms) and its "(12 campaigns)" smoke
    count would change (A0R → seven D.3a arms, 14 smoke campaigns; D.3b family gains A5 − A3). Make the G1
    runner take the signed arm list, smoke count and contrast families as parameters, and say which
    pre-declaration revision the design is against. Relatedly, D:101 lists "1 repetition" as a fact and D:37
    hard-codes the cap 80; PD:47, 56 and 526–527 make both proposed/parameter values — mark them PROPOSED or
    read them from the signed pre-declaration/key block.

## NOTES

1. **"§7.3 exact tests" (D:94).** §7.3 is a two-sided Student t with pooled df = Σ(mₙ−1) = 119, Holm
   step-down within each stage, a degenerate-SE rule and a stratified percentile bootstrap (PD:362–379;
   S:56–76, 399–445). It is not an exact test; use "§7.3 tests/intervals" to avoid an implementer choosing
   an exact test.
2. **Y(w) curve wording (D:75–76).** R1-D3-OUTCOMES2 defines the curve for w = 5,10,15,20 and calls Y(20)
   the primary Y (PLAN:1562). D calls only Y(5), Y(10), Y(15) "secondary" and Y(20) "primary". If Y(20) stays
   primary, still state the Y(20) point for the descriptive runs-to-match family (PLAN:1562(c)) and define
   the curve as the four declared points; otherwise MAJOR 1's final-incumbent reading changes the label.
3. **G7/G8 dependencies (D:105–106; PD:509–510).** The design's outputs (snapshots, last-kept trial, final
   config, Y_w rows) cannot become an `r1_d3_outcome/v1` table without G7's outcome-table builder and G8's
   replicate/usage accounting; PD §12 lists both as missing. Name them as dependencies and add them to the
   design's "missing" list, otherwise G1/G6 could be implemented and still not feed S.
4. **Trial budget.** PD:57 fixes the trial budget equal to the LLM-call cap so it never binds; D:37 uses
   `c3_budgets(W=20, LLM_CAP=80)` but does not say the trial budget is the cap (`c3_budgets` defaults to it,
   C:351–363). State it so the A0 change (PD §12 G1: replace `budget = 2W`) cannot regress to a binding trial
   budget.

## Answers to the design's §5 questions (before code)

1. **Snapshot semantics.** Yes, the counter must include replicate and verify runs, but as the **charged**
   count from `accounting.campaign_usage` (G8): trials' worker runs + 2r per verify + replicate runs. It is
   not the number of trials. A snapshot after every completed decision boundary, recording the actual w, is
   the only implementable reading unless the harness exposes a per-charged-run hook; exact w = 5,10,15,20 may
   fall inside a multi-run step (FIXR3 r=3, EGATE pairs, A1/A2 verify 4 runs) and must not be invented. A
   final snapshot at the actual w is required and correct — for the primary Y (MAJOR 1), not as a relabelled
   Y(20).
2. **Y(w) cache/missing.** No imputation and `missing_w` rows are correct for the four descriptive Y(w)
   points; cache reuse is fine if it is deterministic, provenance-recorded and disclosed. But the primary Y's
   final snapshot must be audited for every campaign (including cap-ended zero-run campaigns, Y = 0 by the
   c == c0 rule), and the analysis must not substitute a Y(w) miss for it.
3. **Audit jobs.** Separate jobs after seal, as proposed, are the right choice (keeps the audit off the GPU
   campaign chunk and makes cache sharing explicit). Fix the scheduling model (deepthought direct vs
   HTCondor), run the per-arm jobs serially on the one host or share the 16 workers, define the seal point,
   and use a single-writer/atomic cache with provenance (MINOR 5).
4. **Chunk granularity.** `(stage, node, arm, repetition)` with 18 instances, one GPU, 16 CPU workers and no
   per-instance job is correct and matches PD §11/§12 G1; the 16-worker CPU layout inside the GPU job is
   acceptable because G6 audits are separate CPU jobs on deepthought under §7.2.
5. **Missing STOP/preflight items.** See MINOR 2 (constants file sha, arms-frozen constants, S sha/tests,
   stage-note preconditions), MINOR 9 (measured GPU chunk time/walltime/P7), MINOR 8 (skip display, proposal
   schema/temperature, server `cache_prompt`/thinking flags, memory mode, manifests with seeds), MINOR 6 (no
   label/evaluation blocks in G6) and MINOR 7 (P10 verify-seed re-run, smoke count/projection). Add the
   stage-wide STOP coordination of MINOR 3 as well.

## Evidence and scope limits

`git show e16235b3:docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` (118 lines); `git show
a24a55bf:docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` (620 lines, §§2,4,7,8,9,10,11,12
read); `git show e16235b3:docs/r1/PLAN.md` lines 1560–1564; `git show a24a55bf:r1/c3/d3_analysis.py`,
`r1/c3/audit.py` and `r1/c3/control.py`. No code, job, campaign, audit or test was run; no label, evaluation,
split, sweep-table or sealed file was opened. I did not re-run the namespace check (it is a G1 implementer
deliverable under PD:122); the seed arithmetic above was hand-checked only. The design's §3.1 `Y(w)` formula,
K = 10 audit seed law and §7.2 audit conditions were checked against PD and match.

VERDICT: ACCEPT WITH CHANGES
