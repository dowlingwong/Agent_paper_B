"""Integration trial 14 Nov (review U7 B1): ``offline_eval.assemble`` calls the analysis guard before it reads
``build.json``, so a table under an ``r1_sealed`` path STOPs on the sealed-path guard, never on its contents."""
import json

import pytest

from r1.c3 import offline_eval as oe


def test_sealed_table_stops_on_the_guard_before_build_json_is_read(tmp_path):
    table = tmp_path / "r1_sealed" / "table"
    table.mkdir(parents=True)
    # contents that would raise a different error if build.json were read first
    (table / "build.json").write_text(json.dumps({"classification": {"sha256": "x"}, "label": "DRYRUN"}))
    (table / "proposals.jsonl").write_text("")
    (table / "audits.jsonl").write_text("")
    with pytest.raises(RuntimeError, match="r1_sealed"):
        oe.assemble(table)
