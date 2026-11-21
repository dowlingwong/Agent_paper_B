# R1-TRACKG-AR-COND7 option A — round-4 infrastructure-retry session — RESULT (21 November 2026)

**Status: STOP_EXTERNAL_CONTENTION — the bounded retry window allowed two fresh attempts; both were launched on
cards verified idle (0 compute apps, ≥ 40 GiB free) and both had another user's GPU job start on the same card
within 1–3 minutes; the monitor aborted each attempt under the no-shared-card rule. Neither attempt produced any
run record, so no clean isolated smoke and no measured transfer slowdown exist. Attempt cap (2/2) was reached
~2 h 20 min before the 3 h window end; the session therefore stopped. Every attempt is preserved (no deletion,
no retry after a code/unit failure; this session stopped for external contention only).** This round was
authorized by the coordinator as an **infrastructure retry** of the one failed U2 smoke (distinct from the U2
one-smoke rule), after the 20 Nov attempt at `ar_cond7a_smoke_20261120T223548Z` failed with a CUDA OOM caused by
a co-tenant that joined its card mid-run (see that result directory).

## 1. Authority / objects

- PLAN row **R1-TRACKG-AR-COND7** option A (CUDA IPC removed from the result path; logits to the parent through
  the CPU `memfd`; `cuda_open` init; pins updated; one isolated smoke then U2; slowdown measured/disclosed), on
  published main `df58bcd5…` (`docs/r1/PLAN.md:1317`); accepted code review
  `docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` sha256 **`261a03e9…`** (ACCEPTED code, C1–C6), and
  its fixed code-unit report at the branch tip sha256 **`370782ab…`**; harness-isolation fix review
  `c8e468c7…` condition C3.
- Kit branch **`mac-trackg-iso-ar-cond7a-20261120`** @ **`73303380197477df971e865440d0ae11135fe1b3`** (base
  `448f6820…`), pushed to harness origin; executed from the dedicated Ada worktree
  `/home/dowling/r1_trackg_20261117/harness_iso_ar_cond7a_20261120` (created in the previous round, HEAD `==
  7330338` and tracked-clean throughout; **no code change this round**; existing worktrees untouched).
- Executed command: one `python -m tests.trackg.port_smoke_gpu --node autoresearch_fixedtokens --gpu-uuid
  <idle> --cpus <cpus> --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0 (enforced cgroup)" --runs-root <attempt evidence dir>/runs --provisional-timeout 1800` in a
  delegated 8 GiB user scope with the torch312 environment, `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=""`, taskset,
  gate re-checked immediately before launch and a **fresh run root/evidence dir per attempt**.

## 2. Retry session setup (bounded watcher)

- Session dir: **`/home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z`** (copied here);
  start **2026-11-20T23:28:47Z**, **3 h window** to 2026-11-21T02:28:47Z, **max 2 fresh attempts**.
- Launch gate per attempt: card must show **0 live compute apps and ≥ 40 GiB (40,960 MiB) free**; the Paper A gate
  is re-checked immediately before launch (`clear_finished`, key false, `paper_a_processes: []`,
  `unidentified_apps: 0`, newest configured `live_*`); after launch a 25 s monitor watches the used card for
  other users' compute apps; two consecutive foreign-app ticks ⇒ **abort the attempt (cgroup.kill)** and record
  it as external-contention STOP, never a shared-card run.
- No card qualified during the initial wait; the two cards that did qualify were taken by other users within
  1–3 minutes (see below). No code/unit failure occurred in either attempt (none ran a single smoke run
  record).

## 3. Attempt 1 — external co-tenant abort (0 run records)

- Candidate **card 5 `GPU-5357dc5f-5d1d-af80-a3f4-3eb5aeb38f0d`** at **23:40:00Z**: **48,427 MiB free, 0 compute
  apps, 0 % util** (qualifies with 40 GiB margin); gate pre-check JSON `gate_precheck_234000Z.json` sha
  `a50e9850…` (UTC 23:40:00Z, `clear_finished`, unidentified 0).
