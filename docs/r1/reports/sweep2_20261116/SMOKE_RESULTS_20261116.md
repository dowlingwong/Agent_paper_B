# S2-C2 round-5 ENGINEERING smoke at 32,768 (16 Nov 2026)

Purpose: exercise the reviewed round-5 wrapper paths at the R1-SWEEP2-SETTINGS context (32,768) with a 2-instance
chunk per memory mode (S2-C4 layout), before any full chunk. ENGINEERING_ONLY; no B.2 audits; no audit seeds
7001–7010; outputs never enter a label table/training/selection.

| chunk | cluster | host | wall | queue | GGUF fetch | collector | gates | model/KV MiB | offload |
|---|---|---|---|---|---|---|---|---|---|
| digits_mlp-append_only_summary-pilot | 759728 | g3608.nemo.privat | 1043 s | 23 s | 74.9 s | 210.4 s | PASS (2/2 roots, 40 calls, 0 parse failures) | 18,675.55 / **1,360.0** | 61/61 |
| digits_mlp-none-pilot | 759729 | g3610.nemo.privat | 868 s | 23 s | 89.5 s | 184.9 s | PASS (2/2 roots, 40 calls, 0 parse failures) | 18,675.55 / **1,360.0** | 61/61 |

Both rc 0, `ENGINEERING_ONLY`, image `69b06b35…`, model `2959c1b0…`, harness `a3fedbb…`, server build
`0.7.0-dev (build 11669, commit 620d2225c)`, `-c 32768 -ngl 999 -np 1`, non-numeric differences
(`--no-webui`, `-lv 4`) recorded. Noise source pinned (`3d12ce05…`) and manifest-verified. Disk peak 30.33 GB,
memory peak 10.95 GB.

**32k effect:** KV cache 1,360 MiB vs 680 MiB at the 16k pilot (model buffer unchanged). Measured layout at 32k:
full 18-instance chunk **9,387 s**, 16 chunks → **41.72 GPU-h**; proposed `+RequestWalltime = 12,203 s`,
`request_disk = 42,460,977` kB, `request_memory = 32,000` MB; no split.

Sealed evidence: `/ceph/srv/dwong/paperb/sweep2/s2smoke-20261116-a/digits_mlp-{append_only_summary,none}-pilot/`
(SHA256SUMS verified, SEAL_RECEIPT.json); repo copies in `smoke_20261116/`.

This validates the round-5 fixes (32k server start, noise pre-check/manifest, `/proc` CPU class, sweep-1 gates,
evidence-preserving STOPs, tar transfer + seal) and settles the 16k→32k layout question. It is not a label table and
not evidence.
