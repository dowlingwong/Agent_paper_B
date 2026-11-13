# M10 next step — `manager_proposal/v2-diff` wired into a manager and a campaign path (14 November 2026)

**AI-assisted (Claude, Mac-local agent). Synthetic tests only (fake CPU node, scripted or loopback LLM); no GPU, server or model.** Unit 3 of `prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md`, with the accepted review's interpretations S7b, S8 and S11. The author's answer to the 10 Nov question Q8 (M10 §5 questions 1–8, option (a) for all, start message of 13 Nov) accepts the repeated-timeout cap, so the cap is **on** in the v2-diff path.

## Commits

| Repo | Branch | Commit | Content |
|---|---|---|---|
| harness | `r1-local-trackg-v2-20261114` (from `r1-local-trackg-20261109` @ `76bc49f2`) | `776282e9424b39d95d06d976db1c6598a61899f8` | `src/autoresearch/trackg/manager_v2_diff.py`, `src/autoresearch/trackg/campaign_v2_diff.py`, `tests/trackg/test_trackg_campaign_v2_diff.py` |
| paper | `mac-trackg-v2-20261114` (from `mac-trackg-20261109` @ `f56f7f35`) | this report | documentation only |

No file of the base `a3fedbb` changed (`git diff --diff-filter=MDRT --name-only a3fedbb 776282e9` is empty), and no module outside `src/autoresearch/trackg/` imports the package. The T0 test `tests/trackg/test_trackg_t0_identity.py` passes unchanged, both its byte-for-byte `manager_proposal/v1` probe and its structural test.

## The manager

**Which manager.** The kit had no LLM manager for Track G. Its smoke campaign (`autoresearch.trackg.smoke`) uses a fixed list of v2-diff proposals, and the v1 managers (`autoresearch.manager.LangGraphManager`) cannot take v2-diff: `autoresearch.llm.providers.manager_response_format` refuses every version except v1, and changing it would break T0 identity. So the wired manager is a new `V2DiffManager` inside `autoresearch.trackg`. It follows the smoke and runner conventions: proposals against the incumbent's code snapshot, run records through `manager_view`.

**What it sends and records.**
- Prompt `trackg_v2_diff_prompt/v1`:
  - the node's editable text files of the incumbent (frozen files excluded; each file capped at 20,000 characters);
  - the metric name and direction, and the fixed run budget;
  - up to 12 earlier steps (summary, decision, validation value). The test metric is never shown.
- Request: the structure-only v2-diff `response_format`, `temperature` 0, a seed derived from the campaign seed and the step, and `max_tokens` 4096.
- Record: prompt SHA-256, seed, raw reply and its SHA-256, and usage.
- A reply that does not parse is an **invalid proposal**: charged, recorded with the parse error, never repaired. A transport failure is a STOP.
- The transport is injectable. `openai_compatible_chat` is a stdlib HTTP transport for llama-server; it adds no dependency.

## The campaign path

`run_v2_diff_campaign(spec, node_dir, runs_root, manager, limits, budget, enable_v2_diff=True, timeout_cap=2, max_infra_reruns=2)`. **Without `enable_v2_diff=True` it refuses and creates nothing.** It runs the baseline first, then `budget` manager calls:

| Situation | Decision |
|---|---|
| reply does not parse | `invalid_proposal` (charged; no run) |
| diff refused, inert or duplicate | `not_run_<status>` |
| `ok`, strictly better on validation | `kept`; the next incumbent is the run's pre-run code snapshot |
| `ok`, not better | `discarded` |
| `divergent` | `discarded_divergent` |
| `infrastructure_failure/timeout` | the same code state is rerun. **After 2 timeouts of the same code state:** `divergent` with reason `timeout_repeated`, registered as evaluated, so an identical code state later is a duplicate and is not run |
| any other `infrastructure_failure` (launch error, kill, log pattern, or an HTCondor-level reason such as `htcondor_eviction`) | rerun up to 2 times, then `infrastructure_failure_final`. These reruns never count toward the timeout cap (review S8) |

Reruns do not consume manager calls. Each step appends one line to `campaign_ledger.jsonl` (never overwritten): the proposal, the manager call record, every run record of the step, the final outcome, the decision, and the incumbent and best value after the step.

## Tests

`tests/trackg/test_trackg_campaign_v2_diff.py`:
- the flag is required;
- a mixed campaign: kept, invalid, discarded, duplicate, divergent and inert steps, with ledger equality, the request fields and the history in later prompts without test metrics;
- the repeated-timeout cap with a real timeout of the fake node (two timeouts → `timeout_repeated`; the same diff proposed again is a duplicate);
- other infrastructure failures rerun twice, then are final;
- the prompt shows only editable files;
- the loopback HTTP transport;
- a transport failure STOPs.

`PYTHONPATH=src pytest tests/trackg`: 168 passed (161 at `76bc49f2` plus 7 new), in `/tmp/trackg_venv`.

## Open or not done

- **Inference parameters.** The prompt text and the budget of prompt context are a first version (`trackg_v2_diff_prompt/v1`). A real model's diffs may need more context per file or a different layout. Track G porting decides this, with the representative edits.
- **Server settings.** `cache_prompt` and any server-side reasoning settings are not set by default. A caller passes them through `extra_payload`, as the exam does with `cache_prompt: false`.
- **Not done.** No noise-aware keep rule, controller or observer: this is the closed-loop proposal path, not the label sweep. Wiring into `run_real_campaign` is not done, because it would change base files.
