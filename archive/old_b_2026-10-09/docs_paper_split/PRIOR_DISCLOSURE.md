> Copied from the source repository at S = 4154f153, 7 October 2026; the whole file is retained (it covers both papers).
> The source copy in agent-checkpoint-intervention is the historical one.

# Prior-disclosure ledger (verified from repository records)

**Compiled:** 2026-09-25, commit `6ebc608b` baseline, branch `paper-split-2026-09-24`.
**Rule:** every entry is `VERIFIED_IN_REPO` (with path:line) or `ABSENT`.
Nothing here asserts outside knowledge; where the runbook names material that
the repository cannot substantiate, it is marked `BLOCKED`.

## 1. This project's manuscript: public/archival history

| Item | Status | Evidence |
|---|---|---|
| arXiv version of current or older manuscript | ABSENT | No self-identifier anywhere; all arXiv hits are third-party citations. `archive/MERGE_PLAN_2026-08-04.md:438-441` mentions "Paper 1 to arXiv first" as a *plan* for a different paper. |
| Workshop submission (the "29 Aug" deadline) | ABSENT as an event | `archive/MERGE_PLAN_2026-08-04.md:439-441`, `archive/MERGE_CHECKLIST_2026-08-04.md:716-717` are forward-looking plan/risk statements about "Paper 1". No submission, name, or outcome record. |
| TMLR/ICML/AISTATS/ICLR/UAI submission | ABSENT | Recorded venue decisions/targets only: `README.md:32-51`, `paper/VENUE_AND_STRATEGY.md:6-10`. ICLR 2027 declined 2026-08-23. |
| Public repository release | ABSENT | `archive/reference/planning/STAGE_4A2P_PACKAGE.md:85` "No released artifact was verified"; `README.md:228-231` licence not chosen; `docs/paper_track/freeze_repair_bind_2026-09-23/COMPLETION_REPORT.md:8` "nothing was pushed". |
| Outreach draft delivery | ABSENT | `archive/paper_outreach_2026-09-22/outreach_revision_report.md:5-10` prepared a de-anonymised draft; no recipient/delivery record; the named PDF is not in the tree. |
| External disclosure (review service) | VERIFIED | Manuscript source text sent to TypeSafe/JEV review 2026-09-21 with user authorization: `round10/decision_support/jev_paper_review_20260921/REVIEW.md:5-9`, `spine_novelty_request.json:11-25`. Review transmission, not publication. |
| Older manuscript *Calibrating Recoverability* (24 pp, 2026-08-03) | VERIFIED as internal upload | `archive/reference/COMPARISON_2026-08-04_old_vs_current.md:1-4`; sha256 `f7131f7c…` in `docs/paper_track/theory_repair_pass_20260922/PRESERVATION_BASELINE.json:684-687`. Public status ABSENT. |
| Pre-empirical LaTeX tree | VERIFIED as archival, not public | `archive/README.md:30-34`; title page `archive/preempirical_latex_2026-08-04/pf_main.tex:54-57`. |
| Output PDFs `output/pdf/*/main.pdf` | VERIFIED internal | `docs/paper_track/state_audit_20260922/IMPLEMENTATION_REPORT.md:16` (75 pp), `CORRECTION_REPORT_2026-09-22.md:83` (76 pp). External sharing ABSENT. |

**Conclusion for A's submission:** no public archival version exists that could
create a TMLR originality conflict from this project's own history. TMLR
originality rules still require author confirmation at submission time.

## 2. The "KDD ETAAI paper" — BLOCKED

- Only occurrence of "ETAAI" in the repository: `paper/VENUE_AND_STRATEGY.md:47`,
  pointing to `PAPER_POSITIONING_AND_EDITS.md`, which does not exist.
- No KDD ETAAI citation, PDF, DOI, proceedings record, or claim text.
- **Verdict:** the runbook's §3.2 overlap item cannot be verified or refuted
  from this repository. Affected: B's prior-disclosure completeness (B-C4 and
  the related-work section). **Next action:** author supplies the ETAAI
  manuscript/DOI; until then B must not claim to have audited it.

## 3. Nearest prior for Paper B — *Calibration Is Not Control* (2606.21399v1)

