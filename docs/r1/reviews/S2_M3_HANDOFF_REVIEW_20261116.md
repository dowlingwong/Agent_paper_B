Reviewed base: a5f21dbbdefd4580566254b36361f4640ce9fad6

# S2-M3 cluster hand-off — independent review record (16 November 2026)

Branch `mac-s2-m3-handoff-20261116` from `author-decisions-20261116` @ `4da73306`. Unit: `proposals/S2_M3_CLUSTER_HANDOFF_20261116.md`. One freshly spawned independent reviewer agent (AI-assisted, Claude), three rounds.
- **Round 1 (`5f6fb573`): REVISE.** 1 BLOCKING, 7 MAJOR and 9 MINOR.
  - The BLOCKING finding: the wrapper has no resume path, so "resubmit the same spec" would be a full re-run.
  - The MAJOR findings were the `label_source` schema, the failed pilot worker runs, the canary timing, the missing B.2 exclusion and the ENGINEERING text in records, unredacted copy-back, provenance, and requests.
- **Round 2 (`e05eaea7`): ACCEPT,** with 6 minors.
- **Round 3 (`a5f21dbb`, minors fixed): ACCEPT.**

Accepted commit (last round): a5f21dbbdefd4580566254b36361f4640ce9fad6

The round texts are reproduced unchanged below.

---

# Independent review — S2-M3 cluster hand-off (Paper B / R1), round 1

- **Unit:** `docs/r1/proposals/S2_M3_CLUSTER_HANDOFF_20261116.md`
- **Worktree / branch:** `/tmp/pb/wt/s2m3`, `mac-s2-m3-handoff-20261116`
- **Reviewed base:** `5f6fb573faa12238abc2c3f53f1acca1d8cf651a`. It is one commit on `author-decisions-20261116` @ `4da73306`, and it adds only this file.
- **Reviewer:** fresh, read-only. No commits, no state-changing git, no network or SSH. The only scratch files are in `/tmp/pb/rev_s2m3/src/`: copies of the cluster code at `acae9fde`, made for reading.

VERDICT: REVISE

There is 1 BLOCKING finding, 7 MAJOR and 9 MINOR. Most concrete values (digests, hashes, URL, sizes, CPU model, chunk ids, layout numbers, walltime, paths) match their sources. The problems are in how the draft uses them:
- the resume rule;
- the label-source schema;
- the canary timing;
- the redaction rule for what gets copied back;
- provenance;
- the validity of the S2-C4 pilot it builds on.

---

## Findings

### 1. BLOCKING — §6 "the only retry is a resume": the wrapper has no resume path

**Where:** §6 (bullets 3–4), §7 ("Failed attempts stay in their own directories"), §8 header, §9 "resumes".

**What the draft says:** "Resubmit the same spec unchanged. The wrapper's resume pin check and the collector's A.5 resume take over from the preserved `out/`."

**Evidence (cluster code at `acae9fde`):**
- **No staging-in of outputs.** `render_jdl.py` sets `transfer_input_files` to the staged files only: `s2_c2_job.sh`, `s2_c2_lib.py`, `s2_c2_spec.json` and the note. Neither `out/` nor `out.tar`/`work.tar` is transferred into a new job. `render_jdl` also refuses an existing `--stage-dir`, so a resubmission is a fresh render into a fresh sandbox.
- **The record placeholder is wiped.** `s2_c2_job.sh` `_precreate` runs `: > job_record.json` unconditionally at job start.
- **So a resubmission is a fresh full run.** In a new sandbox `_resume_state()` finds no `out/manifest.json` and an empty record, so `resume = False`. The resubmission silently re-runs the whole chunk from scratch: it is not a resume.
- **Re-staging by hand fails too.** If someone staged and untarred the old `out/` by hand, `_resume_state` returns True. `_check_resume_record` then `json.loads` the truncated empty record and raises an uncaught `JSONDecodeError` (a traceback, not a `Stop`).
- **No attempt dimension in the seal.** `seal()` writes to the fixed path `SEALED_ROOT/<run_id>/<chunk_id>` and refuses if it exists. A failed attempt that is sealed blocks sealing the rerun, and an unsealed one exists only in its submit directory. "Failed attempts stay in their own directories" is not something the code provides.
- **The S2-C2 review already flagged this.** Its r4 says the resume "needs the prior `out/work` staged back into the next job's sandbox — the unit doc does not describe that staging". No such staging exists in `S2_C2_UNIT.md` or in the code.
- **HTCondor itself re-runs jobs.** With `when_to_transfer_output = ON_EXIT`, an evicted job restarts from scratch automatically, and `condor_release` of a held job does the same. Neither is mentioned.

