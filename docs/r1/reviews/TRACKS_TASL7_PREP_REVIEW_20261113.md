# Independent review — Track S `digits_mlp` TASL-7 launch units and prep record (13 Nov 2026)

**Reviewer:** fresh independent reviewer; did not write the units or the record. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified. TASL-7 checks were read-only only
(`ls`/`stat`/`cat`/`sha256sum`/`git rev-parse`/`git status`/`cat-file`/`tmux ls`/`nvidia-smi`/`flock -n`/`pgrep`/`ps`/
`/proc/locks`); no script was executed, no signal or write was sent to the running B1 `_c` scene, and TASL-2 was not
contacted. This review executes nothing.

## Unit reviewed

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch **`trackS-ops-20261030`**, commit
  **`2e69cee81453ee92f19cc10e754a0dcc92f34087`** (parent **`d810e47b30d1a714bf39172ab0d4990d78fdf4f1`**).
- `git diff --name-status d810e47b 2e69cee8` lists **only four added files** (225 insertions, 0 deletions):
  `A docs/r1/reports/TRACKS_TASL7_PREP_20261113.md`,
  `A r1/tracks/ops/launch/tasl7_digits_s01_20261113.sh`,
  `A r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh`,
  `A r1/tracks/ops/launch/tasl7_digits_s05b_20261113.sh`.
- Exact digests (verified against the git blobs and against the digest block in the record):

```
f86ce11e948186c195a687c88d39862dfde3d78695f8d9c2f9ea09658fd740f2  r1/tracks/ops/launch/tasl7_digits_s01_20261113.sh
87c05587daed193dd127512c4c76f59abbdd3c10d4b0b64f47a0e5f2673b9067  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh
3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a  r1/tracks/ops/launch/tasl7_digits_s05b_20261113.sh
ba7737cadc353da6274811ba20c24cb029727c8d9114ad621a3ef9b9ecff8eb6  docs/r1/reports/TRACKS_TASL7_PREP_20261113.md
```
  The record's three launch-unit digests match byte-for-byte (blobs `66f726b5…`, `af6deb0c…`, `1db5a68a…`; mode
  `100755`). The record is blob `703bbc89…`, 60 lines.

## Reference texts used

- Track S operator runbook rev 3.3, docs commit `13badb0`, sha256
  `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53` — Phase 1, Phase 4 S0.5/S0.5b, §0.2 pins,
  §0.5 shards, §0.6 failures, §0.7 copy-back, §10 STOP table, §11.1–11.4 wrapper templates.
- Accepted TASL-2 equivalents on the same branch: `r1/tracks/ops/launch/tasl2_s01.sh` (blob `33bded64…`) and
  `r1/tracks/ops/launch/tasl2_s05_20261112.sh` (blob `57c4e18e…`, added by `25907343`). I also read the accepted
  9 Nov S0.1 rerun script (`tasl2_s01_rerun_20261109.sh`) as the most recent executed S0.1 procedure.
- `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` rev 2 (accepted; re-review `TRACKS_DIGITS_HOSTMOVE_REVIEW_R2_20261112.md`)
  and `docs/r1/reports/TRACKS_HOST_FACTS_20261030.md` §0.5/§0.9.
- Pinned code at `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`: `r1/tracks/collect.py`, `r1/tracks/probes/determinism.py`.

## 1. Fidelity — PASS

**S0.1** (`diff -u tasl2_s01.sh tasl7_digits_s01_20261113.sh`). Differences are host-specific and guard/log only:
header/authority, `OUT=$R/out/digits_mlp` unchanged, `S01=s01_t7_20261113`, new launch log
`$R/logs/s01_t7_20261113_launch.log`, added priority-marker guard, existing-output-dir guard, session-collision guard,
paper pin `8237fd02…` + clean-worktree guard, `trks_llm`-running guard, bounded 900 s readiness poll on **both**
`/v1/models`, and `log()` instead of `echo`. The probe calls are token-for-token identical to the accepted TASL-2
script (22 and 26 tokens; only `--out` changes `$OUT/s01$S01` → `$OUT/$S01`): serial `--url 18101 --mode serial
--n 200 --repeats 3 --order-seed 1 --proposal-schema manager_proposal/v1 --node digits_mlp --server-args "$S1"`;
concurrent adds `--url 18102 --mode concurrent --clients-per-url 2 --order-seed 2 --server-args "$S1 | $S2"`. Server
strings `S1`/`S2` are byte-identical to the TASL-2 ones and match the installed `trks-servers` invocation
(`-ngl 999 -c 8192 --parallel 1 --verbose --alias r1-manager --host 127.0.0.1 --port 1810[12]`).

