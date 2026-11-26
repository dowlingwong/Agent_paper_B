# R1-T1-HOST-TASL TASL-7 proposer llama-server engineering smoke — independent review (21 November 2026)

**Reviewer.** Fresh independent reviewer (`tasl7-proposer-reviewer`), delegated by the lead; no involvement in
writing the report, scripts, captures or run. Read-only: the only file written is this review. No server
start/stop (the host binary was invoked once with `--version` only, which exits without binding), no Ada writes,
no TASL-2 write (see the command record: one read-only `git status` on TASL-2 may have created/removed a
transient `.git/index.lock`; no file content changed), no push/delete/HTCondor action, and no touch of the
attempt-1 archive or lease logs. TASL-7 and TASL-2 were inspected with read-only `ssh -o BatchMode=yes`
commands (`sha256sum`, `stat`, `find`, `ps`, `ss`, `flock`, `nvidia-smi`, `tailscale status`, `ip route get`,
file reads, `llama-server --version`, read-only `python -B`/`sed`). The submitted probes, the smoke and the
server were **not** re-run.

**Object under review.** Report `docs/r1/reports/trackg_g0_20261117/TASL7_PROPOSER_SMOKE_20261121.md`
(272 lines, 18 860 B, sha256 `d27c35437fa943e8549e7a4161841e2cb8b6993f758d26a35542bb3305f140e8`; untracked in
`ops-tasl-20261116` at HEAD `ebe03cd5`) and its sibling captures
`TASL7_PROPOSER_SMOKE_20261121_captures/` (62 files; `SHA256SUMS` covers 61 files, sha256
`c5e3643e2c65bb38df66c1c9a49e3f60607376d0b340e69f751f6e7f1cd0d66d`; 61/61 `shasum -c` OK locally and live on
TASL-7). Host run root `/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121/`; its live `captures/`
`SHA256SUMS` sha and 62-file bundle are identical to the delivered sibling.

**Verdict: ACCEPTED for the ENGINEERING_ONLY proposer-smoke purpose, with conditions C1–C7; 0 BLOCKING,
2 MAJOR, 10 MINOR.** The engineering result is real and reproducible from the delivered bytes plus the live
host: identity, exact flags, a single `.51`-only start/stop, the flock lease with untouched lease logs, three
real manager-sized calls from TASL-2 through the shared-node `.50` alias, 3/3 six-key parses, and an
attempt-1 archive that is content-identical now, not only pre/post. The two MAJORs are record/gate conditions,
not run failures: (M1) the accepted host-check review's C4 fixes `MemoryMax=8G`, while the run used `48G` with
no recorded waiver/amendment; (M2) the report's literal-`.51` timing/error figures contradict its own capture.
This is not a T1 label row, not an exam attempt and not Track P evidence; no such claim is made in the report.

## Authority and inputs

- **Task authority asserted:** author row **R1-T1-HOST-TASL**, in the **R1-TRACKG-AR-U2-TASL2** context,
  delegated by the lead. That id is **not** in the committed `docs/r1/PLAN.md` (the committed rows name
  `R1-TASL7-TRACKP` and `R1-TRACKG-AR-COND7`, not this id). The only written scope text I could find is the
  host-check report's: "scope = HARNESS_ISOLATION §3 host checks on TASL-7 only, STOP if any condition fails,
  preserve the attempt-1 archive and lease log, no deletion, no push, **no proposer llama-server start**"
  (`TASL7_ISOLATION_HOST_CHECK_20261121.md` lines 26–28). The smoke record does not quote the separate
  lead/author delegation that authorized the start (m6/C6). This does not change the engineering facts, but the
  record trail is incomplete.