**Consequence:** following §6 performs exactly what the S2-M1 note forbids ("Resumable only by the collector's A.5 resume … No ad-hoc retries"): a whole-chunk re-run, reported as a "resume".

**Fix:**
1. Replace §6's retry rule with: any job that does not finish rc 0 with a complete record is a STOP; preserve it, report it, and the author decides.
2. Ban `condor_release`, `condor_rm` and resubmission of a chunk without an author instruction.
3. Make `NumJobStarts > 1` (an automatic restart) a STOP.
4. If a resume is wanted, add a gating item "Fix E: resume staging". It must:
   - stage `out.tar`/`work.tar`/`job_record.json` back in and untar them;
   - not truncate an existing record;
   - give the seal an attempt dimension, or define how attempts are sealed;
   - be reviewed.
5. Change §7's "own directories" sentence to match whatever is decided.

### 2. MAJOR — the `label_source` block in §2, and §1.2, do not match the accepted schema

**Where:** §2 template `"label_source": {"authorization": {"path": "docs/r1/authorizations/c3_sweep2_<date>.md", "sha256": "<note sha256>"}}`; §1.2 "Its sha256 goes into every chunk spec (`label_source.authorization`)".

**Evidence:**
- `resolve_label` needs `label_source.authorization` to be a **string** matching `SAFE = ^[A-Za-z0-9_.-]+$` (no `/`), and reads the hash from a sibling key **`label_source.authorization_sha256`**.
- `render_jdl.py` refuses a non-basename (`"must be a bare basename"`). The `S2_C2_UNIT.md` M4 and the S2-C2 review round 3 (r1) confirm this.
- As written, the template fails at render. It fails closed, but the field is invented, and it is not marked `[fix X]`, so the cluster agent will take it as the accepted schema.

**Fix:** use `"label_source": {"authorization": "c3_sweep2_<date>.md", "authorization_sha256": "<note sha256>"}`, and pass the repo path through `render_jdl.py --auth-note docs/r1/authorizations/c3_sweep2_<date>.md`. Correct §1.2 to say `label_source.authorization_sha256`.

### 3. MAJOR — the S2-C4 pilot's worker runs appear to have all failed; the "measured" layout and fix list rest on it

**Where:** header, §0 S2-C4 row, §3 Estimate, §5.3, and §0's fix list.

**Evidence:**
- In both committed S2-C4 job records (`s2c4_run_20261116/job_record_{none,append_only_summary}.json`), every worker-run line visible in `collector.stderr_tail` is `running: python3 train.py` followed by `run_command finished in 0.0s` (or `0.1s`) with `success=False metrics={}`. That is 10/10 in one record and 9/9 in the other, with no `success=True`. The manager keeps re-proposing the same edit (`HIDDEN_UNITS: 32 → 64`), which fits runs that never finish.
- **Probable cause:** `run_job` does not put the harness env on `PATH`. Its env has `PYTHONPATH` etc. but no `PATH`. The node command `python3 train.py` therefore likely ran the container's system `python3`.
- **Sweep 1 guarded exactly this:** `c3_label_sweep.py` `package_environment()` STOPs if the `PATH` `python3` differs from the collector interpreter, and `evidence_node_commands()` admits only the verified `python3 train.py` forms. That gate is missing from the S2 wrapper.
- It is also missing from fix C, which restores only liveness, `max_parse_failure_rate` and `collection_gates`. None of those three catches failing worker runs. D28 liveness (keep after trial 1; invalid rate < 30 %) probably would, so the (g)4 unit and S2-C3 should stop it before EVIDENCE.
- **Effect on the numbers:** the 8,289 s/chunk and 36.84 GPU-h then mostly measure LLM calls plus failing runs, not training time. The projection STOP (60 GPU-h / 48 h) is checked against a likely underestimate.
- **Review status:** neither the cluster's results report nor any review records this, and the S2-C4 results have no post-run review on the branch.

**Fix:**
1. In §0/§3, state that the S2-C4 timing is provisional, and why: the worker runs in the record tails failed.
2. Add a gating item, e.g. **Fix E′: worker environment**. It restores sweep 1's `package_environment`/`evidence_node_commands` checks in the job, or sets `PATH` to the harness env and checks it.
3. Require the re-pilot or S2-C3 at 32,768 to show successful worker runs. Re-derive walltime, memory, disk and the estimate from it.
4. Add to the canary checks, the STOP list and the §9 template counts of worker runs succeeded and failed, plus LLM calls and parse failures. These are counts of the kind in sweep 1's `collection_checks.json`, not metrics.