**S0.5** (`diff -u tasl2_s05_20261112.sh tasl7_digits_s05_20261113.sh`). Only host-specific paths/dirs/sessions/log
names plus added guards: `RUN=$OUT/s05_t7_20261113`, `WRUN=$WORK/s05_t7_20261113`, `SESSION=trks_s05_t7`, LOG
`s05_t7_20261113_launch.log`, paper pin + clean guard, prior file + sha256 guard, empty-manifest guard. The collector
argument vector is **37/37 tokens identical** after substituting `$OUT/a2u_prior_r2_20261111.json`/`$PRIOR`,
`$OUT/s05/STOP`/`$RUN/STOP`, `$OUT/s05`/`$RUN`, `$WORK/s05`/`$WRUN`: `--phase S0.5 --node digits_mlp --prior <PRIOR>
--prior-sha256 5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607 --obs-inflation 1.0 --W 40
--instances 20 --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label
ENGINEERING_ONLY --deadline 28800 --stop-file <STOP> --out <RUN> --work <WRUN>`; k = 1 on 18101. No scientific
parameter is changed.

**S0.5b** (no TASL-2 launch counterpart; derived from rev-3.3 Phase 4 and the pinned code). `trks-run trks_s05b_t7 -
collect --phase S0.5b --node digits_mlp --truncate-W 8,10,12,20 --out $RUN --work $WRUN` — identical to the runbook
command modulo the new dirs, CPU phase (`-`, no `TRKS_PORT`/pins). I verified in the pin that `PHASES` contains
`S0.5b`, `--truncate-W` exists (dest `truncate_W`), `s05b_phase` is dispatched before manifest construction (so no
`--W` needed), reads `manifest["prior_path"]`, uses `manifest["work"]` and refuses a different `--work`, and appends
`s05b_truncated.jsonl`.

## 2. Wrapper correctness — PASS

