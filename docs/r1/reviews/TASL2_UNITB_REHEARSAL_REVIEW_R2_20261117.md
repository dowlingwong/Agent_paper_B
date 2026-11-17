# Independent review (round 2) — TASL-2 ENGINEERING host/env/CLI readiness rehearsal, revision 2 (17 November 2026)

**Status: NOT ACCEPTED — 1 residual BLOCKING (round-1 BLOCKING-1 is only partially closed), 3 MAJOR, 11 MINOR.**
Fresh independent reviewer (no part in drafting the unit, the Track P code, the attempt-2 plan or the TASL-2
worktree; round 1 was a different reviewer). **Review only: the unit was not executed, no host write, no
commit/push, no GPU.** Read-only SSH to TASL-2 (`portal_zhixu`, user `dowling`) was used for the host facts; the
only workspace change is this uncommitted review file. The revision-2 bytes answer the *substance* of both round-1
BLOCKINGs — the scope claim is now honest and the bytecode/index writes are prevented — but the "clean" criterion
and its baseline set are still not objective/complete for the unit's own STOP conditions, so the revision needs a
short round 3.

## 0. Method and limits

- Canonical unit bytes were read from the worktree at the given path, hashed and line-counted (§1). The round-1
  review was read first (`docs/r1/reviews/TASL2_UNITB_REHEARSAL_REVIEW_20261117.md`, sha `601a3b29…`, 366 lines).
- The D code was read at the delivered commit `8662e35991659f7a661fb7ed6be4980791d302f3` from the repository
  object store (`git show 8662e359:…`) and the local code worktree, not from a mutable working copy; the statements
  in §4/§5 are about those bytes. All hashes in this review were recomputed.
- TASL-2 facts were re-verified **read-only** with `ssh portal_zhixu '…'` on **2026-11-17T00:22–00:26Z**:
  `hostname`, `whoami`, `date -u`, `nvidia-smi --query-gpu/--query-compute-apps`, `df`, `ls`/`stat`/`find`/
  `sha256sum`/`cat`, and `git --no-optional-locks` with `GIT_OPTIONAL_LOCKS=0` (no index refresh). `uv pip freeze
  --python …` was **streamed to the reviewing machine** and hashed locally.
- **No host write**: `trackp.py --check-config` was **not** run on TASL-2 (it would write bytecode into the D
  worktree); its two outputs were recomputed on the reviewing machine from the streamed config bytes, which are
  proven identical to the D blob (`049bafed…`). No Python was executed on TASL-2, `torch.cuda.is_available()` was
  not invoked there, no directory/file was created, moved or deleted, and no process/session/lock was signalled.
- The `ops-tasl-20261116` worktree is being written concurrently by other agents (Track G untracked files; this
  unit is a working-tree modification). Acceptance is tied to the unit bytes only; the concurrent files are
  unrelated.
- No evidence claim is made or evaluated here; TASL-2 stays a non-evidence host.

## 1. Canonical bytes, revision delta and authority

- Unit `docs/r1/proposals/TASL2_UNITB_REHEARSAL_20261117.md`: **sha256
  `8495dd0807eb41f7cb1a55de9a8563ddd3ecfaf89ed504ab90438a2636310165`, 77 lines** — matches the given canonical
  bytes exactly. The reviewed bytes are the **uncommitted working-tree** version: worktree HEAD `45fcf0fa` holds
  the round-1 bytes (`a6a2cba3…`, 60 lines) and `git diff --numstat` is `77 60`. Committing the exact 77-line
  bytes unchanged (and recording `8495dd08…`) is required; any byte change voids this review.
- **Concurrent-write note.** While this review was being written, another agent replaced the worktree unit: the file
  now holds a **101-line draft** (current sha256 `13f67b8da5e119c5a74c9df10038eabdc2b4a4af98988da663f9a503ec4affcb`,
  mtime 2026-11-17 01:29 local) that adds a "§3b. Mandatory baselines and result record (round-2 review
  conditions)", a distinct guard run dir and a 600 s wall-time bound. That draft is **not** the canonical bytes
  given to this reviewer (`8495dd08…`, 77 lines) and is **not reviewed here**; the verdict and findings below apply
  only to `8495dd08…`. If the 101-line draft is intended as revision 3 it needs its own review: it already
  implements most of the MAJOR/MINOR items below (distinct guard dir, ≤600 s bound, §3b baseline/result-record
  list), but it has a duplicated step number "5", keeps the "for the Unit B DRYRUN path" title, and does not yet
  restate §3.5(ii)/(iii) delta-relative or baseline the HF caches/the venv (see §5, §9).
