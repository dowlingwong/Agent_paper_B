# Independent review: J3 visible GPU selector helper

**Verdict: NOT ACCEPTED pending API correction and precise scope.** Reviewed candidate `8d2f9c2c4e6a035d7dcf65dac2511e189bfd3935` against HoreKa runbook §3(3),(7). No test suite, temporary fixture, Slurm command, remote host, model, GPU, experiment or deletion was used. One local Python standard-library introspection command was run with bytecode disabled.

The helper correctly retains `SLURM_JOB_GPUS` separately from the selected value in `CUDA_VISIBLE_DEVICES`, and the specific fake example `3` versus `0` is represented in the tests. It is not wired into a runner or submitter and cannot establish device identity, occupancy, selector validity in an allocation, site readiness, or HK6 authority. No current runtime use was found in `r1/**/*.py` beyond the tests. The code uses standard-library features compatible with Python 3.9; actual Python 3.9 execution was not performed.

## Blocking API mismatch

`job_visible_gpu` documents `environment` as a mapping and its exception says `environment must be a mapping`, but the first check uses `isinstance(environment, dict)`. Python's actual `os.environ` is a mapping but is not a `dict`: local `python3 -B -c` reported `_Environ True False` for its type name, `isinstance(os.environ, collections.abc.Mapping)`, and `isinstance(os.environ, dict)`. A natural future caller passing the process environment directly will be refused before any valid selection. Accept `collections.abc.Mapping` and add a fake non-dict mapping test, or explicitly specify and consistently document that callers must pass a copied dict and justify that contract. Retain no access to real environment values in test output.

## Scope and evidence

The regex is a lexical prefilter, not a validator for all CUDA GPU or MIG identifiers: e.g. `GPU---` matches it and exact-string deduplication cannot identify aliases or abbreviated identifiers that name the same device. The report's general statement that malformed selector strings are rejected should be narrowed to the implemented character/list checks; actual UUID resolution, distinct physical identity, correct child-process CUDA namespace, and mixed selector treatment remain mandatory runner/site validation. `SLURM_JOB_GPUS` is only checked for a nonempty, newline/NUL-free string and preserved unparsed, as intended. An entry accepted by this helper is not proof it refers to a usable or authorized GPU.

The report states three pure in-memory unittest cases passed, but this review did not rerun them and no standalone test output log was supplied. Their source includes the 3/0 example, exact duplicates and invalid indexes. A focused non-dict-mapping regression is missing. Nothing here approves the author's k choice, an evidence job, the J3 runner, or HK6.

SHA-256: helper `09a50db2cc49ee0312f57d7041fec12278ac00acc90c284a5206d4eea6e54d1f`; tests `23f8f152fedd67b27f0c2c54439174298138e8deb2d90043f84beaf5f6ccfc4e`; report `2ab4e13fae157baba18d83edc80a711d98e6d480c5484979104c797017fa6946`.
