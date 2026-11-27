Verdict: CHANGES REQUIRED

# D.3 G1 launchers — second independent tier-E review (R2)

**Fresh re-review, 27 November 2026.** I wrote the first review of this unit
(`D3_G1_LAUNCHERS_REVIEW_20261127.md`, commit `da23bd5e`, sha256
`0d427b4f1fbfb9fde8a37e43abf2cbd120a5e41d39bba6460da5693e51b07186`) and have kept it as history. This R2
reviews the fix commit `38d9ff7dff7c5b37c85fd9d729987ac2ca41bc47` on top of `067f7312`, not the earlier tips. I
ran only synthetic, CPU-only tests and read-only inspection; I started no job, campaign, server, audit or
evaluation and read no label, split, sweep-table or sealed file.

## 1. Inputs and hashes checked

| Input | Revision / location | sha256 |
|---|---|---|
| **R6b** = launcher design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md` | `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d` |
| **R6c** = replicate-arm design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md` | `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521` |
| **First review** (history) | `docs/r1/reviews/D3_G1_LAUNCHERS_REVIEW_20261127.md` @ `da23bd5e` | `0d427b4f1fbfb9fde8a37e43abf2cbd120a5e41d39bba6460da5693e51b07186` |
| **base** | `origin/main` `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536` (unchanged; base list reused) | — |
| **tip** | `compute-d3-launchers-20261127` @ `38d9ff7dff7c5b37c85fd9d729987ac2ca41bc47` | — |
| `r1/c3/d3/launch.py` | tip | `756e8793329c5ad165f2d7a26b75b37a0b36b7797e8dd138234258a8374bf702` |
| `r1/c3/d3/probe.py` | tip | `79622c2e0d43545c6afc163fc2c3540c877266c7aace447063fd9f0ba2ac886f` |
| `r1/c3/d3/launch_htcondor.py` | tip | `5dae455fe8ef880ab47f3fcbc5d408f9db575916f08c9d5eb25c2df82bb37e3e` |
| `r1/c3/d3/launch_ssh.py` | tip | `ecd18402c7a112ada21fed825c00235fe5a779aa4df034da7e0919783a5037c6` |
| `r1/c3/d3/campaign_chunk.py` | tip | `2fc943ec355f08641239027a9b0b2360176916fac55326371ae000654505674d` |
| `r1/tests/test_d3_launchers.py` | tip | `6deaa8c93bfabff986e36c557c835017a1013e43073a08bd21083fa872c337fb` |
| `docs/r1/reports/d3_g1_20261127/D3_G1_LAUNCHERS_UNIT_20261127.md` | tip | `564c17849008bfdd9c592c03b83310bf027e959014caaa0b964e980ffe08e57c` |

All code hashes match the refreshed unit report. `git diff --stat 067f7312..38d9ff7d` shows the fix commit adds
`probe.py` and changes only the launcher/chunk files, the launcher tests, the unit report and my first review.

## 2. Commands and counts

Focused suite, tip `38d9ff7d`, cwd the review worktree:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py
```

Result: **44 passed in 2.27s** (14 launcher tests, 10 chunk tests, 20 snapshot tests). The report's 44 matches.

Full `r1/tests` suite, tip `38d9ff7d`, cwd the review worktree:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider r1/tests
```

Result: **114 failed, 5000 passed, 163 skipped, 4 warnings, 3 errors, 71 subtests passed in 704.02s
(0:11:44)**.

Base list reused from the R1 review's base run at the unchanged `2d88fe1b`: **114 failed, 4985 passed,
163 skipped, 3 errors, 71 subtests**, 117 unique failure/error ids (`d3_base_full.log`). The R2 tip has 117
unique ids; `comm -13 base_ids.txt tip_r2_ids.txt` is **empty**. **New failures: none.** The 15 extra passes
are the 11 tests from the first unit plus the 4 new ones (44 − 40 = 4, 5000 − 4985 = 15).

Read-only probes used below:

```
# SSH/direct host: the probe echoes the launch host, not socket.gethostname()
actual hostname: Wongs-Mac-mini.local
launch {launcher: ssh, host: TASL-2} -> probe_from_records host = TASL-2
launch {launcher: htcondor, host: TASL-2} -> probe_from_records host = Wongs-Mac-mini.local
# check_hardware then passes for the SSH record because observed host == launch host

# default required GPU memory vs the reviewed L40S
nvidia-smi (fake): NVIDIA L40S, GPU-abc, 570.211.01, 45468, 45468
probe_from_records(no launch hardware) -> required_memory_mib=46000, memory_check=fail
probe_from_records(hardware.required_memory_mib=20000) -> required_memory_mib=20000, memory_check=pass

# rendered launcher scripts
SSH probe=True: python3 -m r1.c3.d3.probe --launch launch.json --manifest manifest.json \
                  --out observed.json --lease-path "$lease"
HTCondor wrapper probe=True: same probe line before exec of the chunk
chunk_argv (unchanged): ['python3','-m','r1.c3.d3.campaign_chunk','--launch','launch.json',
                         '--out','out','--manifest','manifest.json','--observed','observed.json']
```

