# B1 final host preflight (`_c`): independent review of the filled invocation and local transport

- Date: 2026-11-12
- Reviewer: independent (did not author the unit). Review was read-only on TASL-7; only this file was written.
- Run HEAD: `4b312844962e1106db04d5a60bf996fad0e3e514` (`_c` restart).
- Verdict: **accepted**.

## 1. Inputs reviewed

| Item | Path / value | SHA-256 |
|---|---|---|
| Accepted template at run HEAD | `docs/r1/proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` read from the staged checkout; byte-identical to the local `/tmp` copy | `edc99db6c56d01be7504b1328d05d061683e1018ff127b3285d85d03722b3e11` |
| Filled remote body | `/tmp/paper-b-final-host-preflight-c-20261112-4b31/remote.sh` | `e53f6d72a2bcad4440efba25b34e4d291a41ff5c5626e87a63cde86901ad0c71` (recomputed) |
| Local transport | `/tmp/paper-b-final-host-preflight-c-20261112-4b31/transport.sh` | `84207fa422e8e0318b44a5430ca018424890e0e0408a0bb77dcca06f5e1d041a` |

The `/tmp` template copy is not stale: its digest equals the template at the run HEAD.

## 2. Fidelity to the accepted template

`diff -u` of the template's remote bash block against `remote.sh` shows exactly four differing lines:

1. `HEAD=4b312844962e1106db04d5a60bf996fad0e3e514` (filled HEAD literal).
2. `CAP=/home/dowling/r1_b1_engineering/b1_final_gate_preflight_4b31_20261112_a`
3. `OUT=/home/dowling/exam-x/work/b1_host_preflight_4b31_20261112_a`
4. `CACHE=/home/dowling/r1_b1_engineering/b1_final_gate_pycache_4b31_20261112_a`

All other 53 lines are byte-identical: `set -eu`, `umask 077`, every `unset`/`export`, the `HOME`/path/absence/executable guards, `mkdir -m 700 "$CAP"`, `set -C`, the `AR_HARNESS_ROOT`-before-import ordering, the quoted gate heredoc (including the `EXPECTED_HEAD`/rule/author-gate/anchor checks and `GATE_PASS` print), `gate.exit`, the `b1_host_preflight` invocation, `preflight.exit`, the `PRIVATE_CAPTURE`/`PREFLIGHT_OUTPUT` print, the four-file `sha256sum`, and `exit "$probe_rc"`. No guard, export, check or record was added, removed or weakened.

The transport differs from the template only in its three placeholders: `REMOTE_SCRIPT` path, `EXPECTED_SCRIPT_SHA`, and the run-specific `mktemp -d /private/tmp/paper-b-final-host-preflight-capture-c-20261112.XXXXXXXX` prefix. All control flow is identical.

## 3. Bindings (verified on TASL-7)

- HEAD literal is exactly the run HEAD, 40 lowercase hex characters, and passes the `case`/length guards. The derived `PAPER` path is `/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`, which exists and is not a symlink.
- `HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` exists, is not a symlink, is at pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, and is clean (`git status --porcelain --untracked-files=all` = 0).
- `PY=/home/dowling/exam-x/work/venv/bin/python` is executable; it is a venv symlink to uv CPython 3.13.4, `sys.executable` = the venv path, `sys.prefix` = `/home/dowling/exam-x/work/venv`; sibling `python3` is the same file, so `worker_environment()` identity checks hold.
- `CAP`, `OUT`, `CACHE` are all absent and non-symlinks; the absence checks precede `mkdir`. `OUT`'s parent is exactly `work_dir=/home/dowling/exam-x/work`, so the direct-child rule in `b1_host_preflight.check_inputs` holds.
- The unrelated `_c` batch child `/home/dowling/exam-x/work/b1_4b31_20261112_c` is absent and is not referenced or created by the script/preflight.
- Config `paper_commit=1334c61619f76e71a7c6ba83c837714f9d3f0720` is an ancestor of HEAD (`merge-base --is-ancestor` OK), and `git diff --name-only 1334c616 4b312844 -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty (0 lines). This also satisfies the constructor's working-tree protected-path check.
- Config `work_dir`, `models_dir`, `host=TASL-7`, `gpu_uuid`, `harness_commit`, rule sha and the Stage A/amendment/acceptance/reference pins all match the staged bytes (see §4).
- `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1` are exported, and `worker_environment()` re-forces the same; the worker `PATH` prepends the venv and resolves `python3` to the same interpreter.
- `GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/index/object/alternate/config-count/config-parameters/global/system variables are unset; `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_OPTIONAL_LOCKS=0`, so the read-only git checks cannot take index locks.
- `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPYCACHEPREFIX="$CACHE"` prevent checkout bytecode writes; `set -C` (noclobber) is active before the first `>` capture write.
- Restricted `PATH` resolves `python`, `python3`, `git`, `nvidia-smi`, `sha256sum` and `mkdir` (all present under `/usr/bin` or the venv).

## 4. Staged-site state (read-only)

