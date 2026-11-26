# Independent review — experiment agent runbook, 11 Nov 2026 (pre-execution gate)

**Reviewed artifact.** `docs/r1/prompts/EXPERIMENT_AGENT_RUNBOOK_20261111.md`, repo `Agent_paper_B` (origin `https://github.com/dowlingwong/Agent_paper_B.git`), branch `docs/runbooks-11nov` @ `7cfbe7c9bd2f4339818b9fb45472e21a32eda472`.

**Status.** Interim verdict (pre-ruling): `VERDICT: changes required` (two MAJOR findings). **Final verdict: accepted**, after the author ruling of 11 Nov 2026 — see the Addendum at the end of this file.

**Reviewer status.** Fresh, independent reviewer. I did not write the runbook, I have not executed any of its actions, I did not ssh to any TASL host, and I did not modify anything under `/Users/wongdowling/Documents/agent_paper_B` (only read-only `git cat-file`/`rev-parse`/`log`/`diff`/`merge-base`/`ls-remote` there). Writes were confined to `/tmp` and `/Users/wongdowling/Documents/agent_sys_paper/`.

**References.** `RB:NN` = line NN of the runbook (a byte-identical working copy at `/tmp/RUNBOOK_20261111.md`). `/tmp/dsh_pb` = shallow temp clone with origin refs; `/tmp/gov` = extracted §0 documents; `/Users/wongdowling/Documents/agent_paper_B` = the operator's repo (read-only).

---

## 0. Artifact verification

- The working copy is byte-identical to the branch blob:
  - `git show docs/runbooks-11nov:docs/r1/prompts/EXPERIMENT_AGENT_RUNBOOK_20261111.md | shasum -a 256` → `cff517a62dd4a8d63d3fdaba16d6cbe14a91f01b3ae06ee6f9d3317a238c882c`
  - `shasum -a 256 /tmp/RUNBOOK_20261111.md` → same value.
- `docs/runbooks-11nov` = `7cfbe7c9bd2f4339818b9fb45472e21a32eda472`; subject matches the one named in the review brief.
- Nothing under `agent_paper_B` was written by me; no push, fetch-to-repo, or checkout was performed there.

---

## 1. Fact-check of load-bearing literals

52 checked items. **43 PASS / 5 FAIL / 4 UNVERIFIABLE.** Evidence column is the exact command result or document location.

