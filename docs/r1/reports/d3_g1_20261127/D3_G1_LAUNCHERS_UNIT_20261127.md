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
| `r1/c3/d3/launch.py` | `c854de4849f579cc56877e180f46dc462e068b96267fbc6ebd126eb205055ff5` | The `r1_d3_launch/v1` record validation (delegating the signed W, LLM cap and 6201–6218 seeds to `ChunkSpec.from_launch`), the one chunk argv, the reviewed HTCondor request and its refusal on any edit, count/memory-only other-process parsing, the free-memory check and the lease probe. |
| `r1/c3/d3/launch_htcondor.py` | `413f6c6a21a539afdcfb00bf25743179e1fa72763cb07ac823dfb8a498bc46fe` | `render_submit` / `submit`: one job per chunk, the same `python -m r1.c3.d3.campaign_chunk` argv, the exact reviewed request, a pinned repo tarball, `d3_chunk.sh` and a submit record. |
| `r1/c3/d3/launch_ssh.py` | `a2e966d1262d218201d856aa1fc192e525e09dd5a0bea6d080003132d3f783f8` | `render_remote_script` / `launch`: stages `launch.json`/`manifest.json`/`observed.json`, takes the card's lease with `flock -n` for the whole chunk, runs the same argv in a delegated user scope, and refuses a failed observed memory/lease record. |
| `r1/c3/d3/campaign_chunk.py` | `98c6c4788012aec2ced0e5269056df7183195ac1c6e65432b8b64be91e7e715a` | Adds the job entry `main` and an optional `end_sampler`; after the last campaign and before `chunk.json`, the launcher's end sample fills `other_processes_end` (count and memory only). The campaign, snapshot, audit and record logic is unchanged. |
| `r1/tests/test_d3_launchers.py` | `38cbcb9798a4afc14bf7f8a647d03e2b7ac8c7956363e362f59d006fc00597b3` | 10 tests: signed-value refusals, argv parity, request immutability, tarball pin, count/memory-only record, memory and lease helpers, SSH refusals and dry-run fields, cluster-id parsing. |

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
lease or memory check before a campaign directory exists.

## Tests

Run with Python 3.12.8, pytest 9.2.0, harness `9bb41680`:

```
AR_HARNESS_ROOT=<harness9bb> python -m pytest -q \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py
40 passed
```

Focused new tests: **10 passed**; chunk + snapshot focus: 40 passed. The full `r1/tests` suite is
run with the independent review.

## What this unit does not do

- It does not submit an HTCondor job (no matching GPU), start an SSH chunk, open a server, or run a
  campaign. The HTCondor path is exercised by rendering and a dry-run submit record only.
- The G6 audit's `direct` launcher on deepthought is a separate G6 unit; this record covers the two
  G1 launchers only.
- The exact repo tarball and the manifest/observed files are inputs to a future launch; this unit
  pins and transfers them but does not create a campaign manifest or a real observed record.

## Decided alone

To keep the launcher record additive to `r1_d3_launch/v1` and to require the pinned repo tarball
rather than assume the image contains the paper code; to sample the card's other compute processes
after the last campaign through an optional `end_sampler` so `chunk.json` still carries the end
record it promises; to use `fcntl` for the local lease probe so the unit is testable on the Mac while
the hosts keep `flock`.
