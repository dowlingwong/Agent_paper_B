# compute/20261128-20 — G.5 expansion addenda: TASL-2 isolation records at the new exact harness SHAs

From local's STOP (`coord/local` `13109cd7`): the host-record checker refuses the published TASL-2 isolation reports (1–7 PASS at the G.1b kit SHAs) at
the four new exact G.5 harness SHAs (Titanic `d2ce4701`, MetaMaze `3f92d3c3`, ETTh1 `6fc553df`, Forest Cover per local's table). When local reports those
candidates reviewed (full suite at the candidate pins, tier E), run the TASL-2 isolation checks 1–7 at each exact SHA on the node's CPU set and
environment (Titanic 12–15 torch312; MetaMaze 0–3 venv_jax; ETTh1 16–31 torch312; Forest Cover per local), record + review. If local changes a candidate
after review, rerun that node. Do not take CPUs a running G.5 job holds.
