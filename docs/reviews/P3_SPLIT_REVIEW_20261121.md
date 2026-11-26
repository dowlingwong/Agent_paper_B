Reviewed base: published `main` `f6baf12c`; accepted at `39ecfa492415ec7c15732a805912143c4f88a121` (split file `r1/c3/splits/c3_p3_split_v1.json` sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`)

# Independent review record — the P3 split file (PRE-SPLIT A)

**Unit.** On `mac-p3-split-20261121`: `r1/c3/p3_split.py` (generator, `load`, `assignment`, `split_of`), the committed split file
`r1/c3/splits/c3_p3_split_v1.json`, `r1/tests/test_p3_split.py` and `docs/r1/reports/p3_split_20261121/P3_SPLIT_20261121.md`.
Authority: the signed preregistration (R1-SWEEP2-PREREG) PRE-SPLIT A and §9; the queue of 21 Nov 2026, item 1.

**Process.** One independent reviewer for both rounds, read-only, scratch under `/tmp/rev_p3/` moved to its `_to_delete/`.
It recomputed both tiers' assignment and the disclosure figures from seeds and salts only, without the module, and read
no label or evaluation value. Round 1 accepted with minor findings m1–m8; all were fixed in `39ecfa49` without changing the
split file's bytes, and round 2 (same reviewer) confirmed them.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `bc58da88` | ACCEPTED (minors m1–m8) |
| 2 | `39ecfa49` | CONFIRMED |

**Open items.** None for the unit. Carried condition (m1): the G.5 amendment that adds `autoresearch_fixedtokens` must adopt instance seeds 5101–5112 and G5-SPLIT to use this file; otherwise that node is not supplied.

## Round 1 (`bc58da88`)

> Verdict: ACCEPTED
>
> I found no blocking or major issues. Everything I checked matches the preregistration, and below are only minor fixes.
>
> **What I recomputed myself (from seeds and salts only, using `git show bc58da88:…`, not the module):**
> - **T0:** for each of the 8 nodes in `gate.T0_NODES`, I used seeds 100+10k+(Σord mod 7) for k=0..17 and ids `<node>__s<seed>`, ordered by sha256("c3_p3_split/v1:"+id), split 9/3/6. All 8 nodes match the file exactly. For example, digits_mlp runs 104…274 and openml_wdbc / openml_credit_approval run 100…270.
> - **T1:** for each of the 8 nodes, I used seeds 5101–5112 (matching the G.5 draft's "5100 + k"), ordered by sha256("c3_t1_split/v1:<node>:<seed>"), split 6/2/4. All match.
> - **File layout:** the node sets match; ids are distinct within and across tiers; there is no zero padding.
> - **Pin:** the committed file's sha256 is `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`, which equals `P3_SPLIT_SHA256` and the report.
> - **Disclosure figures:** I recomputed how many of each node's 9 P3 test instances were in `trackp_sft/v1`'s training set (salt from `r1/scripts/configs/trackp_sft.json`; 3 test, 3 val, 12 train) and got 5, 7, 6, 5, 6, 5, 6, 5. This matches the report and PRE-SPLIT B.
> - **Output is deterministic:** `sort_keys`, `indent=1`, `ensure_ascii`, lists kept in hash order.
> - **Fails closed:** `load` checks the sha256 and then byte-for-byte equality with `render(build())`. Even with a different `sha256=` it still demands the generator's output. `split_of` refuses unknown ids.
> - **Tests:** 8 passed with `AR_HARNESS_ROOT` set, so the `e1b_collect` seed test ran and was not skipped.
>
> **Item (3), carrying `autoresearch_fixedtokens`:** carrying it is correct and harmless. It does not conflict with the G.5 note.
> - Carrying a node enrols nothing; enrolment is governed by PRE-T1 A (only nodes whose train/dev labels were released).
> - Leaving it out would be worse. The G.5 draft (lines 359–362) says leave-one-suite-out needs a third-suite node. If autoresearch joined later, a second split file would be needed, which would hit §6 "a split that differs from the signed split file" after the freeze.
> - "The signed note records the resulting assignment and its sha256" (G.5 §2.7) is satisfied: the G.5 note cites this file's sha256, and its seven nodes are a subset of the file.
> - The remaining risk is m1.
>
> **Item (4), instance ids:** the gate treats ids as opaque strings and checks that they don't overlap. The sweep-2 report folders name instances `<node>__s<seed>` (e.g. `openml_climate__s264`, `openml_credit_approval__s200`, `tabular_mlp__s112`), and these are in the universe. The job record names `e1b_collect.py` as the seed source. I opened no label or evaluation files.
>
> **Blocking:** none.
>
> **Major:** none.
>
> **Minor:**
> - **m1** — `docs/r1/reports/p3_split_20261121/P3_SPLIT_20261121.md:14-15` and `r1/c3/p3_split.py:39-41`. The autoresearch entries silently assume that the future G.5 amendment for this node (G.5 draft line 419) will keep seeds 5101–5112 and G5-SPLIT. If the amendment chose a different seed block, its instances would be refused and the frozen file would no longer fit. **Fix:** state this assumption in the report and the module comment, and record it as a condition for whoever drafts that amendment ("must adopt instance seeds 5101–5112 and G5-SPLIT to use this file; otherwise the node is not supplied").
> - **m2** — `r1/c3/p3_split.py:19`. The docstring says unknown instances are "refused by `load` users (`assignment`)", but `split_of` refuses them; `assignment` does not. **Fix:** change it to "refused by `split_of`".
> - **m3** — `r1/c3/p3_split.py:123-140`. `assignment()` and `split_of()` accept any dict, so a caller who parses the JSON directly skips the pin. **Fix:** let `split_of` call `load()` by default when no assignment is passed (e.g. `split_of(inst, assign=None)`), or have `assignment` reject input whose `schema` isn't `SCHEMA`. At minimum, document that callers must go through `load`.
> - **m4** — `r1/c3/p3_split.py:69`. The count check is an `assert`, which `python -O` strips. **Fix:** raise `SplitError` instead.
> - **m5** — `r1/tests/test_p3_split.py:65`. `sys.path.insert` is never undone. **Fix:** use `monkeypatch.syspath_prepend`.
> - **m6** — `r1/tests/test_p3_split.py:29`. The comment "pinned sha given for altered bytes" is wrong: the test passes the altered file's own sha. **Fix:** change it to "matching sha supplied for altered bytes → generator-equality check".
> - **m7** — Tests. Nothing tests the report's disclosure figures (5,7,6,5,6,5,6,5), and nothing pins a literal per-node assignment. **Fix:** add a test that recomputes the `trackp_sft/v1` training ∩ P3 test overlap per node with `sft_data.assign_splits` and its default config. Optionally hard-code a few known ids, e.g. `digits_mlp__s204` → test, `digits_mlp__s214` → dev.
> - **m8** — `P3_SPLIT_20261121.md:16`. The sweep-2 reports also contain ids `<node>__s9011`–`__s9014` (B.2 cache / smoke instances). **Fix:** add one sentence saying these are outside the design universe and would be refused by `split_of`.
>
> **Scratch:** my scratch is in `/tmp/rev_p3/_to_delete/`. Nothing was edited, committed or deleted, and the worktree is clean.

## Round 2 (`39ecfa49`)

> Verdict: CONFIRMED
>
> All eight fixes in commit 39ecfa49 check out against `git diff bc58da88 39ecfa49`, and the split file is unchanged. At 39ecfa49 its sha256 is still `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`, so my round-1 recomputation of T0, T1 and the disclosure figures still applies. The worktree's HEAD is 39ecfa49 and it is clean.
>
> - **m1, done:** the condition is now stated in three places: the report (lines 15–17), the module docstring and the comment above `T1_NODES`. It says the G.5 amendment adding `autoresearch_fixedtokens` must adopt seeds 5101–5112 and G5-SPLIT, or else the node is not supplied (a second split file would be a §6 STOP).
> - **m2, done:** the docstring now names `split_of` as the function that refuses outside instances.
> - **m3, done:** `assignment` refuses anything that is not a dict or whose `schema` is not `SCHEMA` (message "use load()"). `split_of(None, inst)` loads the file through `load()`, so the pin and the generator-equality check apply. A test covers `{}`, a wrong schema, and the real file with its schema changed.
> - **m4, done:** `_partition` raises `SplitError` instead of using an assert, and a new test covers it.
> - **m5, done:** the test now uses `monkeypatch.syspath_prepend`.
> - **m6, done:** the comment is corrected.
> - **m7, done:** a new test rebuilds the `trackp_sft/v1` assignment with `sft_data.assign_splits`, using the `splits` block of `r1/scripts/configs/trackp_sft.json` (salt `trackp_sft/v1`, 3/3/12). It asserts the per-node overlap is [5, 7, 6, 5, 6, 5, 6, 5], which matches my own round-1 recomputation. The literal checks `digits_mlp__s204` → test and `digits_mlp__s214` → dev match the file.
> - **m8, done:** the ids `__s9011` to `__s9014` are explained in the report and the docstring, and a test shows `split_of(None, "digits_mlp__s9011")` is refused.
>
> **Tests:** I ran only `r1/tests/test_p3_split.py`, with `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, `TMPDIR=/tmp/rev_p3/t2` and `/tmp/tgport312/bin/python`. 11 passed and none were skipped.
>
> There are no new findings. One small observation that needs no action: `split_of(None, …)` re-reads and re-checks the file on every call. That is fine for now; a bulk caller should call `assignment(load())` once and reuse the result.
>
> I read no labels or evaluation values and edited, committed or deleted nothing. All scratch is in `/tmp/rev_p3/_to_delete/`.

---

Code-Commit: 39ecfa492415ec7c15732a805912143c4f88a121
Verdict: ACCEPTED

Accepted: the split file sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569` is the value for the preregistration's `split_file` field.
