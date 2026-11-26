# Independent review — B1 restart STOP report and record, run `fffa_20261111_b` (11 November 2026)

**Reviewer.** Fresh, independent reviewer. I did not write the unit reviewed and did not modify anything
under `/Users/wongdowling/Documents/agent_paper_B`. The unit was fetched only from the remote into a
throwaway clone at `/tmp/b1rev/repo` (a second, clean copy). TASL-7 was contacted only with read-only
commands (`hostname`, `ls`/`stat`/`cat`/`sha256sum`, `git rev-parse`/`status`/`log`, `tmux ls`/
`list-panes`, `nvidia-smi` queries, non-blocking `flock`, `pgrep`/`ps`, `df`); no writes, no signals, no
GPU work, no server start, no deletion. Local writes were this review and `/tmp` only. This review does
not accept a scientific result, retire or restore a marker, retry anything, or authorize a restart; it is
a verdict on whether the STOP record is accurate and sufficient.

**Unit.** `git ls-remote` on the public remote returns
`4da9cc526b898b1fee0b339692714996aa4a1221 refs/heads/mac-b1-20261107` as the tip; no other remote ref
contains it. The unit is the linear pair `386dc554751a4d688ba303efce5b2589161baf8b` (parent
`45945e56e07fcbea5da14254c8935de4ab21be30`) → `4da9cc526b898b1fee0b339692714996aa4a1221`. Both commits are
authored and committed by `Dowling Wong <wangdowling@gmail.com>` and their bodies say "AI-assisted;
operator: DSH experiment-agent session." The change set is documentation only: `docs/r1/STATUS.md` (one
new top entry), `docs/r1/reports/B1_STOP_FFFA_20261111.md` (75 lines) and the 12-file evidence directory
`docs/r1/reports/b1_stop_fffa_20261111/`; `4da9cc52` adds the two `.log` evidence files (`+181`). No
code, pin, configuration, authorization, registry or results file changed.

## 1. Load-bearing facts against the host — PASS, with two documentary exceptions (F1, F2)

All of the following were checked against the live host scene and the private captures; every value in
the report and STATUS entry matched unless noted.

- **Stop time.** Interruption `time` `1794405069.9573767` = `2026-11-11T13:51:09.957377Z`; report
  `docs/r1/reports/B1_STOP_FFFA_20261111.md:7` says 13:51:09.957 UTC. PASS.
- **Batch status.** Host `batch_state.json` (SHA-256 `0e0926dafee940b84d19d9d4d793b2d23933dd4ba6e02bf8ac3f9f444e370e85`,
  `census_ssh.log:47`) is `status STOPPED`, with one interruption (`returncode 1`, `killed false`) and the
  `stop_reason` text quoted verbatim in the report, STATUS and `batch_state_extract.json`. PASS.
- **`b1.exit` / `b1.log`.** `b1.exit` = `1` (SHA-256 `4355a46b…`, `SHA256SUMS:1`); `b1.log` is 653 B,
  SHA-256 `38b0d40f55e92e999e078aba25074773c926edcdaf1d88f91bacd95ebd36cdae` (`SHA256SUMS:2`), and contains
  the STOP line and the shutdown-writes note twice plus `B1_EXIT=1`, as the report says. PASS.
- **Run window.** Launch capture
  `/private/tmp/paper-b-b1-launch-capture-20261111.poqVLDF7/launch.log` records
  `b1_fffa_20261111_b: 1 windows (created Wed Nov 11 03:03:48 2026)`; the host local zone is −0800
  (handover capture `prechecks.log`: `host-local 2026-11-11T03:01:56-0800`), i.e. 11:03:48Z. The
  registry snapshot mtime `2026-11-11 03:03:49 −0800` (`census_ssh.log:48`) supports runner start
  11:03:49Z. Duration 2 h 47 min. PASS.
- **Own session gone.** `tmux ls` now shows only `trks_watch`; `census_ssh.log:4–5` agrees. PASS.
- **64 completed roots and per-candidate counts.** Host `batch_state.completed` is a 64-entry mapping;
  the derived counts are `qwen25_coder_7b/off 12`, `qwen36_27b/off 12`, `qwen38_27b/off 12`,
  `qwen38_27b/on 4`, `random_valid/off 12`, `scripted/off 12`, matching
  `docs/r1/reports/B1_STOP_FFFA_20261111.md:24–31`. The three anchor campaigns are the three rows above
  with 12 each (`docs/r1/reports/B1_STOP_6835_20261108.md:7` names them: `random_valid`, `scripted`,
  `qwen25_coder_7b`), so they are fully completed, consistent with line 33. The count 64 itself is correct;
  the `completed_count` field-name attribution on line 22 is F2 below. PASS otherwise.
