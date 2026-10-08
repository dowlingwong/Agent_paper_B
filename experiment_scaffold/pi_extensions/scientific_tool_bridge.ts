/**
 * Scientific tool bridge extension (Round 8, Phase 2).
 *
 * Registers exactly the seven frozen scientific tools and forwards every
 * request over a private per-branch Unix-domain socket to the Python
 * ToolBridge. The Python side owns all policy and execution. There is no shell
 * evaluation here and no access to assignment, risk, adjudicator, sibling, or
 * evidence state.
 *
 * Protocol (length-prefixed JSON frames, 4-byte big-endian length + JSON):
 *   request  = {protocol_version, run_id, branch_id, tool_call_id, tool_name,
 *               arguments, token}
 *   response = {protocol_version, tool_call_id, ok, result, error}
 *
 * Environment variables set by the Python adapter:
 *   PI_TOOL_BRIDGE_SOCKET, PI_TOOL_BRIDGE_TOKEN,
 *   PI_TOOL_BRIDGE_PROTOCOL_VERSION, PI_TOOL_BRIDGE_RUN_ID, PI_TOOL_BRIDGE_BRANCH_ID
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import * as net from "node:net";
import { createHash, randomUUID } from "node:crypto";

const PROTOCOL_VERSION = "r8-tool-bridge-1";
const MAX_FRAME = 16 * 1024 * 1024;

type BridgeResponse = { ok: boolean; result: unknown; error: string | null };

/** Send one length-prefixed JSON frame and read the single response frame. */
function bridgeSend(payload: Record<string, unknown>): Promise<BridgeResponse> {
	const socketPath = process.env.PI_TOOL_BRIDGE_SOCKET;
	const token = process.env.PI_TOOL_BRIDGE_TOKEN;
	if (!socketPath || !token) {
		return Promise.reject(new Error("tool bridge socket or token not configured"));
	}
	return new Promise((resolve, reject) => {
		const sock = net.createConnection(socketPath);
		const chunks: Buffer[] = [];
		let settled = false;

		const finish = (fn: () => void) => {
			if (!settled) {
				settled = true;
				fn();
			}
		};

		sock.on("connect", () => {
			const body = Buffer.from(JSON.stringify({ token, ...payload }), "utf8");
			const header = Buffer.alloc(4);
			header.writeUInt32BE(body.length);
			sock.write(Buffer.concat([header, body]));
		});

		sock.on("data", (chunk: Buffer) => {
			chunks.push(chunk);
			const buf = Buffer.concat(chunks);
			if (buf.length < 4) return;
			const length = buf.readUInt32BE(0);
			if (length <= 0 || length > MAX_FRAME) {
				finish(() => reject(new Error(`tool bridge invalid frame length: ${length}`)));
				sock.destroy();
				return;
			}
			if (buf.length < 4 + length) return;
			const body = buf.subarray(4, 4 + length).toString("utf8");
			finish(() => {
				try {
					resolve(JSON.parse(body) as BridgeResponse);
				} catch (err) {
					reject(new Error(`tool bridge malformed response: ${String(err)}`));
				}
			});
			sock.end();
		});

		sock.on("error", (err) => finish(() => reject(new Error(`tool bridge socket error: ${err.message}`))));
		sock.on("close", () =>
			finish(() => reject(new Error("tool bridge socket closed before response"))),
		);
	});
}

function bridgeRequest(
	toolCallId: string,
	toolName: string,
	arguments_: Record<string, unknown>,
): Promise<BridgeResponse> {
	const runId = process.env.PI_TOOL_BRIDGE_RUN_ID ?? "unknown";
	const branchId = process.env.PI_TOOL_BRIDGE_BRANCH_ID ?? "unknown";
	return bridgeSend({
		protocol_version: PROTOCOL_VERSION,
		run_id: runId,
		branch_id: branchId,
		tool_call_id: toolCallId,
		tool_name: toolName,
		arguments: arguments_,
	});
}

