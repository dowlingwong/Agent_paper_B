# Independent review of the `gc7rc_forestcover` G.5 isolation host check (28 November 2026)

**Verdict: ACCEPTED WITH MINORS.** At the originally reviewed tip `5fc98d52` the capture set was two files short
and did not verify; commit `3a334d52` force-adds exactly those two files, and on the new tip the set is 36 files
with `shasum -a 256 -c SHA256SUMS` returning 35 OK and rc 0. The fix is mechanical: no host check or job was
rerun, and the record and every previously published payload are byte-identical. Five minor
documentation/evidence-coverage issues remain, listed below.

I did not write this record or its captures. I reviewed the exact branch tips below in this worktree. The only
host access was read-only (`ssh tasl2`); I ran no G.5/G.1b job, read no labels, and modified nothing on TASL-2.

## Tips and artifacts reviewed

| Item | Value |
|---|---|
| Branch | `compute-g5-expansion-isolation-forestcover-20261128-review` |
| Final deliverable tip (re-reviewed) | `3a334d528d4be799c049d3748b8fec4c8c01f58b` |
| Previous tip (first review) | `5fc98d52d967ae199149d238429a8d4030294a6c` |
| Round base (parent of first tip) | `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce` |
| Record | `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261128.md` |
| Record sha256 | `00b84d688d1b167bab1817709919fa7b8c8237ccaff3d60a1245e10a5c27eb12` (unchanged) |
| Captures | `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261128_captures/` |
| `SHA256SUMS` sha256 | `95fb1af5f2d0aef4633a872cffde35dd9a5bea14796e930dadfe71096285e736` (unchanged) |
| Harness pin under test | `3f7b09febf401a83f3aa881f00eecdd032024416` |
| Harness review compared | `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md`, sha256 `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3` (matches) |
| Paper test base | `57e6d1ed5945ab48684e24e145b69d333b4f77d4` (present) |

## Checks run and results

### 1. Record hash — PASS

`shasum -a 256` of the record equals `00b84d688d1b167bab1817709919fa7b8c8237ccaff3d60a1245e10a5c27eb12`, the
same value as at the first review. The fix commit did not touch it.

### 2. Capture-set integrity — PASS after the fix

On the new tip:

- The capture directory contains **36 files: 35 payload files + `SHA256SUMS`**.
- `SHA256SUMS` still hashes to `95fb1af5f2d0aef4633a872cffde35dd9a5bea14796e930dadfe71096285e736`.
- From inside the capture directory, `shasum -a 256 -c SHA256SUMS` reports **35 OK and exits rc 0**.
- The two added logs match their listed entries:
  - `records/forestcover_smoke/run.log` → `9b7c8df0e97caccea061255b3d350cab087c50bca989c030df4b9194a62ff7d1`
  - `records/forestcover_gpu_smoke/run.log` → `c4111f9b3c897d97102532c8ef459014d3a517b6af154068ee4eb9463f9f5440`
- No AppleDouble `._*` files exist (0).
- No file listed in `SHA256SUMS` is missing and there is no unlisted payload file.

At the first-reviewed tip `5fc98d52` this check failed: the branch carried 33 payloads, the two `run.log` files
were absent because `.gitignore` line 3 is `*.log`, and `shasum -c` exited 1 with two `FAILED open or read`.
Commit `3a334d52` force-adds exactly those two files; the host copy and hashes were already correct, so this was
a publication fix only.

### 3. Diff between the two tips — PASS

`git diff --name-status 5fc98d52d967ae199149d238429a8d4030294a6c 3a334d528d4be799c049d3748b8fec4c8c01f58b`
lists only:

```
A .../records/forestcover_gpu_smoke/run.log
A .../records/forestcover_smoke/run.log
```

`git diff --stat` is 19 insertions in those two files. The record and all previously verified payloads are
byte-identical; no other capture changed and none was removed.

### 4. `c*.json` condition flags, stop items, pytest, C6 and C7 — PASS

- `c1_userns_env.json`, `c1_userns_syspy.json`, `c2_ptrace.json`, `c3_cgroup.json`, `c4_interp.json`,
  `c5_smoke.json`, `c6_gpu_smoke.json`, `c7_final.json`: `condition_1_pass` … `condition_7_pass` are all
  `true`.
- `stop_items.txt` is 0 bytes.
- `pytest_isolation.json`: `rc: 0`, `passed: 27`, `skipped: 1`; the tail shows `27 passed, 1 skipped in 14.11s`
  and a `taskset -c 4-7 timeout 900 … pytest tests/trackg/test_trackg_isolation.py` command.
