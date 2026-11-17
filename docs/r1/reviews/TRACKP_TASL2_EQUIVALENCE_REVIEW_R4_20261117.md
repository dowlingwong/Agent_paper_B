# Review R4 — Track P host-equivalence check on TASL-2, revision 4 bytes (ENGINEERING; 17 November 2026)

**Status: ACCEPTED — 0 BLOCKING, 0 MAJOR, 10 MINOR.** The canonical revision-4 bytes
(`docs/r1/proposals/TRACKP_TASL2_EQUIVALENCE_20261117.md`, sha256
`bfc8d97eef0366e572cb818999b5451cba2bf8fbed59ac94138d4abdf094ad34`, 96 lines) correctly carry the two
round-3 fixes: **BLOCKING-1** is closed — §3.3/§3.5 now require **two** lease lines (191 → 193,
`start`/`end`, no `acquired`) and no `stage` key; **MAJOR-1** is closed — the two `FETCH_HEAD` paths are
separated correctly (main clone 17,593 B / `69545606…` unchanged; `8e13e77` worktree gitdir absent →
104 B / `83c64a87…`). The literal `8e13e77` + `897d83c` command/config, the protected env, the preflight
pins, the after-checks, the comparator/tolerance/STOPs, and the "not a test of D"/same-host statements are
unchanged and remain correct and authority-consistent (all re-verified read-only against TASL-2). Ten R3
MINORs remain (three partially applied), including the revision label and parts of the record-field list;
none affects whether the run reproduces the pre-declared configuration or how its result is judged. **The
unit may be executed once, as written, on TASL-2**, and the MINORs can be closed in the result record or a
follow-up revision. Review only: the unit was **not executed** (no training/comparator run, no `flock`, no
fetch, no GPU command), **no host write**, **no commit/push**; read-only SSH to TASL-2 (`ssh portal_zhixu`,
user `dowling`) was used for host facts. The only workspace change made by this review is this uncommitted
review file.

## 0. Canonical bytes, authority and method

| Object | sha256 / lines | Where / state |
|---|---|---|
| **Unit under review (rev 4)** | `bfc8d97eef0366e572cb818999b5451cba2bf8fbed59ac94138d4abdf094ad34`, **96 lines** | `docs/r1/proposals/TRACKP_TASL2_EQUIVALENCE_20261117.md`, worktree `ops-tasl-20261116`; **uncommitted-untracked** (`??`); matches the canonical value given; unchanged across this review (mtime 2026-11-17T03:16:10+0100). Line 1 still reads "Unit (revision 3)" and line 3 still describes "Revision 2 answers the round-1 review" — see MINOR new-1 |
| R3 review | `3644882c43f059689ff7b0ec1140c8ed52a070d62b6708145b4bbf761ff9f696`, 228 lines | `docs/r1/reviews/TRACKP_TASL2_EQUIVALENCE_REVIEW_R3_20261117.md`; matches the given sha |
| Authority `R1-TRACKP-TASL2-HOST` | commit `45fb94cc8bfe9aafea8d57b45aaf06d19a3e0a44` (17 Nov 2026) | Row at `docs/r1/PLAN.md:1275` in that commit; on `origin/author-decisions-20261117b`, not `origin/main` `26177d82…` |
| `R1-TASL2-REHEARSAL-SCOPE` / rehearsal result | `33c823516ad5c9c879df432fe958be8d57003a29`; result `ec98fb18c7c630cbec4baacb8f3c6f374db5160d71f3e75c4007c16fa7bf62a9`, 44 lines, PASSED | same branch; `docs/r1/reports/TASL2_UNITB_REHEARSAL_RESULT_20261117.md` |
| Pre-declaration (reused) | `4ed7ef92816c6160c0e144b249bd39c309f8ddd0faa1693e32aeceb7848fd726`, 33 lines | `…/tasl7_equivalence_20261026/PREDECLARATION.md` |
| Comparator / TASL-7 precedent | `bd957c0d3e984b4ec9e27ef090d29580654cfef91d73174bf05a615cd4bf6084`, 37 lines; precedent `0793eddb…` `equivalent: true` | `…/tasl7_equivalence_20261026/{compare.py,comparison.json}`; `ABS` 0.05/0.05, `REL` 0.10, exit 0/1 |
| Portal reference report / manifest | report `7c1be5e98fc896074aae33ec301263c3b02973c02a1c387130eb3f45c21d41e0` (1,986 B); manifest `77f8cc3e88d13d8482a2521a7dcb63e4aa4db12c72cb174f57dcdf04b2410284` | `…/trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/`; manifest: `config_sha256 588869fa…`, `evidence_label "DRYRUN"`, `data_manifest_sha256 b963be2d…`, `gpu_lease` 2 entries, **no `host` key** |
| Reference code / harness | paper `8e13e77cd49532c7ac2e78ad8e5c1ee45401b286`; harness `897d83c8efa364ec2fdd37288241cc42e01d7274` | content shas `trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…`; no `--stage` |

