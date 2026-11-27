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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from r1.c3.d3.snapshots import (
    ENDED_ON,
    SnapshotRecorder,
    SnapshotStop,
    SNAPSHOT_SCHEMA,
    sha256_json,
    utc_now,
    wrap,
)

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

    ``observed`` carries ``model`` (GPU model identifier), ``proposer_model`` and
    ``memory_check`` (``pass``/``fail``) plus optional ``lease``.  A mismatch is a placement
    refusal (re-place), not a scientific STOP; the caller records it and does not run.
    """
    want_model = str(manifest.get("campaign_model", ""))
    got_model = str(observed.get("model", ""))
    if want_model and got_model and want_model != got_model:
        raise ChunkStop(f"GPU model mismatch: manifest {want_model!r}, observed {got_model!r}")
    want_prop = str(manifest.get("proposer_model", ""))
    got_prop = str(observed.get("proposer_model", ""))
    if want_prop and got_prop and want_prop != got_prop:
        raise ChunkStop(f"proposer model mismatch: manifest {want_prop!r}, observed {got_prop!r}")
    if observed.get("memory_check") == "fail":
        raise ChunkStop("insufficient free GPU memory for the declared footprint")
    lease = observed.get("lease")
    if lease is False:
        raise ChunkStop("the declared lease is not held")


CampaignFactory = Callable[[ChunkSpec, int, Path, SnapshotRecorder], tuple[dict[str, Any], str]]
"""``(spec, seed, campaign_dir, recorder) -> (run_real_campaign kwargs, ended_on)``.

The factory must pass ``wrap(kwargs, recorder)`` to ``run_real_campaign``; it returns the
``ended_on`` value (one of :data:`ENDED_ON`).  It must not write ``snapshots/final.json``.
"""


def _validate_kwargs(kwargs: Mapping[str, Any]) -> None:
    need = ("node_spec", "campaign_id", "budget", "manager_mode", "memory_mode", "records_path",
            "worker", "controller", "snapshot_hook", "compute_budget")
    missing = [key for key in need if key not in kwargs]
    if missing:
        raise ChunkStop(f"campaign factory did not return run_real_campaign kwargs; missing {missing}")


def run_chunk(spec: ChunkSpec, out_dir: Path, factory: CampaignFactory, *,
              manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run one chunk and write its records.  The output directory must be absent."""
    out = Path(out_dir)
    if out.exists():
        raise ChunkStop(f"refusing an existing chunk directory {out}")
    if manifest is None:
        raise ChunkStop("a chunk needs the locked campaign manifest (campaign_manifest.json)")
    if str(manifest.get("campaign_model_source_sha256", "")) and \
            str(manifest["campaign_model_source_sha256"]) != sha256_json(dict(spec.campaign_model_source)):
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
        if kwargs.get("snapshot_hook") is not recorder:
            raise ChunkStop("the factory did not bind the chunk recorder as the snapshot hook")
        if ended_on not in ENDED_ON:
            raise ChunkStop(f"unknown ended_on {ended_on!r}")
        run_real_campaign(**kwargs)
        w_final = recorder.count
        if recorder._last_budget is not None and recorder._last_budget.worker_runs != w_final:
            raise ChunkStop("charged-run parity failed at the end of a campaign")
        final_sha = recorder.write_final(w_final=w_final, ended_on=ended_on)
        record = {
            "schema": CAMPAIGN_SCHEMA,
            "stage": spec.stage, "arm": spec.arm, "node": spec.node,
            "repetition": spec.repetition, "instance_id": inst, "instance_seed": seed,
            "worker_runs": w_final, "llm_calls": getattr(recorder._last_budget, "llm_calls", None),
            "ended_on": ended_on, "snapshots": recorder.snapshot_hashes(),
            "final_sha256": final_sha, "snapshot_schema": SNAPSHOT_SCHEMA,
        }
        _write_json(cdir / "campaign.json", record)
        sha256sums(cdir)
        campaigns.append(record)

    chunk = {
        "schema": CHUNK_SCHEMA, "created_utc": utc_now(),
        "stage": spec.stage, "arm": spec.arm, "node": spec.node,
        "repetition": spec.repetition, "launcher": spec.launcher, "host": spec.host,
        "W": spec.W, "llm_cap": spec.llm_cap,
        "campaign_manifest_sha256": sha256_json(dict(manifest)),
        "campaign_model_source": dict(spec.campaign_model_source),
        "hardware": dict(spec.hardware), "notes": dict(spec.notes),
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
