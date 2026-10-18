"""F8: Pi tool definitions for the live candidate-consistency task.

The tools make the exact submission format explicit.  The fit tool returns the
executable candidate it evaluated; the agent never retypes a fitted expression.
"""

from __future__ import annotations

CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "feature": {"type": "integer", "description": "feature index"},
        "threshold": {"type": "number", "description": "decision threshold"},
        "direction": {"type": "integer", "enum": [1, -1],
                      "description": "+1 predict 1 when x > threshold; -1 when x <= threshold"},
    },
    "required": ["feature", "threshold", "direction"],
}

TOOLS = [
    {
        "name": "fit_candidate",
        "description": "Fit a candidate on the visible development data and return the exact executable candidate.",
        "input_schema": {"type": "object", "properties": {}},
        "returns": CANDIDATE_SCHEMA,
    },
    {
        "name": "verify_candidate",
        "description": "Check a candidate against visible development diagnostics; replace only on a strict improvement.",
        "input_schema": {"type": "object", "properties": {"candidate": CANDIDATE_SCHEMA},
                         "required": ["candidate"]},
        "returns": CANDIDATE_SCHEMA,
    },
    {
        "name": "submit_candidate",
        "description": "Submit the final executable candidate for hidden evaluation.",
        "input_schema": {"type": "object", "properties": {"candidate": CANDIDATE_SCHEMA},
                         "required": ["candidate"]},
        "returns": {"type": "object", "properties": {"accepted": {"type": "boolean"}}},
    },
]


def tool_names() -> list[str]:
    return [tool["name"] for tool in TOOLS]
