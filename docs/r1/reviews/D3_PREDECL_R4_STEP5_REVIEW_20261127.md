# D.3 pre-declaration revision 4, independent step (5) review

**Task:** `local/20261127-16`. **Reviewed source:** `c025ee244a4e8b1461d16d8e6ae17abcf431713e`.
Independent tier-E reviewer (Codex, 27 Nov 2026), separate from the local worker who prepared the unit. Scope is
the complete revision 4 declaration, pinned analysis and synthetic tests under R1-D3-PREDECL-R4 (2), with
production interface checks for the declared outcome. Reference for the diff-only re-check is
`bd406db9d03f3bbdf3471431d1af96748e1f9556` and its accepted revision 4 review.

**Full step (5): NOT ACCEPTED.** The terminal incumbent can be lost on the harness path. The replicate path
can produce two valid but different audits at W, which the table builder and analysis refuse. Keep
`frozen: false` and hold D.3 evidence launch. Approval fields and publication are with the coordinator.

## Blocking findings

1. **G1 harness campaigns can audit the wrong primary incumbent.** Declaration §7.1 names the last kept
   configuration, including a keep on the final trial. The recorder saves the pre-decision incumbent at E1
   (`r1/c3/d3/snapshots.py:312–331`); writing final at W copies the earlier w20 snapshot, and writing final
   below W uses the stored trial state (`:503–525`). The campaign wrapper calls the recorder after the
   harness returns without supplying the terminal incumbent (`r1/c3/d3/campaign_chunk.py:231–239`).
   An independent run of the pinned harness campaign control flow with a scripted manager and a synthetic
   worker used monotonically improving metrics and the default keep decision. The ledger kept trial 20 at
   W and trial 7 at an early call cap. In both cases the recorded final config differed from the restored
   node's actual terminal config. At W the actual config hash was
   `4b1b4f8dcc271f804508a0e122a570b3f3c14b78527b849ac50eeb69eb414cfb` and the recorded hash was
   `a12ae00c87ecb01463f2b10a59e7699166f10523f58d38b5f983c4c3adfa9185`. The roles of the
   hashes reversed at the early cap. Revision 6c §4 explicitly left the harness 5b path in place.
   This affects the primary outcome and can also make G7's required last-keep audit disagree with the final audit.
2. **G1/G6 can produce a legitimate replicate last keep that G7 and analysis reject.** The replicate recorder
   writes a w20 snapshot before the decision (`snapshots.py:412–427`), while the loop keeps the new config and
   writes a distinct post-decision final (`replicate_campaign.py:282–285,323–329`). Revision 6c §4 and its
   review explicitly distinguish these records. G6 audits both when the configurations differ
   (`r1/c3/d3/audit.py:317–335`). Independently ran the actual FIXR3 loop with one synthetic early failed replicate
   and increasing paired metrics. It reached W=20 and kept its last proposal. The w20 snapshot had configuration
   `X = 5` and synthetic audited `y_raw = 0.600`; the final record had `X = 6` and `y_raw = 0.700`.
   G7 refused the pair with “the snapshot audit is the final audit (one canonical audit)”
   (`r1/c3/d3_outcome_table.py:224–228`), and the pinned analyser independently refused the populated synthetic
   table with “y_raw_w at w = 20 must equal y_raw” (`r1/c3/d3_analysis.py:327–336`). Neither guard can choose
   the scientific definition by its implementation.

The signed text at `bd406db9` already requires the primary incumbent from the last keep (§7.1) and equality
between reported Y(20) and terminal Y for W=20 (§7.5(a), §8). R1-D3-OUTCOMES2 also preserves the primary
outcome and calls for the incumbent after the w-th charged run. The coordinator should route a tier-E G1/G6/G7
correction that proves the terminal record against the last keep at W and at an early cap, and uses that
post-decision audit as the canonical reported Y(20) if W is reached. Preserve the pre-decision snapshot and its
provenance as a distinct replay record. A proposal to publish a distinct pre-decision Y(20) under the same
curve changes the signed equality and needs an author row. Re-review the complete assembly with final-charge
keep and no-keep cases on both runner routes, the declared fresh audit seeds, and a full suite comparison
for any code changes before completing step (5). The screening measurement and its disposition retain their
prerequisite under R1-D3-ORDER and R1-SCREEN-MEASURE.

## Diff-only re-check

**ACCEPTED for binding changes only.** The signed-source declaration SHA-256 is
`bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769`. Its diff to the reviewed declaration
covers the harness/verify allocation, G2 fit receipt and hash, gate-report source and key, and SMAC3 version.
The analysis and test bytes are identical to the signed-source revision. The declared arms, paired design,
Holm families, readings, one-hardware-class pairing, whole-chunk retries, literal shared-card rule, and
every-kept-incumbent audit requirement are preserved. Item 16 remains open as authorized.
`git diff --check` passed on the declaration, script and tests. This scoped verdict does not close step (5).

| Binding | Check |
|---|---|
| Reviewed declaration | SHA-256 `142ea688ff62736216dc6c77328f186efb7801e8427ac97687f999a37045f663` |
| `r1/c3/d3_analysis.py` | SHA-256 `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce`, equals §§9/14 |
| `r1/tests/test_d3_analysis.py` | SHA-256 `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4`, equals §§9/14 |
| Verify seeds | Harness `9bb416805175149eb87b71f28d77530572aa4bce`; checker `e44d966f201d15aa627d5399ca2fe7ada0e15958`, SHA-256 `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2` |
| Reviewed G2 constants | SHA-256 `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`, equals §§5.0/14 |
| Gate-report utility | `r1/c3/d3_gate_output.py` fixes `results/r1/evidence/d3_offline_online_utility/gate_utility.json` and `per_node_utility`; its A2/A3/A5 node values match the shape expected by the pure analysis helper |
| HPO-REF | `r1/c3/d3_hpo_ref.py::SMAC_PINS` pins `smac==2.4.0`, `ConfigSpace==1.2.2` and `scikit-learn==1.6.1`; all seven node config bytes match the prior sweep-2 harness pin |

The independent namespace command returned PASS for base 20000, two pairs at indexes 1–80, 160 seeds in
20010–20801. Running `d3_analysis design` reproduced 126 paired instances, df 119, and the normal reference
0.3185745 for D.3a and 0.3044507 for D.3b without A6. Synthetic tests passed, **137 tests and 18 subtests**,
with the pinned harness source and the published noise-floor constants. The tested files were
`test_d3_analysis.py`, `test_d3_verify_namespaces.py`, `test_d3_g1_snapshots.py`,
`test_d3_g1_replicate.py`, `test_d3_audit_g6.py` and `test_d3_outcome_table.py`.
The focused tests cover the separate contracts; the targeted cross-unit reproductions expose their mismatch.
No real campaign or server job ran. No gate output, label, sealed partition or evaluation value was opened.
