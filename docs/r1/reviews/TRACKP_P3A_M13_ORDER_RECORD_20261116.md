# M13 — P.3a attempt-1 serialisation template order/version: determination and attempt-2 recording mechanism (16 November 2026)

**Reviewer/analyst:** independent reviewer (M13; no part in drafting the attempt-2 plan, the attempt-1 export or the
code under review). **Read-only local analysis.** No model, tokenizer, GPU, training or probe code was executed; no
host (TASL-7 or otherwise) was written, signalled or contacted; no git write, commit, merge or push was made. The
only actions were reads, `shasum -a 256`, `git cat-file`/`git rev-parse` (read-only object reads in the local repo)
and Python standard-library parsing/hashing of the exported bytes. Attempt 1 stays preserved and unmodified.

**Status: this is the M13 order/version record required by Unit A.** It does not authorize Unit B, A6, a P.3a
re-run, or any code change. Verdict at the end.

**Canonical bytes.**
- Repo `/Users/wongdowling/Documents/agent_paper_B`; branch `origin/ops-tasl-20261116` @ **`8db32cf5`**
  (`8db32cf5b9acc4d18fb9cf3a839ac820a1c64bd6`, "P.3a attempt-1 inventory export + Unit A execution record
  (M13/order input)"); worktree `.claude-worktrees/ops-tasl-20261116` (clean before this uncommitted record).
- Exported attempt-1 inventory: `docs/r1/reports/trackp_p3a_attempt1_inventory_20261116/` — **243 files**,
  `SHA256SUMS` sha256 **`5c35ef2b9bf148ca4d73b28aa195ec2e439fd5f877559a7c85a3d3e6a291f950`** (242 entries).
  **Integrity re-verified here:** all 242 entries hash to the recorded digest (0 bad) and the 242 listed paths are
  exactly the 242 files present besides `SHA256SUMS` (no unlisted, no missing).
- Attempt-1 artifacts in the export: `runs/p3a_operator_20261027/` (129 `manifest.json`, 39 `report.json`,
  5 `probes.stdout.log`, `journal.jsonl` 81 lines, `gpu_lease_log.jsonl` 111 lines, launch log, launch script);
  pinned source at `Agent_paper_B/r1/…`; installed Kev encoder `venvs/trackp-gpu/lib/python3.12/site-packages/kev`
  + `kev-0.1.0.dist-info`.
- Cited committed docs (sha256 at this worktree): M13 inventory `docs/r1/reports/MAC_M13_TEMPLATE_INVENTORY_20261105.md`
  `b8f4c8ef…`; spec `docs/r1/TRACK_P_POST_TRAINING.md` `2fa74132…`; PLAN `docs/r1/PLAN.md` `b8581212…`;
  accepted Unit A review `docs/r1/reviews/TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md` `94d4c1de…` (444 lines);
  attempt-2 plan `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md` `8fcb37cc…` (131 lines);
  amendment `docs/r1/authorizations/trackp_p3a_amend_20261104.md` `cd867e95…`; Unit A execution record
  `docs/r1/reports/TRACKP_P3A_ATTEMPT1_INVENTORY_RESULT_20261116.md` `95560838…`.

---

## 0. Bottom line

1. **Attempt 1 ran the pinned source `b9ad6f8f` clean, not a later tree.** All 39 run manifests and the
   `campaign_start` journal record paper `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` on `trackp-20261026`,
   `dirty: false` (39/39); the exported pinned source files are **byte-identical to the `b9ad6f8f` git blobs**
   (11/11 compared, see §1.3). So the exported source *is* the attempt-1 source.
2. **The four-base pool used exactly two wrapper families**, not one template: `kev-0.8b` / `kev-4b` →
   `PointerWrapper` (Kev pointer frame, encoded by `kev.model.encode` @ `2074cc44`); `qwen3.5-0.8b-base` /
   `qwen3.5-4b-base` → `BinTokenWrapper` (Qwen bin-token frame). The journal confirms only these four bases
   started; no `laya`/`startlux` unit exists.
3. **Order: history-first for both families of the four-base pool.** In every case the loop state — whose text
   contains the ledger history, oldest first — is encoded **before** the proposal, and the proposal is the first
   content of the family's branch/prefix after the state. **No attempt-1 base is proposal-first.** However, the
   literal "proposal immediately before `<decide>`" form is **not** what attempt 1 rendered: Kev's fixed frame puts
   the question text and the 12 option spans between the proposal and the `<decide>` token
   (`<|fim_suffix|>`), and the Qwen frame puts the question and the listed bins between the proposal and the
   `Belief:`/`Action:` readout positions and has **no `<decide>` token at all**. So attempt 1 is
   **history-before-proposal**, not **decide-adjacent** (§2.6 states this precisely; it is the one interpretation
   point that could still matter).
4. **Version:** the only version string in the pinned code is `PROMPT_VERSION = "trackp_prompt/v1"`
   (`r1/c3/train/types.py:26`). The wrappers **never read it**; it is written only into `serialize_view`'s
   `DecisionPrompt.meta` (`serialize.py:204`), a path the P.3a E0/probes flow does not use (`exam_synthetic`
   builds prompts directly and the built-in E0 rows carry no `meta`). The attempt-1 template is therefore
   **`trackp_prompt/v1`, as rendered by the two family wrappers at `b9ad6f8f`** — the version string is shared,
   the order is wrapper-level (exactly M13's warning).
5. **Attempt 1 recorded nothing that pins this.** 0 of the 168 exported run artifacts (129 manifests + 39 reports)
   contains a prompt/template/serialisation version field; the journal (81 lines) and lease log (111 lines) contain
   none either; the 4 probes manifests have `model_files_sha256: {}` (and `data_manifest_sha256` = the empty-list
   hash `e3b0c442…`). Attempt 1's order/version is **derived from source by provenance**, not read from a run-time
   field (§2.7).
6. **A6 is unimplemented** (`exam_run.py` has no A6; spec marks it "(proposed)"). A6 would have to compare two
   renders of the *same* states, but its spec-defined arms ("proposal immediately before `<decide>`" vs
   "proposal-first") do not map cleanly onto either attempt-1 family frame (§4).
7. **Verdict: `Verdict: accepted`** for closing M13 for Unit A purposes: the order/version *is* determinable from
   the exported bytes, the negative recording fact is established, and a concrete, fail-closed attempt-2 recording
   mechanism (sidecar + journal + retro-tag) is specified. Residual risks and the exact interpretation gap are in
   §5; the mechanism is a specification (implementation/testing belongs to the reviewed probes-only runner unit).

---

## 1. Evidence base and provenance chain

### 1.1 What pins the attempt-1 launch (run-time evidence)

| Claim | Evidence in the export |
|---|---|
| Paper commit `b9ad6f8f`, branch `trackp-20261026`, clean | `git.paper` in **39/39** run manifests; `campaign_start.pins.paper` in `journal.jsonl`; `preflight.txt` (`capture_utc=2026-11-16T10:13:36Z`, attempt-1 checkout still at `b9ad6f8f` clean) |
| Harness `897d83c8`, clean | `git.harness` in 39/39 manifests; `campaign_start.pins.harness` |
| All 39 units used one identical resolved config | `config_sha256` = `64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c` in 39/39; the config bytes are exported (`r1/scripts/configs/trackp_portal.json`, sha `049bafed…`) |
| Pinned Kev encoder `2074cc44…` | `environment.packages.kev.pip_commit` in 39/39; installed-dist `direct_url.json`; `uv pip freeze` line 38 of `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt` |
| Same host/boot as the preflight | `tasl7_driver.boot_id` = `2c9bb104-cc3c-4c60-be67-c1c8f0287fe4` in 39/39 manifests |
| Launch route | `runs/p3a_operator_20261027.sh` (sha `6fc8f4cb…`): `cd /home/dowling/r1_trackp/Agent_paper_B`, then `venvs/trackp-gpu/bin/python -m r1.scripts.trackp_p3a_guarded --root …/p3a_operator_20261027` |
| Fail-closed pins during the run | `trackp_p3a_guarded.py` `verify_pins` (26–58) and `verify_live_pins` (86–96) re-check paper/harness commits and cleanliness before **every** unit; `run_unit` (166–293) re-checks boot id (168–169) and manifest label/boot/lease (276–288) |

`journal.jsonl` (sha `1e73e80f…`, 81 lines) events: 1 `campaign_start`, **40 `unit_start`**, **39 `unit_complete`**,
1 `STOP`. Units started per label/base: DRYRUN `kev-0.8b` 8; EVIDENCE `kev-0.8b` 8, `kev-4b` 8,
`qwen3.5-0.8b-base` 8, `qwen3.5-4b-base` 8 (the 8th — `probes` — failed: the 4b OOM STOP). No other base started.
The interrupted 4b `probes` unit wrote **no** `manifest.json`/`report.json` (its `unit_start.argv` is recorded; the
failure is in `probes.stdout.log`); that is a missing artifact in attempt 1, not an M13 evidence gap — it ran the
same pinned code as the three completed probes units.

### 1.2 What pins the exported source to the commit (decisive check)

The R2 review notes the `b9ad6f8f` object is present locally (`origin/trackp-20261026`). I compared each exported
pinned-source file against `git cat-file blob b9ad6f8f:<path>`: **11/11 byte-identical** (sha256 below). Combined
with "the run's paper checkout was clean at `b9ad6f8f` throughout" (§1.1), this closes the chain
**run code = commit `b9ad6f8f` = exported bytes**. No inference about the run's code text is needed.

| File (pinned source used here) | sha256 (exported = `b9ad6f8f` blob) |
|---|---|
| `r1/c3/train/types.py` | `7b7c1a01029f967c79c217e15338bdb2eb68364329b385f383fad25d933c8008` |
| `r1/c3/train/serialize.py` | `bf58b3f0b36b6bdf3cd860d0547473f66a4138eddde36dc7cb6cf5bbea8894b6` |
| `r1/c3/train/model.py` | `82f815569a062059f9a7bb791cf45926ff7faa6e3bbb64dd91601ca01e886933` |
| `r1/c3/train/exam_run.py` | `88afa4915612d978065d62e9ba2af666673c55d4c3980dd924bd51391cc37f84` |
| `r1/c3/train/exam_synthetic.py` | `6c9004ae8fd5c537c21ef5a01ca34664e936dcec60701a608dc4b1505e0372cb` |
| `r1/c3/train/registry.yaml` | `e60cdb28580785ab7341ad8191b0e78f7212c6868829dec4a419407e48fd4371` |
| `r1/scripts/trackp.py` | `2d3aeef6268a7700f31203d570b016ffda88ee38ce7dcb91927f0f1e2a942ab1` |
| `r1/scripts/trackp_p3a_guarded.py` | `169ab361efed44b8a2f0d77ca64a470522f702b09b09204833c6e0ee0c85270d` |
| `r1/scripts/trackp_p3a_watchdog.py` | `98a4d0b607561af3b48440c2cbbfd25c0ce6f45af14b981550748124f57858a8` |
| `r1/scripts/configs/trackp_portal.json` | `049bafede821e9a15b38cdfc96b9198f1d1cbdd63153dced25250e045e71c2f7` |
| `r1/c3/train/data/e0_v1.jsonl.gz` | `4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290` |

Note: current worktree HEAD (`8db32cf5`) has *different* `r1/c3/train/model.py` (`d53a5260…`) and `r1/scripts/trackp.py`
(`ecb71742…`) than the pin; the exported copies are the pinned ones. This is exactly why the export was required and
why this record uses the exported bytes, not the current tree.

### 1.3 Installed Kev encoder (external dependency)

- `kev-0.1.0.dist-info/direct_url.json`: `https://github.com/jaredpalmer/kev`,
  `commit_id 2074cc44256200bb37540103fa4572901faa10f3`; `METADATA` version `0.1.0`; matches the 39 manifests'
  `environment.packages.kev.pip_commit` and the recorded freeze.
- **Install integrity re-verified:** all 41 hashed entries in `kev-0.1.0.dist-info/RECORD` hash to the recorded
  values (0 bad), i.e. the installed package tree is unmodified since install.
- Files used for the token-stream determination (export-relative):
  `…/venvs/trackp-gpu/lib/python3.12/site-packages/kev/model.py` sha256
  `2ff3b2e67c048e3bc5a0d1a32aafe50804ed315a5564fce06bb4b95697c5271c` (508 lines);
  `kev/__init__.py` is empty (`e3b0c442…`).
- **Residual (stated, not hidden):** the up-stream git object `2074cc44` is not available locally, so the installed
  `kev/model.py` is not byte-compared to its GitHub commit here; the pin rests on `direct_url.json` + freeze +
  RECORD integrity, and on the wrapper's call site agreeing with the framing below. This does not affect the
  determination (the framing used is read from the installed file itself, which the manifests pin).

### 1.4 E0 data (the text every wrapper consumes)

`r1/c3/train/data/e0_v1.jsonl.gz` (sha `4f4db29b…`) — re-parsed here: **4,000 rows**, all `version =
"trackp_e0/v1"`, 3,000 train / 1,000 test, prompt keys exactly `group, options, proposal, question, state`, **no
`meta` and no `prompt_version` anywhere**. Example row 0 (excerpt, verbatim):

```
state:     Node: openml_sonar (…)
           Metric: val_auc …; noise level sigma_node = 0.016
           Memory: append_only_summary
           Budget: trial 6 of 10 (5 worker runs left before this trial)
           Incumbent configuration (active keys): C=0.01, … 
           Incumbent metric: 0.98403; recorded gain since the first valid trial: z = +0.68
           History (oldest first):
           t1: max_iter 1500 -> 1500; discarded, z +0.20
           …
proposal:  Edit: scaler: none -> standard (file config.yaml)
           Forecast note: … / Edited key is active … / …
question:  How much will this proposed edit change the validation metric, …
options:   12 entries (`BIN_OPTIONS`, canonical order)
```

So the **history is inside `state`** (oldest first) and the **proposal is a separate field**; every wrapper below
places `state` first. This is direct artifact evidence of the text layer. (`exam_synthetic.py:181–190` built these
prompts with `state_text` from `serialize.py:125–127`; `E0_VERSION` is a **dataset** label, not a serializer or
wrapper version — M13's point stands.)

---

## 2. Attempt-1 template order/version per family (M13's question)

### 2.1 The shared version string and what it does *not* establish

- `PROMPT_VERSION = "trackp_prompt/v1"` — `r1/c3/train/types.py:26`; also `MAX_TOKENS = 1024` (:27),
  `BIN_OPTIONS` fixed order (:17–21), `QUESTION` (:23–24).
- Its **only** use in the pinned code: `serialize.py:35` (import) and `serialize.py:204`
  (`info = {"prompt_version": PROMPT_VERSION, …}` inside `serialize_view`'s returned `DecisionPrompt.meta`).
- `model.py` never imports or reads `PROMPT_VERSION` (grep over the exported source: no other reference). There is
  no template-version field in the model, in `describe()`/`save()` (`model.py:180–199`), in `trackp.py`'s manifest
  path, or in the guarded supervisor's journal.
- The P.3a E0/probes flow does **not** go through `serialize_view`: `exam_run.e0_rows`/`rows_of_items` rebuild
  `DecisionPrompt`s from the E0 dicts (`exam_synthetic.prompt_from_dict`, `exam_synthetic.py:197–199`) with
  `meta={}`, and the E0 dicts have no `meta`. So even the in-memory `prompt_version` is absent on this path.
- **Conclusion:** `trackp_prompt/v1` names the *shared neutral text template* (`serialize.render_text`,
  `serialize.py:130–133`: state → proposal → question → options), not the model's actual token order. The model
  order is decided entirely by each wrapper (`model.py`) and, for Kev, by `kev.model.encode`. This is exactly the
  "shared version string ≠ wrapper-level order" warning in M13.

### 2.2 Kev family — `kev-0.8b`, `kev-4b` (`PointerWrapper` + `kev.model.encode`)

Config mapping: `trackp_portal.json` bases `kev-0.8b`/`kev-4b` → `family "kev"`; `build_model` dispatches
`"kev" → PointerWrapper` (`model.py:769–770`). Wrapper records:

```
model.py:294–309  records():
  recs.append({"state": p.state, "questions": []})            # :302  Kev *state* = the loop state (history inside)
  q = {"instr": f"{p.proposal}\n\n{p.question}", "options": list(p.options), "label": 0}   # :306
model.py:311–315  forward(): km.encode(self.tok, rec, max_state=ctx["max_state"], max_branch=ctx["max_branch"], strict=True)
model.py:317      rows_form(encs): True for hybrid backbones (all four bases are Qwen3.5 hybrids)
model.py:275      self.packing = not self.kev.hybrid  → False
```

The encoder (`kev/model.py:87–127`) packs `[<state> …]` then each question `[<q> instr <opt> o </opt>… <decide>]`:

```
kev/model.py:9–11  SPECIAL = [<|fim_prefix|>, <|fim_middle|>, <|box_start|>, <|box_end|>, <|fim_suffix|>]
                   = [<state>,          <q>,            <opt>,             </opt>,            <decide>]
kev/model.py:104   S  = [<|fim_prefix|>] + tokenize(rec["state"])[: max_state-1]
kev/model.py:109   instr = [<|fim_middle|>] + tokenize(q["instr"])           # instr = proposal + "\n\n" + question
kev/model.py:110   spans = [[<|box_start|>] + tokenize(option_k) + [<|box_end|>] for k in 0..11]
kev/model.py:111   branch = instr + concat(spans) + [<|fim_suffix|>]         # <|fim_suffix|> = <decide>, last token
kev/model.py:124–125  ids += branch; decide_idx = last token; opt_idx = each </opt> token
kev/model.py:188–201, 329–333  rows form (hybrid): row = state tokens + branch tokens, positions continued;
                   readout = <|fim_suffix|> hidden state scored by the pointer head against each </opt> state
```

**Actual token stream per prompt (Kev, attempt 1):**

```
<|fim_prefix|>  NODE/BUDGET/INCUMBENT/HISTORY-oldest-first  …  <|fim_middle|>
PROPOSAL  \n\n  QUESTION
  <|box_start|> option_0 <|box_end|>  …  <|box_start|> option_11 <|box_end|>
<|fim_suffix|>   ← the <decide> token; the pointer readout
```

Order: **history-first** (the history-bearing state is the longest prefix, before the proposal); the proposal is
the first content of the question branch, i.e. **after** the history and immediately after `<|fim_middle|>`; it is
then followed by the question text and the 12 option spans before `<decide>`. Therefore: **not proposal-first**,
but also **not "proposal immediately before `<decide>`"** — the family frame interposes the question and the option
list. Limits/positions: `max_state=1024` and `training_context(1024) → max_branch=1664` (wrapper default
`max_state=1024`, `model.py:249`; `kev/model.py:31–38`), `strict=True`; the E0 histories are short (≤12 lines), so
the state limit is not expected to bind, and `encode` cuts state only in non-strict mode (`kev/model.py:98–104`).

### 2.3 Qwen control family — `qwen3.5-0.8b-base`, `qwen3.5-4b-base` (`BinTokenWrapper`)

Config mapping: `family "qwen_control"` → `build_model` dispatches to `BinTokenWrapper` (`model.py:782–796`).

```
model.py:642–647  prefix(): lines = [p.state, "", "Proposed edit:", p.proposal, "", f"Question: {p.question}"]
                  if self.list_bins: lines += ["Bins:"] + [f"{BIN_TOKENS[k]} {p.options[k]}" for k in self.bin_order]
                  return "\n".join(lines) + "\n"
model.py:649–662  segments(): ids = tokenize(prefix) ; ids += tokenize("Belief:"); belief_pos = last token of "Belief:"
                  ids += tokenize("\nAction:") ; action_pos = last token
model.py:594–609  list_bins default True; bin_order default list(range(12)) → canonical order
model.py:588–590, 70–71  reserved tokens <b0>…<b11>, <exec>, <skip> (no <decide> token exists in this frame)
```

**Actual token stream per prompt (Qwen, attempt 1):**

```
NODE/BUDGET/INCUMBENT/HISTORY-oldest-first   …(state text)…
\n\nProposed edit:\nPROPOSAL
\n\nQuestion: QUESTION\nBins:\n<b0> option_0\n…\n<b11> option_11\n
Belief:          ← belief position (LM head restricted to <b0>…<b11>)
\nAction:        ← action position (logit <exec> − logit <skip>)
```

Order: **history-first** (state, which contains the history, comes first), proposal second, then question, the 12
listed bins, then the readout positions. **Not proposal-first**, and **not decide-adjacent** (there is no
`<decide>`; the question/bins intervene).

### 2.4 Per-family table (the four-base pool actually run)

| Base (attempt 1) | Family / wrapper | Pinned frame | Field order in the model's token stream | Readout position | Order class | Version string | Decide-adjacent? |
|---|---|---|---|---|---|---|---|
| `kev-0.8b` | `kev` / `PointerWrapper` + `kev.model.encode` | Kev record: `state` + question `instr`/options | `<|fim_prefix|>` state(node,budget,incumbent,history-oldest-first) → `<|fim_middle|>` → **proposal** → question → 12×(`<|box_start|>` option `<|box_end|>`) → `<|fim_suffix|>` | `<|fim_suffix|>` = `<decide>`; options read at `</opt>` | **history_first** | `trackp_prompt/v1` | No (question + 12 option spans between) |
| `kev-4b` | `kev` / `PointerWrapper` + `kev.model.encode` | same | same | same | **history_first** | `trackp_prompt/v1` | No |
| `qwen3.5-0.8b-base` | `qwen_control` / `BinTokenWrapper` | Qwen prefix: state, edit, question, bins, Belief/Action | state(…history…) → "Proposed edit:" → **proposal** → question → `Bins:` 12×`<bk> option` → `Belief:` → `\nAction:` | last token of `Belief:`; action at last token of `\nAction:` | **history_first** | `trackp_prompt/v1` | No (no `<decide>`; question/bins between) |
| `qwen3.5-4b-base` | `qwen_control` / `BinTokenWrapper` | same | same | same | **history_first** | `trackp_prompt/v1` | No |

Why all four are "hybrid/rows" for Kev: every base is a Qwen3.5 model with Gated DeltaNet layers, so
`kev.model.is_hybrid` is true (`kev/model.py:69–72, 262–263, 329–333`), `PointerWrapper` builds with
`packing=False`, and each question runs as its own causal row (state + branch). The attempt-1 saved-model manifests
independently record `kev_hybrid: true` for all 54 saved/checkpoint kev manifests and
`bin_order: [0..11], list_bins: true` for all 36 qwen saved/checkpoint manifests — i.e. the wrapper
*configuration* is partly pinned by the saved artifacts even though the *order* is not.

### 2.5 Why the two-family scope is complete for the four-base pool

`R1-C3-POOL` / `R1-C3-POOL-EXAM` fix the P.3a pool at these four bases; the attempt-1 journal confirms only these
four bases started (the pinned supervisor's `BASES` tuple still lists `laya` and the three StartLux bases,
`trackp_p3a_guarded.py:20–21`, but the run STOPped at `qwen3.5-4b-base/probes` before reaching them). So M13's
"per family" for the preserved attempt is exactly the two families above. For completeness only: the unexecuted
wrappers are also family-specific — `LayaWrapper.state_text` puts the proposal **before** state
(`model.py:394–396`), `StartLuxWrapper.prompt_text` puts state before the edit (`model.py:552–556`) — further
evidence that the shared version string does not imply a universal order.

### 2.6 What attempt 1's manifests do and do not record

**Do not record (the negative fact):**
- 0 of the **129** `manifest.json` + **39** `report.json` (168 JSON run artifacts) contain any field or string
  matching `prompt_version`, `template_version`, `serialisation`/`serialization`, `template`, `trackp_prompt`, or
  an order field. Journal (81 lines) and lease log (111 lines): same, 0.
- The 4 `probes` run manifests have **`model_files_sha256: {}`** and `data_manifest_sha256 =
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (sha of the empty data list). 9 manifests total
  have empty `model_files_sha256` (4 probes + 5 CPU-only `e0-select`); 30 e0 manifests have it populated.
- The attempted-but-failed `qwen3.5-4b-base/probes` unit has no manifest at all (no write before the OOM).
- No run-time rendered prompt / token-id capture exists anywhere in the export (no log line contains
  `Proposed edit`, `History (oldest first)`, `<|fim_prefix|>`, `Bins:` or `Belief:`); the 5 `probes.stdout.log`
  files contain the printed report plus loader output (and, for 4b, the OOM traceback) — no rendered
  prompt bytes.

**Do record (usable provenance):**
- Paper commit + branch + clean (39/39), harness commit + clean (39/39), one `config_sha256` (39/39), host boot id
  (39/39), environment package commits including `kev 2074cc44` (39/39), per-unit `argv`, and `head_form`
  (`linear12` for e0-fresh and probes; `softmax12` for native/select) — via `trackp.py:317` `extra` and
  `run_manifest`'s v1 fields.
- The E0 dataset bytes (sha `4f4db29b…`) whose rows show history inside `state` and proposal separate (§1.4).
- The **saved-model manifests** (`model.py:180–199` `describe()`): family, `model_version: trackp_model/v1`,
  `head_form`, `action_head`, plus `kev_hybrid/pointer_temperature/released_temperature` (kev) or
  `list_bins/bin_order` (qwen). For every base, `EVIDENCE/<base>/final/saved/manifest.json["files"]` **equals**
  `EVIDENCE/<base>/final/manifest.json["model_files_sha256"]` — so attempt-2 can bind the loaded attempt-1 model
  to attempt-1's recorded hashes even though the probes manifest itself has `{}`.

### 2.7 Established vs. inferred (precisely what the evidence supports)

| Statement | Status |
|---|---|
| Attempt 1 ran `b9ad6f8f` clean; the exported source equals that commit's bytes | **Established** (39/39 manifests + campaign_start; git blob equality 11/11) |
| `PROMPT_VERSION = "trackp_prompt/v1"`; it is never consumed by any wrapper | **Established** (source; no other reference) |
| E0 prompt text has history inside `state` (oldest first), proposal separate, no version field | **Established** (dataset bytes: 4,000 rows parsed, sha `4f4db29b…`) |
| Kev stream = state → `<q>` → proposal → question → 12 options → `<decide>` | **Determined from source** (`model.py:294–336` + installed `kev/model.py:87–127`, pinned by manifest/commit + RECORD); no run-time token capture exists |
| Qwen stream = state → proposal → question → bins → `Belief:`/`Action:` | **Determined from source** (`model.py:589–703`); no run-time capture exists |
| Attempt 1 is *history-before-proposal* for all four bases; no base is proposal-first | **Determined from source** (strong: deterministic code, pinned commit, clean trees) |
| Attempt 1 satisfies the literal "proposal immediately before `<decide>`" | **False for both families** (question/options interposed; Qwen has no `<decide>`) — see §5 R3 |
| The Kev installed bytes equal upstream `2074cc44` | **Not byte-verified locally** (no local git object); pinned by dist metadata + freeze + RECORD integrity |

No source randomness, branching or configuration switch changes the order: `records()`/`prefix()` are pure string
constructions; `build_model` dispatch is fixed by config family; `head_form`/`target`/`stage`/`list_bins` do not
reorder state vs proposal (only `bin_order`, which is canonical in every saved manifest, and the A5 probe, which
temporarily permutes it and restores it in `finally`, `exam_run.py:305–318`). The only way the order could differ is
if the run's code differed from the commit — excluded by §1.1–1.2.

---

## 3. Attempt-2 recording mechanism

### 3.1 Requirements and design principles

Sources: amendment `trackp_p3a_amend_20261104.md:19` ("Every P.3a result records the serialisation template version
it used (R1-P3A-OOM-OPTION3 (G2))"); PLAN `R1-P3A-OOM-OPTION3` (G2) at `PLAN.md:778`; spec §2.2
(`TRACK_P_POST_TRAINING.md:90`, "The template carries a version field") and §5.6 A6 (`:305`); attempt-2 plan §1a
and §1c.2 (`TRACKP_P3A_ATTEMPT2_20261116.md:31–45, 64–84`); R2 review conditions 3–5
(`TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md:379–386`).

Principles:
1. **Attempt 2 runs the attempt-1 template** (round-1 MAJOR-1 fix (i); no 4-Nov-order code is in the run pin), so
   the recorded attempt-2 `template_id` must equal the retro-tagged attempt-1 `template_id`, and the record says so
   explicitly.
2. **Declared, not inferred at read time**: the order class and frame id come from a reviewed constant table that
   a golden test pins to the actual rendered token stream, not from an eye-balled doc or from `PROMPT_VERSION`
   alone.
3. **Per result, not just per campaign**: every attempt-2 unit directory gets the field (sidecar), and the journal
   every unit references it by identity and hash. Fail closed on disagreement.
4. **The probe unit cannot mutate or rewrite the child's `manifest.json`/`report.json`** (preserve outputs); the
   field goes in a separate reviewed sidecar written by the reviewed probes-only runner.
5. **Attempt 1 is never edited**; its order/version is attached as a clearly-labelled *derived* provenance record.

### 3.2 New artifact: per-result sidecar `runner_manifest.json` (schema `trackp_p3a_unit_manifest/v1`)

Written by the reviewed probes-only runner **after** the child `trackp.py probes` process exits 0 and after it has
re-read the child `manifest.json`/`report.json` (finite-JSON check as in `trackp_p3a_guarded.py:61–76`), **before**
the runner emits journal `unit_complete`. Any failure to obtain a value is a fail-closed STOP.

| Field | Value source | When written / rule |
|---|---|---|
| `schema` | literal `"trackp_p3a_unit_manifest/v1"` | unit start (constant) |
| `unit` = `{label, base, unit, run_dir}` | runner's own arguments + child path | after child exit 0 |
| `attempt2_template.version` | **imported** `r1.c3.train.types.PROMPT_VERSION` (not a literal copy) — `types.py:26` | after child exit; also asserted equal to the campaign value |
| `attempt2_template.version_source` | literal `"r1/c3/train/types.py:26"` | same |
| `attempt2_template.family` | `base.family` from the child manifest (`kev` / `qwen_control`) | same |
| `attempt2_template.frame` | reviewed constant table keyed by family: `kev_pointer_v1` / `qwen_bintoken_v1`; golden test compares a fixed `DecisionPrompt`'s rendered token ids to the declared field order | same; mismatch = STOP |
| `attempt2_template.order` | declared constant `history_first` (a full reorder would be a new template id and a different, separately authorized unit) | same |
| `attempt2_template.field_order` | declared per frame: `["state","proposal","question","options","decide"]` (kev) / `["state","proposal","question","bins","belief","action"]` (qwen) | same |
| `attempt2_template.readout` | `kev.model.encode`'s `<decide>` token (`<|fim_suffix|>`) / `Belief:`+`\nAction:` positions; source `kev/model.py:104–111, 125` and `model.py:649–662` | same |
| `attempt2_template.encoder` | kev: `{"kind":"kev.model.encode","repo":"jaredpalmer/kev","commit":<manifest environment.packages.kev.pip_commit>,"kev_model_sha256":<hash>}`; qwen: `{"kind":"transformers","version":<child manifest environment.transformers>,"tokenizer_repo":<base.base_repo>,"tokenizer_revision":<base.base_revision>}` | after child exit; kev hash computed by the runner over the installed `kev/model.py` |
| `attempt2_template.wrapper_config` | `kev_hybrid/pointer_temperature` (kev) or `list_bins/bin_order` (qwen), from the loaded model's `describe()`/attempt-1 saved manifest | after load; must match the pinned values |
| `attempt2_template.template_id` | composed: `trackp_prompt/v1/<frame>/<order>/<encoder id>` e.g. `trackp_prompt/v1/kev_pointer_v1/history_first/kev@2074cc44…` | same |
| `attempt1_provenance.root` | literal attempt-1 root `/home/dowling/r1_trackp/runs/p3a_operator_20261027` | campaign start (constant) |
| `attempt1_provenance.journal_sha256` / `.lease_log_sha256` | computed from the preserved attempt-1 files read-only | at campaign start; recorded once |
| `attempt1_provenance.paper_commit` / `.paper_branch` / `.paper_dirty` | attempt-1 `campaign_start.pins.paper` (verified against all 39 manifests) | campaign start |
| `attempt1_provenance.loaded_artifact` | for `probes` units: the attempt-1 `EVIDENCE/<base>/final/saved` directory path from `--load`; `null` otherwise | after args parse |
| `attempt1_provenance.loaded_model_files_sha256` | `EVIDENCE/<base>/final/saved/manifest.json["files"]` cross-checked against `EVIDENCE/<base>/final/manifest.json["model_files_sha256"]`, then re-hashed from disk; mismatch = STOP | unit start (this is the plan §1c.2 "attempt-1 input binding" that attempt 1's `probes` manifest lacked) |
| `attempt1_provenance.derived_prompt_version` | `"trackp_prompt/v1"` (from this record) | campaign start |
| `attempt1_provenance.derived_order` | `"history_first"` (from this record) | campaign start |
| `attempt1_provenance.derived_template_id` | same composite string as `attempt2_template.template_id` | campaign start |
| `attempt1_provenance.recorded_at_run_time` | **`false`** (Boolean; attempt 1 had no such field) | campaign start |
| `attempt1_provenance.derivation` | `{"doc":"docs/r1/reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md","sha256":<this file>}` | campaign start |
| `attempt1_provenance.label` | literal `"derived"` | campaign start |
| `inputs.child_manifest_sha256` / `.child_report_sha256` | hash of the child's own artifacts | after child exit |
| `inputs.authorization_amend_sha256` | `cd867e95ddab0525827a48d68ea570743977bbf1b6ea819fefb98b3cf460f32d` (must equal the expected pin) | unit start |
| `created_utc` | runner clock | after child exit |

### 3.3 Journal fields (attempt-2 `journal.jsonl`)

| Event | Added fields | Value source / when |
|---|---|---|
| `campaign_start` | `serialisation_schema: "trackp_p3a_unit_manifest/v1"`, `template: {…}` (same block as §3.2 `attempt2_template`, computed once from the reviewed commit before any unit), `attempt1_provenance: {…}` (§3.2 block) | once, immediately after `verify_pins` and before the first `unit_start` |
| `unit_start` | `template_id` (string), `attempt1_input` = `{root, loaded_artifact, loaded_model_files_sha256}` or `null` | per unit, before spawning the child |
| `unit_complete` | `template_id`, `runner_manifest_sha256` (hash of the sidecar) | per unit, after sidecar write + re-read verification |
| `STOP` | `template_id` | on any STOP, alongside the existing error fields |

The runner must re-verify at each `unit_start` that the campaign `template`/`attempt1_provenance` blocks still equal
a freshly recomputed value (same idea as `verify_live_pins`, `trackp_p3a_guarded.py:86–96`); mismatch = STOP.

### 3.4 Code locations to populate (specification only — no code written here)

| Location | What goes there |
|---|---|
| `r1/c3/train/types.py:26` | Existing single source of the version string. Optionally add a companion declared order/frame map here (or in `model.py` next to the wrappers) so the sidecar value is produced by the same module that defines the template; no change is needed to make attempt 2 valid — the runner may import `PROMPT_VERSION`. |
| `r1/c3/train/serialize.py:130–133` (`render_text`) and `:204` (`prompt_version` in `meta`) | The neutral text order. If a first-class field is wanted later, `render_text`'s declared order is the natural place for a `render_order()`/`template_descriptor()` helper. Not required for the sidecar route. |
| `r1/c3/train/model.py:180–182` (`_Wrapper.describe()`), `:283–286` (`PointerWrapper.describe()`), `:639–640` (`BinTokenWrapper.describe()`) | The wrapper attributes the sidecar copies (`family`, `model_version`, `kev_hybrid`, `pointer_temperature`, `list_bins`, `bin_order`). The **declared frame table** and its golden test anchor to the code these `describe()` values describe: Kev `:294–309`; Qwen `:642–647`, `:649–662`. |
| Installed `kev/model.py:87–127` (+ `:104–111`, `:125`, `:188–201`, `:329–333`) | The exact Kev field order the sidecar's `field_order`/`readout` must state; hash this file into `attempt2_template.encoder.kev_model_sha256`. |
| `r1/scripts/trackp.py:223–233` (`cmd_probes`), `:315–325`/`:317` (manifest write and `extra`) | The child-manifest route if a first-class field is later chosen: return a `serialisation` dict from `cmd_probes`/`cmd_e0` and add it to `extra`, or write the sidecar from the runner. `trackp_run_manifest/v1` has no template field today (R2 §1.3), and `run.py` is **not in the export**, so its line numbers cannot be cited here. |
| `r1/scripts/trackp_p3a_guarded.py:26–58` (`verify_pins`), `:166–293` (`run_unit`), `:340–351` (campaign journal) | Template for the new reviewed probes-only runner: where to compute/assert the template, where to write the sidecar, and where to add the journal fields. |
| `r1/c3/train/exam_run.py:260–337` (`probes`) | Where A6 would live if authorized (§4); not part of the recording mechanism. |

**Route recommendation (resolves R2 P-M3).** Use the **sidecar + journal** route written by the reviewed probes-only
runner. It (a) needs no edit to pinned Track P code (the A3 delta can stay flag/tests-only as planned), (b) does not
rewrite the child's preserved artifacts, and (c) still gives every P.3a result a self-describing record
(`<unit>/runner_manifest.json` + hash in the journal). Do **not** use a bare `trackp.py probes` (no template field,
no journal, R2 §1.3). A first-class `trackp_run_manifest/v2` field is the right route for P.3b onward, not for this
attempt-2 unit.

### 3.5 Retro-tagging attempt 1 by provenance (not re-labelling)

Attempt 1 is **not** edited, renamed, re-run or assigned a field it did not write. Instead the attempt-2 sidecar (and
the P.3a report) carry the block below, with `recorded_at_run_time: false`, `label: "derived"`, and the derivation
document + sha. Per base:

| Attempt-1 base | Derived `derived_prompt_version` | Derived `derived_order` | Derived `derived_template_id` | Run-time field? |
|---|---|---|---|---|
| `kev-0.8b` | `trackp_prompt/v1` | `history_first` | `trackp_prompt/v1/kev_pointer_v1/history_first/kev@2074cc44256200bb37540103fa4572901faa10f3` | none recorded |
| `kev-4b` | `trackp_prompt/v1` | `history_first` | same as above | none recorded |
| `qwen3.5-0.8b-base` | `trackp_prompt/v1` | `history_first` | `trackp_prompt/v1/qwen_bintoken_v1/history_first/transformers@5.19.0+qwen3.5-tokenizers` | none recorded |
| `qwen3.5-4b-base` | `trackp_prompt/v1` | `history_first` | same as above | none recorded |

`attempt1_provenance` must also carry `root`, `journal_sha256` (`1e73e80f…`), `lease_log_sha256`
(`69505091…`), `paper_commit` (`b9ad6f8f…`) and, for the re-run 4b probes, the loaded
`EVIDENCE/qwen3.5-4b-base/final/saved` file hashes. The P.3a report then shows attempt-1 results **with** this
provenance tag and attempt-2 results **with** the identical `template_id`; it must not present the tag as a
run-time field and must not alter attempt-1 bytes.

### 3.6 P.3a report table (required by STOP-5 review)

Every result row in `docs/r1/reports/TRACKP_P3a_<date>.md` should carry: `base`, `unit`, `template_id`,
`template_from` (`attempt-2 sidecar` vs `attempt-1 derived`), `provenance_sha256` (sidecar or derivation-record
sha). STOP-5 crosses these against the journal and sidecars (R2 condition 5). Nothing in this record authorizes the
report itself.

---

## 4. A6 implication

**A6 as specified** (`TRACK_P_POST_TRAINING.md:305`, §5.6; R1-BX-REVISIONS (d), `PLAN.md:759`): "The same states
serialised history-first (proposal immediately before `<decide>`) and proposal-first. Report mean |Δ RPS| and the
change in decision utility on the exam set; descriptive, not disqualifying *(proposed)*. It runs once on the E0
model of each candidate, and again on the P.3b finalists." Option 3 (G2) expects A6 to quantify the difference and
make the "P.3a is not re-run if mean |Δ RPS| ≤ 0.01" call.

**What A6 would need to compare / hold fixed:**
- The **same exam states** (the E0 items, `e0_v1.jsonl.gz` sha `4f4db29b…`), rendered under **two orders only**:
  (a) "history-first" and (b) "proposal-first" (proposal before the state/history block).
- Everything else fixed: identical state/proposal/question/option text, identical tokenizer and pinned revisions,
  identical token budget (1,024 / the 1,024-token family limit), identical option order (`BIN_OPTIONS`; Qwen
  `list_bins`/`bin_order` canonical), identical readout head and checkpoint.
- Per candidate base: load the **preserved attempt-1 E0 model** (`EVIDENCE/<base>/final/saved` exists for all four
  bases), predict under both renders, and report mean |Δ RPS| (bin-distance metric) plus Δ decision utility
  (spec §3.5, line 166: `Δ_audit·keep − g·execute`, g = 0.1σ_node) on the exam set; descriptive.
- No retraining is needed for the E0-model sweep (inference only), which makes a separate A6 unit feasible and
  cheap relative to a re-run — but it is still **new code** (a wrapper-level order switch + a probe + tests) and a
  **new authorized unit**.

**Implementation reality:**
- **A6 is unimplemented.** `exam_run.probes` (`exam_run.py:260–337`) implements A3/A4/A5/A1/A2 only; there is no
  order switch in `types.py`/`serialize.py`/`model.py`/`exam_run.py`; the spec marks A6 "(proposed)"; no attempt-1
  artifact contains an A6 result.
- **The spec's two arms do not map cleanly onto either attempt-1 family frame.** The literal "proposal immediately
  before `<decide>`" arm cannot be produced by `kev.model.encode` without changing the record mapping (the encoder
  always emits `instr` = proposal+question, then option spans, then `<decide>`), and the Qwen frame has no
  `<decide>` at all. So an A6 implementation must first **define the arms operationally**: (a) history-first =
  the attempt-1 family frame (state → proposal → family frame → readout), (b) proposal-first = proposal before
  state; and, if the literal adjacency is wanted, a **third** template/encoder variant. This definition must be
  fixed before A6 runs, or A6 would measure a template that was never used.

**Disposition (not decided here; the author/coordinator must choose):**
- **(i) Separate reviewed A6 unit** — scope: wrapper-level order switch behind a flag, tests (both arms render the
  expected streams; same tokens otherwise; no change to the default path), inference on 4 preserved E0 models,
  report mean |Δ RPS| + Δ utility; new authorization. Pro: discharges (G2) and gives the P.3b order change a
  measured basis. Con: new code + review + GPU time; its "history-first" arm must be defined as attempt-1's frame
  (see above).
- **(ii) Recorded deferral with disclosure** — record that A6 is deferred, the 2k/8k A3 rows are omitted under
  `R1-P3A-OOM-OPTION3`, no order comparison was made, attempt-1/attempt-2 results are tagged with the derived
  `trackp_prompt/v1/history_first` provenance, and the P.3a report discloses both limitations. Pro: no new unit;
  attempt 2 is a probes-only re-run and the M13 determination already answers the "which order did P.3a use"
  question (not proposal-first). Con: (G2)'s quantification and the "≤0.01" re-run rule are not exercised; P.3b's
  order change is unquantified.

**Reviewer's recommendation (for the coordinator to decide).** Record **(ii) for attempt 2 now** (it is accurate and
unblocks the run: no order change is in the attempt-2 code pin), **and queue a separate reviewed A6 unit before
any P.3b order change**, with its "history-first" arm defined as the attempt-1 family frame. Note that under §2 the
attempt-1 determination **narrows** A6's original purpose: attempt 1 was not proposal-first, so the "if P.3a used
proposal-first, record and never re-label" branch is not triggered; what remains to quantify is the family-frame /
adjacency question, which A6 must state explicitly.

---

## 5. Review verdict

### `Verdict: accepted`

**This record is sufficient to close M13 for Unit A purposes.** It determines, from the committed exported bytes,
the template version and order that the preserved P.3a attempt 1 used per family for the four-base pool, establishes
the negative fact that attempt 1 recorded neither, specifies a fail-closed attempt-2 recording mechanism with exact
fields/sources/write points, specifies the provenance retro-tag, and states the A6 implication. It satisfies R2
condition 4 (order per family wrapper; shared `trackp_prompt/v1` string; attempt-1 results retro-tagged by
provenance, not claimed as recorded; attempt-2 mechanism) and R2 P-M1/P-M2/P-M3 in form. The one point that is an
*interpretation* rather than an evidence gap is R3 below; it does not change what attempt 1 did, only how it is
labelled against the 4-Nov wording.

**Residual risks / exact gaps.**

- **R1 — no run-time rendered-prompt capture.** The order is determined from pinned source, not from a preserved
  token stream (none exists in the export). The chain is strong (clean commit throughout; exported bytes = commit
  blobs; deterministic rendering; installed-encoder pin + RECORD integrity) but remains a derivation. *No
  additional read-only evidence is needed for the determination.* If direct empirical confirmation were ever
  demanded, the minimum would be a bounded re-render of the preserved E0 prompts through the pinned wrapper under
  a reviewed replay unit — i.e. execution, out of scope here; there is no existing stdout/serialized-prompt
  artifact to read.
- **R2 — Kev encoder bytes not byte-compared to upstream git `2074cc44`** (object unavailable locally). Pinned by
  `direct_url.json`, the recorded TASL-7 freeze and RECORD integrity. Low risk; disclose the limitation.
- **R3 — "history-first" definitional gap (the one item that could still change a downstream decision).** Attempt 1
  is unambiguously **history-before-proposal**, but it is **not** literal "proposal immediately before `<decide>`".
  The 4-Nov order text (`:90`) says "history → the proposal → `<decide>` (and the options, where the family's
  interface lists them)", which can be read as permitting the family option list between proposal and `<decide>`
  (in which case attempt 1 already conforms), or as requiring adjacency (in which case it does not, and the
  `≤0.01`/A6 question is live). **This record deliberately does not decide that reading** (it is the
  author/coordinator's call, gated by A6); it records both facts so the decision is made on evidence. Nothing in
  attempt 1 should be described as "proposal-first", and nothing should be described as "proposal immediately
  before `<decide>`" without qualification.
- **R4 — the recording mechanism is specified but not yet implemented/tested.** M13 closes as a determination +
  mechanism record; the sidecar, journal fields, golden-token test and input-hash binding are deliverables of the
  reviewed probes-only runner unit, and the attempt-2 template field must not be declared satisfied until that
  unit's review records its commit sha and test list (R2 conditions 3–4).
- **R5 — four-base scope.** The determination covers the two wrapper families actually run. `laya`/`startlux`
  units never started (journal); if the pool is ever re-expanded, their wrapper orders must be determined/reviewed
  separately (pinned source: Laya proposal-before-state, `model.py:394–396`; StartLux state-before-edit, `:552–556`).
- **R6 — attempt-1 completeness.** The interrupted `qwen3.5-4b-base/probes` unit has no manifest/report; its
  template is still determined by the same pin and its `unit_start.argv` is in the journal. Attempt 1's
  `probes` manifests also lack the loaded-model hash binding (`model_files_sha256: {}`); the binding is
  recoverable from `final/saved/manifest.json["files"]` = `final/manifest.json["model_files_sha256"]` (verified for
  all four bases) and must be recorded by attempt 2 (§3.2).

**What would make this `not accepted`:** finding that the run's code differed from `b9ad6f8f` (contradicted by
39/39 manifests + `verify_live_pins`), that a wrapper reordered state/proposal at run time (contradicted by the
pinned source), or that the installed Kev encoder's `encode` differs from the framing above (contradicted by the
exported installed file, which is RECORD-intact and matches the manifests' pin). None holds.

**What this verdict does not do:** it does not accept Unit A, authorize Unit B, authorize A6, authorize a P.3a
re-run, authorize any code change, or claim that the attempt-2 field already exists. Attempt 1 remains preserved
and unmodified.

---

## Appendix — pinned symbols and paths used (all in the exported inventory)

- Worktree-relative inventory root:
  `docs/r1/reports/trackp_p3a_attempt1_inventory_20261116/` (SHA256SUMS sha `5c35ef2b…`, 243 files).
- Pinned paper source: `…/Agent_paper_B/r1/c3/train/{types.py,serialize.py,model.py,exam_run.py,exam_synthetic.py,registry.yaml}`,
  `…/Agent_paper_B/r1/scripts/{trackp.py,trackp_p3a_guarded.py,trackp_p3a_watchdog.py}`, `…/configs/trackp_portal.json`,
  `…/r1/c3/train/data/e0_v1.jsonl.gz` (sha256s in §1.2).
- Installed Kev: `…/venvs/trackp-gpu/lib/python3.12/site-packages/kev/` (`model.py` sha `2ff3b2e6…`) +
  `kev-0.1.0.dist-info/` (`direct_url.json` commit `2074cc44…`, RECORD sha `f5c6ed14…`).
- Attempt-1 runs: `…/runs/p3a_operator_20261027/` (journal sha `1e73e80f…`; lease log sha `69505091…`; launch log
  sha `76672735…`; launch script sha `6fc8f4cb…`), 129 manifests / 39 reports / 5 probes stdout logs.
- Key symbol/anchor: `PROMPT_VERSION` `types.py:26`; E0 rows `e0_v1.jsonl.gz`; wrapper order `model.py:294–309,
  311–336` (Kev) and `model.py:589–703` (Qwen); Kev encoding `kev/model.py:9–11, 87–127, 188–201, 329–333`;
  dispatch `model.py:765–796`; config families `trackp_portal.json`; journal/manifest write `trackp.py:315–325`,
  `trackp_p3a_guarded.py:166–293, 340–351`; A6 absence `exam_run.py:260–337`.
