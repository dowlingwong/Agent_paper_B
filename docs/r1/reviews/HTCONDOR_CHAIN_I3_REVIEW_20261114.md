# Independent pre-submission review — I3 GPU job: pinned HuggingFace GGUF + llama-server on the ghcr gpu image (15 Nov 2026)

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the unit, not the executing agent; I
did not write, submit or run anything on the cluster. The only external check I made is a read-only public
HuggingFace API request to verify the pinned model revision (below).

**Date/time of review:** 15 November 2026, 09:55–10:20 CET (Europe/Berlin).

**Reviewed unit:** `docs/r1/reports/htcondor_chain_20261114/i3/{i3_run.sh, i3_nemo2_l40s.jdl,
i3_topas_v100s.jdl, submit_i3.sh}`, committed at worktree HEAD **`ea9a9a0f`** ("I3 unit (HF pinned GGUF download
+ sha256 + llama-server), TOpAS ProvidesEtpCeph finding"); pinned below by SHA-256. No I3 job has been submitted
(the chain report says "no I3 job submitted yet"; nothing of this unit appears in the job/queue records).

**Basis.** Author's 15 Nov decision (option e) and the chain-report §I3/§S5/§GPU-image evidence
(`docs/r1/reports/HTCONDOR_CHAIN_20261114.md` L106–L128); the verified ghcr gpu image
(`ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…5296`: SIF 5,226,487,808 B, three envs, torch 2.6.0+cu124,
`llama-server --version` rc 0 on NEMO2 L40S in S5); the S5 sandbox evidence used for the disk sizing (chain report
L114: OCI cache under `/srv`, job dir ≈ 11 GB during the run); the `gpu_availability.tsv` snapshots
(pre-S5 rows at 01:41 CET: NEMO2 L40S 10 slots / 7 idle / 3 drained, H200 3/1/1; TOpAS V100S 14/7/0/7, A100
16/3/0/13); the author's original I3 spec (docker universe on TOpAS V100S, container universe on NEMO2); and the
read-only HF API (independent verification of the pinned revision, below).

**Hard limits of this review.** No SSH, no HTCondor commands, no submission, no git commit/push, no file written
except this review. The image's final-layer contents (`curl` presence, docker daemon state on TOpAS) cannot be
inspected from here; those are stated as pre-submission gates, not as findings of fact.

---

## 1. Files reviewed and pinned (SHA-256)

| File | Bytes | SHA-256 |
|---|---|---|
| `i3/i3_run.sh` | 3957 | `d984550cd3119727d4039c3a2b090ac98e623d89a2cb0471738f88f16bf32ee8` |
| `i3/i3_nemo2_l40s.jdl` | 702 | `3ffe933741ba93e84b80c5ae4cd8d6bfb19f93d10cec240da6225f3a44dc1bbc` |
| `i3/i3_topas_v100s.jdl` | 648 | `f1454e8f994effbfa59f6a8ee58f3ef9ae9e80e6acbc12359519444ac681ede0` |
| `i3/submit_i3.sh` | 2056 | `5be02f05641c6db031dfc2cc144d7228e2078ec2ffe438a15574b57855f5bf2b` |

### Independent verification of the model pin (HF API, read-only)

`https://huggingface.co/api/models/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/tree/13fb94bfda8c8cf22497dc57b78f391a9acb426a`
returns the revision's file list; `qwen2.5-coder-7b-instruct-q4_k_m.gguf` is present with
`size = 4,683,073,536` and LFS `oid = 509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`.
That matches **exactly** the unit's URL file name, `EXPECT_BYTES` and `EXPECT_SHA` (the LFS oid is the sha256 of
the file content). The revision `13fb94bf…426a` is a full 40-hex commit sha, i.e. immutable; the file is public
(no credentials needed). Verified independently of the operator's claim.

---

## 2. Checks performed, and results

### 2.1 JDLs against the author's I3 spec

