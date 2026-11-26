# B1 `_d` run HEAD review — `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` (13 November 2026)

**Reviewer.** Freshly spawned independent reviewer; I did not write this unit and did not modify anything under
`/Users/wongdowling/Documents/agent_paper_B`. Writes only in
`/Users/wongdowling/Documents/agent_sys_paper/_xfer/b1_runhead_d_review_20261113/` and `/tmp`. TASL-7 access was
read-only (`cat`/`stat`/`sha256sum`/`git rev-parse`/`tmux ls`/`nvidia-smi`/`flock`/`lsof`/`ps`/`pgrep`); the `_c`
STOP scene, the `_b`/6835 scenes and the paused Track S S0.5 scene were not touched.

## Unit

- Branch `ops-b1-restart-d-20261113`, HEAD `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` (run-ID prefix `7912`), single
  parent `999759b7fec7158e930950544db6aac4988569bb`.
- Base is the `Accepted commit:` of round 4 in `docs/r1/reviews/B1_MODEL_OUTPUT_REVIEW_20261113.md` on delivery branch
  `mac-b1-modelout-20261113`, tip `a877fd7f7347a8538f29b47328b4a4b036981e5d`, from bundle
  `/Users/wongdowling/Documents/agent_paper_B/Claude outputs/b1_modelout_20261113.bundle`, SHA-256
  `ee9e8b762f7a57f15aa2af982103ad4227dae23d56544afbebe3c2c5cbf88a67` (verified; bundle verifies; it requires
  `4b312844`).
- Run checkout inspected: `/private/tmp/pb_exec` (clean, HEAD = the unit, origin = `https://github.com/dowlingwong/Agent_paper_B.git`).

## Checks

1. **Base/branch — PASS.** `git rev-list --count 999759b7..7912b7ff` = 1; `--merges` = 0; parent list is exactly
   `999759b7`; fresh `git ls-remote origin` gives `refs/heads/ops-b1-restart-d-20261113` = `7912b7ff…` (push reflog
   `update by push` at 2026-11-13T14:03:38+01:00); branch date `20261113` = commit date `2026-11-13T14:03:36+01:00`
   (13:03:36Z); prefix `7912` = HEAD's first four hex.
