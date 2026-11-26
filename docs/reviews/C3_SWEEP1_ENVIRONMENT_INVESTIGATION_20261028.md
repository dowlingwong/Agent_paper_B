# B.1 runtime environment investigation, 28 October 2026

AI-assisted independent read-only investigation (OpenAI Codex). The author chose to continue investigating the historical environment and keep B.2 stopped. No batch files, environments, or jobs were modified.

## Evidence

- The B.1 batch `r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw` has `uv_sync.log` stating `venv: wrapper for /ceph/dwong/r1_prepare_20261025/venv/bin/python`; the wrapper invokes that interpreter. The batch `python_versions.log` records Python 3.13.15, NumPy 2.4.4, pandas 3.0.3, and scikit-learn 1.8.0.
- `/ceph/dwong/r1_prepare_20261025/freeze.txt` has SHA256 `a8a4d73aaf02095904a771d642c5ce39463e133ce9b0a53025e06c176a78c159` and mtime 25 October 2026 00:30:17 UTC. `freeze_with_lightgbm.txt` has SHA256 `c760b28f2d03cfd31ae491b13b13ec6a348caee603b051349d9f85f9af282406` and mtime 00:30:21 UTC. The preparation scripts `setup_env05.sh` and `caches_and_tests_05.sh` indicate the first freeze followed creation of the shared venv and the second followed installation of lightgbm. The latter contains 58 packages.
- `docs/r1/reports/DT_PHASE2_RECHECK_20261026.md` identifies the same venv, documents the later installation of `narwhals==2.27.1` and records the major metric and manager-library versions. Its recorded harness `uv.lock` SHA256 is `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090`.
- The current venv's package metadata matches the 58 historical freeze versions plus `narwhals==2.27.1`. The latter metadata has mtime and ctime 26 October 2026 22:09:12 UTC, before B.1 began; the read-only search found no non-bytecode site-packages file with a post-launch mtime. These are current-state and filesystem-time observations, not a contemporaneous launch-time attestation.
- The batch's `prepare.json` has no complete environment freeze or freeze digest, and `uv_sync.log` only identifies the wrapper. Searches of the batch, local sweep scratch and available 26–27 October records did not locate a complete launch-time freeze.

## Conclusion

The 25 October freeze, 26 October report and current metadata together provide useful supporting evidence about the shared environment, but the first freeze predates the documented narwhals installation and none is bound to the 27 October launch. Current versions and mtimes cannot rule out changes subsequently restored. Full runtime identity at launch, and hence exact same-environment verification for B.2, remains **NOT CHECKABLE**. Do not treat a reconstructed list or today's environment as the original freeze. The four versions recorded in the batch can be independently compared, but that does not prove all runtime dependencies match.

The author clarified on 28 October that seeds 7006–7010 may be used for B.2 task-level joint-seed model retraining and evaluation, while remaining excluded from C3/Track P training, tuning and selection. That clarification does not resolve this environment limitation. B.2 remains stopped unless the environment evidence is established or the author adopts an independently reviewed alternative.
