# G.5 expansion addendum template

Status **draft for `local/20261126-12`**. The G.5 switch has no addendum reader yet. Use one addendum per node after
review of that reader and the node's published G.1b determinism PASS. The coordinator publishes the filled note
under `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>_addendum_<N>.md`. The date identifies the file.

Authority comes from R1-G5-EXPANSION-JOIN, R1-STEP-ORDER (2)(a), R1-G5-S9 and the signed main G.5 note. Bind that
note and spec by exact path and SHA-256. The addendum preserves the published launch implementation, K, campaign
settings, run-budget rule, host/lease checks, schedule, stop rules and release order. Fill only the joining node's
parameters and its prerequisite citations. The G.1b note and spec below are the expansion inputs already on `main`.

```text
approved: false
node: <one node from the expansion G.1b spec>
base_g5_note: <published path and sha256>
base_g5_spec: <published path and sha256>
launch_code: <exact paper.commit bound by the published G.5 note and addendum switch>
g1b_note: docs/r1/authorizations/g1b_x_t1_tasl_20261126.md sha256 16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539
g1b_spec: sweep2/t1_tasl/g1b_tasl_x_spec.json sha256 d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238
g1b_determinism: <published per-node completion record and sha256, determinism PASS>
g1b_noise_floor: <published summary, assembly and authorized runs copy paths and sha256s for D6>
node_spec_entry: <reviewed per-node spec entry path and sha256>
node_bindings: <implementation, node-spec, isolation, environment and data manifest pins from the node's reviewed records>
execution_layout: <node device, CPU set and lease with the published placement and audit checks>
label_tail: <declared law and provenance before assembly, with nu and sd matching for Student-t>
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: <published v2 amendment path and sha256>
supply: <MLGym arms and primary gate, or 1GC separate descriptive output>
projection: <R1-BX-D14-G4B recompute with the joining node, path and sha256>
review: <independent acceptance of the filled addendum and applicable checks>
```

Under R1-G5-S9, `mlgym_titanic` and `mlgym_metamaze` enter the arms and primary gate in suite MLGym after their
G.5 labels and published releases. `gc7rc_etth1` and `gc7rc_forestcover` retain their reviewed CPU-only conditions.
Report their G.5 results per node as descriptive extra tasks, separate from the SFT table, arms and gate.

Before approval, confirm the note and spec publish together with the exact reviewed switch. Independently verify
that a missing or nonpassing completion, unpublished note, changed pin, incompatible CPU placement, wrong split or
1GC supply request is refused. Keep train/dev and test/evaluation partition access under the signed release rows.
