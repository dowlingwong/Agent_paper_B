"""D.3 G1 real adapter: node specs, the pinned gemma4_31b manager, the seven arms and their constants.

ENGINEERING_ONLY. AI-assisted (compute worker, 27 Nov 2026). Tier E: it fixes keep/execute decisions through the
controllers it builds, so the unit needs an accepted independent review before any D.3 campaign cites it.

This is the adapter seam that ``r1/c3/d3/campaign_chunk.py`` reserves for itself::

    kwargs, ended_on = factory(spec, seed, campaign_dir, recorder)

``factory`` is :func:`make_campaign_factory` here (harness arms) or :func:`make_replicate_factory` (FIXR3/EGATE).
Both read one campaign manifest (schema ``r1_d3_campaign_manifest/v1``) that pins every value the D.3 pre-declaration
and the G1/G6 design name:

* the D.3 node set and the arm set (pre-declaration §14 ``d3_nodes``, ``d3a_arms``, ``d3b_arms``);
* ``W = 20``, ``llm_call_cap = 80`` and the trial budget (80), for every arm including A0;
* ``memory_mode = append_only_summary``;
* harness ``9bb41680…`` with ``verify_seed_base = 20000``, ``verify_runs = 2`` and ``verify_split_policy = vary``
  (R1-D3-VERIFY-SEED; task ``compute/20261127-16``);
* the G2 constants file (``d3_constants.json``), the noise summary, the D.3 pre-declaration and the P3 split file,
  each by path and sha256;
* the proposer: ``gemma4_31b`` at Q4_K_M under ``manager_proposal/v1``, temperature 0.2, thinking off, its GGUF
  sha256 and the llama-server base URL.

**What the adapter does not do.** It opens no label, evaluation or test partition; it starts no server, no GPU job and
no evidence run; it does not resume a campaign and refuses an existing campaign directory. The launcher starts the
pinned server and passes its base URL in the manifest.

**Arms.** A0, A0R, A1, A2 and LADDER are built here from the constants file. FIXR3 and EGATE go through
:func:`make_replicate_factory` (design revision 6c), never the harness factory. A3, A5 and A6 need a frozen learned
artefact that the arms-frozen record has not produced; the adapter refuses them with a named error rather than
substituting a prior. A frozen artefact enters through :class:`LearnedArm` in a later reviewed unit.

**Manager.** ``LangGraphManager`` resolves the llama.cpp host from ``LLAMACPP_BASE_URL``, so
:func:`apply_proposer_environment` sets it from the manifest before the first campaign and refuses a contradictory
value already in the environment. The campaign records the base URL and the GGUF sha256 in ``notes``.

**Memory (replicate arms only).** ``run_replicate_campaign`` owns the ledger and does not hand it to ``propose``;
the replicate unit therefore keeps one bounded line per completed step and gives the manager a
``MemoryContext`` built from those lines. The line format is the harness summary display (trial id, summary,
metric, decision). This is stated in the unit record and in the chunk notes; it is not presented as the harness
``TrialRecord`` memory.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from r1.c3 import arms_constants as AC
from r1.c3 import d3_analysis as D3
from r1.c3.accounting import table_ended_on
from r1.c3.arms import ConstantPrior, RulesPrior
from r1.c3.control import RuleController, SKIP_DISPLAY, c3_budgets
from r1.c3.d3_controllers import D3_RULE_LAYER, a0r_controller, ladder_controller, ladder_eta
from r1.c3.d3.snapshots import SnapshotRecorder, config_sha256, wrap
from r1.c3.features import NodeContext, apply_edit
from r1.c3.prior_model import TableArmPrior
from r1.harness import import_harness, harness_root

HARNESS = import_harness()

from autoresearch.control_plane.action_versions import (  # noqa: E402
    KEEP_RULE_DEFAULT, NEW_CAMPAIGN_VERIFY_SPLIT_POLICY, VERIFY_RESPONSE_MEAN, ActionVersions,
)
from autoresearch.control_plane.controller import ContinueController  # noqa: E402
from autoresearch.manager.langgraph_manager import LangGraphManager  # noqa: E402
from autoresearch.memory.similarity import RepeatedBadStats  # noqa: E402
from autoresearch.memory.summarizer import MemoryContext, MemoryMode  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402

SCHEMA = "r1_d3_campaign_manifest/v1"
HARNESS_PIN = "9bb416805175149eb87b71f28d77530572aa4bce"
VERIFY_SEED_BASE = 20000
VERIFY_RUNS = 2
VERIFY_SPLIT_POLICY = "vary"
W = 20
LLM_CAP = 80
TRIAL_BUDGET = 80
MEMORY_MODE = "append_only_summary"
D3_NODES = tuple(AC.D3_NODES)
D3A_ARMS = tuple(D3.ARMS_D3A)
D3B_ARMS = tuple(D3.ARMS_D3B_WITH_A6)
ALL_ARMS = D3A_ARMS + tuple(a for a in D3B_ARMS if a not in D3A_ARMS)
HARNESS_ARMS = ("A0", "A0R", "A1", "A2", "LADDER")
REPLICATE_ARMS = ("FIXR3", "EGATE")
LEARNED_ARMS = ("A3", "A5", "A6")
PROPOSAL_SCHEMA = "manager_proposal/v1"
PROPOSER_TEMPERATURE = 0.2
REPO = Path(__file__).resolve().parents[3]
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_BASE_URL = re.compile(r"https?://[^\s]+")
FORBIDDEN_SUFFIXES = (".jsonl", ".log", ".diff", ".patch", ".npz", ".npy", ".parquet")


class AdapterStop(RuntimeError):
    """A pre-declared refusal: the run is not the run the manifest authorises."""


# ---------------------------------------------------------------------------
# the manifest
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Pin:
    path: str
    sha256: str

    @classmethod
    def parse(cls, payload: Mapping[str, Any], what: str) -> "Pin":
        if not isinstance(payload, Mapping):
            raise AdapterStop(f"{what} must be {{path, sha256}}")
        path, digest = str(payload.get("path") or ""), str(payload.get("sha256") or "")
        if not path or not _HEX64.fullmatch(digest):
            raise AdapterStop(f"{what} needs a path and a 64-hex sha256")
        if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES:
            raise AdapterStop(f"{what}: refusing a data/log file {path!r} (this unit reads pins, not data)")
        return cls(path=path, sha256=digest)


@dataclass(frozen=True)
class Manifest:
    stage: str
    campaign_model: str
    campaign_model_source: Mapping[str, Any]
    proposer_model: str
    proposer_alias: str
    proposer_base_url: str
    proposer_model_sha256: str
    proposal_schema: str
    temperature: float
    thinking: bool
    harness_commit: str
    constants: Pin
    noise: Pin
    predeclaration: Pin
    split: Pin
    data_cache_root: str | None
    nodes: tuple[str, ...]
    arms: tuple[str, ...]
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def proposer_id(self) -> str:
        return f"llamacpp/{self.proposer_alias}"

    def chunk_manifest(self) -> dict[str, Any]:
        """The fields ``campaign_chunk.run_chunk`` requires of its locked manifest."""
        return {
            "campaign_model": self.campaign_model,
            "proposer_model": self.proposer_model,
            "campaign_model_source_sha256": _sha_json(dict(self.campaign_model_source)),
            "harness_commit": self.harness_commit,
            "constants_sha256": self.constants.sha256,
            "noise_sha256": self.noise.sha256,
            "predeclaration_sha256": self.predeclaration.sha256,
        }


def _sha_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise AdapterStop(message)


def load_manifest(source: str | Path | Mapping[str, Any], *, repo_root: Path | str | None = None,
                  check_files: bool = True) -> Manifest:
    """Read and validate one campaign manifest; a missing or contradictory field is a refusal.

    ``check_files`` (default) also hashes the four pinned files; a launcher keeps it on, a unit test can pin
    synthetic files.
    """
    raw = json.loads(Path(source).read_text()) if isinstance(source, (str, Path)) else dict(source)
    _require(raw.get("schema") == SCHEMA, f"manifest schema must be {SCHEMA!r}")
    stage = str(raw.get("stage") or "")
    _require(stage in ("a", "b"), "stage must be 'a' or 'b'")
    _require(int(raw.get("W", -1)) == W, f"D.3 binds W = {W}")
    _require(int(raw.get("llm_cap", -1)) == LLM_CAP, f"D.3 binds the LLM-call cap = {LLM_CAP}")
    _require(int(raw.get("trial_budget", -1)) == TRIAL_BUDGET, f"D.3 binds the trial budget = {TRIAL_BUDGET}")
    _require(str(raw.get("memory_mode")) == MEMORY_MODE, f"memory_mode must be {MEMORY_MODE!r}")
    _require(int(raw.get("verify_runs", -1)) == VERIFY_RUNS, f"verify_runs must be {VERIFY_RUNS} (R1-D3-VERIFY-SEED)")
    _require(int(raw.get("verify_seed_base", -1)) == VERIFY_SEED_BASE,
             f"verify_seed_base must be {VERIFY_SEED_BASE} (R1-D3-VERIFY-SEED)")
    _require(str(raw.get("verify_split_policy")) == VERIFY_SPLIT_POLICY, "verify_split_policy must be 'vary'")
    harness = str(raw.get("harness_commit") or "")
    _require(bool(_HEX40.fullmatch(harness)), "harness_commit must be a 40-hex commit")
    _require(harness == HARNESS_PIN, f"this unit is written for harness {HARNESS_PIN}; got {harness}")
    campaign_model = str(raw.get("campaign_model") or "").strip()
    _require(bool(campaign_model), "campaign_model is required (one GPU model per instance's arms)")

    proposer = raw.get("proposer")
    _require(isinstance(proposer, Mapping), "proposer must be an object")
    model = str(proposer.get("model") or "")
    alias = str(proposer.get("alias") or "")
    base_url = str(proposer.get("base_url") or "")
    model_sha = str(proposer.get("model_sha256") or "")
    schema = str(proposer.get("schema") or "")
    temperature = proposer.get("temperature")
    thinking = proposer.get("thinking")
    _require(model == "gemma4_31b", "the D.3 proposer is gemma4_31b (R1-D3-MIN)")
    _require(bool(alias), "proposer.alias is required")
    _require(bool(_BASE_URL.fullmatch(base_url)), "proposer.base_url must be an http(s) URL")
    _require(bool(_HEX64.fullmatch(model_sha)), "proposer.model_sha256 must be a 64-hex sha256")
    _require(schema == PROPOSAL_SCHEMA, f"proposal schema must be {PROPOSAL_SCHEMA!r}")
    _require(temperature == PROPOSER_TEMPERATURE, "proposer temperature must be 0.2 (D15/D26)")
    _require(thinking is False, "thinking must be off for D.3")

    nodes = tuple(str(n) for n in raw.get("nodes") or ())
    _require(nodes == D3_NODES, f"nodes must be exactly the seven D.3 nodes, in order: {D3_NODES}")
    arms = tuple(str(a) for a in raw.get("arms") or ())
    _require(bool(arms), "arms must be non-empty")
    unknown = sorted(set(arms) - set(ALL_ARMS))
    _require(not unknown, f"unknown arms {unknown}; declared arms are {ALL_ARMS}")
    if stage == "a":
        _require(set(arms) == set(D3A_ARMS), f"stage a runs exactly {D3A_ARMS}")
    else:
        _require(set(arms) == set(D3B_ARMS), f"stage b runs exactly {D3B_ARMS}")

    constants = Pin.parse(raw.get("constants"), "constants")
    noise = Pin.parse(raw.get("noise"), "noise")
    predecl = Pin.parse(raw.get("predeclaration"), "predeclaration")
    split = Pin.parse(raw.get("split"), "split")
    source = raw.get("campaign_model_source")
    _require(isinstance(source, Mapping) and bool(source.get("sha256")), "campaign_model_source needs its sha256")
    cache_root = raw.get("data_cache_root")
    if cache_root is not None:
        cache_root = str(cache_root)

    manifest = Manifest(
        stage=stage, campaign_model=campaign_model, campaign_model_source=dict(source),
        proposer_model=model, proposer_alias=alias, proposer_base_url=base_url,
        proposer_model_sha256=model_sha, proposal_schema=schema, temperature=float(temperature),
        thinking=bool(thinking), harness_commit=harness, constants=constants, noise=noise,
        predeclaration=predecl, split=split, data_cache_root=cache_root, nodes=nodes, arms=arms,
        raw=dict(raw),
    )
    if check_files:
        check_pinned_files(manifest, repo_root=repo_root)
    return manifest


def check_pinned_files(manifest: Manifest, *, repo_root: Path | str | None = None) -> dict[str, str]:
    """Hash the four pinned files and refuse a mismatch; returns path -> sha256."""
    root = Path(repo_root) if repo_root is not None else REPO
    out = {}
    for pin, what in ((manifest.constants, "constants"), (manifest.noise, "noise"),
                      (manifest.predeclaration, "predeclaration"), (manifest.split, "split")):
        path = Path(pin.path) if Path(pin.path).is_absolute() else root / pin.path
        _require(path.is_file(), f"{what} file not found: {path}")
        digest = _sha_file(path)
        _require(digest == pin.sha256, f"{what} sha256 mismatch: {digest} != {pin.sha256}")
        out[pin.path] = digest
    return out


def check_harness(manifest: Manifest, observed: Mapping[str, Any]) -> None:
    """A launcher's harness record must name the pinned commit and a clean checkout."""
    _require(str(observed.get("commit") or "") == manifest.harness_commit,
             f"harness checkout is {observed.get('commit')!r}, not the pinned {manifest.harness_commit}")
    _require(observed.get("dirty") is False, "harness checkout is dirty")


