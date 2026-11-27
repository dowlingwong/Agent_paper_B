# Independent tier-E review — local/20261127-27

**ACCEPTED** `c5fd2afaf243935404e68ba45bb3f2116ef2baf6` against `35c42b81880a444c55d25d604007366c7533ec82`. No findings remain. The final test stub now exits 0 after emitting either valid verdict, matching the production CLI. The driver checks the verdict itself and exits 1 on STOP.

Each successful seal appends two arguments, `--attempt` and its path. The old loop stopped after two seals because the array length had reached four. The fix counts argument pairs and submits exactly three sealed attempts on success, within six launches. S13 and S14 still require the signed leases, three distinct complete and deterministic attempts on TASL-2 CPUs 0–7, bit-identical outcomes to the declared sealed G.1b attempt, and every run within 9.486 s.

Preserve the `20261127` STOP and its two attempts in place. The reviewed driver derives the literal `tasl2-cpuset-mlgym_houseprice-YYYYMMDD` ID from the current UTC date and refuses either an existing live root or an existing sealed root. A fresh run must use the next unused UTC date, earliest **2026-11-28**, once the fix is on published `main` and the leases are available. Generate all three attempts in that run.

`git diff --check` and `bash -n sweep2/t1_tasl/run_cpuset_check.sh` passed. `PYTHONDONTWRITEBYTECODE=1 /Users/wongdowling/anaconda3/bin/python -m pytest -q -p no:cacheprovider r1/tests/test_t1_cpuset_driver.py` passed all three cases at the final candidate. An independent temporary fixture reproduced the old two-seal STOP and checked clean and interleaved-retry completion, six-launch exhaustion, immediate exit on node or timing STOP, missing attempt or failed seal, and refusal with either or both dated roots present. The fixture confirmed both root guards preserve the existing scene.

The input hashes matched `R1-G5-SIGNATURE`.

- Signing sheet at `6ddd7b77` — `dfc86b327190cb660c489162c5884bfd1af01167e454525fb730ff2141ede3b0`
- Revision 13 draft at `ef06a65c` — `3229de2b3a803740f3934957ffcd93b3e112428cd6632ab6bfdcd11f7c41aa34`
