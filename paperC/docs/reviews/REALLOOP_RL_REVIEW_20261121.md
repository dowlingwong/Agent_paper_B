Reviewed base: `1bd69a340816b7dc3e0bc287389225c79243eccf` (branch `mac-paperc-rl-20261121` over `paperc-plan-amend-20261119` @ `461ecae9`; accepted in round 3)

# Independent review record — Paper C real-loop multi-step RL design and CPU skeleton

**Unit.** `paperC/docs/proposals/REALLOOP_RL_DESIGN_20261121.md` (revisions 1–3), `paperC/src/paperc/realloop/`
(`reward`, `layout`, `budget`, `env`, `train`) and `paperC/tests/test_realloop_skeleton.py`. Task (queue of 20 Nov 2026):
the multi-step RL design and code skeleton with a reward in which the infrastructure-log class is not neutral, a
training-split-only worker layout, budget enforcement, and CPU-only tests with tiny models. Checked against the Paper C
plan, addendum 19 Nov (§A.1, §C), the schema, and the isolated harness (`trackg/outcome.py`, `isolation.py`,
`campaign_v2_diff.py`). The design decides nothing: RL-INFRA, RL-TRUNC, RL-LAYOUT, RL-BUDGET, the CPU limit level,
RL-ALGO and the `shared_dev_shm` waivers go to the author.

**Process.** One independent reviewer (a separate agent that did not write the unit) for all three rounds; it edited
nothing in the worktree (scratch under `/tmp/pcrlrev/`), ran the tests, mutation scripts and edge-case probes in its
own clone, and read no labels, results or secrets. Round 2 was interrupted by a usage limit and resumed. Round 3
confirms the fixes made after the round-2 acceptance. The round texts are reproduced below as delivered, as block
quotes.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `3712d1cf (rev 1)` | NOT ACCEPTED (2 blocking, 5 major, 7 minor) |
| 2 | `6a40e43c (rev 2)` | ACCEPTED (7 minor) |
| 3 | `1bd69a34 (rev 3)` | ACCEPTED (notes only) |

**Open for the author and later units.** The decisions of design §10; the harness and runner requirements of §8
(no infrastructure reruns in RL, host evidence from the scheduler and driver, the row server, `cpu.max` and a one-GPU
allow-list, the layout builder, declared run costs, the control rerun under RL-INFRA B, the B11 runner), each with its
own runbook, review and host or cluster test. Round-3 note: a test asserting that no control rerun is requested after an
over-request would pin that path.

## Round 1 (`3712d1cf (rev 1)`)

