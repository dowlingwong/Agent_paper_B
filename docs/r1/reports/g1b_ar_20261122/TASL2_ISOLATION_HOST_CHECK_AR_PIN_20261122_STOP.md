# TASL-2 host check at harness pin `2d09f9a9` for the autoresearch G.1b spec — **STOP / FAIL at §3.3** (22 November 2026)

**Status: STOP — FAIL. No binding record was written; this file is evidence, not a launch record and not an
authorization.** ENGINEERING_ONLY; AI-assisted (DeepSeek Harness agent `ar-pin-hostcheck`, delegated by the lead).
The task was to execute `docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md` §§0–6 and
write `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md` only if C1–C7 pass. The procedure's §3.3 STOP fired:
the spec interpreter `ar-cond7a` now runs **Python 3.12.16**, but §3.3 requires **3.12.15**. Per §7 the run stopped
there ("report and wait; nothing is retried silently"): sections 4–5 (**data staging, C1–C7, the supplementary
pytest and the AST CUDA-IPC scan**) were **not started**, and no `host_check_*` lines were written.

- Host: `TASL-2` only (`ssh -o BatchMode=yes portal_zhixu`), unprivileged uid/euid `1008(dowling)`, no sudo.
- Harness pin: `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` (branch `mac-trackg-t1-ar-20261121`, on GitHub at the pin).
- Run root: `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/` (`scripts/`, `captures/`, `logs/`,
  `records/`, `work/`). Phase-A window 2026-11-22T10:41:24Z–10:41:30Z; end-state capture 10:42:04Z (UTC; TASL-2
  local clock PST, UTC−8).

## 1. What passed

| § | Item | Result | Key evidence |
|---|---|---|---|
| 0 | Preflight: host/uid/disk/GPU/lease/seven-node/attempt-1 archive | **PASS** | TASL-2, Ubuntu 22.04.5, kernel `6.8.0-149-generic`, cgroup v2 `nsdelegate`, 32 CPUs; euid 1008; `/` **352.4 GiB free** (≥ 20 GiB); GPU `GPU-4d623e76-7587-ee15-a633-46f60d220d94` with **no compute apps** and the lease `~/r1_locks/gpu0.lock` **free**; attempt-1 archive `p3a_operator_20261027` mtime 2026-11-17 15:42:26 size 4096 and lease log mtime 2026-11-17 15:42:35 size 55726, `stat` only (`host_facts.json`, `lease_status_pre.txt`, `attempt1_stat_before.txt`) |
| 1 | Second checkout `/home/dowling/r1_tracks/t1_tasl/harness_ar` at the pin | **PASS** | cloned from GitHub (`git clone --no-checkout`), `fetch origin mac-trackg-t1-ar-20261121` (GitHub `ls-remote` gives exactly `2d09f9a9…`), `checkout --detach 2d09f9a9…`; `HEAD` = pin, `symbolic-ref` rc 1 (detached), `git status --porcelain --untracked-files=all` **empty**; `merge-base --is-ancestor c025f89a HEAD` **rc 0**; worktree list has one entry; bundle path not needed because the branch is on GitHub (`harness_ar_pin.txt`, `step1_git_ls_remote.txt`, `logs/step1_*.log`) |
| 1 | Seven-node checkout unchanged | **PASS** | `/home/dowling/r1_tracks/t1_tasl/harness` still at `c025f89a…`, detached, no stash, **tracked tree clean** and unchanged before/after; it carries four **pre-existing untracked `data` symlinks** from the 21 Nov G.1b runs (mtimes 2026-11-21 02:32/14:42/14:52/19:25), not created or changed by this run (`seven_node_before.txt`, `seven_node_after_step1.txt`, `post_state.txt`) |
| 2 | Node pins at the pin (ar-cond7a, `PYTHONPATH=harness_ar/src`) | **PASS** | all four exact: spec file `5bdce00a…`, `raw_sha256` `5c1bdf3d…`, committed pin `147f0d35…`, edit manifest `55f2666a…` (20 frozen entries before the data link) (`node_pins.json/.txt`) |

## 2. The STOP — §3.3 Python

| § | Item | Result | Evidence |
|---|---|---|---|
| 3.1 | `uv --version` | **PASS** | `uv 0.13.6 (x86_64-unknown-linux-gnu)` |
| 3.2 | `uv pip freeze` equals the committed freeze | **PASS** | 122 lines, raw output sha256 **`11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`**, **byte-identical** to `sweep2/g1b/env/ar-cond7a.freeze.txt` (staged sha256 also `11def6ad…`); sorted equal too (`env_freeze_uv.txt`, `env_check.json`) |
| 3.3 | Python must be **3.12.15** | **FAIL — STOP** | `…/venvs/ar-cond7a/bin/python -c "import sys; print(sys.version)"` → **`3.12.16 (main, Oct 26 2026, [Clang 23.1.3])`**; `uv pip freeze` itself says `Using Python 3.12.16 environment at: …/ar-cond7a`; `readlink -f` → `…/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12` (`env_check.json/.txt`, `python_drift_evidence.txt`) |
| 3.3 | torch | **PASS** | `2.6.0+cu124`, CUDA `12.4`, `cuda_available=True` |

