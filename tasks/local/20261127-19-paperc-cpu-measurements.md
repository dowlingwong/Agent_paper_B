# local/20261127-19 — Paper C: the two CPU measurements (R1-PAPERC-MEASURE-FIRST), runbooks first

Owner: local (drafter), with compute for the runs. PLAN R1-PAPERC-MEASURE-FIRST and R1-PAPERC-ROWS-CONFIRMED (once merged; the coordinator is
merging the consolidation now). Paper B work stays first in your queue.

(a) **Fresh-seed audits of retained and final incumbents** on `digits_mlp`, `tabular_mlp`, `openml_credit_approval` and `openml_ionosphere`
(sweep 1). (b) **Guarded first-accept measurement** on digits and tabular, compared with the start configuration from the first step.
For each, write its runbook and pre-declaration (seed block from Paper C's seed registry, checked against every reserved namespace;
outputs; the stakes floor of R1-PAPERC-ROWS-CONFIRMED (3) as the eligibility reading), with code and tests, an independent review until
accepted, and the authorization note the rows require. The CPU host and budget follow the rows; deepthought within its limits. Report each as
a separate unit. After both results exist, the coordinator compiles R1-PAPERC-CORE for the author.
