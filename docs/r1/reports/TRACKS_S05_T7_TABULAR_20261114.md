# Track S — `tabular_mlp` S0.5 + S0.5b on TASL-7 (14–15 November 2026) — **STOP-4 submission (tabular half)**

**Written 15 Nov 2026 by the Track S operator agent (DSH experiment-agent session, Lead: experiment agent);
AI-assisted. ENGINEERING_ONLY.** Not a result. This records the `tabular_mlp` S0.5 pilot and S0.5b truncation
sweep on TASL-7 at paper pin `8237fd02`, at **k = 2** (the accepted S0.1 measurement), and is submitted for the
fresh STOP-4 review. **STOP 4 remains open for the Mac-side S0.5 summary** (and the digits per-node calibration
`fail`); nothing here is a result claim.

**Authority.** Track S operator runbook rev 3.3 Phase 4; the author's 14 Nov amendment **relayed by the Lead**
(14 Nov 23:11 CET: run Track S Phase 3 for `tabular_mlp` on TASL-7 then S0.5/S0.5b as for digits; ~23:2x CET: add
a tabular S0.1 re-run at k=2 after S0.4 and before S0.5, with k fixed by measurement) — **no separate author
artifact/verbatim quote/PLAN §10 row exists for these relays**; the accepted STOP-3 record
(`docs/r1/reviews/TRACKS_S04_T7_TABULAR_REVIEW_20261114.md`, sha `fbf0a874…`) and the accepted S0.1 record
(`docs/r1/reviews/TRACKS_S01_T7_TABULAR_REVIEW_20261114.md`, sha `d01fc724…`, **k = 2**) are cited. The
S0.4-then-S0.1-then-S0.5 order **deviates from the runbook Phase 1→3 order as instructed by the author**.

**Pins.** paper **`8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** (clean), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`, GGUF sha256
`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`. Launchers (committed `e33e1f6b`, repo==host,
`bash -n`): S0.5 `r1/tracks/ops/launch/tasl7_tabular_s05_20261114.sh` sha
**`61a3dd5fbb9381032c8d33c164ea0d07ffaa709be71a354853c05aa46203c7ea`**; S0.5b
`r1/tracks/ops/launch/tasl7_tabular_s05b_20261114.sh` sha `a9cf785c…`. Sessions **`trks_s05t_t7`** and
**`trks_s05bt_t7`**, deliberately distinct from the digits S0.5/S0.5b logs (digits evidence preserved).

## 1. S0.5 pilot (k = 2)

- Launcher start **2026-11-15T00:08:49Z**; k=2 servers in `trks_llm` (`trks-servers 2`, pids 832486/832487),
  endpoints 18101/18102 ready 00:08:51Z; lease HELD; **prior `out/tabular_mlp/s04_t7_20261114/a2u_prior.json`
  sha256 `ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f`** (the S0.4 A2-U prior, not the s01
  dir); collector `trks_s05t_t7`.
- Command (`.cmd` sha **`3cd5c643c273564dca0547c064127c1946ab26d72e9ad86a9d234f3f67d762b5`**):
  `--phase S0.5 --node tabular_mlp --prior <s04>/a2u_prior.json --prior-sha256 ba8f7783… --obs-inflation 1.0 --W 40
  --instances 20 --policy static:0.00057,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1
  --label ENGINEERING_ONLY --deadline 28800 --stop-file $RUN/STOP --out $RUN --work $WRUN` (new dirs
  `out|scratch/tabular_mlp/s05_t7_20261114`).
- **Exit `2026-11-15T02:38:52Z rc=0`**; manifest 1 session `20261115T000852Z–20261115T023851Z`
  **`done = {roots 50, forks 31, leaves 99, failed 0, exhausted 0, deadline_hit false, status "complete"}`**.
- `roots.jsonl` 50 (sha `5e082a58…`), `forks.jsonl` 31 (`b2c4ad5f…`), `leaves.jsonl` 99 (`ebae0c99…`),
  `audit_runs.jsonl` 1930 (`6f17837c…`), `s05_calibration.jsonl` 330 (`e05cd54a…`), `manifest.json` (`28e008f6…`).
  **No `failed_units.jsonl`; no STOP; `exhausted=0`; `deadline_hit=false`.**
- **≤2 % rule: 0 / (50 + 99 + 0) = 0.0 %.**
- Provenance (manifest): paper `8237fd02…`, harness `a3fedbb…`, GGUF `509287f7…`, llama `620d2225…`, host
  `TASL-7`, gpu `GPU-ab72fb4a-…`, `paper_dirty=false`, `harness_dirty=false`, label `ENGINEERING_ONLY`,
  `obs_inflation=1.0`, `g_declared=g0=0.00019`, `prior_sha256=ba8f7783…`, phase `S0.5`.

## 2. S0.5b truncation sweep (CPU, no servers)

