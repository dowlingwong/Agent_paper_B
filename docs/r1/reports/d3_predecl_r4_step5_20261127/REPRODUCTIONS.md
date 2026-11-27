# D.3 revision 4 step (5) synthetic reproductions

Task `local/20261127-16`. Published base `c025ee244a4e8b1461d16d8e6ae17abcf431713e`.
Harness `9bb416805175149eb87b71f28d77530572aa4bce`. The probes use scripted proposals, fake worker metrics
and synthetic audit fixtures. They execute no model training or real campaign and use no sealed inputs.

## Harness arms lose the terminal keep

`SnapshotRecorder` saves the incumbent from E1 and leaves it in place through the E2 decision.
The harness path seals this cached incumbent through `write_final`. At 20 charged runs it copies the
pre-decision `w20.json`. Early termination also takes the cached E1 incumbent if the documented
last keep occurs in the terminating trial.

| End condition | Final keep in ledger | Last keep in final snapshot | Snapshot alias |
|---|---:|---:|---|
| Worker-run cap | 20 | 19 | `w20.json` |
| Synthetic LLM-call cap | 7 | 6 | none |

The checked-out incumbent and the snapshot disagree by rendered configuration hash at both endings.
In the first case the live incumbent is `4b1b4f8dcc271f804508a0e122a570b3f3c14b78527b849ac50eeb69eb414cfb`
and `final.json` records `a12ae00c87ecb01463f2b10a59e7699166f10523f58d38b5f983c4c3adfa9185`.
The early-cap case has the hashes in the opposite order.

## Replicate arms keep both incumbents and fail at assembly

Revision 6c records the exact-charge incumbent inside the replicate step and the terminal incumbent
after its last keep decision. G6 audits them separately when the configurations differ. The synthetic
EGATE case returns `y_raw = 0.50` at `w=20` and `y_raw = 0.70` for the terminal configuration.
G7 refuses the row with `at w = 20 the snapshot audit is the final audit (one canonical audit)`.
When given the same values independently, the pinned analysis refuses the whole table with
`y_raw_w at w = 20 must equal y_raw when the campaign reached W`.

## Reproduce

Copy each Python block to a fresh scratch file. From the published base, set `AR_HARNESS_ROOT` to the
pinned harness checkout and run `PYTHONPATH="$PWD" python -B <scratch file>`. Use a fresh scratch
directory for each run. Successful reproductions print the expected mismatch and refusal records.

### Harness final snapshot

```python
import json
import tempfile
from dataclasses import replace
from pathlib import Path

from r1.tests.test_d3_g1_snapshots import (
    HARNESS, NODE, ConfigMetricWorker, ParityBudget, SnapshotRecorder, ToggleBackend,
    TrialAppendStore, VerifyOnce, _node_copy, load_registered_node, run_real_campaign, wrap,
)
from r1.c3.d3.snapshots import config_sha256

class ScriptedManager(ToggleBackend):
    deterministic = False

class ImprovingWorker(ConfigMetricWorker):
    """Apply fixture edits and report a strictly improving synthetic metric."""
    def run_trial(self, proposal, node_spec, budget_index):
        result = super().run_trial(proposal, node_spec, budget_index)
        return replace(result, parsed_metrics={"val_score": 0.50 + 0.01 * self.runs})

for max_runs, max_calls, ended_on in [(20, 80, 'worker_runs'), (20, 7, 'llm_call_cap')]:
    root = Path(tempfile.mkdtemp(prefix="d3-last-keep-"))
    node = _node_copy(root)
    campaign = root / "campaign"
    records_path = campaign / "ledger.jsonl"
    rec = SnapshotRecorder(campaign, "a", "A0", NODE, 0, f"{NODE}__s6201")
    worker = ImprovingWorker(node)
    kwargs = wrap({
        "node_spec": load_registered_node(NODE, repo_root=HARNESS),
        "campaign_id": rec.instance_id,
        "budget": max_runs,
        "manager_mode": "baseline_manager",
        "memory_mode": "append_only_summary",
        "records_path": records_path,
        "worker": worker,
        "proposal_backend": ScriptedManager(),
        "controller": VerifyOnce(at=99),
        "compute_budget": ParityBudget(max_worker_runs=max_runs, max_llm_calls=max_calls, recorder=rec),
        "verify_runs": 2,
        "verify_split_policy": "vary",
    }, rec)
    run_real_campaign(**kwargs)
    rec.write_final(w_final=rec.count, ended_on=ended_on)
    rows = TrialAppendStore(records_path).read_all()
    final = json.loads((campaign / "snapshots" / "final.json").read_text())
    expected = config_sha256({path: (node / path).read_text() for path in final["incumbent_config"]})
    last = rows[-1]
    decision = getattr(last.decision, "value", last.decision)
    assert rec.count == min(max_runs, max_calls)
    assert str(decision).lower() in {"keep", "kept"}
    assert expected != final["config_sha256"]
    assert final["last_kept_trial_index"] < last.budget_index
    print(json.dumps({
        "count": rec.count, "ended_on": ended_on, "ledger_last_decision": decision,
        "ledger_last_trial": last.budget_index, "snapshot_last_kept_trial": final["last_kept_trial_index"],
        "actual_incumbent_sha256": expected, "snapshot_incumbent_sha256": final["config_sha256"],
        "alias_of": final.get("alias_of"),
    }, sort_keys=True))
```

