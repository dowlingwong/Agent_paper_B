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
