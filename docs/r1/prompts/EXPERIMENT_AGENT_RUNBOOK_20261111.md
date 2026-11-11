# Experiment agent — continuous runbook from 11 November 2026 (B1 restart and Track S rerun)

**Written 11 Nov 2026 by the chat session (Claude); AI-assisted; revision 2 after a self-check against the governing documents (not an independent review).** It adds an order of work and a waiting rule on top of the documents in §0. It authorizes nothing that they do not authorize. Where they differ, they win and you STOP to report the conflict.

You are the **experiment agent**, the operator for TASL-2 and TASL-7 (`prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.3). The Mac-local agent writes the code, the analysis and the hand-offs; you run them on the hosts. You never edit code or pins to make a run work. Work through §2 item by item **without waiting for the author between items**. Stop a track only at the STOPs in §3. While one track waits or stops, the other continues. Report to the author in **Chinese**; files and commits in **English**.

## 0. Governing documents (read once at the start)

| Topic | Document (branch @ commit) |
|---|---|
| Your general rules | `prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.3 (`docs/runbooks-09nov`) |
| B1 diagnosis plan and fix routes | `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` (`docs/runbooks-09nov`) |
| B1 diagnosis capture (done) | `reports/OPS_B1_DIAGNOSIS_CAPTURE_20261109.md` (`ops-b1-20261109` @ `d1d30687`) |
| B1 restart | `proposals/B1_RESTART_HANDOFF_20261109.md` (`mac-b1-r4-20261109` @ `4ddc820e`) |
| Track S procedure | `prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` rev 3.3 (docs commit `13badb0`): §0.2–0.8, Phases 3–4, §10 |
| Track S ruling at STOP 3 | `reports/TRACKS_PHASE3_20261109.md` §11 (`trackS-ops-20261030` @ `8ae46a48`) |

Standing rules stay as they are:
- no deletion (retire into `_to_delete/`);
- never touch what you did not start;
- never preempt another user;
- a fresh independent reviewer at every STOP, and never accept your own unit;
- never push `main`, `r1` or `exam-x-*`, and never force-push;
- never read secrets.

## 1. Waiting for the Mac-local agent

Two deliveries are expected. The Mac-local agent may not be able to push to GitHub, so check **three places every 30 minutes**, also while you are working on the other track, until both have arrived:

1. `git fetch origin`, then the remote branches below;
2. the local branches of `~/Documents/agent_paper_B` (`git branch --list 'mac-b1-diag-report-*' 'mac-tracks-a2u-*'`; worktrees under `.claude-worktrees/`);
3. bundles under `~/Documents/agent_paper_B/Claude outputs/handoff_20261111/`: a `*.bundle` with a `READY.txt` next to it. Check the bundle with `git bundle verify`, then fetch its branches into local branches of the same names.

**Pushing a delivery (authorized here).** When a delivery is ready (table below) and is only local or only in a bundle, push that branch to `origin` yourself, under its own name. The push must be a fast-forward or a new branch, never a force-push. This covers only branches named `mac-b1-diag-report-*` and `mac-tracks-a2u-*`. Record the pushed SHA in your report, and from then on use only the `origin` copy. If a local branch and the bundle disagree, do not push; report it.

| Delivery | Branch | Ready when |
|---|---|---|
| **D-B1**: B1 diagnosis report | `mac-b1-diag-report-20261111` (or a new `mac-b1-diag-report-*`) | `reports/B1_STOP_DIAGNOSIS_<date>.md` is on the branch, and so is its review file, written by a freshly spawned reviewer and ending in *accepted* |
| **D-S**: A2-U fix | `mac-tracks-a2u-stale-20261111` (or a new `mac-tracks-a2u-*`) | three things are on the branch: the fix commit; its review, ending in *accepted*; and a dated PLAN §10 row that names one commit as the new Track S paper pin, which contains the fix |

A branch whose review is not yet *accepted* is not ready, so keep checking. If neither has arrived 12 hours after you start, tell the author once and check hourly from then on.

## 2. Order of work

### 2.0 First: hand the capture to the Mac-local agent (skip if already done)

Copy `ssh.log` and `ssh.rc` unchanged from `/private/tmp/paper-b-b1-stop-diagnosis-20261109.OSnzb5iI/` to `~/Documents/agent_paper_B/Claude outputs/b1_diag_capture_20261111/` (mode 700). Check their SHA-256 against the receipt: `c6bc8a84ae482a249bccd65303397a66615832be97f82338be17a370c3c46df5` for `ssh.log` and `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` for `ssh.rc`. Never `git add` that folder. The originals stay where they are. Tell the author when this is done.

### 2.1 Track S on TASL-2 — when D-S is ready

Here `R=/home/dowling/r1_tracks`, `OUT=$R/out/digits_mlp` and `WORK=$R/scratch/digits_mlp`, as in `r1/tracks/ops/launch/tasl2_s04_20261109.sh`.

1. **Check the delivery.**
   - The review is *accepted*.
   - Let `P` be the commit the PLAN row names as the new pin. `git diff P <branch tip> -- r1/` is empty: anything after `P` is documentation only.
   - `P` descends from the old pin `d10b05b7`, and `git diff d10b05b7 P --stat` touches only the A2-U fix, its tests and docs.

   Record all three checks.
2. **Move the TASL-2 checkout to `P`.**
   - Bring `P` to the host the way earlier pins came: push the branch to the TASL-2 bare repository (the `tasl2` remote).
   - In `$R/work/Agent_paper_B`, check `P` out **detached**. `git status --porcelain` must be empty.
   - The harness stays at `a3fedbb` (clean), llama.cpp at `620d2225…`, the GGUF SHA-256 at `509287f7…`, and the server flags as rev 3.3 §0.2. Any mismatch is a STOP.
   - Record `P` in a STATUS entry before the first run. Rev 3.3 §0.2 requires this for a newer code commit.
3. **New launch script, committed before use.**
   - Copy the 9 Nov launch script to `r1/tracks/ops/launch/tasl2_s04r2_20261111.sh` on `trackS-ops-20261030`.
   - Change only these:
     - the output paths become `$OUT/s04_r2_20261111` and `$WORK/s04_r2_20261111`;
     - the stop file becomes `$OUT/s04_r2_20261111/STOP`;
     - the collector session becomes `trks_s04r2`;
     - the launch log name and the header comment are updated;
     - the guard refuses if the new output directory already exists, unless the run is resuming that directory.
   - The new session name keeps `$R/logs/trks_s04.*` (old STOP evidence) from being appended to.
   - Commit, push, copy the script to `$R/launch/`, and check that its SHA-256 on the host equals the committed one.
4. **Run.**
   - `ssh portal_zhixu bash $R/launch/tasl2_s04r2_20261111.sh`: a fresh `k = 1` server on port 18101, the readiness poll, the lease held, then `trks-run trks_s04r2 18101 collect --phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY --deadline 28800 --stop-file $OUT/s04_r2_20261111/STOP --out $OUT/s04_r2_20261111 --work $WORK/s04_r2_20261111`.
   - All ten instances start from scratch. The old `s04` directories are never read or written.
   - The 3.0 pause drill is not repeated. It is repeated only if `git diff d10b05b7 P` touches the server, watcher or collector session path; then do it as rev 3.3 §3.0 and say so in the report.
5. **Until finished.**
   - When `trks_s04r2` exits, read `jq '.sessions[-1].done' $OUT/s04_r2_20261111/manifest.json`.
   - Run the identical command with `--dry-run` (its own session name, for example `trks_s04r2_dry`).
   - If `roots_todo > 0` and nothing is exhausted, re-run the launch script (same command; it resumes).
   - The phase is finished when the dry run shows `roots_todo = 0` and `leaves_todo = 0`.
   - With ten roots, **one exhausted unit is already more than 2 %**, so `exhausted ≥ 1` is a STOP.
   - Exit 3 and other exit codes follow rev 3.3 §0.6.
6. **Liveness and prior** (CPU; run directly; servers not needed):
   - `trks collect --phase liveness --node digits_mlp --out $OUT/s04_r2_20261111`. Exit 3 is a STOP.
   - `trks collect --phase fit_prior --node digits_mlp --out $OUT/s04_r2_20261111 --sigma-node 0.0066 --obs-inflation 1.0 --prior $OUT/a2u_prior_r2_20261111.json`. Record the prior's SHA-256.
7. **Close.**
   - Stop the servers (`tmux kill-session -t trks_llm`, only the session you started).
   - Verify the host: lease free, no compute app, no llama-server, `trks_watch` running, no STOP file or marker.
   - `rsync` the new `$OUT/s04_r2_20261111` and the prior to `results/r1/tracks/digits_mlp/s04_r2_20261111/`, with `SHA256SUMS`.
   - Write `reports/TRACKS_S04_RERUN_20261111.md` and a STATUS entry. Push to `trackS-ops-20261030`.
8. **Review.** A fresh reviewer runs until *accepted* (`reviews/TRACKS_OPS_S04_RERUN_REVIEW_20261111.md`).

   Expected time for steps 1–8: about 1 hour of running plus the reviews.

9. **Phase 4 for `digits_mlp` — only if line L1 (§4) is in your start message — after step 8 is accepted.**
   - First a new launch script, committed before use, as in step 3. It runs S0.5 in session `trks_s05` and refuses if `$OUT/s05` exists. The command is rev 3.3 Phase 4, filled in for digits:
     `trks-run trks_s05 18101 collect --phase S0.5 --node digits_mlp --prior $OUT/a2u_prior_r2_20261111.json --prior-sha256 <its sha256> --obs-inflation 1.0 --W 40 --instances 20 --policy "static:0.00198,0" --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label ENGINEERING_ONLY --deadline 28800 --stop-file $OUT/s05/STOP --out $OUT/s05 --work $WORK/s05`
     Here 0.00198 = 0.3 × σ_node = 0.3 × 0.0066.
   - Check that the S0.5 manifest records `obs_inflation` 1.0, as in the prior's metadata. A difference is a STOP.
   - A session that stops at the 8-hour deadline is resumed with the identical command. The phase is finished as in step 5, with the same 2 % rule (Σ exhausted / Σ (roots + leaves + exhausted)). A fork-rebuild mismatch or an A/A mismatch is a STOP.
   - When S0.5 is finished, stop the servers. Then run S0.5b, which needs no servers: `trks-run trks_s05b - collect --phase S0.5b --node digits_mlp --truncate-W 8,10,12,20 --out $OUT/s05 --work $WORK/s05`.
   - Copy `$OUT/s05` back with `s05_calibration.jsonl` and `s05b_truncated.jsonl`. Write the report and a STATUS entry, then get a fresh review until *accepted*.
   - **Then Track S pauses (§2.4).** The S0.5 summary, the calibration gate and STOP 4 need `tabular_mlp`, which needs TASL-7.

   Expected time: about half a day, not measured.

### 2.2 B1 on TASL-7 — when D-B1 is ready

1. **Read the report yourself.** Continue only if all three hold:
   - its class line says **class D**;
   - its H1 line says **supported**;
   - its D7 line says **PASS**, and the 7B duplicate rate it gives lies inside the exact interval [0.42386590667728663, 0.5800007633587785] when you check it yourself.

   Do not rely on a summary field alone. Anything else is a STOP (§3).
2. **Prepare the restart**, following the restart hand-off §§0–2 in its order. Expected time: 2–3 hours, mostly reviews.
   - Check that the remote tip of `mac-b1-r4-20261109` is `4ddc820e`, the reviewed base.
   - Make the run-HEAD note commit on a new branch `ops-b1-restart-<YYYYMMDD>`, exactly as hand-off §1 says: the prose only; the JSON bindings stay byte-identical. Push it without force.
   - Get a fresh review of that exact HEAD, until *accepted*.
   - Check it out clean and detached in the TASL-7 exam work tree, then run the real author gate on it.
   - Run the read-only occupancy check, the host preflight and the handover, each re-reviewed for the new HEAD and run ID, as hand-off §2 step 4 lists. Publish the STATUS entry that R1-EXAM-B1-STATUS-FEATURE-07NOV requires.
   - Do the Track P marker transition exactly as hand-off §2 step 4:
     1. confirm the P.3a safe pause first;
     2. retire the old marker with `b1_o2_marker.py retire` and its receipt; nothing is deleted;
     3. keep both receipts;
     4. create the new marker in the new handover.
   - Use the new run ID `<first four hex of the run HEAD>_<UTC start date YYYYMMDD>_b` and the output tree `/home/dowling/exam-x/work/b1_<run ID>`. Nothing else of run `6835_20261108_a` is moved, overwritten or deleted.
3. **Launch** as for run 6835 and send the first monitor capture. The three anchors take about 30 minutes. The anchor gate now records the scripted-vs-random ordering descriptively; the 7B duplicate-rate check still stops the run if it fails.
4. **While the 15 candidates run** (estimated 2–4 days): take a read-only monitor capture at least every 12 hours (every 4–6 hours when you are connected anyway), and send the author a short Chinese status message once a day.
5. **At the end:** copy back as the exam runbook says, write the B1 report and a STATUS entry, and get a fresh review until *accepted*. **B2 is not started** by this runbook.

### 2.3 Connection windows for the HoreKa agent

KIT VPN and Tailscale cannot run at the same time on the Mac. Host jobs keep running in tmux while you are disconnected.
- When both tracks are in a long unattended stretch, tell the author: "VPN window possible now; next check needed by <time>". Examples: B1 candidates running and Track S idle, paused or in S0.5.
- The window may last up to the 12-hour B1 check interval.
- At the next check, reconnect and do the read-only captures.
- Never start, resume or review a host step while disconnected.

### 2.4 End state of this runbook

You are done when two things are true:
- **B1** has finished and its report is accepted, or it is at a STOP.
- **Track S** is paused: after §2.1 step 8 without line L1, after step 9 with it, or at a STOP.

Then send one closing Chinese summary. It covers: both tracks' state, commits and review verdicts; what is still open, namely the B2 gate, `tabular_mlp` on TASL-7 (Phase 3 S0.4/liveness/prior, the TASL-7 pause drill, 3.0b), and the Phase 4 summary and STOP 4; and the decisions the author needs to make.

## 3. STOPs

At a STOP: stop that track, preserve everything, report, and get a review. The other track continues.

- **B1:**
  - the diagnosis report is not class D with H1 supported and D7 PASS;
  - the restart base is not `4ddc820e`, or a commit after it is not reviewed;
  - the author gate fails;
  - another user's process occupies TASL-7's GPU (wait and report; never preempt);
  - the old Track P marker does not match its receipt;
  - the P.3a pause cannot be confirmed;
  - any STOP inside the new run. It is preserved and reported, never retried.
- **Track S:**
  - any pin mismatch, or the delivery checks of §2.1 step 1 fail;
  - `exhausted ≥ 1` in the S0.4 rerun, or more than 2 % in S0.5;
  - exit 3 twice in a row, or any other non-zero exit (rev 3.3 §0.6);
  - `liveness` exit 3;
  - an `obs_inflation` mismatch;
  - a fork-rebuild or A/A mismatch;
  - a forced pause (`FORCED` in `watch.log`);
  - anything that would need a code or pin change.
  - If a launch script REFUSEs because of a priority marker, a foreign GPU process or a held lease, that is not a STOP: wait, report, and re-check every 30 minutes. Never remove the cause.
- **Reviews:**
  - a finding you can fix only with a code or pin change;
  - a review still not *accepted* after five rounds.
- **Both tracks:**
  - a conflict between this file and the governing documents;
  - an unexpected host state after a reboot. Run a census, resume nothing, and report.

## 4. Lines the author may paste into your start message

Act on a line only if it appears in the start message.

- **L1 (Track S Phase 4, digits):** `Track S：STOP 3 重跑审查通过后，digits_mlp 继续 Phase 4 的 S0.5 和 S0.5b（新目录），完成后拷回并停下报告；S0.5 汇总和 STOP 4 等 tabular。`

## 5. Reporting

After each finished item, accepted review or STOP:
1. write a report under `docs/r1/reports/`;
2. add a STATUS entry;
3. send the author a short Chinese message: what was done, the commits, the review verdict, and what is next.

If the next item can start, start it in the same turn.

## 6. If your session restarts

Resume nothing on a host automatically. First read your own latest reports, the STATUS entries and the host state (read-only), and find the last item that finished with an accepted review. Then continue with the next item in §2, and say in your first message where you resumed.
