# Track S `digits_mlp` host move to TASL-7 — proposal (13 November 2026, rev 3)

**Author decision recorded here; not yet executed.** In the chat of 12 Nov 2026 the author chose the option
"migrate `digits_mlp` to TASL-7 and run it after the B1 `_c` run ends" (recorded by the Lead; the author's selection
is the decision, no sentence is quoted as verbatim). This is an ENGINEERING_ONLY Track S change; it starts nothing by
itself.

## 1. Why

TASL-2 became unreachable on 12 Nov 2026 (TCP/ICMP to 100.120.160.70 failed; the Tailscale peer showed rx 0 while
TASL-7 was reachable). The Phase 4 S0.5 attempt started on TASL-2 at 2026-11-12T19:55:59Z and was last seen running
with 4 committed roots (20:02Z); it cannot be censused, resumed or copied while the host is down. Track S operator
runbook §10 says a TASL-2 reboot/outage is "anything not covered → STOP and ask"; the author has now decided to move
the node to TASL-7. **The TASL-2 `s05` scene is preserved, never modified or deleted.**

## 2. What TASL-7 already has (verified read-only, 2026-11-12T22:41Z; bare refs re-checked after the 22:49Z pushes)

- 1 × RTX 4090, driver 580.178.04, 24 CPUs; `/home/dowling/r1_tracks` with `bin/`, `launch/`, `logs/`, `models/`,
  `opt/llama.cpp`, `remotes/Agent_paper_B.git`, `scratch/`, `out/` and `work/`.
- `work/Agent_paper_B` exists at the **previous** paper pin `d10b05b7` (clean) → the clone must fetch the new
  branch/object and check out **`8237fd02` detached** before use. `work/autoresearch_harness` at `a3fedbb…`
  (clean). The TASL-7 bare repo now has `trackS-ops-20261030` and `mac-tracks-a2u-stale-20261111` (`c8b13b5…`,
  whose history contains `8237fd02`); these refs were pushed at 22:49Z, after the 22:41Z layout verification.