- `R1-TASL2-UNITB-REHEARSAL` exists on **`origin/author-d8-confirm-20261117` @ `26177d82`** (descendant of main
  `16185b0b`; verified **absent** from `16185b0b` by `git grep`). The row's relevant text is (ellipses mark
  elided leading/trailing text):
  "…按已提交 freeze `reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` 装 trackp-gpu 环境（排序 diff 为空），
  干净检出代码 D `8662e359`，在明确标为 ENGINEERING 的临时目录跑 kev-0.8b 的 DRYRUN 路径；不是 attempt-2 root，
  永不计入；单元先独立审查。Track P 的 evidence 表仍只在 TASL-7 产出（R1-TASL7-TRACKP）。"
  (quote with the leading and trailing portions elided by "…"; no emphasis altered). Revision 2 cites the row id
  but no longer quotes it, and does not explicitly record the deviation from the row's literal "kev-0.8b 的
  DRYRUN 路径" (the unit runs a CPU tiny `--family kev` stand-in; see MINOR R2-2).
- `R1-TRACKP-UNITB` is on **`origin/main` = `16185b0b`** and says: "…在 TASL-7 上用交付的代码 D `8662e359`
  （`trackp-p3a-code-20261116`；host 先验证 HEAD 等于 D、工作树 clean、runner sha）运行…". It names **D**, so the
  §5 authority-amendment condition for any D2 is mandatory, not optional — §5 gets this right (§8).
- `R1-TASL7-TRACKP` (Track P evidence only on TASL-7) and `R1-TASL2-LOCK` (TASL-2 may be the second card only for
  work that never enters an evidence table) are correctly invoked; the unit is explicitly ENGINEERING-only and
  never claims an evidence label, an attempt-2 root or a TASL-7 action.

## 2. Disposition of round-1 findings

| Round-1 item | Revision 2 | This review |
|---|---|---|
| BLOCKING-1 (bytecode/index writes make "no file outside scratch" false) | adds the env prefix `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=` to "all commands"; adds a tracked-file SHA256 baseline and after-checks (i)–(vi) | **Partially closed.** Prevention is fixed; the *baseline set* is still insufficient to verify the unit's own STOPs → **residual BLOCKING-1** (§5) |
| BLOCKING-2 (bare `--tiny` cannot rehearse the Unit B DRYRUN) | title + §1 re-scope to "host/env/CLI readiness rehearsal", explicit "NOT rehearsed" list, result label "host/env/CLI rehearsal clean" | **Closed** (§6) |
| MAJOR-1 (`CUDA_VISIBLE_DEVICES` `setdefault`) | explicit `CUDA_VISIBLE_DEVICES=` in the prefix | **Closed for prevention**; manifest/no-GPU evidence still not required → part of MAJOR-2 |
| MAJOR-2 (defect path C2/D2/amendment) | §5 adds C2 + mechanical pin D2 + TASL-7 delivery + amendment because the row names D | **Mostly closed**; TASL-7 exact-D2 re-verification and record conditions missing → MAJOR-3 |
| MAJOR-3 ("clean" not objective) | rc/report keys/guard/after-check skeleton added | **Partially closed**: manifest values, exact report values, host preflight, result-record and wall-time bound still missing → MAJOR-2/3 |
| MINOR-1…13 | only a few touched | mostly open, see R2-1…R2-11 |

## 3. TASL-2 host facts re-verified (read-only)

All unit §2 facts were re-checked on 2026-11-17T00:22–00:26Z and **all match** (the unit's stated capture window
00:12–00:25Z is consistent):