- **Server intervals.** All five epoch pairs convert to the exact UTC times in
  `docs/r1/reports/B1_STOP_FFFA_20261111.md:39–43`; the last, `qwen36_27b`/on, is 13:22:05–13:51:10Z. PASS.
- **Anchor record.** `anchor_gate` point `0.0045958931135726055`, interval
  `[-0.0006244365634484693, 0.008944090671411787]`, 12 instance pairs, `descriptive_only true`,
  duplicate rate `0.49586776859504134`, pinned interval `[0.42386590667728663, 0.5800007633587785]`; the
  reference file has SHA-256 `84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd`, matching
  the `reference.sha256` in the batch state. Report line 33 matches. PASS.
- **`llm_call_failed` event.** `root_events.jsonl` SHA-256
  `c15e8dc9e687d2fb39fa2305667b57c5a64456e937918169d268afb1248fcfa0` has exactly one `llm_call_failed`:
  `2026-11-11T13:51:09Z`, `openml_credit_approval__s9001-trial-013`, `LengthFinishReasonError`,
  completion 31,551 / prompt 1,217 / total 32,768, seed `2042897189`, one transport attempt
  (`non_retryable`, 713.940988 s), policy `bounded_transport_retry/v1`, `max_attempts 1`. Report lines
  47–50 match. PASS.
- **Root cause chain as observed.** `runner.log` SHA-256
  `cffeb054ec7f4d576a44417b637f1ab4d0b159affe6caa4941e0d0ab3d4cdb2b` ends in
  `openai.LengthFinishReasonError`; the batch records the root worker exit 1 (`interruptions[0]`). PASS.
- **Server evidence.** `llama_server_56851_r2.log` SHA-256
  `6dab331fbe4ec285b30d8aaa54c16b41baa938fd3acd11c74e98c1f9bdfdd029` contains
  `stop processing: n_tokens = 32767, truncated = 1`, `eval time = 713316.03 ms / 31551 tokens`, then
  `cleaning up before exit`. Record SHA-256
  `7ce7f80c1a957f3f94c46d5ac670d94ab54cd4f0893fbbce117f8619304d6904` shows `-c 32768`,
  `--chat-template-kwargs {"enable_thinking":true}`, `--reasoning-budget 2048`, `started_utc
  2026-11-11T13:22:05Z`, `stopped_utc 2026-11-11T13:51:10Z`, `returncode 0`. Report lines 52–53 match. PASS.
- **Failing root trials.** `root_trials.jsonl` has exactly 12 lines, SHA-256
  `178add2f8a1dc0b506aef0d804a8ed671a3274ebd310f83650d767b81376652a` (report line 55). PASS.
- **Marker (NOT retired).** Live marker: dev 66306, ino 56261610, mode 600, 82 B, SHA-256
  `23fa767be7346809d087d0a2352241e6042abdd04df2f198e476b8f39eab4c9a`, content
  `{"head": "fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa", "run_id": "fffa_20261111_b"}`
  (`census_ssh.log:15–17`); report line 59 matches. `_to_delete/` holds only the retired 6835 marker
  (`trackx_evidence.active.c51a7c43…`); nothing deleted. PASS.
- **Quiescence.** A clean (non-self-matching) probe finds no `python … b1_fffa_20261111_b`, no
  `llama-server`, no `exam_runner`; `nvidia-smi` reports 236 MiB used, 0 % and no compute applications;
  `flock -n` probe returns LEASE-FREE (`census_ssh.log:19–21`). The run tree has no file newer than 13:55Z,
  i.e. nothing was written after the STOP. PASS.
- **Other tracks.** `trackp_evidence.active` absent and `trks_drill.active` absent (`census_ssh.log:23`);
  `trks_watch` alive (pane pid 1388760), `watch.log` last line the 2026-11-08 pause record
  (`census_ssh.log:26–28`). PASS.
