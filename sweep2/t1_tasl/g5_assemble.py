"""The G.5 T1 label table: assembly from the sealed tree, in two locked stages (G.5 code unit part 3b-2). AI-assisted
(Claude). EVIDENCE table.

Authority: the G.5 authorization draft revision 8 §3 (the label table), §6 (staged release; R1-T1-LABELS-UNSEAL,
R1-T1-LABELS-TEST-RELEASE), §2.4 (G5-AUDIT A, E5 on the label seeds), §9; the frozen preregistration's PRE-STAGE A,
PRE-DELTA A (as amended by REL-T1-G1B), PRE-DIV A and §6; R1-SWEEP2-RELEASE-DECISIONS (REL-SCOPE A, REL-CODE A,
REL-T1-G1B); the conditions of ``proposals/R1_LABEL_RELEASE_ROWS_DRAFT_20261121.md`` ("G.5 completion schema", "G.5
outputs": a reviewed extraction step places the label and evaluation blocks, with their completion record, in an
unsealed audit directory).

**What it writes**, in the layouts ``r1.c3.release`` and ``r1.c3.gate_input_builder`` read for a gate source
(``source g5``, tier T1), so that neither changes:
- a table directory: ``proposals.jsonl`` (one row per proposal of the assembled nodes, the sweep-table fields the
  builder and the release step use: ``proposal_id`` ``g5.<mode>:<node>__s<seed>:t<step>``, ``instance``,
  ``instance_seed``, ``node``, ``memory_mode``, ``noop``, ``duplicate``, ``delta_hat``, ``sigma_node``, ``sigma_cmp``,
  ``incumbent_hash``, ``candidate_hash``, ``features`` (empty: the T1 featurisation for A3/A5 is not this unit's)) and
  ``build.json`` (deterministic: every input's sha256, the readings below);
- an evidence directory: ``label_block.jsonl`` (``audit.evidence_blocks``' row shapes: ``rule_noop`` for no-ops,
  ``audit`` with ``delta_label``/``se_label``/``soft_parameters`` at the label seeds, ``divergent`` when E5 makes the
  proposal divergent) and ``evidence_completion.json`` (schema ``g5_t1_evidence_completion/1``, not the B.2 audit's
  ``r1.c3_audit_completion/``, so ``release.evidence_tier`` gives no tier and every raw reader needs both tiers' test
  rows); after the test row, ``evaluation_block.jsonl`` (PRE-DIV A's ``divergent_seeds``/``k_evaluation``) and
  ``evidence_completion_test.json``.

**Two stages, each behind its release row** (every read of sealed content goes through ``g5_seal.SealedTree``, which
checks the purpose's row and logs the opening):
- ``traindev`` (R1-T1-LABELS-UNSEAL on the committed PLAN, through ``release.release_row``): the nodes the row names
  (its G.1b summaries, PRE-DELTA), their sealed campaign ledgers, plans and audit rows; values are kept at the **label
  seeds only** (an evaluation-seed value is dropped when its row is parsed and never stored); σ_node is the cited
  summary's joint σ. The label block holds every instance of those nodes (train, dev and test), because the release
  step's test stage requires the same label block; it stays in the evidence directory, where only the release step
  (and, after the test row, the tier's raw readers) may open it.
- ``test`` (R1-T1-LABELS-TEST-RELEASE, which itself needs the arms-frozen record, and the train/dev row): the table and
  label block are re-derived and must be byte-identical; then the evaluation seeds are read and the evaluation block is
  written.
- ``verify_evidence`` is the G.5 integrity check the release step runs (registered in ``r1/c3/release_checks.py`` under
  REL-CODE A): inside the release step's integrity context it re-derives the blocks from the sealed tree and compares
  bytes; before the test row it reads label seeds only and refuses an evaluation block that already exists.

**Labels** (§2.4, E5 on the label seeds; R1-MAIN-PROPOSER (e)). Each audited proposal belongs to the cross-instance
group (incumbent hash, candidate hash) of its wave's plan, or of wave 1's when wave 2 carried it; every member of a
group carries the group's label. Per label seed s, d_s = sign × (value of the candidate unit − value of the parent
unit), sign +1 for ``metric_direction: maximize`` and −1 for ``minimize`` (read from the node spec at the family's
G.5 commit, checked against ``node_spec_sha256``). More than half of the label seeds divergent on the candidate:
``label_kind: divergent``. Otherwise the seeds where both sides are ok give ``delta_label`` (mean) and ``se_label``
(sd / √k), ``k_label`` < K_label marking a partial label; a parent diverging so that fewer than half the label seeds
remain is a STOP for the author (E5 gives no rule). Evaluation (PRE-DIV A): ``divergent_seeds`` are the evaluation
seeds where the candidate diverged; at most half: Δ_true over the rest; more than half: divergent (no value); an
evaluation seed where only the parent diverged is a STOP for the author (the frozen builder ties ``k_evaluation`` to
``divergent_seeds``).

**Readings this unit proposes** (recorded in ``build.json``; each needs the author's confirmation, see the report):
σ_cmp = σ_node; proposals not run (invalid, refused, final infrastructure failures) left out of the table as the
sweep tables leave out skipped proposals, counted; Δ̂ = sign × (campaign value − best before the step), 0 for no-ops
and duplicates; Δ̂ of a proposal that diverged or timed out in its campaign: ``refuse`` by default (the assembly
STOPs), or ``neg_inf`` (−∞, "never kept", which the frozen builder handles but which is not standard JSON) only when the
author chooses it. G5-AUDIT B is refused (the draft gives no table rule for unaudited in-campaign divergent proposals).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_tasl as G  # noqa: E402
import g5_job as J  # noqa: E402
import g5_seal as SE  # noqa: E402
import g5_tasl as S  # noqa: E402

L = G.L
Stop = G.Stop
SOURCE = "g5"
STAGES = ("traindev", "test")
TABLE_SCHEMA = "g5_t1_table/1"
COMPLETION_SCHEMA = "g5_t1_evidence_completion/1"
SPEC_REL = "sweep2/t1_tasl/g5_tasl_spec.json"
DIVERGENT_DELTA_HAT = ("refuse", "neg_inf")
TABLED = ("kept", "discarded", "discarded_divergent", "not_run_inert", "not_run_duplicate")
DIRECTION = re.compile(r"^metric_direction:\s*(maximize|minimize)\s*$", re.M)
SUITE = re.compile(r"^suite:\s*([a-z0-9_]+)\s*$", re.M)
READINGS = {
    "sigma_cmp": "sigma_node (the node's G.1b joint sigma; the draft fixes only the soft-label width; proposed)",
    "excluded_from_table": "invalid_proposal, not_run_refused and other not-run decisions except inert and duplicate, "
                           "infrastructure_failure_final (the sweep tables leave out skipped proposals); counted",
    "delta_hat": "sign x (campaign value - best before the step), sign +1 maximize / -1 minimize; 0.0 for no-ops and "
                 "within-campaign duplicates",
    "label_parent_divergence": "fewer than half the label seeds left after the parent's divergent seeds: STOP",
    "evaluation_parent_only_divergence": "an evaluation seed where only the parent diverged: STOP",
}


def _dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(", ", ": "))


def _lines(rows: list[dict]) -> bytes:
    return "".join(_dumps(r) + "\n" for r in rows).encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# =============================================================================================== inputs
def node_metric(spec: dict, node: str, *, git=G._sh) -> dict:
    """The node's metric direction and suite, from its node spec at the family's G.5 commit (sha256 checked)."""
    n = S.node_entry(spec, node)
    fam = spec["harness_families"][n["family"]]
    res = git(["git", "-C", fam["harness_dir"], "show", f"{fam['g5_commit']}:{n['spec_path']}"])
    raw = res.stdout if isinstance(res.stdout, bytes) else (res.stdout or "").encode()
    if res.returncode != 0 or _sha(raw) != n["node_spec_sha256"]:
        raise Stop(f"STOP: {node}'s node spec at the G.5 commit is missing or differs from node_spec_sha256")
    text = raw.decode()
    d, s = DIRECTION.findall(text), SUITE.findall(text)
    if len(d) != 1 or len(s) != 1:
        raise Stop(f"STOP: {node}'s node spec must name metric_direction and suite exactly once")
    return {"metric_direction": d[0], "sign": 1.0 if d[0] == "maximize" else -1.0, "suite": s[0]}


def noise_by_node(spec: dict, row: dict) -> dict:
    """σ_node per node from the G.1b summaries the train/dev row cites (PRE-DELTA A, REL-T1-G1B): each a committed
    REL-T1-G1B copy (the row check verified its bytes); the seven nodes' must be the spec's seven-node copy, and
    autoresearch's the spec's copy under G5-ARPEND B (under A the completion record named it at every job start)."""
    out = {}
    cited = row.get("g1b_summaries") or {}
    if not cited:
        raise Stop("STOP: the train/dev row cites no G.1b summary (PRE-DELTA)")
    nf = spec["noise_floor"]
    for node, c in sorted(cited.items()):
        S.node_entry(spec, node)
        raw = (S.REPO_ROOT / c["path"]).read_bytes()
        if _sha(raw) != c["sha256"]:
            raise Stop(f"STOP: {c['path']} differs from the sha256 the row cites")
        key = "ar" if node == S.AR else "seven"
        e = nf[key]
        if key == "seven" or S.options(spec)["G5-ARPEND"] == "B":
            if (c["path"], c["sha256"]) != (e.get("copy"), e.get("sha256")):
                raise Stop(f"STOP: the row's G.1b summary for {node} is not the spec's REL-T1-G1B copy "
                           f"(noise_floor.{key})")
        s = json.loads(raw)
        if s.get("schema") != e["schema"] or s.get("run_id") != e["run_id"] or s.get("label") != G.ENGINEERING_ONLY:
            raise Stop(f"STOP: {c['path']} is not the {e['schema']} summary of {e['run_id']}")
        v = (s.get("verdicts") or {}).get(node) or {}
        sigma = v.get("sigma_joint")
        if v.get("qualifies_D21") is not True or not isinstance(sigma, (int, float)) or not math.isfinite(sigma) \
                or sigma <= 0:
            raise Stop(f"STOP: {node} has no qualifying G.1b verdict with a positive joint sigma (STOP 5)")
        out[node] = {"sigma_node": float(sigma), "summary": c["path"], "summary_sha256": c["sha256"]}
    return out


def _one_attempt(d: Path) -> Path:
    """The one complete sealed attempt of a job or chunk directory; every other sealed attempt ended in an
    infrastructure STOP (one attempt per job, chosen by the rule, never by result)."""
    done, others = [], []
    for _, p in G.attempts(d):
        SE.verify_sealed(p)
        rec = json.loads((p / "job_record.json").read_text())
        (done if rec.get("stop") is None else others).append((p, rec))
    if len(done) != 1:
        raise Stop(f"STOP: {d} has {len(done)} complete sealed attempts (one is needed)")
    bad = [p.name for p, r in others if r.get("stop_class") != "infrastructure"]
    if bad:
        raise Stop(f"STOP: {d} has sealed attempts {bad} that ended in an author STOP; an author row decides")
    return done[0][0]


def sealed_node(spec: dict, node: str, spec_sha256: str) -> dict:
    """The node's sealed inputs: one complete attempt per job and chunk, its sealed plans, all bound together."""
    root = SE.sealed_run(spec) / node
    SE.verify_sealed(root / "_node")
    out = {"campaigns": {}, "chunks": {}, "index": {}, "records": []}
    for wave in (1, 2):
        camp = _one_attempt(root / f"campaigns-wave{wave}")
        idx_path = root / "_node" / f"wave{wave}_plan_index.json"
        if not idx_path.is_file():
            raise Stop(f"STOP: {node} wave {wave} has no sealed plan index")
        idx = json.loads(idx_path.read_text())
        crec = json.loads((camp / "job_record.json").read_text())
        if idx.get("campaign_out_tar_sha256") != crec.get("out_tar_sha256") or \
                idx.get("campaign_out_tar_sha256") != L._sha_file(camp / "out.tar"):
            raise Stop(f"STOP: {node} wave {wave}: the plan was not made from the sealed campaign attempt")
        chunks = []
        for i in range(idx["chunks"]):
            c = _one_attempt(root / f"audits-wave{wave}" / f"chunk-{i}")
            r = json.loads((c / "job_record.json").read_text())
            if r.get("plan_sha256") != idx["plan_json_sha256"] or r.get("chunk") != i or r.get("K") != idx["K"]:
                raise Stop(f"STOP: {node} wave {wave} chunk {i} does not belong to the sealed plan")
            chunks.append(c)
            out["records"].append(r)
        extra = sorted(p.name for p in (root / f"audits-wave{wave}").glob("chunk-*")
                       if not re.fullmatch(rf"chunk-({'|'.join(map(str, range(idx['chunks'])))})", p.name))
        if extra:
            raise Stop(f"STOP: {node} wave {wave} has chunks outside its plan: {extra}")
        out["campaigns"][wave], out["chunks"][wave], out["index"][wave] = camp, chunks, idx
        out["records"].append(crec)
    for r in out["records"]:
        if r.get("spec_sha256") != spec_sha256 or r.get("run_id") != spec["run_id"] or r.get("node") != node:
            raise Stop(f"STOP: a sealed record of {node} was written under another spec, run or node")
    if out["index"][1]["K"] != out["index"][2]["K"]:
        raise Stop(f"STOP: {node}'s two waves were planned at different K (P4: K is uniform)")
    return out