2. **Prose-only — PASS.** `git diff --name-only 999759b7..7912b7ff` = only
   `docs/r1/authorizations/trackx_b1_20261105.md` (1 insertion, 1 deletion; no other path; no deletions). The
   ```json fence-to-EOF SHA-256 is `7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be` at both
   parent and HEAD; the block parses and `approved` is `true`. The one changed line names `_d`, the stopped run
   `4b31_20261112_c`, reviewed base `999759b7fec7158e930950544db6aac4988569bb`, PLAN
   `R1-EXAM-B1-MODEL-OUTPUT-INVALID`, the paper re-pin `02a914944cc546fc33a6428b1eb92a8993542bef`, and hand-off
   `proposals/B1_RESTART_HANDOFF_D_20261113.md`. It keeps "The real gate, current host preflight and handover remain
   required"; no claim that they are satisfied; no `fffa_20261111_b` and no stale `_c` text (the only `_c` is inside
   `4b31_20261112_c`).
3. **Metadata/scope — PASS.** Author = committer = `Dowling Wong <wangdowling@gmail.com>`; message is accurate about
   the restart, base, PLAN row, pin and byte-identical JSON. No deletions. Protected-path diffs are empty for both
   `02a91494..999759b7` and `999759b7..7912b7ff` over `r1/exam`,
   `r1/scripts/exam_runner.py`, `r1/scripts/llama_server_instance.py`, `r1/scripts/llamacpp_probe.py`,
   `r1/headroom/e1b_collect.py`. `r1/scripts/configs/exam_b1_v2.json` `paper_commit` =
   `02a914944cc546fc33a6428b1eb92a8993542bef`. All four PLAN §10 rows (`R1-EXAM-B1-ANCHOR-R4`,
   `R1-EXAM-B1-ANCHOR-R4-H2`, `R1-EXAM-B1-TRUNCATION-INVALID`, `R1-EXAM-B1-MODEL-OUTPUT-INVALID`) are present.
4. **Hand-off §0/§1 readiness — PASS.** Round 4 is recorded accepted at `999759b7`;
   `git diff --name-only 999759b7..a877fd7f` is only `docs/r1/reviews/B1_MODEL_OUTPUT_REVIEW_20261113.md`; the
   diagnosis `docs/r1/reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` exists and §1.4 is explicitly PENDING/optional;
   its §4.5 gives 758 passed / 18 failed / 0 skipped against baseline `4b312844` 699 / 18 / 0 with the same 18 IDs
   (112 pass in the host-version venv). The live frozen venv `/home/dowling/exam-x/work/venv` matches the truncation
   diagnosis §2.3 exactly: openai 2.36.0, langchain_openai 1.2.1, langchain_core 1.3.3, langgraph 1.1.10,
   pydantic 2.13.4, pydantic_core 2.46.4, httpx 0.28.1.
5. **Marker discrepancy — documented (major for the `_d` handover, not a blocker for this HEAD).** See R1 below.
6. **Scene/state — PASS.** The `_c` STOP scene `b1_4b31_20261112_c` is unchanged (mtime 12 Nov 19:01; no file newer
   than 2026-11-13; `batch_state.json` STOPPED, 89 completed; `_c` handover `b1.exit` = 1); the `_c` staged checkout
   `b1_paper_final_4b312844…/paper` is at `4b312844` and clean; `_b` (`b1_fffa_20261111_b`) and 6835
   (`b1_6835_20261108_a`) are present and untouched. The paused Track S S0.5 scene
   `/home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113` is `status: paused` (`trks_s05_t7.exit` rc=0,
   `STOP` present); its tmux session is gone. TASL-7 is quiescent: no `exam_runner`/`llama-server`, no GPU compute
   app, GPU 243 MiB idle / 0 %, `gpu0.lock` free with no holder, default tmux only `trks_watch`. The preserved
   6835 tmux server on its private socket holds only an idle `bash` with no child.

## R1 — the `_c` Track X marker was already retired; the `_d` handover must record the predecessor receipt

**Severity: major for the `_d` handover review; documented here, so not a blocker for this HEAD.**

`docs/r1/proposals/B1_RESTART_HANDOFF_D_20261113.md` §2.4 (at parent `999759b7` and HEAD `7912b7ff`) still says
"The `_c` run's `~/r1_locks/trackx_evidence.active` is still present" (content `{"head":"4b312844…","run_id":"4b31_20261112_c"}`,
SHA-256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, creation receipt
`/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c/marker-receipt.json`, SHA-256
`e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`) and prescribes `b1_o2_marker.py retire`.
That is false now. The accepted STOP-case unit `docs/r1/proposals/B1_C_STOP_MARKER_RETIREMENT_20261113.md`
(`trackS-ops-20261030`, executed 2026-11-13T10:49:31Z) already retired it, and the hand-off was written later
(commit `afdd6e9c`, 2026-11-13T13:09:03+01:00 = 12:09Z).

Live state (TASL-7, 2026-11-13T13:07Z): `~/r1_locks/trackx_evidence.active` **absent**; the archive is
`~/r1_locks/_to_delete/trackx_evidence.active.040ffbe17da643a28264bbf90ccd88fe`, content
`{"head": "4b312844962e1106db04d5a60bf996fad0e3e514", "run_id": "4b31_20261112_c"}`, SHA-256
`f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`; the `_c` handover dir holds
`marker-retirement_stop.json` (SHA-256 `2bfc6542ebc2b41679a436ad39b12d541d31ad0872691b095eb9e09ac987447a`),
`marker-retirement_stop.note` (source receipt path + SHA-256 `e0da112f…`), `.rc` = 0, `.err` empty; the original
creation receipt is unchanged. `b1_o2_marker.py retire` opens the marker with `O_RDONLY`, so following §2.4 now
fails (ENOENT / receipt mismatch) and the handover fails closed — a blocked launch, not a scene change.

**Required adaptation, to be covered by the `_d` handover review before launch.**
1. Verify `~/r1_locks/trackx_evidence.active` is absent and the archive `…040ffbe1…` matches SHA-256 `f8c8624f…`
   and the content above; if the live marker unexpectedly exists, STOP.
2. Do **not** call `retire`. Record the predecessor retirement receipt in the new `_d` handover directory: path +
   SHA-256 of `marker-retirement_stop.json` (`2bfc6542…`) and `.note`, `.rc` = 0, `.err` empty, plus the source
   creation receipt path + SHA-256 (`e0da112f…`) and the retired name/hash (`040ffbe1…` / `f8c8624f…`). Write
   nothing into the `_c` handover directory.
3. Still confirm the P.3a safe pause / Track P paused before creating the new marker; then create the `_d` marker
   with `b1_o2_marker.py create` (`O_EXCL`, so absence is what makes it work) and keep its receipt. Keep Track P
   paused throughout.
4. Fix the same stale wording in `Claude outputs/READY.txt` item 5 and, if the row is re-published, PLAN row
   `R1-EXAM-B1-MODEL-OUTPUT-INVALID` ("the `_c` Track X marker is retired at restart"): the retirement is already
   done by the accepted STOP-case unit; the `_d` handover records that receipt instead of performing a second
   retirement.

## Residual notes

- The run branch is already on origin (`7912…`); the delivery branch `mac-b1-modelout-20261113` is deliberately not
  on origin (bundle-only), consistent with the stated pattern and READY item 5.
- The review record is not in the run HEAD tree (it is only on `a877fd7f`). That is allowed by hand-off §1
  ("reviewed base or a later review-record-only commit") and does not change the run's code/config.
- The auth note calls `999759b7` "the fix"; the code commit is `02a91494`, which the same sentence names — a wording
  nit, not ambiguous.
- The accepted STOP report header still says "rev 2" although the commit and its R3 review are rev 3; that cosmetic
  point is already recorded in its own R3 review and is outside this unit.
- `git diff --name-only 999759b7..a877fd7f` is exactly the review file; `a877fd7f`'s tree otherwise equals the base.

VERDICT: accepted
