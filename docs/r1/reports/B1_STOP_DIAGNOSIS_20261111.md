# B1 STOP diagnosis — run `6835_20261108_a` (11 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local agent). Diagnosis report of plan `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §§2–4, from the single read-only capture of `proposals/B1_DIAGNOSIS_HANDOFF_20261109.md`. Review: pending. Nothing here changes the recorded STOP, a criterion or a pin.

## 1. Result

| Item | Result |
|---|---|
| **Class (plan §4, pre-declared rules)** | **D — resting on H2 alone** |
| H1 design (two random anchors cannot be ordered) | **NOT SUPPORTED** |
| H2 metric (incumbent-relative increment not monotone in quality) | SUPPORTED (`random_valid` increment drop, 0.756 σ_joint) |
| H3 power | SUPPORTED |
| H4 engineering | NOT SUPPORTED (no flag) |
| **D7** (7B duplicate rate, the next gate) | **PASS**: 120 / 242 = 0.4959, inside [0.42386590667728663, 0.5800007633587785] |
| **R4 under line A1** (PLAN `R1-EXAM-B1-ANCHOR-R4`) | **Not applicable**: A1 covers class D with H1 supported; a D resting on H2 alone goes to the author |

**Consequence.** The restart hand-off (`proposals/B1_RESTART_HANDOFF_20261109.md`, branch `mac-b1-r4-20261109`) is **not armed**. B1 stays stopped until the author chooses a route (§6).

## 2. Provenance

