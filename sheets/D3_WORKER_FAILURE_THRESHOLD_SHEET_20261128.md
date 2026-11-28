# D.3: the stage worker-failure STOP is based on the wrong memory mode (level 2, for the author)

Coordinator, 28 Nov 2026. Records: P7 at the frozen runtime (`compute-d3a-p7-exact-20261128` @ `db9fb948`; review pending), sweep-2 report on `main`
(`docs/r1/reports/sweep2_20261116/SWEEP2_REPORT_20261121.md`, chunk table), frozen rev 4 (`e091b1b5…`).

**What happened.** P7 at the frozen server settings (`-c 32768`, q8_0 K/V; fits on the 4090, 22.0 GB) charges 50 worker failures in 276 runs = **18.12 %**
(all `invalid_config`), above rev 4's stage STOP of **12.99 %**. The earlier P7 at `-c 8192` gave 12.18 %.

**Why the threshold does not fit.** Rev 4 sets the STOP at "sweep 2's pooled 7.99 % + 5 pp". That 7.99 % pools **both** sweep-2 memory modes. D.3 runs
`append_only_summary` **only** (rev 4 §2, R1-MINSUB-CHOICES (4)), and in sweep 2 the `none` mode had almost no failures. Rev 4 itself says "the per-mode split
is not on `main`, so the `append_only_summary` value is unknown" (line 106). From sweep 2's own chunk table:

| Sweep 2, same proposer and server settings | failures / trials | rate |
|---|---:|---:|
| all 8 nodes, both modes (rev 4's basis) | 460 / 5,760 | 7.99 % |
| the seven D.3 nodes, `append_only_summary` only | 341 / 2,520 | **13.53 %** |
| `openml_climate`, `append_only_summary` (the P7 node) | 84 / 360 | 23.33 % |

So sweep 2 itself, in the mode D.3 uses, would trip rev 4's 12.99 % STOP; and P7's 18.1 % on `openml_climate` is *lower* than that node's sweep-2 rate. The
failure rate is a property of the memory mode and the node, not a runtime defect. Under rev 4 a D.3a stage would very likely STOP on this rule alone.

| Option | Content | Cost |
|---|---|---|
| **A (recommended)** | **Revision 5**, one change: the stage STOP becomes **18.53 %** = sweep 2's `append_only_summary` pooled rate on the seven D.3 nodes (13.53 %) + 5 pp, the same form as the signed rule, now on the matching mode. Nothing else changes | Rev 5: review, your signature, freeze, step (8) again, the D.3a note rebound. About half a day of agent work, no GPU. No D.3 outcome has been seen; the basis is sweep-2 data already on `main` |
| B | Revision 5 with **per-node** limits: each node's sweep-2 `append_only_summary` rate + 5 pp (e.g. `openml_climate` 28.3 %, `digits_mlp` 5 %) | As A, plus a per-node rule in the analysis code and its tests (tier E) |
| C | Keep rev 4 and launch D.3a; a STOP on this rule is recorded as evidence | No revision; a stage STOP is likely and costs its GPU hours |

Why A: it keeps the rule's signed form (sweep-2 rate + 5 pp) and fixes only its basis, which rev 4 already flagged as unknown. Under A, P7's 18.12 % on
the highest-failure node passes narrowly (18.53 %); the seven-node stage rate is expected near 13.5 %, well inside. B is more precise but adds code and
a per-node rule that sweep 2 never used. C spends GPU hours on a STOP we can predict now.

Reply: **"签 D.3 rev 5 A"** (or "D.3 rev 5 B" / "D.3 按 rev 4 C").
