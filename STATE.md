# State — 26 Nov 2026, 20:30Z, `main` at `4cb92b70`

**Read `HANDOVER.md` first.** The interim coordinator (a chat session) has stopped its hourly rounds (paused 16:11Z).

| Role | Working on | Blocked on |
|---|---|---|
| cluster, experiment (on `main`; one `compute` agent in the draft row R1-AGENT-COMPUTE) | Nothing picked up from this branch yet. Queue: kit c1 record; torch tests of the host-config fill; houseprice re-check after the fix; D.3 runner G1 and audit G6 | The agents have not been started |
| local | Nothing picked up yet. Queue: houseprice cpuset fix; screening smoke STOP; D.3 pre-declaration revision 4; S9 | — |
| writer | Nothing picked up yet. Queue: manuscript restructure after R1-ALIGN-OUTCOME | — |
| design (new on `main`, from Codex; no PLAN row) | Next-phase runbook (draft for review) | The author's review |
| coordinator | Handover written. Owed: the G.5 signing sheet; the expansion note publication (after c1) | The author: rows (f), (g); who coordinates next |

**Rows of 26 Nov (f) and (g) are drafts on branch `coordinator-rows-fg-20261126`, not on `main`.** Until they are,
the dated rules on `main` apply: expansion G.1b cutoff 2 Dec 00:00 CET (latest starts at 1.5×: Titanic 30 Nov
20:33 CET, Forest Cover 30 Nov 23:31, MetaMaze 1 Dec 13:25, ETTh1 1 Dec 21:36); T1 release by 17 Dec; arms-frozen
record by 20 Dec.

`main` moved from `53b72f1d` to `4cb92b70` by two direct commits (Codex): next-phase runbook, design agent, indexes,
hygiene audit, a rewritten Paper C plan view. Documentation only; PLAN unchanged; not reviewed.

Open STOPs: (1) houseprice TASL-2 cpuset check, procedure defect (`main-t1-g5-prep-20261126`, report §4);
(2) screening-measurement engineering smoke, `determinism_unverifiable openml_breast_w c5 seed 999`
(`screen-measure-prep-20261126`); (3) P.4 T4, tokenizer staging cannot be exercised with the CPU image
(`trackp-p4-cluster-20261125` `8a9d48a1`); (4) P.4 T6 and T1, no H200 in the pool.
