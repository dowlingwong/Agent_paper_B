# Sweep-2 scheduler dry runs on integrated `main` (R1-SWEEP2-INTEGRATE process note P1)

20 November 2026. ENGINEERING_ONLY. Rendered from the integrated sweep-2 code on published `main` `3a6dcf4d`
(merge `62b92bf8` of `int-sweep2-c5-20261119` / `dd1e22be`; independent review `SWEEP2_C5_INTEGRATION_REVIEW_20261119.md`).
The 16 chunk JDLs use the H200-only measured layout and the approved sweep-2 note run id `s2ev-20261119-a`;
`condor_submit -dry-run` was run for every chunk on deepthought. No job was submitted and no queue state changed.

- chunks: **16/16** dry-run rc 0; all carry `request_memory = 32000`, `request_disk = 42460970`,
  `+RequestWalltime = 8735`, v1 image `sha256:69b06b35…`, `periodic_hold = (NumJobStarts > 1)`, and
  `TARGET.GPUs_DeviceName =?= "NVIDIA H200"`.
- outputs retained: `/work/dwong/htcondor_prep_20261114/s2_dryrun_20261120/` (per-chunk JDL, dry-run txt/err/rc;
  `DRYRUN_SHA256SUMS_FULL`); this report commits the hash file `SWEEP2_SCHEDULER_DRYRUN_20261120_SHA256SUMS`

| chunk | JDL sha256 | dry-run sha256 |
|---|---|---|
| digits_mlp-append_only_summary | `b512932fd7c7262165fdd46d564d0f5fe85f0b3a6d7e5c1445e7958b0acf780b` | `e791488e5889252c32b178f094fb08b1e6d90bec2e1c0c3c0cb3147a8f03a291` |
| digits_mlp-none | `de63c862656ef432ec899ffba1a2469f179d972f723b21896f9a379563c706d1` | `75f18573a82d146722a1af4a8456087d550f5793d4c0c58333d64c49f20b87f1` |
| openml_breast_w-append_only_summary | `877b880ccd484c1b45bef496b73b67c0b4d66b3c459aacceecc2db6669ac98a3` | `cd55bcaaa7ce18c6b23500eb3f20acbcc4d0468dd3cf71b5ef997c3bdaabf670` |
| openml_breast_w-none | `453414f6b13a8f3d2bb0925a6777971bd7b3646edf537822b5c737d528904e17` | `b4ccecbf3778be0b6cf2f40b5d44cccfc1f5e74edadaa7ead1fd06aebe10cd34` |
| openml_climate-append_only_summary | `187fa6f43b25cc351b899d917fa8e7457963fdaaeb0377f1ce6a82d285965903` | `fbf2ae436bd1392f87f3ab5fbf0ef7105715f853de9dca60e664de9646012208` |
| openml_climate-none | `46a527c1a09378ad12ee69fa827a5e5073b7055c99ac7574833f368d317474d2` | `8f377569d700e615fbc70636da610481f20afcc3e0ae2a38b9e63ccc91b217cf` |
| openml_credit_approval-append_only_summary | `aa0c0d7455152c3e0d6c2cd8518c6eba6350880a823d5d7914f2ebd51fc91881` | `92f63ce3ef1cc219a9f0c5f357143978b6173a81d2dc1abda23b886cb257659b` |
| openml_credit_approval-none | `07b7ad4b0ca6dbf1a498b262701daf256dd80d085b51228fcfb33bb9c653d3a8` | `db57f05d9638e88c327c31b7149ea48464121a53151dd600f538f2d4cf57deb0` |
| openml_ionosphere-append_only_summary | `91ff04743dda3307a4b6835459c07eecbed634e52717baa52790f5038a8e136e` | `8e6dab6069065335092612e1bdec2b00c4b5d4431ea91aed2f06a56a0a4ae697` |
| openml_ionosphere-none | `2fd6f30ea6ba1369f4c937f7d6cedb29bed0e0110ac467094af91f2f4494e6a4` | `400b36ec0caa4adc426117e14ff5fb8cc6cc43f5b903827478124827743bc25a` |
| openml_sonar-append_only_summary | `c376276acc000eeae21e375eade735eac48f4a7d7ebc0e3354ad16c0ad389db4` | `0a33f459a882e6b83f826f2028614a7bfa55d7b7cea09c05768654b2abd13c8a` |
| openml_sonar-none | `b58acc36fccc106b1c9f4beffe4e27b5342b137d3fd23a4f1b0b9946b77fa94f` | `52dcaabaf2379d426661102fa1835bb94bf05828f15ada9e624410e2d81ce485` |
| openml_wdbc-append_only_summary | `d605d1253d7be07750b64d717567bfbe19abed0d85958bab25bfa6d7c7df9651` | `bc8ee4ecb4ccd63697ffd211c0246ca2fdcbf43b33393e8a1e7f71deb8eaf334` |
| openml_wdbc-none | `b360099088edda3c377f7f4f3886367b936b76c12c24af98ec23c4b0445b53f7` | `76284f36123cd094b14b2806ec7f5c4f252ce8d67648dd051f9bad270d57eead` |
| tabular_mlp-append_only_summary | `c15b20a8cb422bdcc3eeeb8bc0c55baf444ace3dcd45a60c80001c1dfdf680a0` | `9de549d15525ac6fb6ad9921ace6444bab12b429f408013f0a8f27e5a8e8db2f` |
| tabular_mlp-none | `5cf1b4dc19526a22a46659a01f907f049cb40732698ef9e52d7c9d3ebd144d5b` | `ba00d273bc1dbcea2a204fc23bd2baf6e13aec0d321d8171b7e8162dae47b6c3` |

Hash file also covers each `s2_c2_job.dryrun.rc` and `s2_c2_job.dryrun.err` (64 entries).

Per-chunk check: `request_memory = 32000`, `request_disk = 42460970`, `+RequestWalltime = 8735`,
`container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…`, `periodic_hold = (NumJobStarts > 1)`,
H200 requirement present, dry-run rc 0 — 16/16 pass (no failures).
