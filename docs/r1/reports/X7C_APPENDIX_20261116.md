# X.7(c) appendix: C3 premises against proposer strength, from B1/B2 (16 November 2026)

**AI-assisted (Claude, Mac agent). Unit S2-M5. Not an author decision.**

The declared rule finds **differences, not the null**: the finalist and two anchors differ on two C3 premises beyond
their 95 % intervals.

- **Authority.** R1-EXAM-X7 (c) (`author-sweephost-20261116` @ `fd275c53`); RUNBOOK X.7 (c).
- **Declaration.** `proposals/X7C_APPENDIX_DECLARATION_20261116.md`, committed at `4af42d8a` before the script existed
  and before any interval or comparison was computed. It records the B1 summary values that were seen before it.
- **Script.** `r1/scripts/x7c_appendix.py` at `655a8a4b` (sha256 `19106320…`), committed before its run. A smoke run at
  B = 50 was not read.
- **Environment.** `/tmp/np244`: Python 3.13.18, NumPy 2.4.4.
- **Command.** `python r1/scripts/x7c_appendix.py --b1-manifests … --b1-usage … --b1-analysis … --b2-manifests …
  --b2-roots … --json …`. The inputs are extracted read-only from the refs in the declaration's §1; their sha256 are
  recorded in the output's `inputs`.
- **Output.** `reports/x7c_appendix_20261116/x7c_output.json` (sha256 `f35a5a87…`) and `x7c_output.md` (sha256
  `4dc35e13…`).
- **Self-checks.** For every row, μ̂ reproduces the B1 analysis (`07cb62de…`) to 1e-12, and the per-root trial counts
  of the usage table sum to each manifest's trial count.

## 1. Decision (declared rule, §4)

The comparisons are the finalist `gemma4_31b` minus each anchor, on thinking-off roots of B1 (12 shared instance
clusters), with 95 % paired cluster bootstrap intervals (B = 10,000).

| Anchor | Quantity | Finalist | Anchor | Difference | 95 % CI | Beyond CI | Bonferroni (7) CI |
|---|---|---|---|---|---|---|---|
| random_valid | Q1 rule-skippable share | 0.175 | 0.579 | −0.404 | [−0.461, −0.340] | **yes** | [−0.480, −0.316] |
| random_valid | Q2 increment sd | 0.0127 | 0.0302 | −0.0175 | [−0.0308, −0.0054] | **yes** | [−0.0354, −0.0028] |
| scripted | Q1 | 0.175 | 0.149 | +0.026 | [−0.024, 0.080] | no | [−0.042, 0.099] |
| scripted | Q2 | 0.0127 | 0.0072 | +0.0055 | [0.0013, 0.0089] | **yes** | [−0.0007, 0.0100] |
| qwen25_coder_7b | Q1 | 0.175 | 0.545 | −0.371 | [−0.429, −0.320] | **yes** | [−0.450, −0.300] |
| qwen25_coder_7b | Q2 | 0.0127 | 0.0411 | −0.0284 | [−0.0446, −0.0050] | **yes** | [−0.0495, 0.0100] |
| qwen25_coder_7b | Q3 A4 Brier | 0.239 | 0.214 | +0.024 | [−0.010, 0.074] | no | [−0.017, 0.098] |

**Five of the seven comparisons differ beyond the 95 % CI, so the appendix does not report a null.**
- With the Bonferroni intervals (descriptive), three still differ: Q1 against `random_valid` and against
  `qwen25_coder_7b`, and Q2 against `random_valid`.
- No bootstrap resample was dropped as NaN.

## 2. Reading

1. **Rule-skippable share (Q1) is the clear difference.**
   - With the pick, 17.5 % of thinking-off trials repeat an evaluated configuration or the incumbent. With
     `qwen2.5-coder:7b`, sweep 1's manager, the share is 54.5 %; with `random_valid` it is 57.9 %. Scripted is at
     14.9 %.
   - The B2 replication on fresh instances gives the same: 0.188 [0.142, 0.242].
   - C3_DESIGN §2.3 took "39–77 % of LLM trials repeat an evaluated configuration" from qwen2.5-coder pilot data. Under
     the pick that premise is much weaker.
   - What this means for the rule layer (A2) in sweep 2: the duplicate / no-op rules will skip far fewer runs than in
     sweep 1. This is a C3 premise that differs by proposer and should be disclosed with the cross-proposer tables.
   - Across all 18 rows, Q1 falls as μ̂ rises (Spearman ρ = −0.43, descriptive).
2. **Increment dispersion (Q2) differs, but the pooled sd hides node structure.**
   - The pooled sd is lower for the pick than for `qwen2.5-coder:7b` and `random_valid`, and higher than for scripted.
   - Per node, the pick's sd is about 0.005 on `digits_mlp`, against 0.063 for qwen2.5-coder and 0.044 for
     random_valid. On `openml_credit_approval` it is 0.0052 against 0.0018 and 0.0175. On `openml_ionosphere` it is
     0.021 against 0.008 and 0.024.
   - So the pooled qwen2.5-coder difference comes from its large `digits_mlp` spread. On the other two nodes the pick is
     the more dispersed of the two.
   - The pooled Q2 is the declared primary; per-node sds were declared secondary because the nodes' metric scales
     differ.
   - The B2 replication agrees: 0.0135 [0.0076, 0.0182], with similar per-node values.
3. **A4 calibration (Q3) does not differ.** The pick's Brier score, 0.239, is not distinguishable from qwen2.5-coder's
   0.214, and its correlation with μ̂ across rows is weak (ρ = 0.09). The B2 Brier is 0.260 [0.233, 0.282]. Q3 is not
   applicable to the software anchors, which have no forecasts.
4. **Proposer strength itself is not claimed.**
   - The pick's B1 μ̂ (−0.00089) is below the scripted anchor's (−0.00059), with overlapping intervals, as R1-EXAM-X7 (a)
     requires to be disclosed.
   - The finalist was selected on these data (winner's curse).
   - The appendix compares premises only.

## 3. Descriptive table

All 18 B1 rows, thinking off, ordered by μ̂, with 95 % cluster intervals: see `x7c_output.md`.

## 4. Limits

- **Small and narrow data.** Twelve clusters per row and three nodes: the percentile intervals may undercover. Seven
  comparisons were made; the Bonferroni intervals are reported.
- **Q1 depends on budget use.** It counts all trials, invalid ones included. A root's trial count depends on how many
  trials it used (for example, `random_valid` used 356 trials over 12 roots).
- **Q2 mixes metric scales.** It pools nodes with different scales; see the per-node values.
- **Audit noise differs between B1 and B2.** B1 uses K = 4 audits (9101–9104) and B2 uses K = 10 (9201–9210).
- **Thinking-on roots are excluded** (descriptive only, R1-EXAM-X7).
