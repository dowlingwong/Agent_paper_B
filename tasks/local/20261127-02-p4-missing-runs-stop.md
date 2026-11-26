# local/20261127-02 — P.4: a missing runs path is a protocol STOP (blocks the host-config fill)

Owner: local. Runbook §4 (P.4). Base: `4490a0a9`.

Compute's report `reports/20261126-05-hostconfig-torch-tests.md` on `coord/compute` @ `087ac8df`: with the filled host config
(`p4-hostconfig-fill-20261126` @ `021c4eec`), `r1/tests/test_trackp_p4_runner.py::test_trackp_runs_the_clone_script_from_the_job_directory`
fails. `sft-select --runs <missing>` reaches `SFT.select_lr`, which raises `FileNotFoundError` (rc 1, infrastructure Stop) where the test
expects a protocol STOP (rc 2, `STOP:`). The TODO config only hid this. Fix it in code: a missing or unreadable runs path is
`STOP:` with rc 2 before any read. Keep the test's expectation; add a test with the filled config. Tier E (Track P runner): full suite
on a host with torch (or compute runs the two torch files), and review. Then compute re-runs `cluster/20261126-01` on the fill merged
with your fix.
