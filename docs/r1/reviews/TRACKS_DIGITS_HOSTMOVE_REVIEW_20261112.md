# Independent review — Track S `digits_mlp` host-move proposal/author-decision record (12 Nov 2026)

**Reviewed artifact.** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` (70 lines, sha256
`a31317ab4a10a2f8e723a6f94f2243e8c55accbf0f39da443f800566145b36e0`) and the top
`docs/r1/STATUS.md` entry (whole file sha256
`ffb81bc2a9975032dd0e9fc44eca7ca9bcc165d2bb0aa5b604880b68ce18ce42`), repo
`https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, commit
`23a83b3b3a31394c9d66fe07db16257509d9a44f` (parent
`25907343728fe48fbe9f1543b6b3a0921eb7012d`; report blob and STATUS blob above), committed
`2026-11-12T23:47:52+01:00` (`22:47:52Z`) by `Dowling Wong <wangdowling@gmail.com>`,
message "AI-assisted; operator: DSH experiment-agent session."

**Reviewer status.** Fresh, independent; I did not write this record. Read-only on `tasl7`
(`ls/stat/cat/sha256sum/git rev-parse/status/tmux ls/nvidia-smi/flock probe/ps/pgrep`); no writes,
signals, GPU use or server start on TASL-7; TASL-2 not contacted. Writes only under
`/Users/wongdowling/Documents/agent_sys_paper/` and `/tmp`; nothing under
`/Users/wongdowling/Documents/agent_paper_B` was modified. This review executes nothing and starts no run.

**Unit verified.** `/tmp/tshm_review` clone: `git ls-remote`/fetch; `23a83b3b` resolves; parent
`25907343` is the S0.5 launch-script commit (`2026-11-12T20:54:50+01:00` = `19:54:50Z`). The same
unit is in the TASL-7 bare repo (`refs/heads/trackS-ops-20261030 = 23a83b3b…`). The branch also
contains the accepted S0.4 rerun (review `TRACKS_S04_RERUN_REVIEW_20261111.md`, last line
"Verdict: accepted") and the PLAN row `R1-TRACKS-A2U-STALE` is *not* on this branch's `docs/r1/PLAN.md`
(see F7).

---

## 1. Author-decision recording — PASS, with wording notes

