# TASL-7 proposer llama-server engineering smoke (21 November 2026)

**Status: PASS — ENGINEERING_ONLY, one server start, three manager-sized calls from TASL-2 over
Tailscale, server stopped and verified gone.** This is **not** a T1 label run, not an exam attempt and
not a Track P action; Track P remained paused. Nothing was committed or pushed; the attempt-1 archive,
its EVIDENCE and both attempt-1 lease-log candidates are provably untouched. One server was started
**exactly once** and SIGTERMed after the calls; no `llama-server` remains and the GPU is idle.

Task authority: author row **R1-T1-HOST-TASL**, in the **R1-TRACKG-AR-U2-TASL2** context, delegated by
the lead. Preconditions accepted independently: TASL-7 isolation host check
(`TASL7_ISOLATION_HOST_CHECK_20261121.md`) and its review (`docs/r1/reviews/TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md`,
ACCEPTED with conditions C1–C4; operating set = per-command delegated cgroup for workers, GPU by UUID,
`shared_dev_shm: false`, documented `flock` lease, no CUDA IPC requirement).

## Verdict summary

| Item | Result |
|---|---|
| Server started once / stopped | **PASS** — lease `02:28:56Z`, health 200 `02:29:01Z`, SIGTERM `02:31:38Z`, exit in 1.0 s |
| Binary identity | **PASS** — sha256 `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`, `0.7.0-dev (build 1, commit 620d222)` |
| Model identity | **PASS** — sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` (19 598 489 952 B) |
| Exact exam flags | **PASS** — exact flag string below; only add-ons: `-a gemma4_31b` (optional alias) and `-m` model path |
| Bind | **PASS** — `100.106.74.51:8095` **only** (never `0.0.0.0`); `ss` shows the single listener |
| GPU lease | **PASS** — `flock -n -x` on `/home/dowling/r1_locks/gpu0.lock` held by the server's fd 9 for its whole lifetime; re-probe from another process = `LOCK_BUSY`; **no lease-log write** |
| GPU idle preflight / cleanup | **PASS** — 44 MiB, 0 %, no compute apps before; after stop 44 MiB, 0 %, 37 °C, no compute apps |
| TASL-2 reachability | **PASS via shared-node alias** — literal `100.106.74.51` times out from TASL-2; `100.106.74.50` (TASL-2's Tailscale alias for the same node) serves `/health` 200 and `/v1/models` 200 (see F1) |
| 3 manager-sized calls | **PASS** — 3/3 HTTP 200; wall p50 **3.76 s** (min 3.6555, max 3.9257); prompt 995 tokens; completion 124/124/115; `cached_tokens` 0; finish `stop` |
| JSON schema parse | **PASS** — 3/3 replies parse to exactly the six required `manager_proposal/v1` keys |
| Server cleanup | **PASS** — no `llama-server`, port 8095 free, flock free, scope collected, cgroup memory released |
| Preservation | **PASS** — attempt-1 archive byte-identical pre/post (tree `299237d0…`, content `af7ede86…`); both lease logs sha256+stat identical; `gpu0.lock` stat identical; no file created outside the new smoke dir |

No STOP condition was triggered. The one operational surprise (F1, Tailscale alias) is a topology
fact, not a smoke failure: the server bound to the mandated address and served TASL-2.

## Host and inputs

- TASL-7 (`ssh -o BatchMode=yes tasl7`), uid/euid 1011 `dowling`, non-root, Linux `6.8.0-149-generic`,
  Ubuntu 22.04.5, 62 GB RAM (64 001 MB visible, ≈60 GB available), RTX 4090 24 564 MiB, driver
  `580.178.04`, GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, `/` 514 GB free.
- Run root (new, on TASL-7): `/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121/`
  (`scripts/`, `captures/`, `records/`). No file was created on TASL-7 outside this run root
  (`captures/new_files_outside_smoke.txt` is empty).
- Reported captures copied to this report's sibling
  `TASL7_PROPOSER_SMOKE_20261121_captures/` (62 files, 968 KiB; `SHA256SUMS` covers 61 files,
  `sha256 = c5e3643e2c65bb38df66c1c9a49e3f60607376d0b340e69f751f6e7f1cd0d66d`, verified both on
  TASL-7 and locally with `shasum -a 256 -c SHA256SUMS`; `scripts/` inside the bundle holds the exact
  run scripts).
- Frozen prompt set: `/home/dowling/exam-x/frozen_inputs/trackx_stagea_promptset_20261031/prompts.jsonl`
  (50 records; file sha256 in `captures/request_prompt.json`).
- Schema provenance: generated on TASL-2 from
  `/home/dowling/r1_trackp/autoresearch_harness/src/autoresearch/llm/providers.py`
  (harness `897d83c8efa364ec2fdd37288241cc42e01d7274`, branch `trackp-20261026`; file sha256
  `de343bf77003c943ed95eae98ed7dc84540e788dcfa178debfc4be6425417247`), loaded standalone as
  `manager_response_format("manager_proposal/v1")`.

## Exact launch (once)

Identity verified **before** start (`captures/binary.identity.txt`, `captures/model.identity.txt`;
re-hashed identically after stop, `captures/identity_after.txt`):

```
/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server
  b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b
  version: 0.7.0-dev (build 1, commit 620d222), built with GNU 11.4.0 for Linux x86_64

