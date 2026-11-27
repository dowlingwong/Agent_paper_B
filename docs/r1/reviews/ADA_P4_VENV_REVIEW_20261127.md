# Independent review — Ada P.4 venv from the Track P GPU lock (27 November 2026)

Verdict: CHANGES REQUIRED

**Reviewer.** I am an independent, AI-assisted reviewer in a fresh session. I did not write
`docs/r1/reports/trackp_p4_20261127/ADA_P4_VENV_20261127.md` (the record under review), I did not build the
venv, and I did not run the torch smoke. This was a desk review of the committed record and captures: I opened
no credential, secret or sealed file, made no SSH connection and read no label or evaluation value. I changed
nothing except writing this review file.

**Summary.** The technical result is supported: the committed freeze is byte-identical to the P.4 lock
(121/121 lines, `50238e5a…`), and the smoke capture is credible (`available: true`, capability `[8, 9]`,
0.53 s, 168.1 MiB, empty card 2). One MAJOR finding and four MINOR findings remain. The MAJOR is an evidence
bundle defect, not a contradiction of the freeze or smoke numbers: `setup.log`, which the record lists as a
capture and `SHA256SUMS` hashes, is not in the commit, so the manifest does not recompute. The Python-version,
account-uid, cuDNN, disk-size, build-wheel and lease claims therefore have no committed capture behind them.

## Inputs reviewed

