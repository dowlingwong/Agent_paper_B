# Track G isolated port-kit update after the accepted harness-isolation fix (19 November 2026)

**Status.** The three Track G isolated port-kit branches on Ada were updated to the accepted core fix
`5403392e94cb59d732f45d6702fc857531ad8fd5` (merge + node-copy update, local commits only, **not pushed**), the
eight node copies of `ar_isolated.py` now equal the fixed master `37d99ab0…`, and all eight recomputed
`frozen_pin_sha256` values match the accepted fix review's table exactly. The five per-node GPU smokes whose data
is on Ada (**mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv, mlgym_cifar10, mlgym_fmnist**) ran isolated with no
waivers and **passed** (`CHECKLIST_E_PASSED`, every executed record `effective: true`, `waivers {}`,
`exceptions []`, 9/9 records in each run).
The autoresearch GPU smoke was attempted last and is **BLOCKED by condition 7** (CUDA IPC cannot cross the
worker's user namespace on this host/driver: `RuntimeError: CUDA error: invalid resource handle` at
`ar_isolated.cuda_open`), exactly as the accepted fix review disclosed — it did not pass and is not claimed to.
House Prices is a **STOP** (the user's Kaggle `train.csv` is absent) and Breakout/MinAtar is **not run** (its JAX
environment does not import on Ada and no data is present). ENGINEERING_ONLY; AI-assisted.

## 1. Authority and inputs

- Published paper main `de3de54f`; accepted isolation core
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e`, accepted Ada fix
  `5403392e94cb59d732f45d6702fc857531ad8fd5` (branch `mac-harness-isolation-fix-20261119`; condition 6 **PASS**,
  condition 7 **BLOCKED/documented**).
- Fix report `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_FIX_20261119.md` (§"Kit-side update") and
  review `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (ACCEPTED; conditions C1–C4; C2 is this
  update). Read on the Mac ops worktree; the fix branch and its worktree on Ada were used read-only as the merge
  source.
- Kit plan: merge `5403392` into each kit, copy the new master `src/autoresearch/trackg/node_lib/ar_isolated.py`
  over the 8 node copies, recompute each node's `frozen_pin_sha256`, commit locally, then rerun the per-node
  smoke (fix report §"Kit-side update"; review C2).
- Ada host `ucrtasl` (Linux 5.15.0-151, uid 1030, 96 CPUs, 8× RTX 6000 Ada), workspace
  `/home/dowling/r1_trackg_20261117`. Read-only on TASL hosts; no TASL-7/TASL-2, HTCondor/deepthought, root/sudo,
  deletion, push or force operation was used. Run evidence root:
  `/home/dowling/r1_engineering/iso_kit_update_20261119/` (captures copied next to this report).

## 2. Kit branches — commits (Ada, local only, not pushed)

All three worktrees were clean and at the exact tips given in the task before the update; the fix worktree was
clean at `5403392`. Each kit got **two** commits — a normal `--no-ff` merge of the fix, then a copy/pin commit
(the merge was clean in all three, matching the review's `git merge-tree` check: no conflicts, no force, no
history rewrite).

| kit | worktree | branch | pre tip | merge commit | copy/pin commit = new tip | clean after |
|---|---|---|---|---|---|---|
| ar | `harness_iso_ar` | `mac-trackg-iso-ar-20261117` | `5d3dccccf1790203212d2e0aa96c969f7c703fdc` | `2e65922d2add7edaf6228d2bad7dd8b8b0b0db16` | **`448f6820f885d70ee6872b692284fe861afd3a33`** | yes |
| mlab | `harness_iso_mlab` | `mac-trackg-iso-mlab-20261117` | `0aae2f68376a5665ce1869e835906615b7e08ecc` | `f7db8e24e1899a2c504d9fba8bd3553ff88562ad` | **`fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9`** | yes |
| mlgym | `harness_iso_mlgym` | `mac-trackg-iso-mlgym-20261117` | `061d638edc91254477d699b3be89e40625cc99ec` | `0c1df3a73c838c5e2b4076d988b66776f5b2e50f` | **`f07875de79a5a57739227b13e0fd52d31646edaf`** | yes |