- **Accepted prerequisite:** host check `TASL7_ISOLATION_HOST_CHECK_20261121.md` (sha256
  `0150c80a480b1e0f6ddc5f5a32ea57fa33947e07ceb2c40efc2ffc072769a209`) and its review
  `docs/r1/reviews/TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (sha256
  `18e261cd3641d3ec370599c8f38131862ef8c3e5e1b92659f08c984202fa15d5`), **ACCEPTED with conditions C1–C4**
  (report-text/record conditions; no re-run). The host-check review was completed at 02:18:45Z, before this
  smoke started at 02:27:30Z, so the host-check GO's "after independent review" timing is satisfied. However
  **C1–C3 are still open**: the host-check report sha is unchanged and its status line still says "PASS for all
  seven TASL-7 host conditions" (m5/C6). The smoke does not take CUDA-IPC credit, correctly.
- **Exam settings checked against** `docs/r1/proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md` and
  `docs/r1/PLAN.md`: context 32 768, `-ngl 999`, `-np 1` (one slot), q8_0 K/V, `--jinja`, thinking kwarg
  `{"enable_thinking":false}`, temperature 0.2 with the D26 seed, `cache_prompt: false` on every call
  (R1-EXAM-CACHE-REV), structure-only `manager_proposal/v1` (R1-SCHEMA), `max_completion_tokens = 16384`
  (R1-EXAM-B1-TRUNCATION-INVALID), `stream: false`.
- **Identity pins:** binary sha `b70f4882…` and version `0.7.0-dev (build 1, commit 620d222)` are the exam
  binary recorded in the repo (`docs/r1/RUNBOOK.md` Track X Stage A row; `B1_TRUNCATION_HOST_CHECK_HANDOFF_
  20261111.md`); model sha `2959c1b0…` / 19 598 489 952 B is the pick in the sweep-2 authorization note.
- **Provenance:** frozen prompt set `…/trackx_stagea_promptset_20261031/prompts.jsonl` sha256
  `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a` (50 records); schema from
  `/home/dowling/r1_trackp/autoresearch_harness/src/autoresearch/llm/providers.py` sha256
  `de343bf77003c943ed95eae98ed7dc84540e788dcfa178debfc4be6425417247`, harness HEAD
  `897d83c8efa364ec2fdd37288241cc42e01d7274`, branch `trackp-20261026`.

## Independent verification performed

### 1. Binary, model, exact flags, metrics, thinking (live re-verified on TASL-7)

- Binary sha256 re-computed live:
  `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`; `--version` →
  `version: 0.7.0-dev (build 1, commit 620d222)`, `built with GNU 11.4.0 for Linux x86_64`. Matches the
  capture and the repo pin.
- Model sha256 re-computed live over the full 19.6 GB:
  `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`; size `19598489952` B; mtime
  `2026-11-01 09:05:45.678565088 -0800`. Matches.
- The launched argv tail (`-c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs
  {"enable_thinking":false} --cache-type-k q8_0 --cache-type-v q8_0 --host 100.106.74.51 --port 8095
  --no-webui -lv 4`) matches the specified string one-for-one; the only add-ons are the required `-m` and the
  allowed `-a gemma4_31b`. No numeric value changed; `--metrics` is absent from the argv, and the captured
  `/metrics` requests return HTTP 501 ("Start it with `--metrics`").
- `server.log` has one start banner (`listening on http://100.106.74.51:8095`, line 230) and one shutdown
  (`cleaning up before exit...`, line 322); exactly three `new prompt` blocks (tasks 0/128/256) and three
  `print_timing` blocks; every release line says `truncated = 0`.
