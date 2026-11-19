# Track G G.0 U2 isolated-node results — accepted MINOR record-text corrections (19 November 2026)

**Status: record/capture corrections APPLIED to the five reviewed U2 node results; no GPU/U2 run, no unit/code
change, no deletion, no commit/push.** Correction window: **2026-11-19T04:23–04:31Z** (record notes stamped
`2026-11-19T04:30Z`). This note is the campaign-level correction record and change list for the five result
directories under `docs/r1/reports/trackg_g0_20261117/`; each corrected result carries its own short correction note
with the same date/UTC and the new shas are listed below.

**Authority / inputs.**
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` sha256
**`965dc993b0dc4ea35d327869b7445218d1898ecdfb0b2768838de877b55245e1`** (all five nodes ACCEPTED, MINOR-only
conditions: C1–C5, I1–I2, O1–O2, M1–M2, F1–F2 and shared S1–S10). Executed unit revisions accepted by
`TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` sha256
`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`; accepted kit report
`TRACKG_ISO_KIT_UPDATE_20261119.md` sha256 `fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`
with review `TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`. Worktree `ops-tasl-20261116` at HEAD
`1cc54d81`; `origin/main` `de3de54f`; no commit/push was made. Read-only SSH to Ada (`experiment_zhixu`, host
`ucrtasl`) was used to refresh the one divergent capture and to cross-check all five captures against live evidence.

**Scope rule applied.** Only record-text/citation corrections (and the one capture-fidelity refresh) were made. No
measured number was changed except where the record had cited the wrong source file (C1 disk `df` values) or a
pre-run size instead of the post-run footprint (I2/O1/M1/F1); in those cases the value now comes from the actual
`disk_before/after.txt` / `runs_du.txt` captures. No unit, no code, no runner, no pin, no isolation record, no
data manifest and no smoke-log content was modified. No retry/second smoke was run.

## 1. Per-node record/SHA256SUMS shas (old → new) and changed files

| node | result md (old → new sha256) | `SHA256SUMS` (old → new sha256) | changed files besides the result md |
|---|---|---|---|
| `mlab_cifar10` | `c8e0ab2e…` → **`72f122d4292ff697e31ec64f651f500bae0c1e5cfa037bd06e6fad2a5a8a8cbf`** | `cbf6fe82…` → **`03698f00c9aafa9b9a7f5dac5032cdbf79aeaa6b081032009ae50e4464124391`** | `unit/U2_ISO_MLAB_CIFAR10_UNIT_20261119.md` added (preserved executed-unit bytes); `SHA256SUMS` regenerated (428 entries) |
| `mlab_imdb` | `77154ec2…` → **`85ec0506b21465bb7b91950c8a2b7fcced0ca6b94852be185b714ed8ee320ee1`** | `f3ce6738…` → **`c07efc45599808bf2ceda639a673157a0df2e90b4380c7bd7e87312029baf6bd`** | `RESULT_STATUS.txt` **refreshed from live Ada** (new sha256 `1752f80ca232129d88940a4060f17bb6e541e036c27d35ec9c528b979d25e8fe`; was `7bd2f2ff…`); superseded local copy preserved as `RESULT_STATUS.local_v1.txt` (`7bd2f2ff…`); `unit/U2_ISO_MLAB_IMDB_UNIT_20261119.md` added; `SHA256SUMS` regenerated (427 entries) |
| `mlab_ogbn_arxiv` | `93947556…` → **`57d040ce5d07085cc436542a466f406abc3af9f38249f76f832a637d6d8d7ae5`** | `2f773102…` → **`bbfd8bbb924d5f5325f6d47add69796d23960519dd9402fc0ca7e0e1b1bd17ab`** | `unit/U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` added; `SHA256SUMS` regenerated (426 entries) |
| `mlgym_cifar10` | `ba68f5e2…` → **`4d009c011ffb3cad4b844512a91809ebf4c755fec38cc1d2727dd0b5893fc6ea`** | `7699dc03…` → **`1d79f745f1bdb2048c7cb324ae9fb417ca2d71b94f1dd4e3ca76781d5d7be457`** | `unit/U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` added; `SHA256SUMS` regenerated (426 entries) |
| `mlgym_fmnist` | `e8ef1fca…` → **`315c8411830e25c5eae7518315f654d54378c1d93278b85591cb12c90f1b4ea5`** | `6aac3e22…` → **`63712a4f4b0b9be1dcec0f1b11c1bc47a4419036f33a442fb63ab1a8cf5eed4d`** | `unit/U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` added; `SHA256SUMS` regenerated (426 entries); wrong-timestamp dir moved out of the reports tree (§5) |

The old values in the table's `…` positions are the full shas recorded in the accepted review §table; the new values
are the actual post-correction hashes (all 64-hex in full above). Every result's own post-correction sha256 is the
corresponding result-md entry inside its `SHA256SUMS`, so the record identity is machine-checkable.

## 2. Node-specific corrections

- **`mlab_cifar10` (C1–C5).** C1: disk numbers now from `disk_before.txt`/`disk_after.txt`
  (**74,632,835,072 B / 74,630,283,264 B**, both 69.5 GiB free, > the 50 GiB STOP floor) instead of
  `RESULT_STATUS.txt`'s second `df` sample; the unused source is named in the record. C2: gate time now the gate
  JSON's own `utc` **`2026-11-19T03:37:51Z`** (and `gate_check.txt` `03:37:51Z`), with the filename/evidence-dir
  timestamp `03:37:47Z` explained as the runner start (`launch_mlab_cifar10.log`). C3: setup-log sha
  **`6747f821af7e6b89db3667a2fbd9115b3031b9a6f5446c4d072806fa01c1eb95`** added (verified live). C4: licence/
  provenance line added (CIFAR-10 generic citation/disclosure, `R1-TRACKG-LICENCES`; same line the other four carry).
  C5: the `RESULT_STATUS` original `STOP` → `status_corrected=PASS` is disclosed (the STOP is the v1 verifier
  false-negative preserved as history; corrected verifier rc 0 on the same records, no smoke re-run).
- **`mlab_imdb` (I1–I2).** I1: the local `RESULT_STATUS.txt` differed from live Ada in wording only (local
  `7bd2f2ff…`, live `1752f80c…`); it was **refreshed from live Ada** (now byte-identical, sha256 `1752f80c…`),
  `SHA256SUMS` regenerated, and the superseded local copy preserved as `RESULT_STATUS.local_v1.txt` (`7bd2f2ff…`),
  still hash-listed. I2: footprint corrected to the post-run `runs_du.txt` **3.8 M** / `disk_after.txt` evidence
  **4.5 M** (not the pre-run `evidence 60K, runs 4.0K`), and "run root 4.0K" corrected to 3.8 M.
- **`mlab_ogbn_arxiv` (O1–O2).** O1: footprint corrected to post-run `runs_du.txt` **3.8 M** / `disk_after.txt`
  evidence **4.0 M**; "run root 4.0K" corrected. O2: explicitly disclosed that representative edit **E4** measured
  **`elapsed_seconds_info_only = 21.8 s` > derived node timeout 16.953 s** (= 3 × B1 5.651 s); the measuring smoke
  was governed by the **provisional 1800 s** (`limits.provisional_timeout_seconds: 1800.0`, `process.timed_out:
  false`), so this is not a smoke timeout, but under a future label run that edit would be a timeout/failed
  proposal — recorded for the census/funnel.
- **`mlgym_cifar10` (M1–M2).** M1: footprint corrected to post-run **3.9 M** runs / **4.3 M** evidence; "run root
  4.0K" corrected. M2: `outcome.value` is the **validation accuracy** (`metric_name: val_accuracy`,
  `selection_split: validation`, `AR_METRIC val_accuracy=…` = 0.491 baseline), **not** "test accuracy"; the sealed
  test metric is `AR_TEST test_accuracy=…` → `sealed.test_accuracy` (0.4926). All "test accuracy" wording for
  `outcome.value` removed; the census row must name **`val_accuracy`** for `outcome.value` and keep
  `test_accuracy` separate.
- **`mlgym_fmnist` (F1–F2, S2).** F1: footprint corrected to post-run **3.9 M** runs / **4.4 M** evidence; "run
  root 4.0K" corrected. F2: same metric-label fix (`val_accuracy` 0.861667 for `outcome.value`; sealed
  `test_accuracy` 0.8515). S2: the wrong-timestamp directory was moved out of the reports tree (§5).

**Census-directed metric labels.** All five node specs use `metric_name: val_accuracy` (selection split
validation); only the two `mlgym` records had mislabelled it. Census-directed values are therefore:
`mlab_cifar10` val_accuracy 0.5152 / sealed test 0.5015; `mlab_imdb` 0.9048 / 0.89924; `mlab_ogbn_arxiv` 0.275982 /
0.238442; `mlgym_cifar10` 0.491 / 0.4926; `mlgym_fmnist` 0.861667 / 0.8515. No U2 census row exists in this
worktree to edit (the only census report present, `TRACKG_CENSUS_20261117.md`, predates the port kits and lists the
U2 rows as pending); the corrected records now unambiguously supply `val_accuracy` as the `outcome.value` name for
the future U4 row.

## 3. Shared corrections (S1–S10)

- **S1 — Ada launcher dry-runs disclosed (all five records).** Two dry-runs for `mlab_cifar10` exist in the
  campaign evidence root: `dryrun_u2_iso_mlab_cifar10_20261119T033214Z` (inner command
  `taskset -c 0-7 /usr/bin/time -v -o … true -m tests.trackg.port_smoke_gpu …` — `true` swallows the smoke args) and
  `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z` (inner command `/usr/bin/env python -c "import sys, torch; …"` — a
  Python/torch-only dry check, with the same trailing smoke args; accurate live record — only dry-run 1 used
  `true -m`). Both executed **no U2 run and no GPU work**, both correctly went `STOP` on missing
  `CHECKLIST_E_PASSED` (`status=STOP`; `DONE_STOP`), and they are **not smokes and not retries**; they are not
  counted in the one-smoke claim. Launcher logs: `dryrun_launcher.log` sha256 `24ebcd6fbde344fc7d275150915730041c34c3ebadf82e993d779b62c1273202`,
  `dryrun2_launcher.log` sha256 `9e4abc5e93c43855825758c9894f8605013974ad114863556a9511681792ada0` (live).
- **S2 — wrong-timestamp directory moved aside (documented in `mlgym_fmnist` + here).**
  `docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS_MOVED_ASIDE/` was a
  wrong-timestamp staging copy containing only eight files, all byte-identical (sha256) to the fmnist result
  directory's `static/`+`scripts/` copies, and no run evidence. It was **moved, not deleted**, out of the reports
  tree to
  `docs/r1/reports_moved_aside/u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS/`, with a
  `README_MOVED_ASIDE.txt` recording its origin, the duplicate hashes and the reason. The reports tree now contains
  exactly the five reviewed node result directories.
- **S3 / mR6 — record identity fields added (all five).** Each result now records its own file path and (via
  `SHA256SUMS`) its sha256; the node-spec raw sha and **canonical `node_spec_sha256`** (recomputed with the kit's
  own loader: `sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False, default=str))`
  — all five match every run record: `90c8364f…`, `0123a8a7…`, `e952df6a…`, `f1360bcd…`, `65f229af…`); the
  representative-edit manifest sha and the E1–E4 diff shas (cited from `kit.txt`); `process.killed_with: null`,
  `returncode 0`, `timed_out false`, `leftover_processes_killed false` on every executed record; and the one-JSON-
  line-per-run smoke-log check.
- **S4 — full shas.** All result headers now cite the **full** kit-update report sha
  `fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`, the kit-update review sha
  `d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, and the R3 unit-review sha
  `99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7` (no `fe232e2b…` prefixes left).
