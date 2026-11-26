Reviewed base: `06673f50` (the accepted P.4 evaluator and phase-1 draft rev 3, `mac-trackp-p4-20261120`); accepted at `3b65dfec90aeec806a7cc693526a2072951bc869`

# Independent review record — P.4 phase-1 authorization draft revision 4: host NEMO2 H200 with image v2 (approved: false)

**Unit.** `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`, revisions 4–4.1, on
`mac-trackp-p4-h200-20261121`: the host re-targeted to NEMO2 H200 with image v2 as an HTCondor job under R1-T1-HOST-TASL;
phase 1 only; new decisions P4-MB and P4-JOB; the cluster prerequisites (the queue of 21 Nov 2026, item 3). The
evaluator code is unchanged.

**Process.** One independent reviewer for all three rounds, read-only, scratch under `/tmp/rev_p4h/` moved to its
`_to_delete/`; no secrets, labels or evaluation values read. Round 3 confirms the fixes after the round-2 acceptance.
The round texts are reproduced below as delivered.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `583e46ec (rev 4)` | CHANGES REQUESTED (3 major, 6 minor) |
| 2 | `afb000ab (rev 4.1)` | ACCEPTED (2 minor) |
| 3 | `3b65dfec` | ACCEPTED (confirmation) |

**Open for the author and the runner unit.** The seven phase-1 decisions; prerequisites P1–P8 (in particular the I3 v2
result record, the reviewed H200 smoke and E0 equivalence, the SFT fit and timing probe, the P.4 runner unit with the
HTCondor job, R1-T1-HOST-TASL on `main`).

## Round 1 (`583e46ec (rev 4)`)

