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
- Analysis: `proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py <ssh.log>` at commit `6c2a857f` (SHA-256 `c97b8e77713ecd084c910d3e8d82464796b2afcaae632f65448543d720f8aafe`), exit 0. That commit adds the three recomputations of review note N1 to the accepted script (standardised D1 values from the rows and the pinned σ_joint; D3/D4/D8 summaries from the rows; D7 reference equal to the pinned constant, bounds, source and SHA-256), each with a refusal test that fails on the previous version. The classification rules and thresholds (Z_SMALL 0.10, Z_DROP 0.25, COUNT_RATIO 1.5) are unchanged from the accepted version.
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

The class follows mechanically from the pre-declared rules (analysis script docstring). The reading below explains the numbers; it does not override the rules.

- **H4 — no engineering defect shown.** Every D0 counter is 0; every one of the 36 roots ended `worker_cap` with exactly 20 worker runs; no software root lacks audited proposals; the D1 recomputation reproduces the recorded STOP (lower bound ≤ 0); no anchor × node has more than half its trials invalid. With the code checks (`reports/B1_STOP_CODE_CHECKS_20261109.md`) this closes class E.
- **H1 — not supported.** Both rule disjuncts fail: the D1 point is positive (+0.0046), and the mean standardised per-instance difference (+0.187) is above Z_SMALL with scripted ahead on all three nodes. The two random anchors are ordered in the expected direction on every node; the data do not show "cannot be ordered".
- **H3 — supported.** Point > 0, all three node means > 0, lower bound −0.0006 ≤ 0: a consistent but small difference on 12 pairs. On the raw scale digits_mlp has the largest per-instance differences in both signs (2 of 4 pairs positive), which widens the interval.
- **H2 — supported, by `random_valid` alone.** Its pooled standardised mean falls by 0.756 σ_joint from the first to the second half of each root's audited sequence (rule: > 0.25). The drop is concentrated on digits_mlp (+0.0072 → −0.0163); the other two nodes change little. This is the mechanism the plan describes: `random_valid`'s grid jumps raise the incumbent early (in-run gain +0.072 on digits_mlp vs +0.015 for scripted), so its later increments are measured against a better incumbent. The count-ratio disjunct did not fire (scripted / random_valid audited counts 1.56, 1.18, 1.41; it needs > 1.5 on two nodes). Scripted's own drop is below the threshold. The 7B anchor shows the same first-half / second-half pattern on digits_mlp (D8, information only).
- **Class.** H4 not supported and not undetermined, H2 supported → **D**. H3 is also supported; under the plan's ordering D precedes P, so the class is D, and both the D and P routes of plan §4 are relevant to the author's choice.

## 5. Additions to plan §4 made by the analysis (declared, not used tonight)

The accepted analysis (round 2 of `reviews/B1_DIAG_REVIEW_20261109.md`) fixed three handling rules that plan §4 does not state. None of them was triggered by this capture; they are listed so the appendix can name them.

1. **Class `REVIEW`.** If H4 is UNDETERMINED (an anchor × node with invalid / trials > 0.5) and not SUPPORTED, the class is REVIEW and goes to the author; it blocks R4. Class order: E → REVIEW → D → P → UNCLASSIFIED.
2. **Zero audited proposals.** A software-anchor root with no audited proposal is accepted only as a cross-checked null pattern (no D1 recomputation possible, `D1_error` recorded); it makes H4 SUPPORTED, so the class is E.
3. **Zero evaluated 7B proposals.** D7 is then FAIL, exactly as `anchor_gate` treats a missing rate.

Also declared: R4 under A1 requires class D **with H1 supported** and D7 PASS (PLAN `R1-EXAM-B1-ANCHOR-R4`); a D resting on H2 alone, P, REVIEW, UNCLASSIFIED and any D7 FAIL go to the author.

## 6. What the author needs to decide

Line A1 does not cover this outcome, so B1 restarts only after a new author line. The options are those of plan §4; each is disclosed in the appendix as a post-hoc amendment made after seeing the anchors, with the original criterion and the numbers of §3.

- **R4 for this outcome too.** Drop the anchor-ordering STOP, report the anchors descriptively, keep the 7B duplicate-rate check (which passes), let the frozen B1 rule carry the ranking. The fix and its restart checkout already exist and are reviewed (`mac-b1-r4-20261109` @ `4ddc820e`); only the PLAN row's condition ("class D with H1 supported") and the restart hand-off's precondition would need a reviewed one-line widening to "class D (H1 or H2)". Plan §4's reason for R4 — any ordering gate chosen after seeing these anchors is not a real test — holds whether the D comes from H1 or H2.
- **P (a): σ_node-standardised ordering** or **P (b): more anchor-only instance seeds.** Both change the criterion after seeing a consistent positive point with a lower bound just below 0, so a pass would carry little evidential weight; (b) also costs anchor runs on TASL-7.
- **R2** (order `random_valid` against the 7B) or **R3** (campaign-level final-incumbent criterion): R2 is post hoc as well (D8 is visible above); R3 needs new code and review because B1 computes no final Y.

Recommendation: **R4 for this outcome**, by widening the condition of `R1-EXAM-B1-ANCHOR-R4` to class D via H1 or H2 with D7 PASS, followed by the restart hand-off unchanged otherwise.

Paste-ready (if the author agrees): `B1 诊断为 D（仅 H2，H1 不成立，H3 成立，D7 PASS）：同样采用 R4，把 R1-EXAM-B1-ANCHOR-R4 的条件放宽为"D 类（H1 或 H2）且 D7 PASS"，附录照常披露为事后修订；改动审查后按重启 hand-off 直接重跑。`

## 7. Not done here

No change to `mac-b1-r4-20261109`, the PLAN row or the restart hand-off (they wait for the author's line). No host action. The private capture stays uncommitted until this report's review is accepted.
