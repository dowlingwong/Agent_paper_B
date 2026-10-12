"""Paper B route R1: analysis-side package (branch records, baselines, theory code, pilots).

Every module here runs against a pinned commit of the governed harness
(``autoresearch_harness``, branch ``r1``).  Nothing in this package writes a
harness ledger.  Outputs of pilots are labelled ``PILOT`` or ``ENGINEERING_ONLY``
and are never quoted as results.
"""
