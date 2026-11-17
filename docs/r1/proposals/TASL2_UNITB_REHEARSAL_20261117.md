# Unit (revision 5) — TASL-2 ENGINEERING rehearsal of the Unit B DRYRUN invocation (17 November 2026)

**Status: proposal for fresh independent review; not executed.** Revision 4 follows the author's 17 Nov
clarification and re-scopes within `R1-TASL2-UNITB-REHEARSAL` (no deviation): rehearse **Unit B's exact
DRYRUN invocation** — `kev-0.8b`, `--budget --a3-short`, `n=8`, same flags as A2 — on TASL-2 in an
ENGINEERING scratch root, never an attempt-2 root, never counted. The earlier tiny-kev attempt (revisions
1–3) was abandoned because `--tiny` forces A3 v1 0/2k/8k and cannot reach the `--a3-short` path
(`proposals/TASL2_UNITB_REHEARSAL_20261117.md` history; reviews R1–R3). Authority: `R1-TASL2-UNITB-REHEARSAL`
(`author-d8-confirm-20261117` @ `26177d82`) + `R1-TASL2-REHEARSAL-SCOPE` (`author-decisions-20261117b` @
`33c82351`) + `R1-TRACKP-TASL2-HOST` (same branch @ `45fb94cc`), `R1-TRACKP-UNITB` (main `16185b0b`), `R1-TASL7-TRACKP`.

## 1. Scope and the one recorded difference from A2

