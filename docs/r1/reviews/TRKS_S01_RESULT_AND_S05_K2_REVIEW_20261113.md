# Independent review — Track S TASL-7 `digits_mlp` S0.1 result, k = 2 decision and revised k = 2 S0.5 unit (13 November 2026)

**Reviewer.** Fresh, independent; I did not write the result report, the S0.5 unit or the records. I read the
repository in a `/tmp` clone and checked TASL-7 **read-only only** (`ls`, `stat`, `cat`, `sha256sum`, `tmux ls` /
`tmux list-panes -p`, `pgrep`/`ps`, `nvidia-smi`, `ss -ltnp`, a `flock -n` probe, `git rev-parse`/`git status`,
`find` for an entry count). I started, stopped, signalled and wrote nothing on TASL-7; the two S0.1 servers and
`trks_watch` were left untouched. Nothing under `/Users/wongdowling/Documents/agent_paper_B` was modified; only this
file and `/tmp` were written. This review executes nothing.

## Unit

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch **`trackS-ops-20261030`**. Commits
  **`b1bdd78b9a570da1c159ef5a8f39c90e2fb9bac5`** (result report + revised S0.5; parent
  `065e2456bce480eb4cc9cf9c0134cc718cc483d6`) and **`8aa3e18993d3d2eeadb49c96e9ead62061f726c7`** (k references;
  parent `b1bdd78b`). `origin/trackS-ops-20261030`, the `/tmp` clone and the TASL-7 bare
  `refs/heads/trackS-ops-20261030` all resolve to **`8aa3e189`**.
- `git diff --stat b1bdd78b^ b1bdd78b` = 2 files, +61/−9 (the report is new, 46 lines;
  `r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh` changed). `git diff --stat 8aa3e189^ 8aa3e189` = the two
  records only, +5/−4. No code, probe, collector or wrapper file is touched by either commit.
- Exact digests (repo bytes):

```
00c5578b141324bcb76b0ea88a01bf456abe751f8878ed04668bd072061d7467  docs/r1/reports/TRACKS_S01_TASL7_RESULT_20261113.md
3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh
87c05587daed193dd127512c4c76f59abbdd3c10d4b0b64f47a0e5f2673b9067  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh  (k = 1, b1bdd78b^)
c1deee130d8d67b495c4dcf2ad2b46b37153a6ae33224754e7b0e4f1be99c0f8  r1/tracks/ops/launch/tasl7_digits_s01_20261113.sh
b9f5b01bf9908b572b6ea3a08755fc753eae45770a674a2594546d6dc8eaab42  docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md
31e966da878718c87935ca3e7cff01aeafca62cc949c9ec87384c6be07c99bf7  docs/r1/reports/TRACKS_TASL7_PREP_20261113.md
```

- The S0.5 digest in the unit matches the prep record's digest block (`3e957464…`); the S0.1 digest is unchanged
  (`c1deee13…`, the reviewed re-run script) and is the file installed on TASL-7.

## 1. S0.1 result accuracy — PASS

Both JSONs were read from the host and re-derived against the report's table. `serial.json` is 10,493 B,
sha256 `e0c3060ef418084d0f6a61c53d02eca803d4f0dbc870cc1903de9884ea501929`; `concurrent.json` is 17,482 B,
sha256 `94d95b0350fe80399e1c1374118db530bdfa440f2476e9edcba75657df46fd4b`. Sizes match the report exactly.

| report row | JSON evidence | check |
|---|---|---|
| serial 18101, identity 1.0, errors 0, n 600, mean 0.675453, p95 0.706379 | `per_url[…]`: `identity_rate 1.0`, `errors 0`, `n 600`, `mean_s 0.6754532571928575`, `p95_s 0.7063787640072405` | PASS |
| concurrent 18101, identity 1.0, errors 0, n 1200, mean 2.717904, p95 2.843610 | `n 1200`, `mean_s 2.717903650098403`, `p95_s 2.8436102853156626`, `identity_rate 1.0`, `errors 0` | PASS |
| concurrent 18102, identity 1.0, errors 0, n 1200, mean 2.714058, p95 2.838630 | `n 1200`, `mean_s 2.714057663263908`, `p95_s 2.8386302841827273`, `identity_rate 1.0`, `errors 0` | PASS |
| `cross_server_identity 1.0` | top level `1.0`; both `identity_rate_per_client [1.0, 1.0]` | PASS |
| temperature 0.2, fixed D26 seeds, `cache_prompt` recorded | top-level and `request_example.temperature 0.2`; `provenance`; `cache_prompt false`, label `explicit`; probe at pin uses `manager_seed("tracks_s01", i, 0)` | PASS |
| CPU census 24 CPUs; ≈0.15/23.85 and ≈1.0/22.99; ≈0.86/23.14 and ≈1.93/22.07 | `cpus 24`; `cpu_before`/`cpu_after`: `0.146484375/23.853515625`, `1.01220703125/22.98779296875`, `0.85595703125/23.14404296875`, `1.927734375/22.072265625` | PASS |
| host TASL-7, model `r1-manager`, provenance GGUF/llama/server args | `host "TASL-7"`, `model "r1-manager"`, `gguf_sha256 509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`, `llama_build 620d2225cc436ab0b001e3200e590e3b286ef9ab`, both server commands | PASS |