def _values(rows_lines: list[str], chunk: dict, keep: set[int]) -> dict:
    """{(unit, seed): (kind, value or None)}: the rows checked as the job checks them (``g5_job.read_rows``), the value
    (``outcome.value``) kept only at the seeds in ``keep`` and only for ok rows; any other value is dropped here."""
    J.read_rows(rows_lines, chunk)
    out = {}
    for line in rows_lines:
        if not line.strip():
            continue
        r = json.loads(line)
        kind = r["outcome"]["kind"]
        if kind == "infrastructure_failure":
            raise Stop("STOP: a complete chunk holds an infrastructure row (contract)")
        value = None
        if r["seed"] in keep and kind == "ok":
            value = r["outcome"].get("value")
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                raise Stop("STOP: an ok audit row lacks a finite outcome.value (contract: non-finite is divergent)")
            value = float(value)
        out[(r["unit"], r["seed"])] = (kind, value)
    return out


def read_node(spec: dict, node: str, inputs: dict, tree, stage: str, *, purpose_head: str) -> dict:
    """Ledgers, plans and audit row outcomes of one node through the sealed tree's reader."""
    if SE.PURPOSES.get(purpose_head, (None,))[0] != stage:          # the purpose's lock is the stage's row
        raise Stop(f"STOP 11: {purpose_head!r} is not a declared purpose of the {stage} stage")
    k = inputs["index"][1]["K"]
    seeds = S.audit_seeds(spec, k)
    keep = set(seeds["label"]) | (set(seeds["evaluation"]) if stage == "test" else set())   # evaluation values: test only
    root = SE.sealed_run(spec) / node
    ledgers, plans, values = {}, {}, {}
    for wave in (1, 2):
        got = tree.open_members(inputs["campaigns"][wave], "out.tar", J.LEDGER_MEMBER,
                                f"{purpose_head} {node} campaign ledgers wave {wave}")
        ledgers[wave] = {name: raw.decode().splitlines() for name, raw in got.items()}
        raw = tree.open_members(root / "_node", f"wave{wave}_plan.tar", ("plan.json",),
                                f"{purpose_head} {node} plan wave {wave}")["plan.json"]
        if _sha(raw) != inputs["index"][wave]["plan_json_sha256"]:
            raise Stop(f"STOP: {node} wave {wave}: the sealed plan differs from its index")
        plans[wave] = json.loads(raw)
        for i, cdir in enumerate(inputs["chunks"][wave]):
            m = tree.open_members(cdir, "out.tar", J.CHUNK_MEMBERS, f"{purpose_head} {node} audit rows wave {wave} "
                                                                     f"chunk {i}")
            chunk = json.loads(m["out/chunk.json"])
            if chunk.get("chunk") != i or chunk.get("K") != k or chunk.get("node") != node or chunk.get("wave") != wave:
                raise Stop(f"STOP: {node} wave {wave} chunk {i}: the sealed chunk file does not match")
            for key, v in _values(m["out/audit/rows.jsonl"].decode().splitlines(), chunk, keep).items():
                if key in values:
                    raise Stop(f"STOP: {node}: the audit run {key} appears in two chunks")
                values[key] = v
    return {"K": k, "seeds": seeds, "ledgers": ledgers, "plans": plans, "values": values}


