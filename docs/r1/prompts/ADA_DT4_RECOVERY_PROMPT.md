# Prompt: commit-only recovery of the DT4 rerun on Ada (13 Oct 2026)

*Written by Claude (coordinating session) at the author's request. Hand this whole file to the agent that ran `ADA_DT4_RERUN_PROMPT.md`. It runs on the author's Mac and reaches Ada as `experiment_zhixu`.*

---

You are the implementation agent for Paper B, route R1. The DT4 rerun finished collection but stopped while staging its artifacts: `docs/r1/reports/HEADROOM_PILOT_20261013_llm_tables.md` ended with a blank line, `git diff --cached --check` failed, and the STATUS commit was blocked as well. The author approved a **commit-only recovery** (PLAN §10, row **R1-COMPUTE (DT4 commit-only recovery, 13 Oct)**). Your job: commit the generator fix, regenerate the tables from the existing collection, commit the DT4 artifacts, run the committed-data regeneration check, write one STATUS entry, and report.

## Fixed facts

- Batch: `B=/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS`; clone `C=$B/agent_paper_B`; environment `$B/env.sh`.
- Python: `PY=/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/.venv/bin/python`.
- Collection: the one `results/r1/pilot/E1b_20261013T*` directory in `$C` that is **not** `E1b_20261013T090510Z` (the earlier interrupted attempt, which stays untouched). Call its repository-relative path `OUT`.
- Expected collection facts: 144 leaves, 12 audits, 1,440 LLM calls, 0 collection failures, 0 parse failures.
- The cause is fixed in `r1/headroom/e1b_analyze.py` (`markdown()` now ends with a single newline) and covered by `r1/tests/test_e1b_markdown.py`. `run_dt4` now also saves after-collection offload telemetry for future runs. For this run that telemetry is missing; record the gap and do not try to recreate it.

## Hard rules

