# S2-C4 — timing pilot unit (1 node × 2 instances × both memory modes; ENGINEERING, unit for review)

**Authority:** `docs/r1/prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` (`docs/runbooks-16nov` @ `a2789ea6`) §3 S2-C4;
engineer units may proceed before P1–P7 (runbook §0). It builds on the **accepted S2-C2 wrapper**
(`S2_C2_REVIEW_20261116.md`, final ACCEPTED for the ENGINEERING path). No EVIDENCE, no labels read.

## What the unit does

`S2-C4` measures the L40S job cost on the real sweep stack and fixes the job layout for sweep 2:

1. **`sweep2/s2_c4_pilot.py make-specs --run-id <id> --out-dir <dir>`** derives two S2-C2 job specs from the
   reviewed `spec.example.json`, both for one node (`digits_mlp`), **2 instances**, one per memory mode
   (`append_only_summary`, `none`), each with its own `chunk_id`, ENGINEERING label, and the frozen v1 gpu digest /
   B2 harness pin from the base spec. It creates a fresh dir and refuses an existing one.
2. The two jobs are submitted exactly through the reviewed S2-C2 path (renderer staging + `condor_submit`), with
   the JDL's output transfer (`out/`, `work/`, `job_record.json`, `SHA256SUMS`, `llama-server.log`) back to the
   submit host; the S2-C2 wrapper records host/GPU/CPU/image/model/server identity and the GGUF fetch time.
3. **`collect --chunk-dir <dir> …`** reads the transferred chunk outputs and records per chunk: queue wait and wall
   time (HTCondor user log), GGUF fetch seconds, collector seconds, llama-server model/KV buffers (MiB), offload
   layers, host/GPU. It writes `timing.json` + `S2_C4_TIMING.md` with the measured values and the extrapolated
   full-sweep layout (8 nodes × 2 modes; `full_wall = pilot_wall × 18/2`; total GPU-hours; proposed
   `+RequestWalltime`, disk, memory; one (node, memory mode) chunk per job). It refuses any chunk whose record is
   not `ENGINEERING_ONLY` (no labels read).

## Why it matters

- The first ENGINEERING run uses a **small chunk** (2 instances) rather than an 18-instance/7200 s guess, so a
  misestimated walltime/memory/disk cannot hold or kill a long job; the S2-C2 residual r4 guidance is followed.
- The pilot pins the real `request_disk`/`request_memory`/`+RequestWalltime` and gives the provisional sweep-2
  estimate (P5); S2-C3 (deployment check) remains a separate unit, and the sweep-2 authorization (P3) uses the
  measured numbers.

## Tests and dry-run

- `r1/tests/htcondor/test_s2_c4_pilot.py`: 4 synthetic tests (pilot spec generation/validation, HTCondor log
  parse, layout extrapolation, llama buffer parse) — pass with the S2-C2 suite (**27 tests total**).
- The generated pilot specs are validated by the accepted S2-C2 validator (so the same pins/class/transfer rules
  apply); their JDLs are rendered by the accepted renderer. No submission was made for review; the two ENGINEERING
  jobs will be submitted only after this unit's review accepts them.

## STOP / no-retry / no-deletion

Existing spec dir; non-ENGINEERING record; missing HTCondor log or chunk record; inconsistent timestamps; empty
timing set — all STOP (keep the transferred chunks; no retry; no deletion; no labels read). The S2-C2 wrapper's own
STOP conditions apply unchanged to the two jobs.

## Review checklist

- Are the pilot dimension (1 node × 2 instances × both modes) and the extrapolation formula (`×18/2`, 16 chunks)
  the right basis for the layout/estimate?
- Is the timing collection sound (HTCondor user log queue/wall, job record GGUF/collector/server, llama buffer
  lines) and does it avoid reading labels?
- Are the STOPs and the "small chunk first" rule sufficient; anything missing before the two ENGINEERING jobs may
  be submitted?
