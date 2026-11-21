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
  a node with no labels simply has no instances in any table.
* Missing instances drop out without reassignment (the gate reports ``off_design_size``/``off_split``); an
  instance outside the file is refused by ``load`` users (``assignment``).

``python -m r1.c3.p3_split write <path>`` writes the file; ``verify <path>`` regenerates it and compares bytes and
the pinned sha256 (``P3_SPLIT_SHA256``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "c3_p3_split/v1"
T0_SALT = "c3_p3_split/v1"
T1_SALT = "c3_t1_split/v1"
SPLITS = ("test", "dev", "train")
# gate.T0_NODES (r1/c3/gate.py v3.1), copied so this module imports nothing from the gate; a test checks equality
T0_NODES = ('digits_mlp', 'openml_breast_w', 'openml_climate', 'openml_credit_approval', 'openml_ionosphere', 'openml_sonar', 'openml_wdbc', 'tabular_mlp')
T0_INSTANCES_PER_NODE = 18
T0_COUNTS = {"test": 9, "dev": 3, "train": 6}
# G.5 T1 nodes (draft rev 6, R1-TRACKG-G3-EARLY) and the node that joins after its U2 (R1-TRACKG-AR-U2-TASL2)
T1_NODES = ("mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist",
            "mlgym_breakout_minatar", "mlgym_houseprice", "autoresearch_fixedtokens")
T1_SEEDS = tuple(range(5101, 5113))
T1_COUNTS = {"test": 6, "dev": 2, "train": 4}
DEFAULT_PATH = Path(__file__).resolve().parent / "splits" / "c3_p3_split_v1.json"
P3_SPLIT_SHA256 = "b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569"   # the committed file; test_p3_split checks it


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
    assert len(order) == sum(counts.values())
    return {"test": order[:n_test], "dev": order[n_test:n_test + n_dev], "train": order[n_test + n_dev:]}


def build() -> dict:
    t0 = {}
    for node in T0_NODES:
        ids = [instance_id(node, t0_instance_seed(node, k)) for k in range(T0_INSTANCES_PER_NODE)]
        if len(set(ids)) != len(ids):
            raise SplitError(f"duplicate T0 instance seeds for {node}")
        t0[node] = _partition(_ordered([(i, f"{T0_SALT}:{i}") for i in ids]), T0_COUNTS)
    t1 = {}
    for node in T1_NODES:
        t1[node] = _partition(_ordered([(instance_id(node, s), f"{T1_SALT}:{node}:{s}") for s in T1_SEEDS]),
                              T1_COUNTS)
    return {
        "schema": SCHEMA,
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


def render(split: dict) -> bytes:
    return (json.dumps(split, indent=1, sort_keys=True, ensure_ascii=True) + "\n").encode()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path | str = DEFAULT_PATH, *, sha256: str | None = None) -> dict:
    """The split file, refused unless its bytes have the pinned sha256 (``P3_SPLIT_SHA256`` by default) and equal
    the generator's output."""
    raw = Path(path).read_bytes()
    want = sha256 or P3_SPLIT_SHA256
    if sha256_bytes(raw) != want:
        raise SplitError(f"{path} is not the pinned P3 split file (sha256 {sha256_bytes(raw)[:12]}…, "
                         f"want {want[:12]}…)")
    if raw != render(build()):
        raise SplitError(f"{path} does not equal the generator's output")
    return json.loads(raw)


def assignment(split: dict) -> dict[str, dict]:
    """{instance id: {"tier", "node", "split"}} over both tiers."""
    out = {}
    for tier in ("t0", "t1"):
        for node, parts in split[tier]["nodes"].items():
            for part in SPLITS:
                for inst in parts[part]:
                    if inst in out:
                        raise SplitError(f"{inst} appears twice in the split file")
                    out[inst] = {"tier": tier.upper(), "node": node, "split": part}
    return out


def split_of(assign: dict, inst: str) -> str:
    """The split of one instance; an instance outside the file is refused (never reassigned)."""
    if inst not in assign:
        raise SplitError(f"instance {inst!r} is not in the P3 split file")
    return assign[inst]["split"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write"); w.add_argument("path")
    v = sub.add_parser("verify"); v.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    a = ap.parse_args(argv)
    raw = render(build())
    if a.cmd == "write":
        Path(a.path).parent.mkdir(parents=True, exist_ok=True)
        Path(a.path).write_bytes(raw)
        print(sha256_bytes(raw))
        return 0
    try:
        load(a.path)
    except SplitError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"OK {sha256_bytes(raw)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
