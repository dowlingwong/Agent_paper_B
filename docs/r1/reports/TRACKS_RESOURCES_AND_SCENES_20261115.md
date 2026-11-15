# Track S — resources used and scenes left in place (15 November 2026)

**AI-assisted (Claude, Mac agent). Inventory only; nothing was moved, changed, stopped or deleted.** Written for
the author's STOP 4 decision (`R1-TRACKS-STOP4-END`, draft row `proposals/PLAN_ROW_R1-TRACKS-STOP4-END_DRAFT_20261115.md`).
The decision leaves every Track S scene as it is; this file lists them so that any later clean-up is a separate,
informed author decision.

**How this was compiled.** The Mac agent has no server access. The host sections come from the committed records,
not from a fresh census:
- `docs/r1/STATUS.md` on `trackS-ops-20261030` @ `fab88fce`;
- the per-phase reports and their copy-back trees under `results/r1/tracks/`;
- operator runbook rev 3.3 (`13badb0d`);
- the B2 execution plan on `ops-b2-exec-20261115` @ `2f4970e5`.

Each host fact carries the date of its last record. The repository section was read from the Mac checkout on
15 Nov 2026 (read-only `git` commands; branch tips re-read for this revision).

## 1. Compute used

Session wall-clock from the copied-back manifests (`sessions[].start_utc/end_utc`), plus S0.1 runs whose start and
end are recorded in their reports. Each LLM session held the host's single RTX 4090 through `~/r1_locks/gpu0.lock`.

| Host | Phase (node) | Date | Hours | Source |
|---|---|---|---|---|
| TASL-7 | Phase 0 smoke (`tabular_mlp`) | 30 Oct | 0.10 | `results/.../tabular_mlp/smoke/manifest.json` (2 sessions) |
| TASL-7 | S0.1 (`digits_mlp`, re-run b) | 13 Nov | 0.57 | `reports/TRACKS_S01_TASL7_RESULT_20261113.md` (11:13:01–11:47:17Z) |
| TASL-7 | S0.4 + pause drill (`tabular_mlp`) | 14 Nov | 0.44 | `tabular_mlp/s04_t7_20261114/manifest.json` (2 sessions) |
| TASL-7 | S0.1 (`tabular_mlp`, k = 2) | 14 Nov | 0.61 | `reports/TRACKS_S01_T7_TABULAR_20261114.md` (23:11:05–23:47:41Z) |
| TASL-7 | S0.5 (`digits_mlp`) | 13–14 Nov | 2.46 | `digits_mlp/s05_t7_20261113/manifest.json` (2 sessions) |
| TASL-7 | S0.5 (`tabular_mlp`) | 15 Nov | 2.50 | `tabular_mlp/s05_t7_20261114/manifest.json` |
| TASL-2 | Phase 0 smoke (`digits_mlp`) | 30 Oct | 0.03 | `digits_mlp/smoke/manifest.json` |
| TASL-2 | S0.1 re-run (`digits_mlp`, k = 2 servers) | 8–9 Nov | 0.58 | `reports/TRACKS_S01_RERUN_20261109.md` (servers 23:59:57Z → launch returns 00:34:30Z) |
| TASL-2 | S0.4, stopped at the 2 % rule (`digits_mlp`) | 9 Nov | 0.36 | `digits_mlp/s04/manifest.json` (3 sessions) |
| TASL-2 | S0.4 re-run at pin `8237fd02` (`digits_mlp`) | 11 Nov | 0.74 | `digits_mlp/s04_rerun20261111/manifest.json`; the copy in `_to_delete/` is the same session |

**Totals tallied (lower bounds):** about 6.7 h on TASL-7 and 1.7 h on TASL-2.

Not tallied, because no start/end pair is in a copied-back manifest:
- TASL-2 and TASL-7: the 30 Oct S0.1 runs (Phase 1) and the D6 follow-ups F1/F2 (31 Oct, both hosts).
- TASL-7: the 31 Oct `tabular_mlp` S0.1 re-run marked INVALID.
- TASL-2: the 12 Nov S0.5 attempt. It started 19:55:59Z and was last seen at 20:02Z with 4 committed roots; the host
  went down and its end is unknown.
- TASL-7: the operator-stopped 13 Nov S0.1 (73 s).

CPU-only phases took seconds to minutes each: S0.5b (about 15 s per node), S1.1 (`digits_mlp`, `tabular_mlp`,
`openml_breast_w`), liveness and fit_prior.

**Calendar and people.** Track S ran from 29 Oct (host rows; adopted 30 Oct) to 15 Nov. It also took an operator agent
on the hosts, the Mac agent's review units, and the author's STOP rulings (STOP 0, 1, 3, 4, the TASL-2 outage, and
the host move).

## 2. Scenes left on the hosts

### 2.1 TASL-7 (last record: STATUS 15 Nov, after the tabular S0.5b)

