# D.3a production route record — independent tier-E review

Reviewer: independent subagent (fresh clone; did not write the record). Date: 28 Nov 2026.
Task: `compute/20261128-22`. Method: fresh clone of
`https://github.com/dowlingwong/Agent_paper_B.git`, independent re-execution of the manifest,
launch, cache, policy and test checks on TASL-2 against the clean checkouts named by the record,
and cross-checks of every capture against the host files. I read the task card
(`tasks/compute/20261128-22-d3a-production-route.md`), frozen rev 5 §§2, 7.2, 10, 11, and the
D.3a authorization draft.

| Item | Value |
|---|---|
| Published base | `origin/main` `c3a484055f717865e4e6826833e405af41771013` |
| Deliverable branch | `compute-d3a-production-route-20261128` @ `6120d0e7b5f26d2cb8a844cb7c557aacd92c9f9d` |
| Earlier tips reviewed | `89021459…`, `fafb7795…`, `2dbfc846…`, `ffae05bd…` |
| Record directory | `docs/r1/reports/d3a_production_route_20261128/` |
| Review branch | `compute-d3a-production-route-20261128-review`, rebased on `6120d0e7` |
| Host | TASL-2, RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01 |
| Clean checkouts used | repo `/home/dowling/r1_tracks/work/d3a_prod_20261128/repo` @ `c3a48405`, harness `/home/dowling/r1_tracks/work/harness_9bb_20261127` @ `9bb41680` (both `git status --porcelain` empty) |

## Verdict

**ACCEPTED WITH MINORS.** No blocker remains. The two blockers and both majors of my first pass
were resolved at `ffae05bd`; `6120d0e7` applies the remaining non-blocking findings (driver
`status()` order, derived-scratch wording, GiB/GB units, environment timestamps, dry-run call
reproducibility, the adjacent `D3_IMAGE` observation, `/props` wording, matrix-validation wording,
cache provenance). I re-verified the seal, hashes, driver and dry-run at the final tip. The few
residual items are informational/cosmetic and need no re-review.

## Review history

- **`89021459`** (first pass): CHANGES REQUIRED — the seal failed because `server.log`/`status.log`
  were gitignored, and the manifest's data cache was absent.
- **`fafb7795`** added the production driver, the launcher dry-run capture, the Python/shim hashes
  and the P7-environment linkage; the seal defect was unchanged.
- **`2dbfc846`** was a Markdown reflow plus its `SHA256SUMS` line; no data change.
- **`ffae05bd`** force-added the two logs, staged the reviewed cache, fixed the driver
  label/argv and added the Level 2 author-row text. That resolved B1, B2, M1 and M2.
- **`6120d0e7`** (final, reviewed here) applies the non-blocking minors. The diff is five files,
  all inside the record directory: the report, the root and capture `SHA256SUMS`, the dry-run
  capture and the driver. No data, JSON, manifest, ledger or capture value changed; the history is
  linear (`c3a48405` → `89021459` → `fafb7795` → `2dbfc846` → `ffae05bd` → `6120d0e7`) and the
  note/PLAN/`authorizations/` are untouched.

## Re-check at `6120d0e7` (final tip)

**Seal.** On a clean checkout at the final tip, both checks pass:

```
record root:  shasum -a 256 -c SHA256SUMS  -> exit 0, 38 lines OK, 0 failed
captures/:    shasum -a 256 -c SHA256SUMS  -> exit 0, 29 lines OK, 0 failed
root contains 6690c5f2…  ./captures/SHA256SUMS
```

The changed files hash to the values in §8: report `4734992b…`, driver `bd027076…`, dry-run
capture `f2b902f0…`, `captures/SHA256SUMS` `6690c5f2…`, root `SHA256SUMS` `9007304f…`. The
`server.log`/`status.log` entries are unchanged (`27094920…`, `78e60837…`) and still match the host
files.

**Driver `status()` order (M-1).** The function is now defined (line 31) before the cache loop
(line 34); `bash -n production_driver.sh` passes; the chunk command is still exactly the reviewed
`chunk_argv` (no `--repo-root`/`--harness-root`). The driver remains a disclosed, unexecuted
template.

**Dry-run reproducibility (N4).** The capture now records the explicit 20G call with
`out_dir="/tmp/d3a_prod_dryrun2/out"`, the record manifest and the GPU lease. I re-rendered it on
TASL-2 with the record's launch record and got exactly the stated
`536b1192746885ea35adb985e9c5be34a5960056b7a769da8bbc8cdcc2b3d887`; the rendered script still
calls `python3` (3.10.12), as recorded.