const OBSERVED_SYSTEM_PROMPT_TOOL = "__observed_system_prompt__";
const OBSERVED_REQUEST_SYSTEM_PROMPT_TOOL = "__observed_request_system_prompt__";

/**
 * Forward the digest of the rendered system prompt Pi just built. This is an
 * out-of-band observation on the same socket as tool calls; the Python side
 * intercepts it before tool dispatch and compares it to its reconstruction.
 */
function bridgeObserve(systemPrompt: string, turnIndex: number): Promise<BridgeResponse> {
	const runId = process.env.PI_TOOL_BRIDGE_RUN_ID ?? "unknown";
	const branchId = process.env.PI_TOOL_BRIDGE_BRANCH_ID ?? "unknown";
	const sha256 = createHash("sha256").update(systemPrompt, "utf8").digest("hex");
	return bridgeSend({
		protocol_version: PROTOCOL_VERSION,
		run_id: runId,
		branch_id: branchId,
		message_type: "observed_system_prompt",
		tool_call_id: `obs-${randomUUID()}`,
		tool_name: OBSERVED_SYSTEM_PROMPT_TOOL,
		arguments: { sha256, turn_index: turnIndex },
	});
}

/**
 * Forward the digest of the system message of ONE provider request. Same
 * socket, same interception on the Python side; a distinct sentinel so the
 * two granularities are never confused.
 */
function bridgeObserveRequest(
	sha256: string,
	requestIndex: number,
	role: string,
	messageCount: number,
	shape: string,
): Promise<BridgeResponse> {
	const runId = process.env.PI_TOOL_BRIDGE_RUN_ID ?? "unknown";
	const branchId = process.env.PI_TOOL_BRIDGE_BRANCH_ID ?? "unknown";
	return bridgeSend({
		protocol_version: PROTOCOL_VERSION,
		run_id: runId,
		branch_id: branchId,
		message_type: "observed_request_system_prompt",
		tool_call_id: `obsreq-${randomUUID()}`,
		tool_name: OBSERVED_REQUEST_SYSTEM_PROMPT_TOOL,
		arguments: { sha256, request_index: requestIndex, role, message_count: messageCount, shape },
	});
}

const TOOL_NAMES = [
	"read_artifact",
	"write_artifact",
	"edit_artifact",
	"run_registered_command",
	"inspect_dataset",
	"submit_candidate",
	"request_verification",
] as const;

/** Recursively sort keys so the canonical schema digest matches the Python side. */
function canonicalStringify(value: unknown): string {
	if (Array.isArray(value)) {
		return `[${value.map(canonicalStringify).join(",")}]`;
	}
	if (value !== null && typeof value === "object") {
		const keys = Object.keys(value as Record<string, unknown>).sort();
		return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalStringify((value as Record<string, unknown>)[k])}`).join(",")}}`;
	}
	return JSON.stringify(value);
}

function makeTool(name: string, description: string, parameters: ReturnType<typeof Type.Object>) {
	return {
		name,
		label: name,
		description,
		parameters,
		async execute(
			toolCallId: string,
			params: Record<string, unknown>,
			_signal: AbortSignal,
			_onUpdate: unknown,
			_ctx: unknown,
		) {
			const response = await bridgeRequest(toolCallId, name, params);
			if (!response.ok) {
				throw new Error(response.error ?? `tool ${name} failed`);
			}
			return {
				content: [{ type: "text" as const, text: JSON.stringify(response.result) }],
				details: {},
			};
		},
	};
}