Method: local reads/`git show` of the unit, R1–R3 reviews, the authority row (`45fb94cc:PLAN.md`),
pre-declaration, comparator, TASL-7 comparison, reference report/manifest and the `8e13e77` blobs; plus
read-only SSH to TASL-2 on **2026-11-17 ≈02:18–02:21Z** (host clock; host local = PST) using only
`date`, `hostname`, `ls`, `find`, `stat`, `sha256sum`, `wc`, `df`, `nvidia-smi --query…`, `lsof`,
`cat`/`head`/`tail`/`grep` of small files, and `git rev-parse`/`status --porcelain -uall`/
`rev-parse --git-path`/`worktree list`/`remote -v`/`config --get`/`ls-tree`/`show` reads (all `git status`
reads with `GIT_OPTIONAL_LOCKS=0`). One frozen-interpreter query (`sys.version`, `torch.__version__`) was
the only code executed on the host (no repo code, no CUDA initialisation). No unit child run, no
training/compare code, no `flock`, no `git fetch`, no GPU command, no commit/push, no host write — verified
by the unchanged invariants below and by `find -newermt` (no file under the venv or the repo `.git`
changed during the review; `nvidia-smi` had 0 compute apps before and after).

Integrity note: host invariants are identical before/after this review — lease log **191 lines /
`0a4a14ae…`**, main-clone `FETCH_HEAD` **17,593 B / `69545606…`**, `8e13e77` worktree `FETCH_HEAD`
**still absent**, both worktree HEADs unchanged and clean, linked indexes `070b4ead…` (8e13e77) /
`855fec75…` (D) unchanged, `.pyc` 65, no `ENGINEERING_equivalence*` root, no `*.active` marker, GPU
353 MiB / 0 %. No file was created or deleted on the host.

## 1. R3 BLOCKING-1 — fixed (verified)

- §3.1 (lines 54–56): "lease-log count/sha (**191 lines / `0a4a14ae…`** at acceptance) with expected
  after-state **193 / two added lines** (`start`/`end`; the reference code `8e13e77` has no `acquired`
  event — that was added by `08aeaff9`)".
- §3.3 (lines 66–68): "report `max_steps`=2000/patience=5 as in the reference config (this code vintage has
  no `stage` key); lease log gained exactly **two** lines (`start`/`end`; no `acquired`)".
- §3.5 (line 78): "lease-log before/after + **two** lines (191→193; no `acquired`)".

No `stage` requirement remains anywhere. Verified: `run.py` at `8e13e77` writes `start` then `end` only
(no `acquired`, no `monotonic_s`, no `tasl7_driver`); the portal reference manifest's `gpu_lease` has two
entries; on TASL-2 the Oct-26 `trackp e0 kev-0.8b` lease-log entries are two-line `start`/`end` pairs, the
single `acquired` event in the whole 191-line log is the 17 Nov D-code rehearsal, and the `8e13e77` report
schema has no `stage` key. 191 → 193 with two added lines is the correct after-state.

## 2. R3 MAJOR-1 — fixed (verified)

- §3.1 (lines 57–60): "both FETCH_HEAD files: the main clone `.git/FETCH_HEAD` (17,593 B sha
  `69545606…`; expected unchanged) and the worktree gitdir
  `…/.git/worktrees/Agent_paper_B_8e13e77/FETCH_HEAD` (absent now; expected created, 104 B sha
  `83c64a87…`; no ref move/object download — a ref move is a STOP; record both before/after)".
- §3.5 (lines 78–80): "both FETCH_HEAD files before/after (main clone 17,593 B/`69545606…` unchanged;
  worktree gitdir absent → 104 B/`83c64a87…`)".

