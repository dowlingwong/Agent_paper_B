# cluster/20261126-01 — torch tests of the host-config fill (open since 26 Nov, 02:40 CET)

In a deepthought checkout of `p4-hostconfig-fill-20261126` at its tip, with a torch environment (CPU is enough):

    python -m pytest -q -p no:cacheprovider r1/tests/test_trackp_p4_runner.py r1/tests/test_trackp_sft.py

Change nothing. Done when: your report gives the tip you tested, pass/fail counts and the id of any failure. With
zero failures the coordinator publishes the fill (R1-AUTONOMY (3)).
