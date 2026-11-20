Reviewed base: `0cd8593375b9e768e86560ab94104fdae8062492` (branch `mac-g1b-h200-20261120`; accepted in round 5)

# Independent review record — G.5 T1 label-run authorization draft (approved: false)

**Unit.** `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (revisions 1–5) on `mac-g1b-h200-20261120` over
`main` `94db94bb`, with the projection it cites (`sweep2/g4/g5_projection.py`, `g4_lib.g5_node`). Authority:
R1-BX-D14, R1-T1-HOST-H200, R1-B2-DECOUPLE, R1-BX-D3, R1-TRACKP-SFT-DUP, C3_DESIGN §4; the queue of 20 Nov 2026,
item 3. The draft decides nothing: its author decisions (G5-W, G5-TEMP, G5-MEM, G5-AUDIT, G5-DIV, G5-CAP, G5-SPLIT)
carry options and recommendations. G.1b and G.4 are separate units with their own records.

**Process.** One independent reviewer (a separate agent that did not write the draft) for all five rounds; it edited
nothing (scratch under `/tmp/g5rev/` only) and read no secrets and no results of seeds 7001–7010. Round 5 confirms the
fixes made after the round-4 acceptance. The round texts are reproduced below as delivered, as block quotes.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `f2cf8df1 (draft rev 1, bdf9e078)` | NOT ACCEPTED |
| 2 | `2a646ea8 (rev 2)` | NOT ACCEPTED |
| 3 | `3308d813 (rev 3)` | NOT ACCEPTED |
| 4 | `b011f3fa (rev 4)` | ACCEPTED (2 minor) |
| 5 | `0cd85933 (rev 5)` | ACCEPTED (no findings) |

**Open for the author (from the round-4 and round-5 texts).** The author decisions of §2 and their PLAN rows; the
release rows R1-T1-LABELS-UNSEAL and R1-T1-LABELS-TEST-RELEASE; the cluster tests C1–C9 (C2 now also checks
fixed-seed determinism of edited code states, on which the proposed parent-run reuse relies); prerequisites P1–P11.

## Round 1 (`f2cf8df1 (draft rev 1, bdf9e078)`)

> Reviewed base: f2cf8df1934af6df97aa2c5c05485ca285c24659
>
> # Independent review (round 1): G.5 T1 label-run authorization draft
>
> - **Unit:** `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261121.md`, added in `bdf9e078`. The blob (`fd614345…`) is
>   unchanged at the reviewed tip `f2cf8df1` (branch `mac-g1b-h200-20261120`, worktree `/tmp/pb/wt/g1b`).
> - **Inputs read:**
>   - the G.1b plan, spec and lib, and the G.4 plan, spec, dates params and lib, all at `f2cf8df1`;
>   - `docs/r1/PLAN.md` on `origin/main` = `94db94bb`. PLAN line numbers below refer to that file;
>   - census `docs/r1/reports/trackg_g0_20261117/TRACKG_U2_ISO_RESULTS_20261119.md` @ `6bbf4b3e` (sha256 `8e228778…`,
>     matching the G.1b plan) and its result review;
>   - `C3_DESIGN.md` §4, the sweep-1 authorization, and `sweep2/s2_c2_lib.py` for the sweep shape.
> - **What I did not do:** no results of seeds 7001–7010 were read, nothing in the worktree was modified, and there
>   was no network or SSH.
> - **Draft line references** are to the 161-line file.
>
> ## Summary
>
> - **The draft covers every item the task asks for:** K, the seeds, W = 20, about 150 audited per node, STOPs
>   including the 2 × census question, sealing, and `approved: false`.
> - **Most PLAN citations are accurate:**
>   - R1-T1-HOST-H200 and R1-TRACKG-G3-EARLY;
>   - R1-BX-D3 and R1-BX-PROPOSED-CONFIRM (D3, D4, Track G E4);
>   - R1-BX-D8-V3-B (12 instances, T1 ≥ 3 test instances);
>   - R1-BX-D8-CONFIRM (gate sha);
>   - R1-TRACKG-PORT-DECISIONS (4);
>   - R1-HARNESS-ISOLATION.
> - **The projection arithmetic is reproduced exactly** (87.53 / 123.84 GPU-h).
> - **The note is not signable as written:**
>   - The two rules the task singles out, the divergence STOP and the sealing, are not enforceable as written.
>   - Several choices that change declared scientific content are made silently instead of being put to the author:
>     - W as manager calls rather than worker runs;
>     - the memory mode;
>     - the audit scope.
>   - The projection omits material cost terms, and its 150 GPU-h cap is likely to bind.
>
> ## Findings
>
> ### Blocking
>
> **B1. The divergence STOP cannot be enforced as written** (lines 21, 66, 79–81, 100, 156).
>
> - **(a) The citation is wrong.** The text the draft calls the "signed rule" is not the author's decision:
>   - The author's decision is "设 20% STOP" (PLAN :1016). It answered a question about **"its audited label
>     proposals' divergence fraction"** (:1012).
>   - The sentence the draft quotes is the recorder's *(proposed)* consequence (:1020).
>   - The draft labels it "Signed rule" and drops "audited".
> - **(b) The denominator is undefined.** It could be all 240 proposals, the valid ones, the ran ones, or the audited
>   `ok` ones. At a 0.6 executed share these give rates that differ by nearly a factor of 2.
> - **(c) The divergence definition does not match the confirmed one.**
>   - Confirmed REVISIONS (c)/E5 (:780) defines divergence per proposal **over the audit seeds**: a non-finite loss or
>     no metric, and a proposal is divergent when more than half of its seeds diverge.
>   - The draft's counters read in-campaign ledgers (line 156), which is single-seed divergence.
>   - The draft audits only `ok` proposals (line 61). So an in-campaign divergence is never audited, and E5's
>     seed-level rule never applies to it (see B4).
> - **(d) There is no evaluation point and no minimum count.**
>   - HTCondor transfers outputs at job exit, and the layout is "one job per node × instance block" (line 152).
>   - If the blocks run concurrently, the node-level STOP can only be computed after every campaign has finished. It
>     then saves nothing but the audits.
>   - Evaluated early on small n, it fires on noise. For example, 2 of the first 5 ran proposals is 40 %.
> - **(e) The timeout coupling is unchecked.**
>   - A timeout counts toward divergence (line 100).
>   - But the timeout basis is 3 × the **Ada** census time, and run time on H200 next to a resident llama-server is
>     unmeasured (G.4 plan §6 item 3).
>   - So spurious timeouts would inflate the STOP statistic.
>
> *Fix:*
> - Cite the author's words and the question exactly. Put the denominator to the author: "audited label proposals",
>   as asked, is recommended.
> - State the numerator under E5: proposals with more than half of their audit seeds divergent, plus in-campaign
>   divergent proposals once B4 has been decided.
> - State where the STOP is computed:
>   - in-campaign: a ledger pre-check on ran proposals, as an early warning;
>   - audit-level: the binding rule, computed before the next audit chunk is spent.
> - State when it is computed: after each instance-block job, with a minimum count (for example ≥ 40 ran proposals),
>   and with the blocks run in waves (for example 4 + 8 instances) so the STOP can act before most of the spend.
> - Make the H200 timeout check (cluster test C3) a prerequisite.
>
> **B2. Sealing is neither precise nor enforced** (lines 67–68, 105–118).
>
> - **(a) "Sealed" means integrity here, not access control.** The seal step reused from G.1b (`g1b_lib.py seal`,
>   `SEALED_ROOT` `/ceph/srv/dwong/paperb/…`) checks sums and copies without overwriting. It does not restrict
>   reading.
> - **(b) The only code-level lock is already open.**
>   - R1-BX-D8 (:752) makes readers refuse to run without a PLAN line containing `R1-BX-D8-CONFIRM`.
>   - That row has been on `main` since 17 Nov, and it says "Sweep-2 label tables may be analysed from this row on"
>     (:1252).
>   - So every existing reader would read the T1 table today.
>   - Line 24 ("The analysis lock stands") and `d8_lock: true` (line 68) therefore describe a lock that no longer
>     gates anything.
> - **(c) There is no defined unseal trigger.** "The R1-BX-D8-CONFIRM analysis run" (line 112) is not a defined
>   artefact. No commit, PLAN row or preregistration sha releases the seal.
> - **(d) Who may read is incomplete.** Only "operators and agents" are named. The draft does not say whether the
>   author, the reviewers, or the Track P loaders and SFT pipeline (R1-TRACKP-SFT-DEV) may read, or when.
> - **(e) What may be read is ambiguous.**
>   - The campaign ledgers carry per-proposal validation metrics and keep/discard decisions, which are single-seed
>     increments. The STOP counters read them (line 156), but they are not listed as allowed or forbidden.
>   - "The gate results" (line 110) could mean the isolation record gate or the C3 gate.
>   - The sealed task test metric is not mentioned.
> - **(f) Release happens in one step, but the analysis needs several.**
>   - The arms must be trained on the train partition and selected on validation before the gate reads the test
>     partition.
>   - Line 112 has the whole table "unsealed only by the analysis run".
>
> *Fix:*
> - Add an explicit unseal authority, for example an author row `R1-T1-LABELS-UNSEAL`, citing:
>   - the sha of the analysis preregistration (P3 split, gate v3, floors);
>   - the sha of the instance-split file.
> - Require every T1 reader to refuse without that row. Make this a P5 code requirement with a test.
> - Write the audit outputs only into the sealed tar, and have the job emit one `diagnostics.json` with a fixed schema.
>   That file is the only one operators and agents may open before release. Its schema lists the count and share
>   fields; ledger metric values are excluded.
> - Release in stages:
>   - the train and validation partitions to the C3 training pipeline (and to Track P only if the author says so);
>   - the test partition only to the gate run;
>   - sealed task test metrics never.
> - Name the author's own access rule.
> - Fix line 24 and define or drop `d8_lock`.
>
> **B3. The campaign shape is decided silently: W semantics and memory mode** (lines 31, 53–55; no memory mode
> anywhere).
>
> - **W is manager calls here, worker runs everywhere else.** The draft, following G.4 (`g4_lib.py:112`), sets
>   W = 20 **manager calls**. That contradicts:
>   - D1 (:335): the budget is compute (worker runs) plus an LLM-call cap;
>   - sweep 1 (`c3_sweep1_20261027.md`: "instances 18 × memory modes × W = 20") and sweep 2
>     (`s2_c2_lib.py:644`, `--runs 20`), which use worker runs;
>   - R1-W2-3-STOP (:1189): every Track P source ledger must use exactly W = 20 worker runs. T1 ledgers would fail
>     that check;
>   - R1-BX-D8's utility "scaled to a 20-run campaign" (:752).
> - **The memory mode is never declared.**
>   - Sweep 2 passes `--memory-mode` per chunk and runs both modes.
>   - R1-BX-PROPOSED-CONFIRM, Track G (E4) (:780) says "both memory modes; about 12 campaigns per T1 node".
>   - The draft does not say which mode G.5 uses, nor whether 12 instances means 12 campaigns or 24.
>
> *Fix:* add author decisions, each with options, the cost under each option, and a recommendation:
> - **G5-W.**
>   - (A) 20 manager calls: about 150 audited per node at a 0.62 share, but a T0/T1 run-budget mismatch and a
>     W2-3 conflict that needs an exemption.
>   - (B) 20 worker runs plus an LLM-call cap such as 80: matches the sweeps, gives about 240 audited per node, and
>     raises the projection by about 1.6×.
> - **G5-MEM.**
>   - (A) `append_only_summary` only, disclosed.
>   - (B) both modes with 12 instances each.
>   - (C) both modes with 6 instances each. This conflicts with V3-B's 12.
>
> **B4. The audit scope conflicts with confirmed rules** (lines 32–36, 61, 154).
>
> - The draft audits "every proposal that ran with an `ok` outcome".
> - `C3_DESIGN.md` §4 audits **every non-inert evaluated proposal**. No-ops are labelled by rule, and duplicates get no
>   label. The sweep-1 authorization (line 11) says the same.
> - Confirmed E5 (:780) gives a divergent proposal u = −g, and it judges divergence over the audit seeds.
> - With an `ok`-only scope:
>   - in-campaign divergent or timed-out proposals never get the seed-level test;
>   - inert and duplicate `ok` proposals would be audited at a cost and then labelled inconsistently.
> - The scope changes which proposals carry labels. That is declared content.
>
> *Fix:*
> - Align with C3_DESIGN §4 and E5: audit every non-inert, non-duplicate evaluated proposal, including in-campaign
>   divergent ones and timeouts. Label no-ops by rule. Give duplicates no label.
> - Or put the deviation to the author as decision G5-AUDIT, with its cost.
> - Count the parent incumbents correctly in either case (M2).
>
> ### Major
>
> **M1. The G5-DIV decision is framed unfairly, and its recommendation breaks down** (lines 82–87).
>
> - **No alternatives are listed.** Only one recommendation is given.
> - **The literal reading is not spelled out.** The census does give a number: each node has 1 deliberately divergent
>   record (`s002`, non-finite) among 8 executed records. That is 12.5 %, so "2 × census" is 25 %. That is looser than
>   20 % and would never bind.
> - **The recommended bound fails at a zero rate.**
>   - "2 × the G.4 pilot rate" becomes 0 when the pilot sees no divergence, which is likely with about 36 ran
>     proposals per node. The first divergent label proposal would then STOP the node.
>   - It covers at most 3 of the 6 nodes. The pilot runs on `mlab_cifar10`, `mlgym_fmnist` and
>     `mlgym_breakout_minatar` (R1-TRACKG-G3-EARLY :1330).
>   - It measures single-seed divergence per ran proposal. The 20 % rule may concern audited proposals (B1). So
>     "whichever is lower binds" compares two different quantities.
>
> *Fix:* present the options:
> - (A) the 20 % rule alone, with the literal census reading shown as non-binding;
> - (B) 2 × the pilot rate with a floor, for example STOP above min(20 %, max(2 × the upper 95 % Clopper–Pearson
>   bound of the pilot rate, 10 %)), on the same denominator as the 20 % rule;
> - (C) 2 × the G.1b divergent-row rate per node, which exists for all six nodes on H200 but covers declared edits,
>   not LLM proposals.
>
> Recommend one, and say what nodes without a pilot measurement get.
>
> **M2. The projection and the cap are incomplete** (lines 64–65, 99, 129, 131–148).
>
> - **The arithmetic checks out.** My recompute from the census B1 times with the stated assumptions (60 s per LLM
>   call, 0.6 executed share, 144 executed + 12 baselines audited) gives 87.53 / 123.84 GPU-h, matching the draft
>   to within rounding.
> - **Terms the projection omits:**
>   - *Per-job startup.* G.4 declares 1,500 s per job: GGUF fetch, environment, data, server. That is 2.5 GPU-h at one
>     job per node, or 30 GPU-h at one job per instance (72 jobs). The layout is not fixed.
>   - *Parent incumbents beyond the 12 baselines.* Each keep creates a new parent. At 20 % keeps that adds 16.8 GPU-h
>     at K = 10.
>   - *Slow runs.* Timeouts cost 3 × the census time, and edits can slow a run: `mlab_ogbn_arxiv` E4 took 21.8 s
>     against 5.65 s.
>   - *Speed on H200.* The census times are from Ada, without server co-tenancy.
> - **The audit volume has no cap.** "Every ok proposal is audited (not a cap)" means the volume is set by the share:
>
>   | Executed share | K = 6 (GPU-h) | K = 10 (GPU-h) |
>   |---|---|---|
>   | 0.8 | 107 | 155 |
>   | 1.0 | 127 | 185 |
>
> - **A plausible combination exceeds the cap.** At share 0.8, 20 % keeps, 1.25 × run inflation and 13 jobs per node,
>   the total is 177 GPU-h at K = 6 and 247 GPU-h at K = 10. Both are above 150.
> - **P7 points at a recompute that models a different shape.** `g4_lib.recompute_dates` uses ⌈150/share⌉ proposals,
>   audits 150 × K × run, and counts no baselines or parents. It gives 86.1 / 121.0 GPU-h. So the G.4 recompute
>   that P7 relies on (line 129) does not project the 12 × 20 shape this note declares.
> - **The cap is weaker than the G.1b one.**
>   - It applies only to projections. There is no running meter of consumed GPU-hours.
>   - Unlike the G.1b validator, it does not bound the requested slot-hours. Under G.4's walltime rule
>     (+3,600 s, ×1.5), the requested slot-hours at K = 10 would be about 190 or more.
> - **Two audit jobs would breach the walltime STOP.** At K = 10 the `mlab_imdb` audits take 100,062 s and the
>   `mlgym_breakout_minatar` audits 95,547 s. Run as one job per node, either exceeds 86,400 s and trips STOP 7.
>
> *Fix:*
> - Declare the binding formula: campaigns + (audited + 12 + keeps) × K × run + jobs × startup, with timeouts at 3×.
> - Make the G.4 recompute implement that formula, or say that the G.5 projection is computed separately from the
>   pilot medians.
> - Bound requested slot-hours and consumed GPU-hours as well as the projection.
> - Fix the audit-job layout under 86,400 s.
> - Present the cap as an author decision with options, for example:
>   - (A) 150 GPU-h with K = 6 only;
>   - (B) 250 GPU-h covering K = 10 with overheads;
>   - (C) 150 GPU-h with audits capped by a pre-declared random subset.
>
> **M3. "About 150 audited proposals per node" is not guaranteed and is stated as if measured** (lines 32–33, 62).
>
> - With 12 × 20 fixed (V3-B), the audited count is 240 × share.
> - It equals about 150 only at a share of about 0.62. At a share of 0.3 it is 72, and at 0.9 it is 216.
> - "At the pilot's executed share" refers to a pilot that has not run. The 0.6 is G.4's fallback value.
>
> *Fix:* state the dependency. Add a pre-launch author STOP if the pilot projects an audited count per node outside a
> declared band, for example [100, 200], with the options listed: accept, change W (B3), or cap the audits.
>
> **M4. The timeout basis is not tied to the G.1b decision** (lines 22, 100–101, 128).
>
> - G.1b plan §2a puts G1B-TIMEOUT to the author. Option B, recommended there, is 3 × the slowest census record,
>   because `ogbn` E4 exceeds 3 × B1.
> - P6 lists only G1B-EDITS.
> - G.5 uses 3 × the census time without saying which basis.
> - Under G.5, a timeout counts as divergence (B1).
>
> *Fix:* add G1B-TIMEOUT to P6 and state that G.5 uses the same timeout basis as the table's noise floor. Add the
> H200 run-time check, cluster test C3.
>
> **M5. Signed prerequisites are missing** (§6, lines 120–129).
>
> - **(a) The imdb baseline freeze.** R1-TRACKG-PORT-DECISIONS (3) (:1289) requires the port-written imdb baseline to
>   be frozen and independently reviewed **before any label run**.
> - **(b) Authority for the image.** R1-SWEEP2-IMAGE (:1287) says "image v2 只用于 Track P", and R1-QTORCH-AMEND
>   (:1276) approves v2 for Track P. No PLAN row authorizes the v2 digest for the T1 table. G.1b cites only the
>   20 Nov task text. The draft's image line (line 47) has no row in §1.
> - **(c) The heavy-tail declaration.** Confirmed E5 says "a heavy-tailed node uses a Student-t, declared before
>   labels are built". There is no step for it after G.1b.
> - **(d) A K check failure.** R1-BX-D3 (:747) requires a STOP for the author if the K check fails. K must also be
>   fixed at signature and uniform within the T1 table.
>
> *Fix:* add P8 (imdb freeze and review cited), P9 (an author row for image v2 on the T1 table), P10 (the per-node
> Gaussian or Student-t declaration, made from the G.1b summary before any label is assembled), and extend P4 with (d).
>
> **M6. The STOP list is incomplete or vague** (§4, lines 77–103).
>
> - **Pinned-identity STOPs are not incorporated.** The G.1b §7 and G.4 §7 STOPs are not carried over: image or
>   VERSIONS, GPU model or device-name variant, environment freeze, data manifest, GGUF or `llama-server` build and
>   offload, and the deadline. Add "every G.1b and G.4 STOP applies" explicitly.
> - **LLM-output STOPs are missing:**
>   - every call carries a completion cap, and a truncated reply is invalid (R1-EXAM-B1-TRUNCATION-INVALID :1141;
>     G.4 uses `max_tokens` 4096);
>   - there is no parse or invalid-share STOP like sweep 2's `max_parse_failure_rate` 0.2;
>   - there is no prompt-length STOP against the 32,768 context.
> - **The liveness threshold is ambiguous.** "Below the pilot's *(proposed)* 0.25" (line 91) could be an absolute
>   0.25 or a quarter of the pilot's value. It is also undefined for nodes that were not in the pilot.
> - **The consequences of a node STOP are unspecified.** Are partial instances kept sealed? Are they labelled? Do they
>   count toward B.7 if 3 or more test instances exist?
> - **Leave-one-suite-out is not addressed.** The current six nodes have no autoresearch-suite T1 node. Under
>   R1-BX-D8-CONFIRM (:1252), leave-one-suite-out STOPs at B.7 unless `autoresearch_fixedtokens` joins. The draft
>   should say this to the author.
>
> *Fix:*
> - Add the missing STOPs.
> - Define the liveness threshold as an absolute value, applying to every node.
> - State the partial-node rule: sealed, kept, and included or excluded by an author row.
> - Add the leave-one-suite-out risk to §5.
>
> **M7. The key values miss declared content** (lines 43–69).
>
> - **Missing fields:**
>   - the memory mode (B3);
>   - the W semantics and the LLM-call cap (B3);
>   - temperature 0.2 and the D26 per-call seed (:385);
>   - the completion cap;
>   - the timeout basis (M4);
>   - the GGUF sha256 (`2959c1b0…`);
>   - the harness commit (`c11ef75f`, branch `mac-trackg-t1-20261120`, the same as G.1b and G.4);
>   - the audit host (H200, same image and environment) and the job layout.
> - **The switch cannot check what is absent.** The note says the switch will match these lines, so anything missing
>   here goes unchecked.
>
> *Fix:* add these fields.
>
> ### Minor
>
> - **m1 (line 24, line 68).** "The analysis lock stands" is stale after R1-BX-D8-CONFIRM (:1252). Restate:
>   R1-BX-D8-CONFIRM is committed, and the existing preregistration and analysis gates remain. Also define or drop
>   `d8_lock` (see B2).
> - **m2 (line 118).** R1-TRACKG-ROLE (:536) is about test-scored tasks: select on the task's validation metric. It
>   does not govern the C3 test instances.
>   - *Fix:* add the rule "labels and keep decisions use the validation metric; the sealed task test metric is never
>     read for labels or selection". Cite the preregistration/V3-A (:1208) for the test-instance rule.
> - **m3 (line 115).** The T1 instance split is fixed only "before unsealing".
>   - *Fix:* fix it in the signed note now, deterministically from P3 (1/3 : 1/6 : 1/2 gives 4 / 2 / 6 instances, for
>     example by instance index or a declared seeded shuffle). The per-instance STOP diagnostics are then read after
>     the split exists.
> - **m4 (line 7).** "After the pilot (§7)" should be §8.
> - **m5 (line 15).** "By an amendment of this note" adds a procedure that R1-TRACKG-G3-EARLY does not have (it says
>   "join as soon as their U2 passes").
>   - *Fix:* mark it *(proposed)*, and say that a joining node also needs its H200 G.1b noise floor and its own
>     projection.
> - **m6 (lines 71–75).** The disjointness list for 5001–5012 is correct as far as it goes.
>   - It omits the census seeds 8001–8010 (E4 :780) and the exam blocks 9101+/9201+ (:732).
>   - 5001–5006 were the E1b audit seeds on CPU nodes (:395). There is no leak, since the nodes differ, but disclose
>     it or use 5101–5112.
>   - Require the G.5 validator to refuse every other block, as G.4's does.
> - **m7 (lines 18, 114).** V3-B's consequence is not stated: "a node below the floor is excluded from the IQM, kept
>   in the PoI and reported".
> - **m8 (line 38).** Say which σ̂ is meant: G.1b `joint` σ from seeds 3001–3030, `vary` split. Add the heavy-tail
>   declaration (M5c).
> - **m9.** G.1b plan §8 notes that Breakout's evaluation keys are public constants, which "matters for the label
>   table". The draft does not address this. State the mitigation (isolation, sealed test) or a disclosure.
>
> ### Notes
>
> - **N1. Facts verified as correct against `main` `94db94bb`:**
>   - **R1-T1-HOST-H200 (:1329):** H200 for G.1b, G.4 and G.5; one GPU model per table; whole-table fallback to Ada.
>   - **R1-TRACKG-G3-EARLY (:1330):** the six nodes and the later joiners.
>   - **R1-BX-D3 (:747) and PROPOSED-CONFIRM D3 (:780):** K = 10 until a PASS row, K = 6 for T1 only.
>   - **Track G E4 (:780):** 7001–7003 / 7006–7008.
>   - **R1-BX-D8-V3-B (:1234):** 12 instances per node as the author's addition; T1 ≥ 3 test instances.
>   - **R1-BX-D8-CONFIRM (:1252):** gate `6aa9985c`, sha256 `ffb70d7a…`; T0 and T1 pooled with tier as a stratum;
>     partial-T1 disclosure; leave-one-suite-out rule.
>   - **R1-BX-D14 (:758):** recompute after the pilot, reported to the author.
>   - **D4 (:780).**
>   - **R1-TRACKG-PORT-DECISIONS (4) (:1289).**
>   - **R1-B2-DECOUPLE (:678) and the 28 Oct clarification (:623).**
>   - **R1-SWEEP2-SETTINGS (1) (:1207).**
>   - **Census times:** the B1 values match the census table, and the census sha matches the G.1b plan.
>   - **Image digest:** matches G.1b and G.4.
> - **N2. The census times have limits.** They are single B1 runs on Ada; `mlgym_fmnist` B2 was 16 % faster than B1.
>   They size jobs. They are not H200 throughput.
>
> ## What still needs a cluster test
>
> - **C1.** Everything in G.1b plan §6 items 1–12 and G.4 plan §6 items 1–3:
>   - isolation in the container on H200, which on failure moves the T1 table to Ada;
>   - the VERSIONS sha, egress for wheels and data, the data bytes, JAX on H200, pushed commits, the device-name
>     variant, scratch and memory, GPU UUID variables, CPU affinity, walltime enforcement;
>   - the `llama-server` sha and build in v2, GGUF egress, and server co-tenancy.
> - **C2.** The audit runner, which does not exist yet, on H200. It must:
>   - re-materialise each proposal's code state and its parent incumbent from the ledger;
>   - run them isolated at joint seeds;
>   - show fixed-seed determinism of audit pairs on H200.
> - **C3.** Run time on H200 with a resident `llama-server`, against 3 × the Ada census time. This tests timeout
>   margins and false divergence, and feeds B1 and M4.
> - **C4.** Getting ledgers or diagnostics out mid-job, or in waves, so the node-level STOPs can act before most of
>   the spend (B1(d)).
> - **C5.** The audit-job split that keeps K = 10 imdb and breakout audits under 86,400 s (M2).
> - **C6.** Read restriction on the `/ceph` seal target (permissions or encryption) and the `diagnostics.json`-only
>   path (B2).
> - **C7.** GGUF transfer per job (19.6 GB × jobs) or a cache. Availability of the assumed 4 concurrent H200 slots.
>
> ## Verdict
>
> - **Not accepted.** B1 to B4 must be fixed before the note can go to the author for signature.
> - **What the fixes need:**
>   - a precise and enforceable divergence STOP;
>   - an enforced, staged sealing rule with a named unseal trigger;
>   - explicit author decisions for W, the memory mode and the audit scope;
>   - the M-items, chiefly the projection and cap terms and the missing prerequisites.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`2a646ea8 (rev 2)`)

> Reviewed base: 2a646ea8cf08e61a2478e9b0f654b353b71a8d84
>
> # Independent review (round 2): G.5 T1 label-run authorization draft, revision 2
>
> - **Unit:** `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (305 lines) and
>   `sweep2/g4/g5_projection.py` (34 lines), at `2a646ea8` on `mac-g1b-h200-20261120`.
> - **Diff checked:** against `f2cf8df1`. It is a full rewrite plus the projection script.
> - **PLAN:** `origin/main` `94db94bb`, as in round 1.
> - **Engine checked:** the harness at the pinned commit `c11ef75f`, read with `git show` in `/tmp/pb/wt/t1h`. These
>   are the files G.4 and G.5 reuse: `trackg/manager_v2_diff.py`, `trackg/campaign_v2_diff.py` and
>   `trackg/pilot_g4.py`.
> - **Projection check:** I ran the projection script read-only (`python3 -I -B`). The worktree is still clean.
> - **Not read:** no results of seeds 7001–7010.
>
> ## Status of the round-1 findings
>
> | R1 | Status in rev 2 |
> |---|---|
> | B1 divergence STOP | **Mostly resolved.** The author's question and answer are quoted exactly (line 28 = PLAN :1012/:1016). The denominator is now audited proposals and the numerator E5. There is a minimum of 40 and an in-campaign early warning, and the timeout is tied to G1B-TIMEOUT. **Remaining:** the order of audits and waves (R2-M3); the noise at the first look (R2-m3). |
> | B2 sealing | **Partly resolved.** It now has a `diagnostics.json` schema, the release row, a reader lock, staged release, and a named list of readers. **Remaining:** mode 0700 restricts nobody when everyone uses one uid; logs are transferred in clear; stage 2 has no trigger (R2-M4). |
> | B3 W and memory mode | **Addressed as decisions, but the memory option misdescribes the engine** (R2-B1). Decision interactions are missing (R2-M1). |
> | B4 audit scope | **Resolved as decision G5-AUDIT.** The new duplicate key creates a risk of leakage across the split (R2-M2). |
> | M1 G5-DIV framing | **Resolved.** Options A, B and C are given, each with its weakness, and the literal reading (25 %, non-binding) is shown. |
> | M2 projection and cap | **Formula and table resolved:** reproduced exactly (below). **The cap is not:** under the recommended option, a cap on requested slot-hours blocks K = 10 (R2-M1). |
> | M3 audited band | **Added, but it is incompatible with G5-W B** (R2-M1). |
> | M4 timeout basis | **Resolved.** It is in P6 and in the key values (lines 151, 187). |
> | M5 prerequisites | **Resolved.** P8–P10 added, and P4 now covers a K check failure. |
> | M6 STOPs | **Resolved,** except that two new thresholds are not marked *(proposed)* (R2-m1). |
> | M7 key values | **Extended, but one value contradicts the engine** (R2-B1). |
> | m1–m9 | **Resolved.** The split is fixed (G5-SPLIT). Seeds are 5101–5112 with the full disjointness list, checked. The tails are declared, the Breakout risk is disclosed, and the D8 text is corrected. |
>
> **PLAN facts rechecked against `94db94bb`:**
> - D1 :335; E4 and E5 :780; V3-A (3) :1208; V3-B :1234; D8-CONFIRM :1252; D26 :385;
>   R1-EXAM-B1-TRUNCATION-INVALID :1141; G5-DIVERGENCE :1012–1020; PORT-DECISIONS (3) and (4) :1289;
>   R1-SWEEP2-IMAGE :1287; R1-QTORCH-AMEND :1276.
> - All are quoted or paraphrased correctly.
>
> **Projection:** the table at lines 272–277 is reproduced exactly by `g5_projection.py`: 117.9 / 169.1 / 144.8 /
> 211.8 / 188.6 / 270.5 / 178.6 / 260.5 GPU-h, and 130 / 173 / 216 audited per node.
>
> ## Findings
>
> ### Blocking
>
> **R2-B1. The proposer settings in the draft are not the ones the engine uses; one is a silent scientific choice.**
> Lines 25, 55–56 and 184.
>
> - **What the draft declares.** Line 25 and the key values (line 184) declare "temperature 0.2; every manager call
>   carries a seed derived from (instance, trial index, repetition)" (D15/D26). The note says the switch will "match
>   every one" of these.
> - **What the engine does.** The v2-diff manager that G.4 runs and G.5 reuses
>   (`manager_v2_diff.py` @ `c11ef75f`):
>   - hard-codes `"temperature": 0.0`;
>   - lists `temperature` in `PINNED_FIELDS`, and `__post_init__` refuses any `extra_payload` that would override it;
>   - derives the per-call seed as `sha256(f"{base_seed}:{step}")`.
> - **Consequences:**
>   - **The pilot would be measured under different settings.** The G.4 pilot will measure liveness, invalid,
>     divergent and executed shares at temperature 0. These numbers drive G.5's projection, the 100–200 band, the
>     liveness STOP and G5-DIV B. They do not carry over to temperature 0.2.
>   - **Instances lose their diversity.** At temperature 0 on a deterministic server (R1-S2C3-DIAG found the H200
>     runs bit-identical), the seed has no effect. At step 1 the prompt is identical in all 12 instances of a node:
>     the same baseline code and no history. So every instance makes the same first proposal. The instances diverge
>     only through the metric values that later enter the history. This cuts proposal diversity and the audited count,
>     and it feeds R2-M2.
> - **The memory description in G5-MEM A is also inaccurate.**
>   - Option A (lines 55–56) says "`append_only_summary` only… the memory contrast stays on T0".
>   - The v2-diff engine has no memory-mode parameter (`run_v2_diff_campaign` takes none). It always sends its own
>     history: the **last 12 steps** (`MAX_HISTORY = 12`), each as summary → decision (metric).
>   - That is not the T0 `append_only_summary` mode (`autoresearch/memory/summarizer.py`).
>   - With W = 20 calls, steps 13–20 see a truncated history.
>   - Options B and C need a `none` mode that does not exist in the engine. The draft does not say so.
> - **A confirmed row is amended silently.** Option A also amends confirmed E4 ("both memory modes", :780), but the
>   draft does not say that an amending author row is needed.
>
> *Fix:*
> - State the engine's actual settings: temperature 0.0, its seed rule, and its last-12-step history.
> - Add an author decision **G5-TEMP**:
>   - (A) keep the engine as piloted, with temperature 0. This is a disclosed T1 deviation from D15/D26. Say what it
>     does to diversity across instances and to duplicates.
>   - (B) change the engine to temperature 0.2 with a D26-style per-call seed. This is a harness change and needs its
>     own review.
> - Give a recommendation.
> - Rewrite G5-MEM in terms of the engine:
>   - (A) the engine's own last-12 history, disclosed as different from both T0 modes, amending E4 by a row;
>   - (B) both modes, which requires building `none` and an `append_only_summary` rendering that matches T0;
>   - (C) as before.
> - **The pilot must match.** Make P3 require that the G.4 pilot ran with the W, memory and temperature the author
>   decides. Otherwise its shares cannot feed §8, the band or the STOPs, and the pilot is re-run or amended. The G.4
>   plan already says its W = 20 "is the one the T1 label campaigns use". The same must hold for temperature and
>   memory.
>
> ### Major
>
> **R2-M1. The decisions interact, but each is framed as if the others were fixed at A.** Lines 41–49, 93–104,
> 154–156 and 272–277.
>
> - **The band STOP rules out G5-W B by construction.**
>   - Under G5-W B the draft's own table gives 216 audited per node at any share (240 × 0.9).
>   - STOP 9 halts anything outside 100–200 audited per node after wave 1.
>   - So choosing B triggers the band STOP. The decision is constrained without saying so.
> - **Cap B (220 GPU-h) does not cover W B or MEM B at K = 10.**
>   - W B projects 260.5–270.5 GPU-h at K = 10.
>   - MEM B roughly doubles the campaigns. My extension of the script gives 229–283 GPU-h at K = 6 and 331–417 at
>     K = 10 under W A.
>   - Cap B "covers K = 10" only for W A, MEM A, AUDIT A, and only at share ≤ 0.8. At share 0.8 and K = 10 the margin
>     is 4 %.
> - **The cap on requested slot-hours blocks the recommended option at K = 10.**
>   - Line 103 applies the cap to "the requested slot-hours" as well.
>   - With the declared walltime rule (+3,600 s per job, ×1.5), the requested slot-hours under W A are:
>
>     | Share | K = 6 | K = 10 |
>     |---|---|---|
>     | 0.6 | 184 | 263 |
>     | 0.8 | 225 | 328 |
>
>   - So W A at K = 10 exceeds 220 even when the projection fits. Recomputed in `/tmp/g5rev/scripts/proj2.py` from the
>     script's own terms.
> - **G5-W B's cost is overstated at share 0.8.** "About 1.6 × the cost" (line 48) holds at share 0.6. At share 0.8
>   the ratio is 1.23 × (178.6 / 144.8 and 260.5 / 211.8).
> - **G5-DIV A's denominator depends on G5-AUDIT.** It is "audited proposals (G5-AUDIT)". Under G5-AUDIT B,
>   in-campaign divergent proposals are not audited, so the 20 % rule becomes weaker. This is not stated.
>
> *Fix:*
> - Add a short joint table of the decisions and their consequences for cost and audited count, with W × MEM × K at
>   share 0.6 and 0.8.
> - Make the band depend on G5-W: 100–200 under A, for example 150–240 under B.
> - Either give the cap per combination, or set the cap on requested slot-hours separately (for example 1.6 × the
>   GPU-h cap, or bound the requested hours by the cap divided by the walltime factor).
> - Correct "1.6 ×".
> - State how G5-DIV and G5-AUDIT couple.
>
> **R2-M2. Duplicates across instances can leak labels across the split.** Lines 64–67 and 106–110.
>
> - **The draft's rule.** G5-AUDIT A gives duplicates "(same node, incumbent, candidate)" no label and no audit,
>   across instances.
> - **Why the label is shared.** Audits use common seeds 7001+. So the label of an (incumbent, candidate) pair is the
>   same whichever instance proposed it.
> - **Where it leaks.** G5-SPLIT puts instances into train, validation and test. A duplicate group that spans
>   partitions either:
>   - leaks one label into test, if every copy is labelled; or
>   - removes the test copies, and the copy that keeps the label depends on job order, which is undefined.
> - **How often.** At temperature 0 (R2-B1), the step-1 proposal is duplicated across all 12 instances of each node.
> - **PLAN groups by instance.** R1-MAIN-PROPOSER (e) (:732) groups duplicates by **(instance, incumbent hash,
>   edit hash)**, and its cross-source rule only takes train to test. The draft's key drops the instance without
>   saying why.
>
> *Fix:*
> - Declare the grouping key and a partition-aware rule. For example: group by (incumbent hash, edit hash) across
>   instances; audit once; give the label to every member for folds; and keep groups that span train/validation and
>   test out of the test-side evaluation (or assign each group wholly to its earliest-split partition), disclosed.
> - Put this to the author inside G5-AUDIT.
> - Add the expected duplicate rate as a pilot read-out in P3.
>
> **R2-M3. The order of audits and waves is unspecified, so the divergence STOP may not act before the spend.** Lines
> 83–84, 117–118 and 121.
>
> - G5-DIV A evaluates "after each audit chunk, from at least 40 audited proposals". The STOP "halts that node's
>   remaining audits and campaigns".
> - §3 says each wave's diagnostics are read before the next wave is submitted. It does not say that the wave-1 audits
>   run before wave 2.
> - If the audits start only after both waves, the binding STOP can only stop audits.
> - Wave 1 (4 instances) gives 4 × 20 × s × 0.9 audited proposals: 43 at s = 0.6, but 36 at s = 0.5. That is below
>   the minimum of 40, so the first evaluation then slips to wave 2.
>
> *Fix:* declare the sequence:
> 1. wave-1 campaigns;
> 2. wave-1 audits;
> 3. the G5-DIV, band and liveness checks;
> 4. wave 2.
>
> Also say what happens when wave 1 yields fewer than 40 audited proposals (for example, evaluate at the end of wave 2
> with an early warning only).
>
> **R2-M4. Sealing still depends on goodwill in three places.** Lines 208–227.
>
> - **(a) Mode 0700 restricts nobody when everyone shares one uid.**
>   - The target is mode 0700 "for the operator account" under `/ceph/srv/dwong/…`.
>   - The operator, the cluster agent and the author all work under that one account, so 0700 restricts nobody. C6
>     would find that same-uid reads succeed.
>   - The out.tar files also arrive on the submit host in clear before sealing.
> - **(b) Logs are transferred outside the seal.** G.4's job transfers `llama-server.log` and `g4_run.log` in clear
>   (`g4_lib.py:48`). Server logs can contain prompts, and the prompts carry per-step metric values (`build_prompt`
>   writes `(metric)` per history line). The draft says per-proposal values go "only into the job's sealed `out.tar`",
>   but the transfer list is not constrained.
> - **(c) Stage 2 has no trigger.** "Test partition only to the gate run, after the arms are fixed" (line 226) has no
>   artefact. R1-T1-LABELS-UNSEAL releases both stages at once, and the reader lock checks only that row.
>
> *Fix:*
> - Encrypt `out.tar` inside the job to a release public key held by the author, leaving only `diagnostics.json`,
>   `job_record.json` and the sums in clear. Or declare openly that the seal is procedural (STOP 11 plus the recorded
>   sha256 of every file and an access log) and drop the 0700 claim.
> - Put every log inside the sealed tar, and give `job_record.json` a fixed schema with no per-proposal values.
> - Make stage 2 need its own trigger: a second row, or a field in R1-T1-LABELS-UNSEAL that cites the sha256 of the
>   frozen arms. The reader lock should refuse the test partition until then.
>
> **R2-M5. "Or its pushed successor" leaves the harness pin open, and it contradicts P5.** Lines 176 and 247–248.
>
> - **The two lines conflict.**
>   - Line 176 allows "c11ef75f… or its pushed successor".
>   - P5 requires that "its harness pin equals the G.1b pin".
> - **G.5 needs harness changes.** It needs at least the audit runner, `diagnostics.json`, and possibly a worker-run
>   budget, a memory mode or temperature (R2-B1).
> - **So one of three things follows:**
>   - G.1b runs at a successor, which is not its current spec;
>   - the labels run at a different harness from the noise floor;
>   - or P5 fails.
>
> *Fix:* choose and state one of these:
> - freeze the G.5-ready harness before G.1b launches, so both use one pin;
> - declare a file-level identity check, so that the measurement path (runner, isolation, `noise_floor`, node kits)
>   is byte-identical between the G.1b pin and the G.5 pin;
> - record the pin difference as an author decision.
>
> Remove the open-ended "or its pushed successor".
>
> ### Minor
>
> - **R2-m1 (lines 140–141, 154–156).** Two thresholds are written as settled without *(proposed)* and are missing
>   from P6:
>   - the absolute liveness threshold 0.25;
>   - the audited band 100–200.
>
>   Both are thresholds the draft introduces. *Fix:* mark them *(proposed)* and list them in P6, or fold them into
>   G5-DIV and G5-W.
> - **R2-m2 (lines 43–44).** "The per-proposal labels and the gate's per-proposal utility… do not depend on it"
>   overstates the case. The labels' definition does not depend on W, but the population of proposals does:
>   incumbent quality, trial index, about 12 runs per campaign against 20 on T0. That matters for pooling with tier as
>   a stratum. *Fix:* soften the sentence and disclose the difference in population.
> - **R2-m3 (line 83).** At the first look (n = 40), a node whose true E5 rate is 15 %, below the rule, STOPs with
>   probability 0.135 (binomial P(X ≥ 9)). At 18 % the probability is 0.29, and repeated looks raise both. At n ≈ 130
>   the 15 % figure is 0.047. *Fix:* give these numbers in G5-DIV A, so the author sees what "at least 40" costs.
>   Offer the alternative of evaluating at wave ends only.
> - **R2-m4 (lines 279–280).** `recompute_dates` "sizes the dates, not this table". The R1-BX-D14 dates are therefore
>   computed from 86 / 121 GPU-h, while the G.5 table is 118–212 GPU-h, so the dates reported to the author are
>   optimistic. *Fix:* make `recompute_dates` take the G.5 projection, or report both.
> - **R2-m5 (line 264).** "Audited = 0.9 × ran (inert and duplicates excluded)": in the engine, inert proposals and
>   duplicates within a campaign are not run at all (`campaign_v2_diff`, step 2). So the 0.9 factor can only stand for
>   duplicates across instances. *Fix:* state where 0.9 comes from, and replace it with the pilot's measured duplicate
>   rate (R2-M2).
> - **R2-m6.** The G.4 plan (§3) still defers its divergence reference to the G.5 draft. G.5's binding rule is now
>   E5 on audited proposals, which the pilot cannot measure because it runs no audits. *Fix:* align the G.4 plan text
>   so that the pilot's `divergence_vs_census` feeds only G5-DIV B and the early warning.
>
> ### Notes
>
> - **N1. G5-SPLIT** is procedural, with one *(proposed)* rule. That is acceptable. The hash ordering is
>   deterministic and pre-declared, and 6 / 2 / 4 matches P3. Fixing it now resolves round-1 m3.
> - **N2. Wave sizes 4 + 8** are procedural and acceptable. Under MEM B combined with W B, wave 2 projects to
>   92k s of walltime on imdb, which is above 86,400 s. Recheck the layout if the author picks that combination.
> - **N3. Framing is otherwise fair.**
>   - G5-AUDIT and G5-DIV each give options with their weaknesses stated.
>   - G5-DIV keeps the task's "2 × census" in its literal form and says plainly that it never binds.
>   - G5-CAP C's coverage cost is stated.
>
> ## Fairness and silent-choice audit (as requested)
>
> | Decision | Options and recommendation | Fair? | Silent choices left |
> |---|---|---|---|
> | G5-W | A, B; A recommended | Mostly | B's cost overstated at s = 0.8; the band and cap exclude B without saying so (R2-M1); the claim of no dependence is overstated (R2-m2) |
> | G5-MEM | A, B, C; A recommended | **No** | A misdescribes the engine's memory and amends E4 without a row; B and C need an engine mode that does not exist (R2-B1) |
> | G5-AUDIT | A, B; A recommended | Yes | The duplicate key and split rule (R2-M2) |
> | G5-DIV | A, B, C; A recommended | Yes | The audit/wave order (R2-M3); the noise at the first look (R2-m3); the coupling to G5-AUDIT (R2-M1) |
> | G5-CAP | A, B, C; B recommended | Partly | Valid only for W A / MEM A; the slot-hour bound blocks K = 10 (R2-M1) |
> | G5-SPLIT | one *(proposed)* rule | Acceptable | none |
> | — | — | — | **Temperature 0 versus 0.2 is not a decision at all (R2-B1).** Harness pin "or successor" (R2-M5). Liveness 0.25 and band 100–200 unmarked (R2-m1). |
>
> ## Cluster tests
>
> C1–C7 (§10) are complete for what is declared. Add:
>
> - **C8.** Temperature-0 behaviour on H200: the rate of identical proposals across instances, from the G.4 pilot's
>   3 instances (R2-B1, R2-M2).
> - **C9.** The requested slot-hours against the cap under the chosen W and K (R2-M1).
> - **For C6:** that the read restriction holds against the shared operator uid, or that encryption works end to end
>   (R2-M4).
>
> ## Verdict
>
> - **Not accepted.** R2-B1 must be fixed before the note goes to the author. As written, the note declares
>   temperature 0.2 with the D26 seed and an `append_only_summary` memory. The engine that G.4 pilots and G.5 reuses
>   runs temperature 0.0, its own seed rule, and a last-12-step history. That is a scientific choice made silently.
> - **R2-M1 to R2-M5** are needed for the decisions to be framed fairly and for the cap, the band, the duplicates, the
>   STOP order and the seal to be enforceable.
> - **Everything else from round 1 is resolved or nearly so.**
>
> VERDICT: NOT ACCEPTED