**Not pushed, verified:** local branch refs are the new tips while
`refs/remotes/origin/mac-trackg-iso-{ar,mlab,mlgym}-20261117` still point at the pre tips
(`5d3dccc / 0aae2f6 / 061d638`); no `origin` ref changed and no new remote branch exists. Committer/author is
`Dowling Wong <wangdowling@gmail.com>` (same as the branch history).

Merge diffstat, identical in all three kits (no other file changes; `git diff --numstat` pre..merge):

```
 src/autoresearch/trackg/node_lib/ar_isolated.py | 50 ++++++++++++++++-
 src/autoresearch/trackg/runner.py               | 34 ++++++++++++
 tests/trackg/test_trackg_isolation.py           | 73 +++++++++++++++++++++++++
 3 files changed, 154 insertions(+), 3 deletions(-)
 47  3  src/autoresearch/trackg/node_lib/ar_isolated.py
 34  0  src/autoresearch/trackg/runner.py
 73  0  tests/trackg/test_trackg_isolation.py
```

Copy/pin commit diffstat: ar **1 file, +47/−3**; mlab **3 files, +141/−9**; mlgym **4 files, +188/−12** (each
node's `ar_isolated.py` only).

## 3. Master copy and frozen pins

The fixed master `src/autoresearch/trackg/node_lib/ar_isolated.py` in every kit after the merge has sha256
`37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`; all eight node copies were overwritten with it
byte-identically (each verified with `sha256sum`). The copies are:

- ar: `nodes/autoresearch_fixedtokens/ar_isolated.py` (1)
- mlab: `nodes/mlab_{cifar10,imdb,ogbn_arxiv}/ar_isolated.py` (3)
- mlgym: `third_party/mlgym/nodes/mlgym_{breakout_minatar,cifar10,fmnist,houseprice}/ar_isolated.py` (4)

`frozen_pin_sha256` was recomputed with each kit's **own** spec and `isolation.frozen_file_hashes`, exactly as
`WorkingCopyRunner` takes it (`sha256` of `json.dumps(files, sort_keys=True)`); no other frozen file changed for
any node (the checker printed `changed_frozen_files == ["ar_isolated.py"]` for all eight). All eight pins match
the accepted review's table exactly:

| kit | node | old pin | new pin (committed node files) |
|---|---|---|---|
| ar | autoresearch_fixedtokens | `b84828756b0ce0f5efc95e648354f8e04ad89c078849f4cad386a68832f563e9` | **`b5f0ec2f351d59369fb14996848fce540309393646cc20c36b6651387b1e4453`** |
| mlab | mlab_cifar10 | `b85990cb284198cd3234818e368ad0b46c6eddf8b8e247c929597628a6d5cec7` | **`1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2`** |
| mlab | mlab_imdb | `080fc88d6fafc04ec614e9eee441a9e5eb185c5a5e1535c62d581b36c8943a6c` | **`4b1019a60b1ac96028944d1dcc02be582f84e1fab0dbfd11d00011f460fb97fb`** |
| mlab | mlab_ogbn_arxiv | `a75f717d789655505e60b533230a2c9aaf23367f0164f8bc8bfbfbfdf4f8db4a` | **`bd71fdf4c6b3a66715cb602a41a7a1f5bdeeaa6e23439c558a96c2bda061c9d7`** |
| mlgym | mlgym_breakout_minatar | `d37f92aebe0ca285d1c11f6b3fb75970506f58ed7211cf24dbc276bfe3a2579e` | **`cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4`** |
| mlgym | mlgym_cifar10 | `dd149c3fdf1f9e847f482a6ae73addb54df29845a62d620b2c0d40e38d204716` | **`2d7e533b2a1075000d15a21445f98b94d7df2cf527baff0264f3ae306f93022e`** |
| mlgym | mlgym_fmnist | `977f666ce44fffee606fba6875a33e33522db86845652d886fd1ca3f6267edad` | **`eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3`** |
| mlgym | mlgym_houseprice | `4cc1f9646b08da9791299a8dfda0c4da411a1d8ee81b2aa260c066c69773b1a1` | **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`** |

The new pins are recorded in each copy/pin commit's message. No kit YAML pin file exists or needed editing (the
node-spec comments name the isolation branch, not a sha; the pin is computed from the kit at pin time).

**Deployed-pin note (important for the census).** After `setup_command` links `data/` into a node,
`frozen_file_hashes` hashes that symlink as `data: link:<absolute target>`, so a run record's
`frozen_pin_sha256` is a **deployed** pin that also commits the data-root path. The five torch smokes' records
carry e.g. mlab_cifar10 `a459b3d823075953d05422594cc97fa743723f22e79e1f8368480007dd041388` (vs the committed-file
pin `1f047ad7…`); recomputing the pin with the data link present reproduces the record values exactly. The
census must commit one documented convention — the fix report's table is the committed-file pin (no data link),
the smoke records are deployed pins — and not compare the two by accident. The table above is the committed-file
pin and matches the accepted review.

## 4. Static tests

CPU-masked (`taskset -c 0-15`), GPU-masked (`CUDA_VISIBLE_DEVICES=`), under a delegated user cgroup
(`systemd-run --user --scope -p Delegate=yes`, `AR_TEST_CGROUP_PARENT` set), `-p no:cacheprovider`,
`PYTHONDONTWRITEBYTECODE=1` so nothing was written into the kits. Command shape, from each kit root:

```
PYTHONPATH=src <envs/torch312/bin/python> -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"
```

| kit | pre-update `tests/trackg` (kit files, core isolation file excluded) | post-update full `-k "not smoke"` |
|---|---|---|
| ar | 200 passed, 2 failed, 3 deselected (113.15 s) | **227 passed, 2 failed, 1 skipped, 3 deselected** (137.61 s) |
| mlab | 191 passed, 2 failed, 5 deselected (22.08 s) | **218 passed, 2 failed, 1 skipped, 5 deselected** (45.32 s) |
| mlgym | 198 passed, 2 failed, 6 deselected (24.00 s) | **225 passed, 2 failed, 1 skipped, 6 deselected** (47.17 s) |

The core isolation file on the **pre-update** kits could not complete on Ada (the `68cdd1a` host-check defect):
`tests/trackg/test_trackg_isolation.py` alone reached `...FFFFFF.F.` and then **hung**; a `timeout 300` wrapper
ended it with exit 124 (capture `pytest/pre_iso_ar.log`) — the host-check report's `14 failed / 9 passed / 1
skipped` for `68cdd1a` is the same defect. After the update the same file is **27 passed, 1 skipped in 22.82 s**
(capture `pytest/post_iso_ar.log`), matching the fix report.

The same **two** tests fail before and after the update in every kit — they are environment failures, not
kit/isolation regressions:

1. `tests/trackg/test_trackg_review_round2.py::test_child_that_leaves_the_group_but_not_the_session_is_killed`.
   The fixture's job runs under the spec's `python3`; on Ada `PATH`'s `python3` is `/usr/bin/python3` **3.10.12**,
   whose `subprocess.Popen` has no `process_group=` keyword, so `job.py` dies before writing `child.pid` (the
   test then fails reading it). Re-running just this test with `envs/torch312/bin` first on `PATH` gives
   `1 passed in 1.61 s` (capture `pytest/post_childkill_pathfix.txt`), so the behaviour under test is fine.
2. `tests/trackg/test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`.
   The known t0 environment failure recorded in the port report: the probe raises
   `ImportError: langchain-openai is required for OpenAI-compatible providers…` because that package is not
   installed in `envs/torch312` (reproduced manually with the probe; base commit `a3fedbb` exists and
   `git archive` works).

Both pre-date this update and are independent of fixes A/B; no test was skipped or weakened to make the counts
look better, and the one skip is the pre-existing root-only uid-65534 test.

## 5. Data setup (runtime state, not committed)

`setup_command` was run per node with `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the
repository); for the five existing trees it re-checked the read-only data against its manifest and re-linked
`data/` into the node (no download). Runtime `data` symlinks are untracked in the kit worktrees (expected).

