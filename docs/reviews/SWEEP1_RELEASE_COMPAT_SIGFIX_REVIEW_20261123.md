# Independent review — R1-SWEEP1-RELEASE-COMPAT follow-up signature fix (23 November 2026)

Reviewer: `reviewer-signature-fix`, independent and read-only. Reviewed branch
**`rel-sweep1-compat-20261122` @ `18550a3f`** (pushed; `origin/main` = `1402f466`, unchanged; branch contains
`1402f466`). The fix commit is `c6cf9aa3..18550a3f` and touches **only `r1/c3/audit.py`** (`+9/−2`). Method: read
the branch objects through `git show`/`git grep`/`git diff` without checking out or editing the branch; no worktree,
job or sealed data was touched. The only write is this file. Local environment has no pytest/venv, so I did not
rerun the suites (deepthought and `r1/tests` belong to the lead); test evidence below is quoted from the lead, and
the failure mechanism was independently traced in the tests and code. Review date 2026-11-23 (Europe/Berlin).

## Bottom line

**ACCEPTED.** The fix is minimal and does exactly what it claims: on the default path the call signatures are once
again identical to pre-branch `1402f466`, and the sweep-1 release path still receives the v2 compatibility builder.
The only new `replay_builder=` keyword is now reached when a builder is actually supplied, so the monkeypatched
`lambda *args` / `def verify(...)` seams (which reject keywords) no longer break. Residuals are non-blocking; the
one open gate is the lead's full `r1/tests` rerun, which this review does not substitute for.

## What the fix does, and why it is needed

Before the fix, both `audit.py` call sites always forwarded the new optional hook:

```python
# pre-fix (regressed c6cf9aa3 and earlier branch commits)
_verify_replay(table, paper_root, index, classification, replay_builder=replay_builder)   # audit.py:918
plan, binding = evidence_plan(..., source, replay_builder=replay_builder)                 # audit.py:1369
```

`replay_builder` is `None` on every non-release path, so this was pure argument-shape drift. Any monkeypatched
replacement declared as `lambda *args` / `lambda *a` (or a `def verify(table, block, paper_root, index,
classification, source="sweep1")` stub) raises `TypeError: unexpected keyword argument 'replay_builder'` — which is
the reported 16 new full-`r1/tests` failures, all confined to the three files the lead re-ran. The affected patches
are reached through `verify_evidence_completion` (guards, sweep-2 audit and sweep-2 D4B tests, including the
helper-built worlds `_completion_world`/`_verify_world` and the 9-case D4B refusal matrix) and through
`evidence_plan`'s default replay (guards test patching `_verify_replay`). Static tracing confirms every such patch
site is a keyword-intolerant mock.

The fix guards both call sites (`audit.py:918-921`, `:1369-1373`): `None` → the exact pre-branch positional call;
non-`None` → the extra keyword. Nothing else is changed; the release wiring in `release_checks.sweep1_integrity`
(`release_checks.py:58-60`, `replay_builder=sweep1_compat.rebuild_v2_table`) is untouched, as is the
`_sweep1_compat_published` guard and the sealed-commit pin.

## Independent verification

| Check | Result |
|---|---|
| Fix scope | `git diff --name-status c6cf9aa3..18550a3f` = `M r1/c3/audit.py` only; no tests, docs, `release.py`, `PUBLISHED_PATHS` or PLAN edits. Commit trailer is the repo's standard `AI-assisted:` line. |
| Default path = pre-branch | AST comparison of `1402f466` vs `18550a3f`: every default-path call shape exists post-fix — `_verify_replay(table, paper_root, index, classification)` (`:919`), `_verify_replay(table, paper_root, index, None)` (`:950`), `evidence_plan(table, paper_root, index, classification, source)` (`:1231`, `:1370`) — with no keyword, byte-for-byte the pre-branch calls; no pre-branch default call is lost or changed. |
| Release path preserved | The only keyword-bearing calls are the two guarded `else` branches; `sweep1_integrity` still passes `sweep1_compat.rebuild_v2_table`, so `_verify_replay`'s compat branch (builder subprocess + provenance normalisation + classification-sidecar re-check) still runs. Unchanged from the accepted round-2 unit. |
| Sweep-2 path untouched | `_sweep2_plan` still calls `_verify_replay(..., None)` with no builder; `sweep2_integrity` still calls `verify_evidence_completion(..., source="sweep2")` with no builder; the early sweep-2 return in `evidence_plan` is unchanged. |
| Other callers | Production callers are only `r1/c3/offline_eval.py:125` (default, no builder) and `release_checks.sweep1_integrity`/`sweep2_integrity`; no other `r1/` caller passes a builder. Adding a defaulted 6th/7th parameter is backward-compatible for all of them. |
| No unintended test edits | The two changed/added test files (`test_c3_release.py`, `test_sweep1_release_compat.py`) come from earlier commits `b2b7489a`/`5c5e3bc7e`/`72e65a8e9`/`e629472cc`; the fix commit adds no test-id churn. The `verify` stub's `replay_builder=None` parameter was already correct for the release path. |
| No main push | `git ls-remote`: `refs/heads/main` = `1402f466`, `refs/heads/rel-sweep1-compat-20261122` = `18550a3f`; `1402f466` is an ancestor of the branch. The fix is pushed on the branch only. |
| Syntax/whitespace | Extracted post-fix `audit.py` compiles (`py_compile`); `git show --check 18550a3f` clean. |
| Targeted tests | Lead's deepthought run on the three previously failing files (`test_c3_evidence_guards.py`, `test_c3_sweep2_audit.py`, `test_c3_sweep2_d4b.py`): **131 passed**, consistent with the mechanism above. I did not duplicate this run (no local pytest; deepthought is the lead's environment). |

## Residuals (non-blocking)

1. **Full-suite gate is open (the one acceptance condition).** The first full branch run had 16 new failures plus
   one transient extra failure, `test_c3_control_dryrun_end_to_end`, which passes standalone on both branch and
   baseline; the lead's full `r1/tests` rerun is in progress. This review accepts the *fix*; final branch
   push/merge should be gated on that full-suite result being green against baseline, with the transient recorded
   as environmental/flaky rather than silently dropped.
2. **No direct regression test for the default-path call shape.** The previously failing monkeypatch tests now act
   as implicit coverage (they fail again if a keyword is reintroduced on the default path), but a three-line explicit
   test — patch `_verify_replay`/`evidence_plan` with a no-keyword recorder and assert the call shape — would make
   the invariant intentional. Optional.
3. **`replay_builder` is silently ignored for `source='sweep2'`.** `evidence_plan` returns `_sweep2_plan` before the
   guarded call and `verify_evidence_completion` forwards the hook unconditionally; a caller passing a builder with
   sweep-2 would get no effect rather than a refusal. No current caller does this; fail-closed rejection would be
   cleaner but is out of scope for the fix.
4. **Record/runbook prose does not mention this commit.** The branch report's "default behaviour unchanged" sentence
   is true again as of `18550a3f`, but it does not record the sigfix commit or the full-suite evidence. A one-line
   provenance note in the report/runbook before the merge would keep the reviewed-unit record coherent (docs-only).
5. **Process note.** Round 2 was accepted on file-scoped 50-test evidence; the full `r1/tests` was not run then, which
   is how this regression reached a pushed branch. The release acceptance record should name the full-suite command
   and result, not only the new/changed files.

Nothing in the residuals changes the code assessment; the fix itself requires no further change.

VERDICT: ACCEPTED
