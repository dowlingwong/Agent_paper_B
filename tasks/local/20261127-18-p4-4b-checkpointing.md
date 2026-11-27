# local/20261127-18 — P.4: activation checkpointing for the two 4B arms (R1-P4-4B-CHECKPOINT)

Owner: local. PLAN **R1-P4-4B-CHECKPOINT** (author, 27 Nov; `main` `c76e1b49`). Turn on activation checkpointing only for `kev-4b` and
`qwen3.5-4b-base` on the P.4 path. Micro-batch 8, the effective batch, the steps and the data stay as specified. Record the setting in the job
record and the probe spec. Tests show that the 0.8B arms are byte-identical in configuration and that the 4B arms carry the flag. Tier E: full
suite plus the torch files in a torch env, then review. Then compute re-runs the synthetic-label probe for the two 4B arms on an empty Ada card,
with peak memory, timing, outcome and charge (R1-P4-PROBE-CHARGE). A repeat OOM is a STOP for the author.