| # | Unit's recorded fact | Re-verified value |
|---|---|---|
| 1 | TASL-2 / `dowling` | `hostname`=TASL-2, `whoami`=dowling, `date -u`=2026-11-17T00:22:06Z / 00:26:31Z. **Matches.** |
| 2 | RTX 4090, driver 535.309.01, 24,564 MiB, 353 MiB/0 %, no compute app | `nvidia-smi --query-gpu`: `NVIDIA GeForce RTX 4090, 8.9, 535.309.01, 24564 MiB, 353 MiB, 0 %`; `--query-compute-apps` empty. **Matches.** |
| 3 | disk 374 G free (STOP threshold 50 GB) | `df -h /home/dowling`: `/dev/nvme0n1p2 1.9T 1.4T 374G 80%`. **Matches.** |
| 4 | venv Python 3.12.15, torch 2.6.0+cu124; live `uv pip freeze` = 121 lines sha `50238e5a…`, sorted diff vs committed freeze empty | venv python → `Python 3.12.15`; `torch/version.py` → `2.6.0+cu124`; streamed `uv pip freeze --python …` = **121 lines, sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`**, byte-identical to the committed `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` (121 lines, same sha). The host's own `now.sorted`, `pin.sorted`, `venv_freeze_now.txt` all have the same sha (121 lines each). **Matches.** |
| 5 | D checkout clean at `8662e359…`; runner `c045475b…`; child `trackp.py` `d2a30ec2…`; config `049bafed…`, `--check-config` placeholders `[]`, digest `64073cea…` | `git --no-optional-locks rev-parse HEAD` = `8662e35991659f7a661fb7ed6be4980791d302f3` (detached); status porcelain **empty**, untracked-files=all count 0; linked worktree (`gitdir: /home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117`); `sha256sum` of `r1/scripts/trackp_p3a_guarded.py` = `c045475b458b0112315a04b858c2b2f407b668b64b8651f921441a1a24864e56`, `r1/scripts/trackp.py` = `d2a30ec2c1b4c2b33387898a4ccafecff3cd7c584a8df68d586c011a07b09e63`, config = `049bafede821e9a15b38cdfc96b9198f1d1cbdd63153dced25250e045e71c2f7`; recomputed from the streamed config bytes `config_digest` = **`64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`**, placeholders **`[]`**. **Matches.** |
| 6 | 8 pinned model repos (26 G) and HF caches present | `~/r1_trackp/models`: 8 dirs, `26G`; `~/r1_trackp/hf_cache` 91 M; `~/.cache/huggingface` 89 M; pinned Qwen3.5-0.8B-Base snapshot `dc7cdfe2…` contains `config.json`, `merges.txt`, `tokenizer_config.json`, `tokenizer.json`, `vocab.json` (symlinks into `blobs/`). **Matches.** |
| 7 | no `ENGINEERING_rehearsal_*` / `p3a_attempt2_*` roots; no `*.active`; no Track P evidence-marker helper | `find /home/dowling -maxdepth 4` for both patterns = 0; `~/r1_locks`: `gpu0.lock` 0 B (sha `e3b0c442…`), no `*.active`, no `~/r1_locks/bin`, `trackp-evidence` not on PATH and not found under home; `~/r1_trackp/runs/gpu_lease_log.jsonl` = **188 lines, sha `f813ce6633ffeb72590adade02dc84c70dd7589fbc5c583ec254d6e58ca0918d`**, last entries the 26 Oct `trackp probes kev-0.8b` pair. **Matches.** |
| 8 | (needed for BLOCKING-1) pre-existing D bytecode | `git status --ignored` shows the 4 ignored `__pycache__/` dirs; `find` shows **7 ignored `.pyc`** (4 dirs: `r1/__pycache__`, `r1/c3/__pycache__`, `r1/c3/train/__pycache__`, `r1/scripts/__pycache__`), mtime **2026-11-16 16:10:12 −0800**, plus 65 **tracked** `.pyc` under `results/…` (72 total). The round-1 MINOR-2 baseline is still accurate and **the unit does not record it** (§5). |
| 9 | (needed for the after-checks) worktree list, index, parent captures | `git worktree list` = `/home/dowling/Agent_paper_B b5a7aec [main]` + D `8662e35 (detached)`; linked-worktree index `/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117/index` = **1,627,029 B, sha256 `855fec7579f9a7a847949779c749b2ac0f27e25f98390bb0bed9dedb1dcc85ef`**; the scratch parent `…/unitb_rehearsal_20261117/` already contains 4 pre-existing outside-scratch files: `now.sorted` (2,540 B, sha `50238e5a…`), `pin.sorted` (2,540 B, sha `50238e5a…`), `venv_freeze_now.txt` (2,540 B, sha `50238e5a…`), `venv_freeze_err.txt` (78 B, sha `4f201bae…`) — relevant to §5(iii). |

## 4. Command, CPU-only guarantee and write paths (D code at `8662e359`)

The unit command is `python -m r1.scripts.trackp probes --tiny --family kev --head-form linear12 --evidence DRYRUN
--run-dir <scratch>/DRYRUN/kev-0.8b/probes --n-probe 8`, run from the D worktree with the frozen venv and the env
prefix of §3. What the delivered bytes do:

- **`_tiny` is inside the scratch run dir.** `cmd_probes` → `_build` (`r1/scripts/trackp.py:61-73`): for
  `args.tiny`, `work = Path(args.run_dir) / "_tiny"` and `tiny.build_tiny(args.family, work, …)`. In
  `r1/c3/train/tiny.py:60-70` the kev stand-in is `work_dir / "tiny_qwen35_hybrid"` (config/tokenizer/safetensors
  written by `save_pretrained` inside it). The real-base branch (`spec = cfg["bases"][args.base]`) is not reached,
  so no pool weights, no `local_path`, no `--load` (not passed) and no TASL-7 root is touched.
- **Only writes on this path are inside the run dir.** `r1/scripts/trackp.py:43-44` `_write_json` creates
  `<run-dir>/report.json` and `<run-dir>/manifest.json` (`mkdir(parents=True)`); `exam_run.probes` does no file
  I/O (its only `np.save`/`E.load` calls are in `e0`, not `probes`); `run_manifest` writes nothing (it returns the
  dict, including `git_commit`, `environment_record`, `host_record`).
- **No GPU lease, no marker.** `_lease` (`trackp.py:92-100`) yields `None` when `args.tiny`, so `R.gpu_lease` is
  never entered (`run.py:179`), no lease-log line is appended and `manifest["gpu_lease"] == []`. The bare
  `trackp.py` contains no marker code at all; TASL-2 has no Track P marker helper (verified, §3 item 7).
- **The guard is unreachable output-safe.** `_refuse_a3_short_without_budget` (`trackp.py:223-228`) raises
  `TrackPStop("--a3-short needs --budget on a real base: …")` when `--a3-short` is present and (`--budget` absent
  **or** `args.tiny`); `main()` calls it for `probes` **before** config load and before any run-dir work
  (`trackp.py:316`); `TrackPStop` is caught at `trackp.py:343-345`, prints `STOP: …` to stderr and returns **rc 2**.
  So `--tiny --budget --a3-short` cannot create output.
- **CPU-only.** The tiny kev model is built by `tiny.causal_lm(hybrid, seed)` → `AutoModelForCausalLM.from_config`
  with `attn_implementation="sdpa"`, then `M.build_model("kev", path, head_form=…)` → `PointerWrapper` with its
  defaults `dtype=torch.float32, device="cpu"` (`r1/c3/train/model.py:242-278`). The prefix sets
  `CUDA_VISIBLE_DEVICES=` explicitly; `trackp.py:324`'s `os.environ.setdefault` is only a fallback. `host_record`
  (`run.py:319-343`) still runs a read-only `nvidia-smi --query-gpu` and `torch.cuda.is_available()`, which with no
  visible devices is False and opens no CUDA context; `manifest["host"]["device"]` should be `null` and
  `manifest["host"]["cuda_visible_devices"] == ""`.
- **Config / environment.** `--tiny` skips `check_environment` (`trackp.py:328-329`) but `load_config` still runs
  and would STOP on any placeholder; verified `[]`. `--evidence DRYRUN` is redundant (`_evidence` returns DRYRUN
  whenever `args.tiny`, `trackp.py:48-51`); the manifest label is DRYRUN and no authorization note is needed
  (`_require_authorization`, `trackp.py:54-58`).
- **Git calls.** `run_manifest` → `git_commit(REPO)` (`run.py:249-257`) runs `git status --porcelain -z
  --untracked-files=no` and `git rev-parse` in the D worktree; `GIT_OPTIONAL_LOCKS=0` suppresses the optional index
  refresh, which is exactly the round-1 index-write hazard. `git_commit(harness_root())` targets the absent sibling
  `…/unitb_rehearsal_20261117/autoresearch_harness` (verified absent), so `manifest.git.harness` will be
  empty/unknown without a STOP — record that as expected.
- **HF / model downloads.** `tiny.tokenizer` uses `AutoTokenizer.from_pretrained(..., local_files_only=True)`
  (`tiny.py:20-27`) and the pinned snapshot is cached (verified above); `HF_HUB_OFFLINE=1` is also set. In the
  installed `huggingface_hub` 2.2.0 the `local_files_only=True` metadata path returns `OfflineModeIsEnabled`
  before any download, and the `.locks` / `.no_exist` writes live in the download branch, so no cache write is
  expected; there is no `~/.cache/torch` and no `torch.hub`/compile path here. `run_manifest`'s
  `environment_record` imports `torch/transformers/peft/kev/laya/startlux_decide` from the venv (installed from
  git into `site-packages`, `direct_url.json` pins recorded, no `.git` inside site-packages), so no outside git
  call and no bytecode write with `PYTHONDONTWRITEBYTECODE=1` (the venv has 4,539 pre-existing `.pyc`).
- **Report shape for kev tiny.** `exam_run.probes` with `counters=None` takes A3 **v1** (`A3_LENGTHS = (0, 2000,
  8000)`, config default `max_position_embeddings=32768`, so 8k is in-context): `A3` numeric
  (`mean_abs_drps`/`pass`), `A4` and `A4_v1_raw` numeric, `A3_descriptive` **absent**, `A1 == A2 = {"pass": null,
  "reason": "model does not pack …"}` (tiny is hybrid → `packing = not hybrid = False`), `A5 = {"pass": null,
  "reason": "A5 applies to BinTokenWrapper only …"}`. The reviewed test `test_toy_batch_e0_and_probes_dry_run`
  exercises the same `X.probes` path on the kev tiny stand-in (`--with-probes --n-probe 3`), so the n=8 command is
  expected to succeed; note no reviewed test runs the bare `probes` **success** subcommand (R2-5).

**Conclusion for the write-path question:** with the env prefix, no plausible write outside the scratch root
remains on this path; `_tiny` is inside `<scratch>/DRYRUN/kev-0.8b/probes/_tiny`, and report/manifest are inside
the run dir. The residual problem is not a write path but that the unit's own after-check/STOP set does not
*baseline* the artifacts it names (§5).

## 5. Round-1 BLOCKING-1 — partially answered; residual BLOCKING-1

Revision 2 genuinely fixes the *previously false* criterion: `PYTHONDONTWRITEBYTECODE=1` stops the D-worktree and
venv bytecode writes (7 pre-existing ignored `.pyc` in 4 dirs are still there, §3 item 8), `GIT_OPTIONAL_LOCKS=0`
stops the linked-worktree index refresh (index present, sha `855fec75…`), `HF_HUB_OFFLINE=1`/`local_only=True`
stops downloads, and the tracked-file SHA256 baseline + `git status` before/after are a real improvement. That is
why I do **not** find the round-1 BLOCKING as severe as before.

But the unit is still not executable *as written* to a defensible "clean" result, for the same class of reason:

1. **§3.2 does not baseline the artifacts the unit's own STOP list names.** §4 says "Any file outside the scratch
   root changes (**including bytecode, worktree index**, generated files) → STOP", and §3.5(ii) requires "no new
   `__pycache__`/`.pyc` under the D worktree". Yet §3.2 records no `find`/sha of the pre-existing 7 ignored `.pyc`,
   and no sha of the linked-worktree `index` (`855fec75…`). With only `git status --porcelain` (which ignores both)
   the operator cannot decide (ii) or the index part of the STOP objectively.
2. **§3.5(iii) is not baseline-relative and is literally unsatisfiable.** "No untracked file outside the scratch
   root" read literally fails before the run even starts: the scratch parent already contains four pre-existing
   untracked capture files (`now.sorted`, `pin.sorted`, `venv_freeze_now.txt`, `venv_freeze_err.txt`, verified
   §3 item 9), and `~/.cache`, `~/r1_trackp` contain many more. The criterion must be "**no new or changed**
   file outside the scratch root, relative to the step-2 baselines", and the baselines must cover the candidate
   trees (D worktree, linked-worktree git dir, scratch parent, HF caches, venv site-packages).
3. Therefore a result record attesting "clean" would still have to improvise its evidence — the exact failure mode
   round 1 blocked on. The fix is small (four baseline lines + restated criteria, below), so this is a **residual
   BLOCKING-1**, not a new blocker on the command.

**Exact fix (add to §3.2, and restate §3.5(ii)/(iii)):**

```
find <D> -name '*.pyc' -printf '%p %s %TY-%Tm-%TdT%TH:%TM:%TS\n' | sort > <scratch>/baseline_pyc.txt
sha256sum /home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117/index > <scratch>/baseline_gitdir.sha256
find /home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117 -maxdepth 1 -printf '%f %s %TY-%Tm-%TdT%TH:%TM:%TS\n' | sort >> <scratch>/baseline_gitdir.sha256
sha256sum <scratch-parent>/{now.sorted,pin.sorted,venv_freeze_now.txt,venv_freeze_err.txt} > <scratch>/baseline_parent.sha256
```
and require after the run, relative to those baselines: (ii) `baseline_pyc.txt` identical (no new/removed `.pyc`);
(iii') the tracked-file SHA list identical, the linked-worktree index/gitdir listing identical, the scratch-parent
capture hashes identical, and **no new/changed file** under the D worktree, the linked-worktree git dir, the
scratch parent, the HF cache roots and the venv (a `find … -newer <scratch>/baseline_stamp -type f` inventory
excluding the scratch root is sufficient; record it). Also state that "changed" means content/sha/mtime delta,
not atime (reading the config/runner updates atime only).

## 6. Round-1 BLOCKING-2 — answered; the tiny DRYRUN + guard is a useful bounded rehearsal

Revision 2 closes this one:

- Title/§1 now say **host / frozen-env / CLI readiness rehearsal** and §1 has an explicit "**NOT rehearsed**" list
  (the guarded runner, its real `--budget --a3-short --load attempt-1/…/final/saved` child, real `kev-0.8b`, the
  A3 budget-v2 path, A1/A2/A5 values, attempt-1 inputs, TASL-7 paths), with the reason (those inputs are TASL-7
  evidence and must not be fabricated/copied on TASL-2). Result label is **"host/env/CLI rehearsal clean"**, never
  "Unit B DRYRUN rehearsed". No evidence label, no attempt-2 root, no TASL-7 action.
- The tiny+guard rehearsal is **useful and bounded**: it exercises the frozen venv import chain
  (torch/transformers/kev/laya/startlux_decide), the shipped config load with no placeholders, the CPU tiny
  kev build/save, the A3-v1/A4 probe path and report/manifest writing, the guard refusal, and the containment
  checks — and it cannot reach the real DRYRUN/A3-short/lease/marker paths. It is not a substitute for the
  TASL-7 DRYRUN (which stays mandatory) and revision 2 says so.
- Residual: the authority row's literal "kev-0.8b 的 DRYRUN 路径" is deviated from (tiny CPU stand-in) without an
  explicit recorded deviation or coordinator confirmation → MINOR R2-2; the title still says "for the Unit B
  DRYRUN path", which §1 corrects but the title should read "toward, and explicitly not, …" → R2-1.

## 7. Are the acceptance criteria objective and complete? (question 2)

Objective and checkable as written: scratch root "must not exist" and UTC naming; positive command rc 0; wall time
recorded; `report.json` parses with the A1–A5 keys; guard rc 2 + STOP text + no run dir; tracked-file SHA256
baseline + `git status` before/after; no new `.pyc` (once baselined); lease-log count/sha; worktree list; nvidia-smi
compute-apps list; no `*.active`; no helper.

Still missing or ambiguous (see findings): the baseline set for the unit's own STOP conditions (BLOCKING-1); the
guard's exact argv/run-dir (MAJOR-1); exact report values and manifest/no-GPU values (MAJOR-2); host preflight
values (HEAD, freeze sha/lines, config digest/placeholders, disk, date) are only §2 prose, not step-2 commands
(MAJOR-2); wall-time **bound** (MINOR-R2-8); result-record required fields (MAJOR-3); scratch file-tree/SHA256SUMS
scope (R2-10).

**CPU-only / no-lease (question 3): confirmed.** The tiny build is CPU by construction (`PointerWrapper`
`device="cpu"`, `dtype=float32`), `_lease` yields `None` for `--tiny` so `gpu_lease`/lease-log are never entered,
no marker code exists in this CLI and TASL-2 has no helper; `CUDA_VISIBLE_DEVICES=` is explicit in the prefix and
`host_record`'s `nvidia-smi` query is read-only (the manifest's `host.device` should be `null`). The only note:
the step-2 `flock -n ~/r1_locks/gpu0.lock true` probe briefly takes and releases the GPU lock without logging a
lease — that is fine, but the result record should say so (R2-10).

## 8. STOP/defect path (question 5)

§5 is **correct in substance** for `R1-TRACKP-UNITB`: a defect → STOP; a new code unit on `trackp-p3a-code-*`; a
new independently reviewed code commit **C2**; a **mechanical delivery-pin child D2**; deliver D2 to TASL-7; and an
**authority amendment** because `R1-TRACKP-UNITB` names D `8662e359` (verified on main `16185b0b`; the D commit is
the mechanical child of C `5b7ad0cb`, runner blob identical except the single `EXPECTED_PAPER_HEAD` line). This
answers round-1 MAJOR-2.

Missing items (MAJOR-3): the TASL-7 side must be re-verified at **exactly D2, clean**, with the preflight
re-checking HEAD/runner sha/executing bytes and refusing any post-review commit; the result must record that **no
unreviewed change reached TASL-7**; the TASL-2 result stays ENGINEERING and the rehearsal is not re-run on changed
code without a fresh review; and the result record's required fields are not defined (unit bytes sha, authority
refs, scratch root, exact argv, host snapshot, before/after baselines, capture/report/manifest/SHA256SUMS hashes,
guard outcome, §1 non-goal text, no-GPU/lease/marker evidence, TASL-2-is-not-the-evidence-host, scratch retained,
timestamp, and where/on which ops branch it is committed).

## 9. Findings and exact fixes

### BLOCKING-1 (residual, round-1 BLOCKING-1 not fully closed)

See §5. Fix: add the four baseline lines and restate §3.5(ii)/(iii) as delta-relative checks, including the
linked-worktree git dir, the pre-existing 7 ignored `.pyc` / 4 `__pycache__` dirs (mtime 2026-11-16 16:10:12
−0800), the scratch parent's four pre-existing files, the HF caches and the venv; define "changed" as content/sha/
mtime.

### MAJOR-1 — the negative guard check is ambiguous and reuses an existing run dir

§3.4 says "the same command plus `--budget --a3-short` … and create no run directory." "The same command" would
reuse `<scratch>/DRYRUN/kev-0.8b/probes`, which step 3 already created, so "create no run directory" is vacuous or
a false STOP; and there is no full negative argv. **Fix:** write the exact argv with a fresh path, e.g. `python -m
r1.scripts.trackp probes --tiny --family kev --head-form linear12 --evidence DRYRUN --run-dir
<scratch>/guard-refusal --n-probe 8 --budget --a3-short`, require `rc == 2`, stderr contains
`--a3-short needs --budget on a real base`, and `<scratch>/guard-refusal` does not exist (do not accept argparse's
rc 2 for a usage error as a substitute — the full argv is valid, so the rc 2 is the guard's).

### MAJOR-2 — "clean" still lacks the manifest/no-GPU/preflight/report-value definition

**Fix (add to §3.3/§3.5):**
1. `report.json`: `A3` present with `mean_abs_drps` and a boolean `pass` (v1; record `protocol` absent);
   `A4` and `A4_v1_raw` present; `A1 == A2 == {"pass": null, "reason": "model does not pack (spec §5.6: packed
   models only)"}`; `A5 == {"pass": null, "reason": "A5 applies to BinTokenWrapper only (spec §5.6)"}`;
   `A3_descriptive` absent; record explicitly that this is the v1 path, not attempt-2's v2 path.
