# Review R1 — Track P host-equivalence check on TASL-2 (ENGINEERING; 17 November 2026)

**Status: NOT ACCEPTED — 2 BLOCKING, 2 MAJOR, 9 MINOR.** The authority, the scope (ENGINEERING, once,
not counted), the pre-declared reference values, the tolerance and the comparator are all correct and
byte-verified. The command as written, however, does **not** run the pre-declared configuration: under
delivered code **D** the default `e0` stage is the R1-E0-BUDGET *final* budget (6,000 steps, patience 10),
not the pre-declaration's 2,000-step / patience-5 schedule, and D's e0 path also changed the LoRA start
state (the portal reference trained LoRA from the *fitted* head; D restores the *fresh* head first). The
unit's claim at lines 35–38 that D "differs only in the reviewed P.3a/A3-short changes" is therefore
false, and the comparison as written is not the pre-declared host-equivalence reproduction. Two further
MAJORs: the env omits `PYTHONDONTWRITEBYTECODE=1`/`GIT_OPTIONAL_LOCKS=0`, so the run would by construction
violate §3.3/§4's "no `.pyc`/worktree changes"; and there is no "Before" preflight/pin step, so the
"config/model/freeze mismatch" STOP and every before/after claim are not checkable. **The unit may not be
executed as written.** Review only: the unit was not executed (not even partially), no host write, no
commit/push, no GPU command; read-only SSH to TASL-2 (`ssh portal_zhixu`, user `dowling`) was used for the
host facts. The only workspace change made by this review is this uncommitted review file.

## 0. Canonical bytes, authority and method

| Object | sha256 / lines | Where / state |
|---|---|---|
| **Unit under review** | `c0912349d275a6d7b942ca28558e85a3528f0883815c4dd8f3bf8acc35ea9129`, **63 lines** | `docs/r1/proposals/TRACKP_TASL2_EQUIVALENCE_20261117.md`, worktree `ops-tasl-20261116`; **uncommitted-untracked** (`??`) — matches the canonical value given |
| Authority `R1-TRACKP-TASL2-HOST` | commit `45fb94cc` (17 Nov 2026, 02:41 +0100) on branch `author-decisions-20261117b` (remote; **not** on `origin/main` `26177d82…`) | `docs/r1/PLAN.md` row; read from the local git object |
| `R1-TASL2-REHEARSAL-SCOPE` | `33c82351` (same branch) | same row family |
| `R1-TRACKP-UNITB` | `16185b0b` (main) | PLAN row |
| Rehearsal result (passed) | `ec98fb18c7c630cbec4baacb8f3c6f374db5160d71f3e75c4007c16fa7bf62a9`, 44 lines | `docs/r1/reports/TASL2_UNITB_REHEARSAL_RESULT_20261117.md` |
| Pre-declaration | `4ed7ef92816c6160c0e144b249bd39c309f8ddd0faa1693e32aeceb7848fd726`, 33 lines | `docs/r1/reports/tasl7_equivalence_20261026/PREDECLARATION.md` |
| Comparator | `bd957c0d3e984b4ec9e27ef090d29580654cfef91d73174bf05a615cd4bf6084`, 37 lines | `docs/r1/reports/tasl7_equivalence_20261026/compare.py` (committed, unmodified) |
| TASL-7 comparison (precedent) | `0793eddba25b675f49a40ec5670dfb9550e2f1b362b3167ff09a92e01c505b76`, 117 lines; `equivalent: true` | `…/comparison.json` |
| Portal reference report | `7c1be5e98fc896074aae33ec301263c3b02973c02a1c387130eb3f45c21d41e0` | `docs/r1/reports/trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/report.json`; byte-identical in the `b9ad6f8f` tree (verified `git show b9ad6f8f:… \| sha256sum`) |
| Delivered code **D** | `8662e35991659f7a661fb7ed6be4980791d302f3` (detached), clean | TASL-2 `…/unitb_rehearsal_20261117/Agent_paper_B_D_20261117` |

