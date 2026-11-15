"""Seed registry generated from code (build runbook P2; plan §11.1). ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 15 Nov 2026).

Paper B's seed blocks are read from the code at recorded pins with ``git show <pin>:<path>`` and ``ast``. No module
is imported. Every block is a half-open integer range [lo, hi). Paper B uses one integer namespace for worker seeds:
instance seeds, audit seeds and noise-floor seeds are all passed to the worker as train/split seeds. The registry
therefore treats every block as global, never per node.

A seed defined by a formula is bounded by enumerating a declared domain:

* ``e1b_collect._instance_seed(node, k) = 100 + 10 k + (sum(map(ord, node)) % 7)``. Node names enter only through a
  residue mod 7, so the bound is taken over seven synthetic names that cover every residue, for k < ``K_DOMAIN``
  (90: the largest domain whose seeds stay below the next Paper B block at 1001; a Paper B run with >= 90
  instances per node would collide with the noise-floor seeds, which ``paper_b_overlaps`` would then report).
* Base + count blocks whose count is a run-time argument (noise-floor ``SEED_BASE``, E1b ``AUDIT_SEED_BASE``) are
  bounded by the spacing of their bases (1000), the code's own layout.

Entries that the plan's prose names but no code at the pins defines are recorded with ``kind = "prose_only"`` and
reserved conservatively; ``SEED_REGISTRY_CHECK_20261115.md`` lists them.

Paper C's own blocks (``PAPER_C_BLOCKS``) are a proposal for the author; ``check_disjoint`` asserts that they
intersect no Paper B block, with a margin.

Run ``python -m paperc.seeds`` from the repository root to regenerate ``paperC/seeds/registry_v1.json``.
"""
from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REGISTRY_SCHEMA = "paperc_seed_registry/v1"
OUT = Path(__file__).resolve().parents[2] / "seeds" / "registry_v1.json"

CANONICAL = "d4ea56c101e2f127c75dd49a22e758a24c7e1596"   # origin/author-qtorch-20261115 (latest PLAN on 15 Nov)
TRACKS = "fab88fced839c5fb794ed62a0742b4646cb76ea2"      # origin/trackS-ops-20261030 (Track S code on 15 Nov)

K_DOMAIN = 90            # e1b instance index k: largest k whose seeds stay below the next Paper B block (1001);
                         # sweeps use k < 18 (config 'instances': 18), liveness k < 2
COUNT_DOMAIN = 1000      # declared domain for base + count blocks (bases are spaced 1000 apart)
MARGIN = 1000            # minimum gap between a Paper C block and any Paper B block


@dataclass(frozen=True)
class Block:
    name: str
    lo: int
    hi: int              # exclusive
    kind: str            # "literal" | "formula" | "base_count" | "prose_only" | "proposal"
    ref: str | None      # commit the value was read from
    path: str | None
    symbol: str | None
    note: str = ""

    def __contains__(self, seed: int) -> bool:
        return self.lo <= seed < self.hi


# Paper C proposal (author to confirm): instances, audit seeds, and RNG keys for design draws.
PAPER_C_BLOCKS = (
    Block("paperc_instances", 50_000, 60_000, "proposal", None, None, None,
          "campaign instance seeds; splits (train/dev/test) are sub-blocks fixed in SPT-0"),
    Block("paperc_rng_keys", 60_000, 61_000, "proposal", None, None, None,
          "keys for fork selection, epsilon draws and other design randomness (not worker seeds)"),
    Block("paperc_audits", 1_000_000, 2_000_000, "proposal", None, None, None,
          "fresh audit seeds; per-instance stride as in Track S"),
)
PAPER_C_CAMPAIGN_PREFIX = "pc-"   # D26 manager seeds hash the campaign id; this prefix keeps them disjoint


# ---------------------------------------------------------------- reading code at a pin

def git_show(repo: Path, ref: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], check=True, capture_output=True,
                          text=True).stdout