/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf
  2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
```

The server was launched exactly once, inside a live delegated per-command cgroup, with the generated
argv in `captures/launch_spec.json`:

```
systemd-run --user --scope --unit=tasl7-proposer-smoke-20261121 --collect \
  -p Delegate=yes -p MemoryMax=48G -p MemorySwapMax=0 \
  -E XDG_RUNTIME_DIR=/run/user/1011 -E DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1011/bus \
  -- timeout --signal=TERM --kill-after=30 3600 bash scripts/serve.sh
```

and `scripts/serve.sh` (the process that owns the lease):

```
exec 9>>/home/dowling/r1_locks/gpu0.lock
flock -n -x 9                       # no lease-log write anywhere
export CUDA_VISIBLE_DEVICES=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
exec /home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server \
  -m /home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf -a gemma4_31b \
  -c 32768 -ngl 999 -np 1 --jinja \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --host 100.106.74.51 --port 8095 --no-webui -lv 4
```

The launched cmdline was verified from `/proc/<pid>/cmdline` and `systemctl --user status` and matches
one-for-one (`captures/poststart_state.txt`). `-lv 4` and `--no-webui` are in the specified flag string
(non-numeric differences disclosed by the task); `-a gemma4_31b` is the permitted optional alias.

## GPU / VRAM / cgroup

| Phase | nvidia-smi (GPU 0, UUID `GPU-ab72fb4a-…`) |
|---|---|
| before start | 44 MiB, 0 %, 36 °C, 14 W, **no compute apps** |
| loaded, idle | **21 565 MiB used** (compute app 21 516 MiB, reserved 493 MiB), 39 °C, 64.8 W, 0 % |
| after 3 calls | 21 585 MiB used (app 21 536 MiB), 42 °C, 65.8 W, 0 % |
| after stop | **44 MiB, 0 %, 37 °C, no compute apps** (three settled samples) |

- Delegated scope: `tasl7-proposer-smoke-20261121.scope`, `Delegate=yes`, `memory.max = 51 539 607 552`
  (48 GiB), `memory.swap.max = 0`, `nsdelegate` present, cgroup `cgroup.kill`-capable v2 subtree
  (`captures/poststart_state.txt`).
- Server cgroup memory: `memory.current` 374 MB at start, `memory.peak` ≈ 1.12 GB after the calls.
  Host `VmHWM` 19.47 GB during load (GGUF read-through), `VmRSS` 1.61 GB → 2.34 GB after the calls.
- `CUDA_VISIBLE_DEVICES = GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` (GPU named by UUID, as C4 requires).
- `-lv 4` memory breakdown at exit: CUDA0 total 24 071 MiB = free 2 486 + self 21 069
  (model 18 675 + context 1 997 + compute 396) + unaccounted 515; host self 1 179 MiB.

## TASL-2 reachability

TASL-7 is a **shared Tailscale node**: TASL-7's own tailnet address is `100.106.74.51`, while TASL-2's
tailnet sees the same node (`tasl-7.tail119748.ts.net`) under the shared-node alias `100.106.74.50`.
TASL-2 has no route to `100.106.74.51` (its kernel routes it out of the LAN gateway: "network
unreachable"; TCP and `curl` time out after 8 s). Traffic that TASL-2 sends to `.50` arrives on TASL-7
as `.51` (confirmed independently: an established ssh connection to this host has local address
`100.106.74.51`), so the mandated `.51`-only bind is served to TASL-2 through the `.50` alias.

| From TASL-2 | literal `http://100.106.74.51:8095` (as instructed) | shared alias `http://100.106.74.50:8095` |
|---|---|---|
| `/health` | **TimeoutError after 15.0057 s**, HTTP 000 | **200** `{"status":"ok"}`, 0.185 s first probe (0.102 s inside client) |
| `/v1/models` | **OSError(101, Network is unreachable) after 1.067 s**, HTTP 000 | **200**, model `gemma4_31b`, `n_ctx` 32768, 0.026–0.028 s |

