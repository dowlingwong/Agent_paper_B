# Independent review — Track S `tabular_mlp` S0.1 re-run on TASL-7 (k = 2 decision), 14–15 November 2026

**Reviewer.** Fresh independent reviewer; I did not write the output, launcher, report, STATUS entry or
copy-back. I verified only from the operator runbook rev 3.3 (`13badb0`), PLAN rows, the commits, the
committed/host files, and TASL-7 itself. TASL-7 was used **read-only only** (`ssh`, `ls`, `stat`, `sha256sum`,
`wc`, `tail`/`head`, `awk`/`grep`, `tmux ls`, `pgrep`, `nvidia-smi`, `ss`, `flock -n`, `git rev-parse`/`status`).
I wrote nothing on TASL-7, started/stopped/signalled nothing there, attempted nothing on TASL-2. On the Mac I
wrote only this file plus files under `/tmp`. I did not touch the main worktree and made no git write operation
in the operator worktree.

## Scope

The author's 14 Nov amendment (relayed by the Lead): add a `tabular_mlp` S0.1 re-run at k=2 on TASL-7 at the
new paper pin `8237fd02`, **after** S0.4 (accepted STOP-3) and **before** S0.5; k fixed by measurement, any
identity < 100 % is a STOP for the author, no k=1 fallback. Authority: runbook rev 3.3 Phase 1 and
§0.5/§0.8; the reviewed digits TASL-7 S0.1 discipline (`reports/TRACKS_S01_TASL7_RESULT_20261113.md`, launcher
`tasl7_digits_s01_20261113.sh`); `R1-CACHEPROMPT-FALSE`; PLAN §10 Track S rows. Canonic unit: branch
`trackS-ops-20261030`, tip **`7606dae79e04896d490fc48febece77243e350c1`**.

Everything below was re-derived; the operator's report, commit message and STATUS were treated as claims to be
checked, not as evidence.

## 1. Provenance — PASS

- Tip **`7606dae7`**; parent **`db5f187b`**. `git merge-base --is-ancestor db5f187b 7606dae7` is true and
  `git log db5f187b..7606dae7` contains exactly one commit (**fast-forward**, no force). `git reflog show
  trackS-ops-20261030` lists only commits (no `reset`/`rebase`/`push --force` entry).
- `origin/trackS-ops-20261030` = **`7606dae7`** (`git ls-remote origin`), and the TASL-7 bare
  `/home/dowling/r1_tracks/remotes/Agent_paper_B.git` `refs/heads/trackS-ops-20261030` = **`7606dae7`**. Neither
  host remote was force-moved. TASL-2's remote-tracking ref remains `78a1b65e` (no push attempted; TASL-2 is
  down — see §8).