- **S5 — 8 GiB floor basis and mid-run rule (all five).** Basis: accepted kit update §6 measured a **~2.85 GB
  (2,853 MiB)** per-run torch GPU peak under the 8 GiB cap, and the prior accepted run-1 floor was **24 GiB**
  (`TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md`); each node's chosen card had ≈ 48.4 GiB free. Rule recorded: a free-VRAM
  drop below baseline peak + 2 GiB or a new co-tenant on the used card is a STOP/recorded, and **no card switch from
  the launch card** occurred (the selected UUID is the only card in qualify/before/mid/after and every record).
- **S6 — no-resume line and filesystems (all five).** "No resume (R3 mR10): an interrupted unit re-runs wholly from
  a new `<runs-root>`; no resume occurred." Disk captures name the filesystem: `/dev/md0p3` mounted `/`
  (`df -B1 /`; cifar also records `/`, `/home`, `/tmp`, all the same filesystem).
- **S7 — data-root wording (all five).** "data root not writable / `data_root_writable=no (read-only)`" reworded to
  **node data dir not writable** (the capture tests `[ -w "$BASE/data/<node>" ]`; node data dir `dr-xr-xr-x`,
  ro-bound in the worker sandbox), while the **top-level `data/` root is operator-writable (`drwxrwxr-x`)** — the
  integrity claim that matters is the node data read-only/ro-bind, not the whole root.
