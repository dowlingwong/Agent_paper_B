# Independent L3 review — 27 October 2026

**Verdict: NOT ACCEPTED.** The displayed serial arithmetic is reproducible, but the evidence does not establish that it is the critical path for the adopted full route, or that its parallel prerequisites finish in time. The numerical milestones are an optimistic scenario, not independently verified phase forecasts. This review addresses `proposals/ICML_REPLAN_20261027.md` at paper commit `d5375785429d7304219d05e4dc3374f50d32c604`; no remote state was inspected. L3 remains at STOP pending corrections and review; only the author may adopt scope or dates in PLAN §10.

## Findings

### MAJOR 1 — The proposed full-route path omits and does not schedule required work

The proposal says “Full route” keeps B.6, Track G and C4 (proposal lines 76–80), while its main chain has no dated B.6, C.2, D.1 or Track G milestones (lines 17–25, 57–60). RUNBOOK Phase B lists the second sweep as B.6, Phase C lists aggregation C.2, and D.1 requires LONO for A3/A5/A6 **and** G.5 transfer (RUNBOOK §§5 B, C, D). PLAN §9 requires both held-out benchmark transfer and a second manager; these are not automatically optional under the existing quality bar. The proposed 14-day D.1 has no start/end and cannot be established as finishing before integration: A6 and its pins are outputs of P.5, budgeted through 6 December, so a conservative sequential illustrative 14-day D.1 starting 7 December ends 20 December, not before integration starts 17 December. G.5 and its authorized noise/role decisions can extend it further; sharing TASL-7 with the 4B deployment can also serialize work. A 30 December finish remains conceivable if integration overlaps and all results arrive in time, but is unproved. The second-manager work, aggregation, transfer, C4 and E.2/E.3 need explicit dated dependencies, durations or unknowns, and resource conflicts. A focused scope must identify the required author decision and the specific §9 quality-bar consequence, not assume a waiver.

### MAJOR 2 — Track P and offline-gate prerequisites are not time-bounded

The serial chain puts P.3b on 11–13 November and assumes P.3a and migration succeed in parallel (proposal lines 13, 20, 55). STATUS 26 October records a portal DRYRUN only, plus open Phase 5 design, spec and pin questions; TASL-7 requires author-provided access, reboot, pinned installation and independently reviewed host equivalence (STATUS host and Track P merge entries; `prompts/PORTAL_TRACK_P_RUNBOOK.md` host-change header). Phase 5 is projected ~1 day **plus** reviews/authorization; Phase 6 requires ≥400–500 training-partition labels with committed hash, exam membership/hash, rule hash in PLAN, and the P.3b authorization. There is no dated allocation showing these all complete by 10 November. Likewise, B.3 and B.4 are distinct offline arms, with B.4 on deepthought, whereas the 14–20 November row labels only TASL-7 and Mac (RUNBOOK B.3–B.5; proposal line 21). Account for each arm, review, required author decision and host contention, including the author decision after P.4 before B.7 (`PORTAL_TRACK_P_RUNBOOK.md` Phase 8). The three-day P.3b projection is a run duration, not evidence that its review and author response also fit within three days.

### MAJOR 3 — Label availability and actual resource budget are assumptions, not a verified critical path

The B.2 audit/table allocation is three guessed days (proposal line 19), with no measured aggregate throughput, available CPU allocation, count of eligible edits, storage headroom, or demonstrated process for publishing a stable early training subset. `PORTAL_TRACK_P_RUNBOOK.md` Phase 6 requires an origin/main label artifact and hashes, not merely an audit in progress; `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` phases 8–9 describe audit and final dataset/report. No cited record demonstrates that the 400–500 qualifying labels, split/membership and hashes can all be available by 10 November. State this as a specific unverified implementation and author-gate assumption, including the possible delay to P.3b; do not treat it as an established early-label pipeline. Compute ceilings in proposal lines 65–72 are arithmetically valid, clearly theoretical, and appropriately state utilisation unknown; they are not a workload budget or proof of feasibility. Quantify the known per-stage projected loads where possible, and explicitly mark unknown per-host demand and contention, especially P.3/P.4/P.5, D.1/D.3, second sweep and CPU audits. Do not imply all four deepthought or eight Ada cards are reserved.

