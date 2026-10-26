Paper post-change CPU test comparison
Paper: d4c76d227729efc20a9bd42b5a4261d3b819af85; harness: 897d83c8efa364ec2fdd37288241cc42e01d7274.
Baseline: /private/tmp/paper-b-baseline-paper-20261027, commit 1f5c27ed0731917d52a3f58b07ea2e1633b78c11.
Main matched suite: identical 599 test IDs and statuses: 510 passed, 55 failed, 34 skipped, 2 deselected. No new/resolved failures or skip changes. Baseline failures remain, including permission-restricted fake service tests, one process-census assertion and two reproducibility assertions. See comparison.txt and full JUnit.
Focused random-weight selection: identical 48 IDs and statuses: 8 passed, 1 failed (missing kev), 39 skipped (empty offline tokenizer cache).
H8 fixture-only selection: 26 passed; separate from baseline comparison.
Test files added after baseline were ignored for main selection and run separately; same remaining baseline exclusions and deselections apply, specified in run.json. Recorded CPU/offline settings, commands, elapsed times, exits and 590 s timeout: run.json, focused-run.json, h8-run.json; logs and JUnit files accompany each. Exact selected IDs and individual outcomes are in the XML. All clones remained clean. No claims of scientific readiness.
Initial main run used a different inherited PATH suffix; it was preserved as initial-path-run.json, initial-path-run.log and initial-path-junit.xml. The main comparison above uses the replacement with the exact baseline recorded PATH.
