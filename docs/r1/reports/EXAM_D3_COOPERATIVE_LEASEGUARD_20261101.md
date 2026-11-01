# Track X Stage A — cooperative lease guardian, FD/OFD chain and cold-cache gate

Date: 31 October – 1 November 2026. Author decision: `R1-EXAM-COOPERATIVE-UID`
(`docs/r1/authorizations/TRACKX_SAME_UID_COOPERATIVE_20261031.md`, commit `9c8ff4f`).
**Same-UID non-interference is an AUTHOR ASSUMPTION, not an observed property.**
Host-wide process exclusivity is **NOT CHECKABLE**. Nothing here shows that same-UID
users did not interfere or that only one service existed on the host.

**Status: implementation independently ACCEPTed and published; real-lock preflight with
the real native server PASSED; the new Stage A attempt STOPped on a footprint-floor
infrastructure defect and the site (guardian + flock + preserved native server) was
retained. Stage A evidence was not completed. B1/B2 were not started; P.3a and B.2
remain STOP.**

## 1. Defects repaired in this batch

1. Stage A qualification `MECHANICAL_FAILURE` exited nonzero while the runner treated
   every nonzero exit as STOP, so the legitimate 32k→16k fallback was unreachable; and
   early drafts confused a plain nonzero exit with an offload failure. Now only a PASS
   or a fully recorded CUDA allocation OOM with a healthy idle post-state returns 0, and
   the runner re-validates that evidence before the fallback.
2. Guardian liveness/PID/start-tick and lock inode identity could not show the guardian
   and workers held the same open file description. Now every edge carries explicit
   `pass_fds` inheritance plus `/proc` FD dev/ino, exact FD set, pid/start-ticks/parent
   identity, ancestor→descendant `kcmp(KCMP_FILE)` where a kcmp is used, and
   `flock_relock_while_guardian_live` for the child→guardian edge; errors/EPERM are never
   SAME.
3. The guardian candidate could exit (dropping the flock) when its stdout pipe broke,
   and there was no normal-completion release contract. Now `hold_forever` is
   exception-proof (SIGPIPE/-HUP/-INT/-QUIT/-TERM/-USR1/-USR2/-ALRM ignored, stdout/stderr
   to `/dev/null`, loop swallows `BaseException`) and release requires a validated
   `trackx_lease_completion/v1` whose server entries cover **every** `llama_server_*.json`
   record under the run root (qualification probe, CPU control and replay servers), with
   dead-PID / PID-reuse, record-digest, stop-time and SAME-OFD checks.
4. Cold-cache gate: the dedicated replay service runs the 50 frozen prompts first as
   descriptive cold-true-first (`cache_prompt: true`, first call must report zero cached
   tokens), then every normal Stage A request is explicitly `cache_prompt: false` and is
   rejected by the recorder if a cache hit is reported. Requests, responses (bytes +
   SHA-256), seeds, free/schema mode, cache counts, census snapshots, ordering and errors
   are journaled. Missing/malformed VRAM telemetry is an infrastructure STOP, never a
   model offload failure; unreadable `/proc` entries are recorded gaps.
5. Portal config completed for Stage A (host, approved roots, GPU UUID, frozen prompt
   path + SHA-256, llama.cpp binary SHA-256 + build line, `cache_prompt: false`,
   `d3_policy: author_same_uid_cooperative_20261031`, paper pin). Future-phase values
   remain author-pending placeholders and are not needed by Stage A. A pinned launch tool
   builds the guardian manifest and refuses a dirty/mis-pinned checkout or any existing
   run directory.

## 2. Independent review

Reviewer: a separate independent reviewer subagent (not the implementer, no edits to the
artifact), document `docs/r1/reviews/TRACKX_STAGEA_COOPERATIVE_REVIEW_20261101.md`
(SHA-256 `8b7a5765c7ca9a4c6b09022e962314515d0821e82f831a306983081b19ab5135`).

