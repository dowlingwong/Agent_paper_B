# Independent review — T1 data-manifest census erratum (option A): `mlgym_fmnist` and `mlgym_cifar10`

**Reviewed record.** `docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md`,
sha256 `9b40944be4df5f214066d689f7f0537590ed95895f9754b55630d8e774077799` (280 lines, uncommitted at review
time). **Captures.** `docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122_captures/`,
`SHA256SUMS` sha256 `8bc790875c6dc0bf4d336dcadbfede7381b150eb308828faedeb9c10950721d9`, 32 listed files,
`sha256sum -c` → 32/32 OK (independently re-run). **Reviewed base.** branch `ops-tasl-20261116` @ `b93d8c88`,
record and captures untracked.

**Process.** Fresh reviewer, read-only. Local: hashing, `sha256sum -c`, `git cat-file`/`git show`, byte
diffs of the fetched manifest files, re-check of every capture hash. Hosts: read-only SSH to Ada
(`ssh -o BatchMode=yes experiment_zhixu`, host `ucrtasl`, uid 1030), TASL-2 (`ssh -o BatchMode=yes portal_zhixu`,
uid 1008) and TASL-7 (`ssh -o BatchMode=yes tasl7`, uid 1011), 2026-11-22T10:50–10:57Z; commands were
`ls`/`stat`/`sha256sum`/`cat`/`find -newermt`/`git rev-parse`/`git archive`/`git status` (with
`GIT_OPTIONAL_LOCKS=0`)/`uv pip freeze` (metadata read)/`nvidia-smi`/`ps`. No write of any kind was made on
any host, no job was started, no GPU/lease was acquired, no HTCondor/deepthought resource was touched, and no
data was produced. The only file written by this review is this file. Authority text checked against
`docs/r1/PLAN.md` heading line 1393 and row line 1398 (`R1-T1-DATA-MANIFEST`); the record quotes it correctly
and does what option A requires (census values only; whole-manifest comparison rule and code unchanged; no
T1 label/evidence row; ENGINEERING_ONLY).

## Verdict: **ACCEPTED** (corrected values independently reproduced; five documentation-precision findings, none
affecting a value or conclusion; editorial conditions C1–C3 in §4).

| required check | result |
|---|---|
| 1. corrected manifests `24cb3448…` 951 B / `54d3a74d…` 959 B; byte-identical on TASL-2 and TASL-7; equal to staged T1 manifests; census differs only `source.datasets` 5.0.1→3.6.0 | **PASS** |
| 2. four `.npy` sha256/bytes identical at Ada census, staged (where present) and fresh; no data bytes differ; staged T1 data untouched | **PASS** |
| 3. setup in frozen `torch312` (`c025f89a`, archive `98723a28…`, env freeze `d2e70fe4…`) into fresh scratch on both hosts; no GPU/lease; no T1 jobs | **PASS**, with finding F2 (the outer `taskset`/env wrapper is not in the captures) |
| 4. origin of the 5.0.1 census manifest determinable (Ada `envs/torch312` pre-re-pin) | **PASS** (determinable; chain independently reproduced) |
| 5. no other census manifest library version differs | **PASS** (one-sentence answer in §1.5) |
| 6. record/captures SHAs and accuracy; deviations disclosed; no overclaim | **PASS** for accuracy of values; findings F1–F5 for wording/evidence precision |

## 1. Verification against the live hosts (independent of the captures)

All values below were read from the hosts at 2026-11-22T10:50–10:57Z (UTC); the captures' own values were
hashed locally first, then each was re-derived live.

### 1.1 Manifests and byte-identity