| node | data link | data_manifest.json sha256 | setup exit |
|---|---|---|---|
| mlab_cifar10 | `…/data/mlab_cifar10` | `43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3` | 0 |
| mlab_imdb | `…/data/mlab_imdb` | `a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c` | 0 |
| mlab_ogbn_arxiv | `…/data/mlab_ogbn_arxiv` | `9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c` | 0 |
| mlgym_cifar10 | `…/data/mlgym_cifar10` | `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` | 0 |
| mlgym_fmnist | `…/data/mlgym_fmnist` | `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` | 0 |
| autoresearch_fixedtokens | `…/data/autoresearch_fixedtokens` | `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51` (13 files) | 0 |

None of the real data manifests carries a `synthetic` marker (`"synthetic"` absent from every
`data_manifest.json`; the kits' synthetic smoke writes one into its own temp copy only), so no run was refused on
that ground; the record checker re-checks the marker in every run's `work/data/data_manifest.json`.

## 6. GPU gate and co-tenancy

Paper A gate (`r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`) immediately
before the smokes: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`
(capture `paper_a/gate_smoke_*.json`); the pre-run GPU snapshot is `gpu/before_*` at 01:52:57Z (the 02:08Z artifact is `paper_a/gate_smoke_20261119T020823Z.json`).

Two cards were idle at selection time and used: GPU 2 `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154` and GPU 6
`GPU-3b36edea-1a09-a37e-aa42-8277c7319e77` (each 5 MiB used / 48,427 MiB free / 0 %, no compute app). The other
six cards carried other users' jobs throughout and were never used. Every smoke ran in its own
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` (the enforced memory cap recorded
as `memory_method: external`), with `AR_TEST_CGROUP_PARENT` set to the delegated scope and `taskset` CPU
affinity (mlab chain `0-7`, mlgym chain `8-15`; the two chains ran concurrently, one per card). Observed peak
per-run GPU memory: **~2.85 GB (2,853 MiB)** for the torch nodes and **~2.0 GiB** (recorded) for autoresearch — under the
8 GiB cap; each node's card returned to 5 MiB / 0 % after its own runs (`gpu_before.txt` / `gpu_after.txt` in every runs
root), no compute app was added or removed except our own, and the closing snapshot shows both cards idle. No
Track G U2/census run was started; the smokes are the per-node port smoke only.