**Wording fixes (N1–N7, N9).** Verified in the diff: the scratch row now says the 14.9 MiB is
derived from 18× the largest P7 campaign and is not a measured 18-instance chunk (with the P7 §4
warning); the scope is stated as 20 GiB (`20G`) ≈ 21.47 GB ≈ 1.50× the 14.27 GB decimal peak, with
the decimal 1.4× value rounded to 20G; the environment capture's base header is 19:27:58Z and the
appended Python/shim/docker block is dated 19:34Z; `/props` `n_ctx` is "absent", not "null"; the
matrix check is described as ad hoc; `D3_IMAGE` v2.2 `49dd9900…` vs §2 v1 `69b06b35…` is recorded
as an adjacent observation for the HTCondor route (not used here); and the cache section says only
the raw cache files are used, with no `6adf3859` harness code executed in production.

The cache itself is unchanged by this commit (`captures/cache_staging.txt` still `ced91811…`) and
was independently verified in the `ffae05bd` pass: `MANIFEST.json 1987cc00…`, root tree
`3843b53c…`, all five per-node hashes equal the §4 table, and `prepare_node_dir` OK for all seven
nodes with 4 files / 1 ARFF / `data_match True`.

## Previously resolved blockers and majors (re-verified at `ffae05bd`, still true)

- **B1.** `server.log` and `status.log` are tracked, their hashes match the host files and their
  content is byte-identical; both seals pass (above); the root binds `captures/SHA256SUMS`.
- **B2.** The reviewed screening cache is staged at the manifest's `data_cache_root`; the MANIFEST
  (`1987cc00…`), total tree (`3843b53c…`) and per-node hashes match; `read_data_cache` and
  `prepare_node_dir` pass for all seven nodes; the two ignored harness node caches hold the real
  files and the harness stays `git status` clean.
- **M1.** The driver is labelled a template, the executed proof is `endpoint_run.sh`, and the
  chunk command is the reviewed `chunk_argv`.
- **M2.** §4 records the image/environment change as a Level 2 author binding (PLAN §10 row or note
  amendment) that binds Python 3.11.17 or adds an `environment_sha256` field, with draft wording;
  a Local `image:` edit alone is stated to be insufficient.

## Checks that pass at the final tip

1. **Manifest pins and adapter.** All five pinned paths exist in the clean `c3a48405` checkout and
   their sha256 matches (`700d93ca…`, `4f5f686b…`, `3d12ce05…`, `b5967dd7…`, `0d696535…`);
   `load_manifest(..., check_files=True)` and `validate_deployment_launch(..., source_dir=record)`
   pass.
2. **Launch identity.** Retry ledger `d3a-prod-20261128-a`, attempt `a01`; chunk stage `a`, node
   `digits_mlp`, arm `A0`, repetition 0, seeds 6201–6218, `manifest_sha256 42670584…`, GPU model
   `NVIDIA GeForce RTX 4090`; UUID/lease/CPU-lease agree with `observed.json`.
3. **Matrix.** 49 unique `(node, arm, rep 0)` rows over seven nodes × seven arms, one seed list
   6201–6218, one run id, one manifest hash, one GPU/UUID and the two canonical leases; the
   `digits_mlp`/`A0` row equals the exemplar's `remote_dir`.
4. **Server argv.** Canonical `94ba0434…`; `captures/server_argv.txt 9ed9d647…` byte-identical to
   the accepted P7 exact-runtime file.
5. **Endpoint chain.** `server.pid` = `ss_listen.txt` pid = compute-apps pid = `server_status.txt`
   Pid = 1673663; fds 8/9 → `/home/dowling/r1_locks/cpus-16-31.lock` and `gpu0.lock`;
   `observed.json` same UUID, lease true, `memory_check: pass`, zero other processes; `/v1/models`
   `meta.n_ctx 32768`, `props` `default_generation_settings.n_ctx 32768`; after stop no compute app,
   353 MiB used.
6. **Environment.** Python 3.11.17; the four pinned package versions through the shim; the venv
   python resolves to the pinned binary `ff9b2ac4…`; shim tree `1737028c…` reproduces; model
   `2959c1b0…`; `llama-server 646caa00…`; docker permission denied / no group; apptainer and
   singularity absent; the P7 exact `pins.txt` records the same Python and package set.
7. **Arithmetic.** 14,837 s per node ×7 = 28.85 h; the 1.5× requests check; 858,382 ×18 =
   15,450,876 B (14.73 MiB), +123,531 B = 15,574,407 B (14.85 MiB, now labelled derived); 14.27 ×
   1.4 = 19.98 GB decimal, rounded to the 20 GiB scope. The 858,382 B and 266–630 kB figures
   reproduce from the P7c run root, and 123,531 B from `scratch_samples.csv`.