- Thinking-off finding F2 is correctly disclosed: log warning `Setting 'enable_thinking' via
  --chat-template-kwargs is deprecated. Use --reasoning on / --reasoning off instead.` at `0.00.032.808`, and
  `init: chat template, thinking = 1` at `0.03.612.344`. For all three calls `completion_tokens == predicted_n`
  (124/124, 124/124, 115/115), `finish_reason = stop`, content starts with `{` and is pure six-key JSON
  (383/383/326 chars). No thought-channel text and no unbounded thinking: maximum generation was 124 tokens
  against the 16 384 cap. (The stronger statement "grammar-constrained output leaves no room for a thought
  prefix" is an inference — the -lv 4 log does not print a grammar/response_format line — see m10.)

### 2. Start/stop, bind, lease, cgroup, GPU (live re-verified)

- **One start / one stop.** Lease `2026-11-21T02:28:56Z`, health 200 `02:29:01Z`, SIGTERM to PID 187900
  `02:31:38Z`, exit 1.0 s later; one listening line and one cleanup line in the append-mode server log; no
  earlier attempted start (the lease file contains only the acquisition line, never `LEASE_BUSY`). Live now
  (02:40Z): no `llama-server`, port 8095 free, `gpu0.lock` free, no smoke `run-*` scope or cgroup leftover,
  GPU 44 MiB / 0 % / 35 °C / no compute apps.
- **Bind only the Tailscale address.** `ss -ltnp` shows the single listener
  `100.106.74.51:8095` (pid 187900); no `0.0.0.0`, no second listener. The host check's "GPU by UUID" and
  no-CUDA-IPC conditions are also met (`CUDA_VISIBLE_DEVICES=GPU-ab72fb4a-…`; single-process server).
- **Shared-node routing (F1) independently confirmed.** TASL-7's own tailnet address is `100.106.74.51`
  (`tailscale status`: `100.106.74.51 tasl-7`); TASL-2's `tailscale status` lists the same node as
  `100.106.74.50 tasl-7.tail119748.ts.net` (a shared node), and `ip route get 100.106.74.51` on TASL-2 goes
  via the LAN gateway `169.235.24.1 dev enp2s0` (not tailscale0), while `ip route get 100.106.74.50` goes via
  `tailscale0`. So literal `.51` from TASL-2 is genuinely not routable; `.50` is the correct alias and the
  server's `.51`-only bind served it. This is a topology fact, not a smoke failure.
- **Lease.** `serve.sh` opens `~/r1_locks/gpu0.lock` (`exec 9>>`), takes `flock -n -x 9` and `exec`s the
  server; `poststart_state.txt` shows fd 9 → `/home/dowling/r1_locks/gpu0.lock`, a second-process probe
  returning `LOCK_BUSY_AS_EXPECTED`, and `stop.txt` returns `LOCK_FREE` after exit. Both lease-log candidates
  are sha256- and stat-identical before/after, and still are now (`trackp_evidence.log` `2e762c16…`; 
  `gpu_lease_log.jsonl` `e97e03d2…`). `gpu0.lock` is 0 B, inode 56251186, mtime/ctime
  `2026-11-20 17:59:38.612690398 -0800` — unchanged by this run.
- **Cgroup.** Live delegated per-command scope `tasl7-proposer-smoke-20261121.scope`, `Delegate=yes`,
  `memory.max = 51539607552` (= 48 GiB), `memory.swap.max = 0`, `nsdelegate=1`; the cgroup was collected after
  exit (unit not found, no leftover dir). **This is not C4's literal `MemoryMax=8G`** — see M1.
- **GPU / VRAM.** Pre 44 MiB / 0 % / 36 °C / no compute apps; loaded 21 565 MiB used (app 21 516, reserved
  493), 39 °C, 0 %; after calls 21 585 MiB (app 21 536), 42 °C; after stop 44 MiB / 0 % / 37 °C / no compute
  apps (three settled samples). The report's 21.5 GB figure and cleanup claims are accurate.

### 3. The three manager-sized calls from TASL-2

- The request body is captured byte-for-byte in `calls_tasl2.json`: one user message with the frozen prompt,
  `temperature 0.2`, `cache_prompt false`, strict `json_schema` response format, `max_completion_tokens 16384`,
  `stream false`, model `gemma4_31b`. `request_sha256 9ec93e3e…` and `response_format_sha256 682134ae…`
  recompute exactly from the captured JSON (canonical sorted-key hashes).
- Prompt: 2 925 chars, sha256 `08e7c0149919cf3d659c13ec8ce0c19c6928a5e972fd18355fff62a5f1631bca`; the base64
  payload decodes to record index 18 of the frozen 50-record set (`openml_breast_w`,
  `openml_breast_w__s105-trial-007`), whose `prompt` field is byte-identical. Prompt tokens are 995 on all
  three calls (server usage and log). (The "median" wording is slightly off — see m1.)
- Schema provenance verified on TASL-2: `providers.py` sha `de343bf7…` at HEAD `897d83c8…` branch
  `trackp-20261026`; `manager_response_format("manager_proposal/v1")` in that file returns exactly the captured
  structure — fields `rationale, summary, objective, param, old_value, new_value`, all strings, all required,
  `additionalProperties: false`, `strict: true`, name `manager_proposal_v1`.
- Results: 3/3 HTTP 200, wall 3.9257 / 3.7600 / 3.6555 s (p50 3.7600, min 3.6555, max 3.9257, mean 3.7804),
  prompt 995, completion 124/124/115, `cached_tokens 0` on all three, `finish_reason stop`, 3/3 parse to
  exactly the six required keys. Server-side `-lv 4` confirms `temp = 0.200`, `cached n_tokens = 0,
  memory_seq_rm [0, end)` for each call (cache disabled), and `truncated = 0`. Contents are 383/383/326 chars,
  all choosing `C: 0.3 → 0.1`; content is pure JSON. No secrets (no API key is set on the server, and the
  prompt/request files contain no credentials).
- "From TASL-2": the client output's `client_host` is `TASL-2` and the harness pyc write is timestamped at the
  run (see §4); combined with the independently verified `.50`-only topology, the capture is consistent with a
  real TASL-2 call path. (Server log at -lv 4 does not print the remote address.)

### 4. Preservation and host state (live re-verified)

- **Attempt-1 archive** `/home/dowling/r1_trackp/runs/p3a_operator_20261027`: I recomputed the fingerprint
  live, read-only, with no output files: `find -printf … | LC_ALL=C sort | sha256sum` =
  `299237d06012f42b13cff4b476b2167bec55fa2c2463f056567f986ff7e1e003`; the content-hash pipe =
  `af7ede86da7abbe36ff4ec35ef2029ce4e6233afd5fbe4f49e14684c4d16e965`; 1040 entries / 724 files /
  11 925 743 308 B; root inode 56889763, EVIDENCE inode 56890010, `journal.jsonl` 28 967 B inode 56889764.
  These equal the pre and post captures, so the archive is content-identical **now**, not merely pre/post.
- Both lease logs unchanged (sha and stat, above); `gpu0.lock` stat unchanged. No file exists outside the new
  run root under `~/r1_engineering`, `~/r1_locks`, `~/r1_trackp` (depth 3), `~` or `/tmp` newer than run start,
  except the known TASL-2 pyc and the transient git metadata noted in m7. `preflight_before/after` differ only
  in time, memory, GPU temperature/session-scope id; boot id, kernel, `/dev/shm` (15 objects) and disk (514 GB
  free) are unchanged.
- The TASL-2 disclosure is real: `…/src/autoresearch/llm/__pycache__/providers.cpython-310.pyc` (4370 B,
  mtime 18:30:46 PST = 02:30:46Z, sha `1d904cc1…`) was created by the client's `providers.py` import. The
  harness worktree is at its recorded tip and the source tree is unchanged.
- **Host-check conditions:** the smoke kept the operating set it claims (delegated per-command cgroup, GPU by
  UUID, no CUDA IPC, flock lease, no-compute-apps preflight) except the literal `MemoryMax=8G` (M1). The
  host-check report's own STOP/GO text asks only for a delegated per-command scope, `AR_TEST_CGROUP_PARENT`
  (for the kit) and GPU-by-UUID; the accepted review's C4 additionally fixes `MemoryMax=8G`.

### 5. Bundle integrity, accuracy and labels

- Report sha `d27c3543…` and captures `SHA256SUMS` sha `c5e3643e…` match the task's values; 62 files, 61
  checksums, 61/61 verify; the host copy has the same `SHA256SUMS` sha and file list, and the six captured
  `scripts/*` are byte-identical to the host run scripts that actually ran. The report's "62 files, 968 KiB"
  is the host `du -sk` figure and is consistent.
- The bundle supports most of the report's numbers (identity, flags, lease, cgroup, VRAM, calls, tokens,
  latencies, parse, cleanup, attempt-1, lease logs). Exceptions are M2 (literal-`.51` numbers) and the minors
  below.
