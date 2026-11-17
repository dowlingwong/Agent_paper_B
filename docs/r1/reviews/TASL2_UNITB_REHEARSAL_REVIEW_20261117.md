# Independent review — TASL-2 ENGINEERING rehearsal of the Track P Unit B DRYRUN path (17 November 2026)

**Status: NOT ACCEPTED — 2 BLOCKING, 3 MAJOR, 13 MINOR; revision and re-review needed before execution.**
Fresh independent reviewer (no part in drafting the unit, the Track P code, the attempt-2 plan or the TASL-2
worktree). **Review only: no execution of the unit, no host write, no commit/push, no GPU.** Read-only SSH to TASL-2
(`portal_zhixu`, user `dowling`) was used for the host facts; the only workspace change is this uncommitted review
file. The two BLOCKING findings are small, local fixes (an environment prefix on the command and a scope paragraph);
the unit is otherwise close to executable.

## 0. Method and limits

- Canonical unit bytes were read from the worktree at the given path, hashed and line-counted (§1).
- The authority rows were read from the repository objects (`git show`/`git grep`) and the unit's quotation compared
  line by line (§1).
- The D code was read at the reviewed delivery commit `8662e359` (`git show 8662e359:…`), not from a working copy,
  so the code statements below are about the delivered bytes (§3).
- TASL-2 facts were re-verified with read-only commands (`ssh portal_zhixu '…'`): `hostname`, `date -u`, `whoami`,
  `nvidia-smi --query-*`, `df -h`, `ls`/`stat`/`sha256sum`/`cmp`, `git --no-optional-locks rev-parse|status`, and
  `uv pip freeze --python …` piped to the reviewing machine. `git status` was run with `--no-optional-locks` so it
  takes no index lock. `python -m r1.scripts.trackp --check-config` was **not** run on the host (it would write
  bytecode into the D worktree); its two outputs were recomputed on the reviewing machine from bytes proven
  identical to the host file (§2, item 4). `torch.cuda.is_available()` was **not** invoked on TASL-2 (to avoid any
  CUDA context on the card); the CUDA-availability claim is assessed from the torch build, the driver and the config
  comment instead, and is flagged as not re-invoked (§7).
- One transient exception to "no host write": a first freeze capture wrote `/tmp/uvfreeze.out` and
  `/tmp/uvfreeze.err` on TASL-2; both were removed immediately and their absence verified. The final freeze capture
  was streamed to the reviewing machine instead. No repository, venv, lock, lease-log or scratch file was touched.
- The worktree `ops-tasl-20261116` was being written concurrently by other agents (`M r1/scripts/configs/paper_a_status_ada.json`,
  untracked `TRACKG_*` files). They are unrelated to this review; acceptance is tied to the unit bytes only.

## 1. Canonical bytes and authority

- Unit `docs/r1/proposals/TASL2_UNITB_REHEARSAL_20261117.md`: **sha256 `a6a2cba3cc2c2978335a308f8e3f8d497e4bd459774b242dd9064254c49a8f83`, 60 lines, 4,255 bytes** — matches the
  given canonical bytes exactly. At review time the worktree HEAD is `c921983e` (branch `ops-tasl-20261116`,
  `origin/ops-tasl-20261116`) and the unit is **untracked**; the review is of these bytes, so committing them
  unchanged and recording acceptance is required, and any byte change voids the acceptance.
- `R1-TASL2-UNITB-REHEARSAL` exists in `docs/r1/PLAN.md` on **`origin/author-d8-confirm-20261117` @ `26177d82`**
  (17 Nov 2026, "author decisions 17 Nov (2)"), which is a **descendant of main `16185b0b`**; the row is **not yet on
  main** (`git grep R1-TASL2-UNITB-REHEARSAL 16185b0b` → absent; `… 26177d82` → present). The unit's quoted Chinese
  text is **verbatim the PLAN row**, except that the row's `**…**` emphasis markers are removed and the quote is
  wrapped in `"…"`; no substantive word differs.
- `R1-TRACKP-UNITB` is on **main `origin/main` = `16185b0b`** (author decisions 17 Nov): Unit B is probes-only,
  qwen3.5-4b, new root, DRYRUN first, 45-h GPU budget, **on TASL-7 with delivered code D `8662e359`**, host to
  verify HEAD == D / clean / runner sha, accepted-plan STOPs, A6 deferred.
- `R1-TASL7-TRACKP` (PLAN §10): every P.3a and later Track P evidence table is produced on TASL-7 only.
  `R1-TASL2-LOCK` (PLAN §10): TASL-2 may be Track P's second card, but **only for work that does not enter an
  evidence table**. The rehearsal's authority therefore correctly permits a TASL-2 ENGINEERING-only activity.
