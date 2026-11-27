"""E-SYN campaign simulator writing ``spt_transition/v1`` rows (build runbook P3, steps 3 and 6).

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

One campaign of an ``ESynWorld`` under a policy. The loop follows Paper B's governed loop as Track S runs it:

* slot t = 1 .. llm_cap: one proposal per slot (one LLM call, one slot), drawn from the Track S proposal law
  (``worlds.proposal_sequence``, decision-independent given the stream); a rule-detectable proposal is a
  rule-forced E1 ``skip`` (``rule_noop``); slot 1 is never rule-detectable, and its proposal is executed and kept
  (``rule_first_trial``), because there is no incumbent metric before it;
* E1 ``execute`` / ``skip``; an execute costs one run; when fewer than ``run_cost`` runs remain the campaign ends
  (reason ``W``), else after the last slot (reason ``llm_cap``);
* ``verify`` (config worlds): after an execute, while the candidate has fewer than ``max_obs`` measurements and a
  run remains, ``verify`` re-measures it or ``no_verify`` moves on to E2;
* E2 ``keep`` / ``discard``;
* ``reaudit`` (config worlds): after a keep, while the incumbent has fewer than ``max_obs`` measurements and a run
  remains, ``reaudit`` re-measures the incumbent or ``no_reaudit`` moves on. Re-audit is offered **only right after
  a keep** (the schema allows it anywhere between decisions), so its timing is not a decision here and a re-audit
  is in effect a post-keep verify of the new incumbent;
* ``final`` (config worlds): one ``select`` row among the kept configurations (``State.candidates``).

Belief model ``a2u`` (Track S A2-U, keyed mode): per key a conjugate normal posterior on theta from N(mu0, tau0^2),
updated after every executed proposal (``worlds.key_update``); E1 forecast (a, A) and V* = E[max(m_hat, 0)]; E2
m_hat = a + A / (A + s^2) (delta_hat - a), where s is the comparison sd (increment worlds: sig(kind); config worlds:
sigma_meas sqrt(1 / n_cand + 1 / n_inc), with n_inc = 0 for the exactly known start). Policies decide from these
state fields only (``obs_from_state``), so ``check_campaign`` can replay them.

**Stochastic policies** (``stochastic = True``) read ``obs["u"]``, a uniform keyed by
``[EPS_KEY, world code, i, step]`` (``decision_uniform``; key 60002, claimed in the seed registry); their rows log the
probability of the logged action and ``eps_seed = 60002``, so ``check_campaign`` replays them exactly.

**Privileged forecasts.** A policy with ``privileged = True`` (an oracle member that knows world parameters) gets
extra forecasts whose names start with ``privileged:``; only then are they written. The interaction world's
``privileged:interaction`` forecast carries in ``mu`` the complement value of keeping this key now, computed from
the true matrix M (sum of M[j][k] over keys k not yet in the incumbent; 0 once j is in it). Learner featurisers and
non-oracle baselines must exclude ``privileged:*`` forecasts (``PRIVILEGED_PREFIX``); a test checks that no
non-privileged policy's rows carry one.

**Fork continuations** (build runbook P6; plan §6 SPT-3; ``ForkSpec``). ``run_campaign(..., fork=ForkSpec(...))``
replays the root campaign under its behaviour policy up to the fork point (trial t_f, epoch E1 or E2), forces the
arm there (a ``forced`` row, ``rule = "fork_arm"``, no propensity, ``behaviour_action`` / ``behaviour_prob`` logged),
and runs the rest under the declared continuation policy (deterministic policies only). Randomness after the fork:

* proposals, sizes and proposal effects (eta) of trials t > t_f come from a continuation stream keyed by
  (fork point, continuation policy, replicate) and **shared by the arms**: common random numbers, as Track S
  (``worlds.proposal_sequence``: the root stream up to the fork trial, then the continuation's own stream; the
  collector's ``run_leaf``: the proposer seed depends on the replicate, not on the arm);
* every measurement made after the fork decision (the E1 execute arm's measurement and verifies at t_f, re-audits
  from t_f on, every later measurement, the terminal audits) comes from a stream keyed additionally by the arm.
  **This departs from Track S's analysis simulator** (``simulate_controls.Sim.run_leaf``), which shares the
  measurement stream between the arms and reuses the root's own measurement at the fork trial. The reason: in the
  real loop each arm's continuation is a separate worker run on a different configuration, so measurement noise is
  not shared. The convention sets the within-fork variance, so precision and power figures computed with it (P6
  validation) are conditional on it; an arm whose action equals the behaviour's is therefore not the root's own
  continuation;
* everything up to the fork decision is the root's, so the fork's first row reproduces the root's state.

Privileged forecasts in a fork follow the policy acting at each decision (the behaviour before the fork, the
continuation after it).

Keys: ``SeedSequence([60003, 1, world code, i, t_f, epoch code, continuation index, replicate])`` (proposals) and
``[60003, 2, ..., arm code]`` (measurements); sub-key 0 is the fork selection (``paperc.forks``); key 60003 is claimed
in the seed registry. Recorded fork rows (from the forced row on) carry ``branch_path =
["<fork_id>:<arm>:c<continuation index>:r<replicate>"]``, the root's campaign id, ``fork_id``, the fork design and
``policy.continuation_policy_id``. ``CampaignResult.immediate`` is the true increment of the forked candidate if it is
kept at t_f (the E1 execute arm's own E2, or the E2 keep arm), else 0: Track S's ``immediate`` without audit noise.

Campaign value: Y = true value of the final configuration minus y0 (no audit noise), as Track S's ``y_true``. The
recorded ``Terminal`` adds audit noise sigma_audit per audit seed.

Randomness: every draw of campaign i comes from ``numpy.random.SeedSequence([60001, world.code, i])`` (root key
60001 is claimed in the Paper C seed registry, block ``paperc_rng_keys``): a 128-bit integer from it seeds the
Track S ``Stream`` and ``theta_table``, and a spawned child seeds the verify / re-audit / audit draws. The recorded
``instance_seed`` is 50000 + i (``paperc_instances``), so a campaign is regenerated by
``run_campaign(world, policy, instance_seed - INSTANCE_BASE)``; the recorded ``audit_seed_block`` /
``audit_seeds`` (10,000,000 + n_audit i ..., ``paperc_audits``) are **nominal labels**: the audit noise comes from
the campaign's own generator. The oracle uses index ranges 1,000,000 + i (selection), 2,000,000 + i (evaluation)
and 3,000,000 + i (decomposition). These are numerically inside Paper B's ``tracks_oracle_*`` blocks, but they
only ever enter the Paper C root key, so the streams are disjoint from Track S's (different SeedSequence entropy).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Callable, Protocol

import numpy as np

from paperc import schema as S
from paperc.esyn import worlds as WD
from paperc.esyn.extra import ESynWorld

RNG_KEY = 60_001
INSTANCE_BASE = 50_000
AUDIT_BASE = 10_000_000
SELECT_BASE = 1_000_000
EVAL_BASE = 2_000_000
DECOMP_BASE = 3_000_000
MAX_RECORDED = 10_000
PRIVILEGED_PREFIX = "privileged:"
EPS_KEY = 60_002            # stochastic policies: per-decision uniforms (claimed in the seed registry)
FORK_KEY = 60_003           # fork design: selection (sub-key 0), continuation proposals (1), measurements (2)
EPOCH_CODE = {"E1": 1, "E2": 2}
ARM_CODE = {"execute": 1, "skip": 2, "keep": 3, "discard": 4}
FORK_ARMS = {"E1": ("execute", "skip"), "E2": ("keep", "discard")}
_PHI_INV = NormalDist().inv_cdf
_PHI = NormalDist().cdf


# ---------------------------------------------------------------- policy interface

class Policy(Protocol):
    name: str

    def act(self, obs: dict) -> tuple[str, float, str | None]:
        """(action, probability of that action, selected hash for final rows)."""


def decision_uniform(world_code: int, instance: int, step: int, key: int = EPS_KEY) -> float:
    """The uniform a stochastic policy uses at a decision: SeedSequence([key, world code, i, step]) with the logged
    ``eps_seed`` as key; ``behaviour_for`` recomputes it from a record (eps_seed, node, instance_seed -
    INSTANCE_BASE, step_index)."""
    ss = np.random.SeedSequence([int(key), int(world_code), int(instance), int(step)])
    return float(np.random.default_rng(ss).random())


def _code_of_node(node: str) -> int:
    import zlib
    return zlib.crc32(node.removeprefix("esyn_").encode()) & 0xFFFF


def obs_from_state(epoch: str, state: S.State, env: S.EnvContext) -> dict:
    """What a policy may read: decision-time state fields only (the same view ``check_campaign`` replays)."""
    f = state.forecasts.get("a2u")
    oi = state.forecasts.get(PRIVILEGED_PREFIX + "interaction")
    return {"epoch": epoch, "W": env.W, "llm_cap": env.llm_cap,
            "v_star": f.v_star if f else None, "m_hat": f.m_hat if f else None,
            "tau": f.tau if f else None, "sigma": f.sigma if f else None,
            "bonus": oi.mu if oi is not None and oi.mu is not None else 0.0,
            "runs_left": state.runs_left, "slots_left": state.slots_left, "calls_left": state.calls_left,
            "incumbent_obs": state.incumbent_obs, "candidate_obs": state.candidate_obs,
            "candidate_delta_hat": state.candidate_delta_hat, "keeps_so_far": state.keeps_so_far,
            "incumbent_hash": state.incumbent_hash, "key_seen": state.key_seen,
            "candidates": [(c.hash, c.recorded, c.obs) for c in state.candidates]}


def behaviour_for(policy: Policy) -> Callable[[S.DecisionView], tuple[str, float]]:
    """The replay hook for ``check_campaign(behaviour=...)``."""
    def replay(view: S.DecisionView) -> tuple[str, float]:
        ob = obs_from_state(view.identity.epoch, view.state, view.env)
        if getattr(policy, "stochastic", False):
            if view.eps_seed is None:                    # a stochastic row must name its randomisation key
                return "<missing eps_seed>", float("nan")
            ob["u"] = decision_uniform(_code_of_node(view.identity.node), view.instance_seed - INSTANCE_BASE,
                                       view.identity.step_index, view.eps_seed)
        a, p, _ = policy.act(ob)
        return a, p
    return replay


# ---------------------------------------------------------------- randomness

def campaign_seed(world: ESynWorld, instance: int) -> tuple[np.random.SeedSequence, int]:
    """The campaign's SeedSequence and the 128-bit integer seeding Track S's ``Stream`` and ``theta_table``."""
    ss = np.random.SeedSequence([RNG_KEY, world.code, int(instance)])
    return ss, int.from_bytes(ss.generate_state(4, dtype=np.uint32).tobytes(), "little")


class Draws:
    def __init__(self, world: ESynWorld, instance: int):
        ss, seed = campaign_seed(world, instance)
        n = world.llm_cap
        self.stream = WD.Stream(seed, n)
        self.tab = WD.theta_table(world.base, world.regime, seed, int(instance))
        rng = np.random.default_rng(ss.spawn(1)[0])
        self.eps_v = rng.standard_normal((n + 2, world.max_obs))     # verify measurements
        self.eps_r = rng.standard_normal((n + 2, world.max_obs))     # re-audit measurements
        self.z_audit = rng.standard_normal(world.n_audit)
        self.z_start = rng.standard_normal(world.n_audit)


@dataclass(frozen=True)
class ForkSpec:
    """One fork continuation: force ``arm`` at the ``epoch`` decision of trial ``trial`` and continue under
    ``continuation`` (replicate ``replicate`` of continuation policy number ``cont_index``)."""
    trial: int
    epoch: str
    arm: str
    continuation: object
    cont_index: int = 0
    replicate: int = 1
    fork_id: str | None = None
    design: S.ForkDesign | None = None

    def __post_init__(self) -> None:
        if self.epoch not in FORK_ARMS or self.arm not in FORK_ARMS[self.epoch]:
            raise ValueError(f"fork arm {self.arm!r} not allowed at {self.epoch!r}")
        if self.replicate < 1 or self.cont_index < 0 or self.trial < 2:
            raise ValueError("fork: replicate >= 1, cont_index >= 0, trial >= 2 (trial 1 is rule-forced)")
        if getattr(self.continuation, "stochastic", False):
            raise ValueError("fork continuations use deterministic policies")

    @property
    def branch(self) -> str:
        return f"{self.fork_id}:{self.arm}:c{self.cont_index}:r{self.replicate}"


def fork_seed(world: ESynWorld, instance: int, trial: int, epoch: str, sub: int, *rest: int) -> np.random.SeedSequence:
    return np.random.SeedSequence([FORK_KEY, int(sub), world.code, int(instance), int(trial), EPOCH_CODE[epoch],
                                   *(int(x) for x in rest)])


class ForkDraws:
    """Randomness after a fork decision (see the module docstring)."""

    def __init__(self, world: ESynWorld, instance: int, f: ForkSpec):
        n = world.llm_cap
        ss = fork_seed(world, instance, f.trial, f.epoch, 1, f.cont_index, f.replicate)
        self.stream = WD.Stream(int.from_bytes(ss.generate_state(4, dtype=np.uint32).tobytes(), "little"), n)
        rng = np.random.default_rng(fork_seed(world, instance, f.trial, f.epoch, 2, f.cont_index, f.replicate,
                                              ARM_CODE[f.arm]))
        self.eps = rng.standard_normal(n + 2)
        self.eps_v = rng.standard_normal((n + 2, world.max_obs))
        self.eps_r = rng.standard_normal((n + 2, world.max_obs))
        self.z_audit = rng.standard_normal(world.n_audit)


def _size(world: ESynWorld, p: WD.Proposal, stream: WD.Stream) -> float:
    if not world.sizes or p.kind != "filler":
        return p.size
    u = _PHI(float(stream.z_size[p.t]))
    acc = 0.0
    for s, q in zip(world.sizes, world.size_probs):
        acc += q
        if u < acc:
            return float(s)
    return float(world.sizes[-1])


def _key_index(world: ESynWorld, key: int) -> int | None:
    """Recurring key -> 0 .. n_keys - 1 (interaction matrix index); None for fresh, probe and follow-up keys."""
    i = key - (world.llm_cap + 2)
    return i if world.base.n_keys > 0 and 0 <= i < world.base.n_keys else None


# ---------------------------------------------------------------- results

@dataclass
class CampaignResult:
    Y: float
    runs_used: int
    calls_used: int
    end_reason: str
    decisions: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    immediate: float | None = None      # fork continuations: the forked candidate's true increment if kept, else 0
    fork_step: int | None = None        # fork continuations: step index of the forced row


# ---------------------------------------------------------------- the campaign

def run_campaign(world: ESynWorld, policy: Policy, instance: int, *, record: bool = False,
                 label: str = "ENGINEERING_ONLY", phase: str = "P3", trace: list | None = None,
                 fork: ForkSpec | None = None) -> CampaignResult:
    """One campaign, or one fork continuation of it (``fork``; ``policy`` is then the root's behaviour policy).
    ``trace`` (tests): receives one dict per executed proposal with the true quantities."""
    w, base = world, world.base
    if record and not 0 <= int(instance) < MAX_RECORDED:
        raise ValueError(f"recorded campaigns use instances 0 .. {MAX_RECORDED - 1} (seed blocks)")
    if fork is not None and record and (fork.design is None or not fork.fork_id or ":" in fork.fork_id):
        raise ValueError("recorded fork continuations need a design and a fork_id without ':'")
    stochastic = bool(getattr(policy, "stochastic", False))
    cur = policy
    forked = False
    immediate = 0.0 if fork is not None else None
    fork_step = None
    d = Draws(w, instance)
    fd = ForkDraws(w, instance, fork) if fork is not None else None
    tf = fork.trial if fork is not None else None
    props = WD.proposal_sequence(base, w.regime, d.tab, d.stream if fd is None else [(1, d.stream), (tf + 1, fd.stream)])

    def pstream(t: int) -> WD.Stream:          # proposal-side draws of trial t
        return fd.stream if fd is not None and t > tf else d.stream

    def after_e1(t: int) -> bool:              # a measurement of trial t before its E2 comes after the fork decision
        return fd is not None and (t > tf or (t == tf and fork.epoch == "E1"))

    def after_e2(t: int) -> bool:              # a measurement of trial t after its E2 comes after the fork decision
        return fd is not None and t >= tf
    cap, W = w.llm_cap, w.W
    sig_m = w.sigma_meas
    config = w.comparison == "config"
    M = w.interaction

    runs = calls = keeps = skips = 0
    slots_left = cap
    inc_hash, inc_true = "c0", base.y0
    inc_meas: list[float] = []            # config: measurement errors of the incumbent
    inc_rec, inc_obs = base.y0, 0         # the start's value is known exactly (Track S meta y0)
    kept_keys: set[int] = set()
    keep_log: list = []                   # P2 feedback records
    posts: dict[int, tuple[float, float]] = {}
    prior = (base.mu0, base.tau0 ** 2)
    chain: dict[str, list] = {}           # kept configurations: hash -> [true value, measurement errors]
    rows: list[dict] = []
    decisions: list = []
    step = 0
    end_reason = "llm_cap"

    env = S.EnvContext(proposer_model="scripted", manager_gguf_sha256=None, thinking="n/a", W=W, llm_cap=cap,
                       memory_mode="none", skip_display="n/a", edit_schema="synthetic", run_budget="synthetic",
                       constants={"run_cost": float(w.run_cost), "mu0": base.mu0, "tau0": base.tau0,
                                  "sigma_eta": base.sigma_eta, "sigma_cmp": base.sigma_cmp, "y0": base.y0,
                                  "p_rule": w.regime.p_rule, "sigma_audit": w.regime.sigma_audit})
    node = f"esyn_{w.name}"
    inst_seed = INSTANCE_BASE + int(instance) if record else int(instance)
    camp_id = f"pc-esyn-{w.name}-{policy.name}-{inst_seed}"
    audit_lo = AUDIT_BASE + w.n_audit * int(instance)
    seeds = S.Seeds(instance_seed=inst_seed, manager_rep=0, worker_seed=None,
                    audit_seed_block=[audit_lo, audit_lo + w.n_audit - 1])
    prov = S.Provenance(host="esyn", gpu=None, harness_commit=None, paper_commit=None, llama_build=None,
                        cache_prompt=None, phase=phase, label=label, controller_version="paperc.esyn.sim/v1")

    def state(*, prop_hash, cand_hash, rule_forced, noop=False, key_seen=False, cand_dhat=None, cand_obs=0,
              forecasts=None, candidates=()):
        return S.State(proposal_hash=prop_hash, proposal_ref=None, candidate_hash=cand_hash, duplicate=False,
                       noop=noop, eligible=not rule_forced, rule_forced=rule_forced, key_seen=key_seen,
                       incumbent_hash=inc_hash, incumbent_recorded=inc_rec, incumbent_obs=inc_obs,
                       candidate_delta_hat=cand_dhat, candidate_divergent=False, candidate_invalid=False,
                       candidate_obs=cand_obs, runs_used=runs, runs_left=W - runs, calls_used=calls,
                       calls_left=cap - calls, slots_left=slots_left, keeps_so_far=keeps, prior_skips=skips,
                       sigma_node=base.sigma_cmp, noise_source="esyn", history_ref=None,
                       forecasts=forecasts or {}, candidates=[S.Candidate(*c) for c in candidates])

    def obs_direct(epoch, *, fc=None, oi_mu=0.0, cand_dhat=None, cand_obs=0, candidates=(), key_seen=False):
        return {"epoch": epoch, "W": W, "llm_cap": cap,
                "v_star": fc.v_star if fc else None, "m_hat": fc.m_hat if fc else None,
                "tau": fc.tau if fc else None, "sigma": fc.sigma if fc else None, "bonus": oi_mu,
                "runs_left": W - runs, "slots_left": slots_left, "calls_left": cap - calls,
                "incumbent_obs": inc_obs, "candidate_obs": cand_obs, "candidate_delta_hat": cand_dhat,
                "keeps_so_far": keeps, "incumbent_hash": inc_hash, "key_seen": key_seen,
                "candidates": list(candidates)}

    def decide(epoch, st, ob, forced_rule=None, forced_action=None):
        if forced_rule is not None:
            return forced_action, 1.0, None, forced_rule
        ob = obs_from_state(epoch, st, env) if record else ob
        if stochastic and not forked:
            ob["u"] = decision_uniform(w.code, instance, step)
        a, p, sel = cur.act(ob)
        return a, p, sel, "policy"

    def fork_here(epoch, t, st, ob, rule_forced):
        """At the fork point: the behaviour's own decision (logged), then the forced arm; switch policies."""
        nonlocal forked, cur, fork_step
        if rule_forced:
            raise ValueError(f"fork point trial {t} {epoch} is rule-forced, not eligible")
        b_act, b_prob, _, _ = decide(epoch, st, ob)
        forked, cur, fork_step = True, fork.continuation, step
        return b_act, b_prob

    def emit(epoch, st, action, prob, rule, outcome, selected=None, forced=False, b_act=None, b_prob=None):
        nonlocal step
        decisions.append((epoch, action))
        if record and (fork is None or forked):
            # The forced row carries the replayed behaviour state. The continuation acts after it.
            pol = policy if forced else cur
            rows.append(S.Transition(
                schema=S.SCHEMA,
                identity=S.Identity(node=node, suite="E-SYN", tier="E-SYN", instance_id=f"{node}:{inst_seed}",
                                    campaign_id=camp_id, step_index=step, epoch=epoch,
                                    branch_path=[fork.branch] if fork is not None else [],
                                    root_id=camp_id, fork_id=fork.fork_id if fork is not None else None),
                env=env, policy=S.PolicyInfo(policy=pol.name, policy_sha=getattr(pol, "sha", None),
                                             action_prob=None if forced else prob,
                                             eps_seed=EPS_KEY if stochastic and fork is None else None,
                                             continuation_policy_id=fork.continuation.name if fork is not None else None,
                                             behaviour_action=b_act, behaviour_prob=b_prob),
                seeds=seeds, state=st, action=S.Action(action=action, forced=forced, rule=rule, selected=selected),
                outcome=outcome, provenance=prov, fork=fork.design if fork is not None else None))
        step += 1

    def comparison_sd(n_c: int, n_i: int, kind: str) -> float:
        if not config:
            return base.sig(kind)
        return sig_m * math.sqrt(1.0 / n_c + (1.0 / n_i if n_i > 0 else 0.0))

    for p in props:
        t = p.t
        if W - runs < w.run_cost:
            end_reason = "W"
            break
        ph, ch = f"p{t}", f"c{t}"
        if p.rule and fork is not None and not forked and t == tf:
            raise ValueError(f"fork point trial {t} {fork.epoch} is rule-forced, not eligible")
        if p.rule:
            st = state(prop_hash=ph, cand_hash=ch, rule_forced=True, noop=True) if record else None
            emit("E1", st, "skip", 1.0, "rule_noop",
                 S.Outcome(runs_consumed=0, calls_consumed=1, next_incumbent_hash=inc_hash) if record else None)
            calls += 1
            slots_left -= 1
            skips += 1
            continue
        size = _size(w, p, pstream(t))
        kidx = _key_index(w, p.key)
        post = posts.get(p.key, prior)
        a, A_ = WD.key_forecast(post, size, p.off, base.sigma_eta)
        s1 = comparison_sd(1, inc_obs, p.kind)
        fc = S.Forecast(pi=None, mu=a, tau=math.sqrt(A_), sigma=s1, v_star=WD.v_star(a, A_, s1), m_hat=None)
        first = t == 1
        key_seen = p.key in posts
        st = state(prop_hash=ph, cand_hash=ch, rule_forced=first, key_seen=key_seen,
                   forecasts={"a2u": fc}) if record else None
        ob1 = obs_direct("E1", fc=fc, key_seen=key_seen)
        fx = {}
        if fork is not None and not forked and t == tf and fork.epoch == "E1":
            b_act, b_prob = fork_here("E1", t, st, ob1, first)
            act, prob, rule, fx = fork.arm, None, "fork_arm", {"forced": True, "b_act": b_act, "b_prob": b_prob}
        else:
            act, prob, _, rule = decide("E1", st, ob1, *(("rule_first_trial", "execute") if first else ()))
        if act == "skip":
            emit("E1", st, "skip", prob, rule,
                 S.Outcome(runs_consumed=0, calls_consumed=1, next_incumbent_hash=inc_hash) if record else None, **fx)
            calls += 1
            slots_left -= 1
            skips += 1
            continue
        # execute: the true increment given the incumbent's keep log and kept keys
        th = WD.theta(base, w.regime, d.tab, p.key, t, keep_log)
        delta = size * (th - p.off) + base.sigma_eta * float(pstream(t).eta[t])
        inter = 0.0
        if M and kidx is not None and kidx not in kept_keys:
            inter = float(sum(M[i][kidx] for i in kept_keys))
            delta += inter
        cand_true = inc_true + delta
        if trace is not None:
            trace.append({"t": t, "key": p.key, "kidx": kidx, "size": size, "theta": th, "interaction": inter,
                          "delta": delta, "kept_keys": sorted(kept_keys), "inc_true": inc_true})
        e_meas = float(fd.eps[t] if after_e1(t) else d.stream.eps[t])
        if config:
            cand_meas = [sig_m * e_meas]
            dhat_single = cand_true + cand_meas[0] - inc_rec
        else:
            cand_meas = []
            dhat_single = delta + base.sig(p.kind) * e_meas
        dhat = dhat_single
        emit("E1", st, "execute", prob, rule,
             S.Outcome(runs_consumed=1, calls_consumed=1, next_incumbent_hash=inc_hash, delta_hat=dhat_single)
             if record else None, **fx)
        runs += 1
        calls += 1
        slots_left -= 1
        n_c = 1

        def e2_forecast():
            sc = comparison_sd(n_c, inc_obs, p.kind)
            m_hat = a + A_ / (A_ + sc * sc) * (dhat - a)
            return S.Forecast(pi=None, mu=a, tau=math.sqrt(A_), sigma=sc,
                              v_star=WD.v_star(a, A_, sc), m_hat=m_hat), sc

        # verify loop
        while "verify" in w.epochs and not first and n_c < w.max_obs and W - runs >= w.run_cost:
            fc2, _ = e2_forecast()
            st = state(prop_hash=ph, cand_hash=ch, rule_forced=False, key_seen=key_seen, cand_dhat=dhat,
                       cand_obs=n_c, forecasts={"a2u": fc2}) if record else None
            act, prob, _, rule = decide("verify", st, obs_direct("verify", fc=fc2, cand_dhat=dhat, cand_obs=n_c,
                                                                 key_seen=key_seen))
            if act == "no_verify":
                emit("verify", st, "no_verify", prob, rule,
                     S.Outcome(runs_consumed=0, calls_consumed=0, next_incumbent_hash=inc_hash) if record else None)
                break
            e = sig_m * float((fd.eps_v if after_e1(t) else d.eps_v)[t, n_c - 1])
            single = cand_true + e - inc_rec
            emit("verify", st, "verify", prob, rule,
                 S.Outcome(runs_consumed=1, calls_consumed=0, next_incumbent_hash=inc_hash, delta_hat=single)
                 if record else None)
            runs += 1
            cand_meas.append(e)
            n_c += 1
            dhat = cand_true + float(np.mean(cand_meas)) - inc_rec

        # E2
        fc2, sc = e2_forecast()
        oi = {}
        bonus = 0.0
        if M and kidx is not None and getattr(cur, "privileged", False):
            bonus = 0.0 if kidx in kept_keys else float(sum(M[kidx][k] for k in range(len(M))
                                                            if k not in kept_keys and k != kidx))
            oi = {PRIVILEGED_PREFIX + "interaction": S.Forecast(pi=None, mu=bonus, tau=None, sigma=None, v_star=None,
                                                               m_hat=None)}
        st = state(prop_hash=ph, cand_hash=ch, rule_forced=first, key_seen=key_seen, cand_dhat=dhat, cand_obs=n_c,
                   forecasts={"a2u": fc2, **oi}) if record else None
        ob2 = obs_direct("E2", fc=fc2, oi_mu=bonus, cand_dhat=dhat, cand_obs=n_c, key_seen=key_seen)
        fx = {}
        if fork is not None and not forked and t == tf and fork.epoch == "E2":
            b_act, b_prob = fork_here("E2", t, st, ob2, first)
            act, prob, rule, fx = fork.arm, None, "fork_arm", {"forced": True, "b_act": b_act, "b_prob": b_prob}
        else:
            act, prob, _, rule = decide("E2", st, ob2, *(("rule_first_trial", "keep") if first else ()))
        keep = act == "keep"
        if fork is not None and t == tf and keep:
            immediate = cand_true - inc_true
        if trace is not None:
            trace[-1].update({"a": a, "A": A_, "v_star": fc.v_star, "tau": fc.tau, "sigma1": fc.sigma,
                              "m_hat": fc2.m_hat, "sigma": sc, "dhat": dhat, "kept": keep, "first": first,
                              "runs_left_e1": W - runs + (n_c), "slots_left_e1": slots_left + 1})
        emit("E2", st, act, prob, rule,
             S.Outcome(runs_consumed=0, calls_consumed=0, next_incumbent_hash=ch if keep else inc_hash, kept=keep)
             if record else None, **fx)
        posts[p.key] = WD.key_update(post, size, dhat, p.off, base.sigma_eta, sc)
        if not keep:
            continue
        # keep: the incumbent becomes the candidate
        entry = WD.keep_log_entry(base, t, runs, W)
        if entry is not None:
            keep_log.append(entry)
        if kidx is not None:
            kept_keys.add(kidx)
        keeps += 1
        inc_hash, inc_true = ch, cand_true
        if config:
            inc_meas = list(cand_meas)
            inc_rec, inc_obs = inc_true + float(np.mean(inc_meas)), len(inc_meas)
        else:
            inc_rec, inc_obs = inc_rec + dhat, 1
        chain[ch] = [inc_true, inc_meas]

        # re-audit loop
        k = 0
        while "reaudit" in w.epochs and inc_obs < w.max_obs and W - runs >= w.run_cost:
            st = state(prop_hash=f"r{t}.{k}", cand_hash=None, rule_forced=False) if record else None
            act, prob, _, rule = decide("reaudit", st, obs_direct("reaudit"))
            if act == "no_reaudit":
                emit("reaudit", st, "no_reaudit", prob, rule,
                     S.Outcome(runs_consumed=0, calls_consumed=0, next_incumbent_hash=inc_hash) if record else None)
                break
            e = sig_m * float((fd.eps_r if after_e2(t) else d.eps_r)[t, k])
            single = inc_true + e - inc_rec
            emit("reaudit", st, "reaudit", prob, rule,
                 S.Outcome(runs_consumed=1, calls_consumed=0, next_incumbent_hash=inc_hash, delta_hat=single)
                 if record else None)
            runs += 1
            inc_meas.append(e)
            inc_rec, inc_obs = inc_true + float(np.mean(inc_meas)), len(inc_meas)
            chain[inc_hash] = [inc_true, list(inc_meas)]
            k += 1
    else:
        end_reason = "W" if W - runs < w.run_cost else "llm_cap"

    if fork is not None and not forked:
        raise ValueError(f"fork point trial {tf} {fork.epoch} was not reached (the root skipped it or ended)")
    y_final = inc_true
    if "final" in w.epochs:
        cands = [(h, v + float(np.mean(m)) if m else None, len(m)) for h, (v, m) in chain.items()]
        st = state(prop_hash="final", cand_hash=None, rule_forced=False, candidates=cands) if record else None
        act, prob, sel, rule = decide("final", st, obs_direct("final", candidates=cands))
        sel = sel or inc_hash
        emit("final", st, "select", prob, rule,
             S.Outcome(runs_consumed=0, calls_consumed=0, next_incumbent_hash=sel) if record else None,
             selected=sel)
        y_final = chain[sel][0] if sel in chain else base.y0
    Y = y_final - base.y0

    if record and rows:
        last = rows[-1]
        aud = [audit_lo + i for i in range(w.n_audit)]
        per = [y_final + w.regime.sigma_audit * float(z) for z in (fd.z_audit if fd is not None else d.z_audit)]
        start = [base.y0 + w.regime.sigma_audit * float(z) for z in d.z_start]
        last.episode_end = S.EpisodeEnd(kind="terminated", reason=end_reason)
        last.terminal = S.Terminal(y_terminal=float(sum(per) / len(per)), y_terminal_per_seed=per, audit_seeds=aud,
                                   y_start=float(sum(start) / len(start)))
    return CampaignResult(Y=Y, runs_used=runs, calls_used=calls, end_reason=end_reason, decisions=decisions,
                          rows=[S.to_dict(r) for r in rows] if record else [], immediate=immediate,
                          fork_step=fork_step)


def campaign_values(world: ESynWorld, policy: Policy, instances) -> np.ndarray:
    return np.array([run_campaign(world, policy, i).Y for i in instances])
