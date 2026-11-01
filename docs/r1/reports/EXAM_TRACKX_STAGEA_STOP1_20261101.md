# Track X Stage A — new attempt STOP 1 (footprint-floor infrastructure defect)

Date: 2026-11-01 ~00:07 UTC (01:07 Europe/Berlin). Batches:
- Stage A run: `/home/dowling/exam-x/work/r1_stagea_20261101_a7c41e`
- Lease evidence: `/home/dowling/exam-x/work/r1_stagea_lease_20261101_a7c41e`
- Checkpoint: `9418d75ef6b78bb1fd2ec90b9c47d72b62acacb4` (clean portal checkout), config
  `paper_commit=82dfaf5`, guardian manifest SHA-256 `e08363d53310ae9737d4231e286bbf00d365e64f7cb208fd7c5db6b4a83c5203`.

## What happened

1. The reviewed guardian acquired the real `~/r1_locks/gpu0.lock` (dev 66306, inode
   120090387) and launched the pinned Stage A runner. The learner anchors
   `random_valid` and `scripted` completed.
2. `qwen25_coder_7b` exact-path qualification PASSED: `footprint_mib: 5784`, full GPU
   offload, route `gpu_memory`, CPU-control speedup 11.673 (`qualification.json`,
   `probe_20261101T000711Z.json`).
3. The dedicated replay server started (pid 2611135, port 56073) with the verified
   inherited lease FD (FD 4, `/proc/.../fd/4 → gpu0.lock`, SAME-OFD kcmp recorded in
   `servers/qwen25_coder_7b/llama_server_56073.json.lease_inheritance`).
4. The runner's post-start offload check measured **5782 MiB** for that new server while
   the qualification footprint pinned earlier was **5784 MiB**. Route (ii) treats a server
   below the pinned footprint as not fully offloaded:
   `"route (ii): server pid 2611135 uses 5782 MiB ... below the pinned footprint 5784 MiB"`;
   `full: false`.
5. The runner raised a mechanical failure while its dedicated server was alive. Stage A's
   STOP rule is to preserve rather than signal it, so the run stopped with
   `PreparationStop: STOP: preserve Stage A server after failure`
   (`batch_state.json` status STOPPED; guardian `STOP.json`).

## Classification

**Infrastructure/tooling STOP.** Not a candidate offload failure and not a parse/candidate
failure: qualification passed and full offload was measured; the defect is that a footprint
measured on one server instance is used as a strict floor for a different instance, and a
2 MiB measurement difference trips it. The fix (reviewed tolerance or a re-measured
replay-server footprint) is not applied here.

## Preserved site (do not clean, signal, retry or resume)

- Guardian pid **2576846** holds the real flock (in `/proc/locks`: FLOCK WRITE on inode
  120090387) and wrote `STOP.json` with `lease_retained: true`, `retry_permitted: false`,
  `completed_release: false`. Its tmux session `r1stagea_a7c41e` remains alive.
- Preserved native server pid **2611135** (llama-server, `qwen25_coder_7b`, ctx 32768)
  retains FD 4 → `gpu0.lock`; a read-only guardian→server `kcmp(KCMP_FILE)` on FD 4
  returned **rc 0**, so the same open file description is retained after the runner
  STOPped. This is the intended retention behaviour directly observed (not a reason to
  retry).
- Runner pid 2576851 exited; the run root and the evidence directory are untouched.
- No signal was sent to any process; nothing was deleted, moved or relabelled.

## Required before any further Stage A attempt

An author decision on resolution (release the retained guardian/server after evidence
review) and a **new independently reviewed** fix of the footprint-floor check; then a
fresh, separately identified new attempt. The STOPped batch must never be resumed, and
this STOP must not be counted as Stage A evidence.
