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
`trks_drill.active` all absent); no B1 process. **Old scenes preserved read-only and untouched** (full table; mtimes UTC; `inputs/` is an empty dir; the
`s01_rerun_INVALID…` scene is **31 Oct**, not Oct-30):

| path | bytes | mtime (Z) | sha256 |
|---|---|---|---|
| `out/tabular_mlp/s01/serial.json` | 10408 | 2026-10-30T10:20:21Z | `31d463c4a190cf2c9fd18ef77ccca452a3a49bb647fd35f66499423883bc54c8` |
| `out/tabular_mlp/s01/concurrent.json` | 17410 | 2026-10-30T10:46:36Z | `d65c4c815cd57715dfc805b57d176b447b4807d88b8d99aed561a1d051554328` |
| `out/tabular_mlp/s01_diag/cache_prompt.json` | 1119804 | 2026-10-30T11:48:28Z | `4407899844d3e2940d5fee3d283875580de460d334c5ae8076031f6910da613f` |
| `out/tabular_mlp/s01_diag_f1/cache_prompt_true_cold.json` | 596898 | 2026-10-31T01:27:54Z | `a08d45aea509749f3e06b9eb115dff60764eae92265f19efbaf90f83f1ffefc8` |
| `out/tabular_mlp/s01_diag_f2/plain_single_absent.json` | 596845 | 2026-10-31T01:34:34Z | `f6a196310e317b586f6688941e7b81ce5d100004cbef89972305ec3d2bd1428b` |
| `out/tabular_mlp/s11/tabular.json` | 9688 | 2026-10-30T10:52:39Z | `5ac5154bf5aca6cbe84a9ed3f901b383b38b04f6ccc0ae47826964da4ac90eaa` |
| `out/tabular_mlp/s01_rerun_INVALID…/serial.json` (31 Oct) | 5022 | 2026-10-31T11:20:50Z | `8ca4740e2631f14e0dbd200d516baa4b58d5ee7aa93f09bab6b8f86e2adfa63b` |
| `out/tabular_mlp/s01_rerun_INVALID…/concurrent.json` (31 Oct) | 6605 | 2026-10-31T11:21:28Z | `81b72cc58df8c28aed88ef62a13c928185fef0887d8c5aa81b1cfd2910148c8a` |
| `out/smoke/manifest.json` | 5340 | 2026-10-30T01:24:38Z | `4aa160b1ee39d0f912926a23b35db2d6c1392859b2d7148b2677635a99ebd1ad` |
| `out/smoke/roots.jsonl` | 13317 | 2026-10-30T01:24:38Z | `c6c8e65605ed373f7de73f8f9eda245e39683ef550dc9e05a0b66e96149f191e` |
| `out/smoke/s04_rows.jsonl` | 7114 | 2026-10-30T01:24:38Z | `619206ddaf1a34657f877ab8ea433216cf582bd94ea338ea38993a918b46750c` |
| `out/smoke/audit_runs.jsonl` | 14193 | 2026-10-30T01:24:38Z | `37798e383dbdfd9f2fef57a908155d4a68b7cbebd1ee128ebc84a2ddb632b9d9` |
| `out/smoke/failed_units.jsonl` | 217 | 2026-10-30T01:17:18Z | `a1d3548853bf97bd92518e8594b631a98c003367d24b148cfeb7f6a9625db9bb` |
| `out/smoke/failures/root__…s30000.json` | 3058 | 2026-10-30T01:17:18Z | `ff12d2238188ba16d502e56e7065cf0fb56dd73637b0fb1bd2e850aee2a6b797` |
| `out/tabular_mlp/inputs` | empty dir | 2026-10-30T10:13:46Z | — |
| `scratch/tabular_mlp/smoke/` | 30 files | 2026-10-30T00:56–01:20Z | byte-identical to committed copies (e.g. `root_trials.jsonl` `a161a3e7…`, `root_events.jsonl` `90006403…`, `node/train.py` `b29adf67…`) |

The **transient watcher STOP** was created and deleted in `out/tabular_mlp/s04_t7_20261114/`,
`out/digits_mlp/s05_t7_20261113/` and `out/smoke/` (all 0 B, sha `e3b0c442…`; recorded in
`host_logs/STOP_FILES.s04t_20261114T222237Z.txt` before deletion); the digits S0.5 scene's eight data files were
then re-verified byte-identical to its accepted copy-back — **no content file changed**.
**New dirs did not exist** (`out/tabular_mlp/s04_t7_20261114`, `scratch/tabular_mlp/s04_t7_20261114`).
Disk 526 G free (71 %). B2 hand-off draft on `origin/mac-b2-handoff-20261114` (tip `2120956c`) explicitly
**NOT ARMED**; no armed hand-off and no `trackx_evidence.active` present.