## 7. Per-node isolated smokes — attempt 1 (PATH defect) and attempt 2 (result)

**Attempt 1 (kept, not deleted).** `port_smoke_gpu.py` was started with the node environment's Python but
without that environment on `PATH`. The node spec's `run_command` is `python3 run_fixed_budget.py`, so inside the
sandbox `python3` resolved to `/usr/bin/python3` (3.10, no torch): the baseline run failed with
`ModuleNotFoundError: No module named 'torch'` in `ar_worker.py`, the smoke then failed `check_baseline_log`
("loss_regex matched no line of the baseline log"). Only the per-edit runs (which the smoke passes with
`interpreter=sys.executable`) succeeded. Affected: mlab_cifar10 and mlgym_cifar10 (the later nodes were stopped
for the fix). Partial outputs are preserved under
`/home/dowling/r1_engineering/iso_kit_update_20261119/smoke/runs/` with logs `smoke/{mlab_cifar10,mlgym_cifar10}.log`;
this is an operational requirement, not a kit defect: **the smoke must be started with the node's Python
environment first on PATH** (`PATH=…/envs/torch312/bin:$PATH`), because fix B binds the smoke's
`sys.executable` chain and the spec command then finds the same `python3`.

**Attempt 2 (with `PATH` fixed).** Each node: fresh runs-root outside the repository, same GPU/CPU/cgroup
settings, `smoke_one.sh` launching `python3 -m tests.trackg.port_smoke_gpu` through the delegated 8 GiB scope.
Command shape (per node):

