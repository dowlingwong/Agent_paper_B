#!/usr/bin/env python3
"""S0.1 probe: LLM determinism, latency and CPU census on one host (runbook rev. 3 §2 S0.1).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. Runs on the host (TASL-2, TASL-7) against the
host's own llama-server(s); it never starts or stops a server.

N fixed manager prompts (the harness LangGraph prompt for the node at trial indices 2..N+1; every
other prompt carries a deterministic non-empty memory block (``memory_text``), so both prompt shapes are
probed; or ``--prompts FILE`` with one {"prompt", "seed"} JSON object per line) are sent with their
fixed D26 seeds (``manager_seed("tracks_s01", i, 0)``) to each URL, ``--repeats`` times each:

* ``--mode serial``      (a) one server: every call serial;
* ``--mode concurrent``  (b) several servers (one thread per URL, each serial), all at once.

Reported per URL: within-server identity rate (share of prompts whose every repeat returned the same
content; a prompt with an errored repeat counts as NOT identical, review m7), mean and p95 latency; across URLs: cross-server identity (recorded, not required);
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


def chat_payload(prompt: str, seed: int, model: str, *, temperature: float = 0.2, max_tokens: int = 512,
                 proposal_schema: str | None = None) -> dict:
    """The OpenAI-compatible request the harness llamacpp provider sends (one user message, D26 seed); with
    ``proposal_schema`` (sweep 1: ``manager_proposal/v1``) the same ``response_format`` json_schema grammar."""
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": float(temperature),
               "seed": int(seed), "max_tokens": int(max_tokens), "stream": False}
    if proposal_schema:
        from r1.harness import import_harness
        import_harness()
        from autoresearch.llm.providers import manager_response_format
        payload["response_format"] = manager_response_format(proposal_schema)
    return payload


def post(url: str, payload: dict, timeout: float = 300.0) -> tuple[str, float]:
    """POST ``payload`` to ``<url>/chat/completions``; returns (content, latency seconds)."""
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - operator-given local URL
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"], time.perf_counter() - t0


def identity_rate(contents: dict, repeats: int | None = None) -> float | None:
    """``contents``: prompt index -> list of repeat contents (``None`` = an errored call); share of prompts whose
    ``repeats`` repeats all returned and are identical. A prompt with an errored or missing repeat is not
    identical (review m7)."""
    if not contents:
        return None
    need = repeats if repeats is not None else max(len(v) for v in contents.values())
    if need < 2:
        return None
    ok = [len(v) == need and None not in v and len(set(v)) == 1 for v in contents.values()]
    return sum(ok) / len(ok)


def cross_identity(per_url: dict) -> float | None:
    """Share of prompts whose first content is identical across all URLs."""
    urls = list(per_url)
    if len(urls) < 2:
        return None
    common = set.intersection(*(set(per_url[u]) for u in urls))
    if not common:
        return None
    def first(u, i):
        v = per_url[u][i]
        return v[0] if v else None
    return sum(None not in (firsts := [first(u, i) for u in urls]) and len(set(firsts)) == 1
               for i in common) / len(common)


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


def memory_text(i: int) -> str:
    """A deterministic memory block in the deployed display's format (summary lines; one_line/v1 skips)."""
    lines = []
    for t in range(1, 1 + (i % 6) + 1):
        if t % 3 == 0:
            lines.append(f"tracks_s01-trial-{t:03d}: summary=edit {t}; skipped by the control plane: predicted no gain")
        else:
            lines.append(f"tracks_s01-trial-{t:03d}: decision={'kept' if t % 2 else 'discarded'}; summary=edit {t}; "
                         f"metric={0.9 + 0.001 * t:.6f}; delta={0.001 * (t % 3 - 1)}")
    return "\n".join(lines)


def fixed_prompts(n: int, node: str = "digits_mlp") -> list[dict]:
    """N harness manager prompts with their D26 seeds; odd indices carry a memory block (``memory_text``)."""
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
        if i % 2:
            from types import SimpleNamespace
            ctx = SimpleNamespace(context_text=memory_text(i))
        state = _prepare_context({"status": status, "memory_context": ctx, "node_spec": spec})
        out.append({"prompt": state["context_text"], "seed": manager_seed(SEED_KEY, i, 0)})
    return out


def run_url(url: str, model: str, prompts: list[dict], repeats: int, max_tokens: int, timeout: float,
            proposal_schema: str | None = None) -> dict:
    contents: dict[int, list] = {i: [] for i in range(len(prompts))}
    lat: list[float] = []
    errors = 0
    for r in range(repeats):
        for i, p in enumerate(prompts):
            try:
                text, dt = post(url, chat_payload(p["prompt"], p["seed"], model, max_tokens=max_tokens,
                                                  proposal_schema=proposal_schema), timeout)
            except Exception:  # noqa: BLE001 - a failed call is counted (and is not identical), never retried
                errors += 1
                contents[i].append(None)
                continue
            contents[i].append(text)
            lat.append(dt)
    return {"contents": contents, "latency": latency_stats(lat), "errors": errors,
            "identity_rate": identity_rate(contents, repeats)}


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
    ap.add_argument("--proposal-schema", default=None, help="send sweep 1's response_format (manager_proposal/v1)")
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
        results[args.url[0]] = run_url(args.url[0], args.model, prompts, args.repeats, args.max_tokens, args.timeout,
                                       args.proposal_schema)
    else:
        threads = [threading.Thread(target=lambda u=u: results.__setitem__(
            u, run_url(u, args.model, prompts, args.repeats, args.max_tokens, args.timeout,
                       args.proposal_schema))) for u in args.url]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    report = {"schema": PROBE_SCHEMA, "label": "ENGINEERING_ONLY", "host": args.host_label, "mode": args.mode,
              "n_prompts": len(prompts), "repeats": args.repeats, "model": args.model,
              "proposal_schema": args.proposal_schema,
              "per_url": {u: {k: v for k, v in r.items() if k != "contents"} for u, r in results.items()},
              "cross_server_identity": cross_identity({u: r["contents"] for u, r in results.items()}),
              "cpu_before": census_before, "cpu_after": cpu_census()}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["per_url"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
