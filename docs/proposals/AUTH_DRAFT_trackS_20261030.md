# Authorization note (DRAFT) — Track S evidence runs S3a and S3e

**Draft prepared 30 Oct 2026 by the chat session (Claude); AI-assisted. It authorizes nothing until the author edits it as needed, moves it to `docs/r1/authorizations/trackS_<date>.md` and commits it. That happens after the pre-declaration (S0.8) is committed with its hash in PLAN §10.**

## What is authorized

The Track S evidence runs, as specified in the operator runbook `docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, Phase 8:

- **S3a** (descriptive): about 150 forks per node, roots under m\*.
- **S3e** (primary): n = 300 fresh instances per node under π\*, m\* and the matched static. The exact placebo comes first (10 instances), followed by the descriptive placebo (15 instances). The secondaries run on 30 instances.

Both runs are labelled **EVIDENCE**.

## Conditions

- **Design and rules:** design revision 7.4 (`docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` at docs commit `<commit>`, sha256 `<sha256>`); the operator runbook revision 3 (or the revision in force) at `<commit>`; the pre-declaration `docs/r1/predeclarations/trackS_<date>.json` with sha256 `<hash>`, and PLAN §10 rows R1-TRACKS-ADOPT, R1-TRACKS-S02, R1-TRACKS-FRAMING and R1-TRACKS-HOST/-2.
- **Hosts:** `digits_mlp` runs on TASL-2 only and `tabular_mlp` on TASL-7 only. The GPU lease is held throughout. Track X and Track P evidence runs keep priority.
- **Pins:**
  - paper `9bb64ba<full hash>`;
  - harness `115df37<full hash>`;
  - llama.cpp v0.7.0, commit `620d2225cc436ab0b001e3200e590e3b286ef9ab`, built on each host;
  - GGUF `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` @ `13fb94bfda8c8cf22497dc57b78f391a9acb426a`, file `qwen2.5-coder-7b-instruct-q4_k_m.gguf`, sha256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`;
  - schema `manager_proposal/v1`.
- **Declared values:** λ = `<λ>`; near band b = `<b>` with p_near 0.5; S3a: 30 roots per node, `--forks 4`; π′ file sha256 `<sha256>` (frozen after S3a, before S3e); k = `<k>` shards per host.
- **Budget:** at most 5 days of GPU time per host.
- **STOP conditions:** those of design §10 and of the operator runbook. A STOP deletes nothing. Design §10 decides whether a run is void. Resuming after a STOP in an EVIDENCE phase needs the author's written approval. A pause caused by a priority marker is not a STOP.
- **Interpretation:** the outcome is mapped to the paper's framing only by R1-TRACKS-FRAMING. A "no gain found" result is never reported as evidence that the loop is one-step.

## Signed

Author: ______________________ Date: ____________