- **Run/provenance.** Host paper checkout is `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`, clean
  (`git status --porcelain --untracked-files=all` empty); harness is `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`;
  prior is `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`. The launch log
  `$R/logs/s01_t7_20261113b_launch.log` (375 B, sha256
  `11aeafae2b338efeaddbf8059cc1b3d30fc93bcb0926bfd64ebbccf279b7848e`) reads `11:13:01Z` start, `11:13:01Z`
  both endpoints ready, `11:20:02Z serial rc=0`, `11:47:17Z concurrent rc=0`, `11:47:17Z S01 DONE`.
  `trks_s01_serial.exit` records `2026-11-13T11:19:47Z rc=0` and `trks_s01_conc.exit`
  `2026-11-13T11:47:13Z rc=0`; the report's `11:19:47Z` serial and `11:47:17Z` concurrent are the `.exit` and
  launch-log values respectively (see R3).
- **First attempt history.** `s01b_launch.rc` is `rc=2` then `rc=0`; `s01_t7_20261113_launch.log` (204 B) has the
  `11:12:20Z S0.1 start` line and no readiness line, consistent with the pre-suffix script refusing on the existing
  `s01_t7_20261113/`; the b-suffixed run is the reviewed one. This matches the report's account.
- **Preserved scene.** `$OUT/digits_mlp/s01_t7_20261113/` is empty (0 entries under it), inode 56915422,
  mtime `2026-11-13 02:50:12.431930123 -0800` — untouched; the outputs are in `s01_t7_20261113b/`.

## 2. k decision — PASS