- `git diff --name-status db5f187b 7606dae7` = `M docs/r1/STATUS.md` (+10 lines), `A` the report, `A` the 11
  copy-back files (`SHA256SUMS` + 10 payload files). **The S0.1 launcher is not in the tip commit**: it was
  first added in `ce0da8cd` and revised to its final content in `6aaa800e` (15 Nov 00:04:38 +01:00 =
  **2026-11-14T23:04:38Z**, i.e. before the STOP-3 acceptance at 23:10:15Z and the run at 23:11:05Z; the STOP-3
  review explicitly reviewed that revision, `reports`/review §12 note "refuses unless exactly two llama-server
  processes"). So the launcher, report, STATUS and copy-back span `ce0da8cd`/`6aaa800e` + `7606dae7`, not the
  tip commit alone — a framing correction, not a provenance gap.
- The accepted STOP-3 review file committed at `db5f187b` is exactly
  **`fbf0a874aad6d526f1fa9c8f79ff4faf4bcfadb36ab4cdc45dbaf1a34949908b`** (`git show
  db5f187b:… | sha256sum`), and is unchanged at the tip (same blob).
- Worktree: no tracked modifications. Two **untracked** S0.5 launcher drafts exist (see MINOR-4).

## 2. Launcher — PASS

- `r1/tracks/ops/launch/tasl7_tabular_s01_20261114.sh`: file sha256
  **`0f3d05befb05d7736e39fd9704906218371f1228b8f48a5450f9ab8e265fa520`**, 4987 B. Committed blob (in tree at
  the tip) sha256 = the same value and size 4987 B; deployed `$R/launch/tasl7_tabular_s01_20261114.sh` on
  TASL-7 is 4987 B with the same sha256 → **byte-identical**. `bash -n` passes on the committed blob and the
  working file.
- Guards present and ordered as declared: priority markers (`trackx_evidence.active`,
  `trackp_evidence.active`, `$R/trks_drill.active`), new-output-dir refusal, duplicate-session refusal,
  paper pin `8237fd02` **and** dirty-worktree refusal, `trks_llm` present, then **exactly 2** live
  `llama-server … --port 1810[12]` processes before probing. No destructive command (only `tee -a` to the
  launch log; `mkdir -p` of the new out dir; no `rm`/`mv`/truncate).
- Probe commands (launcher vs `trks_s01t_serial.cmd` / `trks_s01t_conc.cmd`, written by `trks-run` from the
  executed command): serial — `--url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 --order-seed
  1 --proposal-schema manager_proposal/v1 --node tabular_mlp`; concurrent — `--url …18101/v1 --url …18102/v1
  --mode concurrent --clients-per-url 2 --n 200 --repeats 3 --order-seed 2 --proposal-schema
  manager_proposal/v1 --node tabular_mlp`. Matches runbook Phase 1 and the digits discipline exactly.
- `serial.json`/`concurrent.json` record `cache_prompt: false`, `cache_prompt_label: "explicit"`,
  `temperature: 0.2`, `manager_proposal/v1`, `n_prompts 200`, `repeats 3`, `clients_per_url 1/2`,
  `label ENGINEERING_ONLY`, `host TASL-7`, GGUF `509287f7…` / llama `620d2225…` / full `server_args`. The
  harness `a3fedbb` injects `cache_prompt` and the probe posts the harness body; `request_example` has no
  `max_tokens`.

## 3. The server-log offsets — explicit statement

Recorded in `$R/logs/s01_t7_20261114_launch.log`:

```
OFFSET_START 2026-11-14T23:11:05Z llama_18101=1013600752 llama_18102=398591403
… 23:11:18Z llama_18101.log size at start: 1014105122 bytes; llama_18102.log size at start: 399095773 bytes
OFFSET_END   2026-11-14T23:47:41Z llama_18101=1316952707 llama_18102=598535821
```

- The **`OFFSET_START` values are correct pre-start sizes**, verified independently: byte `1013600753` of
  `llama_18101.log` is the first line of *this* server (`0.00.031.935 I srv llama_server: initializing ...`)
  and byte `398591404` of `llama_18102.log` is likewise its first init line; the bytes immediately before each
  offset are the previous run's last line. The launcher's own first reading (23:11:18Z, after readiness) is
  504 370 B / 504 370 B larger — consistent with the startup output. The first probe launch lines are at
  offsets 1014107631 (18101) and 399100021 (18102), i.e. inside the range.
- The **`OFFSET_END` values equal the current final file sizes** exactly (1 316 952 707 / 598 535 821); the files
  have mtime 2026-11-14 23:46:26Z and were not written after, and the range covers all 1 799 + 1 199 prompt
  launch lines and 1 800 + 1 200 responses.
- Factual note: the `OFFSET_START` line is **operator-authored** (the launcher itself records only the
  post-start sizes; the reviewed digits launcher records no offsets at all). The *values* are nevertheless the
  demonstrably correct pre-start boundaries, so the offsets **do support a clean, complete recomputation**; no
  classification issue arises. The ordering within the launch log (the line precedes the `S0.1 start` line) is
  the only direct evidence that it was captured before the servers wrote, and no contrary evidence exists.

## 4. Identity recomputation from the append-only server logs — PASS

Method (independent of the operator): I extracted the two event streams on the host from exactly the byte
ranges above — the `launching slot` lines that carry the rendered prompt (including the per-prompt seed and
`"Budget index (trial number): N"`), and the `Parsed message: {"role":"assistant",…}` response lines. Both
streams are in task-completion order (`id_task` strictly increasing 0…188821 on 18101 and 0…125788 on 18102).
In this build a launch line is emitted when the *next* task starts and carries the task that just finished; a
logging race can put a launch line before its own `Parsed message`, so I pair the two streams **by index**, not
by adjacency. The last completed task has no following launch line (1 799 launches vs 1 800 responses on
18101; 1 199 vs 1 200 on 18102 — the same residual the 13 Nov digits TASL-7 recomputation recorded); the one
unpaired last response is attributed to the only short prompt group and checked byte-equal to it.

| probe (of this run) | calls | prompts | result |
|---|---|---|---|
| serial 18101 (first 600 = 200 prompts × 3) | 600 | 200 | **200/200** prompts with all 3 repeats identical |
| concurrent 18101 (next 1199 pairs + last response) | 1200 | 200 | **200/200** with 6/6 identical (budget 191 5 → +trailing byte-equal) |
| concurrent 18102 | 1200 | 200 | **200/200** with 6/6 identical (budget 65 5 → +trailing byte-equal) |
| `cross_server_identity` (18101 concurrent vs 18102) | 200 prompts | 200 | **200/200 = 1.0000** |

- **Negative control (one-call shift).** Re-pairing each response with the *previous* call's prompt gives
  **3/200** all-identical groups in serial, **0/200** on concurrent 18101 and **0/200** on concurrent 18102, so
  the 200/200 result is discriminating, not an artefact of the few distinct outputs.
- **No truncation artefact.** All 1 800 + 1 200 logged response contents are complete JSON objects, 302–375
  characters, with exactly the six `manager_proposal/v1` fields; there are 34 distinct content strings.
- **Schedule/seed cross-check.** The recorded `order_head` values are reproduced exactly from the probe's own
  rule (`random.Random(f"{seed}|{url_index}|{client}")`): serial `[[163,1],[7,2],[134,1],[86,0],[0,0]]`; both
  clients on URL 0 and URL 1 match their recorded heads; the launch-line budgets equal prompt index + 2; each
  prompt's seed is constant across its calls, and budget 2's seed is `1332422715` = `request_example.seed`.
- **Parameters in the traffic itself.** Every prompt launch line (1 799/1 799 on 18101, 1 199/1 199 on 18102)
  carries `"temperature":0.20000000298023224`; `"n_prompt_tokens_cache":<nonzero>` occurs **0** times on both
  servers (no prompt-cache reuse), consistent with `cache_prompt:false`.
- This recomputation matches the committed aggregates exactly: serial `identity_rate 1.0`, errors 0, n 600;
  concurrent 18101/18102 `identity_rate 1.0`, `identity_rate_per_client [1.0,1.0]`,
  `cross_client_identity 1.0`, n 1200 each, errors 0; top-level `cross_server_identity 1.0`.

## 5. Measurements and run window — PASS

Read from the committed JSONs and re-checked against the report table:

| probe | URL | identity | errors | n | mean (s) JSON → report | p95 (s) JSON → report |
|---|---|---|---|---|---|---|
| serial | 18101 | 1.0 | 0 | 600 | 0.6980372734802465 → **0.698037** | 0.7400350021198392 → **0.740035** |
| concurrent | 18101 | 1.0 | 0 | 1200 | 2.812054386822274 → **2.812054** | 2.99497283808887 → **2.994973** |
| concurrent | 18102 | 1.0 | 0 | 1200 | 2.8069242642330936 → **2.806924** | 2.9779010070487857 → **2.977901** |

- CPU census (24 CPUs; `cores_free_est = cpus − loadavg_1m`): serial 0.224609375 → 1.11376953125 load,
  23.775390625 → 22.88623046875 free; concurrent 1.1044921875 → 2.00537109375, 22.8955078125 →
  21.99462890625. The report's rounded values are exact.
- Window: servers 2026-11-14T23:11:05Z (waiter tmux creation and `OFFSET_START`), both `/v1/models` ready
  23:11:18Z, serial `.exit` rc=0 **23:18:18Z**, concurrent `.exit` rc=0 **23:46:26Z**, `S01 DONE` in the launch
  log **23:46:34Z** (the launcher's post-poll line; the `.exit` value is the correct rc timestamp and the report
  uses both correctly). PIDs **817988/817989** are recorded in the launch log; the report's pid→port mapping is
  covered in MINOR-1.

## 6. k decision — k = 2 is the rule output, and it is correct

Within-server identity is **100 % on both URLs** (serial 18101 200/200; concurrent 18101 200/200; concurrent
18102 200/200) **and `cross_server_identity` is 100 %** (200/200 = 1.0) — independently recomputed in §4 and
matching the committed JSONs. Under runbook rev 3.3 §0.5/Phase 1 as amended by the author (k by measurement;
any identity < 100 % = STOP for the author; **no k=1 fallback**), the rule output is **k = 2**, fixed for
`tabular_mlp` on TASL-7; all later tabular phases must run k = 2. The report §3 states k = 2, "no k = 1
fallback is used", "all later tabular phases on TASL-7 must run k = 2 servers". See MINOR-3 for the one
missing sentence (the explicit author STOP clause).

- **STOP-3 acceptance does not authorise S0.5 by itself.** The record says so: prior STATUS (S0.4 entry)
  "STOP-3 acceptance is NOT S0.5 authorisation: … the tabular S0.1 re-run …, its independent review, … remain
  open"; the new STATUS entry and report §6 both say "No S0.5 until the S0.1 review accepts; then S0.5/S0.5b
  at k = 2". **This S0.1 review is the remaining gate** for starting S0.5 at k = 2. (§3.0b remains OPEN but
  gates Phase 6/0.3(c), not S0.5.)