- Capture receipt: `reports/OPS_B1_DIAGNOSIS_CAPTURE_20261109.md` on `ops-b1-20261109` @ `d1d30687`. Single run, 2026-11-11 00:07:34–00:07:40 UTC, wrapper exit 0, `DIAGNOSIS_CAPTURE_COMPLETE` and one `SSH_EXIT=0` line present; diagnosis script SHA-256 `82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93` (accepted, `reviews/B1_DIAG_REVIEW_20261109.md`).
- Private copy checked before analysis: `ssh.log` SHA-256 `c6bc8a84ae482a249bccd65303397a66615832be97f82338be17a370c3c46df5`, `ssh.rc` SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` (both equal to the receipt). The capture states `batch_state.json` equal to the pinned state of the accepted descriptive capture (`cfe74faf…5794`) and `stop_changed` false; the script would have refused otherwise.
- Analysis: `proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py <ssh.log>` at commit `db73a0d0` (SHA-256 `fdbfbeb155e5bbbf0d6ce8c0a1385c90e51a7632764394425bac710b760b970a`), exit 0; the output is identical to that of `6c2a857f`. Commit `6c2a857f` adds the three recomputations of review note N1 to the accepted script (standardised D1 values from the rows and the pinned σ_joint; D3/D4/D8 summaries from the rows; D7 reference equal to the pinned constant, bounds, source and SHA-256), each with a refusal test that fails on the previous version; `db73a0d0` adds a check that each root's proposals are in budget order (the D4 half-split relies on it). The classification rules and thresholds (Z_SMALL 0.10, Z_DROP 0.25, COUNT_RATIO 1.5) are unchanged from the accepted version.
- **Not committed until this report's review is accepted:** `ssh.log`, `ssh.rc` and every per-proposal `delta_audit` (including the 7B values). This report carries only aggregates over proposals.

## 3. Tables

Values are incumbent-relative audited increments `delta_audit` on each node's metric (higher is better); σ_joint from the D21 noise floor (`NOISE_FLOOR_COMMON_20261022.md` Table 1: digits_mlp 0.0102, openml_credit_approval 0.0279, openml_ionosphere 0.0410).

### D1 — the gate recomputed (scripted − random_valid, 12 instance pairs)

| point | lower | upper | reproduces the STOP (lower ≤ 0) |
|---|---|---|---|
| +0.0046 | −0.0006 | +0.0089 | yes |

| node | instance pairs with scripted ahead | node mean of (difference / σ_joint) |
|---|---|---|
| digits_mlp | 2 of 4 | +0.221 |
| openml_credit_approval | 4 of 4 | +0.181 |
| openml_ionosphere | 3 of 4 | +0.158 |
| all | 9 of 12 | +0.187 |

### D0 / D2 — counts per anchor × node (4 roots each)

| anchor / node | trials | evaluated | invalid | duplicates | no-ops | parse failed | skipped | audited | keeps (incl. first) | in-run gain after first keep | worker runs | termination | D0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen25_coder_7b / digits_mlp | 82 | 82 | 2 | 31 | 2 | 0 | 0 | 47 | 27 | +0.2862 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| qwen25_coder_7b / credit_approval | 80 | 80 | 6 | 43 | 6 | 0 | 0 | 33 | 10 | +0.0018 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| qwen25_coder_7b / ionosphere | 80 | 80 | 27 | 46 | 27 | 0 | 0 | 30 | 8 | +0.0074 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| random_valid / digits_mlp | 105 | 105 | 25 | 52 | 25 | 0 | 0 | 48 | 13 | +0.0724 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| random_valid / credit_approval | 126 | 126 | 46 | 64 | 46 | 0 | 0 | 56 | 18 | +0.0187 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| random_valid / ionosphere | 125 | 125 | 45 | 74 | 45 | 0 | 0 | 46 | 17 | +0.0747 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| scripted / digits_mlp | 80 | 80 | 0 | 1 | 0 | 0 | 0 | 75 | 13 | +0.0146 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| scripted / credit_approval | 81 | 80 | 0 | 10 | 0 | 0 | 1 | 66 | 21 | +0.0177 | 20,20,20,20 | worker_cap | 0, 0, 0 |
| scripted / ionosphere | 81 | 80 | 0 | 11 | 0 | 0 | 1 | 65 | 17 | +0.0495 | 20,20,20,20 | worker_cap | 0, 0, 0 |

"In-run gain after first keep": mean over roots of the final kept record's in-run metric minus the first valid trial's (the harness keeps the first valid trial unconditionally and never audits it; no unedited start metric exists in the ledger). D0 = (k ≠ 4, None in vectors, delta mismatch).

### D3 — `delta_audit` per anchor × node

| anchor / node | n | mean | median | share harmful | mean / σ_joint | median / σ_joint | mean / median sd(δ) |
|---|---|---|---|---|---|---|---|
| random_valid / digits_mlp | 48 | −0.0036 | +0.0000 | 0.396 | −0.351 | +0.000 | −0.543 |
| random_valid / credit_approval | 56 | −0.0048 | −0.0000 | 0.500 | −0.172 | −0.000 | −1.600 |
| random_valid / ionosphere | 46 | −0.0064 | +0.0000 | 0.478 | −0.156 | +0.000 | −0.399 |
| scripted / digits_mlp | 75 | −0.0016 | +0.0000 | 0.333 | −0.157 | +0.000 | −0.243 |
| scripted / credit_approval | 66 | +0.0004 | +0.0000 | 0.439 | +0.013 | +0.000 | +0.121 |
| scripted / ionosphere | 65 | −0.0004 | +0.0000 | 0.385 | −0.009 | +0.000 | −0.023 |
| D8 (information only): qwen25_coder_7b / digits_mlp | 47 | +0.0035 | +0.0049 | 0.426 | +0.343 | +0.478 | +0.530 |
| D8: qwen25_coder_7b / credit_approval | 33 | −0.0007 | −0.0000 | 0.545 | −0.024 | −0.000 | −0.225 |
| D8: qwen25_coder_7b / ionosphere | 30 | −0.0042 | +0.0000 | 0.467 | −0.102 | +0.000 | −0.260 |

### D4 — first vs second half of each root's audited sequence; budget index ≤ 10 vs > 10

| anchor / node | first half mean (n) | second half mean (n) | b ≤ 10 mean (n) | b > 10 mean (n) |
|---|---|---|---|---|
| qwen25_coder_7b / digits_mlp | +0.0129 (24) | −0.0063 (23) | +0.0091 (32) | −0.0084 (15) |
| qwen25_coder_7b / credit_approval | −0.0006 (18) | −0.0008 (15) | −0.0006 (27) | −0.0012 (6) |
| qwen25_coder_7b / ionosphere | −0.0009 (17) | −0.0084 (13) | −0.0039 (21) | −0.0048 (9) |
| random_valid / digits_mlp | +0.0072 (26) | −0.0163 (22) | +0.0075 (23) | −0.0138 (25) |
| random_valid / credit_approval | −0.0045 (29) | −0.0051 (27) | −0.0080 (21) | −0.0029 (35) |
| random_valid / ionosphere | −0.0053 (24) | −0.0076 (22) | −0.0063 (21) | −0.0064 (25) |
| scripted / digits_mlp | −0.0025 (39) | −0.0006 (36) | −0.0026 (36) | −0.0007 (39) |
| scripted / credit_approval | +0.0013 (34) | −0.0006 (32) | +0.0013 (35) | −0.0007 (31) |
| scripted / ionosphere | +0.0008 (33) | −0.0016 (32) | +0.0008 (35) | −0.0018 (30) |

### D7 — 7B duplicate rate (the next gate)

| duplicates | evaluated | rate | pinned interval (unrounded, as the gate reads it) | inside |
|---|---|---|---|---|
| 120 | 242 | 0.49586776859504134 | [0.42386590667728663, 0.5800007633587785] | yes |

## 4. Reading of each hypothesis

The class follows mechanically from the pre-declared rules (analysis script docstring). The reading below explains the numbers; it does not override the rules, and where the data are only consistent with an explanation it says so.

- **H4 — no engineering defect shown by the pre-declared checks.** Every D0 counter is 0; every one of the 36 roots ended `worker_cap` with exactly 20 worker runs; no software root lacks audited proposals; the D1 recomputation reproduces the recorded STOP (lower bound ≤ 0); no anchor × node has more than half its trials invalid. Together with the code checks (`reports/B1_STOP_CODE_CHECKS_20261109.md`) this gives no ground for class E.
- **H1 — not supported by the rule.** Both disjuncts fail: the D1 point is positive (+0.0046), and the mean standardised per-instance difference (+0.187) is above Z_SMALL with all three node means positive. These are point estimates: digits_mlp has only 2 of 4 pairs with scripted ahead, and the D1 interval includes 0, which is why the gate stopped. The data therefore do not show that the anchors "cannot be ordered", nor that they are ordered.
- **H3 — supported by the rule.** Point > 0, all three node means > 0, lower bound −0.0006 ≤ 0: a small, mostly consistent difference on 12 pairs. On the raw scale digits_mlp has the largest per-instance differences in both signs, which widens the interval.
- **H2 — supported by the rule, on one anchor × node.** `random_valid`'s pooled standardised mean falls by 0.756 σ_joint from the first to the second half of each root's audited sequence (rule: > 0.25). The fall comes from digits_mlp (+0.0072 → −0.0163); without digits_mlp, `random_valid`'s pooled change is about −0.036 σ_joint, far below the threshold. Scripted shows no drop (its pooled second half is slightly higher, +0.030 σ_joint). The pattern is consistent with the plan's mechanism (a proposer whose incumbent improves early faces a better incumbent later), but these data do not establish it: the "in-run gain" column covers the whole run, not its first half, and `random_valid` has an equally large in-run gain on ionosphere (+0.0747) without a drop there. The count-ratio disjunct did not fire (scripted / random_valid audited counts 1.56, 1.18, 1.41; it needs > 1.5 on two nodes). The 7B anchor falls from first to second half on digits_mlp as well (D8, information only).
- **Class.** H4 neither supported nor undetermined, H2 supported → **D** by the rule order E → REVIEW → D → P → UNCLASSIFIED. Plan §4 defines P as "H3 without H1/H2", so P is excluded here because H2 fired, although H3 is supported. The D rests on the H2 signal above, i.e. on a single anchor × node.

## 5. Additions to plan §4 made by the analysis (declared, not used tonight)

The accepted analysis (round 2 of `reviews/B1_DIAG_REVIEW_20261109.md`) fixed handling rules that plan §4 does not state. None of the first three was triggered by this capture; they are listed so the appendix can name them.

1. **Class `REVIEW`.** If H4 is UNDETERMINED (an anchor × node with invalid / trials > 0.5) and not SUPPORTED, the class is REVIEW and goes to the author; it blocks R4.
2. **Zero audited proposals.** A software-anchor root with no audited proposal is accepted only as a cross-checked null pattern (no D1 recomputation possible, `D1_error` recorded); it makes H4 SUPPORTED, so the class is E.
3. **Zero evaluated 7B proposals.** D7 is then FAIL, exactly as `anchor_gate` treats a missing rate.
4. **Class `UNCLASSIFIED`.** No rule fires (H1, H2, H3 and H4 all not supported); goes to the author.
5. **Class order** E → REVIEW → D → P → UNCLASSIFIED, and R4 under A1 only for class D **with H1 supported** and D7 PASS (PLAN `R1-EXAM-B1-ANCHOR-R4`); a D resting on H2 alone, P, REVIEW, UNCLASSIFIED and any D7 FAIL go to the author.

## 6. What the author needs to decide

Line A1 does not cover this outcome, so B1 restarts only after a new author line. Each option below is disclosed in the appendix as a post-hoc amendment made after seeing the anchors, with the original criterion and the numbers of §3.

**The tension to weigh first.** H2 says the incumbent-relative increment may not be monotone in proposer quality. The frozen B1 rule (`r1/exam/rules/x5_rule_v2.yaml`) ranks the candidates on exactly that quantity, `pooled_audited_mean_proposal_increment`. If H2 is real, it questions the B1 ranking itself, not only the anchor gate; that is why PLAN `R1-EXAM-B1-ANCHOR-R4` left an H2-only D to the author. Against that, the H2 signal here rests on one anchor × node (§4), and the ranking quantity was pre-specified before Stage A.

Options of plan §4 for class D:

- **R4.** Drop the anchor-ordering STOP, report the anchors descriptively, keep the 7B duplicate-rate check (which passes), let the frozen rule rank. The code fix and restart checkout exist and are reviewed (`mac-b1-r4-20261109` @ `4ddc820e`). Applying it to this outcome needs a reviewed change in several places on that branch, not one line: the PLAN row's condition, the restart hand-off §0, the RUNBOOK X.3 note ("i.e. H1 supported"), and the appendix draft, whose stated reason ("the two random anchors cannot be ordered") this diagnosis does not support and which would be rewritten around H2 / the design of the check.
- **R1.** Keep the ordering on σ_node-standardised increments. Plan §4: only sensible if D3 shows a clear standardised gap the raw scale hid. D3's standardised means are small for both anchors (random_valid −0.16 to −0.35, scripted −0.16 to +0.01), and D1's node means of the standardised difference are +0.16 to +0.22, so the gap is not clear.
- **R2.** Order `random_valid` against `qwen25_coder_7b`. Post hoc: D8 above shows its answer.
- **R3.** A campaign-level criterion (final-incumbent audited improvement), matching Paper B's primary outcome. It answers H2 directly, but B1 computes no final Y today (only B2 does): new code, review and a longer restart.

(Plan §4 lists "more anchor-only instance seeds" only for class P, so it is not an option for this D.)

**Recommendation: R4, with the tension disclosed.** Reasons: the H2 signal is one anchor × node and does not show on the other two nodes; the ranking quantity was fixed before the data and changing it now (R3) would be the larger post-hoc change; any new ordering gate chosen after seeing these anchors (R1, R2) would not be a real test. The appendix should state that H2 fired on random_valid / digits_mlp and that the ranking quantity is an incumbent-relative increment. If the author regards H2 as real, **R3** is the consistent choice instead.

Paste-ready (R4): `B1 诊断为 D（仅 H2，且只在 random_valid/digits_mlp 上；H1 不成立；H3 成立；D7 PASS）：采用 R4，把 R1-EXAM-B1-ANCHOR-R4 的条件放宽为"D 类（H1 或 H2）且 D7 PASS"，同步改重启 hand-off §0、RUNBOOK X.3 注和附录草稿（理由改为检查本身的设计与 H2，并披露排序量是相对 incumbent 的增量）；审查后按重启 hand-off 重跑。`

Paste-ready (R3): `B1 诊断为 D（仅 H2）：采用 R3，改用 campaign 级终点（最终 incumbent 的审计改进）作为锚点判据；先实现并独立审查，再重启。`

## 7. Not done here

No change to `mac-b1-r4-20261109`, the PLAN row or the restart hand-off (they wait for the author's line). No host action. The private capture stays uncommitted until this report's review is accepted.