- The report quotes only the decision ("quoted only as the decision …"), names the author and the date
  (author's chat message, 12 Nov 2026), and labels it "not yet executed". It does not present itself
  as a PLAN row. PASS.
- §4 is explicitly a "PLAN §10 row draft", "to be committed by the author/Mac agent or with the
  author's relay"; the operator note (lines 60–62) says the operator does not add author decisions to
  PLAN unilaterally and that until the row is committed the report only records the decision and
  conditions. This is governance-correct: no self-authorization, no execution, no operator-invented
  author decision. PASS.
- Note (F10): the quotation says "**migrate** `digits_mlp` to TASL-7" while the brief/STATUS say
  "**move**". The substance is the same, but quote marks imply verbatim; mark it as a paraphrase or
  quote the original. Minor.
- Note (F12): the STATUS heading says the move "**authorised**" while the PLAN row is a draft
  pending. The report's own "only records the decision" controls; since no work depends on it yet
  (runbook §1: "A decision is a dated row in PLAN §10 before work depends on it"), this is not a
  self-authorization, but "decision recorded; PLAN row pending" is the accurate wording. Minor.

## 2. Host facts (read-only TASL-7, 2026-11-12/13)

| Fact | Report | Observed | Verdict |
|---|---|---|---|
| hostname / GPU / driver / CPUs | TASL-7, RTX 4090, 580.178.04, 24 | same (`nvidia-smi` 580.178.04, 24; `nproc` 24) | PASS |
| `$R` layout | `bin/ launch/ logs/ models/ opt/llama.cpp remotes/Agent_paper_B.git scratch/ out/ work/` | all present | PASS |
| `work/Agent_paper_B` | `d10b05b7` clean | `d10b05b738fc0e0dba54e0e692c248bedf095482`, `status --porcelain` empty, detached | PASS |
| `work/autoresearch_harness` | `a3fedbb` clean | `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, clean | PASS |
| llama.cpp / server | `620d2225…`, `v0.7.0-dev`, build 11669 | same; `version: 0.7.0-dev (build 11669, commit 620d2225c)` | PASS |
| GGUF sha256 | `509287f7…4d3c` | `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` | PASS |
| Track S venv | Python 3.11.18, numpy 2.4.6, sklearn 1.9.1 | same (`venv/bin/python -V`; numpy 2.4.6 / sklearn 1.9.1; `pip_freeze.txt` sha `f1c818e5…`) | PASS |
| S0.1 evidence on TASL-7 | only `tabular_mlp`; no `digits_mlp` S0.1 | `$OUT` = `smoke/`, `tabular_mlp/` only. Precision: the checkout also contains the *TASL-2* digits S0.1 (`results/r1/tracks/digits_mlp/s01/serial.json`, `"host": "TASL-2"`); the claim is true only as "no TASL-7-hosted digits S0.1" (F6) | PASS with precision note |
| Bare repo | `remotes/Agent_paper_B.git` | `refs/heads/mac-tracks-a2u-stale-20261111 = c8b13b5d63d3d30f5afa642928f1458e863e8935`; `trackS-ops-20261030 = 23a83b3b…`; pin `8237fd02…` present and an ancestor of `c8b13b5d`; no branch *named* for the pin (F8) | PASS with note |
| Disk | (not stated in report) | `/home/dowling` 529 G avail, 71 % used | PASS (no contradiction) |
| B1 `_c` running + marker | `4b31_20261112_c` | tmux `b1_4b31_20261112_c`; `exam_runner` pid 3736030; GPU 18,010 MiB / 99 %; `~/r1_locks/trackx_evidence.active` = `{"head":"4b312844…","run_id":"4b31_20261112_c"}`, dev 66306, ino 56261618, sha256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, matching `b1_handover_4b31_20261112_c/marker-receipt.json` | PASS |
| Track P marker | absent | `trackp_evidence.active` absent; no `r1p_*` tmux | PASS |
| TASL-2 s05 preservation | preserved | unverifiable (TASL-2 unreachable by design); no Mac copy exists | UNVERIFIED |
| **TASL-2 Track S venv comparison** | **"differed (numpy 2.4.4 / sklearn 1.8.0)"** | **contradicted**: `TRACKS_HOST_FACTS_20261030.md` §0.5 records the two Track S venvs' `pip_freeze.txt` as byte-identical (65 packages, sha `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687`; only Python patch 3.11.17 vs 3.11.18), and `TRACKS_PHASE3_20261109.md` §1 records TASL-2's frozen venv as Python 3.11.17, **numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, pandas 3.1.0**, matching the freeze. The 2.4.4/1.8.0 figures are the deepthought/noise-floor harness-locked venv (`STATUS.md:665`, `NOISE_FLOOR_COMMON_20261022.md`), not TASL-2 Track S. | **FAIL — STOP-grade factual discrepancy (F1)** |

No other host-fact disagreement was found.

## 3. Conditions — completeness and safety

| Condition (report lines) | Verdict |
|---|---|
| 1. B1 `_c` normal end + marker retired by reviewed post-run procedure; lease free; no foreign compute; STOP waits for author (33–35) | PARTIAL — the procedure is not written/defined; Track X authority ambiguous (F4, F5) |
| 2. digits host facts + Phase-1-equivalent S0.1 on TASL-7, failure = STOP (36–40) | FAIL — no committed TASL-7 S0.1 launch script and no independent review of the S0.1 result before S0.5 (F2) |
| 3. pin `8237fd02…` detached/clean via TASL-7 bare repo (41–42) | PASS in substance; "the pin branch" is imprecise and the refs were pushed at 22:49:25Z, after the 22:41Z verification/22:47Z commit (F8) |
| 4. prior `5c849d15…` copied and verified, host change disclosed (43–45) | FAIL premise — the "worker-venv host difference" is false (F1); the prior hash itself is correct (`5c849d15…` in `results/r1/tracks/digits_mlp/s04_rerun20261111/a2u_prior_r2_20261111.json`) |
| 5. new `tasl7_s05_*` / `tasl7_s05b_*`, new dirs, k=1, prior sha, W 40/20 instances/static:0.00198,0/obs 1.0/8 h/ENGINEERING_ONLY, committed+reviewed (46–49) | PASS for S0.5/S0.5b; does not cover the S0.1 script (F2) |
| 6. nothing of Track X/Track P/TASL-2 touched; Track P paused; no Track P marker; TASL-2 preserved (50–51) | FAIL — literal wording contradicts condition 1: retiring the B1 (Track X) marker is a Track X scene change; the operator is not told not to perform it (F4) |
| 7. after S0.5 run S0.5b, copy back, report+STATUS, fresh review, pause (L1) (52–54) | PARTIAL — copy-back target `results/.../s05/` collides with the preserved TASL-2 s05 scene (F3); Phase 4 calibration gate and §10 STOPs not restated (F9) |

## 4. Risks / caveats

- **Worker/library difference:** the stated TASL-2 vs TASL-7 library difference does not exist for the
  Track S venv (F1). The real differences are Python patch 3.11.17/3.11.18, 32 vs 24 CPUs, GPU UUID,
  per-host llama.cpp build and TASL-2's unsynchronised clock. This *strengthens* prior reuse but must
  be disclosed correctly; the PLAN row and STATUS currently enshrine the false version.
- **24 vs 32 CPUs:** stated in §2 but its effect on the S0.5 projection/runtime is not discussed. The
  8 h deadline + resume covers it; the report should say the projection is recomputed on TASL-7 and a
  deadline stop is a resume, not a failure.
- **Prior computed on TASL-2:** correctly disclosed; cross-host comparability is not claimed. The
  Phase 4 calibration gate (coverage in [0.70, 0.90], λ₂ branch, second failure = STOP) is the actual
  safeguard and should be restated in condition 7.
- **What would invalidate the move:** S0.1 identity < 100 %, pin/GGUF/llama/flag mismatch, B1 STOP,
  lease not free, or a TASL-2 return before B1 ends. These are covered except a TASL-2 return *after*
  the TASL-7 S0.5 starts (F11).
- **Missing STOP conditions:** the §10 5-day GPU-time cap (TASL-7 is shared with tabular/B1), the 2 %
  exhausted rule, exit 3 twice, fork-rebuild/A-A mismatch, and the calibration gate are not restated;
  "the same rev-3.3 Phase 4 command" implies them but the record should say so (F9).

## 5. What must still happen independently

1. **B1 `_c` marker retirement:** the Track X/Mac agent must write the post-run procedure, a fresh
   reviewer must accept it, and the retirement receipt must name the creation receipt; the Track S
   operator must only verify it. The proposal says "reviewed post-run procedure" but defines no
   artifact, reviewer, or receipt location, and no such procedure exists yet (F5).
2. **TASL-7 S0.1:** a new `tasl7_s01_digits_<date>.sh` (new `--out`, node `digits_mlp`, k=1, ports
   18101/18102) must be committed and independently reviewed; the existing `launch/tasl7_s01.sh`
   (sha256 `226dbfa2fd6ea1fc80bb97ed987da58bed38c854b72795ff06ff5826a430cbb7`) is hardcoded to
   `tabular_mlp`/`$OUT/tabular_mlp` and must not be reused. The S0.1 report (identity/latency, and
   the saved contents/server-log recomputation used on 9 Nov) must be independently reviewed before
   S0.5 starts. The proposal currently allows this review to be skipped (F2).
3. **S0.5/S0.5b launch scripts:** committed and independently reviewed before use — present in
   condition 5; PASS (no gap found).
4. **S0.5 report/result:** fresh review, then pause/report (L1) — present in condition 7; PASS.
5. **PLAN row:** author/Mac agent commits a dated row; operator does not. The draft is paste-ready but
   names no target branch (F7).

---

## Findings

### F1 — MAJOR (STOP-grade factual discrepancy): the TASL-2/TASL-7 Track S worker-venv difference is false

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:24-25` (host facts), `:43-45`
(condition 4), `:58` (PLAN row draft); `docs/r1/STATUS.md:7` (preconditions bullet).
**Issue:** The report says "**The TASL-2 Track S venv differed** (numpy 2.4.4 / sklearn 1.8.0 on the
B1-side check; the Track S venv on TASL-2 is frozen separately)" and builds condition 4/PLAN/STATUS on
a "worker-venv host difference". This is contradicted by the committed records: the two Track S venvs'
`pip_freeze.txt` is byte-identical (65 packages, sha256
`f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687`; `TRACKS_HOST_FACTS_20261030.md`
§0.5, "Only the patch level differs"), and TASL-2's frozen Track S venv on 9 Nov was Python 3.11.17,
**numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, pandas 3.1.0**
(`TRACKS_PHASE3_20261109.md:47`). The 2.4.4/1.8.0 numbers belong to the deepthought/noise-floor
harness-locked venv (`STATUS.md:665`, `NOISE_FLOOR_COMMON_20261022.md`), not TASL-2 Track S. The
S0.4 rerun on 11–12 Nov used the frozen venv untouched.
**Minimal fix:** Correct all four locations: the Track S venvs share the same third-party stack
(numpy 2.4.6, scipy 1.17.1, sklearn 1.9.1, pandas 3.1.0; `pip_freeze` sha `f1c818e5…`); only the
Python patch (3.11.17/3.11.18) and host hardware differ. Replace the "worker-venv difference"
disclosure with the real host differences (24 vs 32 CPUs, GPU UUID, per-host llama.cpp build,
TASL-2 clock not NTP-synchronised). If the B1/exam venv is intended, name it and say why it is
relevant — it is not the Track S worker venv.

