"""Round 5 TITAN compact-exam gates, topology profiles and ranking rules.

Everything here is pure: it consumes recorded numbers and returns reasons. It is
kept out of the scripts so that each rule can be tested directly, and so that
there is exactly ONE implementation of each rule rather than a registry-driven
path and a hard-coded fallback that disagree.

Nothing in this module starts a server, downloads an artifact, materialises a
manifest, or issues a model request.

Why a new module rather than parameters on ``round4_qualification``
------------------------------------------------------------------
Round 4 froze *two* workers on *two* L40 cards over *1000* roots in *200 x 5*
shape, and several of its guards are written as equalities against those
numbers. Widening those equalities into parameters would have deleted the
guards, because a guard that accepts any worker count is not a guard. The Round
4 module therefore keeps its constants and its verdicts exactly as they are, and
Round 5 states its own. The three rules that are genuinely round-independent --
the trajectory-depth population, censoring classification, and canary drift --
are imported from Round 4 and re-exported here, so a Round 5 caller never has to
reach into a Round 4 namespace and pick up a Round 4 constant by accident.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

#: The repository root, so a protocol artifact can name evidence by its
#: repository-relative path and a checker can resolve it without a flag.
REPO_ROOT = Path(__file__).resolve().parents[3]


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

# Round-independent rules, imported rather than reimplemented. Re-exported so
# that Round-5 code imports Round-5 names only.
from causal_branch.round4_qualification import (  # noqa: F401
    assess_canary_drift,
    classify_censoring,
    gguf_conversion_blockers,
    summarize_trajectory_depth,
)

# --------------------------------------------------------------------------
# Identity of this exam
# --------------------------------------------------------------------------

PROTOCOL_NAME = "round5_titan_compact_exam_v1"
EXAM_POOL = "model_selection_round5_titan_compact"
EXAM_MANIFEST_KIND = "round5_titan_compact_exam_manifest_candidate"
EXAM_GENERATION_RECORD_KIND = "round5_titan_compact_exam_generation_record"
REGISTRY_KIND = "round5_titan_candidate_registry_candidate"
STAGE_A_ARTIFACT_KIND = "round5_titan_stage_a_compatibility"
STAGE_B_ARTIFACT_KIND = "round5_titan_stage_b_compact_exam"
STAGE_B_PLAN_KIND = "round5_titan_stage_b_execution_plan"
SELECTION_ARTIFACT_KIND = "round5_titan_cross_candidate_selection"
SELECTION_REFUSED_KIND = "round5_titan_cross_candidate_selection_refused"
READINESS_ARTIFACT_KIND = "round5_titan_zero_model_call_readiness"
EVIDENCE_MANIFEST_KIND = "round5_titan_evidence_manifest"
APPENDIX_ARTIFACT_KIND = "round5_titan_appendix_render"

# The L40S predecessor is preserved and never ranked. Any artifact carrying one
# of these markers is refused by the selector rather than quietly pooled.
# Paths whose mere presence in a Stage-B invocation means a PREDECESSOR round's
# artifact is being ranked. Each marker names a specific superseded artifact.
#
# `model_selection` alone used to be in this list, and it matched the Round-5
# TITAN compact manifest's own canonical path --
# `protocols/model_selection_round5_titan_exam_manifest_candidate.yaml` -- so
# Stage B refused every candidate with
# `non_ranking_predecessor_artifact:model_selection` and the exam could never
# run at all. The bare substring is replaced by the specific predecessors it was
# meant to catch; nothing it actually guarded against is now allowed.
#
# This is the SECOND line of defence, not the only one: `manifest_blockers`
# already requires `artifact_kind == round5_titan_compact_exam_manifest_candidate`,
# and every predecessor manifest declares a different kind.
NON_RANKING_PREDECESSOR_MARKERS = (
    "round4_l40",
    "model_selection_round4_l40",
    "l40",
    "L40",
    "wp3_baseline_model_qualification",
    "wp3_baseline_model_four_root_smoke",
    "model_selection_round2",
    "model_selection_round3",
    "model_selection_round5_replacement",
    "model_selection_round5_manifest",
    "round5_replacement_manifest",
    "round5_compact_exam_manifest",
)
SUPERSEDED_POOLS = (
    "model_selection",
    "model_selection_round2",
    "model_selection_round3",
    "model_selection_round4_l40",
)

# --------------------------------------------------------------------------
# Hardware -- the host a registry declares it is for
# --------------------------------------------------------------------------
#
# The exam is defined independently of the accelerator it runs on, but a
# candidacy VERDICT is not. A wall rail converts generation speed into a
# condition on measurability, so the same arm can return an instrument
# nonverdict on one card class and a clean measurement on another. The host
# gates below therefore read the hardware the registry DECLARES rather than
# assuming the Titan host, and hold the live machine to that declaration.
#
# The Titan names stay as module constants because they are the default and
# because existing artifacts and tests refer to them by name.

TITAN_GPU_COUNT = 4
TITAN_GPU_NAME_FRAGMENT = "TITAN X"
TITAN_COMPUTE_CAPABILITY = "5.2"
TITAN_CUDA_ARCHITECTURE = "52"
TITAN_MEMORY_MIB = 12288
TITAN_MEMORY_TOLERANCE_MIB = 64
TITAN_NVLINK_ASSUMED = False
TITAN_P2P_ASSUMED = False

#: Registry-declared hardware identifiers.
HARDWARE_TITAN = "titan_x_4x12gib"
HARDWARE_L40 = "l40_2x48gib"
HARDWARE_BLACKWELL = "rtx_pro_6000_blackwell_2x96gib"
#: Two cards LEASED from an eight-card shared host. The name says both
#: halves on purpose: what the exam holds, and that it does not hold the
#: machine.
HARDWARE_ADA_LEASED = "rtx_6000_ada_2x48gib_leased"
DEFAULT_HARDWARE = HARDWARE_TITAN

#: What the LIVE host must be for each declared hardware profile. `nvidia-smi`
#: reports an L40 and an L40S alike as 46,068 MiB, and the `L40` fragment
#: matches both, which is intended: the exam does not distinguish them, and a
#: registry that means one specifically must pin the UUIDs.
HOST_SPECS: dict[str, dict[str, Any]] = {
    HARDWARE_TITAN: {
        "hardware": HARDWARE_TITAN,
        "gpu_count": TITAN_GPU_COUNT,
        "gpu_name_fragment": TITAN_GPU_NAME_FRAGMENT,
        "compute_capability": TITAN_COMPUTE_CAPABILITY,
        "cuda_architecture": TITAN_CUDA_ARCHITECTURE,
        "memory_total_mib": TITAN_MEMORY_MIB,
        "memory_tolerance_mib": TITAN_MEMORY_TOLERANCE_MIB,
        "nvlink_assumed": TITAN_NVLINK_ASSUMED,
        "p2p_assumed": TITAN_P2P_ASSUMED,
        "not_a": "titan_x",
    },
    HARDWARE_L40: {
        "hardware": HARDWARE_L40,
        "gpu_count": 2,
        "gpu_name_fragment": "L40",
        "compute_capability": "8.9",
        "cuda_architecture": "89",
        "memory_total_mib": 46068,
        # Wider than the Titan tolerance on purpose: ECC state and vBIOS
        # revision move the reported total on these cards by a few hundred MiB,
        # and a readiness gate that fails on that is a gate people learn to
        # pass with a flag.
        "memory_tolerance_mib": 1024,
        "nvlink_assumed": False,
        "p2p_assumed": False,
        "not_a": "l40",
    },
    HARDWARE_BLACKWELL: {
        "hardware": HARDWARE_BLACKWELL,
        "gpu_count": 2,
        "gpu_name_fragment": "RTX PRO 6000 Blackwell",
        "compute_capability": "12.0",
        "cuda_architecture": "120",
        # Observed directly on the target host with NVIDIA-SMI 595.71.05.
        "memory_total_mib": 97887,
        "memory_tolerance_mib": 1024,
        "nvlink_assumed": False,
        "p2p_assumed": False,
        "not_a": "rtx_pro_6000_blackwell",
    },
    HARDWARE_ADA_LEASED: {
        "hardware": HARDWARE_ADA_LEASED,
        # The number of cards the exam HOLDS, not the number the host has. For
        # this profile `host_blockers` is given the leased cards and the host's
        # true size separately, because there is no longer one number that means
        # both -- and pretending there is, is how a two-card lease on an
        # eight-card box would come to be described as a two-card machine.
        "gpu_count": 2,
        "gpu_name_fragment": "RTX 6000 Ada",
        "compute_capability": "8.9",
        "cuda_architecture": "89",
        # Observed on ucrtasl, driver 545.23.08 / CUDA 12.3, 2026-09-02.
        "memory_total_mib": 49140,
        "memory_tolerance_mib": 1024,
        "nvlink_assumed": False,
        "p2p_assumed": False,
        "not_a": "rtx_6000_ada",
        # The flag that turns off the whole-host identity check, and the reason
        # it has to be written down rather than inferred. Every other profile
        # can assert "this host IS the declared machine". This one can only
        # assert "these two cards are the declared cards, and six others we do
        # not control are in the same chassis". Timing evidence from this
        # profile must be read with that in view.
        "shared_host": True,
        "shared_host_note": (
            "two cards leased from a multi-tenant host; neighbouring cards are "
            "outside the exam's control and share the chassis power and cooling "
            "budget, so decode throughput is not constant across the run"),
    },
}


def host_spec(hardware: str | None = None) -> dict[str, Any]:
    """The live-host requirements for a declared hardware profile."""
    key = str(hardware or DEFAULT_HARDWARE)
    if key not in HOST_SPECS:
        raise Round5GuardFailure(f"unknown hardware profile: {key}")
    return dict(HOST_SPECS[key])

# Occupancy canary. A timed stage never starts on a contaminated host, and the
# manager waits rather than running. It never kills a process it did not start.
OCCUPANCY_MAX_UTILISATION_PERCENT = 5.0
OCCUPANCY_MAX_BASELINE_VRAM_MIB = 64
TIMING_CONTAMINATED_NONVERDICT = "TIMING_CONTAMINATED_NONVERDICT"

#: GPU monitoring evidence could not be obtained, or could not be trusted:
#: the inventory query failed, the process query failed, the XML was malformed,
#: or either returned incomplete evidence about a host we know has cards.
#:
#: A SHARED ENVIRONMENTAL nonverdict, and deliberately not one of the other two
#: answers. It is not contamination -- nothing was observed on a leased card --
#: and it is emphatically not "clear", which is what an empty sample list used
#: to mean. No scored root may proceed under it and no candidate is blamed for
#: it.
MONITORING_UNKNOWN = "MONITORING_UNKNOWN_SHARED_ENVIRONMENTAL_NONVERDICT"

# --------------------------------------------------------------------------
# Topology profiles
# --------------------------------------------------------------------------

TITAN_SINGLE_4X = "titan_single_4x"
TITAN_PAIR_2X = "titan_pair_2x"
# The same exam on two 48 GiB Ada cards. Every candidate fits on one card
# there, so there is no layer-split profile: the pair profile existed only
# because 12 GiB could not hold the larger candidates.
L40_SINGLE_2X = "l40_single_2x"
BLACKWELL_SINGLE_2X = "blackwell_single_2x"
#: Two single-card servers on cards LEASED at run time. Structurally the
#: same shape as the profiles above -- one card per worker, no split, no
#: peer copy -- and different from all of them in one respect: its device
#: groups are not known when the profile is written.
ADA_LEASED_2X = "ada_leased_2x"

TOPOLOGY_PROFILES: dict[str, dict[str, Any]] = {
    TITAN_SINGLE_4X: {
        "profile": TITAN_SINGLE_4X,
        "description": "four fully independent single-slot servers, one per GPU",
        "servers": 4,
        "workers": 4,
        "gpus_per_worker": 1,
        "device_groups": ((0,), (1,), (2,), (3,)),
        "split_mode": "none",
        "tensor_split": None,
        "explicit_device_required": True,
        "root_block_sizes": (8, 8, 7, 7),
        "peer_copy_permitted": False,
    },
    L40_SINGLE_2X: {
        "profile": L40_SINGLE_2X,
        "description": "two fully independent single-slot servers, one per L40",
        "servers": 2,
        "workers": 2,
        "gpus_per_worker": 1,
        "device_groups": ((0,), (1,)),
        "split_mode": "none",
        "tensor_split": None,
        "explicit_device_required": True,
        # 30 roots over two workers. Worker count is a throughput parameter and
        # does not change per-root wall time, which is the quantity the rail
        # tests, so this partition is comparable with the four-worker one at the
        # level of a root even though the elapsed totals are not.
        "root_block_sizes": (15, 15),
        "peer_copy_permitted": False,
    },
    BLACKWELL_SINGLE_2X: {
        "profile": BLACKWELL_SINGLE_2X,
        "description": (
            "two fully independent single-slot servers, one per RTX PRO 6000 "
            "Blackwell GPU"),
        "servers": 2,
        "workers": 2,
        "gpus_per_worker": 1,
        "device_groups": ((0,), (1,)),
        "split_mode": "none",
        "tensor_split": None,
        "explicit_device_required": True,
        "root_block_sizes": (15, 15),
        "peer_copy_permitted": False,
    },
    ADA_LEASED_2X: {
        "profile": ADA_LEASED_2X,
        "description": "two single-card servers on cards leased from a shared host",
        "servers": 2,
        "workers": 2,
        "gpus_per_worker": 1,
        # PLACEHOLDERS. These are lease SLOTS, not physical cards, and binding
        # them is mandatory: `bind_topology_to_lease` replaces them with the
        # cards actually held. Using this profile unbound would confine both
        # servers to physical GPUs 0 and 1, which on the observed host were the
        # two busiest cards on the box -- the precise accident the lease exists
        # to prevent, and one that would have looked like a successful launch.
        "device_groups": ((0,), (1,)),
        "device_groups_are_lease_slots": True,
        "split_mode": "none",
        "tensor_split": None,
        "explicit_device_required": True,
        "root_block_sizes": (15, 15),
        "peer_copy_permitted": False,
    },
    TITAN_PAIR_2X: {
        "profile": TITAN_PAIR_2X,
        "description": "two disjoint two-GPU layer-split servers",
        "servers": 2,
        "workers": 2,
        "gpus_per_worker": 2,
        "device_groups": ((0, 1), (2, 3)),
        "split_mode": "layer",
        "tensor_split": "1,1",
        "explicit_device_required": True,
        "root_block_sizes": (15, 15),
        "peer_copy_permitted": False,
    },
}

PROHIBITED_SPLIT_MODES = ("tensor", "row")


class Round5GuardFailure(RuntimeError):
    """A Round 5 execution guard refused to run."""


class UnknownTopology(Round5GuardFailure):
    """A candidate named a topology profile that does not exist."""


def topology_profile(name: str) -> dict[str, Any]:
    """The frozen profile, or a refusal.

    There is no default. A candidate record that does not name a topology has
    not said which machine it was measured on, and a four-worker number and a
    two-worker number are not the same measurement.
    """
    try:
        return dict(TOPOLOGY_PROFILES[str(name)])
    except KeyError:
        raise UnknownTopology(
            f"unknown topology profile {name!r}; expected one of "
            f"{sorted(TOPOLOGY_PROFILES)}"
        ) from None


def bind_topology_to_lease(
    profile_name: str,
    lease: Any,
) -> dict[str, Any]:
    """Resolve a lease-slot topology into the cards actually held.

    Returns a profile whose `device_groups` are physical ordinals and which also
    carries `device_group_uuids` -- the identity that servers are confined by.
    Both are recorded because they answer different questions: the ordinals are
    what the occupancy canary and the per-device GPU-hour accounting speak, and
    the UUIDs are what survives a renumbering.

    Slot order is preserved, so worker 0 gets the lowest-numbered leased card.
    That is arbitrary but fixed, which is what matters: the alternative -- any
    rule that prefers one card over another -- would make the worker-to-card
    assignment depend on the state of the machine, and root blocks are not
    interchangeable across workers.
    """
    profile = topology_profile(profile_name)
    if not profile.get("device_groups_are_lease_slots"):
        raise Round5GuardFailure(
            f"topology {profile_name!r} has fixed device groups and must not be "
            f"bound to a lease")
    devices = list(getattr(lease, "devices", ()) or ())
    slots = profile["device_groups"]
    required = sum(len(group) for group in slots)
    if len(devices) != required:
        raise Round5GuardFailure(
            f"topology {profile_name!r} needs {required} leased cards, "
            f"lease holds {len(devices)}")
    bound: list[tuple[int, ...]] = []
    uuids: list[tuple[str, ...]] = []
    position = 0
    for group in slots:
        chosen = devices[position:position + len(group)]
        position += len(group)
        bound.append(tuple(int(device.index) for device in chosen))
        uuids.append(tuple(str(device.uuid) for device in chosen))
    profile["device_groups"] = tuple(bound)
    profile["device_group_uuids"] = tuple(uuids)
    profile["bound_to_lease"] = True
    profile["device_groups_are_lease_slots"] = False
    return profile


def execution_topology_profile(
    profile_name: str,
    *,
    lease: Any | None = None,
) -> dict[str, Any]:
    """Return the topology that a live process is permitted to execute.

    Dedicated-host profiles carry physical device ordinals in the frozen
    profile and need no run-time binding.  The Ada profile deliberately carries
    *lease slots* instead.  Treating those slots as ordinals sends the exam to
    GPUs 0 and 1 regardless of which cards were leased, so a live caller must
    supply the verified lease and resolve it here.
    """
    profile = topology_profile(profile_name)
    if profile.get("device_groups_are_lease_slots"):
        if lease is None:
            raise Round5GuardFailure(
                f"topology {profile_name!r} requires a verified GPU lease")
        return bind_topology_to_lease(profile_name, lease)
    return profile


def topology_blockers(
    *,
    profile_name: str,
    split_mode: str | None,
    device_groups: Sequence[Sequence[int]] | None,
    tensor_split: str | None = None,
    main_gpu_only: bool = False,
) -> list[str]:
    """Every way a launch configuration fails to be the declared topology.

    ``--main-gpu`` alone is explicitly insufficient evidence that other cards
    were unused: it selects a primary device without preventing allocation
    elsewhere, so a "single-card" server can still touch three other GPUs and
    the residency claim in the paper would be false.
    """
    blockers: list[str] = []
    try:
        profile = topology_profile(profile_name)
    except UnknownTopology as exc:
        return [f"unknown_topology_profile:{exc}"]

    if str(split_mode) in PROHIBITED_SPLIT_MODES:
        blockers.append(f"prohibited_split_mode:{split_mode}")
    elif str(split_mode) != profile["split_mode"]:
        blockers.append(
            f"split_mode_{split_mode}_not_{profile['split_mode']}_for_{profile_name}")

    if main_gpu_only:
        blockers.append("main_gpu_alone_is_not_device_isolation_evidence")

    if device_groups is None:
        blockers.append("device_groups_absent")
        return sorted(set(blockers))

    groups = [tuple(int(d) for d in group) for group in device_groups]
    expected = [tuple(group) for group in profile["device_groups"]]
    if len(groups) != profile["servers"]:
        blockers.append(f"server_count_{len(groups)}_not_{profile['servers']}")
    if any(len(group) != profile["gpus_per_worker"] for group in groups):
        blockers.append(
            f"gpus_per_worker_not_{profile['gpus_per_worker']}")
    flat = [device for group in groups for device in group]
    if len(set(flat)) != len(flat):
        blockers.append("device_groups_overlap")
    # The bound is the profile's OWN card count, not the Titan card count: a
    # two-card profile must not be validated against four cards it does not
    # have, and a device index of 3 on a two-L40 host is out of range.
    profile_gpu_count = int(profile["servers"]) * int(profile["gpus_per_worker"])
    if sorted(set(flat)) and (min(flat) < 0 or max(flat) >= profile_gpu_count):
        blockers.append(
            "device_index_outside_the_four_titan_cards"
            if profile_gpu_count == TITAN_GPU_COUNT
            else f"device_index_outside_the_{profile_gpu_count}_cards_"
                 f"of_{profile['profile']}")
    if sorted(groups) != sorted(expected):
        blockers.append(
            f"device_groups_{groups}_not_the_frozen_{expected}")

    if profile["gpus_per_worker"] > 1:
        if str(tensor_split or "") != str(profile["tensor_split"]):
            blockers.append(
                f"tensor_split_{tensor_split}_not_{profile['tensor_split']}")
    elif tensor_split:
        blockers.append("tensor_split_declared_for_a_single_card_server")

    return sorted(set(blockers))


def root_schedule(
    root_ids: Sequence[str], *, profile_name: str, candidate_index: int
) -> list[dict[str, Any]]:
    """Assign the frozen ordered roots to workers in frozen blocks.

    Blocks are ``8/8/7/7`` on four single-card servers and ``15/15`` on two
    pair-split servers. Which physical device receives the FIRST block rotates
    with the candidate's position in the frozen order, so a systematically
    slower card cannot advantage or disadvantage the same block of templates in
    every candidate.
    """
    profile = topology_profile(profile_name)
    sizes = list(profile["root_block_sizes"])
    if sum(sizes) != EXAM_ROOTS:
        raise Round5GuardFailure(
            f"{profile_name} blocks sum to {sum(sizes)}, not {EXAM_ROOTS}")
    if len(root_ids) != EXAM_ROOTS:
        raise Round5GuardFailure(
            f"the schedule covers exactly {EXAM_ROOTS} roots, got {len(root_ids)}")

    groups = list(profile["device_groups"])
    rotation = int(candidate_index) % len(groups)
    assignments: list[dict[str, Any]] = []
    position = 0
    for block_index, size in enumerate(sizes):
        worker = (block_index + rotation) % len(groups)
        devices = list(groups[worker])
        for root_id in root_ids[position:position + size]:
            assignments.append({
                "root_id": str(root_id),
                "block": block_index,
                "worker": worker,
                "devices": devices,
                "topology": profile_name,
            })
        position += size
    return assignments


# --------------------------------------------------------------------------
# Frozen runtime contract
# --------------------------------------------------------------------------

CONTEXT_TOKENS = 40960
KV_CACHE_TYPE_K = "q8_0"
KV_CACHE_TYPE_V = "q8_0"
OUTPUT_CEILING_TOKENS = 4096
TEMPERATURE = 0.0
ENABLE_THINKING = False
PI_AUTO_COMPACTION = False
GPU_LAYERS = 999
SLOTS_PER_SERVER = 1
ROOT_WALL_RAIL_SECONDS = 360.0

# --------------------------------------------------------------------------
# Deterministic root budget (Round 7 onward)
# --------------------------------------------------------------------------
#
# A WALL rail makes eligibility a property of the machine. A root that would
# settle in 150 s on an idle card binds at 360 s on a contended one, and the
# zero-censoring gate then disqualifies the model for somebody else's job. The
# same mechanism made a slower accelerator disqualifying outright:
# gemma-4-12b-it NQ'd on TITAN for missing 360 s on the 32k probe, which is a
# statement about Maxwell, not about Gemma.
#
# These bounds are contention-invariant. A root on a busy card, or on a slower
# card, consumes the same tool calls and the same tokens and reaches the same
# verdict; it simply takes longer in wall time. Calibrated from the 200 settled
# Round-6 roots: 314 tool calls and 31,453 completion tokens were the observed
# maxima for a root that finished, so both ceilings sit above anything a
# settled root has ever needed. The 11 rail-bound Round-6 roots were LOOPS --
# a median of 216 tool calls producing the same ~4,200 tokens a settled root
# produces in 8. Round 7 lets such a root continue until a deterministic budget
# or the safety stop ends it; either terminal is an observed task failure, not
# clock-derived unmeasurability.
ROOT_MAX_TOOL_CALLS = 400
#: Cumulative across the whole root, not per completion. Raised from 40,960 on
#: 2026-09-02. At 40,960 the ceiling sat only 30 per cent above the slowest root
#: that FINISHED in Round 6 (31,453 tokens), so it was not a backstop against
#: pathology, it was a cap on reasoning -- and the Round-6 loops it was supposed
#: to catch were the opposite shape, a median of 216 tool calls producing about
#: 4,181 tokens. Loops are caught by ROOT_MAX_TOOL_CALLS; this ceiling exists
#: only to stop unbounded generation, so it belongs far above any legitimate
#: use. 250,000 is about eight times the slowest finisher. In practice the
#: 5,400 s safety stop binds first for any slow model, which is intended: this
#: is the deterministic backstop, not the operative bound.
ROOT_MAX_COMPLETION_TOKENS = 250_000
#: A safety stop, not a gate, and the ONLY wall-clock bound that can end a
#: Round-7 root. Recorded on every root; a root that hits it is reported and is
#: NOT censored in Round 7, because exceeding it is a statement about the
#: machine. The historical >360-second count is retained as a diagnostic only.
#:
#: Sized for the machine it will actually run on, which is the point. Round-6
#: settled roots had a p90 of 150 s and a maximum of 363 s on quiet, exclusively
#: held cards. The Round-7 host is an eight-card box shared with other
#: researchers: the two leased cards sit in a chassis whose neighbours were
#: observed drawing 274-296 W of a 300 W cap at 64-72 C, and clocks fall under
#: that load. A timeout set at a small multiple of the quiet-machine maximum
#: would therefore fire on legitimate roots exactly when the box is busiest,
#: which is the failure the deterministic budget was introduced to end -- and it
#: would reintroduce it through the back door, as a hard stop rather than as a
#: gate. 5,400 s is just under 15x the slowest root ever observed to finish
#: (363 s in Round 6) and 36x the settled p90 of 150 s, so no
#: plausible degree of contention brings a real root near it, while a genuinely
#: wedged process still cannot hold a leased card for more than 90 minutes.
#:
#: Runaway agents also have the deterministic call/token budgets. Which stop
#: binds first depends on decode speed; either one is scored as a task failure.
ROOT_SAFETY_TIMEOUT_SECONDS = 5400.0
BUDGET_EXHAUSTED = "budget_exhausted"
NETWORK_DURING_ROOTS = "denied"
SPECULATIVE_DECODING = False
MTP_EXCLUDED = True

FROZEN_RUNTIME_FIELDS = {
    "context_tokens": CONTEXT_TOKENS,
    "kv_cache_type_k": KV_CACHE_TYPE_K,
    "kv_cache_type_v": KV_CACHE_TYPE_V,
    "output_ceiling_tokens": OUTPUT_CEILING_TOKENS,
    "temperature": TEMPERATURE,
    "enable_thinking": ENABLE_THINKING,
    "pi_auto_compaction": PI_AUTO_COMPACTION,
    "gpu_layers": GPU_LAYERS,
    "slots_per_server": SLOTS_PER_SERVER,
    "root_wall_rail_seconds": ROOT_WALL_RAIL_SECONDS,
    "network_during_roots": NETWORK_DURING_ROOTS,
    "speculative_decoding": SPECULATIVE_DECODING,
}


def runtime_blockers(runtime: Mapping[str, Any] | None,
                     *, hardware: str | None = None) -> list[str]:
    """Refuse a runtime block that has drifted from the frozen contract.

    Everything the shared schema defines -- context, ceilings, the historical
    360-second boundary, sampling and thinking -- is frozen identically on every
    host. Round 7 re-labels that boundary as diagnostic and separately declares
    its safety stop; completed rounds continue to enforce it as their rail. The
    CUDA target architecture is checked against the declared hardware rather
    than a constant.
    """
    if not isinstance(runtime, Mapping):
        return ["runtime_block_absent"]
    blockers: list[str] = []
    for field, expected in sorted(FROZEN_RUNTIME_FIELDS.items()):
        actual = runtime.get(field)
        if isinstance(expected, bool):
            if bool(actual) is not expected:
                blockers.append(f"runtime_{field}_{actual}_not_{expected}")
        elif isinstance(expected, float):
            try:
                if float(actual) != expected:
                    blockers.append(f"runtime_{field}_{actual}_not_{expected}")
            except (TypeError, ValueError):
                blockers.append(f"runtime_{field}_unreadable:{actual}")
        elif isinstance(expected, int):
            try:
                if int(actual) != expected:
                    blockers.append(f"runtime_{field}_{actual}_not_{expected}")
            except (TypeError, ValueError):
                blockers.append(f"runtime_{field}_unreadable:{actual}")
        else:
            if str(actual) != str(expected):
                blockers.append(f"runtime_{field}_{actual}_not_{expected}")
    if runtime.get("engine") != "llama.cpp":
        blockers.append("runtime_engine_not_llama_cpp")
    if runtime.get("model_format") != "GGUF":
        blockers.append("runtime_model_format_not_gguf")
    if not runtime.get("required_commit"):
        blockers.append("runtime_llama_cpp_commit_unbound")
    toolchain = runtime.get("build_toolchain") or {}
    expected_arch = host_spec(hardware)["cuda_architecture"]
    if str(toolchain.get("cuda_architectures") or "") != expected_arch:
        blockers.append(f"runtime_cuda_architectures_not_{expected_arch}")
    # A registry that still carries a single common quantization is the Round-4
    # assertion that rejects Google's official QAT Q4_0 artifact. Quantization
    # is bound per substrate in Round 5.
    if "quantization" in runtime:
        blockers.append("runtime_declares_a_single_common_quantization")
    return sorted(set(blockers))


# --------------------------------------------------------------------------
# The development exam set
# --------------------------------------------------------------------------

EXAM_TEMPLATES = 30
EXAM_ROOTS_PER_TEMPLATE = 1
EXAM_ROOTS = 30
IDEAL_SUCCESS_TEMPLATES = 16
IDEAL_NONSUCCESS_TEMPLATES = 14
IDEAL_SOLVER_YIELD = IDEAL_SUCCESS_TEMPLATES / EXAM_TEMPLATES  # 0.5333...
IDEAL_SOLVER_YIELD_TOLERANCE = 1e-9

SOURCE_NAMESPACE = "round5_calibration_v2_validation"
PROTECTED_NAMESPACE_MARKERS = (
    "instrument", "confirmatory", "final", "sealed", "e0_gate",
    "pair_development", "model_training", "calibration_v2_selection",
)
PERMITTED_USES = ("compact_model_candidacy_exam", "development_only")
PROHIBITED_USES = (
    "any_inference",
    "any_effect_estimate",
    "pair_instantiation",
    "confirmatory_inference",
    "e0_qualification",
    "claim_manifest",
)


def _sha256_hex(*parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
    return digest.hexdigest()


def selection_key(protocol_digest: str, template_id: str) -> str:
    """``SHA256(protocol_digest || template_id)`` -- the frozen stratum key."""
    return _sha256_hex(protocol_digest, template_id)


def root_variant_index(exam_seed: str, template_id: str,
                       available_root_count: int) -> int:
    """``SHA256(exam_seed || template_id) mod available_root_count``."""
    if int(available_root_count) < 1:
        raise Round5GuardFailure(
            f"{template_id} declares {available_root_count} available roots")
    return int(_sha256_hex(exam_seed, template_id), 16) % int(available_root_count)


def stratified_exam_selection(
    templates: Sequence[Mapping[str, Any]],
    *,
    protocol_digest: str,
    exam_seed: str,
) -> dict[str, Any]:
    """The exact stratified hash construction, and nothing else.

    ``templates`` carries, per template, its id, its FROZEN ideal-solver outcome
    and how many root variants exist for it. The ideal outcome partitions; the
    hash of ``protocol_digest || template_id`` orders within a stratum; the hash
    of ``exam_seed || template_id`` picks the root variant. None of the three
    consults a candidate, a model, or an observed outcome, which is the entire
    point: the exam set is a function of frozen inputs only.

    The returned order is ascending selection key over the UNION of the two
    strata, so the ordered root list is itself a frozen function of the same
    inputs rather than of which stratum happened to be built first.
    """
    successes: list[tuple[str, Mapping[str, Any]]] = []
    nonsuccesses: list[tuple[str, Mapping[str, Any]]] = []
    seen: set[str] = set()
    for row in templates:
        template_id = str(row.get("template_id"))
        if not template_id or template_id == "None":
            raise Round5GuardFailure("a permitted template has no template_id")
        if template_id in seen:
            raise Round5GuardFailure(f"duplicate template id {template_id}")
        seen.add(template_id)
        if "ideal_solver_success" not in row:
            raise Round5GuardFailure(
                f"{template_id} has no frozen ideal-solver outcome; the strata "
                "cannot be formed from an outcome that does not exist yet")
        key = selection_key(protocol_digest, template_id)
        (successes if bool(row["ideal_solver_success"]) else nonsuccesses).append(
            (key, row))

    if len(successes) < IDEAL_SUCCESS_TEMPLATES:
        raise Round5GuardFailure(
            f"only {len(successes)} ideal-success templates are permitted; "
            f"{IDEAL_SUCCESS_TEMPLATES} are required")
    if len(nonsuccesses) < IDEAL_NONSUCCESS_TEMPLATES:
        raise Round5GuardFailure(
            f"only {len(nonsuccesses)} ideal-nonsuccess templates are permitted; "
            f"{IDEAL_NONSUCCESS_TEMPLATES} are required")

    chosen = (sorted(successes, key=lambda pair: pair[0])[:IDEAL_SUCCESS_TEMPLATES]
              + sorted(nonsuccesses, key=lambda pair: pair[0])[:IDEAL_NONSUCCESS_TEMPLATES])
    chosen.sort(key=lambda pair: pair[0])

    roots: list[dict[str, Any]] = []
    for key, row in chosen:
        template_id = str(row["template_id"])
        available = int(row.get("available_root_count") or 0)
        variant = root_variant_index(exam_seed, template_id, available)
        roots.append({
            "root_id": f"{template_id}-v{variant:02d}",
            "task_template_id": template_id,
            "root_variant_index": variant,
            "available_root_count": available,
            "ideal_solver_success": bool(row["ideal_solver_success"]),
            "selection_key": key,
            "task_sha256": row.get("task_sha256"),
            "task_family": row.get("task_family"),
            "difficulty": row.get("difficulty"),
        })

    observed_yield = sum(1 for row in roots if row["ideal_solver_success"]) / len(roots)
    if abs(observed_yield - IDEAL_SOLVER_YIELD) > IDEAL_SOLVER_YIELD_TOLERANCE:
        raise Round5GuardFailure(
            f"constructed ideal yield {observed_yield:.4f} is not the frozen "
            f"{IDEAL_SOLVER_YIELD:.4f}")
    return {
        "roots": roots,
        "ideal_solver_yield": IDEAL_SOLVER_YIELD,
        "ideal_success_templates": IDEAL_SUCCESS_TEMPLATES,
        "ideal_nonsuccess_templates": IDEAL_NONSUCCESS_TEMPLATES,
        "order_rule": "ascending SHA256(protocol_digest || template_id) over both strata",
        "root_variant_rule": "SHA256(exam_seed || template_id) mod available_root_count",
    }


def namespace_blockers(
    ledger: Mapping[str, Any] | None, *, namespace: str
) -> list[str]:
    """Development-only permission, read from the ledger rather than assumed."""
    if not isinstance(ledger, Mapping):
        return ["namespace_ledger_absent_or_unreadable"]
    blockers: list[str] = []
    lowered = str(namespace).lower()
    for marker in PROTECTED_NAMESPACE_MARKERS:
        if marker in lowered:
            blockers.append(f"protected_namespace_marker:{marker}")
    entry = (ledger.get("namespaces") or {}).get(str(namespace))
    if not isinstance(entry, Mapping):
        blockers.append(f"namespace_not_in_ledger:{namespace}")
        return sorted(set(blockers))
    if entry.get("classification") != "development":
        blockers.append(
            f"namespace_classification_{entry.get('classification')}_not_development")
    if entry.get("spent") is not True:
        blockers.append("namespace_not_recorded_as_spent")
    permitted = set(entry.get("permitted_uses") or [])
    if "compact_model_candidacy_exam" not in permitted:
        blockers.append("namespace_does_not_permit_the_compact_candidacy_exam")
    for prohibited in ("confirmatory_inference", "any_effect_estimate"):
        if prohibited in permitted:
            blockers.append(f"namespace_permits_a_prohibited_use:{prohibited}")
    if entry.get("opened_by_a_prior_run") is True:
        blockers.append("namespace_roots_were_already_opened")
    return sorted(set(blockers))


def validate_exam_generation_record(
    record: Mapping[str, Any] | None,
    *,
    manifest_sha256: str | None,
    protocol_digest: str | None = None,
) -> list[str]:
    """Every way the one-shot exam record can fail to prove what it claims.

    Checking only that the file exists proves nothing: an empty file, a copy of
    a Round-4 record, or a record written before the manifest was rebuilt all
    satisfy ``is_file()``. In particular the recorded manifest digest must equal
    the digest of the manifest actually on disk -- otherwise the exam was
    rematerialised or hand-edited after the record was written, and the one-shot
    guarantee is already broken.
    """
    if record is None:
        return ["exam_generation_record_absent_or_unreadable"]
    if not isinstance(record, Mapping):
        return ["exam_generation_record_is_not_an_object"]

    blockers: list[str] = []
    if record.get("artifact_kind") != EXAM_GENERATION_RECORD_KIND:
        blockers.append(
            f"exam_generation_record_wrong_kind:{record.get('artifact_kind')}")
    if record.get("protocol") != PROTOCOL_NAME:
        blockers.append(f"exam_generation_record_wrong_protocol:{record.get('protocol')}")
    if record.get("one_shot") is not True:
        blockers.append("exam_generation_record_does_not_declare_one_shot")
    if record.get("rematerialisation") != "prohibited":
        blockers.append("exam_generation_record_does_not_prohibit_rematerialisation")
    if not record.get("generated_at_utc"):
        blockers.append("exam_generation_record_has_no_generation_timestamp")
    if record.get("pool") != EXAM_POOL:
        blockers.append(f"exam_generation_record_wrong_pool:{record.get('pool')}")
    if record.get("roots_opened") not in (0, None) and int(
            record.get("roots_opened") or 0) != 0:
        blockers.append("exam_generation_record_reports_opened_roots")

    recorded_manifest = record.get("manifest_sha256")
    if not recorded_manifest:
        blockers.append("exam_generation_record_does_not_bind_the_manifest_hash")
    elif manifest_sha256 is None:
        blockers.append("exam_manifest_unreadable_for_generation_record_check")
    elif recorded_manifest != manifest_sha256:
        blockers.append("exam_manifest_does_not_match_one_shot_generation_record")

    for field in ("hidden_table_sha256", "construction_script_sha256",
                  "protocol_digest", "exam_seed"):
        if not record.get(field):
            blockers.append(f"exam_generation_record_does_not_bind_{field}")
    if (protocol_digest is not None and record.get("protocol_digest")
            and record.get("protocol_digest") != protocol_digest):
        blockers.append("exam_generation_record_protocol_digest_mismatch")

    for field, expected in (("templates", EXAM_TEMPLATES),
                            ("roots", EXAM_ROOTS),
                            ("roots_per_template", EXAM_ROOTS_PER_TEMPLATE),
                            ("ideal_success_templates", IDEAL_SUCCESS_TEMPLATES),
                            ("ideal_nonsuccess_templates", IDEAL_NONSUCCESS_TEMPLATES)):
        try:
            if int(record.get(field)) != expected:
                blockers.append(
                    f"exam_generation_record_{field}_not_{expected}:{record.get(field)}")
        except (TypeError, ValueError):
            blockers.append(f"exam_generation_record_{field}_is_not_a_number")

    if "ideal_solver_yield" not in record:
        blockers.append("exam_generation_record_does_not_record_the_frozen_ideal_yield")
    else:
        try:
            if abs(float(record["ideal_solver_yield"]) - IDEAL_SOLVER_YIELD) > 1e-4:
                blockers.append(
                    f"exam_generation_record_ideal_yield_not_"
                    f"{IDEAL_SOLVER_YIELD:.4f}:{record['ideal_solver_yield']}")
        except (TypeError, ValueError):
            blockers.append("exam_generation_record_ideal_yield_is_not_a_number")

    ordered = record.get("ordered_root_ids")
    if not isinstance(ordered, Sequence) or isinstance(ordered, (str, bytes)):
        blockers.append("exam_generation_record_has_no_ordered_root_list")
    else:
        if len(ordered) != EXAM_ROOTS:
            blockers.append(
                f"exam_generation_record_ordered_roots_{len(ordered)}_not_{EXAM_ROOTS}")
        if len(set(str(value) for value in ordered)) != len(ordered):
            blockers.append("exam_generation_record_ordered_roots_are_not_unique")

    return sorted(set(blockers))


def manifest_blockers(manifest: Mapping[str, Any] | None) -> list[str]:
    """The 30-root manifest, checked by content."""
    if not isinstance(manifest, Mapping):
        return ["exam_manifest_absent_or_unreadable"]
    blockers: list[str] = []
    if manifest.get("artifact_kind") != EXAM_MANIFEST_KIND:
        blockers.append(f"exam_manifest_wrong_kind:{manifest.get('artifact_kind')}")
    if manifest.get("one_shot") is not True:
        blockers.append("exam_manifest_does_not_declare_one_shot")
    if manifest.get("classification") != "development_calibration_material_not_confirmatory":
        blockers.append("exam_manifest_is_not_declared_development_material")

    pool = (manifest.get("pools") or {}).get(EXAM_POOL)
    if not isinstance(pool, Mapping):
        return sorted(set(blockers + [f"{EXAM_POOL}_pool_absent"]))

    roots = list(pool.get("roots") or [])
    templates = [str(row.get("task_template_id")) for row in roots]
    if len(roots) != EXAM_ROOTS:
        blockers.append(f"exam_root_count_{len(roots)}_not_{EXAM_ROOTS}")
    if len(set(templates)) != len(templates):
        blockers.append("exam_templates_are_not_distinct")
    if len(set(str(row.get("root_id")) for row in roots)) != len(roots):
        blockers.append("exam_root_ids_are_not_unique")
    if any(row.get("task_sha256") in (None, "") for row in roots):
        blockers.append("exam_roots_are_not_all_task_digest_bound")

    successes = sum(1 for row in roots if row.get("ideal_solver_success"))
    if successes != IDEAL_SUCCESS_TEMPLATES:
        blockers.append(
            f"exam_ideal_success_templates_{successes}_not_{IDEAL_SUCCESS_TEMPLATES}")

    permitted = set(pool.get("permitted_uses") or [])
    prohibited = set(pool.get("prohibited_uses") or [])
    if permitted != set(PERMITTED_USES):
        blockers.append("exam_pool_permitted_uses_incorrect")
    if not set(PROHIBITED_USES) <= prohibited:
        blockers.append("exam_pool_prohibited_uses_incomplete")

    # The hidden table is bound by digest and must never be reachable from a
    # manifest field that execution code reads.
    for row in roots:
        if "hidden_outcome" in row or "expected_answer" in row:
            blockers.append("exam_manifest_exposes_a_hidden_outcome_to_the_runner")
            break
    return sorted(set(blockers))


# --------------------------------------------------------------------------
# Hard gates and the descriptive score
# --------------------------------------------------------------------------

MAX_TOOL_MALFORMATION = 0.02
MIN_SETTLED_COMPLETION = 0.95
MIN_TASK_SUCCESS = 0.4000
MAX_TASK_SUCCESS = 0.70
MIN_MEDIAN_TRAJECTORY_DEPTH = 2
MAX_RAIL_BOUND_OR_CENSORED_ROOTS = 0
MIN_OBSERVED_TOOL_CALLS = 1

# 0.75 x 0.5333... = 0.4000 exactly, at the frozen four-decimal presentation.
TASK_SUCCESS_FLOOR_RULE = "0.75 x 0.5333 = 0.4000"

SCORE_WEIGHTS = {"Y": 0.50, "C": 0.15, "S": 0.15, "T": 0.10, "R": 0.10}
SCORE_FORMULA = "100 * (0.50*Y + 0.15*C + 0.15*S + 0.10*T + 0.10*R)"

RANKING_RULE = (
    "hard-gate eligibility -> adjudicated_successes / total_GPU_hours -> higher "
    "candidacy score -> lower peak VRAM -> the frozen candidate order"
)


def candidacy_score(components: Mapping[str, Any]) -> float:
    """``100 * (0.50*Y + 0.15*C + 0.15*S + 0.10*T + 0.10*R)``.

    Every component must be present. Treating an absent component as zero would
    let a candidate that never reported tool conformance score as though it had
    reported a real zero, and treating it as one would be worse.
    """
    total = 0.0
    for name, weight in sorted(SCORE_WEIGHTS.items()):
        if name not in components:
            raise Round5GuardFailure(f"candidacy score component {name} is absent")
        value = float(components[name])
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise Round5GuardFailure(
                f"candidacy score component {name}={value} is outside [0, 1]")
        total += weight * value
    return 100.0 * total


def component_outcomes(row: Mapping[str, Any]) -> dict[str, Any]:
    """``Y``, ``C``, ``S``, ``T`` and ``R`` over ALL 30 attempted roots.

    ``T`` is valid tool calls divided by ALL observed tool calls, and is ZERO
    when no tool call was observed. Scoring ``0/0`` as a clean pass is the exact
    Round-4 H1 defect: it hands a perfect tool-conformance score to a model that
    never proved the tool bridge works at all.
    """
    attempted = int(row.get("n_roots") or 0)
    if attempted != EXAM_ROOTS:
        raise Round5GuardFailure(
            f"component outcomes require all {EXAM_ROOTS} attempted roots, "
            f"got {attempted}")
    observed_tool_calls = int(row.get("total_tool_calls") or 0)
    malformed = int(row.get("malformed_tool_calls") or 0)
    valid_tool_calls = max(0, observed_tool_calls - malformed)
    rail_bound = int(row.get("rail_bound_roots") or 0)
    censored = int(row.get("censored_roots") or rail_bound)
    # `R` is the "was this measurable" component. Under the wall rail it meant
    # "did the clock cut it off", which is a property of the machine: the same
    # root is measurable on an idle card and unmeasurable on a busy one, and a
    # slower accelerator makes every candidate less measurable at once. When a
    # run records deterministic budget exhaustion, that is the honest source --
    # it counts roots the MODEL spent out, not roots the cluster spent out.
    # Absent (every completed round), the rail remains the source and those
    # artifacts score exactly as they always did.
    #
    # Budget exhaustion is NOT unmeasurability, and treating it as such was the
    # wall rail's mistake carried forward under a better name. A root that spent
    # 400 tool calls or its token ceiling without submitting did not fail to be
    # observed -- it was observed, completely, doing something that did not work.
    # That is a RESULT, and it belongs in the task-success denominator with every
    # other failure, where it already lands: `Y` counts adjudicated successes
    # over all 30 attempted roots, and such a root contributes none.
    #
    # Under the previous rule a single over-budget root disqualified the whole
    # candidate, so a model that reasons at length was excluded for reasoning at
    # length. Cost is not ignored by this change; it is charged where it belongs.
    # The selection rule divides successes by GPU-hours, so a model that thinks
    # ten times longer pays ten times the denominator and ranks accordingly.
    #
    # What is left for `R` is the genuinely unmeasurable: a root the PROVIDER
    # failed to serve. Harness failures do not appear here at all -- they abort
    # the whole comparison as a shared cause rather than scoring one row -- and
    # contamination is a nonverdict for the same reason. So `R` now asks one
    # narrow question, "was any root lost to something other than the model?",
    # and its zero-tolerance gate is finally about something zero tolerance is
    # the right rule for.
    budget_exhausted = row.get("budget_exhausted_roots")
    if budget_exhausted is None:
        unmeasurable = max(rail_bound, censored)
        unmeasurable_source = "wall_rail"
    else:
        unmeasurable = int(row.get("provider_errors") or 0)
        unmeasurable_source = "provider_error"
    # A budget-exhausted root reached a DEFINED terminal state: it ran out of a
    # stated envelope and stopped. That is not the same event as a root that
    # hung or never terminated, which is what the settled-completion gate exists
    # to catch, so it is not counted against `C`. Without this the gate stacked a
    # second cliff behind the first -- 0.95 over 30 roots permits exactly one
    # unsettled root, so two long-thinking roots disqualified a candidate no
    # matter how the budget itself was scored.
    settled = int(row.get("settled_roots") or 0)
    if budget_exhausted is not None:
        # The safety stop is treated exactly like the budget, and for the same
        # reason. A root we stopped at 5,400 s reached a terminal state we chose
        # for it; it did not hang undetected. Leaving it to count against `C`
        # would have left one wall-clock path to exclusion still open -- two
        # safety-stopped roots fail 0.95 -- so a model slow enough to be stopped
        # twice would be disqualified for being slow, which is the rule this
        # round exists to remove. It still scores zero on those roots, so a
        # model that never answers is caught by the task-success floor, which is
        # a statement about the model rather than about the machine.
        settled = min(attempted,
                      settled + int(budget_exhausted)
                      + int(row.get("timeouts") or 0))
    return {
        "Y": int(row.get("adjudicated_successes") or 0) / attempted,
        "C": settled / attempted,
        "S": int(row.get("valid_submissions") or 0) / attempted,
        "T": (valid_tool_calls / observed_tool_calls) if observed_tool_calls else 0.0,
        "R": 1.0 - (unmeasurable / attempted),
        "unmeasurable_roots": unmeasurable,
        "unmeasurable_source": unmeasurable_source,
        "budget_exhausted_roots": (None if budget_exhausted is None
                                   else int(budget_exhausted)),
        "settled_or_budget_exhausted_roots": settled,
        "provider_errors": int(row.get("provider_errors") or 0),
        "total_tool_calls": observed_tool_calls,
        "malformed_tool_calls": malformed,
        "tool_calls_observed": observed_tool_calls > 0,
        "malformation_rate": (malformed / observed_tool_calls
                              if observed_tool_calls else None),
        "rail_bound_roots": rail_bound,
        "censored_roots": censored,
        "n_roots": attempted,
    }


def evaluate_hard_gates(
    row: Mapping[str, Any], *, stage_a_passed: bool
) -> dict[str, Any]:
    """The seven gates, evaluated together and reported together.

    Reporting every failure at once matters: a candidate that fails three gates
    should not have to be rejected three times, and a reader deciding whether a
    later reserve was justified needs the complete reason.
    """
    outcomes = component_outcomes(row)
    reasons: list[str] = []

    if not stage_a_passed:
        reasons.append("gate_stage_a_not_passed")

    if outcomes["total_tool_calls"] < MIN_OBSERVED_TOOL_CALLS:
        # Zero observed calls gives tool conformance zero; it is never read as a
        # perfect zero-malformation rate.
        reasons.append("gate_tool_calls_no_call_observed")
    elif outcomes["malformation_rate"] > MAX_TOOL_MALFORMATION:
        reasons.append(
            f"gate_malformed_tool_calls_{outcomes['malformation_rate']:.4f}_"
            f"above_{MAX_TOOL_MALFORMATION}")

    if outcomes["C"] < MIN_SETTLED_COMPLETION:
        reasons.append(
            f"gate_settled_completion_{outcomes['C']:.4f}_below_{MIN_SETTLED_COMPLETION}")
    if outcomes["Y"] < MIN_TASK_SUCCESS:
        reasons.append(
            f"gate_task_success_{outcomes['Y']:.4f}_below_{MIN_TASK_SUCCESS:.4f}")
    if outcomes["Y"] > MAX_TASK_SUCCESS:
        reasons.append(
            f"gate_task_success_{outcomes['Y']:.4f}_above_ceiling_{MAX_TASK_SUCCESS:.4f}")

    depth = row.get("median_trajectory_depth")
    if depth is None:
        reasons.append("gate_median_trajectory_depth_absent")
    elif float(depth) < MIN_MEDIAN_TRAJECTORY_DEPTH:
        reasons.append(
            f"gate_median_trajectory_depth_{float(depth):g}_below_"
            f"{MIN_MEDIAN_TRAJECTORY_DEPTH}")

    # Eligibility follows the same source the R component used, so a candidate
    # is never disqualified by a busy neighbour or a slow card.
    # The reason string is historical for the wall-rail source: Round-5 and
    # Round-6 artifacts contain "gate_rail_bound_or_censored_roots_N" verbatim,
    # and re-deriving eligibility from that archived evidence must reproduce the
    # archived text character for character. Only the new source gets a new name.
    unmeasurable = int(outcomes["unmeasurable_roots"])
    if unmeasurable > MAX_RAIL_BOUND_OR_CENSORED_ROOTS:
        if outcomes["unmeasurable_source"] == "wall_rail":
            reasons.append(f"gate_rail_bound_or_censored_roots_{unmeasurable}")
        else:
            reasons.append(f"gate_provider_error_roots_{unmeasurable}")

    return {
        "eligible": not reasons,
        "ineligibility_reasons": sorted(reasons),
        "components": outcomes,
        "candidacy_score": candidacy_score(outcomes),
        "score_formula": SCORE_FORMULA,
        "gates": {
            "stage_a": "pass",
            "max_tool_malformation": MAX_TOOL_MALFORMATION,
            "min_observed_tool_calls": MIN_OBSERVED_TOOL_CALLS,
            "min_settled_completion": MIN_SETTLED_COMPLETION,
            "min_task_success": MIN_TASK_SUCCESS,
            "min_task_success_rule": TASK_SUCCESS_FLOOR_RULE,
            "max_task_success": MAX_TASK_SUCCESS,
            "min_median_trajectory_depth": MIN_MEDIAN_TRAJECTORY_DEPTH,
            "max_rail_bound_or_censored_roots": MAX_RAIL_BOUND_OR_CENSORED_ROOTS,
        },
    }


# --------------------------------------------------------------------------
# GPU-hour accounting and resource-normalized ranking
# --------------------------------------------------------------------------

GPU_HOUR_RECONCILIATION_TOLERANCE_SECONDS = 1.0


def gpu_hours_from_device_intervals(
    intervals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Charge EVERY participating GPU for its FULL server lifetime.

    A two-card candidate occupies two cards for as long as its server lives,
    whether or not both cards were busy at every instant, so its cost is twice
    the wall time of that server. Charging only "active" time, or charging one
    card per server, would let a two-card model pay a single-card price and win
    a comparison it did not earn. Roots-per-second is therefore never compared
    across a four-worker and a two-worker topology; GPU-hours are.
    """
    if not intervals:
        raise Round5GuardFailure("GPU-hour accounting requires at least one interval")
    per_device: dict[str, float] = {}
    total_seconds = 0.0
    for entry in intervals:
        device = str(entry.get("device"))
        start = float(entry.get("start_monotonic"))
        end = float(entry.get("end_monotonic"))
        if not math.isfinite(start) or not math.isfinite(end):
            raise Round5GuardFailure(f"device {device} interval is not finite")
        seconds = end - start
        if seconds < 0:
            raise Round5GuardFailure(f"device {device} interval ends before it starts")
        per_device[device] = per_device.get(device, 0.0) + seconds
        total_seconds += seconds
    return {
        "total_gpu_seconds": total_seconds,
        "total_gpu_hours": total_seconds / 3600.0,
        "per_device_gpu_seconds": dict(sorted(per_device.items())),
        "devices_charged": len(per_device),
        "accounting_rule": (
            "every participating GPU charged for its full server lifetime; "
            "idle-but-held time is charged because the card was unavailable"),
    }


