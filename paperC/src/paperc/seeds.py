"""Seed registry generated from code (build runbook P2; plan §11.1). ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 15-16 Nov 2026; revised after review round 1).

Paper B's seed blocks are read from the code at two recorded pins with ``git show <pin>:<path>`` and ``ast``; no
module is imported. Every block is a half-open integer range [lo, hi). The sources are declared in ``SOURCES``
(worker-seed blocks) and ``RNG_KEYS`` (RNG roots), and ``paper_b_blocks`` reads exactly those.

**Namespace.** Worker seeds (train / split seeds passed to a node's run: instance seeds, audit seeds, noise-floor
seeds, the harness nodes' default seed) form one integer namespace across Paper B, and the registry treats every
worker-seed block as global, never per node: a Paper C run on the same node, configuration and seed would repeat a
Paper B measurement. RNG roots of the simulators, the bootstrap and the samplers are registered too (``RNG_KEYS``),
so no Paper C block contains one. Outside the registry's scope, and stated here so the omission is deliberate:

* D26 manager seeds: a 32-bit hash of (campaign id, budget index, repetition, revision). Paper C keeps the *inputs*
  disjoint through the campaign-id prefix ``pc-`` (Track S builds ``tracks_{node}__s{seed}``); the 32-bit outputs
  could collide only by hash chance. The Paper C runner must use ``pc-`` ids, and ``check_campaign`` enforces the
  prefix when given this registry;
* ML training seeds (Track P uses 0-2) and small RNG defaults (``seed=0``): they seed optimisers and samplers, not
  node runs, so they cannot repeat a measurement. Paper C reserves ``paperc_train_seeds`` for its own (SPT-5).

**Bounds.** A seed defined by a formula is bounded by enumerating a *declared* domain; the code itself puts no upper
bound on ``--instances``, ``--seeds`` or ``--audit-seeds``:

* ``e1b_collect._instance_seed(node, k) = 100 + 10 k + (sum(map(ord, node)) % 7)``, enumerated for k < ``K_DOMAIN``
  = 90 over seven names covering every residue mod 7 (90 is the largest k whose seeds stay below the next block at
  1001; sweeps use k < 18);
* base + count blocks with a run-time count are bounded by ``COUNT_DOMAIN`` = 1000, the spacing of their bases.

**Completeness.** ``scan_constants`` reads, in every non-test ``r1/**/*.py`` at both pins, (a) every module-level
constant whose name contains ``SEED`` or ends in ``_BASE(S)``, (b) every integer passed as a worker-seed keyword
(``train_seed``, ``split_seed``, ``instance_seed``, ``worker_seed``, ``audit_seed(s)``), and (c) every integer >= 10
used as the default or keyword of any seed-named parameter, as an argparse ``--*seed*`` default, or as the first
argument of an RNG constructor. ``unaccounted`` requires every such integer (every *range* in full,
not only its ends) to lie in a registry block or to be on ``IGNORED`` with a reason; string-valued constants (file
names, key sets) are listed as skipped. The test requires ``unaccounted`` to be empty.

Run ``python -m paperc.seeds`` from the repository root to regenerate ``paperC/seeds/registry_v1.json``.
"""
from __future__ import annotations

import __future__ as _future
import ast
import copy
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

REGISTRY_SCHEMA = "paperc_seed_registry/v1"
OUT = Path(__file__).resolve().parents[2] / "seeds" / "registry_v1.json"

CANONICAL = "d4ea56c101e2f127c75dd49a22e758a24c7e1596"   # origin/author-qtorch-20261115 (latest PLAN on 15 Nov)
TRACKS = "fab88fced839c5fb794ed62a0742b4646cb76ea2"      # origin/trackS-ops-20261030 (Track S code on 15 Nov)

K_DOMAIN = 90            # declared domain of the e1b instance index k
COUNT_DOMAIN = 1000      # declared domain of run-time counts in base + count blocks
MARGIN = 1000            # minimum gap between a Paper C block and any Paper B block


@dataclass(frozen=True)
class Block:
    name: str
    lo: int
    hi: int              # exclusive
    kind: str            # "literal" | "formula" | "base_count" | "rng_key" | "prose_only" | "external" | "proposal"
    ref: str | None      # commit the value was read from
    path: str | None
    symbol: str | None
    note: str = ""

    def __contains__(self, seed: int) -> bool:
        return self.lo <= seed < self.hi


