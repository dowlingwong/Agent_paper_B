# Unit (revision 2) — Track G G.0 U0 on Ada: deploy harness + verify Paper A gate (17 November 2026)

**Status: proposal for fresh independent review; final verification re-run after acceptance.** Revision 2
answers the round-1 review (`reviews/TRACKG_U0_DEPLOY_REVIEW_20261117.md`, sha `3fb81927…`, not accepted:
BLOCKING-1 the gate could not detect a new waiting Paper A campaign — tmux `paper_a_live` is not a Paper A
v4 signal and a waiting campaign has no GPU process; MAJOR-1 the nvidia-smi wrapper failed open because it
lacked `pipefail`; plus MINORs). Authority: `R1-TRACKG-G0-GO`, `R1-TRACKG-PORT-OWNER`
(`author-d8-confirm-20261117` @ `26177d82`), `R1-ADA-CENSUS`, `R1-TRACKG-G1B-HOST`. G.0 only; no
noise-floor/D21/D28 on Ada. AI-assisted, ENGINEERING_ONLY, no GPU.

## 1. Scope

No-GPU prep unit: (a) deploy the Track G harness `r1-local-trackg-v2-20261114` @ `717ad835` on Ada;
(b) configure `r1/scripts/configs/paper_a_status_ada.json` and verify the Paper-A-first gate is decidable
(`clear_running`/`clear_finished`, `paper_a_live_waiting_for_card` present and false); (c) define and run
the **mandatory pre-launch liveness check** that closes the stale-run-dir false-clear (below). U0 starts
no GPU job and measures nothing.

## 2. The Paper-A gate and its mandatory liveness check (BLOCKING-1 fix)

`paper_a_status.py` alone cannot detect a *new* Paper A v4 campaign that is waiting for a card: the v4
launcher uses `setsid nohup` (no tmux; `paper_a_live` is a placeholder, not a v4 signal), a waiting
campaign has no GPU process, and the configured run dir with its stale `panel/finalize.json` would read
`clear_finished`. Therefore **before every Paper B GPU unit on Ada** (including each U2 unit), after
`paper_a_status.py` returns a clear verdict, the operator must also verify:

1. **Newest live run dir:** `ls -dt results/paper_a/replay_panel_v4/live_*` (under the Paper A checkout) —
   its first entry must equal the configured `run_dir`. A newer `live_*` directory means a new campaign
   exists → the status check is stale → **STOP** (do not launch).
2. **Paper A process scan:** `pgrep -u $(id -u) -af 'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'`
   — excluding the check's own command line (and the SSH shell), it must be **empty**. Any match → STOP.
3. `paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json` must return
   `verdict` in {`clear_running`,`clear_finished`} and `paper_a_live_waiting_for_card` present and false
   with `unidentified_apps: 0`.

All three must pass; U0 records the exact outputs. The same three checks are copied into every later Ada
GPU unit (U2) as a pre-launch gate; a STOP there is a unit STOP, not the night.

## 3. Facts verified read-only (17 Nov 2026, 00:10–00:30Z; re-checked after acceptance)

- Ada `ucrtasl`, `dowling`; **162.5 G free** (≥50); 8× RTX 6000 Ada; no `dowling` GPU compute PID and no
  Track G process at check.
- Harness `/home/dowling/r1_trackg_20261117/autoresearch_harness`: HEAD exactly
  `717ad835df32bbe1047d032fb5bb8dde5384a258`, branch `r1-local-trackg-v2-20261114`, **clean**.
- Paper worktree `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b` detached at `16185b0b`;
  the only dirty path is the intentionally deployed config (` M r1/scripts/configs/paper_a_status_ada.json`),
  which is identical to the committed ops-branch config.
- Paper A checkout `/home/dowling/agent-checkpoint-intervention` on branch `paper-a-v4-ada`, HEAD
  `6b0ac021…` (2026-10-21, "Record completed panel v4 live run and strict receiving outputs"); the v4 live
  run dir `results/paper_a/replay_panel_v4/live_20261018T234416Z`; `panel/finalize.json` and
  `panel/manifest.json` (`phase: main`, `status: COMPLETED`) exist; `console.log` ends 2026-10-21T13:11:35Z
  "not resuming: the run completed". It is the **newest** `live_*` directory.
- `paper_a_status.py` sha256 `6a36d24f…` (from the `16185b0b` worktree); config file sha256
  `c75bf9c35624b4474bd2260bd3e14621f25ce29c7f09bb237f6b49218e566856` (pinned by the commit that carries
  this unit; validate it by the status run — `paper_a_status.py` has no `--check-config` path, and the
  `64073cea…` digest from the TASL-2 Unit B record does not apply here). The deployed Ada copy must equal
  this commit blob; a mismatch is a STOP before the gate run.
- Wrapper `/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live` sha256
  `7e0ec81af481b914aeed5cbb0c10040f19cd9a3b624630adfa5d69eabbb6aaf0`, mode 755: drops only GPU-compute
  entries whose `used_memory` is 0 (stale namespace-hidden contexts that `ps` cannot read), and uses
  `set -uo pipefail` so a failed `nvidia-smi` fails closed (MAJOR-1 fix). Raw query 30 apps / 4
  zero-memory → filtered 26 apps / 0 unidentifiable.
- Verified final gate run (2026-11-17T00:40:27Z, capture `reports/trackg_g0_20261117/u0_status_20261117.json`, sha `6b62dd2a…`):
  `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `unidentified_apps: 0`; newest
  `live_*` == configured run dir; no Paper A process (the check's own SSH/bash line excluded).
- Minor notes: an earlier duplicate draft config exists in `…/u0_verify/paper_a_status_ada.json` (not used;
  the deployed copy is the worktree one); the repo at Ada HEAD shows the 2026-10-21 commit (not 10-17).

## 4. Procedure (after acceptance)

1. Confirm harness HEAD/branch/clean; paper worktree `16185b0b` and its expected ` M` config; config,
   script and wrapper sha256s match the values in §3/commit; disk ≥50 GB; no `dowling` GPU compute PID.
2. Run the **three-check Paper A gate** of §2 and capture each output with SHA256SUMS.
3. **Install step (MAJOR-2 fix):** deploy the exact committed `paper_a_status_ada.json` to
   `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json`,
   verify its sha256 equals the acceptance-commit blob, set the frozen wrapper `7e0ec81a…` at
   `/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live`, move any stale `u0_verify/` wrapper aside (never
   delete), and record the deployed config/wrapper sha256 and the gate-run timestamps in the capture.
4. Record **U0 deployed / Paper A gate verified** with: unit/config/script/wrapper/capture sha256s, the
   deployed-config sha and gate timestamps, the acceptance commit, harness facts, paper worktree/Paper A branch+HEAD+run dir+marker/console line, disk,
   the full verdict JSON, the newest-run-dir and pgrep results, and an explicit no-GPU confirmation.
5. No GPU work; later units (U2) must re-run §2 before each launch.

## 5. STOPs (item STOP, not the night)

Harness HEAD/branch mismatch or dirty; paper worktree/config/script/wrapper sha mismatch; any of the three
Paper A checks not passing; a newer `live_*` or any Paper A/pgrep match; `paper_a_status.py` failing
(including a wrapper failure — it must fail closed); disk <50 GB; any need to touch another user's
files/processes, sudo, or a GPU job in U0. Preserve the capture and record the STOP.

## 6. Must not

No GPU job/lease in U0; no noise-floor/D21/D28 measurement; no T1 sweep; no TASL-7/TASL-2 action; no other
user's files/processes; no deletion; no push to main/exam-x; no model downloads; no change to Paper A's
files.