## Round 3 (`3308d813 (rev 3)`)

> Reviewed base: 3308d8131aac526b847b211a1a3ba91c22042920
>
> # Independent review (round 3): G.5 T1 label-run authorization draft, revision 3
>
> - **Unit:** `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (378 lines), together with the
>   `g4_lib.g5_node` / `recompute_dates` formula it relies on (from `f2997027`) and `sweep2/g4/g5_projection.py`.
>   Branch `mac-g1b-h200-20261120`; diff checked against `2a646ea8`.
> - **Harness checked:** `b5747066` (`/tmp/pb/wt/t1h`, read with `git show`). I diffed it against `c11ef75f`.
> - **PLAN:** `origin/main` is now `df58bcd5`. Its PLAN.md is byte-identical to the `94db94bb` copy used in rounds 1–2.
> - **Projection check:** I ran the projection script read-only (`python3 -I -B` from `/tmp`).
> - **Constraints kept:** both worktrees are clean; no results of seeds 7001–7010 were read.
>
> ## Status of the round-2 findings
>
> | R2 | Status in rev 3 |
> |---|---|
> | B1 engine settings | **Resolved.** §1 now describes the engine correctly. I verified at `b5747066`: `V2DiffManager.temperature` (default 0.0, range-checked, still pinned against `extra_payload`); `include_history` (False is `none`); `MAX_HISTORY = 12`; seed `sha256("<seed>:<step>")[:8]`. The G.4 spec passes `temperature: 0.2`, `memory_mode: history`, harness `b5747066`. G5-TEMP gives A and B fairly, and B's cost (re-pilot, step-1 duplication) is stated. G5-MEM is written against the engine's real modes, says that A needs a row amending E4, and says that a T0-matching rendering would be new work. P3 binds the pilot to the decided W, memory mode and temperature. |
> | M1 interactions | **Resolved.** The §2.8 table is reproduced exactly by `g5_projection.py` (all 16 cells, GPU-h, slot-h and audited). The band depends on W, and the cap options are re-based (B = 230). The ratios 1.61 × / 1.23 × are checked. The coupling between DIV and AUDIT is stated, and slot-h ≤ 1.6 × cap holds in the recommended row (348.4 ≤ 368). **Plumbing left:** R3-M2. |
> | M2 duplicates | **Resolved in substance.** The key follows R1-MAIN-PROPOSER (e); cross-instance groups are audited once; the primary test population excludes groups seen in train or validation; the pilot measures the rate (`cross_instance_duplicates` in `pilot_g4.summarise`, keyed on (incumbent code state, candidate code state), verified). **Left:** it is not quite "the same rule as R1-TRACKP-SFT-DUP" (R3-m1). |
> | M3 order | **Resolved.** §3 gives wave 1 → its audits → checks → wave 2, and handles the case of fewer than 40 audited. |
> | M4 seal | **Resolved as declared.** The seal is stated to be procedural, with encryption as an alternative. Logs go inside `out.tar`, and the schemas are fixed. There are two release rows, and the stage-2 row cites the arm sha256s. **Wording left:** R3-m2. |
> | M5 harness pin | **Mostly resolved.** "Or successor" is removed. G.5 must descend from the G.1b pin, with a path-identity check. **Left:** the list of paths is incomplete (R3-M1). |
> | m1–m6 | **Resolved.** 0.25 and the band are *(proposed)* and in P6; the W wording is softened; the first-look odds match my numbers; the 0.9 factor is replaced by a duplicate factor of 1.0; the G.4 plan wording is updated. **m4 is only partly resolved:** see R3-M2. |
>
> ## Findings
>
> ### Blocking
>
> **R3-B1. E5 divergence is decided over all K audit seeds, so evaluation seeds feed training labels and node
> selection.** Lines 92–93, 118, 194 and 278.
>
> - **What the draft says.**
>   - G5-AUDIT A (line 92): "E5 then decides divergence **over the audit seeds** for every audited proposal."
>   - G5-DIV A (line 118): numerator = "more than half of **their audit seeds** divergent".
>   - The audit seeds are the K seeds: 7001–7010 at K = 10, or 7001–7003 plus 7006–7008 at K = 6. Half of them are
>     **evaluation** seeds.
> - **Consequence 1: evaluation seeds decide training labels.** E5 (:780) gives a divergent proposal the action target
>   u = −g, and marks a proposal with some divergent seeds as partial. If that test counts evaluation-seed outcomes,
>   then a C3 **training** label is decided partly by evaluation seeds.
> - **Consequence 2: evaluation seeds decide which nodes stay.** The G5-DIV STOP removes nodes from the table, which is
>   selection. It would be driven partly by evaluation seeds.
> - **The signed rule this breaks.** R1-B2-DECOUPLE (:678) and its 28 Oct clarification (:623) say the evaluation
>   seeds are "never [used for] C3/Track P training, tuning or selection". Round 1 confirmed that seed blocks are
>   "never mixed" in the sweep-1 authorization.
> - **It is also visible before release.** `diagnostics.json` (line 278) carries an "E5-divergent" count before
>   release. If that count includes evaluation seeds, information from the evaluation block is read before release.
> - **Why it is blocking:** it is a silent scientific choice that conflicts with a signed row.
>
> *Fix:*
> - State that E5 is applied **per seed block**:
>   - the label-side classification (divergent, partial, u = −g for training) uses the **label seeds only**: 7001–7005,
>     or 7001–7003, where "more than half" means at least 3 of 5, or at least 2 of 3;
>   - the evaluation-side `y_eval` treats evaluation-seed divergence by its own rule, written into the preregistration.
> - Base the G5-DIV numerator and the `diagnostics.json` count on the label seeds only.
> - If the author prefers all K seeds for the STOP, write that up as an explicit option, with the R1-B2-DECOUPLE
>   conflict and the amending row it would need.
>
> ### Major
>
> **R3-M1. The measurement path in P5 is incomplete, so the identity check can pass while the path changes.**
> Lines 319–322.
>
> - P5 lists `runner`, `isolation`, `noise_floor`, `outcome`, `selection` and the six node kits. At `b5747066`,
>   `runner.py` and `noise_floor.py` import further modules that are not on the list:
>   - `trackg/determinism.py`;
>   - `trackg/diff_support.py`, which applies diffs, computes code-state hashes and tracks evaluated states;
>   - `trackg/node_template.py`;
>   - `trackg/gpu_identity.py`;
>   - `autoresearch/control_plane/permissions.py` and `autoresearch/nodes/spec.py`, through `diff_support` and
>     `node_template`;
>   - `trackg/declared_edits.py`, which builds G.1b's edit configurations.
> - The isolated worker library `trackg/node_lib/ar_isolated.py` is also missing.
>   - R1-TRACKG-AR-COND7 (:1317) requires a change to `ar_isolated.cuda_open`, and to the result path, before
>     `autoresearch_fixedtokens` can join.
>   - A G.5 harness carrying that fix would change the isolation layer of all six nodes while
>     `git diff --quiet <listed paths>` still passes.
>
> *Fix:*
> - Define the path as the import closure of `noise_floor` and `runner`, plus `node_lib/` and the node kits, and list
>   the files explicitly.
> - Or check identity on the whole `src/autoresearch/trackg/` except `campaign_v2_diff.py`, `manager_v2_diff.py`,
>   `proposal_v2_diff.py` and `pilot_g4.py`, plus the two cross-package modules.
> - State what happens when the COND7 change lands: either G.1b is re-measured on the six nodes, or the change has to
>   be shown not to touch their path.
>
> **R3-M2. The binding P7 number and the cap check in `recompute_dates` do not follow the decisions.** Lines 143–144,
> 313–315 and 344–346.
>
> - **(a) MEM B is not modelled.** `recompute_dates` has no memory-mode factor, so it always projects one mode. Under
>   G5-MEM B the binding P7 number would be about half the true cost: §2.8 shows MEM B as 2 ×.
> - **(b) The pilot's duplicate rate is not used.** `recompute_dates` uses `params["dup_factor"]` (1.0) and never reads
>   the pilot summary's `cross_instance_duplicates`. Yet §8 implies that the measured rate replaces the pre-pilot
>   factor, and P3 requires the pilot to report it. The 1.0 is conservative for cost, but it overstates the audited
>   count that the band STOP extrapolates.
> - **(c) The cap value is stale in two places.** `g4_dates_params.json` has `g5_cap_gpu_hours: 220`, and the G.4 plan
>   says "220 as proposed in the G.5 draft". The draft's G5-CAP B is 230, so `g5_within_cap` is checked against the
>   wrong cap.
> - **(d) Slot-hours are not checked.** `recompute_dates` does not check requested slot-hours against 1.6 × the cap,
>   although STOP 9 includes it.
>
> *Fix:*
> - Add `memory_modes` (1 or 2) and the measured duplicate factor to `recompute_dates`, so that P7 models the decided
>   combination.
> - Set the cap from the signed G5-CAP; until then use 230 or leave it undecided, and fix the G.4 plan text.
> - Add the slot-hour check.
>
> ### Minor
>
> - **R3-m1 (lines 99–101).** The duplicate rule is called "the same rule as R1-TRACKP-SFT-DUP", but it is not.
>   - SFT-DUP (:1288) excludes from the **held-out (validation and test)** sets the proposals that duplicate the
>     **training** set.
>   - The draft excludes test members of groups that also occur on train **or validation**, and leaves
>     validation-side duplicates of train in place. Those inflate validation, which is where arms are selected.
>   - *Fix:* align with SFT-DUP (also exclude validation-side members of train groups from the primary validation
>     population), or state the difference and why.
> - **R3-m2 (line 273).** "What makes the procedural seal checkable": receipt hashes detect changes, not reads. An
>   access log that a same-uid process writes for itself is honour-based. *Fix:* say "auditable for changes; reads are
>   governed by STOP 11 and the access log, which are honour-based", so the author signs knowing this.
> - **R3-m3 (lines 58–62 and 213–215).** Two things in the decision text are incomplete:
>   - **The band under W B.** Ran proposals are fixed at 240 per node, so the 200–240 band acts as a STOP on
>     cross-instance duplicates at about 17 %. Also, "doubled under MEM B" ignores that twin campaigns share labels by
>     key.
>   - **G5-W B's schedule cost is not stated.** P3 needs the pilot to match the decided W, and the engine has no
>     worker-run budget yet. So B requires the code unit and a re-pilot before G.5, which delays the dates.
>   - *Fix:* state both in G5-W B, and define "audited count" as unique audited groups.
> - **R3-m4 (line 138).** Cap B covers the recommended row with a margin of 4.2 GPU-h (1.8 %). A ran share of about 0.82
>   or more, or K = 10 with a keep share of 0.3, would exceed it. *Fix:* say this in one line, so the author knows that
>   B is close to binding at share 0.8.
> - **R3-m5.** The dates in `recompute_dates` assume total ÷ 4 slots. The new per-node order adds a serial critical
>   path: campaigns → audits → operator check → campaigns → audits, with a submission and a human read between steps.
>   *Fix:* add the per-node critical path, about 1.4 days for imdb at K = 10 before queueing, plus the read gaps, as a
>   stated assumption.
>
> ### Notes
>
> - **N1.** All six decisions now list their options, and the recommendations are argued with costs on both sides.
> - **N2.** The G.4 pilot already runs at the recommended temperature and memory mode, which makes A cheaper. This is
>   disclosed (G5-TEMP B "would have to be re-run"), so the framing stays fair.
> - **N3.** The PLAN facts re-verified on `df58bcd5` are correct as cited:
>   - D15/D26 :385;
>   - R1-MAIN-PROPOSER (e) :732;
>   - R1-TRACKP-SFT-DUP :1288 (wording, see R3-m1);
>   - R1-B2-DECOUPLE :678;
>   - the rows carried over from rounds 1–2.
> - **N4.** The disjointness of seeds 5101–5112 holds against 1001–3030, 4001–4099, 7001–7010, 8001–8010, 9001+ and
>   5001–5006.
>
> ## Silent-choice audit
>
> | Item | State |
> |---|---|
> | G5-W, G5-TEMP, G5-MEM, G5-AUDIT, G5-DIV, G5-CAP | Options plus a recommendation; framed fairly (N1, N2). Small gaps: R3-m3, R3-m4. |
> | G5-SPLIT, liveness 0.25, band, 1.6 × slot cap | Marked *(proposed)* and listed in P6. |
> | **Seed block for E5 (labels and STOP)** | **Silent, and in conflict with R1-B2-DECOUPLE (R3-B1).** |
> | Measurement-path definition | Under-specified (R3-M1). |
> | Duplicate rule versus SFT-DUP | Stated, but mis-cited (R3-m1). |
>
> ## Cluster tests
>
> - **C1–C9 are complete.** C1 now covers G.4 §6 items 1–8; G.4's item 4 (JAX preallocation next to the server)
>   matters for the Breakout audits.
> - **Add to C2:** the audit runner computes E5 per seed block (R3-B1).
>
> ## Verdict
>
> - **Not accepted:** R3-B1 must be fixed before the note goes to the author for signature. E5 is applied over all K
>   audit seeds, so evaluation seeds 7006–7010 would decide training labels (u = −g, partial) and the node-level
>   divergence STOP. That conflicts with R1-B2-DECOUPLE. The fix is a few lines: apply E5 per seed block, with labels
>   and the STOP on the label seeds.
> - **R3-M1 and R3-M2** should be fixed in the same pass.
> - **Everything else from rounds 1–2 is resolved.**
>
> VERDICT: NOT ACCEPTED

## Round 4 (`b011f3fa (rev 4)`)

> Reviewed base: b011f3fa81c7cebd258cdb6aa9b6836d2c1fd591
>
> # Independent review (round 4): G.5 T1 label-run authorization draft, revision 4
>
> - **Unit:** `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (398 lines), at `b011f3fa` on
>   `mac-g1b-h200-20261120`. I diffed it against `3308d813`.
> - **Code the draft relies on:** `g4_lib.g5_node` / `recompute_dates` and `g4_dates_params.json`, changed in
>   `0a2ae3c8`, which is included at `b011f3fa`.
> - **Harness:** `b5747066`, unchanged since round 3, read with `git show`.
> - **PLAN:** main `df58bcd5`. Its PLAN.md is identical to the copy used in rounds 1–3.
> - **Projection:** I ran it read-only (`python3 -I -B` from `/tmp`).
> - **Constraints kept:** the worktree is clean, and no results of seeds 7001–7010 were read.
>
> ## Status of the round-3 findings
>
> | R3 | Status in rev 4 |
> |---|---|
> | **B1** E5 over all K seeds | **Resolved.** Lines 94–98: E5 per seed block. The label status (divergent, partial or not) uses the **label seeds only** (7001–7005, or 7001–7003). Evaluation-seed divergence goes to `y_eval` through the preregistration and "never changes a training label, the divergence STOP or a pre-release count". Using all K seeds is named as needing a row amending R1-B2-DECOUPLE and is not recommended. The G5-DIV numerator (line 126), STOP 8, the diagnostics schema and C2 agree. This is consistent with R1-B2-DECOUPLE (:678) and its 28 Oct clarification (:623). |
> | **M1** measurement path | **Resolved.** P5 (lines 332–339) now covers all of `src/autoresearch/trackg/` except the four v2-diff/pilot files; adds `nodes/`, `third_party/`, `configs/trackg/` and `node_lib/`; and adds the import closure of `noise_floor` outside `trackg/`. That closure brings in `runner` → `diff_support` → `control_plane.permissions` and `nodes.spec`. `ar_isolated.py` is inside `trackg/node_lib/`, so the COND7 change now fails the check, as the draft states. All the paths exist at `b5747066`. One gap remains: R4-m1. |
> | **M2** recompute plumbing | **Resolved.** At `0a2ae3c8`, `recompute_dates` now does all of the following: applies `mem_modes` to GPU-h and slot-h; uses the pilot's measured cross-instance duplicate factor (median over pilot nodes of 1 − (ran in groups − groups) / ran); uses cap 230 with a slot cap of 1.6 × 230 = 368 and reports both checks; makes the label span max(total / slots, the longest node); and requires a `k_check_row` that is on `origin/main` before K = 6 binds. The G.4 plan text no longer says 220. |
> | m1 validation-side duplicates | **Resolved.** Lines 104–108 now also exclude validation members of train groups. On the test side the rule is slightly stricter than SFT-DUP, which is harmless (R4-n1). |
> | m2 changes versus reads | **Resolved.** Lines 293–296. |
> | m3 W B band and re-pilot | **Resolved.** The band under B is 150–240 (line 62), and G5-W B states that it needs the engine change and a re-pilot, which moves the dates. |
> | m4 margin | **Resolved.** The figures are 197.0 against 230: a 33 h margin, 17 % of the projection. |
> | m5 serial path | **Resolved** in `recompute_dates`. The human read between waves is still not modelled (R4-n2). |
>
> **Projection.** At `b011f3fa`, all 16 cells of §2.8 are reproduced exactly by `g5_projection.py`:
> - W A / MEM A: 111.6 / 158.6 at share 0.6 and 136.0 / 197.0 at 0.8 GPU-h (K = 6 / 10), through to W B / MEM B at
>   484.9 GPU-h;
> - slot-h 174.9 to 777.6;
> - audited 144 / 192 / 240 / 288 / 384 / 480.
>
> The ratios check: 1.60 × and 1.23 × (line 59), and slot-h ≈ 1.55 × GPU-h (line 143). Cap A (150, K = 6 only)
> covers 136.0. Without parent reuse, the recommended row is 179.6 GPU-h, which is still under 230. So the cap does not
> depend on the new reuse assumption.
>
> ## Findings
>
> No blocking or major findings remain.
>
> ### Minor
>
> - **R4-m1 (P5, line 337; §9, line 376).** The identity check, as written, conflicts with the build plan.
>   - The check is `git diff --quiet <g1b pin> <g5 pin> -- src/autoresearch/trackg/ minus four files`. That fails on
>     any **new** file under `trackg/`.
>   - §9 adds an audit runner and per-job `diagnostics.json` code, but does not say where they live. If the audit
>     runner is placed in the harness's `trackg/` next to `noise_floor` and `pilot_g4`, P5 fails by construction, and
>     the signed note would need an amendment.
>   - The check fails closed, so nothing unsafe would run.
>   - *Fix:* add one sentence to P5. Either name the G.5 files that may be added (for example the audit runner module),
>     or say "files present at the G.1b pin are unchanged; files added in the G.5 pin are allowed only if no file of
>     the measurement path imports them".
> - **R4-m2 (lines 164 and 356–358; `g4_lib.g5_node` docstring).** Parent-run reuse is a new audit-protocol detail,
>   stated only where cost is discussed.
>   - The claim is that "a kept proposal's audit runs serve again when it is a later parent… on a
>     fixed-seed-deterministic host". On a deterministic host this is numerically the same as re-running the parent.
>   - The docstring adds "which G.1b checks". G.1b checks fixed-seed determinism only for the **baseline** at the
>     node's default seeds, not for edited code states at audit seeds. That is what C2 is for.
>   - On a code state that is not deterministic, reuse makes chained labels share one realization of the parent:
>     labels P → Q are correlated through m(P, s). This is valid as a paired measurement, but it differs from
>     C3_DESIGN §4's "run candidate and incumbent… on K common fresh joint seeds" as literally written.
>   - *Fix:*
>     - In G5-AUDIT A, mark reuse *(proposed)*.
>     - State the fallback: if C2 finds non-determinism on edited states, set `reuse_parent_runs: false`. Its cost is
>       179.6 GPU-h, still within cap B.
>     - Change the docstring to say that C2, not G.1b, checks this.
>
> ### Notes
>
> - **R4-n1.** The duplicate rule (lines 104–108) is described as "the same rule as R1-TRACKP-SFT-DUP". It is the same
>   on the validation side. On the test side it also excludes test members of groups seen only in validation, which
>   SFT-DUP (:1288) does not. That is stricter and harmless. "Following R1-TRACKP-SFT-DUP, and also…" would be exact.
> - **R4-n2.** The label span now honours the longest node's serial work. Two things are not modelled:
>   - the operator's read and resubmission between the steps of the order of work (§3);
>   - that under MEM B the two modes could run in parallel, so the doubled serial span is conservative.
>
>   Neither changes a decision.
> - **R4-n3.** The duplicate factor is measured on the pilot's 3 instances. With 12 instances there will be more
>   duplicates (step 1 duplicates in 11 of 12 rather than 2 of 3 instances). So the factor overstates the audited
>   share. That is conservative for cost, but it can push the extrapolated audited count above the true one when the
>   band STOP is checked after wave 1 (4 instances). The code comment says so; one sentence in STOP 9 would make it
>   visible to the author.
>
> ## Fairness and silent-choice audit
>
> | Item | State |
> |---|---|
> | G5-W, G5-TEMP, G5-MEM, G5-AUDIT, G5-DIV, G5-CAP | Each has options and a recommendation with costs on both sides. The interactions are shown in §2.8, and the couplings (DIV–AUDIT, band–W, cap–row) are stated. **Fair.** |
> | E5 seed block | Now explicit. The all-K alternative is named together with the row it would need. **Fair.** |
> | G5-SPLIT, liveness 0.25, band, 1.6 × slot cap, duplicate rule | Marked *(proposed)* and listed in P6. |
> | Parent-run reuse | Stated, but only in the cost sections. Needs *(proposed)* in the protocol text and a stated fallback (R4-m2). Not material on a deterministic host. |
>
> No other scientific choice is made silently.
>
> ## Cluster tests
>
> - **C1–C9 are complete.** C2 now covers E5 per seed block and the determinism that parent reuse relies on.
> - **Add to C2:** fixed-seed determinism on **edited** code states, which is what R4-m2 needs. The baseline alone is
>   not enough.
>
> ## Verdict
>
> - **Accepted.** All blocking and major findings from rounds 1–3 are resolved, and the decisions are framed fairly.
> - **Two minors (R4-m1, R4-m2)** should be applied before the note goes to the author for signature. Both are wording
>   or precision edits. Neither changes a recommendation or a number in the decision table.
>
> VERDICT: ACCEPTED