## 3. Closure of the first review

| First-review finding | Status | Evidence |
|---|---|---|
| **B1** end sample never enabled | **CLOSED** | `main` now sets `gpu_uuid = args.gpu_uuid or observed.get("gpu_uuid")` and installs `end_sampler` unless `--no-end-sample`; `chunk_argv` is unchanged, so both launchers' shared argv now produce the end record. |
| **B2** real `nvidia-smi` units | **CLOSED** | Both compute-apps queries use `--format=csv,noheader,nounits`; `parse_other_processes` strips `MiB` and counts `N/A` in `unknown_memory_count`; the new test covers it. I re-ran the parser on `MiB`/`N/A`. |
| **M1** observed record declared, not sampled | **CLOSED (core)** | `probe.py` samples model/UUID/driver/total/free and other processes at chunk start; HTCondor's wrapper and the SSH script run it before the chunk. Remaining card-selection issues are R2-M1/R2-M2. |
| **M2** host mismatch | **NOT CLOSED in substance** | The host check exists in `check_hardware` and skips HTCondor, but the SSH/direct probe feeds it the declared launch host (R2-B1), so no mismatch can be observed. |
| **M3** HTCondor lease | **CLOSED** | `probe_from_records` records `lease: true`, `lease_path: null`, `lease_kind: "htcondor"` for HTCondor and `lease_kind: "lease"` for SSH; the docstring and report document it. I verified the record values. |

## 4. Findings

### BLOCKING

**R2-B1. The SSH/direct host check is vacuous: the probe records the launch's declared host, not the host it
runs on.**
`probe_from_records` sets `host = str(launch.get("host") or "")` for every non-HTCondor launcher
(`probe.py:99`); `probe` only falls back to `socket.gethostname()` when `host` is empty (`probe.py:61`).
The observed host therefore always equals the launch host, and `check_hardware`'s comparison
(`campaign_chunk.py:141–143`) can never see a mismatch. I ran `probe_from_records` with launch host `TASL-2` on
this Mac (hostname `Wongs-Mac-mini.local`): the record said `TASL-2` and `check_hardware` passed. The HTCondor
path (`host=None`) correctly records the actual worker. The new `test_check_hardware_refuses_a_host_mismatch`
constructs the observed record by hand, so it does not catch this. Fix: for SSH/direct, let the probe use
`socket.gethostname()` (or query the host over the SSH connection) and compare that with the launch host; if the
launch host is an alias, record the actual and requested names separately. This is the first review's M2: the
check is present but its input is the declaration, not an observation.

### MAJOR

**R2-M1. The probe always samples GPU 0; the SSH launcher never passes the leased card's index/UUID.**
`probe` runs `nvidia-smi -i {gpu_index}` (`probe.py:53`, `:62`) and `probe_from_records` defaults
`gpu_index=0` (`probe.py:85`). The SSH remote script runs the probe without `--gpu-index`
(`launch_ssh.py:63–65`), and the launch
record's `hardware` is not consulted for an index; the lease path is only recorded. On a multi-GPU host whose
lease is `gpu3.lock`, the observed model/UUID/memory is GPU 0, not the leased card. Design §3 requires the
lease to be per card actually used and never a fixed `gpu0.lock` on a multi-GPU host; the probe's fixed GPU 0
is the same class of error. Fix: pass `--gpu-index` from the lease/launch record (or select the card by the
lease UUID) and test a two-card case. HTCondor with one visible GPU is likely index 0; the SSH/direct path is
the gap.

**R2-M2. The probe's default `required_memory_mib=46000` exceeds the reviewed L40S card and is undocumented.**
`probe_from_records` uses `int(hardware.get("required_memory_mib") or 46000)` (`probe.py:96`), and the launch
record's `hardware` is not produced by this unit. The reviewed preflight card is `NVIDIA L40S` with
`GPUs_GlobalMemoryMb = 45468` (`D3_HTCONDOR_PREFLIGHT_20261127.md:36–38`); an empty-card free value cannot
reach 46000. I ran the probe with total/free 45468 and no launch hardware: `memory_check = fail`, so the chunk
would refuse; with `hardware.required_memory_mib = 20000`: `pass`. The A100-40GB target is worse. The unit
report and its "Decided alone" do not name 46000. Fix: require the launch record to declare the required GPU
memory (fail closed if absent) or use a reviewed value, and test the L40S/A100 memory sizes. A hidden default
currently decides placement.