def _assignments(src: str) -> dict[str, ast.expr]:
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            out[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            out[node.target.id] = node.value
    return out


def _eval(expr: ast.expr, env: dict):
    """Literals, names bound earlier in the same file, ``range``/``tuple``/``list`` calls and +, -, * on ints."""
    if isinstance(expr, ast.Constant):
        return expr.value
    if isinstance(expr, ast.Name):
        if expr.id in env:
            return env[expr.id]
        raise ValueError(f"unbound name {expr.id}")
    if isinstance(expr, (ast.Tuple, ast.List)):
        return [_eval(e, env) for e in expr.elts]
    if isinstance(expr, ast.Dict):
        return {_eval(k, env): _eval(v, env) for k, v in zip(expr.keys, expr.values)}
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, (ast.Add, ast.Sub, ast.Mult)):
        a, b = _eval(expr.left, env), _eval(expr.right, env)
        return a + b if isinstance(expr.op, ast.Add) else a - b if isinstance(expr.op, ast.Sub) else a * b
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id in ("range", "tuple", "list"):
        args = [_eval(a, env) for a in expr.args]
        if expr.func.id == "range":
            return range(*args)
        return list(args[0])
    raise ValueError(f"unsupported expression {ast.dump(expr)[:80]}")


def constants(src: str, names: Iterable[str]) -> dict:
    assigns, env = _assignments(src), {}
    for n, e in assigns.items():         # evaluate in file order, keeping what can be evaluated
        try:
            env[n] = _eval(e, env)
        except ValueError:
            pass
    missing = [n for n in names if n not in env]
    if missing:
        raise KeyError(f"constants not found or not literal: {missing}")
    return {n: env[n] for n in names}


def function(src: str, name: str):
    """Compile one top-level pure function from its own AST (the module is not imported)."""
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            mod = ast.Module(body=[node], type_ignores=[])
            ns: dict = {"__builtins__": {"sum": sum, "map": map, "ord": ord}}
            exec(compile(mod, f"<{name}>", "exec"), ns)
            return ns[name]
    raise KeyError(f"function {name} not found")


# ---------------------------------------------------------------- Paper B blocks

def paper_b_blocks(repo: Path) -> list[Block]:
    blocks: list[Block] = []

    # Track S (collect.py at the Track S pin)
    p = "r1/tracks/collect.py"
    c = constants(git_show(repo, TRACKS, p),
                  ["INSTANCE_SEED_BLOCKS", "AUDIT_SEED_BASES", "AUDIT_BLOCK_CAPACITY", "SELECTION_SEED"])
    for phase, (lo, hi) in c["INSTANCE_SEED_BLOCKS"].items():
        blocks.append(Block(f"tracks_instances_{phase}", lo, hi, "literal", TRACKS, p, "INSTANCE_SEED_BLOCKS"))
    for phase, base in c["AUDIT_SEED_BASES"].items():
        blocks.append(Block(f"tracks_audits_{phase}", base, base + c["AUDIT_BLOCK_CAPACITY"], "literal", TRACKS, p,
                            "AUDIT_SEED_BASES + AUDIT_BLOCK_CAPACITY"))
    s = c["SELECTION_SEED"]
    blocks.append(Block("tracks_selection_key", s, s + 1, "literal", TRACKS, p, "SELECTION_SEED",
                        "RNG key for fork selection, not a worker seed; reserved anyway"))

    # Campaign instance seeds of the E1b collector (sweeps, liveness, E1b pilot)
    p = "r1/headroom/e1b_collect.py"
    src = git_show(repo, CANONICAL, p)
    f = function(src, "_instance_seed")
    names = ["a" * i for i in range(1, 8)]                       # sum(map(ord, name)) % 7 takes every residue
    assert {sum(map(ord, n)) % 7 for n in names} == set(range(7))
    vals = [f(n, k) for n in names for k in range(K_DOMAIN)]
    blocks.append(Block("e1b_instances", min(vals), max(vals) + 1, "formula", CANONICAL, p, "_instance_seed",
                        f"k < {K_DOMAIN} over all node-name residues mod 7 (bounded by the next block at 1001); "
                        "sweeps use k < 18 (seeds 100..276)"))
    base = constants(src, ["AUDIT_SEED_BASE"])["AUDIT_SEED_BASE"]
    blocks.append(Block("e1b_leaf_audits", base, base + COUNT_DOMAIN, "base_count", CANONICAL, p, "AUDIT_SEED_BASE",
                        "AUDIT_SEED_BASE + i, i < k_audit (run-time); E1b used 5001..5006"))

    # Noise floor (C1 tables)
    p = "r1/noise/e1_noise_floor.py"
    bases = constants(git_show(repo, CANONICAL, p), ["SEED_BASE"])["SEED_BASE"]
    for cond, b in bases.items():
        blocks.append(Block(f"noise_floor_{cond}", b, b + COUNT_DOMAIN, "base_count", CANONICAL, p,
                            f"SEED_BASE[{cond!r}]", "SEED_BASE + s, s < n_seeds (run-time; C1 uses 30)"))

    # C3 fresh-seed audits
    p = "r1/c3/audit.py"
    seeds = constants(git_show(repo, CANONICAL, p), ["DEFAULT_SEEDS"])["DEFAULT_SEEDS"]
    blocks.append(Block("c3_audits", min(seeds), max(seeds) + 1, "literal", CANONICAL, p, "DEFAULT_SEEDS"))

    # Track X exam namespace
    p = "r1/exam/namespace.py"
    c = constants(git_show(repo, CANONICAL, p), ["INSTANCE_SEEDS", "AUDIT_SEEDS"])
    blocks.append(Block("exam_instances", c["INSTANCE_SEEDS"].start, c["INSTANCE_SEEDS"].stop, "literal", CANONICAL,
                        p, "INSTANCE_SEEDS"))
    blocks.append(Block("exam_audits", c["AUDIT_SEEDS"].start, c["AUDIT_SEEDS"].stop, "literal", CANONICAL, p,
                        "AUDIT_SEEDS"))

    # Named in the plan's prose (§11.1) but not defined in code at these pins
    blocks.append(Block("trackg_g1b_audits", 8001, 8011, "prose_only", None, None, None,
                        "plan §11.1 'G.1b 8001–8010'; not found in code at the pins; reserved conservatively"))
    return sorted(blocks, key=lambda b: (b.lo, b.name))