## Round 5 (`0cd85933 (rev 5)`)

> Reviewed base: 0cd8593375b9e768e86560ab94104fdae8062492
>
> # Independent review (round 5, confirmation): G.5 T1 label-run authorization draft, revision 5
>
> **Scope.** This round confirms only the minor fixes made after acceptance in round 4 (R4-m1, R4-m2, and the round-4
> notes the coordinator named).
>
> - Reviewed: `git diff b011f3fa 0cd85933` in `/tmp/pb/wt/g1b`. It touches:
>   - `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (+12 / −5);
>   - `sweep2/g4/g4_lib.py` (the `g5_node` docstring only);
>   - `sweep2/g4/G4_PILOT_PLAN.md` (one sentence).
> - Out of scope:
>   - the new `docs/r1/reviews/G1B_H200_REVIEW_20261121.md` in the same commit, which is the G.1b review record and a
>     separate unit;
>   - commit `5b0dfcb7`, which is under separate review.
> - I wrote nothing in the worktree, which is clean, and read no results of seeds 7001–7010.
>
> ## Fixes checked
>
> | Item | Change | Check |
> |---|---|---|
> | **R4-m2** parent-run reuse | G5-AUDIT A, new bullet (draft lines 94–98): marked *(proposed)*. It says reuse relies on fixed-seed determinism of **edited** code states on H200; that G.1b checks this only for each node's baseline and declared edits at the default seeds; that C2 checks it for audit pairs; and that the fallback is `reuse_parent_runs: false`, at 179.6 GPU-h in the recommended row, still within cap B. | **Correct.** <br>• G.1b's `default`/`default_repeat` pair runs for every configuration (baseline and declared edits) at the node defaults, as the plan's seed table and the G.1b review record state. <br>• 179.6 GPU-h is what `g5_projection.py` / `g5_node(reuse_parent_runs=False)` gives for W A / MEM A / share 0.6 / K = 10 (round 3 table), and it is below 230. <br>• Because the item is inside G5-AUDIT, it is covered by P6. <br>• The `g5_node` docstring and the G.4 plan sentence no longer claim that "G.1b checks" the determinism. They now point to C2. |
> | **R4-m1** new G.5 files | P5: the `git diff --quiet` runs over the files present at the G.1b pin. New files (*(proposed)* `trackg/audit_g5.py`, `trackg/diagnostics_g5.py`) are allowed if they are outside the import closure of `noise_floor`; the validator checks that no measurement-path module imports them. The COND7 sentence is kept. | **Correct, and the conflict with §9 is gone.** <br>• A changed or deleted file that existed at the G.1b pin still fails the check. <br>• An added file can neither enter nor alter the measurement path unless something on that path imports it, and the validator refuses that case. <br>• The audit runner itself remains under P5's code review. |
> | STOP 9 band | "200–240 under B" becomes **150–240 under B**, consistent with G5-W (line 62). | **Correct.** The draft is now internally consistent. |
> | Extrapolation note (R4-n3) | STOP 9: "The cross-instance duplicate share seen in 4 instances understates the share for 12, so the extrapolation overstates the audited count." | **Correct.** The direction matches the `recompute_dates` comment: duplicates measured on 3 instances are a lower bound for 12. |
>
> No other text changed. The decision table, the recommendations, the STOPs and the prerequisites are as accepted in
> round 4.
>
> ## Findings
>
> None.
>
> VERDICT: ACCEPTED

---

Code-Commit: 0cd8593375b9e768e86560ab94104fdae8062492
Verdict: ACCEPTED

Accepted commit: `0cd8593375b9e768e86560ab94104fdae8062492` (round 5; draft revision 5).
