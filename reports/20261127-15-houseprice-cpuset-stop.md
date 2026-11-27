# STOP — houseprice TASL-2 CPU-set check (`compute/20261127-15`)

**Result: STOP (`too_few_attempts`).** The reviewed driver ran after Forest Cover released CPUs 4-7, produced **two**
complete, deterministic, reference-identical attempts on CPUs 0-7, and then its verdict step refused because the
procedure requires **three** attempts. No run was truncated and no assertion was relaxed; the scene is kept.

- Task: `compute/20261127-15` (with `compute/20261127-01`, `experiment/20261126-03`).
- Checkout: `/home/dowling/r1_tracks/work/paperB_base_d669` (detached `d669b0bf`, ancestor of `origin/main` `280c0015`).
- Capture: `/home/dowling/r1_tracks/t1_tasl/captures/cpuset_houseprice_20261127_b/`.
- Run id: `tasl2-cpuset-mlgym_houseprice-20261127`; sealed attempts 1 and 2 under
  `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/tasl2-cpuset-mlgym_houseprice-20261127/mlgym_houseprice/attempt-{1,2}`.
- Check record: `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261127.json` sha256
  `95a3d8d3061739e6ba85bb6d230a9f876183ad2c8e3fef3e74f5232ce87f02e3`; `run.log` sha256
  `30910797192edfc1cf94b56a7cf62d07b3a81cedfa1149186072730a2d08aec6`.
- Both attempts: `complete: true`, `deterministic: true`, `identical_to_reference: true`, `affinity_ok: true`,
  `within_budget: true`; attempts 1/2 `c0_median_wall_s` 3.065 / 2.954, `max_wall_s` 3.775 / 3.941.

A pre-check capture `..._20261127/` is preserved: the driver refused before any run because the checkout had no
`origin/main` ref (`HEAD d669b0bf is not on published origin/main`). After adding the fetched `origin/main` ref to the
shared checkout, the reviewed driver ran unchanged in the new `..._b` capture.

**Decided alone:** to use a new capture directory after the pre-check refusal; not to edit the reviewed driver or the
attempt count. **Needs:** a reviewed unit or task that produces the third attempt (or a signed change to the
procedure), then the single PASS record; `experiment/20261126-03` stays blocked.
