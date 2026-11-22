# Track P P.4 phase 1 — the author's decision list (one page; approved: false)

For the authorization draft `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` on
`mac-trackp-p4-h200-20261121` @ `3eeccf9a` (revision 4.1, accepted in review, unpublished). Prepared by the Mac-desk
agent (Claude), AI-assisted, 21 Nov 2026, against published `main` `16e0b52c` and the accepted queue-1 units of the same
day. Each line is a decision with a recommendation. The full options are in the draft's §2. Two items are new since
revision 4.1: P4-LABELS, and the effect of the signed PRE-SPLIT A on P4-P1SPLIT.

| # | Decision | Recommendation | Why, in one line |
|---|---|---|---|
| 1 | **P4-PHASE1-TEST**: a real-label test read in phase 1? | **A: none.** The evaluator runs on synthetic labels only. | A phase-1 read would use up the evidence test partition before the phase-2 arm, lr, seeds and temperature are fixed. |
| 2 | **P4-P1SPLIT**: phase-1 instances | **A: P3, now settled.** Tick it; there is no live choice. | R1-SWEEP2-PREREG signed PRE-SPLIT A. Since the Track P P3 unit (`mac-trackp-p3-20261121` @ `84b86b83`), real labels are refused without the signed split file at build, at load and in the CLI, so B (`trackp_sft/v1`) is no longer buildable. The draft's A text must now say "the P3 split file is the assignment (`split_file`)" and drop "salt `c3_p3_split/v1` … over the fixed universe" before the note is final. Its evaluator already passes on a P3 build (tested in that unit). |
| 3 | **P4-LABELS** (new): where phase-1 labels come from | **A: the receipted sweep-1 train/dev partition** (`label_block.traindev.jsonl` with `RECEIPT.json`), released under R1-S2-LABELS-TRAINDEV-RELEASE after the preregistration freeze. | The release-step unit (`mac-release-20261121` @ `275d7dcb`) makes `LabelBlockSource` open only a receipted partition until the T0 test release row exists. The draft's `labels: …/label_block.jsonl` line is therefore refused in phase 1. P1 becomes "freeze signed + train/dev release receipt". B would be a PLAN row exempting ENGINEERING phase 1 from PRE-STAGE, plus a code change. Not recommended: phase 1 would then read P3-test labels through the raw block. |
| 4 | **P4-ARMS**: bases | **A: kev-0.8b and kev-4b**, minus a Kev base whose P.3a record shows an E0 failure or E4 hard limit; both Qwen controls always carried. | R1-C3-POOL-EXAM / R1-C3-CONTROL. A control that cannot be trained is a STOP, not a silent drop. P.3b no longer gates P.4. |
| 5 | **P4-MB**: micro-batch on H200 | **A: 8** (effective batch 16, two accumulation steps). This means changing `trackp_htcondor_v2.json` `sft.micro_batch` from 16 to 8, which changes the host-config sha256 the note records. The H200 SFT probe (P5) confirms the fit with checkpointing off. | It is the SFT default. 16 may approach 141 GB on a 4B base at 1,024 tokens. An OOM is a STOP either way. |
| 6 | **P4-JOB**: HTCondor job layout | **A: one job per base** (grid → `sft-select` → learning curve inside the job), four jobs. | No state crosses jobs, and startup is ≤ 2 GPU-h. B (one job per run: 64 jobs under P3) costs up to 32 GPU-h of startup and breaks 40 once training is added. |
| 7 | **P4-LC**: learning curve | **A: the points below the training-set size, plus the full set as the last point.** Under P3 (≈ 590 training rows) that is 250, 500 and full. | 1k/2k cannot be run on phase-1 data. The full-set point is the selected-lr grid run, at no extra cost. |
| 8 | **P4-CAP**: GPU budget | **A: 40 GPU-h**, slot-hours ≤ 1.6 × cap. Recompute from the H200 probe before signature. | Under P3, training alone, without early stopping: per base 9 + 3 × 750/590 ≈ 12.8 full-run equivalents of ≈ 3.9 min, i.e. ≈ 0.83 h per 0.8B base. That gives ≈ 9.9 GPU-h if 4B = 5 × 0.8B and ≈ 14.9 GPU-h if 4B = 8 × 0.8B; adding startup (≤ 2) and the probe (≤ 2) gives ≈ 14 and ≈ 19 GPU-h. 40 keeps margin for one 4B repeat on an untested GPU. B would be 25 GPU-h (tighter: against the ≈ 19 GPU-h total at 8 ×, a repeated 4B job of ≈ 6.6 GPU-h would be an author STOP). |

**Prerequisites that change with these choices** (draft §7):
- **P1**: the sweep-1 label freeze signed *and* the train/dev release receipt (P4-LABELS A). Neither is on `main` today.
- **P3**: the P.4 runner unit binds `split_file` (P4-P1SPLIT A) and `LabelBlockSource` on the receipted partition.
- **P8** (R1-T1-HOST-TASL on `main`): now satisfied (`16e0b52c`).
- The rest are unchanged: P2 per-base P.3a records; P4 per-suite logging not applicable to phase 1 (an author tick); P5 the H200 smoke, E0 equivalence, I3 record and SFT probe; P7 `--check-config` clean.

**Draft edits before the final note** (desk work, then a confirmation review):
- §1's base: `4aac5209` → current `main`.
- The `split:` and `split_file:` key lines: P3 only.
- The `labels:` key line: the release receipt and partition sha256.
- §4: add a STOP for a label source that is not the receipted partition.

**Not decided here:** everything in the draft's §9 (evidence phase: P4-TARGET, data composition, RL-gate population,
the sweep-2 release to Track P, the host, the budget). The P.3b exam set's source is EX-SOURCE in the Track P P3 unit's
report (recommended: sweep 1, disclosed, until sweep 2 exists).