**Process.**
- tmux session **`trks_watch`** running `bin/trks-watch`: Track S's watcher, started by the Track S operator.
- No `trks_llm` server session and no Track S collector.
- Lease `~/r1_locks/gpu0.lock` free; GPU idle (243 MiB).
- No Track S marker or `STOP` outside the finished phase directories.

**Work directory `/home/dowling/r1_tracks/`** (runbook §0.1 and Phase 0; approved by the author on 30 Oct):

| Path | Content (as recorded) |
|---|---|
| `bin/` | `trks`, `trks-run`, `trks-servers`, `trks-watch`, `trks-status`. `trks-status` was updated on 14 Nov to `PAPER_SHA 8237fd02…` (sha `70fbe8bd…`). |
| `venv/` | Python 3.11.18, frozen after Phase 0 (the same 65-package freeze as TASL-2, which has 3.11.17; digits host-move note) |
| `opt/llama.cpp/` | v0.7.0 @ `620d2225`, built for sm_89 |
| `models/` | manager GGUF `qwen2.5-coder-7b-instruct-q4_k_m.gguf`, sha256 `509287f7…` |
| `remotes/Agent_paper_B.git` | bare repo, fast-forwarded to `110b01a8` on 15 Nov |
| `work/Agent_paper_B` | paper checkout, detached at `8237fd02`, clean |
| `work/autoresearch_harness` | harness checkout, detached at `a3fedbb` |
| `launch/` | the launch scripts deployed from `r1/tracks/ops/launch/` (`tasl7_*.sh`) |
| `logs/` | `watch.log`, server logs `llama_18101`/`llama_18102` (append-only; S0.1 identity offsets recorded against them), `*.exit` lines, launch logs, `STOP_FILES.s04t_20261114T222237Z.txt` |
| `out/tabular_mlp/` | the 30–31 Oct scenes (`s01`, `s01_diag`, `s01_diag_f1`, `s01_diag_f2`, the INVALID 31 Oct S0.1 re-run, `s11`) and `out/smoke`, listed with sha256 in `reports/TRACKS_S04_T7_TABULAR_20261114.md` §1; plus `s04_t7_20261114`, `s01_t7_20261114`, `s05_t7_20261114` |
| `out/digits_mlp/` | `s01_t7_20261113` (empty, preserved after the operator-stopped probe), `s01_t7_20261113b` (the accepted S0.1), `s05_t7_20261113` (with `_to_delete/STOP.retired.20261114T103527Z`), and the copied prior `5c849d15…` |
| `scratch/tabular_mlp/`, `scratch/digits_mlp/` | per-unit working trees of every phase. The runbook keeps these "until Track S is closed" (S0.5b needed them). |

**Copied back.**
- On the Mac: every `out/` phase directory except three, whose raw files are on the host only:
  - the two digits S0.1 directories (the `s01_t7_20261113b` values are in its report);
  - the INVALID 31 Oct `tabular_mlp` S0.1 re-run (its two JSONs are hashed in the tabular S0.4 report §1).
- `scratch/` stays on the host only.

Disk: 526 G free (14 Nov).

### 2.2 TASL-2 (last record: 12 Nov before the outage; unreachable at every later check, last on 15 Nov)

**Process.**
- The S0.5 attempt (`digits_mlp`) was last seen running at 12 Nov 20:02Z, with 4 committed roots.
- `trks_watch` was recorded running after the S0.4 re-run (12 Nov, about 00:15Z); the outage record does not mention it.

Their state since the outage is unknown. The outage report says the S0.5 scene is preserved and is never resumed.

**Work directory `/home/dowling/r1_tracks/`.** Same layout as TASL-7: `bin/`, `venv/`, `opt/llama.cpp`, `models/`,
bare repo, `work/` detached at `8237fd02` / `a3fedbb` since 11 Nov.

`out/digits_mlp/`:
- `smoke`, `s01`, `s01_diag*`, `s11` (the 30 Oct S1.1 output), `s01_rerun20261109`;
- `s04`: the 9 Nov STOP scene, preserved by the STOP 3 ruling;
- `s04_r2_20261111`;
- `s05`: the 12 Nov partial pilot, never censused or copied back;
- the `scratch/` counterparts of all of these.

**Bare repo.** Behind; the push of the 14–15 Nov commits was deferred while the host was down.

**Outside the work directory.** The scratch pytest environment `/tmp/trks_pytest_20261111.FI7Fdoi8` from the 11 Nov
precondition test.

Disk: 187 G free (12 Nov).

### 2.3 Items that are live, not static (flagged; no action taken)