- First verdict on snapshot v2 (`SHA256SUMS` `5d8b1065…98f9`): **BLOCK** with three real
  defects (Stage A dispatch still hard-stopped; completion record coverage limited to
  `servers/` so a clean run could never release; preflight record outside that tree).
- All three were fixed; re-review of v3 (`SHA256SUMS` `8f033b81…3413d`):
  **ACCEPT with conditions** (bind the paper commit, confirm the harness pin, run the
  real-lock preflight, then Stage A; full Stage A evidence belongs to the receiving
  review).
- The in-repo config cannot equal `HEAD` (self-reference), and the launcher's equality
  check was therefore unsatisfiable; C3 changed it to the runtime's own rule (ancestor +
  no change on the runtime-checked paths). C4 stopped resolving the venv interpreter
  symlink (resolving it would have launched the runner without numpy/scipy/transformers).
  Both deltas were independently confirmed; **ACCEPT remains** (conditions M1–M3).

Accepted code: **`82dfaf5`** (contains the reviewed v3 bytes for all 49 files),
config binding `aa45dd1`, launcher deltas `d61394a` and `9418d75`; branch
`codex/trackx-stagea-cooperative-20261031`, pushed to GitHub origin and the portal bare
repository; portal checkpoint clean at `9418d75`. Reviewer-verified: `82dfaf5` tree ==
accepted v3 `files/`; `82dfaf5..9418d75` changes only `exam_portal.json` and
`trackx_stagea_launch.py`; runtime-checked paths diff is empty; relevant subset on the
final commit **366 passed, 1 skipped**.

## 3. Tests

- Mac CPU tests (no GPU/model): the exam/cache/lease/completion subset above —
  **366 passed, 1 skipped** (the skip is the Linux-only real-`kcmp` test).
- Guardian/preflight/launch unit tests cover the BrokenPipe hold, runner rc≠0 hold,
  missing/live/foreign/uncovered completion records, symlinked/outside-root records,
  digest/pid/start mismatch, duplicate rows, release-on-valid-completion (independent
  contender succeeds afterwards, lock inode unchanged), manifest pinning and reserved
  env rejection.
- Host synthetic chain (TASL-2, new `/tmp/trackx_lease_synthetic_20261101_*` roots, new
  synthetic locks, `/bin/sleep` stand-in, no GPU/model/real lock): 16/16 checks, including
  real `kcmp` rc 0 in both ancestor→descendant edges and broken-stdout hold.
- Kernel note: on TASL-2 (6.8.0-136, Yama `ptrace_scope=1`) a descendant→ancestor
  `kcmp(KCMP_FILE)` READ was observed to return 0; no edge relies on that direction and
  errors are never SAME.

## 4. Real-lock preflight with the real native server (PASSED)

Run at checkpoint `9418d75` from a clean portal checkout, manifest built by the reviewed
launcher (`manifest_sha256` `b8964592c2ed4b72db35b276a14b3f93fd3ee0ed39f180d6e97aec831bfb2589`,
186 pinned files), under the reviewed guardian with the **real** `~/r1_locks/gpu0.lock`.
It loaded the real pinned llama-server with the real `qwen25_coder_7b` GGUF at ctx 32768,
issued **no** chat-completion/generation request, proved FD/OFD retention, stopped the
server and released the lock through the validated completion contract.

| Item | Observed |
|---|---|
| Guardian / runner / native server PIDs | 2565994 / 2565998 / 2566067 |
| Lock file | `/home/dowling/r1_locks/gpu0.lock`, dev 66306, inode 120090387, uid 1008 |
| Guardian→runner `kcmp(KCMP_FILE)` | rc 0 (`kcmp_same_ofd` true), FD 4 |
| Runner→native server `kcmp(KCMP_FILE)` | rc 0, FD 4, `/proc/2566067/fd/4` dev/ino equal |
| Native server FD set | `[4]`, exact; ppid = runner pid; start ticks recorded |
| Generation requests | 0 |
| Release | `released: true`, `reason: validated_completion`, `records_verified: 1` |
| Lock after | not held (`/proc/locks` empty for the inode), inode/size/nlink unchanged |
| GPU after | back to the pre-run desktop footprint (436 MiB, 0 % util) |

