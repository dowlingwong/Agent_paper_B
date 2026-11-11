# B1 truncation STOP — read-only host check for the experiment agent (11 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This is item (1) of the author's route for the STOP of run `fffa_20261111_b` (report `docs/r1/reports/B1_STOP_FFFA_20261111.md`, branch `mac-b1-20261107` @ `8af27919`). The author's ruling is to handle the STOP as an engineering problem; it is recorded in PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID` on branch `mac-b1-trunc-20261111` and is not quoted here. This hand-off **only reads and copies**. Run it on TASL-7 over SSH from the Mac, in the same capture style as the STOP census (a private `/private/tmp/…` capture directory with `ssh.log` and `ssh.exit`).

## 0. Boundaries

- **Read only on the host.** Do not start, signal or stop any process. Do not touch the GPU, the lease or the marker. Do not modify, move, retire or delete anything under `/home/dowling/exam-x/work/b1_fffa_20261111_b/`, the run-6835 tree, the staged checkouts or the llama.cpp checkout. Write nothing on the host, not even temporary files.
- The only program started on the host is the pinned `llama-server` with `--version` and `--help` (step 2.2). The B1 runtime already runs `--help` before every server start; both calls exit in the argument parser, before any backend or model is loaded.
- Git: run only `git --no-optional-locks …` read commands. They write no index or lock files.
- Files go to the Mac at `~/Documents/agent_paper_B/Claude outputs/b1_fffa_usage_20261111/`. Nothing is committed to the repository by this hand-off.

Below, `W=/home/dowling/exam-x/work/b1_fffa_20261111_b` and `L=/home/dowling/exam-x/work/llama.cpp`.

## 0a. Read-only census first

`ssh <tasl7> "nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv; pgrep -af '[l]lama-server|[e]xam_runner|[r]1\.exam'" > census.txt` (the bracketed pattern keeps `pgrep` from matching its own shell). Classify every listed process by its full command line and owner: the Track S watcher and other users' processes are not B1's. Then:
- **No B1/exam process** (`exam_runner`, `r1.exam`, or a `llama-server` from `/home/dowling/exam-x/work/llama.cpp/build-exam`) and **no compute application**: go on with everything.
- **A compute application that is not B1's** (another user's job; R1-TASL7-AGENT-OCCUPANCY-07NOV): go on with steps 1, 2.1 and 2.3–2.5, 3 and 4 (pure reads). **Skip only the two binary calls of step 2.2**, and note this in `llama_check.txt`.
- **Any B1/exam process or a pinned `llama-server`**: the scene is not as the STOP report left it. STOP, report, do nothing further.

## 1. Root ledgers and events (for the per-root completion table)

1. `sha256sum $W/batch_state.json`. Expected `0e0926dafee940b84d19d9d4d793b2d23933dd4ba6e02bf8ac3f9f444e370e85` (STOP report §6). If it differs, record it and go on; the analysis will report the difference.
2. Stream a tar of the per-root evidence to the Mac, read-only on the host:
   ```
   ssh <tasl7> "cd $W && find . -mindepth 5 -maxdepth 5 -path './*/b1/*/*' -type f \( -name root_events.jsonl -o -name root_trials.jsonl \
       -o -name a4_observer_requests.jsonl -o -name campaign_manifest.json -o -name job.json \) -print0 \
       | sort -z | tar --null -T - -cf - batch_state.json" > roots.tar
   ```
   (`find` lists root files only; `tar -cf -` writes to stdout.)
3. On the host, the same file list with `sha256sum`, to stdout:
   `ssh <tasl7> "cd $W && { sha256sum batch_state.json; find . -mindepth 5 -maxdepth 5 -path './*/b1/*/*' -type f \( … same names … \) -print0 | sort -z | xargs -0 sha256sum; }" > host_sha256.txt`.
4. On the Mac: `tar -tf roots.tar | wc -l` must equal `wc -l < host_sha256.txt`. Extract into `roots/` beside the tar and check it with `cd roots && shasum -a 256 -c ../host_sha256.txt`, which must say OK for every file.