1. **The TASL-7 watcher keeps acting.**
   - While it runs, any priority marker makes it touch a `STOP` file in **every** `out/` directory with a
     `manifest.json`, finished Track S phases included (runbook §11.4). The B2 run uses such a marker
     (`trackx_evidence.active`), so when B2 creates it the finished Track S directories on TASL-7 will gain new
     `STOP` files on the host. (These records do not show whether B2 has started.)
   - The Mac copies are not touched. Of the TASL-7 directories with a `manifest.json` (per the copy-backs), the three
     13–15 Nov phase trees (`digits_mlp/s05_t7_20261113`, `tabular_mlp/s04_t7_20261114`, `tabular_mlp/s05_t7_20261114`)
     carry `SHA256SUMS` on the Mac. The old `out/smoke` tree has none; its file hashes are only in the table of
     `reports/TRACKS_S04_T7_TABULAR_20261114.md` §1.
   - The B2 execution plan already inventories these touches (`b2_exec_20261115/PLAN.md` step 5; `prechecks.sh`
     records the watcher and the existing `STOP` files).
   - Stopping the watcher would itself change the scene. Under the draft row, Track S processes are left as they are,
     so stopping it needs an author decision.
2. **TASL-2.** The S0.5 collector of 12 Nov is bounded by its 8 h deadline (`--deadline 28800`), so it cannot still
   be running unless the host froze. If the outage was network-only, the Track S servers (`trks_llm`), the watcher
   and the TASL-2 GPU lease `~/r1_locks/gpu0.lock` may still be held. The outage report's rule applies on return:
   read-only census only, the scene preserved, and the author decides.
3. **The lease file `~/r1_locks/gpu0.lock`** is a shared cooperative lock, not Track S property. Other tracks on
   these hosts use it as well.

## 3. Repository side (Mac checkout, read 15 Nov 2026)

**Branches.**

| Branch | Tip | Where |
|---|---|---|
| `trackS-ops-20261030` | `fab88fce` | local, `origin`; the Mac's `tasl7/…` ref is `fab88fce` (later than the `110b01a8` STATUS records for the bare repo, so a push after that record is implied); `tasl2/…` is `78a1b65e` (behind) |
| `trackS-20261029` (paper code) | `9bb64ba6` | local, `origin` |
| `docs/trackS-decisions-30oct` | `13badb0d` | local, `origin` |
| `mac-tracks-a2u-stale-20261111` | `c8b13b5d` | local, `origin`, `tasl2`, `tasl7` |
| `mac-tracks-s05-summary-20261114` | `3e0fa203` | `origin` |
| `mac-tracks-s05-summary-both-20261115` | `1417807b` | bundle only (`Claude outputs/s05both_20261115/`) |
| `backup-trackS-ops-e7417c5e-20261114` | `e7417c5e` | local only |

The harness branch `trackS-20261029` lives in `autoresearch_harness`. The harness pin `a3fedbb`
(`cacheprompt-20261031`) is shared with Track X B1/B2, so it is not Track S property.

**Worktree and remotes.**
- Worktree: `.claude-worktrees/trackS-ops-20261030` at `fab88fce` (listed as prunable; not pruned).
- Scratch checkout `.claude-worktrees/_trks_ops_s11/`: uncommitted; the `openml_breast_w` S1.1 ran there
  (`reports/TRACKS_PHASE1_20261030.md`). It still exists (15 Nov).
- Git remotes `tasl2` and `tasl7` point at the hosts' bare repos.

**Data and code in the repo.**
- `results/r1/tracks/`: `digits_mlp` 6.7 MB, `tabular_mlp` 6.4 MB, `openml_breast_w` 12 KB, `s05_summary` 212 KB.
  Seven phase trees carry `SHA256SUMS`: `digits_mlp/{s01_rerun20261109, s04, s04_rerun20261111, s05_t7_20261113}`
  and `tabular_mlp/{s01_t7_20261114, s04_t7_20261114, s05_t7_20261114}` (plus the `_to_delete/` copy). The 30–31 Oct
  trees (`s01`, `s01_diag*`, `s11`, `smoke` on both nodes, and `openml_breast_w/s11`) have none. For the old TASL-7
  `tabular_mlp` scenes the hash table in the tabular S0.4 report §1 is the substitute; for the others there is none.
  Host copies of those trees are therefore not provably redundant.
- `r1/tracks/`: collector, analysis, A2-U, simulators, the ops scripts and the launchers.
- Reports in `docs/r1/reports/TRACKS_*.md` and reviews in `docs/r1/reviews/`.
- Nothing here is changed by the decision.

**Container scratch (this agent's session, not on the Mac).** Worktrees under `/tmp/pb/wt/`: `s05sum`, `s05both`,
`stop4end`, `tsr`, `pin8237`, `harness-pin`, among others. They vanish with the session and hold nothing that is not
in a delivered bundle.

## 4. Not done here

- No census, no SSH, no file or process touched on either host.
- No branch deleted or pruned; no worktree removed.
- No PLAN row committed. The row is a draft for the author.