- The report is correctly labelled **ENGINEERING_ONLY**, says it is not a T1 label run / exam attempt / Track P
  action, and says "nothing here is evidence for a T1 label row"; `SUMMARY.json` has `engineering_only: true`
  and `t1_label_run: false`, and the captures README repeats the label. No overclaim of evidence status found.
- Cleanup and end state are as claimed (live re-checked): no process, port free, flock free, scope/cgroup gone,
  GPU idle, no leftovers of ours.

## Explicit requirements — result

| Requirement | Result |
|---|---|
| Binary sha/version, model sha/size, exact flags, no numeric changes, `--metrics` absent | **PASS** (live re-hashed) |
| `enable_thinking` deprecation warning / `thinking = 1` disclosed; no thinking tokens / no unbounded thinking | **PASS** (disclosed; completion==predicted, finish stop, cap 16384) |
| Bind only Tailscale `.51`; TASL-2 works via `.50` shared alias; F1 correct | **PASS** (topology independently verified) |
| One start / one stop; flock held; lease logs untouched; 48 GB cgroup disclosed; VRAM ~21.5 GB; idle after stop | **PASS with M1** (8 G cap condition not met) |
| 3 manager-sized calls from TASL-2: frozen prompt/tokens, schema, temp 0.2, `cache_prompt:false`, cap 16384, parse/tokens/latencies, no secrets, p50/min/max | **PASS** |
| Host-check accepted prerequisite / C4 operating set | **PASS except C4 `MemoryMax=8G`** (M1); host-check C1–C3 themselves still open (m5) |
| Attempt-1 archive byte-identical pre/post and now; no other host change; no compute apps during/after | **PASS** (archive recomputed live; no new files; only server as compute app during; none after) |
| Report/captures accuracy, SHA256SUMS, no overclaim, ENGINEERING_ONLY / no T1 label, cleanup | **PASS with M2 + minors** |
| MAJOR / BLOCKING | **0 BLOCKING; 2 MAJOR** (M1, M2) |

