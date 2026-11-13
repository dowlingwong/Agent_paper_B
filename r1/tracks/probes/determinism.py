#!/usr/bin/env python3
"""S0.1 probe: LLM determinism, latency and CPU census on one host (runbook rev. 3 §2 S0.1).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. Runs on the host (TASL-2, TASL-7) against the
host's own llama-server(s); it never starts or stops a server.

N fixed manager prompts (the harness LangGraph prompt for the node at trial indices 2..N+1; every
other prompt carries a deterministic non-empty memory block (``memory_text``), so both prompt shapes are
probed; or ``--prompts FILE`` with one {"prompt", "seed"} JSON object per line) are sent with their
fixed D26 seeds (``manager_seed("tracks_s01", i, 0)``) to each URL, ``--repeats`` times each:

* ``--mode serial``      (a) one server;
* ``--mode concurrent``  (b) several servers (one thread group per URL), all at once;
* ``--clients-per-url 2`` two concurrent client streams per server (the planned two campaigns per server).

Every client sends every (prompt, repeat) pair once in its own randomised order (``--order-seed``, recorded), so
the repeats of a prompt are interleaved with different predecessors and prompt-cache / KV-order effects show up
as non-identical repeats (final review MAJOR 6). The request body is the harness's own (``chat_payload``: no
max_tokens; the same seed, temperature and optional grammar). The report records the GGUF sha256, the llama.cpp
build and the server command line (all required) and the server's ``/props``.

Reported per URL: within-server identity rate (share of prompts whose every repeat returned the same
content; a prompt with an errored repeat counts as NOT identical, review m7), mean and p95 latency; across URLs: cross-server identity (recorded, not required);
and a CPU census (cores, load, cores free). The pass criterion of S0.1 (100 % within-host identity in
the setting S3 will use) is applied by the author, not here.

  python -m r1.tracks.probes.determinism --url http://127.0.0.1:18083/v1 --model r1-manager \\
      --n 200 --repeats 2 --mode serial --clients-per-url 2 --host-label TASL-2 --gguf /models/m.gguf \\
      --llama-server-bin /opt/llama.cpp/build/bin/llama-server --server-args "-np 1 -c 8192 --port 18083" \\
      --out s01_tasl2_serial.json
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

PROBE_SCHEMA = "tracks_s01_probe/v2"
SEED_KEY = "tracks_s01"


def chat_payload(prompt: str, seed: int, model: str, *, temperature: float = 0.2,
                 proposal_schema: str | None = None) -> dict:
    """The exact request body the harness sends (final review MAJOR 6): built by the harness's own LangGraph
    client (``langchain_client._build_chat_model`` for ``llamacpp/<model>`` with the D26 seed, and the
    ``manager_proposal/v1`` ``response_format`` when ``proposal_schema`` is set), one user message. No
    ``max_tokens``: the harness sets none."""
    from r1.harness import import_harness
    import_harness()
    from langchain_core.messages import HumanMessage
    from autoresearch.llm.langchain_client import _build_chat_model
    from autoresearch.llm.providers import manager_response_format, resolve_llm_config
    kwargs = {"response_format": manager_response_format(proposal_schema)} if proposal_schema else {}
    old = os.environ.get("LLAMACPP_BASE_URL")
    os.environ["LLAMACPP_BASE_URL"] = "http://127.0.0.1:9/v1"   # the URL is not part of the body; nothing is sent
    try:
        llm = _build_chat_model(resolve_llm_config(f"llamacpp/{model}"), float(temperature), seed=int(seed), **kwargs)
        payload = dict(llm._get_request_payload([HumanMessage(content=prompt)]))
        # R1-CACHEPROMPT-FALSE (31 Oct 2026): the OpenAI SDK merges ``extra_body`` into the JSON body it
        # posts, so the harness's on-the-wire body carries ``cache_prompt`` at top level. This probe posts
        # the payload itself, so it must do the same merge to send exactly what the harness sends.
        extra = payload.pop("extra_body", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return payload
    finally:
        if old is None:
            os.environ.pop("LLAMACPP_BASE_URL", None)
        else:
            os.environ["LLAMACPP_BASE_URL"] = old


def post(url: str, payload: dict, timeout: float = 300.0) -> tuple[str, float]:
    """POST ``payload`` to ``<url>/chat/completions``; returns (content, latency seconds)."""
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - operator-given local URL
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"], time.perf_counter() - t0


_PAYLOAD_LOCK = threading.Lock()


def schedule(n_prompts: int, repeats: int, order_seed: int, url_index: int, client: int) -> list[tuple[int, int]]:
    """One client's call order: every (prompt, repeat) pair once, in a random order keyed by (order_seed, URL,
    client), so repeats are interleaved and a prompt's predecessors differ between its repeats (KV / prompt-cache
    order effects become visible)."""
    import random
    items = [(i, r) for r in range(repeats) for i in range(n_prompts)]
    random.Random(f"{order_seed}|{url_index}|{client}").shuffle(items)
    return items


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


def run_client(url: str, payloads: list[dict], order: list[tuple[int, int]], timeout: float,
               log: list | None = None) -> dict:
    """One serial client stream against one server, in ``order`` (``payloads``: the harness request per prompt)."""
    contents: dict[int, list] = {i: [] for i in range(len(payloads))}
    lat: list[float] = []
    errors = 0
    for i, r in order:
        try:
            text, dt = post(url, payloads[i], timeout)
        except Exception:  # noqa: BLE001 - a failed call is counted (and is not identical), never retried
            errors += 1
            contents[i].append(None)
            continue
        contents[i].append(text)
        lat.append(dt)
        if log is not None:
            log.append(dt)
    return {"contents": contents, "latencies": lat, "errors": errors}


def run_url(url: str, model: str, prompts: list[dict], repeats: int, timeout: float,
            proposal_schema: str | None = None, *, clients: int = 1, order_seed: int = 0, url_index: int = 0,
            temperature: float = 0.2) -> dict:
    """``clients`` concurrent client streams (threads) against one server, each with its own randomised,
    interleaved schedule of all prompts x repeats. Identity is over every call of a prompt on this server (all
    clients and repeats); per-client identity and the clients' first-call agreement are reported too."""
    per_client: list[dict] = [None] * clients  # type: ignore[list-item]
    with _PAYLOAD_LOCK:  # chat_payload sets LLAMACPP_BASE_URL briefly: build every body before any thread starts
        payloads = [chat_payload(p["prompt"], p["seed"], model, temperature=temperature,
                                 proposal_schema=proposal_schema) for p in prompts]
    orders = [schedule(len(prompts), repeats, order_seed, url_index, c) for c in range(clients)]
    threads = [threading.Thread(target=lambda c=c: per_client.__setitem__(
        c, run_client(url, payloads, orders[c], timeout))) for c in range(clients)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    contents = {i: [x for pc in per_client for x in pc["contents"][i]] for i in range(len(prompts))}
    lat = [x for pc in per_client for x in pc["latencies"]]
    return {"contents": contents, "latency": latency_stats(lat), "errors": sum(pc["errors"] for pc in per_client),
            "identity_rate": identity_rate(contents, repeats * clients), "clients": clients,
            "identity_rate_per_client": [identity_rate(pc["contents"], repeats) for pc in per_client],
            "cross_client_identity": cross_identity({c: pc["contents"] for c, pc in enumerate(per_client)}),
            "order_head": [orders[c][:5] for c in range(clients)]}


def server_props(url: str, timeout: float = 10.0) -> dict | None:
    """llama-server's ``/props`` (build info, default generation settings, model path) when it answers."""
    base = url.rstrip("/")
    base = base[:-3] if base.endswith("/v1") else base
    try:
        with urllib.request.urlopen(base + "/props", timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read())
    except Exception:  # noqa: BLE001 - recorded as missing
        return None


def sha256_path(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def provenance(args) -> dict:
    """GGUF sha256, llama.cpp build / commit and the server arguments (all required; "unknown" refused)."""
    import subprocess
    gguf = args.gguf_sha256 or (sha256_path(args.gguf) if args.gguf else None)
    build = args.llama_build
    if not build and args.llama_server_bin:
        try:
            r = subprocess.run([args.llama_server_bin, "--version"], capture_output=True, text=True, timeout=30)
            build = (r.stdout + r.stderr).strip() or None
        except Exception:  # noqa: BLE001
            build = None
    missing = [name for name, v in (("--gguf/--gguf-sha256", gguf), ("--llama-build/--llama-server-bin", build),
                                    ("--server-args", args.server_args)) if not v or str(v).lower() == "unknown"]
    if missing:
        raise SystemExit(f"the S0.1 report needs provenance: {', '.join(missing)}")
    return {"gguf_sha256": gguf, "gguf_path": args.gguf, "llama_build": build, "server_args": args.server_args}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", action="append", required=True, help="llama-server OpenAI base URL (.../v1); repeatable")
    ap.add_argument("--model", default="r1-manager")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--mode", choices=["serial", "concurrent"], default="serial")
    ap.add_argument("--clients-per-url", type=int, default=1,
                    help="concurrent client streams per server (2 = the planned two campaigns per server)")
    ap.add_argument("--order-seed", type=int, default=20261029, help="seed of the randomised call order (recorded)")
    ap.add_argument("--node", default="digits_mlp")
    ap.add_argument("--prompts", default=None, help="JSONL of {prompt, seed} (default: harness prompts)")
    ap.add_argument("--temperature", type=float, default=0.2, help="the collector's manager temperature")
    ap.add_argument("--proposal-schema", default=None, help="send sweep 1's response_format (manager_proposal/v1)")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--host-label", required=True)
    ap.add_argument("--gguf", default=None, help="the served GGUF (its sha256 is computed)")
    ap.add_argument("--gguf-sha256", default=None)
    ap.add_argument("--llama-build", default=None, help="llama.cpp build / commit")
    ap.add_argument("--llama-server-bin", default=None, help="llama-server binary (its --version is recorded)")
    ap.add_argument("--server-args", default=None, help="the llama-server command line (e.g. '-np 1 -c 8192 ...')")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.mode == "serial" and len(args.url) != 1:
        ap.error("--mode serial takes exactly one --url")
    if args.clients_per_url < 1:
        ap.error("--clients-per-url must be >= 1")
    prov = provenance(args)
    prompts = ([json.loads(l) for l in Path(args.prompts).read_text().splitlines() if l.strip()]
               if args.prompts else fixed_prompts(args.n, args.node))[: args.n]
    census_before = cpu_census()
    results: dict[str, dict] = {}

    def one(u: str, idx: int) -> None:
        results[u] = run_url(u, args.model, prompts, args.repeats, args.timeout, args.proposal_schema,
                             clients=args.clients_per_url, order_seed=args.order_seed, url_index=idx,
                             temperature=args.temperature)

    if args.mode == "serial":
        one(args.url[0], 0)
    else:
        threads = [threading.Thread(target=one, args=(u, k)) for k, u in enumerate(args.url)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    report = {"schema": PROBE_SCHEMA, "label": "ENGINEERING_ONLY", "host": args.host_label, "mode": args.mode,
              "n_prompts": len(prompts), "repeats": args.repeats, "clients_per_url": args.clients_per_url,
              "order": {"seed": args.order_seed, "rule": "per (URL, client): every (prompt, repeat) once, shuffled"},
              "model": args.model, "temperature": args.temperature, "proposal_schema": args.proposal_schema,
              "request_example": chat_payload(prompts[0]["prompt"], prompts[0]["seed"], args.model,
                                              temperature=args.temperature, proposal_schema=args.proposal_schema)
              if prompts else None,
              "provenance": prov, "server_props": {u: server_props(u) for u in args.url},
              "per_url": {u: {k: v for k, v in r.items() if k != "contents"} for u, r in results.items()},
              "cross_server_identity": cross_identity({u: r["contents"] for u, r in results.items()}),
              "cpu_before": census_before, "cpu_after": cpu_census()}
    # R1-CACHEPROMPT-FALSE (31 Oct 2026): top-level field so a summariser does not have to dig into the
    # request body. Records written before the harness sent the field carry no cache_prompt key at all;
    # they are labelled with the author's wording, because an absent field means llama-server's default.
    cp = (report.get("request_example") or {}).get("cache_prompt", "__absent__")
    report["cache_prompt"] = None if cp == "__absent__" else bool(cp)
    report["cache_prompt_label"] = ("absent (= true, llama-server default)" if cp == "__absent__"
                                    else "explicit")
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["per_url"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
