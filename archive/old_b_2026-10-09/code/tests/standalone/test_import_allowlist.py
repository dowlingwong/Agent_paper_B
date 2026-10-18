"""B's code must import nothing outside an explicit allowlist.

This replaces the repository-wide ``check_split.py``.  It walks the AST of every
Python file under B's code roots and collects:

- ``import x`` / ``from x import y`` module names, resolving relative imports
  against the ``causal_branch`` package root and expanding ``from pkg import
  name`` to ``pkg.name`` when that name is a module;
- the literal module name in ``importlib.import_module(...)`` and
  ``__import__(...)`` calls;
- the literal path in ``importlib.util.spec_from_file_location(...)`` calls
  (checked separately: it must resolve inside this repository).

Every ``causal_branch`` name must be in :data:`ALLOWED_CAUSAL_BRANCH`; every
other name must be in the standard library, :data:`ALLOWED_THIRD_PARTY`, or a
local module of this repository.  The measurement core is forbidden by name,
with ``variance_adaptive`` called out explicitly.

**What this test cannot see.**  It only understands literal module names and
literal file paths.  A computed module name or path — built at run time from a
variable, ``getattr``, ``__import__`` with a non-literal, or an ``importlib``
call whose argument is not a string literal — is invisible to it.  It also does
not execute imports, so a conditionally executed import that is still
syntactically present is caught, but a module assembled dynamically is not.
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
    # The copied shared modules B depends on (closure and live lane).
    *sorted((PKG / "causal_branch").glob("*.py")),
    PKG / "causal_branch/adapters",
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

ALLOWED_CAUSAL_BRANCH_PREFIXES = ("causal_branch.control",)

#: Paper A's measurement core.  B does not import it.
FORBIDDEN_CAUSAL_BRANCH = {
    "causal_branch.measurement",
    "causal_branch.state_audit",
    "causal_branch.replay_validity",
    "causal_branch.finite_repeat_identification",
    "causal_branch.finite_budget_decisions",
    "causal_branch.variance_adaptive",
}

#: Third-party packages B may import.  Local repository modules are handled
#: separately by :data:`LOCAL_MODULES`.
ALLOWED_THIRD_PARTY = {
    "numpy", "yaml", "sklearn", "hypothesis", "torch", "clm",
}

_IMPORT_CALLS = {"import_module", "__import__"}
_FILE_CALLS = {"spec_from_file_location"}

SKIP_PARTS = {".git", "third_party", "__pycache__", ".venv", "node_modules"}


def _local_module_names() -> set[str]:
    names = set()
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        names.add(path.stem)
        if path.name == "__init__.py":
            names.add(path.parent.name)
    return names


LOCAL_MODULES = _local_module_names()


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


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_submodule(package: str, name: str) -> bool:
    """Whether ``package.name`` is (or would be) a module rather than an attribute.

    Inside ``causal_branch`` a name counts as a submodule when it is a file or
    package in this repository or a known forbidden module (which is absent).
    """
    if package != "causal_branch" and not package.startswith("causal_branch."):
        return False
    full = f"{package}.{name}"
    if full in FORBIDDEN_CAUSAL_BRANCH:
        return True
    target = PKG.joinpath(*full.split("."))
    return target.with_suffix(".py").is_file() or (target / "__init__.py").is_file()


def imports_from_source(source: str, filename: str, mod_of=None) -> set[str]:
    """The literal module names a source string imports."""
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
                base_name = ".".join(basepkg + ([node.module] if node.module else []))
            elif node.module:
                base_name = node.module
            else:
                continue
            found.add(base_name)
            # ``from pkg import name`` may import the submodule ``pkg.name``.
            for alias in node.names:
                if alias.name != "*" and _is_submodule(base_name, alias.name):
                    found.add(f"{base_name}.{alias.name}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in _IMPORT_CALLS and node.args:
                literal = _literal_string(node.args[0])
                if literal:
                    found.add(literal)
    return found


def dynamic_file_literals(source: str, filename: str) -> list[str]:
    """Literal paths passed to ``spec_from_file_location``."""
    found = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in _FILE_CALLS and len(node.args) >= 2:
                literal = _literal_string(node.args[1])
                if literal:
                    found.append(literal)
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
                    if top in LOCAL_MODULES:
                        continue
                    offenders.append(f"{path}: {name}")
        self.assertEqual(offenders, [])

    def test_dynamic_file_literals_stay_inside_the_repository(self):
        offenders: list[str] = []
        for root in ROOTS:
            for path in _iter_py(root):
                for literal in dynamic_file_literals(path.read_text(), str(path)):
                    resolved = (path.parent / literal).resolve()
                    if not str(resolved).startswith(str(ROOT.resolve())):
                        offenders.append(f"{path}: {literal}")
        self.assertEqual(offenders, [])

    def test_shared_modules_are_scanned(self):
        # The copied shared modules are roots, so a forbidden import there is
        # caught by the real scan.
        shared = (PKG / "causal_branch/checkpoint.py").resolve()
        scanned = {p.resolve() for root in ROOTS for p in _iter_py(root)}
        self.assertIn(shared, scanned)

    def test_rejects_planted_forbidden_import(self):
        planted = "import causal_branch.variance_adaptive\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertTrue(names & FORBIDDEN_CAUSAL_BRANCH)

    def test_rejects_planted_from_causal_branch_import(self):
        planted = "from causal_branch import variance_adaptive\n"
        names = _causal_branch_names(imports_from_source(planted, "planted.py"))
        self.assertTrue(names & FORBIDDEN_CAUSAL_BRANCH)

    def test_rejects_planted_relative_from_import(self):
        # ``from .. import state_audit`` in a module under control/ resolves to
        # ``causal_branch.state_audit``.
        filename = str(PKG / "causal_branch/control/planted.py")
        planted = "from .. import state_audit\n"
        names = _causal_branch_names(imports_from_source(planted, filename, _mod_of))
        self.assertTrue(names & FORBIDDEN_CAUSAL_BRANCH)

    def test_rejects_planted_shared_module_import(self):
        # A forbidden import planted in a copied shared module is caught.
        shared = (PKG / "causal_branch/checkpoint.py").read_text()
        names = _causal_branch_names(
            imports_from_source(shared + "\nimport causal_branch.state_audit\n", str(PKG / "causal_branch/checkpoint.py"), _mod_of)
        )
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