- **MINOR-1 (citation precision):** the unit's bracket "(`author branch author-d8-confirm-20261117 @ 26177d82`; also
  main `16185b0b`)" reads as if `R1-TASL2-UNITB-REHEARSAL` were also on main; it is only on the author branch
  `26177d82` (a descendant of main `16185b0b`). (`R1-TRACKP-UNITB` is on main `16185b0b`.) Also note the local `main`
  ref in this worktree is stale (`bc31e15e`); the main the citations mean is `origin/main` = `16185b0b`. Fix: write
  "`R1-TASL2-UNITB-REHEARSAL` (`origin/author-d8-confirm-20261117` @ `26177d82`, descendant of `origin/main`
  `16185b0b`, not yet merged); `R1-TRACKP-UNITB` (`origin/main` `16185b0b`)".
- The unit's authority chain (R1-TASL7-TRACKP evidence-only-TASL-7; Track X priority on TASL-2 under
  R1-PORTAL-SCHEDULE) is cited correctly and is consistent with the rehearsal being an ENGINEERING-only, never-counted
  activity. Nothing in the unit claims an evidence label or an attempt-2 root.

## 2. TASL-2 host facts re-verified (read-only)

All values below were read on 2026-11-17T00:12–00:25Z from TASL-2.

| # | Unit's recorded fact | Re-verified value |
|---|---|---|
| 1 | Host TASL-2, user `dowling`; RTX 4090, driver 535.309.01, 24,564 MiB; disk 374 G free | `hostname`=TASL-2, `whoami`=dowling; `nvidia-smi`: `NVIDIA GeForce RTX 4090, 535.309.01, 24564 MiB`, 353 MiB used, 0 % util, **no compute app**; `df -h /home/dowling`: 374 G free. **Matches.** |
| 2 | venv Python 3.12.15, torch 2.6.0+cu124, `torch.cuda.is_available()==True` | `…/venvs/trackp-gpu/bin/python --version` → 3.12.15; `torch/version.py`: `__version__='2.6.0+cu124'`, `git_version='2236df17…'`; `torch-2.6.0+cu124.dist-info`; `uv 0.13.6`. **Python/torch/uv match.** CUDA availability was not re-invoked (§0, §7); driver 535 ≥ CUDA-12.0 minimum, so cu124 minor-version compatibility holds, consistent with the config comment. |
| 3 | `uv pip freeze --python` = 121 lines, sorted diff vs committed portal freeze = 0 | Live freeze streamed to the reviewer: **121 lines, sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`** — byte-identical to the committed `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` (121 lines, same sha256). `sort` diff = 0 lines. The host's own artifacts `…/unitb_rehearsal_20261117/{now.sorted,pin.sorted,venv_freeze_now.txt}` are also 121 lines each with sha256 `50238e5a…` and `cmp now.sorted pin.sorted` rc 0. **Exact match; no reinstall needed.** |
| 4 | D worktree at `8662e35991659f7a661fb7ed6be4980791d302f3`, clean; `--check-config` placeholders `[]`, config sha `64073cea…` | HEAD = `8662e359…` (detached); `git --no-optional-locks status --porcelain` **empty**, `--untracked-files=all` count 0; linked worktree (`gitdir: /home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117`); `r1/scripts/trackp_p3a_guarded.py` sha256 `c045475b458b0112315a04b858c2b2f407b668b64b8651f921441a1a24864e56` and `r1/scripts/trackp.py` sha256 `d2a30ec2c1b4c2b33387898a4ccafecff3cd7c584a8df68d586c011a07b09e63`, identical to the D blobs. Delivery pin line 50: `EXPECTED_PAPER_HEAD = "5b7ad0cb7fedd083bad457968dc3dd3e920ac154"`. Config file sha256 = `049bafede821e9a15b38cdfc96b9198f1d1cbdd63153dced25250e045e71c2f7`; recomputed `config_digest` from those exact bytes = **`64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`** and `placeholders == []`. **Matches.** |
| 5 | disk ≥ 50 GB | 374 G free. **Matches.** |
| 6 | models/HF cache present | `~/r1_trackp/models`: **8 dirs, 26 G**; `~/r1_trackp/hf_cache` 91 M; default `~/.cache/huggingface` 89 M. The pinned tokenizer revision is cached in the default cache: `models--Qwen--Qwen3.5-0.8B-Base/snapshots/dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68/` contains `tokenizer.json`, `tokenizer_config.json`, `config.json`, `merges.txt`, `vocab.json` (present in the `r1_trackp/hf_cache` cache too). **Matches.** |
| 7 | (needed for the clean/lease checks) | `~/r1_locks`: `gpu0.lock` 0 B (16 Nov 01:54), **no `*.active` marker**, **no `~/r1_locks/bin/trackp-evidence`** helper on TASL-2, `_to_delete/` dir present; `~/r1_trackp/runs/gpu_lease_log.jsonl`: **188 lines, sha256 `f813ce6633ffeb72590adade02dc84c70dd7589fbc5c583ec254d6e58ca0918d`**, last entries the 26 Oct `trackp probes kev-0.8b` pair; no `p3a_*` root on TASL-2 (attempt 1 is a TASL-7 root); **no `p3a_attempt2_*`** root anywhere under `/home/dowling` (maxdepth 4); **no `*ENGINEERING_rehearsal*`** root exists yet. |

**MINOR-2 (pre-existing outside writes must be baselined).** An earlier verification step (the unit records a `--check-config` run) already wrote outside
any scratch root: the D worktree has ignored bytecode `r1/__pycache__`, `r1/c3/__pycache__`, `r1/c3/train/__pycache__`,
`r1/scripts/__pycache__` with 7 `.pyc` files, mtime `2026-11-16 16:10:12 -0800` (the rehearsal-run modules
`exam_run`, `tiny`, `model`, `metrics`, … are not among them yet). The unit's step-3 criterion "no file outside the
scratch root changed" is therefore relative to an already-non-pristine D worktree; record this baseline (or disable
bytecode writes, BLOCKING-1).

## 3. The command and the D code — what it does and does not exercise

The unit's command (unit §2.2):

```
python -m r1.scripts.trackp probes --tiny --family kev --head-form linear12 --evidence DRYRUN \
       --run-dir <scratch>/DRYRUN/kev-0.8b/probes --n-probe 8
