# Notes: `calibration.ipynb` (wdkns/modern_genai_bilibili, llms/架构/jev)

Source: https://github.com/wdkns/modern_genai_bilibili/blob/main/llms/%E6%9E%B6%E6%9E%84/jev/calibration.ipynb (last commit "update notes", kernel `verl`, run 2026-10-11). Summary in our own words.

## Metrics
- Brier score: mean squared error between forecast probability and outcome.
- ECE: bin-weighted |accuracy − confidence|, typically 10–15 bins. Reliability diagram: bars below the diagonal = overconfident.
- Low ECE does not imply good discrimination; ECE is only meaningful together with accuracy.
- Two binning conventions matter:
  - **all-options** (GPT-4 report Fig. 8 style): every option's probability is a point (MMLU: 56,168 points);
  - **top-1**: only the chosen option (14,042 points).

## LLM calibration background (as summarised in the notebook)
- Tian et al. 2023 on SciQ (gpt-3.5): sampled-majority "label prob" ECE 0.256; linguistic expressions 0.166; verbalized top-1 0.234; **verbalized top-4 0.065** — listing alternatives spreads probability and restores calibration.
- GPT-4 report: pretrained ECE 0.007 on MMLU subset → 0.074 after PPO.
- Yue et al. 2025: RLVR sharpens the distribution (entropy, perplexity down; per-question accuracy pushed to 0/1) — the stated reason post-trained logprobs lose calibration.
- Damani et al. 2025 (RLCR): binary rewards are not proper scoring rules and hurt calibration; adding a Brier term on verbalized confidence fixes it; pretraining log loss is proper, which is why pretrained models are calibrated.

## Jev experiments
- MMLU test, 14,042 questions, zero-shot, Choice type (25 questions per request → 562 requests):
  - all-options ECE **0.011**; top-1 ECE **0.022** (95 % CI 0.020–0.027); external article (1,200 items) top-1 0.031.
- Biased-coin probe: state "coin lands heads p %", p = 5…95.
  - Jev **Noul** ("Will this flip land heads?") tracks p roughly along the diagonal.
  - Jev **Choice{heads, tails}** behaves like a step function at 50 % (55 % heads → p(heads) ≈ 0.985).
  - Qwen instruct P(Yes) from first-token logprobs: also a step function.
  - Reading: Choice/argmax-style heads report "which answer is most likely", not the outcome distribution; Noul reports the aleatoric probability.
- Credit-card fraud (ULB, 0.17 % positives): undersampling shifts logit by −log β; analytic prior correction ≈ Platt scaling; decision rule p · 0.9 · amount > 5. When to recalibrate: train/deploy distribution mismatch (resampling, class weights, prior shift), non-log-loss models, overconfident nets (temperature scaling).
