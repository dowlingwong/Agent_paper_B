# Review: Track S operator runbook and authorization draft (30 Oct 2026)

Independent reviewer (Claude), read-only. I checked `prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` (cited as L#) and `proposals/AUTH_DRAFT_trackS_20261030.md` (A#) against the design, PLAN §10, the host reports and the code (paper `835efcf`, harness `115df37`).
- I ran every CLI's `--help` and read the collector, analysis and simulator code.
- I tested the flock/tmux pattern in a scratch directory.
- Tests: all 151 paper tests pass (7 min), and the 14 harness tests are collected. Both counts match the runbook.

**Verdict: REVISE.** The phase order, labels and gates are right. But five steps fail or silently produce wrong data, and the parallel model cannot be run with the current code.

## BLOCKING

**B1. The GPU lease is not held (L45).** `flock -n lock tmux new -d …` locks only the tmux client, which exits at once. I tested this:
- If a `dowling` tmux server already exists (likely, since Track X and Track P use tmux), the lock is released immediately while the servers keep running.
- If flock starts the tmux server itself, the lock is held for as long as any `dowling` tmux session exists.

Fix: `tmux new -d -s trks_llm "exec flock -n ~/r1_locks/gpu0.lock bash start_servers.sh"`, where the script starts both servers and then `wait`s.

**B2. "2 servers × 2 campaigns" is not implementable as written (L131).** The collector is one serial process with one `LLAMACPP_BASE_URL`. It has no `--url`, no sharding, and a shared `--out` would race. Pin all of the following:
- one process per (server, slot), each with its own `--out` and instance range (`--seed-base`/`--instances`);
- a fixed instance→server map across S0.7 and S3e, or require 100 % identity *across servers* in S0.1(b). L136 covers only identity across hosts.
- the exact-placebo shard runs alone, to completion, before any other S3e shard (design §3);
- `assemble` merges the shards.

**B3. S0.5 and S0.5b (L173–178).**
- `--W` is required outside S0.4; add `--W 40`.
- The second call, with the same `--out` and a changed `llm_reps`/`rep_instances`, is refused. Use one call: `--policy "static:<0.3σ>,0" --rep 0 --rep 1 --rep-instances 10`. This is the tested form.
- S0.5b reads `<work>/roots/*/root_trials.jsonl`. With a different `--work` it silently audits the **start configuration**. Pin the S0.5 `--work` and never clean it.
- Use `--forks 1.5` for about 30 forks; 2 gives about 40. State 0.3σ explicitly: 0.00198 for digits, 0.00057 for tabular.

**B4. S3a and π′ (L272–276).**
- With no `--instances`, the run makes 1 root, which yields at most about 40 forks, not 150.
- `--near-band`/`--p-near` default to off, which silently drops the design §6 oversample.
- `--a2-fraction` defaults to 0.2 and adds descriptive A2 roots the design does not have.
- `--policy-out` is a **directory**. It receives `<node>.pi_prime.json`, and then `analyze analyze` exits 2 ("decision node has no S3e campaign result").
- Pin the roots × forks, b, p_near and `a2_fraction`. Document the exit-2 behaviour or add a `fit-policy` subcommand. Fix L286's path.

**B5. The obs-inflation revision is not carried forward (L199).** A new λ changes A2-U's decisions, so S0.5 needs a new `--out`. Every later tune, S3 and campaign command then needs `--obs-inflation λ`; otherwise those commands silently run at λ = 1. The code requires λ ≥ 1. Declare the rule for choosing λ.

## MAJOR

**M1. The flags written as "as above" (L176, L227, L238, L273, L284).** `--manager` defaults to `scripted`. If the manager flags are left out, the command runs **without the LLM** and still gets an EVIDENCE label.
- Give one verbatim flag block for every LLM command: manager/model/schema, GGUF and its sha, build, binary, `--host-label TASL-2|TASL-7`, `--gpu`, prior and its sha, `--W`, `--obs-inflation`, `--work`.
- Pin `LLAMACPP_BASE_URL=http://127.0.0.1:<port>/v1` (L115).

**M2. Failures and pre-emption (L47, L301).**
- The collector has no circuit breaker. If a server dies, every remaining unit fails, and with retries = 2 all units are exhausted after three sessions.
- Run bounded `--deadline` sessions, check `/health` before each one, and stop on a burst of transport errors.
- On pre-emption, stop the collectors before the servers.
- Poll the Track X marker between sessions; a daily check (L301) is too slow.
- TASL-7 has no Track P marker, so L43 cannot be applied. Ask the author for a request marker or for fixed windows.

**M3. The g-extension (L232).** With the same `--out` it is refused. With a new `--out` it re-runs all 18 statics, about 12k extra calls. Run only `select`'s `extension_configs`: three `--policy` entries with `--instances 20`. For `--centres-from`, use the assembled `dev_roots.jsonl`.

**M4. S0.6 inputs and outputs (L210, L245, L310).**
- `--between-policy-sd` must be taken at W = cap (untruncated roots).
- `--dev-between-sd` is the mean pairwise sd over the static grid.
- Neither number is printed by `s05-summary` or `select`.
- `--controls` takes one file, but the simulator writes one per node. Specify how to merge them.
- The FIXTURE controls lower `decision.label` to **FIXTURE** (`combine_labels`).
- Decide these points before S0.8, when the sha256 of `analyze.py` is frozen.

**M5. Provenance (L7, L70–73, L92).**
- The bundle name does not match R1-REPO-ACCESS.
- The "recorded docs head" is never given.
- `835efcf` contains no Track S documents and no PLAN rows, so merge the docs branch into the ops worktree.
- The design file's header says **rev 7.3**, not 7.4.
- Check out the hosts detached at the accepted code commit, because provenance records `HEAD`.
- Freeze the venv after Phase 0.

**M6. The copy list (L62).** The Mac-side steps also need `s05_calibration.jsonl`, `s05b_truncated.jsonl`, `forks.jsonl`, `failed_units.jsonl`, `s04_rows.jsonl` and `a2u_prior.json`. Without the first two, the calibration is silently reported as "insufficient". `assemble` cannot read a gzipped file.

**M7. Design §10 STOPs.**
- D28 liveness is never checked; state it on S0.4.
- The rebuild and A/A STOPs are missing for S0.5, which also has forks.
- Phase 5 has no STOP or review.
- State that any collector `Stop` exit is a STOP.

**M8. Pre-declaration template (L243, L251).** `select` needs a valid v4 file already in Phase 6. Give:
- the parser's field names (`primary_nodes`, `fallback_active`, `nodes.*.{role, sigma_node, delta_Y, sigma_cmp_vary, g_declared, sizing.sigma_D_ucl_s05b}`, `tuning.n_dev`, `analysis_script_sha256`);
- the collection settings: λ, b, the roots and forks, the shard map.

The code fits π′ with a fixed `ridge_alpha`, not "λ by inner CV". Declare what the code does.

## MINOR

1. **Build (L105).**
   - Use `-DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.2/bin/nvcc`; `nvcc` is not on PATH on either host. Add `Release` and `--target llama-server`.
   - Deepthought needed `-include iomanip`.
   - Pin by commit, not by the build number (L35).
   - Pin the GGUF revision `13fb94bf…`, its file name and its size.
   - Add `--verbose` so the offload line appears.
2. TASL-2 has Python 3.10 with no ensurepip and no uv. Pin a user-level install of uv and Python 3.11 (L96).
3. Pin `OMP/OPENBLAS/MKL_NUM_THREADS=1`.
4. `--url` is repeatable; remove the hedge at L128.
5. "Other members" means the best member of each other channel, two campaigns. `--instances 30` with the default seed base already gives the first 30 S3e instances (L290).
6. TASL-7 has GitHub credentials and a pending reboot. The S0.6 outputs are labelled FIXTURE (L49).
7. State the fallback projection formula; the author confirms it (L201).

## Authorization draft

- **A16:** cite the design by commit and sha256.
- **A19–23:** give full hashes, the GGUF file and revision, the runbook commit, λ, b, the roots and forks, and the π′ sha256.
- **A25:** replace "voids nothing" with: a STOP deletes nothing, design §10 decides voidness, and resuming after an EVIDENCE STOP needs the author. A pause is not a STOP.

## Re-check (revision 2)

Same reviewer, read-only. I checked runbook revision 2 (cited as R#), the revised authorization draft and paper commit `9bb64ba` against every CLI's `--help`. I ran the §11.1 wrapper and the §11.2 lock script, extracted verbatim from the runbook, in a scratch directory with a stub `python` and stub servers. Tests: the full paper suite passes, 168 tests in 7 min, as R137 states. That includes the 17 tests of the new `test_tracks_ops.py`.

### Original findings

| # | Status | Evidence |
|---|---|---|
| B1 lease | **resolved** | Tested under tmux with a **pre-existing tmux server**: the lock is held while the servers run; a second `trks-servers` start exits 1; `tmux kill-session -t trks_llm` kills both servers and frees the lock |
| B2 parallelism | **partly** | `--shard` (index mod k, the same in every phase), `--exact-placebo-only` and the shard checks in `assemble` all work. But see N2 and N3 |
| B3 S0.5/S0.5b | **resolved** | One S0.5 call with `--W 40` and the correct `--rep` flags. `--work` is recorded, and S0.5b refuses a different or empty one |
| B4 S3a/π′ | **resolved** | `--instances 30 --forks 4 --near-band --p-near 0.5`; `--a2-fraction` defaults to 0; `analyze fit-policy` runs without S3e data and does the ridge CV |
| B5 λ | **resolved** (MINOR N6, N7) | `fit_prior`/`set_obs_inflation` record λ in the prior. S0.5b, S3, tune and campaign refuse a different `--obs-inflation`. The re-run uses a new out-dir |
| M1 flags | **partly** | The code now requires `--manager` and refuses EVIDENCE without the pins. But the wrapper that injects the pins breaks every LLM call (N1) |
| M2 failures and priority | **partly** | Health check, exit 3 and `--stop-file` work (tests pass), and the Track P marker is an author item. The watcher has gaps (N4) |
| M3 | **resolved** | `--tune-g-extension-only` (MINOR N9) |
| M4 | **resolved** | `between_policy_sd_at_cap` and `dev_between_sd` are printed; `--controls` is repeatable; the decision label comes from S3e alone and `controls_label` is reported separately |
| M5 | **resolved** (MINOR N12) | Bundle and PLAN R1-REPO-ACCESS now agree; the design header says 7.4; checkouts are detached; the venv is frozen |
| M6 | **resolved** | The whole `<OUT>` trees are copied back; `.jsonl.gz` files are read |
| M7 | **resolved** | `--phase liveness` (exit 3), the S0.5 STOPs, and STOP 5 |
| M8 | **resolved** | `predecl-template`; `select` accepts a draft; `analyze`/`fit-policy` refuse one |
| Minors | **resolved**, except: the harness's public clone on TASL-2 is still unverified (R128; fall back to the bare-repo push) |

### New issues

**BLOCKING**

- **N1. The wrapper's pin flags break every LLM `collect` call (§11.1, R400).** `PIN="… --gpu 'NVIDIA GeForce RTX 4090'"` is expanded unquoted as `$PIN`. The single quotes therefore stay literal and the value splits into four words: `['NVIDIA] [GeForce] [RTX] [4090']`. I verified this with the template text. argparse then fails with `unrecognized arguments: GeForce …`. The smoke test, S0.4, S0.5, tune, S3 and campaign all fail. **Fix:** make the pins a bash array, `PIN=(--manager llamacpp … --gpu "NVIDIA GeForce RTX 4090")`, and expand it as `"${PIN[@]}"`. Alternatively, use the GPU UUID, which has no spaces. Do the same for the `probe` branch.
- **N2. The S3e flag variable passes literal quotes (R325–331).** `S3E="… --policy '<π*>' …"` expanded as `$S3E` gives the argument `'static:…'` with the quote characters included. I verified this: the collector reports `unknown or unimplemented policy "'static:0.001,0'"`. Every EVIDENCE S3e command fails at launch, and an operator might improvise a fix. **Fix:** use a bash array, `S3E=(--W <W> --instances 300 --policy "<π*>" …)`, expanded as `"${S3E[@]}"`.

**MAJOR**

- **N3. With k = 2, the exact placebo breaks "one instance, one server" (R72, R327).** `--exact-placebo-only` runs m\* at rep 0 on instances 0–9 on port 18101. The shards exclude those units. So for instances 1, 3, 5, 7 and 9, the primary pair D = Y(π\*) − Y(m\*) compares π\* run on 18102 (shard 1) with m\* run on 18101. R72 says identity across servers is not required, so these 5 of 300 pairs rest on an untested assumption. **Fix:** either require 100 % identity *across servers* in S0.1(b) before choosing k = 2 (the probe already reports it), or let the code accept `--exact-placebo-only --shard i/k`, so that each server runs its own placebo instances first.
- **N4. The watcher may silently not pause (§11.3, R65).**
  - It searches only `$R/work/out`, but the runbook never defines `<OUT>` or `<WORK>`. Fix them in §0, for example `OUT=/home/dowling/r1_tracks/work/out` and `WORK=/home/dowling/r1_tracks/work/scratch`.
  - `-newer logs/watch_started` skips a collector that was already running when the watcher was (re)started. Touch `STOP` in every out-dir whose manifest status is running, or drop `-newer`. Stray `STOP` files are removed before resuming anyway.
  - The watcher waits for the `trks_*` tmux sessions to end. That only happens if each collector is the session's command (`tmux new -d -s trks_<phase>_s<i> "TRKS_PORT=… trks collect …"`), not if it runs inside an interactive shell. State this; otherwise the watcher waits forever and the servers keep the card.

**MINOR**

- **N5.** The `set_obs_inflation` command at R240 omits `--out`, which argparse requires (verified). Add `--out <OUT>/s05`.
- **N6.** The §11.5 snippet uses field names that do not exist. `s05_calibration.jsonl` has `mu`, `sd` (which already includes the audit se) and `delta_audit`, which can be `null`; skip those rows. Also note that λ ≥ 1 cannot change the stratum-0 intervals and cannot narrow coverage that is too high. A failure of either kind therefore ends in the STOP, which is acceptable.
- **N7.** S0.5 is not in `LATER_PHASES`, so an S0.5 re-run with `a2u_prior_l2.json` but a forgotten `--obs-inflation λ₂` is not refused. Add S0.5 to the check.
- **N8.** The smoke test (R157) has no `TRKS_PORT=18101`, so the wrapper aborts.
- **N9.** In the member stage (R280), `--centres-from <ND>/dev_roots.jsonl` is a Mac path. Copy the file to the host first.
- **N10.** Under `pipefail`, the wrapper exits 1 with no message for `--phase=X` and for `trks collect assemble`. State that only the `--phase X` form may be used, or print a message.
- **N11.** The fallback at R244 counts S0.7 + S3a + S3e. Design §2 S0.5b counts S0.7 + S3e. Align them, or record this as a declared, stricter choice.
- **N12.** R106 says to verify "the docs head recorded in PLAN R1-REPO-ACCESS", but that row records no docs commit. Record the head in STATUS or with the bundle. Design §11 has no entry for 7.3 → 7.4.

### Authorization draft

**Resolved.** It now has the design commit and sha256, the runbook commit, the full pins, the GGUF revision and file, λ, b, p_near, the S3a roots and forks, the π′ sha256, k, and the corrected STOP and pause wording. The only addition I suggest is to state the exact-placebo server rule (N3).

### Verdict

The lease, sharding, code-side guards and analysis plumbing are now correct. Two fail-loud quoting bugs (N1, N2) mean the runbook as written cannot launch any LLM phase or any S3e phase. N3 and N4 affect pairing and Track X/P priority. Fixing N1–N4 is a small edit.

**not accepted**

## Re-check (revision 3)

Same reviewer. Revision 3 changes only the runbook (cited as R3:#); the code is still paper `9bb64ba`. I copied §11.1–11.4 verbatim from the runbook into a scratch tree and re-tested them, changing only the paths. I used a stub `python` (a fake collector that honours `--stop-file`), stub servers (`sleep`) and a tmux server that **was already running**. I also ran a real `collect --phase S0.4 --dry-run` with the full pin set.

| # | Status | Evidence |
|---|---|---|
| N1 wrapper word-splitting | **resolved** | The pins are an array and the GPU is identified by UUID, with no spaces. All 18 pin tokens arrive intact, and a value containing a space stays one argument. The real collector accepts the full pin set (dry run OK). A hand-passed `--gpu` or `--host-label=` is refused (exit 2), and so is a run with no `TRKS_PORT`. `--phase=tune`, `collect assemble`, `liveness` and `probe` behave correctly |
| N2 literal quotes | **resolved** | `S3E`/`SEC` are bash arrays expanded as `"${…[@]}"`, and policy strings are unquoted. `trks-run` writes the command with `printf %q`; I checked the `.cmd` file and `static:0.1,0` arrives as one argument. Because the session environment comes from the tmux server, `TRKS_PORT` is set inside `.cmd`, which is the right choice |
| N3 cross-server pairing | **resolved** | k = 2 now also requires `cross_server_identity` = 1.0, a field the probe writes (`determinism.py`:314). The rule is stated in §0.5 and Phase 1 |
| N4 watcher | **resolved** | `OUT`, `WORK` and `IN` are defined. End-to-end test: a marker appears → `STOP` is touched in every manifest directory, including one created before the watcher started → the collector pauses ("status paused", rc=0 in `.exit`) → `trks_llm` is killed → the lock is free → `trks-servers` refuses to start while the marker exists (rc=1). `trks-run` refuses a duplicate session (rc=1) and a name without the `trks_` prefix (rc=2). The 1 h forced path was checked by reading the code |
| N5–N12 (minors) | **resolved** | `--out` added to `set_obs_inflation`; the snippet uses `mu`/`sd` and skips null values; the over-coverage and stratum-0 STOPs are correct, since stratum-0 intervals come from the prior alone and λ does not enter them; manual λ check at S0.5; smoke test through `trks-run … 18101`; `$IN` copies with sha256; fallback is S0.7 + S3e; heads file next to the bundle; the design has its §11 7.4 entry; fallback for the harness clone |
| Authorization draft | **resolved** | Now cites runbook revision 3 "or the revision in force" |

### New issues (all MINOR)

1. **The S3e follow-on sessions (R3:358–372) contradict the prose.**
   - The block lists `trks_s3e_s<i>`, `trks_s3e_other_s<i>` and `trks_s3e_sec_s<i>` one after another. But `trks-run` returns at once, so a script copied from the block starts all three together: three clients on one single-slot server.
   - S0.1 tested only two clients per server, and the CPU plan assumes k × 2 campaigns.
   - R3:372 says the sessions run one after another. Make the block match: a separate launch script per stage, or `while tmux has-session -t trks_s3e_s<i>; do sleep 60; done`, plus a check that the `.exit` line says rc=0, before the next `trks-run`.
2. **The watcher's `pgrep` also matches CPU-only collector phases** (S0.5b, liveness, fit_prior), which take no `--stop-file`.
   - If a marker appears during S0.5b (about 1,000 audit runs), the watcher waits up to 1 h and logs `FORCED`, even though no GPU unit is affected.
   - Either note that a `FORCED` during CPU-only phases is not an incident, or run those phases under a separate session or pattern.
   - Running S0.5b through `trks-run trks_s05b - collect …` also protects it from an ssh drop. It resumes regardless.
3. **Run the Phase 1 probes through `trks-run trks_s01_* - probe …`** as well, so an ssh drop does not kill a 20–40 min foreground run.
4. **The GGUF is not re-checked after Phase 0 (pre-existing).** When given both `--gguf` and `--gguf-sha256`, the collector records the given sha256 and never re-hashes the file. Have `trks-status` (§11.5) or each phase report re-run `sha256sum` on the GGUF, so a replaced file cannot pass silently after Phase 0.8.

None of these causes wrong data or blocks a phase. Items 1 and 2 should be fixed before Phase 6, the first sharded phase, and the others when convenient.

### Verdict

Every BLOCKING and MAJOR finding from the original review and from the revision-2 re-check is resolved and verified. Four MINOR items remain.

**accepted**
