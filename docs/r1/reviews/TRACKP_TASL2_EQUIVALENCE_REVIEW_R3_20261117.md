# Review R3 — Track P host-equivalence check on TASL-2, literal reference-code path (ENGINEERING; 17 November 2026)

**Status: NOT ACCEPTED — 1 BLOCKING, 1 MAJOR, 10 MINOR.** The bytes submitted as "revision 3"
(`docs/r1/proposals/TRACKP_TASL2_EQUIVALENCE_20261117.md`, sha256 `c7d1fa3c…`, 89 lines) carry only a
**partial** application of the round-2 fix list. Applied and verified: R2 **M-1** (the three stale pins),
**m-6** (run cwd + absolute interpreter) and **m-10** (same-host premise in §1). Still open: R2 **B-1**
in §3.3/§3.5 — the "194 / three added lines → 193 / two added lines" replacement was made only in §3.1;
§3.3 still *requires* "lease log gained exactly three lines" and §3.5 still records "+ three lines", and
§3.3 still demands a `stage` field — plus R2 **m-1, m-2, m-3, m-4, m-5, m-7, m-8, m-9**. A fresh check
of the fetch side effect finds a **new MAJOR**: the `17,593 B → 104 B` `FETCH_HEAD` pin names two different
files (the main clone's `.git/FETCH_HEAD` vs the `8e13e77` worktree's per-worktree `FETCH_HEAD`), so a
correct run would not produce the stated after-state for either path. The document still titles itself
"revision 2". **The unit may not be executed as written.** Review only: the unit was **not executed** (not
even partially), **no host write**, **no commit/push**, **no GPU command**; read-only SSH to TASL-2
(`ssh portal_zhixu`, user `dowling`) was used for host facts, plus one failed reachability probe to TASL-7
from the Mac (no writes). The only workspace change made by this review is this uncommitted review file.

## 0. Canonical bytes, authority and method

| Object | sha256 / lines | Where / state |
|---|---|---|
| **Unit under review ("rev 3")** | `c7d1fa3c0ee967287b1c00b59a42c065cc17bf018d89d14971562a419e399dad`, **89 lines** | `docs/r1/proposals/TRACKP_TASL2_EQUIVALENCE_20261117.md`, worktree `ops-tasl-20261116`; **uncommitted-untracked** (`??`); matches the canonical value given; title still says "(revision 2)" (line 1). Unchanged across the review (mtime 2026-11-17T03:07:11+0100) |
| R2 review | `8d4a36e6333a7360aa43163acfd6b45908365519dcfd1c3869d495188b004104`, 247 lines | `docs/r1/reviews/TRACKP_TASL2_EQUIVALENCE_REVIEW_R2_20261117.md`; uncommitted-untracked; matches the given sha |
| Round-1 review | `c14cbb391b7d3d07285a70135f1d810bc8a77ced96f2242abf2d5946e2f52287`, 236 lines | same dir |
| Authority `R1-TRACKP-TASL2-HOST` | commit `45fb94cc8bfe9aafea8d57b45aaf06d19a3e0a44` (17 Nov 2026) | Row at `docs/r1/PLAN.md:1275`; on `origin/author-decisions-20261117b`, **not** `origin/main` `26177d82…` |
| `R1-TASL2-REHEARSAL-SCOPE` | commit `33c823516ad5c9c879df432fe958be8d57003a29` | same branch |
| Rehearsal result (PASSED) | `ec98fb18c7c630cbec4baacb8f3c6f374db5160d71f3e75c4007c16fa7bf62a9`, 44 lines | `docs/r1/reports/TASL2_UNITB_REHEARSAL_RESULT_20261117.md` |
| Pre-declaration (reused) | `4ed7ef92816c6160c0e144b249bd39c309f8ddd0faa1693e32aeceb7848fd726`, 33 lines | `docs/r1/reports/tasl7_equivalence_20261026/PREDECLARATION.md` |
| Comparator | `bd957c0d3e984b4ec9e27ef090d29580654cfef91d73174bf05a615cd4bf6084`, 37 lines | `…/tasl7_equivalence_20261026/compare.py` — `ABS` 0.05/0.05, `REL` 0.10, exit 0 = equivalent / 1 = miss |
| TASL-7 comparison precedent | `0793eddba25b675f49a40ec5670dfb9550e2f1b362b3167ff09a92e01c505b76`, 117 lines; `equivalent: true`, all three criteria pass | `…/tasl7_equivalence_20261026/comparison.json` |
| Portal reference report | `7c1be5e98fc896074aae33ec301263c3b02973c02a1c387130eb3f45c21d41e0` (1,986 B) | `docs/r1/reports/trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/report.json`; on TASL-2 present in the **D worktree** copy (same sha); **absent** from the `8e13e77` worktree |
| Reference code `8e13e77` | `8e13e77cd49532c7ac2e78ad8e5c1ee45401b286` | files `trackp.py 9959a106…`, `run.py bdec6784…` (`r1/c3/train/`), `exam_run.py 6125b364…`, config `10ead2a5…` / loaded digest **`588869fa…`**; no `--stage` argument |
| Harness `897d83c` | `897d83c8efa364ec2fdd37288241cc42e01d7274` | portal reference manifest and TASL-7 run manifest both record `897d83c…` |