**§3.0b Track P integration check: OPEN** — not performed (Track P not ready/paused; no helper invocation; no
author permission requested). It does **not** block STOP 3; it gates Phase 6 / Phase 0.3(c) on TASL-7.

## 2. Phase 2 — S1.1 interaction check (`tabular_mlp`): existing record cited, no re-run

The 30 Oct S1.1 record `results/r1/tracks/tabular_mlp/s11/tabular.json` (sha256
**`5ac5154bf5aca6cbe84a9ed3f901b383b38b04f6ccc0ae47826964da4ac90eaa`**; host copy
`$R/out/tabular_mlp/s11/tabular.json` byte-identical; 30 seeds 37001–37030, `vary` split, `n = 30`,
ENGINEERING_ONLY) is cited as **pin-independent node-data analysis**, because the S1.1 code path is **identical**
between the pins under which it was produced (`9bb64ba` / harness `115df37`) and the current pins (`8237fd02` /
harness `a3fedbb`):

- `git diff 9bb64ba 8237fd02 -- r1/tracks/probes/s1_factorial.py` is **empty** (probe unchanged); its imports are
  stdlib + `numpy`/`scipy` only (`argparse`, `json`, `math`, `re`, `tempfile`, `pathlib`; `numpy`, `scipy.stats`)
  — no harness/LLM path.
- `r1/c3/audit.py` (`run_config`) and `r1/harness.py` are **unchanged**; `r1/c3/prior_model.py` changed
  (`d10b05b7`, cache_prompt on A4/manager-question queries) but is **not** on the S1.1 path (`run_config` imports
  only `r1.harness`, `autoresearch.manager.base.ManagerProposal`,
  `autoresearch.nodes.registry.load_registered_node`, `autoresearch.worker.local_worker.LocalWorker`).
- The harness `115df37→a3fedbb` diff is **LLM-only** (`control_plane/campaign.py` proposal-error logging, `llm/*`,
  `manager/langgraph_manager.py` + a test); the S1.1-path harness modules and the `tabular_mlp` node assets are
  unchanged; accepted `R1-CACHEPROMPT-FALSE` covers the cache_prompt change.

Interaction table (30 seeds 37001–37030, `vary`, `n = 30`):

| pair | levels | interaction | sd | se | t-95 % CI | bootstrap-95 % CI | main A | main B |
|---|---|---|---|---|---|---|---|---|
| HIDDEN_UNITS × BATCH_SIZE | 32/64 × 64/128 | **+0.002647** | 0.002386 | 0.000436 | [+0.001756, +0.003537] | [+0.001796, +0.003499] | +0.002412 | −0.004029 |
| HIDDEN_UNITS × LEARNING_RATE_INIT | 32/64 × 1e-3/0.002 | **−0.002659** | 0.002619 | 0.000478 | [−0.003637, −0.001681] | [−0.003634, −0.001701] | −0.000240 | −0.000151 |
| BATCH_SIZE × LEARNING_RATE_INIT | 64/128 × 1e-3/0.002 | **+0.004889** | 0.002250 | 0.000411 | [+0.004049, +0.005730] | [+0.004124, +0.005685] | −0.002908 | +0.003623 |

S1.1 is **descriptive and not a gate**; it is reported with the result and reviewed together with Phase 3. **No
re-run was made and no new `s11` directory was created.**

## 3. Launcher guards (the committed script)

No priority/drill marker; no pre-existing `trks_s04_t7` session; refuse an existing new `--out`/`--work` dir
without a resumable manifest; no foreign GPU compute when starting our server; lease free. The S0.4 launcher has **no HEAD/dirty guard**; the run's pin evidence is the manifest/roots
provenance (`paper_commit 8237fd02…`, `harness_commit a3fedbb…`, `paper_dirty=false`, `harness_dirty=false`) plus
the precondition `trks-status` check (`OK` on all four pins, 0 tracked paper modifications). `bin/trks`
(sha `26a240fa…`) only injects `PIN`/`PROBE_PIN` flags — it performs no `git rev-parse`/`git status`. Starts a fresh **k = 1**
server in tmux `trks_llm` (`trks-servers 1`) if absent, bounded 900 s readiness poll on
`127.0.0.1:18101/v1/models`, logs the server pid / GPU compute apps / lease, then
`trks-run trks_s04_t7 18101 collect --phase S0.4 --node tabular_mlp --instances 10 --label ENGINEERING_ONLY
--deadline 28800 --stop-file $NEW/STOP --out $NEW --work $NEWW`. The old tabular scenes are never read or written.