**NEMO2 (`i3_nemo2_l40s.jdl`)** — `universe = container` (L1), `container_image = docker://ghcr.io/dowlingwong/
r1-htc-gpu@sha256:69b06b35…5296` (L2, the verified gpu digest, no placeholder), `executable = i3_run.sh` (L3),
`arguments = "$(ClusterId).$(ProcId)"` (L4), transfer YES/ON_EXIT (L5–L6), input `i3_run.sh` (L7), six output
files (L8), `output/error/log` (L9–L11), `+RequestWalltime = 2400` (L12), CPUs 4 (L13), Memory 16000 (L14),
`request_disk = 12000000` kB (L15), `request_GPUs = 1` (L16, whole GPU, no `+RequestGPUMemoryMB`),
`+RemoteJob = True` (L17), `requirements = (TARGET.CloudSite =?= "BwForCluster-Nemo2") &&
(TARGET.GPUs_DeviceName =?= "NVIDIA L40S")` (L18), `queue 1`. Device string and CloudSite are the measured ones
(S1/S2); no `ProvidesETPResources` on a remote job. **Conforms except for the disk sizing — MAJOR M1 — and the
walltime headroom — MAJOR M2.**

**TOpAS (`i3_topas_v100s.jdl`)** — `universe = docker` (L1), `docker_image = ghcr.io/dowlingwong/r1-htc-gpu@
sha256:69b06b35…5296` (L2, **no `docker://` prefix**, correct for docker universe), `executable = i3_run.sh`
(L3), `arguments` (L4), transfer fields (L5–L8), `output/error/log` (L9–L11), walltime 2400 (L12), CPUs 4 /
Memory 16000 / disk 12,000,000 (L13–L15), `request_GPUs = 1` (L16), `+RemoteJob = True` (L17),
`requirements = TARGET.GPUs_DeviceName =?= "Tesla V100S-PCIE-32GB"` (L18). Correct for the author's original I3
spec (docker universe on TOpAS V100S). The docker-universe match gate is appended by `condor_submit` as
`TARGET.HasDocker` (not `HasDockerURL`; the latter belongs to container-universe `docker://` URLs) — and
`HasDocker=true` was measured on the TOpAS slots (`raw_container_attrs_topas.txt`; chain report L125: 18×A100 /
13×V100S, all `ProvidesEtpCeph=true`, `HasDocker=true`). The dry-run ad must confirm this (gate). The ghcr
package passed anonymous registry verification, so an anonymous `docker pull` of the digest should work if the
TOpAS daemon has egress; the expected failure is an image-pull hold (see §2.5) — MINOR m2.

### 2.2 `i3_run.sh` — pinned download, verification, server, evidence

- **Pin:** `URL` (L10) is the HF `resolve/<full sha>/qwen2.5-coder-7b-instruct-q4_k_m.gguf` form (verified
  above), `EXPECT_SHA` (L11) and `EXPECT_BYTES` (L12) match the HF API values exactly.
- **Download:** `curl -L --fail --retry 3 --retry-delay 5 --max-time 1500 -o model.gguf "$URL"` (L27), timed
  (L26–L29); `-L` follows the HF CDN redirect; `--fail` fails on HTTP errors; `--retry` covers transient
  codes (408/429/5xx) — 404 fails fast, correct for a bad revision/path; `--max-time 1500` bounds it. `i3_download.txt`
  records URL, rc, seconds, bytes vs expected and the log tail (L31–L35); the byte check + rc gate FAIL (L36).
- **sha256 gate:** `sha256sum` → `i3_sha.txt` with got/expected/match; FAIL on mismatch (L37–L40). ✓
- **Server:** `/opt/r1/llama/bin/llama-server -m model.gguf --host 127.0.0.1 --port 8091 -ngl 99 -c 2048` (L44),
  120 × 2 s = **240 s** `/health` wait (L46–L51), `/v1/models` fetched ≤400 chars (L53), then `kill` + `wait`
  (L54), CUDA/offload/load-time lines captured from the server log (L60), `server_ready` gate (L62). ✓ No
  nvidia-smi gate (the S5 artefact is avoided — good; it records `/proc/driver/nvidia/version`, `/dev/nvidia*`
  and torch instead).