Verified on TASL-2: main clone `.git/FETCH_HEAD` = 120 lines / **17,593 B** / **`69545606…`**, mtime
17:58 PST (operator provisioning fetch); `git rev-parse --git-path FETCH_HEAD` in the `8e13e77` worktree
resolves to `/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_8e13e77/FETCH_HEAD`, **absent**; the
D worktree gitdir `FETCH_HEAD` is the expected **104 B / `83c64a87…`**, one line
`26177d82904e8e72802ddf985ff35ffe0aaea479\t\tbranch 'main' of https://github.com/dowlingwong/Agent_paper_B`.
Two independent confirmations that this is a *creation* in the linked worktree, not a rewrite: the D
provisioning fetch produced the per-worktree file, and `git fetch` renders the remote display URL without
the `.git` suffix here (the main clone's 120-line `FETCH_HEAD` lines also render it without `.git`), so the
pinned 104 B/`83c64a87…` after-content is right.

## 3. The rest of the unit — unchanged and correct

- **Command/config are the literal pre-declared check.** §2/§3.2 run
  `python r1/scripts/trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001
  --run-dir <scratch>/kev-0.8b/fresh_soft_lr0.0001` from the `8e13e77` worktree with the absolute
  frozen-venv interpreter — the TASL-7 `driver.sh` form, **no `--steps`/`--stage`** (they do not exist at
  `8e13e77`). Config `10ead2a5…` declares `e0 = {protocol "trackp_e0/v2", max_steps 2000, eval_every 100,
  patience 5, batch_size 8, seed 0}`, and the loaded digest is **`588869fa…`** — exactly the portal
  reference/TASL-7 `config_sha256`; the reference report itself has `max_steps 2000, eval_every 100,
  patience 5, batch_size 8, protocol "trackp_e0/v2", variant "fresh", target "y_soft", n_test 1000`.
  The protected env (`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=<harness worktree>`) is
  present; scratch root `…/unitb_rehearsal_20261117/ENGINEERING_equivalence_<UTC>` is new, never an
  attempt-2 root, never counted.
- **Preflight pins match the host** (all verified read-only): both worktrees present and clean at
  `8e13e77cd495…` / `897d83c8efa3…`; file shas `9959a106…` / `bdec6784…` / `6125b364…` / `10ead2a5…`;
  freeze 121 lines `50238e5a…` (committed `pip_freeze_trackp-gpu.txt` and the three byte-identical copies
  in the rehearsal parent); torch 2.6.0+cu124 / Python 3.12.15; both model dirs present; parent listing
  holds the two new worktrees + D + the rehearsal scratch + four pre-existing files; `.pyc` **65**
  (D 72); indexes `070b4ead…` / `855fec75…`; `git worktree list` = main + 8e13e77 + D; `origin/main` =
  `26177d82…`; GPU RTX 4090 `GPU-4d623e76-…`, driver 535.309.01, idle, no compute app, lock free, no
  marker/`*.active`; disk 374 G available (≥50 GB); no `ENGINEERING_equivalence*` root.
- **After-checks/STOPs correct.** rc 0; report/manifest shas; `max_steps`/patience (no `stage`); two lease
  lines; worktree-gitdir `FETCH_HEAD` created 104 B/`83c64a87…` while the main-clone file is untouched;
  `manifest.host` absent (take GPU/driver/UUID from `nvidia-smi`); no tracked/.pyc/index/worktree change
  outside the recorded lease/fetch side effects; lease released; GPU idle; wall time ≈25 min; a comparison
  miss/no re-run; "not a test of D" and same-host (portal host) statements.
- **Comparator/tolerance/authority.** `lora.test` values `0.922998/1.011556/1.98913e-4`, `ABS` 0.05,
  `ABS` 0.05, `REL` 0.10, exit 0/1; TASL-7 precedent `0793eddb…` is `equivalent: true`; the authority
  requires this TASL-7-style check once on TASL-2, ENGINEERING, after the rehearsal passed and while
  TASL-7 is unreachable (rehearsal result `ec98fb18…` PASSED; TASL-7 still unreachable — see §4 m-3).

## 4. Remaining MINORs (non-blocking)

| ID | Status | Finding in `bfc8d97e…` | Fix (for the result record / a follow-up revision) |
|---|---|---|---|
| m-1 | partial | §3.3 asserts only `max_steps`=2000/patience=5; `stage` correctly dropped | add eval_every=100, batch_size=8, protocol "trackp_e0/v2", variant "fresh", target "y_soft", n_test=1000, and `manifest.gpu_lease` two entries |
| m-2 | partial | `manifest.host`-absent note is applied; harness branch "HEAD" (detached) and the portal `git.paper.dirty=true` vs clean-`8e13e77` false delta are still not required to be recorded | record them as descriptive |
| m-3 | open | no preflight re-check of TASL-7 reachability and no Track X `STATUS.md` evidence-status record (TASL-7 verified unreachable now: `ssh tasl7` → `100.106.74.51:22` "Operation timed out", exit 255; marker absent) | add the reachability STOP/re-route check and the STATUS.md gate record |
| m-4 | partial | copy+sha+precheck now present (§3.4); still missing recorded copy sha before/after, copy path, `comparison.json` sha and comparator exit code, the `lora.test` three-key/`head_fit.test` pre-check, and a schema/`KeyError` failure as a STOP distinct from a tolerance miss; §3.1's "copy into scratch **or run from the worktree**" still conflicts with §3.4 (the `8e13e77` worktree has neither file — confirmed by `find`) | spell the copy/run place and the recording |
| m-5 | partial | §3.5 expanded but still has no rc, comparison exit code, `manifest.evidence_label=="DRYRUN"`, `data_manifest_sha256 b963be2d…`, `head_form=="linear12"`, `gpu_lease` two entries, stdout/stderr sha + `SHA256SUMS`, disk, authority commit/branch, exact cwd/interpreter, TASL-7 state, portal-dirty/clean delta | add those fields |
| m-7 | open | no instruction to compute the loaded config digest with `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0` (`--check-config` imports repo code) and record `.pyc` 65 before/after that check | add to §3.1 |
| m-8 | open | no sentence that Unit B's `--load` target (TASL-7 attempt-1 `EVIDENCE/kev-0.8b/final/saved`, absent on TASL-2) is unresolved and that a pass is not Unit B readiness | add to §1 |
| m-9 | open | §1 still says the pre-declaration is "unchanged" without noting that only the run-dir is superseded by the TASL-2 scratch | add the note; re-verify the comparator uses `lora.test` tolerances from the committed pre-declaration |
| new-1 | partial | line 1 now says "(revision 3)" but this is the revision-4 submission; line 3 change note still reads "Revision 2 answers the round-1 review" (two rounds stale) | retitle "(revision 4)" and update the change note to the R2/R3 history |
| new-2 | open | §3.1 still lists "`r1/scripts/trackp.py`/`run.py`/`exam_run.py`/config file shas" — `run.py`/`exam_run.py` are at `r1/c3/train/`, not `r1/scripts/` | spell the exact paths |

## 5. Host facts (read-only, TASL-2, 2026-11-17 ≈02:18–02:21Z host clock; local PST)

| Fact | Verified value |
|---|---|
| Host | `TASL-2` (zhixu portal), read-only SSH user `dowling` |
| `8e13e77` worktree | `…/unitb_rehearsal_20261117/Agent_paper_B_8e13e77`; detached **`8e13e77cd49532c7ac2e78ad8e5c1ee45401b286`**; `status --porcelain -uall` = 0 lines; index `070b4ead…`; `.pyc` **65**; files `trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…`; no `compare.py` and no reference report anywhere in the worktree (only `trackp_e0v2_dryrun_20261026/{driver.sh,full_suite.txt,summarize.py,trackh_modules.txt}`) |
| Harness worktree | `…/autoresearch_harness_897d83c`; detached **`897d83c8efa364ec2fdd37288241cc42e01d7274`**; `status -uall` = 0 lines; `src/autoresearch/` present |
| Main clone / refs | `/home/dowling/Agent_paper_B` on `main` `b5a7aeca…`; `worktree list` = main + `8e13e77` + D (`8662e359…`); `origin/main` = **`26177d82…`**; origin URL `https://github.com/dowlingwong/Agent_paper_B.git` (git 2.34.1) |
| `FETCH_HEAD` | main clone `.git/FETCH_HEAD`: **120 lines / 17,593 B / `69545606…`**, mtime 2026-11-16 17:58 PST (provisioning); `8e13e77` worktree gitdir `FETCH_HEAD`: **absent**; D worktree gitdir `FETCH_HEAD`: **104 B / `83c64a87…`** (one line `26177d82… branch 'main' of https://github.com/dowlingwong/Agent_paper_B`) |
| D worktree (context) | detached `8662e359…` clean, index `855fec75…`, `.pyc` 72; contains reference report `7c1be5e9…` and `compare.py bd957c0d…` |
| Freeze / venv | `trackp-gpu`: Python 3.12.15 (uv), torch 2.6.0+cu124; freeze 121 lines `50238e5a…` (committed file + three byte-identical copies in the rehearsal parent; the venv has no separate freeze file) |
| Models | base `…/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41` and adapter `…/models/jaredpalmer__kev-0.8b@788ddbdd6571` present; config `models_dir` = `/home/dowling/r1_trackp/models` |
| GPU / lease | RTX 4090, `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01, 24,564 MiB, 353 MiB / 0 %, 0 compute apps; `~/r1_locks/gpu0.lock` 0 B, no `lsof` holder → free; no `*.active` marker |
| Lease log | **191 lines, sha `0a4a14ae…`**; last job = 2026-11-17T01:47:49Z D-code rehearsal (`acquired`/`start`/`end`); exactly **1** `acquired` event in the file; Oct-26 reference-code jobs are two-line `start`/`end` pairs |
| Disk / roots | 1.9 T total / 1.4 T used / **374 G available**; no `ENGINEERING_equivalence*`; no attempt-2 root (only Oct-26 `attempt1` history under `r1_trackp/runs`) |
| TASL-7 | still unreachable from the Mac: `ssh tasl7` → `100.106.74.51:22`, "Operation timed out", exit 255 |

## 6. Verdict

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 10 MINOR.** The revision-4 bytes fix exactly the two round-3 blockers and
leave the science, the literal command/config, the preflight/after pins, the comparator and the
authority/scope statements correct. **It may be executed once, as written, on TASL-2**, with these
expected side effects treated as normal: lease log **191 → 193** lines (one `start`, one `end`, no
`acquired`; before sha `0a4a14ae…`), the `8e13e77` worktree gitdir `FETCH_HEAD` **created** at
104 B / `83c64a87…`, the main clone `.git/FETCH_HEAD` **unchanged** at 17,593 B / `69545606…`, and a wall
time of ≈25 min. No re-run on a comparison miss; preserve and report. The ten MINORs are recording/labeling
gaps and do not block execution.

**Result record (`TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md`) must contain:** unit + exact argv/env
(`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=<harness worktree>`, the
absolute frozen-venv interpreter and cwd), rc, wall time; `8e13e77` HEAD `8e13e77cd495…` + file shas
(`trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…`) and loaded config
digest `588869fa…`; `897d83c` harness HEAD `897d83c8efa3…`/clean (detached); freeze 121 lines
`50238e5a…`; host/GPU/driver/UUID from `nvidia-smi` (not `manifest.host`, which is absent); the scratch
root and `<run-dir>/report.json` + `manifest.json` paths/sha256; `manifest.evidence_label == "DRYRUN"`,
`data_manifest_sha256 b963be2d…`, `head_form=="linear12"`, `gpu_lease` two entries; report keys
(`max_steps=2000`, `eval_every=100`, `patience=5`, `batch_size=8`, `protocol="trackp_e0/v2"`,
`variant="fresh"`, `target="y_soft"`, `n_test=1000`, `lora.test` three keys, `head_fit.test`); lease log
before/after (191 → 193, sha `0a4a14ae…` before, two added `start`/`end` lines, job "trackp e0 kev-0.8b");
**both** `FETCH_HEAD` paths before/after (main clone 17,593 B/`69545606…` unchanged; `8e13e77` worktree
gitdir absent → 104 B/`83c64a87…`; `origin/main` = `26177d82…`; no ref move/object download);
tracked-file/`.pyc` (65)/linked-worktree-index/worktree-list/`nvidia-smi` before/after; disk;
stdout/stderr sha and `SHA256SUMS`; the `compare.py` invocation (`bd957c0d…`, byte-identical copy sha)
against a byte-identical copy of the reference report `7c1be5e9…`, its exit code, and `comparison.json`
(path/sha) with `equivalent: true`, the three criteria and descriptive fields; the explicit statements that
this is ENGINEERING (never counted, no attempt-2/evidence root), that it is a same-host reference
reproduction on the portal host and **not** a test of D (D delivery and Unit B separate), and that the table
host will be disclosed as TASL-2 if Unit B runs there; the TASL-7-reachability state; and that a pass does
not resolve Unit B's `--load` prerequisite. If the comparison misses: preserve, report, STOP — no re-run, no
configuration substitution.
