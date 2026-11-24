# T1 data-manifest census erratum — `mlgym_fmnist` and `mlgym_cifar10` (option A), 22 November 2026

**Status: CENSUS ERRATUM evidence record, submitted for independent review. ENGINEERING_ONLY data-provenance
record — not an evidence row; no noise floor, no D21/D28, no T1 label.** Authority: the author row
`R1-T1-DATA-MANIFEST` (PLAN, "22 November 2026 (c) — G.5 autoresearch scope and harness pins; MLGym data
manifests; autoresearch G.1b environment (author)"), option A: *"for these two nodes the census
`data_manifest_sha256` becomes the manifest the frozen environment produces, recorded as a census erratum with an
independently reviewed record (array sha256 and bytes on Ada, TASL-2 and TASL-7; the manifests produced on both
hosts byte-identical; the origin of the 5.0.1 manifest). The whole-manifest comparison rule and all code stay
unchanged."* AI-assisted. This record writes only the two new paths
`docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md` and
`…_captures/`; it changed no data, manifest, harness, job or lease state, took no GPU lease, touched no
HTCondor/deepthought resource, deleted nothing and pushed nothing.

## Result (the corrected census values)

| node | corrected `data_manifest_sha256` (option A) | bytes | produced by | census value it supersedes (for this node only) |
|---|---|---|---|---|
| `mlgym_fmnist` | `24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32` | 951 | frozen `torch312` on TASL-2 **and** TASL-7 — byte-identical | `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` (951 B) |
| `mlgym_cifar10` | `54d3a74d342d285fe724538a46872d028639533b4280557b00062e3d3c706100` | 959 | frozen `torch312` on TASL-2 **and** TASL-7 — byte-identical | `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` (959 B) |

- The two corrected manifests differ from the census manifests on **exactly one line**:
  `"datasets": "5.0.1"` → `"datasets": "3.6.0"` (`source.datasets`; five bytes; diff captured in
  `_captures/manifests/census_vs_corrected.diff`). All whole-file hashes above are `sha256` of
  `data_manifest.json` bytes; bytes are the file size.
- **No data bytes differ.** All four `.npy` arrays of each node have the same `sha256` and byte size at every
  location checked: the Ada census root, the staged T1 data root on the host that has it, and the fresh
  frozen-environment reproductions on **both** TASL hosts (§1).
- The whole-manifest comparison rule and all code stay unchanged (option A). Only the two census values above
  are superseded; every other census value remains as recorded (§4).

## 1. Arrays and whole-manifest hashes at the three census locations (plus reproduction)

Method: on each host, `sha256sum train_x.npy train_y.npy test_x.npy test_y.npy data_manifest.json` and
`stat -c %s` (GNU coreutils on Linux); Ada and both TASL hosts were read-only for the census roots. Raw output:
`_captures/hosts/Ada_census.txt`, `_captures/hosts/TASL-2_census.txt`, `_captures/hosts/TASL-7_census.txt`;
produced roots: `_captures/setup/TASL-2_setup.log`, `_captures/setup/TASL-7_setup.log`.

### 1.1 Locations, whole-manifest sha256 (`data_manifest.json`) and bytes

| location | path (`<root>/<node>/`) | `mlgym_fmnist` manifest | `mlgym_cifar10` manifest | when read/produced (UTC) |
|---|---|---|---|---|
| Ada census | `/home/dowling/r1_trackg_20261117/data/` | `8d28287b…` 951 B, `source.datasets=5.0.1` | `c0ef1168…` 959 B, `source.datasets=5.0.1` | read 2026-11-22T10:43:02–10:43:06Z |
| TASL-2 staged T1 data | `/home/dowling/r1_tracks/t1_tasl/data/` | `24cb3448…` 951 B, `3.6.0` | **absent** (no TASL-2 T1 job for it) | read 2026-11-22T10:42:03–10:42:05Z |
| TASL-7 staged T1 data | `/home/dowling/r1_tracks/t1_tasl/data/` | **absent** (no TASL-7 T1 job for it) | `54d3a74d…` 959 B, `3.6.0` | read 2026-11-22T10:41:34–10:41:37Z |
| TASL-2 fresh, this record | `/home/dowling/r1_engineering/tasl_data_manifest_20261122/TASL-2/data/` | `24cb3448…` 951 B | `54d3a74d…` 959 B | produced 10:40:17–10:40:49Z |
| TASL-7 fresh, this record | `/home/dowling/r1_engineering/tasl_data_manifest_20261122/TASL-7/data/` | `24cb3448…` 951 B | `54d3a74d…` 959 B | produced 10:40:19–10:41:03Z |

The full hashes: fmnist `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` (census),
`24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32` (frozen env / T1 staged / both hosts);
cifar10 `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` (census),
`54d3a74d342d285fe724538a46872d028639533b4280557b00062e3d3c706100` (frozen env / T1 staged / both hosts).

TASL-2 has no staged T1 `mlgym_cifar10` and TASL-7 has no staged T1 `mlgym_fmnist`; the staged T1 data root
exists only for the nodes whose T1 jobs ran on that host (TASL-2: the G.1b fmnist job; TASL-7: the cross-check
cifar10 job). §2 supplies both nodes on **both** hosts from fresh scratch roots, so the array/byte coverage below
is complete.

### 1.2 Array `sha256` and bytes — identical at every location

`mlgym_fmnist` (all four arrays: Ada census **=** TASL-2 staged **=** TASL-2 fresh **=** TASL-7 fresh):

| array | sha256 | bytes |
|---|---|---|
| `train_x.npy` | `fa55843a054d8d313e1599d2541666e5febd6f186948f84db90dd89f854fa02e` | 47,040,128 |
| `train_y.npy` | `eb6efccc70db136ce327076edeadbbcba39b38ab16fd8f89b0625f62fc605f24` | 480,128 |
| `test_x.npy` | `fa687ea6e35cd511e68bc9cd5049edbadf6eb7dfde574e880a3325309e5aadfd` | 7,840,128 |
| `test_y.npy` | `33e7c41e1d27e7ea46528a86fd6d54e0eb0d60f705e95ae5e9c956635f269cbc` | 80,128 |

`mlgym_cifar10` (all four arrays: Ada census **=** TASL-7 staged **=** TASL-2 fresh **=** TASL-7 fresh):

| array | sha256 | bytes |
|---|---|---|
| `train_x.npy` | `9a8bd8090cac5cb24ff54ef6d51bbbdbed5c0b5e7d97cb9ddf9c2a894c21b0eb` | 153,600,128 |
| `train_y.npy` | `9e2ee9261f6a7c6509b35aaa7161bf15d6d99673bbcac04130702d12a6da88d3` | 400,128 |
| `test_x.npy` | `b57763d00c64ed188c839aa488139ed34ece7a6ef2fcb6a770238c57a756a452` | 30,720,128 |
| `test_y.npy` | `fc48d9ecfdbeacce2dacf004498170f2df12e75e3485475017d2663b587a92f3` | 80,128 |

These are the same file hashes each manifest records for its own files (`_captures/manifests/*.data_manifest.json`),
i.e. the frozen-environment manifests are internally consistent **and** the data they describe is the census data.

## 2. Reproducing `setup_command` on both TASL hosts (frozen `torch312`, fresh scratch roots)

### 2.1 Fixed inputs

- Harness `/home/dowling/r1_tracks/t1_tasl/harness`, `git rev-parse HEAD` =
  `c025f89aeafc2199bf3487b4bcaa16678273c702`, detached HEAD (checked with `git status -sb`: `## HEAD (no branch)`), `git diff --stat` empty;
  `git status --porcelain` held only untracked `data` symlinks before the runs and the identical list after
  (TASL-2: `nodes/mlab_imdb/data`, `nodes/mlab_ogbn_arxiv/data`,
  `third_party/mlgym/nodes/mlgym_fmnist/data`, `third_party/mlgym/nodes/mlgym_houseprice/data`; TASL-7:
  `nodes/mlab_cifar10/data`, `third_party/mlgym/nodes/mlgym_cifar10/data`). Node spec files identical on both
  hosts (`mlgym_fmnist.yaml` `a9844f01…`, `mlgym_cifar10.yaml` `a03585ff…`), captured in
  `_captures/hosts/setup_commands.txt`.
- Node `setup_command` (read from the committed node YAMLs at `c025f89a`):
  `mlgym_fmnist`: `test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_fmnist"`
  (node dir `third_party/mlgym/nodes/mlgym_fmnist`); `mlgym_cifar10`: same with `…/mlgym_cifar10`.
- Frozen environment `envs/torch312` on both hosts: Python 3.12.16, `torch 2.6.0+cu124`, `datasets 3.6.0`,
  `huggingface_hub 0.36.2`, `numpy 2.5.4`; `uv pip freeze` sha256
  `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, byte-identical to the committed freeze
  `sweep2/g1b/env/torch312.freeze.txt` on TASL-2 **and** TASL-7 (`_captures/env/*`). No GPU was assigned, no
  lease was acquired, and `taskset` CPU pinning was used (TASL-2 `16-31`; TASL-7 `16-23`, its non-GPU 8-CPU
  tail; the T1 GPU jobs use `0-7`).
- Dataset revisions resolved live and recorded in the produced manifests:
  `zalando-datasets/fashion_mnist` `531be5e2ccc9dba0c201ad3ae567a4f3d16ecdd2` (U1 prefix `531be5e`),
  `uoft-cs/cifar10` `0b2714987fa478483af9968de7c934580d0bb9a2` (U1 prefix `0b27149`) — the same revisions as in
  the census manifests.

**Deviation, disclosed:** the runs used a fresh, byte-identical extraction of the same commit in the scratch
root instead of the live node directories. Reason: the live node directories at `c025f89a` already carry
untracked `data` symlinks into the **staged T1 data**; `ar_data.link_data()` refuses to replace a link that
points elsewhere (`… already links to …; not replaced`), so running the live path would have failed after
writing data on one node and created new links into the shared T1 harness on the other. To keep staged T1 data
and the live T1 harness untouched, the copy was extracted with
`git -C /home/dowling/r1_tracks/t1_tasl/harness archive c025f89a | tar -x -C <scratch>/harness_c025f89a`
(archive sha256 `98723a283be7494817558f021cb81a876371f035a43f09a4f596d7be06c3f872`, **identical on both hosts**,
captures `_captures/hosts/TASL-{2,7}_env_libs.txt`), and the node files were verified byte-identical to the live
harness before the runs (`prepare_data.py` `e50053587218f31cc14ab31b51b30f659149302bc28ff78514736dcde36dbb57`,
`ar_data.py` `85cec63fffac560fd99b254fb40751efbb392754356e6cdb21c214f924ea3aad`, `cmp` OK; setup logs). The
data manifest's content does not depend on the node directory path (it records only file hashes, the dataset
revision and the library versions), so the produced manifests are the manifests the frozen environment produces.

### 2.2 Exact commands (per node, per host; `set -x` captured in `_captures/setup/*_setup.log`)

```bash
ROOT=/home/dowling/r1_engineering/tasl_data_manifest_20261122/<TASL-2|TASL-7>
PY=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin
cd "$ROOT/harness_c025f89a/third_party/mlgym/nodes/<mlgym_fmnist|mlgym_cifar10>"   # node dir of c025f89a
PATH="$PY:$PATH" AR_TRACKG_DATA_ROOT="$ROOT/data" HF_HOME="$ROOT/hf" PYTHONDONTWRITEBYTECODE=1 \
  taskset -c 16-31 \
  bash -c 'test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/<node>"'
# TASL-7: taskset -c 16-23
```

Fresh scratch roots (new directories; no existing data reused, no staged T1 path referenced): data
`<ROOT>/data/<node>`, HF cache `<ROOT>/hf` (fresh per host — the runs therefore do not depend on, and do not
write, the T1 HF cache `/home/dowling/r1_tracks/t1_tasl/hf`), harness copy `<ROOT>/harness_c025f89a`. Python
resolved to `…/envs/torch312/bin/python3` on both hosts (logged in the setup captures).

### 2.3 Results

| host | node | start–end (UTC) | rc | produced `data_manifest.json` | bytes | arrays |
|---|---|---|---|---|---|---|
| TASL-2 (`TASL-2`, uid 1008) | `mlgym_fmnist` | 2026-11-22T10:40:17Z–10:40:28Z | 0 | `24cb3448…` | 951 | equal to §1.2 |
| TASL-2 | `mlgym_cifar10` | 2026-11-22T10:40:28Z–10:40:49Z | 0 | `54d3a74d…` | 959 | equal to §1.2 |
| TASL-7 (`TASL-7`, uid 1011) | `mlgym_fmnist` | 2026-11-22T10:40:19Z–10:40:29Z | 0 | `24cb3448…` | 951 | equal to §1.2 |
| TASL-7 | `mlgym_cifar10` | 2026-11-22T10:40:29Z–10:41:03Z | 0 | `54d3a74d…` | 959 | equal to §1.2 |

Setup printed `wrote … sha256 24cb3448…` / `54d3a74d…`, then `AR_DATA manifest_sha256=… files=4`, on both hosts.

- **Both hosts' manifests are byte-identical per node**: `cmp` of the fetched files
  `_captures/manifests/tasl2_*.data_manifest.json` vs `tasl7_*.data_manifest.json` reports no difference;
  re-hashed locally: fmnist `24cb3448…` (951 B), cifar10 `54d3a74d…` (959 B), on each host.
- **They equal the T1 staged manifests** for the node each host has: TASL-2 fresh = TASL-2 staged fmnist
  (`24cb3448…`), TASL-7 fresh = TASL-7 staged cifar10 (`54d3a74d…`) — i.e. the T1 jobs already used the frozen
  environment's manifest; there is no data drift.
- The only difference from the census manifests is `source.datasets` 5.0.1 → 3.6.0
  (`_captures/manifests/census_vs_corrected.diff`, line 24). Nothing else in the file changed.

### 2.4 Host facts and disk

| host | kernel | CPUs | uid | disk (`/dev/nvme0n1p2`, 1.9 T) before → after the setup runs |
|---|---|---|---|---|
| TASL-2 | `6.8.0-149-generic` | 32 | 1008(dowling) | used 1,533,198,630,912 → 1,533,805,236,224 B; avail 378,965,622,784 → 378,359,017,472 B (81%) |
| TASL-7 | `6.8.0-149-generic` | 24 | 1011(dowling) | used 1,385,614,561,280 → 1,386,221,129,728 B; avail 526,549,692,416 → 525,943,123,968 B (73%) |

Scratch footprint (harness copy + fresh HF cache + both node data sets): 604,684,817 B on TASL-2,
604,687,260 B on TASL-7 (`du -sb`, see `_captures/hosts/no_t1_or_lease_touch.txt`). Ada: 46,214,828,032 B free
(98 % used) at 10:43:02Z; **nothing was written on Ada** (read-only census only).

### 2.5 Staged T1 data and T1 state — untouched

Staged T1 data was only read (`ls`, `sha256sum`, `stat`): fmnist files on TASL-2 keep mtimes 2026-11-21
14:42:49 −0800 (22:42:49Z), cifar10 files on TASL-7 keep 2026-11-21 16:26:53–54 −0800 (2026-11-22T00:26:5xZ),
and the other staged manifests keep their census-identical hashes (captured in
`_captures/hosts/TASL-{2,7}_census.txt`). No T1 job was started or stopped; no HTCondor/deepthought resource was
used; nothing was deleted (only new scratch directories were created).

**Disclosed external activity (not this record's commands):** during this record's read-only census window,
`/home/dowling/r1_locks/gpu0.lock` on TASL-2 was written by another process at 2026-11-22T10:42:04.636Z
(mtime = ctime; the lease itself was not opened/acquired by any command in this record), and a different
checkout `/home/dowling/r1_tracks/t1_tasl/harness_ar` (HEAD `2d09f9a9…`) was written in the same seconds. That
looks like concurrent external work on the host; it has no effect on any hash or manifest here (those paths are
outside everything this record read or produced). Evidence:
`_captures/hosts/TASL-2_external_activity_disclosure.txt`, `…_lease_probe{,2,3}.txt`. Flagged for the lead.

## 3. Origin of the `source.datasets: 5.0.1` census manifest on Ada

**Determinable: the provenance is the Ada venv `/home/dowling/r1_trackg_20261117/envs/torch312` in its
pre-re-pin state, when it contained `datasets 5.0.1`; the same venv path was re-pinned to `datasets 3.6.0` at
2026-11-17T23:44:40Z, 7½ minutes after the two manifests were written.** Evidence (all read-only, captured in
`_captures/hosts/Ada_census.txt`, `_captures/hosts/Ada_env_libs.txt`, `_captures/env/`):

1. **Only one environment on Ada can produce a `datasets`-based manifest.** `envs/torch312` is the only venv
   with `datasets` installed; `envs/jax312` reports `datasets ABSENT`; `/usr/bin/python3` (3.10.12) has no
   `datasets` either, and the only other venv found on the host
   (`/home/dowling/agent-checkpoint-intervention/.venv`, Python 3.13) also lacks it. The two census manifests
   record `datasets 5.0.1`.
2. **That venv contained 5.0.1 at census-write time.** The census manifests were written
   `2026-11-17 15:36:57.889 -0800` (cifar10) and `15:37:08.589 -0800` (fmnist) = `23:36:57.89Z` /
   `23:37:08.59Z`. The venv's pre-pin freeze capture from the same day
   (`runs/u2_autoresearch_fixedtokens_20261117T094847Z/env_freeze.txt`, 77 lines, sha256
   `dea8a9df3a92f233009d5480921c9685c24ecd1e91e932d9efdfe53fb860eecd`, committed `a411d21e`) contains
   `datasets==5.0.1`; the committed U2 raw-cost proposal `docs/r1/proposals/TRACKG_U2_RAWCOST_20261117.md`
   (commit `61c8f719`) records the same environment with `datasets 5.0.1`. The UV cache holds the
   `datasets 5.0.1` archive (`~/.cache/uv/archive-v0/mphP230sn9Z0K-tq/datasets-5.0.1.dist-info`, mtime
   `2026-11-17 01:01:19 -0800`).
3. **The re-pin to 3.6.0 happened after the manifests.** `site-packages/datasets-3.6.0.dist-info` and the
   venv `bin/` have mtime `2026-11-17 15:44:40.05 -0800` (23:44:40Z); UV's 4.0.0 archive is from
   `15:43:32 -0800` (the 4.0.0/5.x `Column` regression that forced the pin, `TRACKG_U2_DATA_PREP_20261117.md`);
   the 3.6.0 archive from `15:44:40.02 -0800`. The current `uv pip freeze` of that same venv is
   `d2e70fe4…` with `datasets==3.6.0` and is byte-identical to the committed freeze and to both TASL envs.
4. **Timeline corroboration.** The `data` symlinks the census setup created in `harness_mlgym` are stamped
   `15:36:58.009 -0800` (cifar10) and `15:37:08.629 -0800` (fmnist) — the census setup run linking the two data
   directories; the next manifest written, `mlab_imdb` at `15:45:26.705 -0800`, already records
   `datasets 3.6.0` (46 s after the 3.6.0 install), exactly as expected after the re-pin.

So the census manifests were not produced by an unknown or other environment: they are the frozen
`envs/torch312` venv, written 7–8 minutes before the pin that changed it to `3.6.0`. That is why the census
value is stale rather than wrong data: the arrays never changed (§1, §2).

## 4. Every other census node: recorded library version vs its frozen environment

Checked all census nodes that have a `data_manifest.json` (7 of 8; `mlgym_breakout_minatar` has
`setup_command` empty / no data setup / census `data_manifest_sha256: none (simulated)`). Full detail:
`_captures/comparisons/other_nodes.txt`; manifest `source` blocks in `_captures/hosts/Ada_census.txt`.

| node | frozen env | library version recorded in its manifest | frozen env value | differs? |
|---|---|---|---|---|
| `autoresearch_fixedtokens` | `torch312` (Ada data-prep env) | none recorded (base URL/revision/preparation only) | n/a | no (n/a) |
| `mlab_cifar10` | `torch312` | `torchvision 0.21.0+cu124` | `torchvision.__version__` `0.21.0+cu124` | no |
| `mlab_imdb` | `torch312` | `datasets 3.6.0`, `transformers 4.49.0` | 3.6.0 / 4.49.0 | no |
| `mlab_ogbn_arxiv` | `torch312` | `ogb 1.3.6` | `ogb.__version__` 1.3.6 | no |
| `mlgym_cifar10` | `torch312` | `datasets 5.0.1` | 3.6.0 | **yes — this erratum** |
| `mlgym_fmnist` | `torch312` | `datasets 5.0.1` | 3.6.0 | **yes — this erratum** |
| `mlgym_houseprice` | `torch312` | none recorded (from-file CSV sha256/md5/rows only) | n/a | no (n/a) |
| `mlgym_breakout_minatar` | `jax312` | no data manifest (no data setup) | n/a | n/a |

**No other census node differs.** Every manifest that records a library version matches its frozen environment
(or records no library version at all), so the 5.0.1/3.6.0 mismatch is confined to the two MLGym nodes of this
erratum, consistent with §3 (both were written before the 17 Nov re-pin; `mlab_imdb`, written after it, records
3.6.0). The frozen environment used for the comparison is identical on Ada and both TASL hosts
(`uv pip freeze` sha256 `d2e70fe4…`, §2.1).

## 5. Conclusion

1. **Corrected census `data_manifest_sha256`** (option A: the manifest the frozen `torch312` environment
   produces; byte-identical on TASL-2 and TASL-7, and identical to the manifests the T1 jobs already used):
   - `mlgym_fmnist` = `24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32` (951 B);
   - `mlgym_cifar10` = `54d3a74d342d285fe724538a46872d028639533b4280557b00062e3d3c706100` (959 B).
   They supersede `8d28287b…` and `c0ef1168…` for these two nodes only; the change is exactly
   `source.datasets` 5.0.1 → 3.6.0.
2. **No data bytes differ**: the four `.npy` arrays of each node are `sha256`/bytes-identical on the Ada census,
   in the staged T1 data on the host that has it, and in the fresh frozen-environment reproductions on both
   TASL hosts (§1.2).
3. **Origin of the stale value**: Ada venv `/home/dowling/r1_trackg_20261117/envs/torch312` before its 17 Nov
   23:44:40Z re-pin from `datasets 5.0.1` to `3.6.0` (§3). The environment now reports 3.6.0 and is identical to
   the frozen T1 environment on both TASL hosts.
4. **No other census node differs** (§4).
5. The re-issued G.1b / cross-check / G.4 specs and notes are the coordinating chat's action after independent
   review of this record (option A); they must carry the two corrected values above, and the whole-manifest
   comparison rule and all code stay unchanged. The sealed TASL-2 nodes, staged T1 data, T1 jobs and Track P /
   lease state are untouched by this record.

## 6. Evidence, method notes, limitations

- Evidence directory: `docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122_captures/`
  (32 files; `SHA256SUMS` sha256 `8bc790875c6dc0bf4d336dcadbfede7381b150eb308828faedeb9c10950721d9`; verified
  with `sha256sum -c` — 32/32 OK). Layout: `setup/` (raw `set -x` setup logs of both hosts),
  `hosts/` (Ada/TASL-2/TASL-7 census, env-version and lease-probe captures), `manifests/` (the eight fetched
  manifest files, the census-vs-corrected diff, byte table), `env/` (full `uv pip freeze` of the frozen env on
  all three hosts; the pre-pin and committed freezes), `comparisons/other_nodes.txt`.
- Every claim above is reproducible from those captures: array/manifest hashes are raw `sha256sum` output;
  comparisons are `cmp`/`diff` output re-run locally on the fetched files; setup commands and times are the
  hosts' own `set -x` shell logs with `date -u`.
- Limitations: (i) the runs used a `git archive` copy of harness `c025f89a` rather than the live node
  directories, disclosed and justified in §2.1 (the copy's node files are byte-identical to the live ones, and
  the manifest content is path-independent); (ii) fresh scratch `HF_HOME` caches were used, so the runs prove
  the manifest is reproduced by the frozen environment from the hub at the recorded revisions, independent of
  any pre-existing cache; (iii) `mlgym_breakout_minatar` is out of scope (no data setup/manifest);
  (iv) hash reads were done with host `sha256sum`, not by re-deriving arrays in numpy.