def reconcile_gpu_hours(
    reported_gpu_hours: Any, intervals: Sequence[Mapping[str, Any]]
) -> list[str]:
    """Refuse a GPU-hour figure that its own per-device intervals do not support."""
    try:
        derived = gpu_hours_from_device_intervals(intervals)
    except Round5GuardFailure as exc:
        return [f"gpu_hour_intervals_unusable:{exc}"]
    try:
        reported = float(reported_gpu_hours)
    except (TypeError, ValueError):
        return ["reported_gpu_hours_is_not_a_number"]
    if not math.isfinite(reported) or reported <= 0:
        return ["reported_gpu_hours_is_not_positive"]
    delta_seconds = abs(reported * 3600.0 - derived["total_gpu_seconds"])
    if delta_seconds > GPU_HOUR_RECONCILIATION_TOLERANCE_SECONDS:
        return [f"gpu_hours_do_not_reconcile_from_per_device_intervals:"
                f"{delta_seconds:.3f}s"]
    return []


def productive_throughput(adjudicated_successes: int, total_gpu_hours: float) -> float:
    """``adjudicated_successes / total_GPU_hours``."""
    hours = float(total_gpu_hours)
    if not math.isfinite(hours) or hours <= 0:
        raise Round5GuardFailure("total GPU-hours must be finite and positive")
    return int(adjudicated_successes) / hours


