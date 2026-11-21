# Paper C: multi-step RL on the real loop — design and code skeleton (draft for the author)

**Status: DRAFT, ENGINEERING_ONLY. Decides nothing; authorizes no run.** Written by the Mac-desk agent (Claude),
AI-assisted, on branch `mac-paperc-rl-20261121` from `paperc-plan-amend-20261119` @ `461ecae9`. Code:
`paperC/src/paperc/realloop/` (CPU only), tests `paperC/tests/test_realloop_skeleton.py`.

## 1. Why this unit

Paper C trains multi-step RL only after a passed go/no-go (addendum 19 Nov §A.1 item 5), and then compares it with
the strongest non-RL multi-step method (Q3). Its learners (P8: R0 FQI, R1 IQL, N6) are validated on E-SYN, where the
world is simulated. On the real loop the policy's reward comes from runs of edited code inside the isolated harness,
and the harness's own record names three limits that matter once a reward is attached
(`autoresearch/trackg/isolation.py`, READY 60 and 61 author points):

1. an infrastructure log pattern printed by the worker makes the run an `infrastructure_failure`, which the campaign
   reruns without registering the code state as evaluated — "an RL reward must not treat that class as neutral
   without the author's decision";
2. the worker can read every allow-listed path, so validation and test labels that a node keeps there;
3. the worker computes the training itself, so budget accounting stays in the editable process (only the wall time,
   the measured timeout, is enforced outside).

A policy optimised against such a reward can learn to exploit each of these (free reruns, label reads, extra
training within the time limit), directly or by steering the proposer. This unit states the rules that close them,
as author decisions, and implements them as a tested skeleton that the B11 real-loop runner and any RL route (offline
from logged campaigns, or online) must use.

## 2. Scope

- In: the reward and its attribution of run outcomes; the worker layout; budget enforcement; a multi-step environment
  over an injected runner; a tiny CPU trainer as a mechanism check.
- Out: the real runner (B11), real-node collection (B13), LM routes (B14), any change to Paper B's harness (the
  harness changes this design needs are listed in §8 as requirements, not made here).
- Paper B is untouched; nothing here touches Paper B's labels, seeds or tables.

## 3. Reward and attribution (RL-INFRA; `realloop/reward.py`)

Reward in σ_node units: per executing step −g × runs consumed; at the end of a terminated episode the audited
terminal increment (y_terminal − y_start)/σ_node (addendum 19 Nov §C: exhausting W or N is termination). A proposal
failure is charged like any run, gives no gain, and the code state counts as evaluated.

| Run (harness class / reason) | Attribution |
|---|---|
| `ok` | ok |
| `divergent` (any reason, incl. measured `timeout`, and `budget_exceeded` from §5) | proposal failure |
| `infrastructure_failure` / provisional `timeout` | STOP (RL uses measured timeouts only) |
| `infrastructure_failure` / `launch_error`, or any reason with parent-side host evidence, or on an unedited code state | truncate |
| `infrastructure_failure` / `infrastructure_log_pattern`, `killed`, `no_exit_status` on an edited state without host evidence | **RL-INFRA** |

**RL-INFRA (recommendation: A).**
- **A (recommended): host evidence.** Worker-producible infrastructure signals on an edited code state are proposal
  failures; only evidence the worker cannot write truncates: a launch error, a scheduler eviction or preemption, a
  GPU Xid, a node drain, a host disk-full seen by the parent. Cost: a genuine host fault without recorded evidence is
  charged to the proposal (a conservative error, reported as a count).
- **B: control rerun.** An ambiguous failure is resolved by rerunning the unedited incumbent in the same slot: if the
  control also fails as infrastructure, truncate; otherwise proposal failure. One extra run per ambiguous case
  (not charged to the policy), and a fault that clears between the two runs is charged to the proposal.
