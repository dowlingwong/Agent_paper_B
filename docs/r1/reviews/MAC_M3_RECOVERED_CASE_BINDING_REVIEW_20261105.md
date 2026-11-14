# Independent M3 recovered-case binding review — 5 November 2026

AI-assisted (Codex). Target `6f03ad938689ec675bde5d5f9c17ad15a2d3ba04`. **Round 1: NOT ACCEPTED pending one documentation correction.** This is an offline planning artifact, not an offline-execution boundary, production launch gate, cache-completeness proof, or acceptance of M3 as a whole.

**Round 2: ACCEPTED within the planning-only scope at `2e65bec360ace59ea158df69ad0c613d82f64f2e`.** The same reviewer checked the limited change: the function docstring and report now state that separate paths and matching hashes do not establish physically independent storage, giving hard links and other shared backing as examples. Test wording and the changed error string agree. This acceptance does not establish a usable integration branch, independence, executability, production safety, or authorization.

The same three local test files were rerun at the corrected revision with the same pinned harness and no numerical execution: **17 passed in 16.61 s**.

## Finding

`offline_recovered_cases.py:32–47` checks that source and copy *directory paths* resolve to distinct, non-overlapping locations, then compares file-content snapshots. This does not establish that the copy is physically independent: regular files in the separate trees can be hard links to the same inode. `MAC_M3_RECOVERED_CASE_BINDING_20261105.md` calls them a "private copy" without spelling out this limit. Correct the documentation and relevant test wording to state exactly what was checked and that independently writable storage is not established; alternatively implement and review a stronger identity check. Neither option makes this planning function an execution gate.

## Scope and checks

- `bind_recovered_cases` calls corpus, collector and recovered-case verification; requires the six selected OpenML nodes to have source/copy mappings; compares snapshot fingerprints; and passes all selected cases to the 16-case shape checker. Its returned payload explicitly says `offline_executability: NOT_ESTABLISHED`. The source/code provenance checks, recovered cases, pinned node/schema checks and configuration digests are meaningful identity/shape checks, not a proof that a future worker will execute without I/O or that a snapshot remains unchanged.
- Independent run with `AR_M3_PINNED_HARNESS=/private/tmp/paper-b-m3-harness-6adf385`, `R1_REQUIRE_M3_HARNESS=1`, using `test_m3_config_checks.py`, `test_m3_recovered_cases.py`, and `test_m3_case_binding.py`: **17 passed in 16.78 s**. Tests inspect frozen records and pinned files, and use synthetic cache contents. No model, numerical replay, GPU, server, or external network was used. This includes the recovered 16-case test but does not establish actual historical cache completeness or provenance.
- This candidate imports the separately held `r1/scripts/c3_env_replay.py` as well as `r1/c3/offline_cases.py`; neither is in integration checkout `730da89`. The former is a production-capable driver, not merely an inert source module. **Do not merge or cherry-pick the binding into integration with those dependencies until their complete diffs and import/launch consequences are independently reviewed**, or refactor a narrowly scoped inert dependency and review it. The existing five held files remain with the author.

## Remaining STOPs

The actual 16 configurations' offline executability, cache completeness and independence, time-of-check/time-of-use protection, dependency closure, Linux boundary and host qualification remain unproved. The implementer/reviewer must complete and independently review the non-numerical preflight and supervisor; an authorized operator separately verifies the site. Estimate is one or more engineering days plus host-dependent qualification. This review creates no authority for either execution or policy changes.
