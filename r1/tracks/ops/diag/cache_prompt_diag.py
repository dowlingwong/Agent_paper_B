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

Modes: ``false`` / ``true`` add ``cache_prompt``; ``absent`` sends no such field
(the plain S0.1 body, F2); ``both`` is the 30 Oct pair.

  python r1/tracks/ops/diag/cache_prompt_diag.py --url http://127.0.0.1:18101/v1 \
      --node digits_mlp --n 200 --repeats 3 --order-seed 1 \
      --proposal-schema manager_proposal/v1 --mode absent \
      --resident-server-count 1 --server-pid <listener pid> \
      --server-log /path/llama_18101.log --phase-label f2 --host-label TASL-2 \
      --gguf /path/model.gguf --llama-build 620d2225... \
      --llama-server-bin /path/llama-server --server-args '<measured cmdline>' \
      --out diag.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

SCHEMA = "tracks_s01_cacheprompt_diag/v2"
# "absent" sends no cache_prompt field at all -- the plain S0.1 request stream (F2).
MODES = ("false", "true", "absent")


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


def run_mode(url: str, payloads: list[dict], order: list[tuple[int, int]], flag, timeout: float) -> dict:
    """One serial client stream in ``order`` with ``cache_prompt`` set to ``flag`` (``None`` = omit the field)."""
    n = len(payloads)
    contents: dict[int, list] = {i: [] for i in range(n)}
    latencies: list[float] = []
    calls: list[dict] = []
    errors = 0
    for pos, (i, r) in enumerate(order):
        payload = dict(payloads[i])
        if flag is not None:  # None = "absent": send the plain S0.1 body, no cache_prompt field
            payload["cache_prompt"] = flag
        try:
            text, dt, body = post_full(url, payload, timeout)
        except Exception as exc:  # noqa: BLE001 - counted, never retried (matches the pinned probe)
            errors += 1
            contents[i].append(None)
            calls.append({"order": pos, "prompt": i, "repeat": r, "utc": utc(),
                          "error": f"{type(exc).__name__}: {exc}"})
            continue
        contents[i].append(text)
        latencies.append(dt)
        calls.append({"order": pos, "prompt": i, "repeat": r, "latency_s": dt, "utc": utc(),
                      "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
                      "content_len": len(text), "tokens": tokens_of(body)})
    return {"cache_prompt": flag, "contents": contents, "latencies": latencies, "calls": calls, "errors": errors}


def summarise(res: dict, repeats: int) -> dict:
    from r1.tracks.probes.determinism import identity_rate, latency_stats
    contents = res["contents"]
    identical = [i for i, v in contents.items()
                 if len(v) == repeats and None not in v and len(set(v)) == 1]
    # First call of each prompt in this mode: a first call with prompt_n == 1 was served entirely from the
    # KV cache (a hit); a first call that evaluated its full prompt is a miss. This is the cache-warmth
    # evidence for review S1 / F1 / F2.
    first = {}
    for c in res["calls"]:
        if c.get("error"):
            continue
        first.setdefault(c["prompt"], c)
    pn_first = [((c.get("tokens") or {}).get("prompt_n")) for c in first.values()]
    pn_obs = [x for x in pn_first if x is not None]
    hits = sum(1 for x in pn_obs if x == 1)
    return {"cache_prompt": res["cache_prompt"], "identity_rate": identity_rate(contents, repeats),
            "n_prompts": len(contents), "n_identical_prompts": len(identical),
            "n_differing_prompts": len(contents) - len(identical),
            "differing_prompt_indices": sorted(set(contents) - set(identical)),
            "errors": res["errors"], "latency": latency_stats(res["latencies"]),
            "tokens_evaluated_total": sum((c.get("tokens") or {}).get("prompt_n", 0)
                                          for c in res["calls"] if c.get("tokens")) or None,
            "first_call_cache_hits": hits,
            "first_call_cache_misses": len(pn_obs) - hits,
            "first_call_prompt_n_observed": len(pn_obs),
            "first_call_prompt_n_missing": len(pn_first) - len(pn_obs),
            "first_call_prompt_n_mean": (sum(pn_obs) / len(pn_obs)) if pn_obs else None,
            "usage_prompt_tokens_mean": _mean([(c.get("tokens") or {}).get("prompt_tokens") for c in res["calls"]]),
            "started_utc": res.get("started_utc"), "finished_utc": res.get("finished_utc")}