PAPER_C_BLOCKS = (
    Block("paperc_instances", 50_000, 60_000, "proposal", None, None, None,
          "campaign instance seeds (also worker seeds); train/dev/test sub-blocks fixed in SPT-0"),
    Block("paperc_rng_keys", 60_000, 61_000, "proposal", None, None, None,
          "keys for fork selection, epsilon draws and other design randomness (not worker seeds)"),
    Block("paperc_train_seeds", 61_000, 62_000, "proposal", None, None, None,
          "seeds of Paper C's own model training (SPT-5): optimisers and samplers, not node runs"),
    Block("paperc_audits", 10_000_000, 11_000_000, "proposal", None, None, None,
          "fresh audit seeds; per-instance stride as in Track S (above Track S's oracle blocks 1e6-3e6, below the "
          "date-valued RNG keys)"),
)
PAPER_C_CAMPAIGN_PREFIX = "pc-"
PAPER_C_ROLES = {"instance": "paperc_instances", "worker": "paperc_instances", "eps": "paperc_rng_keys",
                 "audit": "paperc_audits", "train": "paperc_train_seeds"}

# Claims inside the Paper C blocks (added 16 Nov 2026 with build runbook P3, review P3 finding 7). A later phase
# that draws from the same block takes a different key.
PAPER_C_CLAIMS = (
    {"name": "esyn_rng_root", "block": "paperc_rng_keys", "value": 60_001, "phase": "P3",
     "use": "E-SYN campaign generator: SeedSequence([60001, world code, i]). Recorded campaigns: instance_seed "
            "50000 + i (audit seeds 10,000,000 + n_audit i are nominal labels). The index ranges below are "
            "numerically inside Paper B's tracks_oracle_* ranges, but they enter only this Paper C root key, so "
            "their streams are disjoint from Track S's.",
     "index_ranges": {"recorded": [0, 10_000], "p3_selection": [1_000_000, 2_000_000],
                      "p3_evaluation": [2_000_000, 3_000_000], "p3_decomposition": [3_000_000, 4_000_000],
                      "p4_dev": [4_000_000, 5_000_000], "p4_test": [5_000_000, 6_000_000]}},
    {"name": "esyn_decision_uniforms", "block": "paperc_rng_keys", "value": 60_002, "phase": "P4",
     "use": "per-decision uniforms of stochastic E-SYN policies: SeedSequence([60002, world code, i, step]); logged as "
            "eps_seed so that check_campaign replays the policy."},
    {"name": "esyn_fork_design", "block": "paperc_rng_keys", "value": 60_003, "phase": "P6",
     "use": "E-SYN fork design: SeedSequence([60003, 0, world code, i, trial, epoch code, design_rep]) selection "
            "uniforms; [60003, 1, ..., continuation index, replicate] continuation proposals (shared by the arms); "
            "[60003, 2, ..., continuation index, replicate, arm code] continuation measurements."},
    {"name": "analysis_resampling", "block": "paperc_train_seeds", "value": 61_001, "phase": "P6",
     "use": "analysis randomness: numpy default_rng([61001, purpose, ...]); purpose 1: tau^2 cluster bootstrap; 2: N6 "
            "cross-fitting folds and bootstraps; 3: N6 fold draws of the P6 validation's leakage check. Block choice: "
            "these are samplers of Paper C's own analysis (resampling and fold assignment), not node, worker or design "
            "draws, which is the block's 'samplers' use; the value never seeds a campaign."},
)


# ---------------------------------------------------------------- declared sources

