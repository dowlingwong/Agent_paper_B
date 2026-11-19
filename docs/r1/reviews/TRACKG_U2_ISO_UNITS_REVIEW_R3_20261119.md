# Independent review R3 — Track G G.0 U2 isolated-node units, five nodes (19 November 2026)

**Reviewer.** Fresh independent third-round reviewer (`u2-iso-unit-reviewer-r3`), delegated by the coordinator
after the round-2 review; no involvement in drafting the units or in the round-1/round-2 fixes. Read-only: the only
file written is this review record (uncommitted). No unit or code edit, no commit/push/delete, no GPU/U2/census
run, no Ada login, no HTCondor/deepthought. The five unit files and the worktree documents were read in place; the
authority documents that exist only on published `main` (the port-isolation report and its review, and the
`R1-TRACKG-PORT-DECISIONS` / `R1-HARNESS-ISOLATION` PLAN rows) were read with `git show origin/main:…` (no
checkout, no write).

**Objects under review.** Five one-node U2 raw-cost units, **revision 3**, in `docs/r1/proposals/u2_iso_20261119/`
(all untracked; **79 lines each**):

| Unit | sha256 (canonical bytes) |
|---|---|
| `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md` | `77c61820e8183c2ef753677e44bea56f4909816b4a51e621360e63f389fd3448` |
| `U2_ISO_MLAB_IMDB_UNIT_20261119.md` | `8f13a8e24493ad97861d14f3515a81734e7b23ff0992453fc8f51be8e1842d4c` |
| `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` | `d81d1cc307e8c0506d8262c0e6f4796595009f20e0871e9efb36df0a6c61b45a` |
| `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` | `1bc7daaede89c711cea6962137d255de9d3e076a105c18e9f487c7bd43e621f8` |
| `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` | `316a33efcc39a38d9708bc79d710e69058608e45458fd19b7183edb82534dbeb` |

The five are one template with node-specific substitutions (verified by normalized diff: only the kit-branch line,
data-manifest line, licence line and pre-run-reference line differ between nodes; the three MLAB units share
manifest/kit lines and the two MLGym units share them). Findings below therefore cite the template's line numbers;
each node's own file carries the identical line.

**Verdict summary: all five units ACCEPTED — 0 BLOCKING, 0 MAJOR, 10–12 MINOR each.** The three round-2 MAJORs
(M1 peak VRAM, M2 cgroup construction, M5 census pin convention) are closed in substance and, for M5, the
inverted hard-coded pins are replaced by a correct, non-hard-coded convention. The remaining findings are
MINOR record/command-text items; a small pre-execution set is listed as conditions per unit. No unit may be
executed on the strength of any *other* unit's verdict; each is separately accepted and separately executable once
for its own node, one smoke, no timeout/OOM retry.

