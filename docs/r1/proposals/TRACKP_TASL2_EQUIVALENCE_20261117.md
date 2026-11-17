# Unit (revision 3) — Track P host-equivalence check on TASL-2, literal TASL-7-style (ENGINEERING; 17 Nov 2026)

**Status: proposal for fresh independent review; not executed.** Revision 2 answers the round-1 review
(`reviews/TRACKP_TASL2_EQUIVALENCE_REVIEW_20261117.md`, sha `c14cbb39…`, NOT ACCEPTED: running code D at
the e0 final budget would not reproduce the pre-declared 2,000-step/patience-5 configuration and D's e0
path changed after the reference; the env lacked bytecode/index protection; no preflight). It therefore
runs the **literal** check with the **reference code `8e13e77` + harness `897d83c`**, exactly as
`docs/r1/reports/tasl7_equivalence_20261026/driver.sh` did on TASL-7. Authority: `R1-TRACKP-TASL2-HOST`
(`author-decisions-20261117b` @ `45fb94cc`) — the host-equivalence check that `R1-TASL7-TRACKP` required for
TASL-7, once, on TASL-2; `R1-TASL2-REHEARSAL-SCOPE` passed. ENGINEERING, not evidence, not counted; this is the **host/reference-code reproducibility** check, not a
test of D (D delivery and Unit B are separate). **TASL-2 is the portal host**, so a pass is a same-host
reference reproduction (the only variable is the host/environment state), not a cross-host equivalence
claim with TASL-7.

## 1. Pre-declaration (fixed before the run; unchanged from `tasl7_equivalence_20261026/PREDECLARATION.md`)

Reference: portal E0 v2 DRYRUN selected run `kev-0.8b / fresh_soft_lr0.0001`
(`docs/r1/reports/trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/report.json`, sha
`7c1be5e9…`). Metrics `lora.test`; all three must hold:

| Metric | Portal value | Tolerance |
|---|---|---|
| `width_slope_vs_label` | 0.922998 | abs Δ ≤ 0.05 |
| `mean_slope` | 1.011556 | abs Δ ≤ 0.05 |
| `rps` | 1.98913e-4 | relative ≤ 10 % |

A miss on any is a **STOP for the author** (no re-run to pass; no substitution). Descriptive fields are
reported, not judged; the comparison uses the committed `compare.py` (exit 0 equivalent, 1 miss).

## 2. Reference code/environment (exact literal reproduction)

- Clean worktree at **`8e13e77`** (`paper 8e13e77`, detached) under
  `…/unitb_rehearsal_20261117/Agent_paper_B_8e13e77`; harness worktree at **`897d83c`** under
  `…/unitb_rehearsal_20261117/autoresearch_harness_897d83c`; both created by the operator and verified
  clean; `AR_HARNESS_ROOT` points at the harness worktree.
- Frozen venv `/home/dowling/r1_trackp/venvs/trackp-gpu` (freeze 121 lines sha `50238e5a…`, torch
  2.6.0+cu124); config at `8e13e77` (loaded digest **`588869fa…`**, the portal reference/TASL-7
  `config_sha256`); base/adapter local paths as in that config; models present.
- Command (exactly the TASL-7 driver form; 2,000-step cap/patience 5 from the reference config):
  `python r1/scripts/trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001
   --run-dir <scratch>/kev-0.8b/fresh_soft_lr0.0001`
- Scratch root `…/unitb_rehearsal_20261117/ENGINEERING_equivalence_<UTC>` (`%Y%m%dT%H%M%SZ`, must not
  exist; never an attempt-2 root; never counted). Env:
  `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=…`
  with the frozen venv; ordinary GPU lease.

## 3. Procedure