| Input | Ref / path | sha256 |
|---|---|---|
| Record under review | `docs/r1/reports/trackp_p4_20261127/ADA_P4_VENV_20261127.md` on `origin/compute-ada-p4-venv-20261127` @ `ef146a64` | `52dfccdc002d9d06674fa1885d26985de3029225009e182bd0d1d1b34bf3c864` |
| Capture manifest | `…/ADA_P4_VENV_20261127_captures/SHA256SUMS` | `07349c647bca6dcc2ad3e58f0b7666e60546db7f067928868f0638f67464d539` |
| Freeze capture | `…/captures/freeze.txt` (121 lines) | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` |
| Lock copy | `…/captures/lock.sorted` (121 lines) | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` |
| Empty diff | `…/captures/freeze.diff` (0 bytes) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Smoke result | `…/captures/smoke_result.json` | `9477799f8a5f0b3a9a1a6228adaf4dc41bb29f8ceb80d0b45ac5af3512eafd56` |
| GPU before | `…/captures/smoke_gpu_before.txt` | `ac3fdde359f3e54a9a30103a1903a03348467a7d9964f78b278448a17f9d1dfa` |
| GPU after | `…/captures/smoke_gpu_after.txt` | `ee5da2e790a7c86044ca64de90a9f3269536677c451bb7267e9da78c4e6d82d2` |
| Committed P.4 lock | `r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt` @ `ef146a64` (121 lines) | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` |
| Task `compute/20261127-06` | `origin/coord/coordinator:tasks/compute/20261127-06-ada-p4-venv.md` | `e08d9d6c5d71b4fb2b8fd6e4f0c3fd63c7ba439326ee18fb490a9bc602f90bb7` |
| Task `compute/20261127-11` | `origin/coord/coordinator:tasks/compute/20261127-11-ada-route.md` | `5316a2a8ee62133e4b64ec07de615247df2dc8e03c9ad1f0c58f0d1ee6f6ddd7` |
| Canon rules | `canon/README.md` @ `origin/main` | `de4d2dccb734cc33818bf5d8c02095736b6e82c7c4b48caef7da087f011275e2` |
| Canon compute table | `canon/COMPUTE.md` @ `origin/main` | `3b0237ebefd211b0d608429b45b30f9ff494bb9d87e0559a19352a4d400d2024` |
| Git ignore rules | `.gitignore` @ `origin/main` | `cd9ce714d347e82292a245e2679e2549f4befd843101a4f7dcf19f0e636b5e80` |
| Image definition | `r1/scripts/htcondor/docker/Dockerfile` @ `ef146a64` | `40c35e2c9600bbb6dabb8ea8b159c565f00730960122cfba5a4f19f589bb3764` |

Reviewed branch tip: `ef146a644ea0efddb90f8f92516647e91a8e530c`; base `origin/main`
`29099c4bac068355d0b5593b8ac9665e19f38049` (the commit is a single-parent child of `29099c4b`).

## Verification method (read-only)

- Recreated the tip and `origin/main` in scratch worktrees, then recomputed every cited sha256 with
  `shasum -a 256`; the record's `52dfccdc…` matches the task prompt.
- Ran `shasum -a 256 -c SHA256SUMS` in the capture directory; ran `cmp` between `freeze.txt`, `lock.sorted`
  and the committed lock; counted lines with `wc -l`; checked the zero-byte diff.
- Read the image's env3 build block (`Dockerfile` lines 96–140 and the VERSIONS block) to compare the pin,
  the 121-line lock, the source build of `causal-conv1d`, the `TORCH_CUDA_ARCH_LIST` and the ABI flags with
  the record's build paragraph.
- Read the smoke JSON and the before/after `nvidia-smi` captures; checked the card-2 UUID, the 168.1 MiB
  peak, the 0.53 s elapsed time and the GPU-hour arithmetic; diffed before against after.
- Read both task files and the Ada row and shared-host rules in `canon/COMPUTE.md`; checked the record's
  account disclosure and scope against `canon/README.md` rules 3, 4 and 8.
- Checked the commit's file list and `.gitignore` for the missing `setup.log`; checked that no probe, run
  directory, image, label table or evaluation file is added.

## The six checks

### 1. Capture `SHA256SUMS` recomputes; `freeze.txt` equals the sorted lock — FAIL

The freeze part passes exactly:

```
freeze.txt   50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08  (121 lines)
lock.sorted  50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08  (121 lines)
<committed lock> 50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08  (121 lines)
freeze.diff  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  (0 bytes)
```

`cmp` is silent for all three pairs. The manifest, however, does not recompute:

```
$ shasum -a 256 -c SHA256SUMS
freeze.txt: OK
freeze.diff: OK
lock.sorted: OK
smoke_result.json: OK
smoke_gpu_before.txt: OK
smoke_gpu_after.txt: OK
shasum: setup.log: No such file or directory
setup.log: FAILED open or read
shasum: WARNING: 1 listed file could not be read
```

`SHA256SUMS` line 7 is `8ab832e46bbbf45fb9d9b8d00c73f807c0386a8029e36f85f77c3d84ce4d0282  setup.log`,
and the record lists `setup.log` among the captures (record line 12). The commit `ef146a64` adds eight files
and no `setup.log` (`git show --name-status ef146a64`). The cause is the repository's ignore rule:

```
$ git check-ignore -v docs/r1/reports/trackp_p4_20261127/ADA_P4_VENV_20261127_captures/setup.log
.gitignore:3:*.log  docs/r1/reports/trackp_p4_20261127/ADA_P4_VENV_20261127_captures/setup.log
```

So the capture was hashed on the host but was silently left out of the commit by `*.log`. The result is a
record that names a capture it does not carry and a manifest that cannot be verified. This is MAJOR (M1);
the required freeze capture itself is intact.

### 2. Python 3.12.10 vs image 3.12.15, and the package pins — PASS

The record states the venv's Python is **3.12.10**, that the image's Python is **3.12.15**, that this is the
only version difference, and that the difference is reported rather than hidden. It does not claim the image's
Python. The image definition supports the comparison: `ARG PY312=3.12.15` (`Dockerfile` line 37), and the
env3 block says the image is built from the committed 121-line freeze with Python 3.12.15
(`Dockerfile` lines 9–13, 96–99). The lock itself has the expected lines: `causal-conv1d==1.7.0` (line 10),
`torch==2.6.0+cu124` (line 108), with the three pinned VCS packages at their commits (lines 38, 49, 102).

The record also states `torch 2.6.0+cu124`, CUDA 12.4, `causal-conv1d 1.7.0` built from the pinned sdist for
`sm_89` with `_GLIBCXX_USE_CXX11_ABI=0`, and the wheel sha256
`8f676dbd2d42588d4fa85aabcb2da8f1bd9bf46dbdeea7b51c7dddf01e4e3e6f`. That matches the image's documented
route (source build, ABI 0, `TORCH_CUDA_ARCH_LIST`), except that the image builds `8.0;8.9;9.0` while the
record builds `sm_89` only — a deliberate, disclosed choice, adequate for an Ada card (sm_89).

Caveat (MINOR m2): the committed captures do not independently show Python 3.12.10, CUDA 12.4/cuDNN 9.1.0,
the disk figures, the wheel sha256 or the `flock` lease. The smoke JSON carries `torch: "2.6.0+cu124"` and
`cuda: "12.4"`; the rest is only in the record. `setup.log` would have carried most of it.

### 3. Torch smoke capture — PASS

`smoke_result.json` is the claimed one-line result:

```
{"available": true, "capability": [8, 9], "cuda": "12.4", "device_count": 1,
 "elapsed_s": 0.53, "matmul_sum": 127330.1875, "max_memory_allocated_mib": 168.1,
 "name": "NVIDIA RTX 6000 Ada Generation", "torch": "2.6.0+cu124"}
