# Track S `digits_mlp` host move to TASL-7 — proposal (12 November 2026)

**Author decision recorded here; not yet executed.** The author's chat message of 12 Nov 2026 (relayed by the
operator, quoted only as the decision "migrate `digits_mlp` to TASL-7 and run it after the B1 `_c` run ends") moves
the `digits_mlp` node's host from TASL-2 to TASL-7 after B1 `_c`. This is an ENGINEERING_ONLY Track S change; it is
not a scientific result and starts nothing by itself.

## 1. Why

TASL-2 became unreachable on 12 Nov 2026 (TCP/ICMP to 100.120.160.70 failed; Tailscale peer showed rx 0 while
TASL-7 was reachable). The Phase 4 S0.5 attempt started on TASL-2 at 2026-11-12T19:55:59Z and was last seen running
with 4 committed roots (20:02Z); it cannot be censused, resumed or copied while the host is down. Per the Track S
operator runbook §10, a TASL-2 reboot/outage is "anything not covered → STOP and ask"; the author has now decided
to move the node to TASL-7 rather than wait. **The TASL-2 `s05` scene is preserved, never modified or deleted.**

## 2. What TASL-7 already has (verified read-only, 2026-11-12T22:41Z)

- 1 × RTX 4090, driver 580.178.04, 24 CPUs; `/home/dowling/r1_tracks` with `bin/`, `launch/`, `logs/`, `models/`,
  `opt/llama.cpp`, `remotes/Agent_paper_B.git`, `scratch/`, `out/` and `work/`.
- `work/Agent_paper_B` exists at the **previous** paper pin `d10b05b7` (clean) → must be moved to `8237fd02`.
- `work/autoresearch_harness` at harness pin `a3fedbb…` (clean).
- llama.cpp `620d2225…` (`llama-server` `v0.7.0-dev`, build 11669); GGUF sha256
  `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; server flags per rev 3.3 §0.2.
- Track S venv Python 3.11.18, numpy 2.4.6, sklearn 1.9.1 (frozen per host at Phase 0). **The TASL-2 Track S venv
  differed** (numpy 2.4.4 / sklearn 1.8.0 on the B1-side check; the Track S venv on TASL-2 is frozen separately).
- S0.1/determinism/latency and the CPU census were run on TASL-7 for its allocated node (`tabular_mlp`); **no
  `digits_mlp` S0.1 exists on TASL-7**.
- TASL-7 is currently running B1 `_c` (run `4b31_20261112_c`), whose marker is the authoritative priority marker;
  the Track S watcher on TASL-7 pauses on it. Track P marker absent (paused for B1/B2).

## 3. Conditions before a `digits_mlp` run on TASL-7 (all mandatory)

1. **B1 `_c` must have ended normally** and its marker must be retired by the reviewed post-run procedure (with its
   creation receipt kept; nothing of the B1 scene deleted); the GPU lease must be free and no llm/compute process
   of another track present. If B1 `_c` ends in a STOP, this move waits for the author.
2. **Host facts + Phase-1-equivalent check for `digits_mlp` on TASL-7**, after the GPU is free (<1 GPU-h):
   record hostname/driver/CPU/venv versions, the `llama-server` version and GGUF sha; run the S0.1 determinism and
   latency checks for the digits node with the same pinned rule/harness; record the result in a report. A failure is
   a STOP (author). The `digits_mlp` worker venv on TASL-7 differs from TASL-2's; this is disclosed, and the S0.5
   analysis is self-consistent on TASL-7 but not directly comparable with TASL-2 numbers.
3. **Paper pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** checked out detached and clean on TASL-7
   `work/Agent_paper_B` (same pin as the TASL-2 S0.4 rerun; the branch is pushed to the TASL-7 bare repo).
4. **Prior reuse with disclosure**: `a2u_prior_r2_20261111.json` (sha256
   `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`) is copied to TASL-7 `$OUT` and verified;
   it was computed from the TASL-2 S0.4 rerun and is used host-independently, with the host change disclosed.
5. **New launch scripts for TASL-7** (`tasl7_s05_<date>.sh`, `tasl7_s05b_<date>.sh`) with new `--out`/`--work`
   directories (for example `s05_t7_20261113`), session names `trks_s05_t7`/`trks_s05b_t7`, the same rev-3.3 Phase 4
   command (W 40, 20 instances, policy `static:0.00198,0`, obs-inflation 1.0, prior sha above, 8 h deadline,
   ENGINEERING_ONLY), committed and independently reviewed before use. `k = 1`, port 18101.
6. **Nothing of Track X, Track P or the TASL-2 scenes is touched**: TASL-7 Track P stays paused as during B1/B2; no
   Track P marker is created or retired; TASL-2 partial output remains preserved.
7. **After S0.5**: run S0.5b (CPU, no servers), copy back `$OUT/s05_t7_*` and the calibration/truncation files to
   `results/r1/tracks/digits_mlp/s05/`, write the report + STATUS, get a fresh independent review, then pause and
   report (L1). The S0.5 summary and STOP 4 still wait for `tabular_mlp`.

## 4. PLAN §10 row draft (author decision; to be committed by the author/Mac agent or with the author's relay)

`| R1-TRACKS-DIGITS-HOSTMOVE (12 Nov) | The author's chat message of 12 Nov 2026 (relayed by the operator) moves Track S's digits_mlp node from TASL-2 to TASL-7 after B1 run _c ends, because TASL-2 became unreachable on 12 Nov. The TASL-2 s05 partial scene is preserved and never resumed; the move runs only under the conditions in reports/TRACKS_DIGITS_HOSTMOVE_20261112.md: B1 _c normal end + marker retirement, digits_mlp host facts and S0.1 determinism/latency re-established on TASL-7, paper pin 8237fd02, prior 5c849d15 reused with the worker-venv host difference disclosed, new reviewed TASL-7 launch scripts, and no disturbance of Track X/Track P. The run is self-consistent on TASL-7; cross-host comparability with TASL-2 numbers is not claimed. B2, X.7 and sweep 2 remain gated. |`

**Operator note.** The operator does not add author decisions to PLAN unilaterally; the row above is paste-ready for
the author/coordinating session, or can be committed on the author's explicit relay instruction. Until it is on the
branch, this proposal only records the decision and the conditions.

## 5. Open items

- TASL-2 census when/if the host returns: read-only capture of the `s05` scene and the host state; if it returns
  before B1 `_c` ends, the author decides whether to keep the TASL-7 move or return to TASL-2. If both exist, the
  TASL-2 scene is kept as a stopped observation only.
- Track P resumption after B1/B2 is outside this proposal; Track X and Track P order remains the author's.
- The `digits_mlp` S0.1 on TASL-7 must run after the GPU is free; its result gates the S0.5 start.