| location | fmnist `data_manifest.json` | cifar10 `data_manifest.json` |
|---|---|---|
| Ada census `/home/dowling/r1_trackg_20261117/data/<node>/` | `8d28287b819353ee…` 951 B, mtime `2026-11-17 15:37:08.589 -0800`, `source.datasets=5.0.1` | `c0ef1168e9c575fe…` 959 B, mtime `2026-11-17 15:36:57.889 -0800`, `source.datasets=5.0.1` |
| TASL-2 staged `/home/dowling/r1_tracks/t1_tasl/data/mlgym_fmnist/` | `24cb34483c5a23b4…` 951 B, mtime `2026-11-21 14:42:49.673 -0800` | **absent** (verified) |
| TASL-7 staged `/home/dowling/r1_tracks/t1_tasl/data/mlgym_cifar10/` | **absent** (verified) | `54d3a74d342d285f…` 959 B, mtime `2026-11-21 16:26:54.493 -0800` |
| TASL-2 fresh `/home/dowling/r1_engineering/tasl_data_manifest_20261122/TASL-2/data/<node>/` | `24cb3448…` 951 B, mtime `2026-11-22 02:40:28.094 -0800` | `54d3a74d…` 959 B, mtime `2026-11-22 02:40:48.901 -0800` |
| TASL-7 fresh `…/TASL-7/data/<node>/` | `24cb3448…` 951 B, mtime `2026-11-22 02:40:29.268 -0800` | `54d3a74d…` 959 B, mtime `2026-11-22 02:41:02.848 -0800` |

- TASL-2 fresh vs TASL-7 fresh, per node: `cmp` over SSH → **identical** for both nodes.
- TASL-2 fresh vs TASL-2 staged fmnist: `cmp` → **identical**; TASL-7 fresh vs TASL-7 staged cifar10: `cmp` →
  **identical**.
- Independent Ada-vs-TASL-2-fresh diff over SSH, both nodes: exactly one changed line, line 24,
  `"datasets": "5.0.1"` → `"datasets": "3.6.0"`; nothing else (`diff rc=1`, one hunk). This reproduces the
  record's `_captures/manifests/census_vs_corrected.diff` without trusting it.
- Local recomputation of the eight fetched manifest copies: fmnist `24cb3448…`/951 B (both fresh hosts, TASL-2
  staged), cifar10 `54d3a74d…`/959 B (both fresh hosts, TASL-7 staged), census `8d28287b…`/951 B and
  `c0ef1168…`/959 B — all as recorded in the record and in `_captures/manifests/manifest_bytes.txt`.

### 1.2 Arrays

`sha256sum`/`stat` on the four `.npy` files at every present location reproduce the record's tables exactly:

- `mlgym_fmnist`: `train_x` `fa55843a…` 47,040,128; `train_y` `eb6efccc…` 480,128; `test_x` `fa687ea6…`
  7,840,128; `test_y` `33e7c41e…` 80,128 — identical at Ada census, TASL-2 staged, TASL-2 fresh and
  TASL-7 fresh.
- `mlgym_cifar10`: `train_x` `9a8bd809…` 153,600,128; `train_y` `9e2ee926…` 400,128; `test_x` `b57763d0…`
  30,720,128; `test_y` `fc48d9ec…` 80,128 — identical at Ada census, TASL-7 staged, TASL-2 fresh and
  TASL-7 fresh.
- Both manifests' own `files` blocks match the arrays in their directories, so each manifest is internally
  consistent and describes the census data.
- **Staged T1 data untouched**: TASL-2 fmnist files keep mtimes `2026-11-21 14:42:49 -0800`; TASL-7 cifar10
  files keep `2026-11-21 16:26:53–54 -0800`; no file under either staged data root is newer than
  2026-11-22T02:39:00 -0800 (checked with `find -newermt`); the staged manifests of the other nodes are
  census-identical (`mlab_imdb a87254e1…`, `mlab_ogbn_arxiv 91312162…`, `mlgym_houseprice 73ee5597…` on
  TASL-2; `mlab_cifar10 43fdf860…` on TASL-7 — each equal to the Ada census value). T1 HF cache
  `/home/dowling/r1_tracks/t1_tasl/hf` has no file newer than the window (mtime `2026-11-21 14:42:07`).

### 1.3 Setup environment, harness and scratch

- **Frozen `torch312`**: live `uv pip freeze --python …/envs/torch312/bin/python3 | sha256sum` =
  `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` on **all three** hosts (Ada, TASL-2,
  TASL-7), byte-identical to committed `sweep2/g1b/env/torch312.freeze.txt` (77 lines, `git show` hash equal).
  Imported versions verified live on all three hosts: Python 3.12.16, torch 2.6.0+cu124, numpy 2.5.4,
  datasets 3.6.0, huggingface_hub 0.36.2, torchvision 0.21.0+cu124, transformers 4.49.0, ogb 1.3.6.
