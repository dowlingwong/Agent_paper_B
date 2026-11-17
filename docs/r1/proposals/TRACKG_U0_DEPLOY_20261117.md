# Unit — Track G G.0 U0 on Ada: deploy harness + verify Paper A status (17 November 2026)

**Status: proposal for fresh independent review; the read-only reconnaissance below is done, the final
verification is re-run after acceptance.** Authority: `R1-TRACKG-G0-GO` and `R1-TRACKG-PORT-OWNER`
(branch `author-d8-confirm-20261117` @ `26177d82`), `R1-ADA-CENSUS`, `R1-TRACKG-G1B-HOST`; G.0 scope only
(no noise floor / D21 / D28 on Ada; those are G.1b on L40S). AI-assisted, ENGINEERING_ONLY.

## 1. Scope

U0 is a no-GPU prep unit: (a) deploy the Track G harness `r1-local-trackg-v2-20261114` @ `717ad835` on
Ada; (b) configure and verify `r1/scripts/configs/paper_a_status_ada.json` so the Paper-A-first gate is
decidable (it must return `clear_running`/`clear_finished`, i.e. `paper_a_live_waiting_for_card` present
and false; otherwise the item STOPs). U0 does not start any GPU job, does not touch another user's process
or files, and does not measure anything.

## 2. Read-only reconnaissance already done (17 Nov 2026, 00:10–00:15Z)

- Ada `ucrtasl`: disk `/` 152 G free (91% used; our U0 deployment is small; later units stay ≤100 GB of our
  own use); 8× RTX 6000 Ada; other users' Ray jobs occupy cards.
- Harness deployed at `/home/dowling/r1_trackg_20261117/autoresearch_harness`:
  `git rev-parse HEAD` = `717ad835df32bbe1047d032fb5bb8dde5384a258`, `git status --porcelain` empty
  (clean), branch `r1-local-trackg-v2-20261114`.
- Paper repo worktree at `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b` (detached at
  `16185b0b`); the v4 live run exists at
  `/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z`:
  `console.log` ends 2026-10-21T13:11:35Z "not resuming: the run completed"; `panel/finalize.json` is the
  finished marker; the Paper A repo is on branch `paper-a-v4-ada`.
- `paper_a_status_ada.json` was filled: checkout `/home/dowling/agent-checkpoint-intervention`, branch
  `paper-a-v4-ada`, run dir as above, `finished_markers: ["panel/finalize.json"]`, no state file (none was
  found in the run dir), `tmux_session: "paper_a_live"` (no Paper A tmux was running), process pattern
  `agent-checkpoint-intervention`.
- **Why `nvidia_smi_binary` is set to a small wrapper** (`/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live`,
  sha256 `3be54e990bc8741dc69b805e6fd3a7f75143797966bccb7d28510f0f084f6a7e`): the host's `nvidia-smi` lists
  4 stale zero-memory compute entries whose `ps` identity is gone (namespace-hidden), so the unmodified
  check conservatively returns `unknown` ("a GPU compute process could not be identified"). The wrapper
  removes only entries whose `used_memory` is 0; a real Paper A process always holds memory > 0. With the
  wrapper, `nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory` reports 26 live apps, 0
  unidentifiable.
- Verified run (capture `reports/trackg_g0_20261117/u0_status_20261117.json`): `verdict: clear_finished`,
  `paper_a_live_waiting_for_card: false`, `unidentified_apps: 0`, branch `paper-a-v4-ada`, finalize marker,
  tmux no session, no Paper A GPU process.

## 3. Procedure (after acceptance)

1. Confirm harness HEAD `717ad835…` and clean tree; confirm the paper worktree at `16185b0b` and the
   configured `paper_a_status_ada.json` sha256 equals the committed one; confirm the wrapper exists and its
   sha256 matches; confirm the Paper A checkout branch / run dir / finalize marker.
2. Run `python3 r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json` from the
   paper worktree; require `verdict` in {`clear_running`,`clear_finished`} and
   `paper_a_live_waiting_for_card` present and false; capture the JSON with SHA256SUMS.
3. Record **U0 deployed / Paper A status verified** and the exact hashes/sha256s. No GPU work.

## 4. STOPs (item STOP, not the night)

- Harness HEAD/branch mismatch or dirty; paper worktree/config sha mismatch; wrapper missing or sha
  mismatch; Paper A status cannot be made `clear_*`; any need to touch another user's files/processes or
  sudo; disk <50 GB free on Ada. Preserve the capture, record the STOP in this item, skip dependents.

## 5. Must not

- No GPU job/lease on Ada in U0; no noise-floor/D21/D28 measurement; no T1 sweep; no TASL-7/TASL-2 action;
  no other user's processes/files; no deletion; no push to main/exam-x; no model downloads.