# =============================================================================================== labels
def _pairs(values: dict, cu: str, pu: str, seeds: list[int]) -> tuple[list[int], list[int], list[int]]:
    """(candidate-divergent seeds, parent-only-divergent seeds, seeds where both are ok)."""
    cand_div, par_only, ok = [], [], []
    for s in seeds:
        if (cu, s) not in values or (pu, s) not in values:
            raise Stop(f"STOP: the audit runs of {cu} / {pu} at seed {s} are missing")
        ck, pk = values[(cu, s)][0], values[(pu, s)][0]
        if ck == "divergent":
            cand_div.append(s)
        elif pk == "divergent":
            par_only.append(s)
        else:
            ok.append(s)
    return cand_div, par_only, ok


def _mean_se(d: list[float]) -> tuple[float, float | None]:
    k = len(d)
    mean = math.fsum(d) / k
    se = math.sqrt(math.fsum((x - mean) ** 2 for x in d) / (k - 1)) / math.sqrt(k) if k > 1 else None
    return mean, se


def group_label(values: dict, cu: str, pu: str, seeds: list[int], sign: float, sigma: float, group: str) -> dict:
    """E5 and the paired label of one group on the label seeds."""
    cand_div, par_only, ok = _pairs(values, cu, pu, seeds)
    n = len(seeds)
    if len(cand_div) > n / 2:
        return {"label_kind": "divergent", "seeds": list(seeds), "divergent_seeds": cand_div, "audit_group": group}
    if n - len(ok) > n / 2:
        raise Stop(f"STOP: group {group}: the parent diverged at label seeds {par_only}, leaving {len(ok)} of {n}; "
                   f"E5 gives no rule; the author decides")
    d = [sign * (values[(cu, s)][1] - values[(pu, s)][1]) for s in ok]
    mean, se = _mean_se(d)
    return {"label_kind": "audit", "seeds": list(seeds), "delta_label": mean, "se_label": se,
            "soft_parameters": {"inert": False, "sigma_node": sigma, "k_label": len(ok), "delta_label": mean,
                                "se_label": se},
            "divergent_seeds": sorted(cand_div + par_only), "audit_group": group}


