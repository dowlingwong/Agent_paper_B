"""Track S record schema shared by the collector (``collect.py``) and the analysis (``analyze.py``).

AI-assisted (Claude, chat session, 29 Oct 2026). ENGINEERING_ONLY until a Track S
authorization exists. Runbook: docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md (rev. 3).

Units: every metric quantity is in the node's raw declared metric units (no normalisation).
Y_terminal is the mean over the K audit seeds of the final incumbent's audited metric.

One ``LeafRecord`` per (fork, arm, repetition). One ``RootRecord`` per root campaign.
Files: ``roots.jsonl``, ``leaves.jsonl``, ``manifest.json`` in one output directory per (node, phase).

Continuation (computed by the analysis, not stored):
    C = Y_terminal - immediate_measured
where ``immediate_measured`` is the audited increment of the fork trial's own edit over the
incumbent at the fork (mean over the same K audit seeds) if that edit was kept at the fork
trial, else 0.0. For skip/ghost/ctrl_only/discard it is 0.0 by construction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

TRACKS_LEAF_SCHEMA = "tracks_leaf/v1"
TRACKS_ROOT_SCHEMA = "tracks_root/v1"

Epoch = Literal["E1", "E2"]
Arm = Literal["skip", "execute", "ghost", "ctrl_only", "keep", "discard", "aa"]
E1_ARMS = ("skip", "execute", "ghost", "ctrl_only")
E2_ARMS = ("keep", "discard")
# Pre-declared state features for C-hat (runbook §3). Order is fixed.
STATE_FEATURES = (
    "budget_fraction",   # worker runs used / W at the fork
    "runs_left",         # W - runs used
    "trial_index",       # 1-based trial index of the fork trial
    "key_seen",          # 1.0 if the edited key was executed before in this campaign
    "prior_skips",       # E1 skips before the fork trial
    "keeps_so_far",      # keeps before the fork trial (trial 1 counted)
    "index_value",       # V-hat* at E1, m-hat at E2 (base controller's own forecast)
)


@dataclass
class Provenance:
    host: str                    # e.g. "TASL-2"
    gpu: str                     # e.g. "RTX 4090"
    harness_commit: str
    paper_commit: str
    manager_gguf_sha256: str
    llama_build: str             # llama.cpp commit + build flags
    controller_version: str      # e.g. "a2u/v1"
    prior_sha256: str            # A2-U prior file (S0.4)
    phase: str                   # "S0.4" | "S0.5" | "S3" | "S3d" | "synthetic" | "fixture"
    label: str                   # "ENGINEERING_ONLY" | "PILOT" | "EVIDENCE" | "FIXTURE"
    # Added 29 Oct (collector, rev.-4 amendment 2): the declared run price g and the pilot price g0 the
    # roots and continuations ran at (raw metric units); None in records written before the fields existed.
    g_declared: float | None = None
    g0: float | None = None
    # Added 29 Oct (review m3): checkout dirtiness at collection time (None = not recorded).
    harness_dirty: bool | None = None
    paper_dirty: bool | None = None


@dataclass
class Selection:
    uniform: bool                # drawn in the uniform sample
    oversample: bool             # drawn in the near-threshold oversample
    p_select: float              # inclusion probability of this fork (for IPW: w = 1/p_select)
    channel_arms: bool           # this E1 fork is in the random third that gets ghost/ctrl_only


@dataclass
class Forecast:
    pi: float | None
    mu: float | None
    tau: float | None
    sigma: float | None
    v_star: float | None         # E1 one-step value V-hat*_n (no price subtracted)
    m_hat: float | None          # E2 posterior mean of the increment given the result
    g: float                     # declared run price used by the myopic root controller


@dataclass
class LeafRecord:
    schema: str
    node: str
    instance_id: str             # cluster id (one per root campaign instance)
    root_id: str
    fork_id: str                 # unique per fork point
    epoch: str                   # "E1" | "E2"
    fork_trial_index: int
    arm: str                     # see Arm
    rep: int                     # 1 or 2
    llm_seed_base: int           # D26-style seed base of this repetition
    myopic_action: str           # what the root's myopic controller did at this fork ("execute"|"skip"|"keep"|"discard")
    selection: Selection
    state: dict[str, float]      # keys = STATE_FEATURES
    forecast: Forecast
    immediate_measured: float    # see module docstring
    y_terminal: float | None     # mean audited metric of the final incumbent
    y_terminal_per_seed: list[float | None]
    audit_seeds: list[int]
    runs_used: int               # worker runs used after the fork (incl. the fork trial's run if any)
    llm_calls: int
    keeps_after: int
    binding: bool                # W was exhausted before the LLM cap in this leaf
    nf_c_events: int             # later proposals whose duplicate status differs from the sibling arm (filled by analysis if 0)
    dup_filtered_due_to_fork: int  # later proposals filtered as duplicates because of the fork trial's config
    next_proposals: list[dict[str, Any]]  # first 3 proposals after the fork: {key, value, step, duplicate, noop}
    provenance: Provenance
    status: str = "ok"           # "ok" | "failed"
    error: str | None = None
    # Added 29 Oct (collector): A/A leaves only (arm "aa", rep 0): True iff the leaf's decisions after the fork
    # equal the root's (budget index, decision, proposal summary, metric); None for every other arm.
    aa_reproduced: bool | None = None
    # Added 29 Oct (rev.-4 amendment 3): the named policy of the continuation ("" = the root controller).
    policy: str = ""


@dataclass
class RootRecord:
    schema: str
    node: str
    instance_id: str
    root_id: str
    W: int
    llm_cap: int
    y_start: float | None        # audited start configuration
    y_after_trial1: float | None
    y_terminal: float | None
    eligible_e1: int
    eligible_e2: int
    binding: bool
    runs_used: int
    llm_calls: int
    decisions: list[dict[str, Any]] = field(default_factory=list)  # per trial: index, epoch, action, index_value, eligible
    provenance: Provenance | None = None
    status: str = "ok"
    error: str | None = None
    # Added 29 Oct (rev.-4 amendment 3): the named policy of the campaign, e.g. "a2u:g0" for roots,
    # "static:g=<x>,e2off=<y>" or "pi_prime:<model_file>" in the S3e "campaign" phase ("" = unspecified).
    policy: str = ""
    # Added 29 Oct (review M2): the D26 LLM repetition of the campaign (0 = the root repetition).
    rep: int = 0


def to_dict(rec) -> dict:
    return asdict(rec)


def leaf_from_dict(d: dict) -> LeafRecord:
    d = dict(d)
    d["selection"] = Selection(**d["selection"])
    d["forecast"] = Forecast(**d["forecast"])
    d["provenance"] = Provenance(**d["provenance"])
    return LeafRecord(**d)


def root_from_dict(d: dict) -> RootRecord:
    d = dict(d)
    if d.get("provenance") is not None:
        d["provenance"] = Provenance(**d["provenance"])
    return RootRecord(**d)
