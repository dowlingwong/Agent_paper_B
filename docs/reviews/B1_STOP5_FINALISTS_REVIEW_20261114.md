Reviewed base: 7bdce77650cfba4548cd3dacb0e44d020a24d478

# B1 STOP 5: finalist recomputation under x5_rule_v2 — independent review record (14 November 2026)

Branch `mac-b2-plan-20261114` from `mac-b1-20261107` @ `fcf52c09`. One round by one freshly spawned independent reviewer agent (AI-assisted, Claude), who recomputed the finalists from `b1_manifests.json` with their own code before running the target script, and checked the rule hash (`53018aa7…16ad`), the registry hash and all 2,908 deltas. Round 1 (`7bdce776`): **accepted**; finalists `[gemma4_31b]`, identical to `complete_batch_verifier.json`. Notes, not blocking: report §4 should say the B2 config and note *must* bind the verifier file (they are not filled yet); the second-proposer criteria are proposed consequences in PLAN, not settled; gemma4_31b's μ̂ (−0.000891) is below the scripted anchor's (−0.000587) and its B1 thinking-on D28 failed; the script does not re-check the manifest set against the verifier's eligible list (checked by hand).

Accepted commit (last round): 7bdce77650cfba4548cd3dacb0e44d020a24d478

The round texts are reproduced unchanged below.

---

# Independent review: B1 `_d` STOP 5 finalist recomputation (round 1)

Reviewed commit: 7bdce77650cfba4548cd3dacb0e44d020a24d478
(branch `mac-b2-plan-20261114`, base `fcf52c09a4848c2218e3b63b8a8e0acf0dd02e05`; the three target files are unchanged
between 7bdce776 and the worktree HEAD `a0018635`, and the evidence directory is unchanged since `fcf52c09`.)

Verdict: accepted

Reviewer: independent AI reviewer (Claude), did not write the work. No worktree was modified. Scratch in
`/tmp/rev_stop5`, removed at the end.

## What I did