def apply_proposer_environment(manifest: Manifest) -> None:
    """Point ``LLAMACPP_BASE_URL`` at the manifest's server and refuse a contradictory existing value."""
    current = os.environ.get("LLAMACPP_BASE_URL")
    if current:
        normal = current.rstrip("/")
        wanted = manifest.proposer_base_url.rstrip("/")
        if normal.rstrip("/v1") != wanted.rstrip("/v1"):
            raise AdapterStop(f"LLAMACPP_BASE_URL is {current!r} but the manifest pins {manifest.proposer_base_url!r}")
    os.environ["LLAMACPP_BASE_URL"] = manifest.proposer_base_url


# ---------------------------------------------------------------------------
# the G2 constants and the node context
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Constants:
    vectors: Mapping[str, Mapping[str, tuple[float, ...]]]
    noise: Mapping[str, Mapping[str, float]]
    ladder: Mapping[str, Mapping[str, float]]


def load_constants(manifest: Manifest, *, repo_root: Path | str | None = None) -> Constants:
    """The G2 artifact: A1/A2 vectors, noise constants and LADDER c/eta per node, all cross-checked."""
    root = Path(repo_root) if repo_root is not None else REPO
    path = Path(manifest.constants.path) if Path(manifest.constants.path).is_absolute() \
        else root / manifest.constants.path
    data = path.read_bytes()
    _require(hashlib.sha256(data).hexdigest() == manifest.constants.sha256, "constants sha256 mismatch")
    try:
        obj = json.loads(data)
        raw = AC.vectors_of(obj, "D.3 constants")
    except Exception as exc:  # noqa: BLE001 - the constants module refuses with its own error
        raise AdapterStop(f"constants file refused: {exc}") from exc
    _require(set(obj.get("nodes") or {}) == set(manifest.nodes),
             f"constants nodes {sorted((obj.get('nodes') or {}))} are not the manifest's {sorted(manifest.nodes)}")

    noise_path = Path(manifest.noise.path) if Path(manifest.noise.path).is_absolute() \
        else root / manifest.noise.path
    noise_data = noise_path.read_bytes()
    _require(hashlib.sha256(noise_data).hexdigest() == manifest.noise.sha256, "noise sha256 mismatch")
    from r1.c3.dataset import noise_table
    table = noise_table(noise_path)
    noise = {}
    for node in manifest.nodes:
        _require(node in table, f"noise summary has no entry for {node}")
        entry = table[node]
        const = obj["nodes"][node]
        _require(float(const["sigma_node"]).hex() == float(entry["sigma_node"]).hex(),
                 f"{node}: constants sigma_node differs from the noise summary")
        ladder = const["LADDER"]
        eta = ladder_eta(float(ladder["c"]), float(entry["sigma_node"]))
        _require(eta == float(ladder["eta"]), f"{node}: LADDER eta is not c * sigma_node")
        noise[node] = {k: float(entry[k]) for k in ("sigma_node", "sigma_local", "sigma_structural", "delta_n")}
    ladder = {n: {"c": float(obj["nodes"][n]["LADDER"]["c"]), "eta": float(obj["nodes"][n]["LADDER"]["eta"])}
              for n in manifest.nodes}
    return Constants(vectors=raw, noise=noise, ladder=ladder)


