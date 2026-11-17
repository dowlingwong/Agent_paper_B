# Unit (revision 2) — TASL-2 ENGINEERING host/env/CLI readiness rehearsal for the Unit B DRYRUN path (17 November 2026)

**Status: proposal for fresh independent review; not executed.** Revision 2 answers the round-1 review
(`reviews/TASL2_UNITB_REHEARSAL_REVIEW_20261117.md`, sha `601a3b29…`, not accepted: the bare `probes --tiny`
path cannot exercise `--budget/--a3-short` nor the guarded runner, and the "no file outside scratch"
criterion missed Python bytecode/git index writes). This unit is therefore explicitly a **host / frozen-env /
CLI readiness rehearsal**, not a reproduction of the Unit B EVIDENCE command. Authority:
`R1-TASL2-UNITB-REHEARSAL` (`author-d8-confirm-20261117` @ `26177d82`), `R1-TRACKP-UNITB` (main
`16185b0b`), `R1-TASL7-TRACKP`/`R1-TASL2-LOCK` (TASL-2 non-evidence only). AI-assisted; no evidence.

## 1. Scope and explicit non-goal

- **Rehearsed:** TASL-2 host state; the committed `trackp-gpu` freeze; the D checkout; the CLI wiring of
  `trackp.py probes` on the CPU tiny DRYRUN path for the kev family; the `--a3-short` guard; the
  absence of GPU/lease/marker side effects in an ENGINEERING scratch root.
- **NOT rehearsed:** the guarded runner `trackp_p3a_guarded.py --probes-only` and its real
  `probes --base kev-0.8b --budget --a3-short --load attempt-1/EVIDENCE/kev-0.8b/final/saved` child. That
  needs the attempt-1 `final/saved` files and the full pool budget counters, which are TASL-7 evidence
  inputs; TASL-2 must not fabricate or copy them. The result is recorded as **"host/env/CLI rehearsal
  clean"**, never as "Unit B DRYRUN rehearsed".
- No GPU job, no lease, no evidence label, no attempt-2 root, no TASL-7 action.

## 2. Facts verified read-only (17 Nov 2026, 00:12–00:25Z; re-checked after acceptance)

- TASL-2 / `dowling`; RTX 4090 driver 535.309.01, 24,564 MiB, 353 MiB/0 %, no compute app; disk 374 G free.
- `/home/dowling/r1_trackp/venvs/trackp-gpu`: Python 3.12.15, torch 2.6.0+cu124; live `uv pip freeze` =
  **121 lines, sha256 `50238e5a…`, sorted diff against
  `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` empty** → no install needed.
- D worktree `/home/dowling/r1_engineering/unitb_rehearsal_20261117/Agent_paper_B_D_20261117`: detached at
  **`8662e35991659f7a661fb7ed6be4980791d302f3`**, clean; runner sha `c045475b…`; child `trackp.py` sha
  `d2a30ec2…`; config `trackp_portal.json` sha `049bafed…`, `--check-config` placeholders `[]`, config
  digest `64073cea…`.
- 8 pinned model repos (26 G) and HF caches present; no `ENGINEERING_rehearsal_*`/`p3a_attempt2_*` roots; no
  `*.active`; TASL-2 has no Track P evidence-marker helper, so no marker can be taken.

## 3. Procedure (after acceptance; ENGINEERING only)

All commands from the D worktree with:
`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=`, using the frozen
venv `/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python` and `PYTHONPATH=.`.

1. Create the scratch root exactly `…/ENGINEERING_rehearsal_<UTC>` (UTC `%Y%m%dT%H%M%SZ`, must not exist).
2. **Baselines:** `git -C <D> status --porcelain` (empty), `git -C <D> ls-files -z | xargs -0 sha256sum` into
   `<scratch>/baseline_tracked.sha256`, `stat`/sha256 of the runner+child+config, `nvidia-smi` compute-apps
   list, `flock -n ~/r1_locks/gpu0.lock true` probe (must succeed; no Track P marker exists on TASL-2),
   lease log line count/sha256, and `git -C <D> worktree list` (no new worktrees).
3. **Tiny DRYRUN path:** `python -m r1.scripts.trackp probes --tiny --family kev --head-form linear12
   --evidence DRYRUN --run-dir <scratch>/DRYRUN/kev-0.8b/probes --n-probe 8`; require rc 0, wall time
   recorded, `<run-dir>/report.json` parses and has the keys `A1,A2,A3,A4,A5` (values may be N/A; record the
   exact keys/shape), no GPU/lease/marker side effect, and no `EVIDENCE` label.
