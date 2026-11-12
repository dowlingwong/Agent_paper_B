# Independent re-review — Track S `digits_mlp` host-move record, rev 2 (13 Nov 2026)

**Reviewer:** fresh independent reviewer; did not write the record; no writes under
`/Users/wongdowling/Documents/agent_paper_B` and no TASL-2 contact. Read-only checks on TASL-7 only.

## Unit reviewed

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`,
  commit **`5d663f8d834784c75d2e819e0cfed5ee2fda882c`** (parent
  **`23a83b3b3a31394c9d66fe07db16257509d9a44f`**, the rev-1 record).
- Diff `23a83b3b 5d663f8d` touches only two files: `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md`
  (rev 2, +80/−50) and `docs/r1/STATUS.md` (+3/−3). No other change.
- Rev 2 is also present on the TASL-7 bare repo (`remotes/Agent_paper_B.git`, ref
  `refs/heads/trackS-ops-20261030 = 5d663f8d…`).

## Round-1 findings — status against the diff

| # | Status | Evidence in rev 2 |
|---|---|---|
| F1 | **Resolved** | §2 (lines 26–31) now states both Track S venvs are the same 65-package `pip_freeze` (sha256 `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687`; numpy 2.4.6, scipy 1.17.1, sklearn 1.9.1, pandas 3.1.0), only Python 3.11.17 vs 3.11.18 differs, and the 2.4.4/1.8.0 values are a different (exam-x harness-locked) venv. Grep finds no residual "differed"/"worker-venv difference" wording in §2, condition 4, the PLAN row or STATUS. Condition 2's S0.1 bounds the patch difference. Read-only TASL-7: `venv` Python 3.11.18 / numpy 2.4.6 / scipy 1.17.1 / sklearn 1.9.1 / pandas 3.1.0; freeze sha and 65-package count match; exam-x venv (`/home/dowling/exam-x/work/venv`, Python 3.13.4) is 2.4.4/1.8.0, corroborating the attribution. |
| F2 | **Resolved** | Condition 2 (lines 46–50) makes the **new `digits_mlp` S0.1 launch script** explicit (existing `launch/tasl7_s01.sh` is `tabular_mlp`-hardcoded; sha256 `226dbfa2fd6ea1fc80bb97ed987da58bed38c854b72795ff06ff5826a430cbb7` verified), with `--node digits_mlp`, `--out $OUT/digits_mlp/s01_t7_20261113`, committed before use, and **the S0.1 result independently reviewed before S0.5**. Failure = STOP. Residual: the script itself is not explicitly required to be independently reviewed (see notes). |
| F3 | **Resolved** | Condition 5 uses `$OUT/digits_mlp/s05_t7_20261113` and `$WORK/digits_mlp/s05_t7_20261113`; condition 7 copies back to `results/r1/tracks/digits_mlp/s05_t7_20261113/` "not the preserved TASL-2 path". `s05` remains reserved for the TASL-2 scene (TASL-2 script `r1/tracks/ops/launch/tasl2_s05_20261112.sh` does write `$OUT/s05`). |
| F4 | **Resolved** | Condition 6 (lines 63–65) is now "no Track X change other than the separately reviewed post-run marker retirement in condition 1, performed under the B1 procedure"; STATUS says "Track X untouched apart from the reviewed marker retirement". No contradiction with condition 1. Residual: the PLAN row still says simply "Track X untouched". |
| F5 | **Resolved** | New §5 (lines 86–94): a **separate** unit, written + independently reviewed + executed by the **B1/Track X operator** (not Track S); creation receipt `f8c8624f…` named; rename into `~/r1_locks/_to_delete/`, receipts kept, nothing deleted, retirement receipt in the `_c` handover directory, watcher verification. Read-only TASL-7: `b1_handover_4b31_20261112_c/marker-receipt.json` = sha256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, equal to the live marker's sha256; the handover's `marker-retirement.json` is for `_b` (`fffa_20261111_b`), confirming no `_c` retirement exists. |
| F6 | **Resolved** | §2 (lines 32–34) states the Oct-30 `tabular_mlp` S0.1 (serial 0.870 / cross 0.875 STOP) and the `cache_prompt:false` diagnostic 1.000, and that **no valid `digits_mlp` S0.1 exists on TASL-7 at the current pin**; the required one is new. Read-only `out/` holds only `smoke/` and `tabular_mlp/`; numbers match `s01/serial.json` and `s01/concurrent.json`. |
| F7 | **Resolved** | §4 (line 76) names the target branch `trackS-ops-20261030`; the operator note records `R1-TRACKS-A2U-STALE` on `mac-tracks-a2u-stale-20261111` (`f82ff376`, PLAN line 615 verified) and `R1-EXAM-HOST-B1B2-TASL7` on `docs/runbooks-11nov` (PLAN line 964 verified). |
| F8 | **Resolved** | Condition 3 (lines 51–53) names the branch `mac-tracks-a2u-stale-20261111`, the detached/clean checkout, fetch-before-detach, pin on that branch's history, and "no separate 'pin branch'". §2 corrects the clone state. Read-only TASL-7: bare `mac-tracks-a2u-stale-20261111 = c8b13b5d…`, `8237fd02` is an ancestor; work clone is detached `d10b05b7`, clean, has no `8237fd02` object and no a2u remote branch, so "fetch and detach" is required and correctly stated. |
| F9 | **Resolved** | Condition 7 (lines 66–71) restates the calibration gate + λ₂ revision rule (second failure = STOP; coverage-too-high/stratum-0 STOP), the 2 % failed-units rule, exit 3 twice, A/A or fork-rebuild mismatch, and the §10 5-day-GPU cap, all as STOPs; matches runbook rev 3.3 Phase 4 and §10 (docs commit `13badb0`, sha256 `a93fb84b…`). |
| F10 | **Resolved** | Lines 3–5: "the author chose the option …" with "recorded by the Lead; … no sentence is quoted as verbatim"; no fake verbatim quote. |
| F11 | **Resolved** | Condition 8 (lines 72–74): if TASL-2 returns after the TASL-7 S0.5 starts, read-only census, keep both scenes, no host switch/resume, report and let the author decide; scene never resumed or deleted. |
| F12 | **Resolved** | STATUS heading is "**chosen**", bullet is "Author decision (recorded)", the PLAN row remains a paste-ready draft, and the operator note still says the operator does not add author decisions to PLAN unilaterally. |

## "Also verify" checks

1. **Host facts / no new factual inaccuracies — PASS.** Read-only on TASL-7: hostname TASL-7;
   1 × RTX 4090, driver 580.178.04, 24 CPUs; `work/Agent_paper_B` at `d10b05b7…` detached and clean;
   `work/autoresearch_harness` at `a3fedbb…` clean; llama.cpp `620d2225…` (llama-server
   `v0.7.0-dev`, build 11669); GGUF sha256
   `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; venv 3.11.18 / numpy 2.4.6 /
   scipy 1.17.1 / sklearn 1.9.1 / pandas 3.1.0; bare refs `trackS-ops-20261030` (now `5d663f8d`) and
   `mac-tracks-a2u-stale-20261111` (`c8b13b5d`, contains `8237fd02`); B1 `_c` alive
   (`tmux b1_4b31_20261112_c`, `exam_runner b1`), marker sha256 `f8c8624f…`, `gpu0.lock` held by B1
   processes; Track P marker absent. The TASL-2-only figures (unreachability, 19:55:59Z start, 4 roots
   at 20:02Z) cannot be re-verified while TASL-2 is down and were not touched; round 1 already noted
   them as operator-reported and non-load-bearing.
