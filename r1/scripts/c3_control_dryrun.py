#!/usr/bin/env python3
"""Desktop DRYRUN of the C3 control interface end to end (RUNBOOK Track H.9). AI-assisted (Claude). DRYRUN; never evidence.

What runs (all CPU, no model, no GPU, no SSH):

* the fake ``llama-server`` (``r1/scripts/c3_fake_llama_server.py``; OpenAI-compatible,
  no inference) as the manager model behind the harness ``llamacpp`` provider and as the
  endpoint of the A4 typed questions and the LLM self-control side queries;
* two fake forecast sidecars (``r1.c3.serve`` with ``FakeLoader``; sha256-pinned fixture
  files, fixed distributions) for A5 and A6; the A6 sidecar answers its second call too late
  (1.5 s > the 1 s client timeout), so the fallback path is exercised once;
* real ``LocalWorker`` CPU runs on two nodes (``digits_mlp``, ``openml_breast_w``), one
  instance each, W = 4 worker runs, LLM-call cap 4W, trial budget = the cap (never binding,
  review F6), verify runs r = 1, memory ``append_only_summary``, skip display ``one_line/v1``;
  the C3 arms verify at E2 with D23's KG rule (review F3); LLM self-control acts at E1/E2 only
  (review F5); the hybrid re-screens its revision (review F4);
* arms A0 (rho), A1-A3 (fitted on the 19 Oct pilot table), A4 (typed questions), A5/A6
  (sidecar; A6 deployed as its mode bin with a DRYRUN tau_node = 1 sigma_node), and the H.7
  direct-action arms ``awr_direct``, ``llm_self`` and ``hybrid`` (a proposal) -- every arm through
  the harness ``Controller.decide``;
* one interruption: after ``--interrupt-after`` completed campaigns, once the next campaign has
  written a ledger record, the runner's process group is SIGKILLed and the services are stopped
  (as after a preemption); the resume starts new services, keeps completed campaigns byte for byte
  and re-runs the interrupted campaign whole;
* ``matching_report`` over the 20 campaigns (identical instances, W, LLM cap, information set).

Stages (each fits in one short shell call): ``--stage start`` (prepare, run until the
interruption), ``--stage resume`` (finish and report), ``--stage all`` (both in one process).
Only ``summary.json`` and the campaign ledgers/events (gzipped) leave the work directory (``--out``).
Refused on Ada; the work directory must be a marked temporary directory.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

LABEL = "DRYRUN"
ARMS = ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "awr_direct", "llm_self", "hybrid")
NODES = ("digits_mlp", "openml_breast_w")
W = 4
LLM_CAP = 4 * W
TRIALS = LLM_CAP  # review F6 (D1): W and the LLM-call cap bind; the trial budget (= the cap) never does
VERIFY_RUNS = 1   # harness verify runs r for every arm (with r = 2 KG verify never pays at g = 0.1 sigma_node)
MEMORY_MODE = "append_only_summary"
INFO_SET = "control_view/v1+node_context/v1"
ALIAS = "dryrun-manager"
PILOT_TABLE = REPO / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
DATA_CACHE = "experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache"
A6_TAU_Z = 1.0  # DRYRUN constant (z units); the real tau_node is dev-estimated (C3_DESIGN §5)
HYBRID_REVISIONS = 2
# Fixed sidecar distributions (DRYRUN): A5 favourable on both nodes, A6 favourable on digits only.
FIXED = {"A5": {"default": [0.05, 0.0, 0.02, 0.05, 0.1, 0.18, 0.2, 0.2, 0.12, 0.05, 0.02, 0.01]},
         "A6": {"default": [0.05, 0.0, 0.02, 0.05, 0.1, 0.18, 0.2, 0.2, 0.12, 0.05, 0.02, 0.01],
                "by_node": {"openml_breast_w": [0.3, 0.2, 0.2, 0.15, 0.1, 0.04, 0.01, 0, 0, 0, 0, 0]}}}


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def campaign_name(arm: str, node: str) -> str:
    return f"{arm}__{node}"


def check_host(work: Path) -> None:
    if platform.node().split(".")[0] == "ucrtasl":
        raise SystemExit("STOP: DRYRUN is forbidden on Ada")
    temp = Path(tempfile.gettempdir()).resolve()
    if not work.resolve().is_relative_to(temp) or work.resolve() == temp or not (work / ".dryrun").is_file():
        raise SystemExit("STOP: the work directory must be a marked temporary directory")


# ---------------------------------------------------------------------------
# services
# ---------------------------------------------------------------------------

def start_services(work: Path) -> dict:
    from r1.c3.serve import FakeLoader, Pin, Sidecar
    port = free_port()
    log = open(work / f"llama_server_{int(time.time())}.log", "w")
    env = {**os.environ, "R1_FAKE_OLLAMA_ROOT": str(work), "C3_FAKE_LLAMA_LOAD_SECONDS": "0.2"}
    proc = subprocess.Popen([sys.executable, str(REPO / "r1/scripts/c3_fake_llama_server.py"), "-m",
                             str(work / "fixture.gguf"), "--host", "127.0.0.1", "--port", str(port), "-ngl", "99",
                             "-c", "4096", "--alias", ALIAS, "-np", "1"], stdout=log, stderr=subprocess.STDOUT,
                            env=env, start_new_session=True)
    import urllib.request
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with urllib.request.urlopen(url + "/health", timeout=1) as r:
                if r.status == 200:
                    break
        except Exception:  # noqa: BLE001
            time.sleep(0.1)
    else:
        raise SystemExit("STOP: fake llama-server did not become healthy")
    sidecars, urls, digests = [], {}, {}
    for name in ("A5", "A6"):
        kw = {"delay_s": 1.5, "delay_calls": {2}} if name == "A6" else {}
        sc = Sidecar(Pin.load(work / "sidecar" / name / f"{name}_pin.json"), FakeLoader(FIXED[name]), **kw)
        urls[name], digests[name] = sc.start(), sc.digest
        sidecars.append(sc)
    runtime = {"llama_url": url + "/v1", "llama_pid": proc.pid, "sidecars": urls, "sidecar_digests": digests,
               "started_utc": utc()}
    (work / "runtime.json").write_text(json.dumps(runtime, indent=1))
    return {"proc": proc, "sidecars": sidecars, "runtime": runtime, "log": log}


def stop_services(services: dict) -> None:
    for sc in services["sidecars"]:
        sc.stop()
    proc = services["proc"]
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
    services["log"].close()


def prepare(work: Path) -> None:
    from r1.c3.serve import write_fake_pin
    (work / ".dryrun").write_text("Track H control DRYRUN\n")
    (work / "fixture.gguf").write_bytes(b"DRYRUN GGUF fixture; not a model\n")
    for name in ("A5", "A6"):
        write_fake_pin(work / "sidecar" / name, name=name, base=f"dryrun-base-{name}@0")
    state = {"label": LABEL, "created_utc": utc(), "arms": list(ARMS), "nodes": list(NODES), "W": W,
             "trials": TRIALS, "llm_cap": LLM_CAP, "sessions": [], "interruption": None}
    (work / "state.json").write_text(json.dumps(state, indent=1))


# ---------------------------------------------------------------------------
# the runner (a child process; killed once by the driver)
# ---------------------------------------------------------------------------

def _data_sources():
    from r1.harness import harness_root
    return [harness_root(), REPO.parent / "autoresearch_harness", REPO.parents[2] / "autoresearch_harness"]


def _node_copy(node: str, dest: Path) -> Path:
    from r1.harness import harness_root
    shutil.copytree(harness_root() / "nodes" / node, dest, ignore=shutil.ignore_patterns("__pycache__",
                                                                                         ".autoresearch_artifacts"))
    if node.startswith("openml_") and not (dest / "data_cache").exists():
        for src in _data_sources():  # read-only copy of the ignored OpenML cache
            cache = Path(src) / DATA_CACHE.format(node=node)
            if cache.is_dir():
                shutil.copytree(cache, dest / "data_cache")
                break
        else:
            raise SystemExit(f"STOP: no data cache for {node}")
    return dest


def build_arms(runtime: dict) -> dict:
    """arm -> factory(node_ctx, noise) -> (controller kwargs, prior description)."""
    import numpy as np
    from r1.c3 import offline_eval as OE
    from r1.c3.control import AWRDirectController, RuleController, c3_budgets, fit_awr_direct
    from r1.c3.env import label_rows
    from r1.c3.prior_model import ManagerQuestionPrior, SidecarPrior, TableArmPrior, chat_client
    from r1.llm_control import LLMSelfController
    from r1.harness import import_harness
    import_harness()
    from autoresearch.control_plane.action_versions import ActionVersions
    from autoresearch.control_plane.controller import ContinueController

    rows = OE.assemble(PILOT_TABLE)
    priors = {a: TableArmPrior.fit(a, rows) for a in ("A1", "A2", "A3")}
    lab = [r for r in label_rows(PILOT_TABLE) if r.get("delta_label") is not None]  # duplicates have no label
    awr = fit_awr_direct(lab)  # trains on delta_label, the label half of the audit seeds
    llm = chat_client(runtime["llama_url"], ALIAS)
    default_versions = {"action_versions": ActionVersions.new_campaign(), "skip_display": "one_line/v1",
                        "verify_runs": VERIFY_RUNS, **c3_budgets(W, LLM_CAP, TRIALS)}

    def rule(prior, ctx, noise, **kw):
        ctl = RuleController(prior, ctx, sigma_cmp={"local": noise["sigma_local"],
                                                    "structural": noise["sigma_structural"]},
                             fallback=priors["A1"], verify_runs=VERIFY_RUNS, **kw)
        return ctl.campaign_kwargs(W=W, llm_cap=LLM_CAP, trials=TRIALS), {
            "prior_version": prior.version, "prior_digest": prior.digest, "controller_version": ctl.version}

    def sidecar(name):
        return SidecarPrior(runtime["sidecars"][name], priors["A1"], name=name,
                            expected_digest=runtime["sidecar_digests"][name])

    return {
        "A0": lambda ctx, noise: ({"controller": ContinueController(), **default_versions},
                                  {"controller_version": "continue/v1", "keep_rule": "default/v1 (rho)"}),
        "A1": lambda ctx, noise: rule(priors["A1"], ctx, noise),
        "A2": lambda ctx, noise: rule(priors["A2"], ctx, noise),
        "A3": lambda ctx, noise: rule(priors["A3"], ctx, noise),
        "A4": lambda ctx, noise: rule(ManagerQuestionPrior(llm, priors["A1"], model_id=f"llamacpp/{ALIAS}"), ctx, noise),
        "A5": lambda ctx, noise: rule(sidecar("A5"), ctx, noise),
        "A6": lambda ctx, noise: rule(sidecar("A6"), ctx, noise, greedy_bin=True,
                                      tau_node=A6_TAU_Z * noise["sigma_node"]),
        "awr_direct": lambda ctx, noise: ({"controller": AWRDirectController(awr, ctx), **default_versions},
                                          {"controller_version": "awr_direct/v1"}),
        "llm_self": lambda ctx, noise: ({"controller": LLMSelfController(llm, epochs=("E1", "E2")),
                                         **default_versions},
                                        {"controller_version": "llm_self/v1", "epochs": ["E1", "E2"]}),
        "hybrid": lambda ctx, noise: rule(priors["A3"], ctx, noise, hybrid_revise=True,
                                          revision_budget=HYBRID_REVISIONS),
    }


def run_campaigns(work: Path) -> None:
    from r1.c3.dataset import noise_table
    from r1.c3.features import NodeContext
    from r1.harness import import_harness
    from r1.headroom.e1b_collect import _instance_seed, make_manager
    harness = import_harness()
    from autoresearch.control_plane.budget import ComputeBudget
    from autoresearch.control_plane.campaign import run_real_campaign
    from autoresearch.memory.event_store import CampaignEventStore
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import LocalWorker

    runtime = json.loads((work / "runtime.json").read_text())
    os.environ["LLAMACPP_BASE_URL"] = runtime["llama_url"]
    noise = noise_table()
    arms = build_arms(runtime)
    for node in NODES:
        for arm in ARMS:
            name = campaign_name(arm, node)
            d = work / "campaigns" / name
            if (d / "DONE.json").exists():
                continue
            rerun = d.exists()
            if rerun:
                shutil.rmtree(d)  # an interrupted campaign is re-run whole
            d.mkdir(parents=True)
            seed = _instance_seed(node, 0)
            node_dir = _node_copy(node, d / "node")
            spec = load_registered_node(node, repo_root=harness)
            ctx = NodeContext(node=node, start_files={p: (node_dir / p).read_text() for p in spec.editable_paths},
                              sigma_node=noise[node]["sigma_node"], runs_total=W, memory_mode=MEMORY_MODE)
            kwargs, desc = arms[arm](ctx, noise[node])
            manager = make_manager(node, seed, 0, {"kind": "langgraph", "model": f"llamacpp/{ALIAS}",
                                                   "temperature": 0.2})
            t0 = time.time()
            assert kwargs["budget"] == TRIALS and kwargs["compute_budget"].max_worker_runs == W \
                and kwargs["compute_budget"].max_llm_calls == LLM_CAP
            run_real_campaign(node_spec=spec, campaign_id=f"{name}__s{seed}",
                              manager_mode="langgraph_manager", memory_mode=MEMORY_MODE,
                              records_path=d / "trials.jsonl",
                              worker=LocalWorker(node_root=node_dir, artifact_dir=d / "art", train_seed=seed,
                                                 split_seed=seed),
                              proposal_backend=manager,
                              event_store=CampaignEventStore(d / "events.jsonl"), **kwargs)
            manifest = {"label": LABEL, "arm": arm, "node": node, "instance": f"{node}__s{seed}", "W": W,
                        "trials": TRIALS, "llm_cap": LLM_CAP, "verify_runs": VERIFY_RUNS, "memory_mode": MEMORY_MODE,
                        "information_set": INFO_SET, "rerun_after_interruption": rerun,
                        "action_versions": kwargs["action_versions"].to_dict(), **desc}
            from r1.c3.control import declare_skip_display
            declare_skip_display(manifest, kwargs["skip_display"])
            (d / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
            (d / "DONE.json").write_text(json.dumps({"utc": utc(), "seconds": round(time.time() - t0, 2),
                                                     "trials_sha256": sha256(d / "trials.jsonl"),
                                                     "events_sha256": sha256(d / "events.jsonl")}))
            print(f"done {name} in {time.time() - t0:.1f}s", flush=True)


# ---------------------------------------------------------------------------
# the driver
# ---------------------------------------------------------------------------

def launch_runner(work: Path) -> subprocess.Popen:
    log = open(work / f"runner_{int(time.time() * 1000)}.log", "w")
    return subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--runner", "--work", str(work)],
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True, cwd=REPO,
                            env={**os.environ, "PYTHONPATH": str(REPO)})


def done_campaigns(work: Path) -> list[str]:
    return sorted(p.parent.name for p in (work / "campaigns").glob("*/DONE.json"))


def stage_start(work: Path, interrupt_after: int, deadline_s: float) -> dict:
    state = json.loads((work / "state.json").read_text())
    services = start_services(work)
    proc = launch_runner(work)
    order = [campaign_name(a, n) for n in NODES for a in ARMS]
    t0 = time.time()
    interruption = None
    try:
        while time.time() - t0 < deadline_s:
            if proc.poll() is not None:
                raise SystemExit(f"STOP: runner exited (rc {proc.returncode}) before the interruption")
            done = done_campaigns(work)
            if len(done) >= interrupt_after:
                nxt = order[len(done)]
                ledger = work / "campaigns" / nxt / "trials.jsonl"
                if ledger.exists() and ledger.read_text().strip():
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(10)
                    interruption = {"utc": utc(), "signal": "SIGKILL (runner process group)",
                                    "completed": done, "in_progress": nxt,
                                    "partial_records": len(ledger.read_text().splitlines()),
                                    "completed_sha256": {c: json.loads((work / "campaigns" / c / "DONE.json")
                                                                       .read_text())["trials_sha256"] for c in done}}
                    break
            time.sleep(0.05)
        else:
            raise SystemExit("STOP: deadline before the interruption")
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
        stop_services(services)  # as after a preemption: the services go too
    state["interruption"] = interruption
    state["sessions"].append({"stage": "start", "started": services["runtime"]["started_utc"], "ended": utc(),
                              "llama_pid": services["runtime"]["llama_pid"]})
    (work / "state.json").write_text(json.dumps(state, indent=1))
    return state


def stage_resume(work: Path, deadline_s: float) -> dict:
    state = json.loads((work / "state.json").read_text())
    if not state.get("interruption"):
        raise SystemExit("STOP: no recorded interruption to resume from")
    services = start_services(work)
    try:
        proc = launch_runner(work)
        try:
            proc.wait(deadline_s)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            raise SystemExit("STOP: resume deadline reached")
        if proc.returncode != 0:
            raise SystemExit(f"STOP: resumed runner failed (rc {proc.returncode}); see the runner log")
    finally:
        stop_services(services)
    state["sessions"].append({"stage": "resume", "started": services["runtime"]["started_utc"], "ended": utc(),
                              "llama_pid": services["runtime"]["llama_pid"]})
    (work / "state.json").write_text(json.dumps(state, indent=1))
    return state


def report(work: Path, out: Path) -> dict:
    from r1.branch.matching import ArmDescriptor, matching_report
    from r1.c3.accounting import campaign_usage
    from r1.harness import harness_commit, harness_root
    state = json.loads((work / "state.json").read_text())
    order = [campaign_name(a, n) for n in NODES for a in ARMS]
    missing = [c for c in order if not (work / "campaigns" / c / "DONE.json").exists()]
    checks, problems = {}, []
    if missing:
        problems.append(f"campaigns not completed: {missing}")
    intr = state["interruption"] or {}
    unchanged = {c: sha256(work / "campaigns" / c / "trials.jsonl") == h
                 for c, h in (intr.get("completed_sha256") or {}).items()}
    checks["interruption_recorded"] = bool(intr)
    checks["completed_campaigns_unchanged_after_resume"] = bool(unchanged) and all(unchanged.values())
    rerun = json.loads((work / "campaigns" / intr["in_progress"] / "manifest.json").read_text())["rerun_after_interruption"] \
        if intr else False
    checks["interrupted_campaign_rerun_whole"] = bool(rerun)
    usage, per_campaign, descriptors, instances = [], {}, {}, {}
    for c in order:
        d = work / "campaigns" / c
        man = json.loads((d / "manifest.json").read_text())
        rows = [json.loads(x) for x in (d / "trials.jsonl").read_text().splitlines() if x.strip()]
        events = [json.loads(x) for x in (d / "events.jsonl").read_text().splitlines() if x.strip()]
        u = campaign_usage(d / "trials.jsonl", d / "events.jsonl", arm=man["arm"], instance=man["instance"],
                           information_set=man["information_set"], worker_run_cap=W, llm_call_cap=LLM_CAP,
                           manager_deterministic=False, trial_budget=man["trials"])
        usage.append(u)
        instances.setdefault(man["arm"], []).append(man["instance"])
        e1 = [e["payload"] for e in events if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E1"]
        started = [e["payload"] for e in events if e["event_type"] == "campaign_started"][0]
        skip_reasons = {}
        for r in rows:
            reason = (r["extra"].get("control") or {}).get("skip_reason") or (
                (r["extra"].get("control") or {}).get("reason") if r["decision"] == "skipped" else None)
            if r["decision"] == "skipped":
                reason = reason or "controller_skip_without_reason"  # e.g. LLM self-control gives none
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        origins = {}
        for r in rows:
            src = ((r["extra"].get("keep_rule") or {}).get("prior") or {}).get("source")
            if src:
                key = src.rsplit(":", 1)[-1]
                origins[key] = origins.get(key, 0) + 1
        # one forecast for E1 and E2: the keep prior equals the E1 decision's (mu, tau, sigma)
        e1_by_trial = {e["trial_id"]: e["payload"] for e in events
                       if e["event_type"] == "control_decision" and e["payload"]["epoch"] == "E1"}
        same = []
        for r in rows:
            prior = (r["extra"].get("keep_rule") or {}).get("prior") or {}
            if str(prior.get("source", "")).endswith(":e1_forecast"):
                det = e1_by_trial[r["trial_id"]].get("detail") or {}
                same.append((prior["mu"], prior["tau"], prior["sigma"]) == (det.get("mu"), det.get("tau"), det.get("sigma")))
        per_campaign[c] = {
            "arm": man["arm"], "node": man["node"], "instance": man["instance"],
            "decisions": {k: sum(1 for r in rows if r["decision"] == k) for k in ("kept", "discarded", "skipped",
                                                                                  "failed_invalid")},
            "skip_reasons": skip_reasons, "keep_prior_origins": origins, "e1_e2_same_forecast": all(same),
            "e1_e2_same_forecast_trials": len(same),
            "e1_actions": {a: sum(1 for p in e1 if p["action"] == a) for a in ("continue", "skip", "revise")},
            "e2_verify_considered": sum(1 for e in events if e["event_type"] == "control_decision"
                                        and e["payload"]["epoch"] == "E2"
                                        and "verify" in (e["payload"].get("detail") or {})
                                        and "voi" in e["payload"]["detail"]["verify"]),
            "verifies": sum(1 for r in rows if (r["extra"].get("control") or {}).get("verify")),
            "rescreened_skips": sum(1 for r in rows if (r["extra"].get("control") or {}).get("rescreened_after_revise")),
            "trials": len(rows),
            "e1_details_complete": all({"probs", "pi", "mu", "tau", "t_star", "V", "g", "prior_version",
                                        "prior_digest"} <= set(p.get("detail") or {}) for p in e1
                                       if "probs" in (p.get("detail") or {})),
            "a4_fallbacks": sum(1 for p in e1 if str((p.get("detail") or {}).get("fallback") or "").startswith("a4_")),
            "ended_on": None,
            "llm_cap_fallbacks": sum(1 for p in e1 if (p.get("detail") or {}).get("fallback") == "llm_cap_exhausted"),
            "prior_unavailable": u.prior_unavailable, "worker_runs": u.worker_runs, "llm_calls": u.llm_calls,
            "controller_llm_calls": u.controller_llm_calls, "skip_display": started.get("skip_display"),
            "manifest_skip_display": man.get("skip_display"), "prior_digest": man.get("prior_digest"),
            "controller_version": man.get("controller_version"), "rerun_after_interruption": man["rerun_after_interruption"],
            "trials_sha256": sha256(d / "trials.jsonl"),
        }
        descriptors[man["arm"]] = ArmDescriptor(name=man["arm"], family=man["arm"], information_set=INFO_SET,
                                                spending_rule="harness_campaign/v1", intervention_cap=None,
                                                compute_budget=W, llm_call_cap=LLM_CAP, tuning_budget=0,
                                                dev_instances="c3_audit_pilot_20261019T001338Z", instances=None)
    inst_hash = {a: hashlib.sha256(json.dumps(sorted(v)).encode()).hexdigest()[:16] for a, v in instances.items()}
    descriptors = [ArmDescriptor(**{**d.__dict__, "instances": inst_hash[a]}) for a, d in descriptors.items()]
    try:
        matching = matching_report(descriptors, usage)
    except Exception as exc:  # noqa: BLE001
        matching = {"matched": False, "error": str(exc)}
        problems.append(f"matching_report failed: {exc}")
    checks["matching_report_passes"] = bool(matching.get("matched"))  # includes: no campaign ended on trials
    for c, v in per_campaign.items():
        u = next(x for x in usage if x.arm == v["arm"] and x.instance == v["instance"])
        from r1.branch.matching import _ended_on
        v["ended_on"] = _ended_on(u)
    checks["no_campaign_ended_on_the_trial_budget"] = all(v["ended_on"] != "trial_budget"
                                                          for v in per_campaign.values())
    checks["c3_arms_considered_kg_verify"] = all(v["e2_verify_considered"] > 0 for v in per_campaign.values()
                                                 if v["arm"] in ("A1", "A2", "A3", "A4", "A5", "A6", "hybrid")
                                                 and v["decisions"]["kept"] + v["decisions"]["discarded"] > 1)
    checks["every_arm_ran"] = sorted({v["arm"] for v in per_campaign.values()}) == sorted(ARMS)
    checks["skip_display_declared_everywhere"] = all(v["skip_display"] == v["manifest_skip_display"] == "one_line/v1"
                                                     for v in per_campaign.values())
    checks["e1_e2_one_forecast"] = all(v["e1_e2_same_forecast"] for v in per_campaign.values())
    checks["e1_details_complete"] = all(v["e1_details_complete"] for v in per_campaign.values())
    checks["a4_typed_answers_parsed"] = all(v["a4_fallbacks"] == 0 for v in per_campaign.values()
                                            if v["arm"] == "A4")
    checks["hybrid_revised_at_least_once"] = any(v["e1_actions"]["revise"] for v in per_campaign.values()
                                                 if v["arm"] == "hybrid")
    checks["prior_unavailable_logged_and_survived"] = sum(v["prior_unavailable"] for v in per_campaign.values()) >= 1
    checks["sidecar_digests_pinned"] = all(v["prior_digest"] == json.loads((work / "runtime.json").read_text())[
        "sidecar_digests"][v["arm"]] for v in per_campaign.values() if v["arm"] in ("A5", "A6"))
    for key, ok in checks.items():
        if not ok:
            problems.append(f"check failed: {key}")
    paper = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=no"],
                                capture_output=True, text=True).stdout.strip())
    summary = {"label": LABEL, "banner": "DRYRUN — Track H.9 plumbing check; ENGINEERING_ONLY, never evidence.",
               "ai_assisted": "AI-assisted (Claude)", "written_utc": utc(),
               "paper": {"commit": paper, "dirty": dirty}, "harness": {"root": str(harness_root()), **harness_commit()},
               "python": platform.python_version(), "platform": platform.platform(),
               "design": {"arms": list(ARMS), "nodes": list(NODES), "instances_per_node": 1, "W": W, "trials": TRIALS,
                          "llm_call_cap": LLM_CAP, "verify_runs": VERIFY_RUNS,
                          "llm_self_epochs": ["E1", "E2"], "c3_verify": "D23 KG (KGIndexPolicy), posterior_mean/v1", "memory_mode": MEMORY_MODE, "skip_display": "one_line/v1",
                          "information_set": INFO_SET, "manager": f"llamacpp/{ALIAS} (fake llama-server, no inference)",
                          "sidecars": "r1.c3.serve FakeLoader, fixed distributions, sha256-pinned fixtures; A6 "
                                      "answers its 2nd call after 1.5 s (> 1 s timeout)",
                          "A1_A3_fitted_on": str(PILOT_TABLE.relative_to(REPO)), "A6_tau_z": A6_TAU_Z,
                          "hybrid": f"PROPOSAL: prior decides whether; revise instead of skip within "
                                    f"{HYBRID_REVISIONS} revisions"},
               "state": state, "checks": checks, "problems": problems, "pass": not problems,
               "matching_report": matching, "campaigns": per_campaign}
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
    for c in order:
        d = work / "campaigns" / c
        for f in ("trials.jsonl", "events.jsonl", "manifest.json"):
            if (d / f).exists():
                (out / "campaigns" / c).mkdir(parents=True, exist_ok=True)
                with gzip.GzipFile(out / "campaigns" / c / (f + ".gz"), "wb", mtime=0) as fh:
                    fh.write((d / f).read_bytes())
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["all", "start", "resume", "report"], default="all",
                    help="report = rewrite summary.json from a finished work directory")
    ap.add_argument("--work", default=None, help="work directory (a new marked temp dir by default)")
    ap.add_argument("--out", default=None, help="where summary.json goes (stage resume/all)")
    ap.add_argument("--interrupt-after", type=int, default=7)
    ap.add_argument("--deadline", type=float, default=150.0)
    ap.add_argument("--runner", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.runner:
        work = Path(args.work)
        check_host(work)
        run_campaigns(work)
        return 0
    if args.stage in ("all", "start"):
        work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="r1_c3_control_dryrun_"))
        work.mkdir(parents=True, exist_ok=True)
        if any(work.iterdir()):
            raise SystemExit(f"STOP: {work} is not empty")
        (work / ".dryrun").write_text("Track H control DRYRUN\n")
        check_host(work)
        prepare(work)
        state = stage_start(work, args.interrupt_after, args.deadline)
        print(json.dumps({"work": str(work), "interruption": state["interruption"]}, indent=1))
        if args.stage == "start":
            return 0
    else:
        work = Path(args.work)
        check_host(work)
    if args.stage != "report":
        stage_resume(work, args.deadline)
    out = Path(args.out) if args.out else REPO / "results/r1/engineering" / \
        f"c3_control_dryrun_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    summary = report(work, out)
    print(json.dumps({"out": str(out), "pass": summary["pass"], "checks": summary["checks"],
                      "problems": summary["problems"]}, indent=1))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