export default function (pi: ExtensionAPI) {
	const tools = [
		makeTool(
			"read_artifact",
			"Read a file from the workspace. The path must be workspace-relative; hidden paths are denied.",
			Type.Object({ path: Type.String({ description: "workspace-relative file path" }) }),
		),
		makeTool(
			"write_artifact",
			"Write a file into the workspace. The path must be workspace-relative; hidden paths are denied.",
			Type.Object({
				path: Type.String({ description: "workspace-relative file path" }),
				content: Type.String({ description: "file content" }),
			}),
		),
		makeTool(
			"edit_artifact",
			"Replace one occurrence of old_string with new_string in a workspace file.",
			Type.Object({
				path: Type.String({ description: "workspace-relative file path" }),
				old_string: Type.String({ description: "exact substring to replace" }),
				new_string: Type.String({ description: "replacement text" }),
			}),
		),
		makeTool(
			"run_registered_command",
			"Run a command from the registered command grammar. The command name must be allowlisted.",
			Type.Object({ command: Type.String({ description: "registered command name" }) }),
		),
		makeTool(
			"inspect_dataset",
			"Read the dataset manifest for a registered dataset id.",
			Type.Object({ dataset_id: Type.String({ description: "registered dataset id" }) }),
		),
		makeTool(
			"submit_candidate",
			"Submit a candidate result artifact from the workspace.",
			Type.Object({ path: Type.String({ description: "workspace-relative candidate path" }) }),
		),
		makeTool(
			"request_verification",
			"Request an independent verification verdict for a candidate artifact.",
			Type.Object({ path: Type.String({ description: "workspace-relative candidate path" }) }),
		),
	];
	for (const tool of tools) {
		pi.registerTool(tool);
	}
	// Announce the exact tool surface and schema digest on stderr so the Python
	// smoke test can cross-check them against registered_tools.TOOL_SCHEMA_DIGEST.
	const names = TOOL_NAMES.join(",");
	const schemas: Record<string, unknown> = {};
	for (const tool of tools) {
		schemas[tool.name] = tool.parameters;
	}
	const digest = createHash("sha256").update(canonicalStringify(schemas)).digest("hex");
	console.error(`PI_TOOL_SURFACE=${names}`);
	console.error(`PI_TOOL_SCHEMA_DIGEST=${digest}`);

	// Observe the rendered system prompt Pi actually sends. The handler RETURNS
	// NOTHING: it never rewrites the prompt. A send failure is logged and left to
	// the harness, whose absent-observed-digest rule refuses the branch.
	//
	// GRANULARITY. `before_agent_start` fires ONCE PER TURN, before the first
	// completion, with the string Pi is about to snapshot for the turn's agent
	// loop. It is a turn-start observation, not a per-request one.
	let turnIndex = 0;
	pi.on("before_agent_start", async (event) => {
		const thisTurn = turnIndex++;
		try {
			await bridgeObserve(event.systemPrompt, thisTurn);
		} catch (err) {
			console.error(`PI_OBSERVED_SYSTEM_PROMPT_FAILED=${String(err)}`);
		}
	});

	// REQUEST-LEVEL observation. `before_provider_request` fires once per
	// provider request with the exact payload about to be sent (for the
	// OpenAI-completions API: `payload.messages[0]` is the system/developer
	// message carrying the rendered prompt). The handler hashes that content
	// and RETURNS UNDEFINED, so the payload is never modified. If the payload
	// shape is not the one this harness pins (no leading system/developer
	// message), the observation is reported with an empty digest and the
	// shape named, which the harness treats as an absent request observation --
	// it is never filled in from the turn-start digest.
	let requestIndex = 0;
	pi.on("before_provider_request", async (event) => {
		const thisRequest = requestIndex++;
		try {
			const payload = (event as { payload?: unknown }).payload as
				| { messages?: Array<{ role?: string; content?: unknown }> }
				| undefined;
			const messages = Array.isArray(payload?.messages) ? payload!.messages! : [];
			const first = messages.length > 0 ? messages[0] : undefined;
			const role = typeof first?.role === "string" ? first.role : "";
			let sha256 = "";
			let shape = "unrecognised";
			if ((role === "system" || role === "developer") && typeof first?.content === "string") {
				sha256 = createHash("sha256").update(first.content, "utf8").digest("hex");
				shape = "openai_completions_leading_system_message";
			}
			await bridgeObserveRequest(sha256, thisRequest, role, messages.length, shape);
		} catch (err) {
			console.error(`PI_OBSERVED_REQUEST_SYSTEM_PROMPT_FAILED=${String(err)}`);
		}
		return undefined;
	});
}