The server bind itself stayed exactly `100.106.74.51`, and its only listener is `100.106.74.51:8095`
(`ss -ltnp`). The literal `.51` URL from TASL-2 was tried first and its failure is recorded in
`captures/calls_tasl2.json` (`literal_health`, `literal_v1_models`); all measurements below use `.50`.

## Three manager-sized calls from TASL-2

Prompt: frozen Stage A record, chosen by the median prompt-text length over the 50-record set
(true median 2913.5 chars; the chosen 2925-char record is the upper-middle record): **node `openml_breast_w`, trial `openml_breast_w__s105-trial-007`**, prompt
2925 chars, prompt sha256 in `captures/request_prompt.json`. Only the prompt text was copied to
TASL-2 (base64 environment variable; the client writes no request/response files on TASL-2).

Request (identical for all three, sha256 in `calls_tasl2.json`): `model gemma4_31b`; one user message
with the frozen prompt; **`temperature: 0.2`**, **`cache_prompt: false`**, **explicit** in every
request; `response_format = manager_response_format("manager_proposal/v1")` (strict `json_schema`;
schema sha256 `682134ae285d5c9ec475b6e2ecdbe51e7a12623b2b1e92723987c498e73644c3`, six required
string keys `rationale, summary, objective, param, old_value, new_value`); **`max_completion_tokens: 16384`**
(the exam-wide proposer cap, R1-EXAM-B1-TRUNCATION-INVALID); `stream: false`. Thinking off was requested
only through the specified server kwarg `--chat-template-kwargs '{"enable_thinking":false}'`.

| call | HTTP | wall (s) | prompt tokens | completion tokens | cached tokens | finish | 6-key JSON parse | prompt eval | generation |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 200 | 3.9257 | 995 | 124 | 0 | stop | **PASS** | 995 tok / 591 ms (1683 tok/s) | 124 tok / 3152 ms (39.0 tok/s) |
| 2 | 200 | 3.7600 | 995 | 124 | 0 | stop | **PASS** | 995 tok / 545 ms (1825 tok/s) | 124 tok / 3146 ms (39.1 tok/s) |
| 3 | 200 | 3.6555 | 995 | 115 | 0 | stop | **PASS** | 995 tok / 546 ms (1823 tok/s) | 115 tok / 2918 ms (39.1 tok/s) |

**Latency (wall): p50 3.7600 s, min 3.6555 s, max 3.9257 s, mean 3.7804 s (n = 3).**
`cached_tokens: 0` on all three confirms `cache_prompt: false` was honoured (each call re-processed the
full 995-token prompt). No call was truncated (`truncated = 0`). Each reply is a valid bounded manager
proposal; all three chose `C: 0.3 → 0.1` (temperature 0.2; two rationales are near-identical, one differs
slightly). Full content and parsed objects are in `captures/calls_tasl2.json`; the proposal text is
short (326–383 chars), not a truncated or rambling answer.

`-lv 4` confirms the sampler actually used `temp = 0.200` and that the prompt cache was not reused
(`cached n_tokens = 0`, `memory_seq_rm [0, end)`), `captures/server.log`.

### Thinking-off evidence (build finding F2)

The server log warns:

```
0.00.032.808 W Setting 'enable_thinking' via --chat-template-kwargs is deprecated.
             Use --reasoning on / --reasoning off instead.
0.03.612.344 I srv init: init: chat template, thinking = 1
```

