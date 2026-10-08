# Independent review prompt — run in a NEW session after the fix queue

Copy everything below the line into a fresh agent session. It has not seen the
implementation conversation. It reviews; it does not implement.

---

You are an independent reviewer for the source repository,
branch `local-work-2026-09-26`. You did not write this code. **Do not fix
anything.** Produce findings only. Do not trust the implementer's reports; verify
against the code and the outputs you produce yourself.

**Specification:** `docs/paper_split/B_CONTROLLER_DESIGN_20260927.md` and
`FIX_QUEUE_20260927.md`. **Implementer's report:** `docs/paper_split/FIX_REPORT_20260927.md`.
Diff range: from `9494e0bc` to HEAD.

The last review round missed defects because it relied on grep patterns and
function-level tests. Use the targeted checks below. For each one, write down
what you ran and what you observed.

1. **Hidden gates.** Parse `experiment_scaffold/src/causal_branch/control/**`
   (AST). List every function or method that returns an action, regime, score or
   allocation. Check that none of them reads a replay allowance
   (`p`, `p_path`, `allowance`, `replay_*`) directly, through attributes or
   through imports. Trace data flow, not just names.
2. **Comparator identity.** Run every controller on at least three fixture
   worlds with the same inputs. Report the pairwise decision-agreement rate. Flag
   any pair that agrees on 100% of roots in every world. Read the code to confirm
   that the proposed controller uses `V̂_wait(H₁)` from the specified continuation
   target and that the BAVAR-inspired scheduler is context-dependent.
3. **Unused code.** Run the single evaluation entrypoint end-to-end on a fixture
   with coverage. List every public function in `replay_validity`, `allocator`,
   `timing` and `evaluate_tree` that is not executed. For each one, say whether it
   should be reachable.
4. **Leakage.** Try to make a controller read a leaf outcome, hidden data or
   checkpoint-2 information at checkpoint 1 through `DecisionView`, and report
   whether it is blocked. Check that folds are split by template family, with
   descendants and repetitions kept together.
5. **Max-bias.** Independently simulate a null world (true A₂ ≡ 0, noisy
   leaves). Compare the mean of the implemented `V̂_wait` with a naive
   `max(Â₂, 0)` target.
6. **Budget.** Write your own random tests for the allocator: realized calls
   ≤ floor(.25·N), ≤ 1 per root, deterministic ties, unspent capacity retained,
   no phase-2 call for unreached, verified or infeasible roots.
7. **Confidence radius and N1.**
   - Check the Hoeffding width against the contrast range.
   - Read `N1_DISPLACEMENT.md` as a proof and say whether the derived m is
     correct for the implemented allocator.
   - Construct your own single-root perturbation that maximizes the number of
     changed roots.
   - Check that the p-grid report states its interference scope.
8. **Evaluation semantics.**
   - The allocator is re-run inside each bootstrap draw.
   - Policy value is taken over all original roots.
   - Intervals are simultaneous.
   - The readings (supported / practically large / equivalence / not practically
     useful / inconclusive) match design §6.
   - Null diagnostics are present.
9. **Task realism.**
   - Re-run the F9 checks yourself with the scripted behaviours.
   - Confirm the thresholds were frozen before the run (timestamps or commit order).
   - Look for signs the task was tuned toward passing.
   - Confirm the hidden evaluation never enters the workspace.
10. **Live-run safety.**
    - `run_screen.py --mode live` refuses without qualification and authorization.
    - Caps are enforced before dispatch.
    - `bind_runtime_artifacts.py --dry-run` works.
    - No path launches a model.
11. **A supplement.** Build `make supplement-a` yourself and scan the ZIP
    independently for identity leaks (paths, username, author name,
    acknowledgements, git metadata, emails). Confirm the size ≤ 100 MB.
12. **Manuscript B.**
    - Claims match design §8: no optimality, no new-method claim, no unsupported
      null interpretation, and N1 described as qualifying conclusions.
    - Check every newly added citation at its source (network read allowed):
      BAVAR / preprints.org 202608.2057, Calibrate-Then-Act / arXiv 2602.16699,
      Longstaff & Schwartz 2001, and the fitted-Q reference.
    - There is no "reported to" placeholder text.
13. **Checks.** Re-run the full check set from FIX_QUEUE F12 yourself and report
    each exit status.

Write `docs/paper_split/INDEPENDENT_REVIEW_20260927.md` with one finding per line:
`ID | blocker/major/minor/none | file:line | finding | evidence (command + observed output) | required fix`.
Then give a verdict:
- **B design-ready:** yes / no;
- **task realism:** pass / fail;
- **ready to request Ada qualification authorization:** yes / no.

Do not edit any other file. Do not commit anything except the review file.
Do not merge, push, run models or contact anyone.
