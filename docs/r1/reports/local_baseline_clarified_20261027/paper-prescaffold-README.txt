Restricted pre-scaffold CPU/offline comparison
PRE paper HEAD: 8ba81b68c70c58d40612c7a316e8d1669ff5ca33.
POST paper HEAD: d4c76d227729efc20a9bd42b5a4261d3b819af85.
Harness HEAD: 897d83c8efa364ec2fdd37288241cc42e01d7274.

Main PRE: 492 passed, 55 failed, 34 skipped, 2 deselected; make exit 2; 106.275 s. Main POST: 510 passed, 55 failed, 34 skipped, 2 deselected. Common 581 IDs have identical statuses; no PRE-only IDs. Final-only 18 passing IDs: 13 predeclaration cases and 5 pilot figure cases. Exact IDs and outcome comparison are in comparison.txt. The predeclaration tests did not exist at PRE. The test_c3_env.py implementation was modified between revisions, so matching IDs do not guarantee byte-identical tests.

Focused tiny random-weight selection PRE and POST: 8 passed, 1 failed (missing kev), 39 skipped (offline empty tokenizer cache); same 48 IDs and statuses; PRE exit 1 and 9.263 s. New H8 fixture tests were held out of main comparison and do not exist at PRE; POST separately passed 26 cases (see /private/tmp/paper-b-corrected-paper-20261027/h8-junit.xml).

run.py and focused-run.py preserve command and explicit exclusions; run.json and focused-run.json record actual environment and results; logs and JUnit XML preserve failures, skip details, individual IDs and durations. The recorded environment matches POST except intentionally separate output directories. This is a restricted test run, not the full suite: excludes identified label/evidence dryruns and one previously >10-minute test; model tests are run separately, empty offline cache forces skips, and sandbox permissions cause local-service errors. Existing mismatched byte-identity assertions and missing dependency remain unresolved. No scientific-readiness inference follows.