## 2. llama.cpp: does the pinned build support `--reasoning-budget N>0`?

Write everything to `llama_check.txt`:

1. `sha256sum /home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server`. Expected `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b` (`exam_b1_v2.json`).
2. `<binary> --version` (expected `version: 0.7.0-dev (build 1, commit 620d222)`) and `<binary> --help 2>&1 | grep -n -A2 -E 'reasoning-budget|reasoning-format|^ *-rea'`.
3. `git -C $L --no-optional-locks rev-parse HEAD` (expected `620d2225cc436ab0b001e3200e590e3b286ef9ab`), `git -C $L --no-optional-locks status --porcelain --untracked-files=no` (expected empty), and `git -C $L --no-optional-locks log -1 --format='%H %cI %s'`.
4. `cd $L && sha256sum common/arg.cpp tools/server/server-common.cpp tools/server/server-schema.cpp common/sampling.cpp common/reasoning-budget.cpp`. Expected (upstream `ggml-org/llama.cpp` at `620d222`):
   ```
   a10b6e6af910366c5c1abb89e47a7c6711fc1f10708b5fbfd8b59ba1a11d0f4a  common/arg.cpp
   fcb05757dd6a25d349024fd57df9b05c7ff77902cd17d1b70b9f41ac54f6c45c  tools/server/server-common.cpp
   1f9d7b73b4363b90b08de0360b0a5ce0b3d152750bfb8d587a367e90c7904050  tools/server/server-schema.cpp
   e88c45dfdc58ef2e86b5519aac68c83ced333952ade7d4bd8fca5f1ce5bbea02  common/sampling.cpp
   55c730c85e7e2353d44542b5582a0046ffc503aa828cbd58f2bc6a7d957b48b2  common/reasoning-budget.cpp
   ```
5. The four lines the diagnosis rests on, with context:
   `grep -n -A4 '"--reasoning-budget"' common/arg.cpp`;
   `grep -n -B6 -A6 'thinking_end_tags().empty()' tools/server/server-common.cpp`;
   `grep -n -A3 'reasoning budget sampler' common/sampling.cpp`;
   `grep -n -B2 -A3 'add_alias("max_completion_tokens")' tools/server/server-schema.cpp`.

## 3. Server logs of the two thinking-on intervals

Write to `server_grep.txt`, one block per server directory so that one cannot crowd out the other, for `S` in `qwen36_27b` and `qwen38_27b`:
- `ls -l $W/servers/$S`;
- `grep -H -n -E 'chat template, thinking|chat template, example_format' $W/servers/$S/* 2>&1 | cut -c1-400 | head -40`;
- `grep -H -n -i 'reasoning' $W/servers/$S/* 2>&1 | cut -c1-400 | head -60`.

The "chat template" lines are printed at the run's `-lv 4`.

## 4. Client library versions in the frozen venv (no import)

Write to `venv_versions.txt`: `ls /home/dowling/exam-x/work/venv/lib/python3.13/site-packages | grep -E '^(openai|langchain_openai|langchain_core|langgraph|pydantic|pydantic_core|httpx)-[0-9].*\.dist-info$'`. The Mac-local agent re-runs the truncation tests with exactly these versions (diagnosis §2.3).

## 5. Delivery

In `Claude outputs/b1_fffa_usage_20261111/`: `census.txt`, `roots.tar`, `roots/` (extracted), `host_sha256.txt`, `llama_check.txt`, `server_grep.txt`, `venv_versions.txt`, plus the capture's `ssh.log`/`ssh.exit` SHA-256 values in `CAPTURE.txt`. Finish with a Mac-side `SHA256SUMS` over the top-level files. Tell the author or the Mac-local agent when it is there. The Mac-local agent will compute the per-root table with `python -m r1.scripts.b1_completion_usage --roots <…>/roots` and write it into `reports/B1_TRUNCATION_DIAGNOSIS_20261111.md`.

Any step that would write on the host, a B1/exam process (§0a), or a difference in the scene (marker, batch state), is a STOP: report it and do nothing further. Another user's GPU job is not a STOP (§0a).