2. `manifest.json`: `evidence_label == "DRYRUN"`, `subcommand == "probes"`, `base == {"tiny": "kev", "note":
   "random-weight stand-in; not a pool model"}`, `config_sha256 == 64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d
   84f5a17431986f00c`, `git.paper.commit == 8662e359…`, `git.paper.dirty == false`, `gpu_lease == []`,
   `host.hostname == "TASL-2"`, `host.cuda_visible_devices == ""`, `host.device is null`, `extra.argv` = exact
   command; record `git.harness` empty/unknown as expected.
3. Step-2 host preflight (re-check §2 immediately before the run): `date -u`, `git --no-optional-locks -C <D>
   rev-parse HEAD` == D, `git … status --porcelain` empty, `sha256sum` freeze file + line count == 121/`50238e5a…`,
   `--check-config`-equivalent placeholders `[]` + digest `64073cea…`, `df -h` ≥ 50 GB, and the D/runner/child/
   config shas compared to §2 values (not merely recorded).
4. Wall-time **bound** (e.g. `timeout` or STOP if the tiny A3-v1 0/2k/8k×8 CPU run exceeds N minutes; preserve,
   do not retry) — MINOR-R2-8 can fold here.

### MAJOR-3 — defect path / result record incomplete

See §8. **Fix:** add the TASL-7 exact-D2-clean re-verification (HEAD/runner sha/executing bytes, no post-review
commit), the no-unreviewed-change statement, the no-re-run-on-changed-code rule, and the result-record required
fields (list in §8), committed on the ops branch with the scratch root retained (no deletion); record that TASL-2
is not the evidence host and that the TASL-7 Unit B DRYRUN remains mandatory.