## 4. Run and the TASL-7 pause drill (previously open)

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

## 5. S0.4 completion

**Total 10 committed roots, 0 failed, 0 exhausted, deadline not hit.** Manifest `sessions=2`: #0
`20261114T221517Z–20261114T222226Z` `paused` done `2/0/0/0/0`; #1 `20261114T222350Z–20261114T224311Z`
**`complete`** done `8/0/0/0/0`. `roots.jsonl` 10 (sha `321fb1cf…`), `audit_runs.jsonl` 870
(`4601df1e…`), `s04_rows.jsonl` (`62b86291…`), `manifest.json` (`82ab48ff…`); **no `failed_units.jsonl`**, **no
STOP at the run**. Dry-run after exit: `roots_todo=0, forks_known=0, leaves_todo=0, exhausted=0` (exit `rc=0`,
`trks_s04t_dry.exit` `22:46:45Z rc=0`). **≤2 % rule: 0 / (10 + 0 + 0) = 0.0 %.**

## 6. liveness

`trks collect --phase liveness --node tabular_mlp --out $NEW` → **PASS** (`liveness/liveness.json`,
`liveness.md`), `n_trials=400`, evaluated 173, novel 164 = **0.948 ≥ 0.5**, `invalid_rate` **0.0225 < 0.3**,
`keep_after_trial_1 = 68`, no failed criteria, `inactive_key_rejections=0`.

## 7. fit_prior

`trks collect --phase fit_prior --node tabular_mlp --out $NEW --sigma-node 0.0019 --obs-inflation 1.0
--prior $NEW/a2u_prior.json` → prior **`s04_t7_20261114/a2u_prior.json`**, sha256
**`ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f`** (821 B); local `mu0` −0.0010202,
`tau0` 0.000285, `sigma_cmp` 0.0168430, `tau_w` 0.0252581. liveness and fit_prior were run **directly as CPU phases** (no tmux wrapper, hence no per-phase
invocation log); no fit_prior dry-run artifact is claimed or relied on (the only copied dry-run log is the S0.4 dry
run `host_logs/trks_s04t_dry.*`).

## 8. Host end state (verified 22:47Z)

After stopping the phase's own `trks_llm`: lease **FREE**, 0 llama-server, no `trks_llm`, compute apps empty,
0 listeners on 1810x, only `trks_watch`; no markers; **0 STOP under `$R/out`**; GPU idle; disk 526 G free.

## 9. k caveat (open author decision)

`tabular_mlp` has **no new-pin S0.1**: the only tabular S0.1 (Oct 30, old pin) failed its identity tiers
(0.870 serial / 0.875 cross), so **k was never set for tabular**. Per the Lead's instruction and the author's
STOP-1 decision (a) reading, this S0.4 ran **k = 1** (single 18101 server). The author's 14 Nov amendment now
requires a **`tabular_mlp` S0.1 re-run at k = 2** after this STOP-3 and before S0.5: serial + concurrent probes,
200×3, clients-per-url 2, order-seeds 1/2, `manager_proposal/v1`, new out dir `out/tabular_mlp/s01_t7_20261114`,
session names `trks_s01t_serial`/`trks_s01t_conc` (**deliberately distinct** from the digits S0.1's
`trks_s01_serial`/`trks_s01_conc`, whose log files are digits evidence). Its launcher `r1/tracks/ops/launch/tasl7_tabular_s01_20261114.sh` is committed (sha256
**`0f3d05befb05d7736e39fd9704906218371f1228b8f48a5450f9ab8e265fa520`**, superseding the unrun `ce0da8cd` with
the offsets-ordering / k=2-server-count clarifications) but **not run** (waits for STOP-3 acceptance).