def rank_eligible_candidates(
    rows: Sequence[Mapping[str, Any]], *, frozen_order: Sequence[str]
) -> dict[str, Any]:
    """Eligibility first, then productive throughput, then score, VRAM, order.

    The frozen order is the LAST tie-break and it is an execution order, not a
    preference. Reading it earlier would hand every close comparison to whichever
    candidate happens to sit first in the registry, which is the Round-4 B1
    defect in a new costume.
    """
    order_index = {str(name): index for index, name in enumerate(frozen_order)}
    eligible = [row for row in rows if bool(row.get("eligible"))]
    unknown = sorted({str(row.get("candidate")) for row in rows}
                     - set(order_index))
    if unknown:
        raise Round5GuardFailure(
            f"candidate(s) absent from the frozen order: {', '.join(unknown)}")
    if not eligible:
        return {
            "selected": None,
            "reason": ("no candidate passed every hard gate; report "
                       "NO_COMPACT_EXAM_ELIGIBLE_MODEL and stop for an author "
                       "decision"),
            "verdict": "NO_COMPACT_EXAM_ELIGIBLE_MODEL",
            "eligible": [],
            "cascade_order": [],
            "rule": RANKING_RULE,
        }

    def key(row: Mapping[str, Any]) -> tuple[float, float, float, int]:
        return (
            -float(row["productive_throughput"]),
            -float(row["candidacy_score"]),
            float(row["peak_vram_mib"]),
            order_index[str(row["candidate"])],
        )

    ordered = sorted(eligible, key=key)
    cascade = [str(row["candidate"]) for row in ordered]
    tie_breaks: list[str] = []
    if len(ordered) > 1:
        first, second = ordered[0], ordered[1]
        if float(first["productive_throughput"]) == float(second["productive_throughput"]):
            tie_breaks.append("productive_throughput_tied")
            if float(first["candidacy_score"]) == float(second["candidacy_score"]):
                tie_breaks.append("candidacy_score_tied")
                if float(first["peak_vram_mib"]) == float(second["peak_vram_mib"]):
                    tie_breaks.append("peak_vram_tied_resolved_by_frozen_order")
    return {
        "selected": cascade[0],
        "reason": ("highest adjudicated successes per GPU-hour among candidates "
                   "that passed every hard gate"),
        "verdict": "COMPACT_EXAM_PROVISIONAL_SUBSTRATE_SELECTED",
        "eligible": [str(row["candidate"]) for row in ordered],
        "cascade_order": cascade,
        "tie_breaks_applied": tie_breaks,
        "productive_throughput": {
            str(row["candidate"]): float(row["productive_throughput"])
            for row in ordered},
        "candidacy_score": {
            str(row["candidate"]): float(row["candidacy_score"]) for row in ordered},
        "total_gpu_hours": {
            str(row["candidate"]): float(row["total_gpu_hours"]) for row in ordered},
        "topology": {str(row["candidate"]): str(row.get("topology"))
                     for row in ordered},
        "rule": RANKING_RULE,
        "provisional_only": True,
        "provisional_note": (
            "a provisional winner must still pass model-specific determinism, "
            "realistic soak, isolation and qualifying E0 gates; the compact exam "
            "waives none of them"),
    }


# --------------------------------------------------------------------------
# Descriptive intervals
# --------------------------------------------------------------------------

WILSON_Z_95 = 1.959963984540054


def wilson_interval(successes: int, trials: int,
                    *, z: float = WILSON_Z_95) -> dict[str, Any]:
    """Wilson score interval for one proportion.

    With 30 independent templates this is descriptive. It licenses neither an
    equivalence claim nor a statement of broad model superiority, and the
    returned record says so rather than leaving it to a reader's restraint.
    """
    n = int(trials)
    k = int(successes)
    if n <= 0:
        raise Round5GuardFailure("a Wilson interval needs at least one trial")
    if not 0 <= k <= n:
        raise Round5GuardFailure("successes must lie in [0, trials]")
    p = k / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    spread = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denominator
    return {
        "successes": k,
        "trials": n,
        "point": p,
        "lower": max(0.0, centre - spread),
        "upper": min(1.0, centre + spread),
        "method": "wilson_score",
        "z": z,
        "descriptive_only": True,
    }


def paired_template_bootstrap(
    first: Sequence[Mapping[str, Any]],
    second: Sequence[Mapping[str, Any]],
    *,
    field: str = "success",
    resamples: int = 2000,
    seed: int = 20260821,
    interval: tuple[float, float] = (0.025, 0.975),
) -> dict[str, Any]:
    """Paired template bootstrap of a between-model difference.

    Both candidates ran the SAME 30 templates in the same order, so the template
    is the resampling unit and the pairing is preserved inside every replicate.
    Resampling the two candidates independently would discard exactly the shared
    template difficulty that makes the comparison worth making.
    """
    left = {str(row["template_id"]): bool(row[field]) for row in first}
    right = {str(row["template_id"]): bool(row[field]) for row in second}
    if set(left) != set(right):
        raise Round5GuardFailure(
            "a paired bootstrap requires both candidates to have run the same "
            "templates; they did not")
    templates = sorted(left)
    if not templates:
        raise Round5GuardFailure("no templates to resample")
    if resamples < 100:
        raise Round5GuardFailure("at least 100 bootstrap resamples are required")

    point = (sum(left[t] for t in templates) - sum(right[t] for t in templates)) / len(templates)
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(resamples):
        picked = [templates[rng.randrange(len(templates))] for _ in templates]
        draws.append((sum(left[t] for t in picked) - sum(right[t] for t in picked))
                     / len(picked))
    draws.sort()

    def _percentile(values: Sequence[float], probability: float) -> float:
        position = (len(values) - 1) * probability
        low = math.floor(position)
        high = math.ceil(position)
        if low == high:
            return values[low]
        weight = position - low
        return values[low] * (1.0 - weight) + values[high] * weight

    lower = _percentile(draws, interval[0])
    upper = _percentile(draws, interval[1])
    return {
        "difference_point": point,
        "difference_lower": lower,
        "difference_upper": upper,
        "median": _percentile(draws, 0.5),
        "templates": len(templates),
        "resampling_unit": "template_pair",
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "point_within_interval": lower <= point <= upper,
        # Never widened to contain its own point estimate. An unstable replicate
        # set withholds the comparison; it does not rescue one.
        "bootstrap_unstable": not (lower <= point <= upper),
        "descriptive_only": True,
    }


# --------------------------------------------------------------------------
# Candidate set, reserves, and the reserve-activation rule
# --------------------------------------------------------------------------

# ---- the v2 seven-candidate CLOSED panel ----------------------------------
#
# Amended twice, both times prospectively, before any model request and with
# zero Stage-A or Stage-B outcomes observed. Revision 1 opened the panel to
# seven; revision 2 CLOSED it. See archive/round10/archive/ROUND5_TITAN_V2_PANEL_AMENDMENT.md,
# which preserves revision 1 rather than editing it.
#
# Closed means: these seven are the whole exam. No replacement model may be
# activated during it, for any reason. A primary that fails Stage A is reported
# as NQ with Stage B and every score reading NA, and the exam continues through
# the remaining six. That is a weaker exam on the day a candidate fails -- six
# comparable substrates instead of seven -- and it is the price of a candidate
# set that is fixed before the measurements rather than during them. A panel
# that can grow mid-exam is a panel whose membership is a function of the
# outcomes it exists to measure.
#
# Two changes from v1: `qwen3-coder-30b-a3b` is PROMOTED from the two-card
# reserve to a primary (agentic/tool-focused, already shown compatible on the
# L40S host, so it is the strongest operational addition rather than a
# speculative one), and `gpt-oss-20b` is ADDED as a primary for non-Qwen
# architecture diversity with native function calling. Promoting the two-card
# reserve empties that slot, so `devstral-small-2-24b` takes it.
#
# gpt-oss-20b is TWO-CARD by arithmetic, not by preference: its MXFP4 GGUF is
# about 12.1 GB against a 12,288 MiB card, which leaves no room for a
# 40,960-token q8_0 KV cache. Registering it as single-card would have produced
# an OOM that looked like a model defect.
# The ONE spelling of "this candidate produced no measurement". It lives here,
# with the frozen rules, because the renderer, the selector and the manager all
# have to agree on it: a table where one column says "NA", another "-" and a
# third 0 is a table that has to be interpreted before it can be read, and the
# 0 will be read as a measurement.
NA_VALUE = "NA"

PANEL_VERSION = "v2_seven_candidate_closed"
# Operative, not decorative: every reserve path below is gated on this.
PANEL_IS_CLOSED = True
PRIMARY_ORDER = (
    "ornith-1.5-9b",
    "gemma-4-12b-it",
    "qwen3.5-9b",
    "qwen3-8b",
    "qwen3.6-35b-a3b",
    "qwen3-coder-30b-a3b",
    "gpt-oss-20b",
)

# A later protocol may reuse the audited execution machinery without pretending
# that it reused the completed panel. The profile is selected by the registry,
# and the registry's mapping order must match it exactly. Keeping the Round-5/6
# tuple above as the default preserves every historical artifact and fixture.
ROUND7_PANEL_VERSION = "round7_blackwell_two_deployment_strata_v1"
ROUND7_PRIMARY_ORDER = (
    "qwen3-8b",
    "gemma-4-12b-it",
    "qwen3.5-9b",
    "qwen3-coder-30b-a3b",
    "devstral-small-2-24b",
    "qwen3-coder-next-80b-a3b",
    "gpt-oss-120b",
    # Appended, not interleaved, so the seven-model order above is unchanged and
    # the addition is auditable. Both close a family gap rather than adding
    # another chance to clear the gate: four of the first seven slots are Qwen,
    # and architecture diversity is a stated inclusion criterion.
    "muse-glimmer-30b",
    "mistral-small-4-119b",
    # Reinstated. Both were dropped from the Round-7 panel on low Round-6 task
    # yield, and that yield was substantially an artifact of the harness defect
    # this round repairs: `submit_candidate` returned a false success for a
    # malformed artifact, so a model that submitted rarely was scored as a
    # model that could not do the task. On the metric that survives the
    # confound -- successes per VALID submission -- these two were the best in
    # the panel: gpt-oss-20b 3/3, qwen3.6-35b-a3b 4/6. Removing them for a
    # defect and then repairing the defect without them would bake the defect
    # into the result.
    "gpt-oss-20b",
    "qwen3.6-35b-a3b",
)

# --------------------------------------------------------------------------
# Round 7, retargeted: two leased cards on a shared Ada host
# --------------------------------------------------------------------------
#
# The v1 panel above was designed for a machine the exam turned out not to have.
# It declared `rtx_pro_6000_blackwell_2x96gib`; the available host is an
# eight-card RTX 6000 Ada box, compute capability 8.9, 49,140 MiB per card,
# shared with other researchers, of which the exam may hold two.
#
# v1 is NOT edited. It stays here exactly as frozen, because Round-6 rehearsal
# evidence references it by name and an amended-in-place panel version is a
# panel version that means two different things. v2 is a new prospective panel,
# recorded with its withdrawals and their reasons before any draw.
#
# The withdrawals are forced, not chosen. Three arms were admitted to v1 on the
# strength of fitting a single 96 GiB card, which is stated in their own frozen
# registry field (`fit_status_before_stage_a`). None fits 48 GiB. The
# alternatives were to split them across both leased cards -- which would give
# those three a two-card topology while the rest ran on one, reintroducing the
# confound Round 6 was built to remove, and charging them double GPU-hours under
# a selection rule denominated in GPU-hours -- or to re-quantize them, which
# would break each row's predeclared quantization treatment and for which no
# pinned artifact exists. Both are worse than running eight arms.
#
# Narrowing the panel is, on its own terms, a scientific improvement: at eleven
# arms the probability that some arm clears the 12/30 gate on noise alone was
# 0.85, and at eight it is 0.75. That is a consolation, not a justification --
# the panel narrowed because of hardware, and this comment exists so that a
# later reader is not left to infer a design rationale that did not operate.
ROUND7_ADA_PANEL_VERSION = "round7_ada_leased_two_deployment_strata_v2"
ROUND7_ADA_PRIMARY_ORDER = (
    "qwen3-8b",
    "gemma-4-12b-it",
    "qwen3.5-9b",
    "qwen3-coder-30b-a3b",
    "devstral-small-2-24b",
    "muse-glimmer-30b",
    "gpt-oss-20b",
    "qwen3.6-35b-a3b",
)
#: Why each v1 arm is absent from v2. Recorded as data rather than prose so the
#: amendment renderer and the appendix can state it without a human retyping it,
#: and so that a withdrawal cannot be made silently.
ROUND7_ADA_WITHDRAWN = {
    "qwen3-coder-next-80b-a3b": (
        "does_not_fit_one_49140_mib_ada_card_at_Q4_K_M_with_the_frozen_32k_context"),
    "gpt-oss-120b": (
        "does_not_fit_one_49140_mib_ada_card_at_MXFP4"),
    "mistral-small-4-119b": (
        "does_not_fit_one_49140_mib_ada_card_at_Q4_K_M"),
}

#: v3 -- the operative panel. Four rows APPENDED to v2 on 2026-09-02 by author
#: decision, before the draw and before any model request. Appended and never
#: interleaved, so v2's order is a prefix of v3's and the widening is auditable
#: by position alone; that property is asserted by test. v2 is kept beside it
#: rather than edited, because a recorded panel profile is a statement about
#: what a round ran under and editing one rewrites history -- even a profile
#: that, as here, never opened a root.
#:
#: The additions are for COVERAGE the eight-row panel lacked: kat-coder-v2.5-dev
#: is qwen3.6-35b-a3b after an agentic post-training recipe and gives the panel
#: its only base/post-trained pair; qwen3.6-27b is the dense counterpart to that
#: same sparse row; gemma-4-31b-it adds a second size to the only Google
#: lineage; nemotron-3-nano adds an absent vendor. The price is multiplicity:
#: P(some arm clears 12/30 | every arm truly at 0.30) rises from 0.75 at eight
#: arms to 0.88 at twelve, and the expected best-arm rate from 0.421 to 0.440.
#: Both already exceed the 0.40 floor on noise alone. The widening buys
#: coverage and costs screening precision; it does not buy a better chance of a
#: real pass, and the amendment says so.
ROUND7_ADA_V3_PANEL_VERSION = "round7_ada_leased_two_deployment_strata_v3"
ROUND7_ADA_V3_PRIMARY_ORDER = ROUND7_ADA_PRIMARY_ORDER + (
    "kat-coder-v2.5-dev",
    "qwen3.6-27b",
    "gemma-4-31b-it",
    "nemotron-3-nano",
)

# --------------------------------------------------------------------------
# The fresh TITAN panel (v3): fourteen candidates, three tiers
# --------------------------------------------------------------------------
#
# The v2 TITAN panel is closed at seven and its Stage-A outcomes are history.
# The fresh exam is a NEW panel, frozen prospectively in
# `archive/round10/ROUND5_TITAN_FRESH_PANEL_PROPOSAL.md` and recorded in
# `protocols/model_candidate_round5_titan_v3_candidate.yaml`. It is not a
# substitution into v2: the v2 order, membership and verdicts are untouched, and
# a registry that names this panel resolves here and nowhere else.
#
# Nine tier-1 base models, four tier-2 post-training candidates and one tier-3
# licence-gated probe. Every row is `titan_single_4x` except the retained
# `qwen3-coder-30b-a3b`, which is the panel's only `titan_pair_2x` capability
# ceiling. Quantization is written per row rather than defaulted: the whole
# point of the map is that a row cannot quietly arrive at a different quantizer
# from the one the panel registered for it.
#: Thirteen, not fourteen: the licence-gated Nemotron probe is withdrawn. Its
#: pinned repository carries no GGUF, so it cannot be host-bound, its
#: conditional licence entry cannot be added, and the readiness gate refused the
#: whole panel while it was listed. `nemotron_panel_removal_2026-09-19` records
#: the removal; the model stays in HISTORICAL_EXCLUSIONS and is reported NQ if a
#: future panel re-admits it.
V3_TITAN_PANEL_VERSION = "v3_thirteen_candidate_titan_fresh"
V3_TITAN_PRIMARY_ORDER = (
    "qwen3-8b",
    "qwen3.5-9b",
    "ornith-1.5-9b",
    "ministral-3-8b-instruct-2512",
    "granite-4.1-8b",
    "granite-4.1-3b",
    "smollm3-3b",
    "phi-4-mini-instruct",
    "qwen3-coder-30b-a3b",
    "parable-granite-4.1-3b",
    "granite-4.1-8b-fc-xlam",
    "qwen3-8b-agentic-fable5",
    "qwen3.8-9b-hermes-fc",
)
V3_TITAN_TOPOLOGY = {
    name: TITAN_SINGLE_4X for name in V3_TITAN_PRIMARY_ORDER
}
V3_TITAN_TOPOLOGY["qwen3-coder-30b-a3b"] = TITAN_PAIR_2X
V3_TITAN_QUANTIZATION = {
    name: "Q4_K_M" for name in V3_TITAN_PRIMARY_ORDER
}

PANEL_PROFILES: dict[str, tuple[str, ...]] = {
    PANEL_VERSION: PRIMARY_ORDER,
    ROUND7_PANEL_VERSION: ROUND7_PRIMARY_ORDER,
    ROUND7_ADA_PANEL_VERSION: ROUND7_ADA_PRIMARY_ORDER,
    ROUND7_ADA_V3_PANEL_VERSION: ROUND7_ADA_V3_PRIMARY_ORDER,
    V3_TITAN_PANEL_VERSION: V3_TITAN_PRIMARY_ORDER,
}

#: The Stage-B cap each panel closes at. The v2 constant is retained below for
#: historical callers; a panel's cap is its length, by construction.
PANEL_STAGE_B_CAPACITY: dict[str, int] = {
    version: len(order) for version, order in PANEL_PROFILES.items()
}

#: Panel versions that use the Round-7 machinery -- two deployment strata, the
#: Round-7 verdict vocabulary, the deterministic root budget. Membership is by
#: enumeration rather than by string matching so that adding a panel is a
#: deliberate act.
ROUND7_PANEL_VERSIONS = (ROUND7_PANEL_VERSION, ROUND7_ADA_PANEL_VERSION,
                         ROUND7_ADA_V3_PANEL_VERSION)


def panel_version_of(registry: Mapping[str, Any] | None) -> str:
    """Return a supported frozen panel version, failing closed on unknowns."""
    if not isinstance(registry, Mapping):
        return PANEL_VERSION
    version = str(registry.get("panel_version") or PANEL_VERSION)
    if version not in PANEL_PROFILES:
        raise Round5GuardFailure(f"unsupported_panel_version:{version}")
    return version


def panel_order_of(registry: Mapping[str, Any] | None) -> tuple[str, ...]:
    """The only operative candidate order for the registry's panel."""
    return PANEL_PROFILES[panel_version_of(registry)]


