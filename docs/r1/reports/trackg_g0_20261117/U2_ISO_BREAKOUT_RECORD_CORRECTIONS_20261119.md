# Track G G.0 U2 `mlgym_breakout_minatar` — accepted MINOR record corrections (19 November 2026)

**Status: record corrections APPLIED (no GPU/U2 run, no unit/code edit, no deletion, no commit/push).**
Correction window: **2026-11-19T05:20–05:35Z** (record and capture notes stamped `2026-11-19T05:30Z`). This note is
the change record for
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_breakout_minatar_20261119T045751Z/`; the result itself carries a
Correction note with the same date/UTC.

**Authority.** Accepted result review
`docs/r1/reviews/TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` sha256
**`d4cdd9bbd53fd7fceefbca5f41314006b8c824d948e82d56bfadf5818f272ead`** (ACCEPTED — 0 BLOCKING, 0 MAJOR, 7
result-specific + 7 shared-standard MINOR, conditions R1–R7/S1–S7). Underlying accepted unit sha
`1b53c3abc4d70b0e31840ecb18b3a4234df8a58e230d3872b6e1f29f8294604e` (committed at `af5fa558`), unit review sha
`217822fe8385a3ee29f91ddf4f286b0cb890c4c17704fe10892ef7f47035bfa9`, JAX fix record sha
`ad2d139a9b891ebdfedb89ef6056f8aac7491a73d965c2aa6ed74cd9afc1f391`; accepted kit update
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026` and its review
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`; worktree `ops-tasl-20261116` HEAD
`af5fa558`, `origin/main` `de3de54f`. The only files written are inside the result directory and this campaign
note; no commit/push was made and no Ada write occurred (read-only SSH only).

## 1. New shas (old → new)

| object | old sha256 | new sha256 |
|---|---|---|
| result md `U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md` | `532513e7799044959e70fae758a42a2d347defca2e2ede4eeecc990fa1a10323` | **`ca5937fc2695daa667b0ebf4e9856a460596346882d966e0c259867a7288a8a7`** |
| `SHA256SUMS` | `e55aa2827a0e9096b02656adb369440f7f6adeb19296a663ba18297f29ff29ad` (1,115 entries) | **`5abe549cc0b0146d088fcf56abf64efe64820278fae13487286bf82b6ea59c59`** (1,117 entries) |
| `scripts/README.txt` | — (new) | **`c5fcb32dcfb350da526afb3b981e97545ae2d5c1f255cd34ad092b32e222399e`** |
| `references/JAX_ENV_FIX_EVIDENCE_COMPANION_20261119.md` | — (new) | **`c88067f288f70372f7cb13cce2f3919043173c69254b279d59b8ffe66269a3b3`** |

**Changed files:** `U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md`, `SHA256SUMS`, new `scripts/README.txt`,
new `references/JAX_ENV_FIX_EVIDENCE_COMPANION_20261119.md`. **No capture file was modified** (see §4: all
existing captures are byte-identical to live Ada, so none needed refreshing). No file deleted; the executed unit
and JAX fix-record copies in `references/` remain byte-identical to the committed files.

## 2. Conditions applied

- **R1 — executed-unit precheck STOP text reconciled to the accepted M-4/C3 path.** Recorded in the result: the
  executed unit (75 lines, unchanged, sha `1b53c3ab…`) still says the freeze sha "equals the fix record's
  `d33c9612…`" and "pytest available or absence = STOP"; the run followed the accepted test-only-add path
  instead. Verified from captures: pre-add 65-line **sorted** freeze = `d33c9612…` (raw `859b9ff0…`); the first
  `smoke_entry` dry-run failed because pytest was absent; offline add was **exactly** `pytest==9.2.0`,
  `iniconfig==2.3.1`, `pluggy==1.7.0` (`freeze_diff.txt` is exactly those 3 additions); launch 68-line sorted
  freeze = `80a455c6…` (raw `956d0b4f…`); JAX versions (`0.4.35`/`0.4.34`/plugins `0.4.35`), 8 devices and
  absent `nvidia-cuda-nvcc-cu12` unchanged (`env_before`/`env_after`); live env today re-verified read-only as
  the same 68-line `80a455c6…` freeze. No rerun. Since this pass is record-only, the reconciliation is in the
  record (executed unit bytes not amended), per the "no unit/code edit" constraint.
- **R2 — `s002` fields.** Recorded explicitly: `process.returncode: 4`, `process.leftover_processes_killed:
  true`, `killed_with: null`, `timed_out: false`; cgroup kill then `empty_after: true`/`removed: true`; empty
  result channel (`e3b0c44…`); expected for the deliberately divergent run, and the fixed verifier checks rc 0
  only for ok runs.
- **R3 — timestamps.** Corrected: runner/evidence-dir start **`04:57:51Z`** (from
  `launch_mlgym_breakout_minatar_attempt2.log` `start=`), gate JSON `utc` **`04:57:57Z`** (gate_check capture
  time), sampler start `04:57:57Z` with first row `04:57:58.072Z`, inside-scope cgroup/probe capture
  **`04:57:59Z`**. The previous single "launched at 04:57:51Z" sentence is replaced by this sequence.
- **R4 — disk numbers from the captures.** `disk_before.txt`/`disk_after.txt` values
  **`75,439,427,584` / `75,401,625,600` B** now cited; the `RESULT_STATUS.txt` `disk_avail_*` samples
  (`75,439,415,296` / `75,401,555,968`, a different `df` instant) are named as not-the-source. 50 GiB floor
  unaffected; post-run footprint 19 M evidence / 19 M runs.
- **R5 — all-8-card `jax.devices()` allocation and pre-scope call disclosed.** Recorded: the required no-mask
  `jax.devices()` checks initialised a JAX client on all 8 cards — JAX-fix prechecks at
  `04:54:25Z`/`04:54:29Z`, the **pre-scope `env.txt` capture at `04:57:51Z`** (outside the whole-smoke sampler,
  which started `04:57:57Z`), and the inside-scope precheck (`04:57:59Z`; mid-watcher snapshot at `04:58:06Z`,
  pid `246999`, 426 MiB app / 439 MiB used per card). Minimal initialisation (seconds, no GPU compute, no
  process touched); only card 6 was used by the smoke and returned to 5 MiB/0 %. The "no other user's
  process/card was disturbed" wording was narrowed accordingly in the record and its scope statements.
- **R6 — "10 worker pids" corrected.** Now: 10 processes of the run scope = **2 transient `jax.devices()`
  precheck clients** (pids `245960` at 04:58:01–03Z and `246999` at 04:58:06–07Z, each reaching 426 MiB; the
  pre-scope `env.txt` client exited before the sampler started and is not in the sampler list) + **8 run
  workers** (`247898, 265499, 269241, 278721, 290683, 300852, 311394, 321566`); the 634 MiB max is worker pid
  `300852` at `05:03:50.8Z`.
- **R7 — JAX fix captures cited.** New companion note
  `references/JAX_ENV_FIX_EVIDENCE_COMPANION_20261119.md` cites the committed fix record
  (`ad2d139a…`) and the captures in `prechecks_jax_env/` with full shas (raw/sorted pre-add and launch freezes,
  freeze diff, offline install log, env before/after), the live re-verification, and the residual that the exact
  `uv remove nvidia-cuda-nvcc-cu12` command/output was not captured. No environment change.
- **S1 — record identity added.** Result now records its own file path and post-correction sha (via the
  `SHA256SUMS` entry, and this note/`SHA256SUMS`), the newly added capture shas, canonical `node_spec_sha256`
  **`db57b202301e323d4471cf23ef6ad3b822d5f5e0d471f1896ffda3041af2a10a`** with the kit-loader formula (recomputed
  on live Ada read-only; = every run record), raw node-spec sha `b3cedcd6…`, representative-edit manifest
  `a7fe205a…`, E1–E4 diff shas (`8403016b…`, `e9932b59…`, `ec73a85a…`, `089624e9…`), executed unit/review/fix
  shas, and the one-JSON-line-per-run statement (`verify_full.json` `smoke.json_run_lines: 9`).
- **S2 — scripts claim corrected / v1 verifier residual recorded.** The false claim that `scripts/` contained
  "the documented fix patches" is removed; new `scripts/README.txt` records the three live-source copies and
  their shas (`run_node_jax.sh` `4b5113fe…`, `verify_u2_records_jax.py` `8822495f…`, `compute_sampler_max.py`
  `7d9f472e…`), and states that **no v1 verifier source and no fix patch were preserved** (only the v1 outputs
  `verify_full.v1_verifier_bug.json` `75a9fc92…` / `.summary.v1_verifier_bug.txt` `c027c74b…`); a byte-exact v1
  source cannot be reconstructed without guessing. The result's verifier-deviation paragraph cross-references
  this.
- **S3 — floor basis/contamination/no-switch.** Added: 8 GiB floor basis (~2.85 GB measured torch peak, prior
  accepted 24 GiB run-1 floor, chosen card 48,427 MiB free; this JAX node's whole-smoke bound 634 MiB); mid-run
  contamination rule (free VRAM below baseline peak + 2 GiB or a new co-tenant → STOP/record); no switch from
  the launch card (`GPU-3b36edea-…` is the only card in qualify/before/mid/after and every record).
- **S4 — no-resume + filesystem.** Added "no resume (an interrupted unit re-runs wholly from a new
  `<runs-root>`; none occurred)" and named the disk filesystem `/dev/md0p3` on `/`.
- **S5 — "preserved unaltered" not read-only.** The live evidence dirs/files are `drwxrwxr-x`/`-rw-rw-r--`
  (operator-writable, unaltered, hash-matching); wording replaced.
- **S6 — full authority shas.** Kit update report and its review now cited with full 64-hex shas; result-review
  sha cited in the header.
- **S7 — C4/C5 unit-vs-launch-notes split recorded.** The record states the launch notes/captures are the
  operative form and maps C1–C5 to them (C1 licence, C2 JAX fix, C3 prechecks/test-only add/probe, C4
  kit-clean/pin/data-prep/gate, C5 timeout/floor/no-resume/STOPs); the executed unit text was not amended
  (record-only correction), and its superseded precheck wording is reconciled under R1.

## 3. Verification

- `SHA256SUMS` regenerated over every file in the result directory except itself and verified with
  `shasum -a 256 -c SHA256SUMS`: **rc 0, 1,117/1,117 entries OK** (1,118 files including `SHA256SUMS`); the two
  new files are listed; the result md's new sha is the `./U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md`
  entry.
- **Live-Ada cross-check (read-only, no `jax.devices()`, no write):** for the live evidence dir
  `/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/` I hashed every
  file and compared it with the corrected capture: **1,108 live files, 1,108 byte-identical, 0 differing,
  0 live-only**; the local-only files are exactly the **7** Mac record files (result md, three `references/`
  copies, three `scripts/` sources) plus the **2** correction-pass additions (`scripts/README.txt`,
  `references/JAX_ENV_FIX_EVIDENCE_COMPANION_20261119.md`) — i.e. the capture remains byte-faithful to live Ada.
- Live read-only re-verification: canonical `node_spec_sha256` = `db57b202…` (kit loader); campaign script
  shas match the copies; `uv pip freeze` = 68 lines sha `80a455c6…` with jax 0.4.35/jaxlib 0.4.34/plugins
  0.4.35/pytest 9.2.0/iniconfig 2.3.1/pluggy 1.7.0; evidence dir/file modes `drwxrwxr-x`/`-rw-rw-r--`.
- No measured number changed. No unit/code, pin, manifest, run record, sampler CSV, gate JSON, verifier JSON or
  existing capture was modified; no GPU/U2 work, no rerun, no deletion, no commit/push, no HTCondor/deepthought
  action.

## 4. Residuals (recorded, not guessed)

1. **Verifier v1 source / fix patch (S2):** not preserved anywhere (the live verifier was edited in place; only
   v1 outputs remain). Byte-exact reconstruction is not possible without guessing, so none was fabricated. The
   fixed verifier's own docstring still describes the v1 rule (cosmetic; no check uses it).
2. **JAX fix command transcript (R7):** the exact `uv remove nvidia-cuda-nvcc-cu12` command line/output was not
   captured; the fix record plus `env_before/after` evidence (nvcc absent, JAX working) is what exists.
3. **Executed unit text (R1/S7):** not amended (record-only correction, per the no-unit-edit constraint); the
   precheck STOP wording remains in the preserved executed-unit bytes and is reconciled in the record. If a later
   pass is authorised to edit units, the unit could be amended; the measurement does not depend on it.
4. **Mid-smoke utilisation:** remains `NOT_CAPTURED_MID_SMOKE` (the dedicated watcher fired in the precheck
   window; mid-smoke census is sampler-derived). Not recoverable without a rerun, which is not authorised.
5. **Attempt-1 evidence:** the live standalone pre-launch dir
   `u2_iso_mlgym_breakout_minatar_20261119T045646Z/` contains additional pre-launch captures (data_manifest,
   disk_before, env, host, kit, pins, logs) beyond the six files mirrored under the result's
   `attempt1_prelaunch_gate_stop/`; neither the review nor the conditions require them, and no capture was
   changed. Recorded as an observation only (no rerun needed; could be mirrored later if desired).

## 5. Attestation

Written locally in `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116` plus
read-only SSH to Ada (`ssh -o BatchMode=yes experiment_zhixu`, no writes, no GPU device initialisation). Commands:
reads of the review/result/captures/unit/fix record; `shasum -a 256`/`shasum -a 256 -c`; Python recomputation of
the sampler pids and the canonical node spec; `cp`/`write` of the two new record files; regeneration of
`SHA256SUMS`; live `sha256sum`, `stat`, `ls`, `cat`, `uv pip freeze | sort`. No smoke, no retry, no unit/code
edit, no deletion, no commit/push, no TASL/HTCondor/deepthought action.
