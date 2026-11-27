Verdict: ACCEPTED

# D.3 G1 launchers — third independent tier-E review (R3)

**Fresh re-review, 27 November 2026.** I wrote R1 (`D3_G1_LAUNCHERS_REVIEW_20261127.md`, commit `da23bd5e`,
sha256 `0d427b4f1fbfb9fde8a37e43abf2cbd120a5e41d39bba6460da5693e51b07186`) and R2
(`D3_G1_LAUNCHERS_REVIEW_R2_20261127.md`, commit `ceea2f7f`, sha256
`cca1ccfa1a115f465510c82e669b0f487fae7bfb792bc6d367cf8843f0d70030`). Both are kept as history. This R3 reviews the
fix commit `3cfaa6fe88e315b5be6a0f234a8a5d2c261ecb92` on top of `38d9ff7d`, not the earlier tips. I ran synthetic,
CPU-only tests and read-only inspection; I started no job, campaign, server, audit or evaluation and read no label,
split, sweep-table or sealed file.

## 1. Inputs and hashes checked

| Input | Revision / location | sha256 |
|---|---|---|
| **R6b** = launcher design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md` | `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d` |
| **R6c** = replicate-arm design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md` | `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521` |
| **R1 review** (history) | `docs/r1/reviews/D3_G1_LAUNCHERS_REVIEW_20261127.md` @ `da23bd5e` | `0d427b4f1fbfb9fde8a37e43abf2cbd120a5e41d39bba6460da5693e51b07186` |
| **R2 review** (history) | `docs/r1/reviews/D3_G1_LAUNCHERS_REVIEW_R2_20261127.md` @ `ceea2f7f` | `cca1ccfa1a115f465510c82e669b0f487fae7bfb792bc6d367cf8843f0d70030` |
| **base** | `origin/main` `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536` | — |
| **tip** | `compute-d3-launchers-20261127` @ `3cfaa6fe88e315b5be6a0f234a8a5d2c261ecb92` | — |
| `r1/c3/d3/launch.py` | tip | `756e8793329c5ad165f2d7a26b75b37a0b36b7797e8dd138234258a8374bf702` |
| `r1/c3/d3/probe.py` | tip | `b06207be79846aa80c50f0bc51e5384b83f527b91bdadc709ae9a7c27691b2d2` |
| `r1/c3/d3/launch_htcondor.py` | tip | `5dae455fe8ef880ab47f3fcbc5d408f9db575916f08c9d5eb25c2df82bb37e3e` |
| `r1/c3/d3/launch_ssh.py` | tip | `ecd18402c7a112ada21fed825c00235fe5a779aa4df034da7e0919783a5037c6` |
| `r1/c3/d3/campaign_chunk.py` | tip | `2fc943ec355f08641239027a9b0b2360176916fac55326371ae000654505674d` |
| `r1/tests/test_d3_launchers.py` | tip | `3db7585a4087bb9623f93b98d51bbb83724f3607f71ede828a4545bae78a4177` |
| `docs/r1/reports/d3_g1_20261127/D3_G1_LAUNCHERS_UNIT_20261127.md` | tip | `9672a4a7afc923ad1a16b6b242d1dc91054a93c2993f66ca7627bf24ef05d40e` |

`git diff --stat 38d9ff7d..3cfaa6fe` touches only `probe.py`, `test_d3_launchers.py`, the unit report and the R2
review file (the latter two are history/documentation). The launcher, chunk, request, end-sampler and snapshot code
is unchanged from the R2 tip.

## 2. Commands and counts

Focused suite, tip `3cfaa6fe`, cwd the review worktree:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py
```

Result: **47 passed in 8.92s** (17 launcher tests, 10 chunk tests, 20 snapshot tests). The unit report's 47 matches.

I also ran the full `r1/tests` suite at the new tip, so (d) is checked directly rather than inferred:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider r1/tests
```

Result: **114 failed, 5003 passed, 163 skipped, 4 warnings, 3 errors, 71 subtests passed in 682.57s
(0:11:22)**. The 117 unique failure/error ids are identical to the unchanged base `2d88fe1b` list
(`comm -13 base_ids.txt tip_r3_ids.txt` is empty). **New failures: none.** The three extra passes over the R2 tip
(5000 → 5003) are the three new launcher tests.

Manual probes used in the findings:

```
# (a) actual hostname, SSH mismatch refused
monkeypatched socket.gethostname -> TASL-2.actual
probe_from_records({launcher: ssh, host: TASL-2}, lease gpu3.lock)
  -> host TASL-2.actual; nvidia-smi argv ['-i','3']; gpu_uuid GPU-card3
check_hardware(launch host TASL-2, record) -> STOP launcher/host mismatch
check_hardware(launch host TASL-2.actual, record) -> pass

# (b) lease-derived index and HTCondor index 0
gpu_index_from_lease(gpu3.lock) = 3; gpu0.lock = 0; None = 0; GPU-abc.lock = 0
{launcher: htcondor} -> nvidia-smi ['-i','0']; lease true; lease_path null; lease_kind htcondor

# (c) required memory, no launch-record default
probe_from_records(launch without hardware) -> LaunchStop: the launch record must declare
  hardware.required_memory_mib
probe_from_records(hardware.required_memory_mib=20000) -> memory_check pass
```

## 3. Closure of R2

