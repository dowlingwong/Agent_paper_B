# Independent review — Ada P.4 venv record, round 2 (27 November 2026)

Verdict: ACCEPTED

**Reviewer.** I wrote the round-1 review `ADA_P4_VENV_REVIEW_20261127.md` and did not write the record under
review, the venv or the smoke. This round is a desk re-check of the correction commit only: I opened no
credential, secret or sealed file, made no SSH connection and read no label or evaluation value. I changed
nothing except adding this review file.

**Summary.** The correction commit `a1d0cf74` resolves the round-1 MAJOR: `setup.log` is now in the commit,
its sha256 matches both `SHA256SUMS` and the record, and `shasum -a 256 -c SHA256SUMS` passes all seven files.
The circular branch line is gone, the freeze command is now the reproducible `sort -d`, and the Python pin is
separated from the 121-line package lock. The technical freeze, smoke and account claims are unchanged and
still supported. Two round-1 MINORs remain (a stale report cross-reference and some prose-only details); both
are non-blocking. No new MAJOR or BLOCKING finding.

## Inputs reviewed

| Input | Ref / path | sha256 |
|---|---|---|
| Record under review (R2) | `docs/r1/reports/trackp_p4_20261127/ADA_P4_VENV_20261127.md` on `origin/compute-ada-p4-venv-20261127` @ `a1d0cf74` | `3779d3b765ff242666079c6d02a86aca29150f13c7912ced49a0210ce3192d53` |
| Record at R1 | same path @ `ef146a64` | `52dfccdc002d9d06674fa1885d26985de3029225009e182bd0d1d1b34bf3c864` |
| Round-1 review | `docs/r1/reviews/ADA_P4_VENV_REVIEW_20261127.md` @ `e5d1b34e` | `bac2f81ccdb99ceccf0b77f41162a032d6909b6d7c431f2b26e3871b89aec7d9` |
| Setup log (new) | `…/ADA_P4_VENV_20261127_captures/setup.log` (5315 lines, 669,625 bytes) | `8ab832e46bbbf45fb9d9b8d00c73f807c0386a8029e36f85f77c3d84ce4d0282` |
| Capture manifest | `…/captures/SHA256SUMS` | `07349c647bca6dcc2ad3e58f0b7666e60546db7f067928868f0638f67464d539` |
| Freeze capture | `…/captures/freeze.txt` (121 lines) | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` |
| Lock copy | `…/captures/lock.sorted` (121 lines) | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` |
| Empty diff | `…/captures/freeze.diff` (0 bytes) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Smoke result | `…/captures/smoke_result.json` | `9477799f8a5f0b3a9a1a6228adaf4dc41bb29f8ceb80d0b45ac5af3512eafd56` |
| GPU before / after | `…/captures/smoke_gpu_before.txt` / `…_after.txt` | `ac3fdde359f3e54a9a30103a1903a03348467a7d9964f78b278448a17f9d1dfa` / `ee5da2e790a7c86044ca64de90a9f3269536677c451bb7267e9da78c4e6d82d2` |
| Coordinator status | `origin/coord/compute:reports/20261127-10-round-status.md` | `b9d7b32259bae27af7d55b04be5d26e6591b582ba4c575b118594d5f9e269929` |
| Coordinator report | `origin/coord/compute:reports/20261127-11-ada-p4-venv.md` | `39ac73fb559f52ec5f38f018d2f3d2c453cbfd5e9d72058bb19cc50652813da5` |

Reviewed branch tip: `a1d0cf74e103c178503b42009d3b175fff8c94c5`; previous tip `ef146a64`; base
`origin/main` `29099c4bac068355d0b5593b8ac9665e19f38049`. The correction is a new commit on top of
`ef146a64` (no force push); `git show --name-status a1d0cf74` changes only the record (M) and adds
`setup.log` (A).

## Per-finding resolution