### F2 — MAJOR: the TASL-7 S0.1 has no committed launch script and no independent review before S0.5

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:36-40` (condition 2) and `:70`
(open item "its result gates the S0.5 start").
**Issue:** Condition 2 only says "run the S0.1 … record the result in a report". It does not require
(a) a new committed TASL-7 launch script (runbook §0.1: every launch is a committed script; the
existing `launch/tasl7_s01.sh`, sha256 `226dbfa2…`, is hardcoded to `tabular_mlp`/`$OUT/tabular_mlp`
and would write into the wrong evidence tree), or (b) a fresh independent review of the S0.1 result
before S0.5 (runbook §0.8: review loop at every STOP; Phase 1 is STOP 1). As written, the operator
could run an uncommitted command, declare pass, and start S0.5 without a reviewer — the exact skip
the brief asks about.
**Minimal fix:** Add to condition 2: a new `tasl7_s01_digits_<date>.sh` with new `--out`, node
`digits_mlp`, k=1, ports 18101/18102, committed before use and independently reviewed; the S0.1
report must record hostname/driver/CPU/venv/pins, identity/latency, and the saved-contents or
server-log recomputation; a fresh independent reviewer must accept the S0.1 report before any S0.5
launch script is used. Failure or missing review = STOP (author).

### F3 — MAJOR: copy-back to `results/.../digits_mlp/s05/` collides with the preserved TASL-2 s05 scene

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:52-54` (condition 7).
**Issue:** The TASL-2 S0.5 attempt wrote `$OUT/digits_mlp/s05` (TASL-2 launch script
`r1/tracks/ops/launch/tasl2_s05_20261112.sh:16,73-74`); its natural Mac copy-back is
`results/r1/tracks/digits_mlp/s05/`. Condition 7 sends the TASL-7 `s05_t7_*` output to the same
`results/r1/tracks/digits_mlp/s05/`. That conflates/overwrites the preserved TASL-2 scene and
defeats the "preserved, never resumed" promise and the no-cross-host-comparability claim. The S0.4
rerun avoided this with a host-qualified Mac dir (`s04_rerun20261111` vs host `s04_r2_20261111`).
**Minimal fix:** Copy back to `results/r1/tracks/digits_mlp/s05_t7_20261113/` (mirror the host dir
name), with `SHA256SUMS` and a README naming host TASL-7 and the pins; keep `s05/` reserved for any
TASL-2 scene. Never write the moved run into `s05/`.

