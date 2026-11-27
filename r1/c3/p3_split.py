"""The P3 instance split for the sweep-2 C3 analysis (PRE-SPLIT A of the signed preregistration).

AI-assisted (Claude). One generator writes one split file for both tiers; the preregistration (R1-SWEEP2-PREREG,
``docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md``) and the G.5 note cite its sha256. It reads no
table, label or evaluation value: the assignment is a function of node names, instance seeds and two salts only.

* **Instance id** (both tiers): ``<node>__s<seed>``, seed in decimal without padding
  (``sft_data.instance_universe``); it is the gate's instance id.
* **T0** (PRE-SPLIT A): over the fixed design universe — the eight T0 nodes of ``gate.T0_NODES`` × the 18 sweep
  instance seeds ``e1b_collect._instance_seed(node, k)``, k = 0..17 — per node, instances ordered by
  ``sha256("c3_p3_split/v1:" + <instance id>)``; the first 9 are test, the next 3 dev, the last 6 train. (The SFT
  builder reproduces it with ``assign_splits`` and salt ``c3_p3_split/v1``, 9 test and 3 validation per node.)
* **T1** (G5-SPLIT, quoted by PRE-SPLIT A): over the 12 G.5 instance seeds 5101–5112 per node, instances ordered by
  ``sha256("c3_t1_split/v1:" + <node> + ":" + <instance seed>)``; the first 6 test, the next 2 dev, the last 4 train.
  The file carries every node that can enter the T1 table: the seven nodes of the G.5 draft and
  ``autoresearch_fixedtokens`` (R1-TRACKG-G3-EARLY: it joins once its U2 passes). Carrying a node enrols nothing;
  a node with no labels simply has no instances in any table. **Condition** for the future G.5 amendment that adds
  ``autoresearch_fixedtokens``: to use this file it must adopt instance seeds 5101–5112 and G5-SPLIT; otherwise the
  node's instances are refused here and the node is not supplied (a second split file is a §6 STOP after the freeze).
* Missing instances drop out without reassignment (the gate reports ``off_design_size``/``off_split``); an
  instance outside the file (e.g. the B.2 cache / smoke instances ``<node>__s9011``–``__s9014``) is refused by
  ``split_of``. Callers go through ``load`` (pinned sha256 and generator equality); ``assignment`` refuses a dict that
  is not this schema, and ``split_of`` loads the pinned file itself when no assignment is passed.

**Version 2** (R1-G5-S9 (1), split A; ``c3_p3_split_v2.json``, schema ``c3_p3_split/v2``): the same generator, rule
and salts, with the four R1-T1-NODE-EXPANSION candidates added to the T1 block (``mlgym_titanic``, ``mlgym_metamaze``,
``gc7rc_etth1``, ``gc7rc_forestcover``). The ``t0`` block and the eight v1 T1 node entries are byte-identical to v1
(``test_p3_split`` checks it entry by entry), so no instance of an existing node moves. The split is label-free and
deterministic, so v2 lists every candidate now; its ``t1.membership`` block gives each T1 node a **static** role, suite
and supply rule, never a status that changes with a run (the file's bytes stay fixed):

* ``g5_note`` (the eight v1 nodes): labelled under the signed G.5 note; supplied to the arms and the gate.
* ``g5_addendum_mlgym`` (``mlgym_titanic``, ``mlgym_metamaze``): suite MLGym; labelled only through its G.5 addendum
  note, which needs the node's G.1b determinism PASS (R1-STEP-ORDER (2)(a)); supplied to the arms and the gate only
  with its G.5 labels, i.e. after that addendum (R1-G5-S9 (2)-(3)).
* ``g5_addendum_extra_task`` (``gc7rc_etth1``, ``gc7rc_forestcover``): no suite (R1-1GC-FALLBACK); labelled through its
  addendum but **never** supplied to the arms or the gate; reported per node as an extra task. ``arms_freeze`` and
  ``sft_data`` refuse such a node (fail closed).

Both files stay admissible wherever a split file is pinned (``SPLIT_FILES``): v1 is v2 restricted to the v1 nodes, so a
record, receipt or note that cites v1 (the frozen preregistration's block, the signed G.5 note's ``instance_split``, the
train/dev receipts, the P.4 phase-1 spec) keeps its meaning. ``load(path)`` accepts either file by its sha256 and
compares it with the generator output of its version; ``DEFAULT_PATH`` stays v1, so a caller that names no file is
unchanged. A consumer that needs a joining node names v2 (``V2_PATH``, ``load_pinned``).

``python -m r1.c3.p3_split write <path> [--version 2]`` writes a file; ``verify <path>`` regenerates the version its
bytes' sha256 names and compares bytes and the pinned sha256 (``SPLIT_FILES``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "c3_p3_split/v1"
SCHEMA_V2 = "c3_p3_split/v2"
SCHEMAS = {1: SCHEMA, 2: SCHEMA_V2}
T0_SALT = "c3_p3_split/v1"
T1_SALT = "c3_t1_split/v1"
SPLITS = ("test", "dev", "train")
# gate.T0_NODES (r1/c3/gate.py v3.1), copied so this module imports nothing from the gate; a test checks equality
T0_NODES = ('digits_mlp', 'openml_breast_w', 'openml_climate', 'openml_credit_approval', 'openml_ionosphere', 'openml_sonar', 'openml_wdbc', 'tabular_mlp')
T0_INSTANCES_PER_NODE = 18
T0_COUNTS = {"test": 9, "dev": 3, "train": 6}
# G.5 T1 nodes (draft rev 6, R1-TRACKG-G3-EARLY) and the node that joins after its U2 (R1-TRACKG-AR-U2-TASL2);
# autoresearch_fixedtokens is usable only if its G.5 amendment adopts seeds 5101-5112 and G5-SPLIT (module docstring)
T1_NODES_V1 = ("mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist",
               "mlgym_breakout_minatar", "mlgym_houseprice", "autoresearch_fixedtokens")
# R1-G5-S9 (2): the R1-T1-NODE-EXPANSION candidates (sweep2/t1_tasl/g1b_tasl_x_spec.json), in v2 only. The MLGym ones
# enter the arms and the gate as suite MLGym after their G.5 addendum; the 1GC ones are extra tasks, never supplied.
T1_EXPANSION_MLGYM = ("mlgym_titanic", "mlgym_metamaze")
T1_EXTRA_TASKS = ("gc7rc_etth1", "gc7rc_forestcover")
T1_NODES = T1_NODES_V1 + T1_EXPANSION_MLGYM + T1_EXTRA_TASKS      # every node of v2's T1 block (may carry G.5 labels)
T1_SUPPLY_NODES = T1_NODES_V1 + T1_EXPANSION_MLGYM                # the T1 nodes that may reach the arms and the gate
# The gate.SUITES name of each T1 node (None: no suite, R1-1GC-FALLBACK); g5_features.T1_NODE_INFO agrees (tested)
T1_SUITES = {"mlab_cifar10": "MLAgentBench", "mlab_imdb": "MLAgentBench", "mlab_ogbn_arxiv": "MLAgentBench",
             "mlgym_cifar10": "MLGym", "mlgym_fmnist": "MLGym", "mlgym_breakout_minatar": "MLGym",
             "mlgym_houseprice": "MLGym", "autoresearch_fixedtokens": "autoresearch",
             "mlgym_titanic": "MLGym", "mlgym_metamaze": "MLGym", "gc7rc_etth1": None, "gc7rc_forestcover": None}
ROLES = {"g5_note": "labelled under the signed G.5 note; supplied to the arms and the gate",
         "g5_addendum_mlgym": "labelled only through its G.5 addendum note, after its G.1b determinism PASS "
                              "(R1-STEP-ORDER (2)(a)); supplied to the arms and the gate as suite MLGym only with those "
                              "labels (R1-G5-S9 (2)-(3))",
         "g5_addendum_extra_task": "labelled through its G.5 addendum note; never supplied to the arms or the gate; "
                                   "reported per node as an extra task (R1-G5-S9 (2), R1-1GC-FALLBACK)"}
SUPPLY = {"g5_note": "arms_and_gate", "g5_addendum_mlgym": "arms_and_gate_after_g5_addendum",
          "g5_addendum_extra_task": "never"}
T1_SEEDS = tuple(range(5101, 5113))
T1_COUNTS = {"test": 6, "dev": 2, "train": 4}
SPLITS_DIR = Path(__file__).resolve().parent / "splits"
V1_REL = "r1/c3/splits/c3_p3_split_v1.json"
V2_REL = "r1/c3/splits/c3_p3_split_v2.json"
DEFAULT_PATH = SPLITS_DIR / "c3_p3_split_v1.json"
V2_PATH = SPLITS_DIR / "c3_p3_split_v2.json"
P3_SPLIT_SHA256 = "b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569"   # v1, the committed file; test_p3_split checks it
P3_SPLIT_V2_SHA256 = "4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a"   # v2 (R1-G5-S9 (1)), the committed file; test_p3_split checks it
SPLIT_FILES = {1: {"path": V1_REL, "sha256": P3_SPLIT_SHA256}, 2: {"path": V2_REL, "sha256": P3_SPLIT_V2_SHA256}}
VERSION_OF_SHA = {v["sha256"]: k for k, v in SPLIT_FILES.items()}


class SplitError(ValueError):
    """A refusal: a file that is not the pinned split, or an instance outside it."""


def t0_instance_seed(node: str, k: int) -> int:
    """``e1b_collect._instance_seed`` (copied: that module imports the harness); a test checks equality."""
    return 100 + 10 * k + (sum(map(ord, node)) % 7)


def instance_id(node: str, seed: int) -> str:
    return f"{node}__s{int(seed)}"


def _ordered(items: list[tuple[str, str]]) -> list[str]:
    """(instance id, hashed string) pairs ordered by sha256 of the hashed string; returns the ids."""
    return [i for i, _ in sorted(items, key=lambda p: hashlib.sha256(p[1].encode()).hexdigest())]


def _partition(order: list[str], counts: dict) -> dict:
    n_test, n_dev = counts["test"], counts["dev"]
    if len(order) != sum(counts.values()):
        raise SplitError(f"{len(order)} instances for counts {counts}")
    return {"test": order[:n_test], "dev": order[n_test:n_test + n_dev], "train": order[n_test + n_dev:]}


def role_of(node: str) -> str:
    """The static role of a T1 node in v2's ``t1.membership`` (module docstring)."""
    if node in T1_NODES_V1:
        return "g5_note"
    if node in T1_EXPANSION_MLGYM:
        return "g5_addendum_mlgym"
    if node in T1_EXTRA_TASKS:
        return "g5_addendum_extra_task"
    raise SplitError(f"{node} is not a T1 node of the split files")


