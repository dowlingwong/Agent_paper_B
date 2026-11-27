# Report — Ada P.4 probe: two 0.8B bases PASS, both 4B bases STOP at micro-batch 8

**Task:** `compute/20261127-19` (= `compute/20261126-07`), PLAN R1-P4-D3-GPU-PREFLIGHT (1), R1-P4-TESTPLAN-DECISIONS,
R1-HOST-FREE, R1-CARD-SHARE, R1-NO-TIMEOUT. ENGINEERING_ONLY; no SFT evidence run, no label/evaluation read.
**Result: PARTIAL PASS / STOP on the 4B fit.** `kev-0.8b` and `qwen3.5-0.8b-base` pass the 50-step synthetic probe
on an empty RTX 6000 Ada; `kev-4b` and `qwen3.5-4b-base` STOP with CUDA OOM at micro-batch 8 on empty 48 GB cards.
Under P4-MB A an OOM is an arm STOP and the author decides; no micro-batch, checkpointing or memory setting was
changed. The probe charged **2.1603 GPU-h** against phase 1's 40 (reporting threshold).

- **Task branch:** `compute-p4-ada-probe-20261127` @ `4e51adef` (two commits over
  `origin/main` `91cfd48a`; docs/records only, no `r1/` change). Full record:
  `docs/r1/reports/trackp_p4_probe_ada_20261127/P4_ADA_PROBE_20261127.md`, the filled probe spec, all eight sealed
  attempts (job records, receipts, logs, `out.tar`), `probe_charges.json` and the refusal.
- **Independent review:** `compute-p4-ada-probe-review-20261127` @ `609581447c369052af3a9a6873fda1bf3260b7a4`,
  **ACCEPTED** (first review `05d3048a` accepted with minor findings; the re-check closed all four). It reproduced the
  image VERSIONS pin from the OCI layer, verified all seals and charges, the two PASS timings and the two empty-card
  OOMs, and agreed the 4B OOM is the arm STOP. The minors are fixed on the task tip (guard loops stopped; T1-complete
  charge; refusal wording; `p4_run.log` files now committed).
- **Hashes:** probe spec `540bd979…`; host config `bb0c7251…` (at `91cfd48a`); image VERSIONS `aaa1a304…`;
  T1 `versions.out` `49fec111…`; `condor_history.txt` `df41e2df…` (`760065 0 3 0.0`); charge total **2.1603**.
- **Measured:** kev-0.8b peak 25,939 MiB, 3.7188 s/step, attempt-4 charge 0.1231; qwen3.5-0.8b-base peak 27,271 MiB,
  3.7055 s/step, attempt-2 charge 0.4511. 4B peaks 48,385 / 48,399 MiB with `torch.OutOfMemoryError`,
  `stop_class: arm`, `oom: true`, empty card at start and end. Estimate for the two 0.8B arms: 2.52 h and 2.51 h.
- **Decided alone:** empty cards 0/2/6; `~/.local/bin` on PATH for `uv`; a clean harness `897d83c8` checkout at the
  job sibling path (the launcher's native environment forwards only PATH and the lease, so `AR_HARNESS_ROOT` cannot
  reach the job); a 2 s fetch guard kept each clone's `origin/main` current because main moved during staging (one
  qwen3.5-0.8b attempt was sealed as protocol for that race and retried); the idle T1 H200 job was removed as a
  no-progress job after the VERSIONS pin had been read. No reviewed file, spec, seed, assertion or label was changed.
- **Two findings for the phase-1 note:** (1) the note's `harness_commit: none` is false for this code — the synthetic
  `sft-data` step imports the harness, and the SFT manifests record `897d83c8…`; the note or a reviewed runner change
  must settle it. (2) The Ada class has no estimate for `kev-4b` or `qwen3.5-4b-base`; the H200 route remains for
  them, or the author changes micro-batch/checkpointing. The `probe-record` builder cannot emit a full record while
  every arm must be STOP-free; no record was forced.
- **Needs:** coordinator merges the task branch and the review branch after its checks; author/coordinator decide the
  4B route and the note's harness line. No GPU job is left running; the Ada guard loops are stopped.

**Task id:** compute/20261127-19. **Branch/tip:** `compute-p4-ada-probe-20261127` @ `4e51adef`; review
`compute-p4-ada-probe-review-20261127` @ `60958144`. **Tests:** `p4_lib validate --probe` rc 0; all eight seals verify;
the two PASS jobs rc 0; a docs/record branch changes no code. **What happens next:** merge, then the phase-1 note
revision and the author's 4B decision.