### F4 — MAJOR: condition 6 contradicts condition 1 on "Track X untouched" and leaves the Track X marker authority ambiguous

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:33-35` (condition 1) vs `:50-51`
(condition 6); `docs/r1/STATUS.md:7`; `:58` (PLAN row draft).
**Issue:** Condition 1 requires retiring B1 `_c`'s `~/r1_locks/trackx_evidence.active` — a Track X
scene change. Condition 6 says "**Nothing of Track X, Track P or the TASL-2 scenes is touched**", and
STATUS/PLAN repeat "Track X/Track P … untouched". The absolute wording is false under condition 1 and
does not say who may retire the Track X marker. Runbook §0.4/experiment-agent rules say never create
another track's marker and never touch what you did not start; the Track S operator must not retire
it. As written, an operator could read condition 6 as forbidding the very retirement condition 1
requires, or read condition 1 as authorizing the Track S operator to do a Track X action.
**Minimal fix:** Condition 6 becomes: "Nothing of Track X or Track P is touched **except the B1 `_c`
marker retirement required by condition 1, performed under the Track X post-run procedure, not by the
Track S operator**; the Track P marker is neither created nor retired; the TASL-2 scenes are
preserved." Update STATUS and the PLAN draft to match.

### F5 — MAJOR: the "reviewed post-run procedure" for the B1 `_c` marker is undefined and unwritten

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:33-35` (condition 1).
**Issue:** Condition 1 refers to "the reviewed post-run procedure" as if it exists. It does not: the
B1 `_c` handover (`b1_handover_4b31_20261112_c/`) contains the creation receipt
(`marker-receipt.json`, sha256 `f8c8624f…`) but no retirement receipt or procedure, and the B1
handoff `proposals/B1_RESTART_HANDOFF_C_20261111.md` §2.4 defines the `_b`→`_c` *transition*, not the
`_c` post-run retirement. The current marker is intact (content and receipt both `f8c8624f…`), but
the retirement procedure, its reviewer and its receipt location are unspecified. The gate cannot be
objectively evaluated and could be satisfied by an operator-written, self-reviewed note.
**Minimal fix:** Require the Track X/Mac agent to write the post-run retirement procedure (reuse
`b1_o2_marker.py retire`, keep the creation receipt, write a retirement receipt naming it, delete
nothing), a fresh independent reviewer to accept it, and record its path/sha256; absence = STOP. State
explicitly that the Track S operator only verifies it and does not perform it.

