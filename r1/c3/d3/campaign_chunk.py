"""One D.3 G1 campaign chunk — layout, records and SHA256SUMS (ENGINEERING code).

The chunk script is launcher-neutral (design revision 6b §2): it takes a launch record and
an absent output directory, runs the declared instances through the G1 snapshot wrapper and
writes the per-campaign ledger/snapshots plus the chunk record.  It knows nothing about
HTCondor or SSH; a launcher supplies the factory that builds one instance's node spec,
worker, manager backend and controller.

This unit implements the record/layout half and the snapshot wiring.  The D.3 adapter
(real node specs, the gemma4_31b manager, the seven arms and their pinned constants) is a
separate reviewed unit; ``run_chunk`` refuses a factory that does not return the declared
shape.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from r1.c3.d3.snapshots import (
    ENDED_ON,
    SnapshotRecorder,
    SnapshotStop,
    SNAPSHOT_SCHEMA,
    read_worker_config,
    sha256_json,
    utc_now,
    wrap,
)
from r1.c3.d3.summary import COMPLETE_ENDED_ON, build_campaign_summary, keep_records

CHUNK_SCHEMA = "r1_d3_chunk/v1"
CAMPAIGN_SCHEMA = "r1_d3_campaign/v1"
SUMMARY_SCHEMA = "r1_d3_chunk_summary/v1"
REQUIRED_LAUNCH = ("schema", "stage", "arm", "node", "repetition", "instance_seeds", "W", "llm_cap",
                   "launcher", "host", "campaign_model_source")


class ChunkStop(RuntimeError):
    """A pre-declared STOP or a refusal before any campaign starts."""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    text = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False, default=str) + "\n"
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256sums(root: Path, *, sums_name: str = "SHA256SUMS") -> dict[str, str]:
    """Write ``SHA256SUMS`` over every regular file under ``root`` except the sums files.

    Paths are relative, sorted, never absolute and never contain ``..``.
    """
    root = Path(root)
    entries: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in (sums_name, sums_name + ".tmp"):
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith("/") or ".." in Path(rel).parts:
            raise ChunkStop(f"bad relative path in chunk tree: {rel}")
        entries[rel] = _sha256_file(path)
    text = "".join(f"{digest}  {rel}\n" for rel, digest in sorted(entries.items()))
    (root / sums_name).write_text(text, encoding="utf-8")
    return entries


@dataclass(frozen=True)
class ChunkSpec:
    stage: str
    arm: str
    node: str
    repetition: int
    instance_seeds: tuple[int, ...]
    W: int
    llm_cap: int
    launcher: str
    host: str
    campaign_model_source: Mapping[str, Any]
    hardware: Mapping[str, Any] = field(default_factory=dict)
    notes: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_launch(cls, launch: Mapping[str, Any]) -> "ChunkSpec":
        missing = [key for key in REQUIRED_LAUNCH if key not in launch]
        if missing:
            raise ChunkStop(f"launch record misses {missing}")
        if launch["schema"] != "r1_d3_launch/v1":
            raise ChunkStop(f"unknown launch schema {launch['schema']!r}")
        if launch["launcher"] not in ("htcondor", "ssh", "direct"):
            raise ChunkStop(f"unknown launcher {launch['launcher']!r}")
        seeds = tuple(int(s) for s in launch["instance_seeds"])
        if list(seeds) != sorted(set(seeds)) or len(seeds) != 18:
            raise ChunkStop("a D.3 deployment chunk declares 18 distinct instance seeds")
        if any(not (6201 <= s <= 6218) for s in seeds):
            raise ChunkStop("deployment instance seeds are 6201-6218")
        W, cap = int(launch["W"]), int(launch["llm_cap"])
        if W != 20 or cap != 80:
            raise ChunkStop("D.3a/b W=20 and the LLM-call cap=80 are the signed values")
        source = launch["campaign_model_source"]
        if not isinstance(source, Mapping) or not source.get("sha256"):
            raise ChunkStop("campaign_model_source must carry its sha256")
        return cls(
            stage=str(launch["stage"]), arm=str(launch["arm"]), node=str(launch["node"]),
            repetition=int(launch["repetition"]), instance_seeds=seeds, W=W, llm_cap=cap,
            launcher=str(launch["launcher"]), host=str(launch["host"]),
            campaign_model_source=dict(source),
            hardware=dict(launch.get("hardware") or {}),
            notes=dict(launch.get("notes") or {}),
        )

    def instance_id(self, seed: int) -> str:
        return f"{self.node}__s{int(seed)}"


def check_hardware(spec: ChunkSpec, observed: Mapping[str, Any], manifest: Mapping[str, Any]) -> None:
    """The revision-6b placement refusals: model, proposer, lease and memory.

    Fail closed: the manifest must carry ``campaign_model`` and ``proposer_model``; the
    observed record must carry the same values, ``memory_check == "pass"`` and
    ``lease is True``.  A missing field is a placement refusal (re-place), not a pass.  If the
    manifest also carries ``instance_model``, it must agree with ``campaign_model``.
    """
    want_model = str(manifest.get("campaign_model") or "")
    want_prop = str(manifest.get("proposer_model") or "")
    if not want_model or not want_prop:
        raise ChunkStop("the campaign manifest must name campaign_model and proposer_model")
    instance_model = str(manifest.get("instance_model") or want_model)
    if instance_model != want_model:
        raise ChunkStop(f"instance_model {instance_model!r} differs from campaign_model {want_model!r}")
    got_model = str(observed.get("model") or "")
    if not got_model:
        raise ChunkStop("the observed hardware record has no GPU model")
    if want_model != got_model:
        raise ChunkStop(f"GPU model mismatch: manifest {want_model!r}, observed {got_model!r}")
    got_prop = str(observed.get("proposer_model") or "")
    if not got_prop:
        raise ChunkStop("the observed hardware record has no proposer model")
    if want_prop != got_prop:
        raise ChunkStop(f"proposer model mismatch: manifest {want_prop!r}, observed {got_prop!r}")
    if observed.get("memory_check") != "pass":
        raise ChunkStop("the observed memory check must be 'pass' (missing is a refusal)")
    if observed.get("lease") is not True:
        raise ChunkStop("the declared lease is not held (observed lease must be true)")


CampaignFactory = Callable[[ChunkSpec, int, Path, SnapshotRecorder],
                           tuple[dict[str, Any], "str | Callable[[SnapshotRecorder], str]"]]
"""``(spec, seed, campaign_dir, recorder) -> (run_real_campaign kwargs, ended_on)``.