- **Preserved scenes.** Run-6835 batch dir, handover dir and staged checkout (`rev-parse HEAD`
  `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`, `census_ssh.log:166`) are intact; the new run's staged
  checkout `…/b1_paper_final_fffa45a1…/paper` is at `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa`, parent
  `ac32231c…`, and `git status --porcelain` is empty. PASS.
- **Handover / gate / preflight provenance.** `marker-receipt.json` `1cd979ae…`, `marker-retirement.json`
  `4247a6a1…`, `status-receipt.md` `df6fbd0c…` all verify; `prechecks.log`, `handover-run.txt`,
  `launch-run.txt` present. `gate.exit` 0, `gate.log` `da5d3a67…` contains `GATE_PASS fffa45a1…
  53018aa7…`; `preflight.exit` 0, `preflight.log` `b48a639d…` ends `PREFLIGHT_PASS`. Report lines 13–19
  match. PASS.
- **Committed evidence self-consistency.** At the tip, `shasum -a 256 -c SHA256SUMS` verifies all 11
  entries; `host_originals.sha256` matches all four host originals (`batch_state.json`, `root_events.jsonl`,
  `root_trials.jsonl`, `llama_server_56851_r2.log`). `captures_sha256.txt` matches the readable
  `/private/tmp` handover/launch/census captures, whose own `SHA256SUMS` also verify; the handover capture
  records `HANDOVER_PRE_DONE` / `SSH_EXIT=0` and the launch capture `LAUNCHED` / `launch RC=0` /
  `SSH_RC=0`. PASS.
- **Census disk figure — FAIL.** Report line 63 says "Disk free 578,703,351,808 B at the census", but the
  cited census (`census_ssh.log:1` `CENSUS_BEGIN 2026-11-11T17:56:53Z`) reports
  `578471899136` (`census_ssh.log:174`). The value `578,703,351,808` appears nowhere else in the unit and
  is also not the earlier handover precheck value (`578705055744`). This is F1 below.

The report's limit statement (`docs/r1/reports/B1_STOP_FFFA_20261111.md:65`) is accurate and appropriately
preserves the point-in-time-census caveat.

## 2. Governing-document compliance — PASS

- The report is under `docs/r1/reports/` and a STATUS entry exists at the top of `docs/r1/STATUS.md:3–5`.
- The STOP is preserved and reported, and was **not retried**: `b1.log` contains one STOP sequence, no new
  run directory or handover directory was created, the run tree shows no post-STOP writes, and the B1 tmux
  session is gone.
- No configuration/pin change: the staged checkout is still exactly `fffa45a1…` (clean, parent
  `ac32231c…`) and the two commits touch documentation only.
- No marker retirement: the marker is present with its receipt identity; only the pre-existing 6835
  marker was retired (before this run, disclosed in the report and receipts), renamed into `_to_delete/`.
- No deletion and no other-track interference: `_to_delete` retains the 6835 marker, the 6835 scene is
  intact, `trks_watch` is alive and still paused.
- B2, X.7 and sweep 2 remain gated (report line 75 and the STATUS entry); the report states that no
  restart/fix/use of partial results is authorized and that a separately reviewed decision is required.
- The report states that it records observation only, not a causal diagnosis, scientific conclusion,
  author decision or permission to resume (report lines 3, 33, 54, 75), and it states the census limits
  (line 65). PASS.

## 3. Provenance and branch discipline — PASS (with one note)

- The branch is `mac-b1-20261107`, a B1 feature branch, not `main`, `r1` or `exam-x-*`; only this branch
  contains the tip.
- The history is a linear append on `45945e56…` (parent chain `4da9cc52 → 386dc554 → 45945e56`), so the
  earlier running-STATUS commit remains an ancestor and the two commits are fast-forward-shaped with no
  observable rewrite. (Whether the transport actually used `--force` is not provable from the repository;
  there is no evidence of a rewrite, and the pushed parent chain is intact.)