### MINOR (each with the exact fix)

- **R2-1 title.** "host/env/CLI readiness rehearsal **for** the Unit B DRYRUN path" still reads as rehearsing it;
  §1 is correct. Say "toward — and explicitly not — the Unit B DRYRUN path" in the title (round-1 BLOCKING-2(a)).
- **R2-2 authority deviation.** Quote the `R1-TASL2-UNITB-REHEARSAL` row verbatim (with its `**…**` markers) and
  state: the literal "kev-0.8b 的 DRYRUN 路径" cannot be run on TASL-2 without the TASL-7 attempt-1 `final/saved`
  inputs, so the tiny-kev CPU stand-in is what is rehearsed; record that this deviation was reviewed or obtain the
  coordinator's confirmation. Also write the branch/merge status (`origin/author-d8-confirm-20261117` @ `26177d82`,
  descendant of `origin/main` `16185b0b`, not yet merged).
- **R2-3 "re-checked after acceptance"** should be "re-checked immediately before execution from the step-2
  preflight commands" (the §2 facts are point-in-time; round-1 §7.5).
- **R2-4 `--evidence DRYRUN` is redundant.** Keep or drop it, but verify `manifest.evidence_label == "DRYRUN"`,
  not the argv.
- **R2-5 invocation form.** State from where `python -m r1.scripts.trackp` is run (cwd = D, `PYTHONPATH=.`) and
  record `sys.executable`; note that the reviewed tests use the script form (`python r1/scripts/trackp.py`) and that
  the bare `probes --tiny` success path has no reviewed CLI test (this rehearsal is the first end-to-end bare-
  `probes` run; that is a value of the rehearsal, not a defect).