def future_candidate_names(registry: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Return documented model names across the historical registry shapes.

    A missing section predates the on-disk documentation and therefore falls
    back to the original frozen constants.  An explicitly empty section means
    that a newer panel has no future candidates.  Mapping-valued sections may
    also contain metadata (for example ``status`` and ``read_by``), which must
    never be mistaken for candidate names.
    """
    if not isinstance(registry, Mapping):
        return tuple(sorted(FUTURE_CANDIDATES))
    if "future_candidates" not in registry:
        return tuple(sorted(FUTURE_CANDIDATES))
    section = registry.get("future_candidates") or {}
    if isinstance(section, Mapping):
        return tuple(sorted(
            str(name) for name, row in section.items()
            if isinstance(row, Mapping)
        ))
    if isinstance(section, Sequence) and not isinstance(section, (str, bytes)):
        return tuple(sorted(str(name) for name in section))
    return ()


def panel_topology(name: str, *, panel_version: str | None = None) -> str | None:
    """The topology a candidate runs under, for the panel that declares it.

    The appendix fell back to `PRIMARY_TOPOLOGY` -- the Round-5 TITAN map -- for
    any row without an artifact, so a Round-7 row rendered `4 x 1 GPU` or
    `2 x 2 GPU` (TITAN profiles this host cannot run), and the three candidates
    absent from that map rendered `NA`. The panel decides.
    """
    if panel_version in (ROUND7_ADA_PANEL_VERSION, ROUND7_ADA_V3_PANEL_VERSION):
        return (ADA_LEASED_2X
                if name in PANEL_PROFILES[panel_version] else None)
    if panel_version == ROUND7_PANEL_VERSION:
        return BLACKWELL_SINGLE_2X if name in ROUND7_PRIMARY_ORDER else None
    if panel_version == V3_TITAN_PANEL_VERSION:
        return V3_TITAN_TOPOLOGY.get(name)
    return PRIMARY_TOPOLOGY.get(name)


PRIMARY_TOPOLOGY = {
    "ornith-1.5-9b": TITAN_SINGLE_4X,
    "gemma-4-12b-it": TITAN_SINGLE_4X,
    "qwen3.5-9b": TITAN_SINGLE_4X,
    "qwen3-8b": TITAN_SINGLE_4X,
    "qwen3.6-35b-a3b": TITAN_PAIR_2X,
    "qwen3-coder-30b-a3b": TITAN_PAIR_2X,
    "gpt-oss-20b": TITAN_PAIR_2X,
}
# ---------------------------------------------------------------------------
# Hardware profiles
#
# The exam is defined independently of the accelerator it runs on, but a
# candidacy verdict is not: a wall rail turns generation speed into a condition
# on measurability, so an arm can return no measurement on one card class and a
# clean one on another. A registry therefore declares which hardware it is for,
# and the validator holds it to that declaration in both directions -- a Titan
# registry may not carry an L40 string, and an L40 registry may not carry a
# Titan one. Neither is a default that can be inherited by accident.
# ---------------------------------------------------------------------------

#: The Titan hardware map covers the v2 seven-panel and the v3 fresh panel. The
#: v2 entries are unchanged by the union; a v3-only name resolves here so the
#: readiness checker can hold a v3 registry to its declared topology.
TITAN_TOPOLOGY = {**PRIMARY_TOPOLOGY, **V3_TITAN_TOPOLOGY}
# On 48 GiB cards every candidate fits on one device, so the whole panel shares
# one profile and the layer-split profile is not used at all.
L40_TOPOLOGY = {name: L40_SINGLE_2X for name in PRIMARY_ORDER}
BLACKWELL_TOPOLOGY = {name: BLACKWELL_SINGLE_2X for name in PRIMARY_ORDER}
#: Every arm of the v2 panel, on the one leased-pair profile. Keyed off the v2
#: order rather than PRIMARY_ORDER so that a name in the Round-5 map cannot
#: leak a TITAN topology into this round by omission.
ADA_LEASED_TOPOLOGY = {name: ADA_LEASED_2X
                       for name in ROUND7_ADA_PRIMARY_ORDER}

HARDWARE_TOPOLOGY: dict[str, dict[str, str]] = {
    HARDWARE_TITAN: TITAN_TOPOLOGY,
    HARDWARE_L40: L40_TOPOLOGY,
    HARDWARE_BLACKWELL: BLACKWELL_TOPOLOGY,
    HARDWARE_ADA_LEASED: ADA_LEASED_TOPOLOGY,
}
HARDWARE_REQUIRED_PROFILES: dict[str, tuple[str, ...]] = {
    HARDWARE_TITAN: (TITAN_SINGLE_4X, TITAN_PAIR_2X),
    HARDWARE_L40: (L40_SINGLE_2X,),
    HARDWARE_BLACKWELL: (BLACKWELL_SINGLE_2X,),
    HARDWARE_ADA_LEASED: (ADA_LEASED_2X,),
}
#: The fragment a registry's `runtime.gpu` string MUST contain, and the one it
#: must not. The second half is the stale-copy guard: it is how a registry
#: copied from the other hardware round is caught before it opens a root.
HARDWARE_GPU_FRAGMENT: dict[str, str] = {
    HARDWARE_TITAN: "TITAN X",
    HARDWARE_L40: "L40",
    HARDWARE_BLACKWELL: "RTX PRO 6000 BLACKWELL",
    HARDWARE_ADA_LEASED: "RTX 6000 ADA",
}
HARDWARE_FOREIGN_GPU_FRAGMENT: dict[str, tuple[str, str]] = {
    # profile -> (forbidden fragment, blocker id kept stable for existing tests)
    HARDWARE_TITAN: ("L40", "stale_l40s_gpu_string_in_runtime"),
    HARDWARE_L40: ("TITAN", "stale_titan_gpu_string_in_runtime"),
    HARDWARE_BLACKWELL: ("TITAN", "stale_titan_gpu_string_in_runtime"),
    # The stale-copy guard that matters most for this round: the Ada registry is
    # built by carrying rows out of the Blackwell one, so a Blackwell GPU string
    # surviving the carry is the likely error, not a TITAN one.
    HARDWARE_ADA_LEASED: ("BLACKWELL", "stale_blackwell_gpu_string_in_runtime"),
}


def hardware_profile_of(registry: Mapping[str, Any] | None) -> str:
    """The hardware a registry declares, defaulting to the Titan round."""
    if not isinstance(registry, Mapping):
        return HARDWARE_TITAN
    return str(registry.get("hardware_profile") or HARDWARE_TITAN)


PRIMARY_QUANTIZATION = {
    "ornith-1.5-9b": "Q4_K_M",
    "gemma-4-12b-it": "Q4_0",
    "qwen3.5-9b": "Q4_K_M",
    "qwen3-8b": "Q4_K_M",
    "qwen3.6-35b-a3b": "Q4_K_M",
    "qwen3-coder-30b-a3b": "Q4_K_M",
    "gpt-oss-20b": "MXFP4",
}
ROUND7_QUANTIZATION = {
    "qwen3-8b": "Q4_K_M",
    "gemma-4-12b-it": "Q4_0",
    "qwen3.5-9b": "Q4_K_M",
    "qwen3-coder-30b-a3b": "Q4_K_M",
    "devstral-small-2-24b": "Q4_K_M",
    "qwen3-coder-next-80b-a3b": "Q4_K_M",
    "gpt-oss-120b": "MXFP4",
    "muse-glimmer-30b": "Q4_K_M",
    "mistral-small-4-119b": "Q4_K_M",
    "gpt-oss-20b": "MXFP4",
    "qwen3.6-35b-a3b": "Q4_K_M",
}
#: v2 inherits the v1 quantization for every arm it retains. Written out rather
#: than derived so that a change to one panel cannot silently move the other.
ROUND7_ADA_QUANTIZATION = {
    name: ROUND7_QUANTIZATION[name] for name in ROUND7_ADA_PRIMARY_ORDER}
#: The v3 additions all deploy at Q4_K_M, which is the panel's majority
#: quantizer and the only one available as a pinned artifact for any of them.
#: Written out per row rather than defaulted, because a per-candidate
#: quantization map that falls back to a default stops being a check: the whole
#: point of this map is that a row cannot quietly arrive at a different
#: quantizer from the one the panel registered for it.
ROUND7_ADA_V3_QUANTIZATION = {
    **ROUND7_ADA_QUANTIZATION,
    "kat-coder-v2.5-dev": "Q4_K_M",
    "qwen3.6-27b": "Q4_K_M",
    "gemma-4-31b-it": "Q4_K_M",
    "nemotron-3-nano": "Q4_K_M",
}

# The panel is closed, so the operative reserve list is EMPTY. It is kept as a
# named empty tuple rather than deleted so that every reserve-shaped code path
# still resolves and still refuses, loudly, instead of disappearing into a
# NameError the day somebody reopens the question.
RESERVE_ORDER: tuple[str, ...] = ()
RESERVE_RULES: dict[str, dict[str, Any]] = {}

# NOT OPERATIVE. Documentation only, and deliberately separated from anything
# the exam reads.
#
# These three were the v2 revision-1 reserves. Under the closed panel they are
# future candidates: they are not Stage-B members, they are not activatable,
# they are not validated by the readiness gate, and an unbound one is not a
# blocker for an unattended launch. Nothing in this module consults this
# mapping; it exists so that the reasoning behind three specific models is not
# lost, and so that a later round has somewhere to start rather than
# rediscovering it.
FUTURE_CANDIDATES: dict[str, dict[str, Any]] = {
    "gemma-4-E4B-it": {
        "topology": TITAN_SINGLE_4X,
        "quantization": "Q4_0",
        "why": ("official publisher QAT artifact in the same family as "
                "gemma-4-12b-it, at a size that fits a single card comfortably"),
        "operative": False,
    },
    "falcon-h1r-7b": {
        "topology": TITAN_SINGLE_4X,
        "quantization": "Q4_K_M",
        "why": ("non-Qwen, non-Gemma architecture at single-card size; its "
                "licence was never approved and would have to be decided "
                "before any future use"),
        "operative": False,
    },
    "devstral-small-2-24b": {
        "topology": TITAN_PAIR_2X,
        "quantization": "Q4_K_M",
        "why": ("agentic/tool-focused two-card candidate; considered when "
                "qwen3-coder-30b-a3b was promoted out of the reserve slot"),
        "operative": False,
    },
}

# Seven, because the panel is seven and closed. Nothing can grow the exam past
# it, and nothing is supposed to try: with reserves removed the cap is now a
# second, independent statement of the same rule rather than the only one.
MAX_STAGE_B_CANDIDATES = 7
assert MAX_STAGE_B_CANDIDATES == len(PRIMARY_ORDER), (
    "the Stage-B cap and the closed panel are the same number by construction")

# A reserve is triggered by compatibility, never by task performance. These are
# the only Stage-A failure classes that open the reserve list.
RESERVE_TRIGGER_CLASSES = (
    "identity", "licence", "artifact", "load", "memory", "kernel", "context",
    "interface",
)
# Named so that a performance-shaped reason cannot be relabelled into a trigger.
NON_TRIGGER_CLASSES = (
    "task_performance", "score", "yield", "throughput", "candidacy_score",
    "settled_completion", "adjudication",
)
# The class an unrecognised Stage-A reason is given. It is deliberately NOT a
# trigger: defaulting an unmatched reason to `load` meant that missing, garbled
# or newly worded evidence activated a reserve as though the model had genuinely
# failed to load, which is a candidate-shaped conclusion drawn from an absence.
# An unknown reason stops for a human instead.
UNKNOWN_FAILURE_CLASS = "unknown_nontrigger"

# The ONE mapping from a Stage-A failure reason to a frozen trigger class.
# It lives here rather than in the manager so that the "unknown reasons do not
# trigger" rule is testable directly and cannot drift between callers.
# Ordered MOST SPECIFIC FIRST. `artifact_filename_names_a_draft_or_mtp_head`
# contains both "artifact" and "mtp"; it is an identity problem, and a generic
# "artifact" entry placed earlier would have swallowed it.
FAILURE_CLASS_TABLE: tuple[tuple[str, str], ...] = (
    ("licence", "licence"),
    ("mtp", "identity"), ("draft", "identity"), ("target_tensor", "identity"),
    ("architecture", "identity"), ("alias", "identity"),
    ("block_count", "identity"), ("tokenizer", "identity"),
    ("chat_template", "identity"), ("identity", "identity"),
    ("quantization", "artifact"), ("sha256", "artifact"), ("digest", "artifact"),
    ("artifact", "artifact"),
    ("vram", "memory"), ("memory", "memory"), ("oom", "memory"),
    ("sm52", "kernel"), ("sm_52", "kernel"), ("kernel", "kernel"),
    ("cpu_fallback", "kernel"), ("cuda", "kernel"),
    ("context", "context"), ("capacity", "context"),
    ("load", "load"), ("server", "load"), ("health", "load"),
    ("tool", "interface"), ("terminal", "interface"),
    ("coherence", "interface"), ("pair", "interface"),
    ("split_mode", "interface"), ("device_group", "interface"),
    ("provider_metadata", "interface"), ("microtrajectory", "interface"),
    ("network_denial", "interface"), ("cache_isolation", "interface"),
    ("process_group_cleanup", "interface"),
)


def classify_stage_a_failure(reason: str | None) -> str:
    """Map a Stage-A failure reason onto a frozen trigger class, or refuse to.

    Returns ``UNKNOWN_FAILURE_CLASS`` when nothing matches. That value is not a
    trigger: ``activate_reserve`` raises on it. The alternative -- defaulting to
    ``load`` -- turned "we could not parse this evidence" into "the model failed
    to load", which is a claim about the candidate made from an absence.
    """
    text = str(reason or "").lower()
    if not text:
        return UNKNOWN_FAILURE_CLASS
    for needle, klass in FAILURE_CLASS_TABLE:
        if needle in text:
            return klass
    return UNKNOWN_FAILURE_CLASS


HISTORICAL_EXCLUSIONS = {
    "ministral-3-8b-instruct-2512": (
        "historical NQ: zero observed tool calls in the corrected 20-prompt "
        "probe, plus prior smoke instability; reported, not rerun"),
    "nemotron-nano-9b-v2": (
        "historical NQ: prior reasoning overhead, timeouts and rail-bound smoke "
        "roots; reported, not rerun"),
    "qwen3-4b": (
        "historical NQ: repeated tool loop and soak failure; reported, not rerun"),
    "qwen3.5-4b": (
        "historical NQ: failed settled-completion and task-yield requirements; "
        "reported, not rerun"),
}


class ReserveRefused(Round5GuardFailure):
    """A reserve activation was requested that the frozen rule does not permit."""


# --------------------------------------------------------------------------
# The authority matrix: what a failure is allowed to stop
# --------------------------------------------------------------------------
#
# "Stop on any mismatch" is the wrong rule, and it fails in both directions. It
# throws away a whole night because one model's digest moved, and -- worse --
# it invites the operator to make the mismatch go away, because stopping is
# expensive and editing an expected value is cheap. So the scope of a failure
# is frozen here rather than decided at 3am by whoever is awake.
#
# The line is: does the failure impugn ONE candidate, or the COMPARISON?
#
# A candidate-local failure is evidence ABOUT that candidate. It is classified
# under the frozen provenance/Stage-A rules, its exact evidence is preserved,
# and the remaining panel continues -- because six measured substrates plus one
# named exclusion is a result, and an aborted run is not.
#
# A shared failure impugns every measurement the run could still produce: if the
# runtime is not the bound runtime, or the manifest is not the bound manifest,
# then no candidate's number means what the protocol says it means. Continuing
# would manufacture a comparison, so the launch stops.
#
# Contamination and timeouts are neither. Nothing about the candidate was
# measured, so they must never be converted into a candidate verdict.
#
# In no case is an expected value rewritten to match an observed artifact. That
# is the one move that turns a frozen protocol into a description of whatever
# happened to be on disk.

SCOPE_CANDIDATE_LOCAL = "candidate_local_classify_and_continue"
SCOPE_SHARED_GLOBAL = "shared_global_stop_the_launch"
SCOPE_NONVERDICT = "nonverdict_wait_never_a_candidate_verdict"

#: The deployment strata a Round-7 registry may declare, and what each one
#: asserts. `legacy_12gib_fallback` is a MEMORY claim about a 12,288 MiB card
#: and nothing else -- not a timing result, not a gate pass, not permission to
#: import a TITAN number into a Blackwell comparison.
LEGACY_FALLBACK_STRATUM = "legacy_12gib_fallback"
CAPACITY_STRATUM = "blackwell_capacity"
#: The v2 capacity stratum. A separate name, not a renaming: `blackwell_capacity`
#: is written into the v1 registry and into Round-6 rehearsal evidence, and a
#: constant that quietly changed value would relabel those artifacts. The two
#: strata mean the same thing structurally -- "verified to fit the small legacy
#: card" versus "needs the large card" -- but the large card is a different card,
#: and the appendix prints this string, so a v2 table captioned
#: `blackwell_capacity` would be describing hardware the run never touched.
ADA_CAPACITY_STRATUM = "ada_48gib_capacity"
DEPLOYMENT_STRATA = (LEGACY_FALLBACK_STRATUM, CAPACITY_STRATUM,
                     ADA_CAPACITY_STRATUM)


def capacity_stratum_for(panel_version: str | None) -> str:
    """The capacity stratum the named panel uses."""
    return (ADA_CAPACITY_STRATUM
            if panel_version in (ROUND7_ADA_PANEL_VERSION,
                                 ROUND7_ADA_V3_PANEL_VERSION)
            else CAPACITY_STRATUM)
#: The card the fallback label is about.
LEGACY_FALLBACK_CARD_MEMORY_MIB = 12288


def legacy_fallback_blockers(
    registry: Mapping[str, Any] | None, *,
    repo_root: "Path | None" = None,
    digest: "Callable[[Path], str] | None" = None,
) -> list[str]:
    """Every way a `legacy_12gib_fallback` label can be unearned.

    The amendment requires Stage A to verify the label "against archived TITAN
    evidence or a zero-outcome compatibility probe". Nothing implemented it, so
    the study's one structural claim over the predecessor round rested on a
    string in a YAML file, while the same candidates' `fit_status_before_stage_a`
    recorded BLACKWELL fit -- the opposite property.

    A row carrying the label must name archived evidence that (a) exists and
    matches its recorded digest, (b) was taken on a 12,288 MiB card, (c) ran at
    THIS registry's frozen context ceiling, (d) binds the SAME artifact revision
    and digest this registry binds, and (e) recorded free VRAM at peak at or
    above the registered floor. The archived Stage-A STATUS is recorded and
    deliberately not required to be a pass: gemma-4-12b-it's TITAN Stage A was
    an NQ on the 360-second realistic-multiturn probe, which is a speed result.
    Memory fit is what the label claims; timing is what it must never imply.
    """
    if not isinstance(registry, Mapping):
        return ["registry_absent_or_unreadable"]
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    sha = digest or _sha256_path
    blockers: list[str] = []
    candidates = registry.get("candidates") or {}
    # Deployment strata are a Round-7 construct. A panel that makes no such
    # claim has nothing to earn, so an unlabelled Round-5 or Round-6 registry
    # is not in breach; a panel that DOES declare the strata must label every
    # row, because a half-labelled table is a table nobody can read.
    try:
        version = panel_version_of(registry)
    except Round5GuardFailure:
        version = None
    labelled = any(str((spec or {}).get("deployment_stratum") or "")
                   for spec in candidates.values()
                   if isinstance(spec, Mapping))
    require_label = (version in ROUND7_PANEL_VERSIONS) or labelled
    if not require_label:
        return []
    context = int((registry.get("runtime") or {}).get("context_tokens") or 0)
    floor = int((registry.get("stage_a") or {}).get(
        "minimum_free_vram_mib_on_every_participating_gpu_at_peak") or 0)
    for name, spec in candidates.items():
        if not isinstance(spec, Mapping):
            continue
        stratum = str(spec.get("deployment_stratum") or "")
        if not stratum:
            blockers.append(f"{name}:deployment_stratum_undeclared")
            continue
        if stratum not in DEPLOYMENT_STRATA:
            blockers.append(f"{name}:unknown_deployment_stratum:{stratum}")
            continue
        fit = spec.get("legacy_12gib_fit")
        if stratum != LEGACY_FALLBACK_STRATUM:
            # The label is exclusive. A capacity row carrying fit evidence would
            # read as a fallback row in the table it is not in.
            if fit:
                blockers.append(
                    f"{name}:capacity_row_declares_legacy_12gib_fit")
            continue
        if not isinstance(fit, Mapping):
            blockers.append(f"{name}:legacy_12gib_fit_unverified")
            continue
        if str(fit.get("claim") or "") != "memory_fit_only_never_timing":
            blockers.append(f"{name}:legacy_12gib_fit_claim_is_not_memory_only")
        evidence = str(fit.get("evidence_path") or "").strip()
        expected = str(fit.get("evidence_sha256") or "").strip()
        if not evidence or not expected:
            blockers.append(f"{name}:legacy_12gib_fit_evidence_unbound")
            continue
        path = root / evidence
        if not path.is_file():
            blockers.append(f"{name}:legacy_12gib_fit_evidence_absent:{evidence}")
            continue
        if sha(path) != expected:
            blockers.append(
                f"{name}:legacy_12gib_fit_evidence_digest_mismatch:{evidence}")
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            blockers.append(f"{name}:legacy_12gib_fit_evidence_unreadable")
            continue
        observed = record.get("free_vram_mib_at_peak") or {}
        try:
            worst = min(float(value) for value in observed.values())
        except (TypeError, ValueError):
            worst = None
        if worst is None:
            blockers.append(f"{name}:legacy_12gib_fit_free_vram_unrecorded")
        elif floor and worst < floor:
            blockers.append(
                f"{name}:legacy_12gib_fit_free_vram_{worst}_below_{floor}")
        plan = record.get("plan") or {}
        if context and int(plan.get("context_tokens") or 0) != context:
            blockers.append(
                f"{name}:legacy_12gib_fit_evidence_context_"
                f"{plan.get('context_tokens')}_not_{context}")
        evidence_topology = str(record.get("topology") or "")
        try:
            per_worker = int(
                topology_profile(evidence_topology)["gpus_per_worker"])
        except (UnknownTopology, KeyError):
            per_worker = 0
            blockers.append(
                f"{name}:legacy_12gib_fit_evidence_topology_unknown:"
                f"{evidence_topology}")
        if per_worker and per_worker != 1:
            blockers.append(
                f"{name}:legacy_12gib_fit_evidence_is_not_one_card_per_worker")
        if int(fit.get("card_memory_mib") or 0) != LEGACY_FALLBACK_CARD_MEMORY_MIB:
            blockers.append(
                f"{name}:legacy_12gib_fit_card_memory_is_not_"
                f"{LEGACY_FALLBACK_CARD_MEMORY_MIB}")
        # The evidence must bind THIS artifact, not merely a model of the same
        # name at some other revision.
        checks = record.get("checks") or {}
        archived_digest = str(
            ((checks.get("lfs_digest") or {}).get("expected_sha256")) or "")
        archived_revision = str(
            ((checks.get("source_revision") or {}).get("value")) or "")
        if archived_digest and archived_digest != str(spec.get("expected_sha256") or ""):
            blockers.append(
                f"{name}:legacy_12gib_fit_evidence_binds_a_different_artifact")
        if (archived_revision
                and archived_revision != str(spec.get("source_revision") or "")):
            blockers.append(
                f"{name}:legacy_12gib_fit_evidence_binds_a_different_revision")
        if not str(fit.get("archived_stage_a_status") or "").strip():
            blockers.append(f"{name}:legacy_12gib_fit_archived_status_unrecorded")
    return sorted(set(blockers))


CANDIDATE_LOCAL_FAILURES = (
    "licence", "licence_incompatible", "provenance", "artifact_unavailable",
    "digest_mismatch", "sha256", "architecture_mismatch",
    "block_count_mismatch", "tokenizer_mismatch", "chat_template_mismatch",
    "load_failure", "invalid_tool_use", "terminal_answer_failure",
    "identity", "memory", "kernel", "context",
    # A Stage-B guard refusal is now scoped rather than assumed to be a
    # candidate verdict, and this is the one execution-guard blocker that
    # genuinely IS about one candidate. Without it the shared default would
    # stop the whole funnel because one model did not clear Stage A.
    "candidate_did_not_pass_stage_a",
    # Candidate-artifact binding reasons. `sha256` and `identity` above already
    # cover the digest and tensor-identity ones; these are the remaining stems
    # a per-candidate binding failure can produce, and each is about one
    # artifact. Without them an unbound `source_revision` or a bad shard would
    # hit the shared default and stop the whole panel.
    "source_revision", "artifact_shard", "model_shard", "model_file_absent",
)
SHARED_GLOBAL_FAILURES = (
    "protocol_digest_disagreement", "licence_policy_digest_disagreement",
    "registry_digest_disagreement", "runtime_mismatch", "build_mismatch",
    "llama_server_digest_mismatch", "invalid_manifest", "manifest_digest",
    "namespace_invalid", "namespace_ledger",
    # The needle was `execution_authorization_missing`, but the string the
    # guards actually emit is `execution_authorization_not_set`, so the one
    # entry written to catch an unauthorized run never matched it. Match the
    # stem instead of one spelling of it.
    "execution_authorization",
    "schema_disagreement", "schema_contract_digest", "isolation_failure",
    "process_group_cleanup", "manager_defect", "evidence_integrity",
    # An infrastructure exception inside the harness is evidence about the
    # HARNESS. The attempted Stage-B run converted 120 of these into
    # zero-performance candidate records and then reported no eligible model;
    # classifying the class as shared is what makes that impossible to repeat.
    "harness_error", "exam_prompt_unbound", "exam_prompt_digest_mismatch",
    # The runtime-evidence checks name the BINARY, not the candidate. They were
    # reachable only through the Stage-A check NAME, and `sm52_kernels` matched
    # "kernel" in the candidate-local table above, so a runtime built for the
    # wrong architecture was scoped to whichever model happened to expose it and
    # the remaining panel then ran against the same wrong binary. `binary_digest`
    # matched nothing and reached the artifact-exists branch, whose `unmatched`
    # default is candidate-local. Both are properties of one shared runtime, so
    # both belong here, where SHARED is tested first.
    "sm52_kernels", "binary_digest", "runtime_evidence",
)
NONVERDICT_FAILURES = (
    "occupancy", "contamination", "timing_contaminated", "timeout",
    "inconclusive",
)


def failure_scope(reason: str | None, *,
                  unmatched: str = SCOPE_SHARED_GLOBAL) -> dict[str, Any]:
    """How far a failure reaches. Frozen, so nobody decides it at 3am.

    Checked SHARED first. A shared failure often mentions one candidate -- it
    was noticed while that candidate ran -- and matching candidate-local
    keywords first would scope a runtime mismatch to the model that happened to
    expose it, then let six more candidates run against the wrong runtime.

    `unmatched` is the scope for a reason no list recognises, and it defaults to
    SHARED because that is the conservative direction: mistaking a
    candidate-local failure for a shared one costs a night, and mistaking a
    shared one for candidate-local costs the comparison, silently, with a full
    set of confidently labelled artifacts.

    A caller that already knows the failure is candidate-scoped passes
    SCOPE_CANDIDATE_LOCAL. The manager does this for a Stage-A CHECK that
    failed on a candidate whose artifact exists: the evidence is by
    construction about that candidate, and only the reason WORDING is
    unfamiliar. Stopping a seven-model night because one reason string was
    novel is the over-broad rule this matrix replaced -- but the failure still
    carries `unknown_nontrigger`, and it is still reported loudly, because "we
    could not classify this" is a claim a human has to read.
    """
    text = str(reason or "").strip().lower()
    if not text:
        return {"scope": SCOPE_SHARED_GLOBAL, "matched": None,
                "stop_the_launch": True, "continue_panel": False,
                "counts_as_candidate_verdict": False,
                "rule": ("a failure with no recorded reason cannot be shown to "
                         "be candidate-local, and unclassified failures fail "
                         "closed")}
    for needle in NONVERDICT_FAILURES:
        if needle in text:
            return {"scope": SCOPE_NONVERDICT, "matched": needle,
                    "stop_the_launch": False, "continue_panel": True,
                    "counts_as_candidate_verdict": False,
                    "rule": ("nothing was measured about this candidate; follow "
                             "the registered wait/nonverdict behaviour and "
                             "never convert it into an NQ")}
    for needle in SHARED_GLOBAL_FAILURES:
        if needle in text:
            return {"scope": SCOPE_SHARED_GLOBAL, "matched": needle,
                    "stop_the_launch": True, "continue_panel": False,
                    "counts_as_candidate_verdict": False,
                    "rule": ("this impugns every measurement the run could "
                             "still produce; stop the launch and report")}
    for needle in CANDIDATE_LOCAL_FAILURES:
        if needle in text:
            return {"scope": SCOPE_CANDIDATE_LOCAL, "matched": needle,
                    "stop_the_launch": False, "continue_panel": True,
                    "counts_as_candidate_verdict": True,
                    "rule": ("evidence about ONE candidate: preserve it exactly, "
                             "classify under the frozen provenance/Stage-A "
                             "rules, and continue with the remaining closed "
                             "panel. Never rewrite the expected value to match "
                             "the artifact.")}
    if unmatched == SCOPE_CANDIDATE_LOCAL:
        return {"scope": SCOPE_CANDIDATE_LOCAL, "matched": None,
                "stop_the_launch": False, "continue_panel": True,
                "counts_as_candidate_verdict": True,
                "rule": ("the reason wording is unrecognised, but the evidence "
                         "is a failed Stage-A check on this candidate and is "
                         "candidate-scoped by construction. Classified "
                         "unknown_nontrigger, reported loudly, panel continues. "
                         "Never rewrite the expected value to match the "
                         "artifact.")}
    return {"scope": SCOPE_SHARED_GLOBAL, "matched": None,
            "stop_the_launch": True, "continue_panel": False,
            "counts_as_candidate_verdict": False,
            "rule": ("unrecognised failure reason; it cannot be shown to be "
                     "candidate-local, so it fails closed as shared")}


CLOSED_PANEL_REFUSAL = (
    "the v2 panel is CLOSED: no replacement model may be activated during this "
    "compact exam. A primary that fails Stage A is reported as NQ with Stage B "
    "and every score reading NA, and the exam continues through the remaining "
    "candidates."
)


def activate_reserve(
    *,
    failed_candidate: str,
    failure_class: str,
    stage_b_outcomes_exist: bool,
    already_activated: Sequence[str] = (),
    stage_b_membership: Sequence[str] = (),
    licence_approved: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Always refuses. The closed panel has no reserve rule to apply.

    The function is kept, with its original signature, on purpose. Deleting it
    would turn every existing caller into an ImportError at some later moment
    of somebody's choosing; keeping it means any caller that still asks for a
    reserve is told exactly why it cannot have one, at the point of asking, in
    a message that names the decision rather than the mechanism.

    The arguments are accepted and ignored. There is no failure class, no
    vacancy and no licence state that opens the panel, so branching on them
    here would only suggest that some combination might.
    """
    raise ReserveRefused(
        f"{CLOSED_PANEL_REFUSAL} (requested for {str(failed_candidate)!r} on a "
        f"{str(failure_class)!r} failure)")


def stage_a_failure_disposition(candidate: str, reason: str | None,
                                ) -> dict[str, Any]:
    """What the closed panel does with a primary that fails Stage A.

    One place, so the manager, the selector and the renderer cannot each invent
    their own answer. NQ is a real, reportable verdict about the candidate --
    unlike a timeout, which is an absence -- and it carries NA rather than zero
    into every downstream column, because the candidate produced no Stage-B
    measurement at all and a zero would be read as one.
    """
    return {
        "candidate": str(candidate),
        "verdict": "NQ",
        "passed": False,
        "stage_b": NA_VALUE,
        "candidacy_score": NA_VALUE,
        "adjudicated_successes": NA_VALUE,
        "successes_per_gpu_hour": NA_VALUE,
        "reason": str(reason or "stage_a_failed_without_a_recorded_reason"),
        "failure_class": classify_stage_a_failure(reason),
        "replacement_activated": False,
        "replacement_rule": CLOSED_PANEL_REFUSAL,
        "remains_in_the_final_table": True,
    }


# --------------------------------------------------------------------------
# Per-substrate artifact binding
# --------------------------------------------------------------------------

# MXFP4 is gpt-oss-20b's native published format, not a lossy re-quantization
# of it. The exam compares deployable substrates, so it is bound as itself.
PERMITTED_QUANTIZATIONS = ("Q4_K_M", "Q4_0", "MXFP4")


def quantization_blockers(
    *, candidate: str, declared: str | None, expected: str | None,
    independent_source: str | None,
) -> list[str]:
    """Bind quantization per substrate, against an INDEPENDENT source.

    The Round-4 registry asserted one common ``Q4_K_M`` for every candidate,
    which rejects Google's official QAT ``Q4_0`` artifact -- an artifact that is
    not a worse-quantized Gemma but a different, publisher-produced deployable.
    Round 5 compares deployable substrates, so quantization is a property of the
    row. It is still never inferred from the file being tested: a converted file
    describing itself proves nothing about what it was supposed to be.
    """
    blockers: list[str] = []
    if not expected:
        blockers.append("expected_quantization_unbound")
    elif str(expected) not in PERMITTED_QUANTIZATIONS:
        blockers.append(f"expected_quantization_not_permitted:{expected}")
    if not declared:
        blockers.append("declared_quantization_absent_from_artifact_metadata")
    elif expected and str(declared) != str(expected):
        blockers.append(f"quantization_mismatch:{declared}!={expected}")
    if not independent_source:
        blockers.append("expected_quantization_has_no_independent_source")
    elif str(independent_source) in {"downloaded_file", "converted_artifact",
                                     "artifact_under_test", "self_reported"}:
        blockers.append(
            f"expected_quantization_inferred_from_the_artifact_under_test:"
            f"{independent_source}")
    return [f"{candidate}:{reason}" for reason in sorted(set(blockers))]


def mtp_identity_blockers(
    *, candidate: str, metadata: Mapping[str, Any] | None,
    filename: str, speculative_decoding_enabled: bool,
) -> list[str]:
    """Refuse a draft/MTP head presented as the target model."""
    blockers: list[str] = []
    lowered = str(filename).lower()
    for marker in ("mtp", "draft", "eagle", "medusa", "speculat"):
        if marker in lowered:
            blockers.append(f"artifact_filename_names_a_draft_or_mtp_head:{marker}")
            break
    meta = metadata or {}
    if meta.get("is_mtp") or meta.get("multi_token_prediction"):
        blockers.append("artifact_metadata_declares_multi_token_prediction")
    if meta.get("is_draft_model") or meta.get("draft_for"):
        blockers.append("artifact_metadata_declares_a_draft_model")
    if meta.get("target_tensor_identity") in (None, ""):
        blockers.append("target_tensor_identity_unbound")
    if speculative_decoding_enabled:
        blockers.append("speculative_decoding_is_enabled")
    return [f"{candidate}:{reason}" for reason in sorted(set(blockers))]


# --------------------------------------------------------------------------
# Licence policy -- ONE source, digest-compared everywhere
# --------------------------------------------------------------------------

LICENCE_POLICY_KIND = "round5_titan_licence_policy"
# An ALLOWLIST, and it stays one. Each entry is a status the author has
# actually recorded, added explicitly. The tempting generalisations -- accept
# anything starting with "approved", accept any truthy value -- each turn a
# licence gate into a spelling convention.
#
# The third status carries an author decision that is CONDITIONAL: it says the
# author has decided, not that the condition is met. It never clears
# `licence_blockers` on its own; `licence_verification_blockers` has to clear
# too, and on an unbound tree it does not.
CONDITIONAL_LICENCE_STATUS = (
    "approved_for_round5_titan_testing_conditional_on_verified_licence")
APPROVED_LICENCE_STATUSES = (
    "approved",
    "approved_for_round5_titan_testing",
    CONDITIONAL_LICENCE_STATUS,
)


def apply_licence_evidence_bindings(
    policy: Mapping[str, Any], bindings: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    """Overlay remote archive evidence without allowing policy changes.

    The binding file may fill only the evidence fields below. Expected
    SPDX, permitted families, approval status and scope remain owned by the
    frozen policy. Invalid evidence fails closed and is not partially applied.
    """
    resolved = json.loads(json.dumps(policy))
    if not bindings:
        return resolved, []
    blockers: list[str] = []
    if bindings.get("artifact_kind") != "round7_ada_licence_bindings":
        return resolved, ["licence_binding_source_wrong_kind"]
    rows = bindings.get("candidates") or {}
    if not isinstance(rows, Mapping):
        return resolved, ["licence_binding_candidates_not_a_mapping"]
    policy_rows = resolved.get("candidates") or {}
    allowed_fields = {
        "archived_spdx", "archived_sha256", "pinned_revision",
        "gguf_terms_conflict", "archive_path", "base_source_repo",
        "gguf_source_repo", "gguf_pinned_revision",
        "gguf_archived_sha256", "gguf_archive_path"}
    for candidate, evidence in rows.items():
        if candidate not in policy_rows:
            blockers.append(f"licence_binding_candidate_outside_policy:{candidate}")
            continue
        if not isinstance(evidence, Mapping):
            blockers.append(f"licence_binding_not_a_mapping:{candidate}")
            continue
        extra = sorted(set(evidence) - allowed_fields)
        if extra:
            blockers.append(
                f"licence_binding_attempts_policy_change:{candidate}:{','.join(extra)}")
            continue
        expected = ((policy_rows[candidate].get("licence_verification") or {})
                    .get("expected_spdx"))
        if evidence.get("archived_spdx") != expected:
            blockers.append(f"licence_binding_spdx_mismatch:{candidate}")
            continue
        required = (
            "archived_sha256", "pinned_revision", "gguf_terms_conflict",
            "archive_path", "base_source_repo", "gguf_source_repo",
            "gguf_pinned_revision", "gguf_archived_sha256",
            "gguf_archive_path")
        if any(evidence.get(field) in (None, "") for field in required):
            blockers.append(f"licence_binding_incomplete:{candidate}")
            continue
        verification = policy_rows[candidate].setdefault(
            "licence_verification", {})
        verification.update(dict(evidence))
        policy_rows[candidate]["licence"] = evidence["archived_spdx"]
    return resolved, sorted(set(blockers))


def licence_policy_blockers(
    policy: Mapping[str, Any] | None, *,
    expected_candidates: Sequence[str] = PRIMARY_ORDER,
) -> list[str]:
    if not isinstance(policy, Mapping):
        return ["licence_policy_absent_or_unreadable"]
    blockers: list[str] = []
    if policy.get("artifact_kind") != LICENCE_POLICY_KIND:
        blockers.append(f"licence_policy_wrong_kind:{policy.get('artifact_kind')}")
    entries = policy.get("candidates")
    if not isinstance(entries, Mapping) or not entries:
        blockers.append("licence_policy_declares_no_candidates")
        return sorted(set(blockers))
    for name in expected_candidates:
        if name not in entries:
            blockers.append(f"licence_policy_omits:{name}")
    return sorted(set(blockers))


def licence_blockers(
    *, candidate: str, policy: Mapping[str, Any] | None,
) -> list[str]:
    """A candidate's licence status, read from the ONE policy source."""
    if not isinstance(policy, Mapping):
        return [f"{candidate}:licence_policy_absent"]
    entry = (policy.get("candidates") or {}).get(str(candidate))
    if not isinstance(entry, Mapping):
        return [f"{candidate}:licence_not_declared_in_the_policy_source"]
    status = str(entry.get("status") or "")
    if status not in APPROVED_LICENCE_STATUSES:
        return [f"{candidate}:licence_not_approved:{status or 'unset'}"]
    if not entry.get("licence"):
        return [f"{candidate}:licence_terms_unrecorded"]
    if not entry.get("approved_by"):
        return [f"{candidate}:licence_approval_has_no_author_record"]
    # The author's decision exists; the evidence it rests on is a separate
    # question and is asked here, at the only gate that stands between a policy
    # entry and a download. This used to run ONLY for the conditional status,
    # so a plainly `approved_for_round5_titan_testing` row carried a populated
    # `licence_verification` block that nothing ever read -- the archive, the
    # pinned revision, the licence family and the GGUF-terms answer were all
    # asserted and never checked. Every approved status is verified now; the
    # conditional status is a statement about how the decision was reached, not
    # a licence to skip the evidence.
    verification = entry.get("licence_verification") or {}
    families = permitted_licence_families(policy)
    blockers = licence_verification_blockers(
        str(candidate),
        archived_spdx=verification.get("archived_spdx"),
        archived_sha256=verification.get("archived_sha256"),
        pinned_revision=verification.get("pinned_revision"),
        gguf_terms_conflict=verification.get("gguf_terms_conflict"),
        permitted_families=families)
    # The row's own `licence` field was read for truthiness only, so a value of
    # "pending_archived_licence_evidence" or "Apache-2.0_pending_exact_archive"
    # satisfied it. It is free text describing the author's declaration, not an
    # enum, so it is not forced into one; what IS required is that it names an
    # approved family, and that it does not disagree with the archive once the
    # archive exists. Those are the two ways this field can be wrong.
    declared = str(entry.get("licence") or "").strip()
    spdx = str(verification.get("archived_spdx") or "").strip()
    archived = str(verification.get("archived_sha256") or "").strip()
    if declared and not any(family in declared for family in families):
        blockers.append(
            f"{candidate}:{LICENCE_FAMILY_MISMATCH}:declared_{declared}_"
            "names_no_approved_family")
    if declared and spdx and spdx not in declared:
        blockers.append(
            f"{candidate}:{LICENCE_DECLARATION_DISAGREES_WITH_ARCHIVE}:"
            f"declared_{declared}_archived_{spdx}")
    # A declaration still marked pending, over a completed archive, is the
    # exact state that let a row clear the gate while its own text said the
    # evidence had not been taken.
    if archived and any(marker in declared.lower()
                        for marker in ("pending", "unverified", "tbd")):
        blockers.append(
            f"{candidate}:licence_declaration_still_marked_pending_over_a_"
            "completed_archive")
    return sorted(set(blockers))


def policy_digest_blockers(
    *, expected_digest: str | None, artifact_digests: Mapping[str, Any],
) -> list[str]:
    """Every artifact must name the SAME licence policy digest.

    Copying an allowlist into readiness, the probes and the manager is how three
    lists drift apart and a candidate passes one gate it should not. There is one
    file, and every artifact records its digest so a reader can prove they all
    read the same one.
    """
    if not expected_digest:
        return ["licence_policy_digest_unbound"]
    blockers: list[str] = []
    for label, digest in sorted(artifact_digests.items()):
        if not digest:
            blockers.append(f"{label}_does_not_record_the_licence_policy_digest")
        elif str(digest) != str(expected_digest):
            blockers.append(f"{label}_licence_policy_digest_mismatch")
    return sorted(set(blockers))


# --------------------------------------------------------------------------
# Occupancy canary
# --------------------------------------------------------------------------

def occupancy_blockers(
    samples: Sequence[Mapping[str, Any]],
    *,
    owned_pids: Sequence[int] = (),
    hardware: str | None = None,
    devices: Sequence[int] | None = None,
) -> list[str]:
    """Refuse to start a TIMED stage on a contaminated host.

    The manager WAITS on contamination. It never kills a process it did not
    start: a foreign job on the author's own machine may be the author's, and
    killing it to make a benchmark cleaner is not a repair.

    `devices` narrows the check to the cards the exam holds, and is required on
    a shared host. Without it this function asks "is the MACHINE quiet?", which
    on a multi-tenant box is both unanswerable and the wrong question: six
    neighbours at 90% utilisation are not contamination of a two-card lease,
    they are the normal state of somebody else's work. Left unscoped here, the
    manager's wait-on-contamination rule -- which by design never gives up and
    never kills -- would block forever on a host that is behaving exactly as
    expected. Scoped, it still refuses the moment a foreign process appears on a
    card the exam actually holds, which is the contamination that can corrupt a
    measurement.

    The neighbours are not thereby dismissed. They are recorded, and their
    effect on clock stability is carried by the reference canary's drift check,
    which can withhold the performance rank. What must not happen is for
    unavoidable neighbourhood noise to be reported as a per-root verdict.
    """
    owned = {int(pid) for pid in owned_pids}
    spec = host_spec(hardware)
    expected_count = int(spec["gpu_count"])
    blockers: list[str] = []
    if devices is None:
        if spec.get("shared_host"):
            return ["shared_host_occupancy_check_requires_the_leased_devices"]
        if len(samples) != expected_count:
            blockers.append(
                f"occupancy_sampled_{len(samples)}_of_{expected_count}_cards")
    else:
        wanted = {int(device) for device in devices}
        sampled = {int(sample.get("device")) for sample in samples
                   if sample.get("device") is not None}
        missing = sorted(wanted - sampled)
        if missing:
            blockers.append(
                f"occupancy_did_not_sample_held_cards:"
                f"{','.join(str(device) for device in missing)}")
        samples = [sample for sample in samples
                   if int(sample.get("device", -1)) in wanted]
    for sample in samples:
        device = str(sample.get("device"))
        foreign = [int(pid) for pid in (sample.get("compute_pids") or [])
                   if int(pid) not in owned]
        if foreign:
            blockers.append(f"gpu{device}_foreign_compute_process:{sorted(foreign)}")
        # One positively established explanation governs BOTH the memory and the
        # utilisation test. `explained_by_owned_server` is true only when the
        # card carries at least one owned compute PID and every visible PID is
        # owned; an empty pid list, a foreign PID, or ownership evidence that
        # could not be parsed all leave it false.
        #
        # Utilisation was excluded from this before, and under `vram_holder_only`
        # that made Stage B unstartable: the manager tells its own holder to
        # release ~47 GiB per card so a server can load, nvidia-smi samples the
        # card busy while that happens, and the canary reported the manager's own
        # command as sustained foreign utilisation. A foreign process is still
        # caught by the foreign-process test above whatever its load, and a busy
        # card with NO visible owner is still caught here, because absence of
        # evidence never explains anything.
        #
        # No threshold moves.
        explained = bool(sample.get("explained_by_owned_server"))
        used = float(sample.get("memory_used_mib") or 0.0)
        if used > OCCUPANCY_MAX_BASELINE_VRAM_MIB and not explained:
            blockers.append(f"gpu{device}_unexplained_baseline_vram_mib:{used:.0f}")
        utilisation = float(sample.get("utilisation_percent") or 0.0)
        if utilisation > OCCUPANCY_MAX_UTILISATION_PERCENT and not explained:
            blockers.append(
                f"gpu{device}_sustained_utilisation_percent:{utilisation:.1f}")
    return sorted(set(blockers))


def occupancy_verdict(blockers: Sequence[str]) -> dict[str, Any]:
    return {
        "clear": not blockers,
        "blockers": sorted(set(str(b) for b in blockers)),
        "verdict": None if not blockers else TIMING_CONTAMINATED_NONVERDICT,
        "action": ("proceed" if not blockers else
                   "wait; do not run a timed stage and do not kill a foreign process"),
        "max_utilisation_percent": OCCUPANCY_MAX_UTILISATION_PERCENT,
        "max_baseline_vram_mib": OCCUPANCY_MAX_BASELINE_VRAM_MIB,
    }


def monitoring_unknown_verdict(reason: str) -> dict[str, Any]:
    """The occupancy verdict when the evidence for one could not be obtained.

    Same shape as `occupancy_verdict` -- built from it, so the two cannot drift
    -- but carrying MONITORING_UNKNOWN instead of TIMING_CONTAMINATED_NONVERDICT.
    Nothing was seen on a leased card, so this is not contamination; nothing
    could be seen at all, so it is emphatically not clear.

    The thresholds are still reported. They are the gate's configuration, not a
    measurement, and they did not stop applying just because this sample failed.
    """
    verdict = occupancy_verdict([f"{MONITORING_UNKNOWN}:{reason}"])
    verdict["verdict"] = MONITORING_UNKNOWN
    verdict["action"] = ("wait; monitoring evidence is unavailable, so neither "
                         "a clean nor a contaminated verdict can be given")
    return verdict


# --------------------------------------------------------------------------
# Host identity
# --------------------------------------------------------------------------

#: Devices this run bound, sampled DURING a timed arm rather than before it.
MID_ARM_MIN_PROBE_INTERVAL_SECONDS = 15.0


def foreign_process_blockers(
    samples: Sequence[Mapping[str, Any]],
    *,
    owned_pids: Sequence[int] = (),
    devices: Sequence[int] | None = None,
) -> list[str]:
    """Contention detected DURING a timed arm. Foreign compute processes only.

    This is deliberately NARROWER than `occupancy_blockers`, and the difference
    is not a relaxation -- it is a different question asked at a different
    moment.

    Before a stage the host is supposed to be idle, so baseline VRAM above
    64 MiB and sustained utilisation above 5% both mean somebody else is here,
    and `occupancy_blockers` refuses on either. DURING an arm both of those
    signals are OURS by construction: this run's own servers hold GiBs of
    weights and drive the cards to saturation, which is the arm working
    correctly. Reusing the pre-stage predicate mid-arm would therefore fire on
    every probe and void every arm, which is not a stricter gate but a broken
    one.

    The one signal that still means "someone else is on this card" while our
    own work is running is a compute process that is not ours. That is what
    this checks, on the bound devices only.

    Returns reasons with PIDs reduced to COUNTS. A void record names how many
    foreign processes appeared, never who they belong to or what they run.
    """
    owned = {int(pid) for pid in owned_pids}
    bound = None if devices is None else {int(device) for device in devices}
    blockers: list[str] = []
    for sample in samples:
        try:
            device = int(sample.get("device"))
        except (TypeError, ValueError):
            continue
        if bound is not None and device not in bound:
            continue
        foreign = [int(pid) for pid in (sample.get("compute_pids") or [])
                   if int(pid) not in owned]
        if foreign:
            blockers.append(
                f"gpu{device}_foreign_compute_process_count:{len(foreign)}")
    return sorted(set(blockers))


def host_blockers(
    devices: Sequence[Mapping[str, Any]] | None,
    *,
    hardware: str | None = None,
    host_device_count: int | None = None,
) -> list[str]:
    """The live host must BE the machine the registry declares, not resemble it.

    `hardware` defaults to the Titan host, so every existing caller keeps its
    behaviour verbatim. A registry that declares a different host is held to
    that host's card count, name, compute capability and memory instead --
    never to a relaxed version of the Titan one.

    A profile marked `shared_host` is the one exception, and it is a narrowing
    rather than a relaxation. For those, `devices` must be the LEASED cards and
    `host_device_count` the size of the whole machine. The identity checks --
    name, compute capability, memory, distinct UUIDs -- are unchanged and are
    applied to every leased card. What is given up is the claim that no other
    card exists, which on a multi-tenant host is not a claim anyone can make.
    Requiring the host's true size as a separate argument is deliberate: it
    cannot be defaulted, so a shared-host run cannot be recorded as though the
    exam owned the machine simply by omitting to mention the neighbours.
    """
    if devices is None:
        return ["gpu_inventory_unavailable"]
    spec = host_spec(hardware)
    expected_count = int(spec["gpu_count"])
    fragment = str(spec["gpu_name_fragment"])
    expected_capability = str(spec["compute_capability"])
    expected_memory = int(spec["memory_total_mib"])
    tolerance = int(spec["memory_tolerance_mib"])
    blockers: list[str] = []
    if spec.get("shared_host"):
        if len(devices) != expected_count:
            blockers.append(f"leased_card_count_{len(devices)}_not_{expected_count}")
        if host_device_count is None:
            blockers.append("shared_host_requires_declared_host_device_count")
        elif int(host_device_count) < expected_count:
            blockers.append(
                f"host_has_{int(host_device_count)}_cards_fewer_than_the_"
                f"{expected_count}_leased")
    elif len(devices) != expected_count:
        blockers.append(f"gpu_count_{len(devices)}_not_{expected_count}")
    elif host_device_count is not None and int(host_device_count) != len(devices):
        # A dedicated-host profile whose caller can see MORE cards than it was
        # given is being used on a machine it does not describe.
        blockers.append(
            f"host_has_{int(host_device_count)}_cards_but_profile_"
            f"{spec['hardware']}_owns_the_whole_machine")
    for index, device in enumerate(devices):
        name = str(device.get("name") or "")
        if fragment.upper() not in name.upper():
            blockers.append(
                f"gpu{index}_name_{name or 'unknown'}_is_not_a_{spec['not_a']}")
        capability = str(device.get("compute_capability") or "")
        if capability and capability != expected_capability:
            blockers.append(
                f"gpu{index}_compute_capability_{capability}_not_"
                f"{expected_capability}")
        elif not capability:
            blockers.append(f"gpu{index}_compute_capability_unrecorded")
        try:
            memory = int(device.get("memory_total_mib"))
        except (TypeError, ValueError):
            blockers.append(f"gpu{index}_memory_unrecorded")
        else:
            if abs(memory - expected_memory) > tolerance:
                blockers.append(f"gpu{index}_memory_{memory}_mib_not_{expected_memory}")
        if not device.get("uuid"):
            blockers.append(f"gpu{index}_uuid_unrecorded")
    if len({str(device.get("uuid")) for device in devices}) != len(devices):
        blockers.append("gpu_uuids_are_not_distinct")
    return sorted(set(blockers))


# --------------------------------------------------------------------------
# Stage-A requirements
# --------------------------------------------------------------------------

STAGE_A_CAPACITY_PROBE_TOKENS = 40609
STAGE_A_REALISTIC_BUCKET_TOKENS = 32768
STAGE_A_TOOL_PROMPTS = 20
STAGE_A_TERMINAL_PROMPTS = 4
STAGE_A_MIN_FREE_VRAM_MIB = 1024
STAGE_A_COHERENCE_PROBE_CONTEXTS = (2048, 8192, 32768)
STAGE_A_CAPACITY_DIAGNOSTIC_TIMEOUT_SECONDS = 900.0
STAGE_A_PERMITTED_TERMINAL_RETRIES = 1

# A probe proves nothing about capacity unless the PROVIDER agrees how many
# tokens it served. A word-count filler is not tokenizer-exact and HTTP 200 says
# only that a request succeeded, so the gate reads `usage.prompt_tokens` and
# requires it to land in a registered range.
STAGE_A_CAPACITY_MIN_PROMPT_TOKENS = 36864     # 0.9 x the 40,960 ceiling
STAGE_A_CAPACITY_MAX_PROMPT_TOKENS = CONTEXT_TOKENS
STAGE_A_REALISTIC_MIN_PROMPT_TOKENS = STAGE_A_REALISTIC_BUCKET_TOKENS
STAGE_A_TOKEN_CALIBRATION_ATTEMPTS = 6

#: The registered workload's maximum assembled request. Measured on the
#: 2026-09-18 soak: the 32k bucket plus accumulated tool results reached 44,086
#: tokens (server logs), and Pi compaction is disabled so the assembled request
#: is not bounded below the ceiling. A substrate must be able to serve at least
#: this to carry the workload; a model whose native trained context is smaller
#: is NQ. Author decision `workstream_b_context_decision_2026_09_19`, Option C.
WORKLOAD_MAX_ASSEMBLED_TOKENS = 44100


def training_context_blockers(
    training_context_tokens: int | None,
    *,
    required: int = WORKLOAD_MAX_ASSEMBLED_TOKENS,
) -> list[str]:
    """A candidate whose trained context cannot hold the workload is NQ.

    Option C: the fresh exam selects a substrate whose native trained context
    (the GGUF's `n_ctx_train`, which llama.cpp caps the served slot to) holds the
    registered workload's maximum assembled request. `None` means unbound, which
    is a blocker rather than a pass -- an unread context is not a large one.
    """
    if training_context_tokens is None:
        return ["training_context_unbound"]
    observed = int(training_context_tokens)
    if observed < int(required):
        return [f"training_context_{observed}_below_workload_{int(required)}"]
    return []


def training_context_gate_blockers(
    candidate: str,
    spec: Mapping[str, Any] | None,
    *,
    panel_version: str | None,
) -> list[str]:
    """Option C's capacity gate, scoped to the fresh v3 panel.

    The gate is a property of the fresh panel's contract, added before any v3
    outcome was observed. The v2 and Round-7 panels keep the behaviour they ran
    under; retroactively re-gating a completed round would rewrite what it was.
    For the v3 panel a candidate whose bound `n_ctx_train` is absent or below
    the registered workload maximum is NQ -- a missing value is refused rather
    than treated as a large one.
    """
    if panel_version != V3_TITAN_PANEL_VERSION:
        return []
    reasons = training_context_blockers(
        (spec or {}).get("expected_training_context_tokens"))
    return [f"{candidate}:{reason}" for reason in reasons]

# A finite bound on one candidate's Stage A. Twenty tool prompts and four
# terminal probes can each consume a long diagnostic request timeout, and with
# retries a badly behaved model can multiply that into days -- which turns an
# overnight run into a multi-day one with nobody awake to stop it.
#: The per-REQUEST timeout for every Stage-A probe. It used to be
#: ROOT_WALL_RAIL_SECONDS, on all eleven request sites, which meant the 360 s
#: rail was still the operative bound on whether a candidate reached the exam --
#: a probe whose request was cut off returns an error, the check fails, and the
#: candidate is NQ'd for being slow by a route that never mentions time. Taking
#: the elapsed-time COMPARISON out of the multi-turn probe without taking out
#: the timeout underneath it changed nothing.
#:
#: 1,800 s is far above any legitimate probe. `deadline.budget()` still clamps
#: each request to what remains of the candidate's whole Stage-A budget, so this
#: cannot run away.
STAGE_A_REQUEST_TIMEOUT_SECONDS = 1800.0
# Round 7 only: loading a previously unmeasured 27B--35B artifact from a cold
# cache on a shared Ada host gets the same diagnostic allowance as a Stage-A
# request. The completed rounds retain their 420 s acquisition default.
ROUND7_SERVER_START_TIMEOUT_SECONDS = 1800.0

#: The historical whole-candidate Stage-A budget. UNCHANGED at 45 minutes: the
#: Round-5, L40 and Round-6 registries all declare 2,700 in `runtime_budget`,
#: and moving the constant would put the code into disagreement with three
#: completed rounds over a value they actually ran under.
STAGE_A_CANDIDATE_TIMEOUT_SECONDS = 2700.0     # 45 minutes

#: What Round 7 declares instead, in its own registry. An INFRASTRUCTURE stop
#: that keeps a wedged candidate from holding two leased cards indefinitely, not
#: a speed gate -- and at 45 minutes it was becoming one: with per-request
#: timeouts at 1,800 s, two slow probes consume the whole budget and the
#: candidate times out for being slow, which is the same exclusion one level up
#: from the one this round removed. Two hours cannot fire on a model that is
#: merely slow on a contended card, and still bounds the panel.
ROUND7_STAGE_A_CANDIDATE_TIMEOUT_SECONDS = 7200.0     # 2 hours
#: Round 7 only. Declared beside the Stage-A timeout and for the same reason:
#: Round 5, the L40 round and Round 6 all ran under MANAGER_DEADLINE_SECONDS at
#: 22 h, and moving that constant would rewrite what they ran under. Twelve
#: arms at the historical 1.625-2.625 h per-arm band extrapolates to 19.5-31.5
#: h, but that is not a validated upper bound for the new 27B--35B rows. The
#: deadline is a stop, never a gate -- nothing about
#: eligibility, thresholds or root counts depends on it -- but a deadline that
#: bites decides WHICH candidates were measured, and on a shared host it
#: decides that by how busy the neighbours were. That is the machine choosing
#: the panel, which is exactly what this round removed from eligibility.
ROUND7_MANAGER_DEADLINE_SECONDS = 115200               # 32 hours


def stage_a_candidate_timeout_seconds(
    registry: "Mapping[str, Any] | None" = None,
) -> float:
    """The Stage-A budget this registry declares, or the historical default."""
    budget = ((registry or {}).get("runtime_budget") or {}
              if isinstance(registry, Mapping) else {})
    declared = budget.get("stage_a_candidate_timeout_seconds")
    try:
        return float(declared)
    except (TypeError, ValueError):
        return STAGE_A_CANDIDATE_TIMEOUT_SECONDS
MANAGER_DEADLINE_SECONDS = 79200.0             # 22 hours


def manager_deadline_seconds(
    registry: "Mapping[str, Any] | None" = None,
) -> float:
    """The whole-funnel deadline declared by this registry.

    Completed registries that omit the field retain the historical 79,200 s
    default. New registries carry their own value, so a direct or resumed
    manager invocation cannot silently fall back to a different round's bound.
    """
    budget = ((registry or {}).get("runtime_budget") or {}
              if isinstance(registry, Mapping) else {})
    declared = budget.get("manager_deadline_seconds")
    try:
        return float(declared)
    except (TypeError, ValueError):
        return MANAGER_DEADLINE_SECONDS

TERMINAL_STAGE_A_TIMEOUT = "STAGE_A_CANDIDATE_TIMEOUT"

# ---------------------------------------------------------------------------
# The frozen exam prompt, and what a harness failure is allowed to mean
# ---------------------------------------------------------------------------

# The permanent classification of the 2026-08-22 Stage-B attempt's 120 root
# records, assigned by the author's replay ruling
# (archive/round10/archive/ROUND5_TITAN_STAGE_B_REPLAY_RULING_2026-08-23.md). Records carrying
# it are prohibited from scoring, eligibility, comparison, selection, appendix
# results and claim support -- preserved as failure evidence, nothing else.
VOID_SHARED_HARNESS_FAILURE = (
    "VOID_SHARED_HARNESS_FAILURE_BEFORE_FIRST_MODEL_REQUEST")

# Every runtime field the Stage-B chain dereferences or the servers launch
# with. The exam_prompt KeyError survived readiness, rehearsal and 428 tests
# because nothing validated that the fields the LIVE path reads actually
# exist -- the fixture runner never imports the live path. Validated by
# readiness AND again by the Stage-B launcher before any server starts.
REQUIRED_RUNTIME_FIELDS = (
    "engine", "llama_cpp_root", "llama_server", "required_commit",
    "dataset_root", "hidden_table_root",
    "context_tokens", "kv_cache_type_k", "kv_cache_type_v",
    "output_ceiling_tokens", "temperature", "enable_thinking",
    "gpu_layers", "slots_per_server", "root_wall_rail_seconds",
    "pi_entry", "system_prompt", "tool_extension",
    "exam_prompt_path", "exam_prompt_sha256",
)


def runtime_schema_blockers(runtime: Mapping[str, Any] | None) -> list[str]:
    """Every required runtime field must be PRESENT and non-empty.

    Presence only -- host-path existence is a host question, answered by
    readiness with --require flags on the host. What this refuses is the
    configuration shape that produced the void run: a field the live chain
    dereferences that no artifact ever carried.
    """
    if not isinstance(runtime, Mapping):
        return ["runtime_block_absent_or_unreadable"]
    blockers = []
    for field in REQUIRED_RUNTIME_FIELDS:
        value = runtime.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            blockers.append(f"runtime_field_missing_or_empty:{field}")
    return blockers


def exam_prompt_blockers(
    *, runtime: Mapping[str, Any] | None,
    file_exists: bool, file_sha256: str | None, file_text: str | None,
) -> list[str]:
    """Does the frozen exam prompt exist, match its digest, and say anything?

    Pure: the caller does the I/O and hands in what it found. Four separate
    questions, because collapsing them loses which one failed: is a path
    bound, is a digest bound, does the file exist, and do the bytes match.
    An empty prompt passes a digest check trivially and is still not a task,
    so emptiness is refused on its own.
    """
    runtime = runtime or {}
    blockers = []
    path = str(runtime.get("exam_prompt_path") or "").strip()
    expected = str(runtime.get("exam_prompt_sha256") or "").strip().lower()
    if not path:
        blockers.append("exam_prompt_unbound:no_path_in_runtime")
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        blockers.append("exam_prompt_unbound:digest_not_64_hex")
        return blockers
    if not file_exists:
        blockers.append(f"exam_prompt_unbound:file_absent:{path}")
        return blockers
    if str(file_sha256 or "").lower() != expected:
        blockers.append(
            f"exam_prompt_digest_mismatch:expected_{expected[:12]}_"
            f"got_{str(file_sha256 or 'none')[:12]}")
    if not str(file_text or "").strip():
        blockers.append("exam_prompt_unbound:file_is_empty")
    return blockers


def void_manifest_blockers(
    manifest: Mapping[str, Any] | None,
    observed: Mapping[str, str],
) -> list[str]:
    """The void evidence must still be EXACTLY what was classified.

    Pure: the caller walks the void directory and hands in relative path ->
    sha256. Three failures kept separate: a manifested file that vanished, a
    manifested file whose bytes changed, and a file present that the
    classification never covered. Any of the three means the failure evidence
    the ruling ordered preserved is no longer the failure evidence.
    """
    if not isinstance(manifest, Mapping):
        return ["void_classification_absent_or_unreadable"]
    if manifest.get("classification") != VOID_SHARED_HARNESS_FAILURE:
        return [f"void_classification_wrong:{manifest.get('classification')}"]
    declared = manifest.get("files")
    if not isinstance(declared, Mapping) or not declared:
        return ["void_classification_declares_no_files"]
    blockers = []
    for rel, expected in sorted(declared.items()):
        actual = observed.get(str(rel))
        if actual is None:
            blockers.append(f"void_file_missing:{rel}")
        elif str(actual).lower() != str(expected).lower():
            blockers.append(f"void_file_tampered:{rel}")
    for rel in sorted(observed):
        if rel not in declared:
            blockers.append(f"void_file_unmanifested:{rel}")
    return blockers


# The replay ruling and the carry-forward artifact it authorizes. The manifest
# is not decoration: reused Stage-A evidence is verified against it, fail
# closed, BEFORE readiness or membership construction on every replay launch.
REPLAY_RULING_PATH = "archive/round10/archive/ROUND5_TITAN_STAGE_B_REPLAY_RULING_2026-08-23.md"
STAGE_A_CARRY_FORWARD_KIND = "round5_titan_stage_a_carry_forward"
# State a PREPARED replay directory must not contain at first launch. Mirrors
# NEVER_IMPORTED in scripts/prepare_round5_titan_replay.py (which stays
# stdlib-only and cannot import this module).
REPLAY_PROHIBITED_STATE = (
    "readiness.json", "canary/", "canary-drift.json",
    "stage_b_membership.json", "stage_b/", "stages/20-stage-b-*.json",
    "selection.json", "completion.json", "snapshot/", "snapshot.json",
    "heartbeat.json", "launcher.json", "reserve_activations.json", "logs/",
    "evidence_manifest.json", "appendix_*",
)


def stage_a_carry_forward_blockers(
    manifest: Mapping[str, Any] | None,
    observed: Mapping[str, str],
    stage_records: Mapping[str, Mapping[str, Any] | None],
    *,
    prohibited_present: Sequence[str] = (),
    expected_candidates: Sequence[str] = PRIMARY_ORDER,
) -> list[str]:
    """Carried Stage-A evidence must be EXACTLY what the ruling reused.

    Pure: the caller walks the replay run directory and hands in relative
    path -> sha256 for every file under stage_a/ and stages/10-stage-a-*.json
    (`observed`), the parsed carried stage records keyed by candidate
    (`stage_records`, None for unreadable), and any prohibited downstream
    state found before launch. Fail closed: a replay whose reused evidence
    cannot be verified byte-for-byte against the carry-forward manifest, whose
    terminal records do not match their candidates, or whose directory already
    holds downstream state, must stop before the first model request.
    """
    if not isinstance(manifest, Mapping):
        return ["carry_forward_absent_or_unreadable"]
    if manifest.get("artifact_kind") != STAGE_A_CARRY_FORWARD_KIND:
        return [f"carry_forward_wrong_kind:{manifest.get('artifact_kind')}"]
    # The original identifier is retained in immutable historical manifests.
    # Both names designate the byte-identical L0-moved record; no other alias.
    if manifest.get("ruling") not in (
        REPLAY_RULING_PATH,
        "round10/archive/ROUND5_TITAN_STAGE_B_REPLAY_RULING_2026-08-23.md",
    ):
        return [f"carry_forward_wrong_ruling:{manifest.get('ruling')}"]
    declared = manifest.get("files")
    if not isinstance(declared, Mapping) or not declared:
        return ["carry_forward_declares_no_files"]

    blockers: list[str] = []
    expected = tuple(expected_candidates)

    # Exactly the frozen panel's candidates, no more and no fewer.
    declared_candidates = sorted(
        {str(rel).split("/", 2)[1] for rel in declared
         if str(rel).startswith("stage_a/") and str(rel).count("/") >= 2})
    if declared_candidates != sorted(expected):
        blockers.append(
            "carry_forward_candidates_mismatch:"
            f"declared={','.join(declared_candidates)}")

    # Exactly one terminal disposition record per candidate.
    declared_records = sorted(
        str(rel) for rel in declared
        if str(rel).startswith("stages/10-stage-a-")
        and str(rel).endswith(".json"))
    expected_records = sorted(
        f"stages/10-stage-a-{candidate}.json" for candidate in expected)
    if declared_records != expected_records:
        blockers.append(
            "carry_forward_stage_records_mismatch:"
            f"declared={','.join(declared_records)}")

    # Every carried byte matches the manifest; nothing carried is unlisted.
    for rel, want in sorted(declared.items()):
        got = observed.get(str(rel))
        if got is None:
            blockers.append(f"carried_file_missing:{rel}")
        elif str(got).lower() != str(want).lower():
            blockers.append(f"carried_file_tampered:{rel}")
    for rel in sorted(observed):
        if rel not in declared:
            blockers.append(f"carried_file_unmanifested:{rel}")

    # Every reused stage record is a TERMINAL verdict for ITS candidate.
    for candidate in expected:
        record = stage_records.get(candidate)
        if not isinstance(record, Mapping):
            blockers.append(f"carried_record_unreadable:{candidate}")
            continue
        if record.get("disposition") != DISPOSITION_TERMINAL:
            blockers.append(
                f"carried_record_not_terminal:{candidate}:"
                f"{record.get('disposition')}")
        if record.get("key") != f"10-stage-a-{candidate}":
            blockers.append(
                f"carried_record_wrong_key:{candidate}:{record.get('key')}")
        if record.get("candidate") != candidate:
            blockers.append(
                f"carried_record_wrong_candidate:{candidate}:"
                f"{record.get('candidate')}")

    # No downstream state may pre-exist the launch it is supposed to follow.
    for name in sorted(prohibited_present):
        blockers.append(f"replay_state_not_fresh:{name}")
    return blockers


def harness_error_root_blockers(artifact: Mapping[str, Any] | None) -> list[str]:
    """Refuse to score ANY artifact carrying harness-error roots.

    A root record whose invalidity_reason is harness_error describes the
    harness, not the candidate, and arithmetic over it produces the void run's
    exact failure shape: zero successes read as zero performance, a vacuous
    rail component read as a 10.00 score, and a confident no-eligible-model
    verdict about models that were never asked anything.
    """
    if not isinstance(artifact, Mapping):
        return ["stage_b_artifact_absent_or_unreadable"]
    candidate = str(artifact.get("candidate") or "unknown")
    tainted = [str(root.get("root_id") or "?")
               for root in (artifact.get("execution") or {}).get("roots", [])
               or artifact.get("roots", [])
               if isinstance(root, Mapping)
               and str(root.get("invalidity_reason") or "") == "harness_error"]
    if tainted:
        return [f"{candidate}:{VOID_SHARED_HARNESS_FAILURE}:"
                f"{len(tainted)}_harness_error_roots"]
    return []
TERMINAL_MANAGER_DEADLINE = "MANAGER_DEADLINE_EXCEEDED"

STAGE_A_CHECKS = (
    "source_revision", "lfs_digest", "local_sha256", "licence", "architecture",
    "block_count", "tokenizer", "chat_template", "quantization",
    "target_versus_mtp_identity", "response_model_alias",
    "sm52_kernels", "binary_digest",
    "load_at_context_ceiling", "no_cpu_fallback", "device_isolation",
    "free_vram_margin", "concurrent_servers",
    "capacity_probe", "realistic_multiturn_probe",
    "tool_call_probe", "terminal_answer_probe", "pi_microtrajectory",
    "repeated_request_variation", "provider_metadata", "gpu_utilisation",
    "network_denial", "cache_isolation", "process_group_cleanup",
)
STAGE_A_TWO_CARD_EXTRA_CHECKS = ("output_coherence_2k", "output_coherence_8k",
                                 "output_coherence_32k", "pair_symmetry")


def stage_a_required_checks(profile_name: str) -> tuple[str, ...]:
    checks = tuple(STAGE_A_CHECKS)
    if topology_profile(profile_name)["gpus_per_worker"] > 1:
        checks = checks + STAGE_A_TWO_CARD_EXTRA_CHECKS
    return checks


def evaluate_stage_a(
    record: Mapping[str, Any], *, profile_name: str
) -> dict[str, Any]:
    """Stage A passes only when every required check is present AND passed.

    An absent check is a failure, not a pass. The distinction matters because a
    probe that never ran and a probe that ran clean produce the same silence.
    """
    required = stage_a_required_checks(profile_name)
    checks = record.get("checks") or {}
    reasons: list[str] = []
    for name in required:
        entry = checks.get(name)
        if entry is None:
            reasons.append(f"stage_a_check_absent:{name}")
        elif not (entry.get("passed") if isinstance(entry, Mapping) else bool(entry)):
            detail = (entry.get("reason") if isinstance(entry, Mapping) else None)
            reasons.append(f"stage_a_check_failed:{name}" + (f":{detail}" if detail else ""))

    # Only analyse the tool probe when a record EXISTS. An absent probe is
    # already reported as an absent check; reporting it a second time as "no
    # tool call observed" would conflate "we never ran it" with "it ran and the
    # model never called a tool", which are different findings.
    tool = checks.get("tool_call_probe")
    if isinstance(tool, Mapping):
        observed = int(tool.get("observed_calls") or 0)
        prompts = int(tool.get("prompts") or 0)
        if prompts and prompts != STAGE_A_TOOL_PROMPTS:
            reasons.append(f"stage_a_tool_prompts_{prompts}_not_{STAGE_A_TOOL_PROMPTS}")
        if observed < MIN_OBSERVED_TOOL_CALLS:
            # Zero observed calls gives tool conformance zero; it is NEVER read
            # as a perfect zero-malformation rate.
            reasons.append("stage_a_no_tool_call_observed")
        else:
            malformed = int(tool.get("malformed_calls") or 0)
            rate = malformed / observed
            if rate > MAX_TOOL_MALFORMATION:
                reasons.append(
                    f"stage_a_tool_malformation_{rate:.4f}_above_{MAX_TOOL_MALFORMATION}")

    margins = record.get("free_vram_mib_at_peak") or {}
    for device, free in sorted(margins.items()):
        if float(free) < STAGE_A_MIN_FREE_VRAM_MIB:
            reasons.append(
                f"stage_a_free_vram_gpu{device}_{float(free):.0f}_below_"
                f"{STAGE_A_MIN_FREE_VRAM_MIB}")

    return {
        "passed": not reasons,
        "failure_reasons": sorted(set(reasons)),
        "required_checks": list(required),
        "topology": profile_name,
        "status": "PASS" if not reasons else "NQ",
    }


def terminal_answer_verdict(
    *, finish_reason: str | None, content: str | None, retried: bool
) -> dict[str, Any]:
    """``finish_reason == "length"`` is INCONCLUSIVE, not a failure.

    A model that filled the frozen 4,096-token budget did not decline to answer;
    the probe simply did not observe a terminal answer. One prespecified retry at
    the SAME frozen ceiling is permitted. Choosing a candidate-specific token
    limit after seeing an output would tune the instrument to the candidate.
    """
    has_content = bool((content or "").strip())
    if str(finish_reason) == "length" and not has_content:
        if retried:
            return {"passed": False, "verdict": "inconclusive_after_permitted_retry",
                    "reason": "output ceiling reached twice with no terminal content",
                    "output_ceiling_tokens": OUTPUT_CEILING_TOKENS}
        return {"passed": False, "verdict": "inconclusive_retry_permitted",
                "reason": "finish_reason=length is inconclusive, not a failure",
                "retry_permitted": True,
                "retries_permitted": STAGE_A_PERMITTED_TERMINAL_RETRIES,
                "output_ceiling_tokens": OUTPUT_CEILING_TOKENS}
    return {"passed": has_content,
            "verdict": "terminal_answer" if has_content else "empty_terminal_content",
            "finish_reason": finish_reason,
            "output_ceiling_tokens": OUTPUT_CEILING_TOKENS}


# --------------------------------------------------------------------------
# Stage-B execution guards
# --------------------------------------------------------------------------

def check_round5_execution(
    *,
    pool: str,
    mode: str,
    topology: str,
    registry_topology: str | None,
    exam_roots: int,
    templates: int,
    roots_override_requested: bool,
    visible_logical_gpus: int,
    generation_record_valid: bool,
    readiness_green: bool,
    execution_authorization_set: bool,
    candidate_requested: Sequence[str],
    registry_candidates: Sequence[str],
    hash_checks: Mapping[str, tuple[str | None, str | None]],
    referenced_paths: Sequence[str] = (),
) -> list[str]:
    """Every reason this invocation must not produce a Round 5 Stage-B verdict.

    ``hash_checks`` maps a label to ``(expected, actual)``. A missing expected
    value is a blocker, not a pass: an unbound artifact is exactly what the
    guard exists to catch.
    """
    blockers: list[str] = []

    if str(pool) != EXAM_POOL:
        blockers.append(f"pool_not_round5_titan_compact:{pool}")
    if str(pool) in SUPERSEDED_POOLS:
        blockers.append(f"superseded_pool:{pool}")
    if str(mode) not in {"plan", "stage_b"}:
        blockers.append(f"mode_not_explicit:{mode}")

    if registry_topology is None:
        blockers.append("registry_does_not_declare_a_topology_profile")
    elif str(registry_topology) != str(topology):
        blockers.append(
            f"topology_{topology}_differs_from_registry_{registry_topology}")
    try:
        profile = topology_profile(topology)
    except UnknownTopology:
        blockers.append(f"unknown_topology_profile:{topology}")
        profile = None

    if profile is not None:
        needed = max(max(group) for group in profile["device_groups"]) + 1
        if int(visible_logical_gpus) < needed:
            blockers.append(
                f"visible_logical_gpus_{visible_logical_gpus}_below_{needed}_"
                f"for_{topology}")

    # `--roots` is REJECTED, not defaulted. Removing a default is not enough:
    # the Round-4 defect was a guard that checked the MANIFEST size and a runner
    # that then sliced it.
    if roots_override_requested:
        blockers.append("roots_override_requested_in_qualification_mode")
    if int(exam_roots) != EXAM_ROOTS:
        blockers.append(f"exam_roots_{exam_roots}_not_{EXAM_ROOTS}")
    if int(templates) != EXAM_TEMPLATES:
        blockers.append(f"exam_templates_{templates}_not_{EXAM_TEMPLATES}")
    if not generation_record_valid:
        blockers.append("one_shot_exam_generation_record_invalid_or_absent")

    if str(mode) == "stage_b":
        if not readiness_green:
            blockers.append("readiness_gate_is_not_green")
        if not execution_authorization_set:
            blockers.append("execution_authorization_not_set")

    for label, (expected, actual) in sorted(hash_checks.items()):
        if not expected:
            blockers.append(f"{label}_hash_unbound")
        elif expected != actual:
            blockers.append(f"{label}_hash_mismatch")

    requested = [str(name) for name in candidate_requested]
    if len(requested) != 1:
        blockers.append(f"exactly_one_candidate_required:{len(requested)}")
    unknown = sorted(set(requested) - {str(name) for name in registry_candidates})
    if unknown:
        blockers.append(f"candidate_not_in_round5_registry:{','.join(unknown)}")

    for path in referenced_paths:
        text = str(path)
        for marker in NON_RANKING_PREDECESSOR_MARKERS:
            if marker in text:
                blockers.append(f"non_ranking_predecessor_artifact:{marker}")
                break

    return sorted(set(blockers))


def gpu_environment(topology: str) -> dict[str, str]:
    """The devices this topology uses in total. NOT a per-server binding.

    Retained for plan/inventory records only. It must never be exported into a
    server's environment: it names EVERY device the topology touches, so a
    server launched under it can allocate on all of them. Use
    `server_environment()` for anything that actually starts a process.
    """
    profile = topology_profile(topology)
    devices = sorted({device for group in profile["device_groups"] for device in group})
    return {"CUDA_VISIBLE_DEVICES": ",".join(str(index) for index in devices)}


def server_environment(
    devices: Sequence[int],
    *,
    visibility_tokens: Sequence[str] | None = None,
) -> dict[str, str]:
    """The environment for ONE server: exactly its own physical device group.

    This is the confinement itself. Exporting a single CUDA_VISIBLE_DEVICES
    covering all four cards and then naming a device on the launch line does not
    confine anything -- every server still SEES all four and, as measured on
    2026-08-22, every server allocated on all four. Restricting the child's
    device namespace is what makes the declared topology the served topology.
    """
    group = [int(device) for device in devices]
    if not group:
        raise Round5GuardFailure("a server must be given at least one device")
    if len(set(group)) != len(group):
        raise Round5GuardFailure(f"repeated device in server group {group}")
    visible = ([str(token) for token in visibility_tokens]
               if visibility_tokens is not None
               else [str(index) for index in group])
    if len(visible) != len(group) or any(not token for token in visible):
        raise Round5GuardFailure(
            "device visibility tokens must name every server device exactly once")
    if len(set(visible)) != len(visible):
        raise Round5GuardFailure(f"repeated visibility token in {visible}")
    return {"CUDA_VISIBLE_DEVICES": ",".join(visible)}


def logical_device_names(devices: Sequence[int]) -> list[str]:
    """The device names to use INSIDE a confined namespace.

    CUDA renumbers from zero within CUDA_VISIBLE_DEVICES, so a server confined to
    physical GPU 2 must be told `CUDA0`, not `CUDA2` -- `CUDA2` does not exist in
    its namespace and the launch fails or silently falls back. One-card workers
    get CUDA0; two-card workers get CUDA0,CUDA1.
    """
    return [f"CUDA{position}" for position in range(len(list(devices)))]


def device_mapping(
    devices: Sequence[int],
    *,
    visibility_tokens: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Physical-to-logical mapping, recorded in evidence for one server."""
    group = [int(device) for device in devices]
    logical = logical_device_names(group)
    visible = ([str(token) for token in visibility_tokens]
               if visibility_tokens is not None
               else [str(index) for index in group])
    if len(visible) != len(group):
        raise Round5GuardFailure(
            "device visibility tokens do not match the physical device group")
    return {
        "physical_devices": group,
        "physical_device_uuids": (visible if visibility_tokens is not None else None),
        "logical_devices": logical,
        "cuda_visible_devices": ",".join(visible),
        "physical_to_logical": {str(phys): logical[position]
                                for position, phys in enumerate(group)},
    }


# Cache-lifecycle flags, applied UNIFORMLY to every server for every candidate
# in both Stage A and Stage B. `--cache-ram 0` disables the prompt cache,
# `--cache-reuse 0` disables KV-shift reuse, `--no-cache-idle-slots` stops idle
# slots being written back into it. `--slot-save-path` is required by this
# server before POST /slots/:id?action=erase is accepted at all.
CACHE_ISOLATION_ARGV = ("--cache-ram", "0", "--cache-reuse", "0",
                        "--no-cache-idle-slots")


def server_argv(
    *, llama_server: str, model: str, alias: str, port: int,
    devices: Sequence[int], topology: str, slot_save_path: str | None = None,
) -> list[str]:
    """The exact launch line for one server under a declared topology.

    ``--alias`` is load-bearing rather than cosmetic: without it llama.cpp
    reports the full GGUF path as the response model, the substrate-identity
    check compares that against the bound model id, and every root is correctly
    rejected as a mismatch.
    """
    profile = topology_profile(topology)
    group = [int(device) for device in devices]
    if len(group) != profile["gpus_per_worker"]:
        raise Round5GuardFailure(
            f"{topology} serves {profile['gpus_per_worker']} GPU(s) per server, "
            f"got {len(group)}")
    argv = [
        str(llama_server), "--model", str(model), "--alias", str(alias),
        "-c", str(CONTEXT_TOKENS),
        "-ctk", KV_CACHE_TYPE_K, "-ctv", KV_CACHE_TYPE_V,
        "-ngl", str(GPU_LAYERS), "--parallel", str(SLOTS_PER_SERVER),
        "--host", "127.0.0.1", "--port", str(int(port)),
        # LOGICAL names: the server runs confined to its own group by
        # `server_environment()`, and CUDA renumbers from zero inside that
        # namespace. Naming physical indices here was correct only while every
        # server could see every card, which is the defect this replaces.
        "--device", ",".join(logical_device_names(group)),
        "--split-mode", profile["split_mode"],
        "--no-webui",
        *CACHE_ISOLATION_ARGV,
    ]
    if slot_save_path:
        # Without this the server refuses the slot action outright:
        # "This server does not support slots action."
        argv += ["--slot-save-path", str(slot_save_path)]
    if profile["tensor_split"]:
        argv += ["--tensor-split", str(profile["tensor_split"])]
    return argv


# --------------------------------------------------------------------------
# Verdicts
# --------------------------------------------------------------------------

VERDICTS = {
    "selected": "ROUND5_TITAN_COMPACT_EXAM_PROVISIONAL_SUBSTRATE_SELECTED",
    "no_eligible": "NO_COMPACT_EXAM_ELIGIBLE_MODEL",
    "blocked": "ROUND5_TITAN_INSTRUMENT_OR_INFRASTRUCTURE_BLOCKED_NONVERDICT",
    "contaminated": TIMING_CONTAMINATED_NONVERDICT,
    "not_run": "ROUND5_TITAN_COMPACT_EXAM_NOT_EXECUTED",
}
#: The same five outcomes, named for the round that produced them. The Round-5
#: spellings above are unchanged, because they appear in completed artifacts.
ROUND7_VERDICTS = {
    "selected": "ROUND7_GROUPED_EXAM_PROVISIONAL_SUBSTRATE_SELECTED",
    "no_eligible": "NO_COMPACT_EXAM_ELIGIBLE_MODEL",
    "blocked": "ROUND7_GROUPED_INSTRUMENT_OR_INFRASTRUCTURE_BLOCKED_NONVERDICT",
    "contaminated": TIMING_CONTAMINATED_NONVERDICT,
    "not_run": "ROUND7_GROUPED_EXAM_NOT_EXECUTED",
}


def verdicts_for(panel_version: str | None) -> dict[str, str]:
    return (ROUND7_VERDICTS if panel_version in ROUND7_PANEL_VERSIONS
            else VERDICTS)
NOT_REACHED = "not reached"

TERMINAL_COUNTERS = {
    "scientific_roots_opened": 0,
    "intervention_arms_run": 0,
    "compact_exam_roots_opened": 0,
    "model_requests": 0,
    "model_selected": None,
    "r5_2a_signed": False,
    "execution_authorization_set": False,
}


def median(values: Sequence[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


# --------------------------------------------------------------------------
# The runner's view of the exam
# --------------------------------------------------------------------------

EXECUTION_ROOT_FIELDS = ("root_id", "task_template_id", "task_sha256")
HIDDEN_FIELDS = (
    "ideal_solver_success", "selection_key", "hidden_outcome", "expected_answer",
    "hidden_table_sha256", "root_variant_index", "available_root_count",
)


def execution_root_list(manifest: Mapping[str, Any], *,
                        pool: str = EXAM_POOL) -> list[dict[str, Any]]:
    """The ONLY view of the exam that model-serving and eligibility code sees.

    The manifest records each template's frozen ideal-solver outcome because the
    16/14 stratification has to be auditable. The runner must never see it: a
    runner that can read which templates an ideal solver clears could, however
    innocently, order or condition on difficulty, and the exam would stop being
    the same 30 roots in the same order for everybody. Projecting the manifest
    through this function is what makes that structural rather than a promise.
    """
    # `pool` is a parameter so a LATER experiment with its own pool name reaches
    # the same projection instead of writing its own. The DeepSeek follow-up
    # publishes `round5_deepseek_followup`; reading its roots directly would
    # have bypassed the hidden-field strip below, which is the one thing this
    # function exists for. The default is unchanged, so every existing caller
    # behaves exactly as before.
    pool_entry = (manifest.get("pools") or {}).get(str(pool)) or {}
    roots = list(pool_entry.get("roots") or [])
    if len(roots) != EXAM_ROOTS:
        raise Round5GuardFailure(
            f"the execution root list is exactly {EXAM_ROOTS} roots, got {len(roots)}")
    projected: list[dict[str, Any]] = []
    for row in roots:
        projected.append({field: row.get(field) for field in EXECUTION_ROOT_FIELDS})
    if any(field in entry for entry in projected for field in HIDDEN_FIELDS
           if field not in EXECUTION_ROOT_FIELDS):
        raise Round5GuardFailure("the execution root list leaked a hidden field")
    return projected


def ordered_root_ids(manifest: Mapping[str, Any], *,
                     pool: str = EXAM_POOL) -> list[str]:
    return [str(row["root_id"])
            for row in execution_root_list(manifest, pool=pool)]


# --------------------------------------------------------------------------
# One schema contract, shared by the runner, the selector, the manager and the
# renderer
# --------------------------------------------------------------------------
#
# Four components read and write the same records. When each carried its own
# idea of the shape, a field renamed in one place became silently absent
# everywhere else and the reader that needed it printed a zero. The contract is
# therefore declared once, digested, and echoed by every component; readiness
# refuses to proceed when the digests disagree.

SCHEMA_CONTRACT_VERSION = 1
SCHEMA_CONTRACT: dict[str, tuple[str, ...]] = {
    STAGE_A_ARTIFACT_KIND: (
        "artifact_kind", "candidate", "topology", "checks",
        "free_vram_mib_at_peak", "stage_a", "runtime", "licence_policy_sha256",
        "model_requests", "compact_exam_roots_opened", "provenance",
    ),
    STAGE_B_ARTIFACT_KIND: (
        "artifact_kind", "candidate", "topology", "mode", "pool_consumed",
        "exam_manifest", "generation_record", "candidate_registry",
        "licence_policy_sha256", "runtime", "adjudicator", "thresholds",
        "schedule", "roots", "summary", "device_intervals", "canary",
        "scientific_roots_opened", "intervention_arms_run",
        "compact_exam_roots_opened", "selection",
    ),
    SELECTION_ARTIFACT_KIND: (
        "artifact_kind", "common_provenance", "candidates", "ranking",
        "selection", "substrate_qualification_cascade", "licence_policy_sha256",
        "scientific_roots_opened", "intervention_arms_run",
    ),
    EVIDENCE_MANIFEST_KIND: (
        "artifact_kind", "run_dir", "file_count", "files",
        "evidence_manifest_sha256",
    ),
}
SCHEMA_CONTRACT_REQUIRED_SUMMARY_FIELDS = (
    "n_roots", "adjudicated_successes", "settled_roots", "valid_submissions",
    "total_tool_calls", "malformed_tool_calls", "rail_bound_roots",
    "censored_roots", "median_trajectory_depth", "peak_vram_mib",
    "total_gpu_hours", "wall_seconds",
)

# Fields that arrived with the Round-7 deterministic budget. They are NOT in the
# required tuple and NOT in the contract digest, and that is deliberate: every
# archived Round-4/5/6 artifact pins schema_contract_digest, and
# validate_round5_titan_evidence refuses on a mismatch. Making the new field
# unconditionally required would retroactively invalidate frozen evidence for a
# field that run never produced -- a change to the past, not to the contract.
#
# Instead the fields are enforced as a PAIR, in both directions: an artifact that
# declares a root budget must also report what the budget cost, and an artifact
# that reports budget exhaustion must say under which budget. A run either
# predates the budget entirely (neither key; the wall rail remains its source,
# exactly as archived) or it carries both. A half-populated summary -- the shape
# that would let a Round-7 row be scored on the wall rail by omission -- is the
# only new refusal.
SCHEMA_CONTRACT_PAIRED_SUMMARY_FIELDS = ("root_budget", "budget_exhausted_roots")


def schema_contract_digest() -> str:
    """A stable digest of the shared record shape."""
    payload = [f"v{SCHEMA_CONTRACT_VERSION}"]
    for kind in sorted(SCHEMA_CONTRACT):
        payload.append(kind + ":" + ",".join(sorted(SCHEMA_CONTRACT[kind])))
    payload.append("summary:" + ",".join(sorted(SCHEMA_CONTRACT_REQUIRED_SUMMARY_FIELDS)))
    return _sha256_hex(*payload)


def schema_blockers(artifact: Mapping[str, Any] | None, *, kind: str) -> list[str]:
    """Refuse an artifact that is missing a field the contract requires."""
    if not isinstance(artifact, Mapping):
        return [f"{kind}_absent_or_unreadable"]
    required = SCHEMA_CONTRACT.get(kind)
    if required is None:
        return [f"unknown_artifact_kind:{kind}"]
    if artifact.get("artifact_kind") != kind:
        return [f"artifact_kind_{artifact.get('artifact_kind')}_not_{kind}"]
    blockers = [f"{kind}_missing_field:{field}" for field in required
                if field not in artifact]
    if kind == STAGE_B_ARTIFACT_KIND:
        summary = artifact.get("summary") or {}
        blockers.extend(
            f"{kind}_summary_missing_field:{field}"
            for field in SCHEMA_CONTRACT_REQUIRED_SUMMARY_FIELDS
            if field not in summary)
        present = [f for f in SCHEMA_CONTRACT_PAIRED_SUMMARY_FIELDS
                   if f in summary]
        if present and len(present) != len(SCHEMA_CONTRACT_PAIRED_SUMMARY_FIELDS):
            blockers.extend(
                f"{kind}_summary_missing_paired_field:{field}"
                for field in SCHEMA_CONTRACT_PAIRED_SUMMARY_FIELDS
                if field not in summary)
    return sorted(set(blockers))


# --------------------------------------------------------------------------
# Stale-default detection
# --------------------------------------------------------------------------
#
# The failure this guards against is not a typo. It is a Round-4 value surviving
# into a Round-5 profile and producing a confidently labelled artifact that
# describes the wrong machine: two workers on a four-card host, an L40S model
# root, a common Q4_K_M assertion that rejects Gemma's official QAT artifact, or
# a hard-coded qwen3-8b that makes the incumbent the answer by construction.

# Path patterns that mean a Round-4 L40S artifact has been referenced by
# mistake. These are ROUND markers, not hardware markers: the Round-4 L40S run
# was interrupted and its paths must never be read by a later round. A
# legitimate L40 registry is therefore matched on the ROUND-4 patterns only --
# the bare `l40` pattern applies while the declared hardware is not L40, where
# any mention of an L40 path is by definition stale.
STALE_ROUND4_PATTERNS = (
    ("round4-l40", "stale_round4_l40_path"),
    ("model_selection_round4_l40", "stale_round4_l40_pool"),
    ("round4_l40", "stale_round4_l40_path"),
)
# The L40 side is deliberately NARROW, and the asymmetry is the point.
#
# For the Titan round, any `l40` in a path is stale, because the only L40
# material that existed was the interrupted Round-4 run. For the L40 round the
# same rule cannot be inverted onto `titan`: the frozen INPUTS this exam shares
# with the Titan round -- the licence policy, the exam prompt, the task pool,
# the manifest -- are named `*_round5_titan_*` and are shared BY DESIGN. They
# are what makes this the same exam; flagging them would push an operator to
# fork them, which is precisely the corruption the guard exists to prevent.
#
# What must never be read on the L40 side is a Titan RESULT, so the pattern
# targets the Titan evidence tree and nothing else.
STALE_FOREIGN_HARDWARE_PATTERNS = {
    HARDWARE_TITAN: (("l40", "stale_l40s_default"), ("L40", "stale_l40s_default")),
    HARDWARE_L40: (("evidence/round5-titan", "titan_evidence_referenced_by_an_l40_run"),
                   ("evidence/round5_titan", "titan_evidence_referenced_by_an_l40_run")),
    HARDWARE_BLACKWELL: (
        ("evidence/round5-titan", "titan_evidence_referenced_by_a_blackwell_run"),
        ("evidence/round5_titan", "titan_evidence_referenced_by_a_blackwell_run"),
        ("evidence/round4-l40", "l40_evidence_referenced_by_a_blackwell_run"),
        ("evidence/round4_l40", "l40_evidence_referenced_by_a_blackwell_run"),
    ),
}
#: Retained under its original name: existing callers and tests import it, and
#: it is still exactly right for the default (Titan) hardware.
STALE_DEFAULT_PATTERNS = (
    *STALE_FOREIGN_HARDWARE_PATTERNS[HARDWARE_TITAN],
    *STALE_ROUND4_PATTERNS[:2],
)


def stale_default_blockers(
    *,
    registry: Mapping[str, Any] | None,
    referenced_paths: Sequence[str] = (),
) -> list[str]:
    blockers: list[str] = []
    declared_hardware = hardware_profile_of(registry)
    patterns = (
        *STALE_ROUND4_PATTERNS,
        *STALE_FOREIGN_HARDWARE_PATTERNS.get(
            declared_hardware, STALE_FOREIGN_HARDWARE_PATTERNS[HARDWARE_TITAN]),
    )
    for path in referenced_paths:
        text = str(path)
        for needle, reason in patterns:
            if needle in text:
                blockers.append(f"{reason}:{text}")
                break
    if not isinstance(registry, Mapping):
        return sorted(set(blockers + ["registry_absent_or_unreadable"]))

    runtime = registry.get("runtime") or {}
    if "quantization" in runtime:
        blockers.append("stale_common_q4_k_m_assertion_in_runtime")
    if "workers" in runtime:
        blockers.append("stale_flat_worker_count_in_runtime")
    # The stale-copy guard, in both directions. A registry declares the hardware
    # it is for; carrying the other round's GPU string is how a copied file
    # silently measures the wrong machine.
    hardware = hardware_profile_of(registry)
    if hardware not in HARDWARE_TOPOLOGY:
        blockers.append(f"unknown_hardware_profile:{hardware}")
        hardware = HARDWARE_TITAN
    foreign_fragment, foreign_blocker = HARDWARE_FOREIGN_GPU_FRAGMENT[hardware]
    required_fragment = HARDWARE_GPU_FRAGMENT[hardware]
    # Two places a GPU string can hide. `runtime.gpu` is where the interrupted
    # L40S round left one; `hardware.gpu_name_fragment` is the field this
    # registry family actually populates, and is what a file copied from the
    # other round carries. Both are checked, in both directions.
    declared_hardware = registry.get("hardware") or {}
    for field, source in (
            (str(runtime.get("gpu") or ""), "runtime_gpu"),
            (str(declared_hardware.get("gpu_name_fragment") or ""),
             "hardware_gpu_name_fragment")):
        upper = field.upper()
        if foreign_fragment in upper:
            blockers.append(foreign_blocker if source == "runtime_gpu"
                            else f"{foreign_blocker}:{source}")
        if upper and required_fragment not in upper:
            blockers.append(
                f"{source}_does_not_match_hardware_profile:{hardware}")
    # And the declared host must be the host the spec describes. A registry
    # that declares L40 hardware but carries the Titan card count would pass
    # every string check and still schedule four servers onto two cards.
    spec = HOST_SPECS[hardware]
    declared_gpus = declared_hardware.get("gpus")
    if declared_gpus is not None and int(declared_gpus) != int(spec["gpu_count"]):
        blockers.append(
            f"hardware_gpus_{declared_gpus}_not_{spec['gpu_count']}_for_{hardware}")
    declared_cc = str(declared_hardware.get("compute_capability") or "")
    if declared_cc and declared_cc != str(spec["compute_capability"]):
        blockers.append(
            f"hardware_compute_capability_{declared_cc}_not_"
            f"{spec['compute_capability']}_for_{hardware}")
    declared_mem = declared_hardware.get("memory_total_mib_per_gpu")
    if declared_mem is not None and (
            abs(int(declared_mem) - int(spec["memory_total_mib"]))
            > int(spec["memory_tolerance_mib"])):
        blockers.append(
            f"hardware_memory_{declared_mem}_mib_not_"
            f"{spec['memory_total_mib']}_for_{hardware}")

    selection = registry.get("selection") or {}
    if "screening_priority" in selection:
        blockers.append("registry_still_declares_the_retired_screening_priority")
    if "selection_overlap_control" in selection or "selection_overlap_control" in registry:
        # Round 5 has no overlap control. Carrying one forward would silently
        # reinstate an incumbent tie-break the frozen ranking rule does not have.
        blockers.append("round5_ranking_has_no_overlap_control")

    profiles = registry.get("topology_profiles") or {}
    for name in HARDWARE_REQUIRED_PROFILES[hardware]:
        if name not in profiles:
            blockers.append(f"registry_does_not_declare_topology_profile:{name}")
            continue
        frozen = TOPOLOGY_PROFILES[name]
        declared = profiles[name] or {}
        for field in ("servers", "workers", "gpus_per_worker", "split_mode"):
            if str(declared.get(field)) != str(frozen[field]):
                blockers.append(
                    f"{name}_{field}_{declared.get(field)}_not_{frozen[field]}")
        declared_groups = [tuple(int(d) for d in group)
                           for group in (declared.get("device_groups") or [])]
        if declared_groups != [tuple(group) for group in frozen["device_groups"]]:
            blockers.append(f"{name}_device_groups_are_not_the_frozen_groups")
        if tuple(declared.get("root_block_sizes") or ()) != tuple(frozen["root_block_sizes"]):
            blockers.append(f"{name}_root_block_sizes_are_not_the_frozen_blocks")

    candidates = registry.get("candidates") or {}
    try:
        version = panel_version_of(registry)
    except Round5GuardFailure:
        version = PANEL_VERSION
    expected_quantization = {
        ROUND7_PANEL_VERSION: ROUND7_QUANTIZATION,
        ROUND7_ADA_PANEL_VERSION: ROUND7_ADA_QUANTIZATION,
        ROUND7_ADA_V3_PANEL_VERSION: ROUND7_ADA_V3_QUANTIZATION,
        V3_TITAN_PANEL_VERSION: V3_TITAN_QUANTIZATION,
    }.get(version, PRIMARY_QUANTIZATION)
    for name, spec in candidates.items():
        if not isinstance(spec, Mapping):
            blockers.append(f"{name}:candidate_record_is_not_an_object")
            continue
        if not spec.get("topology"):
            blockers.append(f"{name}:candidate_does_not_name_a_topology_profile")
        expected_topology = HARDWARE_TOPOLOGY[hardware].get(str(name))
        if expected_topology is None and hardware == HARDWARE_BLACKWELL:
            expected_topology = BLACKWELL_SINGLE_2X
        if expected_topology is None and hardware == HARDWARE_ADA_LEASED:
            expected_topology = ADA_LEASED_2X
        if spec.get("topology") and str(spec["topology"]) != str(expected_topology or ""):
            blockers.append(
                f"{name}:topology_{spec['topology']}_not_"
                f"{expected_topology}")
        if not spec.get("expected_quantization"):
            blockers.append(f"{name}:expected_quantization_unbound")
        elif str(spec["expected_quantization"]) != expected_quantization.get(str(name), ""):
            blockers.append(
                f"{name}:expected_quantization_{spec['expected_quantization']}_not_"
                f"{expected_quantization.get(str(name))}")

    return sorted(set(blockers))


def candidate_order_blockers(registry: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(registry, Mapping):
        return ["registry_absent_or_unreadable"]
    blockers: list[str] = []
    try:
        expected_order = list(panel_order_of(registry))
        expected_version = panel_version_of(registry)
    except Round5GuardFailure as exc:
        return [str(exc)]
    order = [str(name) for name in (registry.get("candidate_order") or [])]
    if order != expected_order:
        blockers.append(f"candidate_order_{order}_is_not_the_frozen_order")
    if [str(name) for name in (registry.get("candidates") or {})] != order:
        blockers.append("candidate_mapping_order_differs_from_candidate_order")
    # A registry that still declares an ACTIVATABLE reserve list disagrees with
    # the closed panel, and the disagreement matters: the funnel would be
    # reading a candidate set the frozen rules do not contain. Declaring the
    # three future candidates is fine and expected -- under `future_candidates`,
    # where nothing operative reads them.
    reserves = registry.get("reserves") or {}
    reserve_order = [str(name) for name in (reserves.get("order") or [])]
    if reserve_order:
        blockers.append(
            f"registry_declares_an_activatable_reserve_order_{reserve_order}_"
            "on_a_closed_panel")
    if reserves.get("entries"):
        blockers.append("registry_declares_activatable_reserve_entries_"
                        "on_a_closed_panel")
    if not registry.get("panel_is_closed"):
        blockers.append("registry_does_not_declare_panel_is_closed")
    if str(registry.get("panel_version") or "") != expected_version:
        blockers.append(f"registry_panel_version_{registry.get('panel_version')}"
                        f"_is_not_{expected_version}")
    maximum = registry.get("maximum_stage_b_candidates")
    if maximum is None:
        maximum = reserves.get("maximum_stage_b_candidates")
    if int(maximum or 0) != len(expected_order):
        blockers.append(f"maximum_stage_b_candidates_not_{len(expected_order)}")
    return sorted(set(blockers))


def gate_and_score_blockers(registry: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(registry, Mapping):
        return ["registry_absent_or_unreadable"]
    blockers: list[str] = []
    gates = registry.get("hard_gates") or {}
    round7_time_policy = panel_version_of(registry) in ROUND7_PANEL_VERSIONS
    expected_gates = {
        "maximum_tool_call_malformation_rate": MAX_TOOL_MALFORMATION,
        "minimum_observed_tool_calls": MIN_OBSERVED_TOOL_CALLS,
        "minimum_settled_completion_rate": MIN_SETTLED_COMPLETION,
        "minimum_task_success_rate": MIN_TASK_SUCCESS,
        "maximum_task_success_rate": MAX_TASK_SUCCESS,
        "minimum_median_trajectory_depth": MIN_MEDIAN_TRAJECTORY_DEPTH,
    }
    expected_gates[
        "maximum_provider_error_roots" if round7_time_policy
        else "maximum_rail_bound_or_censored_roots"
    ] = MAX_RAIL_BOUND_OR_CENSORED_ROOTS
    for field, expected in sorted(expected_gates.items()):
        try:
            if float(gates.get(field)) != float(expected):
                blockers.append(f"gate_{field}_{gates.get(field)}_not_{expected}")
        except (TypeError, ValueError):
            blockers.append(f"gate_{field}_unreadable:{gates.get(field)}")
    if gates.get("stage_a") != "pass":
        blockers.append("gate_stage_a_not_declared_pass")
    if gates.get("trajectory_depth_population") != "all_attempted_roots":
        blockers.append("gate_trajectory_depth_population_is_not_all_attempted_roots")
    if round7_time_policy:
        for field in ("budget_exhaustion_is_not_a_gate",
                      "safety_stop_is_not_a_gate", "wall_time_is_not_a_gate"):
            if gates.get(field) is not True:
                blockers.append(f"gate_{field}_not_true")
        outcomes = registry.get("component_outcomes") or {}
        if outcomes.get("R") != "one_minus_provider_error_root_rate":
            blockers.append("component_R_is_not_provider_error_only")
        if outcomes.get("C") != (
                "settled_or_deterministically_stopped_root_rate"):
            blockers.append("component_C_does_not_fold_deterministic_stops")

    score = registry.get("candidacy_score") or {}
    if str(score.get("formula")) != SCORE_FORMULA:
        blockers.append(f"score_formula_{score.get('formula')}_not_the_frozen_formula")
    weights = score.get("weights") or {}
    for name, weight in sorted(SCORE_WEIGHTS.items()):
        try:
            if float(weights.get(name)) != weight:
                blockers.append(f"score_weight_{name}_{weights.get(name)}_not_{weight}")
        except (TypeError, ValueError):
            blockers.append(f"score_weight_{name}_unreadable")

    ranking = ((registry.get("ranking") or {}).get("rule") or {})
    expected_ranking = {
        1: "retain only hard-gate-eligible candidates",
        2: "rank by adjudicated_successes / total_GPU_hours",
        3: "break a tie by higher candidacy score",
        4: "then lower peak VRAM",
        5: "then the frozen candidate order",
    }
    for step, text in sorted(expected_ranking.items()):
        if str(ranking.get(step) or "").strip() != text:
            blockers.append(f"ranking_step_{step}_differs_from_the_frozen_rule")

    exam = registry.get("development_exam") or {}
    for field, expected in (("templates", EXAM_TEMPLATES), ("roots", EXAM_ROOTS),
                            ("roots_per_template", EXAM_ROOTS_PER_TEMPLATE),
                            ("ideal_success_templates", IDEAL_SUCCESS_TEMPLATES),
                            ("ideal_nonsuccess_templates", IDEAL_NONSUCCESS_TEMPLATES)):
        try:
            if int(exam.get(field)) != expected:
                blockers.append(f"development_exam_{field}_{exam.get(field)}_not_{expected}")
        except (TypeError, ValueError):
            blockers.append(f"development_exam_{field}_unreadable")
    return sorted(set(blockers))


AUTHORIZATION_FLAG_NAMES = (
    "ROUND5_TITAN_EXECUTION_AUTHORIZATION",
    "ROUND5_TITAN_ALLOW_MODEL_CALLS",
    "R5_TITAN_EXECUTE",
    "EXECUTION_AUTHORIZATION_SET",
)


def authorization_blockers(environment: Mapping[str, str]) -> list[str]:
    """Preflight must be incapable of launching a model, not merely disinclined.

    A preflight that runs with an execution flag already set is one argument
    away from starting a server, and the whole value of a zero-model-call gate is
    that it cannot.
    """
    return sorted(
        f"authorization_flag_set_during_preflight:{name}"
        for name in AUTHORIZATION_FLAG_NAMES
        if str(environment.get(name, "")).strip().lower() not in {"", "0", "false", "no"}
    )


# --------------------------------------------------------------------------
# Stage exit codes -- one meaning per code, read by the manager's state machine
# --------------------------------------------------------------------------
#
# The manager previously recorded every completed subprocess as a terminal
# verdict regardless of its exit code. That made a `TIMING_CONTAMINATED_NONVERDICT`
# indistinguishable from a candidate failure: Stage-A contamination could
# activate a reserve, and Stage-B contamination let the funnel move to the next
# candidate with no valid timing artifact. The exit code is the only signal the
# manager has, so it has to mean exactly one thing.

EXIT_PASS = 0            # the stage completed and produced a verdict
EXIT_NQ = 2              # a genuine candidate failure or refusal; a real verdict
EXIT_NONVERDICT = 3      # no verdict: wait and retry, do not change membership
EXIT_BLOCKER = 4         # a protocol or binding blocker: stop the funnel
# The selector's "I computed the table and am deliberately not acting on it".
# It needs a code of its own: while it shared 3 with the timing nonverdict, the
# manager read a withheld selection as a contaminated host and waited ten
# minutes, three times, for a machine that was never contaminated.
EXIT_SELECTION_WITHHELD = 5
EXIT_CANDIDATE_TIMEOUT = 6  # elapsed-time nonverdict; continue the panel
EXIT_CODE_MEANINGS = {
    EXIT_PASS: "pass",
    EXIT_NQ: "candidate_nq_or_refusal",
    EXIT_NONVERDICT: "nonverdict_wait_and_retry",
    EXIT_BLOCKER: "protocol_or_binding_blocker_stop",
    EXIT_SELECTION_WITHHELD: "selection_withheld",
    EXIT_CANDIDATE_TIMEOUT: "candidate_timeout_no_verdict",
}

DISPOSITION_TERMINAL = "terminal"
DISPOSITION_INTERRUPTED = "interrupted"
DISPOSITION_NONVERDICT = "nonverdict"
DISPOSITION_BLOCKED = "blocked"


def classify_exit_code(returncode: int | None, *, timed_out: bool = False
                       ) -> dict[str, Any]:
    """What the manager is permitted to conclude from one stage's exit code.

    An unrecognised code fails CLOSED. A funnel that treats "I do not know what
    that meant" as success is worse than one that stops, because it produces a
    confidently labelled artifact describing a stage nobody understood.
    """
    if timed_out:
        return {
            "disposition": DISPOSITION_INTERRUPTED,
            "meaning": "timed_out",
            "terminal": False, "retry": True, "stop_funnel": False,
            "counts_as_candidate_verdict": False,
        }
    code = -1 if returncode is None else int(returncode)
    if code == EXIT_PASS:
        return {"disposition": DISPOSITION_TERMINAL, "meaning": "pass",
                "terminal": True, "retry": False, "stop_funnel": False,
                "counts_as_candidate_verdict": True}
    if code == EXIT_NQ:
        return {"disposition": DISPOSITION_TERMINAL,
                "meaning": "candidate_nq_or_refusal",
                "terminal": True, "retry": False, "stop_funnel": False,
                "counts_as_candidate_verdict": True}
    if code == EXIT_NONVERDICT:
        # NOT a candidate verdict. The host was contaminated, so nothing was
        # measured about this candidate at all. Waiting is the whole rule.
        return {"disposition": DISPOSITION_NONVERDICT,
                "meaning": "nonverdict_wait_and_retry",
                "terminal": False, "retry": True, "stop_funnel": False,
                "counts_as_candidate_verdict": False,
                "verdict": TIMING_CONTAMINATED_NONVERDICT}
    if code == EXIT_CANDIDATE_TIMEOUT:
        return {
            "disposition": DISPOSITION_INTERRUPTED,
            "meaning": "candidate_timeout_no_verdict",
            "terminal": False, "retry": False, "stop_funnel": False,
            "counts_as_candidate_verdict": False,
            "verdict": TERMINAL_STAGE_A_TIMEOUT,
        }
    if code == EXIT_SELECTION_WITHHELD:
        # A real, final result: the ranking exists and was deliberately not
        # acted on. Nothing is retried and the funnel does not stop.
        return {"disposition": DISPOSITION_TERMINAL,
                "meaning": "selection_withheld",
                "terminal": True, "retry": False, "stop_funnel": False,
                "counts_as_candidate_verdict": False}
    if code == EXIT_BLOCKER:
        return {"disposition": DISPOSITION_BLOCKED,
                "meaning": "protocol_or_binding_blocker_stop",
                "terminal": True, "retry": False, "stop_funnel": True,
                "counts_as_candidate_verdict": False}
    return {"disposition": DISPOSITION_BLOCKED,
            "meaning": f"unrecognised_exit_code:{code}",
            "terminal": True, "retry": False, "stop_funnel": True,
            "counts_as_candidate_verdict": False}


# --------------------------------------------------------------------------
# Reference canary sufficiency
# --------------------------------------------------------------------------

CANARY_MINIMUM_OBSERVATIONS = 2
CANARY_ARTIFACT_KIND = "round5_titan_canary_observation"
CANARY_DRIFT_ARTIFACT_KIND = "round5_titan_canary_drift"
CANARY_MODEL = "qwen3-8b"


def canary_sufficiency(drift: Mapping[str, Any] | None) -> dict[str, Any]:
    """Insufficient canary evidence WITHHOLDS a timing rank; it never permits one.

    The earlier logic withheld only when ``drift_warning`` was true, so a record
    saying ``observations: 0, drift_warning: false`` -- which is what a canary
    that never ran produces -- read as "no drift detected" and let a
    resource-normalized ranking proceed. Candidates run hours apart and
    sequentially, so an unmeasured machine is exactly the condition under which
    thermal or clock drift would be confounded with model identity. Absence of
    evidence is not evidence of stability.
    """
    if not isinstance(drift, Mapping):
        return {"sufficient": False, "observations": 0,
                "withhold_reason": "reference_canary_evidence_absent",
                "minimum_observations": CANARY_MINIMUM_OBSERVATIONS,
                "drift_warning": None}
    observations = int(drift.get("observations") or 0)
    if drift.get("drift_warning"):
        return {"sufficient": False, "observations": observations,
                "withhold_reason":
                    "reference_canary_drift_invalidates_the_timing_comparison",
                "minimum_observations": CANARY_MINIMUM_OBSERVATIONS,
                "drift_warning": True,
                "maximum_relative_deviation": drift.get("maximum_relative_deviation")}
    if observations < CANARY_MINIMUM_OBSERVATIONS:
        return {"sufficient": False, "observations": observations,
                "withhold_reason": "reference_canary_evidence_insufficient",
                "minimum_observations": CANARY_MINIMUM_OBSERVATIONS,
                "drift_warning": False,
                "note": ("fewer than two valid decode measurements exist, so "
                         "drift is UNDETERMINED rather than absent")}
    return {"sufficient": True, "observations": observations,
            "minimum_observations": CANARY_MINIMUM_OBSERVATIONS,
            "drift_warning": False,
            "maximum_relative_deviation": drift.get("maximum_relative_deviation")}


def valid_canary_observations(
    records: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Keep only observations that carry a real decode measurement.

    A planned-only placeholder has no decode rate. Counting one would let a
    funnel that never ran a canary report two observations and satisfy the
    sufficiency rule with nothing behind it.
    """
    kept: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        if record.get("artifact_kind") != CANARY_ARTIFACT_KIND:
            continue
        if record.get("planned_only") or record.get("fixture_only"):
            continue
        rate = record.get("decode_tokens_per_second")
        try:
            value = float(rate)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value) or value <= 0:
            continue
        kept.append(dict(record))
    return kept


# --------------------------------------------------------------------------
# Stage-A observation provenance
# --------------------------------------------------------------------------
#
# An observation record supplied from outside is only evidence if it is bound to
# the probe implementation that produced it and to the raw server output it
# summarises. Without that binding it is a hand-editable JSON file that decides
# whether a candidate is eligible.

STAGE_A_OBSERVATION_KIND = "round5_titan_stage_a_observations"
REQUIRED_OBSERVATION_BINDINGS = (
    "artifact_kind", "candidate", "topology", "acquisition_module_sha256",
    "acquired_at_utc", "host", "server_log_sha256", "llama_server_sha256",
    "runtime_commit", "checks", "free_vram_mib_at_peak", "occupancy_samples",
)


def observation_binding_blockers(
    observations: Mapping[str, Any] | None,
    *,
    candidate: str,
    expected_acquisition_sha256: str | None,
) -> list[str]:
    """Refuse an observation record that is not bound to a real acquisition."""
    if not isinstance(observations, Mapping):
        return ["stage_a_observations_absent_or_unreadable"]
    blockers: list[str] = []
    if observations.get("artifact_kind") != STAGE_A_OBSERVATION_KIND:
        blockers.append(
            f"stage_a_observations_wrong_kind:{observations.get('artifact_kind')}")
    for field in REQUIRED_OBSERVATION_BINDINGS:
        if field not in observations or observations.get(field) in (None, "", {}):
            blockers.append(f"stage_a_observations_missing_binding:{field}")
    if str(observations.get("candidate") or "") != str(candidate):
        blockers.append(
            f"stage_a_observations_describe_{observations.get('candidate')}"
            f"_not_{candidate}")
    recorded = observations.get("acquisition_module_sha256")
    if expected_acquisition_sha256 and recorded and recorded != expected_acquisition_sha256:
        blockers.append("stage_a_observations_acquisition_module_digest_mismatch")
    if observations.get("model_requests_issued") in (None, 0):
        # A live Stage A issues requests by construction. Zero of them means the
        # record summarises something other than a Stage-A acquisition.
        blockers.append("stage_a_observations_report_no_model_requests")
    return sorted(set(blockers))


# --------------------------------------------------------------------------
# Reserve artifact bindings
# --------------------------------------------------------------------------

# Retained so that a stored artifact or a caller written against the open panel
# still resolves the name. It is no longer emitted by anything.
RESERVE_BINDING_REQUIRED = "RESERVE_BINDING_REQUIRED"
CLOSED_PANEL_NO_RESERVES = "CLOSED_PANEL_NO_RESERVES"
RESERVE_BINDING_FIELDS = (
    "source_repo", "source_revision", "filename", "expected_sha256",
    "expected_quantization", "expected_quantization_source",
    "expected_architecture", "expected_block_count", "tokenizer_sha256",
    "chat_template_sha256", "target_tensor_identity",
)


def reserve_binding_blockers(
    registry: Mapping[str, Any] | None,
    *,
    licence_policy: Mapping[str, Any] | None = None,
    require_all: bool = True,
) -> dict[str, Any]:
    """No reserves exist, so nothing here can block an unattended launch.

    Under the open panel this function existed to stop a specific overnight
    failure: a reserve the funnel could ACTIVATE but not RUN, so a primary was
    marked NQ, its slot spent on a substitute that then failed for a reason
    unrelated to its capability, with nobody awake to notice. The closed panel
    removes the activation, which removes the failure -- and with it the
    reason to hold an unattended launch on three models the exam will never
    load.

    The function is kept, always returning no blockers, so that a caller still
    checking reserve readiness gets a documented "there are none" rather than
    an ImportError. `FUTURE_CANDIDATES` is deliberately NOT consulted: those
    three are documentation, and validating documentation is how a
    non-operative list quietly becomes operative again.
    """
    return {
        "reserves": {},
        "runnable_reserves": [],
        "explicitly_skipped_reserves": [],
        "future_candidates": list(future_candidate_names(registry)),
        "blockers": [],
        "verdict": CLOSED_PANEL_NO_RESERVES,
        "rule": ("the v2 panel is closed: no replacement model is activated, "
                 "so no reserve needs to be bound, downloaded or licensed "
                 "before an unattended launch"),
    }


# The author's conditional approval, encoded rather than paraphrased.
#
# The decision recorded on 2026-08-21 approves internal, non-redistributive
# academic evaluation of the seven primaries ONLY when the archived exact
# licence at the pinned revision verifies as the expected MIT or Apache-2.0
# licence with no conflicting GGUF terms. A mismatch is an NQ/licence blocker
# for that model. It is explicitly NOT permission to reinterpret a licence, so
# nothing below widens the accepted set, and an ABSENT archive is a blocker
# rather than a pass -- an unread licence and an acceptable one are the same
# shape only if you decline to look.
EXPECTED_LICENCE_FAMILIES = ("MIT", "Apache-2.0")
LICENCE_VERIFICATION_PENDING = "LICENCE_VERIFICATION_PENDING"
LICENCE_FAMILY_MISMATCH = "LICENCE_FAMILY_MISMATCH"
LICENCE_DECLARATION_DISAGREES_WITH_ARCHIVE = (
    "LICENCE_DECLARATION_DISAGREES_WITH_ARCHIVE")
# A candidate whose pinned revision ships under terms its declaration does not
# match is excluded on PROVENANCE, which is a frozen Stage-A trigger class. It
# is never resolved by amending this policy to accept what was found -- that
# would make the licence gate a description of the artifacts rather than a
# constraint on them.
PROVENANCE_INELIGIBLE = "PROVENANCE_INELIGIBLE"


def permitted_licence_families(
    policy: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Which licence families THIS round's policy admits.

    `EXPECTED_LICENCE_FAMILIES` is shared with Round 5 and Round 6, whose
    archived evidence must keep re-deriving byte-identically, so it is not
    edited when a later round admits a differently licensed candidate. The
    policy FILE is the policy: a round that widens the set declares it in
    `policy.expected_licence_families`, and that declaration is pinned by the
    digest its builder re-pins deliberately. Both completed policies declare
    exactly `[MIT, Apache-2.0]`, so reading the file rather than the constant
    changes nothing for them -- asserted by test.

    Widening is a PROSPECTIVE decision about which licences the study will
    accept, taken before any model request. It is never a response to terms
    found on an artifact: `PROVENANCE_INELIGIBLE` and `LICENCE_FAMILY_MISMATCH`
    stay exactly as strict, and a candidate whose archive disagrees with its
    declaration is still excluded rather than accommodated.
    """
    declared = (policy or {}).get("policy", {}).get("expected_licence_families")
    if declared is None:
        return EXPECTED_LICENCE_FAMILIES
    if isinstance(declared, str):
        values: Sequence[Any] = (declared,)
    elif isinstance(declared, (list, tuple)):
        values = declared
    else:
        return EXPECTED_LICENCE_FAMILIES
    # Malformed policy data must not manufacture a new licence family through
    # Python's string conversion (for example None -> "None" or 3 -> "3").
    # The documented fallback is the completed-round default, not a widened set.
    if not values or any(not isinstance(value, str) or not value.strip()
                         for value in values):
        return EXPECTED_LICENCE_FAMILIES
    families = tuple(value.strip() for value in values)
    return families or EXPECTED_LICENCE_FAMILIES


def licence_verification_blockers(
    candidate: str,
    *,
    archived_spdx: str | None,
    archived_sha256: str | None,
    pinned_revision: str | None,
    gguf_terms_conflict: bool | None,
    permitted_families: Sequence[str] | None = None,
) -> list[str]:
    """Does this candidate's ARCHIVED licence satisfy the author's condition?

    Four separate questions, because collapsing them loses which one failed:
    is there an archive at all, was it taken at the pinned revision, is its
    licence family one of the two the author approved, and does the GGUF
    repository add terms the base licence does not carry.

    `gguf_terms_conflict is None` means nobody checked, and that is a blocker.
    A GGUF republication can attach terms the base repository never had, which
    is exactly the case the author's "no conflicting GGUF terms" clause is
    about, and it is invisible if you only read the base licence.
    """
    families = tuple(permitted_families or EXPECTED_LICENCE_FAMILIES)
    blockers: list[str] = []
    if not str(archived_sha256 or "").strip():
        blockers.append(f"{candidate}:licence_not_archived")
    if not str(pinned_revision or "").strip():
        blockers.append(f"{candidate}:licence_revision_unpinned")
    spdx = str(archived_spdx or "").strip()
    if not spdx:
        blockers.append(f"{candidate}:{LICENCE_VERIFICATION_PENDING}")
    elif spdx not in families:
        # NQ, not a request for another look. Naming the observed licence keeps
        # the refusal auditable without inviting a reinterpretation of it.
        blockers.append(
            f"{candidate}:{LICENCE_FAMILY_MISMATCH}:{spdx}_is_not_one_of_"
            + "_or_".join(families))
    if gguf_terms_conflict is None:
        blockers.append(f"{candidate}:gguf_terms_not_checked")
    elif gguf_terms_conflict:
        # PROVENANCE-INELIGIBLE, not "approvable under different terms". The
        # pinned revision carries terms the declared licence does not, so what
        # the publisher declares and what the artifact actually ships under
        # disagree -- and the resolution is to exclude the candidate, never to
        # widen this policy to accommodate the terms that were found.
        blockers.append(
            f"{candidate}:{PROVENANCE_INELIGIBLE}:"
            "gguf_terms_conflict_with_base_licence")
    return blockers


def licence_decision_summary(
    policy: Mapping[str, Any] | None, *,
    expected_candidates: Sequence[str] = PRIMARY_ORDER,
    future_candidates: Sequence[str] = tuple(FUTURE_CANDIDATES),
) -> dict[str, Any]:
    """Count every outstanding licence obligation across the SEVEN primaries.

    The closed panel removed the reserves, so it removed their licence rows
    too: three models the exam will never load were three decisions the author
    was being asked to make for no reason.

    What replaces them is narrower and harder. The author's approval is
    CONDITIONAL, so a candidate is only clear when its policy status is
    approved AND its archived licence has been verified against
    the families declared by this policy. `pending_verification` therefore counts
    candidates whose author decision exists but whose evidence does not, which
    on an unbound tree is all of them.
    """
    entries = (policy or {}).get("candidates") or {}
    families = permitted_licence_families(policy)
    approved_statuses = set(APPROVED_LICENCE_STATUSES)
    pending: list[str] = []
    approved: list[str] = []
    pending_verification: list[str] = []
    for name in expected_candidates:
        entry = entries.get(name) or {}
        status = str(entry.get("status") or "unset")
        (approved if status in approved_statuses else pending).append(name)
        if status not in approved_statuses:
            continue
        verification = entry.get("licence_verification") or {}
        # Conditional approvals always owe evidence. Unconditional completed
        # rows that declare a verification block are checked too; otherwise a
        # malformed archive could pass the gate but disappear from this summary.
        if status != CONDITIONAL_LICENCE_STATUS and not verification:
            continue
        if licence_verification_blockers(
                name,
                archived_spdx=verification.get("archived_spdx"),
                archived_sha256=verification.get("archived_sha256"),
                pinned_revision=verification.get("pinned_revision"),
                gguf_terms_conflict=verification.get("gguf_terms_conflict"),
                permitted_families=families):
            pending_verification.append(name)
    return {
        "panel": list(expected_candidates),
        "panel_is_closed": PANEL_IS_CLOSED,
        "pending_decisions": pending,
        "pending_count": len(pending),
        "approved": approved,
        "approved_count": len(approved),
        "pending_primaries": pending,
        "pending_reserves": [],
        "licence_conditional_reserves": [],
        "expected_licence_families": list(families),
        "expected_licence_families_default": list(EXPECTED_LICENCE_FAMILIES),
        "pending_verification": pending_verification,
        "pending_verification_count": len(pending_verification),
        "rule": ("author approval is conditional on the archived exact licence "
                 "at the pinned revision verifying as "
                 + " or ".join(families)
                 + " with no conflicting GGUF terms; a mismatch is an "
                 "NQ/licence blocker for that model, not permission to "
                 "reinterpret the licence"),
        "future_candidates_not_counted": sorted(future_candidates),
    }