# ---------------------------------------------------------------- registry

def check_disjoint(paper_b: Iterable[Block], paper_c: Iterable[Block] = PAPER_C_BLOCKS,
                   margin: int = MARGIN) -> list[str]:
    errs = []
    for c in paper_c:
        for b in paper_b:
            if c.lo < b.hi + margin and b.lo < c.hi + margin:
                errs.append(f"{c.name} [{c.lo},{c.hi}) is within {margin} of {b.name} [{b.lo},{b.hi})")
    return errs


def paper_b_overlaps(paper_b: Iterable[Block]) -> list[str]:
    """Overlaps among Paper B's own blocks (a property of Paper B, reported, not fixed here)."""
    bs = sorted(paper_b, key=lambda b: b.lo)
    return [f"{a.name} [{a.lo},{a.hi}) overlaps {b.name} [{b.lo},{b.hi})"
            for i, a in enumerate(bs) for b in bs[i + 1:] if b.lo < a.hi]


def build_registry(repo: Path) -> dict:
    pb = paper_b_blocks(repo)
    errs = check_disjoint(pb)
    if errs:
        raise RuntimeError("STOP: Paper C blocks collide with Paper B: " + "; ".join(errs))
    return {
        "schema": REGISTRY_SCHEMA,
        "pins": {"canonical": CANONICAL, "tracks": TRACKS},
        "domains": {"K_DOMAIN": K_DOMAIN, "COUNT_DOMAIN": COUNT_DOMAIN, "MARGIN": MARGIN},
        "paper_b": [asdict(b) for b in pb],
        "paper_c": [asdict(b) for b in PAPER_C_BLOCKS],
        "paper_c_campaign_prefix": PAPER_C_CAMPAIGN_PREFIX,
        "paper_b_internal_overlaps": paper_b_overlaps(pb),
    }


def dumps(reg: dict) -> str:
    return json.dumps(reg, indent=2, sort_keys=True) + "\n"


class Registry:
    """Implements ``paperc.schema.SeedRegistry``."""

    def __init__(self, data: dict):
        if data.get("schema") != REGISTRY_SCHEMA:
            raise ValueError("not a Paper C seed registry")
        self.paper_b = [Block(**b) for b in data["paper_b"]]
        self.paper_c = [Block(**b) for b in data["paper_c"]]

    @classmethod
    def load(cls, path: Path = OUT) -> "Registry":
        return cls(json.loads(Path(path).read_text()))

    def paper_b_block(self, node: str, instance_seed: int) -> str | None:   # node unused: one global namespace
        for b in self.paper_b:
            if instance_seed in b:
                return b.name
        return None

    def paper_c_block(self, seed: int) -> str | None:
        for b in self.paper_c:
            if seed in b:
                return b.name
        return None


def main(repo: Path | None = None) -> Path:
    repo = repo or Path(__file__).resolve().parents[3]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dumps(build_registry(repo)))
    return OUT


if __name__ == "__main__":
    print(main())