# (name, ref, path, extractor, symbols, kind, note); extractors are interpreted by ``_read_source``.
SOURCES = (
    ("tracks_instances", TRACKS, "r1/tracks/collect.py", "half_open_dict", ("INSTANCE_SEED_BLOCKS",), "literal", ""),
    ("tracks_audits", TRACKS, "r1/tracks/collect.py", "base_capacity_dict",
     ("AUDIT_SEED_BASES", "AUDIT_BLOCK_CAPACITY"), "literal", ""),
    ("tracks_selection_key", TRACKS, "r1/tracks/collect.py", "int", ("SELECTION_SEED",), "rng_key",
     "RNG key for fork selection, not a worker seed"),
    ("tracks_s11_factorial", TRACKS, "r1/tracks/probes/s1_factorial.py", "int_range", ("S11_SEEDS",), "literal", ""),
    ("tracks_oracle", TRACKS, "r1/tracks/oracle.py", "oracle", ("ORACLE_SELECT_BASE", "ORACLE_EVAL_BASE",
                                                                "ORACLE_BLOCK_SIZE"), "literal",
     "synthetic-world campaign seeds (in memory)"),
    ("e1b_instances", CANONICAL, "r1/headroom/e1b_collect.py", "e1b_formula", ("_instance_seed",), "formula",
     f"k < {K_DOMAIN} over all node-name residues mod 7 (declared; bounded by the next block at 1001); sweeps use "
     "k < 18 (seeds 100..276)"),
    ("e1b_leaf_audits", CANONICAL, "r1/headroom/e1b_collect.py", "base_count", ("AUDIT_SEED_BASE",), "base_count",
     f"AUDIT_SEED_BASE + i, i < k_audit (run-time; declared domain {COUNT_DOMAIN}); E1b used 5001..5006"),
    ("noise_floor", CANONICAL, "r1/noise/e1_noise_floor.py", "base_count_dict", ("SEED_BASE",), "base_count",
     f"SEED_BASE + s, s < n_seeds (run-time; declared domain {COUNT_DOMAIN}); C1 uses 30"),
    ("c3_audits", CANONICAL, "r1/c3/audit.py", "int_range", ("DEFAULT_SEEDS",), "literal", ""),
    ("exam_instances", CANONICAL, "r1/exam/namespace.py", "int_range", ("INSTANCE_SEEDS",), "literal", ""),
    ("exam_audits", CANONICAL, "r1/exam/namespace.py", "int_range", ("AUDIT_SEEDS",), "literal", ""),
    ("e2e_worker_seed", CANONICAL, "r1/e2e.py", "keyword", ("train_seed",), "literal",
     "LocalWorker(train_seed=999, split_seed=999) in the end-to-end check"),
)

# Worker-seed blocks without a defining constant in code at the pins.
EXTRA_BLOCKS = (
    Block("node_default_seed", 42, 43, "external", None, None, None,
          "the harness nodes' default train/split seed: noise-floor 'default' runs and the fixed partner seed of "
          "train-only / split-only runs (r1/noise/e1_noise_floor.py plan_runs passes None; STATUS.md records 42)"),
    Block("trackg_g1b_audits", 8001, 8011, "prose_only", None, None, None,
          "plan §11.1 'G.1b 8001–8010'; no code defines it on the canonical, Track S or Track G branches"),
    Block("tracks_audits_legacy", 33001, 35000, "prose_only", TRACKS, "r1/tracks/IMPLEMENTATION_NOTES.md", None,
          "Track S's earlier audit layout (dev audits 33001–33005, audits 34001+, phase-keyed 33001+ … 33601+), "
          "superseded by AUDIT_SEED_BASES; reserved because early runs may have used it"),
)

# RNG roots read from code (path, symbol or def:/kw: parameter); registered as one-wide blocks.
RNG_KEYS = (
    (CANONICAL, "r1/c3/dataset.py", "PLAN_SEED"),
    (CANONICAL, "r1/theory/t5_report.py", "BASE_SEED"),
    (CANONICAL, "r1/c3/offline_eval.py", "SEED"),
    (CANONICAL, "r1/diagnostics/di_test.py", "SEED"),
    (CANONICAL, "r1/headroom/e1b_compare.py", "SEED"),
    (CANONICAL, "r1/scripts/b1_q2_reference.py", "SEED"),
    (TRACKS, "r1/c3/train/exam_synthetic.py", "SEED"),
    (TRACKS, "r1/tracks/probes/s1_factorial.py", "BOOT_SEED"),
    (CANONICAL, "r1/baselines/evaluate.py", "def:seed"),
    (CANONICAL, "r1/branch/bootstrap.py", "def:seed"),
    (CANONICAL, "r1/exam/guards.py", "def:seed"),
    (CANONICAL, "r1/e2e.py", "kw:seed"),
    (TRACKS, "r1/tracks/simulate_controls.py", "def:seed"),
    (TRACKS, "r1/tracks/simulate_controls.py", "def:seed0"),
    (TRACKS, "r1/tracks/simulate_controls.py", "kw:seed"),
    (TRACKS, "r1/c3/train/model.py", "rngcall:"),
    (TRACKS, "r1/tracks/probes/determinism.py", "argparse:"),
)

