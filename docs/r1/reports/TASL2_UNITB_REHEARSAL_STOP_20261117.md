# TASL-2 ENGINEERING rehearsal — B1 verified, B2/B3 STOP (17 November 2026)

**Authority.** `R1-TASL2-UNITB-REHEARSAL` (`author-d8-confirm-20261117` @ `26177d82`), `R1-TRACKP-UNITB`
(main `16185b0b`), `R1-TASL7-TRACKP` (evidence tables TASL-7 only). AI-assisted; no GPU, no evidence.
Status: **B1 done (environment verified); B2/B3 STOP on a reviewed defect finding; no rehearsal clean
claim.**

## B1 — environment/checkout verification: DONE

- TASL-2 `dowling`: RTX 4090, driver 535.309.01, 24,564 MiB, no compute app; disk 374 G free.
- `/home/dowling/r1_trackp/venvs/trackp-gpu`: Python 3.12.15, torch 2.6.0+cu124; `uv pip freeze` = **121
  lines, sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`**, sorted diff
  against `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` **empty** → committed
  freeze matched; **no install needed**.
- D checkout `/home/dowling/r1_engineering/unitb_rehearsal_20261117/Agent_paper_B_D_20261117`: detached at
  **`8662e35991659f7a661fb7ed6be4980791d302f3`**, clean; runner `c045475b…`; child `trackp.py`
  `d2a30ec2…`; config `049bafed…`, `--check-config` placeholders `[]`, digest `64073cea…`; models 26 G /
  HF caches present; no attempt-2 or `ENGINEERING_rehearsal_*` roots; no Track P marker helper on TASL-2.

## B2/B3 — STOP (reviewed defect)

The proposed tiny kev DRYRUN rehearsal cannot succeed on the delivered bytes, so it was **not executed**:

- The command `probes --tiny --family kev` runs A3 **v1** lengths (0/2,000/8,000) because `--tiny` forces
  `counters=None` (`trackp.py:236-244`). The tiny kev `PointerWrapper` has `max_state=1024`
  (`model.py:249`; `tiny.py:71`), and strict Kev encoding raises `ContextOverflow` for 2k/8k
  (`model.py:274, 313-315`). `exam_run.py:246-258` makes only the *descriptive string* keys
  `descriptive_2000/8000` non-fatal; the v1 integer keys re-raise, so the command ends rc 1 with **no
  `report.json`/`manifest.json`**. The same limitation is committed in
  `docs/r1/reports/trackp_p3a_dryrun_20261026/kev-0.8b_soft/report.json` and
  `TRACKP_P3A_DRYRUN_20261026.md` ("refused by Kev's strict 1,024-token state limit"; introduced by
  `08aeaff9`). The round-2 assumption that the tiny path succeeds was unsupported (the cited test is
  skipped locally and failed in the only committed GPU-venv run).
- Independent reviews: `TASL2_UNITB_REHEARSAL_REVIEW_20261117.md` (`601a3b29…`, not accepted),
  `..._R2_20261117.md` (`8cae98de…`, not accepted), `..._R3_20261117.md` (`2d8e79dd…`, not accepted;
  central finding above). Review option (a) expect the defect STOP, (b) reviewed C2 + new D2 + authority
  amendment, or (c) re-scope step 3 to a runnable path with a recorded authority deviation — all require a
  decision or a new reviewed code unit; none was taken overnight.
- **No host write beyond read-only checks; no GPU; no attempt-2 root; nothing deleted or moved.** TASL-2
  remains non-evidence only; TASL-7's Unit B remains at D `8662e359` (unchanged).

## Decision needed / next

Author/coordinator: either (a) accept a re-scoped readiness rehearsal (e.g. qwen tiny success path + kev
expected-defect STOP + guard, with the authority deviation recorded), or (b) authorize the C2/D2 +
`R1-TRACKP-UNITB` amendment path for a fixed kev DRYRUN. No evidence claim is made either way.
