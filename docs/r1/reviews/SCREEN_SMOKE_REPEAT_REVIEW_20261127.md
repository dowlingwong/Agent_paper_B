# Review: screening smoke repeat after the ARFF fix (compute/20261127-14)

- **Reviewer:** a fresh independent reviewer (AI-assisted Claude subagent, 27 Nov 2026). I did not write the unit. I modified no file on the reviewed branch, read no credential, label, evaluation or sealed file, and made no network access.
- **Target:** `origin/compute-screen-smoke-repeat-20261127` @ `05f3e115`, based on `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30` (merge-base confirmed).
  - Record: `docs/r1/reports/screen_smoke_repeat_20261127/SCREEN_SMOKE_REPEAT_20261127.md` and its seven capture files.
  - Task: `tasks/compute/20261127-14-screen-smoke-again.md` on `origin/coord/coordinator`; prior report `reports/20261127-02-screen-smoke-fix.md` on `origin/coord/local` ("What compute runs next").
- **Method:** a detached worktree of `origin/main` under the session scratchpad. I ran `git diff --stat/--name-status origin/main...branch`, hashed the committed blobs with `shasum -a 256`, verified `captures/SHA256SUMS` with `shasum -c` after `git archive`, recomputed the design and cache tree hashes independently, cross-checked the two JSON manifests, compared the manifest `code_sha256` against `origin/main`, inspected the `screen_measure` CLI, and collected the test file. The worktree was removed; nothing was pushed to `main` or either `coord` branch.

## Findings

### Scope: clean

`git diff --stat origin/main...origin/compute-screen-smoke-repeat-20261127` shows **8 added files, 3,544 insertions, no deletions**, all under `docs/r1/reports/screen_smoke_repeat_20261127/`:

- the record (53 lines);
- `captures/SHA256SUMS`;
- six captures: `smoke_manifest.json`, `data_cache_MANIFEST.json`, `design.json`, `smoke.log`, `data_cache.log`, `cotenancy.log`.

No code, test, data, label, evaluation, sealed file, note or config is touched. The branch carries two commits: `8e57ccc9` (record, sums, three JSON captures) and `05f3e115` (the three logs).

### Hashes: all match

The committed bytes hash as follows; every value is exactly the record's table and `SHA256SUMS`:

