"""D.3 revision 4 step-(5) audit replay. All worker and audit metrics are synthetic."""

import argparse
import json
import math
from pathlib import Path

from r1.c3 import d3_analysis as analysis
from r1.c3 import d3_outcome_table as table
from r1.c3.d3 import assemble
from r1.tests import test_d3_integration as cases


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def verify_case(expected, summary, records, chunk, audit_dir):
    runs, calls, last_keep, keeps, y, terminal_keep = expected
    assert summary["llm_calls"] <= 80
    if calls is not None:
        assert summary["llm_calls"] == calls
    assert (summary["worker_runs"], summary["last_keep_run"], summary["keeps"]) == (runs, last_keep, keeps)
    cid = analysis.campaign_id("D.3a", summary["arm"], summary["node"], summary["instance_seed"], 0)
    campaign = chunk / "campaigns" / cases.INSTANCE
    audit = table._audits_by_campaign(records)[cid]
    row = table.build_row("D.3a", summary, audit)
    final = json.loads((campaign / "snapshots" / "final.json").read_text())
    assert final["config_sha256"] == row["final_config_hash"] == audit["final"]["config_sha256"]
    assert math.isclose(row["y_raw"], y, rel_tol=0.0, abs_tol=1e-12)
    if runs == 20:
        pre = json.loads((campaign / "snapshots" / "w20_pre.json").read_text())
        assert (pre["config_sha256"] != final["config_sha256"]) == terminal_keep
        assert row["ended_on"] == "worker_runs"
        assert audit["20"]["config_sha256"] == final["config_sha256"]
        assert row["y_raw_w"]["20"] == row["y_raw"]
    else:
        assert row["ended_on"] == "llm_call_cap"
        assert row["y_raw_w"]["20"] is None and "20" not in audit
    keeps_full = jsonl(audit_dir / "Y_keep.jsonl")
    keep_hashes = [json.loads(p.read_text()) for p in sorted((campaign / "keeps").glob("keep-*.json"))]
    assert len(keeps_full) == len(keep_hashes) == keeps
    keep_by_run = {r["w"]: r for r in keeps_full}
    keep_ids = {p["keep_run"] for p in keep_hashes}
    assert keep_ids == set(keep_by_run)
    assert all(keep_by_run[p["keep_run"]]["config_sha256"] == p["config_sha256"] for p in keep_hashes)
    assert all(r["seeds"] == list(range(6701, 6711)) for r in keeps_full)
    assert all(r["start_config_sha256"] == row["start_config_hash"] for r in keeps_full)
    ys = [(0, 0.0)] + [(r, keep_by_run[r]["y_raw"]) for r in sorted(keep_by_run)]
    improving = [run for (_, before), (run, after) in zip(ys, ys[1:]) if after > before]
    assert row["last_improving_run"] == (improving[-1] if improving else None)
    return row


def reproduce_analysis(root, original_summary, original_records, chunk, audit_dir):
    # Analysis insists on exact declared coverage. Replicate the production records only
    # to fill other cells. The tested campaign is read from the original G1/G6 paths.
    padding_chunk = root / "coverage_scaffold"
    padding_audit = root / "scaffold_audits"
    padding_audit.mkdir()
    original_id = (original_summary["arm"], original_summary["node"], original_summary["instance_seed"])
    with (padding_audit / "g7_rows.jsonl").open("w") as stream:
        for arm in analysis.ARMS_D3A:
            for node in analysis.NODES:
                for seed in analysis.INSTANCE_SEEDS:
                    if (arm, node, seed) == original_id:
                        continue
                    # The early-cap case has 80 calls, so its cloned coverage rows are valid
                    # independently of arm. Preserve starts to keep within-node pairing valid.
                    summary = {**original_summary, "arm": arm, "node": node, "instance_seed": seed}
                    directory = padding_chunk / "campaigns" / f"{arm}__{analysis.instance_id(node, seed)}"
                    directory.mkdir(parents=True)
                    (directory / "summary.json").write_text(json.dumps(summary))
                    cid = analysis.campaign_id("D.3a", arm, node, seed, 0)
                    for record in original_records:
                        stream.write(json.dumps({**record, "campaign_id": cid}) + "\n")
    assembled = assemble.build(
        "D.3a", [chunk, padding_chunk], [audit_dir, padding_audit],
        predeclaration_path=cases.PREDECLARATION,
    )
    path = table.write_table(assembled, root / "synthetic_table.json")
    loaded = analysis.load_table(path, "D.3a")
    report_path = root / "synthetic_report.json"
    assert analysis.main([
        "analyse", "--d3a", str(path), "--d3b-not-run", "not_started",
        "--predeclaration", cases.PREDECLARATION, "--out", str(report_path),
    ]) == 0
    result = json.loads(report_path.read_text())
    assert result["inputs"]["analysis_sha256"] == "c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce"
    assert result["schema"] == analysis.REPORT_SCHEMA
    assert result["families"]["D.3a"]["family"] == "D.3a"
    assert len(loaded["rows"]) == 882
    return loaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    root = parser.parse_args().output
    root.mkdir()
    plans = (
        ("harness_keep", cases.harness_case, (), True, False, (20, None, 20, 20, 0.0, True)),
        ("harness_discard", cases.harness_case, (), False, False, (20, None, 19, 19, 0.05, False)),
        ("harness_early_cap", cases.harness_case, (), True, True, (7, 80, 7, 7, 0.05, True)),
        ("FIXR3_keep", cases.replicate_case, ("FIXR3",), True, False, (20, None, 20, 6, 0.70, True)),
        ("FIXR3_discard", cases.replicate_case, ("FIXR3",), False, False, (20, None, 17, 5, 0.60, False)),
        ("EGATE_keep", cases.replicate_case, ("EGATE",), True, False, (20, None, 20, 2, 0.80, True)),
        ("EGATE_discard", cases.replicate_case, ("EGATE",), False, False, (20, None, 1, 1, 0.10, False)),
    )
    for name, run_case, args, final_keep, early, expected in plans:
        directory = root / name
        early_arg = {"early": early} if not args else {}
        _, _, _, chunk, audit_dir = run_case(directory, *args, final_keep=final_keep, **early_arg)
        summary, = assemble.load_summaries([chunk])
        records = assemble.load_audits([audit_dir])
        row = verify_case(expected, summary, records, chunk, audit_dir)
        loaded = reproduce_analysis(directory, summary, records, chunk, audit_dir)
        merged_row, = [r for r in loaded["rows"] if r["campaign_id"] == row["campaign_id"]]
        assert row == merged_row
        print(json.dumps({
            "case": name, "charged": row["worker_runs"], "calls": row["llm_calls"], "keeps": row["keeps"],
            "last_keep": row["last_keep_run"], "last_improving": row["last_improving_run"],
            "y_final": round(row["y_raw"], 12), "y_w20": None if row["y_raw_w"]["20"] is None else
            round(row["y_raw_w"]["20"], 12),
            "end": row["ended_on"], "analysis_rows": len(loaded["rows"]),
            "declaration_sha256": loaded["predeclaration_sha256"],
        }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
