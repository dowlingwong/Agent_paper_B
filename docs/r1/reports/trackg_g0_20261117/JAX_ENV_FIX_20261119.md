# Ada JAX environment fix for `mlgym_breakout_minatar` (19 November 2026)

**ENGINEERING environment fix; no GPU/U2 run in this record.** The kit update report recorded Breakout as
not-run because `envs/jax312` could not import jax: `jax 0.4.35` + `nvidia-cuda-nvcc-cu12 12.9.86` raised
`TypeError: ... Path(None)` in `jax._src.lib._try_cuda_nvcc_import` (the nvcc namespace package has
`__file__ = None`).

Fix: removed only `nvidia-cuda-nvcc-cu12` from `/home/dowling/r1_trackg_20261117/envs/jax312` (no other
package/version changed); `import jax` then succeeds and `jax.devices()` returns the 8 Ada RTX 6000 devices
with `jax 0.4.35` / jax-cuda12 plugin. JAX env freeze after the fix: **65 lines, sha
`d33c96120c0be3cf20fcb2b9d783ac5366d6b0d3313e6cfe4c90583f89940217`** (recorded by `uv pip freeze` on Ada).
No torch env change; no data setup (Breakout is a simulated gymnax environment); no deletion.

This unblocks the Breakout node's isolated U2 unit (`docs/r1/proposals/u2_iso_20261119/
U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md`), subject to its independent review; it does not affect the five
completed U2 nodes or the autosearch condition-7 blocker.

## Note (19 Nov, after the Breakout smoke)
The Breakout launch added the test-only `pytest==9.2.0`, `iniconfig==2.3.1`, `pluggy==1.7.0` to `envs/jax312`
(the unit's smoke-entry dry-run needs pytest). JAX versions/devices are unchanged; the launch env freeze is now
**68 lines, sorted sha `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1`** (raw `956d0b4f…`),
while the pre-add 65-line sorted freeze remains `d33c9612…`.