### 4. MAJOR — §5 canary "within the first minutes, check each job record" cannot be done

**Where:** §5.1 and §5.3.

**Evidence:**
- `run_job` writes `job_record.json` only after the collector finishes. Until then only `_precreate`'s empty placeholder exists.
- With `when_to_transfer_output = ON_EXIT`, nothing comes back before job exit.
- The job prints only start and end lines to stdout (`s2_c2_job.sh`), and `s2_c2_lib run` prints its JSON only at the end. So GPU, CPU, GGUF, build, offload and liveness are not observable "within the first minutes".
- §5.3's "completed campaigns per hour against 18 × 20 runs" is not observable mid-job either. It also mixes units: a chunk is 18 campaigns, each of W = 20 runs.

**Fix:** the canary verdict comes from the completed canary jobs (about one chunk wall plus queue wait). The projection is computed from their measured wall, as `ceil(16 / concurrent L40S slots) × chunk wall`. The alternative is a gating change that writes an early identity record or stdout lines and allows `condor_tail`. Say which.

### 5. MAJOR — B.2 exclusion missing, and the wrapper hard-codes ENGINEERING text into EVIDENCE records

**Where:** the whole draft. The words "B.2" and "audit" appear only in the (g)2 row.

**Evidence:**
- **B.2 scope.** R1-SWEEP2-SETTINGS (2) says the sweep-2 note has no B.2. The S2-M1 redraft states this under "Scope". The hand-off never tells the cluster agent that B.2 audits and audit seeds 7001–7010 are out of scope, and has no STOP if any audit runs. The collector's `--audit-seeds 0 --reps 0` comes from the code only.
- **Hard-coded text.** At `acae9fde`, `run_job` writes these into every record whatever the label:
  - `"output_use": "ENGINEERING: never enters a label table, training or selection …"`;
  - `"b2_audits"`;
  - `"manager_settings": {…, "ctx": 16384}`.
- `collector_argv` also writes `"audit": "none (ENGINEERING run: …)"` into the collector manifest.
- An EVIDENCE record would therefore claim it never enters a label table, and would state ctx 16384 at 32,768.
- `acae9fde` was committed after the pilot ran: the pilot records still carry `audit_seeds`. It is unreviewed.

**Fix:**
1. Add to §0/§1 and §8: "no B.2 audits; audit seeds 7001–7010 untouched; any audit run is a STOP".
2. List the label-dependent record and manifest text, and the ctx value, as part of fix A (or a new fix) that must exist before the template is used.

### 6. MAJOR — §10 copies whole job records into the repo, against "counts only; no label read"

**Where:** §9 statement, §10 bullet 3 ("every job record and seal receipt, copied into the repo as in `s2c4_run_20261116/`"), §5.1, §6.

**Evidence:**
- Each job record carries `collector.stdout_tail` and `stderr_tail`: the last 4,000 characters of the harness log, including `metrics={…}` per worker trial. In a working EVIDENCE run these hold in-campaign metric values of sweep-2 campaigns.
- Copying them into git puts sweep-2 data outside sealed storage, where any reader can reach it. That conflicts with R1-BX-D8, and makes the §9 statement "no label, metric or table was read" hard to keep, since §5 and §6 tell the agent to read those records.
- `llama-server.log` at `-lv 4` may also hold prompt text, which includes run histories.

**Fix:**
1. Copy back only a redacted projection of each record: identity fields, timings, counts, rc. Exclude `collector.stdout_tail`/`stderr_tail` and the server log.
2. The canary and the report read only those fields.
3. The full records stay sealed.

### 7. MAJOR — provenance and gate checks are thinner than the B2 style

**Where:** §0 S2-C2 row, §1, §4.

**Evidence and gaps:**
- **What runs in the job.** `render_jdl.py` copies `s2_c2_job.sh`/`s2_c2_lib.py` from wherever it is run (`HERE`). These files are the code the job executes, and the job record holds no hash or commit for them. The hand-off never says to render from a clean checkout of the launch commit, or to record and compare the staged files' sha256.
- **Missing B2-style checks.** The B2 hand-off (§2, §5.1) requires:
  - a clean checkout at the run HEAD;
  - a protected-path diff;
  - an exact-HEAD independent review;
  - a three-way reviewed-base / `Accepted commit:` / READY.txt check.
  None of these is required here for the launch commit.