# Constants the scan finds that are not seed values, each with the reason.
IGNORED = {
    ("r1/scripts/ada_e1b_rerun2.py", "AUDIT_SEEDS"): "a count (6 audit seeds of the E1b rerun), not a seed value",
    ("r1/tracks/collect.py", "REP_BASE"): "a D26 repetition index (100 + r), not a worker seed; namespaced by campaign id",
    ("r1/tracks/collect.py", "AUDIT_SEED_BLOCKS"): "derived from AUDIT_SEED_BASES + AUDIT_BLOCK_CAPACITY (registered)",
    ("r1/exam/namespace.py", "EXAM_SEEDS"): "union of INSTANCE_SEEDS and AUDIT_SEEDS (registered)",
    ("r1/scripts/trackx_lease_guardian.py", "PYTHON_BASENAME"): "a regular expression, not a seed",
    ("r1/noise/e1_noise_floor.py", "argparse:"): "--seeds default=10 is a count of seeds per condition, not a seed",
}


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
    if isinstance(expr, ast.Tuple):
        return tuple(_eval(e, env) for e in expr.elts)
    if isinstance(expr, ast.List):
        return [_eval(e, env) for e in expr.elts]
    if isinstance(expr, ast.Set):
        return {_eval(e, env) for e in expr.elts}
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
    for n, e in assigns.items():
        try:
            env[n] = _eval(e, env)
        except (ValueError, TypeError, KeyError):
            pass
    missing = [n for n in names if n not in env]
    if missing:
        raise KeyError(f"constants not found or not literal: {missing}")
    return {n: env[n] for n in names}


def function(src: str, name: str):
    """Compile one top-level pure function from its own AST (the module is not imported).

    Decorators, annotations and default values are stripped, and the code is compiled with ``dont_inherit`` and an
    explicit ``annotations`` future flag, so nothing from this module or the source module leaks in. Only ``sum``,
    ``map`` and ``ord`` are available as builtins.
    """
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            fn = copy.deepcopy(node)
            fn.decorator_list, fn.returns = [], None
            for a in fn.args.args + fn.args.kwonlyargs + fn.args.posonlyargs:
                a.annotation = None
            fn.args.defaults, fn.args.kw_defaults = [], [None] * len(fn.args.kwonlyargs)
            mod = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
            ns: dict = {"__builtins__": {"sum": sum, "map": map, "ord": ord}}
            exec(compile(mod, f"<{name}>", "exec", flags=_future.annotations.compiler_flag, dont_inherit=True), ns)
            return ns[name]
    raise KeyError(f"function {name} not found")


def _is_int(x) -> bool:
    return isinstance(x, ast.Constant) and isinstance(x.value, int) and not isinstance(x.value, bool)


RNG_CALLS = ("default_rng", "RandomState", "manual_seed", "seed", "Random", "SeedSequence", "PRNGKey")


def _call_name(f) -> str | None:
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None


