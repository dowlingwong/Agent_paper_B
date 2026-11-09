# B1 STOP diagnosis — hand-off for the experiment agent (9 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local overnight agent, `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §1 step 2). Read-only diagnosis of the preserved B1 STOP of run `6835_20261108_a`, plan `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §3 (D0–D4, D7, D8). Run it **once**, only after its independent review is accepted (`reviews/B1_STOP_DIAGNOSIS_SCRIPTS_REVIEW_20261109.md`). It changes nothing on the host: no rerun, no gate change, no signal, no modification or retirement of any host file. Nothing it prints changes the recorded STOP.

## What runs

- Script: `docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py` on branch `mac-b1-diag-20261109` (commit ⟨commit⟩), SHA-256 **`e49ed5501a7c7e715f0adf455c389ca55d2bf97409ac4e0bf2208617fa8393d1`**.
- Host mode (no arguments) reads only under `/home/dowling/exam-x/work/b1_6835_20261108_a`: `batch_state.json`, and for each of the 36 anchor roots (`<anchor>/b1/off/<node>__s<seed>/`) `job.json`, `campaign_manifest.json` and `root_trials.jsonl`. It validates the job binding (HEAD `68357d3d`, phase B1, node, instance seed, audit seeds 9101–9104 in job and config, rule SHA, W = 20) **before** opening each manifest, then the manifest against the batch-state SHA and the job SHA, then `root_trials.jsonl` against the manifest's evidence hash. Files are opened with `O_NOFOLLOW` and `O_NOATIME` (no fallback), must be owned regular files and must not change during the read. No seed 7001–7010 file is opened; no raw per-seed metric vector is printed.
- It prints one JSON line and `DIAGNOSIS_CAPTURE_COMPLETE` only after all 36 roots validate; otherwise it prints `STOP: diagnosis refused: …` on stderr and exits 1.

## Exact command (on the Mac, as for the accepted descriptive capture)

Run from a clean checkout of the commit above. Replace `<worktree>` with its path.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=<worktree>/docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py
EXPECTED=e49ed5501a7c7e715f0adf455c389ca55d2bf97409ac4e0bf2208617fa8393d1
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
CODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-b1-stop-diagnosis-20261109.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
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

1. The capture directory path, `ssh.log` and `ssh.rc`, and the three SHA-256 lines the wrapper prints.
2. The wrapper's own exit code.
3. If the script refused (exit 1), the stderr line; do **not** rerun or adjust anything — report it.

Commit `ssh.log` and `ssh.rc` (or their SHA-256 and the private path) on your branch and push. The Mac-local agent then runs `proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py <ssh.log>` and writes `reports/B1_STOP_DIAGNOSIS_<date>.md` for independent review. The fix route follows from that report (plan §4); the restart hand-off is `proposals/B1_RESTART_HANDOFF_20261109.md`.