- **Neutral** (the harness's rerun-for-free) is refused by the code; it would need an author row.

**Truncation (RL-TRUNC).** Truncated episodes are never complete; they are dropped from training and evaluation and
counted per arm; a spread of truncation rates across arms above a declared level is a STOP (addendum 19 Nov §C).
*(proposed)* level 0.05.

## 4. Worker layout (RL-LAYOUT; `realloop/layout.py`)

Every data file of a node kit gets a role: code, frozen, train inputs, train labels, val inputs, val labels, test
inputs, test labels. `plan_worker_root` lists what the worker root may hold; `check_worker_root` scans a built root
and refuses a file with the bytes of a parent-only file (renamed or moved), a parent-only file name, a symlink, a file
outside the plan, or a planned file with changed bytes.

**RL-LAYOUT (recommendation: A).**
- **A (recommended): training split plus unlabelled validation inputs.** The parent keeps validation labels and all
  test files and scores the worker's answers to its evaluation requests. Labels are out of reach; the worker can
  still fit to the validation inputs (transductively), which the kits' probes narrow.
- **B: training split only.** The parent streams evaluation inputs through the result channel; closes the
  transductive route too; needs a harness change for every node (§8).
- The status quo (labels readable, disclosed) is not allowed for RL training (the code refuses it).

## 5. Budget enforcement (RL-BUDGET; `realloop/budget.py`)

**RL-BUDGET (recommendation: A).**
- **A (recommended): parent-served training examples plus the measured timeout.** The parent serves training example
  indices on request (through the result channel) in a fixed order, one permutation per epoch, and counts them; a
  request beyond examples × epochs is refused and the run becomes `divergent` / `budget_exceeded` (a proposal
  failure), whatever metric the worker reports. The worker can reuse examples it already received; the budget bounds
  data, the wall time bounds compute.
- **B: wall time plus a cgroup CPU/GPU-time limit only.** Compute is bounded, data use is not.
- **C: worker-reported step counts.** Not acceptable: the count is in the editable process.
- The campaign budget (W runs, N manager calls) is the controller's (`CampaignBudget`): the policy asks, the
  controller charges; an `execute` beyond W is turned into a skip; exhausting W or N terminates the episode.

## 6. Environment (`realloop/env.py`)

One episode = one campaign on one instance; at each proposal E1 (execute/skip), after an `ok` run E2 (keep/discard).
The controller attributes each run (§3), folds the parent's example record into it (§5), charges the budget and ends
the episode (terminated with the audited terminal reward; truncated without reward; STOP on a protocol STOP).
**Training-split only:** `mode="train"` refuses any instance outside the training split of the Paper C split (dev and
test campaigns only in `mode="eval"`). The `Runner` protocol is what B11 implements against the pinned harness.

## 7. Learning (RL-ALGO; `realloop/train.py`)

**RL-ALGO (recommendation: A).**
- **A (recommended): offline.** Q3's RL arms are P8's R0 (FQI) and R1 (IQL), trained on logged real-node campaigns
  (B13) whose transitions carry this reward and these attributions; truncated episodes are left out and counted.
- **B: offline, then on-policy fine-tuning** on training instances with the environment of §6; needs its own
  authorization and budget (every rollout is real worker runs).
- `train.reinforce` is a mechanism check only: a linear-softmax policy per phase, REINFORCE with a leave-one-out
  baseline, training-split instances only, truncated episodes dropped and counted, a STOP if every episode
  truncates.

## 8. Requirements on the harness and the runner (later units; need host or cluster tests)

1. **Host evidence in the run record:** the scheduler's eviction/preemption status, GPU Xid events and node drain
   from the parent or the scheduler (HTCondor job ad / event log; `nvidia-smi` Xid query), never from the worker's
   output. *Cluster test on NEMO2 H200.*
2. **Example server:** the frozen parent serves example indices over the result channel and writes the
   `{limit, served, refused_requests}` record; the worker kit's data loader requests them. *Host test per node kit.*
3. **Layout builder:** the runner builds the worker root from the role manifest and runs `check_worker_root` before
   every run; per node, the roles of every data file (where each kit keeps validation and test labels today).
   *Host test per node kit (T0 on CPU; T1 on the GPU host).*
4. **Control rerun** (RL-INFRA B only): a slot-local rerun of the incumbent outside the policy's budget.
5. **B11 runner** implements `Runner` (propose, run, control_rerun, audit) with `pc-` campaign ids and the Paper C
   seed blocks.

## 9. Tests in this unit

`paperC/tests/test_realloop_skeleton.py` (28 tests, CPU, numpy only): every attribution row of §3 and its refusals;
the truncation-imbalance STOP; the layout plans and every scan refusal; the example budget and the campaign budget;
the environment's training-split refusal, an honest episode, a worker that prints infrastructure patterns (charged,
never free), host-evidenced failures (truncated), a worker that over-requests examples and claims a high metric
(proposal failure, no keep), W enforced over the policy; the trainer's split refusal, learning to discard measured
losses on a toy runner, and the all-truncated STOP.

## 10. Author decisions

```
rl_infra: <A host evidence | B control rerun>
rl_trunc_level: <proposed 0.05>
rl_layout: <A train + val inputs | B train only>
rl_budget: <A parent-served examples + measured timeout | B wall time + cgroup limits>
rl_algo: <A offline R0/R1 | B offline then on-policy fine-tuning>
```
