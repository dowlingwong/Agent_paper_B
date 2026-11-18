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