2. **Non-executing / preservation / authority — PASS.** The record says "not yet executed" and "starts
   nothing by itself"; STATUS says "no Track S run is started now". TASL-7 has no `out/digits_mlp`,
   no `s01_t7`/`s05_t7` dirs and no Track S s01/s05 tmux session; the work clone is still at
   `d10b05b7`, not the pin. TASL-2 was not contacted. The PLAN row is explicitly a paste-ready draft;
   the operator note is intact.
3. **Diff scope — PASS.** `git diff --name-status 23a83b3b 5d663f8d` lists only `docs/r1/STATUS.md`
   (M) and `docs/r1/reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` (M); no other file, no mode change.

## Residual notes (not findings — no change required)

- §2 line 32 says "TASL-7's only Track S S0.1 history is the Oct-30 `tabular_mlp` run …"; `out/` also
  contains an explicitly invalid 31 Oct tabular rerun
  (`s01_rerun_INVALID_serial_raced_server_start_20261031T112132Z`) and the diagnostic sub-runs
  `s01_diag_f1`/`s01_diag_f2`. The next sentence already says "no **valid** `digits_mlp` S0.1"; adding
  "valid" to the first sentence would make the exhaustiveness exact.
- Condition 1 quotes the marker only as `{"run_id":"4b31_20261112_c"}`; the live file also carries
  `"head": "4b312844962e…"`. The quoted fragment is a correct identifying subset.
- §2's "these refs were pushed at 22:49Z" is the initial push (bare ref mtimes 2026-11-12 14:49:25
  −0800 = 22:49:25Z); the `trackS-ops-20261030` ref was then advanced to this commit at
  15:01:48 −0800 = 23:01:48Z. Both true, but the sentence should not be read as the current ref.
- Condition 2 requires the S0.1 result to be independently reviewed, but not the S0.1 launch script
  itself (unlike the S0.5/S0.5b scripts in condition 5); round 1's F2 minimal fix also suggested
  recording the saved-contents/server-log recomputation. The result review is the operative gate.
- The PLAN row's "Track X untouched" could mirror condition 6's "apart from the reviewed marker
  retirement".
- Condition 1's "B1 `_c` ended normally" is a precondition written in the past tense; the following
  "until then Track S waits" removes any execution ambiguity.

## Verdict

The rev-2 record corrects the F1 false venv claim everywhere, makes the new S0.1 script and its
independent review explicit, removes the copy-back collision, converts the Track X marker retirement
into a separate B1/Track X-owned reviewed unit, restates the Phase 4/§10 gates, and fixes the decision
and STATUS wording. The unit remains non-executing and the TASL-2 scene is preserved by condition.
The residual notes are precision items only.

VERDICT: accepted
