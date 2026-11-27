# Ada P.4 phase-1 probe bindings

The figures below are copied from `probe_records.json`, SHA-256
`62a92d716ce8a000e72c11930f3cd7cbbab976417eaef7fb3f88a5b2d9efcb81`. The
[re-probe report](P4_ADA_4B_REPROBE_20261127.md) prints shortened charge
hashes. The phase-1 switch requires the full SHA-256 in its source record.
The [independent re-check](../../reviews/P4_4B_REPROBE_REVIEW_RECHECK_20261127.md)
accepted the two 4B runs and the combined record. The two 0.8B entries come
from the [initial Ada probe](../trackp_p4_probe_ada_20261127/P4_ADA_PROBE_20261127.md).

```
p4_probe_host_class: ada_rtx6000
p4_estimate_hours: kev-0.8b 2.52
p4_estimate_hours: kev-4b 6.79
p4_estimate_hours: qwen3.5-0.8b-base 2.51
p4_estimate_hours: qwen3.5-4b-base 6.75
p4_probe_gpu_hours: 3.10
p4_probe_charge_file: trackp-p4-probe-20261125-a _wallclock.json 9a1949a156a23a735a6aae45888c99abc1935b17c069526d7dd6d227b4bf595c
p4_probe_charge_file: trackp-p4-probe-20261127-b _wallclock.json fa49096f90319db735d775e0bdb1be3baf6cbd882fa31583c3ae1049c18f0877
```

The two hashes match the files in `charge_files/`. The 3.10 GPU-h charge
includes every recorded probe attempt and the zero wall-clock time of
HTCondor job `760065` once. The projection is 20.57 GPU-h for the phase-1
jobs including startup, 23.67 GPU-h including probes, and 29.855 slot-hours.
