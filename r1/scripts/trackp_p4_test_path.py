"""Track P P.4 phase 1: the synthetic-label path of the test evaluator inside the P.4 job (P4-PHASE1-TEST A).
ENGINEERING_ONLY; AI-assisted (Claude).

Given a data directory built with **synthetic** labels (``trackp.py sft-data --labels synthetic``) on the pinned
table, and a short ``sft-dev`` run on it, this replays the test proposals' prompts from the sweep
(``sft_test_eval.replay_test_prompts``), loads the run's best model through the same builder as ``trackp.py``
(under the GPU lease), writes the bound logits file (``predict_test``) and the test report with its one-read ledger
(``evaluate_test``; the ledger ``<ledger-dir>/trackp_p4_test_reads.jsonl``, one per table). A data directory with real
labels is refused here before anything is read (the evaluator also refuses a real-label read on ENGINEERING_ONLY
data in phase 1). Called by ``r1/scripts/htcondor/trackp_p4/p4_lib.py`` (``test_path``); returns a JSON summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for name in ("--data", "--table", "--run", "--arm", "--sweep", "--paper-root", "--classification",
                 "--host-config", "--ledger-dir", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    from r1.c3 import dataset as D
    from r1.c3.train import run as R
    from r1.c3.train import serialize as S
    from r1.c3.train import sft_data as SD
    from r1.c3.train import sft_test_eval as TE
    from r1.scripts import trackp as TP

    manifest = json.loads((Path(a.data) / "sft_data.json").read_bytes())
    if (manifest.get("labels") or {}).get("kind") != "synthetic":
        raise SystemExit("STOP: the P.4 phase-1 test path runs on synthetic labels only (P4-PHASE1-TEST A)")
    rows, _ = SD.load_table(a.table, (manifest.get("table") or {}).get("sha256") or {})
    source = SD.SyntheticLabelSource(rows, seed=int((manifest.get("labels") or {}).get("seed", a.seed)))
    inputs = D.sweep_replay_inputs(a.sweep, paper_root=a.paper_root, classification=a.classification)
    prompts, replay = TE.replay_test_prompts(inputs, tokenizers=S.pool_tokenizers(), data_dir=a.data,
                                             table_dir=a.table, label_source=source)
    cfg = R.load_config(a.host_config)
    args = SimpleNamespace(tiny=False, family=None, base=a.arm, head_form="softmax12", seed=a.seed, cmd="sft-dev",
                           run_dir=a.run, cfg=cfg)
    stage_s = Path(a.run) / "stage_s"
    out = Path(a.out)
    lease_log: list = []
    with TP._lease(args, lease_log):
        model, _, _, base = TP._build(args, cfg)

        def loader(best: Path):
            model.load(best)
            return model
        TE.predict_test(loader, prompts, replay, stage_s, a.data, out / "predictions.json", arm=a.arm,
                        model_record=base)
    report = TE.evaluate_test(a.data, a.table, source, out / "predictions.json", stage_s, out / "report", arm=a.arm,
                              ledger=Path(a.ledger_dir) / TE.LEDGER_NAME)
    text = (out / "report" / "test_report.json").read_bytes()
    return {"labels": "synthetic", "arm": a.arm, "report_sha256": hashlib.sha256(text).hexdigest(),
            "test_n": report["populations"].get("primary"), "evaluation_seeds_read": report["evaluation_seeds_read"],
            "lease": lease_log}


if __name__ == "__main__":
    print(json.dumps(main()))
