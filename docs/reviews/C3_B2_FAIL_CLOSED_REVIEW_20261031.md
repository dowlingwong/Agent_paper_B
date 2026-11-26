# Independent B.2 repair review — 31 October 2026

**Scope and verdict:** ACCEPT the narrowly scoped fail-closed change and recovery of the selected historical synthetic fixture files at candidate `7df307be87e3e6e9f7a5cc39dd5f00c3d7f13fb0`, range `007a8d1..7df307b`. This is not acceptance of B.2 readiness, actual task-native attestation, production isolation, replay, or an authorization to run B.2. D5 and PLAN R1-B2-DECOUPLE require B.2 to remain stopped.

## Findings and code tracing

- At `r1/c3/audit.py:683-686`, the attestation requirement unconditionally raises STOP. `evidence_run` invokes it as its first operation at line 695, before provenance, environment, plan, output directory, scratch, or worker creation. The CLI `evidence-run` dispatches to that function. This fail-closed guard does not implement attestation.
- The initial `0d524fd` candidate did not guard `verify_evidence_completion`, allowing the standard evidence consumer to validate older records whose worker runtime was measured in a separate probe. Commit `7df307b` adds the same STOP as the first operation at `audit.py:790-795`, before input reads and planning. `r1/c3/offline_eval.py:117-126, 145-155` routes classified EVIDENCE assembly through that verifier before loading the table or audit rows.
- Legacy `run`, `run_plan`, and `run_config` can still schedule tasks and serve existing engineering workflows. They are not guarded by this EVIDENCE entry STOP. This review does not claim prevention of a deliberate bypass, and those entry points do not confer authority to run B.2 or produce independently validated EVIDENCE.
- Tests at `r1/tests/test_c3_evidence_attestation_stop.py:7-27` cover the two STOP entry points. Downstream guard tests explicitly monkeypatch the STOP solely to exercise fixture-only downstream behavior; these tests do not establish task-native identity.

## Independent checks and limitations

A Git-archive snapshot of `7df307b` was inspected in `/private/tmp/b2-independent-final-20261031`. The local branch and tracking reference both resolved to the full candidate hash at review time. Using Python with a stub `numpy` module, I called both entry functions directly with temporary paths and assertions that provenance and plan were not reached. Both raised the expected task-native-attestation STOP; neither output nor scratch was created. This is a focused control-flow check, not a test of real numpy, worker execution, or task identity.

The requested focused pytest selection (`test_c3_evidence_attestation_stop.py`, `test_c3_evidence_guards.py`, `test_c3_evidence_split_blocks.py`) could not run: the system Python and the existing workspace `.venv` both reported `No module named pytest`; the existing `.venv` also lacks numpy. No pytest pass is claimed. No real task, replay, remote fixture execution, or original-record mutation was performed.

## Recovered fixture hashes

The following SHA-256 values were independently computed on the recovered copies and match `docs/r1/recovery/c3-fixtures-20261031/README.md:3-8`:

| Artifact under `docs/r1/recovery/c3-fixtures-20261031/` | SHA-256 |
| --- | --- |
| `cache/r1/scripts/c3_cache_offline_fixture.py` | `9c7a0851eb82c8688b78be0e0cc948fed7892cfc718a2a8ba3c463743a25e798` |
| `cache/r1/tests/test_c3_cache_offline_fixture.py` | `b22857e80ca0f6ba07275ef3603744a7bf177cee5049d0e4cbc3b2b87a778861` |
| `cache/fixture.log` | `fb34f0668bae4f49d54011ec7daf9dcd286d7985e4a0bba97490e48d7c6b2325` |
| `seccomp/r1/scripts/c3_replay_seccomp_candidate.py` | `d03c03a3213585aabb854e6b29dd5f794b5ad97eb2be06994e9e483ccbacb410` |
| `seccomp/r1/tests/test_c3_replay_seccomp_candidate.py` | `066d1a931d7f49dfc2ad2433050d764873b9a96d0c570caaf0a5d13e04c84056` |

The copied before/after mountinfo hash records agree at `dea2e7c345744026ea28d38be2a7b9201fe01cdef4207139438afd69b7a3176c`. The copied cache log records `1 passed in 15.68s`; this is historical reported evidence, not a rerun or an independent check of its remote source. The seccomp recovery has no original test log in the record. Neither the later production dirfd candidate, Linux production guard behavior, actual sklearn procfd path, dataset preflight, replay evidence, environment conditions, nor actual task-process attestation is established by these copies or this review.