Interpreter/environment (condition M3) recorded in
`r1_stagea_preflight_20261101_a7c41e_env.json`; the preflight evidence directory also holds
`checkpoint.json` (M1: checkpoint hash, accepted config/launcher hashes matched, manifest
hash) and the manifest JSON. These are temporary-directory artefacts, not repository
content; their hashes are recorded on the portal under `/home/dowling/exam-x/work/`.

This proves the claimed chain for the **native server** under the real lock: the server
retains the same open file description as the lock holder, and the lock is released only
through the validated completion contract.

## 5. New Stage A attempt — STOP 1 (infrastructure/tooling; site preserved)

Launched at the same checkpoint via the reviewed launcher
(`manifest_sha256` `e08363d5…c5203`) under the guardian with the real flock, new output
`/home/dowling/exam-x/work/r1_stagea_20261101_a7c41e` and new evidence
`/home/dowling/exam-x/work/r1_stagea_lease_20261101_a7c41e`.

- Anchors `random_valid` and `scripted` completed.
- `qwen25_coder_7b`: independent exact-path qualification **PASSED** (`status: PASS`,
  `footprint_mib: 5784`, full GPU offload, route `gpu_memory`, CPU-control speedup 11.673).
- The dedicated replay server then started (pid 2611135) and the runner's post-start
  offload check measured **5782 MiB** used on the GPU — **2 MiB below the 5784 MiB
  footprint pinned by the qualification** — so route (ii) reported
  `below the pinned footprint 5784 MiB`, `full: false`.
- The runner raised a mechanical failure while its dedicated server was alive; the Stage A
  STOP rule preserved the server instead of signalling it: stop reason
  `PreparationStop: STOP: preserve Stage A server after failure`.

Classification: this is an **infrastructure/tooling STOP**, not a candidate failure and not
a model offload failure. The qualification footprint is measured once on one server
instance and then used as a strict floor for a *different* server instance; a few MiB of
per-process measurement variance (5782 vs 5784) is enough to violate it. Fixing it needs a
reviewed tolerance or a re-measured replay-server footprint; it must not be worked around
silently.

Preserved site (nothing was signalled, cleaned, retried or resumed):
- guardian pid 2576846 holds the real flock (in `/proc/locks`: FLOCK WRITE on inode
  120090387) and has written `STOP.json` (`lease_retained: true`, `retry_permitted: false`,
  `completed_release: false`);
- preserved native server pid 2611135 holds FD 4 → `gpu0.lock`; the guardian→server
  `kcmp(KCMP_FILE)` on that FD returns 0, so the same open file description is retained
  even though the runner STOPped — the intended retention behaviour, directly observed;
- tmux session `r1stagea_a7c41e` (guardian) and the preserved server remain alive for
  review; the run root and evidence directory are untouched.

**No retry or resolution was attempted.** A new attempt requires the author's decision on
recovery (release the retained lock/server after review) and a new independently reviewed
fix of the footprint-floor check; the existing STOPped batch must not be resumed.

## 6. Not claimed / NOT CHECKABLE

Real Stage A request/response/cache evidence (cold true-first zero-cached and explicit
false were exercised only on the preserved attempt up to the STOP, and no Stage A table was
produced); host-global single-server; same-UID non-interference (author assumption);
continuous observation between samples; guardian behaviour under SIGKILL/SIGSTOP/host
crash; fresh `--version` build-line re-read (retained-record corroboration only);
the contents of the stopped namespace fixture (only mtime/ctime and the absence of retry
references were checked); the real GPU state at times not sampled. All values above are
point-in-time observations, not continuous evidence. B1/B2 were not started; P.3a and B.2
remain STOP.
