Reviewed base: 0a1e1088c55f1ddcac2d6611024dbfb09940775e

# Track S STOP 4 end — PLAN row draft, appendix draft, resources inventory — independent review record (15 November 2026)

Branch `mac-tracks-stop4-end-20261115`, from `mac-tracks-s05-summary-both-20261115` @ `1417807b`. Three drafts written after the author's STOP 4 decision of 15 Nov 2026 ((c-iii): Track S ends before EVIDENCE, A2-U unchanged, no re-run, TASL-7 no longer allocated to Track S): `proposals/PLAN_ROW_R1-TRACKS-STOP4-END_DRAFT_20261115.md`, `reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md`, `reports/TRACKS_RESOURCES_AND_SCENES_20261115.md`. Drafts only; nothing on the hosts touched; no PLAN commit. Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`af63833f`): changes requested (2 MAJOR: the appendix's Prop. 8′ reading slid from the Bayes V\*_n to A2-U's index; a false "every tree has SHA256SUMS" statement in the inventory; 14 MINOR).
- Round 2 (`7336a241`): accepted, with 6 non-blocking MINORs.
- Round 3 (`0a1e1088`, the 6 MINORs fixed): **accepted**, no findings.

Accepted commit (round 3, last): 0a1e1088c55f1ddcac2d6611024dbfb09940775e

The round texts are reproduced unchanged below.

---

# Independent review — Track S STOP 4 end drafts (round 1)

Reviewed base: `af63833f` (branch `mac-tracks-stop4-end-20261115`, one commit on `1417807b`; worktree
`/tmp/pb/wt/stop4end`, clean after the review). Files: the PLAN row draft
(`docs/r1/proposals/PLAN_ROW_R1-TRACKS-STOP4-END_DRAFT_20261115.md`), the appendix draft
(`docs/r1/reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md`) and the inventory
(`docs/r1/reports/TRACKS_RESOURCES_AND_SCENES_20261115.md`). Read-only. My only scratch is
`/tmp/pb/rev_stop4end/recompute.py`, which recomputes the numbers from `roots.jsonl`, `s05_calibration.jsonl`,
`s05b_truncated.jsonl` and every `manifest.json` under `results/r1/tracks/`.

VERDICT: REVISE

There are 2 MAJOR findings and 14 MINOR, and no BLOCKING finding. The PLAN row follows the author's decision
and is in the right format. Every pilot number in the three files recomputes. What needs work: one passage of
the appendix's Prop. 8′ reading, its "no claim about A2-U" boundary, and one false integrity statement in the
inventory.

---

## Findings

### 1. MAJOR — Appendix §A.x.2–A.x.4: the Prop. 8′ reading slides from the Bayes V\*_n to A2-U's index, and the "no claim about A2-U" boundary contradicts §A.x.3

Prop. 8′ is a statement about the Bayes quantity V\*_n = E[m_n⁺ | O_n] (t4rev §1–§2). The appendix says so in
§A.x.4 ("A2-U's V\* values are therefore not validated estimates of the Bayes quantity V\*_n"). Four sentences go
against that boundary:

- **(a) §A.x.4, last bullet:** "that is the pattern Proposition 8′ predicts whenever the index used for E1
  exceeds g at every history." Prop. 8′ predicts nothing about an arbitrary or uncalibrated index. A threshold
  rule executes everything whenever its index is above its threshold, and that is plain arithmetic, not
  Prop. 8′. As written, the sentence lends A2-U's index the proposition's authority, which is exactly the
  conflation the section disclaims.
  **Fix:** "With A2-U's index in place of V\*_n, the pilot policies were in the configuration that Proposition 8′
  describes for a low price: every non-duplicate proposal executed, and only the E2 keep left as a decision.
  Whether the price is low for the true V\*_n is not established."
