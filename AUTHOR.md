# Waiting on the author — 26 Nov 2026, about 23:00 CET (`main` `95249de3`)

Answered on 26 Nov: D1 (rows (f)(g), TIMEOUT A, the three additions) → published `95249de3`. D2 (this tmux session
coordinates; Codex does not push `main`; `canon/README.md` rule 1 stands, so no row is needed) → recorded. D3 (P.4 on Ada:
survey first, then a launcher outside HTCondor) → tasks `compute/20261126-01` and `local/20261126-06` unit 1 are in force.
D4 (start order) → see the last row.

| Item | Recommendation | The reply that decides | Blocks |
|---|---|---|---|
| **G.5 signature, S1–S14** (`sheets/G5_SIGNING_SHEET_S1_S14_20261126.md`) | Every line as the draft recommends, except S6: freeze date 2027-12-31 (a technical bound under R1-STEP-ORDER instead of 18 Dec) and S4: the CUDA-IPC acceptance line (no C12 record exists) | "签 G.5：S1–S14 按推荐（S6 = 2027-12-31，S4 = 验收行）+ 推 main" | The T1 labels (≈217 GPU-h). The note also needs the REL-T1-G1B copy and the final render first (compute, local) |
| **Start the agents**, in the order of D4 | compute agent first (kit c1 is the first item of its queue), then the local worker, then the writer | — (start them; this needs no reply) | Every task under `tasks/` |
| Roles row: design agent; E-INT census choice (Codex commits on `main`, no PLAN row) | Defer until G.5 is signed; then one row for the roles (coordinator, writer, design, local, compute) and one for the census | — | Paper C; design-agent tasks |
| S9: how an expansion node joins the frozen eight-node split | Sheet due from the local worker (`local/20261126-04`) | — | The G.5 addendum for expansion nodes |
| Uncommitted local edits in the Mac checkout (`canon/*`, SOUL files, runbook §7, READMEs) | Say whose they are; if they should stand, they go on a branch and through review. `main` now changes `canon/` too | one sentence | Nothing yet; a pull will conflict |
| Signatures to come | screening-measurement note; D.3 pre-declaration revision 4; P.4 phase-1 note (revised to R1-HOST-FREE) | — | D.3; P.4 |
