# B1 `_d` — STOP 5 finalist recomputation under `x5_rule/v2` (14 November 2026)

**AI-assisted (Claude, Mac agent). ENGINEERING_ONLY recomputation; not an author decision.** PORTAL_EXAM_RUNBOOK STOP 5
asks the reviewer to recompute the finalists from the manifests and to check the rule hash. This record does that
recomputation independently of `r1.exam.analyze`. Branch `mac-b2-plan-20261114` from `mac-b1-20261107` @ `fcf52c09`,
the published `_d` evidence.

## 1. Inputs and checks

- **Evidence** `docs/r1/reports/b1_d_20261113_evidence/`: `SHA256SUMS` verifies 10/10. Two files matter here:
  - `b1_manifests.json` (`dc5cd04d…`): 18 manifests (3 anchors, 15 candidates);
  - `complete_batch_verifier.json` (`07cb62de…`): the run's `analyze b1 --batch --config`, rc 0, execution label
    `EVIDENCE`.
- **Rule** `r1/exam/rules/x5_rule_v2.yaml` at the run HEAD `7912b7ff`: sha256
  **`53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`**, the frozen value. Every manifest's
  `rule_sha256` equals it.
- **Registry** `r1/exam/registry.yaml` at `7912b7ff`: sha256 `2c6ef6b3…e723`, equal to every manifest's
  `registry_sha256`. Family, role and registry order match for all 18 rows.
- **Audits**: all 2,908 audited proposals use seeds 9101–9104, with four paired metrics each. Each `delta_audit`
  equals mean(candidate) − mean(incumbent) to 1e-12.
- Script: `r1/scripts/b1_stop5_finalists.py`. Output:
  `docs/r1/reports/b1_stop5_20261114/stop5_finalists.json`.

## 2. Recomputation

- μ̂ is the mean thinking-off `delta_audit`, with the rule's paired node-instance cluster bootstrap (2,000
  resamples, seed 20261026).
- Eligibility requires:
  - role `candidate`;
  - `stage_a_pass`;
  - `d28_pass`;
  - thinking-off capable per the registry `thinking_policy` (not always_on; switchable models need their off switch).
- Finalists are the top 4 by μ̂, plus the best of an eligible family absent from the top four, at most 5. Ties go in
  registry order.

| Candidate | family | d28_pass | thinking-off capable | μ̂ (off) | n audited (off) |
|---|---|---|---|---|---|
| glm47_flash | glm | no | yes | +0.003385 | 98 |
| **gemma4_31b** | gemma | **yes** | yes | −0.000891 | 198 |
| gemma4_12b | gemma | no | yes | −0.001329 | 163 |
| qwen36_27b | qwen | no | yes | −0.001554 | 129 |
| laguna_xs21 | laguna | no | yes | −0.001577 | 117 |
| gemma4_26b_a4b | gemma | no | yes | −0.001842 | 155 |
| qwen3_coder_30b_a3b | qwen | no | yes | −0.002727 | 96 |
| ornith10_35b | ornith | no | yes | −0.003243 | 143 |
| qwen36_35b_a3b | qwen | no | yes | −0.003421 | 94 |
| ministral3_14b | mistral | no | yes | −0.003967 | 125 |
| devstral_small2_24b | mistral | no | yes | −0.004092 | 120 |
| qwen38_27b | qwen | no | yes | −0.004251 | 165 |
| qwen35_9b | qwen | no | yes | −0.006002 | 80 |
| ornith10_9b | ornith | no | yes | −0.008055 | 82 |
| olmo31_32b | olmo | no | yes | −0.038499 | 117 |

Anchors, not ranked: random_valid −0.004895; scripted −0.000587 (d28_pass yes); qwen25_coder_7b +0.000156.

**Finalists: `[gemma4_31b]`.** It is the only candidate that passes D28, so the eligible set has one member. There
is no "top four" to fill and no absent-family extra. This equals the published verifier's finalists, and every
μ̂ and bootstrap interval matches the verifier's to 0.0.

## 3. Limits and a descriptive variant

- **D28 is not re-derived here.** `d28_pass` is read from the batch manifests. The run's `verify_batch` checked it
  against the root ledgers on TASL-7 (`b1_batch.py` l. 229). Those ledgers are not on the Mac; only
  `root-trials.sha256` is published. The finalist set rests on that host-side check.
- *Descriptive only, not the rule:* without the D28 filter the finalists would be glm47_flash, gemma4_31b,
  gemma4_12b, qwen36_27b and laguna_xs21. glm47_flash has the highest μ̂ but fails D28.
- gemma4_31b's μ̂ is negative (−0.00089; interval in the JSON). `x5_rule/v2` has no threshold on μ̂, so this does not
  affect finalist status.

## 4. Consequences for B2

- **`b1_analysis` for B2** is the verified complete-batch analysis, the published `complete_batch_verifier.json`
  (sha256 **`07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc`**, rule sha as above, finalists
  `["gemma4_31b"]`). The B2 config's `b1_analysis` / `b1_analysis_sha256` and the B2 authorization note bind this file.
- **X.7 (a) with one finalist.** B2 ranks only the finalists, so the rule pick will be gemma4_31b whatever its B2 Y.
  The "second proposer" (R1-BX-D6-EXAM-RUNNER-UP, a different family ranked by B2 Y) has no candidate in B2.
- **Thinking-on rerun.** The runner reruns finalists of rank < 3 that are switchable, thinking on and descriptive
  (`exam_runner._evidence_unreviewed`, b2 branch). gemma4_31b is switchable with an off switch, so B2 will also run
  it **thinking on, on all B2 nodes × n instances**. That doubles the B2 roots. It is descriptive and never changes the
  pick, but it costs GPU time. Whether Stage A disabled its thinking-on grammar is a host-side Stage A table fact; the
  B1 run included its thinking-on sensitivity roots, so it was not disabled.
