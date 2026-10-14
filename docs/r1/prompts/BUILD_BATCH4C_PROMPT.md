# Build batch 4c: fix the rerun-2 launch defects and add an end-to-end desktop dry run (14 Oct 2026)

*Written by Claude (coordinating session) at the author's request. Hand this whole file to the implementation agent on the author's Mac.*

---

You are the implementation agent for Paper B, route R1. The first rerun-2 launch on Ada stopped before any inference, because of engineering defects in the runner and the launcher. The newest STATUS entry, "rerun-2 first launch stopped before any inference", records them. Fix them. Then make sure no other runner path can fail this way: run the **real runner end to end on the Mac**, against a fake Ollama and a fake `nvidia-smi`.

**The experiment design does not change.** No PLAN row changes.

## Hard rules

- No real LLM calls, no GPU, no Ada.
- No design change: nodes, arms, budgets, seeds, gates and analysis stay exactly as PLAN §10 states them.
- Production behaviour on Ada stays the same, apart from the three fixes below. The dry-run mode must be impossible to enable by accident on Ada:
  - it requires an explicit `R1_DRYRUN=1`;
  - it labels everything `DRYRUN`;
  - it writes only to a temporary directory;
  - it pushes only to a local bare repository, never to `origin`;
  - it refuses to run on `ucrtasl`.
- Every fix has a fail-before / pass-after test. Do not rewrite history. Label the work AI-assisted.

## Step 0

1. Paper repo: `git pull --ff-only`. `git status --short` must show exactly:
   - ` M docs/r1/STATUS.md`
   - ` M docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md`
   - `?? docs/r1/prompts/BUILD_BATCH4C_PROMPT.md`
2. Review the diff, commit it as "Record rerun-2 launch stop; batch-4c prompt; Ada prompt update", and push.
3. Record the base commits and the baseline test numbers. The harness should stay untouched; if a fix truly needs the harness, stop and report instead.

## Fixes

### X1 — `MODELS` in `r1/scripts/ada_e1b_rerun2.py`

- Define the Ollama models directory from `R1_OLLAMA_MODELS`. It is required: fail with a clear `STOP:` if it is unset or the directory is missing.
- Then search the runner and every helper it loads for **all other names** that were defined in `ada_rerun_dt4.py` or `deepthought_batch1_resume.py` scripts but are not in scope in the rerun-2 runner. Fix each one.
- Add a static guard test: compile the runner together with the helpers in the way it loads them, and check that every global name referenced is defined (an AST-based check or `pyflakes` equivalent, adapted to the exec-loading pattern). The guard must flag the original `MODELS` defect at `7272d77`/`69b2bbd`.

### X2 — git identity in the launcher

- `--prepare` requires `R1_GIT_NAME` and `R1_GIT_EMAIL` (`STOP:` if missing), and sets them as **repository-local** `user.name` / `user.email` in both fresh clones.
- It then checks `git var GIT_COMMITTER_IDENT` in both clones, and `git push --dry-run` to the respective remote branch.
- It records the identity and the check results in `prepare.json`.
- `--start` re-checks them and refuses if they are missing.
- Tests use stubs.

### X3 — dev dependencies

The launcher installs the harness with `uv sync --extra dev`, so that pytest is present. Nobody installs packages by hand. `prepare.json` records the pytest version. Add a test with a stub.

### X4 — end-to-end desktop dry run (the main deliverable)

Add `r1/scripts/rerun2_dryrun.py`, plus a test that runs it. It executes the **real** `ada_e1b_rerun2.py` entrypoint, through every phase and including `finish`, with:

- **A fake `nvidia-smi`** on `PATH`, reporting one shared card with enough free memory and one co-tenant process. The co-tenancy path is exercised.
- **A fake Ollama** started by the runner's own command (point `R1_OLLAMA_BINARY` at a small fake script that serves HTTP on 127.0.0.1:11434). It implements:
  - `/api/version`;
  - `/api/tags` (the pinned digest);
  - `/api/generate`;
  - `/api/ps` (with `size == size_vram`);
  - `/api/chat`, which is what `langchain_ollama` calls. It returns a valid JSON proposal that names an active key for the node (and occasionally an inactive one, to exercise the D25 rejection path). It echoes the received `seed` into its log, so the test can assert that D26 seeds arrive.
- **A tiny design**, accepted only under `R1_DRYRUN=1`: 2 nodes, 1 instance, W = 4, one E2 point, 1 repetition, 1 audit seed.
- **Fresh clones** of both repos into a temporary directory, with a local bare remote for each, so `commit()` really commits and pushes, and the push check passes.
- **A repository-local git identity**, set through the launcher's `--prepare` code path (X2), not by hand.
- **The launcher**: run `ada_e1b_rerun2_launch.sh --prepare` and then `--start` with `R1_RERUN2_*` overrides pointing at the temporary layout. Accept a host-guard override only under `R1_DRYRUN=1`.

**Acceptance.** Run the dry run on the code before your fixes first, and save the log as proof: it must fail at `MODELS`. After the fixes, all of the following must hold:

- every phase completes: preconditions, liveness (it may pass or fail per node; at least 2 nodes are needed, so make the fake proposals novel enough), arm A, arm B, arm C, comparison, finish;
- each arm's results, the tables, the comparison report and the STATUS entry are committed and pushed to the bare remote, and every commit passes the whitespace check;
- the regeneration hashes match;
- a restart of the finished batch refuses (review F10);
- the run takes under about 15 minutes on the Mac CPU.

Write the run summary (phases, commits, wall time) to `results/r1/engineering/rerun2_dryrun_<UTC>/summary.json`, labelled DRYRUN. Do not commit the temporary repositories.

### X5 — launcher self-check on Ada

`--start` prints a single summary line before starting tmux: heads, identity, accepted failures, pytest version, models directory. This lets the operator confirm the setup at a glance. Add a stub test.

## Independent review (required, short)

Spawn one fresh-context subagent. Give it only:

- the newest STATUS entry;
- this prompt;
- both diffs;
- the test logs;
- the dry-run log from before the fixes and the one from after.

It edits no code, and writes `docs/r1/reviews/BUILD_REVIEW_20261014c.md` with MAJOR or MINOR findings. **Checklist:**

1. Do the X1–X3 fixes cover the observed failures, and does the static guard catch the class of defect, not just this instance?
2. Is the dry run really the production runner path, apart from the fake binaries and the tiny design?
3. Can dry-run mode leak into production? Check the guards, `origin` pushes and Ada host refusal.
4. Which runner paths remain unexercised by the dry run? List them, so the author knows the residual risk.
5. Fail-before / pass-after for X1, X2 and X3.

Then one correction round. Append a Resolution section.

## Finish

1. Push.
2. Write one STATUS entry with:
   - commits;
   - tests before and after;
   - the dry-run results (the failing run before the fixes, the passing run after);
   - the list of runner paths that remain unexercised;
   - the review summary.
3. Report to the author, and confirm that `ADA_E1B_RERUN2_PROMPT.md` (updated, committed in Step 0) can be handed over.
