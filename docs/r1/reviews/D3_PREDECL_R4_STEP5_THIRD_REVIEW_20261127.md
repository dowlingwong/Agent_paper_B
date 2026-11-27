# D.3 revision 4 independent step (5) review after integration

**Task** `local/20261127-22`. **Published base** `e92f3c7389e06347a0ff78f5f68971024133c670`.
Fresh independent tier-E reviewer. I did not write revision 4, its analysis or tests, or the G1/G6 integration.
I reviewed the published declaration and exact analysis/test pins and performed a separate binding-only
comparison against `bd406db9d03f3bbdf3471431d1af96748e1f9556`.

- **Full step (5) — ACCEPTED.** The two previous production interface failures are resolved. Seven synthetic
  cases run through the G1, G6 and G7 production paths and the pinned analysis command.
- **Binding-only diff — ACCEPTED.** The differences fill the reviewed harness, verify-seed, G2 artifact,
  SMAC3 and offline–online utility bindings. The script and its pinned tests are byte-identical to the
  previously accepted revision. The signatory and freeze time still require the coordinator's final fill
  and independent diff re-check under R1-D3-PREDECL-R4 (2).
- **Freeze remains pending.** R1-D3-ORDER and R1-SCREEN-MEASURE-SIGNATURE put screening and any
  decision-node SHARED disposition before binding freeze. The recorded original attempt stopped with
  zero runs. Complete the re-issued measurement and record its disposition first.

## Seven-case replay

I reused the published synthetic scenario drivers for the scripted proposals, worker metrics and audit
metrics. Each case ran the pinned harness campaign or actual FIXR3/EGATE engine in G1. The replay
reloaded the original G1 summary and G6 projection from the production disk paths. It verified every
kept configuration hash against its G6 audit on seeds 6701–6710 and derived the last improvement from
the ordered audit gains. It then supplied the unchanged original summary and audit rows to production
`assemble.build` and G7. Exact stage coverage is required by the analysis. Each 882-row synthetic table
fills the other 881 arm/node/seed cells with re-keyed copies of that case's production records. The
original case is excluded from this scaffold and is verified unchanged after serialization and reload.
The CLI rechecked the draft declaration hash, pinned noise source and analysis hash for all seven tables.

| Case | Runs | Calls | Keeps | Last keep | Last improving run | Final raw gain | Run-20 raw gain |
|---|---:|---:|---:|---:|---:|---:|---:|
| Harness, terminal keep | 20 | 20 | 20 | 20 | 19 | 0.00 | 0.00 |
| Harness, terminal discard | 20 | 20 | 19 | 19 | 19 | 0.05 | 0.05 |
| Harness, final keep at call cap | 7 | 80 | 7 | 7 | 7 | 0.05 | null |
| FIXR3, terminal keep | 20 | 7 | 6 | 20 | 20 | 0.70 | 0.70 |
| FIXR3, terminal discard | 20 | 7 | 5 | 17 | 17 | 0.60 | 0.60 |
| EGATE, terminal keep | 20 | 8 | 2 | 20 | 20 | 0.80 | 0.80 |
| EGATE, terminal discard | 20 | 8 | 1 | 1 | 1 | 0.10 | 0.10 |

For six cases that reached W, the final configuration and canonical run-20 audit matched. The
pre-decision snapshot stayed separate and its hash differed exactly when the last run produced a keep.
The early-cap case retained the seventh keep and emitted no run-20 audit. The harness terminal keep
returned to the starting bytes, so its final audit gain was zero under §7.1 despite an improvement
at the previous keep. The 882-row scaffolds exercise schema and analysis coverage and provide
no campaign-effect estimates.

## Declaration, analysis and bindings