def node_context(node: str, node_dir: Path, spec: Any, constants: Constants, *,
                 memory_mode: str = MEMORY_MODE) -> NodeContext:
    start = {p: (Path(node_dir) / p).read_text(encoding="utf-8") for p in spec.editable_paths}
    return NodeContext(node=node, start_files=start, sigma_node=constants.noise[node]["sigma_node"],
                       runs_total=W, memory_mode=memory_mode, trial_budget=TRIAL_BUDGET)


def build_prior(arm: str, node: str, constants: Constants) -> TableArmPrior:
    """A1/A2 as ``TableArmPrior`` over the constants file's own vector (bitwise the fitted vector)."""
    _require(arm in ("A1", "A2"), f"arm {arm!r} has no table prior in this unit")
    vector = tuple(float(x) for x in constants.vectors[arm][node])
    if arm == "A1":
        prior = ConstantPrior()
    else:
        prior = RulesPrior()
    prior.by_node = {node: list(vector)}
    prior.pooled = list(vector)
    return TableArmPrior(prior, arm)


def build_controller(arm: str, ctx: NodeContext, constants: Constants, *,
                     verify_runs: int = VERIFY_RUNS,
                     learned: Mapping[str, "LearnedArm"] | None = None) -> Any:
    """The declared controller of one harness arm (A0, A0R, A1, A2, LADDER).

    ``learned`` carries a frozen A3/A5 prior from a later reviewed unit; without it those arms are refused. A6
    always needs its own reviewed path (RUNBOOK P.5 / R1-C3-POST) and is not accepted here.
    """
    node = ctx.node
    if arm == "A0":
        return ContinueController()
    if arm == "A0R":
        return a0r_controller(ctx)
    if arm in ("A1", "A2"):
        prior = build_prior(arm, node, constants)
        fallback = build_prior("A1", node, constants)
        return RuleController(
            prior, ctx,
            sigma_cmp={"local": constants.noise[node]["sigma_local"],
                       "structural": constants.noise[node]["sigma_structural"]},
            fallback=fallback, verify_runs=verify_runs, split_policy=VERIFY_SPLIT_POLICY,
        )
    if arm == "LADDER":
        return ladder_controller(ctx, c=constants.ladder[node]["c"])
    if arm in REPLICATE_ARMS:
        raise AdapterStop(f"{arm} runs through make_replicate_factory, not the harness factory")
    if arm in LEARNED_ARMS:
        if arm != "A6" and learned and arm in learned:
            entry = learned[arm]
            fallback = build_prior("A1", node, constants)
            return RuleController(
                entry.prior, ctx,
                sigma_cmp={"local": constants.noise[node]["sigma_local"],
                           "structural": constants.noise[node]["sigma_structural"]},
                fallback=fallback, verify_runs=int(entry.verify_runs), split_policy=VERIFY_SPLIT_POLICY,
            )
        raise AdapterStop(f"arm {arm} needs a frozen learned artefact; the arms-frozen record does not exist yet "
                          "(no substitution is made)" + ("; A6 also needs its RUNBOOK P.5 unit" if arm == "A6" else ""))
    raise AdapterStop(f"unknown arm {arm!r}")