def group_evaluation(values: dict, cu: str, pu: str, seeds: list[int], sign: float, group: str) -> dict:
    """PRE-DIV A on the evaluation seeds of one group."""
    cand_div, par_only, ok = _pairs(values, cu, pu, seeds)
    if par_only:
        raise Stop(f"STOP: group {group}: {len(par_only)} evaluation seed(s) where only the parent diverged; the frozen "
                   f"builder has no rule for them; the author decides (counts only are reported)")
    n = len(seeds)
    if len(cand_div) > n / 2:
        return {"seeds": list(seeds), "delta_evaluation": None, "se_evaluation": None, "divergent_seeds": cand_div,
                "k_evaluation": n - len(cand_div), "audit_group": group}
    mean, se = _mean_se([sign * (values[(cu, s)][1] - values[(pu, s)][1]) for s in ok])
    return {"seeds": list(seeds), "delta_evaluation": mean, "se_evaluation": se, "divergent_seeds": cand_div,
            "k_evaluation": n - len(cand_div), "audit_group": group}


# =============================================================================================== the table
def node_rows(spec: dict, node: str, data: dict, metric: dict, sigma: float, stage: str,
              divergent_delta_hat: str) -> dict:
    """Table, label and (test stage) evaluation rows of one node, and the counts."""
    if S.options(spec)["G5-AUDIT"] != "A":
        raise Stop("STOP: the assembly under G5-AUDIT B is not built (no table rule for unaudited in-campaign "
                   "divergent proposals)")
    sign, values, seeds = metric["sign"], data["values"], data["seeds"]
    groups = {}
    for wave in (1, 2):
        for g in data["plans"][wave]["groups"]:
            key = f"{g['parent_state']}:{g['candidate_state']}"
            if key in groups:
                raise Stop(f"STOP: {node}: group {key} is planned in two waves")
            groups[key] = g
    labels_by_group, evals_by_group = {}, {}
    table, labels, evals = [], [], []
    counts = {"excluded": {}, "rows": 0, "noop": 0, "duplicate": 0, "audited_members": 0, "divergent_in_campaign": 0}
    lo = spec["instances"]["seeds"][0] - 1
    for wave in (1, 2):
        want = {J.campaign_dir_name(i) for i in J.wave_instances(spec, wave)}
        if set(data["ledgers"][wave]) != want:
            raise Stop(f"STOP: {node} wave {wave}: the sealed ledgers are not the wave's {sorted(want)}")
        for name, lines in sorted(data["ledgers"][wave].items()):
            led = J.parse_ledger(lines, name)
            if led["stop"] is not None or led["baseline_state"] is None:
                raise Stop(f"STOP: {node} {name}: a complete campaign attempt holds a stopped ledger")
            k, mode = int(name.split("_")[1]), name.split("_", 2)[2]
            seed = lo + k
            inst = f"{node}__s{seed}"
            steps = {st["step"]: st for st in led["steps"]}
            best = led["entries"][0].get("best_after")
            for e in led["entries"][1:]:
                dec, step = e["decision"], e["step"]
                st = steps[step]
                best_before, best = best, e.get("best_after")
                if dec not in TABLED:
                    counts["excluded"][dec] = counts["excluded"].get(dec, 0) + 1
                    continue
                run = (e.get("runs") or [{}])[-1]
                row = {"proposal_id": f"{SOURCE}.{mode}:{inst}:t{step:03d}", "instance": inst, "instance_seed": seed,
                       "node": node, "source": SOURCE, "memory_mode": mode, "budget_index": step, "wave": wave,
                       "decision": dec, "noop": dec == "not_run_inert", "duplicate": dec == "not_run_duplicate",
                       "incumbent_hash": st["parent_state"], "sigma_node": sigma, "sigma_cmp": sigma, "features": {},
                       "audit_group": None}
                row["inert"] = row["noop"]
                row["rule_skip"] = row["noop"] or row["duplicate"]
                if dec in J.RAN:
                    g = groups.get(f"{st['parent_state']}:{st['candidate_state']}")
                    if g is None:
                        raise Stop(f"STOP: {node} {name} step {step}: an audited proposal has no group in the plans")
                    row.update(candidate_hash=st["candidate_state"], audit_group=g["group"])
                    if dec == "discarded_divergent":
                        counts["divergent_in_campaign"] += 1
                        if divergent_delta_hat != "neg_inf":
                            raise Stop("STOP: a proposal that diverged or timed out in its campaign has no logged "
                                       "delta_hat; the author chooses the reading (--divergent-delta-hat neg_inf, or "
                                       "another rule); the assembly refuses until then")
                        row["delta_hat"] = float("-inf")
                    else:
                        value = (e.get("final_outcome") or {}).get("value")
                        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (value, best_before)):
                            raise Stop(f"STOP: {node} {name} step {step}: no finite campaign value or best before it")
                        row["delta_hat"] = sign * (float(value) - float(best_before))
                    if g["group"] not in labels_by_group:
                        labels_by_group[g["group"]] = group_label(values, g["candidate_unit"], g["parent_unit"],
                                                                  seeds["label"], sign, sigma, g["group"])
                        if stage == "test":
                            evals_by_group[g["group"]] = group_evaluation(values, g["candidate_unit"],
                                                                          g["parent_unit"], seeds["evaluation"],
                                                                          sign, g["group"])
                    labels.append({"proposal_id": row["proposal_id"], "node": node, **labels_by_group[g["group"]]})
                    if stage == "test":
                        evals.append({"proposal_id": row["proposal_id"], "node": node, **evals_by_group[g["group"]]})
                    counts["audited_members"] += 1
                else:
                    cand = run.get("code_state_sha256") or (st["parent_state"] if row["noop"] else None)
                    if not cand:
                        raise Stop(f"STOP: {node} {name} step {step}: a duplicate without its code state (repeat key)")
                    row.update(candidate_hash=cand, delta_hat=0.0)
                    if row["noop"]:
                        labels.append({"proposal_id": row["proposal_id"], "node": node, "label_kind": "rule_noop",
                                       "delta_label": 0.0, "se_label": 0.0, "soft_parameters": {"inert": True}})
                        counts["noop"] += 1
                    else:
                        counts["duplicate"] += 1
                table.append(row)
                counts["rows"] += 1
    counts["groups_labelled"] = len(labels_by_group)
    counts["label_kinds"] = {kd: sum(1 for x in labels if x["label_kind"] == kd)
                             for kd in ("rule_noop", "audit", "divergent")}
    counts["label_partial"] = sum(1 for x in labels if x["label_kind"] == "audit"
                                  and x["soft_parameters"]["k_label"] < len(seeds["label"]))
    eval_counts = None                  # test stage only; kept out of build.json, which both stages must give equal
    if stage == "test":
        eval_counts = {"evaluation_divergent": sum(1 for x in evals if x["delta_evaluation"] is None),
                       "evaluation_partial": sum(1 for x in evals if x["delta_evaluation"] is not None
                                                 and x["divergent_seeds"])}
    return {"table": table, "labels": labels, "evaluations": evals, "counts": counts, "eval_counts": eval_counts}