- **S8 — "preserved read-only" wording (all five).** Replaced by **"preserved unaltered"** on Ada (live evidence dirs
  `drwxrwxr-x`, files `-rw-rw-r--`, hash-matching; not filesystem-read-only).
- **S9 — `data_link=` duplicate-target print (all five).** Each result now records the actual in-kit symlink path
  (`nodes/<node>/data` for the mlab kit, `third_party/mlgym/nodes/<node>/data` for the mlgym kit → absolute target),
  cites `kit.txt` `?? nodes/<node>/data` and the deployed pin's `data: link:` entry, and explains that the
  `data_manifest.txt` line prints `readlink -f` on both sides so the in-kit path is implicit (cosmetic only).
- **S10 — executed-unit bytes preserved; runner bytes recorded (all five).** The executed (amended revision-3) unit
  md is copied byte-identically into each result directory as `unit/U2_ISO_<NODE>_UNIT_20261119.md` (shas equal the
  recorded executed-unit shas: `7278932f…`, `bbc02cc5…`, `81a3a393…`, `82e90b7c…`, `0f124d10…`). Preserved runner/
  helper bytes in each `scripts/` and their shas: final `run_node.sh`
  `13a45d7baf7dacac6da2ef1455e86fc794c25fd90f5a835511b50aafccc99444` (byte-identical to the live campaign
  `scripts/run_node.sh`; for `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist` this is also the launch-time runner
  because patch 3 landed at 19:50Z before their 19:51/19:53/19:58Z launches), `_patch2_verifier_s002_fix.py`
  `681d9f8a…`, `_patch3_mid_watcher_fix.py` `ce2ff3b0…`, `compute_sampler_max.py` `7d9f472e…`,
  `verify_u2_records.py` `7f40ed17…`. For `mlab_cifar10`/`mlab_imdb` the **exact launch-time runner bytes are not
  preserved as a file** (the campaign preserved the final runner plus the exact patches and the 19:32Z/19:36Z dry
  runner snapshots `run_node_dry.sh` `c5d2c598…` / `run_node_dry2.sh` `ca891b34…`) — recorded as a residual (§8), not
  guessed.