I checked the seven D.3a arms, the unconditional A3/A5 D.3b continuation and the conditional A6
entry, the 126 paired instances and one GPU model per instance, the 20-run and 80-call caps,
the fresh paired audit, Holm families and directional readings, and the separation of HPO-REF
and secondary outcomes. The published harness node configs match the former pin. The pinned
design command reproduced 126 instances, 119 degrees of freedom, and normal first-step detectable
differences of 0.3185745113 for D.3a and 0.3044506916 for D.3b without A6 in sd(D) units. The
namespace command returned PASS for 160 seeds in 20010–20801. The utility producer's constants
match the declared path `results/r1/evidence/d3_offline_online_utility/gate_utility.json` and
key `per_node_utility`. The HPO-REF package contract binds `smac==2.4.0` and its companion
requirements in `SMAC_PINS`.

| Binding | SHA-256 or commit |
|---|---|
| Previously reviewed declaration | `bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769` |
| Current declaration | `142ea688ff62736216dc6c77328f186efb7801e8427ac97687f999a37045f663` |
| Pinned analysis | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| Pinned analysis tests | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |
| Harness | `9bb416805175149eb87b71f28d77530572aa4bce` |
| Verify-seed checker | `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2` |
| Reviewed G2 constants | `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| Gate utility producer | `59d15d465edca1fb274cfe715653473949f8abeeb9d79adf9d8540ea471a77ab` |
| G6 production audit | `f17d8c15cac5e738cfc2de851c801f008eb55a047701c86540676a6aedfa346f` |
| G7 outcome builder | `a9ce5d904c711642932c4b393f2d1f52e00e7f59e1f6d20cd1ea530fd7fba3ca` |
| Production assembler | `7671543bac1b081ac61c5bdaa32433b5dae886c928ea37080596f82d1d96444a` |
| Synthetic replay script | `e53cdbb53932e96c5255a37150912a685fa110041e847443526350e82d4f77b6` |
| Seven-record stdout | `5f907f74353fe51cf7264d108b468d362d65d90210144b52e17d2438b7b2e06f` |

The focused run passed **158 tests and 18 subtests** with Python 3.12 and NumPy 2.4.4. It covered
D.3 analysis, verify namespaces, G1 snapshots and replication, G6 audit, G7, integration and the
gate-output unit on synthetic fixtures. The scoped `git diff --check` passed. Run the accompanying
replay from the reviewed checkout with Python 3.12, `PYTHONPATH="$PWD"`, `AR_HARNESS_ROOT` at the
exact clean harness pin and one argument giving a new scratch output directory. No campaign evidence,
stored gate output, credentials or sealed files were opened. No live job was submitted.

## Authorization dependencies

The accepted declaration and analysis prescribe actual numbers for §8's `infra_attempts` and
`proposer_gpu_seconds`. At this base both chunk routes omit the optional attempt-count argument,
so the summary writes 1 even after a whole-chunk retry unless another unit passes the attempt
ledger through. The summary fixes GPU seconds at 0.0, which the numeric guard accepts and the
analysis includes in the arm mean. Those values were suitable for the engineering tests. For
D.3a/b evidence, the coordinator should require a reviewed producer for actual attempt counts
and GPU seconds, or obtain an author-approved protocol change before proceeding with unmeasured
compute. The current numeric schema has no unmeasured sentinel. This is a stage authorization
and evidence-accounting dependency. The declaration and its pinned analysis already specify
the required outcomes.

After screening and the signature metadata re-check, the coordinator freezes the exact document
and binds its hash in the appropriate authorization. Per-arm smoke still needs its reviewed
placement and execution conditions. D.3b separately needs the frozen A3/A5 artifacts, an A5
sidecar that passes the launch checks and a signed D.3b note. The image choice remains the
explicitly open §13 item 16. A6 additionally needs the gate pass, its own eligible frozen
record and the D.3b note's entry bit. This replay exercised the declared seven terminal
cases and the D.3a schema. It supplies no D.3b GPU or sidecar readiness finding.

- Full step (5) verdict **ACCEPTED**
- Binding-only diff verdict **ACCEPTED**