### F6 — MINOR: the only TASL-7 S0.1 is the Oct-30 STOP; the report's host-facts bullet reads as if a valid S0.1 exists

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:26-27`.
**Issue:** The Oct-30 TASL-7 S0.1 for `tabular_mlp` (`out/tabular_mlp/s01/`) was 0.870 serial / 0.875
cross-server and raised **STOP 1** (`TRACKS_PHASE1_20261030.md` §2–§3). The 9 Nov S0.1 rerun at
`cache_prompt:false` was `digits_mlp` on TASL-2 only (`TRACKS_S01_RERUN_20261109.md`); the TASL-7
`s01_rerun_INVALID_serial_raced_server_start_20261031T112132Z` is invalid. The 30 Oct diagnostic at
`cache_prompt:false` gave 1.000 on tabular, but that is a diagnostic, not a formal S0.1 pass. The
report should say no *valid* TASL-7 S0.1 at the current pin exists.
**Minimal fix:** Add the STOP (0.870/0.875), cite the D6 F2/30-Oct `cache_prompt:false` diagnostic if
it is the basis for expecting digits to pass, and say the digits S0.1 is the first valid TASL-7 S0.1.

### F7 — MINOR: the paste-ready PLAN row names no target branch; the operator branch's PLAN lacks the referenced rows

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:56-62` (§4).
**Issue:** The row refers to `R1-TRACKS-A2U-STALE` and the host-allocation rows, but on
`trackS-ops-20261030` `docs/r1/PLAN.md` contains neither `R1-TRACKS-A2U-STALE` (it is on
`origin/mac-tracks-a2u-stale-20261111` @ `c8b13b5d…`, row at PLAN line 615, commit `f82ff376`) nor
`R1-EXAM-HOST-B1B2-TASL7` (on `origin/docs/runbooks-11nov` @ `7cfbe7c9…`, line 964). "Until it is on
the branch" names no branch; the S0.4 rerun report explicitly recorded this location issue.
**Minimal fix:** Name the target: commit next to `R1-TRACKS-A2U-STALE` on the branch carrying it
(`mac-tracks-a2u-stale-20261111` or its merge successor), and note that the operator branch's PLAN is
not canonical.