Method: local reads and `git show` of the unit, R1/R2 reviews, authority row, pre-declaration, comparator,
TASL-7 comparison/manifest, portal reference report/manifest, and `8e13e77` blobs in the local object
store; plus read-only SSH to TASL-2 on **2026-11-17 ≈02:09–02:14Z** (host clock; host local = PST) using
only `date`, `hostname`, `ls`, `find`, `stat`/`ls -l`, `sha256sum`, `wc`, `df`, `nvidia-smi --query…`,
`lsof`, `cat`/`head`/`tail` of small files, `git rev-parse`/`status --porcelain -uno`/
`rev-parse --git-path`/`worktree list`/`ls-remote` reads (all `git status` reads with
`GIT_OPTIONAL_LOCKS=0`). No unit child run, no training/compare code, no GPU command, no `flock` taken this
round (lock verified free by `lsof` on the 0-byte lock file), no commit/push, no host write.

Integrity note: the host invariants are identical before/after this review — lease log **191 lines /
`0a4a14ae…`**, main-clone `FETCH_HEAD` **17,593 B / `69545606…`**, `8e13e77` worktree `FETCH_HEAD` **still
absent**, linked-worktree indexes `070b4ead…` (8e13e77) / `855fec75…` (D) unchanged, both HEADs unchanged,
no `ENGINEERING_equivalence*` root, no marker. No file was created or deleted on the host.

## 1. R2 fixes that are present (verified)

- **M-1 (stale pins) — applied.** §3.1 now records the parent listing with the two new worktrees (host
  listing confirmed: `Agent_paper_B_8e13e77`, `autoresearch_harness_897d83c`, `Agent_paper_B_D_20261117`,
  `ENGINEERING_rehearsal_20261117T014743Z` + four files), the `FETCH_HEAD` before-value **17,593 B /
  `69545606…`** (confirmed on the main clone; 120 lines) and after-value **104 B / `83c64a87…`**, and the
  `.pyc` baseline **65** in the `8e13e77` worktree (confirmed 65; D worktree 72). See MAJOR-1 for the
  remaining *path* problem in that pin.
- **m-6 (interpreter/cwd) — applied.** §3.2 now says "once from the `8e13e77` worktree with the absolute
  frozen-venv path"; the venv path is given in §2 (`/home/dowling/r1_trackp/venvs/trackp-gpu`).
- **m-10 (same-host premise) — applied.** §1 lines 11–13: "**TASL-2 is the portal host**, so a pass is a
  same-host reference reproduction … not a cross-host equivalence claim with TASL-7"; the §3.5 record
  requirement repeats it.
