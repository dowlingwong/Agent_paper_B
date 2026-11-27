# D.3 G1 launchers — one chunk script, HTCondor and direct SSH (unit record)

**Status:** ENGINEERING_ONLY, code unit for `compute/20261126-02` (with `cluster/20261126-02`).
No campaign, GPU job, audit, server, label or evaluation value was run or read.

**Design authority.** `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`
sha256 `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d`, `ACCEPTED FOR CODE`
(`docs/r1/reviews/D3_G1_G6_LAUNCHER_REV6B_REVIEW_20261127.md`), with revision 6c for the replicate
branch. The G1 chunk unit (`D3_G1_UNIT_20261127.md`) explicitly left the two launchers to this unit.

**Base:** `origin/main` `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536`.

## What the unit adds

| File | sha256 | Content |
|---|---|---|
| `r1/c3/d3/launch.py` | `756e8793329c5ad165f2d7a26b75b37a0b36b7797e8dd138234258a8374bf702` | The `r1_d3_launch/v1` record validation (delegating the signed W, LLM cap and 6201–6218 seeds to `ChunkSpec.from_launch`), the one chunk argv, the reviewed HTCondor request and its refusal on any edit, count/memory-only other-process parsing (including `MiB` and `N/A`), the free-memory check and the lease probe. |
| `r1/c3/d3/probe.py` | `b06207be79846aa80c50f0bc51e5384b83f527b91bdadc709ae9a7c27691b2d2` | The job-side hardware probe that produces the `r1_d3_observed/v1` record at the start of a chunk: host, card model/UUID/driver, total/free memory, other compute processes (count and memory only), the proposer identity and the launcher's request/scope. HTCondor records the actual worker and its scheduler assignment; SSH records the leased host. |
| `r1/c3/d3/launch_htcondor.py` | `5dae455fe8ef880ab47f3fcbc5d408f9db575916f08c9d5eb25c2df82bb37e3e` | `render_submit` / `submit`: one job per chunk, the same `python -m r1.c3.d3.campaign_chunk` argv, the exact reviewed request, a pinned repo tarball, `d3_chunk.sh` (which probes the assigned card and then runs the chunk) and a submit record. |
| `r1/c3/d3/launch_ssh.py` | `ecd18402c7a112ada21fed825c00235fe5a779aa4df034da7e0919783a5037c6` | `render_remote_script` / `launch`: stages the launch/manifest, takes the card's lease with `flock -n` for the whole chunk, probes the card after the lease, and runs the same argv in a delegated user scope. |
| `r1/c3/d3/campaign_chunk.py` | `2fc943ec355f08641239027a9b0b2360176916fac55326371ae000654505674d` | Adds the job entry `main`, a host-mismatch refusal (SSH/direct; HTCondor's chosen worker is recorded, not compared), and an automatic end sample for a probed card; after the last campaign and before `chunk.json`, `other_processes_end` is filled (count and memory only). The campaign, snapshot, audit and record logic is unchanged. |
| `r1/tests/test_d3_launchers.py` | `3db7585a4087bb9623f93b98d51bbb83724f3607f71ede828a4545bae78a4177` | 17 tests: signed-value refusals, argv parity, request immutability, tarball pin, count/memory-only parsing (including real `nvidia-smi` units), probe parsing, host-mismatch refusal, memory and lease helpers, SSH refusals and dry-run fields, HTCondor job-side probe, cluster-id parsing. |

The chunk's existing `r1/tests/test_d3_g1_chunk.py` gains one test for `end_sampler`.

## The two rules the implementation keeps

1. **One chunk script.** `campaign_chunk.py` remains the only implementation. Both launchers pass
   the same argv (`--launch`, `--out`, `--manifest`, `--observed`) and the same `launch.json`
   fields. The only differences are `launcher`, `request` (HTCondor) versus `scope` (SSH), and
   `lease_path`; the inapplicable field is `null`, never omitted.
2. **No request edited for a slot.** `check_request` compares the full reviewed request
   (`universe = container`, 1 GPU, 8 CPUs, 131,072 MB, 150,000,000 KB disk, 3600 s walltime) and
   refuses any extra, missing or changed value. The preflight finding stands: no runnable L40S or
   A100 was advertised on 27 Nov, so this unit submits nothing now.

The model rule is checked twice: `requirements` names the campaign model when the launch record
carries one, and `campaign_chunk.check_hardware` refuses a different observed model, proposer,
host (SSH/direct), lease or memory check before a campaign directory exists. The observed record
is produced by `probe.py` inside the job, not declared by the submit side: HTCondor's assignment
is the reservation and is recorded with `lease: true`, `lease_path: null`, `lease_kind:
htcondor`; SSH takes and holds the lock file.

## Tests

Run with Python 3.12.8, pytest 9.2.0, harness `9bb41680`:

```
AR_HARNESS_ROOT=<harness9bb> python -m pytest -q \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py
47 passed
```

Focused new tests: **14 passed**; chunk + snapshot focus: 44 passed. The full `r1/tests` suite was
run on base and tip by the independent review; the failure-id lists were identical (114 failed /
4,985 passed on base, 114 / 5,003 on tip at the accepted R3 tip; the same 117 failure/error ids, zero new).

## What this unit does not do

- It does not submit an HTCondor job (no matching GPU), start an SSH chunk, open a server, or run a
  campaign. The HTCondor path is exercised by rendering and a dry-run submit record only.
- The G6 audit's `direct` launcher on deepthought is a separate G6 unit; this record covers the two
  G1 launchers only.
- The exact repo tarball is an input to a future launch; this unit pins and transfers it but does
  not create a campaign manifest.

## Reviewer findings and the fixes

The first review (`compute-d3-launchers-review-20261127` @ `da23bd5e`) was **CHANGES REQUIRED**.
This revision answers it:

- **B1 (end sample never enabled):** the chunk entry now installs the end sampler whenever the
  observed record names a card, so both launchers' unchanged argv produce the end record.
- **B2 (real `nvidia-smi` units):** the parser accepts `MiB` and `N/A`, and the query uses
  `nounits`; `N/A` is counted in `unknown_memory_count` rather than failing the chunk.
- **M1 (observed record declared, not sampled):** `probe.py` samples the card inside the job;
  HTCondor's wrapper and the SSH script both run it before the chunk.
- **M2 (host mismatch):** `check_hardware` refuses an SSH/direct host mismatch; HTCondor's actual
  worker is recorded and disclosed.
- **M3 (HTCondor lease):** the probe records the scheduler assignment as `lease: true`,
  `lease_path: null`, `lease_kind: htcondor`; the SSH path still holds the lock file.

The second review (`ceea2f7f`) found one remaining blocker and two majors; this revision answers
them:

- **R2-B1 (SSH/direct host check vacuous):** the probe now records `socket.gethostname()` for
  every launcher, so `check_hardware` compares the actual host with the launch record; the test
  uses a monkeypatched hostname, not a hand-built record.
- **R2-M1 (GPU 0 always sampled):** the probe derives the card index from the `gpu<index>.lock`
  lease (HTCondor's container has one visible card, index 0); a test runs `nvidia-smi -i 3`.
- **R2-M2 (default 46,000 MiB exceeds an L40S):** `hardware.required_memory_mib` is now required
  in the launch record, with no magic default; the probe refuses without it.  The low-level
  `probe()` helper also has no default.

The third review (`0b4f7490`, reviewed tip `3cfaa6fe`) is **ACCEPTED** with minors only:
the low-level default (now removed), a per-UUID lease falling back to index 0 (only
`gpu<index>.lock` is parsed), an exact SSH host comparison that refuses an alias/FQDN difference
(the launch host must equal the probe hostname), and two test-coverage notes.  The probe's
`hardware.required_memory_mib` guard, actual-host record, lease-index derivation and zero new
failure ids were verified.

## Decided alone

To keep the launcher record additive to `r1_d3_launch/v1` and to require the pinned repo tarball
rather than assume the image contains the paper code; to put the hardware probe in the job (so the
record describes the card actually used) and let the chunk sample the end state; to treat
HTCondor's GPU assignment as the reservation and the SSH lock file as the lease; to use `fcntl`
for the local lease probe so the unit is testable on the Mac while the hosts keep `flock`.