- **Evidence/transfer:** six output names (JDL L8) `i3_identity.txt, i3_download.txt, i3_download.log,
  i3_sha.txt, i3_server.txt, i3_PASSFAIL.txt`; the script pre-creates only **five** (L13 — `i3_download.log` is
  missing) — MINOR m1. The 4.35 GiB `model.gguf` and `llama-server.log` are deliberately **not** in the transfer
  list (correct: transferring 4.35 GiB back would be wasteful/held); the server log's key lines are copied into
  `i3_server.txt` so a load failure is still visible.
- **Writes:** everything is relative to the job sandbox (`model.gguf`, the six files, `llama-server.log`); no
  `/work`, `/tmp` or other path is written; no credentials (public HF URL, no token/auth header); no network
  beyond the download. ✓
- **PASS/FAIL + exit:** `i3_PASSFAIL.txt`, `I3_DONE fail=…`, `exit "$FAIL"` (L67–L70). ✓
- **Dependency risk (MINOR m3):** the script needs `curl` (plus `sha256sum`, `stat`, `seq` from coreutils) inside
  the gpu image. The Dockerfile deliberately drops `curl` from its dnf lists (relying on the Rocky 9 base's
  `curl-minimal`, which caused the first-CI `curl` conflict), and neither the image verification nor S5 ever ran
  `curl`. It is very likely present, but I cannot verify it read-only — see the pre-submission gates.

### 2.3 Caps and GPU-hour accounting

- Two GPU jobs total, **one at a time** (author order: NEMO2 first, then TOpAS once); 1 GPU each; 1.33 GPU-h with
  `+RequestWalltime = 2400` (2 × 2400 s = 4,800 s = 1.33 GPU-h ≤ 10 GPU-h); if M2's fix raises the walltime to
  3600 s, the total is 2 GPU-h — still ≤ 10. One concurrent job ≤ the author's 10-concurrent cap. ✓ (Record the
  queue snapshot before each submission.)
- The walltime/GPU-hour interplay is fine; the concern is **whether 2400 s is enough wall-clock inside the job**
  (M2), not the cap.

### 2.4 TOpAS/NEMO2 context

- **NEMO2:** no Docker (S1: `HasDocker` undefined on all NEMO2 slots), singularity 1.5.4 → container universe with
  the `docker://` digest is the correct route, and S5 already demonstrated the same image pulling through
  Singularity on NEMO2 L40S (pull inside `run_s`). ✓
- **TOpAS:** all A100/V100S slots advertise `HasDocker=true` and `ProvidesEtpCeph=true` (chain report L125;
  `raw_container_attrs_topas.txt` for the container attrs). The docker-universe route the author specified
  should match. `ProvidesEtpCeph` is not needed for the HF route (the author's `/ceph/srv` fallback is recorded,
  not used). The docker daemon's pull of a public ghcr digest and the nvidia-container GPU injection are the two
  unproven steps (m2) — the job itself is the test; record the outcome.
- **GPU compatibility:** the image's llama.cpp is built with CUDA arch `70;80;89;90` (V100 = 70 ✓, L40S = 89 ✓);
  torch 2.6.0+cu124 must also support sm_70 for the V100S — the job's own torch line records this; if torch
  reports "no kernel image is available" that is a stack note, and llama-server is the primary I3 test (m4).

### 2.5 Failure modes to be recorded (not hidden)