def campaign_kwargs(arm: str, controller: Any, *, verify_runs: int = VERIFY_RUNS,
                    verify_seed_base: int = VERIFY_SEED_BASE) -> dict[str, Any]:
    """``run_real_campaign`` kwargs shared by the arm controllers, with the verify settings pinned."""
    if arm in ("A0", "A0R"):
        av = ActionVersions.new_campaign(**{
            "keep_rule": KEEP_RULE_DEFAULT, "verify_response": VERIFY_RESPONSE_MEAN,
            "verify_split_policy": NEW_CAMPAIGN_VERIFY_SPLIT_POLICY,
        })
        kwargs = {"controller": controller, "skip_display": SKIP_DISPLAY, "action_versions": av,
                  **c3_budgets(W, LLM_CAP, TRIAL_BUDGET)}
    else:
        kwargs = controller.campaign_kwargs(W=W, llm_cap=LLM_CAP, trials=TRIAL_BUDGET)
    kwargs["verify_runs"] = int(verify_runs)
    kwargs["verify_seed_base"] = int(verify_seed_base)
    return kwargs


class LearnedArm:
    """The seam for A3/A5/A6 once a frozen artefact exists: a ``PriorModel`` plus the arm name.

    Not constructed by this unit. A later reviewed unit supplies the frozen object and its digest; nothing here
    guesses a prior.
    """

    def __init__(self, arm: str, prior: Any, *, verify_runs: int = VERIFY_RUNS) -> None:
        _require(arm in LEARNED_ARMS, f"{arm!r} is not a learned arm")
        _require(prior is not None, "a learned arm needs its frozen prior")
        self.arm, self.prior, self.verify_runs = arm, prior, int(verify_runs)


