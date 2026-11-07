# B1 TASL-7 O2 handover — executable draft, 7 November 2026

AI-assisted (Codex). **Candidate for independent review; not yet a reviewed handover, an actual handover, or permission to launch.** Implements marker creation and retirement primitives in `r1/scripts/b1_o2_marker.py`. This procedure adapts the accepted conditional `B1_TASL7_HANDOVER_20261107.md` and the 7 November prompt §§0.3–0.5 to the author's later answers in `AUTHOR_B1_EVENING_REPLY_20261107.md`: harness `a3fedbb`, no cgroup/supervisor/freezer/receipt-durability requirement, protect remote files and other tracks, preserve evidence at STOP. The author permitted an approved-note candidate before real gate and preflight, subject to all final launch conditions. The later answer “你继续执行，不用管他。只要能跑就去跑” supersedes earlier blanket non-access if unrelated agents are present, but gives no permission to preempt or alter their processes or evidence. The old handover's author-order clarification and ownership objections are accordingly historical, not current stand-alone STOPs.

## Preconditions and read-only site checks

The operator first reads `~/r1_locks` and full current STATUS for Track X/S/P; inspect hostname, actual GPU UUID and compute applications, disk capacity, and active watcher/collectors/server and P.3a state. Preserve output in a new B1-owned dated record and never print secrets. The historical GPU UUID is `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; recheck rather than treating historical observations as current. Verify the clean committed exact HEAD, accepted combined review, committed note and real author gate, pinned harness and model/build/table/Q2 hashes, worker Python binding, real-worker determinism, Stage A recovery coverage, full-suite disposition, lease and inherited server descriptor, and reviewed host preflight. The separate updated operator message must be reviewed at that final HEAD. No command here waives any phase gate.

Check the running watcher and actual behavior. The 00:15 UTC historical file `trks-watch` SHA `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112` would `touch` STOP beside every `manifest.json` under `/home/dowling/r1_tracks/out`, and may force-stop `trks_llm` after one hour even if collectors remain; a file hash does not prove running code. Before creating a marker, determine whether that watcher is active and what it will touch, inspect all reachable manifest parents and STOP entries (including nonregular entries), and identify the exact Track S server/session and active collectors. The author explicitly directs the Track S watcher to perform its ordinary handover. Its ordinary append to its own watcher log and its STOP-file touches are expected effects and do not themselves violate the no-deletion amendment; inventory and report their actual effects, and preserve bytes and existing evidence. Do not allow a forced stop of a running collector, or an unexpected effect outside that directed watcher handover. If that cannot be established, STOP with scene unchanged; a simple process census is a snapshot, not proof of no future starts. Cooperate with the existing Track S/P operators or an already-established, attributable site mechanism to keep new starts from racing the handover. Do not stop any other operator's process.

Record whether P.3a is absent, already stopped, or running. If running, wait for its owner/process to reach a documented safe point and pause without killing it; do not guess a checkpoint, send signals, or alter its files. Maintain its pause while B1 runs. If safe point or coordination is unavailable, wait; no new author decision is invented. Identify how the previously active Track S/P state can later be restored without deleting or altering other tracks' evidence. If this cannot be established, do not create the marker. This draft supplies no P.3a pause or restart command because none has been established from the available sources.

## Marker and STATUS operation

O2 step 1 and PLAN R1-PORTAL-SCHEDULE require **pushing** the heading `## <date> — Track X B1 running`; `PORTAL_TRACK_P_RUNBOOK.md:21` instructs Track P to read `docs/r1/STATUS.md` on `origin/main`. A local or feature-branch STATUS is not evidence that this publication requirement has been met, even though PLAN also identifies the marker as authoritative. This agent must never push `main`; no permitted route to publish the required heading on `origin/main` has been established. **STOP before marker creation until an independently authorized publisher and a concrete, timely publication path are established, or the author explicitly adopts a different visible channel.** After marker creation, that publisher must push the correct heading immediately before proceeding; if publication fails, retain the marker and STOP. Owner: author/publisher; effort: one narrowly scoped status update or decision, timing unknown. Do not interpret the marker alone as substituting for the expressly required STATUS push. The author may perform their own update; the agent may not push main.