Despite the deprecated kwarg, **no thinking text entered the output**: for every call
`completion_tokens == predicted_n` (124/124, 124/124, 115/115), the content is the constrained JSON
object alone (starts with `{`, 326–383 chars) and no reasoning/thought channel text appears. The
grammar-constrained structured output leaves no room for a thought prefix, so the calls were, in
effect, thinking-off. This is disclosed as a build-behaviour observation (flag kept exactly as
specified) and is analysis only, not a flag change. `captures/thinking_analysis.txt`,
`captures/server_log_warnings.txt`.

## Server health/metrics and other observations

- `/health` 200 `{"status":"ok"}` (0.26 ms on-host, 0.10–0.19 s from TASL-2 including connection),
  `/v1/models` 200 `gemma4_31b` (`n_params` 30 697 345 596, ftype `Q4_K - Medium`), `/props` 200
  (`captures/props.json`).
- `/metrics` returns **HTTP 501** ("does not support metrics endpoint. Start it with `--metrics`"):
  `--metrics` is not in the exact exam flag string, so server metrics were not collected; VRAM/utilisation
  were taken from `nvidia-smi` instead. Disclosed.
- Additional build warnings in `server.log`, disclosed: `--no-webui` is a deprecated alias (use
  `--no-ui`), and "security: no API key is set and CORS allows all origins". The server was bound only
  to the Tailscale address (no LAN/0.0.0.0 listener), which limits that exposure to the tailnet; the
  flags were kept exactly as specified.
- The model load read 19.6 GB through page cache; because the file had just been hashed, start-to-health
  was only ~5 s (load itself completes before `health` turns 200; warm start is not a defect).

## Stop and cleanup

`SIGTERM` was sent to PID 187900 at `2026-11-21T02:31:38Z` (`scripts/stop.sh`, `captures/stop.txt`);
the server logged `cleaning up before exit` and exited **1.0 s** later at `02:31:39Z`. Verified after
stop (`captures/stopped_state.txt`, `captures/gpu_idle_after_stop.txt`, `captures/leftovers_after.txt`):

- `pgrep -af llama-server` → none; port `8095` free; `flock -n` on `gpu0.lock` → free;
- no compute apps; GPU 44 MiB / 0 % / 37 °C; scope `tasl7-proposer-smoke-20261121.scope` collected
  (`--collect`), no `run-*` scope or cgroup leftovers, no `/tmp` leftovers;
- the 3600 s `timeout(1)` watchdog never fired (it was a safety net only).

## Preservation and host-state proof

- **Track P attempt-1 archive** `/home/dowling/r1_trackp/runs/p3a_operator_20261027` (incl. `EVIDENCE`,
  `journal.jsonl`): read-only full-content fingerprint before and after — **identical**:
  `tree_sha256 299237d06012f42b13cff4b476b2167bec55fa2c2463f056567f986ff7e1e003`,
  `content_sha256 af7ede86da7abbe36ff4ec35ef2029ce4e6233afd5fbe4f49e14684c4d16e965`,
  1040 entries / 724 files / 11 925 743 308 B (`captures/attempt1_compare.json`). These values match the
  accepted host-check baseline exactly.
- **No lease-log write.** `/home/dowling/r1_locks/trackp_evidence.log`
  (`2e762c16…`) and `/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl` (`e97e03d2…`) are sha256- and
  stat-identical before/after; the lease was `flock` only.
- `gpu0.lock` stat is identical before/after (size 0, mtime/ctime `2026-11-20 17:59:38.612690398 -0800`,
  inode 56251186) and was held via an append-mode fd, so the lease did not even touch the file.
- No TASL-7 file was created outside the new smoke dir (scan of `~/r1_engineering`, `~/r1_locks`,
  `~/r1_trackp` depth 3, `~/` and `/tmp` newer than the run start is empty); the harness worktrees
  (`harness_cond7a_20261121_t7`, `autoresearch_harness`) are still clean at their recorded tips; boot
  id, kernel, `/dev/shm` (15 pre-existing objects) and disk (514 GB free) unchanged.
- **TASL-2 was not otherwise modified** by the smoke: the client ran from an environment variable and
  wrote nothing except Python bytecode `__pycache__/providers.cpython-310.pyc` generated when the schema
  module was imported from the TASL-2 harness checkout (CPython-3.10 bytecode only, gitignored; the
  worktree `git status` is clean and no source file changed). TASL-2's GPU was busy with an unrelated
  pre-existing workload (≈3.9 GiB / 83 %) throughout; the smoke used only TASL-2 CPU/network.
