# D.3 revision 4, independent step (5) repeat

**Task** `local/20261127-17`. **Published source** `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536`.
Independent tier-E reviewer, separate from the authors of the declaration, analysis, tests and G1 repair.
Reviewed the complete declaration, its pinned analysis and tests, and the production interfaces used by the two
reproductions in the previous step (5) review. The diff-only reference is the accepted revision 4 at
`bd406db9d03f3bbdf3471431d1af96748e1f9556`.

- **Full step (5) — NOT ACCEPTED.** The production D.3a/b audit and outcome-table interfaces cannot yet assemble
  the required row from the campaign's records. The synthetic reproductions passed through G7 and the pinned
  analysis when the review fixture supplied the missing summary fields and kept-incumbent audits.
- **G1 terminal repair — PASS.** Both earlier terminal-outcome defects were resolved at this source.
- **Binding-only diff — ACCEPTED.** The compared declaration changes are binding fills allowed by
  R1-D3-VERIFY-SEED and R1-D3-PREDECL-R4 (2). The analysis and its tests are byte-identical to the reviewed revision.

## Blocking production checks

1. **G1 summaries cannot be read by G7.** Both `r1/c3/d3/campaign_chunk.py::run_chunk` and
   `_run_replicate_chunk` write `summary.json` with schema `r1_d3_campaign_summary/v1`. For each tested G1
   output, passing that record to `r1/c3/d3_outcome_table.py::build_row` gives
   `a campaign summary must hold exactly ...`. G7 requires the stage and arm, start and final config hashes,
   last keep, mechanism counts, compute fields and attempt accounting. The current summaries carry run/call
   counts, snapshot references and other chunk metadata. No D.3a/b producer or adapter for the G7 shape is on the
   reviewed source.
2. **G6 does not produce the per-keep inputs required by G7.** `r1/c3/d3/audit.py::audit_campaign` reads the
   four curve snapshots and the final snapshot and emits `Y_w.jsonl` and `Y_final.jsonl`. It supplies no separate
   per-keep records. Even with a fixture-provided complete summary and normalized G6 rows, G7 refuses all seven
   cases with `one keep audit per keep is required (§7.5 (d); §13 item 25)`. This check enforces the author's
   settled definition of `last_improving_run`. HPO-REF supplies an adapter and its own persisted keep snapshots
   in `r1/c3/d3/hpo_runner.py`; that path is scoped to the HPO-REF stage.

Keep the declaration at `frozen: false`. Route a reviewed integration unit that persists each kept configuration
at its charged-run count, audits each through G6 with the declared seeds and cache, and builds the G7-shaped summary
and audit rows directly from the production records. Re-run both G1 routes and an early-cap case through that unit,
G7 and the pinned analysis using synthetic inputs. A code unit requires its full-suite base comparison. Repeat the
full step (5) review and its independent binding-diff check. The separate screening measurement and disposition
continue to govern freeze under R1-D3-ORDER and R1-SCREEN-MEASURE.

## Synthetic reproduction results

The harness route ran the real campaign loop at harness `9bb416805175149eb87b71f28d77530572aa4bce`. The
replicate route ran the actual FIXR3 and EGATE engines through `run_chunk`. The review supplied scripted proposals
and synthetic worker and audit metrics. The early harness case spent the declared 80 calls and charged seven runs,
with the seventh keep on proposal 80. Every G6 primary audit used the declared seed block 6701–6710. For W=20,
G6 aliased the primary audit to the canonical w20 audit by config hash. The pre-decision record remained in
`w20_pre.json` and had a different config hash exactly in the terminal-keep cases.

| Case | Final charged runs | Last keep at charged run | Keeps | Synthetic primary `y_raw` | Synthetic `y_raw_w["20"]` |
|---|---:|---:|---:|---:|---:|
| Harness, terminal keep at W | 20 | 20 | 20 | 0 | 0 |
| Harness, terminal discard at W | 20 | 19 | 19 | 0.05 | 0.05 |
| Harness, terminal keep at early call cap | 7 | 7 | 7 | 0.05 | null |
| FIXR3, terminal keep at W | 20 | 20 | 6 | 0.70 | 0.70 |
| FIXR3, terminal discard at W | 20 | 17 | 5 | 0.60 | 0.60 |
| EGATE, terminal keep at W | 20 | 20 | 2 | 0.80 | 0.80 |
| EGATE, terminal discard at W | 20 | 1 | 1 | 0.10 | 0.10 |