- **R2-6 HF/cache provenance.** The config's `hf_home` is not read by the code (round-1 MINOR-9); the tiny
  tokenizer resolves through the default `~/.cache/huggingface` (pinned snapshot present, verified). Record that
  (or set `HF_HOME=/home/dowling/r1_trackp/hf_cache` explicitly) and keep `HF_HUB_OFFLINE=1`.
- **R2-7 manifest harness field.** `git.harness` will be empty/unknown (the sibling `autoresearch_harness` is
  absent, verified); record it as expected, not as a STOP.
- **R2-8 wall-time bound.** Record wall time (already required) **and** define a ceiling/timeout; on hang STOP and
  preserve (no deletion/retry).
- **R2-9 scratch path.** Replace "`…/ENGINEERING_rehearsal_<UTC>`" with the absolute
  `/home/dowling/r1_engineering/unitb_rehearsal_20261117/ENGINEERING_rehearsal_<YYYYMMDDTHHMMSSZ>`, state it is not
  a `p3a_attempt2_*` root and not under `~/r1_trackp/runs` (round-1 MAJOR-3 item 1).
- **R2-10 "changed"/"untracked" definition and side-effect disclosure.** Define changed as content/sha/mtime delta
  vs the baselines (not atime); scope `SHA256SUMS` to every file in the scratch root (report, manifest, `_tiny/…`,
  captures) and record the capture filenames/shas; note that `run_manifest`→`host_record` performs a read-only
  `nvidia-smi` query (not a job/lease) and that the step-2 `flock` probe briefly takes/releases `gpu0.lock` without
  logging a lease.