- No deletion, no move-aside, no commit, no push; Track P paused. Only the new smoke run root on TASL-7
  and this report + captures bundle in the Mac `ops-tasl-20261116` worktree exist as new artifacts.

## Disclosures / deviations (complete list)

1. **F1 — Tailscale address**: `100.106.74.51` is TASL-7's own-tailnet IP and is **not routable from
   TASL-2**; TASL-2 reaches the identical node at the shared-node alias **`100.106.74.50`**. The literal
   `.51` URL was attempted from TASL-2 first (timeouts recorded); it is not a server fault. The bind was
   the mandated `.51` only. Any future TASL-2→TASL-7 client must use `.50` (or a Tailscale share/IP
   change would be needed for `.51`).
2. **Cgroup memory cap**: the **proposer service owner scope** used `MemoryMax=48G` because the 19.6 GB GGUF
+ KV/context cannot fit 8G; the host-check C4 8G cap applies to **worker runs** and no worker ran here, so this is
**not an isolation waiver** but a service-scope exception recorded here. The delegated scope used `MemoryMax=48G`, not the 8G worker cap — the 19.6 GB GGUF
   (plus page cache and CUDA host memory) cannot be served under 8G. `Delegate=yes`, per-command scope,
   GPU-by-UUID, `flock` lease and no-CUDA-IPC conditions were all kept.
3. **Optional alias** `-a gemma4_31b` added (explicitly allowed by the task); `-lv 4` / `--no-webui`
   are part of the specified flag string and disclosed as non-numeric differences by the task.
4. **`/metrics` unsupported (501)** because `--metrics` is not in the exact exam flags; VRAM came from
   `nvidia-smi`.
5. **F2 — `enable_thinking` kwarg is deprecated in this build** (warning + `thinking = 1` initial
   template default); no thinking tokens were emitted and all outputs are pure six-key JSON.
6. **`--no-webui` is a deprecated alias** in this build, and the server warns it runs without an API key
   / with permissive CORS; it listened only on the Tailscale IP, and the exact exam flags were kept.
7. **TASL-2 bytecode**: the schema import generated `providers.cpython-310.pyc` (bytecode only,
   gitignored, harness worktree still git-clean) — disclosed rather than deleted, per the no-deletion
   rule.

## Paths and hashes

| Artifact | Path / hash |
|---|---|
| Host run root (new) | `/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121/` |
| Host captures | `…/captures/` (61 files + `SHA256SUMS`; scripts in `…/captures/scripts/`) |
| Host `SHA256SUMS` | `sha256 = c5e3643e2c65bb38df66c1c9a49e3f60607376d0b340e69f751f6e7f1cd0d66d` |
| This review bundle | `docs/r1/reports/trackg_g0_20261117/TASL7_PROPOSER_SMOKE_20261121_captures/` (62 files, `shasum -c` OK) |
| Binary sha256 | `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b` |
| Model sha256 | `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` |
| Launched argv | `captures/launch_spec.json`, `captures/poststart_state.txt` |
| TASL-2 client script sha256 | `310230d7f29b12f7623b2b3cc735bb146b38807a8a438ffc0d4748cddbb0c906` (`captures/client_tasl2.py.sha256`) |
| Attempt-1 before/after | `captures/attempt1_{before,after}.*`, `captures/attempt1_compare.json` |

This report and its captures are **uncommitted** in `ops-tasl-20261116` (HEAD `ebe03cd5`), with **no
push**. The next step for a future T1 label run is a separate authorization; nothing here is evidence
for a T1 label row.

## Review-condition notes (21 Nov)

- C1-C4 host-check citations are in `TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md`; the literal `.51` probe timings are now corrected to the capture values (15.0057 s TimeoutError; 1.067 s OSError(101)); the `.50` alias values are unchanged.
- The prompt median is 2913.5 chars (2925 is the upper-middle chosen record); the three request timestamps have a ≈+32.6 s cross-host clock skew (TASL-2 vs TASL-7), disclosed; the request omits an explicit D26 seed in this engineering smoke, disclosed; the 'GPU busy 3.9 GiB/83%' statement has no capture and is withdrawn; grammar suppression is an inference only.
- Server owner cgroup 48G is a service-scope exception, not a worker isolation waiver; the worker isolation cap remains 8G per host-check C4.
