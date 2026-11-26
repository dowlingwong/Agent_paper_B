# experiment/20261126-03 — houseprice TASL-2 CPU-set check again (waits for local/20261126-01)

Your STOP of 26 Nov (report `G5_TASL_PREP_20261126.md` §4) is a procedure defect: the runner refuses a second attempt
after a complete one, so three sealed attempts cannot exist. The local worker is fixing the procedure. Keep the
sealed attempt 1 and its run root untouched.

Start only when a later task file names the fix's commit on main. Then run the check as that unit's report says and
commit `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_<date>.json`. This blocks only houseprice's TASL-2 jobs in G.5.