- **Unreviewed hotfixes.** §0 lists the wrapper as "accepted (ENGINEERING); hotfixes during S2-C4 up to `c8d07994`, plus disclosure fix `acae9fde`". The accepted base of the reviews is `70e3a116`/`235c9e5f`. The six hotfixes (`f4a85da1` … `c8d07994`) and `acae9fde` change wrapper code and have no review record on the branch. Neither does the S2-C4 results report.

**Fix:**
1. Mark these items in §0 as "not yet reviewed".
2. Add to §4:
   - render from a clean checkout at the launch commit (`git status --porcelain` empty);
   - the staged-file sha256 equals the launch commit's `sweep2/` files;
   - an exact-HEAD review of the launch commit;
   - the three-way base check.

### 8. MAJOR — the requests disagree with the S2-M1 note; disk scaling is unproven; the free-space basis is wrong

**Where:** §2 notes ("The larger fixed values are safe. Whether to lower them is the cluster's call"), §4.6.

**Evidence:**
- **Disagreement with the note.** The S2-M1 redraft writes `request_memory 32,000` MB and `request_disk 42,439,718` kB into the note's "Job layout". The hand-off leaves 128,000 / 50,000,000 or a lower value to the cluster. Its own rule says "the authorization note wins", so a cluster agent cannot obey both.
- **Disk.** The disk peak (30,314,084 kB) was measured with **2 instances**. It includes the 19.6 GB GGUF and both the `out/`/`work/` directories and their tars, so the output part is stored twice at job end. If the non-GGUF part (about 11 GB) scales with instances, 18 instances exceed both 42.4 M and 50 M kB. S2-C4's "scale with instances" assumption covers time only. "Safe" is therefore unsupported.
- **Free space.** §4.6 multiplies the sandbox peak (which includes the GGUF, not transferred) by 16 to get the transfer volume. It ignores the `/ceph` space needed for the untarred sealed copy.

**Fix:**
1. Make requests a pinned value that the note and hand-off share (or "≥ note"), and list a renderer change if needed.
2. Drop "safe".
3. Have S2-C3 or the re-pilot measure disk at a full chunk.
4. Base §4.6 on the measured `out.tar`+`work.tar` sizes for the submit host and the untarred size for `/ceph`.
5. Check `DiskUsage`/`MemoryUsage` against requests at the canary.

### 9. MINOR — §2 misstates what the accepted validator requires

The draft says it requires "`ctx` 16384, `n_gpu_layers` 99 and `--no-webui`". `validate_spec` enforces only `ctx == 16384`. It requires `n_gpu_layers` to be a positive int and does not require `--no-webui`; those values come from `spec.example.json`. The template's 999, compact thinking JSON and absent `--no-webui` already pass every check except ctx. Fix: correct the sentence. Fix A is then the ctx check plus the record text (finding 5).

### 10. MINOR — port collision when chunks share a host

**Evidence:** every spec pins `server.port 18110` on 127.0.0.1, and §4.2 requires the specs to be identical apart from chunk, node and mode. With 14 jobs submitted together, two jobs on the same multi-GPU NEMO2 node (if containers share the host network namespace) would contend for the port. The second job can briefly see the other job's `/health` before its own offload check STOPs.

**Fix:** a distinct port per chunk (allowed by §4.2), or a recorded check that the containers have separate network namespaces.

### 11. MINOR — STOP list (§8) is incomplete

Add:
- any B.2 audit or audit-seed use;
- `NumJobStarts > 1` (eviction or restart);
- any `condor_release`/`condor_rm`/resubmit without an author instruction;
- a seal refusal (target exists; transferred `SHA256SUMS` mismatch);
- a request exceeded (disk or memory) or a walltime/deadline hit;
- the S2-C5 switch failing to refuse another run id or digest;
- a worker-environment mismatch or failing worker runs (finding 3);
- a GGUF fetch error (`URLError` is not a `Stop`; 16 concurrent 19.6 GB fetches from HF, about 314 GB of egress).

### 12. MINOR — how fix C applies `min_live_nodes` 8 in a one-node job is undefined

Each job sees one node. Fix C must say how the per-chunk wrapper enforces 8 live nodes: for example, the (g)4 report pinned by sha in the spec plus a per-node pass. Otherwise "liveness passed (fix C)" in the canary has no defined meaning. Fix: say this is for fix C to define, and what the canary checks.

### 13. MINOR — §4.2/§4.3 operational details

- `s2_c2_lib validate <spec>` on an EVIDENCE spec needs the note's basename in the cwd. Validation only works through `render_jdl.py`, which `chdir`s into the stage, so say so.
- `condor_submit -dry-run` needs an output-file argument (`-dry-run <file>`).
- Add R1-BX-D8, R1-EXAM-X7 and R1-MAIN-PROPOSER to §4.1's list of PLAN rows checked on the launch commit.