**Worktree and authority state.** Worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`,
HEAD **`1cc54d81`** (`ops-tasl-20261116`), merge-base with published main `45fb94cc`; `origin/main` =
**`de3de54fd22dcdd86215be0924307e36a64ed08b`** = authority `de3de54f`. Only untracked: the unit directory and the
R1/R2/R3 review files. The worktree's `docs/r1/PLAN.md` carries `R1-TRACKG-G0-GO:1258` and
`R1-TRACKG-LICENCES:1269` but not `R1-TRACKG-PORT-DECISIONS:1289` / `R1-HARNESS-ISOLATION:1290`; those two rows
and `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` resolve **only against published `main` `de3de54f`**, as
the round-2 review also recorded.

**Authority read.**
- `R1-TRACKG-G0-GO` (`origin/main:docs/r1/PLAN.md:1258`): one node per unit, each unit independently reviewed,
  ENGINEERING_ONLY, re-check idle card/sharing/Paper A gate each time, no noise floor/D21/D28.
- `R1-HARNESS-ISOLATION` (`:1290`): separate process for editable code, append-only metric log, cgroup-wide kill,
  any run with more than one metric line is refused.
- `R1-TRACKG-PORT-DECISIONS` (`:1289`): (3) imdb baseline written by the port — accepted provided it is frozen and
  independently reviewed before any label run, and the **census funnel and appendix** note "baseline written by
  us"; (4) node timeout = census-measured baseline × 3, a timeout is the proposal's failure, not an infrastructure
  rerun; census on Python 3.12.
- Port report `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2 (how every node runs), §3(3)
  (imdb freeze/disclosure: `train.py` written by the port, `BASELINE_SHA256
  01dcb7c4352d4c80495856542683c1c02412fc2da5824c41503e31283215a50a` in `nodes/mlab_imdb/LICENCES.md`, disclosure
  sentence "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us; MLAgentBench ships only a skeleton
  for this task"), §7 steps 2–4; its review `origin/main:docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md`
  (round 4 **ACCEPTED**).
- Accepted kit update `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`, sha256
  **`fe232e2b…`** (= the committed bytes at HEAD `1cc54d81`; reviewed bytes were `3c3ae74a…`), and its review
  `worktree:docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`, sha256 `d8c68f9f…`, **ACCEPTED**, 0
  BLOCKING / 0 MAJOR, conditions C-K1…C-K5.
- Isolation-fix review `worktree:docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md`, sha256
  `c8e468c7…`, **ACCEPTED**; C2 = this kit update, C3 = no autoresearch GPU run until the logits-transfer decision
  + `cuda_open` init fix are reviewed (the five accepted units do not include autoresearch).
- Kit-update captures `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119_captures/`:
  `SHA256SUMS` verified **`341/341` OK, rc 0**; the `pins/new_*.json` / `deployed_*.json`, five
  `smoke/attempt2/<node>/{s000_baseline,s001,…}/run_record.json`, the five smoke logs (with `CHECKLIST_E_PASSED`
  and `# worktree tip:`), the `gpu_before.txt`/`gpu_after.txt` snapshots, the setup logs and the accepted helper
  `scripts/smoke_one.sh`.
- Prior accepted U2 pattern: `reports/trackg_g0_20261117/TRACKG_U2_AR_RESULT_20261117.md` and its review
  `reviews/TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md` (§9 is the result-record standard, and the accepted result
  itself records the 1 s card-level sampler maximum **32,228 MiB** as a **labelled upper bound including
  co-tenants**, not the baseline footprint).

**Method and limits.** A paper review plus capture cross-check. No GPU/U2 run, no Ada login, no live-host state
claimed beyond what the accepted kit-update and fix reviews already verified. Every node value below was
re-derived from the accepted kit report §2–§7, the captured smoke logs (`# worktree tip:`), the captured
`s000_baseline/run_record.json` files (`elapsed_seconds_info_only`, `outcome.value`,
`determinism.torch_version`, `frozen_pin_sha256`), the captured setup logs (`AR_DATA manifest_sha256`), and
`pins/new_*.json` vs `pins/deployed_*.json`.

---

## 1. Round-2 findings — closure status

| Round-2 finding | Status in revision 3 | Where |
|---|---|---|
| **M1 peak VRAM** (MAJOR) | **CLOSED.** The 1 s `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` sampler is required; the result must record sampler command/interval/output path/maximum; the label is now a single defined **whole-smoke upper bound over the GPU(s) used, not a per-run peak and not attributed to the baseline process tree**; "do not call it a per-run peak" is explicit. Residual MINOR (mR2): the "unless a PID-tree mapping is available" clause is undefined/inert, and the max is not pinned to per-process-row vs per-sample sum. | `:51-57`, `:64` |
| **M2 cgroup** (MAJOR) | **CLOSED.** `CG`/`AR_TEST_CGROUP_PARENT` are computed **inside** the `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'` scope, so they cannot point at the caller's cgroup; the command's quoting/order are coherent; the intended `--memory-limit` value equals the accepted smoke's and the records' `limits.external_limit` (the unit wraps it across two lines inside the quotes — see mR1(e)); the `memory.max` (=8G) / `memory.swap.max` (=0) enforcement read is now required and in the result field list. Residual MINOR (mR1): the block omits the accepted smoke's `cd <kit>`, `PYTHONDONTWRITEBYTECODE=1` and `scope_cgroup` echo, so the probe path referenced after start is not resolvable in the launching shell as written; no explicit STOP on a non-8G read. | `:34-48`, `:64` |
| **M5 census pin convention** (MAJOR) | **CLOSED — the inversion is gone.** No pin hex is hardcoded anywhere in the five units (grep-verified: the only pin occurrence is the word `frozen_pin_sha256` in the explanatory sentence); the unit requires the kit's **committed-file `frozen_pin_sha256`** (accepted kit update §3/§10.2, `pins/new_*.json`) and the **deployed run-record pin** (`deployed_*.json` / the run record) recorded separately with no interchange, and directs the **census row to the committed-file pin**. This matches the accepted sources exactly. Residual MINOR (mR3): "separately from the launch record" is imprecise. | `:15-19`, `:66` |
| m1 report citation | **RESOLVED** for the report path (§2/§7, and the explicit "not a PLAN row of that name"); residual MINORs: mR8 (the accepted kit-update report/review are not cited by path/sha) and mR8b (imdb/ogbn licence lines do not cite `R1-TRACKG-LICENCES`). | `:4-8`, `:28` |
| m2 3 × B1 timeout | **RESOLVED.** `--provisional-timeout 1800`; node timeout = 3 × measured B1, recorded; no timeout/OOM retry. | `:58-61` |
| m3 setup/static tests | **PARTIAL → MINOR (mR4).** The instruction exists ("Record the setup command/manifest and the CPU-masked static-test result before the run") but the result-field list still omits the setup command/log path+sha, the CPU-masked static-test command/result/mask and the interpreter (the manifest sha itself is listed, but not the setup/verify log that produced it, nor the file count/size, read-only bit or `du`/`df`). | `:26-27` vs `:61-68` |
| m4 gate capture | **PARTIAL → MINOR (mR5).** "Captured immediately before launch" and "gate capture" are required, but not the JSON path/sha256/UTC, the newest `live_*` == configured run dir, or the self-excluded `pgrep` result. | `:20-22`, `:66` |
| m5/n4 result file/row | **PARTIAL → MINOR (mR6).** `CHECKLIST_E_PASSED` and "8 executed + refused diff" are back and present; still missing per-run `run_record.json`/`run.log` paths+sha256, `killed_with`, `determinism.not_forced`, one JSON line per run, node-spec/representative-edit manifest shas, and the result-file name/path/sha. | `:61-68` |
| m-n1 pins abbreviated | **RESOLVED** — the units no longer quote pins at all, so no abbreviated/inverted value can be copied. | `:15-19` |
| m-n2 metric field names | **PARTIAL and newly inaccurate → MINOR (mR7).** The result must record the metric but the wording is "(`val_bpb`/accuracy as the kit reports)"; `val_bpb` is the **autoresearch** metric and does not apply to these five torch nodes (their records carry `outcome.value` and `sealed.test_accuracy`, and no `peak_vram`/`val_bpb` field). The node's validation metric should be named per its kit spec/result channel. | `:61-62` |
| m-e GPU floor basis / mid-run rule | **PARTIAL → MINOR (mR9).** ≥ 8 GiB free + no other user's compute app + before/mid/after census + STOP on an unrecorded card switch are required; still no basis for 8 GiB (the kit's measured torch peak is ~2.85 GB, so 8 GiB is ≈2.8× but unstated), no rule if free VRAM falls below baseline peak + 2 GiB or a co-tenant appears mid-run, and "unrecorded card switch" permits a *recorded* switch. | `:49-51` |
| m-n3 scope/STOP residue | **PARTIAL → MINOR (mR10).** Still "no force push" rather than "no push"; no explicit autoresearch (C3-blocked) / HousePrice (STOP) / Breakout (not run) exclusion; no "no other host" beyond HTCondor/deepthought; disk threshold without filesystem(s)/footprint accounting; no resumability statement. | `:7-8`, `:69-72` |
| m6 MLGym licence | **RESOLVED.** Both MLGym units now carry `R1-TRACKG-LICENCES`, the CC BY-NC 4.0 non-commercial-with-notice scope and "the gymnax-derived Apache-2.0 parts are not used by this node" (matches port decision (1) and port report §3(1)). | `:28` |
| m7 imdb baseline provenance | **PARTIAL → MINOR (mR11).** The line now says the baseline was written by us (the core of the port-decision (3) note) and that it is frozen/reviewed, but the required disclosure sentence (DistilBERT fine-tuning / MLAgentBench ships only a skeleton) and the census-funnel/appendix duty are not carried, and "disclosed" is asserted without saying where. | `:28` |
| m8 no-deletion/preserve | **RESOLVED** — "no deletion" and "preserve, do not delete". | `:8`, `:68` |
| m9 s001 refused vs executed | **RESOLVED** — "every **executed** record effective:true", the refused `s001` is `executed:false` and not a failure; the STOP is qualified "any executed record". Verified in the captures: every `s001` record is `executed:false`, `outcome:null`, no isolation fields. | `:29-33`, `:71` |