### F8 — MINOR: "the pin branch" does not exist; the pin is reachable only via the a2u branch/object, and the TASL-7 refs were pushed after the record's verification time

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:41-42`.
**Issue:** The TASL-7 bare repo has `refs/heads/mac-tracks-a2u-stale-20261111 = c8b13b5d…` and the pin
object `8237fd02…` (ancestor), plus `trackS-ops-20261030 = 23a83b3b…`; there is no branch named for
the pin. The bare repo's refs were updated at `2026-11-12 14:49:25 -0800` = `22:49:25Z`, after the
report's `22:41Z` read-only verification and `22:47:52Z` commit, so the parenthetical "is pushed" was
not true at record time (it is true now). The work clone has no pin object locally (`git cat-file -t
8237fd02…` fails) and its `origin/trackS-ops-20261030` is stale `2906b67`; a fetch is required.
**Minimal fix:** Say "the a2u branch (tip `c8b13b5d…`) carrying pin `8237fd02…` is in the TASL-7 bare
repo; `git fetch origin mac-tracks-a2u-stale-20261111`, verify
`git merge-base --is-ancestor 8237fd02 c8b13b5d`, then checkout `8237fd02` detached." Do not say "the
pin branch".

### F9 — MINOR: the conditions do not restate the Phase 4 calibration gate and §10 STOPs

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:31-54` (conditions 1–7).
**Issue:** The conditions say "the same rev-3.3 Phase 4 command" but do not restate the Phase 4
calibration gate (coverage in [0.70,0.90], λ₂ branch, second failure = STOP), the 2 % exhausted rule,
exit 3 twice, fork-rebuild/A-A mismatch, or the §10 5-day GPU-time cap. The 5-day cap matters because
TASL-7's Track S GPU time is shared with `tabular_mlp` and with B1.
**Minimal fix:** Add "all rev-3.3 Phase 4 and §10 STOPs apply unchanged on TASL-7; GPU time is counted
per host across nodes; any STOP waits for the author."