| Aspect | What the repository records |
|---|---|
| Decision quantity | Names **intervention advantage**; formalises mismatch as **target error** (`papers/paper_b/legacy/sections/10_related.tex:6-11`; `archive/reference/REVIEW_2026-08-04_soundness_depth_novelty.md:175-184`). |
| Protocol | **Prefix branching**: execute candidate actions from an identical trajectory state. Fixed three-way menu (continue / deployed intervention / quit); "the same prefix provides action-conditioned outcomes for continue, the deployed intervention, and quit" (`paper/figures/coverage_sources.csv:37`). |
| Reconstruction | Replays each prefix to the base-trajectory state, verifies step-by-step agreement, discards mismatches, reports 100% match on retained data; repeated shallow-prefix probe (S3, B.1, B.7) (`10_related.tex:28-33`; `coverage_sources.csv:35-36`). |
| Availability mask | Not reported in inspected scope (`coverage_sources.csv:34`). |
| Harm endpoint | Unknown; App. D not read (`coverage_sources.csv:39`; `coverage_table.tex:25`). |
| Cost accounting | ABSENT from the coverage matrix and records. |
| Verification caveat | Inspected version v1 (19 Jun 2026), HTML truncated before Appendix A; B.1/B.4/B.7 bodies not read (`coverage_sources.csv:34-41`; `docs/paper_track/RL_FRAMING_UPGRADE_IMPLEMENTATION_REPORT.md:32`). |