- Servers stopped first (lease released; no llama-server/listener/compute). Launcher
  `tasl7_tabular_s05b_20261114.sh` ran **03:10:52→03:11:07Z**: `trks_s05bt_t7.exit` **`2026-11-15T03:10:53Z rc=0`**,
  "S0.5b DONE" 03:11:07Z; log `{"out": "$RUN", "truncated_audits": 200}`; `.cmd` sha `bdff166d…`.
- **`s05b_truncated.jsonl` 200 rows** (sha `615aa3909eaaece41c82d026d2e876847ae01b1bd765ca9cc16671943e34c3bb`);
  **`s05_calibration.jsonl` 330 rows**, last line valid; no refusal/nonzero; no STOP.

## 3. k = 2 basis

The accepted S0.1 re-run (`d01fc724…`) measured within-server identity **100 % on both URLs** (serial 18101
200/200; concurrent 18101 200/200, 18102 200/200) and **`cross_server_identity` 200/200 = 1.0000**, with
discriminating negative controls; **k = 2** by the Phase-1 rule. **The author's rule is explicit: any identity
<100 % in any required cell is a STOP for the author — no k=1 fallback/bypass** (recorded in the S0.4/S0.1
records and the S0.1 launcher header). This S0.5 ran with k = 2 servers as required by the S0.5 launcher (it
refuses a `trks_llm` whose live count ≠ 2).

## 4. Host end state (verified 03:10:44Z)

After stopping the phase's own `trks_llm`: lease **FREE**, 0 llama-server, no `trks_llm`, compute apps empty,
**0** listeners on 1810x, only `trks_watch`; no markers; **0 STOP** under `$R/out`; GPU idle (0 %, 243 MiB); disk
525 G free.

## 5. Copy-back (never TASL-2)

`results/r1/tracks/tabular_mlp/s05_t7_20261114/`: run tree (`roots.jsonl`, `forks.jsonl`, `leaves.jsonl`,
`audit_runs.jsonl`, `s05_calibration.jsonl`, `s05b_truncated.jsonl`, `manifest.json`), `host_logs/`
(`s05_t7_tabular_20261114_launch.log`, `trks_s05t_t7.{cmd,log,exit}`, `s05b_t7_tabular_20261114_launch.log`,
`trks_s05bt_t7.{cmd,log,exit}`, `watch.log`) and `operator_capture/` (`s05_waiter.log`). **`SHA256SUMS` verifies
17/17; host==copy verified for all 16 run-tree/log files.** TASL-2 is **down** (TCP timeout) and was not
touched; the TASL-2 bare-repo push remains deferred.

## 6. Governance / scope

- **Lead-relayed author amendment** (no separate author artifact): disclosed above; the S0.4-then-S0.1-then-S0.5
  order deviates from the runbook Phase 1→3 order as instructed. `k` was fixed by the S0.1 measurement (k=2).
- **§3.0b Track P integration check: OPEN** (not performed; Track P not ready/paused; no helper invocation; no
  author permission requested). Does not block STOP 4; gates Phase 6 / Phase 0.3(c) on TASL-7.
- B2 hand-off draft is **NOT ARMED**; no `trackx_evidence.active`. No B2/X.7/sweep 2. TASL-2 down/deferred.
- **Not self-accepted:** STOP-4 submission (tabular half) submitted for the fresh independent review. **STOP 4
  remains open for the Mac-side S0.5 summary** (W, σ_cmp,vary, σ_D UCL, between-rep UCL,
  `between_policy_sd_at_cap`, near band b, calibration status, λ), which must report the **digits per-node
  calibration `fail`** (strata outside [0.70, 0.90]) as well as the tabular rows; the digits-half acceptance was
  **not** a calibration-gate pass. This is **not** an S0.5-close/STOP-4-complete authorization and does not start
  Phase 4/S3.

## 7. Reviewer checklist

1. Pins/clean; launchers `61a3dd5f…`/`a9cf785c…` repo==host, `bash -n`; k=2 servers exactly 2 procs; prior
   `s04_t7_20261114/a2u_prior.json` sha `ba8f7783…`; `.cmd` sha `3cd5c643…`; new dirs only.
2. S0.5 exit `02:38:52Z rc=0`, manifest `50/31/99/0/0 complete`, `deadline_hit=false`; no `failed_units`/STOP;
   `roots 50, forks 31, leaves 99, audit 1930, calibration 330`; 2 % rule 0.0 %.
3. S0.5b `rc=0`, `truncated_audits 200`, `s05b_truncated.jsonl` 200 rows, `s05_calibration.jsonl` 330 valid.
4. k=2 evidence (accepted S0.1 `d01fc724…`; identity 100 % both URLs + cross 100 %); author STOP rule recorded;
   S0.5/S0.5b ran with k=2/S0.5b CPU.
5. Copy-back `SHA256SUMS` 17/17, host==copy 16/16; old scenes/digits logs untouched; host end state; TASL-2
   untouched.
6. Governance disclosures (§6): Lead-relayed amendment, §3.0b OPEN, B2 not armed, TASL-2 down, not self-accepted,
   STOP 4 still open for the Mac-side summary incl. the digits per-node calibration `fail`.