> Verdict: CHANGES REQUESTED
>
> Reviewed 583e46ec against 06673f50, read-only. My scratch files are in /tmp/rev_p4h/_to_delete/. I did not read secrets, labels or seed 7001–7010 values.
>
> What holds:
> - The R1-T1-HOST-TASL quote matches the row on `author-decisions-20261121` @ e5e452a0 word for word.
> - The summaries of R1-QTORCH-AMEND, R1-HTC-QTORCH and R1-TRACKP-I3-H200 are accurate.
> - No TASL host or A′ fallback is left in the protocol, the STOPs or the key values.
> - Phase 1 only; `approved: false`; six open decisions, listed consistently.
> - The P4-CAP numbers recompute: 13.46 and 12.81 full-run equivalents, about 3.51 h for the 0.8B bases, about 10 and 21 GPU-h. The 8× case is 31.5, plus 2 for probes and checks, plus 2 for startup under P4-JOB A, giving 35.5 ≤ 40. The slot-hour cap is 64 = 1.6 × 40.
> - The code matches what the draft says: the SFT `DEFAULT_PROTOCOL` micro-batch is 8, `_stage_s` never enables gradient checkpointing and lets the host config set only the micro-batch, and `--check-config` lists placeholders and fails until they are filled.
>
> **Blocking**
> None.
>
> **Major**
>
> M1. §2 "The host" (l.97), §10 (l.303), §4 OOM STOP, §8. Problem: the draft assumes the "default micro-batch 8" on H200. But the existing host config `r1/scripts/configs/trackp_htcondor_v2.json` sets `"sft": {"micro_batch": 16}`, and `_stage_s` takes `host.get("micro_batch", …)`. A run with that config would use 16, with checkpointing off. A rough activation estimate puts a 4B base at 16 near or above 141 GB. The draft never mentions this config. Fix:
> - Name `trackp_htcondor_v2.json` as the job's host config.
> - Have the P3 runner unit set `sft.micro_batch: 8`, or let the author choose 16 or 8 explicitly.
> - Add a key line `micro_batch: <n> (host config sft.micro_batch)`.
> - Point P7's check-config at that file, including its `TODO_VERIFY_ON_HOST` values (paths, GPU, `lock_path`, the causal_conv1d 9.0 build).
>
> M2. §2 (l.98 "checked by the smoke"), P5 ("the 4B memory and step time from the smoke recorded"), P4-CAP (l.141). Problem: the reviewed, staged H200 Track P smoke (`origin/trackp-h200-20261118`, `stages/smoke_h200/probe.sh`) runs `trackp_gpu_smoke.py` on qwen3.5-0.8b-base. The staged E0 check runs kev-0.8b through E0. Neither runs Stage S SFT or a 4B base, so the smoke cannot show that a 4B base fits at the chosen micro-batch or give its per-run time. Fix:
> - Add an explicit ENGINEERING SFT fit and timing probe: one `sft-dev` run per 4B base on synthetic labels, inside the P4-JOB job, after the smoke and E0 PASS (it is cluster training under R1-HTC-QTORCH).
> - Give it a STOP and include it in the cap's "under 2 GPU-h".
> - Reword P5 and §10 to match.
> - Mark "these 4090 figures are an upper bound" (l.141) as *(assumed)* until that probe has run.
>
> M3. "What exists now" (l.44–46) and P5. Problems:
> - (a) No I3 v2 result record exists on any remote branch. `i3-h200-20261119` holds only the job unit (`i3_v2.jdl/.py/_job.sh`), and its last commit is a fix for an output-transfer hold. "ran on NEMO2 H200 … its result record is not yet on `main`" and P5's "the I3 record of `i3-h200-20261119`" both imply a record that does not exist.
> - (b) The draft leaves out what does exist on `origin/trackp-h200-20261118`: I2 v2 PASS (`I2_V2_RESULT.md` with its independent review), and the staged H200 smoke and E0 jobs with pre-submit reviews and scheduler dry-run PASS. So "No Track P HTCondor job exists yet" is inaccurate; what is missing is the P.4 SFT job.
>
> Fix: say I3 v2 on H200 has no committed result record yet, and make P5 require one with its review. Cite `trackp-h200-20261118` (HANDOFF.md, the I2 result and review, the staged smoke/E0 jobs) as the route to P5. Narrow l.46 to "no P.4 SFT job".
>
> **Minor**
>
> m1. §1 heading "reaching `main`". Problem: R1-T1-HOST-TASL is not on published `main`; `main` 4aac5209 does not contain e5e452a0. Fix: add a prerequisite (P6 or a new P8) that the row is on published `main` before signature, as the G.1b switch requires for its rows.
>
> m2. P4-JOB B and P4-CAP l.143. Problems:
> - Under B a base has 9 grid runs, 1 select job and 6 (split A) or 9 (split B) curve runs: 16–19 jobs, not "about 25"; about 64–76 jobs, not 100.
> - B's own startup bound, even recounted (≤ 32–38 GPU-h), breaks the 40 cap once training is added.
>
> Fix: correct the counts. State that B, as posed, needs a higher cap and that C adds ≤ 4 GPU-h of startup.
>
> m3. P4-JOB A versus the walltime STOP (l.182–183). Problem: under A, a failed or timed-out job repeats a whole base and is never resumed. One repeat of a 4B job in the 8× case (about 14 h) pushes the projection past 40. Fix: state this trade-off of A against C in P4-JOB, and say that a repeat counts against the cap (a STOP if it would exceed it).
>
> m4. P4-JOB "Every job" list and §4 STOPs. Problem: base and adapter weights are not mentioned. Fix: add weights staged at the pinned revisions and bound by sha256 (as the staged smoke's `stage_models.py` does), HF offline mode, and a STOP on a mismatch.
>
> m5. §8 `harness_commit: <… if the SFT path imports the harness; else none>`. Problem: this leaves the value undecided. The SFT path does not import the harness `src`, but `run_manifest` always records `git.harness` of `harness_root()` (`AR_HARNESS_ROOT`, or the sibling checkout). Fix: decide the value: "none; the manifest's `git.harness` records whatever checkout is present", or pin a checkout in the job.
>
> m6. Leftover 4090 context. Problem: l.47–49 and P2 still present the 4090 4B memory and step times "with gradient checkpointing on" as the reference, and l.136 says "to be replaced by the P.3a and probe timings" while l.141 says "the H200 smoke timings". Fix: keep P2 to the E0 and E4 verdicts, and point l.136 at the H200 SFT probe of M2.
>
> Nothing needs saving to memory.

## Round 2 (`afb000ab (rev 4.1)`)

> Verdict: ACCEPTED
>
> Round 2 review of afb000ab against 583e46ec. Read-only; my scratch copy of the draft is in /tmp/rev_p4h/_to_delete/.
>
> All of my round-1 findings (M1–M3, m1–m6) are fixed. I checked each fix against the code, the branches and the arithmetic:
>
> - **M1 (micro-batch):** fixed.
>   - The draft now names `trackp_htcondor_v2.json` and says it sets `sft.micro_batch: 16`, which matches the file.
>   - The new decision P4-MB is posed correctly. Under A, 16/8 gives two accumulation steps; under B, 16/16 gives one.
>   - The key lines `host_config` and `micro_batch` are added.
>   - P7 now lists the config's real `TODO_VERIFY_ON_HOST` fields: the paths, the GPU name and compute capability, `lock_path` and the causal-conv1d build.
> - **M2 (SFT probe):** fixed.
>   - The SFT fit and timing probe runs per base, at most 50 steps, on synthetic labels, with checkpointing off.
>   - It runs only after the smoke and E0 PASS, so it respects R1-HTC-QTORCH. It has a STOP, and its cost sits inside the 2 GPU-h line.
>   - P5 now has P4-CAP recomputed from the probe before signature.
>   - The 4090 timing figures are marked *(assumed)*.
>   - The draft now says correctly that the staged smoke runs qwen3.5-0.8b-base and the staged E0 runs kev-0.8b, and that neither is Stage S or 4B.
> - **M3 (what exists, I3):** fixed.
>   - `trackp-h200-20261118` @ af0ce7e2 is cited accurately: I2 v2 PASS with its review, the staged and pre-submit-reviewed smoke and E0 jobs, and a dry run PASS.
>   - The draft now says "no I3 v2 result record is committed", which is true on every remote branch.
>   - P5 requires each record together with its review.
>   - The line about missing jobs is narrowed to the P.4 SFT job.
> - **m1:** fixed. P8 matches the facts: the row is not yet on `main` 4aac5209.
> - **m2:** fixed in P4-JOB. The new figures are correct: 16–19 jobs per base, 64–76 in all, 32–38 GPU-h of startup, and at most 4 GPU-h under C.
> - **m3:** fixed. One repeat of a 4B job in the 8× case gives 35.5 + about 14 = 49.5, which is over 40, so treating it as an author STOP is right.
> - **m4:** fixed. Weights are staged at their pinned revisions and bound by sha256, Hugging Face runs offline, and there are STOPs for both.
> - **m5:** fixed. `harness_commit: none` is decided and agrees with how `run_manifest` records `git.harness`.
> - **m6:** fixed. P2 keeps only the E0 verdicts and E4 limits; the timings now point to the H200 probe.
>
> I re-checked the P4-CAP arithmetic: about 33.5 GPU-h plus at most 2 of startup under A comes to 35.5, within 40. The slot-hour cap of 64 is still 1.6 × 40. The draft is still phase 1 only, `approved: false`, with seven open decisions listed consistently in the header, §2 and P6.
>
> **Blocking:** none.
> **Major:** none.
>
> **Minor**
> - **m7 — P4-CAP, l.172.** The startup line still says "≤ 50 under B (about 100 jobs)", which contradicts the corrected P4-JOB B text (64–76 jobs, 32–38 GPU-h). Fix: change it to "≤ 32–38 under B (64–76 jobs), ≤ 4 under C".
> - **m8 — §2 "The host", l.109.** The probe runs "inside the P4-JOB job layout", but the probe must PASS before any training job (§4) and before signature (P5). Under A, "inside the layout" could be read as the first part of each per-base training job. Fix: say the probe is a separate short ENGINEERING job (`sft-dev` under R1-TRACKP-SFT-DEV), built from the reviewed P3 job unit with the same image, identity checks and sealing. Its record then feeds P5 before any P.4 job is submitted.
>
> Neither minor finding blocks acceptance.
>
> Nothing needs saving to memory.

## Round 3 (`3b65dfec`)

> Verdict: ACCEPTED
>
> I checked commit 3b65dfec against afb000ab, read-only. The change touches only the draft, 5 lines in and 4 out. Both round-2 minors are fixed and nothing else changed.
>
> - **m7 is fixed.** The startup line in P4-CAP now reads "≤ 2 GPU-h under P4-JOB A, ≤ 32–38 under B (64–76 jobs), ≤ 4 under C". That matches the P4-JOB section and the job counts: 4 × 0.5 h for A, 64–76 × 0.5 h for B, 8 × 0.5 h for C.
> - **m8 is fixed.** The SFT probe is now a separate short ENGINEERING job (`sft-dev` under R1-TRACKP-SFT-DEV). It is built from the reviewed P3 job unit, with the same image, identity checks and sealing. Its record goes into P5 before any P.4 job is submitted. This agrees with the §4 STOP ("a training job before the SFT probe PASS") and with P5, where the cap is recomputed before signature. It still runs only after the smoke and the E0 check PASS.
>
> The probe job's own startup (≤ 0.5 h) plus four runs of at most 50 steps still fits the "under 2 GPU-h" line, so the cap total is unchanged at about 35.5 of 40.
>
> No remaining findings: no Blocking, Major or Minor issues.
>
> Nothing needs saving to memory.

---

Code-Commit: 3b65dfec90aeec806a7cc693526a2072951bc869
Verdict: ACCEPTED

Accepted commit: `3b65dfec90aeec806a7cc693526a2072951bc869` (round 3; draft revision 4.1).
