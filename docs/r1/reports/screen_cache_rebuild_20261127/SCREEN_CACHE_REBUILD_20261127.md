# Screening cache rebuild and engineering smoke — `compute/20261127-26`

**Result: PASS (ENGINEERING_ONLY).** A new cache built from the reviewed cache-layout fix is a fixed
point under the pinned `fetch_openml`, and the 168-run engineering smoke at seed 999 completed
168/168 with 0 failed, no STOP, and one matching evidence worker-runtime receipt per run. No label,
evaluation, test or sealed file was read; no GPU was used; no evidence run was started.

- **Task:** `compute/20261127-26`; base `origin/main` `4a9a1f4aaaadca90edf1ae481cec3163a67e42b0`
  (the task was issued against `83425c70`; main advanced by the docs-only R1-D3-STEP8-HOLD merge).
- **Code:** `c12136d664ae588a2539b76b2602e36742979ce8` — the exact code commit of
  `mac-screen-cache-layout-20261127` (`e9d7f230`), independently reviewed **ACCEPTED** (tier E:
  `docs/r1/reviews/SCREEN_MEASURE_CACHE_LAYOUT_REVIEW_20261127.md`, sha256 `594b7dfd…d524`). It is
  an ancestor of the published `origin/main`. The checkout was a fresh full clone, detached at this
  commit, with a clean working tree.
- **Host / environment:** deepthought; batch venv `/ceph/dwong/r1_prepare_20261025/venv` Python
  3.13.15 (scikit-learn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3); harness
  `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, clean (`harness_dirty=0`). `AR_HARNESS_ROOT` and the
  interpreter were the evidence-runtime values; `python3 -B` was used throughout.
- **Cotenancy at smoke start:** 40 CPUs, 31.9 free for others, load1 8.1, `ok: true`, our workers 0
  (`captures/cotenancy.log`).

## 1. New cache and its fixed-point layout

`data-cache` filled each of the six OpenML nodes once, then performed a fresh offline load and
refused if that load changed the tree. It succeeded.

| Field | Value |
|---|---|
| Cache directory | `/work/dwong/screen_fix_20261127/data_cache_20261127T134927Z` |
| Manifest | `captures/cache_MANIFEST.json`, sha256 `1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21` |
| `tree_sha256` | `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07` |
| `created_utc` | `20261127T134935Z` |
| Harness | `6adf3859de66c4814fcf376eed59880fbd8eeaf7` |

| Node | `tree_sha256` | Files |
|---|---|---|
| `openml_breast_w` | `058343f9759365d02c51eee9c52489ba84097a5428d0e2cf2e95a4456dbe9c94` | 4 |
| `openml_climate` | `3dc7f6bb3b80f5cebe63bc2eb187279ce204ca57137d6f24da80f5fee411cebd` | 4 |
| `openml_credit_approval` | `1dc25c439ca26164d3b47584d8ee70fe4427c95d224edc6bc5184546c1bc7c40` | 4 |
| `openml_ionosphere` | `97951b0b5341d5a44c6e0f367c0d9cab4d46949dbd898dfc92005569725d1c6f` | 4 |
| `openml_sonar` | `36d193ed8aa2be9f8d12ea9233da83b5698bdc285b3061af52e3d215370f2253` | 4 |
| `openml_wdbc` | `afd165f3e610cd198b069c724a185b7362d8ba643a99a2454787e6414df5bc8c` | 4 |

The fix's declared layout is present for the node that stopped the first re-issue:
`openml_breast_w/data_cache/openml/openml.org/data/v1/download/52350/breast-w.arff.gz`. The stopped
scene held the short path `52350.gz`, which `fetch_openml(data_id=15)` materialised into the
longer-path ARFF. The new tree already contains the file the loader writes; the offline load that
`data-cache` runs after filling left the tree unchanged. Independently recomputed read-only on
deepthought with the reviewed module: all six per-node `files` maps and `tree_sha256` values match
the manifest, and the top-level tree recomputes to `3843b53c…`. All 24 cache files with their
stored and decompressed hashes are listed in `captures/cache_file_list.txt`.

## 2. Engineering smoke (seed 999)

Command (exact, in `commands.sh`):

```bash
"$VENV/bin/python3" -B -m r1.noise.screen_measure run --engineering-smoke \
  --out "$SMOKE" --workers 16 --tmp /tmp/r1_smoke_fixed_$STAMP --data-cache "$CACHE"
