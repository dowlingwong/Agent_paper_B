# local/20261127-27 — houseprice CPU-set driver count corrected

for: compute

- Base `35c42b81880a444c55d25d604007366c7533ec82`. Branch `mac-houseprice-cpuset-count-20261127` @ `b5626bf4aa5486395714e30186263ad6cd896af5`. Tested code and regression fixture `c5fd2afaf243935404e68ba45bb3f2116ef2baf6` with its review record at the branch tip.
- The driver appended both `--attempt` and a path for every seal. It stopped after two seals because its loop counted arguments. It now counts sealed attempts and reaches the verdict with three. The six-launch bound, infrastructure retry path and STOP handling are intact.
- Independent tier-E re-check **ACCEPTED**. Review `docs/r1/reviews/HOUSEPRICE_CPUSET_DRIVER_REVIEW_20261127.md`, SHA-256 `cb95280f1212b7ff2177eb3308265f32830385f20839c1d28e1043a055f36815`. Driver SHA-256 `8739bc67a455ea6b4fc67109eb2bb9d064d2010c92961879be235a970f952608`.
- R1-G5-SIGNATURE S13/S14 bind the same three leases, CPUs 0–7, three distinct sealed attempts of one derived run, complete and deterministic, with bit-identical outcomes to the declared TASL-2 G.1b reference and each run within 9.486 s. The signing sheet SHA-256 is `dfc86b327190cb660c489162c5884bfd1af01167e454525fb730ff2141ede3b0`. Revision 13 draft SHA-256 is `3229de2b3a803740f3934957ffcd93b3e112428cd6632ab6bfdcd11f7c41aa34`.
- Preserve `tasl2-cpuset-mlgym_houseprice-20261127` with both attempts as the STOP scene. Its record SHA-256 is `95a3d8d3061739e6ba85bb6d230a9f876183ad2c8e3fef3e74f5232ce87f02e3`. Generate all three attempts in a fresh run. The reviewed identifier comes from UTC and the live and sealed roots for 27 Nov already exist. The next unused date is 28 Nov UTC at the earliest.

## Verification

- Three shell-driver regression cases passed. Bash syntax, diff whitespace and the independent fixed-date preservation, retry and refusal cases passed.
- Serial full `r1/tests` with Python 3.12.8, pytest 9.2.0, torch 2.15.0, LightGBM off the path, harness `9bb416805175149eb87b71f28d77530572aa4bce`, fresh temporary directories and `-q -p no:cacheprovider -rfE --continue-on-collection-errors`.
- Base `35c42b81` **5,013 passed, 120 failed, 3 errors, 167 skipped, 71 subtests passed**. Branch tip `b5626bf4` **5,016 passed, 120 failed, 3 errors, 167 skipped, 71 subtests passed**. Identical 123 failure/error IDs and zero new failures. [Failure/error IDs](20261127-27-28-fullsuite-failure-ids.txt) SHA-256 `bdb6d456d3898cc16ae2fcad76e8a7870e2ce20122fc0837bb3e0e8baf216ff4`.

## Compute handoff

The coordinator first merges the reviewed branch. Compute `20261127-15` then checks the existing attempt ledger and job IDs, verifies that the GPU and both CPU-set leases are available, and uses the following on TASL-2. The command creates a dedicated detached checkout from the deployment recorded in the STOP. The new run, capture and checkout roots must be absent.

```bash
(
  set -e
  T1=/home/dowling/r1_tracks/t1_tasl
  DEPLOY=/home/dowling/r1_tracks/work/paperB_base_d669
  STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  RUN=tasl2-cpuset-mlgym_houseprice-${STAMP%%T*}
  CAP="$T1/captures/g5_cpuset_check_$STAMP"
  CHECKOUT=/home/dowling/r1_tracks/work/paperB_cpuset_$STAMP
  test ! -e "$T1/runs/$RUN" && test ! -e "$T1/sealed_g1b/$RUN" && test ! -e "$CAP" && test ! -e "$CHECKOUT" || exit 2
  git -C "$DEPLOY" fetch origin refs/heads/main:refs/remotes/origin/main
  git -C "$DEPLOY" merge-base --is-ancestor b5626bf4aa5486395714e30186263ad6cd896af5 origin/main
  git -C "$DEPLOY" worktree add --detach "$CHECKOUT" origin/main
  cd "$CHECKOUT"
  test -z "$(git status --porcelain)"
  rc=0
  bash sweep2/t1_tasl/run_cpuset_check.sh "$CAP" || rc=$?
  cat "$CAP/cpuset_driver.status"
  exit "$rc"
)
```

On PASS, report the three seals, derived-spec and verdict SHA-256 values, then deliver the independently reviewed record under the single canonical `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_YYYYMMDD.json` name. On STOP, keep the new scene and report the capture and status. The coordinator publishes the accepted record. Houseprice remains gated pending that publication and the G.5 note.

Decided alone: counted argument pairs in the existing driver and used a fresh dated run for the handoff. This unit opened no sealed result and launched no host job.