def derive(spec: dict, spec_sha256: str, stage: str, tree, row: dict, *, purpose_head: str,
           divergent_delta_hat: str = "refuse", git=G._sh) -> dict:
    """The table, label block and (test stage) evaluation block of the nodes the train/dev row names, as bytes."""
    if stage not in STAGES:
        raise Stop(f"STOP: stage must be one of {STAGES}")
    if divergent_delta_hat not in DIVERGENT_DELTA_HAT:
        raise Stop(f"STOP: divergent_delta_hat must be one of {DIVERGENT_DELTA_HAT}")
    SE.check_seal_mode(spec)
    J.check_access_log(spec)                        # STOP 11 over the job code's reads during the table
    SE.check_access_log(spec)                       # STOP 11 over every earlier opening of the sealed tree
    noise = noise_by_node(spec, row)
    table, labels, evals, nodes, ks, eval_counts = [], [], [], {}, set(), {}
    for node in sorted(noise):
        inputs = sealed_node(spec, node, spec_sha256)
        metric = node_metric(spec, node, git=git)
        data = read_node(spec, node, inputs, tree, stage, purpose_head=purpose_head)
        ks.add(data["K"])
        got = node_rows(spec, node, data, metric, noise[node]["sigma_node"], stage, divergent_delta_hat)
        table += got["table"]
        labels += got["labels"]
        evals += got["evaluations"]
        eval_counts[node] = got["eval_counts"]
        nodes[node] = {**noise[node], **metric, "K": data["K"], "counts": got["counts"],
                       "attempts": sorted(str(p) for p in [*inputs["campaigns"].values(),
                                                           *inputs["chunks"][1], *inputs["chunks"][2]])}
    if len(ks) != 1:
        raise Stop(f"STOP: the assembled nodes were audited at different K {sorted(ks)} (P4)")
    k = ks.pop()
    seeds = S.audit_seeds(spec, k)
    key = (lambda r: r["proposal_id"])
    table_b, labels_b = _lines(sorted(table, key=key)), _lines(sorted(labels, key=key))
    build = {"schema": TABLE_SCHEMA, "label": S.EVIDENCE, "source": SOURCE, "tier": "T1", "run_id": spec["run_id"],
             "spec_path": SPEC_REL, "spec_sha256": spec_sha256, "sealed_run": str(SE.sealed_run(spec)),
             "K": k, "label_seeds": seeds["label"], "evaluation_seeds": seeds["evaluation"],
             "memory_modes": spec["memory"]["modes"], "options": S.options(spec), "nodes": nodes,
             "train_dev_row": {"row_id": row["row_id"], "decision_sha256": row["decision_sha256"]},
             "readings": {**READINGS, "campaign_divergent_delta_hat": divergent_delta_hat},
             "proposals_sha256": _sha(table_b)}
    out = {"proposals": table_b, "build": (json.dumps(build, indent=1, sort_keys=True) + "\n").encode(),
           "label_block": labels_b, "nodes": nodes, "K": k, "seeds": seeds}
    if stage == "test":
        out["evaluation_block"] = _lines(sorted(evals, key=key))
        out["eval_counts"] = eval_counts
    return out


