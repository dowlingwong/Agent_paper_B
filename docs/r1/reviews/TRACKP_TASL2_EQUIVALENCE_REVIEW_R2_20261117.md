# Review R2 — Track P host-equivalence check on TASL-2, literal reference-code path (ENGINEERING; 17 November 2026)

**Status: NOT ACCEPTED — 1 BLOCKING, 1 MAJOR, 10 MINOR.** Revision 2 takes the round-1 reviewer's
alternative: the **literal** TASL-7-style check with **reference code `8e13e77` + harness `897d83c`**, the
exact driver command with the pre-declared 2,000-step / patience-5 config, the protected env, and a real
"Before" preflight. That is the right reading of `R1-TRACKP-TASL2-HOST` ("run the host-equivalence check
that `R1-TASL7-TRACKP` required, once, on TASL-2"), and it resolves R1's two BLOCKINGs: I re-verified that
`cmd_e0` at `8e13e77` has **no `--stage`**, that the loaded config digests to the portal/TASL-7
`config_sha256` **`588869fa…`** and declares `e0 = {max_steps: 2000, eval_every: 100, patience: 5,
batch_size: 8, seed: 0}`, and that the command is byte-for-byte the TASL-7 driver form (no `--steps`), so it
runs the pre-declared budget, not D's 6,000/10. The env fix (R1 MAJOR-1) and the preflight (R1 MAJOR-2) are
present too.
What still blocks a literal execution is a **wrong premise carried over from the D-code units**: the
reference `8e13e77` lease gate writes only **`start`/`end`** — the `acquired` event was introduced by
`08aeaff9` ("Guard P.3a execution and GPU lease budget", 27 Oct) **after** the reference run — so a correct
run takes the TASL-2 lease log **191 → 193 lines with two added lines**, not the unit's "194 / three added
lines (acquired/start/end)", and §3.3's "require … lease log gained exactly three lines" cannot hold. Two
more pins are stale against the host as provisioned for this run: the `.pyc` baseline is **65** in the
`8e13e77` worktree (72 is the D worktree's), and the pinned `FETCH_HEAD` before-state (104 B /
`83c64a87…`) was superseded by the operator's provisioning fetch (**now 17,593 B / `69545606…`**); the
expected after-state (104 B / `83c64a87…`, rewrite only, no ref move) remains right. The comparison design,
tolerance, reference values, authority and scope are sound; this is bookkeeping/preflight, not a science
defect. **The unit may not be executed as written.** Review only: the unit was **not** executed (not even
partially), **no host write**, **no commit/push**, **no GPU command**; read-only SSH to TASL-2
(`ssh portal_zhixu`, user `dowling`) was used for host facts. The only workspace change made by this review
is this uncommitted review file.

## 0. Canonical bytes, authority and method

| Object | sha256 / lines | Where / state |
|---|---|---|
| **Unit under review (rev 2)** | `e46123aef038c0f0c62427d82b110aeae6dcba54662ec5fffcf67b7a9cb8c2e9`, **81 lines** | `docs/r1/proposals/TRACKP_TASL2_EQUIVALENCE_20261117.md`, worktree `ops-tasl-20261116`; **uncommitted-untracked** (`??`) — matches the canonical value given. Unchanged across the review (mtime 2026-11-17T02:57:58+0100) |
| Round-1 review | `c14cbb391b7d3d07285a70135f1d810bc8a77ced96f2242abf2d5946e2f52287`, 236 lines | `docs/r1/reviews/TRACKP_TASL2_EQUIVALENCE_REVIEW_20261117.md`; uncommitted-untracked |
| Authority `R1-TRACKP-TASL2-HOST` | commit `45fb94cc8bfe9aafea8d57b45aaf06d19a3e0a44` (17 Nov 2026, 02:41 +0100) | Row at `docs/r1/PLAN.md:1275`; on remote branch `origin/author-decisions-20261117b`, **not** on `origin/main` `26177d82…` |
| `R1-TASL2-REHEARSAL-SCOPE` | commit `33c823516ad5c9c879df432fe958be8d57003a29` | same branch |
| Rehearsal result (passed) | `ec98fb18c7c630cbec4baacb8f3c6f374db5160d71f3e75c4007c16fa7bf62a9`, 44 lines | `docs/r1/reports/TASL2_UNITB_REHEARSAL_RESULT_20261117.md` ("RESULT: PASSED") |
| Pre-declaration (reused) | `4ed7ef92816c6160c0e144b249bd39c309f8ddd0faa1693e32aeceb7848fd726`, 33 lines | `docs/r1/reports/tasl7_equivalence_20261026/PREDECLARATION.md` (committed) |
| Comparator | `bd957c0d3e984b4ec9e27ef090d29580654cfef91d73174bf05a615cd4bf6084`, 37 lines | `…/tasl7_equivalence_20261026/compare.py` (committed, unmodified) |
| TASL-7 comparison (precedent) | `0793eddba25b675f49a40ec5670dfb9550e2f1b362b3167ff09a92e01c505b76`, 117 lines; `equivalent: true`, all three criteria pass | `…/tasl7_equivalence_20261026/comparison.json` |
| Portal reference report | `7c1be5e98fc896074aae33ec301263c3b02973c02a1c387130eb3f45c21d41e0` | `docs/r1/reports/trackp_e0v2_dryrun_20261026/runs/kev-0.8b/fresh_soft_lr0.0001/report.json` |
| Reference code `8e13e77` | `8e13e77cd49532c7ac2e78ad8e5c1ee45401b286` (26 Oct 2026) | On TASL-2: clean detached worktree (see §5); files `trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…` / loaded digest **`588869fa…`** |
| Harness `897d83c` | `897d83c8efa364ec2fdd37288241cc42e01d7274` | On TASL-2: clean detached worktree; portal reference manifest and TASL-7 run manifest both record `897d83c…` |

Method: local reads of the unit, round-1 review, authority, pre-declaration, comparator, TASL-7 comparison,
portal reference report/manifest, TASL-7 run report/manifest, and `git show` of `8e13e77` / `8662e359` /
`45fb94cc` in the local object store; plus read-only SSH to TASL-2 on **2026-11-17, ≈02:00–02:07Z** (host
clock; host local = PST) using `date`, `uname`, `hostname`, `ls`, `find`, `stat`/`ls -l`, the
mode/size/mtime probes below, `cat` of small files, `sha256sum`, `wc`, `df`, `git rev-parse`/`status`/
`worktree list`/`ls-remote` reads, one `flock -n` probe, `nvidia-smi` query reads, and `tail`/`grep`/`head`
reads of the lease log. No unit child run, no training code, no `compare.py` execution, no GPU compute
command, no commit/push, no host write that changed any recorded file (see integrity note below). The
operator was provisioning the two new worktrees while this review ran; at the last check
(2026-11-17T02:05:51Z host) both were present and clean at the right HEADs — if the operator re-creates
them, re-verify.

Integrity note: the SSH reads touched no repository, venv, lease-log, git-ref, scratch-root or GPU state.
The linked-worktree indexes are byte-identical before/after the review (D `855fec75…`, mtime 00:09:05Z;
`8e13e77` `070b4ead…`, mtime 02:00:38Z; main `20ed4f05…`, mtime 31 Oct), the lease log is unchanged
(191 lines / `0a4a14ae…`), and `FETCH_HEAD` is unchanged (17,593 B / `69545606…`) — so the plain
`git status` reads did not opportunistically rewrite an index. The one `flock -n` probe (same as round 1)
opened the existing lock file only to take/release the advisory lock (FREE). No file was created or deleted
on the host.

## 1. Authority, scope and the choice of path — correct

1. **The authority is quoted correctly.** `R1-TRACKP-TASL2-HOST` (commit `45fb94cc`, row `PLAN.md:1275`):
   Track P evidence tables may be produced on TASL-2 or TASL-7 (both RTX 4090), one host per table with the
   host disclosed; if the TASL-2 rehearsal passes and TASL-7 is still unreachable, Unit B runs on TASL-2,
   and **before running there, the host-equivalence check that `R1-TASL7-TRACKP` required is done once on
   TASL-2 (ENGINEERING)**, with the rehearsal scratch never counted. `R1-TASL7-TRACKP` defines that check as
   "a host-equivalence check (one E0 v2 DRYRUN reproduced)". The literal `8e13e77` re-run is exactly "one
   E0 v2 DRYRUN reproduced", so this is the right reading and the alternative the round-1 review offered.
   `R1-TASL2-REHEARSAL-SCOPE` passed (rehearsal result: PASSED), and TASL-7 is still unreachable
   (verified: `ssh tasl7` → `100.106.74.51:22`, `Operation timed out`, exit 255).
2. **"Not a test of D" is clearly recorded** (lines 10–11, 67–68): ENGINEERING, not evidence, not counted;
   the host/reference-code reproducibility check, **not** a test of D; D delivery and Unit B are separate.
   The literal `8e13e77` run cannot test D and the unit does not claim it does.
3. **Same-host nature is recorded in the result-record requirement** (§3.5: "TASL-2 is the portal host
   (same-host reference reproduction)") and the table-host disclosure if Unit B runs there. Correct: TASL-2
   produced the portal reference, so a pass is a same-host reference reproduction, **not** cross-host
   equivalence between TASL-2 and TASL-7; its value is that the pinned environment reproduces the reference
   on the exact host where Unit B would run. This is what the authority asks for (MINOR-10 suggests also
   saying it in the §1 premise, not only in the record fields).
4. **Scope gap not resolved by this unit (R1 MINOR-8):** Unit B's `--load` targets attempt-1
   `EVIDENCE/kev-0.8b/final/saved`, a TASL-7 artifact absent on TASL-2. This unit does not resolve it; a
   pass must not be read as Unit B readiness. One sentence should say so (MINOR-8).

## 2. Command / environment — the R1 BLOCKINGs are resolved

**Verified correct (local code reads + host):**

- **No wrong budget (R1 BLOCKING-1 resolved).** `r1/scripts/trackp.py` at `8e13e77` (`9959a106…`) has no
  `--stage` argument at all, and `cmd_e0` passes `max_steps=args.steps or e0c["max_steps"]`,
  `eval_every=args.eval_every or e0c["eval_every"]`, `patience=e0c["patience"]`,
  `batch_size=e0c["batch_size"]`, `seed=args.seed` to `X.e0_v2`. The config at `8e13e77`
  (`r1/scripts/configs/trackp_portal.json`, file sha `10ead2a5…`) declares
  `e0 = {protocol: trackp_e0/v2, max_steps: 2000, eval_every: 100, patience: 5, batch_size: 8, seed: 0}`;
  re-computing the loaded digest (`sha256(json.dumps(cfg, sort_keys=True))`) gives
  **`588869fa8e721eec2005607dc25f6f46229aa0960bd3f64dbf5155323094f4b9`** — exactly the portal reference
  and TASL-7 `config_sha256`; placeholders `[]`. So the §2 command (`e0 --base kev-0.8b --evidence DRYRUN
  --variant fresh --lr 0.0001 --run-dir <scratch>/kev-0.8b/fresh_soft_lr0.0001`, no `--steps`/`--stage`)
  runs the pre-declared 2,000-step / patience-5 schedule, as the TASL-7 driver did.
- **No changed e0 path (R1 BLOCKING-2 resolved).** At `8e13e77`, `e0_v2` uses `fit_head_on_states` (AdamW
  on the model's device, best-restored) and trains LoRA from the fitted head — the reference behaviour;
  none of D's `R1-E0-BUDGET`/`R1-E0-HEADFIT`/fresh-head changes exist here. The unit's "not a test of D"
  premise is therefore truthful.
- **Env fixed (R1 MAJOR-1 resolved):** §2 carries `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=…` with the
  frozen venv. `GIT_OPTIONAL_LOCKS=0` matters: the run's `run_manifest` calls `git_commit()`
  (`git status --porcelain -uno`) twice, and `PYTHONDONTWRITEBYTECODE=1` prevents the imports from writing
  `.pyc` (baseline 65 in the `8e13e77` worktree).
- **Code/environment pins verified:** `8e13e77` clean detached worktree; harness `897d83c` clean detached
  worktree with `src/` present; frozen venv `/home/dowling/r1_trackp/venvs/trackp-gpu` = Python 3.12.15
  (uv) / torch 2.6.0+cu124; freeze **121 lines sha `50238e5a…`** (three identical copies in the rehearsal
  dir — `now.sorted`, `pin.sorted`, `venv_freeze_now.txt` — and the committed
  `pip_freeze_trackp-gpu.txt` inside the `8e13e77` worktree, all byte-identical); the config's two model
  dirs (`Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41`, `jaredpalmer__kev-0.8b@788ddbdd6571`) are present.
  `AR_HARNESS_ROOT` pointing at the clean `897d83c` worktree is a stricter, faithful pin of the reference
  harness commit.
- The run-dir is under the named ENGINEERING scratch root (never an attempt-2/evidence root; absent today);
  the scratch parent is `…/unitb_rehearsal_20261117/`, and the run uses the ordinary GPU lease.
- Minor imprecisions: the unit says "python" without the absolute interpreter path and without stating the
  required `cd` into the `8e13e77` worktree (MINOR-6); `manifest.host` does not exist at `8e13e77` and the
  report has no `stage` key (MINOR-1/MINOR-2); the preflight `--check-config` must itself run with
  `PYTHONDONTWRITEBYTECODE=1` (MINOR-7).

## 3. Preflight / after-check — right shape; one wrong side-effect premise and two stale pins

**Verified correct against the host** (§5): both worktrees present, clean, at the right HEADs; freeze,
models, config digest; GPU idle; lock free; no marker/`*.active`, no `trackp-evidence` helper; disk 374 G;
lease log **191 lines / sha `0a4a14ae…`**; remote main = local `origin/main` = `26177d82…`; no
`ENGINEERING_equivalence*` and no `p3a_attempt2*` root; TASL-7 unreachable.

- **BLOCKING-1 — the expected lease-log after-state is the D-code one, not the reference code's.**
  `run.py` at `8e13e77` (`bdec6784…`) `gpu_lease` logs only `start` and `end` (lines ~177/186); the
  `acquired` event (with `monotonic_s`/`pending checks`) was added by `08aeaff9` on 27 Oct, **after** the
  reference run, and D (`8662e359`) also logs a `tasl7_driver` field the reference does not. Corroborated on
  the host: the whole lease log has **one** `acquired` event (the 17 Nov D-code rehearsal at 01:47Z), and the
  Oct-26 reference-code jobs are two-line `start`/`end` pairs; the reference code's own manifest in the
  TASL-7 run has `gpu_lease` = two entries (start/end). A correct run therefore takes the log **191 → 193
  lines with exactly two added lines** (`start`, then `end`, same `job` "trackp e0 kev-0.8b"; no
  `acquired`, no `monotonic_s`, no `tasl7_driver`) and `manifest.gpu_lease` two entries. As written,
  §3.1 ("expected after-state 194 / three added lines"), §3.3 ("require … lease log gained exactly three
  lines") and §3.5 (record "three lines") cannot hold — a correct run would either be flagged as a host
  anomaly or require an unrecorded deviation, i.e. the unit should not be executed as written. The
  comparison science is unaffected; the fix is to replace "194 / three" with "193 / two (`start`,`end`)" in
  all three places and record the two added lines + the after sha.
- **MAJOR-1 — three preflight pins are acceptance-time D-worktree values, stale for the `8e13e77` run.**
  (a) `FETCH_HEAD`: the unit pins "exists, 104 B `83c64a87…`", but the operator's provisioning fetch
  (2026-11-17T01:58Z, needed to materialise `8e13e77`/`897d83c`) left **17,593 B / `69545606…`** with the
  first line `26177d82… branch 'main'`; the expected after-state **is** still 104 B / `83c64a87…` (the
  lease-gate `git fetch origin main` writes that one line; I reconstructed it from the remote main and
  hashed it) — but the before-value must be re-captured at preflight. (b) `.pyc`: the pinned 72 is the D
  worktree's count; the `8e13e77` worktree has **65**. (c) the scratch-parent description ("it holds the D
  worktree, the rehearsal scratch and four pre-existing files") is stale — it now also holds the
  `8e13e77` and harness worktrees. Fix: treat these as "record what preflight finds", pin the
  after-state, and include the actual listing. A ref move or object download from the lease-gate fetch
  remains a real STOP (remote main is still `26177d82…`, so none is expected).
- The rest of the after-list is right: rc 0, report/manifest exist with sha256, `max_steps`=2000 /
  `patience`=5 (see MINOR-1 on `stage`), `FETCH_HEAD` rewrite only, no tracked/`.pyc`/worktree changes,
  lease released, GPU idle, wall time ≈25 min (TASL-7: 25.4 min).

## 4. Comparison / tolerance — correct

| Item | Verified |
|---|---|
| `lora.test.width_slope_vs_label` portal 0.922998, abs Δ ≤ 0.05 | reference report `0.9229977302910213`; `compare.py` `ABS` 0.05 |
| `lora.test.mean_slope` portal 1.011556, abs Δ ≤ 0.05 | `1.0115558700330238`; `ABS` 0.05 |
| `lora.test.rps` portal 1.98913e-4, relative ≤ 10 % | `1.9891323497951143e-4`; `REL` 0.10 |
| All three must hold; a miss is a STOP for the author, no re-run/substitution | pre-declaration + unit lines 25–26; comparator exit 0 = equivalent, 1 = miss |
| Reference values, comparator bytes, TASL-7 precedent | report `7c1be5e9…`; `compare.py` `bd957c0d…`; TASL-7 `comparison.json` `equivalent: true`, all three pass |
| `head_fit`/`lora.test` blocks present in the reference-code report | yes (and in the TASL-7 run report); `compare.py` indexes them unconditionally |

Gaps (MINOR-4): the unit does not say where `compare.py` runs or that the TASL-2 report must be copied back
byte-identically (record copy sha, reference path/sha, comparator sha, `comparison.json` path/sha, the exit
code); and it should pre-check `lora.test` (three keys) + `head_fit.test` before invoking the comparator, so
a `KeyError`/schema failure is recorded as its own STOP cause rather than read as a tolerance miss.

## 5. Host facts (read-only, TASL-2, 2026-11-17 ≈02:00–02:07Z host clock; local PST)

| Fact required | Verified value |
|---|---|
| Host | TASL-2 (zhixu portal), Ubuntu kernel 6.8.0-149-generic; read-only SSH user `dowling` |
| `8e13e77` worktree | `/home/dowling/r1_engineering/unitb_rehearsal_20261117/Agent_paper_B_8e13e77`; detached **`8e13e77cd49532c7ac2e78ad8e5c1ee45401b286`**, `status -uall` = 0 lines; linked gitdir `…/Agent_paper_B/.git/worktrees/Agent_paper_B_8e13e77`, index `070b4ead…`; `.pyc` **65**; files `trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config `10ead2a5…` (loaded digest `588869fa…`); committed freeze 121 lines `50238e5a…` |
| Harness worktree | `…/unitb_rehearsal_20261117/autoresearch_harness_897d83c`; detached **`897d83c8efa364ec2fdd37288241cc42e01d7274`**, `status -uall` = 0 lines; `src/` present (main harness clone `/home/dowling/autoresearch_harness` is at `3c80b53…`, so the `897d83c` pin is the worktree — correct) |
| Main clone / refs | `/home/dowling/Agent_paper_B` on `main` at `b5a7aeca…` clean; `worktree list` = main + `8e13e77` + D; `origin/main` = `26177d82…`; `git ls-remote origin main` = **`26177d82…`** (network read; remote unchanged) |
| `FETCH_HEAD` | currently **17,593 B, sha `69545606c2f5…`**, mtime 2026-11-16 17:58 PST = 2026-11-17T01:58Z (operator provisioning fetch; first line `26177d82… branch 'main'`). Expected after the lease-gate fetch: **104 B, sha `83c64a87…`** (reconstructed: `26177d82…\t\tbranch 'main' of https://github.com/dowlingwong/Agent_paper_B\n`); rewrite only, no ref move |
| D worktree (context) | `…/Agent_paper_B_D_20261117`, detached `8662e359…` clean, index `855fec75…`, `.pyc` 72 |
| Freeze / venv | `trackp-gpu`: Python 3.12.15 (uv), torch 2.6.0+cu124; freeze **121 lines sha `50238e5a07ca…`**, byte-identical to the committed `pip_freeze_trackp-gpu.txt` and to `now.sorted`/`pin.sorted`/`venv_freeze_now.txt` |
| Models | base `…/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41` and adapter `…/models/jaredpalmer__kev-0.8b@788ddbdd6571` present |
| GPU / lease | RTX 4090, `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver 535.309.01, 24,564 MiB, 353 MiB / 0 %, 0 compute apps; `gpu0.lock` present, `flock -n` **FREE**; no `*.active`, no `~/r1_locks/bin/trackp-evidence` |
| Lease log | **191 lines, sha `0a4a14aed5a1…`**; last job = 2026-11-17T01:47:49Z rehearsal (`acquired`/`start`/`end`); only **1** `acquired` event in the whole file; Oct-26 `trackp e0 kev-0.8b` jobs are `start`/`end` pairs |
| Disk | 1,877 G total / 1,407 G used / **374 G available** (80 %) — ≥50 GB |
| Roots | no `ENGINEERING_equivalence*`; no `p3a_attempt2*` (the old `runs/p0/*attempt2*` and `runs/phase2/gpu_smoke_attempt2.json` are 25–26 Oct history, unrelated, as round 1 noted); scratch root absent |
| TASL-7 | still unreachable: `ssh tasl7` (`100.106.74.51:22`) → `Operation timed out` (exit 255) |

## 6. Findings and exact fixes

| ID | Severity | Finding | Exact fix |
|---|---|---|---|
| **B-1** | BLOCKING | The reference code `8e13e77` lease gate writes only `start`/`end`; the `acquired` event was added by `08aeaff9` (27 Oct, after the reference) and D also adds `tasl7_driver`. A correct run gives **193 lines / two added lines** and `manifest.gpu_lease` two entries, not "194 / three added lines"; §3.3's "require … exactly three lines" cannot hold, and §3.5 repeats "three lines" | In §3.1 replace "expected after-state `194 / three added lines`" with "**193 / exactly two added lines** (`start`, `end`; no `acquired`/`monotonic_s`/`tasl7_driver`)"; in §3.3 replace "lease log gained exactly three lines" with "gained exactly two lines (`start` then `end`, same job) and `manifest.gpu_lease` has two entries"; in §3.5 replace "+ three lines" with "+ two lines"; record the two lines and the after sha |
| **M-1** | MAJOR | Three preflight pins are acceptance-time D-worktree values and are stale for this run: (a) `FETCH_HEAD` is now 17,593 B / `69545606…` (the provisioning fetch), not 104 B / `83c64a87…`; (b) `.pyc` = 65 in the `8e13e77` worktree, not 72 (D's); (c) the scratch-parent description omits the `8e13e77` and harness worktrees | Re-capture at preflight: `FETCH_HEAD` before = what is found (today 17,593 B / `69545606…`), expected after = **104 B / `83c64a87…`** (lease-gate fetch of main; remote main = local `26177d82…` — rewrite only; a ref move/object download remains a STOP); `.pyc` baseline = actual (65 today) in the `8e13e77` worktree; parent listing = the two new worktrees + D + rehearsal scratch + the four files. Treat discrepancies from the acceptance snapshot as informational (re-pinned), not automatic STOPs |
| m-1 | MINOR | §3.3 requires report "`max_steps`/patience/stage"; the `8e13e77` report has **no `stage` key** (that is a D config/report field) | Assert `max_steps`=2000, `eval_every`=100, `patience`=5, `batch_size`=8, `protocol`="trackp_e0/v2", `variant`="fresh", `target`="y_soft", `n_test`=1000; drop `stage` |
| m-2 | MINOR | `manifest.host` does not exist at `8e13e77` (`run_manifest` predates `d3bed8b4` "run manifests record host and GPU"); the harness branch will read `"HEAD"` (detached), and `git.paper.dirty` will be `false` versus the portal reference's `true` | Record host/GPU/driver/UUID from `nvidia-smi`/`hostname`, not from `manifest.host`; record the harness branch and the portal-dirty=true vs clean-`8e13e77` delta as descriptive (the TASL-7 precedent also used a clean detached `8e13e77` and passed) |
| m-3 | MINOR | The authority's TASL-2 route is conditional on TASL-7 being unreachable; no immediate re-check is in the preflight, and the lease gate's Track X status gate is not recorded | Preflight: re-check TASL-7 reachability (STOP/re-route if recovered) and record the Track X evidence status (`origin/main:docs/r1/STATUS.md`; the lease gate STOPS if a Track X phase is running) before starting |
| m-4 | MINOR | `compare.py` location/order/copy, exit code and report-schema check are not specified | State: run the committed comparator (`bd957c0d…`) in the Mac worktree `ops-tasl-20261116` against a byte-identical copy of the TASL-2 report (record the copy sha before/after), reference path/sha `7c1be5e9…`; record `comparison.json` path/sha and the exit code; pre-check `lora.test` (three keys) + `head_fit.test`; a schema failure/`KeyError` is its own STOP cause, distinct from a tolerance miss |
| m-5 | MINOR | Result-record fields incomplete | Add: rc; comparison exit code; `manifest.evidence_label == "DRYRUN"`; `data_manifest_sha256` (expected `b963be2d…`); `head_form == "linear12"`; `manifest.gpu_lease` two entries; stdout/stderr sha and `SHA256SUMS`; disk; authority commit `45fb94cc` (branch `author-decisions-20261117b`, not main); TASL-7 state; the portal-dirty/clean delta; the exact argv/env + cwd/interpreter |
| m-6 | MINOR | The command says "python" without the interpreter path or cwd | State `cd` into the `8e13e77` worktree and use `/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python` |
| m-7 | MINOR | Computing the loaded config digest (`--check-config`) executes repo code; without `PYTHONDONTWRITEBYTECODE=1` it would grow the `.pyc` baseline it is meant to pin | Run preflight repo-code checks with `PYTHONDONTWRITEBYTECODE=1` (and `GIT_OPTIONAL_LOCKS=0`), and record the `.pyc` baseline before/after such checks |
| m-8 | MINOR | Unit B's `--load` prerequisite (TASL-7 attempt-1 `EVIDENCE/kev-0.8b/final/saved` absent on TASL-2) is unaddressed | Add one sentence: this unit does not resolve that gap and a pass is not Unit B readiness (separate author-approved route needed) |
| m-9 | MINOR | The reused pre-declaration's command row names the TASL-7 scratch; the unit says "unchanged" | State that only the run-dir is superseded by the TASL-2 scratch; the reference values/tolerance (committed pre-declaration `4ed7ef92…`) are unchanged |
| m-10 | MINOR | The same-host nature appears only in the result-record requirement | Add to §1: TASL-2 produced the portal reference, so this is a same-host reference reproduction (not cross-host equivalence with TASL-7), and not a test of D (D delivery/Unit B separate) |

## 7. Verdict

**NOT ACCEPTED — 1 BLOCKING, 1 MAJOR, 10 MINOR.** It may not be executed as written. The version-2 choice
of path is right — the literal `8e13e77`/`897d83c` re-run is exactly the check `R1-TRACKP-TASL2-HOST`
requires — and R1's BLOCKING-1 (wrong budget), BLOCKING-2 (false "D e0 unchanged" premise), MAJOR-1 (env)
and MAJOR-2 (no preflight) are substantively fixed and verified. What remains is bookkeeping that would
otherwise misfire: the lease-log after-state is the D code's, not the reference code's, and three
acceptance-time pins are stale against the host as provisioned for this run. After **B-1** and **M-1** are
fixed (and preferably the MINORs), a short confirmation round is sufficient; the bytes should then be
re-checked and the unit may be executed **once, as written**, on TASL-2, with the recorded lease/fetch side
effects treated as expected.

**If accepted after the fixes, the result record (`TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md`) must
contain:** unit + exact argv/env (`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=. AR_HARNESS_ROOT=<harness worktree>`, the
absolute interpreter and cwd), rc, wall time (no wall STOP; expected ≈25 min); `8e13e77` HEAD
`8e13e77cd495…` + file shas (`trackp.py 9959a106…`, `run.py bdec6784…`, `exam_run.py 6125b364…`, config
`10ead2a5…`) and loaded config digest `588869fa…`; `897d83c` harness HEAD `897d83c8efa3…`/clean (branch
"HEAD", detached) and the `AR_HARNESS_ROOT` path; freeze 121 lines `50238e5a…`; host/GPU/driver/UUID
(`GPU-4d623e76-…`, driver 535.309.01) from `nvidia-smi`; the scratch root and `<run-dir>/report.json` +
`manifest.json` paths/sha256; `manifest.evidence_label == "DRYRUN"`, `manifest.data_manifest_sha256` =
`b963be2d…`, `manifest.gpu_lease` two entries; report keys (`max_steps=2000`, `eval_every=100`,
`patience=5`, `batch_size=8`, `protocol="trackp_e0/v2"`, `variant="fresh"`, `target="y_soft"`, `lora.test`
three keys, `head_fit.test` present); lease log before/after (191 → 193 lines, sha `0a4a14ae…` before, the
two added `start`/`end` lines, `job` "trackp e0 kev-0.8b"); `FETCH_HEAD`/ref before/after (before =
provisioning value, after 104 B / `83c64a87…`, rewrite only; `origin/main` = `26177d82…` unchanged; no ref
move/object download); tracked-file/`.pyc`(65)/linked-worktree-index/worktree-list/`nvidia-smi` before/after;
disk; stdout/stderr sha and `SHA256SUMS`; the recorded `compare.py` invocation + reference report
`7c1be5e9…` + comparator `bd957c0d…` + exit code; `comparison.json` (path/sha) with `equivalent: true`, the
three criteria and descriptive fields; the explicit statements that this is ENGINEERING (never counted, no
attempt-2/evidence root), that it is a same-host reference reproduction on the portal host and **not** a
test of D (D delivery and Unit B separate), and that the table host will be disclosed as TASL-2 if Unit B
runs there; the TASL-7-reachability state; and that a pass does not resolve Unit B's `--load` prerequisite.
If the comparison misses: preserve, report, STOP — no re-run, no configuration substitution.