4. **A3-short guard:** the same command plus `--budget --a3-short` with a **distinct** run dir
   `<scratch>/guard-refusal/probes` must exit **rc 2** with the
   `--a3-short needs --budget on a real base` STOP text and create no run directory.
5. **Wall-time bound:** the whole rehearsal (steps 2–4) must finish within **600 s**; otherwise STOP and
   record the timeout (it would mean the tiny path is unexpectedly expensive).
5. **After:** re-run the baselines; require (i) no tracked file in the D worktree changed, (ii) no new
   `__pycache__`/`.pyc` under the D worktree (bytecode disabled), (iii) no untracked file outside the
   scratch root, (iv) no GPU compute app/lease/marker, (v) the lease log unchanged, (vi) the git worktree
   list unchanged. Capture stdout/stderr, `SHA256SUMS`, and write the result record.
6. Result: **host/env/CLI rehearsal clean** (with the §1 non-goal stated), or a STOP.

## 3b. Mandatory baselines and result record (round-2 review conditions)

Before step 2, record into `<scratch>/baselines/` with SHA256SUMS: (a) tracked-file SHA256 list
(`git ls-files -z | xargs -0 sha256sum`) and `git status --porcelain --untracked-files=all`; (b) the
pre-existing ignored bytecode inventory (`git status --ignored` + `find . -name '*.pyc'`, 7 ignored + 65
tracked results .pyc observed); (c) linked-worktree gitdir path and index file sha256/size; (d) scratch
parent listing and hash of pre-existing outside-scratch files; (e) `git worktree list`; (f) nvidia-smi
compute-apps list; (g) lease-log line count/sha and `flock -n` probe; (h) host snapshot (hostname, date,
uptime, disk, driver, venv freeze sha); (i) exact argv and env. After step 4, repeat (a)–(g) and require:
no tracked file changed, no new untracked file outside the scratch root, no new `.pyc`, no new worktree,
no GPU compute app, no lease-log change, no marker. The result record must contain: these before/after
capture hashes; the exact report/manifest paths and sha256; the manifest no-GPU fields
(`evidence_label=DRYRUN`, `gpu_lease=[]`, `host.device=null`, `host.cuda_visible_devices=""`); exact
report keys for the kev tiny path — `A1==A2` with `pass:null`/non-packing reason, `A3` numeric v1
(`A3_LENGTHS=(0,2000,8000)`), `A4`/`A4_v1_raw`, absent `A3_descriptive`, `A5` BinToken-n/a reason; guard
rc2 text/no dir at `<scratch>/guard-refusal/probes`; wall time ≤600 s; and the §1 non-goal statement
(TASL-2 is not the evidence host; the TASL-7 Unit B DRYRUN remains mandatory). A runner defect → STOP and
the C2/D2 + amendment rule of §5; TASL-7 re-verification of any D2 and authority naming D2 are required.

## 4. STOPs (item STOP, not the night)

- Any file outside the scratch root changes (including bytecode, worktree index, generated files) → STOP.
- Any baseline/result-record item above missing or not matching → STOP (do not record "clean").
- Wall time >600 s, or the guard creates a directory or exits with rc != 2 → STOP.
- Freeze/venv mismatch, D HEAD/dirty mismatch, runner/child/config sha mismatch, rc != 0 in step 3,
  report keys missing, guard not rc 2 or creating a directory, any GPU/lease/marker side effect, lease log
  change, disk <50 GB, or any need to touch another user's files/processes/sudo. Preserve capture.

## 5. Defect path

If a runner defect appears, STOP; write a new code unit on `trackp-p3a-code-*`, get it independently
reviewed, produce a new reviewed code commit C2 + mechanical pin child D2, deliver D2 to TASL-7, and obtain
an authority amendment if `R1-TRACKP-UNITB` must name D2 (it currently names D). Never change what TASL-7
runs without that review and authorization.

## 6. Must not

- No evidence label, no attempt-2 root, no TASL-7 action, no GPU/lease job, no model download outside the
  cached pools, no other user's files/processes, no deletion, no push to main/exam-x, no installation
  (freeze already matches).