The harness's first case ended on a keep that returns the fixture configuration to its starting bytes, so the
canonical primary `y_raw` is zero by §7.1. The table builder and analysis CLI accepted each corresponding full
882-row synthetic design when the fixture bridged the two blocking interfaces. The reproduced old mismatches
were therefore absent. Both interface refusals and all seven fixture-assisted passes appear in the saved stdout.
Run the accompanying `step5-reproduce.py` from the reviewed source with `AR_HARNESS_ROOT` pointing to a clean
checkout of the pinned harness, a fresh `TMPDIR`, and `PYTHONPATH="$PWD"`. Use `python -B`. The reviewed probe
SHA-256 is `52f639707f47faaa856b0ddd46160ba22151a5ba93e91ad3a346137521be5dfd`. Its saved stdout is
`step5-output.jsonl`, SHA-256 `45bd71b40d63d7e265402373c6ad4a2baf67821bb026033f69073fd7e1a3f551`.

## Declaration, analysis and diff checks

The review checked the seven-arm D.3a and unconditional A3/A5 D.3b scope, the conditional A6 rule, 126 paired
instances, matched W=20 and call cap 80, declared seed blocks, Holm families, the declared outcome readings,
HPO-REF separation, hardware and whole-chunk retry rules, table guards and input restrictions. The binding-only
diff changes the harness pin and verify-seed allocation, constants receipt and hash, SMAC3 package binding, and
offline–online gate-output file and key. The compared arm definitions, outcome definitions, constraints and
analysis were preserved. The unresolved sidecar-image choice remains the allowed item 16.

| Binding | Checked SHA-256 or pin |
|---|---|
| Reviewed signed-source revision 4 | `bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769` |
| Current declaration | `142ea688ff62736216dc6c77328f186efb7801e8427ac97687f999a37045f663` |
| Analysis, §§9/14 | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| Analysis tests, §§9/14 | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |
| Verify seed checker `e44d966f201d15aa627d5399ca2fe7ada0e15958` | `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2` |
| Reviewed G2 constants, §§5.0/14 | `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| Published G6 audit | `452724ec92b9820ddfb187f2ea4999f3c0bbc6c1241b55f4594b8a4b0cd5a4a3` |
| Published G7 builder | `a9ce5d904c711642932c4b393f2d1f52e00e7f59e1f6d20cd1ea530fd7fba3ca` |
| Gate utility | `results/r1/evidence/d3_offline_online_utility/gate_utility.json`, key `per_node_utility`, as declared by the producer code |
| HPO-REF | `smac==2.4.0`, `ConfigSpace==1.2.2`, `scikit-learn==1.6.1` in `d3_hpo_ref.SMAC_PINS`. The harness node configs are byte-identical to the previous pin |

`git diff --check` passed for the declaration, script and tests. G6, G7 and the analysis bytes match
`c025ee244a4e8b1461d16d8e6ae17abcf431713e`. The independent namespace command returned PASS for verify seed base
20000, pairs 0–1, indexes 1–80 and 160 distinct seeds from 20010 through 20801. The analysis design command
reproduced 126 paired instances, df 119, and normal first-step detectable differences of 0.3185745 and 0.3044507
sd(D) for D.3a and D.3b without A6.

**155 focused tests and 18 subtests passed** with Python 3.13.1, pinned NumPy 2.4.4 and the exact harness source.
The tests were `test_d3_analysis.py`, `test_d3_verify_namespaces.py`, `test_d3_g1_snapshots.py`,
`test_d3_g1_replicate.py`, `test_d3_audit_g6.py`, `test_d3_outcome_table.py` and `test_d3_gate_output.py`.
The gate-output tests used synthetic inputs. No real campaign, scheduler job, sealed-data read or gate-output
read occurred. This delivery records review and synthetic reproductions. Production sources and signed fields
come from the published base.
