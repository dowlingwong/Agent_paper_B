# Independent re-review — Track S `digits_mlp` S0.5/S0.5b merged record (R2)

**Reviewer.** Fresh and independent; I did not write the report, the copy-back, the STATUS entry or the run. I read a
`/tmp` clone of the repo and TASL-7 **read-only** (`cat`, `stat`, `sha256sum`, `python3 -m json`, `tmux ls`,
`pgrep`, `nvidia-smi`, `flock -n`), and wrote only this file and `/tmp`. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was touched. One `flock` probe used
`/home/dowling/r1_locks/trks.lease` (not the reported lease path) and created a 0-byte file; I removed it at once.
The reported lease `~/r1_locks/gpu0.lock` was only probed and remains free; no run, log, ledger or lease content was
changed.

## Unit

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, tip
  **`a0a4c7cb2c6cba52048da2fe3e1e207c395da40b`** (parent `b846251e`, then `e008abfb`), clean clone; 41 tracked files
  under the result tree (40 payload + top-level `SHA256SUMS`).
- Report `docs/r1/reports/TRACKS_S05_T7_RESULT_20261114.md` 159 lines, sha256
  `47a5b1409d42ec470a982b65cec27ba696f57c83362a51a985a22daf81c191d7`; STATUS
  `20b5d0ab1b4282f78c92d807a0429cb192760520dbeb722e21e35eae13ccdedd`; copy-back `SHA256SUMS` sha256
  `23b6fdc96892f991ab68649817b3149604242d7d6b763e4d514c29a0fbf5c239` (40 entries).

## Findings re-checked

### F1 — fixed

`sha256sum -c SHA256SUMS` returns **40/40 `OK`**; all 40 payload files are in the commit (23 are `.gitignore`-matched
`*.jsonl`/`*.log`/`_to_delete/` files that were force-added), and the nested `operator_capture/SHA256SUMS` verifies 5/5.
Host==copy for the full run tree and logs (25 files: 8 tree + 17 `host_logs`), with exact shas
roots `039b69556d6b4c14c93fdb52982ffe136d9ac7c3ee4e6714a7434b8750569da5`,
forks `bf638fa6718b6910565710459fe2caa326692d463f50c06c5cac8075cbab7267`,
leaves `427faff6a7d266dd58a312f53ef1cf4ea6421e1def19e6ffa38a080f664df3bc`,
audit_runs `93939187ee1c681972ca0233a1d2c1fbf7508a3fe78bbaecc122f88eed85aed8`,
calibration `2e4c9a8c40ef5fb9a740ad5b4ad12e2d7026c42fdc19b4467ddeefbaacc50a2b`,
truncated `cd296fd8f2029266015d536f0f561521e13da36f83d7f00c84a9439d4c1ce135`,
manifest `68a0d6e077891f22e0a2e40b5b589dd680a1efdd0be19f7f79f2ade18e6e187c`,
retired STOP `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Launchers repo==host `f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3` and
`3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a`; `.cmd` `fe9fae36…` and `bash -n` clean.

### F2 — fixed

Report §7 and STATUS disclose the parallel-phase execution and the record-vs-launch ordering: R2 accepted ~10:40Z,
launch `10:43:33Z`, review-record commit `92680170` at `2026-11-14T10:44:25Z` (verified from git), R2 review sha256
`561c546ae934420eb866f19f0a0adeebb7762da39cfe86dd89a515802683d2a4`.

### F3 — fixed

Report §9b now says the cap binds at the **low** W: binding rows 50/50 (W8), 50/50 (W10), 47/50 (W12), 2/50 (W20);
the W20 quoted 16/40 is the non-binding cell. Means `0.963097 / 0.968334 / 0.970830 / 0.972802` reproduce exactly.
No "higher W" wording remains.

### F4 — fixed on the named facts

`$RUN/STOP` absent; one retired `_to_delete/STOP.retired.20261114T103527Z`, 0 B, inode **57048847**, sha
`e3b0c442…`, mtime `2026-11-13T13:47:35.151Z` (host `05:47:35.151 -0800`); collector exit `13:03:00Z`; the
preflight capture found exactly one file newer than the pause (876 scanned) and `watch.log` records the 13:47:35Z
marker/`pausing` re-touch. §2's "explained re-touch, not a scene change" disposition is present and matches the host.

## Numbers / governance

Calibration 298 rows, level 0.8, k=5, coverage **231/298 = 0.7752**; exact strata `HIDDEN_UNITS + 0` 0/20,
`BATCH_SIZE + 1-2` 20/40, `HIDDEN_UNITS + 1-2` 31/40, `HIDDEN_UNITS + >=3` 75/75, `LEARNING_RATE_INIT - 0` 5/11;
`delta_audit` mean **−0.007418** (min −0.412256, max 0.192200). Truncation 200 rows; totals roots **50**, forks **24**
(5 A/A), leaves **71**, audit_runs **1780**, no `failed_units.jsonl`, exhausted 0. Session #2 `28/18/71/0/0 complete`
(end `20261114T123402Z`); S0.5b `rc=0`, 200 rows. No deletion; descriptive-only language; STOP 4 waits for
`tabular_mlp`. Host end state: only `trks_watch`; `gpu0.lock` free; no llama-server/compute app/collector/18101–18102
listener; GPU 0 %, 236 MiB; markers absent; disk 526 G free (71 %). `trks-status` host sha
`70fbe8bd312fd7aad3a9020b80dcf9284453a8319dbb2cb523e9f6c06f16cc5f` = repo file, `PAPER_SHA=8237fd02`, output
`OK paper/harness/llama`, GGUF OK. TASL-2 is still unreachable (ping/ssh timeout), so "untouched" is consistent but
was not re-censused.

## Residual notes (documentary, non-blocking)

1. Report §9 still says `SHA256SUMS` verifies **39 files** (37 + 2 scripts), but the file has **40** entries and
   `sha256sum -c` is 40/40; STATUS line 13 says **37**. The 40th is the nested `operator_capture/SHA256SUMS` added by
   `a0a4c7cb`. Update to 40 entries (38 run-tree/log/capture files + 2 scripts).
2. Report §1 line 30 still says session #1 was `status=paused` "on a Track X priority marker", while `watch.log`
   places the only 13 Nov marker event at **13:47:35Z**, after the 13:03:00Z collector exit; §2 explains the STOP
   mtime but not the 13:03 trigger. The STOP/manifest facts are unaffected; the cause sentence should be corrected or
   the actual trigger recorded.
3. Round-1 residual 1 remains: `audit_runs.jsonl` 1780 unique rows vs the manifest session sum 1770; consistent with
   post-session S0.5b audits but still not stated. The `trks-status` output also still shows the old `smoke` STOP line
   (not the S0.5 run), so §7's unqualified "no STOP line" is loose.

## Conclusion

The completion facts, copy-back (now complete and host-verified), governance disclosure, low-W truncation wording,
pause/STOP facts, calibration/truncation numbers and host end state all reproduce. The residual items are
documentary and do not change the result or the L1 pause. The merged record supports the L1 pause.

VERDICT: accepted
