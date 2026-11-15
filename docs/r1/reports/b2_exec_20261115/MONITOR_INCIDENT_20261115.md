# B2 monitoring incident — TASL-7 unreachable (15 November 2026, ~21:36 CET)

- At 21:34:17 CET the scheduled 21:34 monitor cycle failed: `ssh: connect to host 100.106.74.51 port 22:
  Operation timed out`. Retries at 21:36 CET: `tailscale ping 100.106.74.51` times out (3/3, `no reply`);
  `ping` 100 % loss; `ssh tasl7.etp.kit.edu` also times out. `tailscale status` shows the node `active; relay
  "lax", tx 2496 rx 0` (we transmit, nothing returns) — the Tailscale node is present in the tailnet but the
  host does not answer at L3.
- **What this means for B2.** The B2 `exam_runner b2` runs on TASL-7 independently of the operator session;
  the last confirmed state (21:22 CET) was RUNNING, 21/24 roots, on `gemma4_31b/b2/on/openml_ionosphere__s9012`;
  the runner writes `b2.exit` through `receipt.sh` when it ends. No operator action can be taken while the host
  is unreachable; nothing was stopped, retried or altered from this side.
- **Planned recovery.** Retry reachability every ~10 min. When it returns: resume the ≤30-min monitor cycles,
  then (only after the runner has ended, `b2.exit` present) run the reviewed post-run chain
  (`postrun_collect.sh` → `retire_marker.sh` → `publish_status_done.sh`), then `stop_trks_watch.sh` and the
  TASL-2 read-only inventory (TASL-2 is still offline since 3 d ago; no network). If the host returns with the
  runner already finished, the review gates still require a normal-exit path or the stopped-run unit; no retry
  and no marker/STATUS deletion.
- **TASL-2:** unchanged, tailnet shows `tasl-2… offline, last seen 3d ago`.