### 14. MINOR — the canary is `digits_mlp`, the same node as the pilot

Both canary chunks and the whole S2-C4 basis are one node. A projection from them does not cover slower nodes. Fix: say so, or pick the expected-slowest node for one canary chunk (S2-C4 review M5 raised the same point).

### 15. MINOR — the sweep index format

The §7 per-chunk index is not the `r1.c3_sweep_index/1` that `r1/c3/dataset.py` reads, which has one manifest per memory mode across all nodes. Fix: state that it is an operational index only, and that a table index is a later, D8-gated unit.

### 16. MINOR — `refuse_sealed` and runbook §0

The draft correctly says `refuse_sealed` does not cover `/ceph/srv/dwong/paperb/sweep2/` (it refuses only `r1_sealed` components). Runbook §0 says raw outputs are stored at "`refuse_sealed` paths". Fix: flag the deviation for the author in one line, not only in passing.

### 17. MINOR — wall projection needs the concurrency

"Above 48 h wall" depends on how many L40S slots run at once. Fix: record the observed L40S slot count (`condor_status`) in the prechecks and use it in the projection.

---

## What I verified (matches its source)

- **Ancestry and scope.** `4da73306` descends from `main` `9ae6d877` (= `gh/main`). The commit adds only the hand-off file.
- **PLAN rows on the worktree.** R1-SWEEP2-SETTINGS (1)–(5), R1-SWEEP-HOST-HTC, R1-BX-D8, R1-BX-D8-V3-A, R1-E1-AUTH and R1-MAIN-PROPOSER (b)/(c)/(g)/(h) are present. The hand-off's projection STOP (60 GPU-h / 48 h), (g)2 order (e1 → e2 → sweep-1 B.2), (g)4 unit and D8 lock ("V3-A lock stands") are consistent with them and with the S2-M1 redraft.
- **Image identity** (against `spec.example.json` and the S2-C4 job records):
  - digest `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093…5296`;
  - `build_utc` `2026-11-14T23:10:24Z`;
  - `llama_server_sha256` `f8d35fd3…3cc0`;
  - llama.cpp commit `620d2225…`;
  - `expected_build` `0.7.0-dev (build 11669, commit 620d2225c)`.
- **Harness.** `a3fedbbd…` = `B2_HARNESS` = `HARNESS_PIN_C3` on `main`.
- **Model and registry.** Model URL, revision `619aca75…`, size 19,598,489,952 and sha256 `2959c1b0…1b75` match the registry doc. The registry doc sha256 is `a04a0346…dc61` (recomputed). `template_repair: null`, so the exam added no `--chat-template-file`.
- **Server argv** against the exam (`llama_server_instance.argv`/`thinking_args`, `runtime.EXAM_SERVER_ARGS`, `ctx_size == 32768`, `n_gpu_layers == 999`):
  - `-np 1` sits in the fixed argv;
  - the thinking switch is compact JSON;
  - the wrapper adds `-lv 4`, as the exam does.
  The template's `extra_args` reproduce this and pass the validator's flag checks.
- **Noise source.** `results/r1/noise/D28_REPAIR_20261027/summary.json` sha256 `3d12ce05…0c34310` (recomputed on `gh/main`), the same as sweep 1's `noise_source`. Sweep 1 passed it as `--e1-summary`. Without it, `e1b_collect` falls back to the latest pilot E1, so fix B is needed, as stated.
- **Sweep-1 gate values.** `min_live_nodes` 8, `max_parse_failure_rate` 0.2 and `collection_gates` match `c3_sweep_deepthought.json` (sha `2fa891f4…`) and `c3_label_sweep.py`.
- **Requirements and design.**
  - `CLOUD_SITE`, `GPU_MODEL`, `MACHINE_REGEX` and `MIN_CPUS` 16 match the code.
  - The CPU model string `INTEL(R) XEON(R) PLATINUM 8562Y+` appears in both pilot records.
  - Workers 16, transport attempts 3, `manager_proposal/v1`, `vary` and W = 20 match.
  - The 16 chunk ids follow the sweep-1 node order × both modes and match `SAFE`.
