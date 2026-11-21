# Paper C: multi-step RL on the real loop — design and code skeleton (draft for the author)

**Status: DRAFT, ENGINEERING_ONLY. Decides nothing; authorizes no run.** Revision 2, after round 1 of the independent
review. Written by the Mac-desk agent (Claude), AI-assisted, on branch `mac-paperc-rl-20261121` from
`paperc-plan-amend-20261119` @ `461ecae9`. Code: `paperC/src/paperc/realloop/` (CPU only), tests
`paperC/tests/test_realloop_skeleton.py`.

## 1. Why this unit

Paper C trains multi-step RL only after a passed go/no-go (addendum 19 Nov §A.1 item 5), and then compares it with
the strongest non-RL multi-step method (Q3). Its learners (P8: R0 FQI, R1 IQL, N6) are validated on E-SYN. On the
real loop the reward comes from runs of edited code in the isolated harness, whose own record
(`autoresearch/trackg/isolation.py`, "Not closed here"; READY 60 and 61) names the limits that matter once a reward is
attached:

1. an infrastructure log pattern printed by the worker makes the run an `infrastructure_failure`, which the campaign
   reruns (`max_infra_reruns`, default 2) without a manager call and without registering the code state as evaluated
   — "an RL reward must not treat that class as neutral without the author's decision";
2. the worker can read every allow-listed path: its working copy and the data, so the validation and test labels
   that a node keeps there;
3. the worker computes the training itself, so budget accounting stays in the editable process (only the wall time,
   the measured timeout, is enforced outside);
4. a node with `shared_dev_shm` gives the worker the host's `/dev/shm`, through which it can keep state between runs;
5. the worker can answer the parent's evaluation requests differently from a fixed model (the kits' probes narrow
   this).

A policy optimised against such a reward can learn to exploit each of these — free rerolls, label reads, extra
training, state carried across runs, transductive answers — directly or by steering the proposer, and it can learn to
cause host-looking faults that delete its bad episodes. This unit states the rules that close what can be closed,
as author decisions, says what stays open, and implements the rules as a tested skeleton that the B11 real-loop
runner and any RL route (offline from logged campaigns, or online) must use.

## 2. Scope

- In: the reward and the attribution of run outcomes; the worker layout; budget enforcement; a multi-step environment
  over an injected runner; a tiny CPU trainer as a mechanism check.
- Out: the real runner (B11), real-node collection (B13), LM routes (B14), any change to Paper B's harness (the changes
  this design needs are requirements in §8, not made here). Nothing touches Paper B's labels, seeds or tables.

## 3. Reward and attribution (RL-INFRA; `realloop/reward.py`)

Reward in σ_node units: per executing step −g × runs consumed; at the end of a terminated episode the audited terminal
increment (y_terminal − y_start)/σ_node (addendum 19 Nov §C: exhausting W or N is termination). A proposal failure is
charged like any run, gives no gain, and its code state is registered as evaluated (a later proposal of it is a
duplicate and is not run).

**Host evidence** counts only faults the job cannot cause, observed by the parent or the scheduler, never read from
the worker's output: a GPU Xid on a hardware allow-list (48, 63, 64, 74, 79, 92, 94, 95; application-triggerable Xids
such as 13, 31, 43 do not count), a preemption by scheduler priority (not a hold or remove for exceeding a resource
request), a node drain, a full filesystem the worker cannot write (worker quotas in place). Residual risk: a
job-caused fault that the scheduler or driver reports as one of these truncates; the truncation-rate STOPs (below)
bound its effect.

