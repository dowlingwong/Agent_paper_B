#!/usr/bin/env python3
"""Track S STOP-1 diagnostic (author-authorised, 30 Oct 2026): does ``cache_prompt: false`` restore
bit-identical repeats on the pinned llama-server?

ENGINEERING_ONLY / DIAGNOSTIC. It is **not** a phase and sets no k.

The hypothesis under test: llama-server's default prompt caching (``cache_prompt`` true) reuses the
slot's KV prefix from the previous request, so batch boundaries depend on the predecessor and outputs
are not bit-identical; the harness request body sends no ``cache_prompt`` field.

This script reuses the **pinned** S0.1 probe (``r1/tracks/probes/determinism.py`` at paper ``9bb64ba``)
without modifying it: its fixed prompts, its per-prompt seeds, the harness ``chat_payload`` body, its
serial interleaved schedule (``order_seed``, ``url_index=0``, ``client=0``), its ``identity_rate``,
``latency_stats`` and ``cpu_census``. The **only** difference from the pinned serial probe is one added
request field, ``"cache_prompt"``: ``false`` for the test run and ``true`` as the control. Both runs use
the identical prompts, seeds, body and call order.

Raw responses are kept: for every call, the call order, prompt index, repeat, latency, a content sha256
and length, and the server's token counts when it reports them; and for every prompt, its per-repeat
contents, so identity can be re-derived from the file.

  python r1/tracks/ops/diag/cache_prompt_diag.py --url http://127.0.0.1:18101/v1 --node digits_mlp \\
      --n 200 --repeats 3 --order-seed 1 --proposal-schema manager_proposal/v1 --mode both \\
      --host-label TASL-2 --gguf /path/model.gguf --llama-build 620d2225... \\
      --llama-server-bin /path/llama-server --server-args "<exact server cmd>" --out diag.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

SCHEMA = "tracks_s01_cacheprompt_diag/v1"
MODES = ("false", "true")  # test first, then the control


def post_full(url: str, payload: dict, timeout: float = 300.0):
    """POST the payload; return (content, latency_s, parsed_body). Mirrors the pinned probe's ``post``
    but also hands back the body so token counts can be recorded. No retry: a failure is counted."""
    req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - operator-given local URL
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"], time.perf_counter() - t0, body


def server_version(binary: str):
    """``llama-server --version`` first lines, for the provenance record (as the pinned probe does)."""
    import subprocess
    try:
        r = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30)
        return " ".join((r.stdout or r.stderr or "").strip().splitlines()[:2])
    except Exception as exc:  # noqa: BLE001
        return f"unavailable ({type(exc).__name__}: {exc})"


def tokens_of(body: dict):
    """Tokens the server reports, if any: ``timings.prompt_n`` (tokens evaluated) and ``usage``."""
    timings = body.get("timings") or {}
    usage = body.get("usage") or {}
    out = {}
    if isinstance(timings, dict):
        for k in ("prompt_n", "prompt_ms", "predicted_n", "predicted_ms"):
            if k in timings:
                out[k] = timings[k]
    if isinstance(usage, dict):
        for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
            if k in usage:
                out[k] = usage[k]
    return out or None


def run_mode(url: str, payloads: list[dict], order: list[tuple[int, int]], flag: bool, timeout: float) -> dict:
    """One serial client stream in ``order`` with ``cache_prompt`` forced to ``flag``."""
    n = len(payloads)
    contents: dict[int, list] = {i: [] for i in range(n)}
    latencies: list[float] = []
    calls: list[dict] = []
    errors = 0
    for pos, (i, r) in enumerate(order):
        payload = dict(payloads[i])
        payload["cache_prompt"] = flag
        try:
            text, dt, body = post_full(url, payload, timeout)
        except Exception as exc:  # noqa: BLE001 - counted, never retried (matches the pinned probe)
            errors += 1
            contents[i].append(None)
            calls.append({"order": pos, "prompt": i, "repeat": r, "error": f"{type(exc).__name__}: {exc}"})
            continue
        contents[i].append(text)
        latencies.append(dt)
        calls.append({"order": pos, "prompt": i, "repeat": r, "latency_s": dt,
                      "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
                      "content_len": len(text), "tokens": tokens_of(body)})
    return {"cache_prompt": flag, "contents": contents, "latencies": latencies, "calls": calls, "errors": errors}


def summarise(res: dict, repeats: int) -> dict:
    from r1.tracks.probes.determinism import identity_rate, latency_stats
    contents = res["contents"]
    identical = [i for i, v in contents.items()
                 if len(v) == repeats and None not in v and len(set(v)) == 1]
    return {"cache_prompt": res["cache_prompt"], "identity_rate": identity_rate(contents, repeats),
            "n_prompts": len(contents), "n_identical_prompts": len(identical),
            "n_differing_prompts": len(contents) - len(identical),
            "differing_prompt_indices": sorted(set(contents) - set(identical)),
            "errors": res["errors"], "latency": latency_stats(res["latencies"]),
            "tokens_evaluated_total": sum((c.get("tokens") or {}).get("prompt_n", 0)
                                          for c in res["calls"] if c.get("tokens")) or None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", default="r1-manager")
    ap.add_argument("--node", default="digits_mlp")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--order-seed", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--proposal-schema", default="manager_proposal/v1")
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--mode", choices=["false", "true", "both"], default="both")
    ap.add_argument("--host-label", required=True)
    ap.add_argument("--gguf", required=True)
    ap.add_argument("--llama-build", required=True)
    ap.add_argument("--llama-server-bin", required=True)
    ap.add_argument("--server-args", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    # The pinned probe, imported unchanged.
    from r1.tracks.probes import determinism as D

    prompts = D.fixed_prompts(args.n, args.node)[: args.n]
    payloads = [D.chat_payload(p["prompt"], p["seed"], args.model, temperature=args.temperature,
                               proposal_schema=args.proposal_schema) for p in prompts]
    order = D.schedule(len(prompts), args.repeats, args.order_seed, 0, 0)  # serial: url_index 0, client 0
    modes = MODES if args.mode == "both" else (args.mode,)

    census_before = D.cpu_census()
    results = {}
    for mode in modes:
        flag = mode == "true"
        raw = run_mode(args.url, payloads, order, flag, args.timeout)
        results[mode] = {"summary": summarise(raw, args.repeats),
                         "calls": raw["calls"],
                         "contents": {str(i): v for i, v in raw["contents"].items()}}
    census_after = D.cpu_census()

    report = {
        "schema": SCHEMA, "label": "DIAGNOSTIC", "engineering_label": "ENGINEERING_ONLY",
        "purpose": "Does cache_prompt=false restore bit-identical repeats? (STOP 1 diagnostic)",
        "reuses": "r1/tracks/probes/determinism.py at paper 9bb64ba, unchanged",
        "host": args.host_label, "url": args.url, "model": args.model, "node": args.node,
        "n_prompts": len(prompts), "repeats": args.repeats, "order_seed": args.order_seed,
        "order_head": order[:10], "temperature": args.temperature,
        "proposal_schema": args.proposal_schema,
        "mode_order": list(modes), "raw_responses_kept": True,
        "provenance": {"gguf_path": args.gguf, "gguf_sha256": D.sha256_path(args.gguf),
                       "llama_build": args.llama_build, "llama_server_bin": args.llama_server_bin,
                       "server_version": server_version(args.llama_server_bin),
                       "server_args": args.server_args},
        "server_props": D.server_props(args.url),
        "cpu_before": census_before, "cpu_after": census_after,
        "results": results,
    }
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({m: {k: v for k, v in r["summary"].items() if k != "differing_prompt_indices"}
                      for m, r in results.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
