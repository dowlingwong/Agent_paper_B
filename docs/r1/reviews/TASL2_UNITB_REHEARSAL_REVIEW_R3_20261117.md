# Independent review (round 3) — TASL-2 ENGINEERING host/env/CLI readiness rehearsal, revision 3 (17 November 2026)

**Status: NOT ACCEPTED — 1 BLOCKING (the mandated kev-tiny report values cannot exist on D; step 3 aborts with
an uncaught `ContextOverflow`), residual BLOCKING-1 (the round-2 baseline set is narrowed but still not complete
for the unit's own "any file outside the scratch root changes → STOP"), 2 MAJOR, 9 MINOR.**

Fresh independent reviewer (round 3; no part in drafting the unit, the Track P code, the attempt-2 plan or the
TASL-2 worktree; rounds 1–2 were other reviewers). **Review only: the unit was not executed, no host write, no
commit/push, no GPU.** Read-only SSH to TASL-2 (`portal_zhixu`, user `dowling`) was used for host facts; the only
workspace change is this uncommitted review file.

Revision 3 answers the *substance* of most round-2 findings — §3b now lists the baselines, the guard run dir is
distinct, a wall-time bound and the result-record/no-GPU fields exist — **but the report values it makes mandatory
(and the "clean" outcome they imply) are not what the delivered bytes `8662e359` do on the kev tiny path.** The
kev `PointerWrapper` encodes strictly at a 1,024-token state limit, and the CLI's bare `probes --tiny` reaches the
A3 v1 `(0, 2000, 8000)` path, whose 2k/8k rows raise an uncaught `ContextOverflow` before any `report.json`/
`manifest.json` is written. Round 2 asserted the opposite (an inference from a test that is skipped locally and
failed in the only committed GPU-venv run), and revision 3 copied that assertion into §3b.

## 0. Method and limits

- Canonical unit bytes were read from the round-3 worktree path, hashed and line-counted (§1). The round-2 review
  was read first (`docs/r1/reviews/TASL2_UNITB_REHEARSAL_REVIEW_R2_20261117.md`, sha `428286d0…`, 346 lines).
- The D code was read at the delivered commit `8662e35991659f7a661fb7ed6be4980791d302f3` from the repository object
  store (`git show 8662e359:…`) and from the committed reports at that commit; all hashes below were recomputed.
- TASL-2 facts were re-verified **read-only** with `ssh portal_zhixu '…'` on **2026-11-17T00:32–00:40Z**:
  `hostname`, `whoami`, `date -u`, `uptime`, `nvidia-smi --query-gpu/--query-compute-apps`, `df`, `ls`/`stat`/
  `find`/`sha256sum`/`wc`/`cat`/`du`, and `git --no-optional-locks` with `GIT_OPTIONAL_LOCKS=0`.
- **No host write**: no Python was executed on TASL-2, `torch.cuda.is_available()` was not invoked there, no
  directory/file was created, moved or deleted, and no process/session/lock was signalled. The `flock` probe was
  not run (the unit's own baseline; §3b(g)).
- No evidence claim is made or evaluated here; TASL-2 stays a non-evidence host and TASL-7 stays the evidence host.

## 1. Canonical bytes, revision identity and authority

- Unit `docs/r1/proposals/TASL2_UNITB_REHEARSAL_20261117.md`: **sha256
  `13f67b8da5e119c5a74c9df10038eabdc2b4a4af98988da663f9a503ec4affcb`, 101 lines** — matches the given canonical
  bytes exactly. The reviewed bytes are the **uncommitted working-tree** version over worktree HEAD `44b52368`
  (whose file is the 60-line round-1 bytes `a6a2cba3…`; `git diff --numstat` = `101 60`). Committing the exact
  101-line bytes unchanged (and recording `13f67b8d…`) would be required after the fixes below; any byte change
  voids this review.
- **The bytes are still self-labelled "revision 2"** (title line 1) and still describe "Revision 2 answers the
  round-1 review" (lines 4–9); there is no revision-3 identity or canonical-hash statement. See MINOR R3-1.
- `R1-TASL2-UNITB-REHEARSAL` is on **`origin/main` = `26177d82`** (the round-2 review saw it on
  `origin/author-d8-confirm-20261117 @ 26177d82`; `origin/main` has since advanced to that commit). The row says:
  "…按已提交 freeze `reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` 装 trackp-gpu 环境（排序 diff 为空），
  干净检出代码 D `8662e359`，在明确标为 ENGINEERING 的临时目录跑 kev-0.8b 的 DRYRUN 路径；不是 attempt-2 root，
  永不计入；单元先独立审查。Track P 的 evidence 表仍只在 TASL-7 产出（R1-TASL7-TRACKP）。" The unit's
  tiny-CPU stand-in is a deviation from the row's literal "kev-0.8b 的 DRYRUN 路径"; §1 gives the reason (the
  real guarded-runner child needs TASL-7 attempt-1 inputs) but the literal quote/recorded deviation R2 asked for
  is still absent (MINOR R3-2). The text is otherwise consistent with the scope.
- `R1-TRACKP-UNITB` is on main `16185b0b` and names **D `8662e359`** ("host 先验证 HEAD 等于 D、工作树 clean、
  runner sha"), so §5's C2/D2 + authority-amendment condition is mandatory for any D2 — §5 states it correctly.
  `R1-TASL7-TRACKP` (Track P evidence only on TASL-7) and `R1-TASL2-LOCK` (TASL-2 may be the second card only for
  work that never enters an evidence table) are correctly invoked; the unit is explicitly ENGINEERING-only.

## 2. Disposition of round-2 findings

| Round-2 item | Revision 3 | This review |
|---|---|---|
| Residual BLOCKING-1 (baseline set insufficient to verify the unit's own STOPs) | §3b adds tracked-file SHA list, `.pyc` inventory, gitdir/index, scratch-parent hashes, worktree list, nvidia-smi list, lease log, host snapshot, argv/env and after-checks | **Partially closed → residual BLOCKING-1** (§6): HF-cache roots and the venv tree are still not baselined, "changed" is still undefined, and §3.5(iii)'s literal "no untracked file outside the scratch root" remains (unsatisfiable) beside §3b's "no new" |
| BLOCKING-2 (bare `--tiny` is not the Unit B DRYRUN) | §1 NOT-rehearsed list + non-goal result label | **Closed** (§4), subject to R3-2's recorded deviation |
| MAJOR-1 (negative guard reuses an existing run dir) | distinct `<scratch>/guard-refusal/probes`, rc 2, STOP text, no dir | **Closed** for the ambiguity; the exact literal argv is still not written down (MINOR R3-7) |
| MAJOR-2 (objective clean criteria: manifest/no-GPU/report values/preflight/wall time/record) | §3b has the no-GPU manifest fields, wall-time ≤600 s and a result-record list; report list included | **Partially closed**: the report list's A3 value is **wrong and fatal** → new **BLOCKING-1** (§5); host preflight still incomplete → **MAJOR-1** (§7) |
| MAJOR-3 (defect/D2 path + result record complete) | §3b adds one sentence ("TASL-7 re-verification of any D2 and authority naming D2 are required") and a partial record list | **Partially closed → MAJOR-2** (§7) |
| MINOR R2-1…R2-11 | see §8 | R2-8 closed (wall bound); R2-1/2/3/6/7/9 not applied; R2-5/10/11 applied partially; plus new MINORs R3-1…R3-9 |

The round-2 review's own §4 report-value claim was wrong for the kev tiny path (R2 lines 130–136: "A3 numeric
v1 … expected to succeed"); revision 3 copied it. See §5.

## 3. TASL-2 host facts re-verified (read-only)

All unit §2/§3b facts were re-checked on 2026-11-17T00:32–00:40Z and **all match** (the unit's capture window
00:12–00:25Z is consistent):

| # | Unit's recorded fact | Re-verified value |
|---|---|---|
| 1 | TASL-2 / `dowling` | `hostname`=TASL-2, `whoami`=dowling, `date -u`=2026-11-17T00:32:37Z. **Matches.** |
| 2 | RTX 4090, driver 535.309.01, 24,564 MiB, 353 MiB/0 %, no compute app | `nvidia-smi --query-gpu`: `NVIDIA GeForce RTX 4090, 8.9, 535.309.01, 24564 MiB, 353 MiB, 0 %`; `--query-compute-apps` empty. **Matches.** |
| 3 | disk 374 G free (STOP threshold 50 GB) | `df -h /home/dowling`: `1.9T 1.4T 374G 80%`. **Matches.** |
| 4 | venv Python 3.12.15; live freeze 121 lines sha `50238e5a…`, sorted diff vs committed freeze empty | venv python `Python 3.12.15`; the three host captures `now.sorted`, `pin.sorted`, `venv_freeze_now.txt` are each **121 lines, sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`**, byte-identical to the committed `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` (same sha/line count). **Matches.** |
| 5 | D clean at `8662e359…`; runner `c045475b…`; child `trackp.py` `d2a30ec2…`; config `049bafed…`, placeholders `[]`, digest `64073cea…` | `git --no-optional-locks rev-parse HEAD` = `8662e359…` (detached); status porcelain empty (untracked-files=all = 0); `sha256sum` runner = `c045475b458b…`, child = `d2a30ec2c1b4…`, config = `049bafede821…`; recomputed from the D config bytes `config_digest` = **`64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`**, placeholders **`[]`**. **Matches.** |
| 6 | 8 pinned model repos (26 G) and HF caches present | `~/r1_trackp/models`: 8 dirs, `26G`; `~/r1_trackp/hf_cache` 91 M; `~/.cache/huggingface` 89 M; the pinned Qwen3.5-0.8B-Base snapshot `dc7cdfe2…` has `config.json`, `merges.txt`, `tokenizer_config.json`, `tokenizer.json`, `vocab.json`. **Matches.** |
| 7 | no `ENGINEERING_rehearsal_*` / `p3a_attempt2_*` roots; no `*.active`; no marker helper | `find /home/dowling -maxdepth 5` for both patterns = 0; no `*.active`; `trackp-evidence` not on PATH and no evidence helper under home; `~/r1_locks` holds `gpu0.lock` 0 B and `_to_delete/` only. **Matches.** |
| 8 | pre-existing D bytecode: 7 ignored + 65 tracked `results/…` `.pyc` | `find` = **72** total: `git ls-files '*.pyc'` = **65** (tracked `results/…`), ignored in 4 `__pycache__` dirs = **7** (`r1/`, `r1/c3/`, `r1/c3/train/`, `r1/scripts/`; mtime 2026-11-16T16:10:12 −0800). **Matches.** |
| 9 | worktree list, linked-worktree index, scratch-parent captures | `git worktree list` = `/home/dowling/Agent_paper_B b5a7aec [main]` + D `8662e35 (detached HEAD)`; linked index = **1,627,029 B, sha256 `855fec7579f9a7a847949779c749b2ac0f27e25f98390bb0bed9dedb1dcc85ef`**; scratch parent holds exactly the 4 pre-existing files `now.sorted` (2,540 B, `50238e5a…`), `pin.sorted` (2,540 B, `50238e5a…`), `venv_freeze_now.txt` (2,540 B, `50238e5a…`), `venv_freeze_err.txt` (78 B, `4f201bae…`). **Matches.** |
| 10 | lease log 188 lines (unit §3b(g)) | `~/r1_trackp/runs/gpu_lease_log.jsonl` = **188 lines, sha256 `f813ce6633ffeb72590adade02dc84c70dd7589fbc5c583ec254d6e58ca0918d`**; last pair the 26 Oct `trackp probes kev-0.8b` run. **Matches.** |

## 4. Command, CPU-only guarantee, guard and write paths (D `8662e359`)

- **Tiny path is CPU-only and lease/marker-free.** `_lease` yields `None` when `args.tiny` (`trackp.py:92-100`,
  `cmd_probes` at `trackp.py:233-240`), so `R.gpu_lease` is never entered: no lock, no lease-log line,
  `manifest["gpu_lease"] == []`. `trackp.py` contains no marker code and TASL-2 has no Track P marker helper
  (host fact 7), so no marker can be taken. The tiny kev model is built by
  `tiny.build_tiny` → `M.build_model("kev", <dir>)` → `PointerWrapper` with `dtype=torch.float32, device="cpu"`
  (`model.py:242-300`); `CUDA_VISIBLE_DEVICES=` is explicit in §3's prefix and `trackp.py`'s
  `os.environ.setdefault` is only a fallback, so `host_record` (`run.py:319-343`) records
  `host.device = null` and `host.cuda_visible_devices = ""` while its `nvidia-smi --query-gpu` stays read-only.
- **Guard is sound.** `_refuse_a3_short_without_budget` raises `TrackPStop("--a3-short needs --budget on a real
  base: …")` when `--a3-short` is set and (`--budget` absent **or** `--tiny`), and `main()` calls it for `probes`
  **before** config load and before any run-dir work (`trackp.py:223-228`, `316`); `TrackPStop` is caught at
  `trackp.py:343-345` (prints `STOP: …`, rc 2). The full argv is valid, so the rc 2 is the guard's, and
  `<scratch>/guard-refusal/probes` is never created. A distinct run dir is now specified (§3.4, §3b).
- **No plausible write outside the scratch root remains on this path**, with one caveat: the tokenizer files are
  loaded from the pinned HF cache with `local_files_only=True` (`tiny.py:20-27`) under `HF_HUB_OFFLINE=1`, and the
  installed `huggingface_hub` 2.2.0 returns the offline/local error before any metadata/download/lock path
  (`site-packages/huggingface_hub/file_download.py:1724-1732`), so no cache write is expected; `_tiny`
  (`<run-dir>/_tiny/tiny_qwen35_hybrid`) and `report.json`/`manifest.json` are inside the scratch run dir; the
  two `git_commit` calls only read (`GIT_OPTIONAL_LOCKS=0` suppresses the optional index refresh — the round-1
  hazard), and `git.harness` will be empty/unknown because the sibling `autoresearch_harness` is absent (expected
  — MINOR R3-6). **However**, the HF-cache and venv trees are exactly the trees §3b does not baseline (§6).
- **A3 v1 is the fatal problem**: see §5. The rest of §3.3's report-shape expectation (A1==A2, A4/A4_v1_raw,
  absent A3_descriptive, A5 n/a) is what the code produces *if* A3 is reached; it is not reached on D.

## 5. BLOCKING-1 — the mandated kev-tiny report values cannot be produced on D

**Finding.** §3b (lines 72–77) makes the result record contain "exact report keys … `A3` numeric v1
(`A3_LENGTHS=(0,2000,8000)`)" and §3.3 (lines 47–50) requires step 3's command to exit **rc 0** and write a
`report.json` with `A1,A2,A3,A4,A5`. On the delivered bytes `8662e359` this is impossible for
`--tiny --family kev` without `--budget`: the command aborts with an **uncaught `kev.model.ContextOverflow`**
at the A3 2,000-token level, before any report/manifest is written.

**Evidence (all read at `8662e359`):**

1. `r1/scripts/trackp.py:236-244` — `cmd_probes` sets `counters = _counters(cfg) if args.budget and not args.tiny
   else None`; the unit's step-3 argv has neither `--budget` (so `counters` is `None`, the v1 A3 path) nor any
   way to reach the v2 path on `--tiny` (`--tiny` forces `None` even with `--budget`).
2. `r1/c3/train/model.py:249,274` — `PointerWrapper.__init__(…, max_state: int = 1024, …)` and
   `self.ctx = km.training_context(max_state)`; `tiny.build_tiny` (`tiny.py:71`) calls
   `M.build_model("kev", <dir>, head_form=…)` without `max_state`, so the tiny kev model encodes with
   `max_state = 1024`.
3. `r1/c3/train/model.py:313-315` — `PointerWrapper.forward` encodes every record with
   `km.encode(self.tok, r, max_state=self.ctx["max_state"], max_branch=self.ctx["max_branch"], strict=True)`.
   kev's `encode` raises `ContextOverflow` when `len(state_tokens) + 1 > max_state` (site-packages
   `kev/model.py:102-104`).
4. `r1/c3/train/exam_synthetic.py:91,398-421` — A3 v1 uses `A3_LENGTHS = (0, 2000, 8000)`; the 2k/8k prompts
   prepend 2,000/8,000 tokens of history to the state, far over 1,024.
5. `r1/c3/train/exam_run.py:246-258, 276-281` — in the v1 branch `_a3_rps` is given the **integer** key
   (`L_ = 0/2000/8000`) and only tolerates `str(key) in {"descriptive_2000", "descriptive_8000"}` (the v2
   descriptive keys); the v1 overflow is re-raised, and the v1 branch's `out["A3"] = …` line is never reached.
6. `r1/scripts/trackp.py:333-345` — `main()` catches only `R.TrackPStop`; a `ContextOverflow` (a `ValueError`)
   escapes as a traceback and the process exits non-zero (rc 1), writing neither `report.json` nor
   `manifest.json` (`_write_json` runs only after `COMMANDS[args.cmd]` returns).
7. This is not hypothetical: the committed v1 A3 report for the real kev base,
   `docs/r1/reports/trackp_p3a_dryrun_20261026/kev-0.8b_soft/report.json`, records exactly these refusals —
   `"2000": "ContextOverflow: state exceeds 1024 tokens: 2383"`, `"8000": "…: 8400"`, with
   `A3 = {"pass": null, "reason": "not all lengths ran"}` and `A3_errors` present; the committed report
   `docs/r1/reports/TRACKP_P3A_DRYRUN_20261026.md` says "the 2k- and 8k-token history prompts were refused by
   Kev's strict 1,024-token state limit (`ContextOverflow`), so A3 did not run". The later commit `08aeaff9`
   ("Guard P.3a execution and GPU lease budget") narrowed `_a3_rps` so that only the **descriptive** string keys
   are non-fatal, which turns the v1 2k/8k refusal into a hard abort — the regression this unit would hit.

**Why round 2 missed it.** R2 (lines 130–136) inferred success from
`r1/tests/test_trackp_cli.py::test_toy_batch_e0_and_probes_dry_run`, which runs `e0 --tiny --with-probes` and so
does hit `X.probes(counters=None)`. That test is *not* green on the reviewed environment: it is listed as skipped
in `docs/r1/reports/local_baseline_20261026/paper-ids.md` ("pool tokenizers not in the local HF cache") and in the
only committed GPU-venv execution record it **failed** (`docs/r1/reports/trackp_phase2_20261026/trackp_tests_in_gpu_venv.txt`,
"FAILED … test_toy_batch_e0_and_probes_dry_run[kev]"). No committed record shows the bare kev tiny probes path
succeeding, so the expected values were never evidence-based.

**Consequence.** The unit as written cannot produce the clean result it mandates: step 3 exits non-zero → §4's
"rc != 0 in step 3 → STOP" fires, §3b's mandatory report values are unattainable, and §3b's defect clause sends
the operator to §5 (C2/D2 + authority amendment) — i.e. the rehearsal's outcome would be a defect STOP, not the
"host/env/CLI rehearsal clean" record, and the unit would then need revision anyway.

**Exact fix (choose one; all require re-review of the revised bytes):**
- **(a) Expect the defect (no code change before running).** Rewrite §3.3/§3b so step 3's expected outcome is
  `rc != 0` with the `kev.model.ContextOverflow: state exceeds 1024 tokens` traceback, no `report.json`/
  `manifest.json`, and an A3 record of `{"pass": null, "reason": "not all lengths ran"}` only if the code is
  later fixed; make the deliverable the STOP record plus the §5 C2/D2 plan. Still record the exact report values
  only for the *post-D2* re-run.
- **(b) Fix the code first, then pin D2.** A reviewed C2 restoring the tolerant `_a3_rps` behaviour for the v1
  integer keys (record `A3_errors` and `A3 = {"pass": null, "reason": "not all lengths ran"}`) or raising the
  eval `PointerWrapper` state limit; mechanical D2; TASL-7 re-verification; authority amendment naming D2. Then
  correct §3b's A3 expectation (it is **not** "numeric v1" even under the tolerant behaviour).
- **(c) Re-scope step 3 to paths that are runnable on D**, e.g. keep the kev build/save rehearsal via
  `python -m r1.scripts.trackp spike --tiny --family kev --run-dir <scratch>/kev-build` (no A3) and run the
  probes-CLI report/manifest rehearsal on a family that does not have kev's 1,024-token limit, recording the
  deviation from the authority's "kev-0.8b 的 DRYRUN 路径" wording. Any such change must be re-reviewed.

Do not "accept with the caveat that it may STOP": the §3b list is mandatory and self-contradictory as written.

## 6. Residual BLOCKING-1 — the baseline set still does not cover the unit's own STOP

Revision 3 genuinely improves the round-2 baseline gap: §3b now captures the tracked-file SHA list
(`git ls-files -z | xargs -0 sha256sum`) and `git status --porcelain --untracked-files=all`, the ignored/tracked
`.pyc` inventory, the linked-worktree gitdir path + index sha/size, the scratch parent listing + capture hashes,
the worktree list, the nvidia-smi compute-apps list, the lease-log count/sha, the host snapshot and argv/env, and
it repeats (a)–(g) after step 4 with delta-relative "no new" wording. That closes the specific hazards R2 named
(D worktree, bytecode, index, scratch parent, worktree list, lease log, GPU list). **But it is not complete against
§4 line 83 ("Any file outside the scratch root changes … → STOP") and §3.5:**

1. **The HF-cache roots and the venv tree are not baselined.** R2's fix enumerated the candidate trees as
   "D worktree, linked-worktree git dir, scratch parent, HF caches and venv site-packages"; §3b covers the first
   three and the venv *freeze sha* only. The host has `~/.cache/huggingface` (89 M), `~/r1_trackp/hf_cache`
   (91 M) and 4,539 pre-existing venv `.pyc`; a `.locks`/`.no_exist` write or a venv bytecode file would be
   invisible to (a)–(g), so the operator could not decide `clean` objectively. Add a
   `find <cache roots> -type f -printf '%p %s %TY-%Tm-%Td…' | sort | sha256sum` (or a `find <scratch-parent>,
   ~/.cache/huggingface, ~/r1_trackp/hf_cache, ~/r1_trackp/venvs/trackp-gpu -newer <scratch>/baseline_stamp
   -type f` inventory excluding the scratch root) baseline and repeat it after.
2. **"Changed" is still undefined.** R2-10 required content/sha/mtime delta vs the baselines, **not atime**
   (reading the config/runner updates atime). §3b does not state it; add it.
3. **§3.5(iii) is still the literally unsatisfiable wording.** Step 5 (line 56–58) still says "(iii) no untracked
   file outside the scratch root", although the scratch parent already contains the four pre-existing capture
   files (host fact 9) and §3b line 70 says "no **new** untracked file". Revision 3 did not restate §3.5(ii)/(iii)
   as R2 required; the two texts now conflict. Replace (iii) with the delta-relative version, cross-reference
   §3b, and state that "changed" means content/sha/mtime delta.

Until 1–3 are fixed, a "clean" record would still have to improvise part of its evidence — the round-2 class of
blocking finding, now narrowed to the cache/venv trees and the definition.

## 7. MAJOR findings

### MAJOR-1 — the host preflight is still not captured/compared (R2 MAJOR-2 item 3, R2-3, R2-11)

§3b(h)'s host snapshot records hostname/date/uptime/disk/driver/venv-freeze sha, but no step captures or compares:
`git --no-optional-locks -C <D> rev-parse HEAD` == `8662e359…` (only the *post-hoc* manifest `git.paper.commit`
contains it), the `--check-config`-equivalent placeholders `[]` + config digest `64073cea…`, the freeze **line
count** 121, or the D/runner/child/config shas **against the §2 values** (`c045475b…`, `d2a30ec2…`, `049bafed…`
are recorded in §3.2 but not declared compared). §4 line 86 makes "D HEAD/dirty mismatch" a STOP, yet no step
reads HEAD — the unit cannot verify one of its own STOPs. §2 line 23 still says "re-checked after acceptance"
(R2-3 asked for "re-checked immediately before execution from the step-2 preflight commands"). **Fix:** add these
exact preflight commands to §3.2/§3b(h) with the expected values and a compare-or-STOP rule
(`date -u`; `git --no-optional-locks -C <D> rev-parse HEAD`; `sha256sum` freeze + `wc -l`; the two `--check-config`
outputs; `df`; runner/child/config shas), and record them in the result.

### MAJOR-2 — the defect/D2 path and the result record are still incomplete (R2 MAJOR-3)

§3b line 78–79 ("A runner defect → STOP and the C2/D2 + amendment rule of §5; TASL-7 re-verification of any D2
and authority naming D2 are required") is a one-line nod. Still missing from R2 MAJOR-3: the TASL-7 side must be
re-verified at **exactly D2, clean**, with its preflight checking HEAD/runner sha/executing bytes and refusing any
post-review commit; the recorded statement that **no unreviewed change reached TASL-7**; the
**no-re-run-on-changed-code** rule; and the result record's own identity/location — unit-bytes sha, authority
refs, scratch-root absolute path, timestamp, where/on which ops branch it is committed, and that the scratch root
is **retained** (no deletion). §5 also says "obtain an authority amendment **if** `R1-TRACKP-UNITB` must name D2"
while §3b says "authority naming D2 **are required**" — the two must be made consistent (the row names D, so the
amendment is mandatory for a D2). **Fix:** put the R2 §8 list into §3b's record and §5's defect clause.

## 8. MINOR findings and exact fixes

- **R3-1 (new) stale revision identity / title.** Line 1 still reads "Unit (revision 2) — … rehearsal **for** the
  Unit B DRYRUN path" (R2-1 not applied) and lines 4–9 still describe revision 2. Retitle "toward — and explicitly
  not — the Unit B DRYRUN path", write "revision 3", and add a canonical-bytes line (sha256 + line count) so the
  reviewed bytes are identifiable.
- **R3-2 (R2-2) authority deviation still not recorded.** Quote the `R1-TASL2-UNITB-REHEARSAL` row verbatim (with
  its `**…**` markers), state explicitly that the literal "kev-0.8b 的 DRYRUN 路径" is not run and that the tiny
  kev CPU stand-in is what is rehearsed, and record the coordinator confirmation / branch status
  (`origin/main` `26177d82`, row present).
- **R3-3 duplicate step numbering.** §3 has two items numbered "5" (wall-time bound at line 54, "After" at line 56).
  Renumber to 5/6/7.
- **R3-4 (R2-9) absolute scratch path absent.** §3.1 still says "`…/ENGINEERING_rehearsal_<UTC>`"; write the
  absolute `/home/dowling/r1_engineering/unitb_rehearsal_20261117/ENGINEERING_rehearsal_<UTC>`, state it is not a
  `p3a_attempt2_*` root and not under `~/r1_trackp/runs`, and add a step that verifies the path does not exist.
- **R3-5 (R2-5/R2-11) invocation not fully pinned.** §3 says "from the D worktree … `PYTHONPATH=.`" but does not
  record `sys.executable` (`/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python`). The command uses
  `python -m r1.scripts.trackp` while the reviewed tests use the script form; `-m` works with the `r1/scripts`
  namespace package (verified locally) but should be stated and recorded.
- **R3-6 (R2-6/R2-7) environment/harness expectations.** Record that `hf_home` in the config is not read by the
  code (the tiny tokenizer resolves through the default `~/.cache/huggingface`), or set `HF_HOME=` explicitly;
  record that `manifest.git.harness` will be empty/unknown (sibling harness absent) as expected, not a STOP.
- **R3-7 (R2-10, R2 MAJOR-1 residual) guard argv + disclosure.** Write the exact literal negative argv (do not
  rely on "the same command plus"), and disclose that the §3.2 `flock -n ~/r1_locks/gpu0.lock true` probe briefly
  takes/releases the GPU lock without logging a lease and that `host_record`'s `nvidia-smi` query is read-only.
  Scope `SHA256SUMS` to every file in the scratch root and record the capture filenames/shas.
- **R3-8 (new) exact report sub-keys under-specified.** §3b names top-level keys only. If the unit keeps the
  report-value list, state the fields: `A3 = {"mean_abs_drps": {2000: float, 8000: float}, "pass": bool}`
  (and `A3_errors` whenever a level is refused), `A4_v1_raw = {"frac_monotone", "descriptive", "criterion_met"}`
  (the `pass` key is renamed `criterion_met`), `A4` = the v2 `{frac_monotone_vs_label, label_ceiling_frac,
  frac_monotone_raw, median_slope_vs_label, pass}`, and record that the A3 protocol key is **absent** in v1.
  (After BLOCKING-1 is fixed, the actual kev-tiny A3 value is `{"pass": null, "reason": "not all lengths ran"}`,
  not numeric — see §5.)
- **R3-9 (new) result-record location/format.** §3.5 says "write the result record" but not where/format/commit.

## 9. Verdict

**Not accepted — 1 BLOCKING (BLOCKING-1: the mandated kev-tiny report values are unattainable on D; step 3 raises
an uncaught `ContextOverflow` at A3 2k/8k and writes no report/manifest, so the unit cannot produce the "clean"
record it mandates), residual BLOCKING-1 (the §3b baseline set still omits the HF-cache/venv trees, "changed" is
undefined and §3.5(iii) still contradicts §3b with an unsatisfiable literal), 2 MAJOR (host preflight not
captured/compared; defect/D2/result-record incomplete), 9 MINOR.** Round-2 MAJOR-1 (guard) and R2-8 (wall-time
bound) are closed; the round-2 BLOCKING-2 re-scope remains honest; the round-2 no-GPU/manifest-field analysis is
confirmed: `_lease` is never entered for `--tiny`, so `gpu_lease == []`, `evidence_label == "DRYRUN"`,
`host.device` is `null`, `host.cuda_visible_devices == ""`, and no marker/lock/lease-log line can be produced; no
plausible write outside the scratch root remains beyond the unbaselined cache/venv trees.

**What acceptance would require:** fix BLOCKING-1 (§5 option (a), (b) or (c) — the expected step-3/report values
must match what the delivered bytes actually do, including the `A3_errors`/`A3 = pass:null, "not all lengths ran"`
fact if the tolerant behaviour is restored), add the residual baselines of §6 (HF caches, venv, "changed"
definition, restated §3.5(iii)), add the MAJOR-1 preflight and MAJOR-2 defect/record items, and apply the MINOR
edits; then commit the exact revised 101-line bytes (recording the new sha256) and re-review those bytes. If the
lead instead prefers to execute revision 3 as a **defect-discovery** run, that must be stated in the unit (the
result record is then the `ContextOverflow` STOP plus the §5 C2/D2 plan, not "clean", and §3b's report-value list
must be dropped/moved to the post-D2 re-run).

---

Reviewer artifact; uncommitted at the time of writing. Canonical unit bytes reviewed:
`13f67b8da5e119c5a74c9df10038eabdc2b4a4af98988da663f9a503ec4affcb` (101 lines), currently a working-tree
modification over HEAD `44b52368` (whose file is the 60-line round-1 bytes `a6a2cba3…`). Round-2 review read:
`428286d0e65d6aaa7e6dec003ccfbc14e32807408be7ed8794b8c897396e3731` (346 lines). Review file sha256 and line
count are reported with the delivery of this review.
