"""B's code must import nothing outside an explicit allowlist.

This replaces the repository-wide ``check_split.py``.  It walks the AST of every
Python file under B's code roots and collects:

- ``import x`` / ``from x import y`` module names, resolving relative imports
  against the ``causal_branch`` package root;
- the string literal first argument of ``importlib.import_module(...)`` and
  ``importlib.util.spec_from_file_location(...)`` calls.

Every ``causal_branch`` name must be in :data:`ALLOWED_CAUSAL_BRANCH`; every
non-``causal_branch`` name must be in the standard library or
:data:`ALLOWED_THIRD_PARTY`.  The measurement core is forbidden by name, with
``variance_adaptive`` called out explicitly.

**What this test cannot see.**  It only understands literal module names.  A
computed module name — built at run time from a variable, ``getattr``,
``__import__`` with a non-literal, or an ``importlib`` call whose argument is not
a string literal — is invisible to it.  It also does not execute imports, so a
conditionally executed import that is still syntactically present is caught, but
a module assembled dynamically is not.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "experiment_scaffold/src"

ROOTS = [
    PKG / "causal_branch/control",
    ROOT / "experiments/paper_b",
    ROOT / "tests/control",
    ROOT / "protocols/paper_b/launch_validator.py",
    ROOT / "scripts/run_local_soak.py",
    ROOT / "scripts/start_bound_server.py",
    ROOT / "scripts/e0_card_availability.py",
    ROOT / "scripts/resolve_pinned_node.py",
    ROOT / "scripts/verify_vendored_pi.py",
    ROOT / "scripts/make_release.py",
    ROOT / "scripts/check_release_independence.py",
    ROOT / "scripts/release_provenance.py",
]

#: Every causal_branch module B is allowed to name.  Sourced from the measured
#: import closure at snapshot S.
ALLOWED_CAUSAL_BRANCH = {
    "causal_branch",
    "causal_branch.types",
    "causal_branch.branching",
    "causal_branch.checkpoint",
    "causal_branch.pi_fork",
    "causal_branch.budget",
    "causal_branch.d7_adjudicator",
    "causal_branch.d7_registered_commands",
    "causal_branch.device_mapping",
    "causal_branch.history_retention",
    "causal_branch.model_client",
    "causal_branch.pi_models",
    "causal_branch.pi_rpc",
    "causal_branch.process_fleet",
    "causal_branch.registered_tools",
    "causal_branch.round4_qualification",
    "causal_branch.round5_titan_exam",
    "causal_branch.round5_titan_runtime_evidence",
    "causal_branch.round5_titan_stage_a_acquisition",
    "causal_branch.round5_titan_stage_b_execution",
    "causal_branch.runtime_identity",
    "causal_branch.substrate_identity",
    "causal_branch.tool_socket",
    "causal_branch.adapters",
    "causal_branch.adapters.toy",
    "causal_branch.adapters.pi_agent",
}

ALLOWED_CAUSAL_BRANCH_PREFIXES = (
    "causal_branch.control",
)

#: Paper A's measurement core.  B does not import it.
FORBIDDEN_CAUSAL_BRANCH = {
    "causal_branch.measurement",
    "causal_branch.state_audit",
    "causal_branch.replay_validity",
    "causal_branch.finite_repeat_identification",
    "causal_branch.finite_budget_decisions",
    "causal_branch.variance_adaptive",
}

ALLOWED_THIRD_PARTY = {
    "numpy", "yaml", "sklearn", "hypothesis", "torch", "clm",
    "release_provenance",
}

DYNAMIC_CALLS = {"import_module", "spec_from_file_location", "__import__"}


def _iter_py(path: Path):
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*.py")):
        yield child


def _mod_of(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(PKG)
    except ValueError:
        return None
    rel = rel.parent if rel.name == "__init__.py" else rel.with_suffix("")
    return ".".join(rel.parts)


def imports_from_source(source: str, filename: str, mod_of=None) -> set[str]:
    """The literal module names a source string imports.

    ``mod_of`` resolves the package context for relative imports; pass ``None``
    for a synthetic fixture that has no file on disk.
    """
    found: set[str] = set()
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and mod_of is not None:
                base = mod_of(Path(filename))
                if base is None:
                    continue
                pkg = base.split(".")[:-1] if Path(filename).name != "__init__.py" else base.split(".")
                up = node.level - 1
                basepkg = pkg[: len(pkg) - up]
                found.add(".".join(basepkg + ([node.module] if node.module else [])))
            elif node.module:
                found.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in DYNAMIC_CALLS and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    found.add(first.value)
    return found


def _causal_branch_names(names: set[str]) -> set[str]:
    return {n for n in names if n == "causal_branch" or n.startswith("causal_branch.")}


def _allowed_causal_branch(name: str) -> bool:
    if name in ALLOWED_CAUSAL_BRANCH:
        return True
    return any(name == p or name.startswith(p + ".") for p in ALLOWED_CAUSAL_BRANCH_PREFIXES)


def _top(name: str) -> str:
    return name.split(".")[0]


class ImportAllowlistTest(unittest.TestCase):
    def test_every_causal_branch_import_is_allowed(self):
        offenders: list[str] = []
        for root in ROOTS:
            for path in _iter_py(root):
                names = _causal_branch_names(imports_from_source(path.read_text(), str(path), _mod_of))
                for name in names:
                    if name in FORBIDDEN_CAUSAL_BRANCH:
                        offenders.append(f"{path}: forbidden {name}")
                    elif not _allowed_causal_branch(name):
                        offenders.append(f"{path}: outside allowlist {name}")
        self.assertEqual(offenders, [])

    def test_no_third_party_import_outside_allowlist(self):
        offenders: list[str] = []
        for root in ROOTS:
            for path in _iter_py(root):
                names = imports_from_source(path.read_text(), str(path), _mod_of)
                for name in names:
                    if _top(name) == "causal_branch":
                        continue
                    top = _top(name)
                    if top in sys.stdlib_module_names or top in ALLOWED_THIRD_PARTY:
                        continue
                    offenders.append(f"{path}: {name}")
        self.assertEqual(offenders, [])

    def test_rejects_planted_forbidden_import(self):
        planted = "import causal_branch.variance_adaptive\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertTrue(names & FORBIDDEN_CAUSAL_BRANCH)

    def test_rejects_planted_measurement_import(self):
        planted = "from causal_branch.measurement import facade\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertTrue(names & FORBIDDEN_CAUSAL_BRANCH)

    def test_rejects_planted_dynamic_literal(self):
        planted = "import importlib\nimportlib.import_module('causal_branch.variance_adaptive')\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertTrue(names & FORBIDDEN_CAUSAL_BRANCH)

    def test_rejects_planted_unknown_causal_branch(self):
        planted = "import causal_branch.deepseek_portal\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertTrue(names - ALLOWED_CAUSAL_BRANCH)

    def test_ignores_computed_module_names(self):
        # Documented blind spot: a computed name is not a literal and is not
        # collected.  This asserts the limitation rather than hiding it.
        planted = "import importlib\nname = 'causal_branch.' + 'variance_adaptive'\nimportlib.import_module(name)\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertEqual(names, set())


if __name__ == "__main__":
    unittest.main()