## 7. Copy-back and preservation — PASS (one accuracy MINOR)

`results/r1/tracks/tabular_mlp/s01_t7_20261114/`:

- `shasum -a 256 -c SHA256SUMS` → **10/10 OK**; `serial.json` sha256 **`db72234e…`** (10 511 B),
  `concurrent.json` **`8bca98b5…`** (17 499 B); `host_logs/` has the launch log
  (`759eedd8…`, incl. both offset lines) and the **6** `trks_s01t_{serial,conc}.{cmd,log,exit}` files;
  `operator_capture/s01_waiter.log` present.
- **Host == copy 9/9** exact sha256: `serial.json`, `concurrent.json`, launch log, and the 6 session files
  (`933c3438…`, `bd90be24…`, `d4398af8…`, `0da6b0b0…`, `1ef1f4ee…`, `4ae87838…`). The 10th SHA256SUMS entry
  (`operator_capture/s01_waiter.log`) is a Mac-side capture not present on the host, correctly excluded from
  the 9/9 claim.
- **Old scenes untouched:** host `out/tabular_mlp/{s01,s01_diag,s01_diag_f1,s01_diag_f2,s11,s01_rerun_INVALID…,
  inputs}` byte-match the committed copies / the recorded 30–31 Oct values (`31d463c4…`/`d65c4c81…`,
  `44078998…`, `a08d45ae…`, `f6a19631…`, `5ac5154b…`, `8ca4740e…`/`81b72cc5…`; `inputs` empty) and carry Oct
  mtimes; `out/smoke`'s six hashes match (`4aa160b1…`, `c6c8e656…`, `619206dd…`, `37798e38…`, `a1d35488…`,
  `ff12d223…`). `scratch/tabular_mlp/` contains only `smoke/` (Oct) and the STOP-3 `s04_t7_20261114/`.
