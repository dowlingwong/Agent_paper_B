# Vendored Pi — local changes

Every modification to the vendored upstream source is recorded here. The table
is the authoritative patch ledger; each row names the file, the behavior
changed, the reason, the tests exercising it, and whether it touches the
scientific state surface (anything the assignment/risk/adjudicator/sibling
boundary depends on).

## Patch ledger

Two vendored source files are modified, both for the DeepSeek substrate's
per-completion identity requirement (handoff Work Package 2). The authoritative,
hash-bound record is [`protocols/pi_local_modifications.yaml`](../../protocols/pi_local_modifications.yaml);
`scripts/verify_vendored_pi.py` classifies a modified file as
`approved_local_modification` **only** when its digest matches that record, so a
further edit to a patched file fails verification exactly as an unrecorded one
does.

| File | Change | Scientific state surface | Tests |
| --- | --- | --- | --- |
| `packages/ai/src/api/openai-completions.ts` | Record the provider's per-completion identity on the assistant message: first nonempty `system_fingerprint` (a mid-stream change throws), raw `chunk.model`, raw `chunk.created`, raw usage block. Request-side behavior unchanged. | None — read-only over the response | `test_substrate_identity.py::RealPiLedgerTests`, `::AdapterLedgerTests` |
| `packages/ai/src/types.ts` | Additive optional fields on `AssistantMessage`: `providerModel`, `systemFingerprint`, `providerCreated`, `providerUsage`. | None | `test_substrate_identity.py::CompletionFromMessageTests` |

**Why these could not be done natively.** The stream handler discarded
`system_fingerprint` outright, and `responseModel` is populated only when the
provider substitutes a *different* model — so against a correctly-answering
provider there was nothing to check. An empirical probe of `message_end` before
the patch confirmed the event carried no fingerprint, no provider time, and no
response model. The fatal identity rule needs proof per completion, and no
native Pi interface exposes it. Pi's normalized `Usage` likewise cannot express
DeepSeek's `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` split, which
the expense ledger reconciles against.

Everything else below remains true: no other vendored file is modified, and the
rest of the integration still uses only native interfaces.

## Why no further Pi source patch was required

The Round 8 scientific integration is implemented entirely through Pi's native
interfaces:

| Requirement | Native mechanism used (no patch) |
| --- | --- |
| Agent-home / session-dir isolation | `PI_CODING_AGENT_DIR` env var + `--session-dir` |
| Disable skills / extensions / context / prompt templates | `--no-skills --no-extensions --no-context-files --no-prompt-templates` |
| Disable built-in tools / MCP / network / auth discovery | `--no-builtin-tools --offline` |
| Tool allowlist | `--tools <comma-list>` |
| Disable auto-compaction / auto-retry | RPC `set_auto_compaction {enabled:false}` / `set_auto_retry {enabled:false}` |
| Model selection | native `models.json` provider `r8-local-openai-compatible` + `--provider`/`--model` |
| System prompt | `--system-prompt <abs path>` |
| Tool execution boundary | explicit extension (`experiment_scaffold/pi_extensions/scientific_tool_bridge.ts`) forwarding over a per-branch Unix socket to the Python `ToolBridge` |
| Quiescence detection | native `agent_settled` event (not `agent_end`) |
| Completed-entry selection | native `get_entries` with `leafId` present in the returned entries |
| Deterministic session truncation | Python `truncate_session_at_entry` (schema-aware, fail-closed) |

The earlier fake-protocol commands (`set_tools`, `tool_requested`, `tool_result`)
were removed; the Python RPC client now uses only native Pi commands and events
(see `experiment_scaffold/src/causal_branch/pi_rpc.py` and the vendored
`packages/coding-agent/docs/rpc.md`).

## Scientific state surface

No patch touches assignment, risk, adjudicator, sibling, or evidence state. The
tool bridge (extension + socket + Python `ToolBridge`) is the only place Pi and
the Python scaffold meet, and it is fully owned by the scaffold.