Read-only on TASL-7: `bin/trks`, `bin/trks-run`, `bin/trks-servers`, `bin/trks-watch` are byte-identical to the
rev-3.3 §11.1–§11.4 templates except the two filled lines in `trks` (`HOST_LABEL=TASL-7`,
`GPU_ID=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; GGUF sha `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`,
llama build `620d2225cc436ab0b001e3200e590e3b286ef9ab`). `trks` injects the `PIN` array into `collect` for
`S0.4|S0.5|S3|tune|campaign` and `PROBE_PIN` into `probe`, and refuses user-passed injected flags; `S0.5b` falls to the
unpinned CPU path. `trks-run` requires a `trks_` session name, writes `$R/logs/<s>.cmd/.log/.exit`, exports
`TRKS_PORT` only for a numeric port, and uses `printf %q` so `--server-args "$S1 | $S2"` survives as one argument.
`trks-servers k` refuses the three priority markers, `exec flock -n ~/r1_locks/gpu0.lock`, starts ports `1810$i`, and
`wait`s so the lock lasts exactly as long as the servers. The scripts use `-` for probes and S0.5b, `18101` for the
S0.5 collector, and `"$S1 | $S2"` exactly as in the TASL-2 script.

## 3. Guards / fail-closed — PASS

- Priority markers (`~/r1_locks/trackx_evidence.active`, `~/r1_locks/trackp_evidence.active`, `$R/trks_drill.active`)
  refused by all three; session collisions (`trks_s01_serial/conc`, `trks_s05_t7`, `trks_s05b_t7`) refused; existing
  `$OUT/s01_t7_20261113` refused; existing `$RUN` refused unless a non-empty `manifest.json` makes it resumable.
- Paper pin `8237fd02…` and `git status --porcelain --untracked-files=all` empty on `$R/work/Agent_paper_B`; prior file
  present and `sha256sum` exactly `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`.
- S0.5 refuses a foreign GPU compute process and a held lease when `trks_llm` is not running; readiness is bounded at
  900 s (S0.1 both endpoints, S0.5 18101) with the server log tailed and exit 3. S0.5b refuses `trks_llm` and
  `llama-server .*--port 1810[12]`, requires a non-empty manifest, and requires
  `sessions[-1].done.status == "complete"` (I exercised the embedded gate against complete / interrupted / deadline /
  empty-sessions manifests: rc 0 only for complete, `REFUSE` for the other three). Both rc checks read the last
  `rc=` line from `$R/logs/<session>.exit` and exit nonzero on empty/mismatch. I also confirmed the `tmux … && { refuse; }`
  and `pgrep … && { refuse; }` forms do not trip `set -e` on the no-hit path.
- Writes are confined to `$OUT/digits_mlp`, `$WORK/digits_mlp`, `$R/logs` (launch logs, `trks-run`
  `.cmd/.log/.exit`, `llama_1810*.log`). No script contains `ssh`, `rsync`, `rm` or any TASL-2 path; the only TASL-2
  mentions are comments. The TASL-2 `s05` scene is never referenced as a target.

## 4. Plan record — PASS

The record's three digests match the three files above. Shared preconditions 1–5 are consistent with host-move
conditions 1–8: B1 `_c` normal end + accepted post-run marker retirement (the unit is
`proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`, accepted at rev 5 by `B1_C_POSTRUN_REVIEW_R5_20261112.md` and still
non-executable: RUNNING/lease held/marker present); paper `8237fd02` detached/clean from the TASL-7 bare
`mac-tracks-a2u-stale-20261111`; prior `5c849d15…`; new `s01_t7_20261113`/`s05_t7_20261113` dirs and
`trks_s05_t7`/`trks_s05b_t7` sessions; Track P paused, Track X untouched, TASL-2 preserved. The copy-back path is
**`results/r1/tracks/digits_mlp/s05_t7_20261113/`** (not the preserved TASL-2 `s05`), and the record says the S0.5
summary and STOP 4 wait for `tabular_mlp`. Precondition 4 makes the **S0.1 result** review gate S0.5. The STOP list
restates §10 and the host-move gates (identity < 100 %, k impossible, calibration twice, > 2 % failed units, exit 3
twice, A/A or fork-rebuild mismatch, marker = pause not failure, any pin/host/GPU/lease anomaly, any deviation from
the reviewed bytes, any TASL-2 request). The header and body say the record executes nothing; commit message says
"nothing executed".

## 5. Site readiness (read-only, 2026-11-13T00:02Z) — PASS

- `$R/work/Agent_paper_B` HEAD **`d10b05b738fc0e0dba54e0e692c248bedf095482`**, worktree clean, origin =
  `remotes/Agent_paper_B.git`; the clone has **no** `8237fd02` or `2e69cee8` object, so the pin/clean guards correctly
  refuse until fetch+detach. `$R/work/autoresearch_harness` HEAD **`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`**, clean.
- TASL-7 bare repo: `refs/heads/trackS-ops-20261030 = 2e69cee81453ee92f19cc10e754a0dcc92f34087`;
  `refs/heads/mac-tracks-a2u-stale-20261111 = c8b13b5d63d3d30f5afa642928f1458e863e8935`; `8237fd02` is an ancestor
  (YES).
- B1 `_c` **RUNNING**: tmux `b1_4b31_20261112_c`, `r1.scripts.exam_runner b1` pid 3736030, campaign pid 3890028;
  marker `~/r1_locks/trackx_evidence.active` = `{"head": "4b312844962e1106db04d5a60bf996fad0e3e514", "run_id":
  "4b31_20261112_c"}`; GPU compute app = B1 `llama-server` pid 3843862, 18010 MiB; `gpu0.lock` held by pid 3736030
  (`/proc/locks` FLOCK WRITE, dev 103:02 inode 56251186 = the lock file). The lease therefore frees when B1 exits.
- Track P absent (no `trackp_evidence.active`); `trks_drill.active` absent; only `trks_watch` and the B1 session run —
  no `trks_llm`/`trks_s01*`/`trks_s05*`. `$R/out/digits_mlp` and `$R/scratch/digits_mlp` do not exist; the prior is
  absent (expected); `$R/out` holds only `smoke/` and `tabular_mlp/`. Venv: Python 3.11.18, numpy 2.4.6, scipy 1.17.1,
  sklearn 1.9.1, pandas 3.1.0 (matches §0.5/rev-2). `launch/tasl7_s01.sh` is still `tabular_mlp` and sha
  `226dbfa2fd6ea1fc80bb97ed987da58bed38c854b72795ff06ff5826a430cbb7`; the three new units are not yet in `$R/launch`.

## 6. Risk check (k = 2 S0.1 vs k = 1 S0.5) — PASS, with a procedural residual

- If a **k = 1** `trks_llm` is left when S0.1 runs, S0.1 passes the session guard, then waits the full 900 s for 18102
  and exits 3 — fail-closed (no data, no wrong k; only wasted time, and an operator must not count this launch-script
  exit 3 as the collector's second exit 3).
- S0.5's "already running `trks_llm`" resume path checks only the session, not its k. A k = 2 session left by S0.1
  would therefore be reused for the k = 1 phase. This is **not material to the S0.5 data**: the collector is
  single-shard and talks only to 18101, so the phase remains a one-server measurement; the second server is idle
  (≈4–5 GB VRAM each on a 24 GB card, no compute contention). It is a procedural deviation from the runbook's
  "restart the servers with k = 1 for all later phases" (and the record says "unless one is already running"). An
  optional guard would be to refuse in the resume path if anything is listening on 18102, or to require an explicit
  k = 1 marker; the accepted TASL-2 script has the same resume path, so this is not a new defect of these bytes.

## 7. Post-run bookkeeping — PASS

The record's copy-back list (calibration/truncation JSONL, manifest, SHA256SUMS) to
`results/r1/tracks/digits_mlp/s05_t7_20261113/`, then report + STATUS, fresh independent review, L1 pause, and the
S0.5 summary/STOP 4 waiting for `tabular_mlp`, matches host-move condition 7 and the runbook §0.7/Phase 4.

## Residual notes (non-blocking; no change required for acceptance)

1. **S0.1 rerun after a partial failure.** The baseline TASL-2 script had `S01_SUFFIX` for a new-dir rerun; the TASL-7
   S0.1 hard-refuses an existing `$OUT/s01_t7_20261113` and has no override. If a priority marker appears mid-S0.1
   (the watcher kills the servers) the probe fails and the dir exists, so the same script cannot be re-run; the
   operator must move the partial dir aside and use a new reviewed dir/date. No data corruption or overwrite risk.
2. **S0.5 `mkdir $RUN` precedes the server start.** A failed server start (lease/marker) exits 3 after creating an
   empty `$RUN`, which the next run then refuses; `rmdir` or rename is needed. Same ordering as the accepted TASL-2
   script.
3. **S0.1 rc is not a scientific check.** The pinned `determinism.py` always returns 0; the script's rc check only
   proves the probe wrote its JSON. The 9 Nov accepted rerun script additionally asserted `errors == 0` and
   `cache_prompt is false` from the JSON; this script relies on the mandatory independent S0.1 result review (which
   reads identity/errors/latency before S0.5). A JSON assertion would make the script self-checking.
4. **Deployment step.** The three units are committed/reviewed but not yet under TASL-7 `$R/launch/`; runbook §0.1
   requires the scp and an installed-bytes check before `ssh tasl7 bash $R/launch/…`. The review covers the committed
   bytes only.
5. **Wrapper shas vs the 30 Oct host-facts table.** Installed `trks-servers` sha `124316b5…` and `trks-watch` sha
   `cf68843e…` differ from `TRACKS_HOST_FACTS_20261030` §0.9 (`47dcf336…`/`3108566d…`), because rev 3.3 mandates the
   re-install of both before Phase 3; the installed bytes match §11.3/§11.4 exactly, and `trks`/`trks-run` match the
   table. No action.
6. **Record notation.** The record uses `$OUT`/`$WORK` both for `$R/out`/`$R/scratch` (`$OUT/digits_mlp/…`) and for the
   node dirs (`$OUT/a2u_prior…`), mirroring the host-move record; the absolute paths in the scripts are unambiguous.
   It also lists `SHA256SUMS` as if it were inside `$RUN`; per §0.7 it is created on the Mac at copy-back.
7. **k-rule wording.** The record restates the runbook's Phase 1 default (2 if both identities 100 %, else 1 if serial
   100 %, else STOP) and does not mention the TASL-2 clause-(b) shorter-projection option cited in the S0.5 header; the
   S0.1 result review should record which rule it applies. S0.5 itself is k = 1 by design either way.

## Verdict

The three units implement the accepted host move faithfully: the probe and collector commands, flags, seeds, W,
instances, policy, obs-inflation, deadline and label are identical in substance to the accepted TASL-2 scripts and the
runbook; the only differences are the TASL-7 paths/dirs/sessions/log names and added fail-closed guards; the wrappers
are used correctly; the plan record's digests, preconditions, gates, copy-back path and STOP list are consistent with
the host-move record and the runbook; TASL-7 currently shows every expected precondition state. The residual items are
procedural/operational and do not change the bytes or the data.

VERDICT: accepted
