# M10 next step — `manager_proposal/v2-diff` wired into a manager and a campaign path (14 November 2026)

**AI-assisted (Claude, Mac-local agent). Synthetic tests only (fake CPU node, scripted or loopback LLM); no GPU, server or model.** Unit 3 of `prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md`, with the accepted review's interpretations S7b, S8 and S11. The author's answer to the 10 Nov question Q8 (M10 §5 questions 1–8, option (a) for all, start message of 13 Nov) accepts the repeated-timeout cap, so the cap is **on** in the v2-diff path.

## Commits

| Repo | Branch | Commit | Content |
|---|---|---|---|
| harness | `r1-local-trackg-v2-20261114` (from `r1-local-trackg-20261109` @ `76bc49f2`) | `776282e9` (first version), `717ad835df32bbe1047d032fb5bb8dde5384a258` (review round 1) | `src/autoresearch/trackg/manager_v2_diff.py`, `src/autoresearch/trackg/campaign_v2_diff.py`, `tests/trackg/test_trackg_campaign_v2_diff.py`; `runner.py` (a kit file added after `a3fedbb`) gains an `interpreter` parameter |
| paper | `mac-trackg-v2-20261114` (from `mac-trackg-20261109` @ `f56f7f35`) | this report | documentation only |

No file of the base `a3fedbb` changed (`git diff --diff-filter=MDRT --name-only a3fedbb 717ad835` is empty), and no module outside `src/autoresearch/trackg/` imports the package. The T0 test `tests/trackg/test_trackg_t0_identity.py` passes unchanged, both its byte-for-byte `manager_proposal/v1` probe and its structural test.

## The manager

**Which manager.** The kit had no LLM manager for Track G. Its smoke campaign (`autoresearch.trackg.smoke`) uses a fixed list of v2-diff proposals, and the v1 managers (`autoresearch.manager.LangGraphManager`) cannot take v2-diff: `autoresearch.llm.providers.manager_response_format` refuses every version except v1, and changing it would break T0 identity. So the wired manager is a new `V2DiffManager` inside `autoresearch.trackg`. It follows the smoke and runner conventions: proposals against the incumbent's code snapshot, run records through `manager_view`.

**What it sends and records.**
- Prompt `trackg_v2_diff_prompt/v1`:
  - the node's editable text files of the incumbent, chosen by the scope validator itself (`diff_support.editable_files`: a walk that does not follow directory links, keeping the paths `validate_edit_scope` accepts); symlinked files are skipped, so a link cannot bring a frozen or outside file into the prompt; each file is capped at 20,000 characters (there is no total cap: open item);
  - the metric name and direction, and the fixed run budget;
  - up to 12 earlier steps (summary, decision, validation value). The test metric is never shown.
- Request: the structure-only v2-diff `response_format`, `temperature` 0, a seed derived from the campaign seed and the step, and `max_tokens` 4096.
- Record: prompt SHA-256, the request without its messages (model, temperature, seed, max_tokens, response_format and any extra fields), the base seed, raw reply and its SHA-256, and usage. `extra_payload` may add fields (for example `cache_prompt: false`) but may not override the pinned ones.
- A reply that does not parse is an **invalid proposal**: charged, recorded with the parse error, never repaired. A transport failure raises `ManagerTransportStop`; the campaign writes a `stop_transport` ledger line and STOPs. (A server answering HTTP 400 for a prompt beyond its context is such a STOP today: open item, as for B1.)
- The transport is injectable. `openai_compatible_chat` is a stdlib HTTP transport for llama-server; it adds no dependency.

## The campaign path

`run_v2_diff_campaign(spec, node_dir, runs_root, manager, limits, budget, enable_v2_diff=True, timeout_cap=2, max_infra_reruns=2, interpreter="python3")`. **Without `enable_v2_diff=True` it refuses and creates nothing.** It runs the baseline first, with the same rerun and cap handling as a proposal; a baseline without an `ok` run writes `baseline_failed` and STOPs. Then `budget` manager calls:

| Situation | Decision |
|---|---|
| reply does not parse | `invalid_proposal` (charged; no run) |
| diff refused, inert or duplicate | `not_run_<status>` |
| `ok`, strictly better on validation | `kept`; the next incumbent is the run's pre-run code snapshot |
| `ok`, not better | `discarded` |
| `divergent` | `discarded_divergent` |
| `infrastructure_failure/timeout` | the same code state is rerun. **After 2 timeouts of the same code state:** `divergent` with reason `timeout_repeated`, registered as evaluated, so an identical code state later is a duplicate and is not run |
| any other `infrastructure_failure` (launch error, kill, an infrastructure log pattern such as Slurm's `DUE TO TIME LIMIT`) | rerun up to 2 times, then `infrastructure_failure_final` (not registered as evaluated, so it can be proposed and run again later, bounded by the manager budget). These reruns never count toward the timeout cap (review S8) |

The timeout count is per code state over the whole campaign: the second timeout may come in a later step. A diff seen before against another incumbent reaches a new code state and is run, with `seen_diff_other_incumbent` recorded (M10 §5 question 7, option (a)). Reruns do not consume manager calls. Each step appends one line to `campaign_ledger.jsonl` (never overwritten): the proposal, the manager call record, every run record of the step, the final outcome, the decision, and the incumbent and best value after the step.

## Tests

`tests/trackg/test_trackg_campaign_v2_diff.py`:
- the flag is required;
- baseline: rerun then `baseline_failed` STOP; an infrastructure failure followed by an `ok` baseline is used (no unconditional keep);
- a mixed campaign: kept, invalid, discarded, duplicate, divergent and inert steps, with ledger equality, the request fields and the history in later prompts without test metrics;
- the repeated-timeout cap with a real timeout of the fake node (two timeouts → `timeout_repeated`; the same diff proposed again is a duplicate);
- other infrastructure failures really rerun twice (outcomes scripted at the log-parsing step), then are final; a timeout, an infrastructure failure and a timeout of the same code state reach the cap;
- `extra_payload` cannot override pinned fields, and the request is recorded; a transport STOP leaves a ledger line;
- the prompt shows only editable files (a symlink to a frozen file and a `./`-prefixed frozen entry stay out);
- the loopback HTTP transport;
- a transport failure STOPs.

`PYTHONPATH=src pytest tests/trackg`: 173 passed (161 at `76bc49f2` plus 12 new), in `/tmp/trackg_venv`. Full harness suite (reviewer, round 1 head): 14 failed / 644 passed / 1 error against 14 / 637 / 1 at the base, with the identical 15-entry failure set listed in the 9 Nov hand-off.

## Open or not done

- **Inference parameters.** The prompt text and the budget of prompt context are a first version (`trackg_v2_diff_prompt/v1`). A real model's diffs may need more context per file or a different layout. Track G porting decides this, with the representative edits.
- **Server settings.** `cache_prompt` and any server-side reasoning settings are not set by default. A caller passes them through `extra_payload`, as the exam does with `cache_prompt: false`.
- **Interpreter.** The campaign passes the run's interpreter to the new-file shadowing check (`interpreter=`; kit review round 3 note); callers must set it when a node uses its own Python (for example `.venv/bin/python`).
- **No resume.** An HTCondor eviction of the job running the campaign ends it; a restart refuses the existing `runs_root`. Unit 2's resume-safe units are not wired in. HTCondor-level reasons (`htcondor_eviction`, …) do not reach this loop; they describe the job, not a run.
- **Walltime.** A proposal that hits a Slurm or HTCondor walltime before the runner timeout is an infrastructure failure bounded by `max_infra_reruns`, not by the timeout cap (HTC-Q1).
- **Not done.** No noise-aware keep rule, controller or observer: this is the closed-loop proposal path, not the label sweep. Wiring into `run_real_campaign` is not done, because it would change base files. The history shown to the model has no baseline or incumbent value line, and the prompt text and `finish_reason` are not stored (prompt design is for Track G porting).
