# Track G G.0 U0 result — deployed / Paper A gate verified (17 November 2026)

**Status: U0 ACCEPTED and verified.** Independent review round 3: `reviews/TRACKG_U0_DEPLOY_REVIEW_R3_20261117.md`
(sha256 `00529912a7a3d4f6afd510807cc1f68713caa07d0ae6f0d5e1c6388329be66f7`, 343 lines; no BLOCKING/
MAJOR; 9 open MINOR doc items). Authority `R1-TRACKG-G0-GO` / `R1-TRACKG-PORT-OWNER`
(`author-d8-confirm-20261117` @ `26177d82`), `R1-ADA-CENSUS`, `R1-TRACKG-G1B-HOST`. ENGINEERING_ONLY; no GPU.

## Pinned items

| Item | Value |
|---|---|
| Acceptance commit | `610fea63` (ops-tasl-20261116) |
| Unit | `proposals/TRACKG_U0_DEPLOY_20261117.md` (rev 3, header fixed after review) |
| Committed config | `r1/scripts/configs/paper_a_status_ada.json` sha256 `c75bf9c35624b4474bd2260bd3e14621f25ce29c7f09bb237f6b49218e566856` |
| Deployed config (Ada) | `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json` = `c75bf9c3…` (2,636 B) |
| Wrapper | `bin/nvidia-smi-live` sha256 `7e0ec81af481b914aeed5cbb0c10040f19cd9a3b624630adfa5d69eabbb6aaf0` (491 B, 755, `set -uo pipefail`); old fail-open copy moved aside to `u0_verify/nvidia-smi-live.stale.20261117T004027Z` (sha `3be54e99…`, not deleted) |
| Gate capture | `reports/trackg_g0_20261117/u0_status_20261117.json` sha256 `6b62dd2aa5bfc2fa99fd10eb7cb0c6e17ecb88b68ba0ddf31e6cd11e22edc79a` (829 B; `utc 2026-11-17T00:40:27Z`) |
| Paper A status script | `r1/scripts/paper_a_status.py` sha256 `6a36d24f…` (from `16185b0b` worktree) |
| Gate timestamps | deploy 00:40:16Z (config) / 00:40:22Z (wrapper); gate run 00:40:27Z; independent re-run 00:43:10Z |
| Harness | `/home/dowling/r1_trackg_20261117/autoresearch_harness` @ `717ad835df32bbe1047d032fb5bb8dde5384a258`, branch `r1-local-trackg-v2-20261114`, clean |
| Paper worktree | `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b` detached `16185b0b`; only ` M r1/scripts/configs/paper_a_status_ada.json`, whose deployed bytes equal the commit blob |
| Paper A checkout/run | branch `paper-a-v4-ada`, HEAD `6b0ac021…`; run dir `results/paper_a/replay_panel_v4/live_20261018T234416Z`; `panel/finalize.json` 1,314 B; `panel/manifest.json` phase main / status COMPLETED / 764 events; console ends 2026-10-21T13:11:35Z "not resuming: the run completed" |
| Disk | 162,443,051,008 B free (~151 GiB) at gate |
| No-GPU evidence | no `dowling` GPU compute PID, no tmux server, no Track G process; no GPU job/lease started in U0 |

## Gate outputs (three checks; all pass)

1. Newest `results/paper_a/replay_panel_v4/live_*` = `…/live_20261018T234416Z` = configured run dir.
2. `pgrep -u $(id -u) -af 'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'`
   from an `ssh host bash -s` heredoc, self-excluded: **empty (rc 1)**. (Naive `ssh "pgrep …"` shows only
   its own `bash -c` line and must not be used.)
3. `paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`: `verdict: clear_finished`,
   `paper_a_live_waiting_for_card: false`, `unidentified_apps: 0`, `compute_apps: 26`,
   `paper_a_processes: []`, rc 0 (full JSON in the capture).

Fail-closed wrapper checks: `nvidia-smi-live --version` rc 255 (same as raw nvidia-smi), old copy rc 0;
config override `/bin/false` → `unknown` ("nvidia-smi failed (rc=1)"); nonexistent binary → `unknown`.

## Residual risks (accepted, record-only)

A future Paper A campaign with a different `live_*` pattern/checkout or renamed module could evade the gate;
a Paper A start after the gate but before launch is TOCTOU; operator mis-exclusion of the pgrep self-line is
possible; filtering all 0-MiB GPU entries is a heuristic (a real process always holds memory >0). Every
later U2 must re-run the three checks immediately before launch and treat any anomaly as a STOP. Known
MINOR doc items (config comment still says repo log 2026-10-17 / "no per-run phase JSON"; config tmux note
still implies coverage; capture embeds path not shas; `u0_verify/` stale draft not README-labelled) are
accepted as non-blocking and recorded here for the next touch.

## What U0 changes

Harness deployed and the Paper-A-first gate is now decidable and fail-closed; U2 may start only when a Mac
port kit exists, and must re-run this gate each time. No GPU work was done in U0.
