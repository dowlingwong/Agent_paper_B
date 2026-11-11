# Experiment agent — continuous runbook from 11 November 2026 (B1 restart and Track S rerun)

**Written 11 Nov 2026 by the chat session (Claude); AI-assisted.** Not independently reviewed. It adds an order of work and a waiting rule on top of the documents below. It authorizes nothing that they do not authorize. Where they differ, they win and you STOP to report the conflict.

You are the **experiment agent** (operator for TASL-2 and TASL-7; `prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.3). The Mac-local agent writes the code, the analysis and the hand-offs; you run them on the hosts. You never edit code to make a run work. Work through §2 item by item **without waiting for the author between items**. Stop a track only at the STOPs in §3. While one track waits, the other continues. Report to the author in **Chinese**; files and commits in **English**.

## 0. Governing documents (read once at the start)

| Topic | Document (branch @ commit) |
|---|---|
| Your general rules | `prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.3 (`docs/runbooks-09nov`) |
| B1 diagnosis and fix routes | `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` (`docs/runbooks-09nov`) |
| B1 diagnosis capture (done) | `reports/OPS_B1_DIAGNOSIS_CAPTURE_20261109.md` (`ops-b1-20261109` @ `d1d30687`) |
| B1 restart | `proposals/B1_RESTART_HANDOFF_20261109.md` (`mac-b1-r4-20261109` @ `4ddc820e`) |
| Track S procedure | Track S operator runbook rev 3.3 (`13badb0`), Phases 3–4 |
| Track S ruling at STOP 3 | `reports/TRACKS_PHASE3_20261109.md` §11 (`trackS-ops-20261030` @ `8ae46a48`) |

Standing rules stay as they are: no deletion (retire into `_to_delete/`), never touch what you did not start, no preemption of other users, fresh independent reviewer at every STOP and never accept your own unit, never push `main`, `r1` or `exam-x-*`, no force-push, never read secrets.

## 1. Waiting for the Mac-local agent

Two deliveries are expected. Check with `git fetch origin` **every 30 minutes** until both have arrived, then stop checking:

| Delivery | Branch | Ready when |
|---|---|---|
| D-B1: diagnosis report | `mac-b1-diag-report-20261111` (or any new `mac-b1-diag-report-*`) | `reports/B1_STOP_DIAGNOSIS_<date>.md` and its review file with *accepted* are on the branch |
| D-S: A2-U fix | `mac-tracks-a2u-stale-20261111` (or any new `mac-tracks-a2u-*`) | the fix commit, its review with *accepted*, and the dated PLAN §10 row naming the fix commit as the new Track S paper pin are on the branch |

A branch whose review is not yet *accepted* is not ready: keep checking. If nothing has arrived after 12 hours, tell the author once and keep checking hourly.

## 2. Order of work

### 2.0 Before any delivery: hand the capture to the Mac-local agent

If not done yet: copy `ssh.log` and `ssh.rc` from `/private/tmp/paper-b-b1-stop-diagnosis-20261109.OSnzb5iI/` unchanged into `~/Documents/agent_paper_B/Claude outputs/b1_diag_capture_20261111/` (mode 700) and check the SHA-256 against the receipt (`c6bc8a84…6df5`, `9a271f2a…86aa`). Never `git add` that folder. The originals stay where they are.

### 2.1 Track S (TASL-2) — when D-S is ready

Exactly as `TRACKS_PHASE3_20261109.md` §11 says:

1. Check the fix tip, its *accepted* review, and that the PLAN row binds the fix commit. Check out that commit detached and clean on TASL-2; check the harness pin `a3fedbb`, the llama.cpp build and the GGUF hash unchanged.
2. Fresh `k = 1` server on port 18101 with the readiness poll; lease held.
3. The Phase 3 S0.4 command, `--instances 10`, into **new** directories (`s04_r2_20261111` for `--out` and `--work`), new session names. All ten instances from the start. The old `s04` STOP scene is never written to.
4. After exit 0 with status `complete`, the dry run must show `roots_todo = 0`, `leaves_todo = 0` and failed units within the 2 % rule. Then `liveness`, then `fit_prior` (`--sigma-node 0.0066 --obs-inflation 1.0 --prior $OUT/a2u_prior_r2_20261111.json`); record the prior's SHA-256.
5. Stop the servers, verify the host state (lease free, no compute app, watcher running), copy back, write the rerun report and a STATUS entry, push to `trackS-ops-20261030`.
6. Fresh independent review until *accepted*.

Expected time: about 1 hour of running plus the review.

7. **Phase 4 for `digits_mlp`, only if line L1 (§4) is in your start message.** After step 6 is accepted: S0.5 and then S0.5b on TASL-2 with the accepted prior, exactly as rev 3.3 Phase 4, into new directories, each in its own session. Copy `$OUT/s05` back with `s05_calibration.jsonl` and `s05b_truncated.jsonl`. Then **stop Track S and report**: the S0.5 summary, the calibration gate and STOP 4 need `tabular_mlp` from TASL-7, which B1 occupies (§3). Expected time: about half a day, not measured.

### 2.2 B1 (TASL-7) — when D-B1 is ready

1. Read the report yourself. Continue only if it says **class D, H1 supported, D7 PASS** (7B duplicate rate inside the exact interval [0.42386590667728663, 0.5800007633587785]). Anything else is a STOP (§3).
2. Run the restart hand-off §§1–2 in its order:
   - the run-HEAD note commit on `ops-b1-restart-<YYYYMMDD>` (prose only; JSON bindings byte-identical);
   - a fresh review of that exact HEAD, until *accepted*;
   - a clean detached checkout on TASL-7, then the real author gate;
   - read-only occupancy check, host preflight, and handover, each re-reviewed for the new HEAD and run ID;
   - the Track P marker transition exactly as hand-off §2 step 4;
   - a new run ID `<first four hex>_<UTC date>_b` and a new output tree.

   Expected time: 2–3 hours, mostly reviews.
3. Launch. Send the first monitor capture. The three anchors take about 30 minutes. The anchor gate now records the ordering descriptively; the 7B duplicate-rate check still stops the run if it fails.
4. While the 15 candidates run (estimated 2–4 days): one monitor capture every 4–6 hours (read-only), and a short Chinese status message to the author once a day.
5. At the end: copy back as the exam runbook says, write the B1 report and a STATUS entry, and get a fresh review until *accepted*. **B2 is not started** by this runbook.

### 2.3 Connection windows for the HoreKa agent

KIT VPN and Tailscale cannot run at the same time on the Mac. Hosts keep running in tmux when you are disconnected. When both tracks are in a long unattended stretch (B1 candidates running; Track S idle or in S0.5), tell the author: "VPN window possible now, next check needed at <time>". Do not plan your work around the HoreKa agent. At each check, reconnect and do the read-only capture.

## 3. STOPs (stop that track, preserve, report, review; the other track continues)

- **B1:** the diagnosis report is not class D with H1 and D7 PASS; any review not accepted after three rounds; the author gate fails; another user's process occupies TASL-7's GPU (wait and report, never preempt); the old Track P marker does not match its receipt; the P.3a pause cannot be confirmed; any STOP inside the new run (preserved and reported, never retried).
- **Track S:** failed units above 2 % in the rerun; `liveness` exit 3; any pin mismatch; in S0.5 a fork-rebuild or A/A mismatch; anything that would need a code or pin change.
- **Both:** a conflict between this file and the governing documents; an unexpected host state after a reboot (census, resume nothing, report).
- **Natural pause:** Track S after S0.5/S0.5b on digits, or after step 6 if line L1 is absent. Report and wait for the author.

## 4. Lines the author may paste into your start message

Act on a line only if it appears in the start message.

- **L1 (Track S Phase 4, digits):** `Track S：STOP 3 重跑审查通过后，digits_mlp 继续 Phase 4 的 S0.5 和 S0.5b（新目录），完成后拷回并停下报告；S0.5 汇总和 STOP 4 等 tabular。`

## 5. Reporting

After each finished item, accepted review or STOP: a report under `docs/r1/reports/`, a STATUS entry, and a short Chinese message to the author with what was done, the commits, the review verdict, and what is next. If the next item can start, start it in the same turn.