The factory must pass ``wrap(kwargs, recorder)`` to ``run_real_campaign``; it returns the
``ended_on`` value (one of :data:`ENDED_ON`) or a resolver called with the recorder after the
campaign, when the end is only known from the final budget (the real adapter uses
``accounting.table_ended_on``).  It must not write ``snapshots/final.json``.
"""


def _validate_kwargs(kwargs: Mapping[str, Any]) -> None:
    need = ("node_spec", "campaign_id", "budget", "manager_mode", "memory_mode", "records_path",
            "worker", "controller", "snapshot_hook", "compute_budget")
    missing = [key for key in need if key not in kwargs]
    if missing:
        raise ChunkStop(f"campaign factory did not return run_real_campaign kwargs; missing {missing}")


def run_chunk(spec: ChunkSpec, out_dir: Path, factory: CampaignFactory | None = None, *,
              manifest: Mapping[str, Any] | None = None,
              observed: Mapping[str, Any] | None = None,
              replicate_factory: "ReplicateFactory | None" = None) -> dict[str, Any]:
    """Run one chunk and write its records.  The output directory must be absent.

    ``replicate_factory`` selects the FIXR3/EGATE branch (design revision 6c); the
    harness-arm branch keeps its original ``factory`` contract unchanged.
    """
    out = Path(out_dir)
    if out.exists():
        raise ChunkStop(f"refusing an existing chunk directory {out}")
    if replicate_factory is not None:
        if factory is not None:
            raise ChunkStop("pass either factory or replicate_factory, not both")
        if manifest is None:
            raise ChunkStop("a chunk needs the locked campaign manifest (campaign_manifest.json)")
        if observed is None:
            raise ChunkStop("a chunk needs the observed hardware record (revision 6b)")
        return _run_replicate_chunk(spec, out, replicate_factory, manifest=manifest, observed=observed)
    if factory is None:
        raise ChunkStop("the harness-arm chunk needs a campaign factory")
    if spec.arm in ("FIXR3", "EGATE"):
        raise ChunkStop(f"{spec.arm} runs through the replicate branch, not the harness factory")
    if manifest is None:
        raise ChunkStop("a chunk needs the locked campaign manifest (campaign_manifest.json)")
    if observed is None:
        raise ChunkStop("a chunk needs the observed hardware record (revision 6b)")
    check_hardware(spec, observed, manifest)
    if "campaign_model_source_sha256" not in manifest:
        raise ChunkStop("the campaign manifest must carry campaign_model_source_sha256")
    if str(manifest["campaign_model_source_sha256"]) != sha256_json(dict(spec.campaign_model_source)):
        raise ChunkStop("the campaign manifest's model source does not match this launch")
    out.mkdir(parents=True)
    campaigns: list[dict[str, Any]] = []
    from autoresearch.control_plane.campaign import run_real_campaign  # local import: no run on import

    for seed in spec.instance_seeds:
        inst = spec.instance_id(seed)
        cdir = out / "campaigns" / inst
        recorder = SnapshotRecorder(out_dir=cdir, stage=spec.stage, arm=spec.arm, node=spec.node,
                                    repetition=spec.repetition, instance_id=inst)
        kwargs, ended_on = factory(spec, seed, cdir, recorder)
        _validate_kwargs(kwargs)
        if str(kwargs.get("campaign_id")) != inst:
            raise ChunkStop("the factory campaign_id is not the instance id")
        if kwargs.get("snapshot_hook") is not recorder:
            raise ChunkStop("the factory did not bind the chunk recorder as the snapshot hook")
        if callable(ended_on):
            resolver = ended_on
        elif ended_on in ENDED_ON:
            resolver = None
        else:
            raise ChunkStop(f"unknown ended_on {ended_on!r}")
        started = time.monotonic()
        run_real_campaign(**kwargs)
        wall_seconds = time.monotonic() - started
        if resolver is not None:
            ended_on = resolver(recorder)
        if ended_on not in ENDED_ON:
            raise ChunkStop(f"unknown ended_on {ended_on!r}")
        w_final = recorder.count
        if recorder._last_budget is not None and recorder._last_budget.worker_runs != w_final:
            raise ChunkStop("charged-run parity failed at the end of a campaign")
        # The harness route's final is the live incumbent after the last E2 decision, not the
        # recorder's cached E1 state (revision 4 step (5) finding 1).  At W the recorder keeps
        # the pre-decision w<W> record as w<W>_pre.json and canonicalises w<W>.json from final.
        final_sha = recorder.write_final_live(
            w_final=w_final, ended_on=ended_on, worker=kwargs["worker"],
            node_spec=kwargs["node_spec"], ledger_path=kwargs["records_path"],
        )
        llm_calls = int(getattr(recorder._last_budget, "llm_calls", 0) or 0)
        record = {
            "schema": CAMPAIGN_SCHEMA,
            "campaign_kind": "harness",
            "stage": spec.stage, "arm": spec.arm, "node": spec.node,
            "repetition": spec.repetition, "instance_id": inst, "instance_seed": seed,
            "worker_runs": w_final, "llm_calls": llm_calls,
            "ended_on": ended_on, "snapshots": recorder.snapshot_hashes(),
            "pre_decision_snapshots": recorder.pre_decision_hashes(),
            "final_sha256": final_sha, "snapshot_schema": SNAPSHOT_SCHEMA,
        }
        record["record_name"] = f"{spec.stage}__{spec.arm}__{inst}__r{spec.repetition}"
        record["campaign_id"] = inst
        records_path = Path(kwargs["records_path"])
        ledger = records_path.read_text(encoding="utf-8") if records_path.is_file() else ""
        (cdir / "ledger.jsonl").write_text(ledger, encoding="utf-8")
        run_rows = []
        for line in ledger.splitlines():
            if not line.strip():
                continue
            try:
                run_rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ChunkStop(f"the ledger line is not JSON: {exc}") from exc
        (cdir / "runs.jsonl").write_text(
            "".join(json.dumps({"instance_id": inst, "record": row}, sort_keys=True) + "\n"
                    for row in run_rows), encoding="utf-8")
        events_path = cdir / "events.jsonl"
        events = []
        if events_path.is_file():
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()
                      if line.strip()]
        config_by_trial = recorder.config_by_trial()
        for keep in keep_records(run_rows, config_by_trial=config_by_trial):
            target = cdir / "keeps" / f"keep-{int(keep['keep_run'])}.json"
            _write_json(target, keep)
        final_config = read_worker_config(kwargs["worker"], kwargs["node_spec"])
        campaign_summary = build_campaign_summary(
            stage=spec.stage, arm=spec.arm, node=spec.node, instance_seed=seed,
            repetition=spec.repetition, gpu_model=str(observed.get("model") or ""),
            status="complete" if ended_on in COMPLETE_ENDED_ON else "stopped",
            records=run_rows, events=events, config_by_trial=config_by_trial,
            start_config=recorder.start_config or {}, final_config=final_config,
            worker_runs=w_final, llm_calls=llm_calls, ended_on=ended_on,
            wall_seconds=wall_seconds,
        )
        _write_json(cdir / "summary.json", campaign_summary)
        _write_json(cdir / "campaign.json", record)
        sha256sums(cdir)
        campaigns.append(record)

    chunk = {
        "schema": CHUNK_SCHEMA, "created_utc": utc_now(),
        "stage": spec.stage, "arm": spec.arm, "node": spec.node,
        "repetition": spec.repetition, "launcher": spec.launcher, "host": spec.host,
        "campaign_kind": "harness", "W": spec.W, "llm_cap": spec.llm_cap,
        "campaign_manifest_sha256": sha256_json(dict(manifest)),
        "campaign_model_source": dict(spec.campaign_model_source),
        "hardware": dict(observed),
        "hardware_claim": dict(spec.hardware),
        "campaign_model": manifest.get("campaign_model"),
        "host_class": observed.get("host_class"), "lease_path": observed.get("lease_path"),
        "chunk_start_utc": observed.get("chunk_start_utc"), "chunk_end_utc": utc_now(),
        "gpu_model": observed.get("model"), "gpu_uuid": observed.get("gpu_uuid"),
        "driver": observed.get("driver"), "driver_version": observed.get("driver"),
        "memory_total": observed.get("memory_total"), "memory_total_mib": observed.get("memory_total"),
        "memory_free": observed.get("memory_free"), "memory_free_mib_at_start": observed.get("memory_free"),
        "memory_check": observed.get("memory_check"),
        "other_processes_start": observed.get("other_processes_start"),
        "other_processes_end": observed.get("other_processes_end"),
        "proposer_expected": manifest.get("proposer_model"),
        "proposer_observed": observed.get("proposer_model"),
        "proposer_check": "pass",
        "request": observed.get("request"), "scope": observed.get("scope"),
        "environment_freeze": observed.get("environment_freeze"),
        "model_check": "pass",
        "status": "stopped" if any(c["ended_on"] in ("stop", "error") for c in campaigns) else "complete",
        "notes": dict(spec.notes),
        "instances": [spec.instance_id(s) for s in spec.instance_seeds],
    }
    _write_json(out / "chunk.json", chunk)
    summary = {
        "schema": SUMMARY_SCHEMA, "stage": spec.stage, "arm": spec.arm, "node": spec.node,
        "repetition": spec.repetition, "campaigns": len(campaigns),
        "worker_runs": sum(c["worker_runs"] for c in campaigns),
        "llm_calls": sum(int(c["llm_calls"] or 0) for c in campaigns),
        "ended_on": {k: sum(1 for c in campaigns if c["ended_on"] == k)
                     for k in sorted({c["ended_on"] for c in campaigns})},
        "campaigns_detail": campaigns,
    }
    _write_json(out / "summary.json", summary)
    sha256sums(out)
    return summary


# ---------------------------------------------------------------------------
# Replicate-arm branch (design revision 6c): FIXR3 and EGATE
# ---------------------------------------------------------------------------

ReplicateFactory = Callable[[ChunkSpec, int, Path, SnapshotRecorder], Any]
"""``(spec, seed, campaign_dir, recorder) -> ReplicateUnit`` (the adapter's engine/manager/worker)."""


def _run_replicate_chunk(spec: ChunkSpec, out: Path, factory: ReplicateFactory, *,
                         manifest: Mapping[str, Any], observed: Mapping[str, Any]) -> dict[str, Any]:
    from r1.c3.d3.replicate_campaign import run_replicate_campaign

    if spec.arm not in ("FIXR3", "EGATE"):
        raise ChunkStop(f"the replicate branch needs FIXR3 or EGATE, not {spec.arm!r}")
    check_hardware(spec, observed, manifest)
    if "campaign_model_source_sha256" not in manifest:
        raise ChunkStop("the campaign manifest must carry campaign_model_source_sha256")
    if str(manifest["campaign_model_source_sha256"]) != sha256_json(dict(spec.campaign_model_source)):
        raise ChunkStop("the campaign manifest's model source does not match this launch")
    out.mkdir(parents=True)
    campaigns: list[dict[str, Any]] = []
    for seed in spec.instance_seeds:
        inst = spec.instance_id(seed)
        cdir = out / "campaigns" / inst
        recorder = SnapshotRecorder(out_dir=cdir, stage=spec.stage, arm=spec.arm, node=spec.node,
                                    repetition=spec.repetition, instance_id=inst)
        unit = factory(spec, seed, cdir, recorder)
        if str(getattr(unit.engine, "arm", "")) != spec.arm:
            raise ChunkStop(f"the replicate engine is {getattr(unit.engine, 'arm', None)!r}, not {spec.arm!r}")
        started = time.monotonic()
        summary = run_replicate_campaign(
            instance_id=inst, repetition=spec.repetition, unit=unit, recorder=recorder,
            stage=spec.stage, node=spec.node, W=spec.W, llm_cap=spec.llm_cap,
        )
        wall_seconds = time.monotonic() - started
        record = {
            "schema": CAMPAIGN_SCHEMA,
            "campaign_kind": "replicate",
            "stage": spec.stage, "arm": spec.arm, "node": spec.node,
            "repetition": spec.repetition, "instance_id": inst, "instance_seed": seed,
            "worker_runs": summary["worker_runs"], "llm_calls": summary["llm_calls"],
            "ended_on": summary["ended_on"], "snapshots": summary["snapshots"],
            "pre_decision_snapshots": recorder.pre_decision_hashes(),
            "final_sha256": summary["final_sha256"], "snapshot_schema": SNAPSHOT_SCHEMA,
            "zero_variance_cases": sum(int(s.get("zero_variance_cases") or 0) for s in summary["steps"]),
        }
        record["record_name"] = f"{spec.stage}__{spec.arm}__{inst}__r{spec.repetition}"
        record["campaign_id"] = inst
        (cdir / "ledger.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in summary["trials"]), encoding="utf-8")
        (cdir / "events.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in summary["events"]), encoding="utf-8")
        (cdir / "runs.jsonl").write_text(
            "".join(json.dumps({"instance_id": inst, "record": a}, sort_keys=True) + "\n"
                    for a in summary["attempts"]), encoding="utf-8")
        config_by_trial = recorder.config_by_trial()
        for keep in keep_records(summary["trials"], config_by_trial=config_by_trial):
            _write_json(cdir / "keeps" / f"keep-{int(keep['keep_run'])}.json", keep)
        campaign_summary = build_campaign_summary(
            stage=spec.stage, arm=spec.arm, node=spec.node, instance_seed=seed,
            repetition=spec.repetition, gpu_model=str(observed.get("model") or ""),
            status="complete" if summary["ended_on"] in COMPLETE_ENDED_ON else "stopped",
            records=summary["trials"], events=summary["events"],
            config_by_trial=config_by_trial,
            start_config=summary["start_config"], final_config=summary["final_config"],
            worker_runs=int(summary["worker_runs"]), llm_calls=int(summary["llm_calls"]),
            ended_on=summary["ended_on"], wall_seconds=wall_seconds,
            attempts=summary["attempts"],
        )
        _write_json(cdir / "summary.json", campaign_summary)
        _write_json(cdir / "campaign.json", record)
        sha256sums(cdir)
        campaigns.append(record)

    chunk = {
        "schema": CHUNK_SCHEMA, "created_utc": utc_now(),
        "stage": spec.stage, "arm": spec.arm, "node": spec.node,
        "repetition": spec.repetition, "launcher": spec.launcher, "host": spec.host,
        "campaign_kind": "replicate", "W": spec.W, "llm_cap": spec.llm_cap,
        "campaign_manifest_sha256": sha256_json(dict(manifest)),
        "campaign_model_source": dict(spec.campaign_model_source),
        "hardware": dict(observed), "hardware_claim": dict(spec.hardware),
        "campaign_model": manifest.get("campaign_model"),
        "host_class": observed.get("host_class"), "lease_path": observed.get("lease_path"),
        "chunk_start_utc": observed.get("chunk_start_utc"), "chunk_end_utc": utc_now(),
        "gpu_model": observed.get("model"), "gpu_uuid": observed.get("gpu_uuid"),
        "driver": observed.get("driver"), "driver_version": observed.get("driver"),
        "memory_total": observed.get("memory_total"), "memory_total_mib": observed.get("memory_total"),
        "memory_free": observed.get("memory_free"), "memory_free_mib_at_start": observed.get("memory_free"),
        "memory_check": observed.get("memory_check"),
        "other_processes_start": observed.get("other_processes_start"),
        "other_processes_end": observed.get("other_processes_end"),
        "proposer_expected": manifest.get("proposer_model"),
        "proposer_observed": observed.get("proposer_model"), "proposer_check": "pass",
        "request": observed.get("request"), "scope": observed.get("scope"),
        "environment_freeze": observed.get("environment_freeze"),
        "model_check": "pass",
        "status": "stopped" if any(c["ended_on"] in ("stop", "error") for c in campaigns) else "complete",
        "notes": dict(spec.notes),
        "instances": [spec.instance_id(s) for s in spec.instance_seeds],
    }
    _write_json(out / "chunk.json", chunk)
    summary = {
        "schema": SUMMARY_SCHEMA, "stage": spec.stage, "arm": spec.arm, "node": spec.node,
        "repetition": spec.repetition, "campaigns": len(campaigns),
        "campaign_kind": "replicate",
        "worker_runs": sum(c["worker_runs"] for c in campaigns),
        "llm_calls": sum(int(c["llm_calls"] or 0) for c in campaigns),
        "ended_on": {k: sum(1 for c in campaigns if c["ended_on"] == k)
                     for k in sorted({c["ended_on"] for c in campaigns})},
        "campaigns_detail": campaigns,
    }
    _write_json(out / "summary.json", summary)
    sha256sums(out)
    return summary