```

| Field | Value |
|---|---|
| Output | `/work/dwong/screen_fix_20261127/smoke_FIXED_20261127T135341Z` |
| Label | `ENGINEERING_ONLY` |
| Seeds | `[999]` |
| Planned / written / failed | **168 / 168 / 0** |
| `stop` | `null` |
| Elapsed | 46.9 s, 16 workers, CPU only |
| `identity_flags` | 37 (declared diagnostic: configurations whose seed-999 metric equals `c0` or one another) |
| Worker runtime receipts | 168 rows; all 168 match the manifest's `worker_runtime_expected` |

The 168 worker-runtime rows all name `worker_python`
`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`, prefix `/ceph/dwong/r1_prepare_20261025/venv`
and package-list sha256 `a089bbf1fc7522a596631f4dd9535a18866336ff18edbbae14932106d94f16d3`. The
runs cover all eight design nodes (`digits_mlp`, `tabular_mlp` and the six OpenML nodes); every run
succeeded (`failed=0`), and every declared edit was applied and verified by the smoke design.

One pre-check STOP is preserved, not counted as a run or a scene:
`captures/precheck_stop.log` records `origin/main is stale or missing` because the checkout's
`refs/remotes/origin/main` was one commit behind the remote (the coordinator's docs-only
`4a9a1f4a` merge landed during setup). The strict environment check runs before any attempt
directory is created, so no run started and no scene exists. After `git fetch`, the same cache and
a new output directory produced the PASS above. Nothing was patched, relaxed or retried.

## 3. Captures and hashes

Branch `compute-screen-cache-rebuild-20261127`; all files under
`docs/r1/reports/screen_cache_rebuild_20261127/`.

| File | sha256 |
|---|---|
| `captures/cache_MANIFEST.json` | `1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21` |
| `captures/manifest.json` (smoke) | `3c6dd543314aa58b0e5dad266c18769f92c881befe8af9dc17e64f955f44d580` |
| `captures/design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `captures/lineage_runs.jsonl` | `0d8221a3ebcc83d5953bc53cb4052a38b1235a91da46127c6d5496caee81e95c` |
| `captures/worker_runtime.jsonl` | `4633b06b663d0f8cd30d7ffea2238e8e75dec1169d613a27f086ff7a32180141` |
| `captures/cotenancy.log` | `7504a1116ca585e953344ceca3d625c79a7cfc5ed719a5775d5f126be9436374` |
| `captures/smoke.log` | `ef7865fe75fee999510edf6c9a25f9fb6bb4a2e1bc10dfa7a3a55c682540504a` |
| `captures/precheck_stop.log` | `eb462ad22bf6f57e054e65d211ad544104795e884c4e5f4f5919129644024c0a` |
| `captures/RUN_ENV.txt` | recorded code, Python, harness commit and clean-harness line |
| `captures/cache_file_list.txt` | the 24 cache files with stored and decompressed sha256 |
| `commands.sh` | the exact build and smoke commands |

## Tests and scope

No code, spec, pin, note, authorization or evidence file changed; this is an engineering run.
The reviewed code's tests and the full-suite comparison were accepted in the local worker's report
(`reports/20261127-23-screen-cache-layout.md` on `coord/local`: 83 screening tests passed; full
`r1/tests` base 5,043 / branch 5,044 passes with identical 156 failure/error IDs). The captures here
add the actual farm run and its runtime receipts; no new test run was needed for a docs-only
deliverable.

## What happens next

The local worker prepares the second re-issue of the screening note with this exact `code_commit`
(`c12136d6`), review path, `tree_sha256` (`3843b53c…`) and cache-manifest sha256 (`1987cc00…`) for
the author's signature. The screening measurement does not start until that note is signed,
published and its strict preflight passes on deepthought. D.3 step (8) stays held per
R1-D3-STEP8-HOLD until the screening result exists.

**Decided alone:** to use the exact reviewed code commit rather than the newer docs-only `main` tip,
to keep the pre-check STOP record while rerunning in a new output directory (no attempt had
started), and to include the per-file cache list for the reviewer.

**Task id:** `compute/20261127-26`. **Branch/tip:** `compute-screen-cache-rebuild-20261127` (tip in
the `coord/compute` report). **Tests:** none new (no code change; reviewed code's suite accepted in
the local report). **Review:** independent review requested after push.