### Replicate G6, G7 and analysis

```python
import json
import tempfile
from pathlib import Path

from r1.c3 import d3_analysis as analysis
from r1.c3 import d3_outcome_table as table
from r1.tests.test_d3_audit_g6 import (
    G, INC5, INC7, INSTANCE, NODE, SIGMA, FakeRunner, snapshot, write_campaign,
)
from r1.tests.test_d3_analysis import synthetic_table
from r1.tests.test_d3_outcome_table import _summary

root = Path(tempfile.mkdtemp(prefix="d3-g6-last-keep-"))
snapshots = {
    **{f"w{w}.json": dict(snapshot(w, INC5), arm="EGATE") for w in analysis.BUDGET_POINTS},
    "final.json": dict(snapshot(20, INC7, final=True), arm="EGATE"),
}
chunk = write_campaign(root / "chunk", snapshots)
audit = G.audit_campaign(chunk / "campaigns" / INSTANCE, root / "audit",
                         sigma_node=SIGMA, runner=FakeRunner())
curve = {str(row["w"]): row for row in audit["w"]}
final = audit["final"]
print(json.dumps({
    "curve20_y_raw": curve["20"]["y_raw"],
    "final_y_raw": final["y_raw"],
    "curve20_config": curve["20"]["config_sha256"],
    "final_config": final["config_sha256"],
    "final_audit_record": final["audit_record"],
}, sort_keys=True))
assert curve["20"]["y_raw"] != final["y_raw"]
assert curve["20"]["config_sha256"] != final["config_sha256"]

summary = _summary("D.3a", "EGATE", NODE, 6201, start_config_hash=final["start_config_sha256"],
                   final_config_hash=final["config_sha256"], last_keep_run=20, keeps=1)
by_point = {**curve, "final": final, "keep": [{"keep_run": 20, **final}]}
try:
    table.build_row("D.3a", summary, by_point)
except table.OutcomeTableError as exc:
    assert "one canonical audit" in str(exc)
    print(f"G7 refuses: {exc}")
else:
    raise AssertionError("expected G7 to refuse")

complete = synthetic_table()
row = next(r for r in complete["rows"] if r["arm"] == "EGATE" and r["node"] == NODE and r["instance_seed"] == 6201)
row["y_raw"] = final["y_raw"]
row["y_raw_w"] = {key: record["y_raw"] for key, record in curve.items()}
try:
    analysis.validate_table(complete, "D.3a")
except analysis.D3InputError as exc:
    assert "must equal y_raw" in str(exc)
    print(f"D.3 analysis refuses: {exc}")
else:
    raise AssertionError("expected D.3 analysis to refuse")
```