- **B-1 (§3.1 part) — applied.** §3.1 now has "expected after-state **193 / two added lines**
  (`start`/`end`; the reference code `8e13e77` has no `acquired` event — that was added by `08aeaff9`)".
  Correct: `run.py` at `8e13e77` logs only `start`/`end`; the portal reference manifest's `gpu_lease` has
  two entries (`start`, `end`), the TASL-7 run manifest likewise (2 entries), and the whole host lease log
  contains exactly one `acquired` event (the 17 Nov D-code rehearsal). But the other two places of B-1 are
  unchanged — see BLOCKING-1.

## 2. BLOCKING-1 (R2 B-1, residual) — the after-check still requires three lease lines and a `stage`

The leases section is internally contradictory: §3.1 is fixed, but

- §3.3 (lines 64–65): "**After:** … report `max_steps`/patience/`stage` as in the reference config
  (2000/5); **lease log gained exactly three lines**;"
- §3.5 (lines 71–72): "Record `TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md` with: … **lease-log before/after
  + three lines**,"

Both cannot hold for the reference code. `run.py` (`bdec6784…`) `gpu_lease` writes exactly `start` then
`end` (no `acquired`, no `monotonic_s`, no `tasl7_driver`; `acquired` was introduced by `08aeaff9`, 27 Oct,
after the reference run). Confirmed independently on the host: the Oct-26 `trackp e0 kev-0.8b` entries in
the lease log are `start`/`end` pairs with **no** `acquired` event for that job (17 starts / 15 ends — two
interrupted runs), the single `acquired` event in the whole log is the 17 Nov D-code rehearsal, and the
portal reference manifest's `gpu_lease` has two entries. A correct run therefore takes the log
**191 → 193 lines with exactly two added lines** (`start`, `end`, same job "trackp e0 kev-0.8b") and
`manifest.gpu_lease` two entries. As written, a correct run would be flagged by §3.3 or recorded wrongly by
§3.5, i.e. the unit must not be executed as written.

**Exact fix:** §3.3 — replace "report `max_steps`/patience/stage as in the reference config (2000/5);
lease log gained exactly three lines" with "report `max_steps`=2000, `eval_every`=100, `patience`=5,
`batch_size`=8, `protocol`="trackp_e0/v2", `variant`="fresh", `target`="y_soft", `n_test`=1000 (no `stage`
key); lease log gained exactly two lines (`start` then `end`, same job) and `manifest.gpu_lease` has two
entries." §3.5 — replace "lease-log before/after + three lines" with "lease-log before/after + the two
added `start`/`end` lines + after sha". (This also closes R2 **m-1**.)

## 3. MAJOR-1 (new, independent) — the `FETCH_HEAD` before/after pin names two different files

The unit pins `FETCH_HEAD` as one object going **17,593 B / `69545606…` → 104 B / `83c64a87…`, "a rewrite
only"** (§3.1 lines 56–58; §3.5 line 73). That is not what the reference code does when run from the
`8e13e77` worktree:

- `r1/harness.py` at `8e13e77`: `REPO = Path(__file__).resolve().parents[1]`, i.e. with the §3.2 cwd the
  REPO is `/home/dowling/r1_engineering/unitb_rehearsal_20261117/Agent_paper_B_8e13e77`.
- `run.py` `track_x_running()` calls `subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "origin",
  "main"])`; `git fetch` writes `$GIT_DIR/FETCH_HEAD`, and in a linked worktree that is the **per-worktree**
  file. On the host, `git -C <8e13e77> rev-parse --git-path FETCH_HEAD` returns
  `/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_8e13e77/FETCH_HEAD` — **absent today**.
