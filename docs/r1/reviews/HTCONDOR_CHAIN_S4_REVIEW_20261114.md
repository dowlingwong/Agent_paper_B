# Independent pre-submission review — S4 local-CPU job with our SIF (I1 + I2 + S6 from a worker), 14 Nov 2026

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the unit, not the executing agent;
I did not write, submit or run anything and I have no cluster access.

**Date/time of review:** 14 November 2026, 11:10–11:32 CET (Europe/Berlin).

**Reviewed unit:** `docs/r1/reports/htcondor_chain_20261114/s4/{s4_local_cpu_sif.jdl, s4_run.sh}`, committed
at branch `htcondor-chain-20261114`, HEAD **`43b0ba8c`** ("docs(r1): HTCondor chain — S3 build section, S4/S5
prepared (scripts, JDLs, pinned checkouts)"), pinned below by SHA-256. Nothing of this unit has been submitted
(no dry-run ad, no job logs, no queue entries in the worktree).

**Basis for the review.** Author instruction S4/S6 as reflected in `docs/r1/reports/HTCONDOR_CHAIN_20261114.md`
(authority L3: write scope `/work/dwong/paperb/`, `/work/dwong/htcondor_prep_20261114/`, `/ceph/srv/dwong/paperb/`;
≤10 concurrent jobs; ≤10 GPU-h; whole GPUs; no deletion) and the Lead's brief; the image contents in
`r1/scripts/htcondor/apptainer/{r1-htc.def, README.md, pip_freeze_trackp-cpu.txt, tracks_freeze_65.txt,
pyproject.toml.a3fedbb}` (S3, under review in parallel); the reviewed I2 reference script
`docs/r1/proposals/B1_TASL7_WORKER_ONCE_60EC_20261107.sh` (on `origin/mac-b1-20261107`, SHA-256
`1be4ae33…a1a5b3` — matches), the B1 result evidence
`docs/r1/reviews/B1_TASL7_REAL_WORKER_RESULT_REVIEW_20261107.md`, and the I2 test source at paper
`60ecf1da:r1/tests/test_c3_audit.py`; the S2 results (`s2/S2L.out`, `s2/S2N1.out`, chain report §S2) and the S6
raw (`raw/s6_xrootd_attempt2.txt`); upstream HTCondor 23.0 `condor_submit`/file-transfer/container-universe
documentation and the job ClassAd attribute reference (links in §2).

**Hard limits of this review (deliberate).** No SSH, no HTCondor commands, no submission, no git commit/push,
no file written except this review. The SIF is still being built; **this review is of the unit, not of the SIF's
existence** — the few checks that need the built SIF or a dry-run are called out explicitly as must-do before
submission. The committed S1/S2 facts are the only measured cluster evidence used here.

---

## 1. Files reviewed and pinned (SHA-256)

| File | Bytes | SHA-256 (16-hex prefix) |
|---|---|---|
| `s4/s4_local_cpu_sif.jdl` | 462 | `0d22d5bdecdac1c2` |
| `s4/s4_run.sh` | 3830 | `966ec99d332d862d` |

Supporting files read (not part of this unit): `r1-htc.def` (8 543 B), `build_sif.sh`, `README.md`,
`pip_freeze_trackp-cpu.txt`, `tracks_freeze_65.txt`, `pyproject.toml.a3fedbb`, the reference script, the B1
result review, `s2/S2L.out`, `s2/S2N1.out`, the S6 raw, `raw/s2_precheck.txt`, and the raw container-attribute
captures. The unit is committed and unchanged since HEAD `43b0ba8c`.

---

## 2. Checks performed, and results

### 2.1 JDL against the S4 brief

| Field | JDL line | Value | Verdict |
|---|---|---|---|
| universe | L1 | `container` | ✓ container universe (Apptainer route, as S2 proved) |
| container_image | L2 | `/work/dwong/paperb/images/r1-htc-20261114.sif` | ✓ matches the brief; absolute SIF path on shared `/work` |
| executable | L3 | `s4_run.sh` (relative; submit from the unit directory) | ✓ |
| transfer | L4–L6 | `should_transfer_files = YES`; `when_to_transfer_output = ON_EXIT`; `transfer_input_files = s4_run.sh` | ✓ (redundant with the executable, harmless) |
| transfer_output_files | L7 | 7 evidence names | ✗ **BLOCKING B1** — these files are not created in the job sandbox |
| walltime | L8 | `+RequestWalltime = 3600` | ✓ |
| requests | L9–L11 | CPUs 2, Memory 8000 MB, disk 30 000 000 kB | ✓ explicit; GPU-free |
| placement | L12 | `requirements = TARGET.ProvidesETPResources` | ✓ local; no GPU request, no `+RemoteJob`; the container clauses are appended by `condor_submit` |
| submit dir | — | relative `executable`, no `initialdir` | ✓ but submit from the unit directory; the dry-run ad must confirm `Iwd`/`Cmd` |

Missing from the JDL: `output`, `error`, `log` — **BLOCKING-adjacent MAJOR B2**; no `should_transfer_container`
— **MAJOR B4**; no SIF-gate/`ContainerImageSource` evidence — **MINOR m1** (no dry-run ad committed).

### 2.2 The job would be HELD at exit as written (B1)

`s4_run.sh` writes every evidence file under `$OUT=/work/dwong/paperb/work/s4_<job>_<UTC>/`
(L9–12, L25, L34, L47, L53, L68). The HTCondor job's sandbox is a different directory: S2L's own output shows
it as `/local/scratch/ssd/condor/execute/dir_1056002` (`s2/S2L.out`, `_CONDOR_JOB_IWD`/`_CONDOR_SCRATCH_DIR`),
with `/work` additionally mounted inside the container. The JDL's `transfer_output_files` names
`i1_envs.txt, i2_run1.log, i2_run2.log, i2_summary.txt, i2_compare.txt, s6_xrootd.txt, identity.txt` relative to
the job's sandbox; the script creates none of them there.

Upstream manual: "When this comma separated list is defined, and any of the files or directories do not exist
as the job exits, HTCondor considers this an error, and places the job on hold"
([file-transfer manual](https://htcondor.readthedocs.io/en/23.0/users-manual/file-transfer.html), same wording
in the `ON_EXIT_OR_EVICT` section). So **every** S4 run would do its work and then be put on hold instead of
completing — the opposite of the intended `COMPLETED exit 0`, and a state that would have to be explained in
the report and cleaned up before S5. This alone blocks submission.

*Exact fix (choose one):*
(a) preferred, given the chain convention of durable outputs on `/work`: **delete the `transfer_output_files`
line** (auto-transfer then applies; the script creates nothing else in the sandbox) and read the evidence from
`$OUT` on `/work` (also print `S4_DONE out=$OUT`, which needs B2's `output`); or
(b) make the script write the seven files into the job sandbox (e.g. `OUT="$PWD/s4_$JOB"`) and keep the
transfer list — then the files are transferred back, but they are lost on eviction and the "writes under
/work/dwong/paperb/" convention changes. Either way, re-run the dry-run and re-review.

### 2.3 No `output`/`error`/`log` (B2)

The JDL has none of the three (13 lines, §1). Upstream `condor_submit`: **`output` defaults to `/dev/null` on
Unix; `error` defaults to `/dev/null`; and "If no `log` entry is specified, HTCondor does not create a log for
this cluster"** ([condor_submit man page](https://htcondor.readthedocs.io/en/23.0/man-pages/condor_submit.html)).
Consequences for S4: (i) **no event log** → no 000/001/004/005/012 events → the job cannot be recorded with the
reviewed `htc_events.py` recorder (the S2-reviewed call shape depends on the `log=` file), and no queue/run
times can go into the chain report; (ii) stdout/stderr are discarded → `S4_DONE out=$OUT` (L71) and every early
failure message (missing `/work` mount, `mkdir`/`cd` failures, missing SIF) are invisible; (iii) without the
`S4_DONE` line the operator cannot learn the timestamped evidence path from the job.
*Exact fix:* add `output = s4.out`, `error = s4.err`, `log = s4.log` (relative to the submit dir; distinct and
small) — and the recorder call becomes
`python3 htc_events.py s4.log --probe <cluster>.0=S4 --utc-offset-minutes 60 --tsv s4_queue_times.tsv`
(same accepted recorder as S2, with the site's CET offset).

### 2.4 Container-universe / SIF semantics and the shared-filesystem image (B4, m1)

- The S2 unit established the route: `universe = container` works on ETP local (S2L, cluster 759670, **COMPLETED
  exit 0**, 27 s wait, 2 s run, host `slot1_44@mdm1.etp.kit.edu`), and `/work`, `/ceph`, `/ceph/srv` are mounted
  **inside** the container (`s2/S2L.out`), so `$B=/work/dwong/paperb` and its checkouts are visible to this job.
  The SIF itself lives on the same shared `/work` and will be visible to the ETP WNs at the same path.
- **Image transfer is unverified and can hold the job.** The JDL has `should_transfer_files = YES` with an
  absolute SIF path. Upstream container-universe docs: "A container image that would otherwise be transferred
  can be forced to never be transferred by setting `should_transfer_container = no`" — i.e. the default is to
  transfer (the 23.0 command name). The job ClassAd attribute reference says `ContainerImageSource` is
  `"local"` for non-transferred images and `"cedar"` for transferred files
  ([job attributes](https://htcondor.readthedocs.io/en/latest/classad-attributes/job-classad-attributes.html)),
  so the dry-run ad decides this. If HTCondor 25.0.12 treats this SIF as a transfer input, the job is held at
  submit/transfer because `MAX_TRANSFER_INPUT_MB` defaults to 100 MiB and a job over it "will be immediately
  placed on hold with a `HoldReasonCode` value of 32" — the SIF (CUDA devel base + three environments +
  llama.cpp) is far above 100 MiB.
  *Exact fix:* after the SIF exists, dry-run and inspect `ContainerImageSource`; add
  `should_transfer_container = no` (or the name the site's 25.0.12 accepts — newer docs use
  `transfer_container = false`; verify with the dry-run), because the image is pre-staged on the shared
  `/work` visible to the ETP WNs; re-run the dry-run and record both ads. If `ContainerImageSource` shows
  `cedar`, this is a second blocking failure.
- **No dry-run ad is committed at all (m1).** S2's precedent (and the runbook-based smoke-first rule) is
  dry-render → review → one real job. Run `condor_submit -dry-run` once the SIF exists and commit
  `dryrun/s4_local_cpu_sif.dry` + `.dry.log`; verify in the ad: `ContainerImage`/`ContainerImageSource`,
  `WantContainer=true`, the appended `TARGET.HasContainer && TARGET.HasSIF` gate (a SIF image matches on
  `HasSIF`/`HasSandboxImage`, not on `HasDockerURL` as the S2 docker:// probes did), `TransferInput`,
  `Request*`, `Iwd`/`Cmd`, and no docker-universe key. **`HasSIF` is not in the committed measurements**:
  `raw/raw_container_attrs_*.txt` records only four booleans per slot, which the S2 review's M1 defined as
  `HasContainer HasDockerURL HasSingularity HasDocker` (grep for `HasSIF` there is empty) — measure it
  read-only before submitting: `condor_status -constraint 'ProvidesETPResources' -af Name HasSIF HasSandboxImage HasContainer`
  (and the same for any site), record the counts, and if `HasSIF` is false on the local fleet the S4 job would
  idle — that is a match failure, not an image/SIF failure.

### 2.5 `s4_run.sh` — I1 (environment/version check)

- Sources all three environments `/opt/r1/envs/{harness,tracks,trackp}` (L16–20), prints each `python -VV`, and
  imports numpy/sklearn/pandas; then trackp torch/CUDA (L21–22), `llama-server --version` (L23), `uv --version`
  (L24), and cats `/opt/r1/VERSIONS.txt` (L15). Against the image def: `/opt/r1/VERSIONS.txt` is written by the
  def (L71–84); `%environment` puts `/opt/uv` and `/opt/r1/llama.cpp/build/bin` on `PATH` (L86–88), so
  `llama-server` and `uv` resolve ✓; `/opt/r1/envs/harness` (`uv sync --frozen --no-dev`), `tracks` (Python 3.11,
  65-package freeze), `trackp` (Python 3.13, Track P freeze + CUDA torch) exist ✓. The harness project's deps
  include numpy/pandas/scikit-learn (`pyproject.toml.a3fedbb`), and tracks/trackp freezes contain them, so the
  three-way import check does not fail on the harness env ✓.
- **Track P is the right environment for I2** and matches the 0.922225 reference stack: `pip_freeze_trackp-cpu.txt`
  pins `numpy==2.4.4` (L55), `pytest==9.0.3` (L70), `scikit-learn==1.8.0` (L78) — exactly the B1 reference stack —
  while `tracks_freeze_65.txt` has numpy 2.4.6 / scikit-learn 1.9.1 / pytest 9.2.0 (L32/50/44). The script uses
  `/opt/r1/envs/trackp/bin/python` for I2 (L41, L45) ✓. **But it does not say why** (the task asked for that):
  the only justifications are in this review. *Fix (m2):* add a three-line comment at L35–36 naming the reference
  stack (numpy 2.4.4 / sklearn 1.8.0 / pytest 9.0.3) and why `tracks` (2.4.6/1.9.1/9.2.0) must not be used.
- I1 does **not print the pytest version** even though pytest 9.0.3 is part of the reference stack (m3):
  add `/opt/r1/envs/trackp/bin/python -m pytest --version`.
- Note the Python patch level: the reference value was produced with Python 3.13.4; the image builds the trackp
  env with `uv venv --python 3.13` (def L48), i.e. whatever 3.13.x is current at build time. Numpy/sklearn/pytest
  are pinned, but the interpreter patch level is not. That is a legitimate small risk to the exact 0.922225
  comparison (residual risk, not a defect); I1's `python -VV` records it, so the report can state it.

### 2.6 `s4_run.sh` — I2 (the 60ec CPU worker determinism test, twice)

- Environment parity with the reference script is good: `env -i HOME=… TMPDIR=… PATH=…/trackp/bin:/usr/bin:/bin`
  plus `PYTHONPATH="$B/src/paper:$B/src/autoresearch_harness/src"`, `AR_HARNESS_ROOT=$B/src/autoresearch_harness`,
  `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `CUDA_VISIBLE_DEVICES=''`,
  `OMP/OPENBLAS/MKL_NUM_THREADS=1` (L41–47) match the reviewed reference's `clean_python`/env block
  (reference L55–57, L66–73) ✓. cwd is the paper checkout (L36), the test path is
  `r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic` (L47, present at `60ecf1da`), with
  `--basetemp` and `-p no:cacheprovider` ✓. `set -uo pipefail` makes the `rc=$?` after each pytest run correct.
- **The comparison reads the wrong file (MAJOR B3).** The test body at `60ecf1da` calls
  `audit.run_config("tabular_mlp", files, [7001, 7001], str(tmp_path), preserve_node_outputs=True, …)` and
  asserts `a[0]["metric"] == a[1]["metric"]`; it **prints nothing**, so the pytest stdout is just pytest's own
  output. The recorded reference value lives in the retained worker `run.log` files: the B1 result review states
  "The two retained log excerpts each report `val_score: 0.922225` and `train_loss: 0.314016`"
  (`B1_TASL7_REAL_WORKER_RESULT_REVIEW_20261107.md` L7), and the reference script's own final step is
  `find "$base/pytest" -type f -name run.log -print -exec sha256sum {} \; -exec cat {} \;` (reference L75).
  The S4 compare heredoc greps `i2_run$i.log` (L61–63), i.e. the pytest stdout, so on a perfectly good run it
  will report `run1_val_score=MISSING`, `run2_val_score=MISSING`, `two_runs_equal=False`,
  `matches_recorded_reference=False` — the author's I2 acceptance is not met by the unit as written.
  *Exact fix:* after each invocation collect the preserved run logs, e.g.
  `find "$B/work/s4_pytest_$i" -name run.log -print | sort` (expect 2 per invocation: seeds [7001, 7001]),
  extract `val_score:` (and `train_loss:`) from each, record `sha256sum` of each run.log and of the pytest
  log, and then compare: (i) all four val_score values equal to each other, (ii) all equal to `0.922225`,
  (iii) train_loss `0.314016` as a secondary check; keep the test's own parsed-metric equality assertion as the
  within-invocation proof and say so in `i2_compare.txt`. Copy the run.log files (or at least their shas and
  values) into `$OUT` so the evidence is durable next to `i2_summary.txt`.
- **The test can silently SKIP (MINOR m4).** It is decorated
  `@pytest.mark.skipif(not (HARNESS / "nodes" / "tabular_mlp").exists() or os.environ.get("C3_SKIP_WORKER") == "1", …)`
  (test L116–119). If `AR_HARNESS_ROOT` is wrong or the harness checkout is missing, pytest exits **0** with
  "1 skipped", the script records `run$i rc=0`, and only the (broken) compare shows MISSING. *Fix:* preflight
  `test -f "$B/src/autoresearch_harness/nodes/tabular_mlp/train.py"` and `test -d "$B/src/paper"` with clear
  `FAIL:` markers; detect skip/pass (`grep -q '1 passed'` / `grep -q 'skipped'`) and mark `i2_pass=no` on skip;
  also `test "$(git -C … rev-parse HEAD)" = 60ecf1da…` / `a3fedbb…` and record `paper_head_ok`/`harness_head_ok`
  (the reference hard-asserts exactly those, reference L24–27; S4 merely records the heads without comparing).
- **No time bound on the test (MINOR m5).** The reference bounds the pytest run with
  `r1/scripts/b1_engineering_timeout.py --seconds 180` (reference L71–73; that script exists at 60ecf1da). S4
  relies only on `+RequestWalltime = 3600`, so a hung worker would occupy a shared local slot for an hour.
  *Fix:* wrap the pytest command in `timeout 600 …` or the reference wrapper.
- **Failure-path visibility (MINOR m6).** The script always ends with `exit 0` (L72) except the missing-paper
  `exit 3` (L36); with B2's stdout/err defaults fixed, write explicit `i2_pass=yes|no`, `i1_ok=` and
  `s6_ok=` lines in `s4_summary`-style output, and make the script's exit code non-zero when the SIF/checkouts/
  I2 are broken (so a `condor_q`/history check does not read as success).

### 2.7 `s4_run.sh` — S6 (xrootd from a worker)

- `timeout 20 xrdfs "root://$ep" ls /dwong` and `timeout 30 xrdcp "root://$ep/dwong/paperb/chain_20261114_xrootd_test.txt" "$OUT/xrdcp_readback.txt" --force`, for both endpoints (L28–32), with rc lines after the pipelines
  (L30–31) — under `set -o pipefail` (L6) those rc values are the timed command's (124 on timeout), which is
  correct (the S6 login-node raw uses the same rc=124 convention). The readback sha is printed (L32) and nothing
  is written outside `$OUT` ✓.
- **Weaker than it can be (MINOR m7):** the readback sha is never compared with the expected value. The test
  file is 51 B with sha256 `90e6b637…d8a7` (chain report §S6; `raw/s6_xrootd_attempt2.txt`). The login-node raw
  also probed `/`, `/dwong`, `/srv/dwong`, `/dwong/paperb` because the export root is ambiguous; the S4 script
  only tries `/dwong`. *Fix:* (i) compute the expected sha from the local file (the worker has `/ceph` mounted —
  `s2/S2L.out` shows `df[/ceph]`): `expected=$(sha256sum /ceph/srv/dwong/paperb/chain_20261114_xrootd_test.txt | awk '{print $1}')`
  and record `match_sha=yes|no` plus `cmp -s` byte equality; (ii) try both `…//dwong/paperb/…` and
  `…//srv/dwong/paperb/…` (and `ls /` / `ls /srv/dwong`) with the same timeouts, so a namespace-root mismatch is
  recorded rather than inferred.

### 2.8 Failure modes, provenance, caps, write scope, credentials

- **SIF / checkouts / mount preflight:** missing paper checkout → `exit 3` ✓; missing harness → silent skip
  (m4); missing SIF → HTCondor itself fails the container start (record `HoldReason`/starter message once B2
  gives an error file); `/work` not mounted in the container → `mkdir`/writes fail silently today (fix by
  preflight `test -d /work && test -d "$B/src/paper"` and a `FAIL:` marker; S2L proves `/work` is normally
  mounted, but the S4 job can land on any of the 245 local slots).
- **pytest basetemp:** `--basetemp="$B/work/s4_pytest_$i"` is safe as-is — pytest removes/recreates its
  basetemp at session start, and run1/run2 use different directories (m8 only recommends the timestamped
  `$OUT` for HOME/TMPDIR: `$B/work/home_$i` and `tmp_$i` are reused across submissions; move them under `$OUT`).
- **Thread env leakage:** `env -i` + explicit OMP/OPENBLAS/MKL=1 + `CUDA_VISIBLE_DEVICES=''` matches the
  reference and isolates leakage ✓. Optional hardening: also set `NUMEXPR_NUM_THREADS=1`
  `VECLIB_MAXIMUM_THREADS=1` (NIT).
- **Job identity (MINOR m9):** `JOB="${_CONDOR_ClusterId:-local}.${_CONDOR_ProcId:-0}"` (L8) will always be
  `local.0`: the S2 container jobs' `_CONDOR_*` environment (s2/S2L.out) contains
  `CHIRP_CONFIG, JOB_IWD, MACHINE_AD, JOB_AD, BIN, SCRATCH_DIR, JOB_PIDS, AssignedGPUs, SLOT` — **no
  `_CONDOR_ClusterId`/`_CONDOR_ProcId`** — so the evidence directory and `identity.txt` are not tied to the
  cluster. *Fix:* pass `arguments = $(ClusterId).$(ProcId)` in the JDL and use `JOB="${1:-local.0}"`, or parse
  `_CONDOR_JOB_AD`.
- **Container image identity (MINOR m10):** `identity.txt` says `container_image=VERSIONS below` (L12) but the
  VERSIONS text goes to `i1_envs.txt`; the SIF's own identity is not recorded. *Fix:* record
  `/opt/r1/VERSIONS.txt` sha256, and the SIF's `/work/dwong/paperb/images/r1-htc-20261114.identity` content
  (`def_sha256`, `sif_sha256`, `sif_bytes` — written by `build_sif.sh` L42–48) plus
  `sha256sum /work/dwong/paperb/images/r1-htc-20261114.sif`, in `identity.txt`.
- **Provenance/read-only:** the script claims "read-only on the checkouts" — it only reads them, and
  `PYTHONDONTWRITEBYTECODE=1` + `-p no:cacheprovider` prevent pycache/cache writes, but nothing verifies it.
  *Fix (NIT):* record `git -C <checkout> status --porcelain` before/after (empty = read-only proof).
- **Caps:** 1 job, CPU only — within the author's ≤10-concurrent / ≤10-GPU-h / no-deletion rules as far as this
  unit adds load. **But** the account-wide cap must be checked at submit time: `raw/s2_precheck.txt` recorded
  `own_active=18` before the S2 submission; record the current `condor_q dwong` and which entries are ours vs.
  the author's, and note the pre-existing over-cap state in the report rather than silently adding to it.
- **Write scope / credentials:** all writes are under `/work/dwong/paperb/` (OUT, work/home/tmp/pytest,
  xrdcp readback) ✓ within the allowed scope; no `/ceph` write, no other user's files, no deletion; the image and
  endpoints need no credentials; no `docker login`/registry/secret is involved. The `git rev-parse`/pytest
  reads are read-only. ✓
- **SIF/apptainer compatibility (Q-S4):** the SIF is built with apptainer 1.5.5-1.el8 on the login node; the
  ETP-local fleet is mixed 1.2.5/1.3.4/1.5.x (chain report L21/L27). S4 is the test; if it lands on an old node
  and fails, record `LastRemoteHost` and that host's `SingularityVersion`
  (`condor_status -af Name SingularityVersion`) before drawing any conclusion — that is an environment finding,
  not a JDL defect. This is also why the EP's `SingularityVersion` must be captured next to the job's result
  (Q-S4's recommendation), which the script itself cannot query from inside the container.

---

## 3. Findings

### BLOCKING

**B1 — `transfer_output_files` guarantees the S4 job is placed on hold at exit.** The seven listed files are
written by `s4_run.sh` under `/work/dwong/paperb/work/s4_<job>_<UTC>/` (L9–12, L25, L34, L47, L53, L68), not in
the job's sandbox; HTCondor treats a listed-but-missing output file as an error and **places the job on hold**
([file-transfer manual](https://htcondor.readthedocs.io/en/23.0/users-manual/file-transfer.html); the
`ON_EXIT_OR_EVICT` section says the same explicitly). Every S4 run would therefore end `HELD`, not
`COMPLETED exit 0`. *Exact fix:* delete the `transfer_output_files` line (evidence stays on shared `/work`,
read it from `$OUT`; the script creates nothing in the sandbox, so auto-transfer has nothing to do), or make the
script write the seven files into the sandbox and keep the list — plus the B2 fields. Re-run the dry-run and the
review after the change.

### MAJOR

**B2 — the JDL has no `output`, `error` or `log`.** Defaults are `/dev/null` (stdout and stderr on Unix) and no
event log at all ([condor_submit](https://htcondor.readthedocs.io/en/23.0/man-pages/condor_submit.html)). Without
them S4 has no event log for the reviewed `htc_events.py` recorder (no queue/execute/end times for the chain
report), no stdout (the `S4_DONE out=$OUT` line that points at the evidence, and every early-failure message, are
lost), and no evidence trail for the smoke-first inspection. *Exact fix:* add `output = s4.out`,
`error = s4.err`, `log = s4.log`; record S4 with
`python3 htc_events.py s4.log --probe <cluster>.0=S4 --utc-offset-minutes 60 --tsv s4_queue_times.tsv`.

**B3 — the I2 cross-run/reference comparison reads the pytest stdout, where `val_score` never appears.** The
metric is in the preserved worker `run.log` files under the pytest basetemp (format `val_score: 0.922225`,
`train_loss: 0.314016`; B1 result review L7; reference script L75). As written, the compare reports MISSING/False
on a good run. *Exact fix:* extract `val_score`/`train_loss` from the two `run.log` files per invocation
(`find "$B/work/s4_pytest_$i" -name run.log`), record their sha256, compare all values to each other and to
`0.922225` (train_loss to `0.314016`), and keep the test's own parsed-metric equality assertion as the
within-invocation proof; copy the run logs' shas/values into `$OUT`.

**B4 — container-image transfer is unverified and, if the image is treated as a transfer input, the job is held
at submit (HoldReasonCode 32).** The JDL uses `should_transfer_files = YES` with an absolute SIF on shared
`/work`; the container-universe default is to transfer unless `should_transfer_container = no` is set (23.0
command name), `ContainerImageSource` distinguishes `"local"` from `"cedar"`, and `MAX_TRANSFER_INPUT_MB`
(default 100 MiB) places over-limit jobs on hold. *Exact fix:* after the SIF exists, dry-run and inspect
`ContainerImageSource`; add `should_transfer_container = no` (or the 25.0.12-accepted equivalent — verify via the
dry-run; newer docs use `transfer_container = false`) so the pre-staged shared-FS image is used in place;
re-dry-run, record the ads. If `ContainerImageSource` shows `cedar`, treat this as a second blocker.

### MINOR

**m1 — no dry-run ad committed; the SIF match gate is unmeasured.** S2's precedent is dry-render → review → one
real job; S4 has only the JDL/script. *Fix:* after the SIF exists, `condor_submit -dry-run` and commit
`dryrun/s4_local_cpu_sif.dry` + `.dry.log`; verify `ContainerImage`/`ContainerImageSource`, `WantContainer`,
the appended SIF gate (`HasSIF`/`HasSandboxImage`), `TransferInput`, requests, `Iwd`/`Cmd`. Measure the gate
read-only before submitting (`condor_status -constraint 'ProvidesETPResources' -af Name HasSIF HasSandboxImage HasContainer`);
it is not in `raw/raw_container_attrs_*.txt` (the four booleans there are `HasContainer HasDockerURL
HasSingularity HasDocker`, per the S2 review).
**m2 — I2's trackp choice is right but unjustified in the script.** The 0.922225 stack is numpy 2.4.4 /
sklearn 1.8.0 / pytest 9.0.3 = the trackp freeze; `tracks` differs (2.4.6/1.9.1/9.2.0). *Fix:* comment at
L35–36 naming the reference stack and why not `tracks`.
**m3 — I1 does not record the pytest version.** Add `/opt/r1/envs/trackp/bin/python -m pytest --version` next to
the numpy/sklearn/pandas imports; also record the SIF identity (m10).
**m4 — the I2 test can silently SKIP** when `AR_HARNESS_ROOT`/`nodes/tabular_mlp` is missing (test L116–119;
pytest rc 0, no metric). *Fix:* preflight the two checkouts, assert heads `60ecf1da`/`a3fedbb` and record
`paper_head_ok`/`harness_head_ok`, detect `skipped`/`passed` and write `i2_pass=yes|no`; nonzero exit on hard
failures.
**m5 — no bound on the pytest run.** Reference wraps it in `b1_engineering_timeout.py --seconds 180`;
S4 has only `RequestWalltime=3600`. *Fix:* `timeout 600 …` or the reference wrapper.
**m6 — failure-path visibility.** The script ends `exit 0` (L72) except missing paper; with B2 fixed, write
explicit PASS/FAIL lines and return nonzero when the SIF/checkouts/I2 fail.
**m7 — S6 evidence is weaker than it can be.** The readback sha is not compared with the expected
`90e6b637…d8a7` (51 B) or with the local `/ceph/srv` copy, and only the `/dwong` namespace root is tried
(the login-node raw tried `/`, `/dwong`, `/srv/dwong`, `/dwong/paperb`). *Fix:* compare sha/bytes against the
local file (the worker has `/ceph` mounted — S2L), try both `…//dwong/paperb/…` and `…//srv/dwong/paperb/…`,
record `match=yes|no`.
**m8 — HOME/TMPDIR reuse.** `$B/work/home_$i`, `tmp_$i` are not timestamped (basetemp itself is safe: pytest
clears it, and run1/run2 use different dirs). *Fix:* place them under the timestamped `$OUT`
(`$OUT/home`, `$OUT/tmp`, `$OUT/pytest_$i`) so retries start clean.
**m9 — job identity is not the cluster id.** `_CONDOR_ClusterId`/`_CONDOR_ProcId` are not in the job
environment (S2L's `_CONDOR_*` list), so `JOB` is always `local.0`. *Fix:* `arguments = $(ClusterId).$(ProcId)`
and use `$1`, or parse `_CONDOR_JOB_AD`.
**m10 — SIF/identity record incomplete.** `identity.txt` line 12 is wrong ("VERSIONS below" but VERSIONS is in
`i1_envs.txt`); add `/opt/r1/VERSIONS.txt` sha256 and the SIF identity
(`/work/dwong/paperb/images/r1-htc-20261114.identity`, `sha256sum` of the SIF).
**m11 — account-wide cap / queue state must be recorded.** `raw/s2_precheck.txt` shows `own_active=18` before
S2; before S4 record `condor_q dwong` (which clusters are ours) and note the ≤10-concurrent condition in the
report; S4 adds 1.
**m12 — SIF/apptainer compatibility (Q-S4).** Record `LastRemoteHost` and that host's `SingularityVersion` after
the run; if S4 fails on an apptainer 1.2.5/1.3.4 node, that is an environment finding, not a JDL defect;
escalate only if needed.

### NIT

**n1** — `transfer_input_files = s4_run.sh` duplicates the executable (harmless; the dry-run shows
`TransferInput="s4_run.sh"`).
**n2** — the compare heredoc invokes `python3` (L56); the Rocky9/CUDA base has `/usr/bin/python3` because `dnf`
is Python-based, but `/opt/r1/envs/harness/bin/python` is a guaranteed path — use it for robustness.
**n3** — thread hardening: also set `NUMEXPR_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1` (optional).
**n4** — provenance: commit the review, the dry-run ad, the job evidence (`$OUT` copy or its sha list),
`clusters.tsv`/`s4_queue_times.tsv` and the submit command with the S4 report; record `git status --porcelain`
for both checkouts before/after to prove the "read-only checkouts" claim.
**n5** — `RequestCPUs = 2` with a threads-1 worker is fine (one process + pytest overhead); keep or reduce to 1,
no impact.

---

## 4. Verdict and what must change before re-review

**The unit cannot be submitted as it stands.** `transfer_output_files` (B1) makes every S4 run end on hold at
exit — a certain, documented HTCondor behaviour — and the JDL has no `output`/`error`/`log` (B2), the I2
comparison reads a file that never contains the metric (B3), and the container-image transfer path is unverified
(B4). The script's environment isolation and reference-stack choice (`trackp`, threads 1, `env -i`, PYTHONPATH/
AR_HARNESS_ROOT) are sound and close to the reviewed reference; the fixes are small and local.

**Minimum change set before re-review (same worktree, then ask for a re-check):**
1. JDL: add `output = s4.out`, `error = s4.err`, `log = s4.log`; remove `transfer_output_files` (keep evidence on
   `/work`); add `should_transfer_container = no` (or the dry-run-verified equivalent); add
   `arguments = $(ClusterId).$(ProcId)`.
2. `s4_run.sh`: fix the I2 comparison to read the preserved `run.log` files (values + sha256, cross-run and vs
   `0.922225`/`0.314016`), copy the run logs/shas into `$OUT`; preflight the checkouts/SIF, assert the two heads,
   detect skip vs pass, bound the pytest run with a timeout, write explicit PASS/FAIL lines and return nonzero on
   hard failures; record the SIF identity and the EP `SingularityVersion` (post-run) in the evidence; try both
   xrootd namespace roots and compare the readback sha with the expected/local sha.
3. After the SIF exists: dry-run + commit the ad; measure `HasSIF`/`HasSandboxImage` read-only and record it;
   then re-review.

**Residual risk that will remain even after those fixes:** the SIF is built with apptainer 1.5.5 while part of the
ETP-local fleet runs 1.2.5/1.3.4 (Q-S4); NEMO2/TOpAS are not involved in S4; the 0.922225 value was recorded on
Python 3.13.4 while the image's trackp interpreter is whatever 3.13.x was current at build time (numpy/sklearn/
pytest match), so a last-digit val_score difference must be reported as a stack-difference note, not silently
accepted or failed; xrootd reachability from a worker is exactly what S6 tests and may legitimately fail; the
account-wide job cap is already above 10 from other jobs (`raw/s2_precheck.txt`), so S4 must not be read as the
cause of cap pressure.

VERDICT: NOT ACCEPTED