- **Harness pin**: both hosts `git rev-parse HEAD` = `c025f89aeafc2199bf3487b4bcaa16678273c702`; detached
  (`## HEAD (no branch)` on TASL-7; Chinese-locale equivalent `## HEAD（非分支）` on TASL-2); `git diff --stat`
  empty; `git status --porcelain` exactly the four untracked `data` links on TASL-2 and the two on TASL-7 that
  the record lists, unchanged before/after. `git -C … archive c025f89a | sha256sum` =
  `98723a283be7494817558f021cb81a876371f035a43f09a4f596d7be06c3f872` on **both** hosts.
- **Node specs/node files**: `mlgym_fmnist.yaml` `a9844f01…`, `mlgym_cifar10.yaml` `a03585ff…` on both hosts;
  the committed `setup_command` lines (yaml line 33) match the record's §2.1; the scratch copy's
  `prepare_data.py`/`ar_data.py` are `cmp`-identical to the live harness files on both hosts (fmnnist
  `prepare_data.py` `e5005358…`; cifar10 `prepare_data.py` `6ff99228…`; `ar_data.py` `85cec63f…` —
  see finding F1 about the record citing only the fmnist `prepare_data.py` hash).
- **Scratch roots** `…/tasl_data_manifest_20261122/{TASL-2,TASL-7}/` are new (created 2026-11-22T10:40Z) and
  contain `data/`, `harness_c025f89a/`, `hf/`. `du -sb` = `604684817` (TASL-2) and `604687260` (TASL-7), as
  recorded; `hf/` holds the fresh HF hub + datasets caches for both revisions; no `__pycache__` in the scratch
  harness copy; setup logs show `python3 used: …/envs/torch312/bin/python3`, `rc=0` and the recorded
  start/end times for all four runs.
- Disk before→after in the setup logs reproduces the record's §2.4 numbers exactly (TASL-2 used
  1,533,198,630,912 → 1,533,805,236,224 B; TASL-7 1,385,614,561,280 → 1,386,221,129,728 B).
- **No GPU/lease by this record**: TASL-7 `r1_locks/gpu0.lock` unchanged (mtime `2026-11-21 02:07:04`);
  TASL-2 `gpu0.lock` mtime=ctime `2026-11-22 02:42:04.636746050 -0800` (= 10:42:04.636Z) — the externally
  written file the record discloses (§2.5); `r1_locks/` otherwise unchanged; no T1/Track-P/`prepare_data`
  runner process, no compute process visible. **No T1 job started/stopped**: TASL-2
  `logs/g1b_tasl2.status` still ends `DONE_AFTER_FMNIST 2026-11-22T04:03:59Z` with mtime `2026-11-21
  20:03:59 -0800`, `runs/` unchanged (last entry `2026-11-21 19:25`), TASL-7 `xc_tasl7.log/status` unchanged
  (`2026-11-21 16:26:54 -0800`).

### 1.4 Origin of the 5.0.1 census manifest on Ada — determinable

The record's §3 is independently reproduced:

1. **Only one environment on Ada can emit a `datasets`-based manifest.** `envs/torch312` is the only
   interpreter with `datasets`; `envs/jax312` and the only other venv (`/home/dowling/agent-checkpoint-intervention/.venv`,
   Python 3.13.4) report `datasets ABSENT`, as do `/usr/bin/python3` (3.10.12), the `/data1/dowling/toolchain/python`
   3.13 base, user site (`~/.local/lib/python3.10`) and system dist-packages; a max-depth-9 `pyvenv.cfg` scan
   finds exactly those three venvs, and the only `datasets-*.dist-info` under `/home/dowling` are the torch312
   one and the UV cache entries.