| Mode | Expected evidence | Handling |
|---|---|---|
| HF 429 / 5xx | curl `--retry 3` retries; download log tail + rc recorded | record rc/seconds; a partial file fails the byte/sha gate → I3_FAIL, exit 1 |
| HF 404 / bad revision | curl `--fail` fails fast; log tail recorded | record; do not retry blindly (the pin is immutable; a 404 means a wrong URL) |
| size/sha mismatch | `i3_sha.txt`/`i3_download.txt` with got vs expected | record; I3_FAIL; do not load the model |
| disk short | curl/`stat` errors; `df` in identity | record; see M1 — a clean pre-download disk check would help |
| llama load failure | `i3_server.txt`: server log head/tail + grep of CUDA/GPU/device/offload/load time | record the exact CUDA/offload lines (e.g. "no CUDA-capable device", "failed to allocate", "offloaded 0/… layers"); this is the author's diagnostic requirement |
| `/health` timeout | `server_ready=0 ready_s≈240`, server killed | record; check whether the process had already exited (`kill -0` breaks the loop) |
| TOpAS docker image pull failure | hold (image-pull family, e.g. `HoldReasonCode 35`, event 012), or container-start failure | record verbatim; do not silently switch to container universe (the author specified docker); put the fallback in the question list |
| walltime hold | hold code 46/47 family, no transferred evidence (ON_EXIT) | record; no blind retry (see M2) |
| GPU not injected | torch `cuda_available False`, no `/dev/nvidia*`, llama load failure; for TOpAS docker, the nvidia runtime may not pass the GPU | record; distinguish "no GPU in container" from "image defect" (S5 proved the image works on a real L40S) |
| model transfer back | n/a | the 4.35 GiB model is not in `transfer_output_files` ✓ (avoid a giant output transfer) |

---

## 3. Findings

### BLOCKING

None certain. The unit is a valid container-universe + docker-universe pair with a correctly pinned model and a
sane server test; the blocking-class risks are the two MAJORs below (both fixed by a JDL number), which must be
fixed before submission.

### MAJOR

**M1 — the NEMO2 `request_disk = 12,000,000` kB is under the measured footprint of this image + the model.**
S5, on the same gpu image and the same container-universe route, recorded the OCI cache inside the job sandbox
(`APPTAINER_CACHEDIR=/srv`) and the job dir **≈ 11 GB during the run** (chain report L114) with
`request_disk = 25,000,000` kB. I3 adds the **4.35 GiB** GGUF download in the same sandbox → about
**15–16 GiB** of sandbox usage, while 12,000,000 kB ≈ **11.4 GiB**. If the NEMO2 EP provisions/enforces the
requested disk (LVM/cgroup), the image cache alone fills it and the model download fails with a disk-full hold;
even without enforcement the request is not sized from evidence. *Exact fix:* set the NEMO2 JDL
`request_disk = 25000000` (the S5-proven value; covers image cache + extraction + model + margin), record the
dry-run `DiskUsage`, and note the S5 measurement as the sizing basis. (TOpAS docker is different: the docker
image lives in the daemon's store, so 12,000,000 kB covers the 4.35 GiB model + logs — keep or raise for
uniformity.)

**M2 — 2400 s walltime has insufficient headroom for the pull + GGUF download + load, and a walltime kill loses
the evidence the author asked for.** In S5 the 4.87 GiB image pull happened **inside `run_s`** (run 830 s). I3
must additionally download 4.35 GiB from HuggingFace (`--max-time 1500` = 25 min cap) and load the model, all
inside the same walltime; the worst case (≈800 s pull + ≤1500 s download + load/health) exceeds 2400 s. Because
`when_to_transfer_output = ON_EXIT`, a walltime kill transfers **none** of the six evidence files — including the
download time the author explicitly wants. *Exact fix:* raise `+RequestWalltime` to **3600** in both JDLs (2
jobs × 1 h = 2 GPU-h ≤ 10; one at a time), and/or lower the curl `--max-time` to ~1200 s so the script always
finishes and records inside the walltime; record a walltime hold if it still happens, and do not retry blindly
(the pull is repeated per job).

### MINOR

