# S2-C3 L40S deployment check — PRE-DECLARED criteria and replay protocol

Written **before** any replay run (16 Nov 2026, CET) under `author-decisions-20261116` @ `4da73306`
(R1-SWEEP-HOST-HTC signed; R1-SWEEP2-SETTINGS (1) context 32,768) and the corrected work plan
`docs/runbooks-16nov` @ `b3289232` §3 S2-C3. ENGINEERING_ONLY: this check produces no label table and starts no B.2
audit; R1-BX-D8 analysis lock unchanged; EVIDENCE remains gated on P2–P7 + `authorizations/c3_sweep2_<date>.md`.

## What is replayed

The **12 thinking-off B2 roots** (3 nodes × seeds 9011–9014), exactly as recorded in the B2 EVIDENCE batch
`/home/dowling/exam-x/work/b2_8709_20261115_b2/gemma4_31b/b2/off/<node>__s<seed>/job.json` (copied read-only, pinned
here by SHA-256; `job.json` fields: phase=b2, mode=off, dryrun=false, W=20, workers=20, llm_call_cap=80,
harness_commit=a3fedbbd44309b3fdf99d853ad841b9ec2c299e2, authorization_checkout_head=8709dce792d45bbb5c05d9f7d239e19454efbb15,
audit_seeds=[9201–9210] = the **B2 exam final-audit seeds**, not the sweep-2 B.2 seeds 7001–7010; no B.2 audit is run
and no 7001–7010 seed is touched). The replay rewrites only `out` (sandbox) and `base_url` (local llama-server);
everything else stays as recorded. The B2 authorization file is present in the paper checkout at 8709dce7.

## Deployment stack under test

- Host: NEMO2 L40S HTCondor (CloudSite=Nemo2, GPUs_DeviceName=NVIDIA L40S, Arch X86_64, OpSys LINUX, Cpus>=16,
  CpuFamily=6, CpuModelNumber=207; runtime /proc check) — R1-SWEEP-HOST-HTC.
- Image: frozen v1 gpu digest `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`.
- Model: pick GGUF sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` (same as B2).
- Paper code: **`8709dce792d45bbb5c05d9f7d239e19454efbb15`** (the B2 run HEAD; contains the B2 authorization and
  `r1.exam.campaign`; a small reviewed patch only overrides the execution label to ENGINEERING_ONLY for this replay,
  it changes no trial/audit logic).
- Harness: `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`.
- Server = exam setting (R1-SWEEP2-SETTINGS): `-c 32768 -ngl 999 -np 1`, `--jinja`,
  `{"enable_thinking":false}`, q8_0 K/V cache, `cache_prompt` false on every request; non-numeric differences
  (`--no-webui`, `-lv 4`) recorded.
- Each job runs 4 roots of one node sequentially with one owned server; 3 jobs total (one per node).

## Pre-declared PASS criteria (no post-hoc relaxation)

The comparison uses the replayed per-instance `final_y` (after the root's recorded B2 final-audit seeds 9201–9210)
against the B2 EVIDENCE values below; the emitted token is compared, no re-rounding of the metric.

| instance | B2 final_y |
|---|---|
| digits_mlp__s9011 | 0.9727019 |
| digits_mlp__s9012 | 0.9710306 |
| digits_mlp__s9013 | 0.9740947 |
| digits_mlp__s9014 | 0.9727019 |
| openml_credit_approval__s9011 | 0.9365820 |
| openml_credit_approval__s9012 | 0.9216943 |
| openml_credit_approval__s9013 | 0.9337075 |
| openml_credit_approval__s9014 | 0.9120051 |
| openml_ionosphere__s9011 | 0.9041795 |
| openml_ionosphere__s9012 | 0.9749224 |
| openml_ionosphere__s9013 | 0.9018575 |
| openml_ionosphere__s9014 | 0.9078947 |

All of the following must hold (a broken stack fails at least one):

1. **final_y:** every instance |Δ| = |replay − B2| ≤ **0.02** absolute, and the mean |Δ| over the 12 instances
   ≤ **0.01**. (Not bitwise identity — the run is a stack check.)
2. **Parse failures:** replay `parse_failed / forecast_queries` ≤ **0.02** (B2: 0/240).
3. **Diagnostics:** invalid/duplicates/noops counts each within **±10 %** of B2's **20/33/20** over the 12 off roots (240 trials)
   (240 trials, 240 evaluated, 20 invalid, 33 duplicates, 20 noops, 0 parse failures, 0 failed forecast queries).
4. **Full offload:** every replay server log shows full offload (61/61 layers at the B2 setting; any change must be
   explained by a numeric server difference, not accepted silently).
5. **Throughput:** replay total wall for the 12 roots ≤ **2×** the B2 EVIDENCE GPU time (B2 off: 0.504917 GPU-hours,
   i.e. ≤ 1.01 h wall across the 3 parallel jobs' critical path basis; recorded per job).
6. **No STOP:** every root campaign exits 0 with a complete campaign_manifest; a nonzero root, missing manifest,
   label leak (anything other than ENGINEERING_ONLY), pin mismatch, or audit-seed mismatch (must be 9201–9210) is a
   STOP for the whole check — retain everything, no retry.

Pass = criteria 1–6 all hold. Any other outcome is NOT PASS and is reported with the failing values; no criteria are
relaxed after seeing data.

## Outputs

- Job outputs: `out.tar`/`work.tar` + `job_record.json` + `SHA256SUMS` + server log per node (same transfer/seal
  machinery as S2-C2), sealed under `/ceph/srv/dwong/paperb/sweep2/s2c3-<stamp>/` with an ENGINEERING_ONLY marker
  (not evidence).
- Comparison report `S2_C3_RESULTS.md` with the per-instance table, the six criteria verdicts, and the B2 hand-back
  SHA-256 pin; independent review before any EVIDENCE claim.


## Correction (pre-data, 16 November 2026 — before any replay data existed)

The first version of this file quoted criterion 2/3 as "0/480" and "58/82/58 over 480 trials". Those are the
**24-root candidate batch** totals (thinking-off + descriptive thinking-on). This replay is the **12 thinking-off
roots** (240 trials); its pinned per-root `campaign_manifest.json` diagnostics sum to **invalid 20, duplicates 33,
noops 20, parse_failed 0, 240 trials/evaluated/forecast_queries** (derived from the 12 pinned inputs, SHA256SUMS
verified). Criteria 2 and 3 are therefore corrected here to `0/240` and `20/33/20 (±10 %)` **before any replay was
run** (the S2-C3 replay has not executed; see the P4 blocker). The original numbers are retained in this paragraph
for transparency; no post-hoc relaxation is made — the corrected numbers are the B2 off-mode evidence values.