```
PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH \
PYTHONPATH=src CUDA_VISIBLE_DEVICES= AR_TRACKG_DATA_ROOT=…/data \
taskset -c 0-7 <envs/torch312/bin/python> -m tests.trackg.port_smoke_gpu \
  --node <node> --gpu-uuid <GPU-…> --cpus 0-7 \
  --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0" \
  --runs-root /home/dowling/r1_engineering/iso_kit_update_20261119/smoke/attempt2/runs/<node> \
  --provisional-timeout 1800
```

| node | kit tip | smoke result | baseline / repeat B2 metric | record gate (`verify_records`/`collect_smoke_summary`) |
|---|---|---|---|---|
| mlab_cifar10 | mlab `fb6e7d7` | **PASS** `CHECKLIST_E_PASSED`, exit 0, 9 runs | 0.5152 / 0.5152 | `effective: true`, `waivers {}`, `exceptions []` on all executed runs; 9/9 records complete |
| mlab_imdb | mlab `fb6e7d7` | **PASS** `CHECKLIST_E_PASSED`, exit 0, 9 runs | 0.9048 / 0.9048 | same |
| mlab_ogbn_arxiv | mlab `fb6e7d7` | **PASS** `CHECKLIST_E_PASSED`, exit 0, 9 runs | 0.275982 / 0.275982 | same |
| mlgym_cifar10 | mlgym `f07875d` | **PASS** `CHECKLIST_E_PASSED`, exit 0, 9 runs | 0.491 / 0.491 | same |
| mlgym_fmnist | mlgym `f07875d` | **PASS** `CHECKLIST_E_PASSED`, exit 0, 9 runs | 0.861667 / 0.861667 | same |
| autoresearch_fixedtokens | ar `448f682` | **BLOCKED (condition 7)** — see §8 | baseline divergent/nonzero_exit (returncode 12) after 32,768,000 tokens / 77.6 s | `effective: false`, `waivers {}`, `exceptions ["shared_dev_shm"]`; worker `cuda_open` invalid-resource-handle |

Each PASS node's 9 runs are: `s000_baseline` (ok), `s001` frozen-path diff refused with `scope_violation`,
`s002` broken diff `divergent/non_finite_loss`, `s003` first declared edit (kept), `E1…E4` every declared edit
(ok), `B2` second baseline with the same seeds (ok, same metric as the baseline). The check also verifies the
baseline log's loss/step lines, exactly one metric line in the result channel (never in the log), the sealed test
line, no stray carriage returns, complete records and `not_forced == ["dataloader_workers"]`. Runs-root and record
paths (all outside the repository):

```
/home/dowling/r1_engineering/iso_kit_update_20261119/smoke/attempt2/runs/<node>/
  runs_smoke/s000_baseline/run_record.json   # baseline, 9 records include s001–s003
  runs_smoke/s001/run_record.json            # frozen diff refused (not executed, no isolation fields by design)
  runs_smoke/s002/run_record.json            # broken diff divergent
  runs_smoke/s003/run_record.json            # first declared edit
  runs_edits/E1..E4/run_record.json          # declared edits
  runs_edits/B2/run_record.json              # repeat baseline
```

Baseline record sha256 / deployed pin / GPU (the same CPU-masked tests verify every record):