- **(b) §A.x.2, paragraph after the three bullets:** "In this regime a forecaster's E1 index cannot change what
  is executed, however it is built, as long as it stays above g. A dynamic threshold that moves within that range
  cannot change it either." The first sentence is a tautology ("as long as it stays above g"), and "that range" is
  undefined. It also misses what Prop. 8′ actually gives in this regime: no E1 rule can beat executing every
  non-duplicate at that step, and a rule that skips one gives up V\*_n − g > 0 in expectation.
  **Fix:** "In this regime no E1 rule, whether a forecaster or a dynamic threshold, can improve on executing
  every non-duplicate proposal at that step; skipping one gives up V\*_n − g > 0. Any one-step value a dynamic
  policy adds must come from E2, or from budget or information effects that Prop. 8′ does not cover."
- **(c) §A.x.3, "Interpretation":** the first two bullets are unqualified ("E1 was trivial", "E2 was not
  trivial"). Read alone, they state facts about the nodes. Both rest on A2-U's index and on A2-U's m̂.
  **Fix:** begin the block with "Under A2-U's index and its m̂:" or similar.
- **(d) §A.x.4, "So we do not claim … anything about A2-U as a forecaster or controller beyond the gate failure
  itself".** §A.x.3 makes such statements: its table reports A2-U's V\*, and "Why A2-U's index was nearly
  constant" gives a structural account of A2-U's prior construction (τ0² = max(τ_A2² − τ_w², floor²), with τ_A2
  bounded by A2's binned labels). Those are descriptive and correct, but they go beyond "the gate failure itself".
  **Fix:** "… beyond the gate failure and the descriptive account of its pilot behaviour in §A.x.3. In
  particular, no claim about its accuracy, about the true V\*_n, or about how it would behave on other nodes or
  priors."

These four together are the honesty boundary the author asked for. Each fix is one sentence.

### 2. MAJOR — Inventory §3 "Every phase tree carries `SHA256SUMS`" is false, and §2.3 item 1 leans on it

The phase trees under `results/r1/tracks/` were listed one by one. 13 of 21 have no `SHA256SUMS`:
- `digits_mlp/{s01, s01_diag, s01_diag_f1, s01_diag_f2, s11, smoke}`;
- `tabular_mlp/{s01, s01_diag, s01_diag_f1, s01_diag_f2, s11, smoke}`;
- `openml_breast_w/s11`.

Only these have one: `digits_mlp/{s01_rerun20261109, s04, s04_rerun20261111, s05_t7_20261113}` (plus the
`_to_delete/` copy), and `tabular_mlp/{s01_t7_20261114, s04_t7_20261114, s05_t7_20261114}`.

§2.3 item 1 says "The Mac copies are sealed by their `SHA256SUMS`". One of the TASL-7 trees the watcher touches
(it has a `manifest.json`), `out/…/smoke`, has none on the Mac. Its hashes exist only in the table of the tabular
S0.4 report §1.

This document exists to support a later clean-up decision. A false integrity statement could lead someone to
treat host copies as redundant.

**Fix:** state which trees carry `SHA256SUMS`. For the others, name the substitute where one exists (the tabular
S0.4 report §1 hash table for the old TASL-7 tabular scenes) or say "none". Correct §2.3 item 1 the same way.

### 3. MINOR — Appendix §A.x.2: the definition of a "low" price contradicts its own exception

The draft defines "Low when g lies below V\*_n at every history" and then says the rule "executes every proposal
except those whose V\*_n is 0". With g > 0, no history with V\*_n = 0 satisfies the definition.
**Fix:** "at every history whose proposal is not a rule-detectable no-op or duplicate".

Corollary 8a is stated "on a bit-exact node". Add that qualifier, or say the nodes meet it.

R2 makes the run's opportunity cost depend on "the remaining budget and the incumbent", not only on "the
remaining runs". Small, but quote it fully.

### 4. MINOR — "Range of V\* across all proposals" (appendix table, row 2; PLAN row in both languages, "range over all proposals" / "全部提议间的极差")

`policy_diag.py` takes the range over the eligible E1 decisions of a2u: 298 on digits and 330 on tabular. Trial 1,
duplicates and invalid proposals have no V\*. The values recompute (0.0355 → 0.036 σ_node; 0.0183 → 0.018).
**Fix:** "over all eligible (non-duplicate) E1 decisions".

### 5. MINOR — Appendix §A.x.3: "every proposal that was not a duplicate was executed, by both policies"

Per policy, 53 (digits) and 51 (tabular) proposals were recorded as `E2:failed_invalid` with no E1 decision. Their
counts add up: 318 + 429 + 53 = 800 = 20 × 40, and 350 + 399 + 51 = 800. Trial 1 is executed without being
eligible.
**Fix:** "every valid non-duplicate proposal". Optionally add the `failed_invalid` counts to the
"E2 keep / discard" row.

### 6. MINOR — Appendix §A.x.4, first bullet understates the calibration failure

The bullet names only the first proposals (stratum 0) as too narrow. Stratum 1–2 is also under-covered on both
nodes (0.674 and 0.653). Add it.

### 7. MINOR — Appendix §A.x.5 disclosures are incomplete

- **Digits S0.5 ran in two sessions.** It paused on 13 Nov at 13:03Z after 22 roots, on a STOP whose origin is
  not evidenced. After one failed resume attempt (rc=1, before any server started), it resumed on 14 Nov at
  10:43Z with a byte-identical command (`TRACKS_S05_T7_RESULT_20261114.md` §1–§2; STATUS 14 Nov). Neither the
  appendix nor the per-node line mentions this. Add one sentence.
- **"The alternatives were to revise A2-U and repeat the pilot, or to narrow the comparison to E2"** leaves out
  (b), changing the price or budget, and (c-ii), dropping a node. Write "Among the alternatives were …", or list
  all of them. For a post-hoc stop it is also fair to disclose that the summary had recommended (a) with
  pre-declared fallbacks.
- **"On the author's instruction"** (the S0.1 order): STATUS records this instruction as relayed by the Lead,
  with no PLAN row. That is acceptable, but a parenthesis would make the provenance exact.

### 8. MINOR — Appendix §A.x and §A.x.2 wording about what Track S compared

- **"Track S was a pre-registered screen."** The formal pre-declaration (S0.8) was never made; this very row says
  it does not take place. What was fixed in advance were the design and settings (R1-TRACKS-ADOPT/-S02) and the
  outcome framing (R1-TRACKS-FRAMING).
  **Suggested:** "a screen whose design, settings and outcome framing were fixed in advance …; its formal
  pre-declaration (S0.8) was to follow the pilot and was never made."
- **"a tuned dynamic execution threshold".** The runbook defines π\* as a "state-dependent (dynamic) threshold
  policy" (tsrb.md, orientation). Its S0.7 members include keep±×0.5 on E2 and the budget/info members. Drop
  "execution".
- **"the worker budget bound in 94 % … of the campaigns".** The denominator is the 50 S0.5b roots, which include
  the 10 rep-1 roots. Say so.

### 9. MINOR — Inventory: §3 and §2.1 contradict each other on the TASL-7 bare repo

§3 lists `trackS-ops-20261030` @ `fab88fce` as present on `tasl7`. §2.1 (and STATUS 15 Nov) say the TASL-7 bare
repo was fast-forwarded to `110b01a8`. That commit is an ancestor of `fab88fce`, two commits behind
(`9b2fba9a`, `fab88fce`), and the Mac agent has no server access to push later.
**Fix:** "tasl7: `110b01a8` (2 behind; per STATUS)", unless a later push is recorded.

The branch locations in §3 come from the Mac checkout, which I cannot see. The container's `gh/` refs were last
fetched on 13 Nov, so I could not verify "origin" either. Treat them as unverified by this review.

### 10. MINOR — Inventory §1: the hours tally does not follow its own stated method

§1 says S0.1 runs "whose start and end are recorded in their reports" are included. Yet the TASL-2 `digits_mlp`
S0.1 re-run sits under "Not tallied" although `TRACKS_S01_RERUN_20261109.md` records it: servers start at
2026-11-08T23:59:57Z and the launch returns at 2026-11-09T00:34:30Z, about 0.58 h. It also started on 8 Nov, not
9 Nov.
**Fix:** tally it, which makes TASL-2 about 1.7 h, or change the method statement. In either case, call the
totals lower bounds.

Separately, "Track S ran from 29 Oct (adoption and host rows)": the host rows are dated 29 Oct, but adoption is
30 Oct (R1-TRACKS-ADOPT).

### 11. MINOR — Inventory: scenes missing from the lists

- TASL-2 `out/digits_mlp/s11`: the 30 Oct S1.1 output, cited at `$R/out/digits_mlp/s11/digits.json` in
  `TRACKS_PHASE3_20261109.md`.
- Mac: `.claude-worktrees/_trks_ops_s11/`, the uncommitted scratch checkout where `openml_breast_w` S1.1 ran
  (`TRACKS_PHASE1_20261030.md`, provenance paragraph). Its current existence is unknown, but it belongs on a
  list made "from records".

### 12. MINOR — Inventory §2.3 item 2 (TASL-2 live items) points at the wrong live item

The runbook gives every LLM session an 8 h deadline (`--deadline 28800`), so the S0.5 collector started on 12 Nov
at 19:55:59Z cannot still be running unless the host froze. What could survive a network-only outage is the
`trks_llm` servers holding TASL-2's GPU and its `~/r1_locks/gpu0.lock` lease. That matters for whether TASL-2 can
be released (row consequence 4).
**Fix:** "The collector is bounded by its 8 h deadline. If the outage was network-only, the Track S servers and
the TASL-2 lease may still be held; census read-only on return."

### 13. MINOR — Who decides about the watcher: inventory and row disagree; the row's consequences omit it

- Inventory §2.3 item 1 says stopping the watcher is "for the author or the operator to decide". Once the row is
  committed, it leaves Track S "processes … as they are, not moved, changed or deleted". Stopping `trks_watch`
  then needs an author decision, not an operator one. Make the inventory say "the author".
- Add a consequence to the row draft's list: as written, the row keeps `trks_watch` running on TASL-7. It will
  touch `STOP` in every finished Track S directory that has a `manifest.json` when B2 creates
  `trackx_evidence.active`. B2 PLAN step 5 already inventories those touches.
- Tense in the inventory: "gain new `STOP` files" should be "will gain … when B2 creates its marker". The records
  do not show whether B2 has started.

### 14. MINOR — Row draft, consequence 4 contradicts itself

It opens with "Track S's allocations of TASL-2 (zhixu portal) and TASL-7 end" and then says "Whether TASL-2 is
also released is the author's call".
**Fix:** "Track S's TASL-7 allocation ends (the row says so, as instructed). TASL-2 is not named …"

### 15. MINOR — Row text: scope of the data and of the phases

- **"The S0.1–S0.5b data stay ENGINEERING_ONLY"** leaves out the Phase 0 smoke runs and S1.1, which are also
  Track S ENGINEERING_ONLY data. Write "All Track S data (Phases 0–4)", or similar, in both language blocks.
- **The list of phases that "do not take place"** (S0.6, S0.7, S0.8, S0.9, S3, S4) does not mention Phase 9 or
  the offline S2/S5 steps. "Track S ends" already covers them, so this is fine. Writing "no later phase,
  including …" would remove the ambiguity.

### 16. MINOR — Row draft "Consequences": R1-TRACKS-ADOPT is listed but not discussed

R1-TRACKS-ADOPT ("Track S is adopted and will be run"; evidence runs gated by S0.8/S0.9) is listed among the
affected rows but has no consequence entry. Add one line: the new row supersedes ADOPT's "will be run". The
15 Nov format uses a bare ID, so the amendment cannot go in the ID cell.

---

## Verified as correct

**Calibration.** Recomputed from `s05_calibration.jsonl`, matching the row and the appendix table:
- digits 35/65 = 0.538, 60/89 = 0.674, 136/144 = 0.944, overall 0.775 (n = 298);
- tabular 21/57 = 0.368, 62/95 = 0.653, 148/178 = 0.831, overall 0.700 (n = 330);
- the gate wording (design S0.5 (iii); [0.70, 0.90]; strata with ≥ 20 predictions);
- stratum 0 as a STOP that λ₂ cannot change (summary §3; STATUS 15 Nov).

**V\* and policy coincidence.** From `roots.jsonl`:
- V\* − g ranges 2.576–2.612 σ_node and 4.038–4.056 σ_node (stated as 2.58–2.61 and 4.04–4.06);
- V\* range 0.036 and 0.018 σ_node (see finding 4 for its denominator);
- 0 decisions below or within ±0.5 σ_node of g or of the static threshold;
- E1 skips 429 and 399, all `rule_duplicate`;
- identical action sequences in 20/20 instances on both nodes, and 20/20 at each W ∈ {8, 10, 12, 20};
- E2 keep/discard 148/170 and 158/192;
- E2 m̂ p05/p95 −0.108/0.114 and −0.055/0.034; within the band: 46 and 38;
- runs used at most 27 of 40; LLM cap reached in every campaign;
- W = 12 binding share 0.94 and 1.00 (50 roots).

**σ_D and the prior.**
- `sigma_D_ucl_s05b` = 0 and `between_policy_sd_at_cap` = 0 on both nodes (`s05_summary_20261115.json`).
- σ_node 0.0066 and 0.0019; g = 0.1 σ_node; static threshold 0.3 σ_node (0.00198, 0.00057).
- τ0 = 0.15 σ_node on both nodes.
- τ_A2 = 2.9 and 3.4 σ_node; τ_w = 7.5 and 13 σ_node.
- `fit_prior` rule τ0² = max(τ_A2² − τ_w², floor²) (`r1/tracks/a2u.py:207,234` at the pin).
- The V\* approximation at μ ≈ 0.

**Pilot set-up.** 20 instances per node; 10 rep-1 instances; W = 40; LLM cap 40; 298/330 audits equal to the
eligible E1 decisions; both pilots on TASL-7; k = 2 by measurement on both nodes; tabular S0.1 run between S0.4
and S0.5 (timestamps); all 50 roots per node `ok`, no failed or exhausted units.

**Hours.** From the manifests: 0.10, 0.44, 2.46, 2.50, 0.03, 0.36 and 0.74 h, and the `_to_delete/` copy is the
same session as `s04_rerun20261111`. From the reports: S0.1 sessions of 0.57 and 0.61 h. Totals 6.68 and 1.13 h;
S0.5b about 15 s.

**Host facts against STATUS.**
- TASL-7: only `trks_watch`; lease free; GPU 243 MiB; 526 G free; `trks-status` updated to `8237fd02` (sha
  `70fbe8bd…`); bare repo fast-forwarded to `110b01a8`; directory layout; three directories not copied back
  (correct); the digits `_to_delete/STOP.retired…`.
- TASL-2: outage on 12 Nov; S0.5 attempt at 19:55:59Z, last seen 20:02Z with 4 roots; preserved, never resumed;
  `trks_watch` after the S0.4 re-run; 187 G free; scratch pytest env path; push deferred.
- The watcher behaviour as described (runbook §11.4: STOP touched in every directory under `out/` that has a
  `manifest.json`; `trackx_evidence.active` is in its marker list).
- B2 PLAN step 5 and `prechecks.sh` inventory the watcher and the STOP state.
- `gpu0.lock` described as a shared cooperative lock.

**PLAN row.**
- It matches the author's decision: (c-iii); before EVIDENCE; no A2-U change; no re-run; TASL-7 no longer
  allocated; appendix with an honest calibration statement and no A2-U claim; scenes untouched. Inferences (D10,
  D14, FRAMING, PICK-REPEAT-DEFER, TASL-2, the DI-FIX proof check) are kept in the "consequences" list, not in the
  row.
- Format matches the 15 Nov B2 rows: `### 15 November 2026 — … (author)`, a blank line, a two-column table, one
  line per row, bare ID, exactly 3 `|` per line, no `<br>`.
- Paste position after `R1-EXAM-B2-INVALID-TRIALS` and before `## 11.`
- `8709dce7` is the latest commit touching PLAN; `2906b676` is the last on `trackS-ops`.
- The summary was accepted at `74808c0a`.
- The Chinese and English blocks match sentence for sentence.
- The author's chat is not quoted.
- No proof check is recorded in PLAN, so R1-T4-DI-FIX is correctly flagged in the row consequences and in the
  appendix conditions.
- RUNBOOK §1 is quoted correctly ("never quoted as results"; "All written documents in English"), and the
  Chinese-row precedent is noted.

**Prop. 8′ content (apart from findings 1 and 3).**
- E2 rule and V\*_n = E[m_n⁺ | O_n].
- E1: execute iff V\*_n > g; gain (g − V\*_n)⁺ relative to always executing.
- Valid without an independence condition.
- One step only; the campaign level needs 10(a′).
- Hard budgets excluded (R2; R1-T4-DI-FIX (4)).
- Cor. 8a: duplicates and no-ops are skipped by the rule layer.

**Labels.** All three files carry "AI-assisted (Claude, Mac agent)". The appendix also carries "Not an author
decision". The row is marked "governs nothing until the author commits it". The inventory states that it comes
from records, not a census, and that it takes no action.

---

# Independent review — Track S STOP 4 end drafts (round 2)

Reviewed base: `7336a241` (one commit on `af63833f`; I read `git diff af63833f 7336a241` and then all three files
in full). The worktree `/tmp/pb/wt/stop4end` was clean at the start and at the end. The review was read-only.

VERDICT: ACCEPT

All 16 round-1 findings are fixed, both MAJOR findings included. I re-checked each fix and its new facts against
the sources. Six new MINOR points remain. They are wording or consistency issues, none changes a number or a
decision, and none blocks acceptance. Fixing them before the author commits the row would still be worthwhile.

---

## Round-1 findings: re-check

| # | Status | What I checked |
|---|---|---|
| 1 MAJOR (a)–(d) | fixed | §A.x.3's lead-in now says "A2-U's index (not the Bayes V\*_n)". The Interpretation heading is qualified. The §A.x.2 paragraph now states the Prop. 8′ consequence (skipping gives up V\*_n − g). The §A.x.4 boundary now allows the descriptive account and excludes accuracy, the true V\*_n and generalisation. The last bullet no longer says Prop. 8′ "predicts" anything about an arbitrary index. No remaining sentence draws a conclusion about the true V\*_n. |
| 2 MAJOR | fixed | The seven trees with `SHA256SUMS` and the 13 without match the directory listing. The substitute table in the tabular S0.4 report §1 covers `s01`, `s01_diag`, `s01_diag_f1/f2`, `s11`, the INVALID 31 Oct re-run and `out/smoke` (I read it). "Not provably redundant" is added. In §2.3.1, the three 13–15 Nov TASL-7 trees with a `manifest.json` carry `SHA256SUMS`; `out/smoke` has none. Both statements are correct. |
| 3 | fixed (see new point R2-1) | The definition now excludes no-ops and duplicates. The bit-exact qualifier and the R2 wording are both correct. |
| 4 | fixed | "Eligible (non-duplicate) E1 decisions" appears in the appendix and in both row blocks; the Chinese text "在全部合格的非重复 E1 决定上的极差" matches. |
| 5 | fixed | The 53 and 51 invalid proposals are counted. Every root of both nodes has E1 decisions plus `failed_invalid` = 40 = `llm_calls`, which I recomputed, so "each campaign's 40 calls are accounted for" holds. |
| 6 | fixed | Stratum 1–2 is added. |
| 7 | fixed | The pause disclosure matches `TRACKS_S05_T7_RESULT_20261114.md` and STATUS 14 Nov: 22 roots, STOP origin not evidenced, failed resume with rc=1 before any server started, byte-identical command. The options and the recommendation (a) with declared fallbacks match summary §7. The provenance "relayed … no PLAN row" matches STATUS. |
| 8 | fixed | The "fixed in advance / S0.8 never made" wording, "state-dependent (dynamic) threshold policy, with members acting on E1 and on the E2 keep" (as in tsrb.md), and the 50-root denominator (S0.5b has 50 rows per W) are all correct. |
| 9 | fixed (see R2-3) | The Mac's `tasl7` ref at `fab88fce` is plausible: the tabular review, round 2, saw `git ls-remote tasl7` = `9b2fba9a`, already past the STATUS value `110b01a8`. `tasl2` at `78a1b65e` is corroborated by both per-node reviews. `9bb64ba6`, `13badb0d` and `c8b13b5d` match the refs in the container copy. |
| 10 | fixed | The 0.58 h row is in the table (23:59:57Z → 00:34:30Z = 0.576 h, as `TRACKS_S01_RERUN_20261109.md` records). TASL-2 is 0.03 + 0.58 + 0.36 + 0.74 = 1.71 h. Both totals are now called lower bounds. "Adopted 30 Oct" is correct. |
| 11 | fixed | `out/digits_mlp/s11` (`TRACKS_PHASE3_20261109.md`) and `_trks_ops_s11` (`TRACKS_PHASE1_20261030.md`) are now listed. I cannot see whether `_trks_ops_s11` still exists. |
| 12 | fixed | `r1/tracks/ops/launch/tasl2_s05_20261112.sh` carries `--deadline 28800`, which confirms it for the actual TASL-2 attempt. The servers, watcher and lease are now named. |
| 13 | fixed | "Only the author" is stated, the tense is now future, and consequence 7 is accurate (runbook §11.4; B2 PLAN step 5). |
| 14 | fixed | Consequence 4 no longer contradicts itself, and it now points to inventory §2.3. |
| 15 | fixed | Both blocks say "All Track S data (Phases 0–4: …)" and "No later phase …, including …". Each row line still has exactly three `\|`. |
| 16 | fixed | Consequence 8 is added. |

The Chinese and English blocks still say the same thing, sentence for sentence. The format still matches the
15 Nov B2 rows. All decision content stays in the row, and everything inferred stays in the consequences list.

---

## New findings (all MINOR)

### R2-1. MINOR — Appendix §A.x.2, second bullet after the "low" definition: "the screening gain (g − V\*_n)⁺ is 0 throughout"

Since round 1, the definition excludes rule-detectable no-ops and duplicates. At those histories V\*_n = 0, so
(g − V\*_n)⁺ = g, and the rule layer collects it by skipping (Cor. 8a). "Throughout" is therefore no longer true.
**Fix:** "is 0 at every such history (at no-ops and duplicates the rule layer's skip earns g)".

### R2-2. MINOR — Appendix §A.x.2: "On a bit-exact node, as both pilot nodes are" has no source

The claim is supported. T4 §1 says CPU nodes are bit-exact at fixed seeds (STATUS 12 Oct), and PLAN §3 says
restore is bit-exact on the CPU nodes (STATUS, L7). Cite one of them, because Cor. 8a's use here depends on it.

### R2-3. MINOR — Inventory §2.1 still says the bare repo was "fast-forwarded to `110b01a8` on 15 Nov", with no qualifier

§3 now reports the Mac's `tasl7` ref at `fab88fce`, and the tabular review, round 2, saw `9b2fba9a`.
**Fix:** add "(STATUS record; later pushes reached at least `9b2fba9a`, and the Mac's tracking ref is `fab88fce`,
§3)". That keeps the two sections consistent.