## Findings

### BLOCKING

None.

### MAJOR

- **M1 — the accepted host-check review's C4 says `MemoryMax=8G`; this run used `MemoryMax=48G`, and no
  waiver or amendment is recorded.** The accepted review's C4 reads: "Every run must use a live delegated
  cgroup parent (`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, or
  `AR_TEST_CGROUP_PARENT` at a live delegated directory) …". The run used the correct mechanism
  (`systemd-run --user --scope`, `Delegate=yes`, `MemoryMax=48G`, `MemorySwapMax=0`; `memory.max =
  51539607552`, `swap.max = 0`, `nsdelegate = 1`) but not the numeric cap. The report discloses and justifies
  this prominently (deviation 2, `launch_spec.cgroup_deviation`, `SUMMARY.json` disclosure 2: a 19.6 GB GGUF
  cannot be served under 8 G), and the host-check report's own STOP/GO text does not repeat the 8 G figure.
  But an accepted condition cannot be reinterpreted by the run's own report: without an explicit
  author/lead amendment of C4 (e.g., a proposer-server cap of 48 G with rationale) or a recorded waiver, the
  smoke cannot be cited as satisfying the accepted C4 operating conditions. This is a record/gate issue, not
  an engineering failure — the cap was never approached (`memory.peak` 1.12 GB, host `VmHWM` 19.47 GB) and the
  other C4 elements were met.
- **M2 — the report's literal-`.51` reachability figures contradict its own capture.** Report §"TASL-2
  reachability", F1 and `SUMMARY.json` disclosure 1 say the literal `http://100.106.74.51:8095` `/health`
  timed out "after 8.0 s" and `/v1/models` also "timeout after 8.0 s", and that "TCP and curl time out after
  8 s". The captured client result is different: `literal_health.wall_s = 15.0057` with
  `URLError(TimeoutError('timed out'))` (client timeout set to 15 s), and `literal_v1_models.wall_s = 1.067`
  with `URLError(OSError(101, 'Network is unreachable'))` — an immediate route failure, not a timeout. The
  conclusion is unchanged and in fact stronger (and the live `ip route get 100.106.74.51` check above confirms
  why), but the evidence table and F1 must quote the capture, not a different 8 s probe whose output is not in
  the bundle. Related: the "0.185 s first probe" in the report is not in the bundle either (the
  captured client `/health` is 0.1019 s); cite the capture or drop it.

### MINOR

- **m1 — "median 2925 chars" is not the median.** Over the 50 frozen records the two central prompt lengths
  are 2902 (index 31) and 2925 (index 18); the median is 2913.5. The run chose the upper middle value (2925),
  which is a defensible "nearest manager-sized / upper median" choice, but the report and
  `request_prompt.json` call it "the median" and the rule "ties/nearest" does not say the tie was broken
  upward. Reword to "upper-median / nearest-to-median tie broken upward (2925 chars)".
- **m2 — cross-host clock skew (~32.6 s) is not disclosed.** A concurrent check gives Mac
  `1795228823.68`, TASL-7 `1795228823.92`, TASL-2 `1795228856.49`: TASL-2's clock is ~32.6 s ahead. Therefore
  `calls_tasl2.json` `started_utc 02:31:11Z` / `finished_utc 02:31:38Z` are TASL-2-clock times
  (≈02:30:38–02:31:05 on TASL-7), and they line up with the TASL-7 server log's three requests at 1.57/2.01/
  2.04 min and cleanup at 2.42 min. The report's absolute times are TASL-7 times; it should say the two
  capture clocks differ so an auditor does not compare them directly.
- **m3 — the "TASL-2 GPU busy ≈3.9 GiB / 83 % throughout" claim has no capture in the bundle.** It appears in
  the report and `SUMMARY.json` disclosure 7 but in no `calls_tasl2.json` field or other capture; TASL-2's GPU
  is 353 MiB / 0 % now, and a retroactive check cannot establish "throughout". Add a TASL-2 `nvidia-smi`
  capture at call time or soften to "reported by the operator, not captured".
- **m4 — the "exact launch" text is not the exact launch.** `scripts/launch.sh` passes
  `-E PYTHONDONTWRITEBYTECODE=1` and the absolute script path; the report's launch snippet and
  `launch_spec.json` `cgroup_launch` omit that `-E` and use `bash scripts/serve.sh`. `commands_and_sequence.txt`
  has the `-E` and the absolute path. Make the report and `launch_spec.json` byte-accurate, or state that
  `launch_spec` is a normalised rendering.
- **m5 — the host-check prerequisite is itself only conditionally accepted.** The host-check report sha is
  unchanged (`0150c80a…`) and its status line still reads "PASS for all seven TASL-7 host conditions"; the
  host-check review's C1–C3 are therefore still open. The smoke cites the check as an accepted precondition
  without saying so. Add "the host check is ACCEPTED with conditions C1–C4; C1–C3 (report/record text) are
  still outstanding; no CUDA-IPC credit is taken from C6".
- **m6 — authority record.** `R1-T1-HOST-TASL` is not in committed `docs/r1/PLAN.md`, and the only written
  scope text (host-check report) explicitly says "no proposer llama-server start". The smoke record should
  quote the lead/author delegation that authorized the start (the packet/instruction text), or reference the
  host-check STOP/GO paragraph that says the proposer/server smoke "may proceed after independent review".
- **m7 — "Only the new smoke run root … exist as new artifacts" is not exact.** It conflicts with the
  report's own disclosure 7 (the TASL-2 `providers.cpython-310.pyc` is a new artifact), and the preflight's
  `git status` on TASL-7 moved the metadata mtime of `autoresearch_harness/.git` and
  `.git/worktrees/harness_cond7a_20261121_t7` to 02:32:01Z (no file inside changed; a transient
  `index.lock`). Add these to a single "host-side exceptions" list, as the host-check review's m3 did for
  `gpu0.lock`.
- **m8 — the "no files outside the smoke dir" scan has no recorded command.** `new_files_outside_smoke.txt`
  contains only section headers; the report cites a specific scan scope (depth-3 `~/r1_trackp`, `~`, `/tmp`).
  My independent re-scan agrees (no new files), but record the exact `find` command/parameters in the capture.
  Also "no `/tmp` leftovers" should read "no leftovers of ours": `leftovers_after.txt` lists a pre-existing
  `hf_risk_smoke.py` owned by another user.
- **m9 — the request omits the D26 manager seed.** The exam/sweep-2 manager call carries the D26 deterministic
  seed (temperature 0.2 with the D26 seed, R1-MAIN-PROPOSER (b)/sweep-2 note); the captured request body has
  no `seed`, and `props.json` shows the server default `seed = 4294967295` (random). For a latency/parse
  smoke this is harmless and the report does not claim seed reproducibility, but if the record implies an
  exam-identical request path it should add the seed or state the omission explicitly.
- **m10 — "grammar-constrained output leaves no room for a thought prefix" is an inference, not a logged
  fact.** The `-lv 4` server log has no grammar/response_format line; what is evidenced is
  `completion_tokens == predicted_n`, pure-JSON content and no thought text. Rephrase as "no thought tokens
  were observed (bounded, finish=stop); the strict `json_schema` grammar is the likely reason, stated as an
  inference", or add a log/capture that shows the grammar was applied.

## Conditions

These are record/gate/text conditions; none requires re-running the smoke (the engineering facts are
reproducible from the delivered bytes plus the live host).

- **C1 (resolves M1, before the smoke is cited as satisfying the accepted host-gate conditions).** Obtain and
  record an explicit author/lead amendment of the host-check review's C4 for proposer-server runs (e.g.,
  `MemoryMax=48G` + `MemorySwapMax=0` with the 19.6 GB-model rationale) or an explicit waiver. Until then, do
  not cite this run as "C4 operating conditions kept" — cite it as "C4 mechanism kept; 8 G cap not applicable
  to the 19.6 GB server, amendment pending".