- Rehearsed command (A2's DRYRUN minus only `--load`, because the attempt-1 `EVIDENCE/kev-0.8b/final/saved`
  files are TASL-7 evidence inputs and are not on TASL-2; the base+adapter are loaded from the committed
  config's local paths):
  `python -m r1.scripts.trackp probes --base kev-0.8b --head-form linear12 --budget --a3-short
   --n-probe 8 --evidence DRYRUN --run-dir <scratch>/ENGINEERING_rehearsal_<UTC>/DRYRUN/kev-0.8b/probes`
- All other flags/paths are A2's; the run uses the frozen TASL-2 `trackp-gpu` venv, the D worktree at
  `8662e359…`, and the committed `trackp_portal.json`. **Expected side effects (recorded, not "outside
  changes")**: the ordinary GPU lease (`~/r1_locks/gpu0.lock`); the shared lease log gains **three**
  lines (`acquired`, `start`, `end`; 188 -> 191), and `manifest.gpu_lease` has **two** entries;
  `gpu_lease`'s status gate on TASL-2 (`portal_guard=True`, `track_x_running(None)`, `run.py:130-141`)
  runs `git -C D fetch -q origin main`, which will write the linked-worktree `FETCH_HEAD` and a loose
  `refs/remotes/origin/main` and uses the network. Preflight records `git ls-remote` (remote main
  `26177d82…` vs local `b5a7aec…`), the `FETCH_HEAD`/ref state before/after, and treats a stalled fetch
  (`TimeoutExpired`) as a host/network STOP, **not** automatically a Unit B defect. Everything else is
  written only under the scratch root.
- **Not rehearsed:** the guarded `trackp_p3a_guarded.py --probes-only` wrapper and the `--load` of attempt-1
  saved weights; TASL-7's Unit B remains mandatory and is the evidence run. This is ENGINEERING on TASL-2,
  not evidence; nothing counts toward the P.3a budget or tables.
- If the command fails (including `ContextOverflow`, missing A3-short marker, rc != 0, no report, OOM or
  CPU fallback), that is a **real Unit B defect**: STOP, preserve, report; the C2/D2 + `R1-TRACKP-UNITB`
  amendment path follows.

## 2. Facts verified read-only (17 Nov 2026, 00:12–00:25Z; re-check after acceptance)

TASL-2 `dowling`; RTX 4090 driver 535.309.01, 24,564 MiB, 353 MiB/0 %, no compute app; disk 374 G free.
Venv `/home/dowling/r1_trackp/venvs/trackp-gpu`: Python 3.12.15, torch 2.6.0+cu124; `uv pip freeze` = 121
lines sha `50238e5a…`, **byte-identical** to `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`.
D worktree `/home/dowling/r1_engineering/unitb_rehearsal_20261117/Agent_paper_B_D_20261117` detached at
`8662e35991659f7a661fb7ed6be4980791d302f3`, clean; runner `c045475b…`; child `trackp.py` `d2a30ec2…`;
config `049bafed…`, `--check-config` placeholders `[]`, digest `64073cea…`. Config `bases.kev-0.8b` points
at local base `…/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41` and adapter
`…/models/jaredpalmer__kev-0.8b@788ddbdd6571`; both present. Lease `~/r1_locks/gpu0.lock` free; lease log
188 lines sha `f813ce66…`; no `*.active`; no Track P marker helper on TASL-2; no `ENGINEERING_rehearsal_*`
or `p3a_attempt2_*` roots.

## 3. Procedure (after acceptance; ENGINEERING only)

All commands from the D worktree with
`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1`, frozen venv, `PYTHONPATH=.`.

1. Create `<scratch>` exactly `…/ENGINEERING_rehearsal_<UTC>` (`%Y%m%dT%H%M%SZ`, must not exist).
2. **Before:** `git -C D status --porcelain --untracked-files=all` (empty); tracked-file SHA256 list;
   ignored/tracked `.pyc` inventory; linked-worktree gitdir/index sha; scratch-parent listing; `git worktree
   list`; `nvidia-smi` compute apps; lease-log line count/sha; `flock -n` probe; disk; exact argv/env.
3. **Run** the §1 command; measure wall time; capture stdout/stderr and the lease log lines added.
4. **After:** repeat the baselines; require: rc 0; `<run-dir>/report.json` and `manifest.json` exist with
   sha256 recorded; `manifest.evidence_label == "DRYRUN"`; `manifest.gpu_lease` non-empty (two entries; GPU uuid in `manifest.host`, duration derived); `report["A3"]["protocol"] == "v2_budget"`; `report["A3_descriptive"] ==
   {"skipped":"R1-P3A-OOM-OPTION3","levels":[2000,8000],"pass":null}`; `A4` and `A4_v1_raw` present (there is no `A4_v1` key); A1==A2 non-packing
   n/a; A5 n/a for kev; no `ContextOverflow`/`A3_errors`; `manifest.gpu_lease` has two entries with the
   GPU uuid in `manifest.host` (duration derived); the lease log gained exactly **three** lines and the
   linked-worktree `FETCH_HEAD`/ref changes are recorded; no tracked file changed; no new untracked file
   outside the scratch root except the recorded lease/fetch side effects; no new `.pyc`; no marker; no
   other worktree; lease released; disk unchanged within tolerance; wall time ≤600 s.
5. Record **"Unit B DRYRUN rehearsal clean"** with: unit/command argv and env; D HEAD/runner/child/config shas; report/manifest sha256 and the exact keys/values above; lease log before/after count+sha and the three added lines; `FETCH_HEAD`/ref before/after; tracked/pyc/untracked/worktree/nvidia-smi before/after; wall time; stdout/stderr and SHA256SUMS; rc; `manifest.gpu_lease`/`trackx_marker`/disk; A1/A2/A5 reasons; report/manifest paths and sha256; the §1
non-goal and the one difference (`--load` absent); or STOP with the enumerated fields.

## 4. STOPs (item STOP, not the night)

- rc != 0, missing report/manifest, `ContextOverflow`/`A3_errors`, missing `A3.protocol=v2_budget` or the
  skipped marker, no lease or lease not released, OOM/CPU fallback, wall >600 s, any tracked-file/untracked-
  outside-scratch/`.pyc` change (lease-log append excepted), any other host action (except the recorded §1 lease/fetch side effects), disk <50 GB, or a
  needed authority/code change. This is a real Unit B defect (**child-path** failure: rc/report/A3/lease-child) → STOP + C2/D2/amendment
path; a host/env/network failure before the child (fetch timeout, missing lease, wrong HEAD/freeze) is an
item STOP, not a Unit B defect. No retry.

## 5. Must not

- No attempt-2 root, no evidence label/table, no TASL-7 action, no deletion, no main/exam-x push, no other
  user's files/processes, no install (freeze matches), no change to code/config/rules; TASL-2 is not the
  evidence host.
