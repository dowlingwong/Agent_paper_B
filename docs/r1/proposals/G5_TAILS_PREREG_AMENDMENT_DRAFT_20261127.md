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
completion record. A later added node follows its approved note. Inert and divergent labels retain
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
| Gate statistic and verdict code | `r1/c3/gate.py` | `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23` |
| Revised builder | `r1/c3/gate_input_builder.py` | `ac7fcc3a2ddedbd034dd8364d5d181adc81bd18d3705a5572bcc420538ae231f` |
| Label law and bins | `r1/c3/labels.py` | `647bbf9c0e7cfe90dda9f16f6c323af2263745cbe6b8d1861a0c314a08200c4f` |
| Arms-frozen training consumer | `r1/c3/arms_freeze.py` | `ab1619b58bcd4d1960e338717ed61329882e959e7800e807d00bb2ff6e2ebee8` |
| T1 SFT label consumer | `r1/c3/train/sft_data.py` | `881f0590f4b109ccbd7d81c71fbcb15ce2ad688ae3ed6b62fdfba66282b9d637` |

## Binding and review before publication

Publish the exact accepted amendment with its SHA-256 and the reviewed implementation commit under
a PLAN §10 row. Keep the historical preregistration and older receipt bytes. Add a reviewed
binding check that selects the new builder only from the published amendment, verifying the original
preregistration digest, exact published amendment digest, code commit and all five code pins above.
The release and arms-frozen verification must agree on the effective gate/builder binding. Existing
T0 train/dev receipts still verify against their historical preregistration, original builder and
release row. T1 and any later gate or arms-frozen records cite the effective amendment binding in
addition to the original preregistration. The old check continues to refuse the revised builder
until the new binding is published. Include both old-receipt and new-publication cases in the
binding review and the base/tip full suite, using synthetic metadata and no sealed read.

The signed release conditions, D8 gate guard, reading order and one-time gate read continue to apply.
The candidate is a code and amendment draft. Keep T1 SFT, arms freezing and the gate read pending
until the published binding passes its checks.

```
approved: false
base_preregistration_sha256: aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5
original_gate_input_builder_sha256: f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808
gate_sha256: a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23
gate_input_builder_sha256: ac7fcc3a2ddedbd034dd8364d5d181adc81bd18d3705a5572bcc420538ae231f
labels_sha256: 647bbf9c0e7cfe90dda9f16f6c323af2263745cbe6b8d1861a0c314a08200c4f
arms_freeze_sha256: ab1619b58bcd4d1960e338717ed61329882e959e7800e807d00bb2ff6e2ebee8
sft_data_sha256: 881f0590f4b109ccbd7d81c71fbcb15ce2ad688ae3ed6b62fdfba66282b9d637
```
