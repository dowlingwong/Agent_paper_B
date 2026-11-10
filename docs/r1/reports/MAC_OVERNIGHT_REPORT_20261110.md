# Mac overnight report — 9/10 November 2026

**AI-assisted (Claude, Mac-local agent).** Runbook `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` (`docs/runbooks-09nov` @ `421a93d21`). Start message carried lines A1, A2 and A3 of its §0.4. Desktop work only: no SSH, no server action, no `approved: true`, no sweep-2 table or label seed read.

## How the night went

- The previous session's workspace VM had filled its disk; its work arrived as patches (`Claude outputs/overnight_20261109/`). This session rebuilt every branch from git bundles of the Mac repository in a cloud workspace, worked and reviewed there, and delivered the branches back as bundles. Temporary files went to `/tmp`, nothing to `$HOME`; no dry-run test that copies the harness was run.
- The cloud workspace could not push (no GitHub access was granted), so **nothing is pushed**. Fetch the bundles and push from the Mac (section "Delivery").
- The work stopped at about 03:15 on 9 Nov when the account's weekly usage limit was reached, and resumed on 10 Nov at 10:18 after your "continue". The 08:30 report deadline was missed for that reason. Everything below was finished and reviewed after the restart unless dated otherwise.
- Every unit was reviewed by a freshly spawned independent agent (goal, runbook, inputs and outputs, not the author's conclusions) until it wrote *accepted*; fixes were made by the executing side. The full review rounds are committed next to each unit.

## Task 1 — B1 STOP (A1 given)

| Piece | Branch @ commit | Review |
|---|---|---|
| Code checks D5/D6 (`reports/B1_STOP_CODE_CHECKS_20261109.md`): no engineering defect in the anchor path; the first valid trial is kept unaudited, so every audited increment is measured against an incumbent that already holds it | `mac-b1-diag-20261109-c` @ `7b08c2ad` | accepted, round 2 (`reviews/B1_DIAG_REVIEW_20261109.md`) |
| Diagnosis script D0–D4, D7, D8 for the experiment agent, read-only, pinned to the accepted descriptive capture's state SHA and the exact duplicate-rate interval; SHA-256 `82140eea68516d46f26100c2df14e7e83e6b747a9a205a6daf0608ff0ee92f93` (script commit `81c81289`) | same | same |
| Hand-off `proposals/B1_DIAGNOSIS_HANDOFF_20261109.md` (exact command, what to send back) | same | same |
| Analysis script → plan §3 tables and class E / REVIEW / D / P / UNCLASSIFIED; R4 only for D with H1 supported and D7 PASS | same | same |
| R4 fix: `anchor_gate` ordering STOP removed, comparison kept as a descriptive field, 7B duplicate-rate STOP unchanged (`fb57c6a4`); `exam_b1_v2.json` `paper_commit` re-pinned to `fb57c6a4` (`4542360e`); PLAN §10 row `R1-EXAM-B1-ANCHOR-R4` (cites line A1 by location, not copied); RUNBOOK X.3 and PORTAL_EXAM_RUNBOOK Phase 5 notes; appendix draft `reports/B1_GATE_AMENDMENT_DRAFT_20261109.md` | `mac-b1-r4-20261109` | accepted, rounds 1–3 |
| Restart hand-off `proposals/B1_RESTART_HANDOFF_20261109.md`: armed only for class D with H1 and D7 PASS; run HEAD = one prose-only note commit on `ops-b1-restart-<date>`; Track P marker transition with the reviewed `retire`; fresh run ID and output tree | `mac-b1-r4-20261109` @ **`4ddc820e49bfc4f60f0257e98591177241b77471`** (the reviewed restart base) | accepted, rounds 4–6 (`reviews/B1_R4_REVIEW_20261109.md`) |

Not done tonight, by design: step 3's diagnosis report needs the experiment agent's capture; no `mac-b1-fix` branch (step 1 found no engineering defect). **Next:** push both branches; the experiment agent runs the diagnosis hand-off; the capture is analysed and the report reviewed; if it is class D with H1 and D7 PASS, the restart hand-off applies without a further message from you.

## Task 2 — HoreKa port kit and diff support (M10 steps 0–1)

- Harness `r1-local-trackg-20261109` @ `76bc49f2` (on `a3fedbb`; 26 new files, no existing file changed, B1 pin untouched). Paper `mac-trackg-20261109` @ `f56f7f35` (checklist `prompts/TRACKG_PORT_CHECKLIST.md`, hand-off `reports/M10_PORTKIT_HANDOFF_20261109.md`).
- Built: strict `trackg_node/v1` spec (fixed step/token budget, wall-clock keys and flags refused), outcome classifier (ok / divergent / infrastructure_failure, never mixed), per-run runner (GPU by UUID, required CPU/memory caps, timeout 3× measured, process-group and session cleanup, determinism shim with a record), validation-only selection, declared-edit manifest, smoke loop; G.2 diff support through the existing scope validator with inert detection, duplicates decided by resulting code state, provenance, `manager_proposal/v2-diff`.
- T0 byte identity: a `manager_proposal/v1` campaign at `a3fedbb` and at HEAD compared byte for byte (worker artifacts unnormalised; only timestamps, event ids and latencies normalised in the two JSONL files) plus a structural test; mutation-checked by the reviewer.
- Tests: `tests/trackg` 161 passed; full harness suite and the 16 harness-importing paper files have the same failure sets as at the base.
- Review: accepted, round 3 (`reviews/M10_PORTKIT_REVIEW_20261109.md`).
- **For the HoreKa agent:** harness `76bc49f2`, paper `f56f7f35`, once pushed. The local copy of `origin/r1` was stale, so the harness branch starts at `a3fedbb` (a descendant); the commits only add files and rebase cleanly (set `TRACKG_T0_BASE_COMMIT` after a rebase). v2-diff is not yet wired into a manager or campaign (later M10 steps).

## Task 3 — M3 code completion, and M4 parts not shared with M3 (A2 given)

- **M3**: `mac-m3-20261109` @ `ec6e30a9` (base: the 8 Nov review branches plus `mac-m3-hup-source`, `-cache-copy`, `-case-binding` merged without conflict). Done in code with synthetic and opt-in kernel tests: bootstrap created by one raw `clone3(CLONE_PIDFD | CLONE_INTO_CGROUP)` (no fork, all waits and kills via pidfd/cgroup); PID 1 in the namespace is a trusted sentinel so withdrawn seccomp notifications are counted by a bounded drain (any withdrawn or pending attempt is a STOP); HUP/completion ordering; non-numerical 16-case preflight that stops at the first model fit, bound to the hashed runtime closure. Tests: regular set 196 passed with the same 7 sklearn-version failures as the base; 53 kernel opt-in tests passed as root and unprivileged. Review: accepted, round 2 (`reviews/MAC_M3_REVIEW_20261109.md`). Not done: the preflight is not wired into `c3_env_replay.run`; site qualification (kernel ≥ 5.9, delegation, closure from the batch venv, real-cache run) is a later host step.
- **M4 (non-shared parts)**: `mac-m4-20261109` @ `5cd32efc`: two-GPU llama-server serving (exact GPU-/MIG- UUIDs, conflicting flags and env refused, offload check per start and per load, CPU fallback anywhere a STOP), single-GPU path byte-identical to the base. Harness `r1-local-m4-20261109` @ `561f71f0` = `a3fedbb` + a test-only defaults check (llamacpp bodies differ only by the PLAN-required `cache_prompt:false`). Review: accepted, round 3 (`reviews/MAC_M4_REVIEW_20261109.md`). **Keep apart from B1:** `llama_server_instance.py` is a B1 protected path, so this must not enter `mac-b1-r4-20261109` or B1's checkout, and B1's harness stays `a3fedbb`. Remaining M4 steps wait for M3 integration (`c3_label_sweep.py`) or need `d10b05b7` (DTQ tool).

## Task 4 — M11 D8 aggregate gate and the confirmation draft

- `mac-m11-d8-20261109` @ `83a12b44`: `r1/c3/gate.py` (SHA-256 `a078cf1f862d23e6dcf10fd99135f0840afcd243bb66374645c238ab46006acd`, commit `050cb9f0`) with IQM/PoI inlined, imports and NumPy pinned, T0 set and suites pinned, Holm ranking label-invariant; known-answer synthetic tests; every sweep-2 reader (incl. `env.label_rows`, `audit._verify_replay`, `dataset.build_from_sweep`) refuses before opening a table without the exact `R1-BX-D8-CONFIRM` row.
- Draft row `proposals/R1_BX_D8_CONFIRM_DRAFT_20261109.md` names the commit, SHA and blob and lists the 13 conventions you would freeze; checked against the real parser. Not committed as an author row.
- Review: accepted, round 3 (`reviews/M11_D8_GATE_REVIEW_20261109.md`). Questions Q1–Q5 must be answered before you paste the row; an answer that changes `gate.py` needs a redraft and re-review.

## Task 5 — W2 budget fields from worker runs (A3 given)

- `mac-w2-budget-20261109` @ `0b62fb03`: `budget_frac_left` and the prompt's budget line count worker runs actually consumed (`features.row_worker_runs`: skips and precheck rejections 0, verify +2r, Track S ghost/ctrl_only 1); `NodeContext.trial_budget` for skipping arms (unset, so bytes unchanged); `FEATURIZER_VERSION` → `c3_features/v3`; read-only check script for real ledgers.
- Identity: a golden file generated with the base commit's own code (`a15300ca`) matches feature hashes, full prompt text and meta on execute-all campaigns; the reviewer also compared 1,068 views against the base.
- Review: accepted, round 3 (`reviews/W2_BUDGET_FIELDS_REVIEW_20261109.md`). The real sweep-1 ledgers are not checked yet (Q6).

## Delivery

Bundles in `Claude outputs/overnight_20261109/out/` on the Mac (`paper_overnight_final.bundle`, `harness_overnight_final.bundle`; the earlier `*_interim.bundle` files are superseded and can go to `_to_delete/`). From `~/Documents/agent_paper_B`:

    git fetch "Claude outputs/overnight_20261109/out/paper_overnight_final.bundle" \
      'refs/heads/*:refs/heads/overnight/*'
    git push origin overnight/mac-b1-diag-20261109-c:mac-b1-diag-20261109-c \
      overnight/mac-b1-r4-20261109:mac-b1-r4-20261109 ...   # one pair per branch below

Paper branches: `mac-b1-diag-20261109-c`, `mac-b1-r4-20261109`, `mac-trackg-20261109`, `mac-m3-20261109`, `mac-m4-20261109`, `mac-m11-d8-20261109`, `mac-w2-budget-20261109`, `mac-overnight-report-20261109`. Harness branches (fetch inside an `autoresearch_harness` clone): `r1-local-trackg-20261109`, `r1-local-m4-20261109`. Do not push into `mac-int-20261107` until you decide the integration order; `mac-b1-r4-20261109` stays unmerged until a qualifying diagnosis.

## Questions

`reports/MAC_OVERNIGHT_QUESTIONS_20261110.md` (Q1–Q10, each with options, recommendation and a paste-ready line).