# =============================================================================================== the stages
def _write_once(path: Path, raw: bytes) -> None:
    with Path(path).open("xb") as fh:
        fh.write(raw)


def _completion(stage: str, d: dict, row_td: dict, row_test: dict | None) -> dict:
    out = {"schema": COMPLETION_SCHEMA, "label": S.EVIDENCE, "source": SOURCE, "tier": "T1", "stage": stage,
           "proposals_sha256": _sha(d["proposals"]), "build_sha256": _sha(d["build"]),
           "label_block_sha256": _sha(d["label_block"]), "label_seeds": d["seeds"]["label"], "K": d["K"],
           "counts": {n: v["counts"] for n, v in d["nodes"].items()},
           "rows": {"traindev": {"row_id": row_td["row_id"], "decision_sha256": row_td["decision_sha256"]}}}
    if stage == "test":
        out.update(evaluation_block_sha256=_sha(d["evaluation_block"]), evaluation_seeds=d["seeds"]["evaluation"],
                   evaluation_counts=d["eval_counts"])
        out["rows"]["test"] = {"row_id": row_test["row_id"], "decision_sha256": row_test["decision_sha256"]}
    return out


def read_evidence(evidence_dir: Path, name: str, *, lock=None) -> bytes:
    """A G.5 evidence file read back by this module: the label block needs R1-T1-LABELS-UNSEAL, the evaluation block
    R1-T1-LABELS-TEST-RELEASE as well (other readers go through ``r1.c3.release``)."""
    check = lock or SE.release_lock
    stage = {"label_block.jsonl": "traindev", "evaluation_block.jsonl": "test"}.get(name)
    if stage is None:
        raise Stop(f"STOP: {name} is not a G.5 evidence block")
    check("traindev")
    if stage == "test":
        check("test")
    return (Path(evidence_dir) / name).read_bytes()