- **Digits S0.1 evidence untouched:** the new session names `trks_s01t_*` are distinct from the digits
  `trks_s01_{serial,conc}.*` (mtimes 13 Nov, unchanged); the digits outputs
  `out/digits_mlp/s01_t7_20261113b/serial.json` = `e0c3060e…` and `concurrent.json` = `94d95b03…` exactly match
  the accepted digits review.
- **S0.4 copy-back not overwritten:** the tip commit touches no `results/.../s04_t7_20261114/` file
  (`git diff db5f187b 7606dae7` empty there); the host `s04_t7_20261114/` dir mtime 22:46Z predates S0.1.
- MINOR-2: report §6 claims a new `scratch/tabular_mlp/s01_t7_20261114`; no such `$WORK` directory exists (the
  Phase 1 probe writes only `--out`). Correct the record.

## 8. Host end state and scope — PASS

- TASL-7 bare ref **`7606dae7`**; paper checkout **`8237fd02`** clean (`--untracked-files=all` empty); harness
  `a3fedbb`; llama `620d2225` build 11669. `trks-status` prints all pinned HEADs **OK**, GGUF sha **OK**,
  `paper tracked-file modifications: 0`, and no STOP condition.
- Only `trks_watch` in tmux; **lease FREE** (`flock -n gpu0.lock true`); 0 `llama-server`, 0 collector,
  0 listener on 1810x, no compute apps; no `trackx_evidence.active`/`trackp_evidence.active`/`trks_drill.active`;
  **0 STOP** under `$R/out`; GPU 0 % (236 MiB used at review time; the report's 243 MiB is the same idle
  baseline snapshot, compute-apps list empty). Files newer than 23:00Z under `$R` are exactly the deploy of the
  launcher, the two server logs, the launch/session logs, the two JSONs and the TASL-7 bare-repo push objects —
  no extra host writes.
