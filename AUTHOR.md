# Waiting on the author — 26 Nov 2026, about 23:30 CET (`main` `ef06a65c`)

Answered on 26 Nov: D1 (rows (f)(g), TIMEOUT A, the three additions) → published `95249de3`. D2 (this tmux session
coordinates; Codex does not push `main`; `canon/README.md` rule 1 stands, so no row is needed) → recorded. D3 (P.4 on Ada:
survey first, then a launcher outside HTCondor) → tasks `compute/20261126-01` and `local/20261126-06` unit 1 are in force.
D4 (start order) → see the agents row. **G.5 signed** ("签 G.5：S1–S14 按推荐…+ 推 main") → row R1-G5-SIGNATURE, `ef06a65c`.

| Item | Recommendation | The reply that decides | Blocks |
|---|---|---|---|
| **Compute agent did not start**: `Model unavailable: deepseek/deepseek-v4.1-flash` (23:22) | Restart Compute only, with a model OpenCode lists, for example `python3 tools/start_workers.py --role compute --compute-model opencode/deepseek-v4.1-flash` (the same model through the OpenCode provider). Choose `deepseek/deepseek-v4-pro` instead if you want the stronger model. Provider and cost are your choice | run the command | Compute's whole queue: kit c1 (launch by 30 Nov 20:33), the REL copy for G.5, the survey for P.4 |
| Roles row: design agent; E-INT census choice (Codex commits on `main`, no PLAN row) | Defer until G.5 is signed; then one row for the roles (coordinator, writer, design, local, compute) and one for the census | — | Paper C; design-agent tasks |
| S9: how an expansion node joins the frozen eight-node split | Sheet due from the local worker (`local/20261126-04`) | — | The G.5 addendum for expansion nodes |
| Uncommitted local edits in the Mac checkout (`canon/*`, SOUL files, runbook §7, READMEs) | Say whose they are; if they should stand, they go on a branch and through review. `main` now changes `canon/` too | one sentence | Nothing yet; a pull will conflict |
| Signatures to come | screening-measurement note; D.3 pre-declaration revision 4; P.4 phase-1 note (revised to R1-HOST-FREE) | — | D.3; P.4 |
| R1-D3-CHOICES (1) quotes the wrong T5 figures (fresh T5 review, m1) | One added row correcting the figure. "+0.47 to +1.84 δ_n" are the oracle-prior figures for digits_on at W = 20; A2's own are +1.38 / +3.27 δ_n in that cell (+1.4–5.7 feasible, +3.3–10.0 oracle across the four cells). The decision of (1) is unchanged | "签 D3-CHOICES 更正" | Nothing; the paper's figure is wrong until then |