def build(version: int = 1) -> dict:
    if version not in SCHEMAS:
        raise SplitError(f"no split file version {version!r}")
    t1_nodes = T1_NODES_V1 if version == 1 else T1_NODES
    t0 = {}
    for node in T0_NODES:
        ids = [instance_id(node, t0_instance_seed(node, k)) for k in range(T0_INSTANCES_PER_NODE)]
        if len(set(ids)) != len(ids):
            raise SplitError(f"duplicate T0 instance seeds for {node}")
        t0[node] = _partition(_ordered([(i, f"{T0_SALT}:{i}") for i in ids]), T0_COUNTS)
    t1 = {}
    for node in t1_nodes:
        t1[node] = _partition(_ordered([(instance_id(node, s), f"{T1_SALT}:{node}:{s}") for s in T1_SEEDS]),
                              T1_COUNTS)
    out = {
        "schema": SCHEMAS[version],
        "label": "P3 instance split of the sweep-2 C3 analysis (PRE-SPLIT A); node names, seeds and salts only",
        "preregistration": "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md (R1-SWEEP2-PREREG)",
        "instance_id": "<node>__s<seed> (seed decimal, no padding); the gate's instance id",
        "missing_instances": "drop out without reassignment; reported by the gate (off_design_size, off_split)",
        "t0": {"rule": "per node, order by sha256('c3_p3_split/v1:' + <instance id>); first 9 test, next 3 dev, "
                       "last 6 train",
               "salt": T0_SALT, "counts": T0_COUNTS,
               "seeds": "e1b_collect._instance_seed(node, k) = 100 + 10k + (sum(ord(c) for c in node) mod 7), "
                        "k = 0..17",
               "nodes": t0},
        "t1": {"rule": "per node, order by sha256('c3_t1_split/v1:' + <node> + ':' + <instance seed>); first 6 "
                       "test, next 2 dev, last 4 train (G5-SPLIT)",
               "salt": T1_SALT, "counts": T1_COUNTS, "seeds": "5101-5112", "nodes": t1},
    }
    if version == 2:
        out["label"] = ("P3 instance split of the sweep-2 C3 analysis (PRE-SPLIT A as amended by R1-G5-S9 (1)), "
                        "version 2; node names, seeds and salts only")
        out["supersedes"] = {"path": V1_REL, "sha256": P3_SPLIT_SHA256,
                             "identity": "the t0 block and the t1 entries of the eight v1 nodes are byte-identical to "
                                         "v1; v1 is this file restricted to the v1 nodes"}
        out["t1"]["membership"] = {n: {"role": role_of(n), "suite": T1_SUITES[n], "supply": SUPPLY[role_of(n)]}
                                   for n in t1_nodes}
        out["t1"]["roles"] = dict(ROLES)
        out["t1"]["role_authority"] = ("R1-G5-S9 (author, 27 Nov 2026): split A, gate a; R1-STEP-ORDER (2)(a); "
                                       "R1-1GC-FALLBACK. The roles are static: whether a node's G.1b passed or its "
                                       "addendum exists is read from those records, never from this file")
    return out