- `c5_smoke.json`: `outcome.kind: ok`, `effective: true`, `waivers: {}`, `exceptions: []`,
  `frozen_files_changed: []`, cgroup removed, `log_intact: true`.
- `c6_gpu_smoke.json`: all 15 `checks` true; `effective: true`, `waivers: {}`, `exceptions: []`; full UUID
  `GPU-4d623e76-7587-ee15-a633-46f60d220d94`; `gpu_report.tensor_sum: 4096.0`, `expected_sum: 4096.0`,
  `matmul_value: 16.0`, `cuda_available: true`, `device_count: 1`, worker `pid: 1`/`ppid: 0`, torch
  `2.6.0+cu124`, CUDA `12.4`; lease acquired `2026-11-28T17:37:33Z`, released `17:37:35Z`; compute-apps query
  empty before and after.
- `c7_final.json`: `condition_7_pass: true`, lease `lease_free`, compute apps empty, all six leftover buckets
  empty, `free_gib: 333.8` (358456438784 bytes) on both paths, harness head `3f7b09fe…`, seven-node head
  `c025f89a…`, Track P `897d83c8…` tracked-clean.

### 5. Factual numbers and hashes in the record — PASS

| Record claim | Capture evidence | Result |
|---|---|---|
| node spec `ff2a585b…` | `pins_*.json` got/expected `ff2a585b69b5…` | match |
| committed pin `78b48db9…` | got/expected `78b48db9d36c…` | match |
| edits manifest `0219deb8…` | got/expected `0219deb80aab…` | match |
| spec file `edd1a076…` | `got.spec_file_sha256` `edd1a076aab8…` | match |
| node/master `ar_isolated.py` `37d99ab0…` | both `37d99ab0…` | match |
| 16 frozen entries | `frozen_entries: 16` | match |
| data manifest `2b5cfb15…` | `datapins`/`c7` `2b5cfb15f3c9…`; `X.npy` and `y.npy` both `match: true` | match |
| torch312 freeze `d2e70fe4…`, 77 lines, Python 3.12.16 | `env_torch312.json`/`.txt`; freeze file hashes to `d2e70fe4…` | match |
| lease window 17:37:33-17:37:35Z | `c6_gpu_lease_status.txt` | match |
| 333.8 GiB free | `c7_final.json` | match |
| seven-node pin `c025f89a` | `c7_final.json` seven-node head | match |
| Track P `897d83c8` | `c7_final.json` Track P head | match |

Host facts also match: TASL-2, Ubuntu 22.04.5 LTS, kernel `6.8.0-149-generic`, 32 logical CPUs, microcode
`0x133`, uid 1008, RTX 4090, driver 535.309.01. The CPU model `i9-14900KF` is not in the captures; a read-only
host check confirms it, so the statement is true but not carried by the deliverable.

### 6. Candidate diff claim — PASS

Read-only on TASL-2 at the harness clone: `git diff --stat 85851664 3f7b09fe` shows only
`src/autoresearch/trackg/audit_g5.py` (added) and `src/autoresearch/trackg/campaign_v2_diff.py` (modified);
`rev-list --count` is 1. The two blobs hash to `5f384204c34e297191281bb3981db57607d58333222adab6def97e8d099e2690`
and `9d4f8e6838c31ebec835fd13434532b8afb8539e3cdd913188e52300d0c0a708`, exactly the reviewed pair. This
matches the record and `G5_EXPANSION_HARNESS_REVIEW_20261128.md`.

### 7. Step 1 checkout — PASS

`step1_checkout.txt` shows `head=3f7b09febf401a83f3aa881f00eecdd032024416`, `symbolic_ref_rc=1` (detached),
`status_start`/`status_end` containing only `?? nodes/gc7rc_forestcover/data`, and `ancestor_rc=0` for
`git merge-base --is-ancestor c025f89aeafc2199bf3487b4bcaa16678273c702 HEAD`. The data entry is a symlink to
`/home/dowling/r1_tracks/t1_tasl_x/data/gc7rc_forestcover` (read-only host check). `checkout_end.txt` agrees:
same head, detached, only the data link untracked, empty stash. Read-only host checks confirm that
`c025f89a` is an ancestor of `3f7b09fe` (rc 0) and that the reverse is not true (rc 1); this is the direction
the recorded command tests.

### 8. CPU pinning and the discarded first attempt — PASS with a documentation minor

