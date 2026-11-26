# B.1 trajectory and provenance corpus freeze candidate — 31 October 2026

Status: **CANDIDATE — not frozen**. This is a reviewable binding for the author's R1-B1-CORPUS-FREEZE clarification. It does not freeze soft-label tables, authorize B.2, satisfy R1-LAYOUT-FLATTEN, or replace the original native records. Independent review of the exact freeze integration and publication is required.

- Classification decision: `R1-SWEEP1-CLASSIFY`, recorded on the published ops branch in `b30cc95`; sidecar `results/r1/evidence/C3_sweep_classification_20261028.json`, SHA-256 `bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc`.
- Source index: `results/r1/pilot/C3_sweep_index_20261028T033315Z.json`, SHA-256 `812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab`. The original audit status is pending.
- Pure move commit `90d9b7fe00a203eb95a182ccad5475112d76c5ff`, published in `origin/ops/c3-sweep1-classify-20261028`: 872 R100 files, 436 per memory mode. Independent evidence: `docs/r1/reviews/C3_B1_CLASSIFICATION_INDEPENDENT_20261031.md`.
- Append-only source corpus: `results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z`; Git tree `6b1c0c6154a604c391f8b7684a2d4ce34ccddd1a`; original native manifest SHA-256 `f18f8a8b47ba17dc1da9e875d500831d6d0d03c69aa7d12b216444aeff1af98f`.
- Memory-none source corpus: `results/r1/evidence/C3_sweep_none_20261027T224356Z`; Git tree `468e57ce4871d0d33f08932c6fe13c2cb0d431ce`; original native manifest SHA-256 `5053067331676e1aaefb0c757cac47ec82200ad124ff81f3d2ae074cf197d440`.
- Each mode has 144 root trajectories. Offload evidence is sampled; subprocess seed snapshots are absent. Scope of seed and launch claims is as documented in the independent reviews.

The audited 7001–7005 soft-label tables do not yet exist; they require the separately gated fresh-seed audit and a later separate freeze. Neither this candidate nor the existing move edits native `PILOT` or batch `ENGINEERING_ONLY` strings.