**B's actual increment beyond this baseline** (must appear in B's introduction):
the decision problem is not the menu choice alone but allocation under
**jointly varying pre-treatment feasibility, verification cost and clean-run
harm**, compared at **matched information, capacity and branch budget**
between outcome-based (failure-risk / utility-deficit) and action-conditioned
allocation, with a **conservative selection rule whose coverage claim is
bounded and explicitly scoped**, and with **batch allocation distinguished
from streaming deployment**. A rejection of the learned-policy null is not a
rejection of oracle ordinal sufficiency (see B manuscript §"What a rejection
does and does not establish").

## 4. Other prior works: what the repository asserts and how B differs

| Work | Repository assertion (quote) | Project difference |
|---|---|---|
| *Causal Agent Replay* (2606.08275) | "Re-executes trajectories under step interventions to estimate counterfactual attribution"; reports an action-match rate; real side-effecting tools out of scope; no distinct feasible arm set (`sources/novelty_collision_audit_2026-08-04.md:22-25`; `coverage_sources.csv:26-33`). | We measure per-layer restoration and the availability mask; branches are executed distinct feasible regimes. |
| *The Replay Gap* (2608.08239) | "Closest mechanical prior art": fresh container + log replay + live continuation, matched control arm, "707/708 branches reconstruct exactly"; two arms; fork points fixed at 30%/70%; no mask (`sources/POSITIONING_AUDIT_2026-08-16.md:120-124`). | We measure per-layer fidelity and the decision-relevant consequence of discrepancy; no mask there. |
| *Harness-R1* (2608.02276) | Training paper; 39 valid patches, 21 reduce batch success; "no sham, no no-fault, no invalid-output constraint, no vector cost constraint, no deployment prevalence" (`sources/harness_r1_delta_2608.02276.md:9-20`). | We ask when a patch proposal should be deployed; harm and cost are endpoints. |
| *Intervention Paradox* (Vasudev et al., 2602.03338) | "A high-AUROC critic can degrade agent performance"; decomposes recovery and disruption (`sources/novelty_collision_audit_2026-08-04.md:9-13`). | We do not claim prediction/effect divergence as new; the no-fault stratum is a designed endpoint. |
| Ao et al. (2601.21471) | Proxy-only indistinguishability with reversed true ordering; audits reveal labels with propensity correction (`docs/paper_track/theory_route_audit_20260922/PRIOR_ART_COMPARISON.md:15`). | A's replay localisation reveals discrepancy events, not intended outcomes; ±p_D remains. |
| Okati et al. 2021 | Budget-constrained triage theorem "subsumes" the ordinal-sufficiency structure (`sources/POSITIONING_AUDIT_2026-08-16.md:15,30-31`). | The ordinal theorem is cited as prior art; B tests learned-policy superiority, not the oracle ordering. |
| Fernández-Loría & Provost 2022 | "Near-identical ordinal condition" under monotone treatment amplification (`sources/POSITIONING_AUDIT_2026-08-16.md:32-34`). | Same: attribution, not re-claim. |
| Kamran et al. 2024 | "Supplies the 'at every capacity' half" (`sources/POSITIONING_AUDIT_2026-08-16.md:35-37`). | Same: attribution, not re-claim. |

## 5. Public history protection rules adopted

1. Historical files under `docs/`, `archive/`, `protocols/`, `evidence/` are
   not edited to match the split. Their paths and text remain as written.
2. A's release manifest includes only A's own package; it excludes B material.
3. B may cite A as a technical report but must not depend on unpublished A
   claims for its validity.
4. If the author later supplies the KDD ETAAI material, this ledger is
   amended by appending a dated entry — never by rewriting the entries above.

## 6. Dated amendment — 2026-09-26: KDD ETAAI item identified

Appended under rule 5.4. The entries above are unchanged.

- The author's records identify the "KDD ETAAI paper" as his own workshop paper
  *Evaluating Governed LLM-Driven ML Experimentation*, published and presented
  at the KDD 2026 ETAAI workshop in August 2026. Its revision history included an
  "ungoverned counterfactual" addition.
- **Status: IDENTIFIED, CONTENT NOT YET AUDITED.** The paper's text is not in
  this repository. Next action: add its PDF (or DOI) and compare it against
  A-C1–A-C4 and B's contribution statement, especially any counterfactual or
  branch-replay material. Record the verdict here as a further dated entry.
- Until that comparison is done, neither A's TMLR submission nor B may state
  that no overlap exists.

## 7. Dated content comparison — 2026-09-26 (L7)

**Status: CONTENT COMPARED, AUTHOR/INDEPENDENT VERDICT PENDING.** This entry
supersedes the unread status in §6 without rewriting historical entries.
Local PDF: `ref/etaai_2026/24_Evaluating_Governed_LLM_Dri.pdf`, 21 pages,
SHA-256 `729d26b5955d35fe163be1e2d194b91671bf9b368697048ff3431d2408c0fb30`. Title page identifies Dowling Wong and KDD ETAAI'26;
this comparison uses the supplied PDF, not an independently verified proceedings
record. Inspected main methods/evaluation §§3–5 (PDF pp3–7), the abstract and
contributions (pp1–2), and supplementary lifecycle/schema material (pp19–21).

| Current claim | ETAAI content and overlap | Boundary of the current increment |
|---|---|---|
| A-C1: audit-to-execution binding in a closed state model | ETAAI's NodeSpec whitelist, pending guard, immutable ledger, provenance hashes and externally owned validation are substantial infrastructure antecedents (§3.2–3.5, pp3–4; Supplement D/E pp19–21). | A's particular restoration audit and immutable consumed payload are narrower measurement objects. They must not be advertised as the first governed harness, scope enforcement, or auditable lifecycle. No code-line reuse audit is claimed here. |
| A-C2: finite-repetition identification and discrepancy bounds | ETAAI reports lifecycle invariants and recomputability, with structural versus empirical validity distinguished (§3.4, p4; §4.5 p6). | In the inspected text, no finite-replay moment identified set, discrepancy allowance p, or localisation/missed-mass theorem was found. This is a scoped reading finding, not a claim of zero conceptual overlap: both concern validity of evidence from agent execution. |
| A-C3: known-truth audit simulation grid | ETAAI includes forced scope/no-op failures, deterministic reruns and a rule-based relabeling check (§3.5 p4; §4.5 p6; Table8 p7; Supplement E pp20–21). | Synthetic/structural validation is shared methodology. A's false/missed-flag and replay-depth grid is a different specified experiment. ETAAI's trial counts or relabeling results cannot support A's 1,890-row claim; A must retain its own evidence lineage. |
| A-C4: complete audit/reference cost comparison | ETAAI reports bounded trial budgets and an LM-training trial duration (§4.1–4.2 p5), and treats task improvement as secondary (§5.1 p6). | The inspected methods/results do not compare complete restoration-audit cost with a same-workload valid reference. A's negative integer-workload comparison has its own denominator and evidence; it is not an extension of ETAAI's task-score result. |
| B: budgeted intervention allocation; N1/N2 PLANNED | ETAAI already allocates trial budget under a fixed lifecycle and deterministic keep/discard authority (§3.4–3.6 p4), and compares governed/ungoverned campaigns (§5.3 p7). | The ungoverned arm is an independent matched campaign, explicitly not reconstructed from the governed ledger (p7). It is not a same-root verify-now/later tree or learned discrepancy-aware advantage gate in the inspected description. B must cite the shared governance substrate while demonstrating a separate decision estimand, matched comparator, feasibility denominator and harm/cost analysis. |

**Draft overlap conclusion:** substantive governance/provenance framing overlaps;
A/B should acknowledge that antecedent. The inspected ETAAI claims do not replace
the specific A identification theorem, its simulation/cost evidence, or B's
PLANNED N1/N2 experiments. This is not an originality or venue-compliance
acceptance and does not authorize a “no overlap” statement. The author and
independent reviewer must confirm artifact reuse and the final disclosure text.

## 8. Dated amendment — 2026-10-04: ETAAI archival status

Appended under rule 5.4. The entries above are unchanged.

- **Author statement (Dowling Wong, 2026-10-04):** the KDD 2026 ETAAI workshop
  is non-archival.
- TMLR allows overlap with the author's earlier work only when the venue is
  "publicly declared, in writing, to be non-archival" (TMLR editorial policies,
  checked 2026-10-04: https://jmlr.org/tmlr/editorial-policies.html).
- **Status: STATED BY AUTHOR; WRITTEN DECLARATION NOT YET RECORDED.** Next
  action: record the CFP or workshop-page wording (URL and quotation), or an
  organizer confirmation, here.
- This does not change §7: the overlapping governance/provenance framing is
  still acknowledged and cited in the third person, and no "no overlap"
  statement is authorized.

## 9. Dated amendment — 2026-10-04: claim IDs in §7 versus the manuscript's (C1)–(C4)

Appended under rule 5.4 (review finding F25). The entries above are unchanged.

§7 uses the ledger IDs of `CLAIMS.yaml`, which predate the manuscript's
identification → use → validation → cost ordering (A-R5). Read §7's rows
against the submitted contribution list as follows:

| §7 row (ledger ID) | Manuscript contribution |
|---|---|
| A-C1: audit-to-execution binding | (C3) validation, audit half; the control matrix is `tab:state-audit-controls` |
| A-C2: finite-repetition identification and discrepancy bounds | (C1) identification; its worked example, calculator and checklist are (C2) use |
| A-C3: known-truth audit simulation grid | (C3) validation, grid half; `tab:state-audit-grid`. The claim was narrowed on 2026-10-04 (F05) to: valid allowances stay valid under false and missed flags, which cost informativeness; ignoring missed flags breaks validity; checkpoints help, repetition at fixed N changes little |
| A-C4: complete audit/reference cost comparison | (C4) cost lesson |

The §7 overlap reading is unaffected: no row changes its ETAAI comparison or
its boundary, and §7's draft overlap conclusion and §8's status still stand.

## 10. Dated amendment — 2026-10-05: ETAAI non-archival status and citation decision

Appended under rule 5.4. The entries above are unchanged.

- **Author determination (Dowling Wong, 2026-10-05):** the KDD 2026 ETAAI
  workshop is non-archival.
- **Public written statement relied on:**
  <https://kdd-eval-workshop.github.io/agenticai-evaluation-kdd2026/> ("KDD
  Workshop on Evaluation and Trustworthiness of Agentic AI", 9 August 2026),
  retrieved 2026-10-04: "The accepted papers will be posted on the workshop
  website but will not be included in the KDD proceedings." The page does not
  use the word "non-archival"; the author treats this sentence as the public
  written declaration that TMLR's overlap policy requires.
- **Citation (author decision, 2026-10-05):** the submitted Paper A no longer
  cites the ETAAI paper. The third-person paragraph in §8 of the manuscript and
  the `wong2026governed` entry in `references.bib` are removed in the commit that
  adds this entry. Basis: §7 found shared governance/provenance framing, and none
  of A's theorem, grid or cost results depends on the ETAAI paper; removing the
  self-citation also removes the only author-identifying string from the
  double-blind PDF and supplement. Mitigation: mention the workshop paper to the
  TMLR action editor if the submission form allows a confidential note, and
  restore the citation in the camera-ready version.
- **Reuse of text, figures or results** from the ETAAI paper: not yet confirmed
  by the author. §7 compared content; no reuse audit was performed.
- For the anonymous submission, this replaces §8's "acknowledged and cited in
  the third person". §7's conclusion that the antecedent should be acknowledged
  is met by the action-editor note and the camera-ready citation. No "no
  overlap" statement is authorised.