def render(split: dict) -> bytes:
    return (json.dumps(split, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path | str = DEFAULT_PATH, *, sha256: str | None = None) -> dict:
    """The split file, refused unless its bytes have a pinned sha256 (``sha256`` if given, else either version's in
    ``SPLIT_FILES``) and equal the generator's output of that version."""
    raw = Path(path).read_bytes()
    got = sha256_bytes(raw)
    want = {sha256} if sha256 else set(VERSION_OF_SHA)
    if got not in want:
        raise SplitError(f"{path} is not the pinned P3 split file (sha256 {got[:12]}…, "
                         f"want {' or '.join(sorted(w[:12] + '…' for w in want))})")
    version = VERSION_OF_SHA.get(got)
    if version is None or raw != render(build(version)):
        raise SplitError(f"{path} does not equal the generator's output")
    return json.loads(raw)


def version_of(split: dict) -> int:
    """1 or 2: the version of a loaded split file (refused if the dict is neither schema)."""
    for v, schema in SCHEMAS.items():
        if isinstance(split, dict) and split.get("schema") == schema:
            return v
    raise SplitError(f"not a {SCHEMA} or {SCHEMA_V2} split (use load())")


def load_pinned(pin) -> dict:
    """The split file named by ``pin`` = {path, sha256}, which must be one entry of ``SPLIT_FILES``."""
    if not isinstance(pin, dict) or set(pin) != {"path", "sha256"} or dict(pin) not in SPLIT_FILES.values():
        raise SplitError(f"{pin!r} is not a pinned P3 split file {list(SPLIT_FILES.values())}")
    return load(SPLITS_DIR.parents[2] / pin["path"], sha256=pin["sha256"])


def pin_of_sha(sha256: str) -> dict:
    """The ``SPLIT_FILES`` entry {path, sha256} with this sha256 (refused otherwise)."""
    if sha256 not in VERSION_OF_SHA:
        raise SplitError(f"sha256 {str(sha256)[:12]}… is not a pinned P3 split file")
    return dict(SPLIT_FILES[VERSION_OF_SHA[sha256]])


def pin_for_nodes(nodes) -> dict:
    """The split file a document over these nodes names: v1 when every node is in v1 (its meaning unchanged), else
    v2. A node in neither is refused."""
    nodes = set(nodes)
    unknown = sorted(nodes - set(T0_NODES) - set(T1_NODES))
    if unknown:
        raise SplitError(f"{unknown} are in no split file")
    return dict(SPLIT_FILES[1 if nodes <= set(T0_NODES) | set(T1_NODES_V1) else 2])


def assignment(split: dict) -> dict[str, dict]:
    """{instance id: {"tier", "node", "split"}} over both tiers. ``split`` must come from ``load``."""
    version_of(split)
    out = {}
    for tier in ("t0", "t1"):
        for node, parts in split[tier]["nodes"].items():
            for part in SPLITS:
                for inst in parts[part]:
                    if inst in out:
                        raise SplitError(f"{inst} appears twice in the split file")
                    out[inst] = {"tier": tier.upper(), "node": node, "split": part}
    return out


def split_of(assign: dict | None, inst: str) -> str:
    """The split of one instance; an instance outside the file is refused (never reassigned).

    ``assign`` is ``assignment(load(...))``; with None the pinned default file is loaded."""
    if assign is None:
        assign = assignment(load())
    if inst not in assign:
        raise SplitError(f"instance {inst!r} is not in the P3 split file")
    return assign[inst]["split"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write"); w.add_argument("path")
    w.add_argument("--version", type=int, default=1, choices=sorted(SCHEMAS))
    v = sub.add_parser("verify"); v.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    a = ap.parse_args(argv)
    if a.cmd == "write":
        raw = render(build(a.version))
        Path(a.path).parent.mkdir(parents=True, exist_ok=True)
        Path(a.path).write_bytes(raw)
        print(sha256_bytes(raw))
        return 0
    try:
        load(a.path)
    except SplitError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"OK {sha256_bytes(Path(a.path).read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