- **Launch 23:40:04Z**, cpuset `94,93,85,61,59,58,42,41`; attempt evidence
  `attempt1_GPU_234004Z/` (fresh run root). Inside-scope prechecks PASS: `envs/torch312` Python 3.12.16, torch 2.6.0+cu124; env-freeze sha `d2e70fe4…` == expected; data manifest `ab7186d2…` == expected; spec
  `raw_sha256 5c1bdf3d…`; committed pin `147f0d35…`, deployed pin expected `069e987a…`; `import`/`smoke_entry`
  OK; **cgroup probe `memory.max=8589934592`, `memory.swap.max=0`**; CUDA-IPC AST scan NONE.
- **Co-tenant arrival (monitor, 25 s ticks):** 23:40:29Z foreign 0 / free 46,854; 23:40:55Z foreign 0 /
  44,754; **23:41:20Z foreign 3 / 42,832**; **23:41:46Z foreign 5 / 32,336** — zihaozhao processes
  `527019/527020/527021` (3,090 MiB each) and `532550/532656/532681` (1,328 MiB each).
- **Abort 23:41:50Z** (`CONTENTION_ABORT.txt`, census `contention_abort_census.txt`, free 32,336 MiB at abort);
  cgroup.kill; runner `DONE_STOP` **23:41:52Z**; **0 `run_record.json`**; classification **external
  contention**. Attempt summary sha `57bc304a…`, monitor log sha `10646826…`.

## 4. Attempt 2 — external co-tenant abort (0 run records)

- Candidate **card 4 `GPU-379470db-a02e-893a-57a0-71b119173890`** at **00:06:24Z**: **48,427 MiB free, 0 compute
  apps, 0 % util**; gate pre-check JSON `gate_precheck_000624Z.json` sha `ce19ef33…` (UTC 00:06:24Z,
  `clear_finished`, unidentified 0).
- **Launch 00:06:28Z**, cpuset `90,73,45,41,40,39,38,35`; evidence `attempt2_GPU_000628Z/`. Prechecks PASS
  identically (env freeze `d2e70fe4…`, data `ab7186d2…`, spec `5c1bdf3d…`, pins `147f0d35…`/`069e987a…`, cgroup
  probe 8589934592/0).
- **Co-tenant arrival (monitor):** 00:06:54Z foreign 0 / 47,889; 00:07:19Z foreign 0 / 47,194; **00:07:45Z
  foreign 1 / 43,980**; **00:08:11Z foreign 1 / 25,872** — hefeifeijiang pid `772533`, **18,876 MiB** on the
  card.
- **Abort 00:08:14Z** (census `contention_abort_census.txt`; free 25,872 MiB); DONE_STOP **00:08:16Z**;
  **0 `run_record.json`**; classification **external contention**. Attempt summary sha `19601a77…`, monitor log
  sha `36297c75…`.
- **Note on the abort policy (important):** the monitor aborts as soon as another user's app is present for two
  consecutive 25 s ticks, because the round-4 clean-attempt rule is "no shared card". At this abort the card still
  had **25,872 MiB free** with the co-tenant using 18,876 MiB, so attempt 2 had **not** failed (no OOM, no run
  record, no checklist reached); the abort is a deliberate clean-measurement/no-shared-card control, not an
  external failure of a running smoke. The same applies to attempt 1 (abort at 32,336 MiB free). Under a policy
  that allows a mid-run co-tenant as long as the smoke does not fail, attempt 2 might have completed — but its
  slowdown would have been co-tenant-contaminated, which the "clean attempt" requirement excludes.

## 5. Session stop — exact STOP evidence

