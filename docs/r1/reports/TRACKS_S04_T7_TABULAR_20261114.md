# Track S — Phase 3 `tabular_mlp` S0.4 + TASL-7 pause drill, 14 November 2026 — **STOP 3 submission**

**Written 14 Nov 2026 by the Track S operator agent (DSH experiment-agent session, Lead: experiment agent);
AI-assisted. ENGINEERING_ONLY.** Not a result. This records the `tabular_mlp` S0.4 dev campaigns at paper pin
`8237fd02` on TASL-7, the **TASL-7 pause drill** (runbook rev 3.3 §3.0/§199-203, previously open), liveness
and fit_prior, and is submitted for the fresh STOP-3 review. The author's 14 Nov amendment adds a `tabular_mlp`
**S0.1 re-run at k=2** after this STOP-3 and before S0.5; its launcher is committed but **not run yet** (waits
for STOP-3 acceptance). **No S0.5, no B2/X.7/sweep 2, no S0.1 run yet.**

**Authority.** Track S operator runbook rev 3.3 (docs commit `13badb0`, sha256 `a93fb84b…`) Phase 3; STOP-3
ruling §11 (author decision (a)); PLAN §10 `R1-TRACKS-A2U-STALE`; the Lead's 14 Nov Phase-3 instruction and
the author's S0.1 amendment (14 Nov ~23:2x CET). Unit: new committed launcher
`r1/tracks/ops/launch/tasl7_tabular_s04_20261114.sh` (commit **`2ce10b8f`**; repo == host sha
**`2c1c1d52ec7879c87d55c9bb71f541c0223cf09b97356ec2cd2333cc827536c7`**, `bash -n` OK), modeled on the
reviewed `tasl2_s04r2_20261111.sh`.