def assemble(spec_path: Path, stage: str, table_dir: Path, evidence_dir: Path, *, lock=None, git=G._sh,
             divergent_delta_hat: str = "refuse") -> dict:
    """Write the T1 table and label block (``traindev``), or the evaluation block (``test``), from the sealed tree."""
    spec_path = Path(spec_path)
    spec = S.load_spec(spec_path)
    spec_sha = L._sha_file(spec_path)
    check = lock or SE.release_lock
    row_td = check("traindev")                      # R1-T1-LABELS-UNSEAL: before anything sealed is opened
    row_test = check("test") if stage == "test" else None
    table_dir, evidence_dir = Path(table_dir), Path(evidence_dir)
    for d in (table_dir, evidence_dir):
        if any(part.casefold() == "r1_sealed" for part in d.resolve().parts) or \
                SE.sealed_run(spec).resolve() in [d.resolve(), *d.resolve().parents]:
            raise Stop(f"STOP: {d} is inside a sealed tree (the release step refuses sealed paths)")
    tree = SE.SealedTree(spec, lock=check)
    if stage == "traindev":
        if table_dir.exists() or evidence_dir.exists():
            raise Stop("STOP: the table and evidence directories are written once (they exist)")
        d = derive(spec, spec_sha, stage, tree, row_td, purpose_head="assembly traindev:",
                   divergent_delta_hat=divergent_delta_hat, git=git)
        table_dir.mkdir(parents=True)
        evidence_dir.mkdir(parents=True)
        _write_once(table_dir / "proposals.jsonl", d["proposals"])
        _write_once(table_dir / "build.json", d["build"])
        _write_once(evidence_dir / "label_block.jsonl", d["label_block"])
        comp = _completion(stage, d, row_td, None)
        _write_once(evidence_dir / "evidence_completion.json",
                    (json.dumps(comp, indent=1, sort_keys=True) + "\n").encode())
        return comp
    if stage != "test":
        raise Stop(f"STOP: stage must be one of {STAGES}")
    build = json.loads((table_dir / "build.json").read_text())
    if (evidence_dir / "evaluation_block.jsonl").exists():
        raise Stop("STOP: the evaluation block is written once (it exists)")
    d = derive(spec, spec_sha, stage, tree, row_td, purpose_head="assembly test:",
               divergent_delta_hat=build["readings"]["campaign_divergent_delta_hat"], git=git)
    for name, raw in (("proposals.jsonl", (table_dir / "proposals.jsonl").read_bytes()),
                      ("build.json", (table_dir / "build.json").read_bytes()),
                      ("label_block.jsonl", read_evidence(evidence_dir, "label_block.jsonl", lock=check))):
        want = d["label_block"] if name == "label_block.jsonl" else d["proposals" if name == "proposals.jsonl"
                                                                       else "build"]
        if raw != want:
            raise Stop(f"STOP: {name} is not the one the sealed tree gives now (changed since the train/dev stage)")
    _write_once(evidence_dir / "evaluation_block.jsonl", d["evaluation_block"])
    comp = _completion(stage, d, row_td, row_test)
    _write_once(evidence_dir / "evidence_completion_test.json",
                (json.dumps(comp, indent=1, sort_keys=True) + "\n").encode())
    return comp