- **Layout numbers** match `timing.json`: 8,289 s, 36.84 GPU-h, walltime 10,776, disk 42,439,718 kB, memory 32,000 MB, KV 680.0 MiB, offload 61/61. The renderer's 128,000/50,000,000 match `render_jdl.py`.
- **Seal command and layout.** The command `python3 -m sweep2.s2_c2_lib seal <job-output> --run-id … --chunk-id …` and the sealed layout match `seal()` and `S2_C2_UNIT.md`. `sha256sum -c SHA256SUMS` in the sealed directory works, because `SEAL_RECEIPT.json` is written after the sums.
- **Render command.** `render_jdl.py <spec> --out --stage-dir --auth-note` matches.
- **Analysis guard.** `analysis_guard.guard_table`/`require_d8_confirmation`/`refuse_sealed` exist, with the stated behaviour.
- **Note format.** The S2-M1 key block (`approved:` line, `label: EVIDENCE`, `run_id:`) satisfies `resolve_label`'s regexes once the author sets `approved: true`.
- **Gating honesty.** The fix A–D placeholders, "should not be used until the fixes exist", and the proposal label on §5 are present. Findings 2–5 show places where the template still gives wrong or incomplete concrete values despite the gating.

## Not verified

- Anything on the hosts, including condor ads, network namespace and L40S slot count.
- Whether the pilot's worker failures cover runs beyond the 4,000-character tails. I read only the committed records, not the sealed outputs.

---

# Independent review — S2-M3 cluster hand-off (Paper B / R1), round 2

- **Unit:** `docs/r1/proposals/S2_M3_CLUSTER_HANDOFF_20261116.md`, worktree `/tmp/pb/wt/s2m3`, branch `mac-s2-m3-handoff-20261116`.
- **Reviewed base:** `e05eaea71471fbe38ef0db38b7d73c8e64aabb11`. It is one commit on `5f6fb573` and changes only the hand-off (+136/−63). The worktree is clean.
- **Reviewer:** the same independent read-only reviewer as round 1. No commits, no state-changing git, no network. The sources are as in round 1, plus the accepted S2-M1 redraft (`/tmp/pb/wt/s2m1b`, `e43faa29`, accepted at `11db0f65`).

VERDICT: ACCEPT

The round-1 BLOCKING finding and all 7 MAJOR findings are resolved. No new BLOCKING or MAJOR finding. Six MINOR items remain (R2-1 … R2-6). They can be fixed in passing and do not block.

---

## Round-1 findings: status

| R1 | Status | Check |
|---|---|---|
| 1 BLOCKING (resume) | **Resolved** | §6 states that no resume path exists. It gives the three reasons, which match `render_jdl.py` (no prior outputs in `transfer_input_files`, fresh stage) and `s2_c2_job.sh` (`: > job_record.json`). It also explains the crash of a hand-staged resume. A non-clean job, `NumJobStarts > 1`, and any release, rm, resubmit or edit without the author are all STOPs (§6, §8). Fix H lists the right parts: stage-in, no truncation, attempts in the seal path. §7 now matches `seal()`: one path per chunk, refusal on a second attempt, failed outputs stay unsealed in the submit directory. "resumes" and "resume pin mismatch" are gone from §8 and §9. |
| 2 MAJOR (`label_source`) | **Resolved** | `{"authorization": "c3_sweep2_<date>.md", "authorization_sha256": …}` matches `resolve_label` (a `SAFE` basename plus a sibling sha) and `render_jdl`'s basename rule. The repo path goes via `--auth-note`. §1.2 and §4.1 are corrected. |
| 3 MAJOR (pilot validity, worker env) | **Resolved** | §0 marks S2-C4 provisional, with the `success=False metrics={}` evidence. It adds fix E (PATH plus `package_environment` / `evidence_node_commands`) and a full-chunk re-measurement gate at 32,768 / `-np 1` with worker runs succeeding. §3 labels the estimate provisional. Worker-run counts appear in §5, §8 and §9. This matches S2-M1 precondition 4 and note 1. |
| 4 MAJOR (canary timing) | **Resolved** | §5.2 takes the verdict from completed jobs and gives the right reason (record written at collector end; `ON_EXIT`). §5.3 uses GPU-h = 16 × the larger canary wall and wall = ⌈16 / slots⌉ × wall. An early record is noted as a further reviewed change. |
| 5 MAJOR (B.2; ENGINEERING text) | **Resolved** | §8 has a B.2 / audit-seed STOP citing R1-SWEEP2-SETTINGS (2). Fix F covers `output_use`, `audit` and `ctx 16384`, consistent with S2-M1 2e. |
| 6 MAJOR (copy-back) | **Resolved** | §7 says only redacted projections leave sealed storage, never the stdout/stderr tails or `llama-server.log`. §10 says the same, explicitly unlike `s2c4_run_20261116/`. |
| 7 MAJOR (provenance; unreviewed hotfixes) | **Resolved** | The §0 S2-C2 row names the accepted base (`70e3a116` / `235c9e5f`). It marks the six hotfixes `f4a85da1` … `c8d07994` (I counted six commits) and `acae9fde` as not reviewed. §4.2 adds the clean checkout, staged-file sha256 against the launch commit's `sweep2/`, the exact-HEAD review and the three-way check. §9 records the staged hashes. |
| 8 MAJOR (requests, disk, free space) | **Resolved** | Requests are the note's values via fix G (= S2-M1 precondition 2e). They are re-derived from the full-chunk re-measurement, and the disk caveats are stated. "Safe" is dropped. §4.7 bases free space on the tars for the submit host and the untarred copy for `/ceph`, without the GGUF. §5.2 checks `DiskUsage` / `MemoryUsage`. |
| 9–17 MINOR | **Resolved** | These are fixed:<br>• validator wording (§2);<br>• per-chunk port, with §4.3's identity rule extended to `server.port`;<br>• STOP additions (§8);<br>• fix C's per-chunk `min_live_nodes` (§2);<br>• validation inside `render_jdl` (§4.3);<br>• `-dry-run <file>` (§4.4);<br>• PLAN rows (§4.1);<br>• the slowest node in the canary (§5.1);<br>• operational index ≠ `r1.c3_sweep_index/1` (§7);<br>• the `refuse_sealed` deviation flagged (§7);<br>• the slot count (§3, §5.3). |

