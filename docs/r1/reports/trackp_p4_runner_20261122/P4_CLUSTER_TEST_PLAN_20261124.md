# Track P P.4 phase 1: cluster test plan for the runner and the H200 SFT probe (no P.4 training run)

Prepared by the Mac-desk agent (Claude), AI-assisted, 24 Nov 2026, for item 3 of the user's list. ENGINEERING_ONLY.
Desk work only: no GPU, no image pull, no server access, no label or evaluation file opened, nothing pushed. Every
repository search in this unit either named its paths or excluded `*block.jsonl`.

**Code basis:** branch `mac-trackp-p4-testplan-20261124`, rebased onto
`bb1a9eb006c523aa0ac604e34d672576f0a16142` (`bb1a9eb0`), the runner tip delivered as READY 101. `bb1a9eb0` is
`4315ab295` plus one docs commit (the runner's v2.2 review record and its full-suite list), so **its code is identical
to `4315ab29535c8844cae943fd1e17b738dc72b037` (`4315ab295`)**, the commit that review accepted. Below, "the code"
means that code. `4315ab295` is the P.4 runner (READY 82) merged onto `main` `3024db3f`, updated for image v2.2 and
R1-TRACKP-P4-RUNNER-DECISIONS (`df616ec63`), plus one commit of fixes after review round 1 of `df616ec6`. Three of
those fixes bear on this plan:
- `p4_switch.check_probe_hours` (new): the probe record must carry `p4_estimate_hours:` lines equal to the spec's
  `estimate.hours` (§4.4);
- `image.versions_sha256_comment` (new in the spec): the procedure for the `VERSIONS.txt` sha256 (T1, §5);
- the note's `env3_freeze:` line now names the admitted forms and the STOP forms (T2, S5).

This plan itself was accepted by independent review at `8d2f61c7d`, with eight minor findings; §9 maps them to the
fixes.

The runner is still under independent review and may change. If it changes, every command below must be checked
again against the new commit (STOP S1). None of `df616ec63`, `4315ab295` or `bb1a9eb0` is on any remote-tracking
ref of this checkout, so the cluster cannot clone them until the coordinating chat publishes them.

**Checked at the desk** (`/tmp/tgport312/bin/python`, `TMPDIR=/tmp/p4tpdev/t`, `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`):
- On `4315ab295` (the same code as `bb1a9eb0`):
  - `p4_lib.py validate r1/scripts/htcondor/trackp_p4/p4_spec.json` gives `"ok": true`, a projection of
    16.94 GPU-h and 24.41 slot-hours, and `within_cap: true`;
  - `p4_lib.py validate --launch …` gives `STOP: paper.commit must be filled (^[0-9a-f]{40}$)` with rc 2;
  - `trackp.py --config r1/scripts/configs/trackp_htcondor_v2.json --check-config` gives rc 1 and lists 19
    placeholders (§5).
- `sha256sum` of the host config gives `18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140`
  (unchanged by `4315ab295`; the spec says the same). The spec file `p4_spec.json` gives
  `04cfd06008e41792fa77250a552a26be073adab45201314a5db8e6d59963d59e` at `4315ab295`; that value changes when its
  fields are filled.
- `r1/tests/test_trackp_p4_runner.py` was run once, on `df616ec63`: 88 passed. I did not rerun it on `4315ab295`; the
  runner report gives 89 passed there.
- `4315ab295` does not change `p4_phase1.py`, `trackp_p4_test_path.py`, `p4_render_jdl.py`, `p4_job.sh`, `trackp.py`
  or the host config. The commands below are unchanged by it, except where stated.

**Terms for commits** (used the same way throughout):
- **code commit**: the commit that `paper.commit` names and that the note's `code_commit:` repeats. The P.4 jobs clone
  it. It carries the runner, the receipt-binding fix (F2), the probe mode, the filled host config with the test
  changes (F5), and the signed label-freeze record (F6).
- **host-config fill commit** (§6 step 4): the commit that fills the 19 host-config values, with the test changes and
  the probe mode. The probe clones it. It may be the code commit or an ancestor of it.
- **spec-fill commit** (§6 step 9): a later commit that changes only `p4_spec.json` and files under `docs/`. It is the
  HEAD of the checkout that renders the T8 stage, and `verify_launch_p4` compares it with the code commit. The spec's
  own `image.versions_sha256_comment` calls this "the launch commit". The spec's `paper.commit` placeholder ("the
  published launch commit carrying this runner") uses the same phrase for the code commit. This plan does not use the
  phrase.

## Status note, 25 Nov 2026 (added; the text below is unchanged except for the inline "[25 Nov 2026: …]" markers added to rows F1, F2, F5 and F7 of §1)

R1-P4-TESTPLAN-DECISIONS (25 Nov 2026 (b)) adopted P4-F2 A, P4-PROBE A, P4-PROBECAP A and P4-INCID A. The unit
`P4_F2_PROBE_HOSTCFG_20261125.md` (beside this plan; branch `mac-trackp-p4-f2-probe-20261125`) implements the
engineering items this plan lists as missing. It is under independent review, so "done" below means "written and
tested at the desk, not yet reviewed or on `main`":
- **F1 (probe mode): done.** `p4_lib.py probe` (`run_probe`), `p4_lib.py validate --probe` (probe strength,
  `validate_probe_spec`, which does not need `h200_sft_probe`), the probe spec template `p4_probe_spec.json`,
  `p4_probe.sh`, `p4_render_jdl.py --probe` (one base per stage, `kev-0.8b` first, the other bases gated on its sealed
  record) and `p4_lib.py probe-record` (the §4.4 record and the §4.5 hours). It follows §4.2 items 1-12, with the
  differences the unit report lists.
- **F2 (receipt/table binding): done** as P4-F2 A, in the job's step 5 and in the render (T5 and T8 now refuse
  another receipt table). S9's manual gate becomes a code gate once the unit is in the code commit.
- **F3:** answered on the cluster by T1 as planned. The probe keeps the job's unscoped `gpu_identity` (T7) and adds a
  check against the HTCondor-assigned `CUDA_VISIBLE_DEVICES` / `NVIDIA_VISIBLE_DEVICES`; its memory sampler is scoped.
- **F4:** kept as planned (device memory from outside by `nvidia-smi --id=<uuid>`); no change to the SFT path.
- **F5: done.** The tests pass for the placeholder and for a filled host config and spec; `test_trackp_sft.py` needed
  the same change (one assertion on `venv.causal_conv1d`), which this plan did not list. `verify_launch_p4` is
  unchanged: the host-config fill is its own reviewed commit before `paper.commit` (§6 step 4).
- **F7: fill hook done** (`p4_fill_host_config.py`); the values are still the cluster's.
- **§4.5 item 2** ("a manual check that the code does not make"): the code now makes it. `caps.probe_gpu_hours`
  (P4-PROBECAP A) is in the spec; launch validation, `charged_hours`, `assemble` and the switch's `check_cap` add it;
  the switch binds it to the probe record's `p4_probe_gpu_hours:` line and the note's `gpu_hours_cap:` line.
- **F6** is met on `main` (`C3_SWEEP1_LABEL_FREEZE_20261124.md`, signed at `20ccf7e3`, unchanged at `912a7e02`).

## 0. Which draft's §10

"The draft" is the P.4 phase-1 **authorization draft**,
`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` (revision 4.2). Its §10 is headed
**"## 10. Needs a cluster test (NEMO2 H200, image v2.1)"** and reads:

> - The diagnostic job, image v2.1, I2 and I3 on v2.1, then the Track P smoke and the E0 equivalence check on H200
>   (R1-TRACKP-IMAGE-V21, R1-QTORCH-AMEND; a prerequisite, P5).
> - The SFT fit and timing probe per base at the P4-MB micro-batch, 1,024 tokens, checkpointing off (P4-CAP's
>   assumption; P5).
> - The synthetic-label test-path run of the evaluator inside the job.
> - The output transfer and the seal of a job's `out.tar` (the I3 job held on output transfer once).
> - The free H200 slot shapes (I3 found only a 10-CPU chunk free) against the job's CPU and memory request.

The other documents were checked:
- The decision list `TRACKP_P4_PHASE1_DECISIONS_20261121.md` is a one-page table with no numbered sections.
- The note draft `TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md` has no numbered sections.
- The runner report's "Needs a cluster test" list is unnumbered, and says its items "also fall within the draft's §10
  and the SFT probe".

§10 names the probe; the same draft defines it in §2 ("The host …" paragraph):

> … then the **SFT fit and timing probe** (P5): a separate short ENGINEERING job (`sft-dev` under R1-TRACKP-SFT-DEV),
> built from the reviewed P3 job unit with the same image, identity checks and sealing, running one `sft-dev` per base
> on synthetic labels at the chosen micro-batch (P4-MB), ≤ 50 steps; its record feeds P5 before any P.4 job is
> submitted. It records peak memory and seconds per step, and an OOM or a step time that would break P4-CAP is a STOP.
> It is cluster training under R1-HTC-QTORCH, so it runs only after the smoke and E0 PASS.

Two readings this plan takes. The first is for the coordinating chat to confirm; the second is the **author's**
decision:
1. **Image.** §10 says image v2.1. Image v2.1 was superseded (R1-TRACKP-IMAGE-V22, R1-TRACKP-IMAGE-V22-B), and the
   runner refuses it (`validate_spec`: "image v2 and v2.1 are not the P.4 image"). This plan applies §10 to image
   v2.2, `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949`.
   §10's first bullet is done on v2.2 (I2 759993, I3 759994, smoke 759997, E0 760000, all PASS in
   `V22_BUILD_20261124.md`), except that the run records still lack an independent review (P5).