```

read from the D worktree with `PYTHONPATH=.` and the frozen venv. Code at D (`8662e359`), `r1/scripts/trackp.py`:

- **`--tiny` is always DRYRUN:** `_evidence()` returns `"DRYRUN"` whenever `args.tiny` (lines 48–51), so the
  manifest's label is DRYRUN even if `--evidence` were omitted or wrong. **No authorization note is needed**: the
  `trackp_p3a_*` note is required only when `_evidence(args) != "DRYRUN"` (lines 54–58). Covered by the reviewed test
  `test_tiny_runs_are_dryrun_and_need_no_note` (`r1/tests/test_trackp_cli.py`).
- **CPU-only by construction:** the tiny builder is `tiny.build_tiny(family, run_dir/"_tiny", head_form, seed)`
  (lines 66–70); `PointerWrapper`'s default is `device="cpu", dtype=torch.float32` and `tiny.build_tiny` builds the
  random stand-in on CPU and saves it **inside the run dir** (`_tiny`). No pool weights are read, no `--load` is
  used, and no TASL-7 root is referenced. The config's `bases.*.local_path` are not touched on the tiny branch.
- **No GPU lease:** `_lease()` yields `None` when `args.tiny` (lines 91–99); no `gpu_lease` call. **No evidence
  marker:** the bare `trackp.py` contains no marker code at all; the Track P marker helper is a TASL-7 guarded-runner
  feature (`~/r1_locks/bin/trackp-evidence`, sha `f457a04e…`) and does not exist on TASL-2.
- **Config load still happens** (`R.load_config`, line 325) and would STOP on placeholders; verified `[]`.
  **`check_environment` is skipped for `--tiny`** (line 328–329), so the rehearsal does not re-check the pinned torch
  or code_pins live; the freeze/torch facts are covered separately by unit §1.
- **Writes:** `_write_json` creates `<run-dir>/report.json` and `<run-dir>/manifest.json`; `_build` creates
  `<run-dir>/_tiny/`. All inside the scratch root. `run_manifest` records the config digest, git state, environment
  and host.
- **Report shape for this family:** `exam_run.probes` with `counters=None` takes the **A3 v1** path (0/2k/8k
  descriptive), so `report.json` has `A3` (v1, no `protocol` key), `A4`, `A4_v1_raw`, `A1`, `A2`, `A5`, and no
  `A3_descriptive`. For the kev family the model is a hybrid (linear-attention) base, so `packing = not hybrid`
  is False and **A1/A2 are recorded as `{"pass": None, "reason": "model does not pack"}`**; the kev family is not a
  BinTokenWrapper, so **A5 is recorded as `{"pass": None, "reason": "A5 applies to BinTokenWrapper only"}`**. Only
  A3 (v1) and A4 carry real numeric results.
- **Negative guard (verified):** `_refuse_a3_short_without_budget` (lines 223–228) raises `TrackPStop("--a3-short
  needs --budget on a real base: …")` when `--a3-short` is present and (`--budget` absent **or** `--tiny`), and it is
  called in `main()` for `probes` **before** config load and before any run-dir work (lines 315–316) and again in
  `cmd_probes` (line 233). `TrackPStop` is caught and printed as `STOP: …` with **rc 2** (lines 343–345). The
  reviewed test `test_cli_refuses_a3_short_with_tiny` asserts rc 2 and that the run dir is not created. So `--tiny
  --budget --a3-short` cannot create output — **matches the unit's step 4 expectation**, provided the exact argv is
  written out and `rc == 2` (not merely "!= 0") is asserted (MINOR-5).
- **`--tiny` can never exercise the changed A3 path:** `counters = _counters(cfg) if args.budget and not args.tiny
  else None` (line 240), so `--budget` is inert for tiny, and the guard refuses `--a3-short` with tiny. The changed
  A3 budget-v2 / A3-short path is therefore **not reachable** in this rehearsal.
- **`--tiny` does not exercise the reviewed Unit B runner.** Unit B's DRYRUN is the first child of
  `r1/scripts/trackp_p3a_guarded.py --probes-only`; its argv is built at `probes_only_units()`: `probes --base
  kev-0.8b --head-form linear12 --budget --a3-short --n-probe 8 --load
  <attempt-1>/EVIDENCE/kev-0.8b/final/saved`, with `--evidence DRYRUN` and `--run-dir <new-root>/DRYRUN/kev-0.8b/probes`
  appended by `run_unit`. `verify_a3_short_report` then requires `A3.protocol == "v2_budget"` and the
  `A3_descriptive` skipped marker. The runner's own module docstring states: "No bare `trackp.py probes` command is
  used by either path." The rehearsal uses exactly such a bare command and never imports or invokes the guarded
  runner (which would in any case STOP on TASL-2 at `verify_live_pins`/hostname/driver/attempt-1-root checks).

**Conclusion for the command questions:** the command is a safe CPU/DRYRUN invocation that needs no attempt-1
`final/saved`, no TASL-7 root, no lease, no marker and no authorization note, and it exercises the probes/A3v1/A4
code path on a random tiny stand-in. It does **not** exercise the A3-short budget-v2 path, the A1/A2 code (N/A for
kev hybrid), A5 (N/A for kev) or the reviewed Unit B guarded runner. That gap is BLOCKING-2 below.

## 4. Findings

### BLOCKING-1 — The "no file outside the scratch root changed" criterion cannot be met as written

The unit's step 3 makes this an acceptance condition for `rehearsal clean`. It is false for the command as
specified:

1. Running `probes --tiny` imports modules not yet compiled in the fresh D checkout — `r1.c3.train.exam_run`,
   `tiny`, `model`, `metrics`, `losses`, `serialize`, `types`, `packing`, `budget`, `registry`, … — and Python writes
   their `__pycache__/*.pyc` **into the D worktree** (outside the scratch root). An earlier verification step
   already did this for 7 files (MINOR-2); the probe run will add more. `run_manifest`'s `environment_record()` also
   imports `torch`, `transformers`, `peft`, `kev`, `laya`, `startlux_decide`, any of which can write bytecode into
   the venv if a `.pyc` is absent.
2. `run_manifest` calls `git_commit(REPO)` → `git status --porcelain --untracked-files=no` and `git rev-parse` on the
   D worktree; `git status` may refresh and rewrite the linked worktree's index under
   `/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117/index` (outside the scratch root).
3. `host_record()` runs `nvidia-smi` (a read-only query, not a job) even for the tiny run.

So either the operator runs a literal "no file outside the scratch root changed" check and gets a false STOP, or the
result record attests something untrue. **Exact fix:** prefix both invocations with
`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=` and restate the criterion as:
(i) `git --no-optional-locks -C <D> status --porcelain` empty and `rev-parse HEAD == 8662e359…` **before and after**;
(ii) no tracked file or git object changed anywhere (D and the main repo's worktrees); (iii) no new file outside the
scratch root, with the **pre-existing** ignored `__pycache__` baseline recorded (4 dirs / 7 `.pyc`, mtime 16:10:12
-0800) and excluded from the comparison; (iv) `~/r1_locks` and `~/r1_trackp/runs/gpu_lease_log.jsonl` unchanged
(hash/line count). The same environment prefix must be used for the negative guard command, otherwise it too writes
bytecode outside the root.

### BLOCKING-2 — The unit's headline claim (Unit B DRYRUN path) is not what the command exercises

The authority is "在明确标为 ENGINEERING 的临时目录跑 **kev-0.8b 的 DRYRUN 路径**", and §2.2 calls the command "the
kev-family DRYRUN path". The accepted attempt-2 plan's DRYRUN is a **real `kev-0.8b` probes unit on TASL-7 under the
reviewed `trackp_p3a_guarded.py --probes-only`, with `--budget --a3-short --load <attempt-1>/EVIDENCE/kev-0.8b/final/saved`,
which must pass `verify_a3_short_report` (`A3.protocol == "v2_budget"` + the A3-short skipped marker)**. The
rehearsal instead runs a bare, tiny, CPU, no-budget/no-a3-short command; per §3 it can never produce
`protocol: "v2_budget"`, never exercises the changed A3 path, never exercises the guarded runner's preflight/lease/
marker/journal/budget checks, and records A1/A2/A5 only as N/A. Calling the result "rehearsal clean" without a scope
statement would be read as evidence that Unit B's DRYRUN path has been rehearsed, which it has not. It also runs the
**v1 A3 0/2k/8k descriptive path** on the tiny stand-in — harmless on a random tiny model, but it is the path attempt
2 must never run on real bases, so it must not be reported as "the DRYRUN path" without that distinction.
**Exact fix (either one, plus the scope paragraph):**
- (a) Re-scope the unit explicitly: title/§2 "ENGINEERING host/environment/CLI readiness check on TASL-2 using the
  CPU tiny stand-in — **not** the Unit B DRYRUN path"; add a "does NOT verify" list (A3 budget-v2/`--a3-short`,
  guarded runner, real `kev-0.8b`, GPU/driver, A1/A2/A5 values, attempt-1 load, TASL-7 paths); state that the
  TASL-7 DRYRUN remains mandatory and that "rehearsal clean" means only "the delivered D code imports and its tiny
  probes path runs in the frozen venv/config on TASL-2"; and answer/record the deviation from the authority's literal
  "kev-0.8b" wording (or obtain the coordinator's confirmation that the tiny stand-in is the intended reading of
  `R1-TASL2-UNITB-REHEARSAL`).
- (b) Strengthen it to cover the changed code paths: additionally run the reviewed CPU tests from D with the frozen
  venv and scratch-contained temp dirs:
  `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES= <venv>/bin/python -m pytest -p no:cacheprovider --basetemp=<scratch>/pytest_tmp -q r1/tests/test_trackp_p3a_a3_short.py r1/tests/test_trackp_p3a_probes_only.py r1/tests/test_trackp_p3a_guarded.py`.
  These exercise the A3-short delta and the guarded-runner logic with stubs (no host state, no GPU); record pass/fail
  and keep the pytest temp tree inside the scratch root. State that only TASL-7 can exercise the real runner/DRYRUN.

### MAJOR-1 — `CUDA_VISIBLE_DEVICES` is a `setdefault`, so a pre-set environment defeats the CPU-only guarantee

`trackp.py` line 323–324 does `os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")`. If the operator's shell already
exports `CUDA_VISIBLE_DEVICES` (e.g. `0`), the tiny build is still CPU by construction, but `run_manifest` →
`host_record()` calls `torch.cuda.is_available()` and, if true, `torch.cuda.get_device_properties(current_device())`,
which initializes a CUDA context on TASL-2's card with **no lease**, while Track X evidence has priority on TASL-2
(R1-PORTAL-SCHEDULE). This is exactly the kind of accidental GPU touch the unit's "no GPU use" STOP is meant to
forbid. **Exact fix:** make the command set it explicitly (`CUDA_VISIBLE_DEVICES=` in the command prefix, as the
repo's own `r1/tests/test_trackp_cli.py` does: `ENV = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "HF_HUB_OFFLINE": "1"}`),
add a preflight assertion that it is unset/empty, and record `manifest.host.cuda_visible_devices` and
`manifest.host.device` (expected `None`) as clean evidence. Note in the unit that `host_record` still runs a
read-only `nvidia-smi` query (not a job/lease).

### MAJOR-2 — The defect-fix path is insufficient as written

Unit §2.5: "If a runner defect appears, STOP the rehearsal, preserve the capture, and write a separate reviewed code
fix on `trackp-p3a-code-*`; A2 on TASL-7 would then use the fixed reviewed commit only." This is not sufficient,
because `R1-TRACKP-UNITB` authorizes **D `8662e359` specifically**, and the code review (R3) binds the identity of
what may run:
- the fix must be an independently reviewed and **accepted new reviewed code commit C2**;
- it must be delivered as a **new mechanical delivery-pin child D2** (D2^ == C2, the runner blob byte-identical to
  C2's blob with the single canonical `EXPECTED_PAPER_HEAD = "C2"` line — a self-pin cycle is impossible; arbitrary
  descendants and one-line crafted children are refused);
- the TASL-7 host must be at **exactly D2, clean**, with the preflight re-verifying HEAD/runner sha/executing bytes
  (`verify_paper_head`, `verify_executing_files`); any post-review commit on top of D/D2 makes the checkout
  unacceptable, and post-review records go to the ops branch;
- because the authorization names D, an **authority record/amendment** (or the author's decision) is needed for
  Unit B to run at D2 instead of D, and the rehearsal result must record that no unreviewed change reached TASL-7;
- the TASL-2 rehearsal cannot find guarded-runner defects it does not exercise (BLOCKING-2), so "if a runner defect
  appears" is under-triggered here — the TASL-7 preflight/DRYRUN is the place that finds them.
**Exact fix:** replace §2.5 with those four conditions plus "the TASL-2 scratch result stays ENGINEERING; no
re-run of the rehearsal on changed code without a fresh review" and name the new reviewed D2 in the result record.

### MAJOR-3 — "rehearsal clean" is not defined objectively enough

The unit lists rc/report keys/no-marker/no-lease/under-root/no-EVIDENCE/no-outside-write/SHA256SUMS and the guard
refusal, which is the right shape, but the acceptance is underspecified: "contains the A1/A2/A3/A4/A5 keys" passes
for the weaker N/A values this command produces; there is no `report.json`/`manifest.json` value list, no exact
negative argv, no before/after baselines, no host snapshot, no wall time, and "no file outside" is BLOCKING-1.
**Exact fix:** define `rehearsal clean` as all of:
1. scratch root recorded and proved non-existent before, matching
   `^/home/dowling/r1_engineering/unitb_rehearsal_20261117/ENGINEERING_rehearsal_[0-9]{8}T[0-9]{6}Z$`, not
   `p3a_attempt2_*`, not under `~/r1_trackp/runs`;
2. positive command rc == 0 (capture `set -o pipefail`), stdout/stderr captured in the scratch;
3. `report.json` keys and values: `A1 == A2 == {pass: null, reason: "model does not pack"}`; `A5 == {pass: null,
   reason: "A5 applies to BinTokenWrapper only"}`; `A3` present (v1, no `protocol` key) with a numeric `pass`/`mean`;
   `A4` and `A4_v1_raw` numeric; `A3_descriptive` absent; record explicitly that this is the v1 path, not the
   attempt-2 v2 path;
4. `manifest.json`: `evidence_label == "DRYRUN"`, `subcommand == "probes"`, `base == {tiny: "kev", note:
   "random-weight stand-in; not a pool model"}`, `config_sha256 == 64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`,
   `git.paper.commit == 8662e35991659f7a661fb7ed6be4980791d302f3`, `git.paper.dirty == false`,
   `extra.argv` = the exact command, `gpu_lease == []`, `host.hostname == "TASL-2"`, `host.cuda_visible_devices == ""`,
   `host.device is None`; record that `git.harness` is expected empty/unknown (no sibling `autoresearch_harness`
   checkout under the parent; the tiny path does not use the harness);
5. no `~/r1_locks/*.active` before/after, no `~/r1_locks/bin` helper present, `gpu0.lock` unchanged,
   `gpu_lease_log.jsonl` sha256/count unchanged (`f813ce66…`, 188 lines baseline);
6. `find` inside the scratch shows only the expected tree (`DRYRUN/kev-0.8b/probes/{report.json,manifest.json,_tiny/…}`)
   plus the capture; `SHA256SUMS` of every file in the scratch;
7. D worktree tracked state unchanged: `git --no-optional-locks status --porcelain` empty, HEAD == D, before/after;
   the pre-existing ignored `__pycache__` baseline recorded; no other repo/writes;
8. negative check with the exact argv
   `probes --tiny --family kev --budget --a3-short --run-dir <scratch>/guard-refusal` → rc == 2, stderr contains
   `STOP: --a3-short needs --budget on a real base`, and `<scratch>/guard-refusal` does not exist;
9. host snapshot (`date -u`, `uptime`, `nvidia-smi --query-gpu=…`, `df -h`, sha256 of the freeze file and of the
   config), and wall time; `rehearsal clean` only if 1–9 all hold; otherwise STOP per §3;
10. result appended to the unit/a result record and committed on the ops branch, retaining the scratch root (no
    deletion), stating TASL-2 is not the evidence host and that Track P evidence stays TASL-7-only.

### MINOR findings (each with the exact fix)

- **MINOR-3 — `--evidence DRYRUN` is redundant.** `--tiny` forces DRYRUN. Keep or drop it, but verify the
  `manifest.evidence_label`, not the argv, as the evidence-label check.
- **MINOR-4 — "journal" does not exist on this path.** The bare `trackp.py` writes only `report.json` and
  `manifest.json` (the journal is the guarded runner's, on TASL-7). Step 3's "capture stdout/stderr/journal" → "the
  captured stdout/stderr log, `report.json`, `manifest.json`, `SHA256SUMS`".
- **MINOR-5 — the negative check argv is abbreviated.** Write the full command including a `--run-dir` inside the
  scratch, expect `rc == 2` and the STOP text, and assert the path was not created. Do not accept argparse's rc 2
  (missing `--run-dir`) as a substitute for the guard's STOP.
- **MINOR-6 — "no `.active` marker was created" is vacuous for the bare CLI.** Only the TASL-7 guarded runner
  creates the marker, and TASL-2 has no helper (`~/r1_locks/bin` absent). Keep the check but rely on the lease-log/
  lock/hash baselines as the real containment evidence.
- **MINOR-7 — authority citation precision** (see §1, MINOR-1 above): author-branch/`origin/main` distinction, and
  the quote's removed `**…**` markers.
- **MINOR-8 — exact interpreter/paths.** Name the venv interpreter
  (`/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python`), the exact `cd <D>` and `PYTHONPATH=.`, and record
  `python -c 'import sys; print(sys.executable)'`. `python -m` already puts the cwd on `sys.path`, but the explicit
  form is clearer for an audit.
- **MINOR-9 — config coverage.** The default config is `r1/scripts/configs/trackp_portal.json` with
  `host: "TASL-2 (zhixu portal)"`, `runs_dir`/`models_dir`/`hf_home` under `/home/dowling/r1_trackp`; `--check-config`
  only checks placeholders and prints a digest (it does not validate the registry or local paths — cf.
  `reviews/TRACKP_2_REVIEW_20261026.md`). The code never reads `hf_home`; the tiny tokenizer resolves through the
  default `~/.cache/huggingface`, where the pinned revision `dc7cdfe2…` snapshot with tokenizer files exists (also in
  `r1_trackp/hf_cache`). Record this, or set `HF_HOME=/home/dowling/r1_trackp/hf_cache` explicitly; add
  `HF_HUB_OFFLINE=1` so no network attempt is possible.
- **MINOR-10 — runtime bound.** The v1 A3 path runs the 0/2k/8k descriptive levels (`n=8`) on CPU; record wall time
  and STOP/preserve (no deletion) if it hangs or errors, rather than retrying.
- **MINOR-11 — "A2 on TASL-7" is ambiguous** (A2 = attempt 2? A2 = the A2 probe?). Write "attempt 2 (Unit B) on
  TASL-7".
- **MINOR-12 — manifest harness field.** `harness_root()` resolves to the absent sibling
  `…/unitb_rehearsal_20261117/autoresearch_harness`, so `manifest.git.harness` will be empty/unknown without a STOP.
  Record that as expected for this CPU tiny path (TASL-7's guarded runner re-checks the harness pin).
- **MINOR-13 — title/authority wording** (covered by BLOCKING-2(a)): make the title/labels say
  "host/environment readiness (tiny CPU stand-in)", not "rehearsal of the Unit B DRYRUN path", unless (b) is added.

## 5. Scope limits, STOPs, must-not — anything missing or unsafe?

- The scope/STOP/must-not list is otherwise good and matches the authority: ENGINEERING-only scratch root, never an
  attempt-2 root, never counted, no evidence label, not TASL-7, no GPU/lease job, cached pools only, no other user's
  files/processes, no deletion, no `main`/`exam-x-*` push, no reinstall when the freeze matches, no TASL-7 touching.
- Missing/unsafe items: (i) the write criterion is unsafe as written (BLOCKING-1); (ii) the CPU-only guarantee depends
  on an inherited env var (MAJOR-1); (iii) the unit should explicitly forbid running the guarded runner on TASL-2
  (it would STOP on the TASL-7 pins; don't try, and don't "work around" the hostname/driver pins); (iv) add "no
  network attempt" (`HF_HUB_OFFLINE=1`); (v) add "record that `host_record` performs a read-only `nvidia-smi` query,
  which is not a GPU job/marker/lease"; (vi) add "the D worktree is a linked worktree; no `git gc`/`git checkout`/no
  branch changes, no index refresh" (covered by `GIT_OPTIONAL_LOCKS=0`); (vii) record that the scratch root is
  retained for audit (no deletion) and is not an attempt root.
- "Rehearsal clean" objectively: not yet — see MAJOR-3; with items 1–9 it becomes objective and checkable.

## 6. Defect path (question 6)

Insufficient as written — see MAJOR-2. A runner defect must produce a new reviewed+accepted C2, a new mechanical
delivery-pin child D2, a TASL-7 checkout verified at exactly D2 clean (HEAD/runner sha/executing bytes), a recorded
authority amendment because `R1-TRACKP-UNITB` names D `8662e359`, and no unreviewed change to any TASL-7 run. Also note
the rehearsal as written cannot surface guarded-runner defects (BLOCKING-2).

## 7. Residual risks and conditions on the result record

1. **Driver vs freeze:** TASL-2 driver is 535.309.01 with torch 2.6.0+cu124 (minor-version compatibility; config
   comment records this). The evidence host TASL-7 is driver 580.178.04; the rehearsal cannot validate GPU/driver
   behaviour for Unit B, and `torch.cuda.is_available()` was deliberately not re-invoked here to avoid a CUDA
   context on TASL-2 (it remains a recorded fact from the unit, consistent with the build/driver).
2. **Tiny CPU path is not the real path:** no real `kev-0.8b`/`qwen3.5-4b-base` weights, no GPU, no A3 budget-v2/
   `--a3-short`, no guarded runner/preflight/lease/marker/journal/budget, A1/A2/A5 N/A, and the v1 2k/8k descriptive
   rows are exercised only on the random stand-in. Nothing here transfers to evidence.
3. **Config host-specific values:** the config is the portal/TASL-2 config; `hf_home` is not read by the code; the
   tokenizer comes from the default HF cache (pinned revision present). `--check-config` checks placeholders only, not
   the registry/paths.
4. **TASL-2 is not the evidence host** (R1-TASL7-TRACKP; R1-TASL2-LOCK permits non-evidence work only). Track X
   evidence has priority on TASL-2 (R1-PORTAL-SCHEDULE): the run is CPU-only, but any CUDA probe (MAJOR-1) would
   violate the priority/lease discipline.
5. **Point-in-time host facts:** freeze equality, D HEAD/cleanliness, config digest and disk were true at
   2026-11-17T00:12–00:25Z; the unit's STOPs require re-checking them immediately before the run.
6. **Conditions on the result record:** it must cite the unit bytes `a6a2cba…` (and note that any edit voids it), the
   authority refs (`26177d82`, `origin/main` `16185b0b`), the exact scratch root, the exact argv, the host snapshot,
   the output hashes, the negative-guard outcome, the pre-existing `__pycache__` baseline, "no evidence label / no
   attempt-2 root / no TASL-7 touch / no GPU lease/marker", that TASL-2 is not the evidence host, and that the TASL-7
   Unit B DRYRUN remains mandatory. Keep the scratch root (no deletion).

## 8. Required revision before re-review

Apply BLOCKING-1 and BLOCKING-2 (and preferably MAJOR-1/2/3) exactly as above; the smallest acceptable revision is:
(1) add the env prefix `PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=` to both
commands; (2) restate step 1/2/3 scope so the unit is a host/environment/CLI readiness check of the tiny CPU
stand-in and explicitly does not rehearse the Unit B DRYRUN path / A3-short / guarded runner (or add the reviewed
pytest step (b) in the scratch); (3) replace the "no file outside" criterion with the exact baseline-based checks;
(4) replace the defect paragraph with the C2/D2 + TASL-7 re-verification + authority-amendment conditions; (5) write
the exact commands, the acceptance checklist (MAJOR-3) and the MINOR edits. Re-review of the revised bytes is then
required; this review accepts none of the changed bytes in advance.

## 9. Verdict

**Verdict: not accepted.** The unit is close and safe in principle — the command is a genuine CPU/DRYRUN/tiny path
with no GPU lease, no marker, no authorization note and no need for attempt-1 `final/saved` or a TASL-7 root, and
every host fact in §1 of the unit was re-verified exactly (freeze byte-identical to the committed 121-line pin,
D `8662e359` clean, config digest `64073cea…` with no placeholders, disk/models/HF cache present). But as written it
cannot meet its own "no file outside the scratch root" criterion (BLOCKING-1) and it does not exercise what it is
titled as rehearsing — Unit B's DRYRUN is the guarded-runner `--budget --a3-short --load` real `kev-0.8b` unit, not a
bare tiny command (BLOCKING-2); the CPU-only guarantee also depends on an inherited env var (MAJOR-1) and the
defect/result conditions are under-specified (MAJOR-2/3). Fix those items, then re-submit the exact revised bytes
for a fresh review.

---

Reviewer artifact; uncommitted at the time of writing. Canonical unit bytes reviewed:
`a6a2cba3cc2c2978335a308f8e3f8d497e4bd459774b242dd9064254c49a8f83` (60 lines). Review file sha256 and line count are
reported with the delivery of this review.
