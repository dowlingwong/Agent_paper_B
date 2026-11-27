# Draft C3 preregistration amendment — signed G.5 tail laws

Prepared for `local/20261127-09`, consumer unit. R1-G5-TAILS-CONSUMERS (3) authorizes the requested
scope. This draft awaits independent review of the exact implementation and coordinated publication
of the amendment and its checks. The original preregistration remains the record of the 21 November freeze.

## Change to the soft-target rule

In §3 and the builder binding for §6, use the existing Gaussian soft-target integration for T0 and
for each T1 Gaussian node. For a T1 Student-t audit label, integrate the Student-t over the same bins
at the same location, with its assembled degrees of freedom and scale `s * sqrt((nu - 2) / nu)`.
Here `s = sigma_node / sqrt(k_label)` in raw units. This preserves the standard deviation, per
R1-G5-TAILS-CONSUMERS. R1-G5-TAILS declares ν = 5 for `mlab_ogbn_arxiv` and
`mlgym_breakout_minatar`. The initial other five nodes use Gaussian. Autoresearch follows its bound
completion record. A later added node follows its approved note. Both require a source-bound
declaration in the T1 context. Refuse missing or conflicting bindings before building targets. Inert and divergent labels retain
their existing treatment. The actual label seed count, the preregistered split, and the existing
oracle, utility, comparisons, gate inference and release order retain their existing definitions.

The SFT G.5 train/dev reader, that same source in the arms-frozen training and calibration,
and the gate's oracle and A2 fit must compute the same bins. On a declared Student-t node missing or
contradictory label metadata stops those consumers. The generic T0 SFT reader remains on its existing
schema. The changes apply before T1 SFT, arms freeze and any gate read.

## Candidate bindings

| Role | Path | SHA-256 |
|---|---|---|
| Original frozen preregistration | `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md` | `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5` |
| Original builder | `r1/c3/gate_input_builder.py` at the original freeze | `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808` |
| `gate_sha256` | `r1/c3/gate.py` | `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23` |
| `gate_input_builder_sha256` | `r1/c3/gate_input_builder.py` | `7cb9b4a95ea185b971ed7ccfacf55412ba0b4a006e43fa0ab6fae9ca8a9e7da4` |
| `labels_sha256` | `r1/c3/labels.py` | `8f2d55696a92e3c0c0df3f192e134530bf48ee07b3f7c23dd8c5fa86d1398792` |
| `arms_freeze_sha256` | `r1/c3/arms_freeze.py` | `7f0d7b6072f817018a1f8e1ff3bcb1be127d1eb483428682e50208fd3a58a603` |
| `arms_constants_sha256` | `r1/c3/arms_constants.py` | `617d33791b6095be6d10a71e73f60a55e003944d6ae94b2a2525def22a8968b0` |
| `sft_data_sha256` | `r1/c3/train/sft_data.py` | `17b88bffd079295f38f2c9177410cdad32ac5978af99b86d8c68a08bd105167f` |
| `fold_analysis_sha256` | `r1/c3/fold_analysis.py` | `fb7193900276071d2dc0046098d805c4746dfe80641b57d8042728f2b87497f3` |
| `release_sha256` | `r1/c3/release.py` | `8b53f117a16ab9bea6980ea46781cb395cef17182df0ad74abb8dff16c3eb243` |

## Binding and review before publication

After independent acceptance, the coordinator publishes this amendment as
`docs/r1/authorizations/C3_SWEEP2_G5_TAILS_AMENDMENT_20261127.md`, sets the signature fields, and records this exact form in an author
decision table in PLAN §10. The digest is that of the final frozen amendment, and the implementation
commit is a published ancestor containing the code pinned above.

`R1-G5-TAILS-PREREG-AMEND` reads:
> Use the reviewed G.5 tail-law amendment `docs/r1/authorizations/C3_SWEEP2_G5_TAILS_AMENDMENT_20261127.md` sha256 `<amendment digest>` with implementation commit `<implementation commit>`.

The resolver verifies the identical published author row, the amendment digest, the original frozen
preregistration and builder, and the code pins at both the implementation commit and the current
checkout. Keep the original preregistration and receipt bytes. Historical T0 train/dev rows verify
against their original binding and cannot publish a fresh release under it from the amended checkout.
The first T0 test release and new T1 releases cite the effective amendment. An arms-frozen record
continues to cite the original preregistration and adds the effective amendment as
`g5_tail_amendment` with its path and digest. The shared check applies to `arms_constants` and
`d3_constants`; complete the pending G2 fit from its reviewed original binding before swapping the
working pin. The gate statistic and verdict code retains its existing SHA.

For noninitial T1 nodes bind the frozen context with `gate_input_builder.bind_g5_tail_laws` before
constructing inputs. The loader checks the already-verified release receipt against the unsealed
table's build SHA and proposals digest. This carries the completion/addendum declaration into
`Tier1.tail_laws`; folds preserve the node subset. SFT accepts the same bound metadata through the
G.5 table directory. A mismatched or missing declaration stops the target computation.

The signed release conditions, D8 gate guard, reading order and one-time gate read continue to apply.
The candidate is a code and amendment draft. Keep T1 SFT, arms freezing and the gate read pending
until the published binding passes its checks.

```
frozen: false
base_preregistration_sha256: aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5
original_gate_input_builder_sha256: f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808
gate_sha256: a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23
gate_input_builder_sha256: 7cb9b4a95ea185b971ed7ccfacf55412ba0b4a006e43fa0ab6fae9ca8a9e7da4
labels_sha256: 8f2d55696a92e3c0c0df3f192e134530bf48ee07b3f7c23dd8c5fa86d1398792
arms_freeze_sha256: 7f0d7b6072f817018a1f8e1ff3bcb1be127d1eb483428682e50208fd3a58a603
arms_constants_sha256: 617d33791b6095be6d10a71e73f60a55e003944d6ae94b2a2525def22a8968b0
sft_data_sha256: 17b88bffd079295f38f2c9177410cdad32ac5978af99b86d8c68a08bd105167f
fold_analysis_sha256: fb7193900276071d2dc0046098d805c4746dfe80641b57d8042728f2b87497f3
release_sha256: 8b53f117a16ab9bea6980ea46781cb395cef17182df0ad74abb8dff16c3eb243
signed_by: PENDING
frozen_utc: PENDING
```
