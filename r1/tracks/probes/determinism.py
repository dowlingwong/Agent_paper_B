#!/usr/bin/env python3
"""S0.1 probe: LLM determinism, latency and CPU census on one host (runbook rev. 3 §2 S0.1).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. Runs on the host (TASL-2, TASL-7) against the
host's own llama-server(s); it never starts or stops a server.

N fixed manager prompts (the harness LangGraph prompt for the node at trial indices 2..N+1, empty
memory; or ``--prompts FILE`` with one {"prompt", "seed"} JSON object per line) are sent with their
fixed D26 seeds (``manager_seed("tracks_s01", i, 0)``) to each URL, ``--repeats`` times each:

* ``--mode serial``      (a) one server: every call serial;
* ``--mode concurrent``  (b) several servers (one thread per URL, each serial), all at once.

Reported per URL: within-server identity rate (share of prompts whose every repeat returned the
same content), mean and p95 latency; across URLs: cross-server identity (recorded, not required);
and a CPU census (cores, load, cores free). The pass criterion of S0.1 (100 % within-host identity in
the setting S3 will use) is applied by the author, not here.

  python -m r1.tracks.probes.determinism --url http://127.0.0.1:18083/v1 --model r1-manager \\
      --n 200 --repeats 2 --mode serial --out s01_tasl2_serial.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import threading
import time
import urllib.request
from pathlib import Path

PROBE_SCHEMA = "tracks_s01_probe/v1"
SEED_KEY = "tracks_s01"


def chat_payload(prompt: str, seed: int, model: str, *, temperature: float = 0.2, max_tokens: int = 512) -> dict:
    """The OpenAI-compatible request the harness llamacpp provider sends (one user message, D26 seed)."""
    return {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": float(temperature),
            "seed": int(seed), "max_tokens": int(max_tokens), "stream": False}


def post(url: str, payload: dict, timeout: float = 300.0) -> tuple[str, float]:
    """POST ``payload`` to ``<url>/chat/completions``; returns (content, latency seconds)."""
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - operator-given local URL
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"], time.perf_counter() - t0


def identity_rate(contents: dict) -> float | None:
    """``contents``: prompt index -> list of repeat contents; share of prompts with all repeats identical."""
    groups = [v for v in contents.values() if len(v) >= 2]
    return (sum(len(set(v)) == 1 for v in groups) / len(groups)) if groups else None


def cross_identity(per_url: dict) -> float | None:
    """Share of prompts whose first content is identical across all URLs."""
    urls = list(per_url)
    if len(urls) < 2:
        return None
    common = set.intersection(*(set(per_url[u]) for u in urls))
    if not common:
        return None
    return sum(len({per_url[u][i][0] for u in urls}) == 1 for i in common) / len(common)


def latency_stats(latencies: list[float]) -> dict:
    """Mean and p95 (nearest-rank) in seconds."""
    if not latencies:
        return {"n": 0, "mean_s": None, "p95_s": None}
    xs = sorted(latencies)
    rank = max(1, math.ceil(0.95 * len(xs)))
    return {"n": len(xs), "mean_s": sum(xs) / len(xs), "p95_s": xs[rank - 1]}


def cpu_census() -> dict:
    cpus = os.cpu_count() or 0
    try:
        load = os.getloadavg()
    except OSError:
        load = (math.nan, math.nan, math.nan)
    return {"cpus": cpus, "loadavg_1_5_15": list(load), "cores_free_est": max(cpus - load[0], 0.0) if cpus else None}


def fixed_prompts(n: int, node: str = "digits_mlp") -> list[dict]:
    """N harness manager prompts (empty memory) with their D26 seeds."""
    from r1.harness import import_harness
    harness = import_harness()
    from autoresearch.control_plane.campaign import _manager_status
    from autoresearch.manager.langgraph_manager import _prepare_context, manager_seed
    from autoresearch.memory.summarizer import MemoryMode, build_memory_context
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import LocalWorker
    spec = load_registered_node(node, repo_root=harness)
    worker = LocalWorker(node_root=harness / "nodes" / node)
    out = []
    for i in range(2, n + 2):
        status = _manager_status(campaign_id=SEED_KEY, budget_index=i, current_best=0.9, node_spec=spec, worker=worker)
        ctx = build_memory_context([], MemoryMode.APPEND_ONLY_SUMMARY, spec, i)
        state = _prepare_context({"status": status, "memory_context": ctx, "node_spec": spec})
        out.append({"prompt": state["context_text"], "seed": manager_seed(SEED_KEY, i, 0)})
    return out


def run_url(url: str, model: str, prompts: list[dict], repeats: int, max_tokens: int, timeout: float) -> dict:
    contents: dict[int, list[str]] = {}
    lat: list[float] = []
    errors = 0
    for r in range(repeats):
        for i, p in enumerate(prompts):
            try:
                text, dt = post(url, chat_payload(p["prompt"], p["seed"], model, max_tokens=max_tokens), timeout)
            except Exception:  # noqa: BLE001 - a failed call is counted, never retried silently
                errors += 1
                continue
            contents.setdefault(i, []).append(text)
            lat.append(dt)
    return {"contents": contents, "latency": latency_stats(lat), "errors": errors,
            "identity_rate": identity_rate(contents)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", action="append", required=True, help="llama-server OpenAI base URL (.../v1); repeatable")
    ap.add_argument("--model", default="r1-manager")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--mode", choices=["serial", "concurrent"], default="serial")
    ap.add_argument("--node", default="digits_mlp")
    ap.add_argument("--prompts", default=None, help="JSONL of {prompt, seed} (default: harness prompts)")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--host-label", default="unknown")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.mode == "serial" and len(args.url) != 1:
        ap.error("--mode serial takes exactly one --url")
    prompts = ([json.loads(l) for l in Path(args.prompts).read_text().splitlines() if l.strip()]
               if args.prompts else fixed_prompts(args.n, args.node))[: args.n]
    census_before = cpu_census()
    results: dict[str, dict] = {}
    if args.mode == "serial":
        results[args.url[0]] = run_url(args.url[0], args.model, prompts, args.repeats, args.max_tokens, args.timeout)
    else:
        threads = [threading.Thread(target=lambda u=u: results.__setitem__(
            u, run_url(u, args.model, prompts, args.repeats, args.max_tokens, args.timeout))) for u in args.url]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    report = {"schema": PROBE_SCHEMA, "label": "ENGINEERING_ONLY", "host": args.host_label, "mode": args.mode,
              "n_prompts": len(prompts), "repeats": args.repeats, "model": args.model,
              "per_url": {u: {k: v for k, v in r.items() if k != "contents"} for u, r in results.items()},
              "cross_server_identity": cross_identity({u: r["contents"] for u, r in results.items()}),
              "cpu_before": census_before, "cpu_after": cpu_census()}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["per_url"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
