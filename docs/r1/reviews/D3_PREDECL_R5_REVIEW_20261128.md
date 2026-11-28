# Independent tier-E review of the D.3 revision 5 draft

Task `local/20261128-09`. Published base `53f58881d691ce50214f2a16f47b41bff89d5047`.
Review by a fresh Codex agent that did not write the draft. The worker recorded the review below.

**Tier-E verdict: ACCEPTED** for `035afb48b7ac22e31914390b0a2eadc7fa8a3012`, draft SHA-256
`0598f314cf82f803ab0dcfa6a3523e5b41760742c8847f4a8ef8de79d0ae3b5c`. The draft is ready for author signature.

The first round returned REVISE on `2ae0d832` because a §10 summary still described the failure-rate STOP
as unchanged. The corrected draft points that summary to R1-D3-REV5 and retains the pre-admitted error
classes and 600 s worker budget. I compared both diffs line by line. The only substantive change from
frozen rev 4 is the pooled stage worker-failure STOP. §10 and §13 item 14 both use a strict cutoff above
**18.53%** and continue counting failed candidate and incumbent replicates. The changelog cites
R1-D3-REV5, and the draft remains unsigned, unapproved and unfrozen.

I independently summed the seven D.3 `append_only_summary` rows in the published Sweep 2 chunk table.
Their failures were 0, 88, 84, 71, 51, 47 and 0, each over 360 trials. The pooled rate is
**341/2,520 = 13.531746…%**, which gives **18.53%** after adding five percentage points and rounding.
The assigned worktree was clean and `git diff --check` passed. Frozen rev 4 retains SHA-256
`e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`, and the analysis source and
synthetic test hashes match their §9 and §14 pins at base and tip. I verified the file hashes
independently and relied on the worker’s separate pytest run for execution results.

The D.3 runtime and analysis tree has no consumer of the numeric stage STOP. The historical P7
reproduction script `docs/r1/reports/d3a_p7_20261128/worker_gate.py` enforces `0.1299` and is pinned
in that report’s manifest. Preserve it as the historical record. Route any P7 gate used under rev 5
separately at **18.53%**. The D.3a note and §8 header builders bind the frozen rev 5 digest in step (8),
after author signature and freeze.