| # | Literal (RB line) | Result | Evidence |
|---|---|---|---|
| 1 | Whole file as the branch blob (RB:1–201) | PASS | SHA-256 `cff517a6…` both sides |
| 2 | Branch `docs/runbooks-11nov` @ `7cfbe7c9` (RB:3) | PASS | `git rev-parse docs/runbooks-11nov` = `7cfbe7c9…` |
| 3 | §0 `prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.3 on `docs/runbooks-09nov` (RB:11) | PASS | file title "revision 3.3"; blob `47b28aac…` on that branch |
| 4 | §0 `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` on `docs/runbooks-09nov` (RB:12) | PASS | blob `786e255f…` on that branch |
| 5 | §0 `reports/OPS_B1_DIAGNOSIS_CAPTURE_20261109.md`, `ops-b1-20261109` @ `d1d30687` (RB:13) | PASS | branch tip `d1d3068733ca…`; file present |
| 6 | §0 `proposals/B1_RESTART_HANDOFF_20261109.md`, `mac-b1-r4-20261109` @ `4ddc820e` (RB:14) | PASS | tip `4ddc820e49b…`; file present. (The task brief's "20260909" is a typo for 20261109; the file is `…_20261109.md`.) |
| 7 | §0 Track S runbook rev 3.3 at docs commit `13badb0` (RB:15) | PASS | title "revision 3.3"; `git show 13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` SHA-256 `a93fb84b…`, exactly the hash quoted in the 9 Nov launch-script header |
| 8 | §0 `reports/TRACKS_PHASE3_20261109.md` §11 on `trackS-ops-20261030` @ `8ae46a48` (RB:16) | PASS | tip `8ae46a4834…`; §11 is the STOP 3 ruling |
| 9 | Three polling places: origin / local branches / bundles under `Claude outputs/` (RB:28–32) | PASS | D-B1 bundle at the exact example path; local branch `mac-b1-diag-report-20261111`; `origin/…` refs |
| 10 | D-B1 bundle example path `b1_diag_capture_20261111/out/b1_diag_report_20261111.bundle` (RB:32) | PASS | file exists, 23,836 B |
| 11 | D-B1 branch `mac-b1-diag-report-20261111` @ `3e4d7cc9` (RB:38) | PASS | bundle head and `origin/…` both `3e4d7cc9fabe…`; local branch same |
| 12 | D-B1 report `reports/B1_STOP_DIAGNOSIS_<date>.md` + review ending *accepted* (RB:38) | PASS | `docs/r1/reports/B1_STOP_DIAGNOSIS_20261111.md`; `docs/r1/reviews/B1_STOP_DIAGNOSIS_REPORT_REVIEW_20261111.md` last line `VERDICT: accepted` |
| 13 | Bundle verifies; prerequisites present (RB:32) | PASS | `git bundle verify` → okay; requires `7b08c2ad…`, present in local repo (worktree `.claude-worktrees/b1-diag-20261109` and `overnight/mac-b1-diag-20261109-c`) and in origin (`origin/mac-b1-diag-20261109-c` = `7b08c2ad…`) |
| 14 | D-B1R branch `mac-b1-r4-20261109` fast-forward beyond `4ddc820e`, or new `mac-b1-r4*-*`/`mac-b1-r3-*` (RB:39) | UNVERIFIABLE | not yet delivered; origin `mac-b1-r4-20261109` is still `4ddc820e` |
| 15 | D-S branch `mac-tracks-a2u-stale-20261111` (or new `mac-tracks-a2u-*`) (RB:40) | UNVERIFIABLE | no such branch/bundle anywhere yet |
| 16 | Local-branch poll patterns `mac-b1-diag-report-* mac-b1-r4* mac-b1-r3-* mac-tracks-a2u-*` (RB:31) | PASS (minor gap) | patterns work for the expected names, but the repo already has `overnight/mac-b1-r4-20261109` (and `overnight/…` deliveries generally), which these patterns do not match — see finding M7 |
| 17 | Push scope: only `mac-b1-diag-report-*`, `mac-b1-r4*` (fast-forward only for `mac-b1-r4-20261109`), `mac-b1-r3-*`, `mac-tracks-a2u-*` (RB:34) | PASS | matches the author's "pushing ready deliveries itself"; the other pushes in §2.1/§2.2 are separately authorised (see §4) |
| 18 | "12 hours … then check hourly" for a non-author-waiting delivery (RB:42) | FAIL | not in any §0 governing document; the author's start message says "check every 30 minutes for D-B1R and D-S" and the B1 plan §6 says "every 30 minutes" — see finding M4 |
| 19 | Capture source `/private/tmp/paper-b-b1-stop-diagnosis-20261109.OSnzb5iI/` (RB:48) | PASS | directory exists, files dated 11 Nov 01:07 |
| 20 | Capture SHA-256 `c6bc8a84…` (ssh.log) and `9a271f2a…` (ssh.rc) (RB:48) | PASS | identical on the source files and on the copies in `Claude outputs/b1_diag_capture_20261111/`; matches the OPS receipt |
| 21 | "Copy … (mode 700)" (RB:48) | FAIL | the two copied **files** are `-rw-------` (0600); the containing **directory** is 0700, as is the source dir. Literal "files mode 700" is false — see finding M6 |
| 22 | "Never `git add` that folder" (RB:48) | PASS | consistent with `*.log` in `.gitignore` and with the capture handling rule |
| 23 | Five committed `s04` roots in `results/r1/tracks/digits_mlp/s04/roots.jsonl` (RB:52) | PASS | 5 lines, 5 `root_id`s (`tracks_S04_digits_mlp__s30001/…04/…06/…07/…09`) on `trackS-ops-20261030` |
| 24 | Ledger path `/home/dowling/r1_tracks/scratch/digits_mlp/s04/roots/<root_id>/root_trials.jsonl` (RB:52) | PASS | `r1/tracks/collect.py:926` writes `work/"roots"/root_id/"root_trials.jsonl"`, and `WORK=$R/scratch/<node>` (Track S §0.1); `--work $WORK/s04` in Phase 3 |
| 25 | `test (c)`, env `TRACKS_S04_ROOTS` (RB:40, 52) | UNVERIFIABLE | these names occur only in this runbook; the D-S deliverable will have to define them. The read-only copy step itself is well guarded (RB:52 "If a path does not exist … copy nothing else") |
| 26 | Old Track S pin `d10b05b7` (RB:61, 82) | PASS | commit exists in local repo, ancestor of `8ae46a48`; also recorded in `TRACKS_PHASE3_20261109.md` pins |
| 27 | Pins harness `a3fedbb`, llama.cpp `620d2225…`, GGUF `509287f7…`, server flags per rev 3.3 §0.2 (RB:67) | PASS | `TRACKS_PHASE3_20261109.md` pins line; Track S §0.2 |
| 28 | 9 Nov launch script `r1/tracks/ops/launch/tasl2_s04_20261109.sh` (RB:56, 70) | PASS | file present on `trackS-ops-20261030`; command shape, `trks_llm`, 18101, 900 s readiness poll, `LOG=$R/logs/s04_phase3_…` all as the runbook describes |
| 29 | New dirs/stop/session `s04_r2_20261111`, `trks_s04r2`, log rename (RB:72–77) | PASS | consistent with the 9 Nov script's `$OUT/s04`, `$WORK/s04`, `trks_s04`, `$R/logs/trks_s04.*`; new session also protects the old `trks_s04.*` STOP evidence |
| 30 | "With ten roots, one exhausted unit is already more than 2 %" (RB:88) | PASS | rev 3.3 §0.6 rate = exhausted/(roots+leaves+exhausted); S0.4 has 10 roots and no forks/leaves → 1/11 = 9.09 % > 2 % |
| 31 | Phase finished at dry-run `roots_todo=0` / `leaves_todo=0` (RB:87) | PASS | rev 3.3 §0.6 |
| 32 | `liveness` exit-3 STOP; `fit_prior --sigma-node 0.0066 --obs-inflation 1.0 --prior $OUT/a2u_prior_r2_20261111.json` (RB:91–92) | PASS | Track S Phase 3 command block; σ_node digits = 0.0066; prior name is exactly the one the STOP-3 ruling specifies |
| 33 | Copy back to `results/r1/tracks/digits_mlp/s04_r2_20261111/` with `SHA256SUMS` (RB:96) | PASS | Track S §0.8 copy-back |
| 34 | §2.1 step 9 gated on L1 present, after step 8 accepted (RB:102) | PASS | L1 (§4, RB:188) authorises exactly "after the STOP 3 rerun review passes, digits Phase 4 S0.5+S0.5b in new dirs, copy back and stop to report; S0.5 summary and STOP 4 wait for tabular" |
| 35 | S0.5 literals: `--W 40 --instances 20 --policy "static:0.00198,0" --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1`, deadline 28800, `$OUT/s05`, `$WORK/s05`; 0.00198 = 0.3 × 0.0066 (RB:104–105) | PASS | Track S Phase 4 template: `static:<0.3·σ_node>,0`; 0.3 × 0.0066 = 0.00198; all other flags match |
| 36 | S0.5b `trks-run trks_s05b - collect --phase S0.5b --node digits_mlp --truncate-W 8,10,12,20 --out $OUT/s05 --work $WORK/s05` (RB:108) | PASS | Track S Phase 4 template (port `-`, CPU phase) |
| 37 | New S0.5 launch script "refuses if `$OUT/s05` exists" (RB:103) vs "resumed with the identical command" (RB:107) | FAIL | with the guard as written, a deadline-stopped S0.5 cannot be resumed through the launch script; see finding M5 |
| 38 | D-B1 result literals: class D via H2 alone, H1 not supported, H3 supported, D7 PASS, 120/242 = 0.4959 (RB:116) | PASS | `B1_STOP_DIAGNOSIS_20261111.md` §1 table: class "D — resting on H2 alone", H1 NOT SUPPORTED, H2 SUPPORTED, H3 SUPPORTED, D7 "PASS: 120 / 242 = 0.4959" |
| 39 | D7 interval `[0.42386590667728663, 0.5800007633587785]` (RB:119) | PASS | `r1/scripts/configs/exam_b1_v2.json` @ `68357d3d`: `anchor_duplicate_reference.lower/upper` exactly these values |
| 40 | New run ID `<first four hex>_<UTC YYYYMMDD>_b`, tree `/home/dowling/exam-x/work/b1_<run ID>` (RB:134) | PASS | B1 handoff §2.5 |
| 41 | `b1_o2_marker.py retire` + receipt; old marker dev 66306 / inode 56261609 / SHA `092023e4…a1af`; keep both receipts (RB:129–133) | PASS | `r1/scripts/b1_o2_marker.py` has `retire` (requires `--receipt`, Linux `renameat2`); values are in B1 handoff §2.4 / B1 STOP report |
| 42 | Reviewed base / remote tip `4ddc820e`; nothing after it unreviewed (RB:124) | PASS | `4ddc820e` is `git log -1 -- docs/r1/reviews/B1_R4_REVIEW_20261109.md`; `git diff ddcf0eaf..4ddc820e` touches only `PLAN.md`, `B1_RESTART_HANDOFF`, `B1_R4_REVIEW` (docs only) |
| 43 | "Three anchors take about 30 minutes"; anchor gate now descriptive; 7B duplicate STOP retained (RB:135) | PASS | plan §7 ("about 30 minutes for the three anchors"); B1 handoff §1 (`fb57c6a4`), draft §4 |
| 44 | 15 candidates, estimated 2–4 days (RB:136) | PASS | plan §7 ("the 15 candidates were estimated at 2–4 days") |
| 45 | "read-only monitor capture at least every 12 hours (every 4–6 hours when connected anyway)" (RB:136) | FAIL | no governing basis; the operative B1 operator message v3 and the B1 monitor captures that state a cadence (INITIAL, SECOND) require **at least every 30 minutes** — see finding M1 |
| 46 | "KIT VPN and Tailscale cannot run at the same time on the Mac" (RB:141) | UNVERIFIABLE | environment fact; the governing HoreKa start-up runbook says the KIT VPN "may cut" the Mac's connections to TASL-2/TASL-7 — a weaker statement. The coordination rule itself is safe |
| 47 | §3 B1 STOP list (RB:159–166) | PASS | matches B1 handoff §0/§2.4 and plan §5.6 |
| 48 | §3 Track S STOP list (RB:167–176) | PASS (minor omissions) | matches rev 3.3 §0.6/§10 in substance; omits §10 "GPU time on a host passes 5 days" and "anything not covered → STOP and ask", and OPERATOR §3 escalations — see finding M3 |
| 49 | "a review still not accepted after five rounds" (RB:179) | FAIL | no governing basis: OPERATOR §0.2 / Track S §0.8 say re-check "until it writes accepted"; the only precedent, `B1_R4_REVIEW_20261109`, took **six** rounds — see finding M2 |
| 50 | §4 L1 text (RB:188) | PASS | semantically identical to the author's L1 (Chinese wording could not be checked byte-for-byte here; the Lead must confirm it is verbatim in the start message) |
| 51 | §5 reporting / §6 session-restart rules (RB:192–201) | PASS | OPERATOR §0.2 (reports + STATUS + Chinese message) and "resume nothing automatically" |
| 52 | §2.4 end state (RB:149–153) | PASS | matches §2.1 step 8/step 9/L1 and the B1 completion/STOP alternatives |

---

## 2. Governing-document consistency

The runbook is, on the whole, carefully aligned with §0. Four points need attention; three are findings and one is a note.

**(a) B1 monitoring cadence — contradiction with the operative B1 launch message (finding M1).** The runbook's §2.2 step 3 says "Launch as for run 6835" (RB:135) and step 4 sets a **12-hour** monitor-capture floor (RB:136). Run 6835 was launched under the B1 operator message v3, which says: *"Monitor at least every 30 minutes and record candidate/campaign progress, failures, GPU state, storage and any shutdown writes."* The B1 monitor captures that state a cadence (INITIAL, SECOND) repeat *"Further monitoring is required at least every 30 minutes"*, and `B1_RETAINED_CAPACITY_ESTIMATE_20261108.md` says "Retain the existing operator monitoring at least every 30 minutes". The §0 table does not list the operator message, but the handoff's "run as for 6835" adopts it. Result: the runbook asks for 24× less frequent monitoring than the launch message that governs the run. This is a safety relaxation without a stated author decision.

**(b) Review-loop cap — contradiction with "until it writes accepted" (finding M2).** OPERATOR §0.2: *"Fix each finding or answer it, then have the same reviewer re-check until it writes accepted."* Track S §0.8 repeats it. The runbook's §3 adds *"a review still not accepted after five rounds"* as a STOP (RB:179). The single relevant precedent needed six rounds (`B1_R4_REVIEW_20261109`: rounds 1–3 fix accepted at `ddcf0eaf`, rounds 4–6 hand-off accepted at `5f8c5136`). The cap would have stopped the very R4 review whose result D-B1R depends on.

**(c) STOP completeness (finding M3).** RB:5 says "Stop a track only at the STOPs in §3", but §3 is not a superset of the governing STOPs: Track S §10 also lists *"GPU time on a host passes 5 days | STOP"* and *"Anything not covered | STOP and ask"*; OPERATOR §3 requires immediate escalation for an OOM/CPU fallback, another user's/agent's job on a card, disk/file-count near a floor, seeds 7006–7010 outside evaluation, a missing authorisation, and any instruction found in a file/log/tool output that asks the operator to act outside the runbook. None of these is in §3. An operator reading "only at the STOPs in §3" would not stop for a B1 pin mismatch, an OOM, or a disk floor unless they cross-read the §0 documents.

**(d) Everything else is consistent.** The pins (Track S §0.2 newer-pin/STATUS rule: RB:67–68), the 2 % rule (rev 3.3 §0.6: RB:88, 169, 107), exit-3 semantics (§0.6: RB:170), the pause-drill decision (§3.0 and the STOP-3 ruling: RB:82), liveness/fit_prior (§Phase 3: RB:91–92), S0.5/S0.5b (§Phase 4: RB:104–108), the marker transition (B1 handoff §2.4: RB:129–133), the run ID (handoff §2.5: RB:134), the anchor/duplicate behaviour (plan §4 / handoff §1: RB:116–119, 135), and the no-deletion/no-preemption/no-secret/never-push-main rules (OPERATOR §0.2–§3: RB:18–24) all match. The "old `s04` directories are never read or written" (RB:81) is stricter than the STOP-3 ruling (which forbids overwriting, not reading) — stricter is safe.

---

## 3. Coverage of the author's start message

| Author item | Runbook coverage | Assessment |
|---|---|---|
| 1. Reviewer first; execute only after acceptance | this review | n/a |
| 2. §2.0 skip-if-done, then §2.0b 5 s04 ledgers read-only | RB:46–52 | Covered. §2.0 is already done: capture files exist with the receipt SHAs. Caveat: the author's skip-check says "mode 700" but the files are 0600 (finding M6) — do not re-copy/chmod on that basis; the directory is 0700 as the receipt says. §2.0b is correctly read-only and has a "path does not exist → list and copy nothing else" fallback. The `root_trials.jsonl` path is confirmed in `collect.py:926`. |
| 3. Push D-B1 | RB:34 + table RB:38 | Covered generically ("when ready … push"). **It is already on origin at `3e4d7cc9`** (remote ref updated by push at 02:08:37 local; origin confirmed by `ls-remote`), so the step is a verify-only no-op. Do not force; if origin differs from the bundle, report. |
| 4. Poll every 30 min in three places; push ready deliveries; first-arriving wins; stop only at §3 | RB:28–42, RB:5 | Covered for the three places and the push scope. The 12 h→hourly relaxation (RB:42) is a deviation from "check every 30 minutes" (M4). "Whichever arrives first" is implied by §1/§2.1/§2.2 rather than stated; fine in practice. |
| 5. B1 route R4, relaxed to "class D H1 or H2 and D7 PASS"; Mac-local revises/reviews; D-B1R | RB:39, 114–137 | **Admissible as framed, with one gap.** §2.2 step 1 (RB:117–120) requires (i) the committed dated PLAN row, (ii) the *updated* handoff §0 admitting exactly the D-via-H2 outcome after the reviewer checks class/H1/H2/D7 themselves, (iii) the exact D7 interval, (iv) an accepted D-B1R review naming the new reviewed base. That is exactly the author's relaxation, provided D-B1R also updates the RUNBOOK X.3 note ("effective only after a qualifying class-D diagnosis, i.e. H1 supported", RB-related doc) and the appendix draft ("A D verdict on H2 alone … is not covered"), which the D-B1R readiness row (RB:39) already requires. **Gap:** neither §1 nor §2.2 pins the route to R4 — the readiness row still permits `mac-b1-r3-*` and "for R3 also the new code and tests" (RB:39), and §1's push scope includes `mac-b1-r3-*` (RB:34). A D-B1R delivered on the R3 route could satisfy the literal checks while contradicting the author's choice. See finding M9. |
| 6. Track S: after STOP 3 rerun review accepted, digits Phase 4 S0.5+S0.5b in new dirs, copy back, stop to report; summary and STOP 4 wait for tabular (L1) | RB:102–112, 149–153, 188 | Covered and authorised by L1. The "S0.5 summary, the calibration gate and STOP 4 need tabular" (RB:110) is correct: `s05-summary` takes both `digits_mlp` and `tabular_mlp` and prints the calibration status. The extra "fresh review until accepted" after S0.5b (RB:109) is not in L1 but is conservative (note M10). |

---

## 4. Operational safety

- **Read-only steps stay read-only.** §2.0 copies from `/private/tmp` to the Mac and says "never `git add` that folder"; §2.0b says "no write, no `touch`, no server" and only rsyncs/scps from the host; §2.2 step 1 and §2.3's captures are read-only. PASS.
- **Old STOP scene.** RB:81 "old `s04` directories are never read or written" protects the preserved STOP scene. The only ambiguity is RB:95 "no STOP file or marker": the old `$OUT/s04/STOP` still exists by design, and Track S §0.4's standard resume uses `find $R/out -name STOP -delete`. Literal reading could tempt the operator to delete it. See M5b.
- **Pushes.** §1 authorises delivery branches only; `ops-b1-restart-<date>` is separately authorised by B1 handoff §1 and `trackS-ops-20261030` by OPERATOR §0.2 / Track S §0.8 (branch transferred). No `main`/`r1`/`exam-x-*`, no force-push, no push of a branch the operator did not receive. PASS, with the note that "This covers only branches named …" (RB:34) could be misread as forbidding the §2.1/§2.2 pushes; they are authorised elsewhere.
- **Marker/receipt handling.** Retire only after confirming the P.3a safe pause; `retire` renames into `_to_delete/` (nothing deleted); keep the old and retirement receipts; create the new marker in the new handover. Matches handoff §2.4. PASS.
- **Never preempt.** B1 STOP "another user's process occupies TASL-7's GPU (wait and report; never preempt)"; Track S "a launch script REFUSEs because of a priority marker, a foreign GPU process or a held lease … wait, report, re-check every 30 minutes. Never remove the cause." PASS.
- **Disconnection.** §2.3 "Never start, resume or review a host step while disconnected"; "host jobs keep running in tmux". Safe. The VPN/Tailscale claim is environment-UNVERIFIABLE but the rule is conservative.
- **Reboot.** RB:182 "unexpected host state after a reboot. Run a census, resume nothing, and report" is safe but conflicts in wording with Track S §10 "TASL-7 reboots | Every unit resumes. Restart the watcher and the servers, then the collectors with the same commands" and OPERATOR §0.2 item 4. See M11.
- **D-B1 capture.** The report says the private capture (`ssh.log` + `ssh.rc`) is "committed after [review] … under `reports/b1_stop_diagnosis_capture_20261111/` with a `SHA256SUMS`", but the branch/bundle contains only `SHA256SUMS` and `ssh.rc`; `ssh.log` is absent (`*.log` in `.gitignore`). This does not affect the runbook's D-B1 readiness criteria (report + accepted review), but the report's provenance claim is false and the Mac-local agent should either force-add `ssh.log` (or state why it is withheld) and correct the report. See Notes.

---

## 5. Internal consistency

- §2.2 step 1 vs §3 B1 STOPs: consistent (the duplicate-rate failure is caught by "Anything else is a STOP (§3)" and by §3's "updated hand-off does not admit the reported outcome"; the reviewed-base condition is in both).
- §2.1 step 9 vs §2.4: consistent ("after step 9 with it"; the closing summary lists the tabular items).
- "one exhausted unit > 2 %" for 10 roots: correct (1/11 = 9.09 %).
- §2.1 step 3 edit list vs step 4 command: consistent (dirs, STOP path, `trks_s04r2`, log rename). But the new output-dir guard vs the "re-run the launch script (same command; it resumes)" rule in step 5 is under-specified: how does the script distinguish a fresh run from a resume? Same issue, more consequentially, for S0.5 (RB:103 vs RB:107). See M5.
- §1 push scope vs §2.2 step 2's `ops-b1-restart-*` and §2.1's `trackS-ops-*`: the §1 "covers only …" sentence is a scope statement for the delivery pushes; the other two pushes are separately authorised. Not a contradiction, but worth one cross-reference sentence.
- §2.1 step 7's copy-back "and the prior": §0.8 says copy `$OUT/<phase>*` trees; the prior lives at `$OUT/a2u_prior_r2_20261111.json` (outside the phase dir). The intended destination of the prior file is not stated. Minor.
- §2.0's "(mode 700)": the files are 0600 (M6).
- Dates/SHAs: all 8 hash literals in the file resolve (`13badb0`, `4ddc820e`, `8ae46a48`, `d1d30687`, `a3fedbb`, `620d2225`, `509287f7`, `d10b05b7`), and the two exact interval bounds match `exam_b1_v2.json` @ `68357d3d`.

---

## 6. The D-B1 deliverable (the first push)

Verified read-only:

- `git bundle verify /tmp/gov/b1_diag_report_20261111.bundle` → **okay**; head `refs/heads/mac-b1-diag-report-20261111` = `3e4d7cc9fabe5ce28a1f9bd79cea016c69820934`; prerequisite `7b08c2ad548e7b2b33362c03d9d005b9e4e5a3b6` is present in the receiving local repo (branch/worktree) and in origin (`origin/mac-b1-diag-20261109-c`).
- Branch tree carries: `docs/r1/reports/B1_STOP_DIAGNOSIS_20261111.md` (class D via H2 alone; H1 NOT SUPPORTED; H3 SUPPORTED; D7 PASS 120/242 = 0.4959, inside the pinned interval; R4-under-A1 "Not applicable" for H2 alone) and `docs/r1/reviews/B1_STOP_DIAGNOSIS_REPORT_REVIEW_20261111.md` whose final line is exactly `VERDICT: accepted`.
- The branch is **already on origin** at the same SHA (remote-tracking ref updated by push at 02:08:37 local; `git ls-remote origin` confirms). The local branch is also at `3e4d7cc9`. Pushing again is a no-op; use the origin copy, as RB:34 says.
- The capture subfolder in the branch has `ssh.rc` (2 B, `0\n`) and `SHA256SUMS` (listing `ssh.log` and `ssh.rc`) but **not `ssh.log`** (see Notes).

---

## 7. Findings

Each finding: severity, runbook line, issue, minimal fix.

**M1 — MAJOR — RB:136 (also RB:135, RB:143).** The B1 monitor-capture cadence is "at least every 12 hours (every 4–6 hours when connected anyway)". Run 6835's operative launch message (B1 operator message v3, which the handoff adopts by "Launch as for run 6835") and the B1 monitor captures that state a cadence require **at least every 30 minutes** ("Monitor at least every 30 minutes and record candidate/campaign progress, failures, GPU state, storage and any shutdown writes"; "Further monitoring is required at least every 30 minutes"). A 2–4 day candidate phase with a 12 h gap can miss a STOP, a disk-floor approach or a hung worker for half a day, and it contradicts the launch message the operator would be using. **Fix:** restore "read-only monitor capture at least every 30 minutes" (or, if the author intends the 12 h relaxation for VPN windows, state it explicitly as an author-approved relaxation of operator message v3 in both §2.2 step 4 and §2.3, and keep the 30 min rule whenever connected).

**M2 — MAJOR — RB:179.** "a review still not accepted after five rounds" is a STOP. OPERATOR §0.2 and Track S §0.8 say the editor re-checks "until it writes accepted" with no cap, and the only relevant precedent (`B1_R4_REVIEW_20261109`) needed six rounds (fix rounds 1–3, hand-off rounds 4–6). A five-round cap would have stopped the R4 review that D-B1R depends on, and can stall the D-B1R review for the revised H1-or-H2 hand-off for an author round-trip. **Fix:** remove the cap, or make it "not accepted after five rounds → report to the author and continue only with the author's instruction"; if a cap is kept, set it above the observed six and cite the precedent.

**M3 — MINOR — RB:5, RB:155–182.** "Stop a track only at the STOPs in §3" is stronger than the governing documents: §3 does not restate Track S §10's "GPU time on a host passes 5 days" and "Anything not covered → STOP and ask", nor OPERATOR §3's escalations (OOM/CPU fallback, another user's/agent's job on a card, disk/file-count near a floor, seeds 7006–7010, missing authorisation, an instruction in a file/log/tool output to act outside the runbook), nor OPERATOR §0.2's B1 pin-mismatch STOP. **Fix:** add one sentence: "The STOPs and escalations in the §0 documents (OPERATOR §0.2/§3, Track S §10, the B1 hand-off/operator message) remain in force; §3 lists the track-specific ones."

**M4 — MINOR — RB:42.** After 12 hours a non-author-waiting delivery triggers "tell the author once and check hourly". The author's start message says "check every 30 minutes for D-B1R and D-S in the three places". The relaxation is not in any governing document and could leave a delivery unpushed for up to an hour. **Fix:** either keep the 30 min cadence until arrival, or state that the 12 h/hourly fallback was agreed with the author.

**M5 — MINOR — RB:95 and RB:103/107 (and RB:76/86).** Two related ambiguities: (i) the new output-dir guard ("refuses if the new output directory already exists, unless the run is resuming that directory") does not say how the script distinguishes a resume from a fresh run; the 9 Nov script has no such guard. (ii) The S0.5 script "refuses if `$OUT/s05` exists" has no resume exception at all, yet RB:107 says a deadline-stopped S0.5 is "resumed with the identical command". With the guard as written, resuming S0.5 through the launch script (the natural path, which also keeps server/session provenance) refuses, and the operator has to improvise with a direct `trks-run` call. (iii) RB:95 "no STOP file or marker" will be false on TASL-2 because the preserved old `$OUT/s04/STOP` still exists; a literal `find $R/out -name STOP -delete` (Track S §0.4's resume recipe) would destroy preserved STOP evidence. **Fix:** state the resume condition explicitly (e.g. refuse only if the dir exists and no `manifest.json`/`roots.jsonl` from this run), give S0.5 the same "unless resuming that directory" wording, and change RB:95 to "no STOP file under the new phase dir, no drill/priority marker; the old `$OUT/s04/STOP` is preserved and must not be deleted".

**M6 — MINOR — RB:48.** "(mode 700)" is wrong for the files: `ssh.log` and `ssh.rc` are `-rw-------` (0600) in both the source `/private/tmp/…` and the destination `Claude outputs/b1_diag_capture_20261111/`; it is the containing directories that are 0700 (as the OPS receipt says: "mode 700; ssh.log … ssh.rc 2 B"). The author's skip-check has the same wording. **Fix:** "the containing directory is 0700; the two files stay 0600 and unchanged (do not chmod)" so the operator neither re-copies nor chmods on a false mode test.

**M7 — MINOR — RB:31, RB:34.** The local-branch poll patterns miss `overnight/…` refs, and the operator's repo already has `overnight/mac-b1-r4-20261109` (the overnight agent's branch name for the same branch) plus other `overnight/…` branches. If the Mac-local agent fast-forwards that local branch rather than a bare `mac-b1-r4-20261109`, the poll misses it. The push scope is likewise written on bare branch names. **Fix:** poll with `git for-each-ref refs/heads | grep -E '(^|/)(mac-b1-diag-report|mac-b1-r4|mac-b1-r3|mac-tracks-a2u)'` (or include `overnight/*`), and say which local ref is the delivery to push (bare name only).

**M8 — MINOR — RB:34.** No instruction for the case where the delivery branch already exists on origin at a **different** SHA (today it exists at the same SHA, so this is not yet triggered). "fast-forward or a new branch, never force" implies a non-fast-forward push fails, but the operator could be tempted to push under a different name or force. **Fix:** "If origin already has the branch at a different SHA, do not push and do not force; compare the origin tip, the bundle tip and the local tip, report all three, and wait."

**M9 — MINOR — RB:39 (and RB:34).** The D-B1R readiness row still admits a new `mac-b1-r3-*` branch ("for R3 also the new code and tests") and the §1 push scope includes `mac-b1-r3-*`, but the author's start message fixes the route to **R4** (relaxed to H1-or-H2). A D-B1R delivered on the R3 route could satisfy the literal readiness checks while contradicting the author's choice (R3 adds new code/tests; R4 does not). **Fix:** say explicitly that the committed route line must be the author's R4 relaxation; any other route (R1/R2/R3) is a STOP to report, not a delivery to accept.

**M10 — MINOR — RB:109.** The fresh review after S0.5b is not in L1 ("copy back and stop to report") and STOP 4 is the Phase-4 review loop after the summary. Extra review is conservative, but it is an added requirement not authorised by the start message, and §2.4's "paused after step 9" does not mention it. **Fix:** either drop it (report and pause, as L1 says) or note it is an optional extra review that must not replace STOP 4.

**M11 — MINOR — RB:182.** "unexpected host state after a reboot. Run a census, resume nothing, and report" is inconsistent in wording with Track S §10 ("TASL-7 reboots | Every unit resumes. Restart the watcher and the servers, then the collectors with the same commands") and OPERATOR §0.2 item 4. An operator could conclude they must not restart Track S after the expected reboot. **Fix:** scope it to "if the host state after a reboot is not the expected one", and point to the Track S §10 restart procedure for an ordinary reboot.

**M12 — MINOR — RB:28, RB:124.** Minor internal/state freshness issues: RB:28's status "D-B1 exists as a bundle" is stale (it was pushed to origin at 02:08, before the runbook commit at 02:10) and "D-B1R waits for the author's route line" is stale (the author has chosen R4; D-B1R waits for the Mac-local revision/review); RB:124's "nothing after `4ddc820e` is unreviewed" assumes the D-B1R branch descends from `4ddc820e` (true for a fast-forward; not stated for a "new `mac-b1-r4*-*`" branch). **Fix:** refresh the status line and say "if the delivery is a new branch, `4ddc820e` must be its merge-base; otherwise STOP".

---

## 8. Notes that do not gate acceptance by themselves

- **D-B1 capture discrepancy (report-level, not a runbook defect).** The D-B1 report §2 says the private capture (`ssh.log`, `ssh.rc`) "is committed after [the review], unchanged, under `reports/b1_stop_diagnosis_capture_20261111/` with a `SHA256SUMS` file", and the tip commit is titled "commit the private capture after the report's review was accepted" — but the tree/bundle contains only `SHA256SUMS` and `ssh.rc`; `ssh.log` is absent (`*.log` in `.gitignore`). The D-B1 readiness criteria (RB:38) are still met, so this does not block the runbook; the Mac-local agent should force-add `ssh.log` (it is no longer private once the review is accepted, per the OPS receipt) or correct the report. The operator should not `git add` the `Claude outputs/` folder (RB:48) to compensate.
- **D-B1 is already pushed.** Origin `mac-b1-diag-report-20261111` = `3e4d7cc9` (remote ref updated by a successful push at 02:08:37). The runbook's "push that branch yourself" step is a verify-only no-op now; verify `origin` tip = bundle tip = local tip and do not force.
- **L1 verbatim.** The §4 Chinese line matches the author's L1 in meaning. I cannot verify byte-for-byte against the original start message from the repository; the Lead should confirm it is the author's line verbatim before relying on "present verbatim".
- **Governing filename in the brief.** The brief's `B1_RESTART_HANDOFF_20260909.md` is a typo; the governing file is `B1_RESTART_HANDOFF_20261109.md`, present on `mac-b1-r4-20261109` @ `4ddc820e`.

---

## 9. Verdict basis

An operator following this runbook plus the author's start message would execute the author's work order correctly and would not push forbidden branches, preempt other users, touch the preserved STOP scene, or write TASL-2 during the read-only steps. Almost every load-bearing SHA, branch, path and arithmetic check is correct (43/52 PASS; the 4 UNVERIFIABLE items are future deliveries or an environment fact). However, two deviations are not "wording" issues and would change what the operator does: the **12-hour B1 monitoring** floor contradicts the operative B1 launch message's 30-minute requirement, and the **five-round review cap** contradicts the governing "until it writes accepted" loop and the six-round R4 precedent. The STOP-list completeness and the resume-guard wording are additional consistency risks. These need the author's decision or a text fix before the operator starts the B1 line.

**Interim verdict (pre-ruling):** changes required — superseded by the Addendum below.

---

## Addendum — author ruling (11 Nov)

**Basis.** The Lead relayed the author's decision on the two MAJOR findings and the related items; it is **in force for this execution**. It is the author's decision, not the Lead's or the reviewer's opinion. I cannot independently authenticate the author's words from the repository; I treat the relayed text as the ruling.

**Ruling (as received).**
1. B1 monitoring follows `B1_OPERATOR_MESSAGE_V3_20261107`: read-only monitor captures **at least every 30 minutes**. RB:136's 12-hour / 4–6-hour wording, and RB:143/§2.3 as a relaxation, are **not authorised and void**. While disconnected, §2.3 applies (no host steps; reconnect and capture).
2. The review loop follows OPERATOR §0.2 / Track S §0.8: re-check until the reviewer writes **accepted**. RB:179's five-round STOP is **void**. If a review is still not accepted after six rounds, report to the author and await instruction — never accept silently, never stop the track without reporting.
3. §1 polling stays **every 30 minutes** for both pending deliveries; RB:42's 12 h→hourly fallback is **void**.
4. The D-B1R route is the author's **R4 relaxation**: class D with H1 or H2 and D7 PASS — committed dated PLAN row + updated hand-off §0 + RUNBOOK X.3 note + appendix draft + accepted review naming the reviewed base. A delivery on R1/R2/R3 is **reported, not accepted** (M9).
5. All §0 governing STOPs and escalations **remain in force alongside §3** (M3).
6. §2.0 is already done and must not be redone: containing dir 0700, files 0600; **no chmod, no re-copy** (M6).
7. Preserve the old `$OUT/s04/STOP`; "no STOP file" means no STOP under the new phase dir and no drill/priority marker (M5(iii)).
8. M5(i)/(ii) (resume-guard) is resolved **operationally**: the new launch scripts will distinguish a fresh run from a resume of the same directory; a deadline-stopped session is resumed with the identical `trks-run` command. A wording clarification, not a runbook text change.
9. M7/M8/M12 are handled **operationally**: poll all refs matching `/(mac-b1-diag-report|mac-b1-r4|mac-b1-r3|mac-tracks-a2u)/`, including `overnight/*`; if origin already has the branch at a different SHA, do not push — compare origin/bundle/local tips and report; stale status lines are refreshed in the operator's report.
10. The extra fresh review after S0.5b (RB:109) **stays as written**: the author said "the rest per the runbook".

**Re-check of the findings against the ruling.**

| Finding | Status after the ruling |
|---|---|
| M1 — 12 h B1 monitor (RB:136/143) | **Resolved** by ruling 1: the governing 30-minute requirement is restored; the runbook's relaxation is void. |
| M2 — five-round review STOP (RB:179) | **Resolved** by ruling 2: "until accepted" restored; the cap is replaced by a six-round report-and-await-instruction, which is the review's recommended fix. |
| M3 — §3 STOP completeness (RB:5/§3) | **Resolved** by ruling 5: all §0 STOPs/escalations keep force. |
| M4 — RB:42 polling fallback | **Resolved** by ruling 3. |
| M5(i)/(ii) — resume guard vs deadline resume | **Resolved operationally** by ruling 8. |
| M5(iii) — "no STOP file" vs preserved old `$OUT/s04/STOP` | **Resolved** by ruling 7. |
| M6 — "mode 700" (files 0600, dir 0700) | **Resolved** by ruling 6. |
| M7 — `overnight/…` refs missed by poll patterns | **Resolved operationally** by ruling 9. |
| M8 — origin branch at a different SHA | **Resolved operationally** by ruling 9. |
| M9 — route not pinned to R4 (R3 still admitted) | **Resolved** by ruling 4. |
| M10 — extra review after S0.5b (RB:109) | Author decision (ruling 10) to keep it as written; conservative, no conflict. |
| M11 — reboot bullet vs Track S §10 / OPERATOR §0.2 | Not named in the ruling, but **resolved in substance** by ruling 5 (the §0 documents, including Track S §10's reboot procedure, remain in force). RB:182 is scoped to an "unexpected host state"; for the expected TASL-7 reboot the operator restarts the watcher/servers/collectors per §10. Wording-only residual note. |
| M12 — stale status / `4ddc820e` ancestry | **Resolved operationally** by ruling 9; the readiness checks still require a fast-forward delivery to descend from `4ddc820e`, and the operator reports the actual status. |

**Residual non-blocking notes.**

- The runbook **text** still contains the voided wording (RB:42, RB:136, RB:143, RB:179). With the ruling in force the operator follows the ruling, so this is **not** a blocking conflict, but the file and the ruling now diverge. Recommended follow-up (not a gate): a small edit to those four lines, or an explicit "the author ruling of 11 Nov supersedes these lines" note at the top, so a later session that sees only the file cannot re-introduce the relaxation.
- M11 remains a wording ambiguity only; §0 and ruling 5 govern the reboot case.
- The D-B1 report claims `ssh.log` is committed; the branch/bundle carries only `ssh.rc` + `SHA256SUMS` (`*.log` is gitignored). Report-level issue; D-B1 readiness is report + accepted review and is met.
- D-B1 is already on origin at `3e4d7cc9` (pushed 02:08:37 local); verify only, never force.
- The L1 verbatim check and the brief's `B1_RESTART_HANDOFF_20260909` filename typo remain on the Lead; no blocking effect.
- The UNVERIFIABLE items (D-B1R/D-S deliveries, `test (c)`/`TRACKS_S04_ROOTS`, VPN/Tailscale) remain forward-looking; the runbook's D-B1R/D-S readiness checks and §2.0b guards cover the first two, and §2.3's rule is conservative.

**Final assessment.** With the author ruling in force, an operator following the runbook + start message + ruling can execute the authorised work — §2.0/§2.0b (verify, no re-copy), the D-B1 verify/no-op push, the R4 D-B1R restart (with the RUNBOOK X.3 note and appendix draft updated for H1-or-H2), and the Track S S0.4 rerun → L1 S0.5/S0.5b → pause/report — without violating the governing documents, without a forbidden or force push, without preempting other users, without touching the preserved STOP scene, and without writing TASL-2 during the read-only steps. No blocking conflict remains.

VERDICT: accepted