def verify_evidence(table_dir: Path, audit_dir: Path, *, test: bool, lock=None, git=G._sh,
                    spec_path: Path | None = None) -> dict:
    """The G.5 integrity check (§6 carve-out), run by ``r1/c3/release_checks.py`` inside the release step's integrity
    context: re-derive the blocks from the sealed tree with the committed spec and compare bytes. Before the test row
    (``test`` False) only the label seeds are read, and an existing evaluation block is refused. Returns pass, counts
    and hashes, never a value."""
    spec_path = Path(spec_path or S.REPO_ROOT / SPEC_REL)
    spec = S.load_spec(spec_path)
    spec_sha = L._sha_file(spec_path)
    table_dir, audit_dir = Path(table_dir), Path(audit_dir)
    build = json.loads((table_dir / "build.json").read_text())
    if build.get("schema") != TABLE_SCHEMA or build.get("spec_sha256") != spec_sha or build.get("source") != SOURCE:
        raise Stop("STOP: the table was not built by this assembly from the committed G.5 spec")
    check = lock or SE.release_lock
    stage = "test" if test else "traindev"
    if not test and (audit_dir / "evaluation_block.jsonl").exists():
        raise Stop("STOP: an evaluation block exists before R1-T1-LABELS-TEST-RELEASE")
    row_td = check("traindev")
    row_test = check("test") if test else None
    tree = SE.SealedTree(spec, lock=check)
    d = derive(spec, spec_sha, stage, tree, row_td, purpose_head=f"release integrity {stage}:",
               divergent_delta_hat=build["readings"]["campaign_divergent_delta_hat"], git=git)
    names = [("proposals.jsonl", table_dir, "proposals"), ("build.json", table_dir, "build"),
             ("label_block.jsonl", audit_dir, "label_block")] + \
        ([("evaluation_block.jsonl", audit_dir, "evaluation_block")] if test else [])
    for name, where, key in names:
        if (where / name).read_bytes() != d[key]:
            raise Stop(f"STOP: {name} differs from the blocks the sealed tree gives")
    comp = _completion(stage, d, row_td, row_test)
    name = "evidence_completion_test.json" if test else "evidence_completion.json"
    raw = (json.dumps(comp, indent=1, sort_keys=True) + "\n").encode()
    if (audit_dir / name).read_bytes() != raw:
        raise Stop(f"STOP: {name} is not the completion record of these blocks")
    return {"check": "g5_assemble.verify_evidence", "pass": True, "stage": stage, "completion": comp,
            "completion_sha256": _sha(raw)}