2. **The venv contained 5.0.1 at census-write time.** The committed pre-pin freeze
   `runs/u2_autoresearch_fixedtokens_20261117T094847Z/env_freeze.txt` (sha256 `dea8a9df3a92f233…`, 77 lines,
   contains `datasets==5.0.1`; the same file is in commit `a411d21e`, verified `git show a411d21e:…` hash
   `dea8a9df…`) and commit `61c8f719`'s proposal both record 5.0.1. The UV cache has exactly three `datasets`
   archives: 5.0.1 (mtime `2026-11-17 01:01:19.911 -0800`), 4.0.0 (`15:43:32.573`) and 3.6.0 (`15:44:40.021`).
   No other `datasets` install exists in the cache between 01:01 and 15:43, so the venv was still on 5.0.1 at
   the manifest writes.
3. **Re-pin happened after the manifests.** Census manifest mtimes `15:36:57.889` (cifar10) and `15:37:08.589`
   (fmnist) −0800 = `23:36:57.89Z`/`23:37:08.59Z`; `site-packages/datasets-3.6.0.dist-info` and the venv `bin/`
   have mtime `15:44:40.053 -0800` (= `23:44:40.053Z`), i.e. **7 min 31 s / 7 min 42 s after** the two manifest
   writes — matching the record's "7½ minutes". `dill`/`fsspec`/`multiprocess` dist-info are `15:43:32.6`.
4. **Timeline corroboration.** `harness_mlgym` `data` symlink dirs are stamped `15:36:58.009` (cifar10) and
   `15:37:08.629` (fmnist) −0800, i.e. 0.12 s / 0.04 s after the respective manifest writes; the next census
   manifest, `mlab_imdb`, is `15:45:26.705 -0800` and records `datasets 3.6.0` (46.7 s after the 3.6.0
   install). `prepare_data.py` line 65 writes `"datasets": datasets.__version__`, so a 5.0.1 manifest can only
   have come from a 5.0.1 environment.

Conclusion: the origin **is determinable** and is the Ada `envs/torch312` venv in its pre-re-pin state; the
census value is stale metadata, not different data (arrays identical, §1.2). No residual alternative
environment exists on the host.

### 1.5 Other census nodes — one-sentence check

**No other census manifest records a library version that differs from the frozen `torch312` environment:
the matching nodes are `mlab_cifar10` (`torchvision 0.21.0+cu124`), `mlab_imdb` (`datasets 3.6.0`,
`transformers 4.49.0`) and `mlab_ogbn_arxiv` (`ogb 1.3.6`), while `autoresearch_fixedtokens` and
`mlgym_houseprice` record no library version and `mlgym_breakout_minatar` has no data manifest — so the
5.0.1/3.6.0 mismatch is confined to the two MLGym nodes of this erratum.** (Verified by reading all seven
live Ada census `data_manifest.json` `source` blocks and the frozen-env values live, not from the capture.)

## 2. Why the two corrected values are trustworthy

The corrected manifests are not merely "whatever ran on two hosts": (i) their `files` hashes equal the actual
array bytes at every location; (ii) the same bytes hash the same at Ada census, staged T1 and both fresh runs,
so the manifests describe census data; (iii) the corrected manifest is what the frozen environment
(`d2e70fe4…`) produces from the hub at the pinned revisions (`531be5e2…`, `0b271498…`) with a fresh HF cache;
(iv) the only difference from the census file is five characters in one line; (v) the T1 jobs had already
used that same manifest (staged files `cmp`-identical). Option A's "manifest the frozen environment produces"
is therefore exactly what is recorded.

## 3. Findings (all non-blocking; none changes a value or conclusion)

- **F1 — minor precision (record §2.1/§6).** The record cites one `prepare_data.py` hash
  (`e50053587218…`) as "the node files" hash. That is the `mlgym_fmnist` node's file; the
  `mlgym_cifar10` node's `prepare_data.py` is `6ff992287…` (`6ff99228d753e0fd…`). The setup log's `cmp`
  covers both nodes and shows both identical to the live harness, so the claim is true but the quoted hash is
  node-specific. `ar_data.py` (`85cec63f…`) is identical for both nodes and is quoted correctly.
