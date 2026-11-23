"""G.5 T1 label job on the TASL pair (G.5 code unit part 3b-1): campaign waves, audit planning and chunks, E5,
diagnostics, the STOP counters and K uniformity. AI-assisted (Claude). EVIDENCE table.

Authority: the G.5 authorization draft revision 8 (``docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md``) §3,
§4, §6, §9; the switch of part 3a (``g5_tasl.launch``) gates every entry point here. Nothing in this module runs a
real job unless the switch has passed: ``run_job`` is the switch's runner, and ``serve_launch`` is behind the same
note check and keys.

**Order per node** (§3; one worker slot, G5-SLOT A): ``campaigns-wave1`` (instances 1-4), ``audits-wave1`` (one
chunk per call; the plan is written once), the wave-1 checks on the diagnostics, ``campaigns-wave2`` (instances
5-12), ``audits-wave2``, the checks again. A job refuses to start out of order, after a node STOP, or when the
consumed worker GPU-hours already exceed the cap (STOP 9).

**Harness engines** (the G.5 harness commits G5-7 / G5-AR; a harness code unit, not in this repository): one new
module ``autoresearch.trackg.audit_g5`` (one of P5's two declared trackg additions, so that ``pilot_g4.py`` stays
G.4's) with the marker ``ENGINE_CONTRACT = "g5_tasl_engine_contract/1"`` and two subcommands, ``campaign`` (input
``trackg_g5_campaign/v1``; output the G.4 ledgers per instance and memory mode) and ``audit`` (input
``trackg_g5_audit_chunk/v1``; output ``rows.jsonl``, with infrastructure rows after 2 reruns), plus truncation as an
invalid proposal in ``manager_v2_diff.py``. ``engine_contract`` states it in full; ``check_engines`` refuses a family
checkout whose G.5 commit lacks the marker and both schemas. Only the named output members are ever read.

**Re-materialisation and audits** (§2.4, G5-AUDIT). From each campaign ledger: the baseline state (step 0), the
chain of kept diffs, and every audited proposal (A: kept, discarded and divergent incl. timed out; B: ``ok`` ones)
as (parent state = incumbent before the step, candidate state). The parent hash must equal the last kept state of
that ledger (integrity). Cross-instance groups (incumbent hash, candidate hash) are audited once. Under
``reuse_parent_runs`` every code state runs once per audit seed within the node (earlier waves included); otherwise
each group has its own candidate and parent units. E5 per group on the **label seeds only**.

**Diagnostics** (§6): counts and shares only, full nested schemas (``check_diagnostics``); no metric value, delta,
label or keep outcome per proposal, and no evaluation-seed outcome count (only planned run counts there). Campaign ledgers, audit rows and every log go only into ``out.tar``; ``out/`` is
removed after the tar is verified. Job code that opens an ``out.tar`` writes an access-log line (STOP 11).
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

import g1b_tasl as G
import g4_tasl as T4
import g5_tasl as S

L = G.L
Stop, NodeStop, TimingStop = G.Stop, G.NodeStop, G.TimingStop
RECORD_SCHEMA = "g5_tasl_job_record/1"
DIAG_CAMPAIGN = "g5_tasl_diagnostics_campaign/1"
DIAG_AUDIT = "g5_tasl_diagnostics_audit/1"
PLAN_SCHEMA = "g5_tasl_audit_plan/1"
CAMPAIGN_SCHEMA = "trackg_g5_campaign/v1"
CHUNK_SCHEMA = "trackg_g5_audit_chunk/v1"
ROW_SCHEMA = "trackg_g5_audit_row/v1"
LEDGER_SCHEMA = "trackg_v2_diff_campaign_ledger/v1"
ENGINE_FILE = "src/autoresearch/trackg/audit_g5.py"      # one of P5's two declared trackg additions
ENGINE_MODULE = "autoresearch.trackg.audit_g5"
ENGINES = {"campaign": (ENGINE_MODULE, "campaign", ENGINE_FILE), "audit": (ENGINE_MODULE, "audit", ENGINE_FILE)}
ENGINE_CONTRACT = "g5_tasl_engine_contract/1"              # the marker the engine module must carry, with both schemas
TRUNCATION_FILE = "src/autoresearch/trackg/manager_v2_diff.py"
RAN = ("kept", "discarded", "discarded_divergent")
AUDITED = {"A": RAN, "B": ("kept", "discarded")}
LEDGER_STOPS = ("stop_integrity", "stop_transport", "stop_unisolated", "baseline_failed")
ACCESS_PURPOSES = ("audit planning:", "wave E5:")
WAVE_INSTANCES = {1: range(1, 5), 2: range(5, 13)}
STARTUP_RESERVE_S = 1800
CHUNK_LIMIT_S = L.MAX_WALLTIME_S - 3600
TIMEOUT_FACTOR = 3.0


def utc(t: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t if t is not None else time.time()))


def job_parts(job: str) -> tuple[str, int]:
    if job not in S.JOBS:
        raise Stop(f"STOP: job must be one of {S.JOBS}")
    kind, wave = job.split("-wave")
    return kind, int(wave)


def engine_contract() -> dict:
    """What the harness unit must provide (G5-7 and G5-AR, byte-identical G.5 code):

    - ``audit_g5.py`` (a new trackg file, one of P5's two declared additions) with the constant ``ENGINE_CONTRACT =
      "g5_tasl_engine_contract/1"`` and two subcommands, so that ``pilot_g4.py`` stays G.4's:
      - ``campaign --campaign <trackg_g5_campaign/v1> --harness-root <h> --out <dir> [--gpu-uuid <uuid>]``: per
        instance and memory mode ``<out>/instance_<k>_<mode>/campaign_ledger.jsonl`` (the G.4 ledger schema, each
        executed run record with ``executed`` and ``elapsed_seconds_info_only``, each manager call with its
        ``request`` including ``cache_prompt``) and ``<out>/campaign_record.json`` (``stop``);
      - ``audit --chunk <trackg_g5_audit_chunk/v1> ...``: ``<out>/rows.jsonl`` and ``<out>/chunk_record.json``. A row
        of kind ``ok`` or ``divergent`` is an executed run with its isolation block (``check_effective``); an
        infrastructure failure is rerun up to 2 times and then written as ONE row of kind
        ``infrastructure_failure`` (``executed`` may be false, the isolation block may be absent). Only these
        members are read; anything else the engine writes under ``<out>`` (working copies, logs, binaries) stays in
        ``out.tar`` unread.
    - in ``manager_v2_diff.py`` (an engine file the labels may change): a reply whose completion reached the cap is an
      ``invalid_proposal`` (R1-EXAM-B1-TRUNCATION-INVALID)."""
    return {"file": ENGINE_FILE, "module": ENGINE_MODULE, "marker": ENGINE_CONTRACT,
            "subcommands": {k: c for k, (_, c, _) in ENGINES.items()},
            "schemas": [CAMPAIGN_SCHEMA, CHUNK_SCHEMA, ROW_SCHEMA], "truncation_invalid_in": TRUNCATION_FILE,
            "infrastructure_reruns": 2}


def check_engines(repo: Path, commit: str, git=G._sh) -> dict:
    """The family's G.5 commit carries the engine module with the contract marker and both input schemas."""
    for needle in (ENGINE_CONTRACT, CAMPAIGN_SCHEMA, CHUNK_SCHEMA):
        res = git(["git", "-C", str(repo), "grep", "-q", "-F", "-e", needle, commit, "--", ENGINE_FILE])
        if res.returncode != 0:
            raise Stop(f"STOP: the G.5 harness commit {commit[:8]} has no {ENGINE_FILE} carrying {needle!r} "
                       f"(harness code unit; engine_contract)")
    return engine_contract()


# =============================================================================================== instances, seeds
def wave_instances(spec: dict, wave: int) -> list[dict]:
    """The wave's campaign instances: instance k has training = split = manager seed 5100 + k (§5), once per memory
    mode (G5-MEM B: twin campaigns sharing instance seeds)."""
    lo = spec["instances"]["seeds"][0] - 1
    out = []
    for k in WAVE_INSTANCES[wave]:
        seed = lo + k
        if not S.INSTANCE_SEEDS[0] <= seed <= S.INSTANCE_SEEDS[1]:
            raise Stop(f"STOP 10: instance seed {seed} outside 5101-5112")
        for mode in spec["memory"]["modes"]:
            out.append({"instance": k, "train_seed": seed, "split_seed": seed, "manager_seed": seed,
                        "memory_mode": mode})
    return out


def campaign_dir_name(inst: dict) -> str:
    return f"instance_{inst['instance']}_{inst['memory_mode']}"


def node_timeout_basis(node: dict) -> float:
    return float(node["slowest_census_seconds"])        # census_slowest_x3 (R1-G1B-TIMEOUT); x 3 in the engine


def campaign_deadline_s(spec: dict, node: dict, wave: int) -> int:
    calls = len(wave_instances(spec, wave)) * (spec["campaign"]["W"] + 1)
    per = float(node["run_seconds"]) + float(spec["projection"]["llm_seconds_fallback"])
    return STARTUP_RESERVE_S + int(math.ceil(calls * per * 1.5))


def campaign_file(spec: dict, node: dict, wave: int, *, interpreter: str, cgroup_parent: str,
                  deadline_epoch: float) -> dict:
    """The ``trackg_g5_campaign/v1`` input of the campaign engine (decided options from the spec)."""
    c = spec["campaign"]
    if c["W_semantics"] != "manager_calls":
        raise Stop("STOP: G5-W B (worker runs with an LLM-call cap) is not built in the engine")
    return {"schema": CAMPAIGN_SCHEMA, "label": S.EVIDENCE, "run_id": spec["run_id"], "node": node["node"],
            "family": node["family"], "wave": wave, "spec_path": node["spec_path"], "node_dir": node["node_dir"],
            "node_spec_sha256": node["node_spec_sha256"], "committed_pin_sha256": node["committed_pin_sha256"],
            "data_manifest_sha256": node["data_manifest_sha256"], "proposal_schema": c["proposal_schema"],
            "extra_payload": {"cache_prompt": False}, "budget": c["W"], "w_semantics": c["W_semantics"],
            "instances": wave_instances(spec, wave), "max_tokens": c["max_tokens"], "temperature": c["temperature"],
            "measured_run_seconds": node_timeout_basis(node), "timeout_factor": TIMEOUT_FACTOR,
            "base_url": spec["proposer"]["server_url"], "model": T4.MODEL["alias"], "cgroup_parent": cgroup_parent,
            "interpreter": interpreter, "isolation_waivers": {}, "deadline_epoch": deadline_epoch,
            "memory_limit": f"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 "
                            f"(delegated scope {cgroup_parent})"}


# =============================================================================================== ledgers -> plan
def _final_run(entry: dict) -> dict:
    runs = entry.get("runs") or []
    if not runs:
        raise Stop(f"STOP: ledger step {entry.get('step')} has no run record")
    return runs[-1]


def parse_ledger(lines: list[str], label: str) -> dict:
    """One campaign ledger: the baseline state, and per step the decision, candidate diff and the two hashes.
    Re-materialisation: a step's parent is the last kept state before it (the baseline at first); its code state
    is that chain of kept diffs plus the candidate diff. The ledger's own hashes must agree (integrity)."""
    entries = [json.loads(x) for x in lines if x.strip()]
    if not entries or entries[0].get("step") != 0:
        raise Stop(f"STOP: {label}: no baseline line")
    base = entries[0]
    if base.get("decision") != "baseline":
        return {"label": label, "baseline_state": None, "steps": [], "stop": base.get("decision"), "entries": entries}
    base_state = _final_run(base).get("code_state_sha256")
    chain: list[str] = []
    current = base_state
    steps, stop = [], None
    for e in entries[1:]:
        if e.get("schema") != LEDGER_SCHEMA:
            raise Stop(f"STOP: {label}: a ledger line is not {LEDGER_SCHEMA}")
        decision = e.get("decision")
        if decision in LEDGER_STOPS:
            stop = decision
            break
        step = {"step": e.get("step"), "decision": decision, "parent_state": current, "chain": list(chain)}
        if decision in RAN:
            run = _final_run(e)
            step["candidate_state"] = run.get("code_state_sha256")
            step["incumbent_seen"] = run.get("incumbent_code_state_sha256")
            step["diff"] = (e.get("proposal") or {}).get("diff")
            if step["incumbent_seen"] != current or not step["candidate_state"] or not isinstance(step["diff"], str):
                raise Stop(f"STOP: {label} step {e.get('step')}: the incumbent hash does not follow the kept chain "
                           f"(re-materialisation integrity)")
            if decision == "kept":
                chain.append(step["diff"])
                current = step["candidate_state"]
        steps.append(step)
    return {"label": label, "baseline_state": base_state, "steps": steps, "stop": stop, "entries": entries}


def audit_plan(spec: dict, node: str, wave: int, ledgers: dict[str, list[str]], *, prior_units: dict | None = None,
               prior_groups: set | None = None, k: int) -> dict:
    """The wave's audit plan: groups (cross-instance duplicates audited once), units (code states to run at the K
    audit seeds) and the members of each group. ``prior_units``: the units of the node's earlier waves (reused under
    ``reuse_parent_runs``; same code state, same seeds)."""
    opt = S.options(spec)["G5-AUDIT"]
    reuse = bool(spec["audit"]["reuse_parent_runs"])
    seeds = S.audit_seeds(spec, k)
    groups: dict[str, dict] = {}
    states: dict[str, list[str]] = {}
    baselines = set()
    for label, lines in sorted(ledgers.items()):
        led = parse_ledger(lines, label)
        if led["baseline_state"] is None:
            continue
        baselines.add(led["baseline_state"])
        states.setdefault(led["baseline_state"], [])
        for st in led["steps"]:
            if st["decision"] not in AUDITED[opt]:
                continue
            key = f"{st['parent_state']}:{st['candidate_state']}"
            states.setdefault(st["parent_state"], st["chain"])
            states.setdefault(st["candidate_state"], st["chain"] + [st["diff"]])
            g = groups.setdefault(key, {"group": hashlib.sha256(key.encode()).hexdigest()[:16],
                                        "parent_state": st["parent_state"], "candidate_state": st["candidate_state"],
                                        "members": []})
            g["members"].append({"ledger": label, "step": st["step"], "decision_class":
                                 "divergent" if st["decision"] == "discarded_divergent" else "ran"})
    if len(baselines) > 1:
        raise Stop(f"STOP: {node}: the instances of the wave disagree on the baseline code state (integrity)")
    prior = dict(prior_units or {})
    carried = [{"group": g["group"], "members": g["members"]} for key, g in sorted(groups.items())
               if key in (prior_groups or set())]          # audited in an earlier wave: members carry that label
    groups = {key: g for key, g in groups.items() if key not in (prior_groups or set())}
    units: dict[str, dict] = {}
    for g in groups.values():
        if reuse:      # a code state runs once per audit seed within the node (its runs serve every role)
            g["candidate_unit"], g["parent_unit"] = g["candidate_state"], g["parent_state"]
        else:          # parents re-run once per distinct parent state, shared by its children (g4_lib.g5_node)
            g["candidate_unit"], g["parent_unit"] = f"candidate:{g['group']}", f"parent:{g['parent_state']}"
        for role in ("candidate", "parent"):
            uid, state = g[f"{role}_unit"], g[f"{role}_state"]
            if uid in prior and (reuse or role == "parent"):
                continue
            units[uid] = {"unit": uid, "state": state, "diffs": states[state]}
    ordered = sorted(groups.values(), key=lambda x: x["group"])
    return {"schema": PLAN_SCHEMA, "label": S.EVIDENCE, "run_id": spec["run_id"], "node": node, "wave": wave,
            "K": k, "seeds": seeds["label"] + seeds["evaluation"], "label_seeds": seeds["label"],
            "audit_option": opt, "reuse_parent_runs": reuse, "groups": ordered, "carried_groups": carried,
            "units": [units[u] for u in sorted(units)], "reused_units": sorted(set(prior) & {
                u for g in ordered for u in ((g["candidate_unit"], g["parent_unit"]) if reuse
                                             else (g["parent_unit"],))}),
            "baseline_state": next(iter(baselines), None)}


def chunk_plan(plan: dict, node: dict) -> list[list[dict]]:
    """Split the plan's runs (unit x seed) into chunks that fit the walltime limit (runs x run time x 1.5)."""
    per_run = float(node["run_seconds"]) * 1.25 * 1.5
    cap = max(1, int(CHUNK_LIMIT_S // per_run))
    runs = [{"unit": u["unit"], "seed": s, "train_seed": s, "split_seed": s} for u in plan["units"]
            for s in plan["seeds"]]
    return [runs[i:i + cap] for i in range(0, len(runs), cap)] or [[]]


def audit_chunk_file(spec: dict, node: dict, plan: dict, index: int, runs: list[dict], *, interpreter: str,
                     cgroup_parent: str, deadline_epoch: float) -> dict:
    used = {r["unit"] for r in runs}
    allowed = set(plan["seeds"])
    for r in runs:
        if r["seed"] not in allowed:
            raise Stop(f"STOP 10: seed {r['seed']} is not an audit seed of K = {plan['K']}")
    return {"schema": CHUNK_SCHEMA, "label": S.EVIDENCE, "run_id": spec["run_id"], "node": node["node"],
            "family": node["family"], "wave": plan["wave"], "chunk": index, "K": plan["K"],
            "spec_path": node["spec_path"], "node_dir": node["node_dir"], "node_spec_sha256": node["node_spec_sha256"],
            "committed_pin_sha256": node["committed_pin_sha256"], "data_manifest_sha256": node["data_manifest_sha256"],
            "measured_run_seconds": node_timeout_basis(node), "timeout_factor": TIMEOUT_FACTOR, "split_policy": "vary",
            "units": [{"unit": u["unit"], "code_state_sha256": u["state"], "diffs": u["diffs"]}
                      for u in plan["units"] if u["unit"] in used],
            "runs": runs, "interpreter": interpreter, "cgroup_parent": cgroup_parent, "isolation_waivers": {},
            "record_gate": "noise_floor.check_effective", "deadline_epoch": deadline_epoch,
            "memory_limit": f"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 "
                            f"(delegated scope {cgroup_parent})"}


# =============================================================================================== rows, E5
def read_rows(lines: list[str], chunk: dict) -> list[dict]:
    """The audit rows of one chunk, reduced to unit, seed, outcome kind and reason; the value is never returned.
    The kind is checked first: an ``infrastructure_failure`` row (after the engine's 2 reruns) skips the isolation and
    execution checks and leads to STOP 7 (a new attempt). Every ``ok`` or ``divergent`` row is an executed run at its
    planned code state and effectively isolated (STOP 2); a row outside the plan is STOP 10; every planned run has
    exactly one row."""
    planned = {(r["unit"], r["seed"]) for r in chunk["runs"]}
    states = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}
    seen, out = set(), []
    for line in lines:
        if not line.strip():
            continue
        r = json.loads(line)
        key = (r.get("unit"), r.get("seed"))
        if r.get("schema") != ROW_SCHEMA:
            raise Stop("STOP: an audit row is not trackg_g5_audit_row/v1")
        if key not in planned:
            raise Stop(f"STOP 10: an audit row {key} is not a planned run (seed or unit outside the plan)")
        if key in seen:
            raise Stop(f"STOP: audit row {key} appears twice")
        seen.add(key)
        kind = (r.get("outcome") or {}).get("kind")
        if kind not in ("ok", "divergent", "infrastructure_failure"):
            raise Stop(f"STOP: audit run {key} has outcome kind {kind!r}")
        if kind != "infrastructure_failure":
            iso = r.get("isolation") or {}
            if iso.get("effective") is not True or iso.get("waivers") != {} or iso.get("exceptions") != []:
                raise Stop(f"STOP 2: audit run {key} is not effectively isolated (stop_unisolated)")
            if r.get("executed") is not True or r.get("code_state_sha256") != states[r["unit"]]:
                raise Stop(f"STOP: audit run {key} did not run the planned code state (integrity)")
        out.append({"unit": r["unit"], "seed": r["seed"], "kind": kind,
                    "reason": (r.get("outcome") or {}).get("reason")})
    missing = sorted(planned - seen)
    if missing:
        raise Stop(f"STOP: {len(missing)} planned audit runs have no row: {missing[:3]}")
    return out


def e5(plan: dict, rows: list[dict]) -> dict:
    """E5 per audited group on the label seeds only (§2.4): the proposal is divergent when more than half of its label
    seeds diverge; partial when some label seed diverged on the proposal or its parent; else complete. Evaluation
    seeds never enter. An infrastructure row is not an E5 outcome (the chunk STOPped before this)."""
    label = set(plan["label_seeds"])
    by, reasons = {}, {}
    for r in rows:
        if r["seed"] in label:
            by[(r["unit"], r["seed"])] = r["kind"]
            reasons[(r["unit"], r["seed"])] = r.get("reason")
    out = {"audited": 0, "members": 0, "divergent_label": 0, "partial_label": 0, "complete_label": 0,
           "parent_divergent_seeds": 0, "baseline_label_timeouts": 0, "baseline_label_divergent_other": 0}
    baseline_units = set()
    for g in plan["groups"]:
        kinds_c = [by.get((g["candidate_unit"], s)) for s in label]
        kinds_p = [by.get((g["parent_unit"], s)) for s in label]
        if None in kinds_c or None in kinds_p:
            raise Stop(f"STOP: group {g['group']} lacks label-seed rows (E5 needs every label seed)")
        d, p = kinds_c.count("divergent"), kinds_p.count("divergent")
        out["audited"] += 1
        out["members"] += len(g["members"])
        out["parent_divergent_seeds"] += p
        if g["parent_state"] == plan.get("baseline_state") and g["parent_unit"] not in baseline_units:
            baseline_units.add(g["parent_unit"])                   # STOP 8 (timeout) or a node STOP (other)
            for s in label:
                if by.get((g["parent_unit"], s)) == "divergent":
                    timeout = str(reasons.get((g["parent_unit"], s)) or "").startswith("timeout")
                    out["baseline_label_timeouts" if timeout else "baseline_label_divergent_other"] += 1
        if d > len(label) / 2:
            out["divergent_label"] += 1
        elif d or p:
            out["partial_label"] += 1
        else:
            out["complete_label"] += 1
    return out


# =============================================================================================== diagnostics
def _q(values: list[float], q: float):
    if not values:
        return None
    values = sorted(values)
    return values[min(len(values) - 1, int(round(q * (len(values) - 1))))]


COUNT_KEYS = ("manager_calls", "proposals", "invalid", "truncated", "truncated_not_invalid", "refused", "inert",
              "duplicate", "ran", "divergent_in_campaign", "timed_out", "kept", "infrastructure_final",
              "prompt_overflow")
SHARE_KEYS = ("invalid_of_calls", "ran_of_valid", "infrastructure_final_of_proposals",
              "single_seed_divergent_of_proposals")


def campaign_counts(ledgers: dict[str, list[str]], *, max_tokens: int, ctx: int,
                    timeout_basis: float | None = None) -> dict:
    """Counts and shares from the wave's ledgers (no metric value): the STOP 3, 4, 6, 7, 8 inputs, and G.4's two
    carried STOPs as states only (§4 preamble): the median executed run time above the timeout basis (the 4090 timing
    STOP; the median itself is not written), and manager requests without ``cache_prompt: false``."""
    d = {k: 0 for k in COUNT_KEYS}
    stops = {k: 0 for k in LEDGER_STOPS + ("baseline_timeout",)}
    prompts, completions, keyed, run_secs = [], [], {}, []
    no_cache_false = 0
    for label, lines in ledgers.items():
        for x in lines:
            if not x.strip():
                continue
            e = json.loads(x)
            dec = e.get("decision")
            if dec in LEDGER_STOPS:
                stops[dec] += 1
                if dec == "baseline_failed" and ((e.get("final_outcome") or {}).get("reason") or "").startswith(
                        "timeout"):
                    stops["baseline_timeout"] += 1
                continue
            if e.get("step", 0) < 1:
                continue
            d["proposals"] += 1
            call = e.get("manager_call") or {}
            if call:
                d["manager_calls"] += 1
            usage = call.get("usage") or {}
            if call and (call.get("request") or {}).get("cache_prompt") is not False:
                no_cache_false += 1
            run_secs += [float(r["elapsed_seconds_info_only"]) for r in e.get("runs") or []
                         if r.get("executed") and isinstance(r.get("elapsed_seconds_info_only"), (int, float))]
            if usage.get("prompt_tokens"):
                prompts.append(float(usage["prompt_tokens"]))
                if float(usage["prompt_tokens"]) + max_tokens > ctx:
                    d["prompt_overflow"] += 1
            if usage.get("completion_tokens"):
                completions.append(float(usage["completion_tokens"]))
            truncated = float(usage.get("completion_tokens") or 0) >= max_tokens
            d["truncated"] += truncated
            d["invalid"] += dec == "invalid_proposal"
            d["truncated_not_invalid"] += truncated and dec != "invalid_proposal"
            d["refused"] += dec == "not_run_refused"
            d["inert"] += dec == "not_run_inert"
            d["duplicate"] += dec == "not_run_duplicate"
            d["infrastructure_final"] += dec == "infrastructure_failure_final"
            if dec in RAN:
                d["ran"] += 1
                d["kept"] += dec == "kept"
                d["divergent_in_campaign"] += dec == "discarded_divergent"
                d["timed_out"] += ((e.get("final_outcome") or {}).get("reason") or "") in ("timeout", "timeout_repeated")
                run = _final_run(e)
                key = (run.get("incumbent_code_state_sha256"), run.get("code_state_sha256"))
                keyed.setdefault(key, set()).add(label.split("_")[1] if "_" in label else label)
    valid = d["proposals"] - d["invalid"]
    rate = (lambda a, b: round(a / b, 6) if b else None)
    groups = [k for k, v in keyed.items() if len(v) > 1]
    return {"counts": d, "ledger_stops": stops,
            "shares": {"invalid_of_calls": rate(d["invalid"] + d["truncated_not_invalid"], d["manager_calls"]),
                       "ran_of_valid": rate(d["ran"], valid),
                       "infrastructure_final_of_proposals": rate(d["infrastructure_final"], d["proposals"]),
                       "single_seed_divergent_of_proposals": rate(d["divergent_in_campaign"], d["proposals"])},
            "prompt_tokens": {"p50": _q(prompts, 0.5), "p95": _q(prompts, 0.95), "max": max(prompts, default=None)},
            "completion_tokens": {"p50": _q(completions, 0.5), "p95": _q(completions, 0.95),
                                  "max": max(completions, default=None)},
            "checks": {"run_median_over_basis": int(bool(run_secs) and timeout_basis is not None
                                                    and _median(run_secs) > timeout_basis),
                       "requests_without_cache_prompt_false": no_cache_false},
            "cross_instance_duplicate_groups": len(groups),
            "ledgers": len(ledgers)}


def _median(values: list[float]) -> float:
    v = sorted(values)
    mid = len(v) // 2
    return v[mid] if len(v) % 2 else (v[mid - 1] + v[mid]) / 2


INT, NUM, STR = "int", "num", "str"


def OPT(t):            # noqa: N802 - a schema constructor
    return ("opt", t)


SEEDS = ("seeds", 7001, 7010)
_E5 = {k: INT for k in ("audited", "members", "divergent_label", "partial_label", "complete_label",
                        "parent_divergent_seeds", "baseline_label_timeouts", "baseline_label_divergent_other")}
_COMMON = {"schema": STR, "label": STR, "run_id": STR, "node": STR, "job": STR, "wave": INT, "attempt": OPT(INT),
           "spec_sha256": STR, "gpu_seconds": OPT(NUM), "stop": OPT(STR), "stop_class": OPT(STR)}
DIAG_SCHEMAS = {
    DIAG_CAMPAIGN: {**_COMMON, "counts": {k: INT for k in COUNT_KEYS},
                    "ledger_stops": {k: INT for k in LEDGER_STOPS + ("baseline_timeout",)},
                    "shares": {k: OPT(NUM) for k in SHARE_KEYS},
                    "prompt_tokens": {k: OPT(NUM) for k in ("p50", "p95", "max")},
                    "completion_tokens": {k: OPT(NUM) for k in ("p50", "p95", "max")},
                    "checks": {"run_median_over_basis": INT, "requests_without_cache_prompt_false": INT},
                    "cross_instance_duplicate_groups": INT, "ledgers": INT},
    # evaluation seeds: planned run counts only, never an outcome count (§6, R1-B2-DECOUPLE, PRE-DIV A)
    DIAG_AUDIT: {**_COMMON, "chunk": OPT(INT), "chunks": OPT(INT), "K": OPT(INT), "plan_sha256": OPT(STR),
                 "runs_planned_label": INT, "runs_planned_evaluation": INT,
                 "label_seed_runs": {"ok": INT, "divergent": INT, "infrastructure": INT},
                 "seeds_planned": SEEDS, "wave_e5": OPT(_E5)},
}


def _check(obj, schema, path: str) -> None:
    if isinstance(schema, tuple) and schema[0] == "opt":
        if obj is None:
            return
        schema = schema[1]
    if isinstance(schema, dict):
        if not isinstance(obj, dict) or set(obj) != set(schema):
            raise Stop(f"STOP: diagnostics {path or 'top level'} keys differ from the fixed schema: "
                       f"{sorted(set(obj) ^ set(schema)) if isinstance(obj, dict) else type(obj).__name__}")
        for k, sub in schema.items():
            _check(obj[k], sub, f"{path}{k}.")
        return
    if isinstance(schema, tuple) and schema[0] == "seeds":
        if not isinstance(obj, list) or any(type(v) is not int or not schema[1] <= v <= schema[2] for v in obj):
            raise Stop(f"STOP: diagnostics {path} must be a list of audit seeds")
        return
    ok = {INT: type(obj) is int, NUM: type(obj) in (int, float), STR: isinstance(obj, str)}[schema]
    if not ok:
        raise Stop(f"STOP: diagnostics leaf {path} must be {schema}, not {type(obj).__name__}")


def check_diagnostics(d: dict) -> dict:
    """The full nested schema of each diagnostics kind (§6): exactly the declared keys at every level, typed leaves;
    counts and shares only, no metric value, delta, label or keep outcome, and no evaluation-seed outcome count."""
    schema = DIAG_SCHEMAS.get(d.get("schema"))
    if schema is None:
        raise Stop(f"STOP: unknown diagnostics schema {d.get('schema')!r}")
    _check(d, schema, "")
    return d


# =============================================================================================== STOP counters
def evaluate_stops(spec: dict, diags: list[dict], *, wave: int, gpu_hours_consumed: float) -> dict:
    """The STOPs evaluated on diagnostics only (§4; no label is read): after each wave's audits, from that wave's
    and earlier waves' diagnostics of the node. Returns {"stops": [...], "warnings": [...]} with each STOP's number and
    class (node: the author decides; infrastructure: a new attempt after diagnosis; timing)."""
    kv = spec["key_values"]
    stops, warnings = [], []
    camp = [d for d in diags if d["schema"] == DIAG_CAMPAIGN and d["wave"] <= wave]
    aud = [d for d in diags if d["schema"] == DIAG_AUDIT and d["wave"] <= wave]
    this_c = [d for d in camp if d["wave"] == wave]
    for d in this_c:
        c, sh, ls = d["counts"], d["shares"], d["ledger_stops"]
        if ls["stop_unisolated"]:
            stops.append({"stop": 2, "class": "node", "why": "a campaign run failed the isolation gate"})
        if ls["stop_integrity"] or ls["stop_transport"]:
            stops.append({"stop": 6, "class": "infrastructure", "why": "stop_integrity or stop_transport ledger line"})
        if ls["baseline_timeout"]:
            stops.append({"stop": 8, "class": "timing", "why": "a baseline timeout STOPs the campaign"})
        elif ls["baseline_failed"]:
            stops.append({"stop": 6, "class": "node", "why": "baseline_failed"})
        if c["prompt_overflow"]:
            stops.append({"stop": 4, "class": "node", "why": "a prompt longer than 32,768 - 4,096 tokens"})
        if d["checks"]["run_median_over_basis"]:
            stops.append({"stop": "timing", "class": "timing", "why": "the median run time on the 4090 is above the "
                                                                      "timeout basis (G.4's timing STOP)"})
        if d["checks"]["requests_without_cache_prompt_false"]:
            stops.append({"stop": "cache_prompt", "class": "infrastructure",
                          "why": "a manager request lacked cache_prompt: false (G.4's STOP)"})
        if c["truncated_not_invalid"]:
            stops.append({"stop": 4, "class": "infrastructure",
                          "why": "a reply at the completion cap was not an invalid proposal (engine contract)"})
        if sh["invalid_of_calls"] is not None and sh["invalid_of_calls"] > kv["invalid_share_stop"]:
            stops.append({"stop": 4, "class": "node", "why": f"invalid share {sh['invalid_of_calls']} > "
                                                            f"{kv['invalid_share_stop']} of the wave's manager calls"})
        if (sh["single_seed_divergent_of_proposals"] or 0) > 0.2:
            warnings.append(f"wave {wave}: in-campaign single-seed divergent share "
                            f"{sh['single_seed_divergent_of_proposals']} > 0.2 (early warning)")
    if wave == 1 and this_c:
        ran = sum(d["counts"]["ran"] for d in this_c)
        valid = sum(d["counts"]["proposals"] - d["counts"]["invalid"] for d in this_c)
        if valid == 0 or ran / valid < kv["liveness_floor"]:
            stops.append({"stop": 3, "class": "node", "why": f"ran-of-valid {ran}/{valid} below the liveness floor "
                                                            f"{kv['liveness_floor']} after wave 1 (D4)"})
    proposals = sum(d["counts"]["proposals"] for d in camp)
    infra = sum(d["counts"]["infrastructure_final"] for d in camp)
    if proposals and infra / proposals > kv["infrastructure_stop_share"]:
        stops.append({"stop": 7, "class": "node", "why": f"final infrastructure failures {infra}/{proposals} above "
                                                        f"{kv['infrastructure_stop_share']}"})
    finals = [d["wave_e5"] for d in aud if d.get("wave_e5")]
    if finals:
        audited = sum(f["audited"] for f in finals)
        divergent = sum(f["divergent_label"] for f in finals)
        if any(f["baseline_label_timeouts"] for f in finals):
            stops.append({"stop": 8, "class": "timing", "why": "the baseline code state timed out at an audit label "
                                                              "seed"})
        if any(f["baseline_label_divergent_other"] for f in finals):
            stops.append({"stop": 6, "class": "node", "why": "the baseline code state diverged (not a timeout) at an "
                                                            "audit label seed"})
        th = S.divergence_threshold(spec, aud[0]["node"])
        if audited >= th["min_audited"]:
            if divergent / audited > th["threshold"]:
                stops.append({"stop": 1, "class": "node", "why": f"E5 divergence {divergent}/{audited} on the label "
                                                                f"seeds above {th['threshold']} ({th['rule']})"})
        else:
            warnings.append(f"wave {wave}: {audited} audited (< {th['min_audited']}); divergence "
                            f"{divergent}/{audited} is an early warning only")
        if wave == 1:
            band = kv["audited_band"]
            per_mode_wave1 = len(WAVE_INSTANCES[1])
            projected = audited * 12 / per_mode_wave1
            if not band[0] <= projected <= band[1]:
                stops.append({"stop": 9, "class": "node", "why": f"audited {audited} after wave 1 extrapolates to "
                                                                f"{projected:g} per node, outside the band {band}"})
    if gpu_hours_consumed > kv["cap_gpu_hours"]:
        stops.append({"stop": 9, "class": "node", "why": f"consumed worker GPU-hours {gpu_hours_consumed:.1f} above "
                                                        f"the cap {kv['cap_gpu_hours']}"})
    return {"wave": wave, "stops": stops, "warnings": warnings}


# =============================================================================================== state on disk
def run_root(spec: dict) -> Path:
    return Path(spec["worker"]["runs_root"]) / spec["run_id"]


def job_dir(spec: dict, node: str, job: str, chunk: int | None = None) -> Path:
    d = run_root(spec) / node / job
    return d / f"chunk-{chunk}" if chunk is not None else d


def complete_attempt(d: Path) -> tuple[dict, dict] | None:
    """The completed attempt of a job directory (stop None), with its record and diagnostics; None if none."""
    for _, p in G.attempts(d):
        rec_path, diag_path = p / "job_record.json", p / "diagnostics.json"
        if rec_path.is_file() and diag_path.is_file():
            rec = json.loads(rec_path.read_text())
            if rec.get("stop") is None:
                return rec, json.loads(diag_path.read_text())
    return None


def node_stopped(d: Path) -> str | None:
    """A node, timing or job STOP recorded in any attempt of the node (a STOPped node is not run further)."""
    for rec in sorted(Path(d).rglob("job_record.json")):
        r = json.loads(rec.read_text())
        if r.get("stop_class") in ("node", "timing"):
            return f"{rec.parent}: {r.get('stop')}"
    for wc in sorted(Path(d).glob("wave_checks_wave*.json")):
        w = json.loads(wc.read_text())
        if any(s["class"] in ("node", "timing") for s in w["stops"]):
            return f"{wc.name}: {w['stops']}"
    return None


def gpu_hours_consumed(spec: dict) -> float:
    """The running meter of STOP 9, per G5-TASL-GPUH: the worker card's time (every G.5 job record's wall seconds,
    closed attempts included); under B also the proposer card held over each campaign wave (the campaign jobs' wall
    seconds, a lower bound of the server's held span until 3b-2 adds TASL-7's server_end.json spans)."""
    total = 0.0
    both = S.options(spec)["G5-TASL-GPUH"] == "B"
    root = run_root(spec)
    if root.is_dir():
        for rec in root.rglob("job_record.json"):
            r = json.loads(rec.read_text())
            if r.get("schema") != RECORD_SCHEMA:
                continue
            secs = float(r.get("gpu_seconds") or 0)
            total += secs * (2 if both and str(r.get("job", "")).startswith("campaigns") else 1)
    return round(total / 3600.0, 3)


def node_diagnostics(spec: dict, node: str) -> list[dict]:
    out = []
    for job in S.JOBS:
        kind, _ = job_parts(job)
        if kind == "campaigns":
            got = complete_attempt(job_dir(spec, node, job))
            if got:
                out.append(got[1])
        else:
            base = job_dir(spec, node, job)
            if base.is_dir():
                for c in sorted(base.glob("chunk-*")):
                    got = complete_attempt(c)
                    if got:
                        out.append(got[1])
    return out


def audits_done(spec: dict, node: str, wave: int) -> bool:
    index = plan_path(spec, node, wave)
    if not index.is_file():
        return False
    n = json.loads(index.read_text())["chunks"]
    return all(complete_attempt(job_dir(spec, node, f"audits-wave{wave}", c)) for c in range(n))


def wave_checks_path(spec: dict, node: str, wave: int) -> Path:
    return run_root(spec) / node / f"wave_checks_wave{wave}.json"


def wave_checks(spec: dict, node: str, wave: int) -> dict:
    """The checks after a wave's audits (§3 steps 3 and 6), from the diagnostics only. Written once per wave
    (append-only: an existing record is returned as it is, never recomputed)."""
    path = wave_checks_path(spec, node, wave)
    if path.is_file():
        return json.loads(path.read_text())
    if not audits_done(spec, node, wave):
        raise Stop(f"STOP: {node} wave {wave}: the audits are not complete")
    res = evaluate_stops(spec, node_diagnostics(spec, node), wave=wave, gpu_hours_consumed=gpu_hours_consumed(spec))
    res["utc"] = utc()
    _write_json(path, res)
    return res


def check_order(spec: dict, node: str, job: str) -> None:
    kind, wave = job_parts(job)
    check_access_log(spec)                                       # STOP 11
    stopped = node_stopped(run_root(spec) / node)
    if stopped:
        raise Stop(f"STOP: {node} has a STOP on record ({stopped}); the author decides before anything else runs")
    consumed = gpu_hours_consumed(spec)
    if consumed > spec["key_values"]["cap_gpu_hours"]:
        raise Stop(f"STOP 9: consumed GPU-hours {consumed} above the cap {spec['key_values']['cap_gpu_hours']} "
                   f"(counted per G5-TASL-GPUH)")
    if kind == "campaigns":
        if complete_attempt(job_dir(spec, node, job)):
            raise Stop(f"STOP: {node} {job} is complete")
        if wave == 2:
            if not audits_done(spec, node, 1):
                raise Stop(f"STOP: {node} campaigns-wave2 needs the wave-1 audits complete (§3)")
            checks = wave_checks(spec, node, 1)
            if checks["stops"]:
                raise Stop(f"STOP: {node} wave-1 checks STOPped the node before wave 2: {checks['stops']}")
    else:
        if not complete_attempt(job_dir(spec, node, f"campaigns-wave{wave}")):
            raise Stop(f"STOP: {node} {job} needs campaigns-wave{wave} complete (§3)")


# =============================================================================================== K, access log
def k_check(spec: dict, k: int) -> dict | None:
    """K uniformity within the table (P4): a K other than the one fixed at the table's first audit chunk STOPs."""
    path = run_root(spec) / "_k_lock.json"
    if path.is_file():
        lock = json.loads(path.read_text())
        if lock["K"] != k:
            raise Stop(f"STOP: K = {k} differs from the table's K = {lock['K']} fixed at its first audit chunk "
                       f"({lock['utc']}); K is uniform within the table (P4)")
        return lock
    return None


def k_lock(spec: dict, k: int, row: str | None) -> dict:
    """Fix K at the table's first audit chunk (called after that chunk's attempt directory exists)."""
    lock = k_check(spec, k)
    if lock is not None:
        return lock
    lock = {"K": k, "K_row": row, "utc": utc()}
    path = run_root(spec) / "_k_lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as fh:
        fh.write(json.dumps(lock) + "\n")
    return lock


def access(spec: dict, path: Path, purpose: str, *, who: str = "g5_job") -> dict:
    """One line in ``<run_id>/_access_log.jsonl`` for each opening of an ``out.tar`` by job code (§6)."""
    if not any(purpose.startswith(p) for p in ACCESS_PURPOSES):
        raise Stop(f"STOP 11: an out.tar opening for {purpose!r} is not a declared job purpose")
    entry = {"utc": utc(), "who": who, "pid": os.getpid(), "path": str(path), "sha256": L._sha_file(path),
             "purpose": purpose}
    log = run_root(spec) / "_access_log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def check_access_log(spec: dict) -> list[dict]:
    """STOP 11 on the access log: every opening must be by job code for a declared purpose."""
    log = run_root(spec) / "_access_log.jsonl"
    out = [json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.is_file() else []
    bad = [e for e in out if e.get("who") != "g5_job" or not any(str(e.get("purpose", "")).startswith(p)
                                                                 for p in ACCESS_PURPOSES)]
    if bad:
        raise Stop(f"STOP 11: out.tar opened outside the job's declared purposes: {bad[:3]}")
    return out


LEDGER_MEMBER = re.compile(r"^out/campaign/(instance_\d+_(?:history|none))/campaign_ledger\.jsonl$")
CHUNK_MEMBERS = ("out/chunk.json", "out/audit/rows.jsonl")


def tar_members(spec: dict, tar_path: Path, wanted, purpose: str) -> dict[str, list[str]]:
    """Read only the named text members of a verified ``out.tar`` (logged), streamed with ``extractfile``.
    ``wanted``: a compiled pattern (its first group names the member) or a tuple of exact member names. Everything
    else in the tar (working copies, logs, binaries) is not opened."""
    attempt = Path(tar_path).parent
    if subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"], cwd=attempt, capture_output=True).returncode:
        raise Stop(f"STOP: {attempt} does not verify against its SHA256SUMS")
    access(spec, Path(tar_path), purpose)
    out = {}
    with tarfile.open(tar_path) as tar:
        for m in tar:
            if not m.isfile():
                continue
            if isinstance(wanted, tuple):
                key = m.name if m.name in wanted else None
            else:
                hit = wanted.fullmatch(m.name)
                key = hit.group(1) if hit else None
            if key is None:
                continue
            fh = tar.extractfile(m)
            out[key] = io.TextIOWrapper(fh, encoding="utf-8").read().splitlines()
    if isinstance(wanted, tuple) and sorted(out) != sorted(wanted):
        raise Stop(f"STOP: {tar_path} lacks {sorted(set(wanted) - set(out))}")
    return out


# =============================================================================================== the job
RECORD_KEYS = {"schema", "label", "run_id", "node", "family", "job", "wave", "chunk", "attempt", "spec_sha256",
               "harness_commit", "K", "K_row", "options", "lease", "host", "affinity", "gpu", "foreign_checks",
               "ptrace_scope", "cgroup", "harness", "environment", "data", "server_record", "server_props_before",
               "server_props_after", "server_stopped", "latency_probe_before", "latency_probe_after", "deadline_epoch",
               "started_utc", "finished_utc", "gpu_seconds", "engine", "engine_rc", "out_tar_sha256", "plan_sha256",
               "stop", "stop_class", "node_log", "output_use", "owner"}


def worker_shim(spec: dict, node: dict, context: dict) -> tuple[dict, dict]:
    """The worker and node in the shapes ``g1b_tasl``'s host checks read; autoresearch's environment comes from the
    completion record under G5-ARPEND A (context ``ar_environment``)."""
    fam = spec["harness_families"][node["family"]]
    w = dict(spec["worker"], harness_dir=fam["harness_dir"])
    envs = dict(spec["envs"])
    node = dict(node)
    env = context.get("ar_environment") if node["node"] == S.AR else None
    if env:
        if not env["freeze"].startswith("sweep2/g1b/"):
            raise Stop("STOP: autoresearch's freeze must be under sweep2/g1b/")
        envs[env["name"]] = {"freeze": env["freeze"][len("sweep2/g1b/"):], "sha256": env["sha256"],
                             "python": env["python"]}
        w["env_python"] = dict(w["env_python"], **{env["name"]: env["interpreter"]})
        node["env"] = env["name"]
    if node["env"] not in envs or node["env"] not in w["env_python"]:
        raise Stop(f"STOP: {node['node']}'s environment {node['env']!r} is not resolved")
    shim = {"hosts": {S.WORKER_HOST: w}, "harness": {"commit": fam["g5_commit"]}, "envs": envs}
    node["host"] = S.WORKER_HOST
    return shim, node


def _write_json(path: Path, obj: dict) -> None:
    with Path(path).open("x") as fh:
        fh.write(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


def run_job(spec_path: Path, node_name: str, job: str, context: dict, *, smi=G._sh, engine=subprocess.run,
            setup=L.run_setup, get=T4._get, git=G._sh, server_record: Path | None = None,
            node_log: str | None = None, clock=time.time) -> dict:
    """The switch's runner (part 3b-1): one campaign wave, or one audit chunk, of one node on TASL-2."""
    spec_path = Path(spec_path)
    spec = S.load_spec(spec_path)
    node = S.node_entry(spec, node_name)
    kind, wave = job_parts(job)
    server_record = server_record or context.get("server_record")
    try:                         # refusals before the lease are recorded too (m7)
        check_order(spec, node_name, job)
        if kind == "campaigns" and not server_record:
            raise Stop("STOP: a campaign job needs the proposer's server_record.json (copied from TASL-7)")
        shim, wnode = worker_shim(spec, node, context)
    except Stop as exc:
        G.write_refusal(run_root(spec), node_name, str(exc), {"job": job, "node": node_name})
        raise
    fam = spec["harness_families"][node["family"]]
    started = clock()
    record: dict = {"schema": RECORD_SCHEMA, "label": S.EVIDENCE, "run_id": spec["run_id"], "node": node_name,
                    "family": node["family"], "job": job, "wave": wave, "chunk": None,
                    "spec_sha256": L._sha_file(spec_path), "harness_commit": fam["g5_commit"], "K": context.get("K"),
                    "K_row": context.get("K_row"), "options": S.options(spec), "stop": None, "stop_class": None,
                    "foreign_checks": [], "started_utc": utc(started),
                    "node_log": node_log or os.environ.get("G5_TASL_NODE_LOG"),
                    "output_use": "EVIDENCE G.5 label runs; sealed; readers open only receipted release partitions"}
    gpu = None if node["device"] == "cpu" else spec["worker"]["gpu_uuid"]
    lease_cm = G.gpu_lease(spec["worker"]["lease"])
    base = run_root(spec)
    try:
        record["lease"] = lease_cm.__enter__()
    except Exception as exc:  # noqa: BLE001
        G.write_refusal(base, node_name, f"STOP: {exc}", record)
        raise Stop(str(exc)) from exc
    try:
        try:
            record["engine"] = check_engines(Path(fam["harness_dir"]), fam["g5_commit"], git)
            record["host"] = G.host_identity(shim, S.WORKER_HOST)
            record["affinity"] = G.check_affinity(shim, wnode)
            record["gpu"] = G.gpu_check(shim, S.WORKER_HOST, smi) if gpu else {"device": "cpu"}
            record["foreign_checks"].append(G.check_no_foreign(gpu, "before the job", smi))
            record["ptrace_scope"] = G.ptrace_scope()
            record["cgroup"] = G.scope_cgroup()
            record["harness"] = G.harness_checkout(shim, S.WORKER_HOST, git)
            record["environment"] = G.environment(shim, S.WORKER_HOST, wnode)
            if kind == "campaigns":
                raw = Path(server_record).read_bytes()
                record["server_record"] = T4.check_server_record(spec, raw, record["spec_sha256"])
                record["server_props_before"] = T4.server_identity(spec, get)
                record["latency_probe_before"] = T4.latency_probe(spec, get=get)
            elif spec["proposer"]["server_stopped_during_audits"]:          # G5-TASL-GPUH B
                record["server_stopped"] = server_down(spec, get)
            if kind == "audits":
                k_check(spec, context["K"])
                plan, chunk_index, runs = next_chunk(spec, node, wave, context["K"])
                record["chunk"], record["plan_sha256"] = chunk_index, plan["sha256"]
                jdir = job_dir(spec, node_name, job, chunk_index)
            else:
                jdir = job_dir(spec, node_name, job)
            record["attempt"], attempt_dir = G.next_attempt(jdir)
            if kind == "audits":
                k_lock(spec, context["K"], context.get("K_row"))          # fixed once the first chunk exists (m2)
        except Stop as exc:
            G.write_refusal(base, node_name, str(exc), record)
            raise
        except Exception as exc:  # noqa: BLE001
            message = f"STOP: unexpected {type(exc).__name__} before the run: {exc}"
            G.write_refusal(base, node_name, message, record)
            raise Stop(message) from exc
        out = attempt_dir / "out"
        out.mkdir()
        if kind == "campaigns":
            (out / "server_record.json").write_bytes(raw)          # sealed with the wave
        diag: dict = {}
        try:
            harness = Path(fam["harness_dir"])
            python = shim["hosts"][S.WORKER_HOST]["env_python"][wnode["env"]]
            os.environ["PATH"] = f"{Path(python).parent}:{os.environ.get('PATH', '')}"     # as G.1b and G.4 (M2)
            for key, value in (spec["worker"].get("extra_env") or {}).items():
                os.environ[key] = value
            record["data"] = setup(harness, wnode, Path(spec["worker"]["base"]), out)
            if kind == "campaigns":
                deadline = started + campaign_deadline_s(spec, node, wave)
                infile = campaign_file(spec, node, wave, interpreter=python,
                                       cgroup_parent=record["cgroup"]["cgroup_parent"], deadline_epoch=deadline)
                (out / "campaign.json").write_text(json.dumps(infile, indent=1) + "\n")
                mod, cmd, _ = ENGINES["campaign"]
                argv = [python, "-m", mod, cmd, "--campaign", str(out / "campaign.json")]
                eng_out = out / "campaign"
            else:
                deadline = started + STARTUP_RESERVE_S + int(math.ceil(len(runs) * float(node["run_seconds"]) * 1.5
                                                                      * 1.25))
                infile = audit_chunk_file(spec, node, plan, chunk_index, runs, interpreter=python,
                                          cgroup_parent=record["cgroup"]["cgroup_parent"], deadline_epoch=deadline)
                (out / "chunk.json").write_text(json.dumps(infile, indent=1) + "\n")
                mod, cmd, _ = ENGINES["audit"]
                argv = [python, "-m", mod, cmd, "--chunk", str(out / "chunk.json")]
                eng_out = out / "audit"
            record["deadline_epoch"] = deadline
            argv += ["--harness-root", str(harness), "--out", str(eng_out)] + (["--gpu-uuid", gpu] if gpu else [])
            record["foreign_checks"].append(G.check_no_foreign(gpu, "before the engine", smi))
            remaining = int(deadline - clock())
            if remaining < 60:          # STOP 9 past the deadline: node class, the author decides (m5)
                raise NodeStop("STOP 9: the job deadline was reached before the engine started")
            env = dict(os.environ, PYTHONPATH=str(harness / "src"), PYTHONDONTWRITEBYTECODE="1",
                       AR_TRACKG_DATA_ROOT=record["data"]["data_root"], CUDA_VISIBLE_DEVICES="")
            for name in ("NVIDIA_VISIBLE_DEVICES", "_CONDOR_AssignedGPUs"):
                env.pop(name, None)
            try:
                res = engine(argv, cwd=harness, env=env, capture_output=True, text=True, timeout=remaining)
            except subprocess.TimeoutExpired as exc:
                (out / "engine.log").write_text(f"{L._text(exc.stdout)}\n--- stderr ---\n{L._text(exc.stderr)}")
                raise NodeStop("STOP 9: the engine reached the job deadline; partial outputs kept") from None
            (out / "engine.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
            record["engine_rc"] = res.returncode
            record["foreign_checks"].append(G.check_no_foreign(gpu, "after the engine", smi))
            if kind == "campaigns":
                try:
                    record["server_props_after"] = T4.server_identity(spec, get)
                except Stop as exc:
                    raise Stop(f"STOP 12: after the wave: {exc} (re-run as a new attempt)") from None
                if record["server_props_after"] != record["server_props_before"]:
                    raise Stop("STOP 12: the proposer /props changed during the wave (re-run as a new attempt)")
                record["latency_probe_after"] = T4.latency_probe(spec, get=get)
                diag = campaign_diagnostics(spec, node, wave, record, eng_out)
            else:
                diag = audit_diagnostics(spec, node, wave, record, plan, chunk_index, infile, eng_out)
            if res.returncode != 0 and not diag.get("stop"):
                raise Stop(f"STOP: the engine exited {res.returncode}")
            if diag.get("stop"):
                record["stop"], record["stop_class"] = diag["stop"], diag["stop_class"]
        except NodeStop as exc:
            record["stop"], record["stop_class"] = str(exc), "node"
        except TimingStop as exc:
            record["stop"], record["stop_class"] = str(exc), "timing"
        except Stop as exc:
            record["stop"], record["stop_class"] = str(exc), "infrastructure"
        except Exception as exc:  # noqa: BLE001
            record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
        if make_tar(attempt_dir):
            record["out_tar_sha256"] = L._sha_file(attempt_dir / "out.tar")
            shutil.rmtree(out)                       # §6: in clear only out.tar, the records and the sums
        else:                                        # out/ stays; 3b-2's seal must take it
            record["stop"] = record["stop"] or "STOP: out.tar could not be written; out/ kept for the seal"
            record["stop_class"] = record["stop_class"] or "infrastructure"
        finished = clock()
        record["finished_utc"] = utc(finished)
        record["gpu_seconds"] = round(finished - started, 1)
        diag = diag or empty_diagnostics(spec, node_name, job, wave, record)
        diag.update(attempt=record["attempt"], gpu_seconds=record["gpu_seconds"], stop=record["stop"],
                    stop_class=record["stop_class"])
        check_diagnostics(diag)
        unknown = set(record) - RECORD_KEYS
        if unknown:
            raise Stop(f"STOP: job record keys outside the fixed schema: {sorted(unknown)}")
        _write_json(attempt_dir / "job_record.json", record)
        _write_json(attempt_dir / "diagnostics.json", diag)
        L._write_sums(attempt_dir, ("out.tar", "job_record.json", "diagnostics.json"))
    finally:
        lease_cm.__exit__(None, None, None)
    if kind == "audits" and record["stop"] is None and audits_done(spec, node_name, wave):
        record["wave_checks"] = wave_checks(spec, node_name, wave)
    if record["stop"]:
        raise Stop(record["stop"])
    return record


def make_tar(attempt_dir: Path) -> bool:
    return subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=attempt_dir, capture_output=True).returncode == 0


def server_down(spec: dict, get) -> dict:
    """G5-TASL-GPUH B: the proposer is stopped during the audits (its card's hours count only over the waves)."""
    try:
        status, _ = get(spec["proposer"]["server_url"].rstrip("/") + "/health")
    except Exception as exc:  # noqa: BLE001 - unreachable is what this check wants
        return {"reachable": False, "error": type(exc).__name__}
    raise Stop(f"STOP: the proposer answers /health ({status}) during an audit job; under G5-TASL-GPUH B it is "
               f"stopped during the audits")


def empty_diagnostics(spec: dict, node: str, job: str, wave: int, record: dict) -> dict:
    kind, _ = job_parts(job)
    base = {"label": S.EVIDENCE, "run_id": spec["run_id"], "node": node, "job": job, "wave": wave,
            "attempt": record.get("attempt"), "spec_sha256": record["spec_sha256"]}
    if kind == "campaigns":
        zero = campaign_counts({}, max_tokens=spec["campaign"]["max_tokens"], ctx=spec["campaign"]["ctx"])
        return {"schema": DIAG_CAMPAIGN, **base, **zero}
    return {"schema": DIAG_AUDIT, **base, "chunk": record.get("chunk"), "chunks": None, "K": record.get("K"),
            "plan_sha256": record.get("plan_sha256"), "runs_planned_label": 0, "runs_planned_evaluation": 0,
            "label_seed_runs": {"ok": 0, "divergent": 0, "infrastructure": 0}, "seeds_planned": [],
            "wave_e5": None}


def campaign_diagnostics(spec: dict, node: dict, wave: int, record: dict, eng_out: Path) -> dict:
    want = {campaign_dir_name(i) for i in wave_instances(spec, wave)}
    ledgers = {p.parent.name: p.read_text().splitlines()
               for p in sorted(Path(eng_out).glob("instance_*/campaign_ledger.jsonl")) if p.parent.name in want}
    counts = campaign_counts(ledgers, max_tokens=spec["campaign"]["max_tokens"], ctx=spec["campaign"]["ctx"],
                             timeout_basis=node_timeout_basis(node))
    node = node["node"]
    crec_path = Path(eng_out) / "campaign_record.json"
    crec = json.loads(crec_path.read_text()) if crec_path.is_file() else {"stop": "no campaign_record.json"}
    d = {"schema": DIAG_CAMPAIGN, "label": S.EVIDENCE, "run_id": spec["run_id"], "node": node,
         "job": f"campaigns-wave{wave}", "wave": wave, "attempt": record.get("attempt"),
         "spec_sha256": record["spec_sha256"], **counts, "stop": None, "stop_class": None}
    ls = counts["ledger_stops"]
    if ls["stop_unisolated"]:
        d["stop"], d["stop_class"] = "STOP 2: a campaign run failed the isolation gate (stop_unisolated)", "node"
    elif ls["baseline_timeout"]:
        d["stop"], d["stop_class"] = "STOP 8: a baseline timeout STOPs the campaign", "timing"
    elif ls["baseline_failed"]:
        d["stop"], d["stop_class"] = "STOP 6: baseline_failed", "node"
    elif ls["stop_integrity"] or ls["stop_transport"]:
        d["stop"], d["stop_class"] = "STOP 6: stop_integrity or stop_transport", "infrastructure"
    elif counts["counts"]["prompt_overflow"]:
        d["stop"], d["stop_class"] = "STOP 4: a prompt longer than 32,768 - 4,096 tokens", "node"
    elif counts["checks"]["requests_without_cache_prompt_false"]:
        d["stop"], d["stop_class"] = "STOP: a manager request lacked cache_prompt: false (G.4's STOP)", \
            "infrastructure"
    elif counts["checks"]["run_median_over_basis"]:
        d["stop"], d["stop_class"] = ("STOP: the median run time on the 4090 is above the declared timeout basis "
                                      "(R1-G1B-TIMEOUT; G.4's timing STOP): the author decides", "timing")
    elif crec.get("stop"):
        d["stop"], d["stop_class"] = ENGINE_STOP_CAMPAIGN, "infrastructure"   # its own text stays in out.tar
    elif sorted(p.parent.name for p in Path(eng_out).glob("instance_*/campaign_ledger.jsonl")) != sorted(want):
        d["stop"], d["stop_class"] = (f"STOP: the engine's ledgers are not the wave's {sorted(want)}",
                                      "infrastructure")
    elif counts["counts"]["proposals"] != len(want) * spec["campaign"]["W"]:
        d["stop"], d["stop_class"] = (f"STOP: {counts['counts']['proposals']} proposals, expected "
                                      f"{len(want) * spec['campaign']['W']}", "infrastructure")
    return d


def plan_path(spec: dict, node: str, wave: int) -> Path:
    """The wave's clear plan index (counts and hashes only; §6): the plan itself, which shows the campaign's kept
    diffs, is in ``plan.tar`` beside it and is opened by job code with an access-log line."""
    return job_dir(spec, node, f"audits-wave{wave}") / "plan_index.json"


def _write_plan(spec: dict, node: str, wave: int, plan: dict) -> dict:
    d = job_dir(spec, node, f"audits-wave{wave}")
    d.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(plan, indent=1, sort_keys=True).encode()
    tar_path = d / "plan.tar"
    with tarfile.open(tar_path, "x") as tar:
        info = tarfile.TarInfo("plan.json")
        info.size, info.mtime = len(raw), 0
        tar.addfile(info, io.BytesIO(raw))
    index = {"schema": "g5_tasl_audit_plan_index/1", "node": node, "wave": wave, "K": plan["K"],
             "chunks": plan["chunks"], "groups": len(plan["groups"]), "units": len(plan["units"]),
             "plan_json_sha256": hashlib.sha256(raw).hexdigest(), "plan_tar_sha256": L._sha_file(tar_path),
             "campaign_attempt": plan["campaign_attempt"], "campaign_out_tar_sha256": plan["campaign_out_tar_sha256"]}
    _write_json(plan_path(spec, node, wave), index)
    return index


def load_plan(spec: dict, node: str, wave: int, purpose: str) -> dict:
    index = json.loads(plan_path(spec, node, wave).read_text())
    tar_path = plan_path(spec, node, wave).parent / "plan.tar"
    if L._sha_file(tar_path) != index["plan_tar_sha256"]:
        raise Stop(f"STOP: {tar_path} differs from its index")
    access(spec, tar_path, purpose)
    with tarfile.open(tar_path) as tar:
        raw = tar.extractfile("plan.json").read()
    if hashlib.sha256(raw).hexdigest() != index["plan_json_sha256"]:
        raise Stop("STOP: the plan differs from its index")
    plan = json.loads(raw)
    plan["sha256"] = index["plan_json_sha256"]
    return plan


def next_chunk(spec: dict, node: dict, wave: int, k: int) -> tuple[dict, int, list[dict]]:
    """The wave's plan (made once, from the completed campaign attempt's ledgers, read by job code with an
    access-log line) and the first chunk without a completed attempt."""
    if not plan_path(spec, node["node"], wave).is_file():
        camp = job_dir(spec, node["node"], f"campaigns-wave{wave}")
        got = complete_attempt(camp)
        if not got:
            raise Stop(f"STOP: no completed campaigns-wave{wave} attempt")
        tar = camp / f"attempt-{got[0]['attempt']}" / "out.tar"
        ledgers = tar_members(spec, tar, LEDGER_MEMBER, f"audit planning: campaign ledgers of {node['node']} "
                                                       f"wave {wave}")
        prior, prior_groups = {}, set()
        if wave == 2:
            p1 = load_plan(spec, node["node"], 1, f"audit planning: wave-1 plan of {node['node']}")
            prior = {u["unit"]: u for u in p1["units"]}
            prior_groups = {f"{g['parent_state']}:{g['candidate_state']}" for g in p1["groups"]}
        plan = audit_plan(spec, node["node"], wave, ledgers, prior_units=prior, prior_groups=prior_groups, k=k)
        chunks = chunk_plan(plan, node)
        plan.update(chunks=len(chunks), chunk_runs=chunks, campaign_attempt=got[0]["attempt"],
                    campaign_out_tar_sha256=got[0].get("out_tar_sha256"))
        _write_plan(spec, node["node"], wave, plan)
    index = json.loads(plan_path(spec, node["node"], wave).read_text())
    if index["K"] != k:
        raise Stop(f"STOP: the wave's plan was made at K = {index['K']}, the note now says K = {k}")
    for i in range(index["chunks"]):
        if not complete_attempt(job_dir(spec, node["node"], f"audits-wave{wave}", i)):
            plan = load_plan(spec, node["node"], wave, f"audit planning: plan of {node['node']} wave {wave}")
            return plan, i, plan["chunk_runs"][i]
    raise Stop(f"STOP: {node['node']} audits-wave{wave}: every chunk is complete")


def audit_diagnostics(spec: dict, node: dict, wave: int, record: dict, plan: dict, index: int, chunk: dict,
                      eng_out: Path) -> dict:
    """Clear diagnostics of one audit chunk (B1): outcome counts on the label seeds only; on the evaluation seeds only
    the number of planned runs (every planned run has a row, or the chunk STOPs). The wave's last chunk adds E5 over
    the wave (label seeds only)."""
    d = empty_diagnostics(spec, node["node"], f"audits-wave{wave}", wave, record)
    label = set(plan["label_seeds"])
    d.update(chunks=plan["chunks"], stop=None, stop_class=None,
             runs_planned_label=sum(r["seed"] in label for r in chunk["runs"]),
             runs_planned_evaluation=sum(r["seed"] not in label for r in chunk["runs"]),
             seeds_planned=sorted({r["seed"] for r in chunk["runs"]}))
    crec_path = Path(eng_out) / "chunk_record.json"
    crec = json.loads(crec_path.read_text()) if crec_path.is_file() else {"stop": "no chunk_record.json"}
    rows_path = Path(eng_out) / "rows.jsonl"
    try:
        rows = read_rows(rows_path.read_text().splitlines() if rows_path.is_file() else [], chunk)
    except Stop as exc:
        d["stop"] = str(exc)
        d["stop_class"] = "node" if str(exc).startswith(("STOP 2", "STOP 10")) else "infrastructure"
        return d
    lab = [r for r in rows if r["seed"] in label]
    d["label_seed_runs"] = {"ok": sum(r["kind"] == "ok" for r in lab),
                            "divergent": sum(r["kind"] == "divergent" for r in lab),
                            "infrastructure": sum(r["kind"] == "infrastructure_failure" for r in lab)}
    if any(r["kind"] == "infrastructure_failure" for r in rows):
        d["stop"], d["stop_class"] = ("STOP 7: final infrastructure failures in the audit chunk after the engine's "
                                      "reruns (a new attempt after diagnosis)", "infrastructure")
    elif crec.get("stop"):
        d["stop"], d["stop_class"] = ENGINE_STOP_AUDIT, "infrastructure"      # its own text stays in out.tar
    elif index == plan["chunks"] - 1:                          # the wave's last chunk: E5 over all chunks
        all_rows = rows + _chunk_rows(spec, node["node"], wave, range(plan["chunks"] - 1))
        if plan.get("reused_units"):                            # reused units' rows come from wave 1
            p1 = json.loads(plan_path(spec, node["node"], 1).read_text())
            reused = set(plan["reused_units"])
            all_rows += [r for r in _chunk_rows(spec, node["node"], 1, range(p1["chunks"]), reused=True)
                         if r["unit"] in reused]
        d["wave_e5"] = e5(plan, all_rows)
    return d


def _chunk_rows(spec: dict, node: str, wave: int, chunks, *, reused: bool = False) -> list[dict]:
    out = []
    for i in chunks:
        cdir = job_dir(spec, node, f"audits-wave{wave}", i)
        got = complete_attempt(cdir)
        tar = cdir / f"attempt-{got[0]['attempt']}" / "out.tar"
        members = tar_members(spec, tar, CHUNK_MEMBERS, f"wave E5: audit rows of {node} wave {wave}"
                                                        + (" (reused units)" if reused else ""))
        chunk_i = json.loads("\n".join(members["out/chunk.json"]))
        out += read_rows(members["out/audit/rows.jsonl"], chunk_i)
    return out


# =============================================================================================== close-attempt
# The engines' own stop text may name values or seeds; it stays sealed in out.tar, and the clear diagnostics and job
# record carry only these fixed reasons (round-2 review n1).
ENGINE_STOP_CAMPAIGN = "STOP: the campaign engine reported a stop (its text is sealed in out.tar)"
ENGINE_STOP_AUDIT = "STOP: the audit engine reported a stop (its text is sealed in out.tar)"


def close_attempt(spec: dict, spec_path: Path, node: str, job: str, attempt_dir: Path, reason: str, *,
                  chunk: int | None = None, alive=None, scan=G.processes_mentioning, now=time.time) -> dict:
    """Close a G.5 attempt that left no job record (an OOM kill in the shared scope, a reboot): after checking that it
    is not running (no process names it, its process is gone, same host, the lease free), write a G.5-schema record
    with stop_class "infrastructure" and the elapsed seconds since the attempt started, counted on the meter
    (STOP 9). Nothing is deleted; out/ stays for the seal."""
    kind, wave = job_parts(job)
    attempt_dir = Path(attempt_dir)
    expected = job_dir(spec, node, job, chunk if kind == "audits" else None)
    if kind == "audits" and chunk is None:
        raise Stop("STOP: an audit attempt is closed with its chunk")
    if attempt_dir.resolve().parent != expected.resolve() or not G.ATTEMPT.fullmatch(attempt_dir.name):
        raise Stop(f"STOP: {attempt_dir} is not an attempt of {node} {job}" + (f" chunk {chunk}" if chunk is not None
                                                                             else ""))
    if (attempt_dir / "job_record.json").exists():
        raise Stop("STOP: close-attempt needs an attempt directory without a job record")
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        raise Stop("STOP: close-attempt needs a reason (at least 10 characters)")
    running = scan(attempt_dir)
    if running:
        raise Stop(f"STOP: processes {running} still name {attempt_dir} on their command line")
    owner_path = attempt_dir / "attempt.json"
    if not owner_path.is_file():
        raise Stop("STOP: the attempt has no attempt.json; its start time is unknown (inspect it by hand)")
    owner = json.loads(owner_path.read_text())
    if owner.get("hostname") != G.socket.gethostname():
        raise Stop(f"STOP: the attempt was started on {owner.get('hostname')!r}; close it there")

    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
    if owner.get("pid") is not None and (alive or _alive)(int(owner["pid"])):
        raise Stop(f"STOP: process {owner['pid']} of the attempt is still alive")
    start = datetime.strptime(owner["started_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    with G.gpu_lease(spec["worker"]["lease"]):
        closed = now()
        record = {"schema": RECORD_SCHEMA, "label": S.EVIDENCE, "run_id": spec["run_id"], "node": node,
                  "family": S.node_entry(spec, node)["family"], "job": job, "wave": wave, "chunk": chunk,
                  "attempt": owner["attempt"], "spec_sha256": L._sha_file(spec_path), "owner": owner,
                  "started_utc": owner["started_utc"], "finished_utc": utc(closed),
                  "gpu_seconds": round(max(0.0, closed - start), 1),
                  "stop": f"STOP: closed without a job record: {reason.strip()}", "stop_class": "infrastructure"}
        _write_json(attempt_dir / "job_record.json", record)
    return record


# =============================================================================================== the proposer
def serve_launch(spec_path: Path, note_path: Path, *, enable: bool, on_main=G._note_on_main, read_main=G._read_main,
                 server=None, launch_binding=None) -> dict:
    """The G.5 proposer on TASL-7 behind the same gate as the jobs: the spec validated for launch, the signed note,
    both keys and the TASL launch binding; then ``g4_tasl.serve_spec`` (lease, binary, build directory, GGUF, exam
    settings, server record) with the G.5 spec."""
    spec_path = Path(spec_path)
    spec = S.load_spec(spec_path)
    S.validate_spec(spec, launch=True)
    S.check_note(note_path, spec_path, spec=spec, on_main=on_main, read_main=read_main)
    if not enable or os.environ.get(S.ENABLE_ENV) != "1":
        raise Stop(f"STOP: the G.5 proposer server is disabled (needs --enable AND {S.ENABLE_ENV}=1)")

    def bind(repo, s, rows):
        imports = S.check_import_sources(repo)
        return {**G.verify_launch_tasl(repo, s, rows, spec_path=spec_path), "imports": imports}
    binding = (launch_binding or bind)(S.REPO_ROOT, spec, S.PLAN_ROWS)
    return (server or T4.serve_spec)(spec, spec_path) | {"launch": binding}