# ---------------------------------------------------------------------------
# the campaign directory and the factory
# ---------------------------------------------------------------------------

def prepare_node_dir(node: str, dest: Path, *, spec: Any, harness: Path, data_cache_root: str | None) -> Path:
    """Copy the node tree, add the declared OpenML data cache, and refuse a missing cache."""
    import shutil
    src = Path(harness) / "nodes" / node
    _require(src.is_dir(), f"harness node tree not found: {src}")
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", ".autoresearch_artifacts"))
    cache = dest / "data_cache"
    if node.startswith("openml_") and not cache.is_dir():
        candidates: list[Path] = []
        if data_cache_root:
            root = Path(data_cache_root)
            if root.name == node:
                candidates.append(root / "data_cache")
            else:
                candidates += [root / node / "data_cache", root / "data_cache"]
        candidates.append(src / "data_cache")
        for candidate in candidates:
            if candidate.is_dir():
                shutil.copytree(candidate, cache)
                break
        else:
            raise AdapterStop(f"{node}: no data_cache under {[str(c) for c in candidates]}")
    return dest


def _manager(manifest: Manifest, seed: int, repetition: int) -> LangGraphManager:
    return LangGraphManager(
        model=manifest.proposer_id(), temperature=manifest.temperature, repetition=int(repetition),
        proposal_schema=manifest.proposal_schema,
    )


