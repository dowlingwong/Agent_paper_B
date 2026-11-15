# Track P GPU freeze capture (read-only, TASL-7, 15 November 2026)

- `tasl7_trackp_gpu_uv_pip_freeze.txt` — `uv pip freeze` of the TASL-7 Track P GPU venv
  (`/home/dowling/r1_trackp/venvs/trackp-gpu`, Python 3.12.15), read-only, 121 lines,
  SHA-256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`; byte-identical to the
  committed `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`.
- `tasl7_vs_committed_freeze.sorted.diff` — `diff <(sort committed) <(sort TASL-7 capture)` = **0 lines**
  (empty; SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), i.e. the sorted
  freeze check the v2 Dockerfile enforces.
- Commands (read-only): `uv pip freeze --python /home/dowling/r1_trackp/venvs/trackp-gpu | sort` on TASL-7;
  `sort docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`; `diff -u` of the two.