- **TASL-2 down/untouched:** `ssh portal_zhixu` → TCP timeout; local `refs/remotes/tasl2/trackS-ops-20261030`
  still `78a1b65e` (no push attempted). Recorded as a host-down gap, not silently skipped.
- **No S0.5 run:** no `out/tabular_mlp/s05*`, no `scratch/tabular_mlp/s05*`, no `s05_t7_tabular`/`trks_s05t_*`
  host logs, no S0.5 tabular launcher deployed. **§3.0b OPEN.** **B2 not armed** (no `trackx_evidence.active`;
  hand-off draft is a document). No B2/X.7/sweep-2 artifacts. Not self-accepted; ENGINEERING_ONLY; report §2–§4
  is descriptive and makes no scientific claim.

## Findings

- **MINOR-1 (accuracy, report §1 line 24; also commit message).** The pid→port mapping "pids 817988 [18102],
  817989 [18101]" is not supported by any saved capture. `trks-servers` starts ports in order 18101 then 18102,
  so the natural mapping is 817988→18101 and 817989→18102 (the opposite); `pgrep` output in the launch log is
  ascending-pid only. It does not affect the per-URL JSONs or the identity result. **Required:** substantiate
  the mapping from a saved `ps -o pid,args` capture, or drop the bracketed port annotations (keep the two pids).
- **MINOR-2 (accuracy, report §6 line 76).** Claims a new `scratch/tabular_mlp/s01_t7_20261114`; that `$WORK`
  directory was never created (Phase 1 probes write only the `--out` JSONs). **Required:** remove the scratch
  path or say no `$WORK` is used by S0.1.
- **MINOR-3 (record completeness, report §3 lines 53–59 and the new STATUS entry line 8).** The decision text
  records k = 2 and "no k = 1 fallback", but not the author's explicit measurement rule "**any identity
  < 100 % would be a STOP for the author**" (it is recorded in the earlier S0.4 STATUS entry and the launcher
  header). Since the else-branch did not fire, the k = 2 outcome is unaffected. **Required:** add the STOP
  clause to the S0.1 report/STATUS so the decision rule is self-contained in the S0.1 record.
- **MINOR-4 (housekeeping).** At review time the operator worktree is not clean: two untracked S0.5 launcher
  drafts (`r1/tracks/ops/launch/tasl7_tabular_s05_20261114.sh`, `…_s05b_20261114.sh`, mtime 15 Nov 00:51 CET,
  i.e. after the 00:49:51 tip). They are not part of the S0.1 unit and nothing was run or deployed (no host
  S0.5 dirs/logs). **Required:** keep them out of the S0.1 submission and do not start S0.5 before this review
  accepts; commit them only as part of the S0.5 submission.

No BLOCKING or MAJOR finding: the provenance, launcher, offsets, identity (serial 200/200, concurrent 200/200
per URL including cross-client, cross-server 200/200 with a discriminating negative control), measurements,
k = 2 decision, copy-back integrity, old-scene/digits preservation and host end state all re-derive correctly.

## Residual limitations (acknowledged, not blocking)

- The S0.1 probe JSON is aggregate-only (`determinism.py` drops per-call `contents`); the identity was therefore
  recomputed from the append-only server logs, which is the route the author accepted at STOP 1 (decision (a)),
  and it is reproducible from the recorded offsets.
- The 14 Nov amendment and the STOP-3/S0.4 ordering remain Lead-relayed author instructions with no separate
  author artifact/PLAN §10 row; the record discloses this. It is not something the operator can manufacture, but
  the author should confirm it in writing when convenient.
- `OFFSET_START` is operator-authored (see §3); its values are independently validated as the correct
  pre-start boundaries.

## Gate

**S0.5/S0.5b for `tabular_mlp` is authorised only after this review accepts** (at k = 2, with no k=1 fallback).
The four MINOR corrections above should be made in the committed report/STATUS record; they do not affect the
measurement or the k = 2 decision. §3.0b and the author's separate confirmations, if any, still gate Phase 6/0.3(c).

Verdict: accepted