def _seed_literals(src: str, which: str) -> list[int]:
    """Integer seeds in a file.

    ``def:<param>`` defaults and ``kw:<name>`` call keywords (exact name); ``anydef:`` / ``anykw:`` for every
    parameter or keyword whose name contains "seed"; ``argparse:`` for ``add_argument("--...seed...", default=N)``;
    ``rngcall:`` for the first positional integer of an RNG constructor (``default_rng``, ``RandomState``,
    ``manual_seed``, ``seed``, ``Random``, ``SeedSequence``, ``PRNGKey``).
    """
    kind, name = which.split(":")
    out = []
    for n in ast.walk(ast.parse(src)):
        if kind == "anykw" and isinstance(n, ast.keyword) and n.arg and "seed" in n.arg.lower() and _is_int(n.value):
            out.append(n.value.value)
        if kind == "anydef" and isinstance(n, ast.FunctionDef):
            a = n.args
            pairs = list(zip([x.arg for x in a.args][len(a.args) - len(a.defaults):], a.defaults))
            pairs += [(x.arg, d) for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
            out += [d.value for p, d in pairs if "seed" in p.lower() and _is_int(d)]
        if kind == "argparse" and isinstance(n, ast.Call) and _call_name(n.func) == "add_argument":
            flags = [a.value for a in n.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if any("seed" in f.lower() for f in flags):
                out += [k.value.value for k in n.keywords if k.arg == "default" and _is_int(k.value)]
        if kind == "rngcall" and isinstance(n, ast.Call) and _call_name(n.func) in RNG_CALLS and n.args \
                and _is_int(n.args[0]):
            out.append(n.args[0].value)
        if kind == "kw" and isinstance(n, ast.keyword) and n.arg == name and _is_int(n.value):
            out.append(n.value.value)
        if kind == "def" and isinstance(n, ast.FunctionDef):
            a = n.args
            pairs = list(zip([x.arg for x in a.args][len(a.args) - len(a.defaults):], a.defaults))
            pairs += [(x.arg, d) for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
            out += [d.value for p, d in pairs if p == name and _is_int(d)]
    return sorted(set(out))


def _read_source(repo: Path, src_decl) -> list[Block]:
    name, ref, path, how, symbols, kind, note = src_decl
    src = git_show(repo, ref, path)
    sym = ", ".join(symbols)
    if how == "half_open_dict":
        d = constants(src, symbols)[symbols[0]]
        return [Block(f"{name}_{k}", lo, hi, kind, ref, path, sym, note) for k, (lo, hi) in d.items()]
    if how == "base_capacity_dict":
        c = constants(src, symbols)
        cap = c[symbols[1]]
        return [Block(f"{name}_{k}", b, b + cap, kind, ref, path, sym, note) for k, b in c[symbols[0]].items()]
    if how == "int":
        v = constants(src, symbols)[symbols[0]]
        return [Block(name, v, v + 1, kind, ref, path, sym, note)]
    if how == "int_range":
        v = list(constants(src, symbols)[symbols[0]])
        return [Block(name, min(v), max(v) + 1, kind, ref, path, sym, note)]
    if how == "oracle":
        c = constants(src, symbols)
        return [Block(f"{name}_{tag}", c[s], c[s] + c[symbols[2]], kind, ref, path, sym, note)
                for tag, s in (("select", symbols[0]), ("eval", symbols[1]))]
    if how == "e1b_formula":
        f = function(src, symbols[0])
        names = ["a" * i for i in range(1, 8)]
        assert {sum(map(ord, n)) % 7 for n in names} == set(range(7))
        vals = [f(n, k) for n in names for k in range(K_DOMAIN)]
        return [Block(name, min(vals), max(vals) + 1, kind, ref, path, sym, note)]
    if how == "base_count":
        b = constants(src, symbols)[symbols[0]]
        return [Block(name, b, b + COUNT_DOMAIN, kind, ref, path, sym, note)]
    if how == "base_count_dict":
        d = constants(src, symbols)[symbols[0]]
        return [Block(f"{name}_{k}", b, b + COUNT_DOMAIN, kind, ref, path, f"{sym}[{k!r}]", note)
                for k, b in d.items()]
    if how == "keyword":
        vals = _seed_literals(src, f"kw:{symbols[0]}")
        return [Block(f"{name}_{v}", v, v + 1, kind, ref, path, sym, note) for v in vals]
    raise ValueError(how)


def paper_b_blocks(repo: Path) -> list[Block]:
    blocks: list[Block] = []
    for decl in SOURCES:
        blocks += _read_source(repo, decl)
    keys: dict[int, list[str]] = {}
    for ref, path, sym in RNG_KEYS:
        src = git_show(repo, ref, path)
        vals = _seed_literals(src, sym) if ":" in sym else [constants(src, [sym])[sym]]
        for v in vals:
            if v >= 10:
                keys.setdefault(v, []).append(f"{path}:{sym}@{ref[:8]}")
    for v, where in sorted(keys.items()):
        blocks.append(Block(f"rng_key_{v}", v, v + 1, "rng_key", None, None, "; ".join(where),
                            "RNG root, not a worker seed"))
    blocks += list(EXTRA_BLOCKS)
    return sorted(blocks, key=lambda b: (b.lo, b.name))


# ---------------------------------------------------------------- completeness scan

SCAN_NAME = re.compile(r"^[A-Z0-9_]*(SEED|_BASE)[A-Z0-9_]*$")
WORKER_KEYWORDS = ("train_seed", "split_seed", "instance_seed", "worker_seed", "audit_seed", "audit_seeds")
HALF_OPEN = {("r1/tracks/collect.py", "INSTANCE_SEED_BLOCKS")}


def _intervals(v, half_open: bool = False) -> list[tuple[int, int]] | None:
    """Inclusive integer intervals covered by a value; None if it holds something other than ints."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return [(v, v)]
    if isinstance(v, range):
        return [(v.start, v.stop - 1)] if len(v) else []
    if half_open and isinstance(v, (tuple, list)) and len(v) == 2 and all(isinstance(x, int) for x in v):
        return [(v[0], v[1] - 1)]
    if isinstance(v, (list, tuple, set)):
        out = []
        for x in v:
            xs = _intervals(x, half_open)
            if xs is None:
                return None
            out += xs
        return out
    if isinstance(v, dict):
        return _intervals(list(v.values()), half_open)
    return None


def _is_textual(v) -> bool:
    if isinstance(v, str):
        return True
    return isinstance(v, (list, tuple, set)) and bool(v) and all(isinstance(x, str) for x in v)


def scan_constants(repo: Path) -> list[dict]:
    found = []
    for ref in (CANONICAL, TRACKS):
        files = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref, "r1"], check=True,
                               capture_output=True, text=True).stdout.split()
        for path in files:
            if not path.endswith(".py") or "/tests/" in path:
                continue
            src = git_show(repo, ref, path)
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            env = {}
            for name, expr in _assignments(src).items():
                try:
                    env[name] = _eval(expr, env)
                except (ValueError, TypeError, KeyError):
                    env[name] = None
                if SCAN_NAME.match(name):
                    found.append({"ref": ref, "path": path, "name": name, "value": env[name], "how": "constant"})
            for n in ast.walk(tree):
                if isinstance(n, ast.keyword) and n.arg in WORKER_KEYWORDS and _is_int(n.value):
                    found.append({"ref": ref, "path": path, "name": f"kw:{n.arg}", "value": n.value.value,
                                  "how": "worker_keyword"})
            for which in ("anydef:", "anykw:", "argparse:", "rngcall:"):
                for v in _seed_literals(src, which):
                    if v >= 10:
                        found.append({"ref": ref, "path": path, "name": which, "value": v, "how": "rng_literal"})
    return found


def _uncovered(lo: int, hi: int, blocks: list[Block]) -> list[tuple[int, int]]:
    """Parts of the inclusive interval [lo, hi] not covered by any block."""
    gaps, cur = [], lo
    for b in sorted(blocks, key=lambda b: b.lo):
        if b.hi <= cur or b.lo > hi:
            continue
        if b.lo > cur:
            gaps.append((cur, b.lo - 1))
        cur = max(cur, b.hi)
        if cur > hi:
            break
    if cur <= hi:
        gaps.append((cur, hi))
    return gaps


def unaccounted(repo: Path, blocks: Iterable[Block], found: list[dict] | None = None) -> list[str]:
    blocks = list(blocks)
    out = []
    for c in (scan_constants(repo) if found is None else found):
        if (c["path"], c["name"]) in IGNORED or _is_textual(c["value"]):
            continue
        ivs = _intervals(c["value"], (c["path"], c["name"]) in HALF_OPEN)
        if ivs is None:
            out.append(f"{c['path']}:{c['name']} at {c['ref'][:8]}: value not evaluable")
            continue
        gaps = [g for lo, hi in ivs for g in _uncovered(lo, hi, blocks)]
        if gaps:
            out.append(f"{c['path']}:{c['name']} at {c['ref'][:8]}: {gaps[:3]} outside every block")
    return sorted(set(out))


def skipped_textual(found: list[dict]) -> list[str]:
    return sorted({f"{c['path']}:{c['name']}" for c in found if _is_textual(c["value"])})


# ---------------------------------------------------------------- registry

def check_disjoint(paper_b: Iterable[Block], paper_c: Iterable[Block] = PAPER_C_BLOCKS,
                   margin: int = MARGIN) -> list[str]:
    errs = []
    for c in paper_c:
        for b in paper_b:
            if c.lo < b.hi + margin and b.lo < c.hi + margin:
                errs.append(f"{c.name} [{c.lo},{c.hi}) is within {margin} of {b.name} [{b.lo},{b.hi})")
    return errs


def paper_b_overlaps(paper_b: Iterable[Block], worker_only: bool = False) -> list[str]:
    """Overlaps among Paper B's own blocks (a property of Paper B, reported, not fixed here).

    ``worker_only`` ignores RNG keys: an RNG root that equals a worker seed (e.g. 999, used as both the e2e worker
    seed and its manager's RNG seed) seeds different generators and repeats no measurement."""
    bs = sorted((b for b in paper_b if not (worker_only and b.kind == "rng_key")), key=lambda b: b.lo)
    return [f"{a.name} [{a.lo},{a.hi}) overlaps {b.name} [{b.lo},{b.hi})"
            for i, a in enumerate(bs) for b in bs[i + 1:] if b.lo < a.hi]


def build_registry(repo: Path) -> dict:
    pb = paper_b_blocks(repo)
    found = scan_constants(repo)
    errs = check_disjoint(pb) + [f"unaccounted: {u}" for u in unaccounted(repo, pb, found)]
    if errs:
        raise RuntimeError("STOP: " + "; ".join(errs))
    return {
        "schema": REGISTRY_SCHEMA,
        "pins": {"canonical": CANONICAL, "tracks": TRACKS},
        "domains": {"K_DOMAIN": K_DOMAIN, "COUNT_DOMAIN": COUNT_DOMAIN, "MARGIN": MARGIN,
                    "note": "declared bounds; the code puts no upper bound on the run-time counts"},
        "paper_b": [asdict(b) for b in pb],
        "paper_c": [asdict(b) for b in PAPER_C_BLOCKS],
        "paper_c_roles": PAPER_C_ROLES,
        "paper_c_claims": list(PAPER_C_CLAIMS),
        "paper_c_campaign_prefix": PAPER_C_CAMPAIGN_PREFIX,
        "paper_b_internal_overlaps": paper_b_overlaps(pb),
        "paper_b_internal_overlaps_worker_seeds": paper_b_overlaps(pb, worker_only=True),
        "scan_skipped_textual": skipped_textual(found),
    }


def dumps(reg: dict) -> str:
    return json.dumps(reg, indent=2, sort_keys=True) + "\n"


class Registry:
    """Implements ``paperc.schema.SeedRegistry`` plus the Paper C membership checks."""

    def __init__(self, data: dict):
        if data.get("schema") != REGISTRY_SCHEMA:
            raise ValueError("not a Paper C seed registry")
        self.paper_b = [Block(**b) for b in data["paper_b"]]
        self.paper_c = [Block(**b) for b in data["paper_c"]]
        self.roles = dict(data["paper_c_roles"])
        self.claims = list(data.get("paper_c_claims", []))
        self.campaign_prefix = data["paper_c_campaign_prefix"]

    @classmethod
    def load(cls, path: Path = OUT) -> "Registry":
        return cls(json.loads(Path(path).read_text()))

    def paper_b_block(self, node: str, instance_seed: int) -> str | None:   # node unused: one global namespace
        for b in self.paper_b:
            if instance_seed in b:
                return b.name
        return None

    def paper_b_range(self, lo: int, hi: int) -> str | None:
        """Name of a Paper B block intersecting the inclusive range [lo, hi], or None."""
        for b in self.paper_b:
            if b.lo <= hi and lo < b.hi:
                return b.name
        return None

    def paper_c_block(self, seed: int) -> str | None:
        for b in self.paper_c:
            if seed in b:
                return b.name
        return None

    def paper_c_check(self, role: str, lo: int, hi: int | None = None) -> str | None:
        """None if [lo, hi] lies inside the Paper C block of ``role``, else a message."""
        hi = lo if hi is None else hi
        name = self.roles[role]
        b = next(x for x in self.paper_c if x.name == name)
        return None if (b.lo <= lo and hi < b.hi) else f"{role} seed(s) [{lo}, {hi}] outside {name} [{b.lo},{b.hi})"


def main(repo: Path | None = None) -> Path:
    repo = repo or Path(__file__).resolve().parents[3]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dumps(build_registry(repo)))
    return OUT


if __name__ == "__main__":
    print(main())