### R2-4. MINOR — Inventory §2.2 "Bare repo. Behind; the push of the 14–15 Nov commits was deferred"

The tracking ref is `78a1b65e` (12 Nov, 11:23 CET), which is 54 commits behind `fab88fce`. The gap therefore
starts on 12 Nov, not 14 Nov. The STATUS deferral note simply begins on 14 Nov.
**Fix:** "Behind: the Mac's tracking ref is `78a1b65e` (12 Nov, §3); pushes deferred while the host is down."

### R2-5. MINOR — Inventory §2.3 item 2: "bounded by its 8 h deadline … cannot still be running"

In runbook §0, `--deadline 28800` stops the collector from scheduling new units after 8 h; it then finishes its
current unit. The conclusion holds, but "stops scheduling new units after 8 h, so it cannot still be running
days later …" is the exact wording.

### R2-6. MINOR — Appendix §A.x.4, first sentence: "The pre-declared gate"

§A.x now says that the formal pre-declaration (S0.8) was never made. Calling the gate "pre-declared" invites a
false reading of a contradiction.
**Suggested:** "The gate fixed in the design before the pilot (design S0.5 (iii))".

---

## Verified as correct in this round (beyond the table)

- **Numbers.** Every number carried over from round 1 is unchanged and still recomputes. The new numbers are
  correct: 53 / 51 invalid proposals, 40 calls per campaign, 0.58 h and 1.7 h, 50 roots per W, and the tips
  `78a1b65e`, `9bb64ba6`, `13badb0d` and `c8b13b5d`.