Method: local read of the canonical, authority, pre-declaration, comparator and reference bytes, plus
`git show`/`git diff`/`git merge-base` on the local repository object store at `8e13e77`, `471f93f7`,
`52b527b9` and `8662e359`; read-only SSH to TASL-2 on **2026-11-17, 01:50–01:56Z** (`date`, `uname`,
`sha256sum`, `wc -l`, `ls`, `find`, `df`, `nvidia-smi` queries, `git --no-optional-locks` reads,
`git ls-remote`, one read-only `flock -n` probe, and one stdlib/version read). No unit child, no training
code, no GPU command, no `compare.py` execution, no commit/push. Integrity note: the single transient
host artifact was a `/tmp` file used for one failed `uv pip freeze` probe and removed inside the same
command; it touched no repository, venv, lease-log, git-ref, scratch-root or GPU state. A re-check
(`find … -newermt 01:40Z`) shows no `.pyc` written and no repo change after the pre-review baseline.

## 1. Authority and scope — correct

1. **The authority is quoted correctly.** `R1-TRACKP-TASL2-HOST` (commit `45fb94cc`): Track P evidence
   tables may be produced on TASL-2 or TASL-7 (both RTX 4090), one host per table with the host disclosed;
   if the TASL-2 rehearsal passes and TASL-7 is still unreachable, Unit B runs on TASL-2 after the
   R1-TASL7-TRACKP host-equivalence check is done **once on TASL-2 (ENGINEERING)**; the scratch is never
   counted. Lines 3–8 and 60–63 implement exactly that; the rehearsal did pass
   (`TASL2_UNITB_REHEARSAL_RESULT_20261117.md`: "RESULT: PASSED"), and TASL-7 is still unreachable
   (verified: `ssh tasl7` to `100.106.74.51:22` timed out at ~01:50Z).
2. **ENGINEERING / not evidence / not counted / never attempt-2** is stated in lines 3–8, 35 and 62.
3. **One job, no re-run** is stated in lines 22, 48, 58. **Table-host disclosure** is stated in lines
   51–52. **No TASL-7 action / no marker / no evidence root** is stated in lines 47–48 and 62. All match
   the authority.
4. **Scope caveat (MINOR-8):** the closing context "then deliver D and run Unit B on TASL-2" remains
   blocked on a separate real gap recorded by the rehearsal: Unit B's `--load` targets attempt-1
   `EVIDENCE/kev-0.8b/final/saved`, a TASL-7 artifact absent on TASL-2. This unit does not resolve it; an
   equivalence pass must not be read as Unit B readiness.

## 2. Command / environment — the central defects

**Verified correct** (read-only): D worktree `…/unitb_rehearsal_20261117/Agent_paper_B_D_20261117` is
detached at `8662e35991659f7a661fb7ed6be4980791d302f3`, `git status --porcelain --untracked-files=all`
empty, `git worktree list` = main `b5a7aeca` + D only; D entry point `r1/scripts/trackp.py`
`d2a30ec2c1b4…`, `r1/c3/train/run.py` `797f00d5ace5…`, `r1/c3/train/exam_run.py` `f0f1ce94f0da…`, config
`r1/scripts/configs/trackp_portal.json` `049bafede821…` (loaded-config digest `64073cea…`); frozen venv
`/home/dowling/r1_trackp/venvs/trackp-gpu` = Python 3.12.15 / torch 2.6.0+cu124, freeze **121 lines sha
`50238e5a07ca…`** (byte-identical to committed `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`;
independently re-listed as 121 distributions with the same pins); kev-0.8b base/adapter local paths present;
the command form `python -m r1.scripts.trackp e0 …` and the flags are valid; the run-dir path is under the
named, non-attempt-2 scratch root; and the comparator invocation order is correct (portal report first).
However:

- **BLOCKING-1 — the command runs the wrong budget.** Under D, `cmd_e0` selects the budget by
  `bud = e0c[args.stage]`, `--stage` defaults to **final** (`r1/scripts/trackp.py` at `8662e359`,
  `cmd_e0`/argparse), and D's config gives `e0.final = {max_steps: 6000, eval_every: 100, patience: 10}`
  versus the reference `e0 = {max_steps: 2000, eval_every: 100, patience: 5}` (raw config at `8e13e77`,
  loaded-config digest `588869fa…`, exactly the `config_sha256` of the portal reference and TASL-7
  manifests). Line 32's command passes no `--steps`, so it will run **6,000 steps with patience 10** —
  not the "same base, lr, seed, **step budget**" that the host-change header (migration step 3, the rule
  R1-TASL7-TRACKP makes applicable here) and the pre-declaration fix. The TASL-7 check reproduced 2,000
  steps. **Fix:** add `--steps 2000` to the command (keep the default `--stage final`, so the
  `head_fit` block that `compare.py` requires is still produced; do **not** pass `--stage screen` — that
  drops `head_fit` and makes `compare.py` raise `KeyError`/exit 1); record `report.max_steps == 2000`,
  `report.stage == "final"`, `report.patience == 10`, `report.budget_override == {"steps": 2000,
  "eval_every": null}`; correct the "~25 min" estimate (it is the 2,000-step figure; the TASL-7 run took
  25.4 min) and record the actual wall time.