Procedure text that fired (verbatim): §3.3 "Run … `It must give 3.12.15`"; §7 "`The freeze or Python of ar-cond7a
differs from §3.`"

## 3. Root cause of the drift (host state changed after the census)

`ar-cond7a` was made as a byte copy of `trackp-gpu`; its `bin/python` is a symlink to uv's **unversioned** alias
`/home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12` (its `pyvenv.cfg` `home` is the
same unversioned alias). On **2026-11-21T09:53:39Z** (01:53:39 PST) that alias was retargeted to
`cpython-3.12.16-linux-x86_64-gnu`; the `3.12` alias link's mtime is exactly then, and the `cpython-3.12.15` install
directory from 25 Oct is still present but no longer reachable through the venv's chain.

- The U2 census recorded `python=Python 3.12.15` at **2026-11-21T02:30:30Z**
  (`TASL2_AR_COND7A_RESULT_20261121_captures/env.txt`); its smoke ran 2026-11-21T01:58:19Z–02:28:10Z.
- The `3.12` alias retarget at 09:53:39Z is **after** that, and coincides with the T1 precheck's
  `uv python install 3.12.16` (`TASL2_T1_PRECHECK_20261121.md` §2.2, which built `torch312`/`jax312` at 3.12.16).
  The later `uv python install` silently moved the shared `3.12` alias, so the "unchanged" AR census venv now
  resolves to 3.12.16. The freeze and torch are unaffected.
- This is launch-blocking beyond the host check: the third-note draft's own STOPs include "`uv pip freeze` of
  ar-cond7a not equal to the committed freeze, **or a Python other than 3.12.15**"
  (`G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md` line 92), and AR-ENV option A says the venv is "unchanged". The AR spec
  still pins `envs.ar-cond7a.python = 3.12.15`.

## 4. What was NOT done (per §7 "report and wait")

Not started after the STOP: §4 data staging under `…/data/autoresearch_fixedtokens` (still **absent**, no HF
download); §5 C1–C7; the supplementary `tests/trackg/test_trackg_isolation.py`; the AST CUDA-IPC scan; §6 binding
record. **No `host_check_host` / `host_check_harness_commit` / `host_check_items` / `host_check_verdict` lines were
written anywhere** — no record was placed at `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md`,
and the spec's `hosts.TASL-2.isolation_host_check.sha256` stays `TODO`.

## 5. State changes and non-authorities

Only TASL-2 was used; TASL-7, HTCondor and deepthought were not contacted. No T1 job was started. Nothing was
deleted, committed or pushed; nothing was moved aside (no collision). The only host changes are the new run root and
the second checkout `/home/dowling/r1_tracks/t1_tasl/harness_ar` (clean at the pin; the `data` link of §4 was not
created). The seven-node checkout's runs/ and sealed_g1b/ trees, the Track P attempt-1 archive and its lease log were
not touched (`stat` only; mtimes unchanged 2026-11-17). The GPU was never used: lease free before/after, no compute
apps, 353 MiB / 0 % idle before and after. `PYTHONDONTWRITEBYTECODE=1` and `taskset -c 16-31` were used for every
Python step. This is host evidence, not a launch authorization: the author's signed note and both keys are still
required, and the AR-ENV interpreter question must be settled first.

## 6. Captures

Fetched copy in this repo (uncommitted):
`docs/r1/reports/g1b_ar_20261122/TASL2_ISOLATION_HOST_CHECK_AR_PIN_20261122_STOP_captures/` — **45 files**
(44 listed + `SHA256SUMS`), 228 KiB; `SHA256SUMS` sha256
**`00f2a9cbab135438ef97a7982714aa9a34dcd0084cf02b613dd7be589b33688e`**; `sha256sum -c` rc 0 on TASL-2 and
`shasum -a 256 -c` rc 0 after fetch. The digest file itself is outside the capture set on the host:
`/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/SHA256SUMS.sha256` (same sha256).
Key files: `SUMMARY.json/.txt`, `stop_items.txt`, `host_facts.json/.txt`, `harness_ar_pin.txt`,
`step1_git_ls_remote.txt`, `node_pins.json/.txt`, `env_check.json/.txt`, `env_freeze_uv.txt`,
`python_drift_evidence.txt`, `seven_node_before.txt`, `seven_node_after_step1.txt`, `post_state.txt`, `logs/`,
`scripts/`.

## 7. Options for the author / lead (not decisions; none was taken)

The AR-ENV interpreter must be settled and the procedure/spec/note text brought in line before the host check can be
rerun at the pin with C1–C7.

1. **Accept 3.12.16** as the AR launch interpreter: it changes the spec (`envs.ar-cond7a.python`), the third note's
   env line/P7 and §3.3 of the procedure (freeze and torch unchanged). It is a *different* interpreter than the U2
   census one, so this is an author decision, not a host-check detail.
2. **Restore the census 3.12.15** in `ar-cond7a`: the venv's `bin/python` chain and `pyvenv.cfg` `home` currently
   resolve through the retargeted unversioned alias; pointing the venv at `cpython-3.12.15-linux-x86_64-gnu` would
   restore it, but it edits the "unchanged" census venv and must be an explicit author/AR-ENV step (and must be
   kept stable against future `uv python install` alias moves).
3. **AR-ENV option B (byte copy under `…/envs/ar-cond7a`)**: note a plain copy now also resolves 3.12.16 through the
   same alias, so option B would have to pin the copy's interpreter to 3.12.15 to satisfy the check; only
   `hosts.TASL-2.env_python` changes in the spec.
4. **AR-ENV option C (uv rebuild from the freeze at 3.12.15)**: not recommended in the note; would be a new
   environment, and the freeze check would have to pass.

Whichever is chosen: the seven-node checkout retains four pre-existing untracked `data` symlinks from the 21 Nov
G.1b runs, so the eventual C7 wording "clean at c025f89a" should be read as tracked-clean / HEAD-unchanged (as the
21 Nov binding's method did), or the procedure should allow those run artifacts explicitly — the same way it allows
the AR checkout's `nodes/autoresearch_fixedtokens/data` link.

**AI-assisted: DeepSeek Harness agent `ar-pin-hostcheck`, 22 Nov 2026. ENGINEERING_ONLY; uncommitted; STOP/FAIL.**