def _ended_on(recorder: SnapshotRecorder, arm: str) -> str:
    budget = recorder._last_budget
    _require(budget is not None, "the recorder saw no compute budget")
    return table_ended_on(worker_runs=int(recorder.count), llm_calls=int(budget.llm_calls), arm=arm)


def make_campaign_factory(manifest: Manifest, constants: Constants, *,
                          harness: Path | str | None = None,
                          apply_env: bool = True,
                          manager_factory: Callable[[Manifest, int, int], Any] | None = None,
                          worker_factory: Callable[[Path, int], Any] | None = None,
                          ) -> Callable[[Any, int, Path, SnapshotRecorder], tuple[dict[str, Any], Any]]:
    """The harness-arm factory: one campaign directory, one ``run_real_campaign`` kwargs dict."""
    root = Path(harness) if harness is not None else Path(harness_root())
    if apply_env:
        apply_proposer_environment(manifest)
    build_manager = manager_factory or _manager

    def build_worker(node_dir: Path, seed: int) -> Any:
        if worker_factory is not None:
            return worker_factory(node_dir, seed)
        return LocalWorker(node_root=node_dir, artifact_dir=node_dir.parent / "art",
                           train_seed=int(seed), split_seed=int(seed))

    def factory(spec: Any, seed: int, campaign_dir: Path, recorder: SnapshotRecorder):
        arm, node = str(spec.arm), str(spec.node)
        _require(node in manifest.nodes, f"node {node!r} is not in the manifest")
        _require(arm in manifest.arms, f"arm {arm!r} is not in the manifest's stage {manifest.stage} set")
        _require(spec.stage == manifest.stage, f"chunk stage {spec.stage!r} differs from the manifest's {manifest.stage!r}")
        spec_node = load_registered_node(node, repo_root=root)
        node_dir = prepare_node_dir(node, Path(campaign_dir) / "node", spec=spec_node, harness=root,
                                    data_cache_root=manifest.data_cache_root)
        ctx = node_context(node, node_dir, spec_node, constants)
        controller = build_controller(arm, ctx, constants)
        kwargs = campaign_kwargs(arm, controller, verify_runs=VERIFY_RUNS, verify_seed_base=VERIFY_SEED_BASE)
        kwargs.update({
            "node_spec": spec_node,
            "campaign_id": spec.instance_id(seed),
            "manager_mode": "langgraph_manager",
            "memory_mode": MEMORY_MODE,
            "records_path": Path(campaign_dir) / "ledger.jsonl",
            "worker": build_worker(node_dir, seed),
            "proposal_backend": build_manager(manifest, seed, spec.repetition),
            "event_store": _event_store(Path(campaign_dir) / "events.jsonl"),
        })
        return wrap(kwargs, recorder), (lambda rec: _ended_on(rec, arm))

    return factory