- **BLOCKING-2 — the claim that D's e0 path is unchanged is false, so the pre-declared comparison does
  not test what it claims.** Lines 35–38 say D "differs only in the reviewed P.3a/A3-short changes".
  Between the reference code `8e13e77` and D `8662e359`, the e0 path also changed:
  (a) **R1-E0-BUDGET** — config `screen`/`final` split (digest `64073cea…` ≠ reference `588869fa…`);
  (b) **R1-E0-HEADFIT** — the descriptive head fit is full-batch CPU L-BFGS (`fit_head_lbfgs`) instead of
  the reference's AdamW `fit_head_on_states`, so `head_fit.best_step/stopped_at/early_stopped` will be
  `null` for the D run (descriptive only — `compare.py` uses `.get()`, so this is survivable but must be
  recorded);
  (c) **the LoRA start state** — commit `52b527b9` ("head fit stays descriptive (LoRA starts from the
  fresh head)") added `model.heads["belief"].load_state_dict(fresh_head)` before the LoRA stage, whereas
  the reference run (`8e13e77`, commits `471f93f7`/`52b527b9` are both later: 26 Oct 14:46/15:55 −0700,
  after the reference ran 26 Oct 10:57–11:22Z) trained LoRA **from the fitted head**. Consequence: even
  with `--steps 2000`, the D LoRA trajectory is a different training run from the reference's, and
  patience 10 (D's final budget) cannot be reduced to the pre-declared 5 without editing the config,
  which §5 forbids. A pass would therefore show "D at the 2,000-step cap on the portal host is within the
  old tolerance", not the pre-declared host-equivalence reproduction; a miss would be ambiguous
  (code-vintage vs host). This matters especially because **TASL-2 is the portal host that produced the
  reference** (RUNBOOK host table "zhixu portal (TASL-2)"; the reference manifest's env paths are this
  host's `…/r1_trackp/venvs/trackp-gpu`; driver 535.309.01; TASL-7 report labels it "Portal (TASL-2,
  driver 535)"), so "host equivalence" here is trivially same-host and the only real variable is code
  vintage. **Fix (before execution; pre-declared, not discovered after):** replace lines 35–38 with an
  accurate statement — D carries R1-E0-BUDGET + R1-E0-HEADFIT + the P.3a/A3-short changes; the run uses
  the pre-declared 2,000-step cap and D's final-stage patience 10; LoRA starts from the fresh head
  (reference: fitted head); the reference values/tolerance are unchanged and `equivalent: true` is
  required with a miss a STOP for the author and no re-run; the comparison record states both config
  digests (`64073cea…` vs `588869fa…`) and the LoRA-start/head-fit deltas; and the unit states that this
  is a same-host **D-code reproducibility** check of the portal reference, not a cross-host check. If the
  author instead wants the literal TASL-7-style check, run the reference code `8e13e77` (config digest
  `588869fa…`) in a clean TASL-2 worktree exactly as `tasl7_equivalence_20261026/driver.sh` did — this
  needs an explicit authority/scope note because it would not test D.
- **MAJOR-1 — the env omits the two variables the accepted rehearsal used to keep the tree clean.** Line
  30 sets only `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 PYTHONPATH=.`; the
  accepted TASL-2 rehearsal ran with `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1`.
  As written, importing `r1.*` from the D worktree writes new `.pyc` under `r1/`, and read-only git
  commands can refresh the linked-worktree index, so §3.3/§4's "no `.pyc`/worktree changes" would be
  violated by construction (current baseline: 72 `.pyc`; linked-worktree index sha
  `855fec7579f9…`). **Fix:** add `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0` to the env and record
  them with the `.pyc`/tracked-file/index baselines.
- **MAJOR-2 — there is no "Before" step and no pins.** §3 only defines after-the-fact checks
  ("record sha256s; wall time; lease log before/after…"), but no preflight, so "config/model/freeze
  mismatch" (line 38/56) and every before/after comparison are uncheckable. **Fix:** add a "Before" step
  (mirror the accepted rehearsal unit §3.2) capturing at least: exact scratch root
  `…/unitb_rehearsal_20261117/ENGINEERING_equivalence_<UTC>` (must not exist; the parent also holds the
  D worktree, the rehearsal scratch and four pre-existing files — include them in the baseline); D HEAD
  `8662e359916…` + `git status --porcelain -uall` empty; D file shas (`trackp.py d2a30ec2`,
  `run.py 797f00d5`, `exam_run.py f0f1ce94`, config `049bafed`/digest `64073cea`, `trackp_p3a_guarded.py
  c045475b`); freeze 121 lines `50238e5a`; the two model dirs; GPU/driver/UUID idle; lock free (`flock
  -n`); no `.active` and no marker helper; disk ≥50 GB (today 374 G); lease log count/sha (**191 lines
  sha `0a4a14ae…`** today, so the expected after-state is 194 lines / three added `acquired`/`start`/`end`
  lines); `git ls-remote origin main` and the `FETCH_HEAD`/ref state (today remote main = local
  `origin/main` = `26177d82…`, `FETCH_HEAD` exists, 104 B sha `83c64a87…` — so the expected lease-gate
  side effect is a `FETCH_HEAD` rewrite only, not a ref move; a ref move or object download is a real
  change to record); tracked-file hash list and `.pyc` inventory; no `p3a_attempt2*` or
  `ENGINEERING_equivalence*` root. Then define the STOP as a mismatch **from these recorded D facts**, not
  from the reference `588869fa`/`8e13e77` — as written, the D manifest's `config_sha256` will be
  `64073cea…`, which a literal reading of "config mismatch is a STOP" would flag even when everything is
  intended.

## 3. Expected result / tolerance — correct

| Item | Verified |
|---|---|
| `lora.test.width_slope_vs_label` portal = 0.922998, \|Δ\| ≤ 0.05 | reference report `0.9229977302910213`; `compare.py` `ABS` 0.05 |
| `lora.test.mean_slope` portal = 1.011556, \|Δ\| ≤ 0.05 | `1.0115558700330238`; `ABS` 0.05 |
| `lora.test.rps` portal = 1.98913e-4, relative ≤ 10 % | `1.9891323497951143e-4`; `REL` 0.10 |
| All three must hold; a miss is a STOP for the author, no re-run/substitution | pre-declaration §Tolerance and lines 14–23/48; comparator exit 0 = equivalent, 1 = miss |
| Comparative/descriptive fields recorded | `compare.py` emits `criteria` + `descriptive`; line 46 requires recording them |

Notes (MINOR-2/3/4 below): `compare.py` unconditionally indexes `p["head_fit"]["test"]` and
`t["head_fit"]["test"]`, so a D report without `head_fit` (e.g. `--stage screen` or a hard/native run)
makes it exit 1 via `KeyError`, indistinguishable from a tolerance miss unless stderr/exit cause is
recorded; D's head-fit block has different descriptive keys (see BLOCKING-2b). The proposal never says
where `compare.py` runs (it lives in the Mac worktree) or where the TASL-2 report is copied for the
comparison; record the copy sha, the reference path/sha `7c1be5e9…`, the comparator sha `bd957c0d…`, the
comparison JSON location/sha and `compare.py`'s exit code. `report.pass` will be a D E0-threshold value
(not the equivalence verdict) and must not be used as the equivalence result.

## 4. STOP / must-not / record completeness

| Required | Unit | Verdict |
|---|---|---|
| rc 0; report/manifest exist; sha256s; wall time | §3.1 | present |
| lease log before/after (+3 lines) and FETCH_HEAD/ref side effects | §3.1 | present; the expected after-state is still not pinned (MAJOR-2) |
| compare.py → `equivalent: true`, all three pass; record comparison/descriptive | §3.2 | present |
| no tracked-file/`.pyc`/worktree change; no marker/evidence; no TASL-7 action | §3.3 | present, but unattainable without MAJOR-1's env fix |
| result record fields | §3.4 | mostly present; see MINOR-4 for the missing fields |
| STOPs: comparison miss, rc≠0, missing report, config/model/freeze mismatch, lease not acquired/released, OOM/CPU fallback, tracked/untracked/`.pyc`/worktree changes, authority/protocol change; preserve, no re-run | §4 | present, but gaps: no disk <50 GB; no stalled lease-gate fetch (`TimeoutExpired`) as a host/network STOP; no "wrong D HEAD/freeze/config before the run" preflight STOP; the "config mismatch" target is ambiguous (MAJOR-2); "CPU fallback" does not carve out the intended CPU L-BFGS head fit (MINOR-6); no TASL-7-reachability re-check immediately before the run (MINOR-5) |
| must-not: attempt-2/evidence root, TASL-7 action, code/config/rule changes, other host, deletion, main/exam-x push, other user's files/processes | §5 | present and correct |
| one job, no re-run | lines 22/48/58 | present |

## 5. Host facts (read-only, TASL-2, 2026-11-17 01:50–01:56Z)

| Fact required | Verified value |
|---|---|
| venv freeze | `trackp-gpu`: Python 3.12.15, torch 2.6.0+cu124; freeze **121 lines sha `50238e5a07ca…`**, byte-identical to the committed `pip_freeze_trackp-gpu.txt` (also the rehearsal's `now.sorted`/`pin.sorted`/`venv_freeze_now.txt` = same sha; independently re-listed 121 distributions) |
| D worktree | HEAD `8662e35991659f7a661fb7ed6be4980791d302f3`, detached, `status -uall` = 0 lines; files: `trackp.py d2a30ec2…`, `run.py 797f00d5…`, `exam_run.py f0f1ce94…`, config `049bafed…`; linked gitdir `…/.git/worktrees/Agent_paper_B_D_20261117`, index `855fec75…` |
| portal reference report | present, `7c1be5e9…` (also byte-identical at `b9ad6f8f`) |
| GPU / lease | RTX 4090, `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01, 24,564 MiB, 353 MiB / 0 %, 0 compute apps; `gpu0.lock` free (`flock -n` FREE); no `*.active`, no `~/r1_locks/bin/trackp-evidence` |
| disk | 1,877 G total / 1,407 G used / **374 G available** (80 %) — ≥50 GB |
| lease log / fetch | 191 lines sha `0a4a14ae…`; `FETCH_HEAD` 104 B sha `83c64a87…` → `26177d82…`; `origin/main` = `26177d82…` = remote main (`git ls-remote`); main worktree HEAD `b5a7aeca` |
| roots | no `ENGINEERING_equivalence*`, no `p3a_attempt2*`, no `p3a_operator_20261027` (older `runs/p0/*attempt2*` and `runs/phase2/gpu_smoke_attempt2.json` are 25–26 Oct history, unrelated); scratch parent holds D worktree + `ENGINEERING_rehearsal_20261117T014743Z` + `now.sorted`/`pin.sorted`/`venv_freeze_now.txt`/`venv_freeze_err.txt` |
| TASL-7 | still unreachable (`ssh tasl7` → `100.106.74.51:22` timeout) |

## 6. Findings and exact fixes

| ID | Severity | Finding | Exact fix |
|---|---|---|---|
| **B-1** | BLOCKING | Command runs D's final budget (6,000 steps / patience 10) because `--stage` defaults to final and no `--steps` is passed; the pre-declaration and the host-change header require the same 2,000-step budget; "~25 min" is the 2,000-step figure | Add `--steps 2000` (keep default `--stage final` so `head_fit` exists for `compare.py`; never `--stage screen`); record `max_steps=2000`/`patience=10`/`budget_override`; restate the wall estimate |
| **B-2** | BLOCKING | Lines 35–38's "D differs only in the reviewed P.3a/A3-short changes" is false: D also carries R1-E0-BUDGET (config digest `64073cea…` vs `588869fa…`), R1-E0-HEADFIT (L-BFGS descriptive fit) and the fresh-head LoRA start (commits `471f93f7`, `52b527b9`; reference LoRA started from the fitted head); the pre-declared comparison therefore does not isolate the host, and TASL-2 is the portal host itself | Re-declare the unit truthfully (pre-run): D-code same-host reproducibility of the portal reference with the 2,000-step cap and the recorded deltas; `equivalent:true` required, miss = STOP/no re-run; record both config digests and the LoRA-start/head-fit deltas; state that TASL-2 = portal host. Or run the literal check with reference code `8e13e77` (config `588869fa…`) with an explicit authority/scope note |
| **M-1** | MAJOR | Env lacks `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0`, so new `.pyc`/index writes make §3.3/§4 unattainable by construction | Add both, as the accepted rehearsal unit did; record `.pyc`/index baselines |
| **M-2** | MAJOR | No preflight/"Before" step and no pins; STOP "config/model/freeze mismatch" and before/after claims uncheckable | Add the "Before" step and the pin/baseline list in §2 above; define mismatch against recorded D facts (`8662e359`, `049bafed`/`64073cea`, `50238e5a`, models), not the reference `588869fa`/`8e13e77` |
| MINOR-1 | MINOR | Using D instead of `8e13e77` is defensible **only** as a declared D-code check (the intent "the code we would run Unit B with" is legitimate and is recorded), but lines 35–38 must not claim the e0 path is unchanged | Covered by B-2; explicitly answer the "using D" question in the text |
| MINOR-2 | MINOR | `compare.py` location/order/output unresolved: it lives in the Mac worktree, needs the TASL-2 report copied back; no record of the copy path/sha, comparison JSON location, or exit code | State: run the committed `compare.py` in the Mac worktree against a byte-identical copy of the TASL-2 report (sha recorded before/after copy); record reference `7c1be5e9…`, comparator `bd957c0d…`, `comparison.json` path/sha and the exit code |
| MINOR-3 | MINOR | `compare.py` fragility: missing `head_fit.test`/`lora.test` keys → `KeyError`/exit 1, indistinguishable from a tolerance miss | Pre-check the D report has `lora.test` (three keys) and `head_fit.test` before invoking; record exit code + stderr; treat a schema failure as its own STOP cause |
| MINOR-4 | MINOR | Result-record fields missing | Add: rc; comparison exit code; `manifest.evidence_label == "DRYRUN"`; config digest `64073cea…`; freeze `50238e5a…`; D file shas; the report-key assertions (`max_steps`, `stage`, `patience`, `budget_override`, `head_fit` present); stdout/stderr sha; disk; `.pyc`/tracked baseline; lease/fetch before-after; authority commit `45fb94cc` (branch, not `origin/main`); table-host disclosure; an independent review of the result before any Unit B step |
| MINOR-5 | MINOR | Re-check TASL-7 reachability immediately before executing; if it recovered, the TASL-2 route is moot and the run must stop/re-route per `R1-TRACKP-TASL2-HOST` | Add to the preflight STOPs |
| MINOR-6 | MINOR | §4's "CPU fallback" STOP reads as forbidding the intended full-batch CPU L-BFGS head fit (`R1-E0-HEADFIT`, descriptive) | State that the CPU head fit is by design, not a fallback; require `nvidia-smi`/manifest to show the LoRA stage on the GPU |
| MINOR-7 | MINOR | STOP list lacks disk <50 GB and a stalled lease-gate fetch (`TimeoutExpired` → host/network STOP, not a comparison miss); also lacks "wrong D HEAD/clean/freeze before the run" | Add the three STOPs |
| MINOR-8 | MINOR | Unit B's `--load` prerequisite (TASL-7 attempt-1 `EVIDENCE/kev-0.8b/final/saved` absent on TASL-2) is unaddressed; the unit's context implies Unit B can follow immediately | Add one sentence: this unit does not resolve the `--load` gap; a pass is not Unit B readiness |
| MINOR-9 | MINOR | Scratch root creation/naming: `<UTC>` root must not exist and is created implicitly by the child (the code's `mkdir(parents=True)` runs only inside the `head_fit` branch); the parent already contains non-scratch files | Pre-create the empty `<scratch>` root explicitly after asserting it does not exist, or record the implicit creation; include the parent listing in the baseline |

## 7. Verdict

**NOT ACCEPTED — 2 BLOCKING, 2 MAJOR, 9 MINOR.** It may not be executed as written. The authority, the
scope, the tolerance, the reference values, the comparator semantics, the D delivery, the frozen
environment, the scratch naming and the must-not list are correct, and the check is worth doing; but the
command currently measures D's 6,000-step final budget, and the unit's factual premise that D's e0 path is
unchanged is wrong (budget + descriptive head fit + LoRA start state), so the pre-declared comparison
would not mean what the unit says. After B-1/B-2 are fixed (and preferably M-1/M-2), the corrected bytes
should be re-checked (a short confirmation round is sufficient) and then the unit may be executed as
written, once, on TASL-2, with the recorded lease/fetch side effects treated as expected.

**If accepted after the fixes, the result record must contain:** unit + exact argv/env
(`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PYTHONPATH=.`), rc, wall time (no wall STOP), D HEAD `8662e359…`/`trackp.py d2a30ec2…`/`run.py 797f00d5…`/
`exam_run.py f0f1ce94…`/config `049bafed…` digest `64073cea…`/freeze 121 lines `50238e5a…`, host/GPU/driver
(uuid `GPU-4d623e76-…`, driver 535.309.01) from `manifest.host`, reference report path/sha `7c1be5e9…`,
`<run-dir>/report.json` + `manifest.json` paths/sha256, `manifest.evidence_label == "DRYRUN"`, the report
keys (`max_steps=2000`, `stage="final"`, `patience=10`, `budget_override`, `head_fit` present,
`lora.test` three keys), lease log before/after (191→194 lines, sha `0a4a14ae…`, the three added
`acquired`/`start`/`end` lines), `FETCH_HEAD`/ref before/after (`83c64a87…` rewrite, `origin/main` =
`26177d82…` unchanged), tracked-file/`.pyc`/worktree/index/nvidia-smi before/after, disk, stdout/stderr
sha and `SHA256SUMS`, the recorded `compare.py` invocation + reference/comparator shas + exit code,
`comparison.json` (path/sha) with `equivalent`, the three criteria and descriptive fields, the explicit
statement that this is ENGINEERING (never counted, no attempt-2 root/table), both config digests and the
D-vintage deltas (B-2), that TASL-2 is the portal host and that a pass is same-host D-code
reproducibility, and that the table host will be disclosed as TASL-2 if Unit B runs there. If the
comparison misses: preserve, report, STOP — no re-run, no configuration substitution.
