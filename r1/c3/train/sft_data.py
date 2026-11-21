"""Track P Stage S (SFT) data builder (spec §3, §6.1; R1-TRACKP-SFT-DEV). ENGINEERING_ONLY; AI-assisted (Claude).

Builds the training view of one C3 proposal table: one row per labelled proposal of the training and validation
instances, holding the ``trackp_prompt/v2`` prompt of the proposal (replayed from the sweep ledgers with the same
featurizer, ``c3_features/v3``, that built the table) and its soft label ``y`` from the **label seeds 7001–7005
only**. Nothing here reads the evaluation seeds 7006–7010.

Pieces
------
* **Label sources** (``LabelSource``): ``label_records()`` returns one record per labelled proposal —
  ``{proposal_id, node, label_kind ("audit" | "rule_noop"), delta_label, k_label, sigma_node}`` — and
  ``provenance()`` what the data manifest records about the source.

  - ``LabelBlockSource``: the ``label_block.jsonl`` that ``r1.c3.audit evidence-run`` writes (sweep-1 B.2; sweep 2's
    B.2 is to write the same file through the same code, so it plugs in with ``sweep="sweep2"``). It opens exactly
    two files: the label block and its ``evidence_completion.json`` (for the label block's sha256, the label seeds
    and the sweep index and classification hashes; the completion file holds hashes and counts only). The sweep is
    derived from the completion's ``index_sha256`` (sweep 1 iff it is the sweep-1 index) and must match ``sweep``
    and, when given, the index the prompts replay; a sweep-2 block (and any non-sweep-1 block) passes the R1-BX-D8
    guard (``analysis_guard.require_d8_confirmation``) before any read, and no ``r1_sealed`` path is opened. It
    refuses any path that names the evaluation block, the run log (``runs.jsonl`` holds both seed blocks) or a mixed
    ``audits.jsonl``, and a label block beside a mixed ``audits.jsonl`` or a ``STOP.json``; a completion whose label
    seeds are not 7001–7005 or whose label-block sha256 differs; and any label row with a field outside the
    label-block schema or a field name matching the evaluation-column pattern (``run.EVAL_COLUMNS``). The full consumption check ``audit.verify_evidence_completion`` re-derives both blocks
    from ``runs.jsonl`` and so reads the evaluation seeds: it is a separate step, run outside this process by the
    agent that consumes the audit; the manifest records that it was not run here.
  - ``SyntheticLabelSource``: deterministic synthetic labels for dry runs (a hash of the proposal id; never audit
    data). Rule no-ops get the inert label and duplicates none, as in the audit.

* **Prompts**: ``campaign_prompts`` replays one root ledger exactly as ``features.replay_campaign`` does (same row
  filter, same ``ReplayView``) and serialises each proposal with ``serialize.serialize_view``; ``sweep_prompts``
  runs it over every ledger of a sweep whose inputs the caller resolved and validated with
  ``dataset.sweep_replay_inputs`` (the resolution step of ``dataset.build_from_sweep``), repeating
  ``_replay_sources``' per-ledger exam and sealed-path refusals. Every replayed proposal's features must equal the table row's (``features_hash``),
  which binds each prompt to its table row.

* **Soft labels**: ``labels.soft_label`` in mode ``pooled_node`` (R1-SOFT-SIGMA; spec §3.4: s = sigma_node /
  sqrt(k_label), k_label = 5); rule no-ops one-hot on the inert bin. ``sigma_node`` of the label must equal the
  table row's.

* **Splits** (spec §3.6; R1-MAIN-PROPOSER (e)): by instance, never by trial. The assignment is computed over a fixed
  **instance universe** — for real runs the authorized design, 8 nodes × 18 instance seeds
  (``e1b_collect._instance_seed``), from the SFT config — so it does not depend on which instances a table holds:
  per node, the universe's instances are ordered by ``sha256(salt + ":" + instance)``; the first
  ``test_instances_per_node`` are test, the next ``val_instances_per_node`` val, the rest train. A table instance
  outside the universe is refused. Sweep 2 reuses sweep 1's instance seeds, so both sources get one assignment even
  if a campaign is missing from one of them. Without a universe (synthetic dry runs only) the table's instances
  serve as one, and ``splits.json`` says so. ``holdout_nodes`` (LONO) puts whole nodes in test; ``splits.json``
  lists them, so an evaluator can separate held-out nodes from in-distribution test instances.
  Cross-split duplicates: the same (node, incumbent configuration, candidate configuration) on two instances —
  frequent, since every campaign of a node starts from the same configuration, and B.2 audits each distinct
  configuration once, so such rows carry the same label. **R1-TRACKP-SFT-DUP** (author, 17 Nov 2026) decides
  the rule, policy ``heldout_excludes_seen`` (default, and the only policy allowed with real labels, both when a
  data directory is built and when it is loaded): every train
  row is kept; the **primary** held-out results exclude the proposals whose key also occurs in the training data —
  a val row whose key occurs on a train instance, and a test proposal whose key occurs on a train or val instance
  (val is used for early stopping, temperature and lr selection, so a test pair seen there is not unseen either);
  the **secondary** results use the full held-out populations, duplicates included. A key counts as seen if
  it occurs on any table row of a train (or val) instance, labelled or not (on sweep 1 this gives the same
  populations as labelled rows only). Such val rows are written with
  split ``val_seen`` (secondary only; never used for early stopping, temperature or selection), and ``splits.json``
  lists the test proposals the primary test population leaves out (the secondary test population is every
  proposal of the test instances). Two earlier policies remain for synthetic comparisons only (refused with real
  labels): ``drop_from_train`` drops a train or val row whose key also occurs on a test instance, and a train row
  whose key occurs on a val instance; ``exclude_from_heldout`` is the primary half of the decided rule without the
  secondary rows.
  Counts are recorded. Test instances contribute no row to the data directory: only their names (and, under
  ``heldout_excludes_seen`` and ``exclude_from_heldout``, the test proposal ids the primary test population leaves
  out), in ``splits.json``.

The manifest records whether the audit's table (the completion's ``proposals_sha256``) is the table given here
(``table_matches_audit_table``); when it is not (e.g. a label block audited on another build of the same ledgers),
every label must still name a proposal of this table with the same node, ``sigma_node`` and inert status, and the
count of table rows without a label is recorded.

Output directory: ``rows.jsonl`` (train, val and val_seen rows: ids, grouping keys, split, prompt, ``y``), ``splits.json``,
``sft_data.json`` (the data manifest: versions, table hashes, label provenance, counts, rows sha256). Rows carry
no evidence label or audit identity (the label-only boundary that ``run.guard_rows`` asks for); provenance lives
in the manifest only.
"""
from __future__ import annotations

