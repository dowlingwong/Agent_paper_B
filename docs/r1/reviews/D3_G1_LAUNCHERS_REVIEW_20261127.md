Verdict: CHANGES REQUIRED

# D.3 G1 launchers — independent tier-E code review

**Fresh reviewer, 27 November 2026.** I did not write this unit, the G1 chunk, the adapter, the D.3 design, or any
earlier D.3 review. I reviewed the updated task tip `067f7312` (code `cfba4c25` plus the docs hash refresh), not the
superseded `a25e9bb2`. I ran only synthetic, CPU-only tests and read-only inspection; I started no job, campaign,
server, audit or evaluation, and read no label, split, sweep-table or sealed file.

## 1. Inputs and hashes checked

| Input | Revision / location | sha256 |
|---|---|---|
| **R6b** = launcher design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md` | `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d` |
| **R6c** = replicate-arm design | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md` | `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521` |
| **T-COMPUTE** = `compute/20261126-02` | `origin/coord/coordinator` `042c1930`, `tasks/compute/20261126-02-d3-launcher.md` | `6a27ea1a7b97ef6d8492ba2f2b625408036e320aada1d2fe298793547f6ccaba` |
| **T-CLUSTER** = `cluster/20261126-02` | `origin/coord/coordinator` `042c1930`, `tasks/cluster/20261126-02-d3-g1-g6-code.md` | `303fbe69f29c3d1269ead04bb437610244762fb7cd834086c545e8d5d6aa173b` |
| **base** | `origin/main` `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536` | — |
| **tip** | `compute-d3-launchers-20261127` @ `067f73123015b911cb90000e83c1e8650a5b3211` | — |
| `r1/c3/d3/launch.py` | tip | `c854de4849f579cc56877e180f46dc462e068b96267fbc6ebd126eb205055ff5` |
| `r1/c3/d3/launch_htcondor.py` | tip | `413f6c6a21a539afdcfb00bf25743179e1fa72763cb07ac823dfb8a498bc46fe` |
| `r1/c3/d3/launch_ssh.py` | tip | `a2e966d1262d218201d856aa1fc192e525e09dd5a0bea6d080003132d3f783f8` |
| `r1/c3/d3/campaign_chunk.py` | tip | `98c6c4788012aec2ced0e5269056df7183195ac1c6e65432b8b64be91e7e715a` |
| `r1/tests/test_d3_launchers.py` | tip | `38cbcb9798a4afc14bf7f8a647d03e2b7ac8c7956363e362f59d006fc00597b3` |
| `docs/r1/reports/d3_g1_20261127/D3_G1_LAUNCHERS_UNIT_20261127.md` | tip | `acb2a5ecdac9f8752b03f68024798296c50afb030a048d43476f80f3d1ec1cd3` |

The five code hashes match the unit report's table at the refreshed tip. `git diff --stat 2d88fe1b..067f7312` touches
only the seven paths named in the task (the three launcher files, `campaign_chunk.py`, the two test files, and the unit
report); `snapshots.py`, `audit.py` and `replicate_campaign.py` are untouched.

## 2. Commands and counts

Focused suite, tip `067f7312`, cwd the review worktree:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py
```

Result: **40 passed in 1.92s**. The new unit contributes 10 launcher tests and 1 chunk `end_sampler` test; the
remaining 29 are the existing chunk/snapshot tests.

Full `r1/tests` suite, base `2d88fe1b`, cwd `/Users/wongdowling/Documents/agent_paper_B-workers/compute-launchers-base-review`:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider r1/tests
```

Result: **114 failed, 4985 passed, 163 skipped, 4 warnings, 3 errors, 71 subtests passed in 749.54s (0:12:29)**.