**Pins.** paper **`8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** (clean, 0 tracked modifications), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (clean), llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`
(`v0.7.0-dev` build 11669), GGUF sha256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`;
`trks-status` OK on all four. **k = 1** for this S0.4 (single 18101 server) — see the **k caveat §8**.

## 1. Preconditions (all fail-closed, verified read-only at 22:14Z)

Lease **FREE**; tmux only `trks_watch`; no `trks_llm`/collector; no llama-server; no GPU compute app; GPU idle
(0 %, 236 MiB); no priority/drill markers (`trackx_evidence.active`, `trackp_evidence.active`,
`trks_drill.active` all absent); no B1 process. **Old `tabular_mlp` scenes preserved read-only and untouched**:
`out/tabular_mlp/{inputs,s01,s01_diag,s01_diag_f1,s01_diag_f2,s01_rerun_INVALID_serial_raced_server_start_20261031T112132Z,s11}`
(key shas: `s01/serial.json` `31d463c4…`, `s01/concurrent.json` `d65c4c81…`, `s11/tabular.json` `5ac5154b…`).
**New dirs did not exist** (`out/tabular_mlp/s04_t7_20261114`, `scratch/tabular_mlp/s04_t7_20261114`).
Disk 526 G free (71 %). B2 hand-off draft on `origin/mac-b2-handoff-20261114` (tip `2120956c`) explicitly
**NOT ARMED**; no armed hand-off and no `trackx_evidence.active` present.

## 2. Launcher guards (the committed script)

No priority/drill marker; no pre-existing `trks_s04_t7` session; refuse an existing new `--out`/`--work` dir
without a resumable manifest; no foreign GPU compute when starting our server; lease free; paper pin/dirty
check only via the runbook (the launcher's own pin check is the `trks` wrapper). Starts a fresh **k = 1**
server in tmux `trks_llm` (`trks-servers 1`) if absent, bounded 900 s readiness poll on
`127.0.0.1:18101/v1/models`, logs the server pid / GPU compute apps / lease, then
`trks-run trks_s04_t7 18101 collect --phase S0.4 --node tabular_mlp --instances 10 --label ENGINEERING_ONLY
--deadline 28800 --stop-file $NEW/STOP --out $NEW --work $NEWW`. The old tabular scenes are never read or written.

## 3. Run and the TASL-7 pause drill (previously open)

| Time (UTC) | Event |
|---|---|
| 22:15:15Z | launcher start; fresh k=1 server pid **800412**; 18101 ready 22:15:17Z; collector `trks_s04_t7` started |
| 22:19:16Z | **first committed root** (drill precondition ≥1 root met) |
| 22:19:30Z | **`touch $R/trks_drill.active`** (drill marker) |
| 22:19:37Z | watcher `priority marker seen (…/trks_drill.active): pausing` (**7 s**) |
| 22:22:26Z | collector `trks_s04_t7` exit **`rc=0`**; manifest `done {roots 2, forks 0, leaves 0, failed 0, exhausted 0, deadline_hit false, status **paused**}` |
| 22:22:37Z | watcher `servers stopped; lease released`; observed lease **FREE**, 0 llama-server, no `trks_llm`, no listener at **22:22:57Z** (≈20 s graceful shutdown); compute apps empty; **no `FORCED`** line |
| — | **pause latency:** marker → watcher "servers stopped" = **3 m 07 s**; marker → observed lease-free = **3 m 27 s** |
| 22:22:37Z | **watcher-created STOP files recorded before deletion** in `$R/logs/STOP_FILES.s04t_20261114T222237Z.txt` (3, all 0 B sha `e3b0c442…`): `out/digits_mlp/s05_t7_20261113/STOP` (inode 57049062), `out/smoke/STOP` (inode 57048195), `out/tabular_mlp/s04_t7_20261114/STOP` (inode 57305747) |
| 22:23:09Z | marker removed; watcher `marker gone` at 22:23:37Z; the 3 STOPs deleted (0 remaining) — this also removes the drill STOP from the digits s05 scene, restoring its post-retirement state; old tabular scenes untouched |
| 22:23:47Z | resume via the same launcher: fresh k=1 server pid **803220**, 18101 ready 22:23:49Z, collector `trks_s04_t7` restarted |
| 22:26:13Z | roots grew 2 → 3; **no duplicate `root_id`** (3 distinct); **no duplicate `(instance, budget_index)`** in `s04_rows.jsonl` (54 rows); `exhausted=0` |
| 22:43:11Z | collector exit **`rc=0`**, manifest session #1 **`status=complete`** |

**Drill verdict: PASS** — pause marker honoured within 7 s (≤~1 min), `rc=0` with `done.status=paused`, servers
stopped and lease released, **no FORCED**, resume grew the roots with no duplicates and `exhausted=0`, pause
latency recorded. The only nuance is the ~20 s graceful server shutdown after the watcher's "stopped" line.

## 4. S0.4 completion

**Total 10 committed roots, 0 failed, 0 exhausted, deadline not hit.** Manifest `sessions=2`: #0
`20261114T221517Z–20261114T222226Z` `paused` done `2/0/0/0/0`; #1 `20261114T222350Z–20261114T224311Z`
**`complete`** done `8/0/0/0/0`. `roots.jsonl` 10 (sha `321fb1cf…`), `audit_runs.jsonl` 870
(`4601df1e…`), `s04_rows.jsonl` (`62b86291…`), `manifest.json` (`82ab48ff…`); **no `failed_units.jsonl`**, **no
STOP at the run**. Dry-run after exit: `roots_todo=0, forks_known=0, leaves_todo=0, exhausted=0` (exit `rc=0`,
`trks_s04t_dry.exit` `22:46:45Z rc=0`). **≤2 % rule: 0 / (10 + 0 + 0) = 0.0 %.**

## 5. liveness

`trks collect --phase liveness --node tabular_mlp --out $NEW` → **PASS** (`liveness/liveness.json`,
`liveness.md`), `n_trials=400`, evaluated 173, novel 164 = **0.948 ≥ 0.5**, `invalid_rate` **0.0225 < 0.3**,
`keep_after_trial_1 = 68`, no failed criteria, `inactive_key_rejections=0`.

## 6. fit_prior

`trks collect --phase fit_prior --node tabular_mlp --out $NEW --sigma-node 0.0019 --obs-inflation 1.0
--prior $NEW/a2u_prior.json` → prior **`s04_t7_20261114/a2u_prior.json`**, sha256
**`ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f`** (821 B); local `mu0` −0.0010202,
`tau0` 0.000285, `sigma_cmp` 0.0168430, `tau_w` 0.0252581. (Dry-run exit `rc=0`.)

## 7. Host end state (verified 22:47Z)

After stopping the phase's own `trks_llm`: lease **FREE**, 0 llama-server, no `trks_llm`, compute apps empty,
0 listeners on 1810x, only `trks_watch`; no markers; **0 STOP under `$R/out`**; GPU idle; disk 526 G free.

## 8. k caveat (open author decision)

`tabular_mlp` has **no new-pin S0.1**: the only tabular S0.1 (Oct 30, old pin) failed its identity tiers
(0.870 serial / 0.875 cross), so **k was never set for tabular**. Per the Lead's instruction and the author's
STOP-1 decision (a) reading, this S0.4 ran **k = 1** (single 18101 server). The author's 14 Nov amendment now
requires a **`tabular_mlp` S0.1 re-run at k = 2** after this STOP-3 and before S0.5: serial + concurrent probes,
200×3, clients-per-url 2, order-seeds 1/2, `manager_proposal/v1`, new out dir `out/tabular_mlp/s01_t7_20261114`,
session names `trks_s01t_serial`/`trks_s01t_conc` (**deliberately distinct** from the digits S0.1's
`trks_s01_serial`/`trks_s01_conc`, whose log files are digits evidence). Its launcher
`r1/tracks/ops/launch/tasl7_tabular_s01_20261114.sh` is committed (**`ce0da8cd`**) but **not run** (waits for
STOP-3 acceptance). **k rule:** k = 2 only if the review confirms identity **100 %** (within-server both URLs and
`cross_server_identity`); otherwise **STOP for the author — no k = 1 fallback/bypass**. No S0.5 until both the
STOP-3 review and the S0.1 review are accepted and k is fixed.

## 9. Copy-back (no TASL-2)

`results/r1/tracks/tabular_mlp/s04_t7_20261114/`: run tree (`roots.jsonl`, `s04_rows.jsonl`,
`audit_runs.jsonl`, `manifest.json`, `a2u_prior.json`, `liveness/`), `host_logs/`
(`s04_t7_tabular_20261114_launch.log`, `trks_s04_t7.{cmd,log,exit}`, `trks_s04t_dry.{cmd,log,exit}`,
`watch.log`, `STOP_FILES.s04t_20261114T222237Z.txt`) and `operator_capture/` (`drill_record.md`,
`waiter_s04t.log`). **`SHA256SUMS` verifies 20/20; host==copy verified for all 18 run-tree/log files.** TASL-2
is **down** (TCP timeout) and was not touched; the TASL-2 bare-repo push is deferred.

## 10. Scope / next

- This is the **tabular_mlp STOP-3 submission**. B2 hand-off is **NOT ARMED**; if it arms / a
  `trackx_evidence.active` marker appears, Track S yields and reports (no B2/X.7/sweep 2).
- Next, in the author's sequence (only after acceptance): (2) the `tabular_mlp` S0.1 re-run at k = 2 →
  report/review/k decision; (3) only after both accepted, S0.5 with the measured k, then S0.5b, copy-back,
  report/STATUS, fresh STOP-4 review, stop.
- **Not self-accepted:** submitted for the fresh STOP-3 review.

## 11. Reviewer checklist

1. Pins/clean/refusal guards; launcher commit `2ce10b8f` sha `2c1c1d52…` repo==host, `bash -n`; new dirs only.
2. Drill: marker 22:19:30Z → watcher 22:19:37Z; `rc=0`; `done.status=paused` (2 roots); servers stopped / lease
   released at 22:22:37Z (observed 22:22:57Z); no FORCED; STOP_FILES recorded (3) before deletion; marker gone
   22:23:37Z; resume 22:23:47Z; roots grew 2→3 with no duplicate `root_id`/`(instance,budget_index)`;
   `exhausted=0`; latency 3 m 07 s / 3 m 27 s.
3. S0.4: 10 roots, 0 failed, 0 exhausted, deadline not hit; dry-run 0/0/0; 2 % rule 0.0 %.
4. liveness PASS; fit_prior prior sha `ba8f7783…` and dry-run.
5. Copy-back `SHA256SUMS` 20/20 + host==copy 18/18; old scenes preserved; host end state; TASL-2 untouched.
6. k caveat and the S0.1 re-run queued (launcher `ce0da8cd`, not run); no k=1 fallback for S0.5.
7. B2 hand-off not armed / no `trackx_evidence.active`; no B2/X.7/sweep 2; TASL-2 down/deferred; STOP 3 open for the author.