**k=1 basis / amendment provenance (open question for the author).** The k=1 S0.4 and the S0.4-then-S0.1 order
rest on **the author's instructions relayed by the Lead**: (a) 14 Nov 23:11 CET — the Lead relayed the author's
instruction to run Track S Phase 3 for `tabular_mlp` on TASL-7, then S0.5/S0.5b as for digits, with the k=1 caveat
under the author's STOP-1 decision (a) reading; (b) 14 Nov ~23:2x CET — the Lead relayed the author's direct
answer adding a `tabular_mlp` S0.1 re-run at k=2 **after** S0.4 (and its drill/liveness/fit_prior) and **before**
S0.5, with k fixed by measurement. **There is no separate author artifact/verbatim quote/PLAN §10 row for these
relays** — they are operator/Lead transcription (the report itself is the only record). This order deviates from
the runbook's Phase 1→Phase 3 order **as instructed by the author**; **k remains unset** until the S0.1
measurement. S0.4 always runs a single collector process on one port (runbook one-process caveat), so the data
impact is limited to one server being used — that does not substitute for the S0.1 or for the author's order. **k rule:** k = 2 only if the review confirms identity **100 %** (within-server both URLs and
`cross_server_identity`); otherwise **STOP for the author — no k = 1 fallback/bypass**. No S0.5 until both the
STOP-3 review and the S0.1 review are accepted and k is fixed.

## 10. Copy-back (no TASL-2)

`results/r1/tracks/tabular_mlp/s04_t7_20261114/`: run tree (`roots.jsonl`, `s04_rows.jsonl`,
`audit_runs.jsonl`, `manifest.json`, `a2u_prior.json`, `liveness/`), `host_logs/`
(`s04_t7_tabular_20261114_launch.log`, `trks_s04_t7.{cmd,log,exit}`, `trks_s04t_dry.{cmd,log,exit}`,
`watch.log`, `STOP_FILES.s04t_20261114T222237Z.txt`) and `operator_capture/` (`drill_record.md`,
`waiter_s04t.log`). **`SHA256SUMS` verifies 20/20; host==copy verified for all 18 run-tree/log files.** TASL-2
is **down** (TCP timeout) and was not touched; the TASL-2 bare-repo push is deferred.

## 11. Scope / next

- This is the **tabular_mlp STOP-3 submission**. B2 hand-off is **NOT ARMED**; if it arms / a
  `trackx_evidence.active` marker appears, Track S yields and reports (no B2/X.7/sweep 2).
- Next, in the author's sequence (only after acceptance): (2) the `tabular_mlp` S0.1 re-run at k = 2 →
  report/review/k decision; (3) only after both accepted, S0.5 with the measured k, then S0.5b, copy-back,
  report/STATUS, fresh STOP-4 review, stop.
- **Not self-accepted:** submitted for the fresh STOP-3 review.

## 12. Reviewer checklist

1. Pins/clean/refusal guards; launcher commit `2ce10b8f` sha `2c1c1d52…` repo==host, `bash -n`; new dirs only.
2. Drill: marker 22:19:30Z → watcher 22:19:37Z; `rc=0`; `done.status=paused` (2 roots); servers stopped / lease
   released at 22:22:37Z (observed 22:22:57Z); no FORCED; STOP_FILES recorded (3) before deletion; marker gone
   22:23:37Z; resume 22:23:47Z; roots grew 2→3 with no duplicate `root_id`/`(instance,budget_index)`;
   `exhausted=0`; latency 3 m 07 s / 3 m 27 s.
3. S0.4: 10 roots, 0 failed, 0 exhausted, deadline not hit; dry-run 0/0/0; 2 % rule 0.0 %.
4. liveness PASS; fit_prior prior sha `ba8f7783…` (fit_prior run directly, no dry-run artifact claimed).
5. Copy-back `SHA256SUMS` 20/20 + host==copy 18/18; old scenes preserved; host end state; TASL-2 untouched.
6. k caveat and the S0.1 re-run queued (launcher sha `0f3d05be…`, not run; supersedes the unrun `ce0da8cd`); no k=1 fallback for S0.5.
7. B2 hand-off not armed / no `trackx_evidence.active`; no B2/X.7/sweep 2; TASL-2 down/deferred; STOP 3 open for the author.
8. Phase 2 (S1.1) cited: `s11/tabular.json` sha `5ac5154b…`, 30 seeds, interactions +0.002647 / −0.002659 / +0.004889 with t-95 % CIs, pin-independence argument; descriptive, **not a gate**.