Full `r1/tests` suite, tip `067f7312`, cwd the review worktree:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider r1/tests
```

Result: **114 failed, 4996 passed, 163 skipped, 4 warnings, 3 errors, 71 subtests passed in 739.40s (0:12:19)**.

Failure-id comparison (logs in `/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/`):

```
grep -E '^(FAILED|ERROR) r1/tests/' d3_base_full.log | sed -E 's/ - .*$//' | sort -u > base_ids.txt
grep -E '^(FAILED|ERROR) r1/tests/' d3_tip_full2.log | sed -E 's/ - .*$//' | sort -u > tip_ids.txt
wc -l base_ids.txt tip_ids.txt
comm -13 base_ids.txt tip_ids.txt
```

Base and tip both have **117** unique failure/error ids; `comm -13` is **empty**. **New failures: none.** The 11 extra
passes on the tip are the new unit's tests. The 117 pre-existing ids are identical on base and tip and are outside this
unit.

Read-only probes used in the findings:

```
# 1) end-sampler parser against realistic nvidia-smi output
parse_other_processes("GPU-abc, 1234, 512\n")       -> {'count': 1, 'used_memory_mib': 512}
parse_other_processes("GPU-abc, 1234, 512 MiB\n")   -> LaunchStop: cannot read a compute-process memory value ...
parse_other_processes("GPU-abc, 1234, N/A\n")       -> LaunchStop: cannot read a compute-process memory value ...

# 2) rendered HTCondor submit + the one chunk argv
H.render_submit(record, submit_dir=tmp) ->
  arguments = -m r1.c3.d3.campaign_chunk --launch launch.json --out out --manifest manifest.json --observed observed.json
L.chunk_argv("launch.json", "out", manifest_path="manifest.json",
             observed_path="observed.json", python="python3") ->
  ['python3', '-m', 'r1.c3.d3.campaign_chunk', '--launch', 'launch.json', '--out', 'out',
   '--manifest', 'manifest.json', '--observed', 'observed.json']
# neither contains --gpu-uuid

