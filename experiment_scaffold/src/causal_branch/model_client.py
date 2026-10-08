"""Generic model-endpoint configuration and client (Round 8 Stage 4).

The Pi adapter targets an OpenAI-compatible endpoint. Local development uses the
already-running Ollama endpoint (`http://127.0.0.1:11434/v1`); remote
qualification swaps the configuration to a llama.cpp worker without changing
adapter code. The endpoint configuration is validated before Pi starts, secrets
are redacted from all logs and manifests, and the `qualifying` flag is explicit.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

# `offline_scripted_rehearsal` is the Round-4 addition: a synthetic endpoint
# for a model-free scripted rehearsal on a host with no server. It is never
# qualifying and its base URL is deliberately unroutable.
ENDPOINT_PURPOSES = ("local_adapter_development", "remote_qualification", "profiling",
                     "offline_scripted_rehearsal")

# Environment-variable overrides. The base URL / key / model may come from the
# environment so a single committed example config is used for both local and
# remote development.
ENV_BASE_URL = "OPENAI_BASE_URL"
ENV_API_KEY = "OPENAI_API_KEY"
ENV_MODEL = "OPENAI_MODEL"

_SECRET_MARKERS = ("api_key", "key", "token", "secret", "password")


def redact(value: Any) -> Any:
    """Recursively redact secret-looking keys from a record."""
    if isinstance(value, Mapping):
        return {
            str(k): ("<redacted>" if any(marker in str(k).lower() for marker in _SECRET_MARKERS) else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def redact_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "<redacted>"
    return key[:4] + "…" + key[-4:]


@dataclass(frozen=True)
class AgentModelEndpoint:
    provider: str
    base_url: str
    api_key: str
    model_id: str
    context_ceiling: int = 32768
    output_ceiling: int = 4096
    sampling: Mapping[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 120.0
    purpose: str = "local_adapter_development"
    qualifying: bool = False

    def __post_init__(self) -> None:
        if self.purpose not in ENDPOINT_PURPOSES:
            raise ValueError(f"purpose must be one of {ENDPOINT_PURPOSES}")
        if not self.base_url or not self.model_id:
            raise ValueError("base_url and model_id are required")
        # Scientific qualification is decided by a signed runtime record and
        # execution authorization, not by this data class. Local examples remain
        # `qualifying: false`; a remote pin may become qualifying only after
        # smoke, capability audit, model provenance, D7, and replacement R5-2A
        # all validate.

    def redacted(self) -> dict[str, Any]:
        record = {
            "provider": self.provider,
            "base_url": self.base_url,
            "api_key": redact_key(self.api_key),
            "model_id": self.model_id,
            "context_ceiling": self.context_ceiling,
            "output_ceiling": self.output_ceiling,
            "sampling": dict(self.sampling),
            "timeout_seconds": self.timeout_seconds,
            "purpose": self.purpose,
            "qualifying": self.qualifying,
        }
        return record


def load_model_endpoint(config_path: Path, *, env: Mapping[str, str] | None = None) -> AgentModelEndpoint:
    """Load and validate an endpoint config, applying environment overrides."""
    record = json.loads(config_path.read_text(encoding="utf-8"))
    env = dict(os.environ if env is None else env)
    base_url = env.get(ENV_BASE_URL) or record.get("base_url")
    api_key = env.get(ENV_API_KEY) or record.get("api_key") or ""
    model_id = env.get(ENV_MODEL) or record.get("model_id")
    if not model_id:
        raise ValueError(
            "model_id is required (set OPENAI_MODEL or provide model_id in the config)"
        )
    sampling = record.get("sampling") or {}
    return AgentModelEndpoint(
        provider=record.get("provider", "openai-compatible"),
        base_url=str(base_url),
        api_key=str(api_key),
        model_id=str(model_id),
        context_ceiling=int(record.get("context_ceiling", 32768)),
        output_ceiling=int(record.get("output_ceiling", 4096)),
        sampling=dict(sampling),
        timeout_seconds=float(record.get("timeout_seconds", 120.0)),
        purpose=record.get("purpose", "local_adapter_development"),
        qualifying=bool(record.get("qualifying", False)),
    )


def endpoint_digest(endpoint: AgentModelEndpoint) -> str:
    """A stable digest over the non-secret identity of an endpoint."""
    payload = json.dumps(
        {
            "provider": endpoint.provider,
            "base_url": endpoint.base_url,
            "model_id": endpoint.model_id,
            "context_ceiling": endpoint.context_ceiling,
            "output_ceiling": endpoint.output_ceiling,
            "sampling": dict(endpoint.sampling),
            "purpose": endpoint.purpose,
            "qualifying": endpoint.qualifying,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ModelClient:
    """Thin OpenAI-compatible client used for endpoint health and model discovery.

    The Pi agent performs actual completion calls; this client is used only to
    verify the endpoint, discover the exact model ID, and run a read-only
    smoke turn.
    """

    def __init__(self, endpoint: AgentModelEndpoint) -> None:
        self.endpoint = endpoint

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.endpoint.api_key}"}

    def _url(self, path: str) -> str:
        return self.endpoint.base_url.rstrip("/") + path

    def list_models(self) -> list[str]:
        import urllib.request

        request = urllib.request.Request(self._url("/models"), headers=self._headers())
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [str(item.get("id")) for item in payload.get("data", [])]

    def health(self) -> dict[str, Any]:
        models = self.list_models()
        return {
            "reachable": True,
            "models": models,
            "exact_model_id": self.endpoint.model_id if self.endpoint.model_id in models else None,
        }

    def complete(self, prompt: str, *, max_tokens: int | None = None) -> dict[str, Any]:
        import urllib.request

        body = {
            "model": self.endpoint.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or self.endpoint.output_ceiling,
            **dict(self.endpoint.sampling),
        }
        request = urllib.request.Request(
            self._url("/chat/completions"),
            data=json.dumps(body).encode("utf-8"),
            headers={**self._headers(), "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.endpoint.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