| node | baseline `run_record.json` sha256 | deployed `frozen_pin_sha256` | GPU UUID in `limits.gpu_uuids` | cgroup kill |
|---|---|---|---|---|
| mlab_cifar10 | `e74912cca8284aa90e4bbb6f907ed2ad4f2059af29920314ac3067d58a6fc3f1` | `a459b3d823075953d05422594cc97fa743723f22e79e1f8368480007dd041388` | `GPU-f439cca8-…` | `cgroup.kill`, empty, removed |
| mlab_imdb | `71e859582644ed6abd9978964b89a5eb6d2b8a260dc9df16522e22ccbce18e97` | `c169a6b875733cdb03d223659d06cc9a6839dd6255a924c420f10982bbefbbb0` | `GPU-f439cca8-…` | same |
| mlab_ogbn_arxiv | `9d4f980cb5b68ece71b3827a74d2960b1e25b4429f91fdea2be6cc26a18ab2cd` | `5ff5824ac22783f05f84b84d6d3222e8f1f4ddbc118e6bb1f657041bfb3285ad` | `GPU-f439cca8-…` | same |
| mlgym_cifar10 | `5f6ada868523f63af93ba2924f4400caa676254bac8a8c55ad2e93361456d116` | `817c90340e7ae004b7cd7161f899cb159a91ae482febc9a7f9ea2d9969f76e62` | `GPU-3b36edea-…` | same |
| mlgym_fmnist | `aea01795f3c1ff96465fc5f8936f02ef30824d9b5aadb699b76ea9f3e9713951` | `ef8043389dbd55a9a01d192227f0483daf2a406043b0a1feaf74eba4d858ddee` | `GPU-3b36edea-…` | same |

Full per-run JSON (run id, outcome, effective, waivers, exceptions, pin, record/log sha256) is in
`smoke/attempt2/summary_all_torch.json`; the smoke stdout (one JSON line per run, `CHECKLIST_E_PASSED`) is in
`smoke/attempt2/<node>.log`. Attempt-1 partial records are under `smoke/runs/` and were not deleted or reused.

## 8. autoresearch_fixedtokens GPU smoke — condition 7 BLOCKED (attempted last)

Run after all five torch-node smokes, same settings (GPU 2, cpus 0-7, 8 GiB scope, `PATH` fixed, runs-root
`smoke/attempt2/runs/autoresearch_fixedtokens`). The baseline completed its full 32,768,000-token training step
(77.6 s, peak VRAM 1,980 MB) and then failed in the frozen worker at the CUDA-IPC hand-off:

```
AR_ERROR worker bind_cuda: … ar_worker.py bind_cuda → iso.cuda_open(meta["buffer"])
  → torch.UntypedStorage._new_shared_cuda(…)
RuntimeError: CUDA error: invalid resource handle
```