| R1 finding | R2 status | Evidence |
|---|---|---|
| **MAJOR M1 — `setup.log` listed in the record and `SHA256SUMS` but absent from the commit; manifest fails** | **RESOLVED** | `setup.log` is now committed at `a1d0cf74`, 5315 lines / 669,625 bytes, sha256 `8ab832e4…`, equal to the `SHA256SUMS` line and to the record's capture list. `shasum -a 256 -c SHA256SUMS` prints `OK` for all seven files, including `setup.log`. The `.gitignore:3:*.log` rule is unchanged, but the file was force-added as intended. |
| **MINOR m1 — branch line had a circular “see the branch tip in the report header”** | **PARTIALLY RESOLVED / REMAINING MINOR** | The circular placeholder is gone. The line now says the coordinator report `coord/compute` names the tip. The relevant report (`reports/20261127-10-round-status.md`, line 12) names `ef146a64`, not this correction commit `a1d0cf74`. The reference is stale but no longer circular; name `a1d0cf74` directly or update the coordinator report. |
| **MINOR m2 — several details had no committed capture** | **PARTIALLY RESOLVED / REMAINING MINOR** | `setup.log` now carries Python 3.12.10, `torch==2.6.0+cu124`, `nvidia-cudnn-cu12==9.1.0.70`, the sdist check (`causal_conv1d-1.7.0.tar.gz: OK`), the `nvcc` line with `-gencode=arch=compute_89,code=sm_89` and `-D_GLIBCXX_USE_CXX11_ABI=0`, and the install paths. Still prose-only: the `zli538` uid 1008, the 5.8 GB / 7.5 GB disk figures, the `flock` lease, the wheel sha256 `8f676dbd…`, driver 545.23.08, host `ucrtasl`, the `dowling` key refusal and “no sudo”. Non-blocking per the task. |
| **MINOR m3 — `uv pip freeze | sort` did not reproduce the cited hash under a plain locale sort** | **RESOLVED** | The record now says `uv pip freeze | sort -d` (package-name order), notes that the host's plain locale sort gives a different textual order for the same 121 lines, and compares to `sort -d` of the lock. `sort -d` of the committed lock is exactly `50238e5a…`; the empty `freeze.diff` and 121-line captures are unchanged. |
| **MINOR m4 — “the image lock is 3.12.15” conflated the Python pin with the freeze lock** | **RESOLVED** | The record now reads “the image's Python pin is 3.12.15 (the 121-line package lock has no Python line)”. The value and the 121-line lock are correct and the two artifacts are distinguished. |

## The six checks (re-run)

### 1. `SHA256SUMS` recomputes; freeze equals the sorted lock — PASS

```
$ shasum -a 256 -c SHA256SUMS
freeze.txt: OK
freeze.diff: OK
lock.sorted: OK
smoke_result.json: OK
smoke_gpu_before.txt: OK
smoke_gpu_after.txt: OK
setup.log: OK
```

`freeze.txt`, `lock.sorted` and the committed lock are all `50238e5a…` at 121 lines; `freeze.diff` is
0 bytes (`e3b0c442…`); `cmp` is silent. `setup.log` is 5315 lines, 669,625 bytes, sha256 `8ab832e4…`, and is
in the commit. This is the round-1 failure fixed.

### 2. Python 3.12.10 vs image 3.12.15, and the package pins — PASS

The record still reports CPython 3.12.10 from `uv` 0.7.8 and the image's Python pin 3.12.15, now explicitly
separated from the 121-line package lock, which has no Python line. `setup.log` corroborates CPython 3.12.10,
`torch==2.6.0+cu124`, `nvidia-cudnn-cu12==9.1.0.70`, the sdist extraction/check and the source build for
`sm_89` with `_GLIBCXX_USE_CXX11_ABI=0`. The lock still has `causal-conv1d==1.7.0` (line 10) and
`torch==2.6.0+cu124` (line 108). The wheel sha256 remains prose-only (m2), which is a non-blocking evidence
gap, not a contradiction: the build lines and the installed `causal-conv1d==1.7.0` are in the log.