**M3/M4/M6 status (the round-2 "resolved as defined" items).** M3 (validated command/env/`which python` and the
recorded resolved invocation) is still present — `PYTHONPATH=src`, the env `bin` first on `PATH`, `VIRTUAL_ENV`,
`CUDA_VISIBLE_DEVICES=""`, `AR_TRACKG_DATA_ROOT`, `taskset -c <cpus>`, `--gpu-uuid/--cpus/--memory-limit/
--runs-root/--provisional-timeout`, and "record `which python` and the resolved invocation" (`:37-48`, `:46-47`) —
with only the MINOR command-text deviations mR1. M4 (≥ 8 GiB free / no other user's compute app / before-mid-after
census / STOP on an unrecorded switch) is present with the mR9 residues. M6 (scope/STOP set: gate, kit, data/env,
other users, non-effective/waivers, synthetic, timeout/OOM, any executed record non-effective, disk < 50 GiB with
the 100 GiB cap, cross-node/evidence/T1) is present with the mR10 residues. `CHECKLIST_E_PASSED` + 8 executed runs +
the refused `s001` diff, no-deletion/preserve, and the `s001` `executed:false` distinction are all present (rows
m5/n4, m8, m9).

**Direct answer on the three round-2 MAJORs: all three are closed.** M1 and M2 are now the required construction,
not a partial one; M5's inverted hard-coded pins are removed rather than swapped, which is strictly safer than the
round-2 remedy. The 10–12 residuals are MINOR and are enumerated below; none changes the procedure, scope,
measurement identity, kit bytes or STOP set.

---

## 2. M5 — pin/convention detail (round-2 MAJOR, now closed)

Unit text (`:15-19`, all five):
> **Pins:** record the kit's **committed-file `frozen_pin_sha256`** (the value from accepted kit update §3/§10.2,
> the one the census commits) and the **deployed run-record pin** separately from the launch record; do not
> interchange them, and do not hardcode either in this unit (the kit update report's `pins/new_*.json` vs
> `deployed_*.json` define the convention). The census row uses the committed-file pin.

**Independent verification of the two sources (no unit value is taken on trust):**

