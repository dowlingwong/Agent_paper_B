# Track P P.3a D2 delivery record — host adaptation (C2 / D2), 19 November 2026

**Status: ENGINEERING delivery record for the mechanically pinned code unit; revision 3 (round-1 and round-2 review
fixes included).** Authority `R1-TRACKP-D2` in `docs/r1/PLAN.md` (published `main` `de3de54f`). No GPU job, no
TASL host, no model, no evidence root, no push, no merge and no deletion. This record is committed by the **D2**
delivery-pin commit; it records C2 and the D2 runner blob, which are fixed before that commit is created.

## Delivered objects

| Object | Value |
|---|---|
| Base **D** | `8662e35991659f7a661fb7ed6be4980791d302f3` (single parent of C2; published base `de3de54f`; `b9ad6f8f` attempt-1 pin) |
| **C2** (code commit) | `9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e` — `fix(r1): Track P D2 host adaptation (TASL-7/TASL-2) + attempt-1 artifact hash verification`; single parent = D |
| **D2** (mechanical delivery-pin child) | the single-parent child of C2 that contains this record; its **runner blob sha256** is `d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750`; its only runner change is the canonical `EXPECTED_PAPER_HEAD = "<C2>"` line, byte-for-byte identical to C2's runner otherwise. The **D2 commit sha** is supplied separately with the completion handoff for the ops delivery record / `R1-TRACKP-UNITB` amendment (a commit cannot contain its own sha). |
| C2/D2 runner sha256 | C2 `ae2a7955225b82a95faacbf0dedd1eff06f20ad7a2eddb6cf0cfc434c9469d72`; D2 `d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750` |
| C2 probes-only tests sha256 | `5bdd61ddc0081270f1a9ac2e53b5e7ada40a36ec152115b5d555c1d128edba86` |
| C2 guarded/budget test stubs sha256 | `58c264c0238edad74293a56789355b5d2f71d3b29f9e45f4fea0061ac057e2eb` / `b596d1f9b76bd26904b267002a63cfa7106749a99c54f45e5fb791b6c08c2470` |
| C2 host snapshot / child record sha256 | `r1/c3/train/run.py` `d1c12ce62a1809ecf3ad913e56c3d36ee4f43fa2f32f9f206227a16ed376df95`; `r1/scripts/trackp.py` `5679ce1bc26721ca129fedf7e9e9bef705d8ce056eb2fac7e745d7879b65aee6` |
| C2 unit report sha256 | `9d594b4a52d1ed71d5739cdb2c3cce5a8ca3765a0a680d16954ce300f457bd35` (`docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md`) |
| C2 code-units addendum sha256 | `319d185263cc2e769df93ea2abdea8f1a32ce971462fbd1e39b016f544612664` (`docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md`) |
| Branch / worktree | `trackp-p3a-d2-20261119` at `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackp-p3a-d2-20261119` |
| Author/committer | `Dowling Wong <wangdowling@gmail.com>` |

## Operator condition (detached HEAD only)

`EXPECTED_PAPER_BRANCH` is unchanged (`trackp-p3a-code-20261116`), so the unchanged paper-head identity rule does
**not** accept the delivery branch name. **Deliver/check out D2 detached** (as the 17 Nov TASL-2 D delivery did);
`verify_paper_head({"commit": D2, "branch": "HEAD"})` accepts it as `delivery_pin_child`, while
`branch: "trackp-p3a-d2-20261119"` is refused. One host per table, named in the run report (`R1-TRACKP-UNITB`).

## What C2 contains (host contract only)

- Host profiles: TASL-7 (`tasl-7`, driver `580.178.04`, TASL-7 freeze pin) and TASL-2 (`tasl-2`, driver
  `535.309.01`, committed portal freeze pin byte-identical to the TASL-7 pin, sha `50238e5a…`); unknown host/wrong
  driver STOP; the multi-base attempt-1 path stays TASL-7-only.
- The attempt-1 boot-id equality gate is removed; the preflight verifies the attempt-1 journal (`1e73e80f…`), the
  four `EVIDENCE/<base>/final/manifest.json` and their saved/model files (recorded inventory manifest sha256 pinned),
  the backup archive (`fa2437ee…`) and the attempt-1 lease log (`69505091…`), and records/discloses the current boot
  id (`boot_id_required: false`).
- **Revision 2 (round-1 review fix):** `build_attempt1_provenance` and `snapshot_attempt1_lease_log` use the same
  host-aware lease-log discovery as the verifier (TASL-2 staged `_attempt1_gpu_lease_log.jsonl`, never the different
  live TASL-2 global log), so a TASL-2 run passes preflight → provenance → `assert_attempt1_pins` → snapshot.
- **Revision 3 (round-2 review fix):** the driver/boot path is host-parameterized, so the TASL-2 fallback is
  executable at code level. `R.host_driver_snapshot(expected_driver)` backs `verify_probes_only_pins` and `run_unit`
  (TASL-7: unchanged `tasl7_driver_snapshot`; TASL-2: `/proc` + `nvidia-smi`, kernel/user agreement, expected driver
  pin, branch package inventory best-effort). The attempt-2 child (`r1/scripts/trackp.py`, via `R.driver_record`)
  records generic `host_driver` on TASL-2 for `--a3-short` probes (top level and per `gpu_lease` event); TASL-7 keeps
  `tasl7_driver` only; `run_unit` accepts either. Real-snapshot CPU tests (OS primitives faked, the blocking
  function not stubbed) cover the TASL-2 preflight, lease record and a full `run_unit`.

**Capability statement (accurate):** TASL-2 execution is now **implemented and CPU-tested at the code level**; this
unit did **not** contact any host, so it does not claim a TASL-2 hardware run. See
`docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md` (§0.3, §3, §7) and the review records
`reviews/TRACKP_P3A_D2_CODE_REVIEW_20261119.md` / `reviews/TRACKP_P3A_D2_CODE_REVIEW_R2_20261119.md`.

## Verification commands

```bash
git -C <d2-worktree> rev-parse HEAD^                                  # == C2 e8816221…
git -C <d2-worktree> rev-list --parents -n 1 HEAD                     # <D2> <C2>  (single parent)
git -C <d2-worktree> diff --name-only HEAD^ HEAD                      # runner + this delivery record only
git -C <d2-worktree> show HEAD:r1/scripts/trackp_p3a_guarded.py | sha256sum   # f284d233…
# byte-exact pin: C2's runner blob with its canonical EXPECTED_PAPER_HEAD line replaced by the line naming C2
# reproduces HEAD's runner blob exactly (the unit's own `_delivery_pin_child(D2)` returns True)
```

CPU tests (no GPU/model/host):

```bash
cd /Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackp-p3a-d2-20261119
../_harness_venv/bin/python -m pytest -q -p no:cacheprovider \
  r1/tests/test_trackp_p3a_guarded.py r1/tests/test_trackp_p3a_probes_only.py
# => 5 failed, 69 passed, 2 skipped (the 5 failures are the pre-existing torch-missing tests; D baseline:
#    5 failed, 49 passed, 2 skipped)
```