## 4. Live-Ada cross-check of the corrected captures

Read-only on Ada (`ssh -o BatchMode=yes experiment_zhixu`, host `ucrtasl`, user `dowling`; no writes): for each of
the five live evidence dirs I hashed **every** file and compared it with the corrected local capture and its
regenerated `SHA256SUMS`:

| node | live files | local/live identical | differing | live-only |
|---|---|---|---|---|
| `mlab_cifar10` | 418 | **418** | 0 | 0 |
| `mlab_imdb` | 416 | **416** (incl. the refreshed `RESULT_STATUS.txt`) | 0 | 0 |
| `mlab_ogbn_arxiv` | 416 | **416** | 0 | 0 |
| `mlgym_cifar10` | 416 | **416** | 0 | 0 |
| `mlgym_fmnist` | 416 | **416** | 0 | 0 |

The only local-only files are the Mac-authored/copied record files: the result md, `SHA256SUMS`, the `unit/` copy,
`static/` copies of the live campaign static-test log + README, `scripts/` copies of the live campaign
runner/verifier/sampler-max sources (byte-identical to the live campaign `scripts/`), the two renamed patch copies
and a README, and (imdb only) `RESULT_STATUS.local_v1.txt`. No live file is un-captured. The previous sole
divergence (imdb `RESULT_STATUS.txt`) is fixed, so all five captures are now byte-faithful to live Ada.