# 3) the new check_pin refuses a wrong pin on both launchers
S.launch(... wrong manifest pin, dry_run=True) -> LaunchStop: manifest sha256 mismatch: ...
H.submit(... wrong manifest pin, dry_run=True) -> LaunchStop: manifest sha256 mismatch: ...
```

## 3. Findings

### BLOCKING

**B1. Neither launcher enables the end sample; `other_processes_end` is null on every real chunk.**
`campaign_chunk.main` installs `end_sampler` only when `--gpu-uuid` is passed
(`campaign_chunk.py:503–504`). `chunk_argv` has no `--gpu-uuid` (`launch.py:124–130`), and both
`launch_htcondor.submit` and `launch_ssh.launch` pass that argv unchanged. The rendered HTCondor arguments and the
SSH command therefore omit it (probe 2 above). `run_chunk` leaves `observed["other_processes_end"]` at its input
value, normally `null`, and `chunk.json` writes that null (`campaign_chunk.py:308`, `:420`). This contradicts design
revision 6b §2 (the SSH launcher "records the other compute processes at start and end") and §3 (the field is required
per chunk), and it makes the unit report's claim that `chunk.json` "still carries the end record it promises" false.
The only covered test (`test_end_sampler_fills_the_chunk_after_the_campaign`) calls `run_chunk` directly, so it does
not test the launcher path at all. Fix: pass `--gpu-uuid` from both launchers (from the observed record or an explicit
argument), or enable the sampler in `main` whenever `observed["gpu_uuid"]` is present.

**B2. The end sampler cannot parse real `nvidia-smi` output; it would abort the chunk after the campaigns.**
`_sample_compute_apps` calls `nvidia-smi --query-compute-apps=... --format=csv,noheader` without `nounits`
(`campaign_chunk.py:456–458`), and `parse_other_processes` does `int(float(parts[-1]))` (`launch.py:156`). Real
compute-apps `used_memory` values are `512 MiB` (or `N/A`); probe 1 shows both raise `LaunchStop`. Every existing
parser in this repository requests `--format=csv,noheader,nounits` for this exact query
(`r1/scripts/htcondor/trackp_p4/p4_direct.py:274`, `p4_lib.py:638`, `r1/scripts/paper_a_status.py:140–141`,
`r1/scripts/llama_server_instance.py:165`). Because the sample runs after all 18 campaigns and before `chunk.json`
and `summary.json` are written, a failure discards the chunk record for a completed chunk (the per-campaign
directories remain, but there is no `chunk.json`, `summary.json` or top-level `SHA256SUMS`). The new test uses the
unitless string `"GPU-abc, 1234, 512"`, so it passes while the real path fails. Fix: add `nounits`, tolerate or skip
`N/A`, and test with a realistic CSV row.

### MAJOR

**M1. `observed.json` is a declared input, not an observation; this unit has no producer for it.**
`observed_record()` (`launch.py:194–224`) takes host, model, UUID, driver and memory from the caller and is never
called outside the tests; `check_pin` only hashes the JSON. Neither launcher runs `nvidia-smi`; `launch_htcondor`
copies a submit-side `observed.json` into the job, and `launch_ssh` reads it on the submit side and heredocs it to the
host. For HTCondor the assigned slot is not known until the job starts, so `check_hardware` compares the manifest with
a declaration, not with the card the chunk actually uses. The unit report says it "does not create ... a real observed
record" (report §"What this unit does not do"), and no other unit in this branch produces one. The task requires the
runner to record host, GPU model and driver per chunk and refuse a chunk that would break the model rule; a
submit-side declaration does not detect the execution card. Fix: add a job-side/host-side sample (or name and pin the
separate preflight unit that produces `r1_d3_observed/v1`) and make the refusal consume that sample.

**M2. A host/launcher mismatch is not refused; `chunk.json.host` is the launch declaration.**
Design §3 lists "a launcher/host/lease mismatch" among the pre-execution refusals. `check_hardware` checks only the
GPU model, proposer model, `memory_check` and `lease` (`campaign_chunk.py:127–155`). It never compares
`spec.host`/`spec.launcher` with `observed["host"]`, and `chunk.json` writes `spec.host` (the launch record) while
`hardware.host` carries the observed value (`campaign_chunk.py:293`, `:297`). `check_observed` checks only
`lease_path` (`launch_ssh.py:66–72`). A chunk can therefore run on host A and record host B without a refusal. Fix:
compare host/launcher (and, for SSH, the lease path) as the design requires, or make `host` a purely observed field.

**M3. The HTCondor path cannot truthfully satisfy the unconditional `lease is True` check.**
`check_hardware` requires `observed["lease"] is True` for every chunk (`campaign_chunk.py:154–155`). The HTCondor
launcher sets `lease_path = None` (`launch_htcondor.py:117–118`) and its wrapper takes no lease; only the SSH script
takes a `flock`. An honest HTCondor observed record (no card lease) is refused, while a runnable one must assert a
lease that was never taken. The design's lease convention is the direct/SSH card lease, not a scheduler claim. Fix:
make the check launcher-aware (skip the lease for HTCondor) or record a distinct field such as
`lease_kind: scheduler|flock` with the corresponding value.

### MINOR

1. **The new `check_pin`/remote-output delta is untested.** No test covers a pin mismatch or the new remote
   `[ -e out ]` refusal; the report still says 10 tests and its table does not mention either. I verified by hand that
   both launchers refuse a wrong manifest pin (probe 3). `check_pin` raises `FileNotFoundError`/`IsADirectoryError`
   for a missing/non-file pin instead of `LaunchStop`, and the check-then-copy/heredoc is a TOCTOU window.
2. **The chunk entry does not re-verify the launch record's pins.** `main` reads `--manifest`/`--observed` and never
   compares their bytes with `launch["manifest"]["sha256"]`/`launch["observed"]["sha256"]`; `check_pin` is
   submit-side only. A manual `python -m r1.c3.d3.campaign_chunk` invocation, or a corrupted transfer, bypasses the
   pin that the launcher checked.
3. **The HTCondor placement line is self-declared.** `requirements` uses `campaign_model_source.model` from the
   caller's launch record (`launch_htcondor.py:67,76–77`), contrary to design §3's "`launch.json` may not
   self-declare a different model"; the chunk later refuses a mismatch, but the placement line is not sourced from
   the manifest. The `image` parameter can also override `D3_IMAGE` without a digest check, and `check_request`
   validates `universe` while `render_submit` hardcodes `universe = container`, so a changed constant would diverge.
4. **Silent correction instead of refusal.** `submit()` overwrites `launch["launcher"]`, `request` and `scope`, and
   `launch()` overwrites `launcher`/`request`, so a contradictory launch record is corrected, not refused; the
   `render_submit`/`render_remote_script` launcher check is bypassed by that overwrite.
5. **Quoting and path traps.** `shell_join` is correct for the bash/SSH script but is also used for HTCondor's
   `arguments`, which is not shell-parsed (single quotes are literal); it is safe only because the fixed relative
   names contain no special characters. `ssh host "mkdir -p {remote_dir} && cd {remote_dir} && bash -s"` is
   unquoted, and the heredoc delimiter is not checked against the JSON text. `remote_dir` defaults to an absolute
   local path, and the SSH launcher stages only the three JSON files, not the code; `python3 -m
   r1.c3.d3.campaign_chunk` needs an existing checkout or `PYTHONPATH`, so the report's "self-contained" remote
   directory overclaims.
6. **Error handling and the end record's loss.** `main()` catches only `ChunkStop`; `LaunchStop` from
   `validate_launch` or the end sample escapes as a traceback. An end-sample failure after 18 campaigns leaves no
   `chunk.json`/`summary.json` (see B2). The sampler counts every compute app on the card, with no own-process
   exclusion, so "other" can include our own server.
7. **Dry-run/record completeness.** HTCondor `submit` writes no `submit_record.json` on failure or in the dry run;
   the SSH dry-run's saved record omits the rendered script (only the returned dict has it); no committed
   `ENGINEERING_ONLY` dry-run artifact exists for the HTCondor path. The report's "dry-run submit record" is not
   evidenced.
8. **Per-card lease is not enforced.** Design §3 says never a fixed `gpu0.lock` on a multi-GPU host, but the
   launcher accepts any lease path and does not compare it with the observed UUID; the unit's own test uses
   `/tmp/gpu0.lock`. The `lease_held` helper is a probe that releases the lock, so it is unsafe as a placement
   decision (it is only used in tests).
9. **The per-instance claim is nominal.** `check_hardware` defaults `instance_model` to `campaign_model`, and
   `Manifest.chunk_manifest()` never supplies `instance_model` (`adapter.py:155–166`), so design rule (b) (the
   per-instance claim across arms) is not separately checked; it is equivalent under the current one-model
   manifest, but not the stated comparison.
10. **The end-sample shape is not validated**, and the new chunk test's `other_processes_start` is the int `0`
    while `observed_record` uses a `{"count", "used_memory_mib"}` mapping, so the test does not exercise the real
    start shape.

## 4. Checklist (the six required points)

1. **One chunk script and the same argv — PASS.** Both launchers call `chunk_argv`; the HTCondor wrapper adds only
   `python3` and the staged `PYTHONPATH`, and the rendered `arguments` equals `shell_join(argv[1:])`. The test
   asserts this and my render probe confirms it.
2. **The reviewed HTCondor request is never edited; a mismatch is refused — PASS.** `check_request` refuses extra,
   missing or changed keys, and the values match the reviewed preflight exactly: `universe = container`, 1 GPU,
   8 CPUs, `request_memory = 131072` MB, `request_disk = 150000000` KB, `+RequestWalltime = 3600`, image
   `sha256:49dd9900...75949`. The `requirements` line only narrows placement. Caveats: minor 3 and 4.
3. **SSH lease, free-memory check, count/memory-only record — PARTIAL/FAIL.** The remote script takes an exclusive
   `flock` and refuses a missing/busy lease; `check_observed` refuses a declared memory failure or a foreign lease
   path; `parse_other_processes` stores only count and total memory. But the free-memory value is declared in
   `observed.json`, not measured (M1), and the end record is never produced (B1), with a parser that fails on real
   output (B2).
4. **Host/GPU model/driver recorded; model mismatch refused via `check_hardware` — PASS with caveats.**
   `chunk.json` carries `host`, `gpu_model`, `gpu_uuid`, `driver`/`driver_version`, memory and the proposer fields;
   `check_hardware` refuses a different model, proposer, memory check or lease, and the chunk test covers those
   cases. The observation is static (M1) and host/launcher is not compared (M2).
5. **`end_sampler` fills `other_processes_end` before `chunk.json`, without changing campaign/snapshot/audit logic
   — PASS mechanically.** The addition is after the campaign loop and before the chunk dict in both the harness and
   replicate branches; the campaign, snapshot and audit code is untouched; the new test passes. It is unreachable
   from the launchers (B1).
6. **G1 scientific logic unchanged — PASS.** The diff is additive (an optional keyword and the `main` entry plus the
   sampler); no arm, budget, seed, snapshot, ledger, outcome or audit logic changes. The 40 focused tests pass and
   the full suite has zero new failure ids.

## 5. Limits

I did not start an HTCondor job, an SSH chunk, a campaign, a server or an audit, and I read no label, split,
evaluation or sealed value. The launchers were exercised only through rendering, dry-run construction and synthetic
unit tests. The 117 pre-existing full-suite failures are recorded by id only to establish that the tip adds none; I
did not triage them for this unit.

I changed nothing except this review file.
