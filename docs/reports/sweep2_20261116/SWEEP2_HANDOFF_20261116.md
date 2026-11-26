# Sweep-2 cluster work — branch/commit hand-off (16 Nov 2026, 23:55 CET)

Authority: `main` = `author-decisions-20261116b` @ `025bfc16` (fast-forwarded by the author); work plan
`docs/runbooks-16nov` @ `b3289232`. P1/P2 PASS; P3/P4/P6/P7 open (see launch checklist). Nothing has launched EVIDENCE.

## Branches to merge/keep (reviewed unless noted)

| branch | tip | content | review / state |
|---|---|---|---|
| `sweep2-main-20261116` | `e17b0437`+ | S2-C2 sweep wrapper (32k settings, CPU class, noise pin `--e1-summary`, liveness job mode, sweep-1 collection gates, evidence-preserving STOPs, tar transfer/seal), 32k smoke results + sealed evidence pointer, launch checklist, this hand-off, S2 documents | S2-C2 round-5 review **ACCEPTED**; worker PATH fix + per-(node,mode) worker-success gate (37 tests); **32k smoke worker bug found** (no training); re-measurement smoke 759743/759744 idle; layout void |
| `s2c3-driver-fix-20261116` | `882362a6` | R1-S2C3-DRIVER: TASL-independent, declared-input, additions-only-shim replay driver for the S2-C3 L40S deployment check; 25/25 declared inputs; 5-gate preflight; 3 specs at 32k layout; operator follow-up runbook | round-2 review **ACCEPTED for the 3-job ENGINEERING run**; worker PATH/audit fix; jobs 759736-759738 cancelled (pre-fix code) — resubmit after the re-measured smoke |
| `s2c3b-fix-20261116` | `0f5c3fdd` | S2-C3b: pick D28 liveness on all 8 nodes + prompt-length re-measure with the pick tokenizer; accepted 32k layout; `liveness_seed_policy=sweep1_d28_reuse` disclosed; assets staged on deepthought, dry-run rc 0 | round-2 review **ACCEPTED for an ENGINEERING run**; worker PATH/audit fix (130 tests); restage assets after the re-measured smoke; run ordered after S2-C3 |
| `s2c5-switch-20261116` | `84a0dc30` | S2-C5 real-submission switch: two-key disabled gate, committed author note under `docs/r1/authorizations/`, run-id/digest/JDL-sha/32k binding, P1–P7 all PASS, no B.2, D8 lock | review **ACCEPTED, remains DISABLED**; 5 tests; no keys/note exist |
| `e1-openml-20261116` | `5d73550a` | R1-E1-OPENML audit: sweep 1 recorded no OpenML data-file/cache hash → **identity UNPROVABLE — STOP for author**; docs only, driver unchanged | independent review **ACCEPTED** |
| `ops-e1-replay-20261116` | `fc7d8e4e` | e1 replay STOP report + independent review | STOP at the pre-declared OpenML hard gate, review accepted |
| `g1b-noise-20261116` | `231b6693` | G.1b noise-floor job prepared (D21 552 runs/node, placeholder-refusing, dry-run rc 0, 23 tests) | prepared only; waits Ada G.0 census; provisional cap 100 GPU-h |
| `htc-image-v2-20261115` | `cbd0238e` | image v2 CI run 7 success (gpu `b1144ece…`, cpu `08a36eff…`); v1 remains the frozen/used digest | not switched; I2/I3 on v2 still pending (lower priority) |

## Environment blocker (current)

NEMO2 `g36xx` L40S nodes are **absent from the pool** (all-GPU query: H200 `g44xx`, deepthought2 portal L40S, TITAN;
no `g36xx`). The 3 queued S2-C3 jobs remain idle; S2-C3b is staged but must run after S2-C3. Operator follow-up
commands for seal + compare are in `S2_OPERATOR_FOLLOWUP_20261116.md` on the driver branch. No action can make the
nodes appear; retry/monitor later.

## Author decisions outstanding

1. **P3** `docs/r1/authorizations/c3_sweep2_<date>.md` with the fields in the launch checklist (incl. P1–P7 evidence,
   v1 digest freeze, 32k layout, no B.2 audits, D8 lock).
2. **P7** confirm the v1 digest `69b06b35…` freeze (or approve v2 with I2/I3).
3. **P6** decide when S2-C5 may be enabled for the authorized run id (`--enable` + `S2C5_ENABLE_REAL=1`).
4. **e1** choose: 4 non-OpenML cases only (protocol/authorization amendment), R1-MAIN-PROPOSER (g)2 exception,
   amended identity standard (author row + review), or leave e1 at STOP.
5. Allow the queued S2-C3 jobs to run once L40S returns, then S2-C3b; afterward P4 evidence review.

No EVIDENCE launch; no B.2/audit; no 7001–7010/8001–8010/9001–9303 seeds; no label reads; main untouched by the
cluster work; no force push/delete.
