# P.4 E0: the evidence and a proposed criterion (level 2, for the author)

Coordinator, 28 Nov 2026. Under R1-P4-E0-REPEATABILITY a change to the E0 criterion comes to the author with the repeat evidence. Records on `main`:
first same-code runs (`972f0e70`, `7716cfce`), repeats `989e8f22` (`docs/r1/reports/trackp_p5_e0_repeat_20261128/`, review ACCEPTED). All four runs: paper
`c80f83bc`, identical config content per host, data `b963be2d…`, Kev-0.8B, seed 0, empty cards; none bit-identical run to run.

| Run | RPS | width slope Δ / mean slope Δ vs the other host's run |
|---|---:|---|
| Ada first | 1.4384e-4 | all cross-host and within-host slope Δ ≤ 0.034 (tolerance 0.05): **slopes pass everywhere** |
| Ada repeat | 1.5773e-4 | |
| TASL-7 first | 1.1638e-4 | |
| TASL-7 repeat | 1.4678e-4 | |

- **Within host, same inputs:** Ada 1.39e-5 (9.7 %), TASL-7 **3.04e-5 (26.1 %)**. The 10 % relative RPS tolerance is below TASL-7's own run-to-run noise:
  TASL-7 fails E0 against itself.
- **Cross host:** host means 1.508e-4 (Ada) vs 1.316e-4 (TASL-7), difference 1.92e-5 (12.7–14.6 %), about 1.15 pooled within-host SDs (1.67e-5, n = 2
  per host). Which pair is compared decides the verdict (firsts: −23.6 %, fail; repeats: +7.5 %, pass). Nothing here separates a host effect from noise.
- Reading: RPS at ~1e-4 is dominated by non-deterministic GPU training noise; the slopes are stable. The E0 question (does the Ada runtime reproduce the
  reference host) cannot be answered with a 10 % relative band on one run per host.

## Proposed criterion (replaces the 10 % relative RPS band for cross-host E0; slopes unchanged)

Ada passes E0 if (i) both slopes pass at absolute 0.05 for every Ada vs TASL-7 pair, and (ii) the difference of the host mean RPS is no larger than
**3.04e-5**, the largest within-host same-code RPS difference already observed (TASL-7's repeat pair).

| Option | How it is applied | Cost |
|---|---|---|
| **A (recommended)** | Rule fixed now; tested on **fresh** runs: two more same-code runs per host (runs 3–4), compared with the existing comparator plus this rule. The margin comes from within-host data already seen; the cross-host test uses only new data, so the verdict is not chosen after seeing it | ≈ 2.2 GPU-h, ≈ 1.5 h wall (Ada and TASL-7 in parallel; both cards free) |
| B | Same rule applied now to the four existing runs: Ada passes (1.92e-5 ≤ 3.04e-5; slopes pass) | none; but the rule is set after the cross-host result is known |
| C | Slopes only as the E0 criterion; RPS reported descriptively | none; drops the RPS check entirely |

Why A: the rule is the natural one (a host difference no larger than a host's own noise), and fresh runs make the verdict independent of the data that
suggested it, for 1.5 h on idle cards. If A fails, the difference is a runtime finding and comes back to you. The phase-1 note still needs its reviewed
timing disposition (R1-P4-PHASE1-SIGNATURE) after E0 passes.

Reply: **"签 E0 新判据 A"** (or "E0 新判据 B" / "E0 新判据 C").