def _event_store(path: Path) -> Any:
    from autoresearch.memory.event_store import CampaignEventStore
    return CampaignEventStore(path)


# ---------------------------------------------------------------------------
# FIXR3 / EGATE: the replicate unit (design revision 6c)
# ---------------------------------------------------------------------------

@dataclass
class _ReplicateState:
    node_dir: Path
    spec: Any
    ctx: NodeContext
    seed: int
    repetition: int
    manager: Any
    worker: Any
    start_files: dict[str, str]
    files: dict[str, str]
    memory_lines: list[str] = field(default_factory=list)
    engine: Any = None


def _parse_constants(node_dir: Path, editable_paths: tuple[str, ...],
                     editable_symbols: tuple[str, ...]) -> dict[str, str]:
    from autoresearch.manager.hyperparam_edits import parse_train_constants
    out: dict[str, str] = {}
    for rel in editable_paths:
        out.update(parse_train_constants(Path(node_dir) / rel))
    if editable_symbols:
        allowed = set(editable_symbols)
        out = {k: v for k, v in out.items() if k in allowed}
    return out


def _memory_context(state: _ReplicateState) -> MemoryContext:
    text = "\n".join(state.memory_lines)
    return MemoryContext(
        mode=MemoryMode(MEMORY_MODE), context_text=text, raw_memory_chars=len(text),
        compressed_chars=len(text), compression_ratio=1.0,
        repeated_bad_stats=RepeatedBadStats(
            repeated_bad_count=0, repeated_bad_rate=0.0, repeated_invalid_count=0,
            repeated_degraded_count=0, flagged_trial_ids=(),
        ),
    )


def _metric_direction(spec: Any) -> bool:
    return str(getattr(spec, "metric_direction", "maximize")).lower().endswith("max")