- llama.cpp `620d2225…` (`llama-server` `v0.7.0-dev`, build 11669); GGUF sha256
  `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; server flags per rev 3.3 §0.2.
- **Track S venvs are the same 65-package `pip_freeze` on both hosts** (`TRACKS_HOST_FACTS_20261030` §0.5,
  sha256 `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687`; numpy 2.4.6, scipy 1.17.1,
  sklearn 1.9.1, pandas 3.1.0 per `TRACKS_PHASE3_20261109`); the only difference is the Python patch version
  (TASL-2 3.11.17, TASL-7 3.11.18). The numpy 2.4.4 / sklearn 1.8.0 values are a different (exam-x
  harness-locked) venv, not the Track S venv. The S0.1 re-check below exists to bound the 3.11.17→3.11.18
  difference at the current pin.
- TASL-7's only Track S S0.1 history is the Oct-30 `tabular_mlp` run (serial 0.870 / cross 0.875 STOP, plus the
  `cache_prompt:false` diagnostic 1.000). **No valid `digits_mlp` S0.1 exists on TASL-7 at the current pin** — the
  one required below is new.
- TASL-7 is currently running B1 `_c` (run `4b31_20261112_c`), whose marker is the authoritative priority marker and
  whose GPU/lease it holds; the Track S watcher on TASL-7 pauses on it. Track P marker absent (paused for B1/B2).

## 3. Conditions before a `digits_mlp` run on TASL-7 (all mandatory)

1. **The `_c` Track X marker has been retired by a separately reviewed unit, and the author's 13 Nov revision allows
   both outcomes.** For a normal end, the post-run unit `proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` (rev
   78c6fd7d, accepted) applies. For the actual STOP ending, the author's 13 Nov 2026 decision (relayed; PLAN §10 row
   draft `proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md`) explicitly allows the move, but **first** the
   STOP-case unit `proposals/B1_C_STOP_MARKER_RETIREMENT_20261113.md` must be independently reviewed and executed: the
   marker is renamed into `~/r1_locks/_to_delete/`, the creation receipt is kept and a retirement receipt/note is
   written, and the `_c` STOP scene is left completely untouched; B1 `_c` is never retried. Performed by the B1/Track X
   operator under that unit, not by Track S (see §5). The marker `trackx_evidence.active` with
   `{"run_id":"4b31_20261112_c"}` must be gone and its retirement documented; the GPU lease must be free and no other
   track's llm/compute process present.
2. **New `digits_mlp` S0.1 launch script for TASL-7** (the existing `launch/tasl7_s01.sh` is hardcoded to
   `tabular_mlp`; sha `226dbfa2…`), committed before use and reproduced from the rev-3.3 Phase 1 command with
   `--node digits_mlp` and `--out $OUT/digits_mlp/s01_t7_20261113`; after it runs (GPU free, <1 GPU-h), the host
   facts and the S0.1 determinism/latency result are recorded in a report and **the S0.1 result is independently
   reviewed before S0.5**. A failure is a STOP (author). This bounds the Python 3.11.17→3.11.18 difference.
3. **Paper pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** checked out **detached and clean** on TASL-7
   `work/Agent_paper_B` (the branch is `mac-tracks-a2u-stale-20261111`, already on the TASL-7 bare repo; the host
   clone must fetch and detach). The pin is on that branch's history; there is no separate "pin branch".
4. **Prior reuse**: `a2u_prior_r2_20261111.json` (sha256
   `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`) is copied to TASL-7 `$OUT` and verified.
   It was computed from the TASL-2 S0.4 rerun and is used host-independently; the host change and the Python patch
   difference are disclosed in the report, and no cross-host comparability is claimed.
5. **New TASL-7 launch scripts** (`tasl7_s05_<date>.sh`, `tasl7_s05b_<date>.sh`), committed and independently
   reviewed before use: new directories `$OUT/digits_mlp/s05_t7_20261113` and
   `$WORK/digits_mlp/s05_t7_20261113` (so the preserved TASL-2 `$OUT/digits_mlp/s05` is not overwritten), sessions
   `trks_s05_t7` / `trks_s05b_t7`, the same rev-3.3 Phase 4 command (W 40, 20 instances, policy
   `static:0.00198,0`, obs-inflation 1.0, prior sha above, 8 h deadline, ENGINEERING_ONLY), k = 1, port 18101.
6. **Track X and Track P untouched**: no Track X change other than the separately reviewed post-run marker
   retirement in condition 1, performed under the B1 procedure; Track P stays paused as during B1/B2, and no
   Track P marker is created or retired by this move. The TASL-2 scenes are preserved.
7. **Phase 4 gates apply on TASL-7**: after S0.5, run S0.5b (CPU, no servers); check the calibration gate and the
   λ₂ revision rule (rev 3.3 Phase 4: a second failure is a STOP; coverage-too-high/stratum-0 STOP); the 2 %
   failed-units rule, exit 3 twice, an A/A or fork-rebuild mismatch, and the §10 5-day-GPU cap remain STOPs. Copy
   back `$OUT/digits_mlp/s05_t7_20261113` and the calibration/truncation files to
   `results/r1/tracks/digits_mlp/s05_t7_20261113/` (not the preserved TASL-2 path), write the report + STATUS, get
   a fresh independent review, then pause and report (L1). The S0.5 summary and STOP 4 still wait for `tabular_mlp`.
8. **If TASL-2 returns after the TASL-7 S0.5 starts**, do not switch host or resume the TASL-2 scene: perform a
   read-only census of TASL-2, keep both scenes, report, and let the author decide any change. The TASL-2 `s05`
   scene is never resumed or deleted by this move. If TASL-2 returns while the TASL-7 S0.1/S0.5 has not started, it is
   still only censused read-only and preserved.
9. **B1 `_d` has priority.** When the D-B1R for `_d` arrives (READY.txt item + origin branch), B1 takes precedence:
   build the new marker per its hand-off; Track S yields through the watcher (the watcher pauses on the new Track X
   marker) and resumes only under its own reviewed procedure after B1. The operator polls `Claude outputs/READY.txt`
   and origin every 30 minutes.

## 4. PLAN §10 row draft (for the author/coordinating session; target branch `trackS-ops-20261030`)

**Superseded draft — do not use.** The row that previously stood here (12 Nov, "B1 `_c` normal end + post-run
retirement only") is replaced by the 13 Nov revision in
`proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md` (STOP ending also allows the move via the accepted
STOP-case retirement unit; B1 `_d` priority; TASL-2 census-only). The revised row remains a draft for the
author/coordinating session; the operator does not commit it to `PLAN.md` unilaterally.

**Operator note.** The operator does not add author decisions to PLAN unilaterally; the row above is paste-ready for
the author/coordinating session or can be committed on the author's explicit relay instruction. Note that
`R1-TRACKS-A2U-STALE` lives on `mac-tracks-a2u-stale-20261111` (`f82ff376`, line 615) and
`R1-EXAM-HOST-B1B2-TASL7` on `docs/runbooks-11nov`; this row should be added next to the Track S rows on the branch
the coordinating session uses.

## 5. Post-run B1 `_c` marker retirement (separate unit; not Track S work)

The `_c` marker is `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe` (dev 66306, ino
56261618); its creation receipt is `$RUN_DIR/marker-receipt.json` (sha256
`e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`), not `f8c8624f…`. The hand-off defines the
`_b`→`_c` transition, not the `_c` retirement. For the STOP ending the author's 13 Nov exception is implemented by
`proposals/B1_C_STOP_MARKER_RETIREMENT_20261113.md` (accepted, executed 2026-11-13T10:49:31Z): the marker was renamed
into `~/r1_locks/_to_delete/trackx_evidence.active.040ffbe17da643a28264bbf90ccd88fe`, the creation receipt was kept,
retirement files `marker-retirement_stop.{json,rc,note,err}` were written, the `_c` STOP scene stayed byte-equal to
the accepted capture, and a fresh reviewer later confirmed the execution is safe and must not be unwound. Track S must
still wait for its own S0.1 gate (see §3).

## 6. Open items

- TASL-2 census when/if the host returns (read-only); the author decides any change; the scene is preserved.
- Track P resumption after B1/B2 is outside this proposal.
- The `digits_mlp` S0.1 on TASL-7 must run after the GPU is free; its reviewed result gates S0.5.