## Remaining minor items (non-blocking)

**R2-1. MINOR — the S2-M1 note still says sweep 2 is "resumable".**
- The accepted S2-M1 redraft (`11db0f65`, Job layout) still says "Resumable only by the collector's A.5 resume and the wrapper's resume pin check".
- The hand-off's §6 now says, correctly, that no resume path exists. Line 17 says the note wins where the two differ.
- The note's line does not authorize a resubmission: a fresh re-run is not an A.5 resume, and §6 and §8 forbid resubmission without the author. Still, the conflict should not be left for the cluster agent to resolve.
- **Fix:** add one sentence to §6: "The note's 'resumable' line does not create a resume path; until fix H exists, no resubmission without the author." Also flag the note line for the author, to amend when copying the note.

**R2-2. MINOR — "failing worker runs" as a STOP is too broad.**
- §8 reads "Failing or mismatched worker runs or worker environment (fix E)".
- Some worker runs fail legitimately inside a healthy campaign, for example a node's `invalid_config` rejection. The invalid-trial rules exist for exactly this case, and D28 tolerates an invalid rate below 30 %.
- Read literally, the STOP would halt a valid sweep. That fails safe, but it is noisy.
- **Fix:** make the STOP cover a failing or mismatched worker environment, zero successful runs in a chunk, or a pre-declared failure share. Fix C/E defines the share. Otherwise the counts are just reported. §5.2 already reads this way.

**R2-3. MINOR — where the worker-run counts come from.**
- The current job record has no worker-run success/failure counts, and sweep 1's `collection_checks.json` has none either.
- Unless a fix writes them, the agent would have to count from the sealed ledgers or tails, which hold metric values.
- **Fix:** have fix E (or C) write worker-run ok/failed counts, LLM calls and parse failures into the job record or `collection_checks.json`. The redacted projection then needs only those fields. An explicit field allowlist for the projection would help.

**R2-4. MINOR — the S2-M1 version is not pinned.**
- Line 17 says the values follow "the S2-M1 redraft" without a commit.
- **Fix:** cite `mac-s2-m1-redraft-20261116`, accepted at `11db0f65` (record `e43faa29`).
- The fix letters differ between the two documents: hand-off E/F/G against note 2a–2e. The hand-off cross-references them (fix G = 2e), and saying that F overlaps 2e would remove the last ambiguity.

**R2-5. MINOR — what happens to other jobs during a STOP.**
- §6 and §8 say "stop, preserve, report". They do not say whether other chunks that are already running continue, or whether their outputs are sealed. `condor_rm` without the author is barred, so in practice they continue.
- **Fix:** say "running jobs continue; their outputs are sealed as usual; no new submission until the author decides".

**R2-6. NIT — template and naming.**
- `"port": <18110 + chunk number>` is an unquoted placeholder, so the template is not valid JSON as written. That is acceptable as a template, but say "18110 + chunk number from §3" (18111…18126).
- §10 says "the sweep index" where §7 says "operational index". Use one name.

## Re-verified in round 2

