# local/20261127-23 — screening cache fixed point and smoke/runtime parity

for: compute (engineering rebuild and smoke after coordinator publication)

- Task base `ab32029ec6af333d48e49262130ff928b105737f`.
- Branch `mac-screen-cache-layout-20261127` at `e9d7f230016ee32a1a338e83af4c01dfd467aeb2`.
  Exact code commit `c12136d664ae588a2539b76b2602e36742979ce8`.
- Independent tier-E verdict **ACCEPTED**. Review `docs/r1/reviews/SCREEN_MEASURE_CACHE_LAYOUT_REVIEW_20261127.md`
  SHA-256 `594b7dfd2f4317f09e7dda5ca12230bf575f2a7bc0a3639969ed82f71124d524`. Runner
  SHA-256 `ba05e1a4a1ff5ee643e749e60fbd6e3aa4e6681209ef2f5af940e6cafd4fdb69`.

The pinned node loader fills the cache once, then makes a fresh offline call. Publication requires
the same file tree, including each file's stored and decompressed SHA-256. The original per-job M1
checks and the four pilot ARFF pins still apply. The 168-run smoke at seed 999 now runs with the
replay-verified evidence environment and the evidence runner's per-job interpreter checks.

The former smoke and evidence manifests bind the same cache tree, with `52350.gz` and no
`52350/breast-w.arff.gz`. Matching the published decompressed description hash
`27baffae3b11d330604b06a9c975f31cf9e6e417a4640dcf1941729945dc5620` shows that the description already
named the longer URL. The stock pinned 1.8.0 loader derives the on-disk path from that URL before
any benchmark split or model work. The gap in the earlier smoke was its parent-only package
manifest and omitted worker-runtime probe. The receipt cannot establish which exact loader or
worker environment allowed its PASS. The new smoke checks the same worker executable, prefix,
versions and package list as evidence and records them per job.

## Tests and local engineering check

- Screening tests **83 passed** on the pinned sklearn 1.8.0 Mac venv, independently repeated with the
  same count. The regression rejects a synthetic short-path cache without networking and confirms the
  canonical-path fixed point. `git diff --check` passed.
- On the pinned harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7` and sklearn 1.8.0, all six public
  OpenML cache loaders verified offline with one ARFF each. The scratch manifest SHA-256 is
  `222d05a927c1792a947493a63e802bd8cd03660f4a09c6d7dbc4ec06e1ebbf26` and its tree SHA-256 is
  `f018ad3b8d9887f82d6b8ca0ec28d9f4b82dbcbbc101d6e3c4f27e35bfb93e7d`.
  Compute must bind its own fresh cache receipt.
- Full `r1/tests` compared one checkout at a time under Python 3.12.8, LightGBM off
  the path, pinned harness `6adf3859` and a fresh `TMPDIR` per run. Command
  `python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.
  Base had **5,043 passes** and branch tip **5,044**. Both had **150 failures, 6 errors,
  171 skips and 71 passing subtests**. The
  [156 sorted failure/error IDs](20261127-23-screen-fullsuite-failure-ids.txt) are identical,
  SHA-256 `79bafd028d4373d0f9aec64c05873680f40048e19d2932752e93b32e7688f44d`.

## Handoff

After coordinator publication and Compute's active-job and attempt-ledger check, use a clean
dedicated deepthought checkout of the exact reviewed code. Use the replay-verified batch harness
and the evidence venv for both commands. Keep the STOP scene `SMEAS_EVIDENCE_20261127T1155Z`.

```bash
set -euo pipefail
code=c12136d664ae588a2539b76b2602e36742979ce8
git fetch -q origin
git merge-base --is-ancestor "$code" origin/main
git checkout -q --detach "$code"
test -z "$(git status --porcelain)"
venv=/ceph/dwong/r1_prepare_20261025/venv
export PATH="$venv/bin:$PATH"
export AR_HARNESS_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness
export PYTHONDONTWRITEBYTECODE=1
stamp=$(date -u +%Y%m%dT%H%M%SZ)
root=/work/dwong/screen_prep_20261126
cache="$root/data_cache_FIXED_$stamp"
smoke="$root/smoke_FIXED_$stamp"
"$venv/bin/python3" -B -m r1.noise.screen_measure data-cache --out "$cache" --tmp "/tmp/r1_cache_build_$stamp"
"$venv/bin/python3" -B -m r1.noise.screen_measure run --engineering-smoke --out "$smoke" \
  --workers 16 --tmp "/tmp/r1_smoke_fixed_$stamp" --data-cache "$cache"
sha256sum "$cache/MANIFEST.json" "$smoke/manifest.json" "$smoke/worker_runtime.jsonl"
jq '{tree_sha256}' "$cache/MANIFEST.json"
jq '{label,planned_runs,written_runs,failed_runs,stop,worker_runtime_expected}' "$smoke/manifest.json"
```

Record the rebuilt tree and file hashes, 168/168 smoke runs, no failure or STOP, and one matching
worker-runtime receipt per run. If the preserved smoke venv remains available, compare its
`python3` path, prefix and `sklearn.datasets._openml` source SHA-256 with the evidence venv during
the read-only diagnosis, and report what can be established from the old receipts. A successful
engineering smoke goes to the coordinator for a second note re-issue with the new exact code
commit, review path, cache digest and code hash. The new evidence attempt requires the author's
signature, publication and strict preflight.

Decided alone: use the node loader directly for cache preparation instead of fitting a model, and
have the real smoke share the evidence-runtime checks. Local submitted no jobs and opened no
sealed partitions.