> Reviewed base: 3712d1cffe96e3e1b258a80fedb08e79f500e555
>
> # Review r1: real-loop multi-step RL design and CPU skeleton (Paper C)
>
> Reviewer: independent (Claude, AI-assisted); did not write the unit. Branch `mac-paperc-rl-20261121` @ `3712d1cf`, base
> `paperc-plan-amend-20261119` @ `461ecae9`. Diff: 8 files, all under `paperC/` (nothing outside `paperC/`, nothing in
> Paper B). Harness checked against `/tmp/pb/wt/t1h` @ `a69c8ef` (`trackg/outcome.py`, `isolation.py`,
> `campaign_v2_diff.py`). Tests: 28 passed in my clone (`/tmp/pcrlrev/clone`). Mutation script
> `/tmp/pcrlrev/scripts/mutate.py` (32 mutants), probe script `/tmp/pcrlrev/scripts/probes.py` (14 probes); outputs are
> quoted below.
>
> Summary: the skeleton is tidy and the REINFORCE gradient is correct, but two of the three exploits the unit exists to
> close are not closed as designed. The example budget can be bypassed by reading the training split, which the
> layout itself puts in the worker root. The free-rerun exploit survives inside the harness's own rerun loop, which the
> design never requires the runner to switch off. Several attribution rows, the layout scan and the env have concrete
> defects, and the limits are stated more strongly than the code supports.
>
> ---
>
> ## Blocking
>
> ### B1. RL-BUDGET A does not bound anything an adversarial worker cannot already do: the training split is on disk in the worker root
> - **Location:** design §5 (RL-BUDGET A), §4 (both layouts), `realloop/budget.py` docstring ("so an edited worker
>   cannot train on more data than the fixed budget", `__init__.py` line 10-11), `realloop/layout.py` `WORKER_ROLES`.
> - **Evidence:** both RL-LAYOUT options put `train_inputs` and `train_labels` in the worker root
>   (`WORKER_ROLES["train_and_val_inputs"]` and `["train_only"]`). RL-BUDGET A serves example **indices** ("serves
>   training example indices on request"). Indices into files the worker can already `np.load` are only advice. An
>   edited worker skips the index server, reads `data/train_*.npy` directly and trains as many epochs as the wall time
>   allows. `served` stays 0 and `refused_requests` stays 0, so `classify_run` passes the run through as `ok`. Even a
>   worker that does use the server can ask for `n_examples` once, cache them and train on them for any number of
>   epochs. The design calls this reuse permitted ("the budget bounds data, the wall time bounds compute"). But the
>   data a worker sees is already capped by the size of the split, so the counter adds no bound beyond what existed
>   before. The exploit `isolation.py` names ("extra training within the time limit") is bounded only by the measured
>   timeout under A. That makes A, in effect, B without the cgroup limit. There is a second gap: `isolation.py` (line
>   ~65) records that `shared_dev_shm` gives the worker the host's `/dev/shm`, "through which it can keep state between
>   runs". A worker can keep weights there and resume them in later runs, so it trains across runs. The design never
>   mentions this limit.
> - **Fix:**
>   1. Either serve example **contents**, not indices, through the parent: under RL-BUDGET A the worker root holds no
>      training data, and layout and budget become one decision. Or state plainly that A bounds data only for a
>      cooperating loader, and that compute is bounded only by the wall time.
>   2. Add the cgroup CPU/GPU-time limit (option B) as a complement, not an alternative.
>   3. Require `shared_dev_shm` off for RL training, or refuse it, or make it a named waiver.
>   4. Correct the claims in `budget.py`/`__init__.py` and the §5 option text so the author decides on true
>      statements.
>
> ### B2. The free-rerun exploit persists inside the harness's rerun loop; the design does not require the runner to disable or attribute it
> - **Location:** design §3 and §8 items 1-5, `realloop/env.py` `Runner.run` and the single `RunRecord` it returns.
> - **Evidence:** `campaign_v2_diff.run_with_retries` (lines ~126-176) reruns any non-timeout `infrastructure_failure`
>   up to `max_infra_reruns` (default 2) times before returning. Reruns cost no manager call and are not counted in the
>   step budget. After the last rerun the outcome is `infrastructure_failure_final`, which is "not registered as
>   evaluated, so it can be proposed and run again later". `attribute()` sees only the record the runner returns.
>   Suppose B11 implements `Runner.run` on the harness campaign path, as §8.5 ("against the pinned harness") invites.
>   A worker can then print `No space left on device` whenever its own holdout estimate looks bad, reroll its
>   nondeterminism, and return the best of up to 3 tries as `ok`. RL-INFRA A never fires, because the final record is
>   `ok`. The design names "free reruns" as the exploit (§1) and states that a proposal failure's "code state counts as
>   evaluated" (§3). Yet nothing in §8 or in the env enforces either point. There is no requirement on
>   `max_infra_reruns` or on `EvaluatedStates.register`, and the env does not track evaluated states (`Proposal.duplicate`
>   is unused).
> - **Fix:** add a §8 requirement that the RL runner runs every code state exactly once per `execute`
>   (`max_infra_reruns = 0`), or that every attempt is returned and attributed (the first worker-producible infra
>   attempt on an edited state makes the proposal a failure, and later attempts are discarded). Require the runner to
>   register a code state as evaluated whenever it is attributed `proposal_failure`. Add an env test with a runner that
>   hides reruns, for example one that returns `runs_consumed=3` with an `ok` record and an attempt history, and assert
>   that the hidden infra attempts are attributed.
>
> ---
>
> ## Major
>
> ### M1. RL-INFRA A's "evidence the worker cannot write" includes signals the worker can **cause**; truncation then becomes an episode-deletion exploit, and the trainer does not apply the imbalance level. Option B trusts the incumbent, which is policy-chosen edited code
> - **Location:** design §3 (RL-INFRA A, B, RL-TRUNC), `reward.py` `HostEvidence`, the `not run.edited` row,
>   `attribute`; `train.py` `reinforce` (the `continue` on truncated episodes).
> - **Evidence:**
>   - **Host evidence:** the list of "host evidence" is a GPU Xid, a scheduler eviction, a node drain and a host
>     disk-full. Several of these can be caused by user code:
>     - Xid 13, 31 and 43 (graphics engine exception, GPU memory page fault, GPU stopped processing) are classically
>       triggered by application errors such as illegal memory accesses.
>     - HTCondor/Slurm evict or hold jobs that exceed their memory or disk request.
>     - The worker's writable working copy and its private `/tmp` sit on host storage, so the worker can fill the host
>       disk.
>
>     The test asserts `HostEvidence(gpu_xid=True)` gives `truncate` (`test_attribution` row 5).
>   - **Truncation in training:** truncated episodes are dropped and **resampled** in `reinforce` (`while len(episodes)
>     < batch: … continue`). A policy whose bad trajectories end in a self-caused Xid or OOM-eviction therefore has its
>     low returns removed from the gradient. The free rerun comes back as a free episode deletion. Addendum §C states
>     that dropping "assumes that truncation does not depend on arm or outcome". The trainer checks neither condition:
>     `truncation_check` is never called from `reinforce`, and the only guard fires when truncations exceed
>     `10 × batch` in one iteration, which allows up to ~90 % truncation.
>   - **Option B:** `RunRecord.edited` is False for "a rerun of the incumbent", and `edited=False` truncates any infra
>     reason. But the incumbent is an edited code state the policy chose to keep. A planted trigger (random, by
>     clock, or by run count through `/dev/shm`) makes later proposals built on it **and** the control rerun fail as
>     infrastructure. Under B that is `truncate`, so the episode is deleted.
> - **Fix:**
>   1. Restrict truncating host evidence to faults not attributable to the job. Allow-list the hardware Xids (for
>      example 48, 63/64, 74, 79, 92/94/95). Count an eviction only when it is a preemption by priority, not a
>      resource-limit hold or remove. Count a disk-full only on a filesystem the worker cannot write, with worker
>      quotas in place.
>   2. State the residual risk in §3.
>   3. In `reinforce`, enforce the declared truncation level per iteration and cumulatively, giving a STOP. Do not
>      resample truncated episodes silently; report the truncation rate together with the return.
>   4. Under B, run the control on the deployed **start configuration** (truly unedited), not on the incumbent. Or
>      state that an incumbent-triggered control failure counts as a proposal failure.
>   5. Rename `edited` to `trusted_code` (true only for the start configuration).
>
> ### M2. The attribution table is not faithful to all harness classes and reasons
> - **Location:** design §3 table, `reward.attribute`, `budget.classify_run`.
> - **Evidence:**
>   - **Measured timeout with host evidence:** `isolation.py` says a suspension of the whole host or batch job "also
>     counts as the proposal's timeout" (`divergent`/`timeout`). `attribute` returns `proposal_failure` for every
>     `divergent` before it looks at `run.host`. Probe P8: `divergent/timeout + scheduler_eviction -> proposal_failure`.
>     So a preemption that the design says truncates (§3 A: "a scheduler eviction or preemption") is charged to the
>     proposal whenever it surfaces as a timeout. This is the commonest form of preemption on batch hosts.
>   - **`budget_exceeded` overrides a STOP and host evidence:** probe P9: provisional `infrastructure_failure/timeout`
>     plus a refused request gives `('divergent', 'budget_exceeded')`. The design's own row says a provisional timeout
>     is a STOP. P9b: an evicted run with a refused request becomes a proposal failure. That one is defensible, but
>     the design does not say so.
>   - **Classes and outcomes the table omits:**
>     - the harness's not-run statuses (diff refused for scope, inert, duplicate: `not_run_<status>`);
>     - `invalid_proposal` (parse failure, charged a call, nothing runs);
>     - `infrastructure_failure_final`;
>     - `timeout_repeated`;
>     - `IntegrityError` and the record-gate STOP, which are raised, not classified.
>
>     Addendum §C says how parse failures are treated (in-episode where charged), and schema `FailureCategory`
>     carries `invalid_edit_scope` and `proposal_precondition_failed`. `Runner.propose` always returns a `Proposal` and
>     `Runner.run` always returns a run, so B11 has no way to express these cases.
>   - **Missing statements:** an OOM kill (cgroup SIGKILL gives `killed`) is a proposal failure under A. That is
>     reasonable, but the design should say it. `no_exit_status` is probably not worker-producible (it is the frozen
>     parent's exit status); listing it there is conservative and should be stated as such.
> - **Fix:**
>   1. Check `run.host` before the `divergent` branch for `divergent/timeout`, and add a table row for it.
>   2. In `classify_run`, let a provisional timeout stay a STOP and let host evidence keep priority. Alternatively
>      state the override as a deliberate choice.
>   3. Add rows and `Runner` return types for: not run, which charges a call and 0 runs (as a duplicate or inert
>      edit); parse failure, as charged per the B11 runbook; `IntegrityError`, which maps to `EnvStop`.
>
> ### M3. The layout scan wrongly refuses common kit layouts, cannot be applied to an edited working copy, can be hung or crashed by special files, and its limits are not stated
> - **Location:** `layout.py` `check_worker_root`, design §4, §8.3.
> - **Evidence:**
>   - **False positive:** `parent_names` holds basenames. Probe P1: a kit laid out as `train/x.npy, train/y.npy,
>     val/x.npy, val/y.npy, test/…` is refused with "train/x.npy: carries the name of a parent-only file". That is the
>     commonest layout, and the test kit (`train_x.npy`, `val_y.npy`) happens to avoid it.
>   - **Edited code:** files with role `code` are hashed into the plan, so every proposal's edit fails (probe P4:
>     "train.py: differs from the planned file"). §8.3 says the runner calls `check_worker_root` "before every run",
>     which would refuse every edited run. If the runner instead excludes or re-hashes the code, then the code
>     directory can hold anything, including label bytes in encoded form. The design does not say which.
>   - **Special files:** probe P6: a FIFO in the root blocks the scan indefinitely (`sha256_file` opens it). Probe P5:
>     a Unix socket raises a bare `OSError`, not a `LayoutError`. Character devices would be read without end.
>   - **Bypasses the hash check misses:** a whole-file sha256 does not catch compressed, encoded, partial or
>     concatenated copies (probe P3: a gzip of `val_y.npy` shipped as `train_x.npy` passes `plan_worker_root`'s clash
>     check). A directory named like a parent-only file passes (probe P2). An empty `__init__.py` clashes with any
>     empty parent-only file (probe P7, a false positive).
>   - **Scope of the scan:** it runs before the run and covers only "the worker root". Files the worker creates at
>     run time, other allow-listed paths (system directories, the data mount if separate, the shim, a shared
>     `/dev/shm`) and anything the parent writes later are outside it. Hard links to a parent-only file are caught,
>     because the bytes are the same.
>   - **What the guarantee rests on:** the real guarantee is that the sandbox's mount namespace is **built from the
>     plan** and parent-only files never enter it. The scan is a belt-and-braces check, yet the design (§4, and
>     "a scan refuses any parent-only file, renamed or not" in `__init__.py`) presents it as the guarantee.
> - **Fix:**
>   1. Compare names by relative path (or by role directory), not by basename, and add a per-split-directory test.
>   2. Hash only non-code files against the plan. Scan code files only against the parent-only hashes, and state that
>      encoded or embedded copies are not detected.
>   3. Use `os.lstat` and refuse anything that is not a regular file or directory, before opening it.
>   4. Refuse a directory carrying a parent-only name.
>   5. Say in §4 that the layout guarantee is the construction of the mount namespace, list what the scan cannot see,
>      and require that parent-only files never reach any allow-listed path.
>
> ### M4. The env's run-budget charging can raise mid-step after a run was spent, and the "controller refuses execute beyond W" branch is dead code
> - **Location:** `env.py` `step` (lines ~222-241), design §5 last bullet, §9 ("W enforced over the policy").
> - **Evidence:**
>   - **Uncaught exception:** the check is `can_run(1)`, but the charge is `charge_runs(run.runs_consumed)`. Probe
>     P10: with `W=3` and a runner returning `runs_consumed=2`, the second execute raises `BudgetExceeded: 2 + 2 runs
>     exceed W = 3` **after** `runner.run` has already spent the runs. The episode is left without an end and with
>     nothing recorded. `runs_consumed > 1` is exactly what B2's rerun accounting would produce.
>   - **Dead code:** `_advance` ends the episode once `runs_used >= W`, so at every E1 `can_run(1)` is true and the
>     `action = "skip"` override cannot be reached when `runs_consumed == 1`. Mutation M06 (removing the override)
>     survives every test. `test_the_policy_cannot_run_beyond_W` only checks termination at W.
>   - **Wrong gradient if it ever fires:** if the override did fire, `train.rollout` would credit the gradient to the
>     policy's sampled `execute` index while the env performed `skip`.
> - **Fix:** decide the rule for a run that would overshoot W. Either refuse before running (the runner declares its
>   cost up front), or charge `min(k, W - used)` and terminate. Make the refusal reachable and tested. Return the
>   action actually taken from `step` so the trainer credits it.
>
> ### M5. Dropping whole truncated episodes for R0/R1 contradicts plan §3.1
> - **Location:** design §7 RL-ALGO A ("truncated episodes are left out and counted"), §3 RL-TRUNC ("dropped from
>   training and evaluation").
> - **Evidence:** plan §3.1 says: "Bootstrapped methods bootstrap at the last observed state of a truncated episode;
>   Monte Carlo targets drop it, and the drop is reported per arm." R0 (FQI) and R1 (IQL) are bootstrapped methods.
>   The design drops their truncated episodes entirely. The task rules forbid contradicting the plan, and addendum §C
>   keeps "the plan's rules" for truncation.
> - **Fix:** for R0/R1, keep a truncated episode's transitions up to the last observed state, with bootstrapping
>   there. Drop truncated episodes only for Monte Carlo targets (`train.reinforce`, N6 returns). If the author should
>   depart from the plan, raise it as an explicit decision.
>
> ---
>
> ## Minor
>
> - **m1. End reasons vs schema.** `env.py` `_finish("truncated", "infrastructure")` is used for every truncation.
>   Schema `END_REASONS["truncated"]` has `"host"`, and a host-evidenced truncation should use it (probe P14 shows that
>   a `launch_error` and an eviction both become `infrastructure`). A protocol STOP raises `EnvStop` and leaves
>   `episode.end = None` (probe P11). Plan §3.1 and schema treat a protocol STOP as a truncation with reason
>   `protocol_stop`, which must be counted per arm; aborting the whole training is a separate choice. **Fix:** map
>   host evidence to `"host"`. Record `truncated/protocol_stop` before raising, or say why the RL STOP is stronger.
> - **m2. Episode shape vs schema rows.** The env offers no E2 row after a proposal failure. Schema row rules say
>   "a divergent or invalid candidate is not kept: its E2 row is a `discard`", and RL-ALGO A trains on logged rows of
>   that shape. **Fix:** document the mapping (a forced discard), or emit the row with no decision.
> - **m3. `N = 0` or `W = 0`.** `reset()` raises `BudgetExceeded` (probe P12), and `_obs` would divide by zero.
>   **Fix:** validate `W, N >= 1` in `CampaignBudget`.
> - **m4. Stored step reward on truncation.** For a truncated episode, `Step.reward` is unused and untested (mutation
>   M11 survives). This is harmless because such episodes are dropped, but `Episode.ret` for truncated episodes
>   should be documented as meaningless or asserted to be 0.
> - **m5. `RunRecord.value` on non-ok runs.** `attribute` checks `value` only for `ok`. A `divergent` record with a
>   value is accepted silently. The env clears it, but `attribute` is public. **Fix:** refuse a value on non-ok runs,
>   as `RunOutcome.__post_init__` does.
> - **m6. Unlisted harness limits.** §1 lists three limits. `isolation.py` also names "it can answer the parent's
>   evaluation requests differently from a fixed model", which bears directly on RL-LAYOUT A's transductive route,
>   and the `shared_dev_shm` state channel (B1). **Fix:** list both and say which RL option covers each.
> - **m7. §9 overstates the tests.** It claims "every scan refusal": the missing-file refusal is untested (M21
>   survives) and special files are untested. It claims "W enforced over the policy": see M4.
>
> ## Note
>
> - **N1. REINFORCE gradient is correct.** `g = -outer(p, x); g[i] += x` is ∇_W log π(a_i|x) for a linear softmax. The
>   leave-one-out baseline is unbiased, the update is ascent, and the whole-episode return with γ = 1 matches plan
>   §3.1. Mutants that flip the sign (M26), drop the update (M27), credit the wrong action (M28), freeze E2 (M30),
>   remove the baseline (M25) or break E2 bookkeeping (M13, M14) are all killed, so the learning test is not trivially
>   passing. It does not test E1: mutation M29 (E1 never updated) survives, so the docstring's "learn to skip" is not
>   checked. Add an assertion on `probs(obs_e1, "E1")[skip]` for a negative forecast.
> - **N2. Surviving mutants worth a test.**
>   - M04: step reward ignores `runs_consumed`. No test uses `runs_consumed > 1`.
>   - M05: truncation level boundary `>` vs `>=`.
>   - M15: STOP turned into truncate inside the env. There is no env-level STOP test.
>   - M17: the `launch_error` carve-out in `classify_run`.
>   - M18: the per-epoch permutation replaced by the identity order.
>   - M32: a mean baseline including self. This is equivalent up to a factor (n−1)/n and needs no test.
> - **N3. Scope.** All changes are under `paperC/`. Nothing touches Paper B's harness, labels, seeds or tables. The
>   harness changes are listed as requirements (§8), not made. RL-ALGO A (offline R0/R1) matches plan §8/§13, where
>   online RL (R3, SPT-7) is an extension. The decisions are presented with options and a recommendation, as required.
>   Two of them (RL-BUDGET A and RL-INFRA A) rest on the false or overstated claims in B1 and M1, and need restating
>   before the author decides.
> - **N4. Option B cost.** The control rerun is "not charged to the policy" but consumes real worker runs. The
>   campaign-level cost per arm should be reported, so that arms are matched on total host use, not only on W.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`6a40e43c (rev 2)`)

> Reviewed base: 6a40e43cda354383851f1565db0a84d121cf5936
>
> # Review r2: real-loop multi-step RL design and CPU skeleton (Paper C), design note revision 2
>
> Reviewer: independent (Claude, AI-assisted); did not write the unit. Diff reviewed: `git diff 3712d1cf 6a40e43c` (8
> files, all under `paperC/`; `git diff --stat 3712d1cf 6a40e43c -- . ':!paperC'` is empty, so Paper B is untouched).
>
> What I ran:
> - Unit tests in my clone (`/tmp/pcrlrev/clone` @ `6a40e43c`): 41 passed.
> - Full `paperC/tests`: 272 passed, 1 skipped, 2 failed. Both failures are `test_ope_p7.py::…[lightgbm]` with
>   `ModuleNotFoundError: No module named 'lightgbm'`, in files this unit does not touch. That is an environment gap,
>   not a regression.
> - New mutation script `/tmp/pcrlrev/scripts/mutate_r2.py` (35 mutants, 29 killed) and probe script
>   `/tmp/pcrlrev/scripts/probes_r2.py` (Q1-Q6).
>
> ## Round-1 findings: status
>
> | r1 | Status | Evidence |
> |---|---|---|
> | B1 example budget bypassable via the training split on disk | **resolved** | RL-LAYOUT A is `served` (`WORKER_ROLES["served"] = {code, frozen}`); `ExampleServer.serve` returns row contents. §5 and the `budget.py`/`__init__.py` text now say the server bounds data, not compute, and that reuse is allowed. `shared_dev_shm` is refused without a waiver (`plan_worker_root`, tested; A28 killed). |
> | B2 free rerun inside the harness | **resolved** | §8.1 requires `max_infra_reruns = 0` and registration as evaluated. `attribute_attempts`: the first attempt decides and all attempts are charged (A03, A04 killed). The env's evaluated registry makes repeats rule-forced duplicates (A12 killed). There is a hidden-reroll env test. Edge cases remain: m1, m2. |
> | M1 worker-causable host evidence; truncation as deletion; B trusts the incumbent | **resolved** | `HARDWARE_XIDS` allow-list (A02 killed); `preempted_by_priority` only; residual risk stated. The trainer has a cumulative-level STOP and a more-than-half STOP (A33 killed; A32 is masked by the duplicate post-batch check, which still enforces the level). B uses the trusted start configuration (A06 killed). |
> | M2 attribution table gaps | **resolved** | Host evidence is checked before `divergent` (A01 killed). The provisional-timeout and `launch_error` carve-outs are in `classify_run` (A09 killed). Not-run, invalid, `timeout_repeated`, OOM, `no_exit_status`, `IntegrityError` and `infrastructure_failure_final` rows are present, and `Proposal.status` is handled. One stated rule is not implemented: m1. |
> | M3 layout scan defects | **resolved** | Relative-path comparison (the per-split test kit now uses `train/x.npy`, `val/x.npy`); `lstat` before opening (symlink, FIFO and socket tests); directory at a parent-only path; code-aware checks; empty files excluded. §4 now says the guarantee is the mount-namespace construction and lists what the scan cannot see. A24-A30 killed. |
> | M4 env budget charge after the run; dead W refusal | **resolved** | Declared `max_runs`, refusal before running (reachable, tested, A13 killed), undeclared overspend is a STOP (A14 killed). `charge_runs` can no longer raise, since `runs <= max_runs <= W - used`. The trainer side has a bias: m3. |
> | M5 truncation handling vs plan §3.1 | **resolved** | §3 and §7: R0/R1 bootstrap at the last observed state, and Monte Carlo targets drop the episode. |
> | r1 minors m1-m7 and notes | **resolved** | `host`/`protocol_stop` end reasons (STOP recorded before raising, A18 killed); forced E2 discard row (A15 killed); W, N >= 1; truncated `ret` = 0; value refused on non-ok runs; five limits in §1; §9 rewritten. The E1 learning assertion kills A34 (it survived in r1). |
>
> ## Blocking
>
> None.
>
> ## Major
>
> None.
>
> ## Minor
>
> ### m1. The stated "refused request beats host evidence" rule is not what the code does
> - **Location:** design §5 RL-BUDGET A ("also when the run later fails with host evidence: the request was the
>   proposal's"); `budget.classify_run` docstring; the test comment `# deliberate` (test line 217); `reward.attribute`
>   line 92.
> - **Evidence:** `classify_run` turns the run into `divergent/budget_exceeded`, but `RealLoopEnv.step` rebuilds the
>   `RunRecord` with `run.host` intact. `attribute` checks `run.host.any()` before `divergent`, so the run truncates.
>   Probe Q1: `('divergent', 'budget_exceeded') -> truncate_host`. The test checks `classify_run` alone, never end to
>   end. Impact is small: the refused rows were never served, and host evidence is no longer worker-causable. But the
>   author is asked to decide on a rule that the code reverses.
> - **Fix:** make the two agree. Either drop `host` when `classify_run` returns `budget_exceeded` (or have
>   `attribute` check `reason == "budget_exceeded"` before the host check), or change §5 and the docstring to "host
>   evidence keeps priority". Add an env-level test either way.
>
> ### m2. `prior_attempts` is only consistent when every prior attempt failed
> - **Location:** `env.py` `step` (lines ~313-342), `reward.attribute_attempts`.
> - **Evidence:**
>   - Probe Q2: first attempt `ok` (10), final `ok` (-5). The attribution is `ok` from the first attempt, but E2 and a
>     keep use the final value (-5). The reroll's value replaces the deciding attempt's value.
>   - Probe Q4: first attempt `ok`, final attempt over-requests, so `classify_run` folds only the final attempt to
>     `budget_exceeded`. The attribution is still `ok`, and E2 then does arithmetic on `run.value = None`:
>     `TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'` once an incumbent exists.
>   - Probe Q3: the budget fold is never applied to the deciding (first) attempt.
>
>   These paths need a runner that breaks §8.1 (retrying after an `ok`). That is exactly the case `prior_attempts`
>   exists to defend against, so it should fail loudly rather than inconsistently.
> - **Fix:** in `attribute_attempts`, refuse with a protocol STOP any attempt that follows an `ok` attempt, so retries
>   are allowed only after a non-ok attempt. Apply the parent's budget record to the attribution of the whole execute,
>   since the server is shared by all attempts. Take the E2 value from the deciding attempt. Add a test for an `ok`
>   followed by a further attempt.
>
> ### m3. The trainer drops a refused `execute` but credits a sampled `skip` at the same state, which biases the gradient
> - **Location:** `train.rollout` (`if taken == action: trace.append(...)`), `env.step` forced-skip branch.
> - **Evidence:** at a state where `execute` does not fit, both actions lead to the same transition. The full score
>   term there, `adv · ∇log π(a|s)`, has zero mean, because `Σ_a π(a|s) ∇log π(a|s) = 0`. Keeping only the `skip`
>   branch leaves `E[adv · 1{a=skip} ∇log π(skip|s)] = E[adv|s] · ∇π(skip|s)`. That is non-zero whenever reaching such
>   a state correlates with the return, and the linear policy shares weights across states, so the bias spreads to
>   feasible E1 states. Mutation A31 (credit every sampled action) survives, so nothing tests this choice. Scope is
>   limited: it only arises with `max_runs > 1`, and `reinforce` is a mechanism check. My r1 fix wording ("credit the
>   action actually taken") was ambiguous here.
> - **Fix:** do not ask the policy at an infeasible E1. Make it a rule-forced `skip` row in `_next_decision`, as for
>   not-run proposals, so neither action is credited. Or credit the sampled action unconditionally, which is unbiased
>   because the override is part of the dynamics. Add a test.
>
> ### m4. "cgroup CPU/GPU-time limit" names a control that cgroup v2 does not have
> - **Location:** design §5 A/B and §8.4; `budget.py` line 12.
> - **Evidence:** cgroup v2 provides `cpu.max` (CPU bandwidth) and device access control, but no GPU-time
>   controller. GPU compute is bounded by the measured timeout only if the run has one exclusive GPU. The compute
>   slack itself is not stated: the measured timeout is census baseline × 3 (`isolation.py`, factor 3), so an edit can
>   roughly triple training compute within the limit, and the reward pays for it. The cgroup limit's level is not
>   declared.
> - **Fix:** write "cgroup `cpu.max`/CPU-time limit plus a one-GPU device allow-list; GPU time bounded by the wall
>   time". State the ×3 slack, and either propose a CPU-time level (for example, near the census baseline's) or list
>   it in §10 as an author value.
>
> ### m5. `launch_error` and trusted-code failures are recorded with reason `host`
> - **Location:** design §3 table rows for `launch_error` and trusted code; `env.py` `_finish("truncated", "host")`.
> - **Evidence:** probe Q6: a `launch_error` gives `truncated/host`. Schema `END_REASONS["truncated"]` distinguishes
>   `infrastructure` from `host`. A launch error, or an infrastructure failure of the start configuration, is
>   infrastructure, not host loss. Mixing the two blurs the per-reason truncation counts that addendum §C asks for.
> - **Fix:** return a separate attribution (for example `truncate_infrastructure`) for `launch_error` and for
>   trusted-code failures, and map it to `infrastructure`. Keep `host` for host evidence only.
>
> ### m6. The start configuration is not registered as evaluated
> - **Location:** `env.py` `__init__` (`self.evaluated = set()`; probe Q5).
> - **Evidence:** a proposal that reverts to the start configuration is run and charged a run. The harness treats an
>   already-evaluated code state as a duplicate that is not run.
> - **Fix:** seed `evaluated` with the start configuration's code-state hash, taken from the runner, and test a
>   revert proposal.
>
> ### m7. Untested lines (surviving mutants)
> - A19: a truncated `ret` that is not zeroed (`ep.ret == 0.0` is asserted only where every step reward is 0 anyway).
> - A20: an unknown `Proposal.status` accepted instead of STOPping.
> - A31: see m3.
> - A10: the `served > limit` clause, which is unreachable with `ExampleServer`. It can stay as defence, but say so.
>
> Add a test for each of the first two.
>
> ## Note
>
> - **N1.** The REINFORCE update is unchanged from round 1 and still correct (A35 killed). The learning test now also
>   pins the E1 decision (A34 killed).
> - **N2.** The cumulative truncation STOP uses the inter-arm imbalance level (0.05) as an absolute rate. That is
>   conservative and stated in §7; it is fine for a mechanism check.
> - **N3.** The decisions in §10 still come with options and a recommendation and decide nothing. The new
>   `shared_dev_shm_waivers` row correctly goes to the author. Nothing contradicts addendum §C or plan §3.1.
>
> VERDICT: ACCEPTED

## Round 3 (`1bd69a34 (rev 3)`)

> Reviewed base: 1bd69a340816b7dc3e0bc287389225c79243eccf
>
> # Review r3: real-loop multi-step RL design and CPU skeleton (Paper C), confirmation of the round-2 minors
>
> Reviewer: independent (Claude, AI-assisted); did not write the unit. Diff reviewed: `git diff 6a40e43c 1bd69a34`. It
> touches 6 files, all under `paperC/`; `git diff --stat 6a40e43c 1bd69a34 -- . ':!paperC'` is empty, so Paper B is
> untouched.
>
> What I ran:
> - Unit tests in my clone (`/tmp/pcrlrev/clone` @ `1bd69a34`): 44 passed.
> - Probe script `/tmp/pcrlrev/scripts/probes_r3.py` (R1-R7). R1-R4 re-check round 2's probes Q1-Q4 against the new
>   code; R5-R7 are new.
> - Mutation script `/tmp/pcrlrev/scripts/mutate_r3.py`: 13 mutants on the changed lines, 10 killed.
>
> ## Round-2 minors: status
>
> | r2 | Status | Evidence |
> |---|---|---|
> | m1 refused request vs host evidence | **resolved** | `attribute_attempts(budget_over=...)` makes the deciding attempt `divergent/budget_exceeded` and drops its host evidence. A launch error and a provisional timeout keep priority. Probe R1, end to end: refused request plus priority preemption gives `proposal_failure`, no truncation. R7: provisional timeout plus refused request is still a STOP. Design §5 and the code agree. Tests: unit and env (`hosted_overspend`). Mutants C02-C05 and C10 killed. |
> | m2 attempts after an `ok`; E2 value; budget on the deciding attempt | **resolved** | An attempt after an `ok` returns `stop`. Probe R2: recorded as `truncated/protocol_stop` before `EnvStop`, where round 2's probe Q2 used the reroll's value. E2 uses the deciding attempt (R4). The budget record is applied to the deciding attempt (R3: host-evidenced first attempt plus over-request gives `proposal_failure`). Round 2's Q4 TypeError path is now a STOP. C01 killed. C07 (E2 from the final attempt) survives, but it is now an equivalent mutant: E2 is reached only with a single attempt, where the final and deciding records coincide. |
> | m3 trainer bias at infeasible states | **resolved** | `_next_decision` turns a proposal whose `max_runs` does not fit into a rule-forced `skip` (`over_budget`), so the policy is never asked there. `rollout` credits every sampled action and STOPs on a mismatch. R6: when every proposal is infeasible, the episode terminates at `llm_cap` with 4 forced rows and no decision. C09 killed. |
> | m4 cgroup GPU-time wording | **resolved** | §5, §8.4 and `budget.py` now say `cpu.max` plus a one-GPU allow-list, that cgroup v2 has no GPU-time controller, and state the ×3 slack. §10 adds `rl_cpu_max_level` as an author value. |
> | m5 reason `host` for launch errors and trusted code | **resolved** | New attribution `truncate_infrastructure` maps to reason `infrastructure` (schema `END_REASONS`). It covers launch errors, trusted-code failures and a failed control under option B. C06 and C12 killed. Design table updated. |
> | m6 start configuration not evaluated | **resolved** | `Runner.start_hash()` is registered at construction (§8.5 requires it from the layout builder). The revert test shows 3 forced duplicates and 0 runs. C08 killed. |
> | m7 untested lines | **resolved** | Tests added for a truncated `ret` that is 0 after charged steps (`late_host_loss`) and for an unknown status as a STOP. The `served > limit` clause is commented as a defence. |
>
> ## Blocking
>
> None.
>
> ## Major
>
> None.
>
> ## Minor
>
> None.
>
> ## Note
>
> - **N1. Surviving mutants, none worth a required change.**
>   - C07: equivalent (see m2 above).
>   - C11: the control rerun is still requested after an over-request. The attribution is unchanged, because
>     `budget_over` decides, so only the host-use count differs. Probe R5 confirms the code skips the control (0
>     calls); a test asserting `control_rerun` is not called would pin this.
>   - C13: the trainer's mismatch STOP is unreachable with this env, since `step` always returns the sampled action. It
>     is a defence for other environments.
> - **N2.** The skeleton is still a mechanism check behind the author decisions in §10 (`rl_infra`, `rl_trunc_level`,
>   `rl_layout`, `rl_budget`, `rl_cpu_max_level`, `rl_algo`, `shared_dev_shm_waivers`). It decides no scientific
>   content, and nothing in revision 3 contradicts addendum 19 Nov §C or plan §3.1. The real-node items in §8 still
>   need their own runbook, review and authorization.
>
> VERDICT: ACCEPTED

---

Code-Commit: 1bd69a340816b7dc3e0bc287389225c79243eccf
Verdict: ACCEPTED

Accepted commit: `1bd69a340816b7dc3e0bc287389225c79243eccf` (round 3; design revision 3, 44 tests).