def _mean(vals):
    xs = [v for v in vals if v is not None]
    return sum(xs) / len(xs) if xs else None


def server_facts(pid: int, log_path: str) -> dict:
    """Measured server identity and request counts -- not claims. ``/proc`` reads only."""
    def read(p):
        try:
            return Path(p).read_text(errors="replace")
        except OSError:
            return ""
    facts = {"pid": pid, "exe": None, "cmdline": None, "cmdline_sha256": None, "start_lstart": None,
             "log": log_path, "completions_before": None, "completions_after": None}
    try:
        facts["exe"] = str(Path("/proc/%d/exe" % pid).resolve())
    except OSError:
        pass
    cmd = read("/proc/%d/cmdline" % pid).replace("\x00", " ").strip()
    if cmd:
        facts["cmdline"] = cmd
        facts["cmdline_sha256"] = hashlib.sha256(cmd.encode()).hexdigest()
    import subprocess
    try:
        r = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True, timeout=15)
        facts["start_lstart"] = r.stdout.strip() or None
    except Exception:  # noqa: BLE001
        pass
    facts["completions_before"] = read(log_path).count("/chat/completions")
    return facts


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
    ap.add_argument("--mode", choices=["false", "true", "absent", "both"], default="both",
                    help="absent = no cache_prompt field (the plain S0.1 request stream, F2)")
    ap.add_argument("--resident-server-count", type=int, required=True,
                    help="how many llama-server processes were resident on the GPU during this run")
    ap.add_argument("--server-pid", type=int, required=True,
                    help="the pid listening on the probed port (measured by the launch script)")
    ap.add_argument("--server-log", required=True, help="that server's own log, for request counts")
    ap.add_argument("--phase-label", required=True, help="f1 | f2 -- which follow-up this run is")
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

    facts = server_facts(args.server_pid, args.server_log)
    if (facts["completions_before"] or 0) != 0:
        raise SystemExit(f"refusing: the server log already shows {facts['completions_before']} completions "
                         f"before this run; the server is not fresh")
    census_before = D.cpu_census()
    results = {}
    for mode in modes:
        flag = {"true": True, "false": False, "absent": None}[mode]
        started = utc()
        raw = run_mode(args.url, payloads, order, flag, args.timeout)
        raw["started_utc"], raw["finished_utc"] = started, utc()
        ex = dict(payloads[0])
        if flag is not None:
            ex["cache_prompt"] = flag
        results[mode] = {"summary": summarise(raw, args.repeats),
                         "request_example": ex,
                         "calls": raw["calls"],
                         "contents": {str(i): v for i, v in raw["contents"].items()}}
    census_after = D.cpu_census()
    facts["completions_after"] = server_facts(args.server_pid, args.server_log)["completions_before"]

    report = {
        "schema": SCHEMA, "label": "DIAGNOSTIC", "engineering_label": "ENGINEERING_ONLY",
        "phase_label": args.phase_label,
        "purpose": "STOP-1 follow-ups F1 (cold cache_prompt=true) and F2 (plain S0.1 body, one server)",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "payload_sha256": {m: hashlib.sha256(json.dumps(r["request_example"], sort_keys=True).encode()).hexdigest()
                           for m, r in results.items()},
        "reuses": "r1/tracks/probes/determinism.py at paper 9bb64ba, unchanged",
        "host": args.host_label, "url": args.url, "model": args.model, "node": args.node,
        "n_prompts": len(prompts), "repeats": args.repeats, "order_seed": args.order_seed,
        "order_head": order[:10], "temperature": args.temperature,
        "proposal_schema": args.proposal_schema,
        "mode_order": list(modes), "raw_responses_kept": True,
        "resident_server_count": args.resident_server_count,
        "server": facts,
        "run_utc": utc(),
        # S4 fix: the exact body that was sent, for the mode that adds a field, so "only added field" is
        # checkable from this file alone. Kept for each mode under results[*].request_example.
        "modes_definition": {"false": "cache_prompt=false added", "true": "cache_prompt=true added",
                             "absent": "no cache_prompt field (plain S0.1 body)"},
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