| File | sha256 |
|---|---|
| `captures/smoke_manifest.json` | `20748f42e5792a78d49abb8249c9a8f85c37116067169031c01be99b9b14ddc7` |
| `captures/data_cache_MANIFEST.json` | `74e688e754346d177cbafbe7e19b4bd984839d37c7808600f20c011602bcbd62` |
| `captures/design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `captures/cotenancy.log` | `fe1d450e9e166e1e8c15c0ee8e28ab2754bf559813be14ff1f318189043c0c50` |
| `captures/data_cache.log` | `a2ba90cb2f756106fb11519fe44b1669147d307873e5ea51df6614380fc9b262` |
| `captures/smoke.log` | `137574df9ebfcf5f7837e2372b053c171c34f0dde50a0c70b7c60d56c2281ddf` |
| `captures/SHA256SUMS` | `0d7ad146570f037e6f5ba644645fe7b51c8c90b56a3435ec884227c6ae54a1ec` |

`shasum -a 256 -c captures/SHA256SUMS` reports **OK for all six** covered captures. The sums file does not list itself, which is the usual convention.

The internal hash chain is also sound:

- `design_sha256` `bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8` is the canonical hash of the committed `design.json`.
- `data_cache_MANIFEST.json`'s total `tree_sha256` `c0c2a3645f3fbcbeed6374e7f1a1b717421ec39985cb875bdc1e4a44f6a9781b` is reproduced from its six per-node trees, and each per-node tree is reproduced from its four recorded files.
- `smoke_manifest.json`'s `data_cache.nodes` and `data_cache.tree_sha256` equal the data-cache manifest's per-node and total trees.

### Record claims: supported

- **168 runs, no STOP.** `smoke_manifest.json`: `planned_runs = written_runs = 168`, `failed_runs = 0`, `stop = null`; the final summary line of `smoke.log` repeats the same values. `smoke.log` contains no STOP or error line; `data_cache.log` ends with the successful `tree_sha256`.
- **`failed_runs.jsonl` absent.** `failed_runs = 0`, and `r1/noise/screen_measure.py` appends that file only on a failure/data-cache stop. No capture contains a directory listing, so absence is inferred rather than directly photographed; nothing contradicts it.
- **37 identity flags.** The list has exactly 37 entries.
- **Edit sets.** `edit_sets` has eight decision nodes, all `"equal"`.
- **Harness.** `harness.commit = 6adf3859de66c4814fcf376eed59880fbd8eeaf7`, `dirty = false`; the data-cache manifest records the same commit.
- **Environment.** `host.python = 3.13.15`; `libraries.scikit-learn = 1.8.0` (also NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1).
- **Cache.** `tree_sha256 = c0c2a364…` and `MANIFEST.json` sha256 `74e688e7…` both match; six nodes, 24 files, one manifest.
- **Base.** `e153df24` is the merge-base and contains `03a352d9` (verified ancestor). All six `code_sha256` entries in the smoke manifest equal the same files at `origin/main` `e153df24` (`screen_measure.py` `5c04aeee…`, etc.), so the driver content used was the base's content.
- **Co-tenancy.** `cotenancy.log` has 40 CPUs, 33.5 free, load1 6.5, `ok: true`, `our_workers: 0`, at `2026-11-27T03:14:09Z`, matching the smoke start.

### Task constraints: met

- **Clean `origin/main` checkout.** The six driver files hash exactly to `origin/main`; the manifest records a clean harness. The record says `git status --porcelain` was empty, but no status capture exists (minor, see n3).
- **New cache directory.** `/work/dwong/screen_prep_20261126/data_cache_ENG_20261127T0417Z`, distinct from the old `…_STOP_arff_suffix` path. `build_data_cache` refuses an existing output directory, and the log shows a single build.
- **Old STOP directory not reused.** The new output path is different; the build's manifest and log reference only the new path. "Not touched" is asserted, not captured (minor, see n2).
- **No `--deadline`.** The CLI (`r1/noise/screen_measure.py`) has no `--deadline` option at all, so a successful run cannot have passed one; the record's command line omits it.
- **Engineering smoke only.** `label = ENGINEERING_ONLY`, `stub = false`, `seeds = [999]`, and the note says it is never a result. No evidence-run or signed-note claim is made.

### Non-blocking findings

- **n1 (date mislabel, should be corrected).** The record calls `..._STOP_arff_suffix` "the 26 Nov STOP directory." That directory is from **27 Nov**: the prior record `docs/r1/reports/screen_smoke_20261127/SCREEN_SMOKE_DATACACHE_STOP_20261127.md` (`33767535`) names `data_cache_ENG_20261127T004046Z_STOP_arff_suffix`. The 26 Nov STOP was the earlier `determinism_unverifiable` scene, a different directory. Fix the date to avoid conflating the two scenes.
- **n2 (provenance note).** The path suffix `20261127T0417Z` is not the run's UTC time (`created_utc 03:11:50Z`, smoke `03:14:09–03:14:57Z`) nor its local time (`04:11–04:14` on the UTC+1 host). The embedded chronology is coherent and the hashes bind the captures, so I read the suffix as an opaque label, not a launch timestamp. The record should not imply otherwise; a one-line note on where the stamp came from would close the gap. The "old STOP not touched" claim likewise rests on the operator, with no mtime/hash capture.
- **n3 (uncaptured status claims).** "Clean checkout / status checked" and "82 passed" are not in the captures. The former is strongly supported by the six code hashes matching `origin/main`; the latter is consistent with the 82 tests collected at `e153df24` (I collected 82, did not execute the pinned environment). State them as reported or add the console captures.
- **n4 (uncaptured size).** "463 KiB" appears in no capture; the manifests record hashes, not sizes. Drop the figure or add a `du`/`ls -l` capture.
- **n5 (intermediate commit).** `8e57ccc9` commits a `SHA256SUMS` that lists the three logs only added by `05f3e115`, so the first commit is internally incomplete. The branch tip is complete; squash if the intermediate is meant to stand alone.
- **n6 (absence capture).** As noted above, the absence of `failed_runs.jsonl` is inferred from `failed_runs = 0` and the code path. A directory listing would make it direct evidence, but this is not material.

No STOP is present in the reviewed run, and I found no claim that the captures contradict.

## Verdict

The diff is documentation-only; every claimed capture hash matches the committed bytes; the cache and design hashes recompute; the 168/168, zero-failure, null-stop, 37-flag, harness, environment and base claims are supported by the manifests and logs; and the task constraints are met. The findings above are documentation/provenance nits, not defects in the engineering-smoke result.

Verdict: ACCEPTED