- **F2 — minor evidence gap (record §2.1, §2.2, §6).** The captured `set -x` setup logs begin inside the
  script (`+ date -u`) and show the inner `python3 prepare_data.py` run and its effects; they do **not**
  contain the outer invocation, so `taskset -c 16-31` (TASL-2) / `taskset -c 16-23` (TASL-7), `HF_HOME=…` and
  `PYTHONDONTWRITEBYTECODE=1` are not in any capture. `HF_HOME` is corroborated by the fresh scratch `hf/`
  cache and `PYTHONDONTWRITEBYTECODE` by the absence of `__pycache__`, but the CPU-pinning claim is not
  independently reproducible from the captures; §6's "every claim above is reproducible from those captures"
  is therefore an overstatement for that sentence. This has no bearing on the manifest/array conclusions and
  the setup remains consistent with the recorded environment and with "no GPU/lease, no T1 job".
- **F3 — minor wording (record §1.1 last paragraph).** "TASL-2: the G.1b fmnist job; TASL-7: the
  cross-check cifar10 job" reads as if those were the only staged nodes. TASL-2's staged root also carries
  `mlab_imdb`, `mlab_ogbn_arxiv` and `mlgym_houseprice` (all census-identical, verified), and TASL-7 carries
  `mlab_cifar10`. The erratum-relevant fact (fmnist staged / cifar10 absent on TASL-2, converse on TASL-7) is
  correct; the sentence is imprecise.
- **F4 — note on the disclosed external activity (record §2.5).** The lease file's mtime=ctime
  (`10:42:04.636746050Z`), `harness_ar` HEAD `2d09f9a9…` and its `.git/index` mtime (`10:42:04.548746045Z`)
  are all reproduced live; the record's disclosure is appropriate and correctly left as "not this record's
  commands". Attribution to "another process" is, however, an inference that no capture can prove (there is
  no audit trail of the writer), and external activity continued after the capture (`harness_ar/.git` dir
  mtime has since advanced to `2026-11-22 02:46:38 -0800`). Neither touches the paths this erratum read or
  produced, and the record flags it for the lead — no effect on the evidence.
- **F5 — cosmetic (record §2.1).** On TASL-2 the `git status -sb` detached-HEAD line renders in the host's
  Chinese locale (`## HEAD（非分支）`), not the English `## HEAD (no branch)` quoted; TASL-7 renders the
  English form. No content difference.

## 4. Conditions / recommendations

None of C1–C3 requires re-running anything; the corrected values stand as reviewed.

- **C1 (from F1/F3).** If the record is published as the reviewed artifact, correct the node-file hash
  attribution (fmnist `e5005358…`, cifar10 `6ff99228…`, both `cmp`-verified) and, in §1.1, say "of the two
  erratum nodes" (or list the other staged nodes).
- **C2 (from F2).** Replace §6's "every claim above is reproducible from those captures" with the accurate
  scope (hashes, byte comparisons, manifest diffs, setup outputs/times are in the captures; the operator's
  outer invocation — CPU pinning/HF_HOME — is stated but not captured), or add the invocation receipt if one
  exists. Do not let the record rest on the uncaptured `taskset` claim for any conclusion; it does not.
- **C3 (from F4).** Keep the external-activity paragraph as a disclosure, not an attribution; if the lead
  cross-checks the other concurrent workstream, record that outcome outside this erratum.

## 5. Limitations of this review

- I did not re-run the setup (read-only mandate), so "what the frozen environment produces" is established
  from the two hosts' live fresh outputs, the setup logs, the live env freeze and the manifests' internal
  consistency — not from a third production run.
- I did not verify historical process/lease attribution (F4); no audit trail exists for who wrote
  `gpu0.lock` in that second.
- Hash reads used host `sha256sum`/`stat`, not numpy re-derivation of arrays; the manifests themselves record
  the same hashes and the byte sizes match.
- The record is uncommitted at review time; this review fixes the reviewed sha
  `9b40944b…`/capture sha `8bc79087…` only.

**Conclusion.** The erratum's two values are correct and independently reproduced on the required hosts, the
array data is unchanged, the origin of the 5.0.1 metadata is determined, and no other census node is affected.
**ACCEPTED** with the documentation-precision conditions above.