Also verified live: the five in-kit data symlinks (`nodes/<node>/data` → `/home/dowling/r1_trackg_20261117/data/<node>`),
node data dirs `dr-xr-xr-x`, top-level data root `drwxrwxr-x`, evidence dirs `drwxrwxr-x`/files `-rw-rw-r--`, the two
dry-run dirs and their `STOP` statuses, the five setup-log shas, the node-spec canonical shas (recomputed with the
kit's own loader), and the campaign runner/patch shas.

## 5. Verification

- Each corrected `SHA256SUMS` was regenerated over all files in its directory except itself and verified with
  `shasum -a 256 -c SHA256SUMS`: **rc 0** on all five; entries **428 / 427 / 426 / 426 / 426** (all OK, none
  missing) — the per-node counts grow by the preserved `unit/` file and, for imdb, by `RESULT_STATUS.local_v1.txt`.
- `unit/` copies hash-equal the executed-unit shas already recorded in the results and the units in
  `docs/r1/proposals/u2_iso_20261119/`.
- The refreshed imdb `RESULT_STATUS.txt` sha256 `1752f80c…` equals the live Ada file exactly (re-hashed live after
  the copy).
- No measured value changed except C1 (disk source corrected), I2/O1/M1/F1 (post-run footprint instead of pre-run
  size) and the metric **labels** M2/F2 (numbers unchanged). No isolation record, gate JSON, run record, sampler CSV,
  verification JSON, unit, code, pin or manifest was modified.
- No GPU/U2 run and no retry was performed; no deletion (the wrong-timestamp dir was moved, and the superseded imdb
  status capture was preserved as `_v1`); no commit or push (`origin/main` still `de3de54f`, HEAD still
  `1cc54d81`); no TASL/HTCondor/deepthought action; no write on Ada.

## 6. Residuals (not verifiable without a rerun; recorded, not guessed)

1. **C5 machine status file.** The live `RESULT_STATUS.txt` still begins with the historical `STOP` line and appends
   `status_corrected=PASS`; it was **not rewritten** (that would break byte-fidelity to live Ada, and no Ada write was
   permitted). The record-level normalisation (`status_corrected=PASS`, STOP as history) plus the DONE
   `DONE_STOP → DONE_PASS_CORRECTED` sequence are disclosed in the cifar result; a census reader should use the
   record-level PASS.
2. **Launch-time runner bytes for `mlab_cifar10`/`mlab_imdb`.** The exact pre-patch runner files are not preserved;
   the final runner and the two exact, asserted string-replacement patches plus the 19:32Z/19:36Z dry-runner
   snapshots bracket them, so the derivation is reproducible but the launch-time byte identity cannot be re-proven
   without the original file (a rerun is not authorised).
3. **R3-reviewed (pre-amendment) unit bytes.** Only the executed amended revision-3 bytes were preserved (current
   unit files); the R3-reviewed pre-amendment bytes were never committed (shared finding S10 in the review), so no
   byte diff against the R3 text is possible — the amendment scope remains verified by content, as the review states.
4. **Mid-run utilisation for `mlab_cifar10`/`mlab_imdb`** remains `NOT_CAPTURED_MID_RUN` (the launcher watcher
   defect); the sampler-derived mid census and the whole-run 1 s sampler are unchanged and still labelled — no rerun,
   so this cannot be recovered.
5. **Census row.** No U2 census row exists yet in this worktree; the corrected records supply the census-directed
   values (committed pin, `val_accuracy` label/value, sealed `test_accuracy`, B1/B2, derived timeout, sampler bound,
   disk before/after). Writing/committing the row is outside this corrections pass.
6. **Review wording on dry-runs.** The accepted review describes both dry-runs as `true -m`; the live dry-run 2
   record actually shows a Python/torch-only dry command (same trailing smoke args, no U2/GPU run, STOP). The
   accurate per-run commands are recorded in the results and here; this is a wording refinement, not a result change.

## 7. Command / attestation record

All work was local to
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116` plus read-only SSH to Ada. Commands:
reads of the review, the five result mds and their captures; `shasum -a 256`/`shasum -a 256 -c`; `python3` reads of
the 45 run records/verifiers/samplers; `cp -p` of the five unit mds into `unit/`; one `cp -p` preserving the imdb
`RESULT_STATUS.local_v1.txt` and one live `cat` to refresh `RESULT_STATUS.txt`; `mkdir`/`mv` of the wrong-timestamp
dir (with a README written); regeneration of the five `SHA256SUMS`; live `sha256sum`, `stat`, `ls -l`, `readlink`,
`git status`, setup-log hashes and a read-only Python canonical-node-spec recomputation. Nothing else was written;
no file deleted; no commit, push, GPU job, HTCondor/deepthought action, or Ada write.
