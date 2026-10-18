"""Native Pi models.json generation for the isolated agent directory (Phase 2).

Pi selects the model through its native `models.json` provider registry, not
through OPENAI_BASE_URL/OPENAI_MODEL alone. For every fresh `PI_CODING_AGENT_DIR`
this module writes a `models.json` binding one project-specific provider
(`r8-local-openai-compatible`) to the exact endpoint and model ID.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .model_client import AgentModelEndpoint

PROVIDER_ID = "r8-local-openai-compatible"


def native_models_record(endpoint: AgentModelEndpoint) -> dict[str, Any]:
    sampling = dict(endpoint.sampling or {})
    thinking = sampling.get("thinking")
    thinking_enabled = bool(
        isinstance(thinking, Mapping) and thinking.get("type") == "enabled")
    hosted_deepseek = "deepseek.com" in endpoint.base_url.lower()
    reasoning_enabled = bool(thinking_enabled or sampling.get("reasoning_effort"))
    compat: dict[str, Any] = {
        "supportsDeveloperRole": False,
        "supportsReasoningEffort": bool(hosted_deepseek and reasoning_enabled),
    }
    if hosted_deepseek and reasoning_enabled:
        compat["requiresReasoningContentOnAssistantMessages"] = True
    model = {
        "id": endpoint.model_id,
        "name": endpoint.model_id,
        # Pi uses this flag when replaying assistant messages.  DeepSeek's
        # thinking-mode tool-call contract requires reasoning_content from a
        # tool-call turn to be carried transiently into the next request.  The
        # old unconditional False still parsed reasoning but did not state that
        # the model was reasoning, leaving replay dependent on incidental block
        # shape.  Local/non-thinking records remain byte-for-byte equivalent in
        # the value of this field.
        "reasoning": reasoning_enabled,
        "input": ["text"],
        "contextWindow": endpoint.context_ceiling,
        "maxTokens": endpoint.output_ceiling,
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "compat": dict(compat),
    }
    if sampling:
        model["samplingParams"] = sampling
    return {
        "providers": {
            PROVIDER_ID: {
                "baseUrl": endpoint.base_url,
                "api": "openai-completions",
                "apiKey": endpoint.api_key,
                "compat": dict(compat),
                "models": [model],
            }
        }
    }


def write_native_models_json(agent_dir: Path, endpoint: AgentModelEndpoint) -> Path:
    agent_dir.mkdir(parents=True, exist_ok=True)
    record = native_models_record(endpoint)
    path = agent_dir / "models.json"
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    # Hosted-provider credentials are transiently carried here because Pi's
    # custom-provider registry requires it.  A shared compute host must never
    # expose the file through the process umask while the branch is alive.
    path.chmod(0o600)
    return path


def models_json_digest(agent_dir: Path) -> str:
    path = agent_dir / "models.json"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def models_record_digest(endpoint: AgentModelEndpoint) -> str:
    payload = json.dumps(native_models_record(endpoint), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