1. **My own recomputation first** (`/tmp/rev_stop5/recompute.py`, written before reading or running the target
   script; it does not import `r1.exam`):
   - `sha256sum -c SHA256SUMS` in `docs/r1/reports/b1_d_20261113_evidence/`: 10/10 OK. `b1_manifests.json` =
     `dc5cd04d…`, `complete_batch_verifier.json` = `07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc`.
   - Rule `/tmp/pb/wt/run7912/r1/exam/rules/x5_rule_v2.yaml` (HEAD `7912b7ff`): sha256
     `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`, equal to the frozen value, to the `.sha256`
     sidecar, and to `rule_sha256` in all 18 manifests (`rule_version` x5_rule/v2 in all).
   - Registry `r1/exam/registry.yaml` at `7912b7ff`: sha256 `2c6ef6b3…e723` = every manifest's `registry_sha256`.
     Family, role and `registry_order` checked against the runner's order (software anchors, LLM anchors,
     candidates, sensitivities, as in `_b1_summary_rows`): 18/18 match. Each candidate manifest's `thinking_policy`
     equals the registry's.
   - 2,908 audited proposals: seeds 9101–9104, 4+4 metrics; |mean(cand) − mean(inc) − delta_audit| ≤ 1.1e-16.
   - μ̂ = mean thinking-off `delta_audit` (the cluster bootstrap's point estimate is the flat mean).
   - Eligibility: role candidate, `stage_a_pass`, `d28_pass`, thinking-off capable (mode off and off_switch, or
     non-switchable), always_on excluded. All 15 candidates with manifests are thinking-off capable; no always_on
     model (muse, lfm, gpt_oss, rico03) has a manifest; `nemotron35_30b_a3b` (Stage A offload fail) and
     `olmo31_32b_think` have none. The manifest set equals the verifier's `batch_verification.eligible_candidates`.
   - **Only `gemma4_31b` has `d28_pass = true` among candidates** (scripted anchor also true, not rankable).
   - Top 4 + absent-family extra, max 5, ties by registry order → **finalists `["gemma4_31b"]`**.
   - Descriptive (not the rule) without D28: `glm47_flash, gemma4_31b, gemma4_12b, qwen36_27b, laguna_xs21`
     (top 4 families glm/gemma/qwen; best absent family laguna).
2. **Comparison with the verifier**: every μ̂ in `complete_batch_verifier.json` equals mine exactly (max diff 0);
   verifier finalists `["gemma4_31b"]`. Running the run-HEAD `analyze.choose_finalists` on the verifier rows with the
   v2 rule also gives `["gemma4_31b"]`.
3. **Target script**: `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin /tmp/trackg_venv/bin/python -I
   r1/scripts/b1_stop5_finalists.py --evidence … --rule … --registry …` → rc 0, output **byte-identical** to the
   committed `stop5_finalists.json`. `finalists_equal: true`, `max_abs_mu_hat_diff: 0.0`,
   `max_abs_interval_diff: 0.0`, 2,908 proposals checked, D28-ignored variant as above. Per row, n_off, d28_pass,
   μ̂ and capability agree with mine (only difference: the script records `thinking_off_capable: null` for the
   `qwen25_coder_7b` anchor where I computed true; irrelevant, anchors are never eligible).
4. **Report claims checked against code/evidence**:
   - 18 manifests = 3 anchors (random_valid, scripted, qwen25_coder_7b) + 15 candidates: correct.
   - Table values and n: match.
   - Analyzer rc 0: `docs/r1/reports/B1_D_RUN_20261113.md` §3 records it.
   - D28 limit: `d28_pass` is cross-checked against primary-root `d28` records in `verify_batch`
     (`r1/exam/b1_batch.py` l. 229–230 at `7912b7ff`); the root ledgers are not in the published evidence, so the
     limit is stated correctly and the finalist set does rest on that host-side check.
   - "Ignore D28" variant: clearly headed "Descriptive only, not the rule" in the report and
     `descriptive_not_the_rule` in the JSON.
   - μ̂ < 0 for gemma4_31b and no μ̂ threshold in x5_rule/v2: correct.
   - One finalist → B2 runs only the finalists (`exam_runner._evidence_unreviewed`: `final=set(screen['finalists'])`),
     so the rule pick is gemma4_31b whatever its B2 Y: correct.
   - Thinking-on rerun: in the v2 b2 branch, finalists with rank < 3 that are switchable and not grammar-disabled get
     `modes=['off','on']`, and in b2 both modes run over `cfg['nodes']` × the same seeds → the B2 roots double.
     gemma4_31b is switchable with off_switch; its B1 manifest has 45 thinking-on audits and
     `thinking_sensitivity_omitted_reason: null`, and B1 v2 would have STOPped had any switchable eligible model been
     grammar-disabled. Correct.
   - `b1_analysis` = `complete_batch_verifier.json`, sha256 `07cb62de…`, rule sha and finalists as stated; its
     gemma4_31b row has `b2_thinking_mode: off`, which the v2 B2 branch requires. Correct.
   - Base branch claim: `fcf52c09` is on `macorigin/mac-b1-20261107`. Correct.

## BLOCKING findings

None.

## NON-BLOCKING findings

1. **§4 `b1_analysis` binding is worded as a present fact.** "The B2 config's `b1_analysis` / `b1_analysis_sha256`
   and the B2 authorization note bind this file." At this commit `r1/scripts/configs/exam_b2_v2.json` l. 59/74 still
   hold `TODO_VERIFY_ON_HOST`, and no B2 authorization note exists. Suggest "must bind (currently
   `TODO_VERIFY_ON_HOST`)" so it is not read as already done.
2. **Second-proposer criteria are cited as settled.** The report describes R1-BX-D6-EXAM-RUNNER-UP as "a different
   family ranked by B2 Y". The author's decision cell (PLAN l. 979) is "是我的决定" confirming "用 exam 第二名"; the
   different-family / B2-Y ranking is the recorder's *(proposed)* consequence (PLAN l. 984). The conclusion holds under
   either reading (B2 has a single finalist, and only one candidate is eligible in B1), but the report should say the
   criteria are proposed and that the author needs to decide what replaces the runner-up.
3. **Context the author may want next to the finalist (descriptive, does not change the rule outcome):**
   gemma4_31b's μ̂ (−0.000891, cluster interval [−0.00186, −0.000052]) is below the scripted anchor's (−0.000587),
   and its descriptive B1 thinking-on D28 failed (`thinking_on_d28 = {pass: false, roots: 4}`). The second point bears
   on whether the doubled-cost B2 thinking-on rerun is worth it. Neither is a rule input. Adding them, marked
   descriptive, would make the B2 consequences more complete.
4. **Script robustness (minor).** The script does not check that its manifest set equals the verifier's
   `batch_verification.eligible_candidates`, and it does not explicitly refuse an always_on manifest. Its eligibility
   would still exclude always_on models, and both checks pass on this evidence (I verified them), so the result is
   unaffected. It also trusts the unpinned `SHA256SUMS` file for evidence digests (the report states the expected
   digests, so a reader can cross-check).

## Overclaims

None found beyond findings 1 and 2. "Independent of `r1.exam.analyze`" is accurate (no import; the logic is a
reimplementation). The equality "to 0.0" claims are reproduced exactly.

Accepted commit: 7bdce77650cfba4548cd3dacb0e44d020a24d478
