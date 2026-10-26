# Track P Phase 5 — P.3a DRYRUN on one model (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). **DRYRUN — not evidence; not independently reviewed** (the Phase 5 STOP review belongs to the authorized evidence runs). Run under the author's overnight permission ("A DRYRUN of Phase 5 on one model is fine"); no authorization note `trackp_p3a_<date>.md` exists, so no evidence run was started. Commit `84c37a2` (clean), evidence label DRYRUN in both manifests. Evidence: `trackp_p3a_dryrun_20261026/`.

Model: kev-0.8b (Kev v1.0 adapter + pointer head on Qwen3.5-0.8B-Base). Command: `python r1/scripts/trackp.py e0 --base kev-0.8b --evidence DRYRUN --with-probes` and the same with `--hard`. E0 per spec §5.5 on the committed E0 set (3,000 train / 1,000 test, held-out cells): (1) frozen-backbone head fit, 200 steps; (2) 200 LoRA steps; soft labels, and the hard-label contrast run. E6 probes at reduced size (n = 32 per probe) on the soft-label model. Wall time 07:08–07:15 UTC.

## Results (held-out test cells)

| Run | stage | RPS | mean slope (target 1; pass ≥ 0.8) | width slope (target 1; pass ≥ 0.7) | width ratio |
|---|---|---|---|---|---|
| soft | head fit | 0.048 | 0.075 | 0.005 | 2.44 |
| soft | + 200 LoRA steps | 0.002 | **1.003** | **0.114** | 1.30 |
| hard | head fit | 0.047 | 0.086 | 0.006 | 2.49 |
| hard | + 200 LoRA steps | 0.016 | 1.150 | −0.006 | **0.25** |

- With soft labels Kev-0.8B learns the location (mean slope 1.00) but not the width (width slope 0.11): under the pre-registered rule (spec §5.7, `p3_rule_v1.yaml`) this DRYRUN would **fail E0**. The hard-label contrast collapses the width (ratio 0.25), as the spec expects.
- The head-fit step is close to a no-op for Kev (the released pointer head trains at lr 2e-5 under the spec §4 policy, P.0 report deviation 5); all learning happens in the LoRA steps.
- E6 (n = 32): A4 width monotonicity 53 % of prompts (pass needs ≥ 95 %): fail. A3: the 2k- and 8k-token history prompts were refused by Kev's strict 1,024-token state limit (`ContextOverflow`), so A3 did not run — the A3 handling for models with a context limit must be decided (truncate the history, raise Kev's training-context state limit, or record "refused"). A1/A2 not applicable (no packing on the hybrid base); A5 only for the bin-token family.

## What this means for Phase 5 (decisions before the evidence run, not taken here)

These are DRYRUN numbers from one configuration; nothing was tuned in response, and the frozen rule is unchanged. Before the authorized P.3a run the author should settle: the E0 head-fit design (released heads at 2e-5; StartLux softmax-12 has nothing trainable in the head fit), whether 200 LoRA steps at the spec lr are the intended budget for the width test, and the A3 policy for context-limited models. Changing any of these after seeing DRYRUN numbers is itself a decision for the author (pre-registration).

## GPU use

Two leased runs, 07:08:18–07:14:58 UTC (≈ 6.6 min).
