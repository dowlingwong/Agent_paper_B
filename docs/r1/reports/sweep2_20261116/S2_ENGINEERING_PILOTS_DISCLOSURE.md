# Sweep-2 ENGINEERING pilots — disclosure for the sweep-2 report (author requirement, 16 Nov 2026)

**Rule (author reminder):** ENGINEERING pilots reuse sweep-2 instance seeds, so they must run **no B.2 audits** and
touch **no audit seeds 7001–7010**; their outputs never enter any label table or training/selection; they are
disclosed in the sweep-2 report as engineering runs (as the 19 Oct pilot).

## S2-C4 timing pilot (`run_id s2c4-20261116-a`)

- Submitted through the accepted S2-C2 wrapper (`--audit-seeds 0`; `--reps 0`; `--points`; no audit stage).
- Clusters 759726 (append_only_summary, g3605) and 759727 (none, g3608), ENGINEERING_ONLY, v1 gpu digest
  `69b06b35…`, B2 harness `a3fedbb…`, pick GGUF `2959c1b0…`.
- **No B.2 audits ran:** `out/audits/` is empty in both sealed chunks; the collector's audit flag is 0; the job
  records declare `b2_audits: none` (the earlier job records listed the reserved 7001–7010 block as a declaration;
  no seed was used — the code now omits that list entirely and states "no B.2 audits; audit seeds 7001–7010 are
  reserved and untouched").
- **Use:** these outputs are ENGINEERING measurements only; they are not a label table, are not used for training
  or selection, and the sealed paths under `/ceph/srv/dwong/paperb/sweep2/s2c4-20261116-a/` are not evidence.
- **Disclosure line for the sweep-2 report:** "The L40S timing pilot (`s2c4-20261116-a`: 1 node × 2 instances × both
  memory modes, clusters 759726/759727) ran without B.2 audits, did not touch audit seeds 7001–7010, and its outputs
  are engineering-only: they never entered a label table, training or selection."

## S2-C3b D28 liveness + prompt-length re-measurement (`run_id s2c3b-20261116-a`)

- New (g)4 unit under R1-SWEEP2-SETTINGS (4): one owned llama-server on a NEMO2 L40S runs the sweep-1 D28 liveness
  over the eight sweep-1 nodes (2 instances × W=10, `append_only_summary`) and re-measures the sweep-2 manager prompt
  lengths with the **pick's** tokenizer (trial-1, 11-record and W=20/19-record classes), sealed through the accepted
  S2-C2 wrapper + `s2_c3b_lib.seal`.
- **Seed reuse accepted by R1-S2C3B-SEEDS** (`author-decisions-20261116b` @ `025bfc16`):
  `liveness_seed_policy = "sweep1_d28_reuse"` — the liveness instance seeds are the first two sweep instance seeds
  per node (10 of the 90 sweep-2 instance seeds), exactly as sweep 1's D28 liveness, because the pinned
  `r1.liveness` CLI has no seed flag. This is an ENGINEERING-only reuse, disclosed here as required; it never enters a
  label table, training or selection.
- **No B.2 audits, no audit seeds:** `b2_audits: none`; audit seeds 7001–7010 are reserved and untouched; no
  7001–7010, 8001–8010 or 9001–9303 seed is used (the collision guard is open-ended ≥ 9001). Prompt-measurement
  seeds are the disjoint block 6101–6108.
- **Use:** the liveness verdict, prompt-token counts and the `1,345`/`1,886` sweep-1 comparison are ENGINEERING
  measurements only; they are not a label table, are not used for training or selection, and the sealed path
  (`/ceph/srv/dwong/paperb/sweep2/s2c3b-20261116-a/liveness-prompt/`) is not evidence. The job never reads a label
  (`label_source.authorization: null`, `paper.evidence_ready: false`).
- **Disclosure line for the sweep-2 report:** "The S2-C3b D28-liveness + prompt-length engineering unit
  (`s2c3b-20261116-a`) ran without B.2 audits, touched no audit seeds 7001–7010 (nor 8001–8010 / 9001–9303), and
  reused 10 of the 90 sweep-2 instance seeds for the D28 liveness exactly as sweep 1 did (accepted by
  R1-S2C3B-SEEDS); its outputs are engineering-only and never entered a label table, training or selection."
