# Track X Stage A — independent receiving review of the executed phase (preflight + STOP 1)

Reviewer: the independent reviewer (not the implementer). Review date/time: 2026-11-01 (Europe/Berlin);
read-only host observations timestamped UTC below. **No process was signalled, no lock was acquired, no
server was started, and the preserved site was not modified.** All host access was `ls`/`cat`/`stat`/
`sha256sum`/`readlink`/`/proc` reads plus a read-only `kcmp(KCMP_FILE)` syscall; the only local write was a
`git fetch` of the pushed coordinator branch to read the docs commit (no worktree change).

**Verdict: `RECEIVING ACCEPT`** — the preflight evidence is accurate and the Stage A STOP is correctly
recorded and correctly preserved; the classification (infrastructure/tooling footprint-floor STOP, not a model
offload failure) and the required resolution gate are correct. **Required documentary corrections** are listed
in §7; they do not require a re-run and do not alter the STOP/preservation.

---

## 1. State under review

| Item | Value (verified) |
|---|---|
| Published code | branch `codex/trackx-stagea-cooperative-20261031`, checkpoint `9418d75ef6b78bb1fd2ec90b9c47d72b62acacb4`, config `paper_commit=82dfaf5` |
| Run checkpoint (portal) | `/home/dowling/exam-x/work/agent_paper_B` at `9418d75`, detached, clean (verified earlier and re-verified via `checkpoint.json` `clean: true`) |
| Preflight | `/home/dowling/exam-x/work/r1_stagea_preflight_20261101_a7c41e` (out) + `.../r1_stagea_preflight_lease_20261101_a7c41e` (guardian/lease evidence) |
| Stage A STOP 1 | `/home/dowling/exam-x/work/r1_stagea_20261101_a7c41e` (out) + `.../r1_stagea_lease_20261101_a7c41e` (guardian/lease evidence) |
| Docs commit | `2b2c82eb2bf7c931c106e43f3d7ec9b4e142473e` on `codex/coordinator-20261031` (pushed to origin; fetched read-only) |
| Preserved lock | `/home/dowling/r1_locks/gpu0.lock`, dev 66306, inode 120090387, nlink 1, size 0 |

---

## 2. Preflight evidence — verified

Read-only files in the two preflight directories. Key checks:

| Check | Observed (file) |
|---|---|
| Guardian / runner / native server | 2565994 / 2565998 / 2566067 (`start.json`, `runner.json`, `preflight.json`) |
| Lock identity | `/home/dowling/r1_locks/gpu0.lock`, dev 66306, inode 120090387, uid 1008, nlink 1 (`start.json`) |
| Guardian→runner `kcmp(KCMP_FILE)` | **rc 0**, `kcmp_same_ofd: true`, FD 4 (`lease_inheritance.json`) |
| Runner→native server `kcmp(KCMP_FILE)` | **rc 0**, FD 4 (`preflight.json`; and the server record's `lease_inheritance`) |
| FD dev/ino + exact set | server `dev/ino = 66306/120090387`, `server_lease_fds: [4]`, `fd_set_exact: true`, `server_ppid = 2565998` (runner), `server_start_ticks = 450105325` |
| Native server record | `server/llama_server_44043.json`: pid 2566067, start ticks 450105325, argv/ctx 32768/model `qwen25_coder_7b` GGUF, `lease_inheritance.kcmp_rc 0`, `fd_set_exact true`, `stopped_utc 2026-11-01T00:02:18Z` |
| Generation requests | `preflight.json`: `chat_completion_requests_issued: 0`, `generation_requests_issued: 0`; the frozen fixture code issues only `/health`, `/v1/models`, `/props`; the server log contains no chat/completion line (it logs no request lines at verbosity 3, so this is code+journal evidence, not packet capture) |
| Completion/release | `lease_completion.json` with `record_path` + digest; guardian `lease_release.json`: `released: true`, `reason: validated_completion`, `records_verified: 1`, `record_files` = the server record, `lock_file_modified: false`, `lock_file_deleted: false` |
| Batch-state binding | `batch_state_sha256 73b519f4…` == `sha256(batch_state.json)`; `batch_state` COMPLETE |
| Release completion hash | `lease_release.json` `completion_sha256 ffe3c83b…` == `sha256(lease_completion.json)` |
| Checkpoint / accepted pins | `checkpoint.json`: `checkpoint 9418d75…`, `clean true`; config `dfe694a4…` and launcher `df988cc2…` match the accepted C4 hashes (`expected_match true`); guardian `ebdfcf40…`, exam_runner `e7cf4f5e…`, runtime `c32bc8d1…`, cooperative_lease `989d4f1b…`, cache_runtime `12b56012…` match the ACCEPTed v3/C4 set |
| Manifest | `manifest.json` SHA-256 `b8964592c2ed4b72db35b276a14b3f93fd3ee0ed39f180d6e97aec831bfb2589`, 186 files, `argv[0]` = venv python, `argv[1]` = preflight fixture, `AR_HARNESS_ROOT=/home/dowling/exam-x/work/autoresearch_harness`; the pinned hashes for config/launcher/guardian/exam_runner/runtime/cooperative_lease/cache_runtime match the accepted set |
| Lock after the preflight | the release evidence and the later Stage A guardian acquisition (00:03:26) show the lock was free between 00:02:19 and 00:03:26; the lock file inode/nlink/size are unchanged. The current holder is the Stage A guardian (§4), not the preflight |
| GPU after stop | `preflight_after.json`: `stopped: true`, used 436 MiB, free 23747 MiB; utilisation 43% in that point sample (0% in the pre-run sample) |

Recorded evidence hashes (SHA-256): preflight lease `start.json 4829126e…`, `runner.json d6eac64f…`,
`lease_inheritance.json 755a4135…`, `lease_completion.json ffe3c83b…`, `lease_release.json 4477aa33…`,
`checkpoint.json 8cd0feaa…`, `manifest.json b8964592…`; preflight out `preflight.json a640d0f6…`,
`preflight_after.json 59cdab6a…`, `preflight_completion_path.json 272fec13…`, `batch_state.json 73b519f4…`,
`server/llama_server_44043.json 1589298b…`; environment file
`r1_stagea_preflight_20261101_a7c41e_env.json c1eb91ea…` (venv python 3.13.4, transformers 5.20.2,
jinja2 3.1.6, tokenizers 0.23.3, numpy 2.4.4, scipy 1.17.1, PyYAML 6.0.3, `cwd_import_ok true`).

**Preflight conclusion: PASSED as claimed.** Both FD/OFD edges are kcmp-proved (ancestor→descendant, RC 0),
the native server retained FD 4/dev-ino and the exact FD set, no generation request was issued, and the lock
was released only through the validated-completion contract with one covered record.

---

## 3. Stage A STOP 1 evidence — verified

| Check | Observed |
|---|---|
| Batch state | `batch_state.json` `status: STOPPED`, `stop_reason: "PreparationStop: STOP: preserve Stage A server after failure"`; `gpu_lease_after_stop: "NOT_CHECKABLE: runner marker is not evidence of held flock"`; `in_progress` = the qualification dir/pid; `server_intervals` has one open interval (start, end null) |
| Offload rejection | `servers/qwen25_coder_7b/exam_offload.json`: `full: false`, `route: null`, `line: "absent"`; reasons: no offload line in the server log, and `"route (ii): server pid 2611135 uses 5782 MiB … below the pinned footprint 5784 MiB"`; `gpu_memory.used_mib 5782`, `footprint_mib 5784`, `compute_apps_read true` |
| Qualification | `qualification.json`: `status: PASS`, `footprint_mib: 5784`, `offload_route: gpu_memory`, `model_sha256 509287f7…`, `context 32768`, `raw_probe_sha256 b7ac7d63…` |
| Raw probe | `probe_20261101T000711Z.json`: `verdict FULL_GPU_OFFLOAD`, `route gpu_memory`, `footprint_mib_to_pin 5784`, offload `full: true` (line absent), `cpu_control.speedup 11.673`, `passed true`, `stop_reasons []`; `min_gpu_mib 4020`; `exam_stage_a true` |
| Preserved server record | `servers/qwen25_coder_7b/llama_server_56073.json`: pid **2611135**, start ticks 450136451, ppid 2576851 (runner), ctx 32768, `qwen25_coder_7b`, `lease_inheritance`: FD 4, dev/ino 66306/120090387, `server_lease_fds [4]`, `fd_set_exact true`, **`kcmp_rc 0`**, `kcmp_same_ofd true`; `healthy_utc 2026-11-01T00:07:29Z` |
| Preserved lease row | `servers/qwen25_coder_7b/lease_inheritance.json` matches the record's row |
| Guardian STOP | `r1_stagea_lease_20261101_a7c41e/STOP.json`: `status STOP`, `lease_retained: true`, `retry_permitted: false`, `completed_release: false`, reason `"STOP: runner ended rc=1; descendants/completion not proven"`, dev/inode 66306/120090387, guardian pid 2576846 |
| Guardian/runner leases | Stage A `start.json`: guardian 2576846, lease FD 4, dev/ino, manifest `e08363d5…`; `lease_inheritance.json`: guardian→runner kcmp **rc 0**; `runner.json`: runner 2576851 |
| Anchors | `random_valid` and `scripted` `stage_a.json` present, `passed true`, `software_anchor true`, `prompts 0` (partial progress inside the STOPped batch; **not** Stage A table evidence) |
| Stage A request/cache evidence | **None produced**: no `d3_true_calls.jsonl`, `d3_false_calls.jsonl`, `d3_non_generation_calls.jsonl`, `stage_a.json`, or Stage A table under `qwen25_coder_7b/stage-a/32768/` (only `qualification/`). The STOP occurred in the post-start offload check, before `run_stage_a`; only the qualification probe's own `cache_prompt:false` calls were journaled (`d3_qualification_gpu.jsonl` 10 lines, `d3_qualification_cpu.jsonl` 5 lines) |

Recorded evidence hashes (SHA-256): Stage A lease `start.json 2074b8c9…`, `runner.json ef38e9ef…`,
`lease_inheritance.json a9fd480a…`, `STOP.json 2d38fece…`; Stage A out `batch_state.json aa2e953b…`,
`qwen25_coder_7b_occupancy_before.json d1161aba…`, `exam_offload.json c4d58b6a…`, server `lease_inheritance.json
c38034cb…`, `llama_server_56073.json 41fc7d81…`, `qualification.json bce060df…`, probe `b7ac7d63…`; Stage A
manifest `e08363d53310ae9737d4231e286bbf00d365e64f7cb208fd7c5db6b4a83c5203` (186 files, `argv[0]` venv,
`argv[1]` exam_runner).

Two independent corroborations that 5782 is the real per-instance footprint of this model/host: the independent
preflight loaded the **same** `qwen25_coder_7b` GGUF and its `compute_apps_after_load` also reported
`used_mib: 5782`; the qualification reported 5784. The 2 MiB delta is per-instance measurement variance.

---

## 4. Preservation — verified read-only

Observed at **2026-11-01T00:17:14Z / 00:19:18Z** (UTC), kernel `6.8.0-136-generic`:

- Guardian pid **2576846** alive (`/proc/2576846/stat` state `S`); native server pid **2611135** alive
  (`llama-server`, state `S`).
- `/proc/2576846/fd/4` → `/home/dowling/r1_locks/gpu0.lock`; `/proc/2611135/fd/4` → `/home/dowling/r1_locks/gpu0.lock`;
  a scan of each process's fd table shows **fd 4 is the only descriptor pointing at gpu0.lock** in each.
- `/proc/locks` contains exactly one line for the lock inode:
  `FLOCK ADVISORY WRITE 2576846 103:02:120090387 0 EOF` — the preserved guardian holds the flock.
- Read-only `kcmp(KCMP_FILE)` from an unrelated same-UID process (my review process, pid 2701422) on FD 4:
  `kcmp(server 2611135, guardian 2576846, 4, 4) = rc 0`, `kcmp(guardian, server, 4, 4) = rc 0`,
  `kcmp(server, server, 4, 4) = rc 0`; negative controls `kcmp(server, guardian, 3, 3) = rc 2` and
  `kcmp(server, guardian, 4, 3) = rc 2`. So the guardian and the preserved native server share the same open
  file description on FD 4 after the runner exited. (The kcmp call is read-only; no signal, no lock operation.)
- Runner pid 2576851 is absent (`/proc/2576851` missing) — the runner exited, as reported; the guardian
  retained the lease because the runner ended rc=1 without a valid completion.
- `find <run root> -newer <STOP.json>` returns nothing — no retry/resume/cleanup marker was created after the
  STOP; `STOP.json` `retry_permitted: false`, `completed_release: false`.
- The stopped namespace fixture `/tmp/d3_namespace_fixture_20261031_d61db5e9b02188f7` is unchanged:
  `mtime = ctime = 1793446875`, mode 700; I did not enter or touch it.
- `gpu0.lock` metadata unchanged (dev 66306, inode 120090387, nlink 1, size 0); I did not open, flock, or
  signal it or any process.

**Preservation conclusion: correct.** The guardian retains the real flock, the preserved native server retains
the same FD/OFD, the runner exited, nothing was signalled/cleaned/retried, and the STOP is recorded with
`retry_permitted: false`.

---

## 5. Classification and required resolution gate — assessment

**Classification "infrastructure/tooling STOP, not a model offload failure": correct, with one precision.**
The model was loaded on the GPU (replay-server `used_mib 5782`, same model/host measured 5782 in the
independent preflight and 5784 in the qualification; no CPU-fallback line; server healthy). The pinned build
prints **no** `offloaded N/N layers` line, so route (ii) (used-MiB on the pinned GPU vs a pinned footprint) is
the only available offload proof. The replay server's 5782 is 2 MiB below the 5784 floor, so the check could
**not establish** full offload and the runner correctly STOPped and preserved the server. That is a
conservative, correct action under the gate; it is **not** evidence that the model failed to offload. The
report should say "the route-(ii) check could not confirm full offload for the replay server; the measured
footprint is consistent with full offload; the 2 MiB delta is per-instance measurement variance" rather than
"full offload was measured" (the qualification measured it on its own instance, not the replay server).

**Required before any further Stage A attempt — the stated gate is right.** An author decision on resolution,
a newly independently reviewed footprint-floor fix, and a fresh separately identified attempt; the STOPped
batch must never be resumed and this STOP must not be counted as Stage A evidence. Resolution options the
author should weigh:

1. **Reviewed tolerance** in route (ii): accept `used_mib >= footprint_mib - tolerance`, with the tolerance
   justified by measured per-instance variance (the preflight's same-model 5782 vs the qualification's 5784 is
   one data point). This changes the offload-acceptance semantics and must remain conservative (a tolerance
   large enough to accept a genuinely non-offloaded server would be a defect).
2. **Re-measured / steady-state footprint**: settle after load and take multiple `nvidia-smi` samples (median /
   min) and pin the footprint with an explicit documented margin; or improve the qualification probe's
   measurement so the pinned floor reflects the same sampling regime as the check.
3. **Stronger offload proof**: use route (i) (the `offloaded N/N` log line) if a build that prints it can be
   pinned/reviewed; this is a heavier build change and is not recommended for a quick retry.
4. **Accept the STOP as inconclusive** and redesign the offload-evidence method before another attempt.

**What must not be done (for the author's decision):**

- Do not resume, retry, or reuse the STOPped batch (including its `random_valid`/`scripted` anchors and the
  qwen25 qualification/server); do not re-label the STOP as a model failure or as Stage A evidence.
- Do not signal, kill, clean, move, or relabel the preserved guardian (2576846) or native server (2611135);
  do not release/acquire the lock manually; do not reuse the preserved server or its port 56073.
- The guardian and the preserved server share **one open file description** for the lock (`kcmp` rc 0). Ending
  the guardian alone will not release the flock while the server still holds FD 4; freeing the lock for a new
  attempt requires the author's decision to end **both** preserved processes after evidence review, recorded
  as an authorized action — not a silent cleanup.
- Do not edit the evidence; do not run B1/B2 (remain STOP); P.3a and B.2 remain STOP; do not touch the stopped
  namespace fixture.
- Preserve the preflight and STOP evidence directories (temporary `/home/dowling/exam-x/work/` artefacts, not
  repo content); the hashes in §2–§3 are the record.

---

## 6. Docs at `2b2c82e` — verified, with misstatements

Fetched read-only from origin (the commit was not in the local clone until fetch):

- `docs/r1/reports/EXAM_D3_COOPERATIVE_LEASEGUARD_20261101.md` (11326 bytes, SHA-256
  `26b59fd448e8903beeb60994208e0def80ecb683883d5bfe60ae2da89cf9ffd2`)
- `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP1_20261101.md` (3422 bytes, SHA-256
  `0d0a53c43c4c6fd863573d63137351c7875d2fd1c9572159465276776cc55554`)
- `docs/r1/reviews/TRACKX_STAGEA_COOPERATIVE_REVIEW_20261101.md` (63680 bytes, SHA-256
  **`8b7a5765c7ca9a4c6b09022e962314515d0821e82f831a306983081b19ab5135`** — **exactly matches** my review,
  copied verbatim ✔)
- The commit adds 5 files (the three docs + `docs/r1/PLAN.md` +1 line + `docs/r1/STATUS.md` +2 lines); the
  STATUS top entry and the PLAN §10 row `R1-EXAM-COOPERATIVE-UID-RUN` are present and their claims (preflight
  passed; 5782 vs 5784 footprint-floor STOP; guardian+server preserved; no Stage A table; author decision +
  newly reviewed footprint fix required) match the portal evidence.

**Misstatements to correct (material in one case):**

1. **`EXAM_D3_COOPERATIVE_LEASEGUARD` §6:** "Real Stage A request/response/cache evidence (cold true-first
   zero-cached and explicit false were exercised only on the preserved attempt up to the STOP, and no Stage A
   table was produced)". The **true-first zero-cached replay did not run**: there is no
   `d3_true_calls.jsonl`/`d3_false_calls.jsonl`/`stage_a.json` under `qwen25_coder_7b/stage-a/32768/` (only
   `qualification/`). The STOP occurred in the post-start offload check before `run_stage_a`; only the
   qualification probe's own `cache_prompt:false` calls were journaled. Correct to: "No Stage A
   request/response/cache evidence was produced; the STOP preceded `run_stage_a`; only the qualification
   probe's own cache_prompt:false calls exist, and they are not Stage A replay evidence." This matters so the
   author does not treat the STOP as containing Stage A cache evidence.
2. **`EXAM_D3_COOPERATIVE_LEASEGUARD` §2:** v2 `SHA256SUMS` abbreviated `5d8b1065…98f9`; the correct value is
   `5d8b1065a32000d7f4c748bfd53f8e0e9cc678c87a87355becb126d4a1a32486` (suffix `…a32486`, not `…98f9`).
3. **`EXAM_D3_COOPERATIVE_LEASEGUARD` §4 table "Lock after | not held (/proc/locks empty for the inode)"**:
   true immediately after the preflight release, but the same inode is now held by the Stage A guardian
   (2576846, FLOCK WRITE) per §5. Clarify "not held immediately after the preflight release; now held by the
   preserved Stage A guardian".
4. **`EXAM_D3_COOPERATIVE_LEASEGUARD` §4 table "GPU after … 436 MiB, 0 % util"**: the after-stop sample in
   `preflight_after.json` is 436 MiB / **43 %** util (the 0 % is the pre-run sample). Clarify the sample.
5. **`EXAM_D3_COOPERATIVE_LEASEGUARD` §5 / `EXAM_TRACKX_STAGEA_STOP1` "tmux session `r1stagea_a7c41e`
   remains alive"**: I did not verify the tmux session (I did not run tmux); the guardian process is alive.
   Mark unverified or drop.
6. **`EXAM_D3_COOPERATIVE_LEASEGUARD` §3 "Host synthetic chain … 16/16 checks"**: reported by the
   implementer; I did not re-run it. It is consistent with the reviewed code/tests but should be marked as
   reported, not independently re-executed in this receiving review.
7. `EXAM_TRACKX_STAGEA_STOP1` step 3 says the guardian→server SAME-OFD kcmp "recorded in
   `servers/qwen25_coder_7b/llama_server_56073.json.lease_inheritance`" — accurate (the record's row has
   `kcmp_rc 0`); no change needed.