- **Labels and status.** The appendix keeps "AI-assisted" and "Not an author decision". Its RUNBOOK §1 and
  R1-T4-DI-FIX conditions are unchanged. The row is still a draft that "governs nothing until the author commits
  it". The inventory still takes no action and says it comes from records.

---

# Independent review — Track S STOP 4 end drafts (round 3)

Reviewed base: `0a1e1088` (one commit on `7336a241`; I read `git diff 7336a241 0a1e1088`). The commit changes
7 lines in the appendix and the inventory. The PLAN row draft is unchanged. The worktree was clean, and the
review was read-only.

VERDICT: ACCEPT

All six round-2 MINORs are fixed and the commit introduces no new error. No BLOCKING, MAJOR or MINOR finding
remains.

| # | Status | Checked against |
|---|---|---|
| R2-1 | fixed | The gain is now "0 at every such history (at a no-op or duplicate it is g, earned by the rule's skip)". This matches Prop. 8′.3 and Cor. 8a. |
| R2-2 | fixed | The text cites PLAN §3 l. 93 at `8709dce7`. Line 93 of the PLAN copy lies inside §3 (§3 runs from l. 63; §4 starts at l. 103) and reads "Restore is bit-exact on the CPU nodes (STATUS, L7)". |
| R2-3 | fixed | §2.1 now gives `110b01a8` (STATUS), `9b2fba9a` (tabular review, round 2) and the Mac's `fab88fce` ref (§3). §2.1 and §3 are now consistent. |
| R2-4 | fixed | `78a1b65e` (12 Nov) is 54 commits behind `fab88fce`; I recomputed the count with `git rev-list --count`. |
| R2-5 | fixed | The new wording ("schedules no new unit and exits once its current unit ends", "should not still be running") matches the deadline check in `collect.py` at the pin (l. 615) and runbook §0. |
| R2-6 | fixed | The gate is now "fixed in the design before the pilot (design S0.5 (iii))". It no longer clashes with "pre-declaration (S0.8) never made". |

Everything verified in rounds 1 and 2 still holds; the commit changes nothing else.

Cosmetic only: the edited lines in all three files run past the files' usual wrap width. This does not affect
the paste-ready row, because the row is unchanged.
