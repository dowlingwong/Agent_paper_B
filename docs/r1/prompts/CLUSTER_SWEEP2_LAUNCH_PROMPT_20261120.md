# Cluster agent: sweep-2 launch (20 November 2026)

Written by the coordinating chat (Claude, AI-assisted) at the author's request. Paste the block into the cluster agent. The startup prompt of 18 November (`CLUSTER_AGENT_PROMPT_20261118.md`) stays in force for rules and working style; PLAN §10 on published `main` wins.

```
Published main now carries the sweep-2 integration: int-sweep2-20261118 plus s2c5-switch-20261116 (merge dd1e22be on branch int-sweep2-c5-20261119), merged into main by the coordinating chat under R1-SWEEP2-INTEGRATE-AMEND, with the independent review docs/r1/reviews/SWEEP2_C5_INTEGRATION_REVIEW_20261119.md (ACCEPTED WITH MINORS; htcondor tests 377 passed; full suite no new failures against main's baseline). Fetch main. Keep exactly one cluster session; work from main, not from int-sweep2-20261118 or sweep2-main-20261116.

Continue autonomously, in this order:
1. Scheduler dry runs on main HEAD (the review's process note P1): render the sweep-2 JDLs from the integrated code on main with H200-only placement, run condor_submit -dry-run for every chunk, check request_memory 32000, request_disk 42460970, +RequestWalltime 8735, the v1 image digest, periodic_hold (NumJobStarts > 1) and the H200 requirement; record the outputs and hashes in a short report.
2. The note: on sweep2-auth-20261119, first merge published main into it, then edit docs/r1/authorizations/c3_sweep2_20261119.md exactly as the review's §5 lists:
   - add `layout_wall_hours: <reviewed value, 0 < x <= 48>` next to layout_gpu_hours (derive both from the measured H200 chunk time and 16 chunks; layout_gpu_hours stays 25.88);
   - P2: PASS, citing the integration merge on main and the review;
   - P3: PASS — this note (R1-SWEEP2-AUTH);
   - P6: PASS, citing the integrated switch on main, the review and your dry-run report from step 1;
   - the key-block line `approved: false` becomes `approved: true` (edit that line, not the prose line that also contains the words);
   - update the prose header so it no longer calls the note a draft with P2/P6 at STOP, and make sure no prose line starts with `word: value`.
   Run the integrated s2_c5_switch.parse_note (and resolve_label) on the note; get a fresh independent review against the parsers and the R1-SWEEP2-AUTH bounds; push sweep2-auth-20261119 with the dry-run report and the review; send the author one short Chinese message with the branch tip. The coordinating chat publishes the note to main.
3. Launch, once the note is on published main: launch commit = main HEAD; rerun the S2-C3b liveness at exactly that commit (8/8, or the 7/8 declared in R1-S2C3B-WDBC — only `openml_wdbc` failing, only `invalid_rate`, observed <= 0.30 — required); then enable S2-C5 with both keys for this run id only and submit the 16 chunks to H200. Nothing may change HEAD between C3b and launch.
4. Monitor all 16 chunks under the declared gates and STOPs (worker gates, collection gates, over-walltime STOP, no resume: whole-chunk rerun only for an eviction without a STOP-listed cause), collect, run the gates, seal (SHA256SUMS), and write the sweep-2 report: counts, gates, GPU models and UUIDs, launch commit, S2-C3 results (incl. the L40S descriptive run if it ran), engineering runs that reused sweep-2 instance seeds. Labels stay sealed under R1-BX-D8-CONFIRM.
5. In parallel and lower priority: image v2 I2, then the Track P H200 smoke and E0; the L40S timing smoke and descriptive S2-C3 when NEMO2 L40S slots appear. The review's minors m1 (S2_C5_UNIT.md out of date) and m3 (old dry-run files with the 12203 layout) can be fixed on a small docs branch.
Report to the author in Chinese at the end, or when everything left is blocked.
```