### F10 — MINOR: the decision quotation is not verbatim ("migrate" vs "move")

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:3-5`; `docs/r1/STATUS.md:6`.
**Issue:** The report quotes "migrate `digits_mlp` to TASL-7 and run it after the B1 `_c` run ends";
the brief/STATUS say "move". Substance is identical, but quote marks imply verbatim. The report does
say "quoted only as the decision", which signals compression.
**Minimal fix:** Quote verbatim or write "in substance: move …"; align the STATUS/report wording.

### F11 — MINOR: no condition for TASL-2 returning after the TASL-7 S0.5 starts

**Location:** `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md:66-68` (§5 open items).
**Issue:** The open item covers a TASL-2 return *before B1 `_c` ends* and says "if both exist, the
TASL-2 scene is kept as a stopped observation only". It does not say what to do if TASL-2 returns
*after* the TASL-7 S0.5 has started, when the TASL-2 collector might still be running. Two S0.5 runs
of the same node could then proceed, and the "preserved" scene could be modified.
**Minimal fix:** Add: if TASL-2 returns after the TASL-7 run starts, read-only capture only, do not
resume or write, do not signal a process not started by us, and STOP to the author before any TASL-2
action; the TASL-2 scene is a stopped observation.

### F12 — MINOR: STATUS says "authorised" while the PLAN row is a pending draft

**Location:** `docs/r1/STATUS.md:3,7`.
**Issue:** The heading "host move to TASL-7 authorised" and "Preconditions before the moved run"
read as if the runbook §1 "decision = dated PLAN row" step is complete; the report says the row is
paste-ready and "until it is on the branch, this proposal only records the decision". No work depends
yet, so this is not self-authorization, but the wording is stronger than the record.
**Minimal fix:** Use "author decision recorded; PLAN row pending" in the STATUS heading/bullet, and
keep "no Track S run is started now".

---

## Residual notes (not findings)

- The TASL-2 S0.5 attempt's `19:55:59Z` start and "4 committed roots (20:02Z)" are operator-reported;
  no TASL-2 capture is committed (host down). The figures are not load-bearing for the move, but a
  "last-seen" capture reference would make the STOP record stronger.
- The TASL-7 `trks_watch` is alive (pid 1388760) but `watch.log` has been in the "priority marker
  seen" state since `2026-11-08T00:46:56Z`; after B1 `_c` marker retirement it should log "marker
  gone" and resume. No action; note for the post-B1 check.
- `$OUT/smoke/STOP` exists from the 8 Nov pause; the digits run uses new dirs and the watcher's
  touch loop only targets `manifest.json` dirs, so it is not a blocker. Do not delete it as part of
  the digits move.
- The TASL-7 `work/Agent_paper_B` clone must fetch the a2u branch before checking out `8237fd02`
  (F8); the pin object is in the bare repo, not in the clone.
- The report's §2 line "no `digits_mlp` S0.1 exists on TASL-7" is true for host-local `$OUT`, but the
  checkout contains the TASL-2 digits S0.1; phrase it as "no TASL-7-hosted digits S0.1".
- The TASL-7 disk (529 G free) and RAM (62 G, 49 G available) are adequate; the report does not state
  them, no contradiction.
- The 24-vs-32-CPU difference is stated but its projection/runtime consequence is not; the S0.1
  latency and 8 h deadline/resume are the safeguards.

---

**Conclusion.** The author-decision recording is governance-correct: it records a real, dated author
decision, does not self-authorize, does not pretend to be a PLAN row, and leaves the row as a
paste-ready draft. The live TASL-7 host facts check out. The conditions are not yet safe to rely on
as written: one STOP-grade factual error (the Track S venv difference), a missing independent review
path for the TASL-7 S0.1 (and no committed S0.1 launch script), a copy-back path that collides with
the preserved TASL-2 scene, an internal contradiction about touching Track X, an undefined post-run
marker-retirement procedure, and several minor precision/STOP-list gaps. These are correctable in the
record without touching any host or starting any run.

VERDICT: changes required