- **C2 (resolves M2).** Replace the literal-`.51` numbers in the report, F1 and `SUMMARY.json` with the
  captured values (`/health` 15.0057 s `TimeoutError`, `/v1/models` 1.067 s `OSError(101, Network is
  unreachable)`; conclusion unchanged), and cite or drop the uncaptured "0.185 s". The `commands_and_sequence`
  `curl --max-time 8` note may stay only if its own output is captured or it is labelled as an illustrative
  command.
- **C3 (resolves m1).** Fix the prompt-selection wording in the report and `request_prompt.json` (median
  2913.5; chosen 2925 = upper middle; tie broken upward).
- **C4 (resolves m2).** Disclose the TASL-2 clock offset (≈+32.6 s) and that `calls_tasl2.json` UTC stamps are
  TASL-2 clock; keep all absolute cross-host comparisons on the TASL-7 host log (or add a synchronized
  timestamp capture).
- **C5 (resolves m4, m7, m8).** Make `launch_spec.json`/report/`commands_and_sequence.txt` agree (include
  `-E PYTHONDONTWRITEBYTECODE=1` and the absolute `serve.sh` path), list the TASL-2 pyc and the transient
  `.git` metadata as declared host-side exceptions instead of "only new artifacts", record the exact
  new-files scan command, and qualify the `/tmp` sentence.