### MINOR

1. **The proposer identity is a default, not read from the campaign manifest.** `probe_from_records` does
   `manifest.get("proposer_model")` (`probe.py:97`), but the D.3 campaign manifest (adapter schema
   `r1_d3_campaign_manifest/v1`) carries `proposer: {model: ...}`; the code falls back to
   `hardware.proposer_model` or the literal `"gemma4_31b"`. That value is correct today because the adapter
   refuses any other proposer, but the report's "proposer identity" is not sourced from the manifest. Read the
   nested field or `adapter.load_manifest`.
2. **The SSH probe path and the lease semantics are untested.** No test runs `render_remote_script(probe=True)`
   or `probe_from_records` for `launcher="ssh"`/`"htcondor"` and asserts `lease`, `lease_path` and `lease_kind`;
   the host test uses a hand-built observed record. The HTCondor test checks the wrapper text, not the produced
   record. Add an end-to-end synthetic probe test for both launchers.
3. **The first review's MINORs still stand** where the fix did not touch them: `check_pin` has no mismatch test;
   the chunk entry does not re-verify the launch record's manifest/observed pins; the HTCondor `requirements`
   model and `image` remain caller-overridable; `submit()`/`launch()` silently overwrite a contradictory
   `launcher`/`request`/`scope`; the SSH `mkdir -p {remote_dir}` is unquoted and the SSH path stages no code;
   `campaign_chunk.main`/`probe.main` do not catch `LaunchStop`; the dry-run records are incomplete; the
   per-instance `instance_model` is still defaulted to `campaign_model`; the new chunk test still uses the int
   `0` for `other_processes_start`.
4. **`lease_kind` is only inside `chunk.json["hardware"]`, not a top-level field.** The design's named fields do
   not require a top-level `lease_kind`, and the report documents the observed record; note the nesting so a
   reader does not look for it beside `lease_path`.
5. **The probe's extra `unknown_memory_count` is fine but should be documented** as part of the count/memory
   record; it is a count, not an identity, and does not violate R1-CARD-SHARE.

## 5. Explicit checks (a)–(e)

- **(a) Chunk entry enables the end sample without changing the shared argv — PASS.** `main` reads
  `gpu_uuid = args.gpu_uuid or observed.get("gpu_uuid")` and installs `end_sampler` unless `--no-end-sample`;
  `chunk_argv` is byte-for-byte unchanged; both launchers pass it. The probe's observed record always carries
  `gpu_uuid`.
- **(b) Real `nvidia-smi` output with `MiB`/`N/A` is parsed — PASS.** Both queries use `nounits`;
  `parse_other_processes` strips `MiB`, treats `N/A`/`[N/A]`/`Not Supported` as an unknown-memory process, and
  the new test covers `512 MiB`, `N/A` and a second card.
- **(c) The job-side probe produces `observed.json` in both launchers — PASS with caveats.** The HTCondor
  wrapper runs `python3 -m r1.c3.d3.probe ... --out observed.json` before `exec`ing the chunk and omits
  `observed.json` from `transfer_input_files`; the SSH script runs the same probe after the `flock` and before
  the chunk. The SSH path has no test, and the probe samples GPU 0 (R2-M1).
- **(d) The host check applies to SSH/direct and not to HTCondor's chosen worker — FAIL in substance.**
  `check_hardware` does skip the comparison for `launcher == "htcondor"` and applies it otherwise, and the
  HTCondor probe records the actual hostname. But the SSH/direct probe records the declared launch host, so the
  comparison cannot detect a mismatch (R2-B1).
- **(e) HTCondor assignment semantics are truthful and documented — PASS.** `probe_from_records` writes
  `lease: true`, `lease_path: null`, `lease_kind: "htcondor"` for HTCondor and `lease_kind: "lease"` with the
  actual lease path for SSH; the docstring and unit report state the convention; `check_hardware` accepts the
  HTCondor record. I verified the values with a synthetic probe. Caveat: no test asserts them, and
  `lease_kind` is nested in `chunk.json["hardware"]`.

## 6. Limits

I did not start an HTCondor job, an SSH chunk, a campaign, a server or an audit, and I read no label, split,
evaluation or sealed value. The launchers were exercised through rendering, the `probe_from_records` /
`parse_other_processes` functions and synthetic unit tests only. The full-suite base list is the R1 review's
`2d88fe1b` run; the base is unchanged and was not re-run. The 117 pre-existing failures are compared by id only.

I changed nothing except adding this R2 review file; the first review is kept at `da23bd5e`.