The disclosure is consistent with an engineering rerun, not an outcome change:

- Attempt 1 (`captures_attempt1_20261128T173529Z/`) has all seven conditions true, an empty `stop_items.txt`,
  the same `torch312.freeze.txt` sha256 `d2e70fe4…`, and 27 passed / 1 skipped at rc 0. Its pytest command has
  no `taskset`, matching the record's account; its C6 smoke is stamped `17:35:47Z`.
- Attempt 2 is the source of every published capture: `c1`-`c4` are stamped `17:37:16/17Z`, the CPU smoke is
  `forestcover_smoke_20261128T173717Z`, the GPU smoke is `forestcover_gpu_smoke_20261128T173733Z`, the lease is
  `17:37:33-17:37:35Z`, and `step1_checkout.txt` is `17:37:42Z`. The published JSONs therefore belong to
  attempt 2, not attempt 1.
- No signed value, spec, note or code changed between the attempts; the pins, spec hashes, frozen entries,
  data manifest and freeze file are identical in substance.

However, the record's sentence "In attempt 2 every C1-C6 step and every step-1-4 capture is `taskset -c 4-7`"
is broader than the captured evidence. `commands.txt` shows `bash scripts/phase3_checks.sh` with no `taskset`
and shows explicit `taskset -c 4-7` only for the step 2-4 reports. The `c1`-`c4` JSONs expose no affinity
field; `c5`/`c6` record a bare `python -s parent.py 5` argv and `limits.cpu_list: null`. Only the pytest tail
shows an inner `taskset -c 4-7`. Step 1 is a git-only block, not a `taskset` command. The claim may well be
true if the (uncaptured) `phase3_checks.sh` pins each step internally, but it is not verifiable from the
captures. This is a minor documentation overstatement, not evidence that the checks ran on the wrong CPUs.

### 9. Read-only host checks — PASS

- `harness_forestcover_g5` is at `3f7b09fe…` with only `?? nodes/gc7rc_forestcover/data` untracked.
- The run root contains `captures/`, `captures_attempt1_20261128T173529Z/`, `records/`, `scripts/`, `work/`,
  etc.; attempt 1 is present.
- `nvidia-smi --query-compute-apps` is empty.

## Resolved blocker

At `5fc98d52`, `SHA256SUMS` listed 35 payload files but the branch carried 33; the two `run.log` files were
absent because `.gitignore` excludes `*.log`, so `shasum -a 256 -c SHA256SUMS` exited 1 and the record's
"35 files + `SHA256SUMS`" and "rc 0 after fetch" statements were false for the branch. `3a334d52` force-adds
those two files only. On the new tip the capture directory has 36 files, the 35 listed payloads verify, rc is 0,
and both log hashes match `SHA256SUMS`. The blocker is closed. The fix was mechanical; no rerun occurred.

## Minors

1. The "every C1-C6 step and every step-1-4 capture is `taskset -c 4-7`" claim is broader than the captures,
   as detailed in section 8.
2. "No CPUs 8-11 were used" and "load average 0.22 at session start" are not in the captures (`host_facts` has
   no load-average field and most JSONs do not record affinity). They are plausible but not evidenced.
3. "The skip is the root-only test" is not evidenced; the pytest tail shows only `27 passed, 1 skipped` and one
   `s`, without the skip reason.
4. `c7_final.json`'s `data.link` block inspects `nodes/gc7rc_forestcover` (reports `is_symlink: false`), not
   `nodes/gc7rc_forestcover/data`; the symlink claim is actually supported by the git status and `datapins`
   `link_present`/`link_target` fields. The field name is misleading, not wrong evidence.
5. The `i9-14900KF` CPU model is not in the captures; a live read-only check confirms it, so this is an
   evidence-coverage gap only.

## Decisive reasons

All substantive checks pass: every condition flag is true; stop items are empty; pytest is 27/1 at rc 0; the GPU
smoke has the full expected UUID, tensor sum 4096.0 and `effective: true`; the lease and end state are clean;
every pin/hash/number matches the captures; the harness diff and its two file hashes match the accepted review;
the checkout is detached at the exact pin with only the data symlink untracked; and the rerun is a disclosed
engineering rerun. The one blocker from the first review — an incomplete, non-verifying capture set — is closed
by `3a334d52`, which adds exactly the two missing `run.log` files without changing the record or any other
capture. The remaining issues are documentation/evidence-coverage minors, not defects in the host-check result.

**Reviewer: compute review agent (independent), 28 November 2026.**
