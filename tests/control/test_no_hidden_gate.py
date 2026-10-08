"""F2/H2: no controller may read a replay allowance or import replay_validity.

The guard parses every control module (except the N1 evaluation modules) and
fails if:

- any function takes a `p`-like parameter;
- any function references an allowance name other than bare `p`
  (`p_path`, `allowance`, `replay_allowance`, `replay_p`, any case);
- a decision-shaped function (one that scores, ranks, fits, reserves, picks a
  regime or grid, allocates or verifies; matched by name stem, not an exact
  list) references bare `p`, as a name or an attribute;
- any module imports `replay_validity`.

Planting each of these must fail the guard (review H2 widened the stems).
"""
import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "experiment_scaffold/src/causal_branch/control"
sys.path.insert(0, str(CONTROL.parent))

FORBIDDEN_NAMES = {"p", "p_path", "allowance", "replay_allowance", "replay_p"}
#: Name stems of functions that return an action, regime, score, reserve,
#: grid or allocation.
DECISION_STEMS = re.compile(
    r"choos|decid|allocat|select|polic|scor|rank|regime|reserv|grid|fit|verif|stage",
    re.IGNORECASE)
#: N1 lives in evaluation only; these modules may use the allowance.
EXEMPT = {"replay_validity.py", "evaluate_tree.py"}


def controller_errors(tree: ast.AST, source_name: str) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any("replay_validity" in alias.name for alias in node.names):
                errors.append(f"{source_name}: imports replay_validity")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "replay_validity" in module or any("replay_validity" in a.name for a in node.names):
                errors.append(f"{source_name}: imports replay_validity")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args + node.args.kwonlyargs + node.args.posonlyargs]
            for bad in FORBIDDEN_NAMES:
                if bad in args or bad in [a.lower() for a in args]:
                    errors.append(f"{source_name}:{node.name} parameter {bad}")
            decision_shaped = bool(DECISION_STEMS.search(node.name))
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    ident, label = sub.id, sub.id
                elif isinstance(sub, ast.Attribute):
                    ident, label = sub.attr, "." + sub.attr
                else:
                    continue
                low = ident.lower()
                if low in FORBIDDEN_NAMES and (low != "p" or decision_shaped):
                    errors.append(f"{source_name}:{node.name} references {label}")
    return errors


class TestNoHiddenGate(unittest.TestCase):
    def test_no_control_module_has_a_replay_allowance_gate(self):
        problems: list[str] = []
        for path in sorted(CONTROL.glob("*.py")):
            if path.name in EXEMPT or path.name == "__init__.py":
                continue
            problems.extend(controller_errors(ast.parse(path.read_text()), path.name))
        self.assertEqual(problems, [])

    def test_planted_allowance_parameter_fails(self):
        planted = "def choose(self, adv1, adv2, p):\n    return 'now' if adv1 - 2*p > 0 else 'never'\n"
        errors = controller_errors(ast.parse(planted), "planted.py")
        self.assertTrue(any("parameter p" in e or "references p" in e for e in errors), errors)

    def test_planted_reference_in_a_non_listed_decision_name_fails(self):
        # H2: `scores`, `regimes_for`, `reserve_mask` were not in the old exact list
        for planted in (
            "def scores(self, rows):\n    return {k: v - 2 * self.p for k, v in rows}\n",
            "def regimes_for(view):\n    return 'now' if view.a1 > 2 * p else 'never'\n",
            "def reserve_mask(views):\n    return [v.s1 < REPLAY_P for v in views]\n",
            "def helper(x):\n    return x - x.p_path\n",
        ):
            errors = controller_errors(ast.parse(planted), "planted.py")
            self.assertTrue(errors, planted)

    def test_bare_p_in_a_non_decision_helper_is_allowed(self):
        # a loop variable named p in a formatting helper is not a gate
        benign = "def describe(items):\n    return [str(p) for p in items]\n"
        self.assertEqual(controller_errors(ast.parse(benign), "benign.py"), [])

    def test_planted_import_fails(self):
        planted = "from causal_branch.control import replay_validity\n"
        errors = controller_errors(ast.parse(planted), "planted.py")
        self.assertTrue(any("imports replay_validity" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