### 3. Torch smoke capture — PASS

`smoke_result.json` is unchanged: `available: true`, `capability: [8, 9]`, `cuda: "12.4"`, `device_count: 1`,
`elapsed_s: 0.53`, `matmul_sum: 127330.1875`, `max_memory_allocated_mib: 168.1`,
`torch: "2.6.0+cu124"`, RTX 6000 Ada. Card 2 is `GPU-f439cca8-…`, empty before (5 MiB, 0 %), 7 % after the
finished smoke; 0.53 s is 0.000147 GPU-h, far under 0.01. The before/after captures still list only GPU
UUIDs, pids and MiB — no user names or command lines. `setup.log` adds no process listing and no other
user's path (only `/data1/zli538/…`), so the redaction boundary is intact.

### 4. Account disclosure — PASS

The **Host and account (disclosed)** section is unchanged: `ssh ada_server` logs in as `zli538` (uid 1008),
not `dowling` (uid 1030); everything is written only under `/data1/zli538/paperb_p4_20261127/`; no sudo; no
other user's file or process; and the coordinator is warned to reconcile the account before the probe.
`setup.log` contains only `/data1/zli538/…` paths (no `/home/…`, no other account name) and no credential
material. The uid itself is still not captured (m2), but the disclosure is correct and not hidden.

### 5. No P.4 probe/SFT, no label/evaluation read, no image or run directory — PASS

`a1d0cf74` adds only `setup.log` and edits the record. It adds no probe script, SFT launch, run directory,
image, label table or evaluation value. The record's **What this does not do** paragraph is unchanged and
still bounded: the probe is unblocked only on the environment side, the launcher must be pointed at the venv
and the actual account, and the phase-1 note is still a draft needing its own task/note. It does not start
the probe.

### 6. Freeze check is the direct `uv pip freeze` comparison, not the P.4 runner — PASS

The record reports `uv pip freeze | sort -d` with sha256 `50238e5a…`, equal to `sort -d` of the lock, with
an empty `freeze.diff`. It does not claim the P.4 runner's `env3` check and does not claim a launch. This is
the direct comparison the task allows; the reproducible sort wording is now correct.

## New findings

No new BLOCKING or MAJOR finding. The correction is narrow and does not change a technical number or a
boundary.

- **Nit (non-blocking) — `lock.sorted` is still a byte copy of the lock.** The record now says it is `sort -d`
  of the lock, which is true because `sort -d` preserves this lock's order; the file name is not misleading
  in that sense. No action needed.
- **Nit (non-blocking) — the force-added `setup.log` remains covered by `.gitignore:3:*.log`.** A future edit
  will be ignored unless force-added again. This is an operational note for the next capture round, not a
  defect in this commit.

## Hashes and verdict basis

- **Reviewed record sha256:** `3779d3b765ff242666079c6d02a86aca29150f13c7912ced49a0210ce3192d53`
- **Reviewed branch tip:** `a1d0cf74e103c178503b42009d3b175fff8c94c5`
- **Round-1 review sha256:** `bac2f81ccdb99ceccf0b77f41162a032d6909b6d7c431f2b26e3871b89aec7d9`
- **Review file sha256:** a file cannot contain its own hash without changing it. The sha256 of the committed
  blob is recorded in the commit message that adds this file (`Review file sha256: …`) and is reported with
  the branch tip. Verify with:
  `git show compute-ada-p4-venv-review-20261127:docs/r1/reviews/ADA_P4_VENV_REVIEW_R2_20261127.md | shasum -a 256`.

No BLOCKING and no MAJOR finding. The one MAJOR from round 1 is resolved, and the two remaining MINORs
(stale coordinator-report cross-reference; prose-only uid/disk/lease/wheel/driver details) do not change a
check outcome, a technical number or the evidence boundary.