### MINOR 1 — Scope and write-up consequences need specificity

The focused option states reduced diversity and coverage (proposal line 79), but should explicitly map deferring the second manager to PLAN §9's second-manager requirement and identify the held-out benchmark, baseline matching, information/action ablations, proof, reproducibility and positioning obligations that remain. Deferring R-B or C4 does not itself waive the required predeclared three-way contrast, action/information ablations, or other quality criteria (PLAN §9 and RUNBOOK D.2). RUNBOOK E.2 also requires a renewed novelty sweep and full-text reading, while E.3 requires disclosure and an anonymised artifact; the 14-day integration row does not enumerate or separately schedule them. No submission readiness follows from a passing implementation check.

### MINOR 2 — Labels and Gantt clarity

`MAC_LOCAL_RUNBOOK.md` L4 gives ~3–5 days for the entire L4, not an isolated G.1 estimate; proposal line 57 should cite it as an upper-end proxy for a broader parallel task, not a direct measured/projected G.1 duration. The Gantt calls P.3b “guess” while the table cites the 2–3-day projection and includes an additional unquantified review/decision; separate those categories. “From 31 December to 16 January” is 16 elapsed days, but only 1–15 January are whole days strictly between 30 December completion and the estimated deadline; state endpoint convention and unknown deadline time zone.

## Independent arithmetic and dependency reconstruction

Using the proposal's **assumed** consecutive inclusive allocations, recomputation gives: readiness 27 Oct–2 Nov (7); B.1 3–7 Nov (5); B.2 8–10 Nov (3); P.3b 11–13 Nov (3); P.4/offline 14–20 Nov (7); B.7 21–22 Nov (2); P.5/P.6 and pilot 23 Nov–6 Dec (14); D.3/D.4 7–16 Dec (10); integration 17–30 Dec (14). Sum 65 days, with every displayed endpoint agreeing exactly. The date differences from 27 October to 16 and 22 January are 81 and 87 days; 81 × 24 = 1,944, and 4 × and 8 × give 7,776 and 15,552. These checks establish arithmetic only. The predecessor network also includes P.3a/migration → P.3b; B.2 + B.3/B.4 + P.4 → B.7; B.7 + RL gate + H.8 → P.5; H.10 → C.3; D.2 committed hash + authorization → D.3; and A6 plus Track G readiness → D.1. The available sources give no defensible within-one-day estimate for the unknown branches, so I cannot agree that this is the full-route critical path within one day per phase.

## Date, gate and authorization checks