- The 17,593 B / `69545606…` file is the **main clone's** `/home/dowling/Agent_paper_B/.git/FETCH_HEAD`
  (120 lines; the operator's provisioning fetch). The run does not touch it.
- Direct proof of the per-worktree behaviour and of the expected after-content: the D worktree's
  `/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117/FETCH_HEAD` is **104 B / sha
  `83c64a873f2d189b512faff299a657672d80f9d5d98485865e5b5189600d37d7`**, one line
  `26177d82… branch 'main' of https://github.com/dowlingwong/Agent_paper_B` (its own provisioning fetch,
  17:47). So the after-state content `83c64a87…` is right, but it belongs to the `8e13e77` worktree gitdir
  and is a **creation, not a rewrite**; the main-clone file stays 17,593 B / `69545606…`.

As written, an executor recording the pinned path sees no `17,593 → 104` rewrite (false alarm/STOP) or
records the wrong file. Severity MAJOR: same class as R2 M-1 (preflight/after-check pin that would misfire
on a correct run), and it is not fixed by the current text.

**Exact fix:** §3.1 and §3.5 — "main clone `/home/dowling/Agent_paper_B/.git/FETCH_HEAD`: 120 lines /
17,593 B / `69545606…` before and after (provisioning artifact; unchanged); the `8e13e77` worktree's
`/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_8e13e77/FETCH_HEAD`: absent before → one line
104 B / `83c64a87…` after (the lease-gate `git fetch -q origin main`; expected content `26177d82…
branch 'main' of https://github.com/dowlingwong/Agent_paper_B`). No ref move/object download (`origin/main`
= `26177d82…` unchanged); the after-state is a creation in the worktree gitdir, not a rewrite of the
main-clone file; a ref move remains a STOP."

## 4. Remaining MINORs

| ID | R2 item | Finding (still open in `c7d1fa3c…`) | Exact fix |
|---|---|---|---|
| m-1 | stage | §3.3 still requires "`max_steps`/patience/**stage**" and only (2000/5); the `8e13e77` report has no `stage` key | Drop `stage`; assert max_steps 2000, eval_every 100, patience 5, batch_size 8, protocol "trackp_e0/v2", variant "fresh", target "y_soft", n_test 1000 (closed by the BLOCKING-1 fix) |
| m-2 | `manifest.host` | §3.5 says only "host/GPU/driver/UUID"; `manifest.host` does not exist at `8e13e77` (confirmed: portal reference manifest keys have no `host`), and the harness branch will be "HEAD" (detached); the portal `git.paper.dirty=true` vs clean-`8e13e77` `false` delta is not required to be recorded | State: take host/GPU/driver/UUID from `hostname`/`nvidia-smi`, not from `manifest.host`; record harness branch "HEAD" (detached) and the portal-dirty=true vs clean=false delta as descriptive (TASL-7 precedent also used a clean detached `8e13e77` and passed) |
| m-3 | Track X / TASL-7 | §3.1 only mentions the marker/`*.active` check "at run time"; it does not re-check TASL-7 reachability or record the Track X evidence status before starting | Add preflight: re-check TASL-7 reachability (currently unreachable from the Mac: `100.106.74.51:22` → `Operation timed out`, exit 255; the `tasl7` alias does not resolve on TASL-2, so probe from the operator/Mac) — STOP/re-route if recovered; record Track X evidence status from `origin/main:docs/r1/STATUS.md` (newest Track X B1/B2 heading at `26177d82` = "14 November 2026 — Track X B1 `_d` completed normally … marker retired" → gate clear). Current state: `~/r1_locks/trackx_evidence.active` absent |
| m-4 | compare.py | §3.1 says "compare.py at `docs/r1/reports/tasl7_equivalence_20261026/compare.py` (copy into scratch or run from the worktree; check its schema/exit …)"; §3.4 gives a relative-path command. On TASL-2 the `8e13e77` worktree has **neither** compare.py nor the reference report (its `docs/r1/reports/` contains only `trackp_e0v2_dryrun_20261026/` with driver.sh/summarize.py/etc., no `runs/`, and no `tasl7_equivalence_20261026/`); compare.py exists there only in the D worktree. Where the comparator runs, the byte-identical copy, recorded shas/exit code, and schema-vs-miss distinction are not specified | State: run the committed comparator (`bd957c0d…`) in the Mac `ops-tasl-20261116` worktree, where the reference report `7c1be5e9…` and compare.py are committed; copy the TASL-2 report byte-identically (record copy sha before/after, its path, `comparison.json` path/sha and the exit code); pre-check `lora.test` three keys + `head_fit.test`; a schema failure/`KeyError` is its own STOP cause, distinct from a tolerance miss |
| m-5 | result record | §3.5 expanded but still missing: rc; comparison exit code; `manifest.evidence_label=="DRYRUN"`; `data_manifest_sha256` (`b963be2d…`); `head_form=="linear12"`; `manifest.gpu_lease` two entries; stdout/stderr sha and `SHA256SUMS`; disk; authority commit `45fb94cc`/branch; TASL-7 state; portal-dirty/clean delta; exact cwd/interpreter (only "argv/env" is listed) | Add those fields to §3.5 |
| m-7 | `--check-config` | No mention that computing the "loaded config digest" runs repo code (`--check-config` exists) and must be done with `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0` so the preflight does not grow the `.pyc` baseline it pins | Add that instruction to §3.1 (and record `.pyc` 65 before/after the config check) |
| m-8 | Unit B `--load` | No sentence that Unit B's `--load` target (TASL-7 attempt-1 `EVIDENCE/kev-0.8b/final/saved`, absent on TASL-2) is unresolved and that a pass is not Unit B readiness | Add one sentence to §1 |
| m-9 | pre-declaration run-dir | §1 says the pre-declaration is "unchanged from `tasl7_equivalence_20261026/PREDECLARATION.md`" without noting that only the run-dir is superseded by the TASL-2 scratch (values/tolerance are unchanged, committed `4ed7ef92…`) | Add the sentence |
| new-1 | — | The document still titles itself "(revision 2)" (line 1) while it is submitted as revision 3; the bytes carry a partial R2 patch set | Retitle "Unit (revision 3)" and add a one-line change note; re-issue the unit as a coherent revision |
| new-2 | — | §3.1 lists "`r1/scripts/trackp.py`/`run.py`/`exam_run.py`/config file shas" — `run.py`/`exam_run.py` are at `r1/c3/train/`, not `r1/scripts/` (confirmed: `bdec6784…`, `6125b364…` at `r1/c3/train/`) | Spell the exact paths so preflight does not look for `r1/scripts/run.py` |

## 5. What is verified correct (unchanged from R2)

- **Command/config/harness — correct and authority-consistent.** The §2 command is the literal TASL-7
  driver form (`…/tasl7_equivalence_20261026/driver.sh`: `cd` + env + absolute-venv
  `python r1/scripts/trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --run-dir
  <scratch>/kev-0.8b/fresh_soft_lr0.0001`, **no `--steps`/`--stage`**), with the protected env added
  (`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=…`). The config at
  `8e13e77` declares `e0 = {max_steps: 2000, eval_every: 100, patience: 5, batch_size: 8, seed: 0}`, and
  the re-computed loaded digest is **`588869fa…`** — exactly the portal reference manifest's
  `config_sha256` (and the TASL-7 run manifest's). `trackp.py` at `8e13e77` has no `--stage`; the harness
  `897d83c` is the commit recorded by the reference manifest. The run is the pre-declared budget, not D's.
- **"Not a test of D" is clear** (§1 lines 10–11, §3.5): ENGINEERING, not evidence, not counted; the
  host/reference-code reproducibility check, not a test of D; D delivery and Unit B separate.
- **Same-host nature** is now stated in §1 as well as in the record fields: TASL-2 produced the portal
  reference, so a pass is a same-host reference reproduction, not cross-host equivalence with TASL-7.
- **Authority/condition:** `R1-TRACKP-TASL2-HOST` requires the `R1-TASL7-TRACKP` host-equivalence check
  once on TASL-2 before Unit B there, conditional on the rehearsal passing and TASL-7 staying unreachable.
  Rehearsal result `ec98fb18…` = PASSED; TASL-7 still unreachable (Mac `ssh tasl7` → timeout, exit 255).
- **Comparison design:** values `0.922998/1.011556/1.98913e-4` match the reference report
  (`0.9229977303/1.0115558700/1.98913235e-4`); comparator `ABS` 0.05/0.05, `REL` 0.10, exit 0/1; TASL-7
  precedent `0793eddb…` is `equivalent: true` with all three passing; a miss is a STOP, no re-run.
- **R2 M-1 pins:** `.pyc` 65 (D 72), parent-listing description updated, freeze 121 lines `50238e5a…`,
  both worktrees clean at the right HEADs, models present, no marker/`*.active`.

## 6. Host facts (read-only, TASL-2, 2026-11-17 ≈02:09–02:14Z host clock; local PST)

| Fact | Verified value |
|---|---|
| Host | `TASL-2` (zhixu portal), read-only SSH user `dowling` |
| `8e13e77` worktree | `/home/dowling/r1_engineering/unitb_rehearsal_20261117/Agent_paper_B_8e13e77`; detached **`8e13e77cd49532c7ac2e78ad8e5c1ee45401b286`**; `status --porcelain -uall` = 0 lines; linked index `070b4ead…`; `.pyc` **65**; files `trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…`; loaded digest `588869fa…`; no `--stage` |
| Harness worktree | `…/autoresearch_harness_897d83c`; detached **`897d83c8efa364ec2fdd37288241cc42e01d7274`**; `status -uall` = 0 lines; `src/autoresearch` present |
| Main clone / refs | `/home/dowling/Agent_paper_B` on `main` `b5a7aeca…` clean; `worktree list` = main + `8e13e77` + D; `origin/main` = remote `main` = **`26177d82…`** |
| `FETCH_HEAD` | main clone `.git/FETCH_HEAD`: **120 lines / 17,593 B / `69545606c2f5…`**, mtime 2026-11-16 17:58 PST (provisioning); `8e13e77` worktree gitdir `FETCH_HEAD`: **absent** (`git rev-parse --git-path` → `.git/worktrees/Agent_paper_B_8e13e77/FETCH_HEAD`); D worktree gitdir `FETCH_HEAD`: 104 B / `83c64a87…` (one-line `26177d82… branch 'main'`) |
| D worktree (context) | `…/Agent_paper_B_D_20261117`, detached `8662e359…` clean, index `855fec75…`, `.pyc` 72; contains copy of reference report `7c1be5e9…` and compare.py `bd957c0d…` |
| Freeze / venv | `trackp-gpu`: Python 3.12.15 (uv), torch 2.6.0+cu124; freeze **121 lines sha `50238e5a07ca…`** (three copies byte-identical, plus committed `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` identical) |
| Models | base `…/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41` and adapter `…/models/jaredpalmer__kev-0.8b@788ddbdd6571` present |
| GPU / lease | RTX 4090, `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01, 24,564 MiB, 353 MiB / 0 %, 0 compute apps; `~/r1_locks/gpu0.lock` 0 B, no `lsof` holder → free; `~/r1_locks/trackx_evidence.active` absent; no `*.active` in the rehearsal parent |
| Lease log | **191 lines, sha `0a4a14aed5a1…`**; last job = 2026-11-17T01:47:49Z D-code rehearsal (`acquired`/`start`/`end`); exactly **1** `acquired` event in the whole file; Oct-26 reference-code jobs are two-line `start`/`end` pairs |
| Disk | 1.9 T total / 1.4 T used / **374 G available** (80 %) — ≥50 GB |
| Roots | no `ENGINEERING_equivalence*`; scratch root absent; no `p3a_attempt2*` (only 25–26 Oct history under `runs/p0`, `runs/phase2`, as before) |
| TASL-7 | still unreachable from the Mac: `ssh tasl7` → `100.106.74.51:22`, `Operation timed out`, exit 255 (the `tasl7` alias does not resolve on TASL-2 itself) |
| Reference report in `8e13e77` worktree | **absent** (`docs/r1/reports/trackp_e0v2_dryrun_20261026/` has no `runs/`); present in the D worktree and in the Mac `ops-tasl-20261116` worktree at `7c1be5e9…` |

## 7. Verdict

**NOT ACCEPTED — 1 BLOCKING, 1 MAJOR, 10 MINOR.** It may not be executed as written. The choice of path
and the science are sound and the R2 M-1/m-6/m-10 fixes are correctly applied, but the "revision 3" bytes
are a partial patch:
1. **BLOCKING-1** — §3.3 still requires three lease lines (and a `stage`) and §3.5 records three lines,
   contradicting the reference code's two `start`/`end` lines (correct state: 191 → 193, two lines).
2. **MAJOR-1 (new)** — the `17,593 B → 104 B` `FETCH_HEAD` pin conflates the main clone's `.git/FETCH_HEAD`
   with the `8e13e77` worktree's per-worktree `FETCH_HEAD`; a correct run leaves the former unchanged and
   creates the latter (104 B / `83c64a87…`).
3. **MINOR** — m-1 (stage/assertions), m-2 (`manifest.host` provenance/branch/portal-dirty delta), m-3
   (TASL-7 re-check + Track X STATUS.md record), m-4 (compare.py place/copy/schema/exit-code record), m-5
   (record fields), m-7 (`--check-config` bytecode), m-8 (Unit B `--load` gap), m-9 (pre-declaration run-dir
   note), plus the revision-label and file-path precision items.

After BLOCKING-1 and MAJOR-1 are fixed (and the MINORs), a short re-confirmation of the re-issued bytes is
sufficient; the unit may then be executed **once, as written**, on TASL-2 with the recorded lease/fetch
side effects treated as expected.

**If accepted after the fixes, the result record (`TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md`) must
contain:** unit + exact argv/env (`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=<harness worktree>`, the
absolute interpreter and cwd), rc, wall time (expected ≈25 min); `8e13e77` HEAD `8e13e77cd495…` + file shas
(`trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…`) and loaded config
digest `588869fa…`; `897d83c` harness HEAD `897d83c8efa3…`/clean (branch "HEAD", detached); freeze 121
lines `50238e5a…`; host/GPU/driver/UUID (`GPU-4d623e76-…`, driver 535.309.01) from `nvidia-smi`; the
scratch root and `<run-dir>/report.json` + `manifest.json` paths/sha256; `manifest.evidence_label ==
"DRYRUN"`, `manifest.data_manifest_sha256` = `b963be2d…`, `manifest.gpu_lease` two entries; report keys
(`max_steps=2000`, `eval_every=100`, `patience=5`, `batch_size=8`, `protocol="trackp_e0/v2"`,
`variant="fresh"`, `target="y_soft"`, `n_test=1000`, `lora.test` three keys, `head_fit.test` present); lease
log before/after (191 → 193 lines, sha `0a4a14ae…` before, two added `start`/`end` lines, job
"trackp e0 kev-0.8b"); **both** `FETCH_HEAD` paths before/after (main clone 17,593 B / `69545606…`
unchanged; `8e13e77` worktree gitdir absent → 104 B / `83c64a87…`; `origin/main` = `26177d82…`; no ref
move/object download); tracked-file/`.pyc`(65)/linked-worktree-index/worktree-list/`nvidia-smi`
before/after; disk; stdout/stderr sha and `SHA256SUMS`; the recorded `compare.py` invocation (from the Mac
worktree against a byte-identical report copy) + reference report `7c1be5e9…` + comparator `bd957c0d…` +
copy sha + exit code; `comparison.json` (path/sha) with `equivalent: true`, the three criteria and
descriptive fields; the explicit statements that this is ENGINEERING (never counted, no attempt-2/evidence
root), that it is a same-host reference reproduction on the portal host and **not** a test of D (D delivery
and Unit B separate), and that the table host will be disclosed as TASL-2 if Unit B runs there; the
TASL-7-reachability state; and that a pass does not resolve Unit B's `--load` prerequisite. If the
comparison misses: preserve, report, STOP — no re-run, no configuration substitution.