- **R2-11 compare, not just record.** State that the `stat`/sha256 of runner/child/config in step 2 are **compared
  to the §2 values** (`c045475b…`, `d2a30ec2…`, `049bafed…`), and record the venv `sys.executable`
  (`/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python`, verified).

## 10. Verdict

**Not accepted — 1 residual BLOCKING (BLOCKING-1), 3 MAJOR, 11 MINOR.** Round-1 **BLOCKING-2 is closed**, and
round-1 **BLOCKING-1 is closed for prevention** (env prefix kills the bytecode/index writes; I re-verified the
relevant host state, including the pre-existing 7 ignored `.pyc` and the linked-worktree index); the residual is
that the **baseline/after-check set is still insufficient to verify the unit's own STOP conditions**, and §3.5(iii)
is unsatisfiable as worded. The command itself is sound, CPU-only, lease-free, marker-free, evidence-free, and
contained in the scratch root; `_tiny` is inside the scratch run dir and the guard refuses before any output. Only
the objective "clean" definition, the guard argv and the result/defect record need the small fixes above
(effectively four baseline lines + restatements + the exact guard argv + the manifest/host-preflight/report lists +
the result-record list).

**What acceptance would require (round 3):** apply BLOCKING-1 and MAJOR-1/2/3 and the MINOR-R2-1/2 edits, commit
the exact revised bytes unchanged, and re-review those bytes. After that the unit **may be executed as written**,
provided the result record contains the before/after baselines (tracked-file SHA list, pre-existing `.pyc` list,
linked-worktree git-dir listing, scratch-parent capture hashes, lease-log count/sha, worktree list, nvidia-smi
compute-apps list), the capture/report/manifest/SHA256SUMS hashes, the manifest no-GPU fields
(`evidence_label=DRYRUN`, `gpu_lease=[]`, `host.device=null`, `host.cuda_visible_devices=""`), the exact argv, the
host preflight values, the §1 non-goal text, the guard outcome, and the statement that TASL-2 is not the evidence
host and that the TASL-7 Unit B DRYRUN remains mandatory. If the lead prefers to execute before a revision, those
same items become mandatory recorded conditions, and the guard command must use a distinct
`<scratch>/guard-refusal` run dir.

---

Reviewer artifact; uncommitted at the time of writing. Canonical unit bytes reviewed:
`8495dd0807eb41f7cb1a55de9a8563ddd3ecfaf89ed504ab90438a2636310165` (77 lines), which at review start were the
working-tree modification over HEAD `45fcf0fa` (round-1 bytes `a6a2cba3…`, 60 lines); the file has since been
replaced by another agent (see the concurrent-write note in §1), so if this revision is to proceed, restore/commit
exactly these reviewed bytes. Review file sha256 and line count are reported with the delivery of this review.