1. **No re-collection and no retries.** Do not run `e1b_collect`, start Ollama, use a GPU, or touch `E1b_20261013T090510Z`.
2. **Do not change data or numbers.** The only regenerated artifacts are `analysis.json` (which must come out byte-identical) and the tables Markdown (which may differ from the runner's version only in trailing newlines). Do not edit the report text or any number.
3. **STOP and report**, leaving everything in place, if any check below fails: unexpected git state, non-identical `analysis.json`, a tables difference beyond trailing newlines, a failing whitespace check, a rejected push, or a regeneration hash mismatch.
4. **Git.** Never force-push or rewrite history. Keep the runner's uncommitted STATUS entry; it is a true record of the stop. Label your work as AI-assisted.
5. **Shared machine.** Do not disturb other users' processes.

## Steps

### 0. Commit the fix on the Mac

```sh
cd ~/Documents/agent_paper_B
git status --short
```

Expect exactly these entries:

```
 M docs/r1/PLAN.md
 M r1/headroom/e1b_analyze.py
 M r1/scripts/deepthought_batch1_resume.py
?? docs/r1/prompts/ADA_DT4_RECOVERY_PROMPT.md
?? r1/tests/test_e1b_markdown.py
```

Then:

1. Read `git diff`. The `PLAN.md` change is one new §10 row. The `e1b_analyze.py` change is the `rstrip`. The `deepthought_batch1_resume.py` change saves `gpu_offload_after_collection.json`.
2. Run `make r1-test` with `AR_HARNESS_ROOT=~/Documents/autoresearch_harness`, then `make test`. All must pass.
3. Commit with the message "Fix trailing blank line in E1b tables; record DT4 commit-only recovery", plus your attribution trailer.
4. `git push origin main`, then confirm that `git ls-remote origin refs/heads/main` equals `git rev-parse HEAD`.

### 1. Preflight and evidence on Ada (read-only, except `$B/recovery/`)

```sh
ssh experiment_zhixu
. "$B/env.sh"; cd "$C"
tmux ls; curl -s 127.0.0.1:11434/api/version || echo no-ollama
mkdir "$B/recovery"
cp "$B/batch_state.json" "$B/recovery/batch_state_at_stop.json"
git status --porcelain > "$B/recovery/git_status_at_stop.txt"
git diff --cached --stat > "$B/recovery/git_staged_at_stop.txt"
git diff > "$B/recovery/git_worktree_at_stop.diff"
cp "$OUT/analysis.json" "$B/recovery/analysis_original.json"
cp docs/r1/reports/HEADROOM_PILOT_20261013_llm_tables.md "$B/recovery/tables_runner.md"
sha256sum "$OUT/analysis.json" docs/r1/reports/HEADROOM_PILOT_20261013_llm*.md > "$B/recovery/sha256_at_stop.txt"
cat "$OUT/collection_checks.json"
```

Check:

- neither `r1_dt4_rerun` nor `r1_ollama_resume_20261012` is running. If our Ollama session is still alive, stop only that session;
- `collection_checks.json` matches the expected collection facts;
- the staged files are only `OUT`, the tables, the report and `docs/r1/STATUS.md`;
- the only tracked modification is `docs/r1/STATUS.md`.

### 2. Unstage and update the clone

```sh
git reset -q                      # unstage only; the working tree is kept
git pull --ff-only origin main    # brings the fix; must fast-forward cleanly
git rev-parse HEAD; git ls-remote origin refs/heads/main   # equal
grep -n 'rstrip' r1/headroom/e1b_analyze.py
```

### 3. Regenerate the tables from the existing collection

```sh
$PY -m r1.headroom.e1b_analyze "$OUT" --md docs/r1/reports/HEADROOM_PILOT_20261013_llm_tables.md
cmp "$OUT/analysis.json" "$B/recovery/analysis_original.json" && echo analysis-identical
$PY - <<'PY'
import pathlib
old = pathlib.Path('/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/recovery/tables_runner.md').read_text()
new = pathlib.Path('docs/r1/reports/HEADROOM_PILOT_20261013_llm_tables.md').read_text()
assert old.rstrip('\n') == new.rstrip('\n'), 'tables content changed'
assert new.endswith('\n') and not new.endswith('\n\n'), 'trailing newline still wrong'
print('tables: only trailing newline differs')
PY
```

If `analysis.json` is not identical, copy `analysis_original.json` back into place, then STOP and report.

### 4. Commit the DT4 artifacts

```sh
git add -f "$OUT" docs/r1/reports/HEADROOM_PILOT_20261013_llm_tables.md docs/r1/reports/HEADROOM_PILOT_20261013_llm.md
git diff --cached --check -- . ':!results/r1/**' ':!experiments/r1/**'   # must print nothing
git commit -m "Record PILOT E1b LLM headroom bracket and scripted comparison" -m "<your attribution trailer>"
git push origin main && git rev-parse HEAD && git ls-remote origin refs/heads/main
```

Do not stage `docs/r1/STATUS.md` in this commit.

### 5. Committed-data regeneration check

This mirrors the check `run_dt4` would have run:

```sh
SRC=$($PY -c "import json; m=json.load(open('$OUT/manifest.json')); print(' '.join(sorted({v['source'] for v in m['noise'].values()})))")
mkdir "$B/recovery/regen"
git archive HEAD r1 "$OUT" $SRC | tar -x -C "$B/recovery/regen"
(cd "$B/recovery/regen" && $PY -m r1.headroom.e1b_analyze "$OUT" > /dev/null)
sha256sum "$OUT/analysis.json" "$B/recovery/regen/$OUT/analysis.json"
```

The two hashes must match. Write `$B/recovery/regeneration.json` with both hashes, the commit from step 4 and the UTC time.

### 6. STATUS entry

`docs/r1/STATUS.md` already holds the runner's uncommitted "Remote batch 1: stopped" entry. Insert a new entry above it (newest first):

```
## 13 October 2026 — DT4 rerun: commit-only recovery

AI-assisted recovery by <agent>, authorized by the author (PLAN §10, R1-COMPUTE DT4 commit-only recovery). PILOT; not evidence.

- Cause of the stop: the generated tables ended with a blank line, which failed `git diff --cached --check`. The runner stopped before committing anything. Fix: <step-0 commit> (`e1b_analyze.markdown` ends with one newline; `r1/tests/test_e1b_markdown.py`).
- No re-collection. Collection `<OUT>`: 144 leaves, 12 audits, 1,440 LLM calls, 0 collection and 0 parse failures; wall time 28.3 min; Ada GPU 1 (`GPU-aa340032-6f94-9783-8f3d-50a15da47a6f`), no co-tenants observed, minimum free memory 43,145 MiB; load offload `size_vram = size = 5,560,907,776` bytes.
- Regenerated `analysis.json` is byte-identical to the runner's (sha256 <…>). The tables differ only in the trailing newline. Committed in <step-4 commit>.
- Committed-data regeneration check: <match/mismatch>, sha256 <…>.
- Gap: the after-collection offload check passed, but its telemetry was not saved (fixed for future runs in <step-0 commit>).
- Evidence of the stopped state: `$B/recovery/`.
- E2 decisions remain open. L11 is not built.
```

Fill every `<…>`. Then:

```sh
git add docs/r1/STATUS.md
git diff --cached --check
git commit -m "Record DT4 staging stop and commit-only recovery" -m "<trailer>"
git push origin main
```

Finally, on the Mac: `git pull --ff-only`.

### 7. Report to the author

Send a short message with:

1. the outcome and the three commits (fix, artifacts, STATUS);
2. the hashes: original vs regenerated `analysis.json`, and the committed-data regeneration check;
3. per node (`digits_mlp`, `openml_ionosphere`, `ALL`), from `$OUT/analysis.json` and, for comparison, from `results/r1/pilot/E1b_20261012T161034Z/analysis.json` (scripted): `estimates.rho` with `ci.rho`, `share_points_verify_changes_leaf`, `mean_verify_minus_continue`, `best_simple`, `headroom_naive` and `headroom_leafsplit` with their CIs. These numbers decide how to read the exactly-zero ionosphere headroom, so give them as numbers, without interpretation;
4. any deviation, and anything that needed rules 3–5.