8. **P10/P11/tests.** Re-run on the clean `c3a48405` checkout (its code tree is identical to the
   final tip outside `docs/`): 97 focused tests pass (2.76 s); P10 PASS for 160 seeds 20010–20801;
   `d3_analysis.py c0be0399…`; the P11 analysis suite passes 53 tests + 18 subtests.
9. **No signed change, no launch.** `c3a48405..6120d0e7` is docs-only in the record directory, the
   note/PLAN/`authorizations/` are untouched, `approved: false` remains, no campaign output exists
   on the host, the run id is unused on other branches, and the history is linear.

## Residual minors at `6120d0e7` (non-blocking)

- **R1.** `captures/launch_ssh_dryrun.txt` gives the exact 20G call but omits the first positional
  `launch_path` argument; the rendered-script hash is nevertheless reproducible with the record's
  `launch_A0_digits_mlp_r0.json` (I reproduced `536b1192…`). Add the path for completeness.
- **R2.** The record dates the appended environment block 19:34Z; the file's mtime is
  19:33:44.324Z. This is a minute-level rounding, not a discrepancy of content.
- **R3.** `captures/cache_staging.txt` has no timestamp or command line; the report explains the
  provenance, but a one-line header would make the capture self-contained.
- **R4.** §8 says the root `SHA256SUMS` hash is stated in the `coord/compute` report; that report
  post-dates this review and was not available to check.

## Checks run (commands and outputs)

Fresh clone (clean checkout at `6120d0e7`, not the working tree):

```
shasum -a 256 -c SHA256SUMS          # record root: exit 0, 38 OK
(cd captures && shasum -a 256 -c SHA256SUMS)   # exit 0, 29 OK
grep 'captures/SHA256SUMS' SHA256SUMS          # present, 6690c5f2…
bash -n production_driver.sh                   # OK
git diff --name-only c3a48405 6120d0e7         # only the record directory
```

TASL-2 (BatchMode SSH; read-only except a transient 20 GB scope test and temp copies):

```
clean checkouts:  repo c3a48405 dirty 0; harness 9bb41680 dirty 0
pins:             all five OK
adapter:          manifest_ok a NVIDIA GeForce RTX 4090 7 7; launch_ok …42670584…
matrix:           49 unique rows, one run id/manifest/seed list/UUID, canonical leases
argv:             canonical 94ba0434…; server_argv.txt 9ed9d647… (== P7)
endpoint:         pid 1673663 everywhere; fds 8/9 → canonical locks; lease true, memory pass;
                  /v1/models n_ctx 32768; clean after stop
cache:            MANIFEST 1987cc00…; root tree 3843b53c…; per-node hashes match; prepare_node_dir
                  OK for all seven; 4 files / 1 ARFF / data_match True
environment:      Python 3.11.17; pandas 3.0.3 / sklearn 1.8.0 / numpy 2.4.4 / scipy 1.17.1;
                  binary ff9b2ac4…; shim 1737028c…; model 2959c1b0…; llama-server 646caa00…;
                  docker denied; apptainer/singularity absent
tests:            97 passed in 2.76s
P10:              PASS, 160 seeds 20010–20801
P11:              c0be0399…; 53 passed, 18 subtests
scope:            systemd-run --scope -p MemoryMax=20G /bin/true → rc 0 (transient, not a chunk)
dry run:          rendered script 536b1192… reproduced from the recorded call
```

## What I did not verify

- I did not observe the 19:27Z endpoint live; the chain is verified from the committed captures,
  their hashes, the host files and cross-consistency.
- I did not re-run a campaign, audit, G6/G7 step or any label/evaluation read; the "no label/audit"
  claim rests on the absence of campaign output, the docs-only diff and the record's statement.
- I could not re-check the 19:28Z job state or the 19:31Z flock check after the fact.
- I did not re-measure the P7 timing basis (28.85/32.91 GPU-h); only the arithmetic and the cited
  values were checked.
- I did not run a chunk under the 20 GiB cgroup (only `/bin/true`), and I did not execute
  `production_driver.sh` (it is a disclosed template).
- I did not verify the note signing, the author's P9, or the `coord/compute` report (not yet
  available), and I did not test model/proposal behaviour.
- The cache staging was verified in the `ffae05bd` pass; this commit changes no cache file.

## Summary

At the final tip `6120d0e7` the record reproduces end to end: every pin, the launch/ledger identity,
the 49-row matrix, the argv hash, the endpoint-to-lease chain, the staged cache, the environment
hashes, the arithmetic, P10/P11 and the 97 tests; both seals verify on a clean clone; the driver is
a correctly labelled, syntactically valid template with the reviewed argv; and the dry-run hash is
reproducible. All first-pass blockers and majors are resolved. **ACCEPTED WITH MINORS** — the
residual items (dry-run call completeness, a one-minute timestamp rounding, a capture header,
the post-review `coord/compute` hash) are cosmetic or informational.
