#!/usr/bin/env python3
"""TASL-2 side of the TASL-7 proposer engineering smoke.

Runs ON TASL-2 only.  Reads the frozen prompt text from the environment
(base64, no secrets), generates the harness manager_response_format() schema by
loading the real providers.py from the TASL-2 harness checkout, then calls the
TASL-7 llama-server over Tailscale: /health, /v1/models, and three
/v1/chat/completions manager-sized calls.  Prints one JSON object to stdout;
writes nothing to disk.
"""
import base64
import hashlib
import importlib.util
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request

PROVIDERS = "/home/dowling/r1_trackp/autoresearch_harness/src/autoresearch/llm/providers.py"
BASE_ALIAS = os.environ["SMOKE_BASE_URL"]          # shared-node alias reachable from TASL-2
BASE_LITERAL = os.environ.get("SMOKE_LITERAL_URL", "")  # the mandated bind address, as instructed
PROMPT = base64.b64decode(os.environ["REQ_PROMPT_B64"]).decode("utf-8")
MAX_COMPLETION_TOKENS = int(os.environ["MAX_COMPLETION_TOKENS"])
N_CALLS = int(os.environ.get("N_CALLS", "3"))
MODEL = os.environ["MODEL_NAME"]
SCHEMA_VERSION = os.environ["SCHEMA_VERSION"]

with open(PROVIDERS, "rb") as fh:
    providers_bytes = fh.read()
spec = importlib.util.spec_from_file_location("harness_providers", PROVIDERS)
mod = importlib.util.module_from_spec(spec)
sys.modules["harness_providers"] = mod
spec.loader.exec_module(mod)
response_format = mod.manager_response_format(SCHEMA_VERSION)
schema_sha256 = hashlib.sha256(json.dumps(response_format, sort_keys=True).encode()).hexdigest()
required_keys = sorted(response_format["json_schema"]["schema"]["required"])

body = {
    "model": MODEL,
    "messages": [{"role": "user", "content": PROMPT}],
    "temperature": 0.2,
    "cache_prompt": False,
    "response_format": response_format,
    "max_completion_tokens": MAX_COMPLETION_TOKENS,
    "stream": False,
}
request_sha256 = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
body_bytes = json.dumps(body).encode()


def http_json(url, data=None, timeout=1200):
    """Return dict with status/wall/body; never raises."""
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    status = None
    raw = b""
    err = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            raw = exc.read()
        except Exception as exc2:  # noqa: BLE001
            err = "read:" + repr(exc2)
    except Exception as exc:  # noqa: BLE001
        err = repr(exc)
    wall = time.monotonic() - t0
    out = {"status": status, "wall_s": round(wall, 4),
           "body_bytes": len(raw), "error": err}
    try:
        out["json"] = json.loads(raw)
    except Exception:  # noqa: BLE001
        out["json"] = None
        if raw:
            out["text_head"] = raw[:800].decode("utf-8", "replace")
    return out


result = {
    "client_host": os.uname().nodename,
    "providers_path": PROVIDERS,
    "providers_sha256": hashlib.sha256(providers_bytes).hexdigest(),
    "schema_version": SCHEMA_VERSION,
    "response_format": response_format,
    "response_format_sha256": schema_sha256,
    "required_keys": required_keys,
    "model_requested": MODEL,
    "prompt_chars": len(PROMPT),
    "request_body": body,
    "request_sha256": request_sha256,
    "max_completion_tokens": MAX_COMPLETION_TOKENS,
    "base_alias": BASE_ALIAS,
    "base_literal": BASE_LITERAL,
    "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}

# literal mandated address, short timeout (expected unreachable from this tailnet)
if BASE_LITERAL:
    result["literal_health"] = http_json(BASE_LITERAL + "/health", timeout=15)
    result["literal_v1_models"] = http_json(BASE_LITERAL + "/v1/models", timeout=15)

result["health"] = http_json(BASE_ALIAS + "/health", timeout=60)
result["v1_models"] = http_json(BASE_ALIAS + "/v1/models", timeout=60)

calls = []
for i in range(1, N_CALLS + 1):
    res = http_json(BASE_ALIAS + "/v1/chat/completions", data=body_bytes, timeout=1800)
    call = {"call": i, "http_status": res["status"], "wall_s": res["wall_s"],
            "error": res["error"], "body_bytes": res["body_bytes"]}
    obj = res.get("json")
    if isinstance(obj, dict):
        choice = (obj.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = msg.get("content")
        call["finish_reason"] = choice.get("finish_reason")
        call["usage"] = obj.get("usage")
        call["timings"] = obj.get("timings")
        call["content"] = content
        parse_ok = False
        parsed = None
        parse_error = None
        try:
            parsed = json.loads(content) if isinstance(content, str) else None
        except Exception as exc:  # noqa: BLE001
            parse_error = repr(exc)
        if isinstance(parsed, dict):
            parse_ok = sorted(parsed.keys()) == required_keys
        call["json_parse_ok"] = parse_ok
        call["parsed_keys"] = sorted(parsed.keys()) if isinstance(parsed, dict) else None
        call["parsed"] = parsed
        call["parse_error"] = parse_error
    else:
        call["raw_text_head"] = res.get("text_head")
    calls.append(call)

result["calls"] = calls
result["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
ok = [c for c in calls if c["http_status"] == 200]
lat = [c["wall_s"] for c in ok]
if lat:
    result["latency_stats_s"] = {
        "n": len(lat), "min": min(lat), "p50": round(statistics.median(lat), 4),
        "max": max(lat), "mean": round(statistics.mean(lat), 4)}
result["calls_http_ok"] = len(ok)
result["calls_json_ok"] = sum(1 for c in calls if c.get("json_parse_ok"))
print(json.dumps(result, indent=2))
