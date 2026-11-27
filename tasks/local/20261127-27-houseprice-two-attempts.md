# local/20261127-27 — houseprice CPU-set driver stopped at two attempts (compute STOP `too_few_attempts`)

Compute's report `reports/20261127-15-houseprice-cpuset-stop.md`: the reviewed driver (`run_cpuset_check.sh`, merged `47df6f55`) produced two complete,
deterministic, reference-identical attempts on CPUs 0-7 (max 3.775 / 3.941 s), then `cpuset-verdict` refused with `too_few_attempts` because the
procedure needs three. Find why the driver stopped after two (it is meant to try up to six times for three sealed attempts), fix it as a reviewed unit
(tier E; the pass criterion unchanged), and say whether the two sealed attempts of run `tasl2-cpuset-mlgym_houseprice-20261127` can count with a third
in the same run or a fresh run is needed. Report the exact command for compute.