2. **"No training run."** The §2 probe takes up to 50 `sft-dev` optimizer steps on the H200. The draft itself calls
   that "cluster training under R1-HTC-QTORCH", and it orders the probe before signature (P5; P4-CAP A: "Recompute
   from the H200 probe before signature"). This plan reads the user's "no training run" as: no P.4 training job; no
   grid, selection or learning curve; no real labels; nothing kept that could count as a trained arm. The ≤ 50-step
   synthetic `sft-dev` is the probe itself (§4). **Whether that counts as "no training run" is the author's
   decision**, not the coordinating chat's. The probe does not run until the author has decided (§6 step 1, STOP S4).

## 1. Findings that block or shape the plan

| # | Finding | Effect |
|---|---|---|
| F1 | **[25 Nov 2026: done, see the status note.]** **No probe mode and no staged job without training.** `p4_lib.py` has four subcommands: `validate`, `job`, `seal` and `assemble` (quoted in §3). `job` always runs the full grid, selection and learning curve, and `run_job` first calls `validate_spec(spec, launch=True)`. Launch strength needs `estimate.source` to be an `h200_sft_probe:` record, so `job` cannot run before the probe exists. No flag such as a dry run, a "stop before training" option or a probe option exists. | The probe needs a new, reviewed mode or job (§4.2). Until then, the H200-side items of §10 and of the runner report can only be exercised by the real first-arm job, after signature. |
| F2 | **[25 Nov 2026: done under P4-F2 A, see the status note.]** **The accepted runner cannot run on the published sweep-1 train/dev release.** The runner accepted as READY 82/101 (code at `4315ab295`) requires, in `p4_lib.inputs` (`p4_lib.py:449-453`), that the receipt's `inputs.proposals_sha256` equal the `sweep1_v3` pin `d0048567…d1d5`, and raises `ProtocolStop` otherwise. The published receipt (`docs/r1/reports/release_20261122/RECEIPT_sweep1_traindev.json`, sha256 `f06e37a9…65c1`, the only sweep-1 train/dev receipt) binds `inputs.proposals_sha256` `b713c423…57c4`: the sealed v2 table, `arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256`. FEAT-ONE A (R1-ARMS-DECISIONS) keeps that sealed v2 table as the release's integrity artefact and joins labels to the v3 table by proposal id after an identity check. The runner review missed this: round 1 (22 Nov) asked for the receipt-to-table check as its finding 4, before the receipt existed (receipt `utc` 2026-11-23T09:23:16Z), so no round compared the check with the published receipt. **No other code catches it before a job runs:** neither the non-preview T8 render (`p4_render_jdl.check_inputs`, `p4_render_jdl.py:79-104`, which checks the partition and receipt sha256 against the spec and the receipt's source block, source and stage) nor `p4_switch.check` compares the receipt's table with the pin. | Every P.4 job, the solo `kev-0.8b` job first, would STOP at step 5 (`inputs`), before staging (`p4_lib.py:648-651`), with T8 and the switch passing. **This is a STOP before any signature (S9):** the author's binding decision and a reviewed runner change must land in the code commit first. It does not block the probe, which reads no label (§4.2, §6 step 7). |
| F3 | **`nvidia-smi` is called unscoped.** `gpu_identity` runs `nvidia-smi --query-gpu=…` and requires exactly one GPU. The trackp GPU lease (`run.foreign_compute_processes`) runs `nvidia-smi --query-compute-apps=…` on every visible GPU. The reviewed H200 smoke and E0 stages scoped both queries to the HTCondor-assigned UUID (`stages/smoke_h200/nvidia-smi-scoped`), after the smoke pre-submit review asked that an unscoped NVML query be shown to cover only the assigned H200. No committed record shows what unscoped `nvidia-smi` lists inside a NEMO2 container job. | T1, the read-only H200 job, runs both unscoped queries first, before any probe mode is written; T7 confirms them inside the probe. If more than one GPU, or a foreign process, is listed, the job STOPs (fail-closed), and the runner needs a reviewed change (STOP S6). |
| F4 | **`sft-dev` records seconds per step but not peak memory.** `Trainer.train` writes `step_s` for each step to `stage_s/metrics.jsonl`. No SFT path calls `torch.cuda.max_memory_allocated`. | The probe measures device memory from outside with `nvidia-smi` sampling (§4.3). If the author wants PyTorch's own peak instead, that needs a code change, which this plan does not make. |
| F5 | **[25 Nov 2026: done, see the status note.]** **Tests pin today's placeholders.** `test_the_shipped_spec_host_config_and_note_draft_name_image_v22` asserts that the host config still holds `TODO_VERIFY_ON_HOST` and that the spec's cluster fields are placeholders. `test_shipped_spec_validates_and_refuses_launch_until_filled` expects launch validation of the shipped spec to STOP on `paper.commit`. `verify_launch_p4` lets the launch checkout differ from the code commit (`paper.commit`) only under `docs/` and in the spec file. | The host-config fill commit must change these tests in the same commit, and the changed tests must pass for both the placeholder spec and the filled spec, because the later spec-fill commit may not touch tests. That is a code change for review under P3. |
| F6 | **The signed label-freeze record must be in the code commit's tree.** `inputs` reads `labels.freeze_record.path` from the job's clone at `paper.commit`. | The signed `C3_SWEEP1_LABEL_FREEZE_<date>.md` must be on `main` at or before the commit chosen as `paper.commit`. No such file is on `main` `3024db3f`. |
| F7 | **[25 Nov 2026: fill hook done; values still open.]** **All 19 host-config placeholders must be filled**, including bases that P.4 never stages (`laya`, `startlux-0.8b`, `startlux-2b`, `startlux-4b`). `configs` STOPs when `--check-config` lists any placeholder. | The coordinating chat chooses values for the unused bases (§5.2). |
| F8 | **The v2.2 run records have no independent review yet.** The v2.2 review on `main` covers the Dockerfile and workflow diff. | The draft orders the probe after the smoke and E0 PASS, "each independently reviewed" (P5, R1-HTC-QTORCH). The probe waits for that review (STOP S4). |
| F9 | `p4_render_jdl.py --preview` still needs the real table files and the receipted partition with its `RECEIPT.json` (`check_inputs`), and it checks the receipt's source block. | The preview render runs only on the host that holds both (deepthought). |
| F10 | The `p4_lib.py seal` command line has no option for another sealed root. It always uses `/ceph/srv/dwong/paperb/trackp_p4/<run_id>/<arm>/attempt-N`. | Probe outputs, if sealed with it, must carry a spec whose `run_id` is not the P.4 run's (§4.2). `charged_hours` and `assemble` then never count them. |

## 2. Preconditions

What must be on `main` before each kind of step, and whether that step may run before the phase-1 note is signed.
None of the cluster tests or the probe may run the P.4 job (`p4_job.sh`, `p4_lib.py job`, `p4_switch.py submit`),
build data from real labels, or run an `sft-dev` without `--steps`.

| Item | State at `3024db3f` / `bb1a9eb0` | Needed before |
|---|---|---|
| The runner (READY 82 plus the v2.2 and RUNNER-DECISIONS update) on `main` | Not on `main`; accepted at `4315ab295` (READY 101, tip `bb1a9eb0`); not published | Any **job** step: `clone_full` requires the commit on `origin/main`. Desk and host checks (T0–T6) may run from a published review commit, recorded by hash. |
| R1-TRACKP-P4-DECISIONS (P4-PHASE1-TEST A, P4-P1SPLIT A, P4-LABELS A, P4-ARMS A, **P4-MB A**, P4-JOB A, P4-LC A, **P4-CAP A**) | On `main`. P4-CAP and P4-MB are decisions inside this row, not separate PLAN rows (no `P4-CAP` or `P4-MB` row exists) | Already met |
| R1-TRACKP-P4-RUNNER-DECISIONS | On `main` (`ffe1edff`) | Already met |
| R1-TRACKP-IMAGE-V22-B, R1-TRACKP-IMAGE-V22, R1-TRACKP-IMAGE-V21, R1-TRACKP-V21-FREEZE, R1-HTC-QTORCH and the rest of `p4_lib.PLAN_ROWS` (11 rows) | All on `main` (the runner test checks this checkout's `PLAN.md`) | Already met |
| Independent review of the v2.2 run records (I2 759993, I3 759994, smoke 759997, E0 760000) | Pending | The probe (§4) |
| The probe mode or job (F1), reviewed | Does not exist | The probe (with the host-config fill commit) |
| Host-config fill commit, with the test changes of F5, reviewed | Not done | The probe (trackp refuses a real run on a config with placeholders) and T3. The probe needs nothing else from `main`: not F2, not the freeze record, not P2 |
| Decision and runner change for the receipt/table binding (F2) | Not decided | **Before any signature** (STOP S9): the code commit must carry the reviewed fix. Not needed for the probe |
| The signed sweep-1 label-freeze record (`docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md`, P1) | **Not on `main`** (no such file) | `validate --launch`, the non-preview render (T8) and the note's P1. It must be in the code commit's tree (F6). Not needed for T0–T6 or the probe. |
| Sweep-1 train/dev release receipt and partition (P1) | Released (`SWEEP1_TRAINDEV_RELEASE_20261123.md`; receipt `f06e37a9…65c1`, partition `6a6327a3…7b2a`; review ACCEPTED) | T5 and T8 (on deepthought); the spec's `labels` fields; but see F2 |
| P.3a records per Kev base (P2) | Not cited yet | The note's `arms:` line. If they remove `kev-0.8b`, the runner STOPs and the question goes to the author. |
| Runner review at the code commit (P3) | Accepted at `4315ab295`; to be repeated at the code commit | Signature |

**May run before signature:** T0–T6 and T8 (desk and deepthought checks, and the read-only T1 job; no training) and the probe (§4),
once its own preconditions are met. **May not run before signature:** `p4_switch.py check` (it needs the signed note
on `origin/main`), `p4_switch.py submit`, `p4_job.sh`, `p4_lib.py job`, and any P.4 training job.

## 3. The runner's cluster tests

### 3.1 Command-line definitions this plan relies on (the code of `bb1a9eb0` = `4315ab295`)

`r1/scripts/htcondor/trackp_p4/p4_lib.py`, `main`:
```
v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
j = sub.add_parser("job"); j.add_argument("spec"); j.add_argument("--arm", required=True)
z = sub.add_parser("seal"); z.add_argument("job_output"); z.add_argument("spec"); z.add_argument("--arm", required=True)
a = sub.add_parser("assemble"); a.add_argument("spec"); a.add_argument("sealed", nargs="+")
```
`r1/scripts/htcondor/trackp_p4/p4_render_jdl.py`, `main`:
```
ap.add_argument("spec", type=Path)
ap.add_argument("stage_dir", type=Path)
ap.add_argument("--table", type=Path, required=True)
ap.add_argument("--partition", type=Path, required=True)
ap.add_argument("--preview", action="store_true")
```
`r1/scripts/htcondor/trackp_p4/p4_switch.py`, `main` (not run before signature):
```
c = sub.add_parser("check"); c.add_argument("--stage", required=True); c.add_argument("--note", required=True)
s = sub.add_parser("submit"); s.add_argument("--stage", required=True); s.add_argument("--note", required=True)
s.add_argument("--enable", action="store_true"); s.add_argument("--arm", default=None)
s.add_argument("--first-record", type=Path, default=None)
```
`r1/scripts/trackp.py`, `main`: the top-level `--config`, `--check-config` and `--allow-placeholders`; per
subcommand `--run-dir`, `--base`, `--seed` (default 0), `--steps` (int), `--lr` (float) and `--eval-every` (int); for
the `sft*` subcommands also `--data`, `--table`, `--table-pin` (default `sweep1_v3`), `--sweep`, `--paper-root`,
`--classification`, `--labels` ("an audit's label_block.jsonl, or 'synthetic'"), `--label-sweep` and
`--label-freeze`. `--check-config` prints `{"config", "placeholders", "sha256"}` and returns 0 only with no
placeholder (or with `--allow-placeholders`). **Its `sha256` is `run.config_digest` (canonical JSON), not the file's
sha256.** The spec and the note need the file's sha256 (`p4_lib.configs` compares `_sha_file`), so use `sha256sum`.

`r1/scripts/trackp_p4_test_path.py`, `parse`: `--data`, `--table`, `--run`, `--arm`, `--sweep`, `--paper-root`,
`--classification`, `--host-config`, `--ledger-dir` and `--out` (all required), and `--seed` (default 0). It is called
only by `p4_lib.test_path`, after training, inside `run_job`.

Where the plan calls a library function directly (`p4_lib.env3_freeze`, `p4_lib.check_local_paths`,
`p4_lib.stage`), it says so. Those functions exist in the code of `bb1a9eb0`; no command-line mode exposes them.

### 3.2 Common setup on deepthought (the HTCondor submit host)

As in earlier records: `/work` and `/ceph` are mounted, apptainer is 1.5.5, `condor_submit` is installed, and the
staging directories are under `/work/dwong/paperb/work/` (`V21_SUBMISSION_LOG.md`, `verify_images.sh`).
`YYYYMMDD` is the day of the run, and `COMMIT` is the published commit under test, set by the coordinating chat.
```
set -o pipefail      # in "cmd | tee file", the status is cmd's when cmd fails, not tee's
export GIT_TERMINAL_PROMPT=0 PYTHONDONTWRITEBYTECODE=1
export APPTAINER_CACHEDIR=/work/dwong/paperb/.apptainer/cache APPTAINER_TMPDIR=/work/dwong/paperb/.apptainer/tmp
D=/work/dwong/paperb/work/trackp-p4-cluster-YYYYMMDD          # new and empty; no overwrite
C=$D/paper                                                    # the checkout under test
COMMIT=<40-hex commit set by the coordinating chat>
IMG=ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949
SIF=$D/r1-htc-gpu-v22.sif
mkdir -p "$D" "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
git clone --quiet --no-checkout https://github.com/dowlingwong/Agent_paper_B.git "$C"
git -C "$C" checkout --quiet --detach "$COMMIT" && test "$(git -C "$C" rev-parse HEAD)" = "$COMMIT"
test -z "$(git -C "$C" status --porcelain)"
apptainer pull --disable-cache "$SIF" "docker://$IMG"
PY="apptainer exec --bind /work,/ceph $SIF /opt/r1/envs/trackp/bin/python -B"   # env3 of image v2.2 (Python 3.12)
```
Every command block below runs in this shell, with `set -o pipefail`, so the exit status of each `cmd | tee file`
line is the command's. Record it right after the line (`echo "rc=$?"`). Where a loop records an rc, it takes
`${PIPESTATUS[0]}` on the line itself. A plain `$?` after `| tee`, without `pipefail`, would be tee's status, almost
always 0. The probe commands (§4.3) have no pipe. Every Python step runs in env3 of the image, because `p4_lib` hard-codes `/opt/r1/envs/trackp/bin/python` and
`/opt/uv/uv`, and deepthought's system Python is 3.9. Results go to a new cluster report directory
**`docs/r1/reports/trackp_p4_cluster_YYYYMMDD/`** on a cluster branch `trackp-p4-cluster-YYYYMMDD`, never directly on
`main`; the coordinating chat merges it. Never commit label files, staged copies of the partition, model weights or
checkpoints.

### 3.3 The tests

**T0 — desk checks (any machine, any checkout of `COMMIT`; no GPU).**
```
cd "$C"
bash -n r1/scripts/htcondor/trackp_p4/p4_job.sh
$PY r1/scripts/htcondor/trackp_p4/p4_lib.py validate r1/scripts/htcondor/trackp_p4/p4_spec.json
$PY r1/scripts/htcondor/trackp_p4/p4_lib.py validate --launch r1/scripts/htcondor/trackp_p4/p4_spec.json
```
- Expected today: `bash -n` gives rc 0. `validate` gives `"ok": true` with 16.94 GPU-h and 24.41 slot-hours.
  `validate --launch` gives rc 2 and `STOP: paper.commit must be filled (^[0-9a-f]{40}$)`. After all fills (§6 step
  9), `validate --launch` must give rc 0.
- Pass: exactly these outputs.
- Committed as `T0_validate.txt`.

**T1 — the image's `VERSIONS.txt` sha256 (an HTCondor job on NEMO2 in the v2.2 gpu image; reads one file; no
training).** This fills `image.versions_sha256` in the spec and `versions_sha256:` in the note. The procedure is the
one in the spec's `image.versions_sha256_comment` and in the runner report (review m1) at `4315ab295`:

> the cluster agent runs `sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt` inside the digest-pinned v2.2 gpu
> image on NEMO2, as an HTCondor job with the same header as the staged smoke
> (docs/r1/reports/trackp_h200_20261118/stages/smoke_h200/probe.jdl: universe = container, container_image =
> docker://<this image.digest>, the NEMO2 requirements); there is no explicit apptainer command in those scripts,
> HTCondor runs the container. It commits the VERSIONS.txt text together with that sha256 line (or commits the
> handback captures of 759994/759997/760000, whose probe scripts cat /opt/r1/VERSIONS.txt, with the sha256 of the
> exact file). The I2 identity's versions_sha256 is of the cpu image and does not apply.

*Route A (a new job).* Submitted from a new directory `$D/T1_versions` on deepthought. The header lines are those of
the committed smoke `probe.jdl`, with the digest changed to v2.2. The executable, arguments, inputs and outputs are
this job's own. The resource lines are kept as in the smoke header, including `request_GPUs = 1` and the H200 term, so
that the file is read on the same kind of slot that the P.4 jobs use. This is a new staged job, so it needs the usual
pre-submit check, as the smoke and E0 stages had.
```
# $D/T1_versions/versions.sh
#!/bin/bash
set -uo pipefail     # no -e: a failing nvidia-smi query is recorded, not fatal
sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt || exit 2
# F3: the two unscoped queries the P.4 job runs, to a separate file so that versions.out stays exact
{
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES-unset}"
  echo "NVIDIA_VISIBLE_DEVICES=${NVIDIA_VISIBLE_DEVICES-unset}"
  echo "== p4_lib.gpu_identity query =="
  nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,compute_cap --format=csv,noheader; echo "rc=$?"
  echo "== run.foreign_compute_processes query =="
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader; echo "rc=$?"
} > gpu_visibility.txt 2>&1
exit 0
```
```
# $D/T1_versions/versions.jdl
universe = container
container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949
executable = versions.sh
requirements = (TARGET.CloudSite =?= "BwForCluster-Nemo2") && (TARGET.GPUs_DeviceName =?= "NVIDIA H200")
+RemoteJob = True
request_GPUs = 1
request_cpus = 4
request_memory = 16000
request_disk = 35000000
+RequestWalltime = 3600
periodic_hold = (NumJobStarts > 1)
job_machine_attrs = CloudSite
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
output = versions.out
error = versions.err
log = versions.log
transfer_output_files = gpu_visibility.txt
queue 1
```
```
cd "$D/T1_versions" && chmod 0755 versions.sh
condor_submit -dry-run versions.dry versions.jdl      # rc 0, JobUniverse = 5, the v2.2 ContainerImage
condor_submit versions.jdl                            # after the pre-submit check
# when the job has left the queue:
head -1 versions.out | tee T1_versions_sha256.txt      # "<64 hex>  /opt/r1/VERSIONS.txt"
tail -n +2 versions.out > T1_VERSIONS.txt
sha256sum T1_VERSIONS.txt                             # must equal the first field of line 1
```
- Expected: exit 0. Line 1 of `versions.out` is `<64 hex>  /opt/r1/VERSIONS.txt`, and the rest is the file itself, so
  `sha256sum T1_VERSIONS.txt` gives the same value. That equality is the check that the committed text is the exact
  file. The text holds, among others, `trackp_gpu_freeze_sha256=50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`,
  `env3_sorted_diff=empty`, `torch_actual=2.6.0+cu124` and an `env3_causal_conv1d_arch=` line. Those field names are
  from the v2 image's VERSIONS in `i3_identity.txt`; v2.2 adds lines per `V22_BUILD_20261124.md`.
- Pass: the job exited 0, the two sha256 values are equal, and the lines above read as stated.
- **F3 in the same job.** `gpu_visibility.txt` holds the two queries exactly as the job runs them:
  `p4_lib.gpu_identity` runs `nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,compute_cap
  --format=csv,noheader`, and `run.foreign_compute_processes` (the trackp GPU lease) runs
  `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader`. Both are unscoped, with no
  `--id`. Pass for F3:
  - the first query prints exactly one line, `NVIDIA H200`, with a uuid equal to `CUDA_VISIBLE_DEVICES`;
  - the second prints nothing (no compute process), and both give `rc=0`.

  More than one GPU line, or a process listed, confirms F3: the runner then needs a reviewed scoping change, as the
  smoke and E0 stages had, before any probe mode is written on top of these steps (STOP S6). Existing evidence, read
  by grep on that one line only: the I3 job on image v2 (`docs/r1/reports/trackp_h200_20261118/i3_h200_20261121/i3_identity.txt`,
  line 55) recorded `NVIDIA_VISIBLE_DEVICES=GPU-a853e181-a8f1-aa6f-88d9-ba45c981e34d`, a single UUID. That shows the
  container was given one GPU. It does not show what unscoped NVML lists inside the container, which is what T1
  answers.
- *Route B (no new job).* Commit the handback captures of 759994, 759997 or 760000, whose probe scripts
  `cat /opt/r1/VERSIONS.txt`, with the sha256 of the exact file. The `sha256sum` of the extracted text must give the
  value. The capture is valid only if it holds the file byte for byte; a log interleaved with other output does not,
  so Route A is the safer route. No such capture is committed today.
- Not this value: the I2 identity's `versions_sha256` (`s4_run.sh`), which is of the cpu image.
- An optional second reading on deepthought, same image digest: `apptainer pull --disable-cache "$SIF" "docker://$IMG"`
  then `apptainer exec "$SIF" sha256sum /opt/r1/VERSIONS.txt` (the `verify_images.sh` pattern). It must give the
  same value; a difference is STOP S5. It does not replace Route A or B.
- Confirmation on the H200: `p4_lib.image_identity` compares the in-job file with the spec value (step 1 of the job
  and of the probe, T7). A difference there is STOP S5.
- Committed: `versions.jdl`, `versions.sh`, `T1_versions_sha256.txt`, `T1_VERSIONS.txt`, `gpu_visibility.txt`, the
  job id and the `condor_history` exit record. The file is image metadata, with no secret.

**T2 — the env3 freeze in the image (deepthought, in the image; no GPU).** This is runner-report item 1 ("the env3
`uv pip freeze` line format in the image"). It calls the job's own step-3 function, `p4_lib.env3_freeze`, which runs
`/opt/uv/uv pip freeze --python /opt/r1/envs/trackp/bin/python` and `p4_phase1.check_env3_freeze` against the clone's
pinned freeze (sha256 `50238e5a…`).
```
cd "$C"
$PY -c "import sys, json; from pathlib import Path; sys.path.insert(0, 'r1/scripts/htcondor/trackp_p4'); import p4_lib as L; print(json.dumps(L.env3_freeze(L.load_spec(Path('r1/scripts/htcondor/trackp_p4/p4_spec.json')), Path('.')), indent=1, sort_keys=True))" | tee "$D/T2_env3_freeze.json"
apptainer exec "$SIF" /opt/uv/uv pip freeze --python /opt/r1/envs/trackp/bin/python > "$D/T2_env3_freeze.txt"
```
- Expected: `"status": "identical"`, `"image_line": "causal-conv1d==1.7.0"`, `"local_label": null`, `"lines": 121`,
  `"pinned_sha256": "50238e5a…"`, rule R1-TRACKP-V21-FREEZE and decision R1-TRACKP-P4-RUNNER-DECISIONS (1).
- The note's `env3_freeze:` line at `4315ab295` states the rule the code applies (`check_env3_freeze`):
  - **admitted**: exactly one causal_conv1d line, either `causal-conv1d==1.7.0` or `causal-conv1d==1.7.0+LABEL`, where
    `LABEL` is a PEP 440 local label (letters and digits in dot-separated segments). The line and any label are
    recorded in the job record's `env3_freeze`; a label is disclosed in the P.4 report. Every other line must match
    the pin exactly;
  - **STOP forms**: a direct reference (`causal-conv1d @ file://…` or `causal-conv1d @ https://…`, even to a file of
    version 1.7.0); the `causal_conv1d==1.7.0` spelling; any other version or operator; a malformed label; a removed or
    added causal_conv1d line; any other difference.
- Pass: as expected (`identical`, bare line, no label), which is what the note says image v2.2 is expected to give. A
  `causal_conv1d_only` result with a well-formed local label is admitted by the rule, but it contradicts the v2.2
  build record ("installed by name", `env3_sorted_diff=empty`). Report it and wait for the coordinating chat before
  going on (STOP S5). Any `STOP:` (one of the STOP forms above) is STOP S5. Check the raw line in
  `T2_env3_freeze.txt` too: `grep -i '^causal' T2_env3_freeze.txt` must print exactly `causal-conv1d==1.7.0`.
- Committed: `T2_env3_freeze.json` and `T2_env3_freeze.txt`.

**T3 — the host config after the `TODO_VERIFY_ON_HOST` fill (deepthought, in the image; no GPU).** Run on the checkout
of the host-config fill commit (§6 step 4). This covers runner-report item 2 ("the host config's local paths relative to the job
directory") at the level of path logic. `check_local_paths` only joins and resolves paths, so a non-existent job
directory is enough.
```
cd "$C"
$PY r1/scripts/trackp.py --config r1/scripts/configs/trackp_htcondor_v2.json --check-config | tee "$D/T3_check_config.json"
sha256sum r1/scripts/configs/trackp_htcondor_v2.json | tee "$D/T3_host_config_sha256.txt"
$PY -c "import sys, json; from pathlib import Path; sys.path.insert(0, 'r1/scripts/htcondor/trackp_p4'); import p4_lib as L; print(json.dumps({a: L.check_local_paths(a, Path('.'), Path('/nonexistent/condor/execute/dir_0')) for a in L.ARMS}, indent=1))" | tee "$D/T3_local_paths.json"
```
- Expected: `--check-config` gives rc 0 and `"placeholders": []`. `T3_local_paths.json` maps each of the four arms
  to `/nonexistent/condor/execute/dir_0/models/<registry key>`, with no `STOP:`.
- Pass: as expected, and the file sha256 is the value that later goes into `host_config.sha256` and the note's
  `host_config:` line.
- Committed: the three files.

**T4 — the staging step (deepthought, in the image; network to Hugging Face; no GPU; optional).** This is the part of
runner-report item 3 ("staging speed and the transfer of a 4B base") that deepthought can show: the registry sizes and
sha256, the curl route, and the pool tokenizers going into `HF_HOME`. It calls `p4_lib.stage`, the job's step 6. The
execute node's network is not deepthought's, so the H200-side timing comes from the probe's staging step (T7). It
needs about 10 GB under `$D` for the 4B pair. Run it only with the coordinating chat's go.
```
cd "$C"
for ARM in kev-0.8b kev-4b; do
  mkdir "$D/T4_stage_$ARM"; T0=$(date +%s)
  $PY -c "import sys, json; from pathlib import Path; sys.path.insert(0, 'r1/scripts/htcondor/trackp_p4'); import p4_lib as L; print(json.dumps(L.stage(L.load_spec(Path('r1/scripts/htcondor/trackp_p4/p4_spec.json')), sys.argv[1], Path('.').resolve(), Path(sys.argv[2])), indent=1))" "$ARM" "$D/T4_stage_$ARM" | tee "$D/T4_stage_$ARM.json"; RC=${PIPESTATUS[0]}
  echo "arm=$ARM rc=$RC seconds=$(( $(date +%s) - T0 ))" | tee -a "$D/T4_timing.txt"
done
```
- Expected: rc 0, and for each arm every registry file of its adapter and base listed with its sha256. The control
  arms stage a subset (the bases only).
- Pass: no `STOP:`. Record the bytes (`du -sb "$D"/T4_stage_*/models`) and the seconds.
- Committed: `T4_stage_*.json` and `T4_timing.txt`. Never commit the weights; they stay under `$D`.

**T5 — the preview stage (deepthought, in the image; no GPU, no submission).** This renders the four JDLs and the stage
manifest from the current spec, placeholders allowed. The table and partition paths are those in the SFT config
(`sweep1_v3.host_path`) and in the release command's `--out` (`SWEEP1_TRAINDEV_RELEASE_20261123.md`), with the
`<release root>/sweep1/traindev/` layout of the draft's §2 (P4-LABELS).
```
cd "$C"
T=/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z
R=/work/dwong/s2_release_20261123/release_sweep1_traindev/sweep1/traindev
$PY r1/scripts/htcondor/trackp_p4/p4_render_jdl.py r1/scripts/htcondor/trackp_p4/p4_spec.json "$D/T5_stage_preview" --table "$T" --partition "$R" --preview | tee "$D/T5_manifest_stdout.json"
```
- Expected: rc 0. The new directory holds `p4_job.sh`, `p4_lib.py`, `p4_spec.json`, the three table files,
  `label_block.traindev.jsonl`, `RECEIPT.json`, `p4_<arm>.jdl` for the four arms, and `STAGE_MANIFEST.json`
  (`"preview": true`). The manifest's `inputs` give `proposals.jsonl` `d0048567…d1d5` and `configs.json` `b585b727…82df`
  (the pins), `build.json` recorded (the SFT config records `7f56619c…1b643` on deepthought), and the partition
  `6a6327a3…7b2a` and receipt `f06e37a9…65c1`. Each JDL has `executable = PREVIEW_NOT_SUBMITTABLE_p4_job.sh`, the v2.2
  digest, `request_GPUs = 1`, `request_cpus = 8`, `request_memory = 131072`, `request_disk = 150000000`, the H200
  requirement, `periodic_hold = (NumJobStarts > 1)` and the transfer lists of `p4_lib`. `+RequestWalltime` follows the
  current estimate: 6282 s for the 0.8B arms and 37656 s for the 4B arms.
- Pass: as expected. A preview (like the non-preview T8 render) checks the receipt's source block, source and stage,
  but **not** the receipt's table. With the published receipt, T5 and T8 therefore pass while every P.4 job would
  STOP at `inputs` (F2). Do not scheduler-dry-run a preview JDL: its executable name does not exist by design.
- Committed: `STAGE_MANIFEST.json`, the four JDLs and `T5_manifest_stdout.json`. Never commit the staged label
  partition or receipt copy; the stage directory stays on `/work`.

**T6 — H200 slot shapes (deepthought; read-only).** This is §10 item 5 ("free H200 slot shapes … against the job's CPU
and memory request"). It uses the `condor_status … -af` form of `gpu_availability.sh`, which notes that this pool's
`condor_status` has no `-af:j`.
```
condor_status -constraint 'GPUs_DeviceName =?= "NVIDIA H200"' -af Name CloudSite State Activity Cpus Memory Disk GPUs | tee "$D/T6_h200_slots.txt"
```
- Expected: at least one slot with `Cpus ≥ 8`, `Memory ≥ 131072` (MB) and `Disk ≥ 150000000` (KB). The P.4 request
  is `p4_spec.json` `layout`.
- Pass: such a slot exists, or is recorded as "would match if drained". If none can match, report it and do not relax
  the request (STOP S11).
- Committed: `T6_h200_slots.txt`, with the UTC time of the snapshot. The P.4 JDL has no `CloudSite` term (the earlier
  H200 JDLs had one); the snapshot also shows whether any H200 slot exists outside NEMO2.

**T7 — the H200-side checks (NEMO2 H200; needs the probe mode of F1).** These are the H200 parts of runner-report
items 1–3 and 5 and of §10 item 4. No command in the code of `bb1a9eb0` runs them without training, so they are done inside the
probe jobs (§4), whose mode must reuse these job steps unchanged and record their outputs:
- `image_identity`: the in-job `VERSIONS.txt` sha256 equals T1's value.
- `gpu_identity`: unscoped `nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,compute_cap
  --format=csv,noheader` lists **exactly one** `NVIDIA H200` (F3; answered first by T1).
- `host_identity`: non-root uid.
- `clone_full`: a full clone at the commit, `origin/main` fetched, not shallow, on main, clean.
- `env3_freeze`: as T2, inside the job.
- The host-config sha256 and `--check-config` clean, as in `configs`.
- `stage` and `check_local_paths`: the staging seconds and bytes for each base on the execute node.
- Then `out.tar`, `job_record.json` and `SHA256SUMS`, transferred back. If the probe mode writes them in the
  `trackp_p4_job_record/1` form, they are sealed with:
  ```
  $PY "$C/r1/scripts/htcondor/trackp_p4/p4_lib.py" seal <probe job output dir> <probe spec> --arm <arm>
  ```
  The probe spec must use a run id other than `trackp-p4-p1-20261122-a` (F10).

Pass: every step STOP-free, with the identity values equal to T1–T3. Committed with the probe record (§4.4).

**T8 — the launch-strength stage and the scheduler dry run (deepthought; no submission; after every spec fill).** Run
on the checkout of the spec-fill commit (§6 step 9).
```
cd "$C"
$PY r1/scripts/htcondor/trackp_p4/p4_lib.py validate --launch r1/scripts/htcondor/trackp_p4/p4_spec.json | tee "$D/T8_validate_launch.json"
$PY r1/scripts/htcondor/trackp_p4/p4_render_jdl.py r1/scripts/htcondor/trackp_p4/p4_spec.json "$D/T8_stage" --table "$T" --partition "$R" | tee "$D/T8_manifest_stdout.json"
cd "$D/T8_stage"
for ARM in kev-0.8b kev-4b qwen3.5-0.8b-base qwen3.5-4b-base; do
  condor_submit -dry-run "$D/T8_dryrun_$ARM.ad" "p4_$ARM.jdl" | tee "$D/T8_dryrun_$ARM.log"; RC=${PIPESTATUS[0]}
  echo "arm=$ARM rc=$RC" | tee -a "$D/T8_dryrun_rc.txt"
done
```
- Expected: `validate --launch` gives rc 0. The render gives rc 0 with `"preview": false`. Each dry run gives rc 0 and
  "1 job(s) dry-run". The ad shows `JobUniverse = 5`, `WantContainer = true`, the v2.2 `ContainerImage`,
  `RequestGPUs = 1`, `RequestCpus = 8`, `RequestMemory = 131072`, `RequestDisk = 150000000`, the H200 requirement and
  each arm's `RequestWalltime` from the recomputed estimate.
- Pass: as expected, and the staged `p4_spec.json` is byte-identical to the committed spec (the switch checks this at
  submit).
- **Do not run `p4_switch.py check` or `submit` here.** `check` needs the signed note on `origin/main`.
- Committed: `T8_validate_launch.json`, `STAGE_MANIFEST.json` (its sha256 is recorded with every later submission),
  the four JDLs, and the dry-run logs and ads. Keep `$D/T8_stage` unchanged on `/work`: it is the candidate stage for
  `p4_switch.py check` after signature. A stage is never re-rendered in place (`p4_render_jdl.stage` refuses a
  non-empty directory).

**T9 — not testable before signature with the code of `bb1a9eb0`.** These are exercised first by the solo `kev-0.8b`
job after signature (R1-TRACKP-P4-RUNNER-DECISIONS (3)), unless the coordinating chat adds them to a no-training
mode:
- the synthetic test path with a real base on the H200 (§10 item 3; runner-report item 4). It is `p4_lib.test_path`,
  step 10 of `run_job`, which runs `trackp_p4_test_path.py` after a 2-step `sft-dev` (`--steps 2 --eval-every 1`). It
  reads no real label (P4-PHASE1-TEST A), but it replays the test instances' prompts, so this plan keeps it out of
  the probe;
- the output transfer and seal of a full job's `out.tar` (§10 item 4; runner-report item 5), unless the probe mode
  covers the format (T7).

## 4. The SFT probe per base at micro-batch 8 (the draft's §2 and §10)

### 4.1 What the draft fixes

- One `sft-dev` per base, **on synthetic labels**, at **micro-batch 8** (P4-MB A; host config `sft.micro_batch: 8`;
  effective batch 16), **≤ 50 steps**.
- The prompt budget is 1,024 tokens (`trackp_sft.json` `prompt.max_tokens`), with **checkpointing off**. `_stage_s`
  never enables gradient checkpointing; the host config's `gpu.gradient_checkpointing: true` serves the E0 path. This
  is Finding 1 of the TASL-2 trial, quoted in the draft's §1.
- It records **peak memory** and **seconds per step**. An OOM, or a step time that would break P4-CAP, is a STOP.
- It is "built from the reviewed P3 job unit with the same image, identity checks and sealing", and runs only after
  the smoke and E0 PASS and their review.
- Bases: the spec's `arms`. **`kev-0.8b` first and alone** (as decision (3) does for the P.4 jobs). Then `kev-4b`,
  `qwen3.5-0.8b-base` and `qwen3.5-4b-base`, each only after the `kev-0.8b` probe record is STOP-free.

### 4.2 What is missing, and what the probe mode must do

In the code of `bb1a9eb0` no command runs this (F1). A small unit must add a probe mode, reviewed and merged on `main` before the
probe, with its own HTCondor job. Examples are a `probe` subcommand of `p4_lib.py`, or a hand-staged `probe.sh` and
JDL in the style of the reviewed smoke and E0 stages that imports `p4_lib`. This plan does not write it: it is more
than a tiny helper, and it needs its own review. To satisfy "built from the reviewed P3 job unit", the mode should
call the existing functions, in this order, and add nothing to the training path:

1. `image_identity`, `gpu_identity`, `host_identity` (T7).
2. `clone_full(commit, job_dir/"paper")`, at the host-config fill commit (published on `main`), which carries the
   filled host config and the probe mode.
3. `env3_freeze`.
4. The host-config sha256 against the probe spec, and `trackp.py --check-config` clean (as `configs`).
5. `stage(spec, arm, clone, job_dir)` and `check_local_paths(arm, clone, job_dir)`.
6. The transferred table files `proposals.jsonl`, `configs.json` and `build.json` moved to `job_dir/table`. The probe
   transfers **no** `label_block.traindev.jsonl` and **no** `RECEIPT.json`, and does not call `inputs` (that step reads
   labels and the freeze record).
7. `data_build(clone, job_dir, {"table_dir": …}, synthetic=True)`, which runs the `sft-data … --labels synthetic`
   command of §4.3.
8. One `sft_dev(clone, job_dir, arm, data, 1e-05, 0, run_dir, extra=("--steps", "50"))`, the command of §4.3, with the
   memory sampler and wall-clock stamps around it. `p4_lib.trackp` classifies a CUDA OOM as `ArmStop` and keeps the
   log.
9. No `test_path`, no `sft-select`, no learning curve, no bootstrap, no `arm_pin`.
10. `out.tar` holding only the logs, `report.json`, `manifest.json`, `stage_s/sft_report.json`,
    `stage_s/metrics.jsonl`, `stage_s/best.json`, the data directory's `sft_data.json` and the memory samples. It holds
    **no** `stage_s/ckpt/` and **no** `stage_s/best/` weight files: those stay in the job scratch, which HTCondor
    removes at job end. Then `job_record.json` (with a probe schema or `trackp_p4_job_record/1`) and `SHA256SUMS`.
11. A probe spec, committed and reviewed with the probe mode, with the same image, env3, host config, SFT config,
    table and `layout` as `p4_spec.json`, but a run id such as `trackp-p4-probe-YYYYMMDD-a`. Its sealed attempts then
    fall under `/ceph/srv/dwong/paperb/trackp_p4/trackp-p4-probe-YYYYMMDD-a/`, outside the P.4 run's tree (F10).
12. **The probe spec's validation (probe strength).** Neither existing strength fits:
    - `validate_spec(spec, launch=True)` cannot pass before the probe: it requires `estimate.source` to name a probe
      record, and it requires the label fields (partition, receipt, freeze record), which the probe does not use;
    - the default `validate_spec(spec)` accepts a placeholder `image.versions_sha256` (and placeholder `paper.commit`
      and `host_config.sha256`). `image_identity` would then STOP only inside the job, after the job has started.

    So the probe mode must have its own probe-strength check, run before submission and again in the job. It runs the
    default `validate_spec`, and then requires these fields filled, with the same patterns as `_pin(…, allow=False)`:
    - `paper.commit`: 40 hex, the host-config fill commit, on `origin/main`;
    - `image.digest`: the v2.2 digest;
    - `image.versions_sha256`: 64 hex, T1's value;
    - `host_config.sha256`: 64 hex, T3's file sha256 at that commit.

    It also requires:
    - `run_id` different from `trackp-p4-p1-20261122-a`;
    - the spec's `arms` and `first_arm` unchanged (the default `validate_spec` requires both controls and `kev-0.8b`
      among the arms). Each probe job takes one arm as its argument, as `p4_lib.py job --arm` does, and the
      `kev-0.8b` job runs first and alone.

    It may leave the label fields, `estimate.source` and `estimate.hours` as placeholders, and the probe must not read
    them. The job records the probe spec's sha256.

The probe JDL should use the fixed lines of `p4_render_jdl.render`: container universe, the v2.2 digest,
`request_GPUs = 1`, the H200 requirement, the no-resume `periodic_hold`, and the `layout` request (8 CPUs,
131072 MB, 150000000 KB), so that the probe also shows a P.4-shaped slot matching. It needs its own executable,
arguments and transfer lists, and a `+RequestWalltime` of its own (proposed: 7200 s per base, to be confirmed by the
probe unit's review).

### 4.3 The commands per base (inside the probe job)

These are exactly the argument lists that `p4_lib.data_argv(…, synthetic=True)` and
`p4_lib.sft_dev_argv(arm, data, 1e-05, 0, run_dir, extra=("--steps", "50"))` build. They run through `p4_lib.trackp`,
with the clone's `trackp.py` by absolute path, the job directory as the working directory, and the offline
environment of `p4_lib.offline_env`. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` matters here: the P.4 runs use
the same setting, so the measured memory matches them.
```
# host: a NEMO2 H200 execute node, inside image v2.2 (ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900…5949)
# working directory: the job scratch J (HTCondor's initial directory); the clone at J/paper; staged models at J/models
J=$PWD
export HF_HOME=$J/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
       PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=$J/paper
PY=/opt/r1/envs/trackp/bin/python
CFG=$J/paper/r1/scripts/configs/trackp_htcondor_v2.json
# once per job: the synthetic-label data build on the pinned sweep1_v3 table (no label file is opened)
$PY -B $J/paper/r1/scripts/trackp.py --config $CFG sft-data --table $J/table --table-pin sweep1_v3 \
    --sweep $J/paper/results/r1/pilot/C3_sweep_index_20261028T033315Z.json --paper-root $J/paper \
    --classification $J/paper/results/r1/evidence/C3_sweep_classification_20261028.json \
    --labels synthetic --label-sweep sweep1 --run-dir $J/out/sft_data_synthetic
# ARM is one of kev-0.8b (first, alone), kev-4b, qwen3.5-0.8b-base, qwen3.5-4b-base; UUID from gpu_identity
mkdir -p $J/out/probe
nvidia-smi --id="$UUID" --query-gpu=timestamp,memory.used,memory.total --format=csv,noheader,nounits -lms 500 \
    > $J/out/probe/$ARM.gpu_mem.csv & SAMPLER=$!
T_START=$(date +%s.%N)
$PY -B $J/paper/r1/scripts/trackp.py --config $CFG sft-dev --data $J/out/sft_data_synthetic/data --base $ARM \
    --lr 1e-05 --seed 0 --run-dir $J/out/probe/$ARM --steps 50
RC=$?; T_END=$(date +%s.%N); kill $SAMPLER
echo "arm=$ARM rc=$RC t_start=$T_START t_end=$T_END" >> $J/out/probe/wall.txt
```
Notes on these commands:
- `--steps 50` sets `max_steps`, so `total_steps = min(5 epochs, 50)`. `run_stage_s` records it as
  `protocol_deviation: {"max_steps": 50}`.
- No `--eval-every` is passed, so validation runs at the protocol cadence (`round(steps_per_epoch × 0.25)`) on the
  synthetic val rows, and the wall time per step carries the same share of evaluation as a real run. `sft-dev` always
  evaluates step 0; the command line has no switch to turn validation off. Early stopping (patience 2) may end the run
  before step 50. `train.stopped_at` records where; an early stop only makes the per-step wall time more conservative.
- The sampler queries the assigned GPU by UUID, as the smoke's scoped shim did. `nvidia-smi` is not a compute
  process, so it does not trip the lease's foreign-process check. `memory.used` is device memory (CUDA context plus
  the caching allocator's reserve). That is the quantity that must fit in the H200's memory, but it is not PyTorch's
  `max_memory_allocated` (F4).
- lr `1e-05` and seed 0 are what `test_path` uses. The timing and memory of a step do not depend on the lr.
- The synthetic labels come from `SyntheticLabelSource` (a hash of seed and proposal id; "Never audit data").

### 4.4 The record

The record is one Markdown file with a JSON sidecar, on the cluster branch, then merged to `main`:
- **`docs/r1/reports/trackp_p4_probe_YYYYMMDD/H200_SFT_PROBE_YYYYMMDD.md`**, the record the spec and note name;
- `probe_records.json` (below);
- per arm, `gpu_mem_<arm>.csv`, `metrics_<arm>.jsonl` (a copy of `stage_s/metrics.jsonl`), `report_<arm>.json` and
  `job_record_<arm>.json`;
- `SHA256SUMS`.

`probe_records.json`, schema `trackp_p4_h200_sft_probe/1`, has one entry per arm. Each field's source is given:

| field | source |
|---|---|
| `arm`, `registry_keys` (adapter, base) | `p4_lib.ARMS` |
| `condor_job`, `hostname`, `gpu` (name, uuid, driver, memory_total, compute_capability) | the job record (`gpu_identity`, `host_identity`); `condor_history` |
| `image_digest`, `versions_sha256` | spec; `image_identity` |
| `paper_commit`, `host_config_sha256`, `sft_config_sha256` | the clone; `sha256sum` |
| `env3_freeze` (status, image_line, local_label) | `env3_freeze` |
| `staging_seconds`, `staged_bytes` | probe-mode timers around `stage` |
| `labels` = `"synthetic"`, `sft_data_sha256`, `n_train` | `report.json` `data.labels`, `data.sft_data_sha256`, `n_train` |
| `micro_batch` = 8, `effective_batch` = 16, `max_tokens` = 1024, `gradient_checkpointing` = `"off (SFT path)"` | `report.json` `protocol`; `trackp_sft.json` |
| `protocol_deviation` = `{"max_steps": 50}` | `report.json` |
| `steps_per_epoch`, `total_steps`, `stopped_at`, `early_stopped` | `report.json` (`train.*`) |
| `wall_s` = `t_end − t_start`; `s_per_step_wall` = `wall_s / stopped_at` | `wall.txt`, `report.json` |
| `step_s_median`, `step_s_p90`, `step_s_max` over steps 6…`stopped_at` | `metrics.jsonl` records with `kind: "step"` |
| `peak_memory_used_mib`, `memory_total_mib`, `headroom_frac` = `1 − peak / total` | max and total of `gpu_mem_<arm>.csv` |
| `oom` (bool), `rc`, `stop`, `stop_class` | `wall.txt`; the job record |
| `gpu_hours_consumed` | the job record's `gpu_hours`, cross-checked with `condor_history` `RemoteWallClockTime` |
| `estimate_hours` | §4.5 |

The Markdown file states, in prose: ENGINEERING_ONLY; synthetic labels; nothing kept as an arm (§4.6); and the
projection of §4.5 with its arithmetic.

**Where the record is named.**
- The spec's `estimate.source` must be **exactly** `h200_sft_probe: docs/r1/reports/trackp_p4_probe_YYYYMMDD/H200_SFT_PROBE_YYYYMMDD.md`
  (with the real date). `validate_spec` uses `re.fullmatch(r"h200_sft_probe: docs/r1/reports/\S+\.md", source)`, so
  no other text may follow.
- `estimate.hours` gives the four values of §4.5, equal to the record's `p4_estimate_hours:` lines (below).
- The note's `h200_sft_probe:` line must contain that path (`check_binding` takes the text after the first `:` of
  `estimate.source`). Example: `h200_sft_probe: docs/r1/reports/trackp_p4_probe_YYYYMMDD/H200_SFT_PROBE_YYYYMMDD.md
  (per base at micro-batch 8: peak device memory and seconds per step; synthetic labels; ≤ 50 steps)`.
- `p4_switch.check` also requires that file to exist on `origin/main` (`git cat-file -e`).

**The `p4_estimate_hours:` lines (new at `4315ab295`).** `p4_switch.check` reads the record's text from
`origin/main` and calls `check_probe_hours(text, spec)`:
```
PROBE_HOURS = re.compile(r"^p4_estimate_hours:\s*(\S+)\s+([0-9]+(?:\.[0-9]+)?)\s*$", re.M)
...
    for arm in spec["arms"]:
        got = found.get(arm, [])
        if len(got) != 1:
            raise Stop(f"STOP: the H200 SFT probe record must give one 'p4_estimate_hours: {arm} <hours>' line "
        ...
        if abs(got[0] - float(spec["estimate"]["hours"][arm])) > 1e-9:
```
So the Markdown record `H200_SFT_PROBE_YYYYMMDD.md` must hold, each on a line of its own starting in column 1, exactly
one line per spec arm, in this form (the hours written as plain decimals, no sign, no exponent, no unit, nothing
after them):
```
p4_estimate_hours: kev-0.8b H1
p4_estimate_hours: kev-4b H2
p4_estimate_hours: qwen3.5-0.8b-base H3
p4_estimate_hours: qwen3.5-4b-base H4
```
Here `H1`…`H4` are the `H_a` of §4.5, written to two decimals, for example `0.86`. The same four numbers, with the same
digits, go into the spec's `estimate.hours`; the check allows a difference of at most 1e-9. Further rules:
- no other line of the record may match the pattern. A second line for an arm, for example a worked example or a
  quoted earlier value at the start of a line, is refused ("found 2"). Write explanations so that they never begin
  with `p4_estimate_hours:`;
- the lines are needed only for the spec's arms. If P2 removes a Kev base, the spec's `arms` and these lines change
  together. A line for an arm outside the spec is ignored by the check, but leave none, for clarity;
- the JSON sidecar repeats the values (`estimate_hours`). The switch reads only the Markdown lines.

The spec's `estimate.hours_comment` and the note's `h200_sft_probe:` `<FILL …>` state the same format. The 8×
placeholder hours of today's spec can therefore launch only if the probe gives exactly them.

### 4.5 Recomputing the P4-CAP projection

Per arm `a`, from its probe entry:
- `n` = `n_train` of the probe's synthetic data directory. It is the same table and the same P3 split file.
  Synthetic labels are drawn for every non-duplicate row, so `n` is expected to equal the real-label build's training
  count. The P.4 job records the real count; a larger real count would make the estimate low (STOP S13).
- `steps(m) = 5 × ceil(ceil(m / 8) / 2)`, for 5 epochs, micro-batch 8 and two accumulation steps (from
  `Trainer.__init__`: `batches_per_epoch = ceil(rows / micro)`, `steps_per_epoch = ceil(batches / grad_accum)`).
- `S_a = 9 × steps(n) + 3 × Σ steps(p)`, the sum over `p ∈ {250, 500}` with `p < n`. That is the grid of 3 lr × 3 seeds
  plus the learning-curve points × 3 seeds, all **without early stopping** (the draft's conservative case).
- `H_a = S_a × s_per_step_wall(a) / 3600`, rounded **up** to 0.01 h. That is `estimate.hours[a]`. `s_per_step_wall`
  folds in model load, the step-0 evaluation, the validation passes, the final prediction and the temperature fit. On
  a 50-step run that overstates the per-step cost of a full run, which is the safe direction.

Worked example, with the 4090 figure the draft uses and not a measurement: if `n = 593`, then `steps(593) = 190`,
`steps(250) = 80`, `steps(500) = 160`, and `S = 9 × 190 + 3 × (80 + 160) = 2,430`. At 1.26 s per step,
`2,430 × 1.26 / 3600 = 0.8505`, which rounds **up** to `H = 0.86 h`; the draft gives 0.83 h.

Then:
1. Write the four `p4_estimate_hours:` lines into the probe record (§4.4). Write the same `H_a`, with the same
   digits, into `estimate.hours`, and `estimate.source` into a working copy of the spec. Then run
   `$PY r1/scripts/htcondor/trackp_p4/p4_lib.py validate <working copy>`. `projection` gives per arm
   `gpu_hours = H_a + 1800/3600` and `walltime_s = ceil(H_a × 3600 × 1.5 + 1800)`; it gives the totals and
   `within_cap`. `validate_spec` STOPs when any `walltime_s` > 86,400 s (that is, any `H_a` > 15.67 h), when
   `H_a` ∉ (0, 20], or when the totals exceed 40 GPU-h or 64 slot-hours.
2. **A manual check that the code does not make.** The draft's P4-CAP total counts "the H200 SFT fit and timing
   probe (four short runs), the host checks and the synthetic test-path run: under 2 GPU-h", and the note's
   `gpu_hours_cap:` says the 14–19 GPU-h "also counts the probe itself". `charged_hours` counts only sealed attempts of
   the P.4 run id, so the probe is not counted by code. The plan checks `projection.total_gpu_hours + Σ
   gpu_hours_consumed(probe) ≤ 40` and records it in the probe record and in the note's `gpu_hours_cap:` text. If the
   probe consumed more than 2 GPU-h, report it.
3. The note's `gpu_hours_cap:` line keeps `40 …; slot_hours_cap: 64`, with the recomputed projection in place of "the
   spec's projection 16.94 GPU-h … in the draft's 8x case".

### 4.6 No evaluation or test data, and nothing that could count as an arm

- **Labels.** The data directory is built with `--labels synthetic`. No label file, no `RECEIPT.json` and no freeze
  record is transferred or opened, and `inputs` is not called. The evaluation block and `runs.jsonl` are refused by
  name by the loaders (draft §4). The data directory holds train, val and val_seen rows only, no test rows (`sft.py`
  module docstring). The prompt replay reads the sweep-1 index, classification and ledgers in the clone, as every
  `sft-data` build does.
- **No test path.** `test_path` and `trackp_p4_test_path.py` are not run in the probe (§4.2 item 9).
- **Nothing kept as an arm.** Five things keep a probe run from ever being used as a P.4 run:
  - `out.tar` carries no checkpoint weights (§4.2 item 10);
  - every probe report records `protocol_deviation: {"max_steps": 50}`, which `check_run_protocol` refuses
    (`ProtocolStop`) and `sft.select_lr` refuses ("not a grid run");
  - the probe's `data_sha256` is that of a synthetic data directory, which `check_run_protocol` refuses against the
    real data directory;
  - the probe runs under its own run id, so `charged_hours`, `check_first_record` and `assemble` (all keyed on
    `<sealed_root>/trackp-p4-p1-20261122-a/`) never see it;
  - `sft-dev` is ENGINEERING_ONLY (R1-TRACKP-SFT-DEV), and its output is used for no selection.

## 5. Field table

### 5.1 `r1/scripts/htcondor/trackp_p4/p4_spec.json`

Who fills: **cluster** = the cluster agent, from host verification; **chat** = the coordinating chat; **author** = at
signature. All spec fills go in the spec-fill commit (§6 step 9). Under `verify_launch_p4`, it may differ from the
code commit only under `docs/` and in this file.

| Field | Today | Who | From which output | Before |
|---|---|---|---|---|
| `paper.commit` | `TODO: the published launch commit carrying this runner` | chat | `git rev-parse` of the reviewed code commit on `main`. It must carry the runner, the receipt-binding fix (F2), the probe mode, the filled host config, the test changes (F5) and the signed freeze record (F6) | T8; the note's `code_commit:` |
| `image.versions_sha256` | `TODO_VERIFY_ON_HOST: …` | cluster records it; chat fills it in the spec-fill commit | T1 per `image.versions_sha256_comment`: line 1 of the NEMO2 job's `sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt` (Route A), or the 759994/759997/760000 captures with the exact file's sha256 (Route B); 64 hex only; confirmed by the probe's in-job `image_identity` | The probe spec (step 1 of the probe mode compares it); T8 |
| `image.versions_sha256_comment` | The procedure (new at `4315ab295`) | — | Not a placeholder (`validate_spec` does not read it) | Leave as is, or keep it accurate |
| `host_config.sha256` | `TODO: sha256 after the TODO_VERIFY_ON_HOST fill …; 18f18cfc… today` | cluster (chat checks) | T3: `sha256sum r1/scripts/configs/trackp_htcondor_v2.json` at the host-config fill commit. Not the `"sha256"` printed by `--check-config` | The probe spec; T8 |
| `labels.partition_sha256` | `TODO: …` | chat (cluster re-verifies) | `SWEEP1_TRAINDEV_RELEASE_20261123.md`: `6a6327a3731dc2d874822e009f3b2d84fbf1a6cbabfef505c657f90b14fd7b2a`; on deepthought `sha256sum $R/label_block.traindev.jsonl` (sha256 only, never the content) | T8. Subject to F2 |
| `labels.receipt_sha256` | `TODO: …` | chat (cluster re-verifies) | Same report: `f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1` (also the sha256 of the committed copy `RECEIPT_sweep1_traindev.json`); on deepthought `sha256sum $R/RECEIPT.json` | T8. Subject to F2 |
| `labels.freeze_record.path` | `TODO: docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md (signed, P1)` | chat, after the author signs the freeze | The published file name; it must match `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_\d{8}\.md` | T8. It must be in the tree of `paper.commit` (F6) |
| `labels.freeze_record.sha256` | `TODO: its sha256` | chat | `sha256sum` of that file at `paper.commit`. Its text must hold the signed approval line and `cdae9c3f…9aca` (`inputs`) | T8 |
| `estimate.source` | `TODO: h200_sft_probe: <probe record>; …` | chat | Exactly `h200_sft_probe: docs/r1/reports/trackp_p4_probe_YYYYMMDD/H200_SFT_PROBE_YYYYMMDD.md` (§4.4) | T8; the note's `h200_sft_probe:` |
| `estimate.hours` (4 values) | The draft's 8× case (0.83 / 6.64) | chat, from the cluster's probe record | §4.5 `H_a`. Each value must equal the record's one `p4_estimate_hours: <arm> <hours>` line within 1e-9 (`p4_switch.check_probe_hours`) | T8; `p4_switch.check` after signature |
| `estimate.hours_comment` | States the line format (new at `4315ab295`) | — | Not a placeholder (`validate_spec` does not read it) | Leave as is |
| `comment` (prose naming the TODO fields) | Mentions the TODOs | chat (optional) | — | No code reads it; it only changes the spec sha256 |

### 5.2 `r1/scripts/configs/trackp_htcondor_v2.json` (19 `TODO_VERIFY_ON_HOST` values)

All are filled by the **cluster**, in one commit reviewed with the test changes of F5, before the probe and T3. The
values must not start with `TODO_VERIFY` (`run.PLACEHOLDER`). `trackp()` runs with the job directory as working
directory, so relative paths resolve inside the job scratch. The values below are those the code forces or suggests;
the cluster confirms them.

| Field | Value forced or suggested by the code | Source and verification |
|---|---|---|
| `bases.kev-0.8b.local_path` | `models/qwen3.5-0.8b-base` (forced) | `check_local_paths`: `job_dir/models/<base registry key>`; T3; probe staging (T7) |
| `bases.kev-0.8b.adapter_local_path` | `models/kev-0.8b` (forced) | Same, adapter registry key |
| `bases.kev-4b.local_path` | `models/qwen3.5-4b-base` (forced) | Same |
| `bases.kev-4b.adapter_local_path` | `models/kev-4b` (forced) | Same |
| `bases.qwen3.5-0.8b-base.local_path` | `models/qwen3.5-0.8b-base` (forced) | Same |
| `bases.qwen3.5-4b-base.local_path` | `models/qwen3.5-4b-base` (forced) | Same |
| `bases.laya.local_path`, `bases.startlux-0.8b.local_path`, `bases.startlux-2b.local_path`, `bases.startlux-4b.local_path` | **chat decides** (F7). Suggested: `models/<key>`, not staged by P.4, so a run naming them fails to load | No P.4 code path reads them; `--check-config` needs them filled |
| `gpu.name` | `NVIDIA H200` | `i3_identity.txt` ("NVIDIA H200"); the smoke stage asserts the name and passed on v2.2 (759997); confirmed by the probe's `gpu_identity` |
| `gpu.compute_capability` | `9.0` | The smoke `probe.sh` asserts `get_device_capability(0) == (9, 0)` and passed on v2.2 (759997); confirmed by the probe's `nvidia-smi … compute_cap` |
| `gpu.lock_path` | Suggested: `gpu0.lock` (job-relative). `gpu_lease` creates its parent and takes a non-blocking flock | Probe lease log |
| `runs_dir` | Suggested: `out`. The lease log goes to `<runs_dir>/gpu_lease_log.jsonl` and then into `out.tar` | Probe `out.tar` |
| `hf_home` | Suggested: `hf`. `offline_env` sets `HF_HOME=<job>/hf`, and `stage` stages the tokenizers there | Probe staging |
| `models_dir` | Suggested: `models` | `check_local_paths` |
| `work_dir` | Suggested: `.` | — |
| `venv.path` | `/opt/r1/envs/trackp` | `p4_lib.ENV3_PYTHON`; T1/T2 |
| `venv.causal_conv1d` | Suggested: "1.7.0 built from source in image v2.2, TORCH_CUDA_ARCH_LIST 8.0;8.9;9.0, build log sha256 fe872a3e…3312 (R1-TRACKP-IMAGE-V22-B)" | `V22_BUILD_20261124.md`; T1 (`env3_causal_conv1d_arch=` and the v2.2 lines of `VERSIONS.txt`); T2 (`causal-conv1d==1.7.0`) |

After the fill, T3 gives the file sha256 for `host_config.sha256` and for the note's `host_config:` line. Any later
change to this file changes both, and the probe spec too.

### 5.3 `docs/r1/proposals/TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md` (`<FILL…>` and PENDING)

`p4_switch.parse_note` refuses any `<…>` left in a field and any P1–P8 that does not start with `PASS — `.
`check_binding` compares `run_id`, `spec_sha256`, `code_commit` and `versions_sha256` **exactly**, so those lines
must hold the bare value with no trailing text.

| Field | Who | From | Before |
|---|---|---|---|
| `spec_sha256:` | chat (at signature) | `sha256sum r1/scripts/htcondor/trackp_p4/p4_spec.json` at the spec-fill commit; bare 64 hex; equal to the T8 stage's `p4_spec.json` | Signature |
| `code_commit:` | chat (at signature) | `paper.commit`; bare 40 hex | Signature |
| `labels:` | chat | Must contain `label_block.traindev.jsonl` and `labels.partition_sha256` | Signature (F2 first) |
| `label_receipt:` | chat | Must contain `RECEIPT.json` and `labels.receipt_sha256` | Signature |
| `label_freeze:` | chat | Must contain `labels.freeze_record.path` and `.sha256` | Signature |
| `host_config:` | chat, from cluster T3 | Must contain `r1/scripts/configs/trackp_htcondor_v2.json` and `host_config.sha256` | Signature |
| `versions_sha256:` | cluster records it (T1); chat fills | Bare 64 hex, equal to `image.versions_sha256` | Signature |
| `h200_smoke_e0:` (its `<FILL: the independent review of these run records>`) | chat | The path of the accepted independent review of the v2.2 run records | The probe (F8) |
| `h200_sft_probe:` (its FILL now reads "… on main, with one line "p4_estimate_hours: ARM HOURS" per arm equal to the spec's estimate.hours (p4_switch check)") | chat, from the cluster's probe record | Must contain the path in `estimate.source`; the record on `main` must carry the four `p4_estimate_hours:` lines (§4.4) | Signature |
| `gpu_hours_cap:` (text, not a placeholder) | chat | The recomputed projection and the probe's consumed hours (§4.5); must start `40` and contain `slot_hours_cap: 64` | Signature |
| `arms:` (text) | chat | Changes with the spec's `arms` only if P2 removes a Kev base | Signature |
| `P1: PENDING` | chat | `PASS — ` + the signed freeze (it must cite `C3_SWEEP1_LABEL_FREEZE_`) + the release receipt | Signature |
| `P2: PENDING` | chat | `PASS — ` + the per-base P.3a records | Signature |
| `P3: PENDING` (with `docs/r1/reviews/<FILL>`) | chat | `PASS — ` + the review at the code commit (it must cite `docs/r1/reviews/`) | Signature |
| `P4: PENDING` | **author** | The author's tick | Signature |
| `P5: PENDING` | chat | `PASS — ` citing R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B (as whole ids), the run-record review and the probe record | Signature |
| `P7: PENDING` | chat, from cluster T3 | `PASS — ` citing `--check-config` (T3), and the env3 freeze (T2; in-job T7) | Signature |
| `approved:` | **author** only | The author's signature | Last |

`P6` and `P8` already read PASS. The other key lines (`run_id`, `source_label_block`, `table_pin`,
`duplicate_policy`, `split`, `split_file`, `lr_grid`, `readiness`, `host`, `micro_batch`, `image`, `env3_freeze`,
`job_layout`, `real_label_test_read`, `evaluation_seeds_read`, `harness_commit`) are filled and need no cluster
value.

**`image.versions_sha256`, exactly** (the spec's `image.versions_sha256_comment` at `4315ab295`; T1):
1. The cluster agent submits, from deepthought, an HTCondor job with the staged smoke header
   (`docs/r1/reports/trackp_h200_20261118/stages/smoke_h200/probe.jdl`: `universe = container`,
   `container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949`,
   the NEMO2 `requirements`). The job runs `sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt` (T1 Route A
   gives the files). HTCondor runs the container; no `apptainer` command is involved.
2. Line 1 of the output is `<64 hex>  /opt/r1/VERSIONS.txt`; the rest is the file. `sha256sum` of the rest must give
   the same 64 hex, which shows the committed text is the exact file.
3. The cluster commits the text together with that sha256 line (`T1_VERSIONS.txt`, `T1_versions_sha256.txt`, the
   JDL, the script and the job id) on its branch; the chat merges it. Route B instead: commit the handback captures of
   759994/759997/760000 with the sha256 of the exact file, valid only if a capture is byte-exact.
4. Do not use the I2 identity's `versions_sha256`: I2 runs on the cpu image.
5. In the spec-fill commit, the chat writes the bare value into `p4_spec.json` `image.versions_sha256`, replacing the
   whole `TODO_VERIFY_ON_HOST: …` string. At signature, it also goes into the note's `versions_sha256:` line, replacing
   the whole `<FILL …>`; `check_binding` compares it exactly.
6. The probe job's `image_identity` compares it with the file inside the job on the H200; a difference is STOP S5. An
   optional deepthought reading (`apptainer exec` on a SIF pulled by the same digest) must agree too.

The value cannot be derived at the desk: VERSIONS has a `build_utc` line, and no raw capture of the v2.2 jobs is
committed.

## 6. Order of operations up to the phase-1 note's signature

No P.4 training job appears here; the first submission comes after signature.

1. **Chat decisions.**
   - The options and the runner change for the receipt/table binding (F2); the decision itself is the author's (below).
   - The probe mode and its job (F1, §4.2), including how peak memory is recorded (F4).
   - The values for the unused bases (F7).
   - Whether the probe's GPU-hours count against the 40 GPU-h (§4.5 item 2; the draft says they do).

   **Author decision**, before the probe: whether the ≤ 50-step synthetic probe counts as "no training run" (§0).
   The chat brings the question to the author; it does not decide it.
   **Author decision**, before the code commit: the receipt/table binding for P.4 (F2; for example FEAT-ONE A applied
   to A5's phase-1 data). The chat prepares the options and the runner change; it does not decide it.
2. **Review of the v2.2 run records** (I2 759993, I3 759994, smoke 759997, E0 760000). This closes `h200_smoke_e0:`
   and part of P5.
3. **Cluster, deepthought:** T0, T2 and T6 on a published review commit, and T4 if the chat says go. **T1** is a
   read-only HTCondor job on a NEMO2 H200 slot. It reads one file, runs the two unscoped `nvidia-smi` queries (F3),
   and trains nothing. T5
   when the table and partition are in place (both exist on deepthought today). Committed to
   `docs/r1/reports/trackp_p4_cluster_YYYYMMDD/`.
4. **Host-config fill commit**: the cluster fills the host config (§5.2), committed with the test changes (F5) and
   the probe mode, reviewed and merged on `main`. Then T3 on that commit. The F2 fix is **not** part of this step:
   the probe does not need it.
   **Step 4a.** The author's F2 binding decision and its reviewed runner change are merged on `main` before the code commit is
   fixed (step 6). This may land before or after the probe; it gates the signature (S9), not the probe.
5. **Signed sweep-1 label freeze** on `main`. The author signs it; the chat publishes it. This must happen before the
   commit chosen as `paper.commit` (F6), so the order of steps 4 and 5 may swap, but `paper.commit` comes after both.
6. **Fix the code commit** (`paper.commit`): the reviewed commit on `main` carrying steps 4, 4a and 5.
7. **The probe**, gated only by the author's decision (step 1), step 2, step 4 and T1's value (STOP S4); not by
   step 4a, 5, 6 or 8. `kev-0.8b` alone, then `kev-4b`, `qwen3.5-0.8b-base` and `qwen3.5-4b-base`. It clones the
   host-config fill commit. T7 is recorded in the same jobs. The probe record and the
   P4-CAP recomputation (§4.4, §4.5), with its four `p4_estimate_hours:` lines, are merged on `main`. If later review changes the code, the probe need not be
   repeated unless the host config, the image or the SFT path changes; the chat decides.
8. **P2 records** cited; `arms` confirmed.
9. **Spec-fill commit** (spec only, plus `docs/`): every §5.1 field. `p4_lib.py validate --launch` gives rc 0 (T0).
10. **T8**: the launch-strength stage and `condor_submit -dry-run` of the four JDLs, from the step-9 checkout. Commit
    the manifest, the JDLs and the dry-run output; keep the stage.
11. **Note completion** by the chat (§5.3), all but `P4` and `approved`.
    - Check 1 of the note draft: the method of `test_the_note_draft_parses_and_its_completion_binds_a_filled_spec`,
      on a temporary in-memory copy, against the T8 stage's spec and its sha256 (`parse_note` + `check_binding`). On
      the real file, the only refusals must concern `P4` and `approved`. Nothing from this check is committed with a
      signed value.
    - P3's review at the code commit is recorded.
12. **Author's signature**: the P4 tick and `approved`. The chat publishes the note as
    `docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md`.

After signature, outside this plan: `p4_switch.py check --stage $D/T8_stage --note …`, then
`p4_switch.py submit --arm kev-0.8b` alone.

## 7. STOP conditions

Each returns to the coordinating chat or the author. Outputs are kept, nothing is deleted, nothing is retried
silently, and no request is relaxed to force a match.

- **S1** The code under test is no longer that of `bb1a9eb0` (= `4315ab295`), or the runner's review changes any function, flag or argument
  list cited here. Re-derive the commands before running them.
- **S2** Any step would run `p4_job.sh`, `p4_lib.py job`, `p4_switch.py submit`, an `sft-dev` without `--steps` or
  with `--steps` above 50, `sft-select`, a learning-curve point, or an `sft-data` build with real labels, before
  signature.
- **S3** Any step would open `label_block.jsonl`, `evaluation_block.jsonl`, `runs.jsonl` or a 7006–7010 value, or
  would transfer the label partition or receipt to a probe job.
- **S4** The probe is about to run before any of these: the author's decision on "no training run" (§0); the
  independent review of the v2.2 run records (P5, R1-HTC-QTORCH); the probe mode reviewed and on `main`; the
  host-config fill commit on `main`; T1's `versions_sha256` value. Nothing else gates the probe (§6 step 7).
- **S5** The image:
  - the T1 values differ from each other or from the in-job `image_identity`;
  - the digest is not v2.2;
  - `VERSIONS.txt` lacks `env3_sorted_diff=empty` or the pinned freeze sha256;
  - T2 or the in-job freeze gives anything other than `identical` with `local_label: null`. That includes every STOP
    form named in the note's `env3_freeze:` line (a direct reference, the `causal_conv1d` spelling, another version
    or operator, a malformed label, a removed or added line, any other difference). A `causal-conv1d==1.7.0+LABEL`
    line is admitted by the rule but contradicts the v2.2 record, so report it before going on.
- **S6** In a job, unscoped `nvidia-smi` lists more or fewer than one GPU, the GPU is not `NVIDIA H200`, the uid is
  0, or the lease reports a foreign compute process (F3).
- **S7** `--check-config` lists any placeholder after the fill, or `check_local_paths` STOPs, or the host-config
  sha256 used by the probe or stage differs from the spec's.
- **S8** Staging: a registry size or sha256 mismatch, a curl failure, or a tokenizer-staging failure.
- **S9** The receipt/table binding (F2) is not decided by the author, or its reviewed runner change is not in the code commit, when
  the note is about to be signed. This is a manual gate: no code refuses it before a job runs. `validate --launch`, the
  T8 render, `condor_submit -dry-run` and `p4_switch.check` all pass with the published receipt; only `p4_lib.inputs`
  inside the job refuses it at step 5, before staging. Do not sign, and do not submit, until it is resolved.
- **S10** The probe:
  - a CUDA OOM at micro-batch 8 (`ArmStop`; P4-MB; the author decides);
  - `protocol.micro_batch` ≠ 8 or `effective_batch` ≠ 16;
  - `data.labels` ≠ `synthetic`;
  - `protocol_deviation` ≠ `{"max_steps": 50}`;
  - rc ≠ 0;
  - a missing memory or wall record;
  - a probe of another base run before `kev-0.8b`'s record is STOP-free.
  
  A device-memory headroom below 15 % is not a code STOP, but it is reported to the author with the record. The
  probe sees the table's real prompt lengths in its shuffled order over at most 50 steps, not a forced worst-case
  batch of 1,024-token prompts.
- **S11** No H200 slot can match 8 CPUs, 131072 MB and 150000000 KB (T6, T8). Report it; the request stays.
- **S12** The cap:
  - any arm's projected walltime is over 86,400 s;
  - the projection is over 40 GPU-h or 64 slot-hours (`validate_spec`);
  - projection plus the probe's consumed GPU-h is over 40 (§4.5 item 2);
  - the probe consumed over 2 GPU-h without the chat's agreement.
- **S13** A later real-label build's `counts.train` is larger than the probe's `n`. The estimate is then low, so
  recompute before any further submission.
- **S14** The signed freeze record is not in the tree of `paper.commit` (F6); the tests of `paper.commit` do not pass
  for both the placeholder and the filled spec (F5); or P2 removes `kev-0.8b` (decision (3) then needs the author).
- **S15** A transferred output is missing or `SHA256SUMS` does not verify. Seal it as an attempt; never resume.
- **S16** Any step would write the note's `approved` field or the P4 tick. Those are the author's alone.
- **S17** The probe record on `main` lacks one `p4_estimate_hours: <arm> <hours>` line for any spec arm, has two for
  one arm, or gives a value that differs from the spec's `estimate.hours` (`check_probe_hours`). Fix the record or the
  spec so that both state the probe's value; never edit the hours toward the cap.
- **S18** T1: the job's exit is not 0, line 1 of `versions.out` is not a sha256 line of `/opt/r1/VERSIONS.txt`, or the
  sha256 of the committed text differs from it. A Route B capture that is not byte-exact cannot be used.

## 8. Points I am unsure of

1. Whether the ≤ 50-step synthetic probe counts as "no training run". That is the author's decision (§0, §6 step 1).
   The draft calls the probe cluster training and puts it before signature.
2. Whether the probe's GPU-hours are to be added to the 40 GPU-h. The draft's arithmetic includes them; the code does
   not (§4.5).
3. Whether unscoped `nvidia-smi` inside a NEMO2 container job sees one GPU (F3). No committed record answers it.
4. Whether the `nvidia-smi` device-memory peak is acceptable as the draft's "peak memory", or whether PyTorch's
   `max_memory_allocated` is wanted. That would need a code change (F4).
5. The probe's walltime request (7200 s proposed) and its use of the full P.4 `layout` request. They are for the
   probe unit's review.
6. The partition path on deepthought: inferred from the release command's `--out` and the draft's layout; the
   cluster confirms it.
7. That `condor_submit -dry-run` refuses a preview JDL. It was not tried; the plan only says not to dry-run one.
8. The T1 job (Route A) is a new staged job. I kept the smoke header's resource lines, including one H200 GPU, so
   that it is "the same header". Whether a smaller CPU-only request would do is for its pre-submit check; the spec
   comment names the smoke header.
9. The FEAT-ONE route for P.4 (F2). R1-ARMS-DECISIONS fixes it for the arms; how the P.4 runner should bind the sealed
   v2 receipt to the v3 table (an identity record, as `require_feat_one` does for A3) is a decision this plan does not
   take.

## 9. Review of `8d2f61c7d` (ACCEPTED, no major findings): minor findings and fixes

The review confirmed blockers F1–F6. The fixes are docs only, applied after rebasing onto `bb1a9eb0`.

| finding | fix |
|---|---|
| **m1** F2 not stated plainly enough | F2 now says that the accepted runner (READY 82/101, code at `4315ab295`) cannot run on the published sweep-1 train/dev release: receipt `f06e37a9…` binds `b713c423…` (`arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256`), and `p4_lib.inputs` (`p4_lib.py:449-453`) requires `d0048567…`. It says the runner review missed it, because round 1 asked for the check before the receipt existed. It says neither the T8 render (`check_inputs`, `p4_render_jdl.py:79-104`) nor `p4_switch.check` checks the receipt's table (also in T5). S9 is reworded as a manual gate with no code behind it, and it is a STOP before any signature: the binding decision and a reviewed runner change land in the code commit first. The precondition row says the same. |
| **m2** Who decides "no training run" | The author decides, in all three places: §0 reading 2, §6 step 1 ("Author decision", taken out of the chat's list) and §8 item 1. S4 gates the probe on it. |
| **m3** The probe spec's validation | §4.2 item 12: launch strength cannot pass before the probe, and default strength accepts placeholders that `image_identity` rejects. The probe mode needs its own probe-strength check: the default `validate_spec`, plus `paper.commit`, `image.digest`, `image.versions_sha256` and `host_config.sha256` filled, its own `run_id`, the arms unchanged with one arm per job, and the label and estimate fields unused. |
| **m4** The probe was coupled to the F2 fix | §6 step 4 no longer carries the F2 fix; a new step 4a does, gating the signature. Step 7, the preconditions table and S4 gate the probe only on the author's decision, the v2.2 run-record review, the host-config fill commit with the probe mode, and T1's value. |
| **m5** rc taken from tee | §3.2 sets `set -o pipefail` and says how each rc is recorded. T4 and the T8 dry-run loop take `${PIPESTATUS[0]}`. Every other piped line (T1, T2, T3, T5, T6, T8) runs under `pipefail`. The probe commands have no pipe. |
| **m6** Worked example | `2,430 × 1.26 / 3600 = 0.8505`, which rounds up to 0.86 (§4.5); the format example in §4.4 now reads `0.86`. |
| **m7** F3 answered late | T1's job also runs the two unscoped queries of `gpu_identity` and `run.foreign_compute_processes`, into `gpu_visibility.txt`, with pass criteria and STOP S6. It cites I3's `NVIDIA_VISIBLE_DEVICES=GPU-…` line (`i3_identity.txt` line 55, read by grep on that line only) as existing evidence. |
| **m8** One term for two commits | "Terms for commits" before §0: **code commit** (`paper.commit`, the note's `code_commit:`), **host-config fill commit** (step 4, cloned by the probe) and **spec-fill commit** (step 9, spec and `docs/` only). "Launch commit" is no longer used for either; the spec comment's use of that phrase is noted. |

