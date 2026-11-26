"""Parser tests for r1/scripts/plan_row_check.py (M1 step 3); no git access."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "plan_row_check", Path(__file__).resolve().parents[1] / "scripts" / "plan_row_check.py")
prc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prc)

PLAN = """# PLAN
## 9. Before
| X-OUTSIDE | not in section 10 |
## 10. Open decisions
> **Historical index.** a note
| ID | Decision |
|---|---|
| R1-A (1 Nov) | first |
| R1-A (1 Nov) | first |
### 4 November 2026 — heading
- a bullet
## 11. After
| X-AFTER | not in section 10 |
"""

STATUS = """# Status

- top entry (4 Nov)
  - nested line
| a | table under the entry |

- second entry

## 31 October 2026 — section
- inside section

| table | under a heading |
A free paragraph.
"""


def test_plan_rows_only_section_10_with_multiplicity():
    rows = prc.plan_rows(PLAN)
    assert rows == ["| ID | Decision |", "| R1-A (1 Nov) | first |", "| R1-A (1 Nov) | first |"]


def test_plan_other_lines():
    assert prc.plan_other_lines(PLAN) == [
        "> **Historical index.** a note", "### 4 November 2026 — heading", "- a bullet"]


def test_status_entries_keep_continuations():
    e = prc.status_entries(STATUS)
    assert e[0] == "# Status"
    assert e[1] == "- top entry (4 Nov)\n  - nested line\n| a | table under the entry |"
    assert "- second entry" in e and "## 31 October 2026 — section" in e and "- inside section" in e


def test_status_lines_outside_entries_are_items():
    e = prc.status_entries(STATUS)
    assert "# Status" in e and "| table | under a heading |" in e and "A free paragraph." in e
    assert all(x.strip() for x in e)


def test_key_uses_first_cell():
    assert prc.key("| R1-A (1 Nov) | first |") == "R1-A (1 Nov)"