Checked 27 October: [ICML future meetings](https://icml.cc/Conferences/FutureMeetings) lists 2027 in South America but no submission dates; [official 2026 dates](https://icml.cc/Conferences/2026/Dates) list 23 January abstract and 28 January full paper (Anywhere on Earth). The 2027 page could not be accessed in this check. Thus 16/22 January 2027 remain local planning estimates, not official deadlines; absence of dates on the checked page does not establish that no announcement exists anywhere.

The proposal correctly labels itself non-adopted, preserves author authorization, B.7 failure fallback, RL and host-equivalence conditions, and states unknown utilization. No unintended decision or evidence authorization was found. In particular, a B.7 fail reports the measured negative and makes C1+C2 carry the paper (RUNBOOK B.7 and failure table); that is not a new permission to run, submit, or silently waive PLAN §9. The outstanding L1 decisions (STATUS 27 October) and all phase-specific STOPs remain binding. No files other than this review were edited; no SSH, model calls or experiments were performed.

## Re-review of `be233a9` — ACCEPTED with stated limitations

The revision resolves the findings for L3 as a **conditional planning proposal**. It explicitly withdraws the claim that the 65-day partial chain is the full-route critical path, supplies a separate illustrative full-route scenario, identifies unverified prerequisites and shared-resource conflicts, and maps scope reductions to PLAN §9. Its guessed dates are not verified predictions, and acceptance does not adopt the scenario, change a gate, establish capacity, or authorize any work. In particular, the document correctly says there is no defensible measured critical-path estimate within one day per phase; the within-one-day agreement below is on the arithmetic of the stated scenario, not a scientific or operational assurance.

Independent inclusive-date reconstruction of the revised scenario:

| Work | Independently computed window | Days | Assessment |
|---|---|---:|---|
| TASL-7 access and equivalence | 27 Oct–2 Nov | 7 | Assumed in parallel with sweep readiness; author access and independent review remain required. |
| P.3a | 3–5 Nov | 3 | Conditional on equivalence, design decisions and authorization; 1 projected run day + 2 guessed review/response days. |
| B.1, B.2 | 3–7 Nov; 8–10 Nov | 5; 3 | Separate deepthought GPU and CPU windows; B.2 throughput is unknown. |
| Label artifact and freezes | 11–12 Nov | 2 | Assumes full B.2 finishes, qualifying split and committed artifacts/PLAN rule are available; author note still required. |
| P.3b and decision | 13–17 Nov | 5 | 3 projected run days + 2 guessed review/decision days, after both P.3a and label prerequisites. |
| B.3, B.4, P.4 | 18–24 Nov | 7 | Parallel only with separate host capacity; includes the prerequisite P.4 review/author decision before B.7 as an assumption. |
| B.7 | 25–26 Nov | 2 | Conditional on completed offline inputs and author decision; failure changes route. |
| P.5/P.6 and C.3 | 27 Nov–10 Dec | 14 | Separate authorizations, RL/C3 gates and H.8/H.10 remain mandatory. |
| B.6 and audits | 27 Nov–8 Dec | 12 | 5 + 3 + 4 assumed days. Requires Track X role decision, fit and authorization; overlaps C.3 and may contend on deepthought, so these dates are not a demonstrated feasible allocation. |
| C.2/C.4 | 11–17 Dec | 7 | D.2 11–13 Dec (3 days) is assumed parallel; actual C.2 and audit demand remains unknown. |
| D.3/D.4 | 18–27 Dec | 10 | D.2 hash and D.3 authorization precede it; 4B resources assumed available. |
| D.1 LONO | 28 Dec–10 Jan | 14 | Serialized after D.3 on TASL-7 and after A6 pins. |
| G.1–G.4 | 27 Oct–14 Nov | 19 | Conditional on host access, noise checks, G.4 role and audit budget; no evidence establishes that this guessed window is achievable. |
| G.5 transfer | 11–17 Jan | 7 | After both G readiness and model pins under the scenario; host and allocation unknown. |
| Integration E.1–E.3 | 18–31 Jan | 14 | Waits for G.5 in this conservative serial illustration, includes novelty and disclosure; 31 Jan is 15 elapsed days after the estimated 16 Jan abstract date. |

The separate partial-chain dates and 65-day sum remain arithmetically correct as originally checked. Neither schedule bounds Track X completion: the full-route B.6 start depends on its finalist/role decision, so the proposed 27 November start remains explicitly conditional. The B.6/C.3 overlap is likewise a flagged unresolved conflict, not evidence that simultaneous deepthought runs are authorized or fit. D.1 and G.5 are sequentially illustrated, though other permitted overlaps could change the finish. The 15-day figure is relative to an **unofficial** abstract-date estimate; early abstract drafting, final paper timing, available GPU-hours and review turnaround are not established. The theoretical capacity ceilings and unknown utilisation remain appropriately qualified.

Corrections accepted: Track P migration, P.3a, split/hash/rule gates, B.4's host and P.4 review are now named; G.1's 5-day value is a guessed proxy for the broader L4 estimate; B.6, C.2, C.4, D.1, G.5 and E.2/E.3 now appear in the illustrative route. No unintended decision or authorization was identified. Re-review used local records only; no SSH, remote operation, model call or experiment was performed.
