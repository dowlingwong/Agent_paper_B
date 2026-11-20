"""Generator of w2_execute_all_golden_a15300ca.json (not a test). Run from a checkout of a15300ca:
    cd <a15300ca checkout> && AR_HARNESS_ROOT=<harness a3fedbb> python -I -c "import sys; sys.path.insert(0, '.'); sys.argv = ['x', 'a15300ca', '<out.json>']; exec(open('<this file>').read())"
so that r1 is imported from the base checkout (FEATURIZER_VERSION c3_features/v2 there)."""
import json, random, sys
from r1.c3 import features as F
from r1.c3.features import NodeContext, ReplayProposal, ReplayView, featurize_view
from r1.c3.train import serialize as S

W = 20
CTX = NodeContext(node="digits_mlp", start_files={"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"},
                  sigma_node=0.0075, runs_total=W, memory_mode="none")
GRID = {"HIDDEN_UNITS": ["32", "64", "128"], "ALPHA": ["1e-4", "1e-3", "1e-2"], "MAX_ITER": ["40", "80", "160"]}

def ledger(seed, failed):
    rng = random.Random(seed); cfg = {"HIDDEN_UNITS": "32", "ALPHA": "1e-4", "MAX_ITER": "40"}; rows = []; best = None
    for b in range(1, W + 1):
        key = rng.choice(sorted(cfg)); new = rng.choice([v for v in GRID[key] if v != cfg[key]])
        metric = round(0.85 + 0.1 * rng.random(), 4); fail = (b - 1) in failed and best is not None
        kept = (best is None or metric > best) and not fail
        rows.append({"budget_index": b, "decision": "failed_invalid" if fail else "kept" if kept else "discarded",
                     "parsed_metrics": {} if fail else {"val_score": metric}, "current_best_before": best,
                     "delta_vs_best": None if (fail or best is None) else metric - best, "worker_mode": "local",
                     "extra": {"manager": {"structured_edit": {"symbol": key, "old": cfg[key], "new": new, "path": "train.py"}}}})
        if kept: cfg[key], best = new, metric
    return rows

class Tok:
    def __call__(self, text, add_special_tokens=False): return {"input_ids": text.split()}

def views(rows):
    out = []
    for i in range(len(rows)):
        edit = rows[i]["extra"]["manager"]["structured_edit"]
        v = ReplayView(budget_index=rows[i]["budget_index"], ledger_prefix=tuple(rows[:i]), current_best=rows[i]["current_best_before"],
                       proposal=ReplayProposal(extra={"structured_edit": edit}))
        res = featurize_view(v, CTX)
        if res is None: out.append(None); continue
        p = S.serialize_view(v, CTX, tokenizers={"fake": Tok()})
        out.append({"features_hash": F.features_hash(res.features), "budget_frac_left": res.features["budget_frac_left"],
                    "text": S.render_text(p), "meta": json.loads(json.dumps(p.meta, default=str))})
    return out

camps = []
for seed, failed in [(201, [4, 9, 13]), (202, [3, 11]), (203, []), (204, [6, 7, 15])]:
    rows = ledger(seed, set(failed)); camps.append({"seed": seed, "rows": rows, "expected": views(rows)})
json.dump({"generated_at_commit": sys.argv[1], "runs_total": W, "campaigns": camps}, open(sys.argv[2], "w"), indent=1, sort_keys=True)