1. **Before (preflight/pins):** exact scratch root absent; parent listing (it holds the D worktree, the
   rehearsal scratch and four pre-existing files; include them); `8e13e77` worktree HEAD/clean,
   `r1/scripts/trackp.py`/`run.py`/`exam_run.py`/config file shas and loaded config digest `588869fa…`;
   `897d83c` harness HEAD/clean; freeze 121 lines `50238e5a…`; the two model dirs; GPU/driver/UUID idle;
   no compute app; `flock -n` free; no `*.active`/marker helper (the reference code's Track X marker gate must be clear; it is checked at
   run time); disk ≥50 GB; lease-log count/sha
   (**191 lines / `0a4a14ae…`** at acceptance) with expected after-state **193 / two added lines**
   (`start`/`end`; the reference code `8e13e77` has no `acquired` event — that was added by `08aeaff9`);
   `git ls-remote origin main` (remote = local `26177d82…`), both FETCH_HEAD files: the main clone `.git/FETCH_HEAD` (17,593 B sha `69545606…`; expected unchanged) and
   the worktree gitdir `…/.git/worktrees/Agent_paper_B_8e13e77/FETCH_HEAD` (absent now; expected created,
   104 B sha `83c64a87…`; no ref move/object download — a ref move is a STOP; record both before/after);
   tracked-file SHA list; `.pyc` count in the `8e13e77` worktree (**65**; 72 is D's); linked-worktree
   index sha; `git worktree list`; the parent listing now includes the two new worktrees; `compare.py` at `docs/r1/reports/tasl7_equivalence_20261026/compare.py` (copy into scratch or run from the
   worktree; check its schema/exit on the reference report before the run);
2. **Run** the §2 command once from the `8e13e77` worktree with the absolute frozen-venv path; measure
   wall time; capture stdout/stderr.
3. **After:** repeat the baselines; require rc 0; report/manifest exist with sha256; report
   `max_steps`=2000/patience=5 as in the reference config (this code vintage has no `stage` key); lease log
   gained exactly **two** lines (`start`/`end`; no `acquired`); the worktree gitdir `FETCH_HEAD` is
   created/rewritten only (104 B `83c64a87…`), the main clone `.git/FETCH_HEAD` (17,593 B `69545606…`) is
   untouched; `manifest.host` is absent — record GPU/driver/UUID from `nvidia-smi`; no tracked-file/`.pyc`/
   worktree changes; no marker/evidence; lease released; GPU back to idle; wall time recorded (expected
   ≈25 min).
4. **Compare:** the `8e13e77` worktree has neither `compare.py` nor the reference report; copy the committed
   `compare.py` (from D/Mac; sha `bd957c0d…`, verify identical) and the portal reference report (sha
   `7c1be5e9…`) into the scratch, then `python <scratch>/compare.py <scratch>/reference_report.json
   <TASL-2 report> > comparison.json`; require `equivalent: true` and all three criteria pass; record the
   comparison JSON and descriptive fields. Check the comparator's schema/exit on the reference before the run.
5. Record `TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md` with: command/argv/env, both worktree HEADs and
   file shas, config/digests, freeze, host/GPU/driver/UUID, lease-log before/after + **two** lines (191→193; no `acquired`),
   both FETCH_HEAD files before/after (main clone 17,593 B/`69545606…` unchanged; worktree gitdir absent →
   104 B/`83c64a87…`), tracked/pyc/index/worktree/nvidia-smi
   baselines (`.pyc` 65 in this worktree), report/manifest shas,
   wall time, full comparison JSON, and the explicit statements that this is ENGINEERING, that TASL-2 is
   the portal host (same-host reference reproduction), and that the table host will be disclosed if Unit B
   runs there. A comparison miss: STOP, preserve, report; no re-run.

## 4. STOPs

Comparison miss; rc!=0 or missing report; `8e13e77`/`897d83c` HEAD/dirty mismatch; config digest ≠
`588869fa…`; freeze/model mismatch; lease not acquired/released; OOM/CPU fallback; ref move/object download
from the lease gate; any tracked/untracked/`.pyc`/worktree change outside the recorded lease/fetch side
effects; disk <50 GB; any protocol/authority change needed. Preserve and report; no re-run.

## 5. Must not

No attempt-2/evidence root or label; no TASL-7 action; no code/config/rule changes; no other host; no
deletion; no main/exam-x push; no other user's files/processes.