- Every concrete value from round 1's verified list is unchanged in the new text: digests, hashes, URL, size, CPU model, chunk ids, harness, noise source, seal and render commands.
- The new statements about the code match `acae9fde`:
  - `render_jdl` inputs, fresh stage, fixed 128000 / 50000000, `ON_EXIT`;
  - `_precreate` truncation;
  - `seal()` single path and refusal;
  - `run_job` writing the record only at the end, with hard-coded `output_use` / `ctx`;
  - `resolve_label` schema;
  - `validate_spec` enforcing ctx 16384 and the flag presence, but not `n_gpu_layers` 99 or `--no-webui`.
- The hotfix list (six commits `f4a85da1` … `c8d07994`) and the accepted bases `70e3a116` / `235c9e5f` match the branch log and the review records.
- Consistency with the accepted S2-M1 (`11db0f65`):
  - re-measurement and worker-runs precondition (its 4 and note 1);
  - 2e (requests, record `ctx`, `output_use`);
  - CPU value/requirement (2d);
  - S2-C5 seal comparison;
  - D8 lock and the `refuse_sealed` remark;
  - projection STOP, (g)2, (g)4, no B.2.
  The only conflict is R2-1.
- The removed text loses nothing still needed. The deleted "resume pin mismatch" STOP and "batch-by-batch sealing" hint are moot or covered.
- The template is honestly gated: the header says "nothing here may be pasted as-is: the template needs fixes A–G", and each `[fix X]` / `<…>` placeholder is present.

Not verified (as in round 1): anything on the hosts.

---

# Independent review — S2-M3 cluster hand-off (Paper B / R1), round 3

- **Unit:** `docs/r1/proposals/S2_M3_CLUSTER_HANDOFF_20261116.md`, worktree `/tmp/pb/wt/s2m3`, branch `mac-s2-m3-handoff-20261116`.
- **Reviewed base:** `a5f21dbbdefd4580566254b36361f4640ce9fad6`. It is one commit on `e05eaea7` and changes only the hand-off (+15/−6). The worktree is clean.
- **Reviewer:** the same independent read-only reviewer. I confirmed the change with `git diff e05eaea7 HEAD`. No commits, no state-changing git, no network.

VERDICT: ACCEPT

All six round-2 minor items are resolved. The diff adds no new problem, and none of the round-1 or round-2 resolutions has regressed.

## Round-2 items: status

| R2 | Status | Check in the diff |
|---|---|---|
| R2-1 (the note's "resumable" line) | **Resolved** | §6 now says the S2-M1 line "authorizes nothing beyond what exists; with the current wrapper it means no resume", and flags it for the author to amend. This removes the conflict with line 17's "note wins" rule. |
| R2-2 (worker-failure STOP too broad) | **Resolved** | §8 now covers a worker-environment failure or mismatch, zero successful runs in a chunk, or a failure share above a bound declared before launch in fix C/E. It gives the reason (legitimate `invalid_config` trials; D28 allows an invalid rate below 30 %). The §5.2 canary bullet matches and points to §8. |
| R2-3 (source of the counts) | **Resolved** | The fix F row now asks fix C or F to write worker runs ok/failed, LLM calls and parse failures into the record. The redacted projection is a field allowlist, so no sealed ledger has to be read. |
| R2-4 (S2-M1 version) | **Resolved** | Line 17 cites `mac-s2-m1-redraft-20261116` @ `11db0f65`, review record `e43faa29`. Both exist: the worktree `/tmp/pb/wt/s2m1b` HEAD is `e43faa29` and its parent is `11db0f65`. Fix F is noted as overlapping S2-M1 2e. |
| R2-5 (running jobs during a STOP) | **Resolved** | §6: running jobs continue and are sealed when they finish. Nothing new is submitted until the author decides. This is consistent with the ban on `condor_rm` without the author. |
| R2-6 (port placeholder; index naming) | **Resolved** | The port is now a quoted placeholder, "18110 + chunk number, i.e. 18111…18126", which matches §3's numbering 1–16. §10 says "operational index", as §7 does. |

## Notes (no action needed)

- The filled spec must carry `server.port` as an integer, since `validate_spec` requires a positive int. The quoted placeholder is clearly a template marker, like the other `<…>` values, and §4.3's validation inside `render_jdl.py` would catch a string.

## Re-verified

- Outside the six edits, the diff touches no concrete value. Digests, hashes, URL, size, CPU model, chunk ids, harness, noise source, layout figures, seal and render commands, and the STOP and report structure are as verified in rounds 1 and 2.

Not verified (as before): anything on the hosts.
