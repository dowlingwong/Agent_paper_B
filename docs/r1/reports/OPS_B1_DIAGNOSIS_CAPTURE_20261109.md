# B1 STOP diagnosis — capture receipt for the Mac-local analysis (9/11 Nov 2026)

**Receipt only; the capture itself is not committed yet.** This is the experiment agent's record of the single read-only run of `docs/r1/proposals/B1_DIAGNOSIS_HANDOFF_20261109.md` (branch `mac-b1-diag-20261109-c`). Nothing on TASL-7 was modified, signalled, rerun, retired or read outside the script's fixed roots. The recorded STOP of run `6835_20261108_a` is unchanged.

## Preconditions verified before the run

- Branch/tip used: `mac-b1-diag-20261109-c` @ **`7b08c2ad548e7b2b33362c03d9d005b9e4e5a3b6`** (clean detached worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/b1-diag-20261109`; `git status --porcelain` empty).
- Independent review: `docs/r1/reviews/B1_DIAG_REVIEW_20261109.md` — round 1 changes requested, **round 2 accepted at `b46ced7c`** (script SHA-256 `82140eea…92f93`). The hand-off's review filename is a typo; the author confirmed this is the review of record.
- Diagnosis script SHA-256 matched the hand-off literal: `82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93`.
- `git diff 81c81289 HEAD -- docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py docs/r1/proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py` is empty.
- Wrapper `/private/tmp/b1-diag-wrapper-20261111.sh` is the hand-off block with `<worktree>` replaced; `bash -n` clean; run once. It hashes and base64-encodes the same bytes, checks the SHA, and sends the script via `exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /usr/bin/python3 -I -B -c`.

## Run (single, read-only)

- Start/finish (UTC): **2026-11-11T00:07:34Z → 00:07:40Z**; script `observed_utc` inside the capture: `2026-11-11T00:07:39Z`.
- `PRIVATE_CAPTURE=/private/tmp/paper-b-b1-stop-diagnosis-20261109.OSnzb5iI` (mode 700; `ssh.log` 77,366 B in 4 lines; `ssh.rc` 2 B).
- `SENT_SCRIPT_SHA256=82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93`.
- Wrapper exit code: **0**; `ssh.rc` contains `0`; the capture contains `DIAGNOSIS_CAPTURE_COMPLETE` and `SSH_EXIT=0`.
- The JSON line's top-level keys are `limitations, observed_utc, rows, source, state_sha256, state_sha256_pinned_to_accepted_descriptive_capture, stop_changed, summary`; it prints per-proposal `delta_audit` and summary counters (no raw per-seed metric vector, no 7006–7010 file). `stop_changed` and the pinned state SHA are part of the capture.

## The three SHA-256 lines printed by the wrapper

```
82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93  /Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/b1-diag-20261109/docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py
c6bc8a84ae482a249bccd65303397a66615832be97f82338be17a370c3c46df5  /private/tmp/paper-b-b1-stop-diagnosis-20261109.OSnzb5iI/ssh.log
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa  /private/tmp/paper-b-b1-stop-diagnosis-20261109.OSnzb5iI/ssh.rc
```

## Handling

- Only these SHA-256 values, the private capture path and the exit-code facts are committed here; **`ssh.log` itself is not committed** until the diagnosis report's independent review is accepted (the hand-off's rule; it holds every per-proposal `delta_audit`, including 7B values).
- `ssh.rc` (SHA-256 `9a271f2a…86aa`) also remains private.
- The Mac-local agent runs `docs/r1/proposals/B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py` on the private copy and writes the diagnosis report; the restart hand-off (`proposals/B1_RESTART_HANDOFF_20261109.md`, branch `mac-b1-r4-20261109` @ `4ddc820e…`) applies only if that report is reviewed and classified D with H1 supported and D7 PASS.
