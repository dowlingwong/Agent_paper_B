# Independent tier-E review — Track P P.4 P3

Task `local/20261127-25`. Fresh reviewer `p3_independent_review`. Published base
`83425c7008826c2a4edb5470c708d8ce083d13f3`. Exact runner candidate
`0b46595418bb21dc0e8e5b234b30f2a84ac5082c`.

The reviewer **accepted the runner change** subject to the required test comparison. Both
`sft-data` label modes and the synthetic evaluator reach the same prompt-replay predicate in
`r1.c3.features`. The reviewer independently imported its actual summarizer from the exact
clean `897d83c8efa364ec2fdd37288241cc42e01d7274` checkout and exercised it on a synthetic
row. The job stages that checkout, records its commit and repository, and selects it for
all three replay subprocesses. The switch checks the exact harness commit across the note,
the spec and the stage manifest. The job and synthetic evaluator have no subprocess deadline.
Git, staging, health and sampler helper guards remain.

The reviewer **accepted the Ada-only spec contents** in
`befb58c8b3f5b222a2cf8973e513b252235453fc`, SHA-256
`d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6`. The spec-only commit
has the pinned code as parent. Launch-strength validation and all four canonical Ada venv
descriptors pass. The reviewer checked the published configuration, split, freeze, train/dev
receipt, VERSIONS and probe charge and timing bindings. An in-memory submit spy verified that
the CLI passes `--spec` to the existing committed-byte and published-tree checks.

The reviewer **accepted the bound draft for the blocked handoff** at
`82940a4988775eba6c8ed2d89de88f220af2e25f`, SHA-256
`33175a171482fffbfc72322e42c745581fac60574e98ac83930372419c060a23`. P2 matches its reviewed
source. Parsing refuses at P3. The standalone binding check requires the missing Ada smoke
and E0 citations. Supplying diagnostic path tokens in memory confirms the remaining bindings.
The draft stays unsigned. P3 needs the project SSH signature on the spec-only commit, P4
needs the author's tick, and P5 needs the reviewed staged Ada smoke and E0 parity with a
timing disposition. No jobs were submitted.

## Full-suite and focused re-check

**Final tier-E runner verdict: ACCEPTED.** The reviewer independently compared the full
node IDs, including parameter whitespace, from the serial base and exact `82940a49`
candidate logs. Base 5,042 passed and candidate 5,044 passed. Both had 153 failures, 6 errors,
170 skips, 7 warnings and 71 passing subtests. The 159 failure/error IDs are identical and
their sorted newline-terminated list has SHA-256
`971c9517afff96ea8074f2e87f34bf597552b491835d07c44ed88a4b121a9718`. Both P.4 torch files
passed on the candidate, 215/215. The exact candidate diff passes `git diff --check`.
