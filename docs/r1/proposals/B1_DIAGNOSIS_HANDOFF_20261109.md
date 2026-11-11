# B1 STOP diagnosis — hand-off for the experiment agent (9 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local overnight agent, `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §1 step 2). Read-only diagnosis of the preserved B1 STOP of run `6835_20261108_a`, plan `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §3 (D0–D4, D7, D8). Run it **once**, only after its independent review is accepted (`reviews/B1_DIAG_REVIEW_20261109.md`). It changes nothing on the host: no rerun, no gate change, no signal, no modification or retirement of any host file. Nothing it prints changes the recorded STOP.

## What runs

- Script: `docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py` on branch `mac-b1-diag-20261109-c`, last changed in commit **`81c81289e1efdd5c778dfb422be08f0511a36028`**, SHA-256 **`82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93`**. The analysis script `docs/r1/proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py` was last changed in the same commit (SHA-256 `2537099feeb8090b161d0e7d29d2a8b64f12ec917a5c8ac3e58bb6873b2ffd07`). A hand-off commit cannot name its own SHA, so this file names the script commit; use the branch tip that contains the accepted review, and check that `git diff 81c81289 HEAD -- docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py docs/r1/proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py` is empty.
- Host mode (no arguments) reads only under `/home/dowling/exam-x/work/b1_6835_20261108_a`: `batch_state.json`, and for each of the 36 anchor roots (`<anchor>/b1/off/<node>__s<seed>/`) `job.json`, `campaign_manifest.json` and `root_trials.jsonl`. It first requires `batch_state.json` to have SHA-256 `cfe74fafdbbff6f10648f7e015b3df52f0438c435d45caf76e9e8c116d0b5794`, the state SHA recorded by the accepted descriptive capture (`reviews/B1_STOP_ANCHOR_DESCRIPTIVE_RESULT_REVIEW_20261108.md`, branch `mac-b1-stop-descriptive-review-20261108`), and opens no job otherwise; any change to the STOP scene since 8 Nov 10:52 UTC therefore refuses the capture. It validates the job binding (HEAD `68357d3d`, phase B1, node, instance seed, audit seeds 9101–9104 in job and config, rule SHA, W = 20, and the exact pinned 7B duplicate-rate reference `[0.42386590667728663, 0.5800007633587785]` with its source path and SHA in `authority_config`) **before** opening each manifest, then the manifest against the batch-state SHA and the job SHA, then `root_trials.jsonl` against the manifest's evidence hash. Files are opened with `O_NOFOLLOW` and `O_NOATIME` (no fallback), must be owned regular files and must not change during the read. No seed 7001–7010 file is opened; no raw per-seed metric vector is printed.
- It prints one JSON line and `DIAGNOSIS_CAPTURE_COMPLETE` only after all 36 roots validate; otherwise it prints `STOP: diagnosis refused: …` on stderr, nothing on stdout, and exits 1. D0 (files present, status, label, audit completeness, k = 4) is realised as refusal plus per-root counters, not as a file inventory.

## Exact command (on the Mac, as for the accepted descriptive capture)

Run from a clean checkout of the branch tip described above. Replace `<worktree>` with its path. The wrapper hashes and base64-encodes the **same bytes** in one Python call, so the bytes sent are the bytes checked.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=<worktree>/docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py
EXPECTED=82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93
PAIR=$(python3 -I -c 'import base64,hashlib,sys;b=open(sys.argv[1],"rb").read();print(hashlib.sha256(b).hexdigest()+" "+base64.b64encode(b).decode())' "$SCRIPT") || exit 1
SENT_SHA=${PAIR%% *}
CODE=${PAIR#* }
[ "$SENT_SHA" = "$EXPECTED" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-b1-stop-diagnosis-20261109.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
printf 'SENT_SCRIPT_SHA256=%s\n' "$SENT_SHA"
if ssh -n -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /usr/bin/python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))'" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc" || exit 1
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx DIAGNOSIS_CAPTURE_COMPLETE "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```

Under `exec(...)` the script's `__name__` is `__main__` and `sys.argv` is `['-c']`, so host mode runs. TASL-7's `/usr/bin/python3` must provide `os.O_NOATIME` (it did for the descriptive capture).

## What to send back

1. The capture directory path, the `SENT_SCRIPT_SHA256=` line, and the three SHA-256 lines the wrapper prints (script, `ssh.log`, `ssh.rc`).
2. The wrapper's own exit code.
3. If the script refused (exit 1), the stderr line; do **not** rerun or adjust anything — report it.

Commit only the SHA-256 of `ssh.log` and `ssh.rc` and the private capture path (as for the accepted descriptive capture), not the files themselves, until the diagnosis report's review is accepted: `ssh.log` holds every per-proposal `delta_audit`, including the 7B values. The Mac-local agent then runs `proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py <ssh.log>` on the private copy (it refuses a capture without `DIAGNOSIS_CAPTURE_COMPLETE` and exactly one `SSH_EXIT=0` line, or with any missing or inconsistent field) and writes `reports/B1_STOP_DIAGNOSIS_<date>.md` for independent review. The fix route follows from that report (plan §4); the restart hand-off is `proposals/B1_RESTART_HANDOFF_20261109.md`.