import dataclasses
import glob
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Protocol, Sequence

import numpy as np

from r1.c3 import labels as LB
from r1.c3.analysis_guard import SWEEP1_INDEX_SHA, guard_table, refuse_sealed, require_d8_confirmation
from r1.c3.features import (FEATURIZER_VERSION, NodeContext, ReplayProposal, ReplayView, featurize_view,
                            features_hash, parsed_metric, read_jsonl)
from r1.c3.train.types import MAX_TOKENS, PROMPT_VERSION, DecisionPrompt

SFT_DATA_SCHEMA = "trackp_sft_data/v1"
LABEL_SEEDS = (7001, 7002, 7003, 7004, 7005)
K_LABEL = len(LABEL_SEEDS)
SIGMA_MODE = "pooled_node"
COMPLETION_SCHEMA_PREFIX = "r1.c3_audit_completion/"
# Files of an audit output directory that hold evaluation-seed values (or both blocks); never opened here.
FORBIDDEN_NAMES = frozenset({"evaluation_block.jsonl", "runs.jsonl", "audits.jsonl", "evaluations.jsonl"})
LABEL_ROW_KEYS = frozenset({"proposal_id", "node", "label_kind", "seeds", "delta_label", "se_label",
                            "soft_parameters"})
SOFT_PARAMETER_KEYS = frozenset({"inert", "sigma_node", "k_label", "delta_label", "se_label"})
SPLITS = ("train", "val", "test")
PARTITION_NAME = "label_block.traindev.jsonl"   # the released train/dev partition (r1.c3.release, PRE-STAGE A)
DEFAULT_SPLITS = {"salt": "trackp_sft/v1", "test_instances_per_node": 3, "val_instances_per_node": 3,
                  "holdout_nodes": [], "cross_split_duplicates": "heldout_excludes_seen"}
DECIDED_DUPLICATE_POLICY = "heldout_excludes_seen"      # R1-TRACKP-SFT-DUP
DUPLICATE_POLICIES = (DECIDED_DUPLICATE_POLICY, "drop_from_train", "exclude_from_heldout")
LABEL_STATUS = ("ENGINEERING_ONLY (R1-TRACKP-SFT-DEV): readiness only; not used for any evidence, selection or "
                "tuning; label seeds 7001-7005 only, never the evaluation block 7006-7010")
SPLIT_UNIVERSE_SCHEMA = "trackp_sft_instance_universe/v1"


def instance_universe(nodes: Sequence[str], instances_per_node: int) -> list[str]:
    """The authorized instance set: ``<node>__s<seed>`` for k = 0..n-1 (``e1b_collect._instance_seed``)."""
    from r1.headroom.e1b_collect import _instance_seed
    return sorted(f"{node}__s{_instance_seed(node, k)}" for node in nodes for k in range(int(instances_per_node)))


class SFTDataError(ValueError):
    """A fail-closed refusal of the SFT data builder."""


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def edit_hash(edit: Mapping | None) -> str:
    return hashlib.sha256(_canonical(edit or {}).encode()).hexdigest()[:20]


def _eval_columns():
    from r1.c3.train.run import EVAL_COLUMNS
    return EVAL_COLUMNS