- PAPER is at the exact HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`, clean including untracked files.
- `r1/scripts/b1_host_preflight.py` is tracked at HEAD; working-tree SHA `7cc2c560bfd7be6a05eac958e88041371124d8ecc6fe1828e6187abd07c83f00` equals `git show HEAD:...`.
- Pinned inputs match their config and authorization-note digests: rule `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`; registry `2c6ef6b329694536df6a23345e4313d0cb2dcbf447113023e18f60fcb608e723`; prompts `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a`; server binary `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b` (build line `version: 0.7.0-dev (build 1, commit 620d222)` matches config); anchor reference JSON `84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd`; Stage A t7h8 table `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c`; t7j10 amendment `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`; acceptance record `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e` (it names both table shas); authorization note `0ef175aaad4544298a9944565ca15437abafb0346ed8e2d03a79fc8d920ed32e`.
- Registry and Stage A rows are consistent for the preflight: 18 eligible rows, every eligible row's `model_sha256` equals its registry `quant_source.sha256`, every passed row has the pinned build and a positive finite footprint, `random_valid`/`scripted` carry `kind` values so the preflight skips them, and the anchor `qwen25_coder_7b` is eligible with model SHA `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` (recomputed from the GGUF).
- All 22 registry model files exist under `/home/dowling/exam-x/models`, sizes equal `size_bytes`, and each `.verified` pin equals the registry SHA. The three template-repair files exist and match the config's `template_repairs` digests, and the config/registry repair maps are identical.
- Free space on the approved filesystem is `567,345,426,432` bytes (≈529 GiB), above the 100 GB floor.
- GPU census: the pinned UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` is present (RTX 4090), 23,812 MiB free, 236 MiB used, 0% utilisation, and `nvidia-smi --query-compute-apps` is empty.
- Lease lock `/home/dowling/r1_locks/gpu0.lock` exists, is a regular non-symlink file owned by uid 1011 with link count 1; a non-blocking `flock` probe acquired and released it, and `/proc/locks` has no `gpu0` entry.
- The `_b` marker `/home/dowling/r1_locks/trackx_evidence.active` is present with run `fffa_20261111_b`; nothing in the gate/preflight path reads or retires it (only `b1_o2_marker.py`, the later handover tool, references it).
- Older staged checkouts are untouched: `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` and `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa` are each at their own HEAD and clean.

## 5. Command correctness and safety

- Quoting/interpolation: the HEAD literal is guarded to `[0-9a-f]{40}` before use; all path expansions in tests and redirections are double-quoted; the gate heredoc is quoted (`<<'PY'`), so no host-side expansion; the gate reads its program from stdin (`-B -`), not from the captured files.
- Transport: `shasum -a 256` is checked against the reviewed literal before any remote action; the capture directory is created with `mktemp -d` (random suffix, exclusive), then `set -C`; `ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' < "$REMOTE_SCRIPT"` sends the exact reviewed bytes; `ssh.exit` is written and hashes are printed; it does not retry.
- Writes: the only write targets are `CAP` (gate/preflight logs and exit records), `OUT` (created by the preflight; server record/log and `_to_delete` versions land under it), and `CACHE` (bytecode prefix, not created because `-B`/`PYTHONDONTWRITEBYTECODE` are in force). Source checkouts, models, tables, the `_b` marker and older outputs are read-only.
- Signals: the invocation itself sends nothing. The native preflight installs handlers and, through the reviewed owned-server stop path, signals only its own `start_new_session` child group after verifying `pgid == getpgid(pid)`; no unrelated process can be signalled.
- Failure behaviour: a non-zero gate exits before the preflight; a non-zero preflight is recorded; a signal/interruption propagates after owned-child stop and lease close; the capture directory and `OUT` are retained; there is no automatic rerun. Missing logs/exit records are STOP, as the accepted template requires.
- No secrets are present in either script; SSH uses `BatchMode`.

## 6. Residual notes (not findings; inherited from the accepted template)

1. The transport has no overall command timeout / `ServerAliveInterval`; a hung remote command leaves the local `ssh` waiting. This is not unsafe (the operator STOPs and preserves the scene), but it should be watched.
2. The local hash-then-read of `remote.sh` leaves a tiny TOCTOU window on the operator's `/tmp`; the path is owner-writable only and this is template-inherited.
3. On gate failure the remote body exits before printing `PRIVATE_CAPTURE`/hashes; `CAP` is a fixed reviewed literal and `gate.log`/`gate.exit` are still created, so evidence is not lost.
4. The preflight legitimately reads/hashes the large GGUFs and starts exactly one owned anchor server; that is the intended evidence-producing work, not a source mutation.

## 7. Conclusion

The filled remote script is substantively the accepted template with only the permitted HEAD and run-specific path substitutions; the transport is the accepted wrapper with only its reviewed literals. All bindings, staged-site preconditions, fresh-path exclusions and safety properties hold on the current TASL-7 state. Running exactly this filled script through exactly this transport once is safe and should yield the gate/preflight evidence the run-HEAD review requires.

VERDICT: accepted