After that publication path and every other condition above are established, and the exact commands are independently reviewed, the site operator uses a new dedicated B1 handover directory and a separate owned local receipt STATUS file, **not the clean executable checkout's tracked STATUS**. This local append is operational evidence only and does not replace the pushed STATUS heading. Set `CHECKOUT` to the exact reviewed clean checkout and `STATUS` to the existing B1-owned local receipt STATUS file; its parent chain must be the intended non-symlink path. `RUN_ID` is a fresh unique identifier, containing letters, digits, underscore or hyphen. `RUN_DIR` is an absent path under the operator's own handover area. Then on TASL-7:

```bash
set -eu
umask 077
mkdir "$RUN_DIR"
HEAD=$(git -C "$CHECKOUT" rev-parse HEAD)
test -z "$(git -C "$CHECKOUT" status --porcelain)"
set -C
python3 "$CHECKOUT/r1/scripts/b1_o2_marker.py" create \
  --lock-dir "$HOME/r1_locks" --status "$STATUS" --run-id "$RUN_ID" --head "$HEAD" \
  > "$RUN_DIR/marker-receipt.json"
```

The primitive exclusively creates the marker and appends a running STATUS; an existing marker is never overwritten. The returned JSON binds its run id, checkout, device/inode and content hash. This primitive **does not verify the scientific gates or watcher safety**: the preceding checks are mandatory. A failed write or lost/empty receipt is STOP: preserve the partial marker, STATUS and receipt, report, and do not rerun automatically. This is a retained identity record, not an fsync or durable-receipt guarantee. Reviewers must test append/partial-failure and adversarial symlink/collision behavior within the cooperative site scope before acceptance.

After creation, observe the actual watcher, the STOP file effects, server shutdown and GPU/lease state. Proceed only after the intended safe pause is confirmed, P.3a is safely paused or absent, no unrelated compute is preempted, and the actual B1 launch conditions still hold. A forced watcher action, an unexpected touched path, a lost identity, or any gate failure is STOP and report. Keep the marker until verified normal completion; monitor and record progress at least every 30 minutes per operator v3.

## Normal completion versus STOP

On verified normal B1 completion, release the B1 lease, then retire **only this run's** marker while preserving bytes, using its receipt:

```bash
set -eu
set -C
python3 "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire \
  --lock-dir "$HOME/r1_locks" --receipt "$RUN_DIR/marker-receipt.json" \
  > "$RUN_DIR/marker-retirement.json"
```

The helper checks marker identity/hash and uses Linux `renameat2(RENAME_NOREPLACE)` into `~/r1_locks/_to_delete/`; failure retains the scene and is STOP. The operator must verify actual site filesystem support before relying on this operation. The checks assume cooperative processes; they do not provide malicious same-UID protection. Preserve every pre-existing STOP and all other-track evidence; any restoration operation involving STOP files must be performed only under the separately reviewed no-deletion Track S procedure and only within its explicit authority. Observe the watcher marker-gone transition, then restore prior Track S/P operation only using their independently reviewed no-deletion procedure; if unavailable, preserve state and report the blocker. Run the complete-batch verifier and publish B1 manifest and verifier result only after normal completion and restoration as instructed.

On any abnormal STOP, stop starting new work; use the B1 runner's reviewed owned-worker and B1 server stop paths, publish STATUS and report shutdown log/record lines. Preserve marker, logs, outputs and ledgers; no automatic retry, pin change, marker retirement or restoration. Report any unsuccessful shutdown rather than claiming completion. No B2, X.7 or sweep 2 is authorized.

## Open items before actual use

1. **Executable draft review**: independent reviewer checks code, tests, exact marker/STATUS boundaries, failures, and cleanup (local engineering/review; short once available). This draft supplies no acceptance.
2. **Site facts and P.3a safe point**: authorized operator reads current watcher, process/lease/marker/STOP and P.3a state and establishes an attributable cooperative pause/restoration, with Track S/P operators if needed (site-dependent; time unknown). If no way exists, wait and report; no unrelated process or data may be modified.
3. **Visible running STATUS**: the author or authorized publisher must establish the required origin/main heading, or the author must explicitly adopt another visible channel; this agent cannot push main. Estimated effort is one small publication or decision; response timing is unknown.
4. **Linux rename and complete launch gates**: independently reviewed site check of no-replace rename and actual filesystem, plus exact-head, tests, real gate and host preflight (implementer/reviewer/operator; effort depends on outstanding results). The existing historical probe is narrow and cannot establish the current final checkout or held lease.