Runbook rev 3.3 Phase 1 (`docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, sha256
`a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`) says k = 2 if, in the concurrent run,
within-server identity is 100 % on both URLs and `cross_server_identity` is 100 %; else k = 1 if serial identity is
100 %; else STOP. All three JSON facts hold: both URLs `1.0`, cross `1.0`, serial `1.0`, zero errors. **k = 2 is the
rule output**, and the report records it. The report also correctly records that this supersedes the k = 1
assumption derived from TASL-2 (the 9 Nov TASL-2 S0.1 chose k = 1 by the adopted R1-TRACKS-S01-RERUN clause (b),
"both tiers pass → the faster projection"); the TASL-7 S0.1 is a new Phase 1 for this host move, and the runbook's
Done-when rule is what the report applies. That supersession is legitimate; R2 asks for the projection and the
rule-basis sentence to make it auditable.
- **Docs consistency.** `TRACKS_DIGITS_HOSTMOVE_20261112.md` condition 5 now says "`K` servers as decided by the
  TASL-7 S0.1 result (the accepted result decided **k = 2**; the collector runs on port 18101, both endpoints
  ready)". `TRACKS_TASL7_PREP_20261113.md` says `K` servers (default **2**) / `trks-servers $K` / waits for
  18101..1810K / refuses a live count ≠ K. Neither record contains a stale "k = 1"; the only k = 1 mentions are
  historical (the TASL-2 assumption and the superseded k = 1 unit), which is correct.

## 3. Revised S0.5 unit — PASS

`diff -u` of `87c05587…` (k = 1) against `3e957464…` (k = 2) contains exactly: the header comment change, the
`K=${K:-2}` line, the `LIVE=$(pgrep -u dowling -f 'llama-server .*--port 1810[12]' | wc -l …)` server-count guard
(with the GPU/lease checks unchanged in content, now in the `else` branch), `trks-servers $K`, the readiness loop
over `seq 18101 $((18100 + K))`, and the k/$K log wording. Nothing else changed.
- **Collector unchanged.** The `trks-run "$SESSION" 18101 collect …` vector is byte-identical between the two
  versions: `--phase S0.5 --node digits_mlp --prior "$PRIOR" --prior-sha256
  5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607 --obs-inflation 1.0 --W 40 --instances 20
  --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label
  ENGINEERING_ONLY --deadline 28800 --stop-file "$RUN/STOP" --out "$RUN" --work "$WRUN"`.
- **Guards unchanged.** Priority markers, `$SESSION` collision, manifest-less/empty-manifest existing-`$RUN` rules,
  paper pin `8237fd02` + clean check, prior existence + `5c849d15…` sha256, and the no-`trks_llm` GPU/lease checks
  are content-identical; only the `trks_llm`-present branch gains the live-count check. No `rm`, `rmdir`, `mv`,
  `unlink` or `truncate` exists in either version. `bash -n` passes.
- **Reuse/refuse semantics.** With the live state (`trks_llm` exists, `trks-servers 2` pane, exactly two
  `llama-server` processes on 18101/18102, `pgrep` count 2), `K = 2` passes the guard and the script takes the
  "already running (resume path); not starting a second server" branch, then checks both endpoints — correct. A
  k = 1 set gives count 1 ≠ 2 and is refused; a k = 0 set never reaches the collector (it exits non-zero at the
  `LIVE=` assignment — fail-closed, but see R4 for the lost message).

## 4. Read-only live state — PASS

`tmux ls`: `trks_llm` (created 2026-11-13 03:12:18 -0800, pane command `/home/dowling/r1_tracks/bin/trks-servers 2`)
and `trks_watch` (30 Oct). `pgrep`: wrapper 4129628 (`flock -n …/gpu0.lock bash -c` starting `for i in $(seq 1 2)`),
servers 4129633 (:18101) and 4129634 (:18102); `nvidia-smi` 0 % utilisation, 10,699 MiB / 24,564 MiB; `ss` listeners
only 127.0.0.1:18101/18102. `flock -n gpu0.lock` → HELD (the k = 2 wrapper). `trks_s01_serial`/`trks_s01_conc`/
`trks_s05_t7` sessions absent (finished/none). The two JSONs are present; the preserved `s01_t7_20261113/` is empty
and untouched; `$OUT/digits_mlp/s05_t7_20261113`, `$WORK/digits_mlp/s05_t7_20261113` and
`$R/logs/s05_t7_20261113_launch.log` do not exist. No Track S collector is running (`pgrep -af 'trks-run|collect
--phase'` empty). Markers `trackx_evidence.active`, `trackp_evidence.active` and `$R/trks_drill.active` are absent.

## 5. Safety / scope — PASS

No S0.5 was started by this review; the result report (§4) and the `b1bdd78b` commit message say no S0.5 until the
result and the revised unit are independently reviewed. No secrets are present in the report, scripts or records (paths and
hashes only). The commits touch only the files stated. The host's paper and harness checkouts, both JSONs, the launch
logs, the empty preserved directory and the live k = 2 servers were not modified.

## Residual notes (non-blocking; no change to the reviewed k = 2 bytes is required for acceptance)

1. **Deployment before running (required operational step).** TASL-7 `$R/launch/tasl7_digits_s05_20261113.sh` is
   still the k = 1 file `87c05587…`, not `3e957464…`. Install the reviewed k = 2 file (scp + installed-bytes check,
   runbook §0.1), verify sha256 `3e957464…` and `bash -n` on the host before the documented
   `ssh tasl7 bash $R/launch/…` run; otherwise the stale k = 1 unit would run (no live-count guard, single-endpoint
   readiness) — a deviation from the reviewed bytes, which the prep record lists as a STOP condition.
2. **Phase 1 projection / rule basis (record completeness).** The report gives mean latency and free cores but not
   the runbook's Phase 1 projection ("reported for the author"). With `C = 80 000`, `R = 60 000`,
   `t_run = 0.9091 s` (Phase-0 smoke, not re-measured on TASL-7), `c = min(free, 2k)`: k = 1 with serial
   `L = 0.675453 s` gives ≈22.6 h; k = 2 with concurrent `L = mean(2.717904, 2.714058) = 2.715981 s` gives ≈34.0 h.
   Indicative only, but the report should add it and state explicitly that the runbook's Done-when (not the
   TASL-2 R1-TRACKS-S01-RERUN clause-(b) faster-k exception) governs this host move.
3. **rc-time provenance (minor).** Serial `11:19:47Z` is from `trks_s01_serial.exit` (the launch-log line is
   `11:20:02Z`); concurrent `11:47:17Z` is the launch-log line (`.exit` is `11:47:13Z`). Cite the file for each, or
   use one source consistently.
4. **k = 0 guard message (minor robustness).** `LIVE=$(pgrep … | wc -l | tr -d ' ')` under `set -euo pipefail` exits 1
   at the assignment when `pgrep` finds no match, before the `REFUSE: trks_llm has $LIVE servers but K=$K` branch
   (verified with a local `/tmp` bash repro). Fail-closed (no collector), but the intended message is lost; `…
   | tr -d ' ' || true` would restore it if desired.
5. **Guard regex scope (minor).** The live-count regex hardcodes `1810[12]`: correct for the decided k = 2, and it
   fails closed for larger K (would undercount and refuse); note it if K is ever generalised.
6. **Record freshness (minor).** The host-move header still says "S0.1 pending a reviewed operator-error re-run"
   (the re-run completed); the prep record's precondition 1 still says "B1 `_c` normal end + post-run unit" (the
   actual path was the author's 13 Nov STOP-case marker retirement), and the host-move condition 5 calls the result
   "accepted" before this review. These are record-text fixes, not unit defects.
7. **JSON standalone reading (minor).** `/props` reports the server default temperature 0.8 while the request and the
   top-level record are 0.2; the report's "temperature 0.2" is the request value and is correct, but a parenthetical
   would prevent a misread of the JSON alone.

VERDICT: accepted