- `session_status.txt` sha **`8a2d1563…`**: `session=STOP_EXTERNAL_CONTENTION`, `attempts=2`,
  `last_ev=…/attempt2_GPU_000628Z`, `stopped_utc=2026-11-21T00:08:25Z` (≈2 h 20 min before the 3 h window end,
  but the **2-attempt cap** is reached).
- Watcher log sha **`64486405…`** records the whole sequence: all 8 cards busy from 23:28Z; candidate card 5 at
  23:40:00Z; launch/abort attempt 1; waiting; candidate card 4 at 00:06:24Z; launch/abort attempt 2; stop.
- Host contention at session end (00:09:56Z census, sha `6d92f8b8…`): all 8 cards carrying other users' apps
  (hongkunyang 3 cards >1 d; asif 2 cards; vla-reasoning / zihaozhao / hefeifeijiang on the rest). Freed cards
  were re-grabbed within ~1–3 min in both attempts. This is the concrete reason no clean attempt exists.
- **No clean attempt succeeded**; none of the clean-attempt requirements were reachable this round:
  `CHECKLIST_E_PASSED` **not produced**, **0 executed records** (not 8 + refused s001), **no B2 repeat**, **no
  measured slowdown vs 17 Nov 564 s / B1 67.901 s**, **no peak host RSS/VRAM**, **no per-run record hashes**. The
  pre-launch checks that did run (HEAD 7330338, env/data/spec/both pins, cgroup 8G/0, gate, no-CUDA-IPC scan,
  private `/dev/shm` isolation template) passed on both attempts, but no run ever reached a record.
- The previous round's one failed smoke (baseline CUDA OOM under co-tenant, record
  `bf41cc7c…`, evidence `docs/r1/reports/trackg_g0_20261117/ar_cond7a_smoke_20261120T223548Z/`) remains the only
  executed run record for this node; it also failed for external co-tenancy, not for option-A code.

## 6. Attestation / preservation

- Every attempt directory, monitor log, abort census, gate pre-check, launch log and runner evidence is
  preserved (no deletion); the session dir is copied here unchanged (40 M). No push, no commit; the new worktree
  remains at HEAD `7330338` and tracked-clean; existing worktrees were not modified; data tree and pins untouched;
  no TASL-7/TASL-2, no HTCondor/deepthought; no shared-card launch (all launches at 0 apps/48,427 MiB).
- Recommendation: a clean attempt needs a card that stays free for the whole ~30–60 min smoke (or a reservation);
  with the host in this state, 40 GiB free at launch is not sufficient because other users start large jobs
  within 1–3 minutes. Two attempts were consumed, so this session ends as an external-contention STOP; a further
  attempt would need fresh coordinator authorization.

## 7. Evidence index (this directory)

`session_status.txt` (sha `8a2d1563…`); `watcher.log` (sha `64486405…`); `wait_census_latest.txt` /
`session_end_census.txt` (sha `6d92f8b8…`); `gate_precheck_234000Z.json` (sha `a50e9850…`) and
`gate_precheck_000624Z.json` (sha `ce19ef33…`); `attempt1_summary.txt` (sha `57bc304a…`),
`attempt1_monitor.log` (sha `10646826…`), `launch_attempt1.log` (sha `195bd97e…`), `attempt1_GPU_234004Z/`
(full runner evidence: prechecks, cgroup probe, env/data/kit/pins, contention abort + census, DONE_STOP,
RESULT_STATUS, samplers, verify/record outputs); `attempt2_summary.txt` (sha `19601a77…`),
`attempt2_monitor.log` (sha `36297c75…`), `launch_attempt2.log` (sha `d15d3d4d…`), `attempt2_GPU_000628Z/`
(identical structure); `references/` (fixed code report `370782ab…`, review `261a03e9…`, `code_change.diff`
`87d0de73…`, spec copy `5bdce00a…`, branch log); `scripts/` (retry runner, watcher, verifier, sampler-max).
`SHA256SUMS` covers every file. Raw evidence preserved read-only on Ada under the session dir
(no deletion).