| node | committed-file pin (accepted kit report §3 table "new pin (committed node files)"; = `pins/new_*.json` `pin`) | deployed run-record pin (= `pins/deployed_*.json` and every captured `s000_baseline` record's `frozen_pin_sha256`) |
|---|---|---|
| mlab_cifar10 | `1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2` | `a459b3d823075953d05422594cc97fa743723f22e79e1f8368480007dd041388` |
| mlab_imdb | `4b1019a60b1ac96028944d1dcc02be582f84e1fab0dbfd11d00011f460fb97fb` | `c169a6b875733cdb03d223659d06cc9a6839dd6255a924c420f10982bbefbbb0` |
| mlab_ogbn_arxiv | `bd71fdf4c6b3a66715cb602a41a7a1f5bdeeaa6e23439c558a96c2bda061c9d7` | `5ff5824ac22783f05f84b84d6d3222e8f1f4ddbc118e6bb1f657041bfb3285ad` |
| mlgym_cifar10 | `2d7e533b2a1075000d15a21445f98b94d7df2cf527baff0264f3ae306f93022e` | `817c90340e7ae004b7cd7161f899cb159a91ae482febc9a7f9ea2d9969f76e62` |
| mlgym_fmnist | `eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3` | `ef8043389dbd55a9a01d192227f0483daf2a406043b0a1feaf74eba4d858ddee` |

- The kit report §3 deployed-pin note is right and is what the unit now points at: after `setup_command` links
  `data/`, `frozen_file_hashes` hashes the symlink as `data: link:<absolute target>`, so the run record's
  `frozen_pin_sha256` is the **deployed** pin (17 frozen entries) while the §3 table is the **committed-file** pin
  (16 entries). §10 item 2 repeats the convention and warns against comparing the two; review **C-K5** says "the
  census must commit the pins with the stated convention (committed-file pin, §3 table)".
- **Correct / unambiguous / sufficient:** yes for the round-2 defect. The units contain no pin values and no
  placeholder pins, so the round-2 inversion cannot be copied; the committed vs deployed roles are named, the
  census row is told to use the committed-file value, and the report's pin captures are cited as the convention.
  Grep confirms the only pin occurrence in each unit is the word `frozen_pin_sha256`.
- **Residual MINOR mR3:** "separately from the launch record" is imprecise — no "launch record" is defined, and
  the deployed pin is a per-run-record field (`run_record.json` → `frozen_pin_sha256`, identical for the runs of
  one smoke) rather than something captured at launch. Reword to name the two source artifacts (kit report §3
  table / `pins/new_*.json`; the run records / `pins/deployed_*.json`) and require both as full 64-hex values in
  the result, so the census row cannot silently take the truncated report prefixes.

---

## 3. M2 — cgroup construction detail (round-2 MAJOR, now closed)

Unit text (`:37-48`, all five):
```
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c
'CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG;
export PYTHONPATH=src; export PATH=…/envs/torch312/bin:$PATH;
export VIRTUAL_ENV=…/envs/torch312;
export CUDA_VISIBLE_DEVICES=""; export AR_TRACKG_DATA_ROOT=…/data;
taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node <node> --gpu-uuid <UUID>
--cpus <cpus> --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0
(enforced cgroup)" --runs-root <outside-repo>/u2_iso_<node>_<UTC> --provisional-timeout 1800'
```

Compared against the accepted `TRACKG_ISO_KIT_UPDATE_20261119_captures/scripts/smoke_one.sh` (the script that
produced the accepted attempt-2 records), lines 26–39:

| element | accepted `smoke_one.sh` | unit rev 3 | assessment |
|---|---|---|---|
| outer scope | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'` | identical | match |
| `CG`/`AR_TEST_CGROUP_PARENT` | computed **inside** the scope; `CG=$(cut -d: -f3 /proc/self/cgroup)` | identical, inside the scope | match — cannot point at the caller cgroup |
| scope path evidence | `echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"` | not echoed | deviation (MINOR) |
| cwd | `cd "$HOME_DIR"` inside the scope | not shown; depends on caller cwd | deviation (MINOR) |
| env | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, `PATH=…/envs/torch312/bin:$PATH`, `AR_TRACKG_DATA_ROOT`, `CUDA_VISIBLE_DEVICES=""` | `PYTHONPATH=src` (no `PYTHONDONTWRITEBYTECODE`), same `PATH`, extra `VIRTUAL_ENV`, same data root and CUDA mask | substantive match; minor omissions/extra |
| interpreter | absolute `$PY = …/envs/torch312/bin/python` | `python` resolved by the exported `PATH` (first entry is the same env bin) | equivalent |
| `--memory-limit` string | `"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)"` (one line) | same text, but wrapped across two lines **inside** the double quotes | intended value is identical and equals the run records' `limits.external_limit` (verified in the five captured baseline records); a literal copy preserves the newline+indent — see mR1(e) |
| CPU affinity | `taskset -c <CPUS>` | `taskset -c <cpus>`, `--cpus <cpus>` | match |

- **Coherence:** the single-quoted outer script contains no embedded single quotes, so the line-wrapped text is
  one well-formed argument to `bash -c`; inside it, `$CG` and `$PATH` expand, the double-quoted `--memory-limit`
  argument is re-parsed by the inner shell and is not subject to the outer quoting, and every statement is
  `;`/newline-separated with `taskset` last. Order (CG → exports → command) is right.
- **Cannot point at the caller cgroup:** inside `systemd-run --user --scope`, the launched `bash` runs in the
  transient scope's cgroup; `/proc/self/cgroup` therefore yields the scope path (captured smoke log:
  `scope_cgroup=/sys/fs/cgroup/user.slice/user-1030.slice/user@1030.service/app.slice/run-…scope`; the records'
  `limits.cgroup_parent` is that scope). The 8 GiB cap and the per-run child cgroups therefore bind the smoke,
  which is the round-2 defect fixed.