| R2 finding | Status | Evidence |
|---|---|---|
| **R2-B1** SSH/direct host check vacuous | **CLOSED** | `probe_from_records` passes `host=None` for every launcher (`probe.py:118–119`); `probe` uses `socket.gethostname()` (`probe.py:71`). I ran the actual-host record and the mismatch check: `check_hardware` refuses `TASL-2` when the probe ran on `TASL-2.actual`, and passes when the launch host is the actual name. HTCondor still records the actual worker and is not compared. |
| **R2-M1** probe always samples GPU 0 | **CLOSED** | `gpu_index_from_lease` reads `gpu<index>.lock` (`probe.py:53–60`); `probe_from_records` uses the lease index unless an explicit `gpu_index` is given (`probe.py:117`); the SSH script passes `--lease-path "$lease"` (`launch_ssh.py:63–65`); HTCondor has no lease and gets index 0. I ran a `gpu3.lock` probe and saw `nvidia-smi -i 3`; HTCondor saw `-i 0`. |
| **R2-M2** default 46,000 MiB | **CLOSED for the launcher path** | `probe_from_records` raises `LaunchStop` when `hardware.required_memory_mib` is absent (`probe.py:106–108`), with no 46,000 fallback; the launcher record test now carries `required_memory_mib: 20000`. I ran the missing-hardware case: it refuses. See MINOR 1 for the low-level `probe()` default that remains. |

## 4. Explicit checks (a)–(d)

- **(a) The probe records the actual hostname for SSH/direct, so a launch-host mismatch is refused — PASS.**
  `probe_from_records` sets `host=None` for all launchers; `probe` uses `socket.gethostname()`. The chunk's
  `check_hardware` compares `observed["host"]` with `spec.host` for non-HTCondor and skips HTCondor. I verified
  the refusal and the matching-host pass manually. Caveat: the test records the actual hostname but does not
  itself call `check_hardware`; MINOR 4.
- **(b) The probe's GPU index comes from the `gpu<index>.lock` lease (index 0 for HTCondor) — PASS.**
  `gpu_index_from_lease` is exact-suffix `gpu(\d+)\.lock`; the SSH script passes the lease path; HTCondor's
  `lease_path` is null and the index is 0. The new test asserts `-i 3`; I verified the mapping and the
  HTCondor `-i 0` case. A per-UUID lease falls back to 0 (MINOR 2).
- **(c) `hardware.required_memory_mib` is required, with no 46,000 default — PASS for the launch/probe entry.**
  `probe_from_records` refuses a missing value and uses `int(hardware["required_memory_mib"])`; the CLI goes
  through it. The 46,000 default remains only in the low-level `probe()` signature (MINOR 1).
- **(d) No new regressions — PASS.** Focused 47 passed; full suite 114 failed / 5003 passed / 163 skipped / 3
  errors with the same 117 ids as base; zero new ids.

## 5. Remaining findings

### BLOCKING

None.

### MAJOR

None.

### MINOR

1. **The low-level `probe()` still has a 46,000 default.** `probe(*, gpu_index: int = 0,
   required_memory_mib: int = 46000, ...)` (`probe.py:63`) keeps the old magic value; `probe_from_records` and
   the CLI require it, so the launcher path is fail-closed, but a direct `probe()` caller can still silently get
   46,000 MiB. Make the parameter required (or raise when it is omitted) so the report's "no magic default" is
   literally true.
2. **A per-UUID lease falls back to index 0.** `gpu_index_from_lease("GPU-abc.lock") == 0`
   (`probe.py:53–60`). Design §3 permits "gpu<index>.lock or a per-UUID lease"; only the indexed form is
   supported. Either select the card by UUID from the lease or document that this unit supports only the indexed
   form (and the launch record must use it).
3. **The SSH launch host must equal `socket.gethostname()` exactly.** The check is an exact string compare
   (`campaign_chunk.py:141–143`), so an SSH alias or a short-name/FQDN difference (`TASL-2` versus
   `TASL-2.etp.kit.edu`) refuses a correct host. Record the matched actual hostname in the launch record or add
   an explicit alias field; document the requirement.
4. **Test coverage of the exact refusal path is thin.** `test_probe_from_records_uses_the_actual_host_and_lease_card`
   asserts the record's host and `-i 3` but does not call `check_hardware`; the rendered SSH probe
   path (`render_remote_script(probe=True)`) and the HTCondor `lease true / null / htcondor` values have no
   direct test. I verified them manually; adding the assertion would prevent a regression of R2-B1/R2-M1.
5. **The unit report's test line is stale.** The table says 17 tests and the code block says 47 passed, but the
   next line still says "Focused new tests: **14 passed**; chunk + snapshot focus: 44 passed", and the full-suite
   sentence still cites the R2 tip's 4,996 passes. The R3 run is 17 new tests, 47 focused and 5,003 full-suite
   passes; update the numbers.
6. **The first review's earlier MINORs remain** where this fix did not touch them: `check_pin` has no mismatch
   test; the chunk entry does not re-verify the launch's manifest pin; the HTCondor `requirements` model and the
   `image` remain caller-overridable; `submit()`/`launch()` silently overwrite contradictory
   launcher/request/scope fields; the SSH `mkdir -p {remote_dir}` is unquoted and the SSH path stages no code;
   `campaign_chunk.main`/`probe.main` do not catch `LaunchStop`; the dry-run records are incomplete; the
   per-instance `instance_model` is still defaulted to `campaign_model`; the chunk test still uses the int `0`
   for `other_processes_start`.

## 6. Limits

I did not start an HTCondor job, an SSH chunk, a campaign, a server or an audit, and I read no label, split,
evaluation or sealed value. The launchers were exercised through rendering, `probe_from_records` /
`parse_other_processes`, `check_hardware` and synthetic unit tests only. The full-suite base list is the unchanged
`2d88fe1b` run; the new tip was run in full and has zero new failure ids. The 117 pre-existing failures are
compared by id only and are outside this unit.

I changed nothing except adding this R3 review file; R1 and R2 are kept in history at `da23bd5e` and `ceea2f7f`.