def _all_keys(obj, depth: int = 0) -> Iterable[str]:
    if depth > 6:
        return
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            yield str(k)
            yield from _all_keys(v, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _all_keys(v, depth + 1)


def refuse_evaluation_path(path: Path | str) -> Path:
    """Refuse a path that names an evaluation-seed (or mixed) file of an audit directory."""
    path = Path(path)
    name = path.name.lower()
    if name in FORBIDDEN_NAMES or "evaluation" in name or "eval_block" in name:
        raise SFTDataError(f"{path}: the SFT data builder never opens evaluation-seed or mixed audit files")
    return path


# ---------------------------------------------------------------------------------------------- label sources

class LabelSource(Protocol):
    def label_records(self) -> list[dict]: ...

    def provenance(self) -> dict: ...


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


class LabelBlockSource:
    """``label_block.jsonl`` of a B.2-style fresh-seed audit (module docstring)."""

    def __init__(self, label_block: Path | str, *, sweep: str = "sweep1", completion: Path | str | None = None,
                 freeze: Path | str | None = None, index_sha256: str | None = None,
                 classification_sha256: str | None = None) -> None:
        if sweep not in ("sweep1", "sweep2"):
            raise SFTDataError(f"unknown label sweep {sweep!r}")
        self.path = refuse_evaluation_path(label_block)
        if self.path.name not in ("label_block.jsonl", PARTITION_NAME):
            raise SFTDataError(f"{self.path}: expected a released {PARTITION_NAME} (or, after the test release row, "
                               "an audit's label_block.jsonl)")
        self.partition = self.path.name == PARTITION_NAME
        self.sweep = sweep
        self.completion_path = refuse_evaluation_path(completion or self.path.parent / "evidence_completion.json")
        self.freeze = None if freeze is None else refuse_evaluation_path(freeze)
        refuse_sealed(self.path, self.completion_path, self.freeze)
        self.index_sha256, self.classification_sha256 = index_sha256, classification_sha256
        self._records: list[dict] | None = None
        self._prov: dict | None = None

    def _load(self) -> None:
        if self.sweep == "sweep2":
            require_d8_confirmation()          # R1-BX-D8: before any sweep-2 label file is opened
        if self.partition:
            return self._load_partition()
        from r1.c3.release import guard_raw_label_path
        guard_raw_label_path(self.path, "T0")  # PRE-STAGE A: a raw sweep label block only after the T0 test row
        self._prov_extra = {}
        if (self.path.parent / "STOP.json").exists():
            raise SFTDataError(f"{self.path.parent}: the audit stopped (STOP.json); its label block is not complete")
        if (self.path.parent / "audits.jsonl").exists():
            raise SFTDataError(f"{self.path.parent}: a mixed audits.jsonl sits beside the label block")
        if not self.completion_path.is_file():
            raise SFTDataError(f"{self.completion_path}: a label block needs its completion record")
        completion = json.loads(self.completion_path.read_bytes())
        if not str(completion.get("schema", "")).startswith(COMPLETION_SCHEMA_PREFIX):
            raise SFTDataError(f"{self.completion_path}: schema {completion.get('schema')!r} is not an audit completion")
        if completion.get("label_seeds") != list(LABEL_SEEDS):
            raise SFTDataError(f"{self.completion_path}: label seeds {completion.get('label_seeds')} != 7001-7005")
        index_sha = completion.get("index_sha256")
        if not isinstance(index_sha, str) or not index_sha:
            raise SFTDataError(f"{self.completion_path}: no index_sha256; the label block cannot be bound to its sweep")
        derived = "sweep1" if index_sha == SWEEP1_INDEX_SHA else "sweep2"
        if derived == "sweep2":
            require_d8_confirmation()
        if derived != self.sweep:
            raise SFTDataError(f"{self.completion_path}: the label block belongs to {derived}, not {self.sweep}")
        if self.index_sha256 is not None and index_sha != self.index_sha256:
            raise SFTDataError(f"{self.completion_path}: audited on another sweep index than the prompts replay")
        if self.classification_sha256 is not None and \
                completion.get("classification_sha256") != self.classification_sha256:
            raise SFTDataError(f"{self.completion_path}: audited under another classification sidecar")
        data = self.path.read_bytes()                       # read once; hash and parse the same bytes
        digest = hashlib.sha256(data).hexdigest()
        if completion.get("label_block_sha256") != digest:
            raise SFTDataError(f"{self.path}: sha256 {digest} differs from the completion record")
        self._parse(data, digest, completion, completion_file={"path": str(self.completion_path),
                                                             "sha256": sha256_file(self.completion_path)})

    def _load_partition(self) -> None:
        """A receipted train/dev partition (PRE-STAGE A): the receipt carries the completion excerpt that the
        release step's integrity check verified."""
        from r1.c3.release import open_partition, ReleaseStop
        try:            # source, stage, row, output sha256 and P3 membership of every row re-checked
            _, receipt = open_partition(self.path.parent, expect_source=self.sweep, expect_stage="traindev")
        except ReleaseStop as exc:
            raise SFTDataError(str(exc)) from exc
        completion = dict((receipt.get("integrity") or {}).get("completion") or {})
        if not str(completion.get("schema", "")).startswith(COMPLETION_SCHEMA_PREFIX):
            raise SFTDataError(f"{self.path}: the receipt carries no audit completion")
        if completion.get("label_seeds") != list(LABEL_SEEDS):
            raise SFTDataError(f"{self.path}: label seeds {completion.get('label_seeds')} != 7001-7005")
        if completion.get("label_block_sha256") != receipt["inputs"]["label_block_sha256"]:
            raise SFTDataError(f"{self.path}: the receipt's completion binds another label block")
        derived = "sweep1" if completion.get("index_sha256") == SWEEP1_INDEX_SHA else "sweep2"
        if derived != self.sweep:
            raise SFTDataError(f"{self.path}: the label block belongs to {derived}, not {self.sweep}")
        if self.index_sha256 is not None and completion.get("index_sha256") != self.index_sha256:
            raise SFTDataError(f"{self.path}: audited on another sweep index than the prompts replay")
        if self.classification_sha256 is not None and \
                completion.get("classification_sha256") != self.classification_sha256:
            raise SFTDataError(f"{self.path}: audited under another classification sidecar")
        data = self.path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != receipt["outputs"][PARTITION_NAME]:
            raise SFTDataError(f"{self.path}: differs from its receipt")
        self._prov_extra = {"release_receipt": {"path": str(self.path.parent / "RECEIPT.json"),
                                                "sha256": sha256_file(self.path.parent / "RECEIPT.json"),
                                                "row_id": receipt["row_id"], "stage": receipt["stage"]}}
        self._parse(data, digest, completion, completion_file={"from_release_receipt": True})

    def _parse(self, data: bytes, digest: str, completion: dict, *, completion_file: dict) -> None:
        pattern = _eval_columns()
        records, seen = [], set()
        for n, line in enumerate(data.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not set(row) <= LABEL_ROW_KEYS:
                extra = sorted(set(row) - LABEL_ROW_KEYS) if isinstance(row, dict) else row
                raise SFTDataError(f"{self.path}:{n}: fields outside the label-block schema: {extra!r}")
            bad = sorted({k for k in _all_keys(row) if pattern.search(k)})
            if bad:
                raise SFTDataError(f"{self.path}:{n}: evaluation-column names {bad}")
            soft = row.get("soft_parameters") or {}
            if not isinstance(soft, dict) or not set(soft) <= SOFT_PARAMETER_KEYS:
                raise SFTDataError(f"{self.path}:{n}: soft parameters outside the schema")
            pid, kind = row.get("proposal_id"), row.get("label_kind")
            if not isinstance(pid, str) or pid in seen:
                raise SFTDataError(f"{self.path}:{n}: missing or duplicate proposal id")
            seen.add(pid)
            if kind == "rule_noop":
                if soft.get("inert") is not True or row.get("delta_label") != 0.0:
                    raise SFTDataError(f"{self.path}:{n}: a rule no-op must be inert with delta 0")
                records.append({"proposal_id": pid, "node": row.get("node"), "label_kind": kind,
                                "delta_label": None, "k_label": 0, "sigma_node": None})
            elif kind == "audit":
                if row.get("seeds") != list(LABEL_SEEDS) or soft.get("k_label") != K_LABEL or soft.get("inert"):
                    raise SFTDataError(f"{self.path}:{n}: an audit label must come from seeds 7001-7005 (k = 5)")
                if not _finite(row.get("delta_label")) or soft.get("delta_label") != row.get("delta_label"):
                    raise SFTDataError(f"{self.path}:{n}: non-finite or inconsistent label value")
                sigma = soft.get("sigma_node")
                if not _finite(sigma) or not float(sigma) > 0:
                    raise SFTDataError(f"{self.path}:{n}: invalid sigma_node")
                records.append({"proposal_id": pid, "node": row.get("node"), "label_kind": kind,
                                "delta_label": float(row["delta_label"]), "k_label": K_LABEL,
                                "sigma_node": float(sigma)})
            else:
                raise SFTDataError(f"{self.path}:{n}: unknown label kind {kind!r}")
        keep = ("schema", "label", "label_block_sha256", "proposals_sha256", "build_sha256", "configs_sha256",
                "plan_sha256", "counts", "label_seeds", "index_sha256", "classification_sha256")
        self._prov = {"kind": "label_block_partition" if self.partition else "label_block", "sweep": self.sweep,
                      "path": str(self.path), "sha256": digest, **self._prov_extra,
                      "completion": {**completion_file, **{k: completion[k] for k in keep if k in completion}},
                      "full_completion_verification": ("run by the release step's integrity check (receipt)"
                                                       if self.partition else
                                                       "not run in this process: audit.verify_evidence_completion "
                                                       "reads the evaluation seeds; run it separately before use"),
                      "freeze": None if self.freeze is None else {"path": str(self.freeze),
                                                                  "sha256": sha256_file(self.freeze)},
                      "n_records": len(records)}
        self._records = records

    def label_records(self) -> list[dict]:
        if self._records is None:
            self._load()
        return [dict(r) for r in self._records]

    def provenance(self) -> dict:
        if self._prov is None:
            self._load()
        return dict(self._prov)


class SyntheticLabelSource:
    """Deterministic synthetic labels for dry runs: delta = sigma_node * (N(0, 1) + shift_z), N drawn from a hash of
    (seed, proposal id). Never audit data."""

    def __init__(self, table_rows: Sequence[dict], *, seed: int = 0, shift_z: float = 0.0) -> None:
        self.rows, self.seed, self.shift_z = list(table_rows), int(seed), float(shift_z)

    def label_records(self) -> list[dict]:
        out = []
        for row in self.rows:
            pid = row["proposal_id"]
            if row.get("noop"):
                out.append({"proposal_id": pid, "node": row["node"], "label_kind": "rule_noop",
                            "delta_label": None, "k_label": 0, "sigma_node": None})
                continue
            if row.get("duplicate"):
                continue
            h = int(hashlib.sha256(f"{self.seed}:{pid}".encode()).hexdigest()[:16], 16)
            z = float(np.random.default_rng(h).standard_normal()) + self.shift_z
            sigma = float(row["sigma_node"])
            out.append({"proposal_id": pid, "node": row["node"], "label_kind": "audit",
                        "delta_label": z * sigma, "k_label": K_LABEL, "sigma_node": sigma})
        return out

    def provenance(self) -> dict:
        return {"kind": "synthetic", "seed": self.seed, "shift_z": self.shift_z,
                "note": "synthetic labels for dry runs; not audit data"}


def soft_target(record: Mapping, table_row: Mapping) -> np.ndarray:
    """Soft label of one record (R1-SOFT-SIGMA pooled_node; rule no-ops inert)."""
    if record["node"] != table_row["node"]:
        raise SFTDataError(f"{record['proposal_id']}: label node {record['node']!r} != table node "
                           f"{table_row['node']!r}")
    if record["label_kind"] == "rule_noop":
        if not table_row.get("noop"):
            raise SFTDataError(f"{record['proposal_id']}: rule no-op label on a table row that is not a no-op")
        return LB.soft_label(None, None, float(table_row["sigma_node"]), inert=True, sigma_mode=SIGMA_MODE)
    if table_row.get("noop") or table_row.get("duplicate"):
        raise SFTDataError(f"{record['proposal_id']}: audit label on an inert table row")
    if float(record["sigma_node"]) != float(table_row["sigma_node"]):
        raise SFTDataError(f"{record['proposal_id']}: label sigma_node differs from the table's")
    return LB.soft_label(record["delta_label"], None, float(table_row["sigma_node"]), inert=False,
                         sigma_mode=SIGMA_MODE, k_label=int(record["k_label"]))


# ---------------------------------------------------------------------------------------------- prompts

def campaign_prompts(records: Sequence[dict], ctx: NodeContext, *, instance: str, source: str,
                     tokenizers: Mapping | None, max_tokens: int = MAX_TOKENS) -> dict[str, tuple]:
    """{proposal_id: (DecisionPrompt, features)} of one root ledger, with ``replay_campaign``'s row filter."""
    from r1.c3.train.serialize import _row_edit, serialize_view
    out: dict[str, tuple] = {}
    rows = list(records)
    for i, row in enumerate(rows):
        b = int(row["budget_index"])
        if row["decision"] == "skipped" or parsed_metric(row) is None:
            continue
        view = ReplayView(budget_index=b, ledger_prefix=tuple(rows[:i]), current_best=row.get("current_best_before"),
                          proposal=ReplayProposal(extra={"structured_edit": _row_edit(row)}))
        res = featurize_view(view, ctx, instance=instance)
        if res is None:
            continue
        pid = f"{source}:{instance}:t{b:03d}"
        prompt = serialize_view(view, ctx, tokenizers=tokenizers, max_tokens=max_tokens, group=pid,
                                meta={"proposal_id": pid})
        if prompt is None:
            raise SFTDataError(f"{pid}: featurized but not serialised")
        out[pid] = (prompt, res.features)
    return out


def sweep_prompts(inputs: Mapping, *, tokenizers: Mapping | None, wanted: set[str] | None = None,
                  max_tokens: int = MAX_TOKENS) -> dict[str, tuple]:
    """Prompts of every proposal of a sweep (``inputs`` from ``dataset.sweep_replay_inputs``). ``wanted`` limits the
    campaigns replayed to those that hold a wanted proposal id (every proposal of such a campaign is replayed)."""
    from r1.c3 import dataset as D
    from r1.exam.namespace import refuse_exam
    out: dict[str, tuple] = {}
    noise = inputs["noise"]
    campaigns = None if wanted is None else {w.rsplit(":", 1)[0] for w in wanted}
    for name, (src, d) in inputs["specs"].items():
        d = Path(d)
        refuse_sealed(d, d / "manifest.json")
        refuse_exam(src, context=f"C3 source {name}")
        if (d / "manifest.json").exists():
            refuse_exam(json.loads((d / "manifest.json").read_text()), context=f"C3 manifest {d}")
        for f in sorted(glob.glob(str(d / src["ledgers"]))):
            inst = Path(f).parent.name
            if campaigns is not None and f"{name}:{inst}" not in campaigns:
                continue
            refuse_exam(inst, context=f"C3 ledger {f}")
            node = inst.split("__s")[0]
            ctx = NodeContext(node=node, start_files=D._start_files(d, inst, node, strict=True),
                              sigma_node=noise[node]["sigma_node"], runs_total=src["runs"],
                              memory_mode=src["memory_mode"])
            records = read_jsonl(Path(f))
            refuse_exam(records, context=f"C3 ledger {f}")
            out.update(campaign_prompts(records, ctx, instance=inst, source=name,
                                        tokenizers=tokenizers, max_tokens=max_tokens))
    return out


def prompt_to_dict(p: DecisionPrompt) -> dict:
    return dataclasses.asdict(p)


def prompt_from_dict(d: Mapping) -> DecisionPrompt:
    return DecisionPrompt(state=d["state"], proposal=d["proposal"], question=d["question"],
                          options=tuple(d["options"]), group=d.get("group", ""), meta=dict(d.get("meta") or {}))


# ---------------------------------------------------------------------------------------------- splits

def dup_key(row: Mapping) -> str:
    return f"{row['node']}|{row['incumbent_hash']}|{row['candidate_hash']}"


def assign_splits(instances: Iterable[str], cfg: Mapping | None = None,
                  universe: Iterable[str] | None = None) -> dict[str, str]:
    """{instance: split} over the instance universe (module docstring); every given instance must be in it."""
    cfg = {**DEFAULT_SPLITS, **(cfg or {})}
    instances = set(instances)
    pool = instances if universe is None else set(universe)
    outside = sorted(instances - pool)
    if outside:
        raise SFTDataError(f"instances outside the split universe: {outside[:5]}")
    by_node: dict[str, list[str]] = {}
    for inst in sorted(pool):
        by_node.setdefault(inst.split("__s")[0], []).append(inst)
    unknown = sorted(set(cfg["holdout_nodes"]) - set(by_node))
    if unknown:
        raise SFTDataError(f"holdout nodes not in the table: {unknown}")
    n_test, n_val = int(cfg["test_instances_per_node"]), int(cfg["val_instances_per_node"])
    out = {}
    for node, insts in sorted(by_node.items()):
        order = sorted(insts, key=lambda i: hashlib.sha256(f"{cfg['salt']}:{i}".encode()).hexdigest())
        if node in set(cfg["holdout_nodes"]):
            out.update({i: "test" for i in order})
            continue
        if len(order) < n_test + n_val + 1:
            raise SFTDataError(f"node {node}: {len(order)} instances, need > {n_test + n_val} for the split")
        for j, inst in enumerate(order):
            out[inst] = "test" if j < n_test else "val" if j < n_test + n_val else "train"
    return out


# ---------------------------------------------------------------------------------------------- table

def load_table(table_dir: Path | str, pins: Mapping | None = None) -> tuple[list[dict], dict]:
    """Table rows plus the table's file hashes; ``pins`` ({file: sha256}) must match when given."""
    table_dir = Path(table_dir)
    # R1-BX-D8 and r1_sealed, before any label file is opened (as dataset.load_table)
    guard_table(table_dir, *[table_dir / n for n in ("proposals.jsonl", "configs.json") if (table_dir / n).exists()])
    blobs = {name: (table_dir / name).read_bytes() for name in ("proposals.jsonl", "configs.json", "build.json")
             if (table_dir / name).is_file()}
    files = {name: hashlib.sha256(b).hexdigest() for name, b in blobs.items()}
    if "proposals.jsonl" not in files:
        raise SFTDataError(f"{table_dir}: no proposals.jsonl")
    for name, want in (pins or {}).items():
        if files.get(name) != want:
            raise SFTDataError(f"{table_dir}/{name}: sha256 {files.get(name)} != pinned {want}")
    rows = [json.loads(x) for x in blobs["proposals.jsonl"].decode("utf-8").splitlines() if x.strip()]
    bad = sorted({k for r in rows for k in _all_keys(r) if _eval_columns().search(k)})
    if bad:
        raise SFTDataError(f"{table_dir}: table rows carry evaluation-column names {bad}")
    return rows, files


# ---------------------------------------------------------------------------------------------- build

def build_sft_data(table_rows: Sequence[dict], label_source: LabelSource, prompts: Mapping[str, tuple],
                   out_dir: Path | str, *, split_cfg: Mapping | None = None, table_record: Mapping | None = None,
                   prompt_record: Mapping | None = None, universe: Sequence[str] | None = None) -> dict:
    """Write the SFT data directory (module docstring); returns the data manifest."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SFTDataError(f"{out_dir}: output directory exists and is not empty (never overwritten)")
    split_cfg = {**DEFAULT_SPLITS, **(split_cfg or {})}
    policy = split_cfg["cross_split_duplicates"]
    if policy not in DUPLICATE_POLICIES:
        raise SFTDataError(f"unknown cross_split_duplicates policy {split_cfg['cross_split_duplicates']!r}")
    if policy != DECIDED_DUPLICATE_POLICY and label_source.provenance().get("kind") != "synthetic":
        raise SFTDataError(f"cross_split_duplicates {policy!r} is for synthetic comparisons only; R1-TRACKP-SFT-DUP "
                           f"decides {DECIDED_DUPLICATE_POLICY!r} for real labels")
    by_id = {r["proposal_id"]: r for r in table_rows}
    if len(by_id) != len(table_rows):
        raise SFTDataError("duplicate proposal id in the table")
    records = label_source.label_records()
    unknown = sorted(r["proposal_id"] for r in records if r["proposal_id"] not in by_id)
    if unknown:
        raise SFTDataError(f"{len(unknown)} labelled proposals are not in the table, e.g. {unknown[:3]}")
    stray = sorted(set(prompts) - set(by_id))
    if stray:
        raise SFTDataError(f"{len(stray)} replayed proposals are not in the table, e.g. {stray[:3]}")
    for pid, (_, feats) in prompts.items():
        if features_hash(feats) != features_hash(by_id[pid]["features"]):
            raise SFTDataError(f"{pid}: replayed features differ from the table row")
    missing = sorted(r["proposal_id"] for r in records if r["proposal_id"] not in prompts)
    if missing:
        raise SFTDataError(f"{len(missing)} labelled proposals have no replayed prompt, e.g. {missing[:3]}")
    split_of = assign_splits({r["instance"] for r in table_rows}, split_cfg, universe)
    keys = {s_: {dup_key(r) for r in table_rows if split_of[r["instance"]] == s_} for s_ in SPLITS}
    labelled = {r["proposal_id"] for r in records}
    rows_out, counts = [], {"table_rows": len(table_rows), "labelled": len(records),
                            "table_rows_without_label": sum(r["proposal_id"] not in labelled for r in table_rows),
                            "test_rows_withheld": 0, "dropped_dup_of_test": 0, "dropped_dup_of_val": 0,
                            "val_dropped_seen_in_train": 0,
                            "train": 0, "val": 0, "val_seen": 0, "rule_noop": 0}
    for rec in sorted(records, key=lambda r: r["proposal_id"]):
        row = by_id[rec["proposal_id"]]
        split = split_of[row["instance"]]
        if split == "test":
            counts["test_rows_withheld"] += 1
            continue
        key = dup_key(row)
        if policy == "drop_from_train":
            if key in keys["test"]:
                counts["dropped_dup_of_test"] += 1
                continue
            if split == "train" and key in keys["val"]:
                counts["dropped_dup_of_val"] += 1
                continue
        elif split == "val" and key in keys["train"]:
            if policy == "exclude_from_heldout":
                counts["val_dropped_seen_in_train"] += 1
                continue
            split = "val_seen"                             # heldout_excludes_seen: secondary (full val) only
        y = soft_target(rec, row)
        counts[split] += 1
        counts["rule_noop"] += rec["label_kind"] == "rule_noop"
        rows_out.append({"proposal_id": rec["proposal_id"], "node": row["node"], "instance": row["instance"],
                         "instance_seed": row["instance_seed"], "source": row["source"], "split": split,
                         "label_kind": rec["label_kind"], "edit_hash": edit_hash(row.get("edit")),
                         "dup_key": key, "prompt": prompt_to_dict(prompts[rec["proposal_id"]][0]),
                         "y": [float(v) for v in y]})
    if not counts["train"] or not counts["val"]:
        raise SFTDataError(f"empty training or validation split: {counts}")
    bad = sorted({k for r in rows_out for k in _all_keys(r) if _eval_columns().search(k)})
    if bad:
        raise SFTDataError(f"output rows would carry evaluation-column names {bad}")
    from r1.c3.evidence_boundary import is_identifiable_sweep_evidence
    if any(is_identifiable_sweep_evidence(r) for r in rows_out):
        raise SFTDataError("output rows would carry an evidence identity (label-only boundary)")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rows.jsonl").write_text("".join(_canonical(r) + "\n" for r in rows_out))
    seen = keys["train"] | keys["val"]
    test_excluded = sorted(r["proposal_id"] for r in table_rows
                           if split_of[r["instance"]] == "test" and dup_key(r) in seen)
    counts["val_full"] = counts["val"] + counts["val_seen"]
    counts["test_rows_seen_in_train_or_val"] = len(test_excluded)
    counts["labelled_test_proposals"] = sum(split_of[by_id[r["proposal_id"]]["instance"]] == "test" for r in records)
    counts["labelled_test_seen_in_train_or_val"] = sum(
        split_of[by_id[r["proposal_id"]]["instance"]] == "test" and dup_key(by_id[r["proposal_id"]]) in seen
        for r in records)
    universe_list = sorted(split_of)
    splits = {"schema": "trackp_sft_splits/v1", "config": split_cfg,
              "universe": {"schema": SPLIT_UNIVERSE_SCHEMA,
                           "source": "configured instance universe" if universe is not None
                           else "the table's instances (dry run; not a fixed universe)",
                           "n": len(universe_list),
                           "sha256": hashlib.sha256("\n".join(universe_list).encode()).hexdigest()},
              "holdout_nodes": sorted(split_cfg["holdout_nodes"]),
              "instances": {s: sorted(i for i, v in split_of.items() if v == s) for s in SPLITS},
              "cross_split_duplicates": policy,
              # heldout_excludes_seen / exclude_from_heldout: the primary test population leaves these test
              # proposals out (their (node, incumbent, candidate) also occurs on a train or val instance); the
              # secondary (full) test population keeps them. Under drop_from_train: None.
              "test_proposals_seen_in_train_or_val": test_excluded if policy != "drop_from_train" else None,
              "heldout_populations": ({"rule": "R1-TRACKP-SFT-DUP", "primary": "val rows (split val); test proposals "
                                       "not listed in test_proposals_seen_in_train_or_val",
                                       "secondary": "val and val_seen rows; every test proposal"}
                                      if policy == DECIDED_DUPLICATE_POLICY else None)}
    (out_dir / "splits.json").write_text(json.dumps(splits, indent=1, sort_keys=True) + "\n")
    labels_prov = label_source.provenance()
    audit_table = (labels_prov.get("completion") or {}).get("proposals_sha256")
    ours = ((table_record or {}).get("sha256") or {}).get("proposals.jsonl")
    matches = None if audit_table is None or ours is None else audit_table == ours
    manifest = {"schema": SFT_DATA_SCHEMA, "label_status": LABEL_STATUS, "ai_assisted": "AI-assisted (Claude)",
                "featurizer_version": FEATURIZER_VERSION, "prompt_version": PROMPT_VERSION,
                "soft_label_version": LB.soft_label_version(SIGMA_MODE), "label_seeds": list(LABEL_SEEDS),
                "table": dict(table_record or {}), "prompts": dict(prompt_record or {}),
                "labels": labels_prov, "table_matches_audit_table": matches,
                "splits_sha256": sha256_file(out_dir / "splits.json"),
                "rows_sha256": sha256_file(out_dir / "rows.jsonl"), "counts": counts}
    (out_dir / "sft_data.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def load_sft_data(data_dir: Path | str, *, secondary: bool = False) -> tuple:
    """(train rows, primary val rows, manifest) with ``prompt`` as DecisionPrompt and ``y`` as a float32 tensor; with
    ``secondary=True``, (train, primary val, val_seen, manifest): the val_seen rows complete the secondary (full) val
    population of R1-TRACKP-SFT-DUP and are never used for early stopping, temperature or selection.

    The data's duplicate policy (``splits.json`` ``config.cross_split_duplicates``; a directory without it was
    built under the earlier default ``drop_from_train``) is put in ``manifest["cross_split_duplicates"]``; a
    policy other than the decided one is refused unless the labels are synthetic (review round 1, M1)."""
    import torch
    data_dir = Path(data_dir)
    manifest = json.loads((data_dir / "sft_data.json").read_bytes())
    if manifest.get("schema") != SFT_DATA_SCHEMA:
        raise SFTDataError(f"{data_dir}: not an SFT data directory")
    blobs = {name: (data_dir / name).read_bytes() for name in ("rows.jsonl", "splits.json")}
    for name, key in (("rows.jsonl", "rows_sha256"), ("splits.json", "splits_sha256")):
        if hashlib.sha256(blobs[name]).hexdigest() != manifest[key]:
            raise SFTDataError(f"{data_dir}/{name}: sha256 differs from sft_data.json")
    if manifest.get("prompt_version") != PROMPT_VERSION or manifest.get("featurizer_version") != FEATURIZER_VERSION:
        raise SFTDataError(f"{data_dir}: built with {manifest.get('featurizer_version')} / "
                           f"{manifest.get('prompt_version')}, this code is {FEATURIZER_VERSION} / {PROMPT_VERSION}")
    policy = (json.loads(blobs["splits.json"]).get("config") or {}).get("cross_split_duplicates", "drop_from_train")
    if policy != DECIDED_DUPLICATE_POLICY and (manifest.get("labels") or {}).get("kind") != "synthetic":
        raise SFTDataError(f"{data_dir}: built with cross_split_duplicates {policy!r}; R1-TRACKP-SFT-DUP decides "
                           f"{DECIDED_DUPLICATE_POLICY!r} for real labels")
    manifest = {**manifest, "cross_split_duplicates": policy}
    out = {"train": [], "val": [], "val_seen": []}
    for line in blobs["rows.jsonl"].decode("utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["split"] not in out:
            raise SFTDataError(f"{data_dir}: row of split {r['split']!r}")
        out[r["split"]].append({"proposal_id": r["proposal_id"], "node": r["node"],
                                "prompt": prompt_from_dict(r["prompt"]),
                                "y": torch.tensor(r["y"], dtype=torch.float32)})
    if secondary:
        return out["train"], out["val"], out["val_seen"], manifest
    return out["train"], out["val"], manifest