- **Enforcement probe:** required ("read and record `$AR_TEST_CGROUP_PARENT/memory.max` (must be 8G) and
  `memory.swap.max` (0) as the enforcement probe") and in the result list (`:64`); enforcement capability itself
  was already verified on this host (the accepted AR U2 review: a delegated `MemoryMax=64M` scope reads
  `memory.max = 67108864`, `memory.swap.max = 0`, and a 200 MB overshoot is SIGKILLed).
- **Residual MINOR mR1:** (a) add `cd <kit worktree root>` inside the scope (or state the block is run from the
  kit worktree root) — otherwise `PYTHONPATH=src` / `-m tests.trackg.port_smoke_gpu` depend on the caller's cwd;
  (b) restore `PYTHONDONTWRITEBYTECODE=1` (the accepted script sets it to keep the kit worktrees free of
  `__pycache__`); (c) echo `scope_cgroup=$AR_TEST_CGROUP_PARENT` inside the scope so the probe path is available
  after start — as written, `$AR_TEST_CGROUP_PARENT` is unset in the launching shell and cannot be read there;
  (d) state the expected bytes (`8589934592` and `0`) and add an explicit STOP if the read does not equal them.
  (e) give the `--memory-limit` value on **one** line: the markdown wraps it inside the double quotes, so a
  literal copy would append a newline+indent to the recorded `limits.external_limit` and diverge from the accepted
  value. These are text-level, do not change the reviewed construction, and are pre-execution conditions below.

---

## 4. M1 — peak-VRAM detail (round-2 MAJOR, now closed)

Unit text (`:49-57`, all five) requires a card with ≥ 8 GiB free and no other user's compute app; before, once
mid-run and after `nvidia-smi` free/used/utilization + compute-app census; STOP on no qualifying card or an
unrecorded card switch; a **1 s** `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1`
sampler for the whole smoke; and the label:

> these torch nodes have no per-run peak field. Report the sampler maximum as a **whole-smoke upper bound over
> the GPU(s) used, not a per-run peak and not attributed to the baseline process tree** unless a PID-tree mapping
> is available; record the sampler command, interval, output path and maximum in the result. A labelled
> whole-smoke upper bound is acceptable for U2; do not call it a per-run peak.

- **The query is valid and available on this host.** `--query-compute-apps` accepts `gpu_uuid`, `pid`,
  `used_memory`; the accepted smoke used exactly this query (without `-l`) in `smoke_one.sh:25,43` and the
  captured `gpu_before.txt`/`gpu_after.txt` files are its output, so the fields resolve on driver 545.23.08.
- **The "no per-run peak field" premise is verified:** the five captured torch `s000_baseline/run_record.json`
  files contain no `peak_vram`/VRAM field (only the autoresearch run logs carry `AR_INFO peak_vram_mb=…`; grep over
  the captures confirms it is absent from all five torch baseline records), so a sampler is the
  only route and the round-1/2 requirement is the right one.
- **The label is no longer self-contradictory in operation.** One measurement is chosen (whole-smoke sampler),
  it is explicitly *not* a per-run peak, and the result list (`:64`) requires "sampler command/interval/output/max
  (whole-smoke upper bound label)", closing round-2 M1 item 3. This also matches the accepted U2 precedent, where
  a 1 s sampler maximum of 32,228 MiB was recorded as a labelled whole-smoke upper bound including co-tenants,
  explicitly not the baseline footprint (`TRACKG_U2_AR_RESULT_20261117.md`).
- **Residual MINOR mR2:** (a) "unless a PID-tree mapping is available" is undefined and inert here — the worker
  runs in a PID namespace and no mapping method is given, and a whole-smoke maximum could not become a
  baseline-tree attribution even if one were; drop the clause or define the mapping and a separate baseline-window
  measurement. (b) "sampler maximum" should be pinned: max single-row `used_memory`, or the per-sample sum over
  the used card's rows (the latter is the conservative "upper bound"); say which, and say the upper bound includes
  co-tenants by construction. (c) state that the sampler is started before the `systemd-run` and stopped after it,
  and that the CSV header line is not counted in the maximum. (d) say explicitly that `val_bpb` is the
  autoresearch metric (see mR7; related but recorded separately).

---

## 5. Node-specific values — independent verification

| Unit | Suite / node | Kit branch @ tip (matches captured smoke log `# worktree tip:` and kit report §2/§7) | `data_manifest.json` sha256 (matches captured setup log and kit report §5) | Pre-run reference `time / metric` (matches captured `s000_baseline` `elapsed_seconds_info_only` / `outcome.value`) | env |
|---|---|---|---|---|---|
| mlab_cifar10 | MLAgentBench / `mlab_cifar10` | `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` | `43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3` (`files=4`) | `12.859 s / 0.5152` (record: 12.859, 0.5152) | `envs/torch312`, torch `2.6.0+cu124` |
| mlab_imdb | MLAgentBench / `mlab_imdb` | same @ `fb6e7d73…` | `a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c` | `61.399 s / 0.9048` (record: 61.399, 0.9048) | same |
| mlab_ogbn_arxiv | MLAgentBench / `mlab_ogbn_arxiv` | same @ `fb6e7d73…` | `9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c` | `5.702 s / 0.275982` (record: 5.702, 0.275982) | same |
| mlgym_cifar10 | MLGym / `mlgym_cifar10` | `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf` | `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` | `24.07 s / 0.491` (record: 24.07, 0.491) | `envs/torch312`, torch `2.6.0+cu124` |
| mlgym_fmnist | MLGym / `mlgym_fmnist` | same @ `f07875de…` | `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` | `26.702 s / 0.861667` (record: 26.702, 0.861667) | same |

Also correct in every unit: exactly one node/suite per unit and no cross-node authorisation or pooling (line 3,
line 8); ENGINEERING_ONLY census with no evidence / no noise floor / D21 / D28, no T1 label (line 7); Ada host
`ucrtasl` only (line 20); 3×B1 timeout rule and no timeout/OOM retry (lines 58–60); `envs/torch312` with Python
3.12.16 / torch 2.6.0+cu124 (`TRACKG_U2_DATA_PREP_20261117.md:11` and the records' `determinism.torch_version`
confirm both), with only Breakout using `envs/jax312` (kit report §9); data root outside the repository and no
synthetic marker; `git rev-parse HEAD` == tip + `git status --porcelain --untracked-files=no` clean as the launch
check (holds with the runtime `data` symlinks); one idle GPU, `--gpu-uuid`, `--cpus`, runs-root outside the repo,
`--provisional-timeout 1800`; isolation fields required on every executed record, synthetic/non-effective =
STOP; the refused `s001` record handled correctly; pre-run values explicitly labelled **reference only**; no unit
claims a U3/unisolated run, a T1 label run, or an excluded/blocked node. The kits are the post-update tips and
the data manifests are post-update.

---

## 6. Process — kit-update report sha, review corrections, and stale text

- The worktree kit-update report is sha256 **`fe232e2b…`** (350 lines) and is now **committed at HEAD
  `1cc54d81`**; `git show HEAD:…` hashes to the same bytes. The accepted review records the reviewed bytes
  `3c3ae74a…` and conditions C-K1…C-K4 (with C-K5 the process condition on pushing/pin convention).
- I re-verified every required correction is present in the current/committed text: **C-K1** six untracked data
  links (`:323`) and the correct 01:52:57Z pre-run GPU snapshot with the 02:08Z artifact identified as
  `paper_a/gate_smoke_20261119T020823Z.json` (`:167`); **C-K2** `smoke/chain_{A,B}_attempt2.log` and the
  `summary_<node>` vs `records_<node>` distinction (`:341`); **C-K3** the explicit "C2-mandated BLOCKED-state
  check … C3 stays in force for the future U2" wording (`:277`); **C-K4** (optional nit) the `~2.85 GB
  (2,853 MiB)` rounding is applied and the "each node's card … after its own runs" qualification is added
  (`:175-177`), while the optional parenthetical that the other card carried the concurrent chain is not (C-K4
  was explicitly optional). No unit relies on any byte that changed: the units take only the §3 pin convention, the §5 manifests and the §7 tips/values, none of which the
  corrections touched, and no unit cites the report sha or the §6/§8/§11/§12 text that changed.
- Authority currency: the cited PLAN rows and the port report/review exist only on published `main`
  `de3de54f`, not in this worktree's tree; the units' citations resolve against published main, and the branch
  carrying this review must not be cited as if those rows were in its own tree until it merges main.
- **Residual process discrepancy (not a per-unit finding).** The committed kit report still says the kit branches
  are "not pushed" (`:4`, `:34`, `:330`, §10.1), while the HEAD commit that committed it is titled
  "…kit branches pushed". The units are unaffected (their launch check is local `git rev-parse HEAD` == tip and a
  tracked-clean worktree, which holds either way), but the operator should not cite the report's push status as
  current; annotate/correct it before a census record cites it. I did not verify push status myself (the harness
  repository is on Ada and this review is read-only with no Ada login).

---

## 7. Unit verdict — `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_cifar10`; kit `mac-trackg-iso-mlab-20261117` @ `fb6e7d73…`; data
manifest `43fdf860…`; pre-run `12.859 s / val 0.5152`; `envs/torch312`; no U3 claim. Pin convention correct
(committed `1f047ad7…` / deployed `a459b3d8…`, neither hardcoded). Cgroup command correct, `CG` inside the scope.
Licence line cites `R1-TRACKG-LICENCES`.

**Findings (file:line).** MINOR: mR1 `:37-48`; mR2 `:51-57`,`:64`; mR3 `:15-19`; mR4 `:26-27` vs `:61-68`;
mR5 `:20-22`,`:66`; mR6 `:61-68`; mR7 `:61-62`; mR8 `:4-8`; mR9 `:49-51`; mR10 `:7-8`,`:69-72`.

**Verdict: ACCEPTED** (0 BLOCKING, 0 MAJOR, 10 MINOR).

**Conditions.** Before the single smoke: apply mR1 (command `cd`/`PYTHONDONTWRITEBYTECODE`/`scope_cgroup` echo +
probe expected bytes/STOP, one-line `--memory-limit`) to the launch command, and mR7 (record the node's validation metric, not `val_bpb`).
mR2–mR6, mR8–mR10 are satisfied in the result record. One smoke only; no retry; do not execute any other node
under this verdict.

## 8. Unit verdict — `U2_ISO_MLAB_IMDB_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_imdb`; same kit/tip `fb6e7d73…`; data manifest `a87254e1…`; pre-run
`61.399 s / val 0.9048`; `envs/torch312`; no U3 claim. Pin convention correct (committed `4b1019a6…` / deployed
`c169a6b8…`). Cgroup command correct. Licence/provenance line (`:28`) now says the baseline was written by us and
is frozen/reviewed, but it is still a paraphrase: it drops the required port-decision (3) disclosure sentence
("The mlab_imdb baseline (DistilBERT fine-tuning) was written by us; MLAgentBench ships only a skeleton for this
task") and the duty to carry it in the census funnel and appendix (neither document exists yet — port report
§3(3)).

**Findings (file:line).** MAJOR: none. MINOR: mR1 `:37-48`; mR2 `:51-57`,`:64`; mR3 `:15-19`; mR4 `:26-27` vs
`:61-68`; mR5 `:20-22`,`:66`; mR6 `:61-68`; mR7 `:61-62`; mR8 `:4-8` (kit-update report/review path/sha);
**mR8b** `:28` (`R1-TRACKG-LICENCES` row not cited); mR9 `:49-51`; mR10 `:7-8`,`:69-72`; **mR11** `:28`
(port-decision (3) disclosure sentence + funnel/appendix duty).

**Verdict: ACCEPTED** (0 BLOCKING, 0 MAJOR, 12 MINOR).

**Conditions.** Before the single smoke: apply mR1, mR7 and mR11 (carry the port-decision (3) sentence and the
funnel/appendix duty into the unit and the result row) and mR8b to the launch command/record template. mR2–mR6,
mR8–mR10 in the result record. One smoke only; no retry.

## 9. Unit verdict — `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_ogbn_arxiv`; same kit/tip `fb6e7d73…`; data manifest `91312162…`;
pre-run `5.702 s / val 0.275982`; `envs/torch312`; no U3 claim. Pin convention correct (committed `bd71fdf4…` /
deployed `5ff5824a…`). Cgroup command correct. Licence line (`:28`) is a bare "OGB/arXiv: generic
research citation/disclosure" without the `R1-TRACKG-LICENCES` row.

**Findings (file:line).** MAJOR: none. MINOR: mR1 `:37-48`; mR2 `:51-57`,`:64`; mR3 `:15-19`; mR4 `:26-27` vs
`:61-68`; mR5 `:20-22`,`:66`; mR6 `:61-68`; mR7 `:61-62`; mR8 `:4-8`; **mR8b** `:28`; mR9 `:49-51`; mR10
`:7-8`,`:69-72`.

**Verdict: ACCEPTED** (0 BLOCKING, 0 MAJOR, 11 MINOR).

**Conditions.** Before the single smoke: apply mR1, mR7 and mR8b. mR2–mR6, mR8–mR10 in the result record. One
smoke only; no retry.

## 10. Unit verdict — `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md`

**Node-specific check.** MLGym / `mlgym_cifar10`; kit `mac-trackg-iso-mlgym-20261117` @ `f07875de…`; data manifest
`c0ef1168…`; pre-run `24.07 s / acc 0.491`; `envs/torch312` is the correct environment (only Breakout uses
`envs/jax312`); no U3 claim. Pin convention correct (committed `2d7e533b…` / deployed `817c9034…`). Cgroup
command correct. Licence line (`:28`) is adequate: `R1-TRACKG-LICENCES`, CC BY-NC 4.0 non-commercial with
notice, and the gymnax-derived Apache-2.0 parts stated not used by this node (port decision (1) / port report
§3(1)).

**Findings (file:line).** MAJOR: none. MINOR: mR1 `:37-48`; mR2 `:51-57`,`:64`; mR3 `:15-19`; mR4 `:26-27` vs
`:61-68`; mR5 `:20-22`,`:66`; mR6 `:61-68`; mR7 `:61-62`; mR8 `:4-8`; mR9 `:49-51`; mR10 `:7-8`,`:69-72`.

**Verdict: ACCEPTED** (0 BLOCKING, 0 MAJOR, 10 MINOR).

**Conditions.** Before the single smoke: apply mR1 and mR7. mR2–mR6, mR8–mR10 in the result record. One smoke
only; no retry.

## 11. Unit verdict — `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md`

**Node-specific check.** MLGym / `mlgym_fmnist`; same kit/tip `f07875de…`; data manifest `8d28287b…`; pre-run
`26.702 s / acc 0.861667`; `envs/torch312` correct; no U3 claim. Pin convention correct (committed `eb60107e…` /
deployed `ef804338…`). Cgroup command correct. Licence line (`:28`) now matches the MLGym pattern and the
round-2 m6 gap is closed: `R1-TRACKG-LICENCES`, CC BY-NC 4.0 non-commercial with notice, Apache-2.0 parts not
used by this node, Fashion-MNIST generic citation.

**Findings (file:line).** MAJOR: none. MINOR: mR1 `:37-48`; mR2 `:51-57`,`:64`; mR3 `:15-19`; mR4 `:26-27` vs
`:61-68`; mR5 `:20-22`,`:66`; mR6 `:61-68`; mR7 `:61-62`; mR8 `:4-8`; mR9 `:49-51`; mR10 `:7-8`,`:69-72`.

**Verdict: ACCEPTED** (0 BLOCKING, 0 MAJOR, 10 MINOR).

**Conditions.** Before the single smoke: apply mR1 and mR7. mR2–mR6, mR8–mR10 in the result record. One smoke
only; no retry.

---

## 12. Summary and required fixes

| Unit | BLOCKING | MAJOR | MINOR | Verdict | sha256 |
|---|---|---|---|---|---|
| `mlab_cifar10` | 0 | 0 | 10 | **ACCEPTED** | `77c61820…` |
| `mlab_imdb` | 0 | 0 | 12 | **ACCEPTED** | `8f13a8e2…` |
| `mlab_ogbn_arxiv` | 0 | 0 | 11 | **ACCEPTED** | `d81d1cc3…` |
| `mlgym_cifar10` | 0 | 0 | 10 | **ACCEPTED** | `1bc7daae…` |
| `mlgym_fmnist` | 0 | 0 | 10 | **ACCEPTED** | `316a33ef…` |

**MINOR findings (shared unless marked mR8b/mR11):**
- **mR1** `:37-48` — command block: add `cd <kit worktree root>` and `PYTHONDONTWRITEBYTECODE=1`; echo
  `scope_cgroup=$AR_TEST_CGROUP_PARENT` inside the scope; specify how the `memory.max`/`memory.swap.max` probe is
  read after start (the launching shell does not carry the variable), state the expected bytes `8589934592` / `0`,
  add an explicit STOP if not, and put the `--memory-limit` value on one line (the markdown wrap would otherwise
  become part of the recorded `limits.external_limit`).
- **mR2** `:51-57`, `:64` — M1 wording: drop/define the PID-tree-map clause; pin "sampler maximum" (max row vs
  per-sample sum over the used card); note co-tenant inclusion; sampler start/stop and header exclusion.
- **mR3** `:15-19` — M5 wording: replace "separately from the launch record" with the two named source artifacts
  and require full 64-hex values for both.
- **mR4** `:26-27` vs `:61-68` — add the setup command/log path+sha (and manifest file count/size, read-only bit,
  `du`/`df`) and the CPU-masked static-test command/result/mask/interpreter to the result fields (the manifest
  sha itself is already listed).
- **mR5** `:20-22`, `:66` — gate capture detail: JSON path/sha256/UTC, newest `live_*` == configured run dir,
  self-excluded `pgrep` form+result.
- **mR6** `:61-68` — result row: per-run `run_record.json`/`run.log` paths+sha256, `killed_with`,
  `determinism.not_forced`, one JSON line per run, node-spec/representative-edit manifest shas, result-file
  name/path/sha.
- **mR7** `:61-62` — metric names: `val_bpb` is the autoresearch metric and does not apply to these torch nodes;
  record the node's validation metric per its kit spec/result channel (the smoke records `outcome.value`; the
  sealed value is `sealed.test_accuracy`).
- **mR8** `:4-8` (all) — cite the accepted kit-update report/review by path+sha.
- **mR8b** `:28` (imdb, ogbn only) — cite `R1-TRACKG-LICENCES` in the licence line.
- **mR9** `:49-51` — state the 8 GiB floor basis (kit's measured ~2.85 GB torch peak; prior accepted run-1 floor
  was 24 GiB); add a mid-run contamination rule (free VRAM < baseline peak + 2 GiB or a new co-tenant in the
  baseline window → STOP/record); "no unrecorded switch" should be "no switch from the launch card".
- **mR10** `:7-8`, `:69-72` — "no push" (not only "no force push"); explicit autoresearch (C3-blocked) /
  HousePrice (STOP) / Breakout (not run) exclusion; "no other host" beyond HTCondor/deepthought; disk
  filesystem(s)/footprint; no-resume statement (an interrupted unit re-runs whole from a new `<runs-root>`).
- **mR11** (imdb only) `:28` — carry the port-decision (3) disclosure sentence and the census-funnel/appendix
  duty.

**Required before execution (pre-execution conditions):** per unit, apply **mR1** and **mR7** to the operator's
launch command/record template; for imdb also **mR11**, and for imdb/ogbn also **mR8b**; then the result record
must satisfy mR2–mR6 and mR8–mR10. These are literal text/recording corrections and, as in the accepted prior U2
pattern, do not need a further independent review round: they change no procedure, scope, measurement identity,
STOP set or kit byte.

**Independence and scope.** Each unit names exactly one node/suite with its own kit tip, data manifest, run root
and pre-run reference; nothing is pooled, and the three MLAB units share the mlab kit while the two MLGym units
share the mlgym kit, as `R1-TRACKG-G0-GO` expects. Because the units are one template, mR1–mR10 are replicated in
all five (plus mR8b in imdb/ogbn and mR11 in imdb); each unit is nevertheless separately accepted and must be separately executed and recorded — acceptance
of one is not acceptance of any other, and no unit authorises autoresearch (C3), HousePrice, Breakout, a T1
label/sweep, another host, or a rerun. A timeout/OOM is the proposal's failure and is not retried.

---

## 13. Attestation and command record

This review is the only file written (uncommitted). I did not run the smoke or any GPU/U2/census job, did not
edit the units or any code, did not commit/push/delete anything, and did not log in to Ada or touch HTCondor,
deepthought, TASL-7/TASL-2. No live-host state is claimed beyond what the accepted kit-update and fix reviews
already verified; every unit value above is re-derived from those accepted records and their captures.

Read-only operations (19 Nov 2026, Europe/Berlin): `pwd`/`git rev-parse HEAD` (`1cc54d81`),
`git rev-parse origin/main` (`de3de54f`), `git merge-base` (`45fb94cc`), `git status --short`,
`git log`/`git ls-files`/`git show HEAD:…` (kit report at `1cc54d81` = `fe232e2b…`); `cat -n` of the five units;
normalized `diff` of the units (template uniformity); `sha256sum` of the five units (`77c61820…`, `8f13a8e2…`,
`d81d1cc3…`, `1bc7daae…`, `316a33ef…`), the kit report (`fe232e2b…`), the kit review (`d8c68f9f…`) and the fix
review (`c8e468c7…`); `sha256sum -c SHA256SUMS` in the kit-update captures (**rc 0, 341/341 OK**); `git show
origin/main:docs/r1/PLAN.md` rows `R1-TRACKG-G0-GO:1258`, `R1-TRACKG-LICENCES:1269`,
`R1-TRACKG-PORT-DECISIONS:1289`, `R1-HARNESS-ISOLATION:1290`; `git show
origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` (§2, §3(3), §7) and its review (round-4 ACCEPTED);
reads of `TRACKG_ISO_KIT_UPDATE_20261119.md` §1–§12, its review, the fix review's conditions C1–C4, the prior U2
AR result and its R2 review; `cat -n scripts/smoke_one.sh`; `cat pins/new_*.json` and `pins/deployed_*.json`;
Python reads of the five `s000_baseline/run_record.json` and the five `s001/run_record.json`; `grep` of the five
smoke logs (`# worktree tip:`, `CHECKLIST_E_PASSED`), the setup logs (`AR_DATA manifest_sha256`), and the torch
records for `peak_vram`/`val_bpb` (absent); `grep` of the units for pin hexes (absent) and for the report/review
citations.
