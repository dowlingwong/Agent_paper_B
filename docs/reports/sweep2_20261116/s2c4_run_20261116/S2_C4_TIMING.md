# S2-C4 timing pilot — 1 node x 2 instances x both memory modes (L40S)

ENGINEERING_ONLY. Counts/timing only; no labels read. Measured on the reviewed S2-C2 job wrapper.

| chunk | mode | host | gpu | queue_wait_s | wall_s | gguf_fetch_s | collector_s | disk_peak_kb | mem_peak_mb | model/kv MiB | offload |
|---|---|---|---|---|---|---|---|---|---|
| digits_mlp-append_only_summary-pilot | append_only_summary | g3605.nemo.privat | NVIDIA L40S | 16.0 | 867.0 | 74.7 | 137.1 | 30314084 | 10781 | 18675.55/680.0 | 61/61 |
| digits_mlp-none-pilot | none | g3608.nemo.privat | NVIDIA L40S | 16.0 | 921.0 | 81.8 | 121.3 | 30314032 | 10853 | 18675.55/680.0 | 61/61 |

## Measured layout proposal

- pilot wall (max): **921.0 s** for 2 instances; estimated full chunk
  (18 instances) **8289.0 s**
- chunks: 16 (8 nodes x 2 memory modes)
- **estimated total GPU-hours: 36.84**
- proposed `+RequestWalltime = 10776` s, `request_disk = 42439718` kB,
  `request_memory = 32000` MB (measured peaks x1.4, above explicit floors); one
  (node, memory mode) chunk per job.

These are the values to pin in the sweep-2 authorization/hand-off; S2-C3 remains a separate unit.
