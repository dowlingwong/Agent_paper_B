# Companion evidence note — Ada JAX environment fix for `mlgym_breakout_minatar` (19 November 2026)

**Purpose (result-review condition R7).** The committed fix record
`docs/r1/reports/trackg_g0_20261117/JAX_ENV_FIX_20261119.md` (sha256
`ad2d139a9b891ebdfedb89ef6056f8aac7491a73d965c2aa6ed74cd9afc1f391`; a byte-identical copy is at
`references/JAX_ENV_FIX_20261119.md`) records the fix but carried no captures. This companion note cites the
captures, which live in this result directory under `prechecks_jax_env/`; they are byte-identical to the Ada
prechecks directory `/home/dowling/r1_engineering/u2_iso_20261119/prechecks_jax_20261119T045425Z/` captured at
`04:54:25–04:54:29Z` (re-verified read-only). It does not change the environment or re-run the fix.

## Captures and hashes (all in `prechecks_jax_env/`)

| capture | sha256 | content |
|---|---|---|
| `freeze_before.txt` | `859b9ff09cd013835900503388c875c05979056082c69e92854660c4f7a00839` | raw 65-line `uv pip freeze` before the test-only add |
| `freeze_before_sorted.txt` | `d33c96120c0be3cf20fcb2b9d783ac5366d6b0d3313e6cfe4c90583f89940217` | sorted 65-line freeze — **exactly the fix record's sha** |
| `freeze_diff.txt` | `a4d9edb5abfaa904eac8711804d7b028d77744f1189a5ca7ef085ff754cef214` | exactly 3 additions: `iniconfig==2.3.1`, `pluggy==1.7.0`, `pytest==9.2.0` (`diff_rc=1`) |
| `pytest_install.log` | `364a157d2b20f93fafcb80d1effc46b966b27c8841903b351116f399b30333e3` | offline resolve of 5 / install of exactly those 3 packages in 14 ms, `install_rc=0` |
| `env_before.txt` | `8c059418aad1a9721171fd4c9746b81c958f0490eb865d36577dbedfd154f4a4` | Python 3.12.16; jax 0.4.35 / jaxlib 0.4.34 / jax-cuda12 plugin+pjrt 0.4.35; nvcc absent; `jax.devices()` = 8 GPU (CudaDevice 0–7); `pytest` ModuleNotFoundError |
| `env_after.txt` | `183bcc9a5fb1862f3554c9d18464cd9dd68826363da29ada6c3f675e6080635c` | same Python/JAX versions and 8 devices; nvcc absent; `pytest 9.2.0`; `smoke_entry` found; imports OK |
| `freeze_after.txt` | `956d0b4fcf28e48451ae4b92a451a2c2db764805378ffbcd6b01a2649caf8d0a` | raw 68-line launch freeze |
| `freeze_after_sorted.txt` | `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1` | sorted 68-line launch freeze (= 65-line `d33c9612…` + exactly the 3 test-only packages) |

Live re-verification (2026-11-19T05:27Z, read-only, **no GPU initialisation**):
`uv pip freeze --python /home/dowling/r1_trackg_20261117/envs/jax312/bin/python | sort | sha256sum` =
`80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1`, 68 lines, with `jax==0.4.35`,
`jaxlib==0.4.34`, `jax-cuda12-plugin==0.4.35`, `jax-cuda12-pjrt==0.4.35`, `pytest==9.2.0`,
`iniconfig==2.3.1`, `pluggy==1.7.0`. The live environment today is the recorded launch environment; no
environment change was made in this correction pass.

## Residual (recorded, not guessed)

The exact `uv` command line that removed `nvidia-cuda-nvcc-cu12` and its console output were not captured at
fix time (the fix record states the removal and the env captures show the package absent); no raw
`jax.devices()` output beyond the `env_before`/`env_after` lines is preserved. These cannot be recovered
without re-running the fix path, which is not authorised. The pre-fix broken state is evidenced by the fix
record's `TypeError: ... Path(None)` citation plus `env_before.txt`'s `pytest`/import failures.