i.e. exactly the driver/namespace limitation the accepted fix review recorded (CUDA IPC does not cross a user
namespace on this host/driver, driver 545.23.08), not a defect of the merged A/B code. All nine smoke runs were
recorded: every executed run is `divergent` (returncode 12, no metric reported) except the deliberately broken
diff `s002` (`divergent/non_finite_loss`), the frozen-diff run `s001` is refused (`scope_violation`, not
executed), and **every** executed record is `effective: false`, `waivers {}`,
`exceptions ["shared_dev_shm"]` (the node's designed exception) — the record gate `collect_smoke_summary`/
`verify_records` passes on those fields (`issues []`). The smoke itself exits 1 at its own `check_baseline_log`
assertion (exactly one metric line in the baseline result channel), which is the correct refusal here: no honest
result was produced. The baseline record
(`smoke/attempt2/runs/autoresearch_fixedtokens/runs_smoke/s000_baseline/run_record.json`, sha256
`2090936167f58df7a77fac98aa2966c4d4e8c7e78c1eac898a84ab3a29fd8c61`) carries deployed pin
`91e50af690fcc6e21894f8f3b392c01ab5d41d2793cb2f44565f062e754c96a5`, and the run's own log carries the
`AR_ERROR` above. GPU 2 returned to 5 MiB / 0 % after the smoke (final snapshot), no compute app left behind. The
kit smoke cannot be claimed as passed on Ada; **condition 7 remains BLOCKED / NOT PASS**.
Per review condition C3 no autoresearch GPU run (and no GPU node that needs CUDA IPC across the namespace) may
be started for U2 until the logits-transfer design decision (socket/CPU buffer, or a documented
non-PID-namespace GPU mode with a waiver) is recorded and `cuda_open`'s missing `torch.cuda.init()` is fixed in
that same reviewed change. This per-node autoresearch smoke is the C2-mandated BLOCKED-state check (it failed closed; it is **not** a U2/evidence run), and C3 stays in force for the future U2. Record paths are under
`smoke/attempt2/runs/autoresearch_fixedtokens/runs_smoke/` (s000_baseline, s001, …) and the smoke log is
`smoke/attempt2/autoresearch_fixedtokens.log`. The remaining smoke runs were allowed to finish and their records
preserved; nothing was deleted.

## 9. STOPs / not run

- **House Prices — STOP (missing input).** `$HOME/r1_inputs/house-prices/train.csv` is absent
  (`/home/dowling/r1_inputs` does not exist), so `mlgym_houseprice`'s `setup_command` cannot run and no
  `data/mlgym_houseprice` exists. Per the instructions the MLGym copy was **not** used (the old U3 node dir
  `harness_mlgym/nodes/mlgym_houseprice` has no data link and was left untouched). The node's pin was updated
  (`88d359f2…`) but its smoke was **not run**. Needs the user's Kaggle `train.csv` (or a recorded decision) before
  U2.
- **Breakout/MinAtar — NOT RUN (JAX environment not ready, no data).** `envs/jax312` cannot import JAX on Ada:
  `import jax` fails before use (`jax 0.4.35` + `nvidia-cuda-nvcc-cu12` namespace package →
  `TypeError: argument should be a str or an os.PathLike object … not 'NoneType'` in
  `jax._src.lib._try_cuda_nvcc_import`), and there is no `data/mlgym_breakout_minatar` tree. Installing
  `requirements_gpu.txt` (jax[cuda12]) and fetching the MinAtar data is required before that node can be tried;
  the node's pin was updated (`cec562e6…`) but its smoke was **not run**.

## 10. Remaining before U2

1. **Root: review and push the three kit branches.** They are local-only: tips `448f682 / fb6e7d7 / f07875d`
   on `mac-trackg-iso-{ar,mlab,mlgym}-20261117`; origin refs still at `5d3dccc / 0aae2f6 / 061d638`. The two
   commits per kit and the pin values are above.
2. **Census: commit the pins with a stated convention.** The table in §3 is the committed-file pin (fix report /
   review convention). Run records carry the deployed pin that additionally hashes the `data` symlink target
   (e.g. mlab_cifar10 `a459b3d8…` vs `1f047ad7…`); the census must record which one it commits so later campaigns
   are compared like-for-like.
3. **autoresearch condition 7 is a hard pre-condition (review C3).** The GPU smoke is BLOCKED; no autoresearch
   U2 GPU run until the logits-transfer design change + `cuda_open` `torch.cuda.init()` fix is reviewed. The other
   five nodes' U2 units can proceed.
4. **Data setup is runtime-only and must be redone on the deploy host** (uncatalogued here as commits): the five
   manifests and the step-2 setup commands are in §5; House Prices needs its Kaggle file; Breakout needs its JAX
   env and data.
5. **Static-test environment repairs (not kit regressions):** put `envs/torch312/bin` first on `PATH` when
   running `tests/trackg` (otherwise the round-2 child-kill test fails under Python 3.10), and install
   `langchain-openai` in the node env to clear the known t0 identity failure — or record both as accepted
   environment exceptions.
6. **Attempt-1 outputs** (PATH defect) are preserved under `smoke/runs/` and logs `smoke/*.log`; they are
   superseded by attempt 2 but not deleted.

## 11. Integrity of this work

No push, force push, branch rewrite or history edit; the only commits are the six local kit commits above plus no
change to any other branch (fix branch and all other worktrees untouched: their tracked files are clean before and
after; after the smokes the three kit worktrees show only the six untracked runtime `data` symlinks created by
`setup_command`, as expected/documented in §5, and every branch tip is the committed sha listed in §2).
No deletion anywhere: attempt-1 outputs, old data trees and old U3 node dirs were left in place; new run roots
are outside the repository. No TASL-7/TASL-2/HTCondor/deepthought interaction, no root/sudo, no U2/census/GPU-kit
run. GPU use was limited to the two idle cards (2 and 6), each run under a delegated 8 GiB memory cap, with
before/after snapshots; other users' cards/processes were not touched, and both cards returned to idle. On the
Mac side this report and its captures are untracked files for the root agent to review and commit; the kit
commits exist only on Ada and were not pushed.

## 12. Evidence index (Ada `/home/dowling/r1_engineering/iso_kit_update_20261119/`, captures next to this report)

- `git/` — `pre_state.txt`, `pre_tips.txt`, `post_state.txt`, `apply_all.log`, `update_{ar,mlab,mlgym}.log`
  (merge/copy/pin/commit records, diffstats, tip shas, clean status), commit messages `msg_*.txt`.
- `pins/` — `old_*.json`, `new_*.json` (committed-file pins), `deployed_*.json` (with data links),
  `pin_changes.json` (`changed_frozen_files == ["ar_isolated.py"]` for all 8).
- `pytest/` — `pre_kit_*.log` (pre baseline), `pre_iso_ar.log` (old-core hang, timeout 124), `post_full_*.log`
  (full post run), `post_iso_ar.log` (27 passed, 1 skipped), `post_childkill_pathfix.txt`.
- `data/` — `setup_*.log` (setup command, data link, manifest sha256), `setup_state.txt`.
- `smoke/` — attempt 2: `smoke/chain_{A,B}_attempt2.log` (staged in captures under `smoke/attempt1/`), `smoke/attempt2/<node>.log` (smoke stdout with `CHECKLIST_E_PASSED`), `smoke/attempt2/summary_all_torch.json`, `smoke/attempt2/summary_<node>.json` only for three nodes (the two cifar10 nodes use `smoke/attempt2/records_<node>.json`), `smoke/attempt2/<node>/gpu_{before,after}.txt` and `smoke/attempt2/<node>/<run_id>/` (each run's `run_record.json`, `run.log`, `result_channel.txt`); attempt 1: `smoke/chain_A.log`, `smoke/chain_B.log`, `smoke/mlab_cifar10.log`, `smoke/mlgym_cifar10.log`, `smoke/attempt1/<node>/<run_id>/` (partial, preserved in place on Ada); autoresearch: `smoke/attempt2/autoresearch_fixedtokens.log`, `smoke/attempt2/summary_autoresearch_fixedtokens.json`, `smoke/attempt2/records_autoresearch_fixedtokens.json`.
- `paper_a/`, `gpu/` — Paper A gate JSON before the smokes, pre-run GPU snapshot, chain close snapshots.
- `scripts/` — every helper used (`apply_kit_update.sh`, `run_pytest.sh`, `run_static_tests.sh`,
  `compute_pins.py`, `pin_diff.py`, `setup_node.sh`, `smoke_one.sh`, `run_chain.sh`, `verify_records.py`,
  `collect_smoke_summary.py`).
- The sibling dir `TRACKG_ISO_KIT_UPDATE_20261119_captures/` mirrors these files (341 files, 3.4 MB); its
  `SHA256SUMS` is the sha256 of every capture file and was verified after copying (341/341).

ENGINEERING_ONLY; AI-assisted. Report and captures are uncommitted on the Mac ops worktree; kit commits on Ada are
local and expected to be reviewed and pushed by the root agent.