- **C6 (resolves m5, m6).** Record the delegation text for the start (the host-check's recorded scope says
  "no proposer llama-server start"; the record must carry the lead/author instruction that changed that), and
  state that the host check is cited as ACCEPTED-with-conditions with C1–C3 still open and no CUDA-IPC credit.
- **C7 (resolves m3, m9, m10).** Add a capture or soften the TASL-2 GPU-busy claim; state that the request
  omits the D26 seed (or add it); rephrase the thinking-off grammar sentence as an inference or evidence it.

## Verdict

**ACCEPTED** for the **ENGINEERING_ONLY** TASL-7 proposer llama-server smoke purpose: identity, exact flags,
single `.51`-only start/stop, the flock lease with untouched lease logs, three real manager-sized calls served
from TASL-2 through the shared-node `.50` alias, 3/3 six-key parses, bounded generation, and a provably
untouched attempt-1 archive — all independently re-verified live, not just from the delivered hashes. **0
BLOCKING, 2 MAJOR (M1 C4 8 G-vs-48 G reconciliation; M2 literal-`.51` figures contradicted by the capture),
10 MINOR.** This acceptance is for the engineering-smoke purpose only, not for a T1 label row, an exam attempt
or Track P evidence; and until C1 is resolved the run must not be cited as satisfying the accepted host-check
review's C4 as written.