```

The capture is credible: capability `[8, 9]` is sm_89, the device is the RTX 6000 Ada, the card is card 2
(UUID `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154` in both before and after), it was empty before (5 MiB used,
0 % utilisation) and only our smoke touched it (7 % after, test finished), and 0.53 s is
0.53/3600 = 0.000147 GPU-h, well under 0.01 GPU-h. 168.1 MiB is far inside the 48 GB card.

`smoke_gpu_before.txt` and `smoke_gpu_after.txt` are present and list only per-GPU totals and process rows as
`GPU-UUID, pid, MiB`; they contain **no user names and no command lines**. That is the required redaction.
The before/after diff is only card 2's utilisation (0 % → 7 %, our smoke) and the other cards' normal
fluctuation; no foreign process was added or removed. Minor caveats: the captures have no timestamp, no
explicit row for our own pid, and the `flock` lease is not shown; none undermines the smoke.

### 4. Account disclosure — PASS

The record opens with a dedicated **Host and account (disclosed)** section. It says `ssh ada_server` reaches
Ada through the jump host and logs in as **`zli538` (uid 1008)**, not `dowling` (uid 1030), that the
`dowling` key is still refused, that everything was written only under
`/data1/zli538/paperb_p4_20261127/`, that no sudo was used, and that no existing file, process or other
user's directory was touched. It also warns that if the coordinator intended the `dowling` account, the route
and the P.4 direct launcher's calling user must agree before the probe.

That is the correct disclosure, not a hidden or overclaimed account. The record does not present `zli538` as
the `dowling` account and does not claim the image's `/opt/r1` Python. It is consistent with the task's route
(`compute/20261127-11`) and with the `canon/README.md` rules: no credential read, no sudo, and no other
user's file or process touched. The one caveat is evidential: the `id -un`/`id -u` output that would prove
uid 1008 is in the missing `setup.log`, so the uid claim cannot be independently recomputed from the commit
(see M1/m2). The disclosure itself is honest.

### 5. No P.4 probe/SFT, no label/evaluation read, no image or run directory — PASS

`git show --name-status ef146a64` adds only the record and its capture directory (eight files, all under
`docs/r1/reports/trackp_p4_20261127/`). There is no probe script, no SFT launch, no run directory, no image,
no label table and no evaluation value. The record's own **What this does not do** paragraph is bounded: it
says the work does not run the P.4 probe or SFT, does not fill `trackp_ada_v1.json`'s TODO host fields, and
does not create a P.4 run directory. Its only forward-looking sentence is that `compute/20261126-07` is
unblocked **on the environment side**, that the direct launcher must be pointed at the venv and the actual
account, and that the phase-1 note is still a draft and the probe needs its own task/note. That does not start
the probe.

### 6. Freeze check is the direct `uv pip freeze` comparison, not the P.4 runner — PASS

The record's **Build** section says: "Freeze comparison: `uv pip freeze | sort` sha256
`50238e5a…`, equal to the sorted lock; `freeze.diff` is empty (0 bytes, sha256 `e3b0c442…`). Every pinned
package line matches." It does not claim the P.4 runner's `env3` freeze check, and it does not claim a
launch. That is the direct comparison the task allows when the runner cannot run on the host. The committed
`freeze.txt` and empty `freeze.diff` support the claim. See m3 for the exact-sort wording.

## Findings

**MAJOR — M1. `setup.log` is listed in the record and in `SHA256SUMS` but is not in the commit.** Evidence:
`SHA256SUMS` line 7 gives its sha256; the record's capture list (line 12) names it; `git show --name-status
ef146a64` has no such path; `git check-ignore -v` shows `.gitignore:3:*.log` matched it, so it was never
added. `shasum -a 256 -c SHA256SUMS` fails on that one line. This is not cosmetic: the missing log is the
only capture that could show `id -un`/`id -u` (the zli538 account claim), `python -VV` (3.12.10), the cuDNN
and disk readings, the wheel sha256 and the `flock` lease. The required freeze and smoke captures are present,
so the technical result stands, but the record's capture set and integrity manifest are wrong as committed.
Fix one of: (a) force-add `setup.log` (`git add -f`) after checking it contains no credential, no other
user's process name/command line and no unredacted sensitive path; or (b) redact/regenerate it and commit the
redacted version; or (c) remove it from `SHA256SUMS` and from the record's capture list and add small separate
captures for `id`, `python -VV`, `torch`/cuDNN, `du -sh`, the wheel sha256 and the lease. Until one is done,
the record overstates its evidence bundle.

**MINOR — m1. The branch line has no tip.** The record says
`**Branch:** compute-ada-p4-venv-20261127 @ (this commit; see the branch tip in the report header)`. There is
no tip in the header; the line is circular. A report should name the branch and the commit. Write
`ef146a64` (or the fix commit) explicitly.

**MINOR — m2. Several factual details have no committed capture.** Python 3.12.10, CUDA 12.4/cuDNN 9.1.0,
the venv size (5.8 GB) and engineering root (7.5 GB), the `flock` lease, the wheel sha256
`8f676dbd…`, the pinned-sdist identity and the `dowling` key refusal are only in the record's prose (or in
the missing `setup.log`). The smoke JSON covers `torch 2.6.0+cu124` and `cuda 12.4`; the rest should be
captured or the record should say which capture carries each claim. This is an evidence gap, not a wrong
value: the values are plausible and consistent with the Dockerfile and the lock.

**MINOR — m3. The stated sort command does not reproduce the cited hash under a plain `sort`.** The
committed lock's order is a package-name/`sort -d` order (it puts `httpcore==1.0.9` before
`httpcore2==2.13.1`, and `langgraph==1.1.10` before `langgraph-checkpoint==4.0.3`). Plain `sort` under the repository's
`en_US.UTF-8` locale gives `673d24fb…`; `LC_ALL=C sort` gives `2d76e44c…`; neither is `50238e5a…`.
`sort -d` and a Python sort keyed on the package name give `50238e5a…`. The equality between `freeze.txt` and the lock is
real, but the record's `uv pip freeze | sort` wording is not the command that produces the cited hash. State
the actual sort (e.g. `sort -d`, or "uv's package-name order") and consider renaming `lock.sorted` to
`lock.copy`, since it is a byte copy of the lock, not a fresh `sort`.

**MINOR — m4. "the image lock is 3.12.15" conflates the Python pin with the freeze lock.** The 121-line
`pip_freeze_trackp-gpu.txt` contains no Python interpreter line; 3.12.15 is the Dockerfile's `ARG PY312`
pin (and the image's `python -VV`). Say "the image's Python pin is 3.12.15" or "the image runs 3.12.15". The
reported values are not wrong, only the noun.

## Scope confirmation

I read only the repository blobs and worktrees named above. I made no SSH connection, read no host state, no
credential and no sealed file. I did not modify `main`, `coord/*`, the reviewed branch, the record, the
captures or any lock. The only file I wrote is this review. The review branch is based on `origin/main`
`29099c4b` and contains this file only.

## Hashes

- **Reviewed record sha256:** `52dfccdc002d9d06674fa1885d26985de3029225009e182bd0d1d1b34bf3c864`
- **Reviewed branch tip:** `ef146a644ea0efddb90f8f92516647e91a8e530c`
- **Review file sha256:** a file cannot contain its own hash without changing it. The sha256 of the committed
  blob is recorded in the commit message that adds this file (`Review file sha256: …`) and is reported with
  the branch tip. Verify with:
  `git show compute-ada-p4-venv-review-20261127:docs/r1/reviews/ADA_P4_VENV_REVIEW_20261127.md | shasum -a 256`.