def make_replicate_factory(manifest: Manifest, constants: Constants, *,
                           harness: Path | str | None = None,
                           apply_env: bool = True,
                           manager_factory: Callable[[Manifest, int, int], Any] | None = None,
                           worker_factory: Callable[[Path, int], Any] | None = None,
                           ) -> Callable[[Any, int, Path, SnapshotRecorder], Any]:
    """The FIXR3/EGATE factory: one ``ReplicateUnit`` per campaign (design revision 6c)."""
    from r1.c3.d3.replicate_campaign import ReplicateUnit
    from r1.c3.d3_replicate import EgateEngine, Fixr3Engine

    root = Path(harness) if harness is not None else Path(harness_root())
    if apply_env:
        apply_proposer_environment(manifest)
    build_manager = manager_factory or _manager

    def factory(spec: Any, seed: int, campaign_dir: Path, recorder: SnapshotRecorder) -> ReplicateUnit:
        arm, node = str(spec.arm), str(spec.node)
        _require(arm in REPLICATE_ARMS, f"{arm!r} is not a replicate arm")
        _require(arm in manifest.arms, f"arm {arm!r} is not in the manifest")
        spec_node = load_registered_node(node, repo_root=root)
        node_dir = prepare_node_dir(node, Path(campaign_dir) / "node", spec=spec_node, harness=root,
                                    data_cache_root=manifest.data_cache_root)
        ctx = node_context(node, node_dir, spec_node, constants)
        start = {p: (node_dir / p).read_text(encoding="utf-8") for p in spec_node.editable_paths}
        state = _ReplicateState(
            node_dir=node_dir, spec=spec_node, ctx=ctx, seed=int(seed), repetition=int(spec.repetition),
            manager=build_manager(manifest, seed, spec.repetition),
            worker=(worker_factory(node_dir, seed) if worker_factory is not None else
                    LocalWorker(node_root=node_dir, artifact_dir=Path(campaign_dir) / "art",
                                train_seed=int(seed), split_seed=int(seed))),
            start_files=dict(start), files=dict(start),
        )

        def propose(step_index: int, incumbent_config: Mapping[str, Any], llm_calls: int) -> Any:
            # The loop restores a discarded candidate only inside the next step's first run; the
            # manager must see the incumbent, so restore it here from the loop's own contents.
            files = dict(incumbent_config)
            if files != state.files:
                for rel in spec_node.editable_paths:
                    (state.node_dir / rel).write_text(files[rel], encoding="utf-8")
                state.files = files
            constants_now = _parse_constants(state.node_dir, spec_node.editable_paths,
                                             tuple(getattr(spec_node, "editable_symbols", ()) or ()))
            from autoresearch.manager.base import ManagerProposal, ManagerStatus
            best = None
            if state.engine is not None and state.engine.incumbent_metrics:
                oriented = math.fsum(state.engine.incumbent_metrics) / len(state.engine.incumbent_metrics)
                best = oriented if _metric_direction(spec_node) else -oriented
            status = ManagerStatus(
                campaign_id=spec.instance_id(seed), budget_index=int(step_index) + 1,
                current_best_metric=best, metric_name=spec_node.metric_name,
                metric_direction=spec_node.metric_direction, current_constants=constants_now,
                effective_config={k: constants_now[k] for k in sorted(constants_now)},
            )
            proposal = state.manager.propose_next_trial(status, _memory_context(state),
                                                        spec_node)
            return proposal

        def validate(proposal: Any) -> tuple[dict[str, str], str] | None:
            extra = getattr(proposal, "extra", None) or {}
            edit = extra.get("structured_edit")
            if not isinstance(edit, dict):
                return None
            try:
                files = apply_edit(state.files, edit)
            except ValueError:
                return None
            return files, config_sha256(files)

        def restore_incumbent(config: Mapping[str, Any]) -> None:
            files = dict(config)
            for rel in spec_node.editable_paths:
                (state.node_dir / rel).write_text(files[rel], encoding="utf-8")
            state.files = files

        def run_trial(proposal: Any, config: Mapping[str, Any], seed_j: int, j: int, budget_index: int):
            files = dict(config)
            for rel in spec_node.editable_paths:
                (state.node_dir / rel).write_text(files[rel], encoding="utf-8")
            state.files = files
            noedit = ManagerProposal(
                manager_mode="d3_replicate_worker", proposal_summary=str(getattr(proposal, "proposal_summary", "")),
                proposal_rationale=str(getattr(proposal, "proposal_rationale", "")),
                target_files=tuple(spec_node.editable_paths), objective="D.3 replicate run; configuration applied.",
            )
            started = __import__("time").perf_counter()
            result = state.worker.run_trial_at_seed(noedit, spec_node, int(budget_index), train_seed=int(seed_j),
                                                   split_seed=int(seed_j))
            seconds = __import__("time").perf_counter() - started
            metric = (result.parsed_metrics or {}).get(spec_node.metric_name) if result.success else None
            ok = bool(result.success) and isinstance(metric, (int, float)) and not isinstance(metric, bool) \
                and math.isfinite(float(metric))
            state.memory_lines.append(
                f"run {budget_index}.{j}: seed={seed_j}; metric={float(metric) if ok else 'failed'}"
            )
            state.memory_lines = state.memory_lines[-20:]
            return ok, (float(metric) if ok else None), seconds

        engine = (Fixr3Engine(int(seed), maximize=_metric_direction(spec_node)) if arm == "FIXR3"
                  else EgateEngine(int(seed), maximize=_metric_direction(spec_node)))
        state.engine = engine
        return ReplicateUnit(
            engine=engine, propose=propose, validate=validate, run_trial=run_trial,
            start_config=dict(state.start_files), restore_incumbent=restore_incumbent,
            node_spec=spec_node,
        )

    return factory