8. `EXAM_TRACKX_STAGEA_STOP1` "No signal was sent to any process; nothing was deleted, moved or relabelled" —
   consistent with the observed state (server alive, fd retained, no newer files); the historical act itself
   is not independently observable (see §8).

---

## 7. NOT CHECKABLE in this receiving review

- Same-UID non-interference and host-global single-server exclusivity (author assumption / NOT_CHECKABLE per
  the author decision).
- Continuous observation between samples; the exact GPU state at unsampled instants.
- The historical claim "no signal was sent" and "nothing moved" — the current state is consistent, but the
  actions themselves are not observable post hoc.
- The 16/16 TASL-2 host synthetic chain (reported by the implementer; not re-run here).
- The tmux session claim (not checked; no tmux run).
- Packet-level proof of "zero generation" for the preflight (the reviewed fixture code + journal + absence of
  request lines in the server log are the evidence; the server does not log requests at this verbosity).
- The real Stage A request/response/cache evidence (not produced; see §3).
- Whether the coordinator docs commit is present in the *portal bare* as well as origin (verified on origin;
  the run checkpoint is detached at `9418d75` and does not contain the docs commit — expected, separate branch).
- Any future attempt's behaviour; this review covers only the executed phase.

---

## 8. Final verdict

**`RECEIVING ACCEPT`.** The real-lock preflight evidence is internally consistent and matches the claims:
both FD/OFD edges are kcmp-proved (rc 0) with FD 4 dev/ino and exact FD set, no generation request, one covered
server record, and a validated-completion release. The Stage A STOP is accurately recorded: the qualification
passed with footprint 5784, the replay server measured 5782, route (ii) rejected it by 2 MiB, and the runner
STOPped with `PreparationStop: STOP: preserve Stage A server after failure`. The preservation is correct and
verified read-only: guardian 2576846 holds the real flock (`/proc/locks`), the preserved native server 2611135
retains FD 4/gpu0.lock, read-only `kcmp` between them on FD 4 is rc 0, the runner exited, no retry/resume marker
exists, and the stopped namespace fixture is untouched. The classification (infrastructure/tooling footprint-floor
STOP, not a model offload failure) and the required gate (author decision + newly reviewed footprint-floor fix +
fresh separately reviewed attempt; never resume the STOPped batch; keep the site preserved) are correct.

The **required documentary corrections** in §6 (especially the Stage A-evidence sentence and the v2 hash suffix)
must be made before the author's resolution decision; they do not require a re-run and do not change the
STOP/preservation. The preserved site must not be disturbed; freeing the lock requires an authorized decision to
end **both** the guardian and the server (they share one OFD), after evidence review.

Review file SHA-256 is reported in the reply; the evidence-file hashes above are the record for this phase.