**m1 — six outputs are listed but only five are pre-created.** JDL L8 lists `i3_download.log`; the script's
pre-created list (L13) omits it (it is only created by the curl redirection at L27). An early abort before the
download would make the missing file a transfer-output error — the S4-B1 pattern (job held for a missing output
instead of showing the real failure). *Fix:* add `i3_download.log` to the `pre=` list (the Lead's "7 outputs, all
pre-created" is not what the files currently say: 6 listed, 5 pre-created).
**m2 — the TOpAS docker pull and GPU injection are unproven.** The digest is a public ghcr package (anonymous
registry verification succeeded), so an anonymous `docker pull` should work, but the TOpAS daemon's egress and
the nvidia-container runtime are not exercised by any earlier job (S2T used container universe). Expected
failure: an image-pull hold (code 35 family) or a container without `/dev/nvidia*`. *Fix:* record the dry-run
`DockerImage`/`HasDocker`/requests; if the pull or GPU injection fails, record verbatim and put the
container-universe fallback in the question list (do not switch silently). The docker-universe match gate is
`TARGET.HasDocker`; `HasDockerURL` is not synthesized for docker universe (both were measured true on TOpAS
anyway).
**m3 — `curl` in the gpu image is unverified.** See §2.2: the Dockerfile relies on the base's `curl-minimal` for
`curl` in the final stages and neither the image verification nor S5 exercised it. *Fix:* one read-only check
(`apptainer exec <gpu SIF> command -v curl sha256sum stat seq`, record) and add a preflight
`command -v curl >/dev/null || { echo "NO_CURL"; FAIL=1; }` to `i3_run.sh`, so a missing tool is a clean recorded
failure; if absent, the I3 unit cannot run as written and needs an image fix or a different downloader.
**m4 — no pre-download free-space check.** `df -h .` is recorded (L23) but not gated; with M1 fixed, add
`avail_kb >= EXPECT_BYTES/1024 + 2 GiB` before the download and FAIL cleanly (record avail vs needed).
**m5 — dry-run ads are written to `/tmp` on the submit host and not committed.** *Fix:* copy the ads into the
repo (like the S4/S5 dryrun records) and check: NEMO2 — `JobUniverse=5`, `WantContainer=true`,
`ContainerImage=docker://…@sha256:69b0…`, `ContainerImageSource=docker`, requirements
`HasContainer && HasDockerURL`, `RequestGPUs=1`, `RemoteJob=true`, `RequestDisk`; TOpAS — `JobUniverse=5`,
`WantDocker=true`, `DockerImage=ghcr.io/…@sha256:69b0…`, requirements `HasDocker`, `RequestGPUs=1`,
`RemoteJob=true`. Commit them with the submission note.
**m6 — no "one at a time / NEMO2 first" guard and no queue check for the other I3 job.** The wrapper submits
whichever target it is given; the operator must run NEMO2 first, inspect the result, then run TOpAS once. *Fix:*
record the queue snapshot before each submit and add a cheap guard (`condor_q dwong -af Cmd | grep -c i3_run`
must be 0) so the two GPU jobs cannot overlap.
**m7 — V100S/torch architecture note.** llama.cpp is built for arch 70 ✓; the job records torch's version and
CUDA line, which will show whether the cu124 wheel has a V100 kernel. A torch "no kernel image" note is a stack
compatibility observation, not an I3 failure (llama-server is the primary test); record it either way.
**m8 — the TOpAS `ProvidesEtpCeph` measurement is only in the report text.** The chain report L125 records
18×A100 / 13×V100S all `ProvidesEtpCeph=true`/`HasDocker=true`, but no raw capture is committed (unlike the S1/S2
raw files). *Fix:* commit the read-only `condor_status` capture behind L125 (or record "measured, raw kept on
the cluster") for the report.
**m9 — server stop is SIGTERM + wait only (no fallback).** The container/procd teardown covers a kill, but if the
server ignored SIGTERM an orphan could persist briefly inside the job. *Fix:* add `kill -9` after a short wait,
or a `trap` that kills the server on exit (NIT-level; no real risk).

### NIT

**n1** — record `i3_download.log`/`llama-server.log` sizes in the evidence (avoid transferring a large curl
progress log if HF chatters).
**n2** — `HEAD -c 400` of `/v1/models` is enough to prove serving; keep it.
**n3** — the model file is correctly excluded from the transfer list; keep it excluded.
**n4** — the S5 lesson (no `nvidia-smi` gate) is applied: I3's gate is download+sha+health, and the GPU
diagnostics are recorded rather than gated. ✓
**n5** — record the exact submit command, cluster ids, submit/execute/end UTC and the wait/run split for both
jobs; the download time comes from `i3_download.txt`, the pull time from `run_s` minus the script's own start
(the NEMO2 pull is inside `run_s`; the TOpAS docker pull likewise).

---

## 4. Verdict, submission order, preconditions and record set

**The unit is close and the design is right** (immutable HF pin verified independently; the same gpu image that
already ran llama-server on a real L40S; a timed download with byte+sha gates; a bounded server test with
CUDA/offload capture and no nvidia-smi artefact), **but two MAJOR fixes are needed before submission:** the
NEMO2 disk request (M1) and the walltime headroom (M2), plus the one-line pre-creation and curl verification
(m1/m3). After those, no further design review is needed; I can re-check the numbers in a quick pass.

**Expected order and preconditions (once M1/M2/m1/m3 are fixed):**
1. Confirm `curl` (and coreutils) in the gpu image read-only (`apptainer exec <gpu SIF>`), and run the HF pin
   check is already verified (above); record.
2. NEMO2 first: fresh GPU snapshot (`gpu_availability.sh`, append-only; the 01:41 snapshot had L40S 7 idle/10 —
   pick model with idle slots and record the reason), dry-run ad (commit it), queue snapshot, submission note
   (image digest + model pin + reason), then submit **NEMO2** alone.
3. Inspect the NEMO2 result before TOpAS: `i3_PASSFAIL.txt`, `i3_download.txt` (download s/bytes), `i3_sha.txt`
   (match=yes), `i3_server.txt` (server_ready, `/v1/models`, CUDA/offload lines), exit code, and the event log
   (`i3.log`, wait/run split with the pull inside `run_s`). If NEMO2 fails on image pull, HF access, disk or
   server load, record it and do **not** submit TOpAS blindly.
4. Then **TOpAS once** (docker universe, V100S): same gates; record whether the docker daemon pulled the ghcr
   digest anonymously (or the pull hold), whether the container got the GPU, and the same run records. Keep 1
   job at a time; total 1.33–2 GPU-h ≤ 10.
5. Record, for both: cluster ids, submit/execute/end UTC, wait/run split (pull inside run), download seconds and
   bytes, sha match, server ready seconds, `/v1/models`, CUDA/offload lines, PASS/FAIL, exit code, site/host/GPU
   and driver; store under `i3/out/` like S4/S5, and commit the dry-run ads + snapshots + submission notes.

**Residual risk I carry:** HF egress/rate limits from the ETP/NEMO2 workers and TOpAS (record 429/404/sha
mismatch; the immutable pin is verified), the TOpAS docker daemon's anonymous pull and nvidia injection, the
V100S torch/cu124 kernel question (llama-server is the primary test), the gpu image's `curl` (unverified),
walltime/disk if the numbers are not fixed, and the repeat of the 4.87 GiB image pull per job (the pull time is
part of `run_s`).

VERDICT: NOT ACCEPTED


---

## Quick re-check — I3 fixes (15 Nov 2026, 10:25–10:35 CET; no full round)

**Scope.** Confirmation of the two MAJORs and the minors, at worktree HEAD **`ea9a9a0f`** with the fixes as
**uncommitted working-tree changes** (the four unit files show as modified; the new raw files are untracked).
The unit hashes match the Lead's new values: `i3_run.sh`
`4cc84f3c6ac3553ead8227957d40be8e90998a68d8060267084426c3823da010`, `i3_nemo2_l40s.jdl`
`fc84425e31e6b29b18351d54afa4f35c3ac16891d5510eee48fc7b518d35ae3a`, `i3_topas_v100s.jdl`
`229634347e1c0d556589fb4bbb806344933d60f2ef9cb12d58298c2f60eab431`, `submit_i3.sh`
`4adf5d70bfe4a8be26824e2d2633f78e83afc81a4e83d5312eaac3881e9abf9a`. **Commit these four files** (the review
binds to these hashes; they are not yet in a commit).

**Verified fixed:**
- **M1** — NEMO2 JDL L15 `request_disk = 25000000` (S5-proven sizing); TOpAS keeps 12,000,000 (docker image in
  the daemon store, only the model in the sandbox). ✓
- **M2** — both JDLs L12 `+RequestWalltime = 3600`; script L29 `curl … --max-time 1200`. 2 jobs × 1 h = 2 GPU-h
  ≤ 10, one at a time. ✓
- **m1** — `pre=` now lists all six outputs including `i3_download.log` (L13), matching the JDL transfer list. ✓
- **m4** — pre-download free-space gate: `AVAIL_KB=$(df -k . | awk 'NR==2{print $4}')`, fails below 12,000,000 kB
  (L26–27). Note it sets FAIL=1 and the download still runs (evidence-first); the message goes to `i3.out` —
  acceptable; an early skip or writing the line into `i3_identity.txt` would be marginally cleaner (NIT).
- **m5/m6** — wrapper now copies the dry-run ad to `dryrun.ad` (L33), keeps the submission note and queue
  snapshot, and refuses to submit while any `i3_run.sh` job is active (L27–30). It does not enforce "NEMO2 first"
  (the guard is one-at-a-time only) — operator order, as planned. ✓
- **m9** — SIGTERM then `kill -9` fallback after 2 s (L56). ✓
- The rest of the script is unchanged and still correct (pinned URL/sha/bytes, byte+sha gates, 240 s `/health`,
  `/v1/models`, `-ngl 99 -c 2048`, CUDA/offload capture, no nvidia-smi gate, model excluded from the transfer
  list, sandbox-only writes, no credentials). ✓

**Two record defects found in the working tree (record-only; fix before/with the commit):**
1. `raw/topas_etpceph_gpu_slots.txt` (untracked, 222 B) contains **only the OpenSSH post-quantum warning** — no
   `condor_status` rows and no `ProvidesEtpCeph`/`HasDocker` data. The chain-report claim (L125: 18×A100 /
   13×V100S, all `ProvidesEtpCeph=true`, `HasDocker=true`) is therefore not backed by the committed raw.
   *Fix:* re-run the read-only capture with output redirection that keeps the command's stdout (e.g.
   `condor_status -pool c03-001-140.gridka.de -constraint '…' -af Name GPUs_DeviceName ProvidesEtpCeph HasDocker`
   and redirect only stderr away), and commit it.
2. `raw/i3_prechecks.txt` — claimed (curl 7.76.1 inside the gpu image; HF URL 302→200 with
   `content-length: 4683073536`) but **absent from the worktree**. *Fix:* commit the precheck output; it is the
   record for the curl presence and HF reachability checks (m3).
Also, the chain report still says "Reviewer re-check pending" and has no m2/m7 note yet — update it in the same
commit (m2: TOpAS docker pull/injection unproven, record hold code 35 family / missing `/dev/nvidia*`, docker gate
is `HasDocker`; m7: V100S is sm_70 and is in the image's llama.cpp arch list 70;80;89;90, llama is the primary
test).

**Confirmed submit order/preconditions/records (unchanged):** commit the unit + raw records; fresh GPU snapshot
with model reason; dry-run ad committed; queue check (the wrapper's guard); **NEMO2 L40S alone**; inspect
`i3_PASSFAIL`, `i3_download` (seconds/bytes), `i3_sha` (match), `i3_server` (`server_ready_s`, `/v1/models`,
CUDA/offload lines), exit code and the event-log wait/run split (the pull is inside `run_s`); then **TOpAS V100S
once**, recording the docker pull result (or its hold) and the same fields; total 2 GPU-h ≤ 10.

VERDICT: ACCEPTED
