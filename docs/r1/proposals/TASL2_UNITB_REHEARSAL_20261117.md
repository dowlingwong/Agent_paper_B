# Unit — TASL-2 ENGINEERING rehearsal of the Track P Unit B DRYRUN path (17 November 2026)

**Status: proposal for fresh independent review; not executed.** Authority: `R1-TASL2-UNITB-REHEARSAL`
(author branch `author-d8-confirm-20261117` @ `26177d82`; also main `16185b0b`): "TASL-2 上排练 Track P
Unit B 的 DRYRUN（ENGINEERING）：按已提交 freeze `reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`
装 trackp-gpu 环境（排序 diff 为空），干净检出代码 D `8662e359`，在明确标为 ENGINEERING 的临时目录跑
kev-0.8b 的 DRYRUN 路径；不是 attempt-2 root，永不计入；单元先独立审查。Track P 的 evidence 表仍只在
TASL-7 产出（R1-TASL7-TRACKP）。" Also `R1-TRACKP-UNITB` (main `16185b0b`) and the accepted
attempt-2 plan. AI-assisted; no GPU evidence.

## 1. Facts already verified (read-only, TASL-2)

- Host TASL-2, user `dowling`; RTX 4090, driver 535.309.01, 24,564 MiB; disk 374 G free.
- The existing `/home/dowling/r1_trackp/venvs/trackp-gpu` is Python 3.12.15 with torch 2.6.0+cu124 and
  `torch.cuda.is_available() == True`; `uv pip freeze --python` gives **121 lines and a sorted diff
  against `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` of 0 lines** — the committed
  portal freeze is matched exactly, so no reinstall is needed.
- `uv 0.13.6` is at `/home/dowling/.local/bin/uv`; the 8 pinned model repos (26 G) and an HF cache are
  present under `/home/dowling/r1_trackp`.
- A clean ENGINEERING worktree was created: `/home/dowling/r1_engineering/unitb_rehearsal_20261117/
  Agent_paper_B_D_20261117` at **D `8662e35991659f7a661fb7ed6be4980791d302f3`** (detached, clean).
- In that worktree, `python -m r1.scripts.trackp --check-config` reports `"placeholders": []` and config
  sha256 `64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`.

## 2. Procedure (ENGINEERING only; no evidence, no attempt-2 root)

1. Create the scratch root **exactly** `…/unitb_rehearsal_20261117/ENGINEERING_rehearsal_<UTC>` (UTC
   `%Y%m%dT%H%M%SZ`); it must not already exist. Never name it `p3a_attempt2_*`; never point it at a
   TASL-7/evidence directory.
2. From the D worktree, with `PYTHONPATH=.` and the frozen venv:
   `python -m r1.scripts.trackp probes --tiny --family kev --head-form linear12 --evidence DRYRUN
   --run-dir <scratch>/DRYRUN/kev-0.8b/probes --n-probe 8`.
   This is the kev-family DRYRUN path on the CPU tiny stand-in (labelled DRYRUN), in the scratch root.
3. Verify: rc 0; `<run-dir>/report.json` exists and contains the A1/A2/A3/A4/A5 keys; no `.active` marker
   was created; no GPU lease was taken; the run dir is under the scratch root only; no EVIDENCE label
   anywhere; no file outside the scratch root changed; capture stdout/stderr/journal and SHA256SUMS.
4. Negative check of the A3-short guard: `probes --tiny --family kev --budget --a3-short …` must be
   refused (rc != 0, the `--a3-short needs --budget on a real base` STOP) and must not create output.
5. Record `rehearsal clean` if all hold. If a runner defect appears, STOP the rehearsal, preserve the
   capture, and write a separate reviewed code fix on `trackp-p3a-code-*`; A2 on TASL-7 would then use the
   fixed reviewed commit only.

## 3. STOP conditions

- Frozen-env mismatch (already zero diff; any change → STOP), D worktree dirty or HEAD != D, config
  placeholders appear, tiny run fails or writes outside the scratch root, a marker/lease/GPU use appears,
  the A3-short guard does not refuse, or any other host action is needed. Preserve and report; do not
  retry an EVIDENCE run (there is none here).

## 4. Must not

- No evidence label, no attempt-2 root, no TASL-7 evidence, no GPU/lease job, no model download beyond the
  cached pools, no other user's process/files, no deletion (move aside only), no push to `main`/`exam-x-*`,
  no installation if the freeze already matches, no touching TASL-7.

## 5. Review and result

Fresh independent review of these exact bytes is required before execution (the reviewer checks the host
facts read-only and the command/scope). After acceptance, execute steps 2–4, then append the before/after
capture, report keys and `rehearsal clean`/STOP to this unit (or a result record) and commit.