---

### Reviewer's command record (21 November 2026; Europe/Berlin; 02:37–02:5xZ)

- **Mac** (`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`): read the report
  and all captures; `shasum -a 256 -c SHA256SUMS` (61/61 OK; `SHA256SUMS` sha `c5e3643e…`); recomputed
  `response_format_sha256` / `request_sha256` / prompt sha and decoded the prompt b64; read
  `docs/r1/PLAN.md`, the sweep-2 authorization note, the TASL-7 host-check report and review
  (`0150c80a…` / `18e261cd…`), the smoke report (sha `d27c3543…`); `git status`/`git log` in the ops worktree;
  no edits except this review.
- **TASL-7** (`ssh -o BatchMode=yes tasl7`, read-only): `sha256sum`/`stat` of binary and model; binary
  `--version`; full model sha256; host captures `sha256sum -c` and `SHA256SUMS` sha; run-root listing and all
  six run-script hashes; attempt-1 tree/content hash recomputation by pipe (no output files), counts/bytes and
  stat; both lease-log hashes and stat; `gpu0.lock` stat; current `pgrep`/`ss`/`flock`/`nvidia-smi`;
  cgroup/scope leftovers; `find -newermt` on the home buckets, `/tmp` and `/dev/shm`; prompt-set record 18 and
  median computation; `tailscale status` / `ip route get`; git metadata mtimes. No server start/stop, no file
  written, no probe re-run.
- **TASL-2** (`ssh -o BatchMode=yes portal_zhixu`, read-only): `providers.py` sha256 and branch/HEAD file
  reads; `manager_response_format` source; pyc existence/sha/mtime; `tailscale status` / `ip route get`;
  `nvidia-smi`; `find` for new files. One `git -C … status --porcelain` was run; like the host-check's own
  read-only status it may have created/removed a transient `.git/index.lock` (only directory mtimes moved; no
  file content changed). No writes otherwise.
- Not done: no server start/stop, no Ada or Track P action, no HTCondor/deepthought action, no push, no
  deletion, no archive/lease-log touch.