- Author/committer are `Dowling Wong <wangdowling@gmail.com>` with the operator disclosed in the body.
  This follows the recorded 11 Nov operator decision on `45945e56…` ("acting operator session is DSH, not
  Codex… the author remains author and the acting agent is committer") and the accepted handover review's
  F7 resolution; it deviates from the O2 draft's literal "Codex as committer", which was already accepted
  as a documented operator decision, not a new defect of this unit.
- No secret is printed: the diff/evidence contain paths, hashes, token-usage fields and argv only; a scan
  for token/key/password patterns finds nothing.

## 4. Completeness for the author decision — PASS (nits only)

The report states what stopped, when, the event chain, how far the run got, what is preserved, what is
open, and what is not authorized. Nits are listed in §6; none prevents a subsequent author decision.

## 5. Findings (changes required)

### F1 — MINOR: census disk-free figure does not match the committed census
- **Location:** `docs/r1/reports/B1_STOP_FFFA_20261111.md:63`.
- **Issue:** The report says "Disk free 578,703,351,808 B at the census". The cited census capture reports
  `578471899136` (`docs/r1/reports/b1_stop_fffa_20261111/census_ssh.log:174`, begun at
  `census_ssh.log:1` `2026-11-11T17:56:53Z`). The report's figure matches neither the census nor the
  earlier handover precheck (`578705055744`). This is a documentary error, not a scene change; no
  load-bearing STOP fact depends on it.
- **Minimal fix:** in a follow-up commit (do not rewrite pushed history) change `578,703,351,808` to
  `578,471,899,136` on that line, or replace it with an explicit reference to `census_ssh.log:174`. The
  report file is not listed in `SHA256SUMS`, so no evidence hash needs regenerating.

### F2 — MINOR: `batch_state.completed_count` is not a batch-state field
- **Location:** `docs/r1/reports/B1_STOP_FFFA_20261111.md:22`.
- **Issue:** "64 root keys completed (`batch_state.completed_count = 64`)". The host
  `batch_state.json` has a `completed` object with 64 entries and no `completed_count` (or
  `completed_by_candidate_mode`) key; those two are derived fields added in the committed
  `batch_state_extract.json`. An auditor grepping the host batch state for `completed_count` finds nothing,
  and the count is correct only as `len(completed)` (also printed as "completed 64" at
  `census_ssh.log:30`).
- **Minimal fix:** reword to "64 root keys completed (`batch_state.completed`: 64 entries; `completed_count
  = 64` in the committed `batch_state_extract.json`)", or simply "64 root keys completed". Markdown-only;
  no hash regeneration needed.

## 6. Non-blocking notes (no change required for a bounded STOP record)

- **N1 (reviewability).** `docs/r1/reports/B1_STOP_FFFA_20261111.md:17` says the preflight script and
  result "were independently reviewed and accepted" but does not cite the review files; they exist in
  `_xfer/b1_preflight_review_20261111/` and `_xfer/b1_preflight_result_review_20261111/` (both end
  "accepted") and are not committed to the branch. A path/commit citation, or committing them,
  would let the author verify the claim from the repository.
- **N2 (clarity).** `docs/r1/reports/B1_STOP_FFFA_20261111.md:33` says "The three anchor campaigns are
  among the completed roots." Naming them (`random_valid`, `scripted`, `qwen25_coder_7b`, 12/12 each) would
  be clearer and matches `docs/r1/reports/B1_STOP_6835_20261108.md:7`.
- **N3 (stale pointer).** The host `batch_state.json` retains an `in_progress` entry pointing at the failed
  root path with pid 3323405 after the STOP. The report's no-process claim is correct, but noting the stale
  pointer would stop a future reader mistaking it for a live root.
- **N4 (bisectability).** At the intermediate commit `386dc554` alone, `SHA256SUMS:2` and `:6` reference
  `b1.log` and `census_ssh.log`, which are only added by `4da9cc52`; `shasum -c` therefore does not verify
  at `386dc554`. The unit is the pair and the tip verifies completely (all 11 entries), and the second
  commit's message explains why the two `.log` files were force-added (they match the `*.log` ignore rule),
  so this is a bisect note only.
- **N5 (restraint check, PASS).** The one open technical question — completion 31,551 tokens versus
  `--reasoning-budget 2048` — is stated as an observation and explicitly "not established" at
  `docs/r1/reports/B1_STOP_FFFA_20261111.md:54`; the report does not present it as a cause, does not
  prescribe a fix, and calls for a separately reviewed diagnosis. This restraint is consistent and
  appropriate.

## 7. Limits of this review

I did not verify TASL-2 / Track S state (out of scope for this STOP and not needed for the claims made),
did not replay the LLM call, and cannot prove from the repository that the transport used a fast-forward
rather than a force push (only that no rewrite is observable). The pre-run provenance rests on the private
`/private/tmp` captures, which are readable and hash-verified against `captures_sha256.txt` and their own
`SHA256SUMS`. A point-in-time census, as the report itself states, cannot prove every descendant process
is absent; my independent clean probe found none and no run-tree writes after the STOP.

**Bottom line.** The STOP observation is accurately and sufficiently recorded, the scene is preserved,
and nothing is overclaimed or authorized; the only defects are two minor documentary inaccuracies (F1, F2)
that should be corrected in a follow-up commit. After that correction, this record can be committed to
`docs/r1/reviews/` as the review record.

VERDICT: changes required

---

## Round 2 — corrections (11 Nov)

**Reviewer.** Same independent reviewer (did not write `94e454c8`). Round 1 above is retained as history
and superseded by this round. The corrected unit was re-fetched from the remote in `/tmp/b1rev/repo`;
TASL-7 was contacted read-only only; local writes were this review and `/tmp` only.

**Corrected unit.** Remote tip `94e454c838064f66853a9b1403a3f6a59a23fc6f`, parent
`4da9cc526b898b1fee0b339692714996aa4a1221`; author = committer `Dowling Wong <wangdowling@gmail.com>`;
`git diff --name-status 4da9cc52 94e454c8` shows only `M docs/r1/reports/B1_STOP_FFFA_20261111.md` plus
the five added `docs/r1/reviews/…` files. No other file changed.

**Resolution of the Round-1 findings:**

- **F1 (disk) — fixed.** `docs/r1/reports/B1_STOP_FFFA_20261111.md:70` now reads
  "Disk free 578,471,899,136 B at the census (committed census log line 174)"; the committed
  `census_ssh.log:174` is `578471899136`. PASS.
- **F2 (`completed_count`) — fixed.** `B1_STOP_FFFA_20261111.md:25–26` now says the batch state's
  `completed` mapping has 64 entries and the committed `batch_state_extract.json` records the derived
  `completed_count = 64`; host `len(completed)` = 64. PASS.
- **N2 (anchors) — fixed.** `B1_STOP_FFFA_20261111.md:37–38` names `random_valid` (off), `scripted` (off)
  and `qwen25_coder_7b` (off), "12 roots (three nodes × four instance seeds)"; the host `completed` mapping
  confirms 4 roots per node for 3 nodes and 3 roots per seed for seeds 9001–9004, 12 each. PASS.
- **N3 (stale `in_progress`) — fixed.** `B1_STOP_FFFA_20261111.md:66–67` records that the preserved
  `in_progress` field still names the failing root with last worker pid 3323405 while the census found no
  such process, and calls it a preserved stale field. Host `in_progress` still names that root/pid and no
  such process exists. PASS.
- **N1 (review citations) — fixed.** `B1_STOP_FFFA_20261111.md:17–20` cites the five review records; they
  are committed under `docs/r1/reviews/` and are byte-identical to the reviewer outputs in `_xfer/`:
  run-HEAD `bdc770a8…`, staging `07c248bd…`, preflight script `960e4963…`, preflight result `a021019e…`,
  O2 handover `9f64e437…`. Each record's last line is `VERDICT: accepted`. PASS.
- **N4 (force-add) — fixed.** `B1_STOP_FFFA_20261111.md:78–79` notes the two `*.log` files are force-added
  by the follow-up `4da9cc52…` and that `SHA256SUMS` verifies at the tip; `shasum -a 256 -c SHA256SUMS`
  at `94e454c8` is 11/11 OK. PASS.

**Re-verified unchanged.** The committed evidence directory is byte-identical (SHA256SUMS 11/11 OK); the
host `batch_state.json` is still SHA-256 `0e0926da…`, the marker is still dev 66306 / ino 56261610 /
mode 600 / 82 B / `23fa767b…` and not retired, no `llama-server` or `exam_runner` exists, and the lease is
free. The correction commit states "No factual change to the STOP observation", and the diff bears that
out: only the six documentary/record items above changed. No new issue was introduced.

**Bottom line.** All Round-1 findings are resolved with the minimal fixes, nothing else changed, and the
corrected report/record remains an accurate, sufficient, preserved and non-authorizing record. It can be
committed to `docs/r1/reviews/` as the review record.

VERDICT: accepted