| Outcome | Attribution |
|---|---|
| `ok` | ok (E2 decision follows) |
| `divergent` (non-finite loss, no metric, multiple metric lines, measured `timeout`, `timeout_repeated`, `budget_exceeded` from §5, …) without host evidence | proposal failure (forced E2 `discard` row) |
| any non-ok outcome with host evidence (incl. a preemption that surfaces as a measured timeout) | truncate, reason `host` |
| `infrastructure_failure` / provisional `timeout` (with or without host evidence) | protocol STOP |
| `infrastructure_failure` / `launch_error` (nothing of the proposal ran) | truncate, reason `host` |
| `infrastructure_failure` / `killed` (incl. an OOM kill), `infrastructure_log_pattern`, `no_exit_status` (the parent's status; listed conservatively) on edited code, no host evidence | **RL-INFRA** |
| any infrastructure failure on trusted code (the deployed start configuration only) | truncate, reason `host` |
| not run: diff refused for scope, inert, a duplicate of an evaluated code state | rule-forced: one call, no run, no policy decision |
| invalid proposal (parse failure beyond retry, charged as an invalid trial by the pinned harness) | rule-forced like a not-run proposal (addendum 19 Nov §C: in-episode where charged) |
| `infrastructure_failure_final` | does not arise: the RL runner makes no infrastructure reruns (§8.1) |
| `IntegrityError`, record-gate STOP (raised by the harness) | protocol STOP |

A protocol STOP is recorded as a truncated episode with reason `protocol_stop` (schema `END_REASONS`) and then stops
the collection (`EnvStop`); per-arm counts follow addendum §C.

**RL-INFRA (recommendation: A).**
- **A (recommended): host evidence.** Worker-producible infrastructure signals on edited code are proposal failures;
  only host evidence (above) or a launch error truncates. Cost: a genuine host fault without recorded evidence is
  charged to the proposal (counted and reported).
- **B: control rerun.** An ambiguous failure is resolved by rerunning the **deployed start configuration** (not the
  incumbent, which is policy-chosen edited code that could carry a planted trigger) in the same slot: truncate only if
  the control also fails as infrastructure. The control's runs are not charged to the policy but are real host use,
  reported per arm. A fault that clears between the two runs is charged to the proposal.
- **Neutral** (rerun for free) is refused by the code; it would need an author row.

**Every attempt counts.** If a runner nevertheless returns earlier attempts (`RunRecord.prior_attempts`), the first
attempt decides the attribution and every attempt's runs are charged (`attribute_attempts`); a reroll never replaces a
failure.

**Truncation (RL-TRUNC).** Truncated episodes are never complete and are counted per arm; a spread of truncation
rates across arms above the declared level is a STOP (addendum §C). *(proposed)* level 0.05. How a learner uses them
follows plan §3.1: bootstrapped methods (R0, R1) keep a truncated episode's transitions up to its last observed state
and bootstrap there; Monte Carlo targets (N6 returns, the trainer of §7) drop it and report the drop.

## 4. Worker layout (RL-LAYOUT; `realloop/layout.py`)

**The guarantee is the construction:** the runner builds the worker's mount namespace from the plan, and parent-only
files never reach any allow-listed path — the worker root, the data mount, the shim, a shared `/dev/shm`.
`check_worker_root` is a check on top, run on the built root before each run. It refuses anything that is not a
regular file or directory (checked with `lstat` before opening: symlinks, FIFOs, sockets, devices), a non-empty file
with the bytes of a parent-only file (a renamed or moved copy, a hard link), a file or directory at a parent-only
path, and a data or frozen file that is missing, unplanned or changed. Code files are edited by every proposal, so
they are checked only against the parent-only bytes; a new file is allowed only next to planned code.

What the scan cannot see: compressed, encoded, partial or embedded copies (only whole-file bytes are compared), files
created at run time, paths outside the root; empty files are not compared by bytes.

**RL-LAYOUT (recommendation: A, tied to RL-BUDGET A).**
- **A (recommended): `served`.** The worker root holds code and frozen files only; the parent serves training rows
  and evaluation inputs through the result channel and keeps every label. No data file is on the worker's disk.
- **B: `train_and_val_inputs`.** Code, frozen, the training split and the validation inputs without labels. Data use
  is bounded only by the split's size, and the worker can fit to the validation inputs (limit 5).
- **C: `train_only`.** Code, frozen and the training split; evaluation inputs streamed by the parent.
- `shared_dev_shm` is refused for RL training unless a named waiver is given (limit 4); a node that needs it
  (`autoresearch_fixedtokens`, CUDA IPC) needs a waiver row or a memfd-only port before RL.
- The status quo (labels readable) is refused by the code.

## 5. Budget enforcement (RL-BUDGET; `realloop/budget.py`)

**RL-BUDGET (recommendation: A).**
- **A (recommended): parent-served training rows, the measured timeout and a cgroup CPU/GPU-time limit.** With
  RL-LAYOUT A the parent holds the training split and serves row **contents** on request in a fixed order (one
  permutation per epoch), counting them; a request beyond rows × epochs is refused and the run becomes `divergent` /
  `budget_exceeded`, whatever metric the worker reports (also when the run later fails with host evidence: the request
  was the proposal's; a launch error and a provisional-timeout STOP keep priority). What this bounds: the data the
  worker can obtain. What it does not: the worker can keep rows it received and train on them again; compute is
  bounded by the measured timeout and the cgroup time limit, not by the server.
- **B: wall time and a cgroup CPU/GPU-time limit only**, with RL-LAYOUT B or C. Compute bounded; data use bounded only
  by the split on disk.
- **C: worker-reported step counts.** Not acceptable: the count is in the editable process.
- The campaign budget (W runs, N calls; both ≥ 1) is the controller's (`CampaignBudget`). Each proposal declares its
  run cost before it runs; the controller turns an `execute` that does not fit in what is left of W into a forced
  `skip`, and a run that consumes more than it declared is a protocol STOP. Exhausting W or N terminates the episode.

## 6. Environment (`realloop/env.py`)

One episode = one campaign on one instance. Each manager call yields a proposal; a not-run or invalid proposal, or a
duplicate of an evaluated code state, is rule-forced (one call, no run). Otherwise the policy chooses E1
(execute/skip); after an `ok` run, E2 (keep/discard); after a proposal failure the E2 row is a forced `discard`. The
controller attributes every attempt (§3), folds in the parent's example record (§5), registers the code state as
evaluated, charges the budget and ends the episode: terminated with the audited terminal reward; truncated (reason
`host`, no terminal reward, `ret` 0); truncated with reason `protocol_stop` and `EnvStop`. `step` returns the action
actually taken, so a learner credits only the policy's own decisions. **Training-split only:** `mode="train"` refuses
any instance outside the training split (dev and test campaigns only in `mode="eval"`). The `Runner` protocol
(propose, run, control_rerun, training_rows, audit) is what B11 implements.

## 7. Learning (RL-ALGO; `realloop/train.py`)

**RL-ALGO (recommendation: A).**
- **A (recommended): offline.** Q3's RL arms are P8's R0 (FQI) and R1 (IQL), trained on logged real-node campaigns
  (B13) whose transitions carry this reward and these attributions; truncated episodes as in §3 (bootstrap at the last
  observed state). Matches plan §8/§13, where online RL is an extension.
- **B: offline, then on-policy fine-tuning** on training instances with the environment of §6; needs its own
  authorization and budget (every rollout is real worker runs).
- `train.reinforce` is a mechanism check only: a linear-softmax policy per phase, REINFORCE with a leave-one-out
  baseline, training-split instances only, only the policy's own decisions credited, truncated episodes dropped and
  counted (Monte Carlo), and a STOP when the cumulative truncation rate exceeds the declared level (after 20 draws) or
  when more than half of an iteration's draws truncate.

## 8. Requirements on the harness and the runner (later units; need host or cluster tests)

1. **No infrastructure reruns in RL:** the RL runner sets `max_infra_reruns = 0` and runs each code state once per
   `execute`; if a runner retries anyway, it returns every attempt (`prior_attempts`). It registers every executed code
   state as evaluated.
2. **Host evidence in the run record** from the parent or the scheduler: the HTCondor job event log (preemption by
   priority vs hold/remove for resource limits), the driver's Xid events, node drain, quota-protected filesystems.
   *Cluster test on NEMO2 H200.*
3. **Row server (RL-BUDGET A):** the frozen parent serves training rows and evaluation inputs over the result channel
   and writes the `{limit, served, refused_requests}` record; each kit's data loader requests them. *Host test per
   node kit.*
4. **cgroup CPU/GPU-time limit** per run, beside the measured timeout. *Host and cluster test.*
5. **Layout builder:** the worker's mount namespace built from the role manifest (RL-LAYOUT), `check_worker_root` run
   before every run, `shared_dev_shm` off (or a waiver); per node, the roles of every data file. *Host test per kit.*
6. **Declared run cost** per proposal (1 unless the runner's protocol says otherwise).
7. **Control rerun** of the start configuration (RL-INFRA B only), outside the policy's budget, reported per arm.
8. **B11 runner** implements `Runner` with `pc-` campaign ids and the Paper C seed blocks; it maps the harness's
   not-run statuses, invalid proposals and integrity STOPs as in §3.

## 9. Tests in this unit

`paperC/tests/test_realloop_skeleton.py` (41 tests, CPU, numpy only):
- every attribution row of §3 (hardware vs application Xids, priority preemption incl. as a measured timeout, OOM
  kill, trusted code, provisional timeout with host evidence) and the refusals (neutral, missing or untrusted control,
  unknown reason, a value on a non-ok run); first-attempt attribution with every attempt charged; the truncation
  imbalance STOP at its boundary;
- the three layouts with per-split directories and edited code; scan refusals (renamed label copy, label bytes in a
  code file, parent-only path as file and as directory, unplanned file, changed data, missing file, symlink, FIFO,
  socket, `shared_dev_shm` without a waiver); empty files; byte clashes at planning;
- the row server (contents, per-epoch order, refusal, `classify_run` priorities) and the campaign budget (W, N ≥ 1);
- the environment: training-split refusal; an honest episode's return equals the charged runs plus the audited
  increment; worker log patterns charged under both RL-INFRA options; a hidden reroll attributed to its first attempt;
  host truncation (`host`, `ret` 0); a STOP recorded as `protocol_stop`; an over-requesting worker that claims a high
  metric never reaches a keep; run costs of 2 with the controller's refusal; an undeclared run cost as a STOP; not-run
  proposals and duplicates rule-forced; W and N enforced;
- the trainer: split refusal; learning to discard a measured loss and to skip a predicted loss; the truncation-level
  STOPs.

## 10. Author decisions

```
rl_infra: <A host evidence | B control rerun of the start configuration>
rl_trunc_level: <proposed 0.05>
rl_layout: <A served (with RL-BUDGET A) | B train + val inputs | C train only>
rl_budget: <A parent-served rows + measured timeout + cgroup time limit | B wall time + cgroup time limit>
rl_algo: <A offline R0/R1 | B offline then on-policy fine-tuning>
shared_dev_shm_waivers: <none | node: row>
```
