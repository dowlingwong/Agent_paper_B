# S2-C4 timing pilot — 1 node x 2 instances x both memory modes (L40S)

ENGINEERING_ONLY. Counts/timing only; no labels read. Measured on the reviewed S2-C2 job wrapper.

| chunk | mode | host | gpu | queue_wait_s | wall_s | gguf_fetch_s | collector_s | disk_peak_kb | mem_peak_mb | model/kv MiB | offload |
|---|---|---|---|---|---|---|---|---|---|
| digits_mlp-append_only_summary-pilot | append_only_summary | g3608.nemo.privat | NVIDIA L40S | 23.0 | 1043.0 | 74.9 | 210.4 | 30329269 | 10951 | 18675.55/1360.0 | 61/61 |
| digits_mlp-none-pilot | none | g3610.nemo.privat | NVIDIA L40S | 23.0 | 868.0 | 89.5 | 184.9 | 30329159 | 10481 | 18675.55/1360.0 | 61/61 |

## Measured layout proposal

- pilot wall (max): **1043.0 s** for 2 instances; estimated full chunk
  (18 instances) **9387.0 s**
- chunks: 16 (8 nodes x 2 memory modes)
- **estimated total GPU-hours: 41.72**
- proposed `+RequestWalltime = 12203` s, `request_disk = 42460977` kB,
  `request_memory = 32000` MB (measured peaks x1.4, above explicit floors); one
  (node, memory mode) chunk per job.

These are the values to pin in the sweep-2 authorization/hand-off; S2-C3 remains a separate unit.
