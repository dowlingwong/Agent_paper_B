# Independent re-review R2 — Track G G.0 U2 unit `mlgym_houseprice` (isolated kit, CPU) (20 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-houseprice-reviewer-r2`), delegated by the coordinator; no involvement
in drafting the unit, the kit update, the five-node U2 campaign, the Breakout unit or any of their reviews. Read-only:
the only file written is this review record (uncommitted). No unit/code edit, no commit/push/delete, no run/GPU/U2/census
job, no Ada login, no HTCondor/deepthought. Read-only verification used the already-present shallow clone of the
published harness kit at `/tmp/u2review/harness_mlgym` (HEAD `f07875de…`, tracked-clean), one network `git ls-remote`
read, and a local `bash -n` syntax check of the unit's launch-command text using scratch files under `/tmp` (no smoke
and no unit was executed).

**Object under review.** `docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md`, sha256
**`397ccfd1d985d8e265a1dc1d6ad687ee8265947ea05282e3c38a1ae3df463551`**, **75 lines**, 6,223 bytes, untracked at review
time (mtime `2026-11-20T22:39:35`); status "proposed unit; run only after a fresh independent review accepts it". This is
the round-2 revision of the unit; the round-1 object was `d45b4431…` (61 lines), reviewed **NOT ACCEPTED** (0 BLOCKING,
1 MAJOR, 16 MINOR) in `docs/r1/reviews/TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_20261120.md` (sha256 `36774ed5…`).

**Verdict summary: ACCEPTED — 0 BLOCKING, 0 MAJOR, 17 MINOR, conditional on C1–C7.** The round-1 **MAJOR is closed**:
the unit now names the correct **committed-file** pin `88d359f2…`, requires reading it from the accepted kit update
§3/§9 / `pins/new_mlgym.json` at launch, keeps the **deployed run-record pin separate**, and directs the **census to the
committed-file pin**; the wrong value (`eb60107e…`, `mlgym_fmnist`'s committed pin) is gone and the file contains no
other pin. I recomputed the committed pin from the kit tip's own bytes and reproduced the captured cifar10/fmnist
committed *and* deployed pins exactly, so the method and the value are sound (full value
`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`, 16 frozen entries). The 16 round-1 MINORs have all
been partially applied; most are now record/citation gaps of the accepted R3/Breakout class. The one **remaining
pre-execution defect that would stop a literal launch** is m4: the launch command is still source-wrapped inside the
single-quoted `bash -c` script and the unit does not carry the accepted "must be one physical line" sentence — a literal
copy fails with a shell syntax error (verified below). One new MINOR, n1: the unit still embeds the truncated correct
pin and does not require recording both pins as full 64-hex values. **No BLOCKING and no MAJOR was found; no execution
until C1–C4 are applied to the launch notes, and C5–C7 are satisfied in the result/execution.**

## 1. Authority, method and limits

**Authority read** (all read-only; full shas verified in this session):

- The delegation names published main `de3de54f…` as the authority baseline. The worktree (`ops-tasl-20261116`) HEAD is
  **`6bbf4b3e3aa6ec411dc183ea9e5d3f35333e1404`** (tracked-clean), `origin/main` has advanced by two docs-only sweep-2
  commits to **`df58bcd5`**, merge-base HEAD/origin = **`94db94bb`**. I re-read the cited rows on `origin/main`:
  `R1-TRACKG-G0-GO` (`:1258`), `R1-TRACKG-LICENCES` (`:1269`), `R1-TRACKG-PORT-DECISIONS` (`:1289`, including **(2)
  House Prices from the user's Kaggle file with `--from-file`, hashes recorded, MLGym's copy not used, and (4) timeout =
  census baseline × 3 as the proposal's failure**), `R1-HARNESS-ISOLATION` (`:1290`), and the 20 November row
  `R1-TRACKG-G3-EARLY` (`:1330`: `mlgym_houseprice` joins T1 "as soon as their U2 passes"). The two newer `origin/main`
  commits are docs-only and touch no cited row/byte used by this unit.
- Port report `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2 (how every node runs; §2(2) House
  Prices from the user's Kaggle file) and §7 (steps for the experiment agent), sha256 **`78d354b8…`**; its review
  ACCEPTED (round 4).
- Accepted kit update report `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`, sha256
  **`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`** (committed at worktree HEAD; reviewed bytes
  `3c3ae74a3788…`), and its review `docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`, sha256
  **`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`**, ACCEPTED (0 BLOCKING / 0 MAJOR; conditions
  C-K1…C-K5). Captures: `SHA256SUMS` verified in this session **341/341 OK, 0 FAILED, rc 0**; `pins/new_mlgym.json`
  sha256 **`8974359b1fd5c11105dc98b593dcb1c84b33d59896fe3e63bf7cb6c3b1e4a451`**, `pins/deployed_mlgym.json` sha256
  **`dcfcb0808445c0af2ee851a27047be89202420f340e815d6f9ad0443b1ea4ee0`** (the latter has **no `mlgym_houseprice` entry** —
  its deployed pin can only come from this node's future run records).
- Harness-isolation fix review `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md`, sha256 **`c8e468c7…`**
  (ACCEPTED; condition C3 keeps the autoresearch U2 GPU run blocked).
- Accepted prior U2 pattern/standards: five-node units + R3 review `docs/r1/reviews/
  TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md`, sha256 **`99daf16d…`** (ACCEPTED; the **"no pin hex hardcoded in the
  unit"** convention, mR1–mR11); Breakout unit + review `docs/r1/reviews/TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md`,
  sha256 **`217822fe…`** (ACCEPTED, 14 MINOR, conditional C1–C7 — including the explicit "the launch command must be one
  physical line" sentence now in that unit); prior raw-cost review `docs/r1/reviews/
  TRACKG_U2_RAWCOST_REVIEW_20261117.md`, sha256 **`c18e25df…`** (MAJOR-5 = the House Prices `--from-file` requirement;
  MINOR-1/3/4/5 = the static-test, B1-basis, timeout-classification and disk conditions).
- 19 November follow-up `docs/r1/prompts/FOLLOWUP_PROMPTS_20261119.md` (`:26`) and
  `docs/r1/prompts/EXPERIMENT_AGENT_PROMPT_20261118.md` (`:55`): the recorded author path was
  `~/r1_inputs/house-prices/train.csv`; the kit update §9 records `/home/dowling/r1_inputs` absent on 19 Nov, so the node
  was a per-node STOP.

**Method and limits.** Paper review plus independent recomputation from the published kit. I confirmed the harness
branch `mac-trackg-iso-mlgym-20261117` on the origin (`github.com/dowlingwong/autoresearch_harness`) at
**`f07875de79a5a57739227b13e0fd52d31646edaf`** by `git ls-remote --heads`, matching the read-only clone's HEAD. I read the
node spec, `prepare_data.py`, `run_fixed_budget.py`, `ar_data.py`, `run_smoke`/`port_support.py`,
`port_smoke_gpu.py`, the SMOKE table, `check_smoke`, `frozen_file_hashes`, `LICENCES.md` and `requirements.txt`, and
recomputed both pin roles from the tip's own bytes (below), validating the method against the captured cifar10/fmnist
committed and deployed pins. I also verified the *formatting* defect of the launch command by extracting it verbatim and
running `bash -n` on (a) the literal multi-line copy and (b) the joined one-line form. I did **not** log in to Ada and
claim no live-host state: the author file's presence/bytes on Ada, the Paper A gate, the CPU co-tenancy, and the kit
worktree state at launch are not independently verified here; the unit's launch checks and conditions C1–C4 must capture
them.

**Record note (not a unit defect).** The kit update report's §10.1/§11 still says the three kit branches are
local-only/not pushed; that wording is now stale — `git ls-remote` shows `mac-trackg-iso-mlgym-20261117` =
`f07875de…` on the origin (and `ar`/`mlab` at `448f682…`/`fb6e7d73…`). No unit byte depends on the push status.

## 2. Round-1 closure — the MAJOR is closed

| Round-1 finding | R2 status | Unit lines |
|---|---|---|
| **M1** (MAJOR): hardcoded **wrong** committed pin | **CLOSED** — correct pin named, read-from-kit required, deployed separate, census commits committed; no wrong pin present | `unit:25-29` |
| m1 author-file provenance/verification not recorded; path differs from the 19 Nov instruction path | PARTIAL — path move + hashes + "hash == MLGym copy, informational" + no-copy stated; host-verification/placement/download evidence still not required | `unit:11-21` |
| m2 "source path/hash appear" is wrong (the manifest has no source path) | PARTIAL — the correct "records the file name, not the path" note was added, but the old wrong phrase remains at `:35`; `provided_by`/`source.sha256`/`md5`/no-synthetic checks and the `AR_DATA` line are still not spelled out | `unit:18-19` vs `:35` |
| m3 setup re-statement drops guards/context | PARTIAL — guards (`test -n`), exact command, log, manifest sha and "setup failure = STOP" added; still no "run from the node dir, `envs/torch312/bin` first on PATH", no "move aside an old/other-source `--out`", no setup-log path+sha in the record | `unit:30-36` |
| m4 source-wrapped launch command | **OPEN — remaining pre-execution MINOR** — still wrapped across 8 source lines; no "must be one physical line" sentence | `unit:47-56` |
| m5 probe read path ambiguous | PARTIAL — expected bytes `8589934592`/`0` + mismatch STOP + `scope_cgroup` record present; the "read it from the echoed `scope_cgroup` path / inside the scope" explanation is still missing | `unit:55-56` |
| m6 Paper A gate too vague | PARTIAL — criteria + JSON+UTC capture present; exact command and JSON field names still missing | `unit:40-41` |
| m7 CPU co-tenancy too vague | PARTIAL — before/mid/after load/jobs/users/CPU count + disturbed=STOP present; idle CPU-set record, load threshold and 8 GiB basis still missing | `unit:41-43` |
| m8 B1/B2 definitions | PARTIAL — 3 × B1, provisional 1800 s, no retry present; B1/B2 definitions and "timeout/OOM = proposal failure" still missing | `unit:58-61` |
| m9 no CPU-masked static-test requirement | PARTIAL — "run the CPU-masked static tests (or record why not)" added; command/result/mask/interpreter/log sha and the expected baseline counts still missing, and "(or record why not)" allows skipping | `unit:58-61` |
| m10 result-standard fields incomplete | PARTIAL — many fields added (per-run record/log/result-channel shas, `killed_with:null`, `determinism.not_forced`, node-spec/rep-edit shas, sealed source, executed-unit copy, SHA256SUMS); still missing `returncode`/`timed_out`, `determinism.shim_loaded`, one JSON line per run, result-file name/path/sha, host/boot, manifest file count/size/read-only, `du`/`df`, 100 GiB cap, cgroup-kill/log-intact | `unit:62-67` |
| m11 isolation field list incomplete | PARTIAL — `effective:true`/`waivers {}`/`exceptions []` + "non-effective isolation" STOP present; `log_intact`, result channel, `cgroup.kill` still missing | `unit:65-66` |
| m12 licence citation vague | PARTIAL — now cites `R1-TRACKG-LICENCES`, CC BY-NC 4.0 non-commercial/attribution/changes, Kaggle terms, only `train.csv`, no MLGym copy; still omits "the gymnax-derived Apache-2.0 parts are not used by this node" and the census row/appendix duty | `unit:37-39` |
| m13 citation gaps | PARTIAL — kit update path+sha `fe232e2b…`, reviewed bytes `3c3ae74a…`, C-K1…C-K4 and "and review" present; still no kit-update review path/sha (`d8c68f9f…`), no C-K5, no `R1-TRACKG-G3-EARLY`, no 19 Nov follow-up instruction, no authority main/commit | `unit:3-9` |
| m14 launch check imprecise | PARTIAL — "HEAD==tip and tracked-clean" present; exact `git rev-parse HEAD` / `git status --porcelain --untracked-files=no` (untracked runtime `data` link permitted) and the `kit.txt` record still missing | `unit:26`, `:43` |
| m15 scope/STOP residues | PARTIAL — STOPs now include no push/deletion, no other host (TASL/HTCondor/deepthought), non-effective isolation, disk < 50 GiB; still "no force push" at `:9`, no no-resume, no explicit autoresearch/Breakout/other-node exclusion, no env-freeze-mismatch STOP, no 100 GiB cap, no resolved-invocation record | `unit:9`, `:67-69` |
| m16 no launch env/import/freeze check | PARTIAL — `which python`, "env import check" and "env freeze" present; versions vs requirements pins (numpy 2.5.4 / pandas 3.1.1 / scikit-learn 1.9.1), the freeze sha and a mismatch STOP still missing | `unit:43` |
| — new **n1** | MINOR — truncated correct pin still embedded; no "record both pins as full 64-hex"; deployed source artifact not named | `unit:27-29` |

For traceability: the round-1 review's condition C5 says "m10–m12, m17", but its findings table carries only m1–m16 — a
numbering slip in that record (the intended item is the result-field set, m10). The round-1 review's bytes are unchanged.

## 3. M1 detail — pin identity (verified, not taken on trust)

**The pin value is correct and is this node's committed pin.** At kit tip `f07875de…` I recomputed the committed-file
pin from the node's own 16 frozen entries (spec `frozen_paths` minus the absent `data/`: `run_fixed_budget.py`,
`ar_worker.py`, `ar_parent.py`, `ar_isolated.py`, `ar_data.py`, `prepare_data.py`, `requirements.txt`, `LICENCES.md`,
`representative_edits/**`), hashing each regular file and computing
`sha256(json.dumps(files, sort_keys=True))` = **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`**.
That equals the accepted kit update §3 table row `mlgym_houseprice` "new pin (committed node files)" (`:91`), its §9
("The node's pin was updated (`88d359f2…`)"), and `pins/new_mlgym.json`'s `pin` (`8974359b…`, 16 files). **Method
validation:** the same code reproduces the captured `mlgym_cifar10` committed `2d7e533b…` + deployed `817c9034…` and
`mlgym_fmnist` committed `eb60107e…` + deployed `ef804338…` exactly, so the recomputation is sound.

**No wrong pin remains.** A hex-token scan of the whole unit finds only `88d359f2` as a pin; `eb60107e…` (fmnist's
committed pin) is absent. The unit states the role correctly: committed-file pin read from the accepted kit update
§3/§9 / `pins/new_mlgym.json` at launch and recorded; the deployed run-record pin recorded separately; **the census uses
the committed-file pin** (`unit:27-29`). This is exactly the accepted convention (kit update §10.2 / C-K5; R3 M5/mR3),
and it closes the round-1 census-integrity defect.

**Residual (n1, MINOR).** The unit still embeds the truncated literal `88d359f2…` in the explanatory sentence, whereas
the accepted five-unit convention is "no pin hex in the unit" (R3 M5: grep shows only the word `frozen_pin_sha256`), and
the R3 mR3 residue explicitly requires recording **both pins as full 64-hex values** so the census cannot silently take
a truncated prefix. The correct expected value as a sanity check is harmless, but the unit should (a) remove or clearly
label it as expected-only, never to be copied, and (b) add "record both as full 64-hex values" and name the deployed
source artifact (the run records; note `pins/deployed_mlgym.json` has no `mlgym_houseprice` entry). Informational
expected deployed value with the unit's data root: **`4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144`**
(17 entries including `data: link:/home/dowling/r1_trackg_20261117/data/mlgym_houseprice`) — the actual value must be
recorded from the run records. The unit's setup path
(`AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data`, `--out "$AR_TRACKG_DATA_ROOT/mlgym_houseprice"`) and
`ar_data.link_data` (symlink target `…/data/mlgym_houseprice`) are consistent with that expectation.

## 4. Author `train.csv` — PASS on hash/path/no-copy; MINOR provenance record

**Hashes — correct and consistent.** `unit:16-17` gives full sha256
**`1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`** (prefix `1e18addf`, suffix `929d41` — correct,
including the earlier `…5929d41` typo not repeated), md5 **`80ccab65fb115cbad143dbbd2bcd5577`**, and "450 K / 1,461
lines" (consistent with 460,676 B and 1,460 data rows + header). These are the values recorded in
`nodes/mlgym_houseprice/LICENCES.md:36` and `run_fixed_budget.py:34` (`MLGYM_COPY_SHA256`) and in the accepted records.

**Path / `--from-file` / no copy — correct in form.** `unit:13-14` uses
`/home/dowling/house-prices-advanced-regression-techniques/train.csv`, states the deliberate move from the earlier
`~/r1_inputs/house-prices/train.csv`, "**no copy**", and "record the actual path beside the hashes". `unit:30-34` passes
that path through the spec's exact `setup_command`
(`test -n "$AR_TRACKG_DATA_ROOT" && test -n "$AR_HOUSEPRICE_TRAIN_CSV" && python3 prepare_data.py --out
"$AR_TRACKG_DATA_ROOT/mlgym_houseprice" --from-file "$AR_HOUSEPRICE_TRAIN_CSV"`). `unit:19-21` correctly says the hash
equals MLGym's forwarded copy and that `same_as_mlgym_copy` is **informational only**, while the setup must still use the
author's file; `run_fixed_budget.py:49-54` refuses a non-synthetic manifest whose `source.provided_by` is not the user
download, and prints `AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=…`. There is no MLGym copy in the setup and
"only `train.csv`" is stated.

**Residual m1 (MINOR).** The section heading "Input (author-supplied) — **verified**" still overclaims: no
verification record is given. The committed prompts record only the 19 Nov `~/r1_inputs/house-prices/train.csv` path, and
the kit update §9 records `/home/dowling/r1_inputs` absent, so the 20 Nov placement at the new path is an assertion with
no committed record. The result must record the author placement (date/quote), the on-host verification
(`sha256sum`/`md5sum`/`stat` output, bytes, mtime), the download date and the Kaggle competition URL
(`https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques`). This does not block the run (the
hash check is a STOP and the file identity is guarded), but it must be captured.

**Residual m2 (MINOR; one wrong phrase survives).** `unit:18-19` was correctly added ("the manifest records the file
name, not the path; do not conflate"), but `unit:35` still says "confirm `synthetic` is false and the **source path/hash
appear**". The manifest's `source` is exactly `{kaggle, provided_by, from_file_name, sha256, md5, rows}` and has **no
path** (`prepare_data.py`); the required checks are `source.provided_by` starts with "user download",
`source.sha256` == the file digest, `md5` present, no `synthetic` marker, plus the manifest sha256, the `AR_DATA` line and
the exact `--from-file` path. Fix the contradiction before launch.

## 5. Setup, data manifest and environment

`unit:30-36` gives the spec's guarded setup, records command/rc/log/manifest sha256, and makes a setup failure a STOP —
the substance of the round-1 C2. `prepare_data.py` confirms the surrounding rules: `--out` must lie under
`$AR_TRACKG_DATA_ROOT`; a non-empty `--out` without a manifest is refused ("move it aside"); a re-run accepts only a
manifest recording the user download, and a `--from-file` given again must be the same file; the directory is made
read-only and `data/` is linked into the node dir; the manifest is named `data_manifest.json`.

**Residual m3 (MINOR).** The setup context is still incomplete: the unit does not say to `cd` to the node dir
(`third_party/mlgym/nodes/mlgym_houseprice`, where `prepare_data.py` lives and where `data/` is linked), to put
`envs/torch312/bin` first on `PATH` (the script imports pandas), and to move aside an old/other-source `--out` (the
port report §7 step 2 explicitly requires it; the accepted `setup_node.sh` capture shows the `cd`, the log and the
`readlink data`/manifest-sha records). It also does not name `envs/torch312` for the setup interpreter explicitly
beyond "Env `envs/torch312`". The script fails closed with an actionable message, so this is a record/text residual, not
a blocking one, but the launched setup log should be preserved with path+sha.

## 6. Kit identity, host, licence and isolation

**Kit tip — correct.** `unit:25-26` names `mac-trackg-iso-mlgym-20261117` @
`f07875de79a5a57739227b13e0fd52d31646edaf`; the origin head is exactly that commit and the clone's HEAD is it. The tip is
the post-fix/post-pin commit the accepted kit update §2/§7 names.

**CPU node / environment — correct.** `unit:36`, `:43`, `:56` say CPU node, `envs/torch312` (Python 3.12.16,
scikit-learn/pandas), no GPU, **no `--gpu-uuid`**. The kit agrees: `port_smoke_gpu.py:27`
`CPU_ONLY_NODES = frozenset({"mlgym_houseprice"})` and the argument check makes `--gpu-uuid` optional only for it; the
spec's `notes.python_env: torch` is "scikit-learn and pandas only; no GPU use"; `requirements.txt` pins
`numpy==2.5.4 pandas==3.1.1 scikit-learn==1.9.1`; the smoke's `SMOKE` entry uses `torch_node=False` and `budget=1`.

**Licence — PASS with the m12 citation residue.** `unit:37-39` records the MLGym task `regressionKaggleHousePrice`
CC BY-NC 4.0 non-commercial with attribution and changes in `LICENCES.md`, the Kaggle terms, "only `train.csv`", "no
MLGym copy", and cites `R1-TRACKG-LICENCES`; this matches the spec's `license` line and `LICENCES.md:11-19,30-36`.
Residual: add "the gymnax-derived Apache-2.0 parts are not used by this node" (true here; the accepted MLGym units carry
it) and the census row/appendix duty, and make the result "licence" field name those duties.

**Isolation requirement — correct.** `unit:65-66` requires every executed record `isolation.effective:true`,
`waivers {}`, `exceptions []`, and the STOP list makes "non-effective isolation" a STOP; the spec's isolation block has
no exception and the host-check/fix reviews show this is achievable on this host. Residual m11: add `log_intact`, the
result channel, `cgroup.kill`, and the explicit "any executed record not effective / with waivers or exceptions = STOP"
wording.

**Residual m13 (MINOR).** The authority block cites the kit update report path+sha and reviewed bytes plus C-K1…C-K4,
and says "and review" — but not the review path/sha (`d8c68f9f…`), not C-K5 (the pin/push convention), not
`R1-TRACKG-G3-EARLY` (the row whose purpose this unit serves), not the 19 Nov follow-up instruction that defines this
node's path, and not the authority main/commit. These are citation completeness, not procedure.

**Residual m16 (MINOR, pre-execution).** `unit:43` says "which python, env import check" and `unit:66` lists "env
freeze", but no versions-vs-requirements comparison (`numpy 2.5.4 / pandas 3.1.1 / scikit-learn 1.9.1`), no
`uv pip freeze` sha, and no env-freeze-mismatch STOP. Add all three (Breakout M-3/M-4 analogue; the `envs/torch312`
freeze already holds those exact versions).

## 7. Command, cgroup, probe and timeout

**Inside-scope cgroup construction — PASS.** `unit:47-54` is the accepted construction: the outer
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`, with `CG` and
`AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG` computed **inside** the scope, `echo scope_cgroup=…`, `cd <kit worktree root>`,
`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, the env `bin` first on `PATH`, `VIRTUAL_ENV`, `CUDA_VISIBLE_DEVICES=""`,
`taskset -c <cpus>`, the spec's smoke module with `--node mlgym_houseprice --cpus <cpus>`, the `--memory-limit` value
`external: systemd-run … (enforced cgroup)`, a runs-root **outside** the repository, and `--provisional-timeout 1800`.
The expected probe contents `8589934592` and `0` with "mismatch STOP" are present. This matches the accepted
`smoke_one.sh` capture and the accepted smokes' `limits.external_limit`.

**Residual m4 (MINOR — the main remaining pre-execution defect).** The block is still **source-wrapped inside the
single-quoted `bash -c` script**: `unit:48` ends `&& export`, `:49` ends `&& export`, `:50→:51` and `:51→:52` begin with
`&&`, and `:52→:53`/`:53→:54` continue the argument list. I verified the consequence empirically: after substituting the
placeholders, a literal copy of `unit:47-54` passes the blob to `bash -c` correctly at the outer level, but the inner
script fails `bash -n` at line 4 with `syntax error near unexpected token '&&'` (and the newline after a bare `export`
leaves `AR_TEST_CGROUP_PARENT`/`PYTHONPATH` unexported), whereas the joined one-line form parses `rc=0`. The failure is
safe-fail (before any run) but the launch as documented would not start. The accepted Breakout unit handles this by
keeping the wrapped block as documentation **and** stating "**The launch command must be one physical line** (join the
`&&` parts and keep `--memory-limit` one line)"; the revised unit carries only "`--memory-limit` one line". Add the
accepted sentence (or give a script) before launch. Round-1 classified this MINOR (m4), and I keep that severity.

**Residual m5 (MINOR).** The probe read path is still ambiguous: `$AR_TEST_CGROUP_PARENT` exists only inside the scope's
shell, so the launching shell must read the probe via the echoed `scope_cgroup=` path (or inside the scope while the
smoke runs); state when/how. The expected bytes and mismatch STOP are present.

**Timeout / B1/B2 — correct basis, m8 wording.** `unit:47` says the pre-run reference is none accepted (correct: the
kit-update House Prices smoke was a STOP, §9); B1/B2, `val_rmse` (`outcome.value`; spec `metric_name` minimize) and
sealed `test_rmse` (`test_metric_regex ^AR_TEST test_rmse=…`, `test_scored: true`) are stated; one fit (`steps 1`;
`read_budget("steps", exact=1)`); "node timeout = 3 × B1; provisional 1800 s; no timeout/OOM retry" matches port
decision (4). Residual m8: define B1 = `s000_baseline`'s `elapsed_seconds_info_only`, say B2 is the same-seed
repeatability baseline only, and state that a timeout/OOM is reclassified as the proposal's failure (port decision (4)),
not an infrastructure rerun.

**Residual m9 (MINOR, pre-execution).** The static test is now mentioned ("run the CPU-masked static tests (or record
why not)"), but the accepted standard records the exact command and result: mlgym kit, CPU-masked
`taskset -c 0-15`/`CUDA_VISIBLE_DEVICES=`/delegated user cgroup, interpreter `envs/torch312/bin/python`, `PYTHONPATH=src
PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`,
`python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"`, expected baseline **225 passed / 2 known
environment failures / 1 skipped / 6 deselected** (kit update §4), log path+sha. Give the command, the expected counts,
and remove the "or record why not" escape.

## 8. Gate, CPU co-tenancy and launch checks

`unit:40-43` requires the Paper A gate clear (`clear_finished`, key false, no Paper A process) immediately before
launch with the gate JSON + UTC, and CPU co-tenancy recording before/mid/after with a STOP if the host is too loaded or a
foreign job would be affected. Good substance. Residuals:

- **m6 (MINOR).** Give the accepted exact command `r1/scripts/paper_a_status.py --config
  r1/scripts/configs/paper_a_status_ada.json`, the three criteria including `paper_a_live_waiting_for_card: false` and
  `paper_a_processes: []`, and record the JSON path/sha/UTC immediately before launch (accepted unit `:20-22`; R3
  mR5; Breakout M-8).
- **m7 (MINOR).** Record the chosen idle CPU set (`<cpus>`), a load threshold, the before/mid/after snapshot, and the
  8 GiB cgroup basis; "disturbed = STOP" is present in prose but not in the STOP list.
- **m14 (MINOR, pre-execution).** "HEAD==tip and tracked-clean" is stated but not the accepted concrete check:
  `git rev-parse HEAD` == `f07875de…` **and** `git status --porcelain --untracked-files=no` empty (the untracked runtime
  `data` symlink permitted — it will exist after setup), recorded in `kit.txt` (Breakout M-5).

## 9. Result record and STOPs

`unit:62-69` now requires a broad accepted-standard result: B1/B2 elapsed+`val_rmse`+sealed `test_rmse` with the sealed
source (`AR_TEST test_rmse`), all edit outcomes, per-run record/log/result-channel shas, `killed_with:null`,
`determinism.not_forced`, node-spec/representative-edit shas, `CHECKLIST_E_PASSED` + 8 executed + refused `s001`,
isolation fields, cgroup probe, CPU/load census, gate JSON+UTC, host/kernel, env freeze, data manifest + source csv
sha256/md5, kit tip + both pins, licence, disk, executed amended unit copy, result directory path + own/sha, captures +
`SHA256SUMS`.

**Residual m10 (MINOR — result record).** Still missing from the accepted layout: `process.returncode`/`timed_out`,
`determinism.shim_loaded` (the per-edit records carry it; `check_smoke` asserts it), one JSON line per run / the ledger,
the result-file name/path/sha (only "result directory path + own/sha"), host/boot (driver not needed on CPU), the
data-manifest file count/size/read-only bit, `du`/`df` before/after, the 100 GiB cap (only the < 50 GiB STOP is given),
and the cgroup-kill/log-intact fields. The exact result directory
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_<UTC>/` is not named.

**Residual m15 (MINOR — scope/STOPs).** `unit:9` still says "no force push" while the STOP list says "no push/deletion"
— align to "no push". Add: no resume, explicit exclusion of autoresearch (C3-blocked), Breakout and the other census
nodes, the env-freeze mismatch STOP, the 100 GiB cap, and "record the resolved invocation". The no-other-host
(TASL/HTCondor/deepthought), non-effective-isolation, synthetic-marker, timeout/OOM and disk-STOP items are present.

**Verified expectations.** 8 executed records + the refused frozen-diff `s001` is correct for this node:
`port_smoke_gpu.py` runs baseline, frozen-diff (refused), broken diff and E1, then `run_smoke` runs E1–E4 and a second
baseline with the same seeds = 8 executed + refused `s001`; `port_smoke_gpu.main` prints `CHECKLIST_E_PASSED` after
`check_smoke` passes, and `check_smoke` asserts the same-seed repeat value, `killed_with:null`, `"sealed" not in
record`, and (for the per-edit records) `shim_loaded:true`. For `torch_node=False` the
`not_forced == ["dataloader_workers"]` check is not applied. The node's `frozen_paths` + the
`data` link give the 16-entry committed / 17-entry deployed pin split described in §3.

## 10. Findings (all MINOR; no BLOCKING, no MAJOR)

| ID | Severity | Unit lines | Finding |
|---|---|---|---|
| **M1** | **CLOSED (round-1 MAJOR)** | `unit:25-29` | Correct committed-file pin `88d359f2c594…` (= kit update §3/§9 / `pins/new_mlgym.json`, independently recomputed from the tip's 16 frozen entries), read-from-kit required, deployed pin separate, census commits the committed one; wrong `eb60107e…` gone. |
| m1 | MINOR | `unit:11-21` | Provenance record incomplete: "— verified" overclaims; no committed record of the 20 Nov placement (tracked prompts give the 19 Nov `~/r1_inputs` path; kit update §9 records it absent); add placement date/quote, on-host `sha256sum`/`md5sum`/`stat` (bytes, mtime), download date, Kaggle competition URL. |
| m2 | MINOR (pre-execution wording) | `unit:18-19` vs `:35` | `:35` still says "confirm … the source path/hash appear"; the manifest `source` has `{kaggle, provided_by, from_file_name, sha256, md5, rows}` and **no path**. Replace with `provided_by` starts-with-"user download", `source.sha256` == digest, `md5` present, no synthetic; record manifest sha256, the `AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=…` line and the exact `--from-file` path. |
| m3 | MINOR | `unit:30-36` | Setup context: add "cd to the node dir (`third_party/mlgym/nodes/mlgym_houseprice`), `envs/torch312/bin` first on `PATH`", "move aside an old/other-source `--out`" (port report §7 step 2; accepted `setup_node.sh`), and the setup log path+sha. |
| m4 | MINOR (mandatory pre-execution) | `unit:47-56` | Launch command still source-wrapped inside the single-quoted `bash -c` (breaks at `:48→:49`, `:49→:50`, `:50→:51`, `:51→:52`, `:52→:53`, `:53→:54`); a literal copy fails `bash -n` (`&&` at line start; bare `export`). Add the accepted "must be one physical line — join the `&&` parts" sentence (as Breakout unit `:53-54`) or give a script. |
| m5 | MINOR | `unit:55-56` | Probe read path ambiguous: `$AR_TEST_CGROUP_PARENT` lives only inside the scope; say "read via the echoed `scope_cgroup=` path (or inside the scope while the smoke runs)". Expected `8589934592`/`0` + mismatch STOP present. |
| m6 | MINOR | `unit:40-41` | Gate too vague: give the exact command (`paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`), `clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`, JSON path/sha/UTC. |
| m7 | MINOR | `unit:41-43` | CPU co-tenancy: add the chosen idle CPU set (`<cpus>`), load threshold, before/mid/after snapshots, 8 GiB cgroup basis; put "disturbed = STOP" in the STOP list. |
| m8 | MINOR | `unit:58-61` | B1/B2: define B1 = `s000_baseline` `elapsed_seconds_info_only`, B2 = same-seed repeatability, and "timeout/OOM = proposal failure" (port decision (4)); the 3 × B1 / 1800 s / no-retry text is correct. |
| m9 | MINOR (mandatory pre-execution) | `unit:58-61` | Static test: add command (`python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"`), mask/interpreter, expected counts (mlgym kit: 225 passed / 2 known env failures / 1 skipped / 6 deselected) and log path+sha; drop "(or record why not)". |
| m10 | MINOR | `unit:62-67` | Result record: add per-run `returncode`/`timed_out`, `determinism.shim_loaded`, one JSON line per run/ledger, result-file name/path/sha, host/boot, manifest file count/size/read-only, `du`/`df`, 100 GiB cap, cgroup-kill/log-intact; name the exact result directory. |
| m11 | MINOR | `unit:65-66` | Isolation list: add `log_intact`, result channel, `cgroup.kill`, and the explicit "any executed record not effective / with waivers or exceptions = STOP"; the effective/waivers/exceptions and "non-effective isolation" STOP are present. |
| m12 | MINOR | `unit:37-39` | Licence: add "the gymnax-derived Apache-2.0 parts are not used by this node" and the census row/appendix duty; `R1-TRACKG-LICENCES` and the NC/attribution/changes/Kaggle-terms/no-copy statements are present. |
| m13 | MINOR | `unit:3-9` | Citations: add the kit-update **review** path/sha (`d8c68f9f…`), C-K5, `R1-TRACKG-G3-EARLY`, the 19 Nov follow-up instruction, and the authority main/commit; the report path+sha and reviewed bytes are present. |
| m14 | MINOR (mandatory pre-execution) | `unit:26`, `:43` | Launch check: state `git rev-parse HEAD` == `f07875de…` and `git status --porcelain --untracked-files=no` empty (untracked runtime `data` link permitted) recorded in `kit.txt`. |
| m15 | MINOR | `unit:9`, `:67-69` | Scope/STOPs: "no push" not only "no force push"; add no-resume, explicit autoresearch (C3-blocked)/Breakout/other-node exclusion, env-freeze-mismatch STOP, 100 GiB cap, resolved-invocation record; keep no-other-host/non-effective/synthetic/timeout items. |
| m16 | MINOR (mandatory pre-execution) | `unit:43`, `:66` | Launch env check: record `which python`, versions vs `numpy 2.5.4 / pandas 3.1.1 / scikit-learn 1.9.1`, the `uv pip freeze` sha, and STOP on mismatch. |
| **n1** | MINOR (new) | `unit:27-29` | Truncated correct pin `88d359f2…` still embedded (accepted convention: no pin hex in the unit — R3 M5/mR3) and no "record both pins as full 64-hex values"; name the deployed source artifact (run records; `pins/deployed_mlgym.json` has no houseprice entry). Expected deployed value `4cbbc5d6…` is informational under the unit's data root. |

No BLOCKING finding. No other overclaim was found: the kit tip, the author csv sha256/md5/prefix/suffix and the
`--from-file` path, the CPU-only `envs/torch312` environment, the licence/terms statement, the inside-scope cgroup
construction with the 8 GiB/0 probe, `--runs-root` outside the repository, the one-fit budget `steps 1`, the 3 × B1
rule, the sealed test metric, and the 8-executed/refused-`s001` expectation are all correct and independently checked.

## 11. Conditions

All conditions are text/record corrections; none changes the procedure, scope, measurement identity, STOP set or kit
byte. **No execution until C1–C4 are applied to the unit/launch notes; C5–C7 are satisfied in the result and the
execution.**

- **C1 (pin record; M1 closed, n1).** Record the **committed-file** `frozen_pin_sha256` as the full 64-hex value from the
  accepted kit update §3/§10.2 / `pins/new_mlgym.json` — expected
  **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`** (16 frozen entries at tip `f07875de…`) — and
  the **deployed run-record pin** as the full 64-hex value from the run records (17 entries incl. `data: link:<absolute
  target>`; expected `4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144` with the unit's data root, else the
  actual value). Do not interchange them; the **census commits the committed-file pin**. Do not copy the truncated
  `88d359f2…` literal; keep it only as an expected sanity check or remove it. No other node's pin.
- **C2 (author file + setup + manifest; m1–m3).** Record the author placement (date/quote) and the on-host verification
  (`sha256sum`/`md5sum`/`stat` bytes/mtime), download date and the Kaggle competition URL, noting the move from the 19 Nov
  `~/r1_inputs` path (kit update §9: absent). Run setup from the node dir with `envs/torch312/bin` first on `PATH`; move
  aside an old/other-source `--out`; record the setup command/rc/log path+sha, the manifest sha256, and the run's
  `AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=…` line and the exact `--from-file` path. Replace the `:35`
  "source path/hash appear" wording with the `provided_by` starts-with-"user download", `source.sha256` == digest, `md5`
  present, no-synthetic checks.
- **C3 (launch command + probe + gate + launch checks; m4–m6, m14).** Give the launch command as **one physical line**
  (join the `&&` parts; keep `--memory-limit` one line) or as a script; read the probe values `8589934592`/`0` via the
  echoed `scope_cgroup=` path (or inside the scope), mismatch = STOP; record the Paper A gate JSON/sha/UTC immediately
  before launch with the exact command and three criteria; record `kit.txt` with `git rev-parse HEAD` ==
  `f07875de…`, `git status --porcelain --untracked-files=no` empty (untracked runtime `data` link permitted), `which
  python`; and add the launch env/import/versions check with the freeze sha and a mismatch STOP (m16).
- **C4 (CPU co-tenancy + B1/B2 + static test + scope/STOPs; m7–m9, m15).** Record the idle CPU set `<cpus>`, load
  threshold and before/mid/after snapshots with "disturbed = STOP" and the 8 GiB basis; define B1 = `s000_baseline`
  `elapsed_seconds_info_only`, B2 = same-seed repeatability, and timeout/OOM = the proposal's failure; run and record the
  CPU-masked static test with command/mask/interpreter/result/log sha (mlgym kit expected 225 passed / 2 known env
  failures / 1 skipped / 6 deselected); add "no push", no-resume, explicit autoresearch (C3-blocked)/Breakout/other-node
  exclusion, env-freeze-mismatch STOP, 100 GiB cap and resolved-invocation record.
- **C5 (result standard; m10–m12).** The result record under
  `docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_<UTC>/` must carry the full accepted standard (per-run
  `run_record.json`/`run.log`/`result_channel.txt` paths+sha256, `process.returncode`/`timed_out`,
  `determinism.not_forced`/`shim_loaded`, one JSON line per run, node-spec + representative-edit manifest shas, sealed
  value source, result-file path/sha, host/boot/kernel, data manifest + `AR_DATA` line with file count/size/read-only
  bit, disk `du`/`df` before/after with the 100 GiB cap, cgroup probe bytes, CPU/load census, gate JSON+UTC, env freeze,
  both pins as full 64-hex, isolation fields incl. `log_intact`/result channel/`cgroup.kill`,
  `CHECKLIST_E_PASSED` + 8 executed + refused `s001`, licence/provenance incl. `R1-TRACKG-LICENCES` and the
  Apache-2.0-not-used sentence and the census row/appendix duty, executed amended unit copy (record its own sha; the
  reviewed bytes are `397ccfd1…`), captures + `SHA256SUMS`), preserved (no deletion).
- **C6 (assembly/record).** The result must record the reviewed unit sha **`397ccfd1d985…`** and preserve the executed
  amended unit bytes; the reviewed unit is untracked at review time, so the executed copy must be committed/preserved
  with the result. No kit byte changes under this acceptance; the harness branch must remain at `f07875de…`.
- **C7 (execution rule).** One smoke only for this node; no timeout/OOM retry; one node only, no cross-node pooling;
  ENGINEERING_ONLY with no evidence/noise/D21/D28, no T1; no HTCondor/deepthought/other host; no deletion/push; a
  timeout/OOM or any non-effective executed record is a STOP, not an infrastructure re-run. Acceptance of this unit does
  not authorise autoresearch (C3-blocked), Breakout, any other census node, a T1 label/sweep or a cross-node comparison.

## 12. Verdict

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 17 MINOR, conditional on C1–C7.** The round-1 MAJOR (the hardcoded wrong committed
pin, `eb60107e…` = `mlgym_fmnist`) is **closed**: the unit names the correct committed-file pin
`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654` (verified three ways — accepted kit update §3/§9,
`pins/new_mlgym.json`, and my independent recomputation from the tip's 16 frozen entries, with the method validated
against the captured cifar10/fmnist committed and deployed pins), requires reading it from the kit at launch, keeps the
deployed pin separate and directs the census to the committed pin; no wrong pin remains. The unit's other
substance — scope/authority, the author csv sha256/md5/prefix/suffix and the direct `AR_HOUSEPRICE_TRAIN_CSV` /
`--from-file` path, the kit tip `f07875de…`, the CPU-only `envs/torch312` path with no `--gpu-uuid`, the licence/terms,
the inside-scope cgroup construction with the 8 GiB/0 probe, the one-line `--memory-limit` value, `--runs-root` outside
the repository, `--provisional-timeout 1800`, the B1/B2 `val_rmse` + sealed `test_rmse` metric, one fit (`steps 1`), the
3 × B1 rule and the 8-executed/refused-`s001` expectation — is correct and independently checked. The 17 MINORs are the
same accepted R3/Breakout record/text classes plus one new pin-recording residue; the only one that would stop a
literal launch is the source-wrapped command (m4). **No execution until C1–C4 are applied to the launch notes; C5–C7
must be satisfied in the result and execution.**

## 13. Attestation and command record

This review is the only file written (uncommitted). I did not run the smoke or any GPU/U2/census job, did not edit the
unit or any code, did not commit/push or delete any repository, unit, evidence or capture file, did not log in to Ada and
did not touch HTCondor or deepthought. Read-only operations (20 Nov 2026, Europe/Berlin): `pwd`/`git rev-parse
--abbrev-ref HEAD` (`ops-tasl-20261116`)/`git rev-parse HEAD` (`6bbf4b3e`), `git rev-parse origin/main` (`df58bcd5`),
`git merge-base` (`94db94bb`), `git status --porcelain` (tracked-clean; the untracked unit and round-1 review before this
file, which is the third untracked file),
`git show origin/main:docs/r1/PLAN.md` rows `R1-TRACKG-G0-GO:1258`, `R1-TRACKG-LICENCES:1269`,
`R1-TRACKG-PORT-DECISIONS:1289`, `R1-HARNESS-ISOLATION:1290`, `R1-TRACKG-G3-EARLY:1330`; `sha256sum` of the reviewed unit
(`397ccfd1…`), the round-1 review (`36774ed5…`), the kit update report (`fe232e2b…`), its review (`d8c68f9f…`), the fix
review (`c8e468c7…`), the port report (`78d354b8…`), the R3 review (`99daf16d…`), the Breakout review (`217822fe…`), the
prior raw-cost review (`c18e25df…`), the 19 Nov follow-up (`4b6a9963…`) and the experiment-agent prompt (`3c34c745…`);
`pins/new_mlgym.json` (`8974359b…`) and `pins/deployed_mlgym.json` (`dcfcb080…`); `shasum -a 256 -c SHA256SUMS` in the
kit-update captures (**341/341 OK, 0 FAILED, rc 0**); `git ls-remote --heads` on
`github.com/dowlingwong/autoresearch_harness` (`mac-trackg-iso-mlgym-20261117` =
`f07875de79a5a57739227b13e0fd52d31646edaf`, `mac-trackg-iso-ar-20261117` = `448f6820…`, `mac-trackg-iso-mlab-20261117` =
`fb6e7d73…`); reads of the existing read-only clone `/tmp/u2review/harness_mlgym` (HEAD `f07875de…`, tracked-clean) —
node spec, `prepare_data.py`, `run_fixed_budget.py`, `ar_data.py`, `port_support.py`, `port_smoke_gpu.py`,
`test_port_mlgym.py` SMOKE table, `frozen_file_hashes`/runner pin logic, `LICENCES.md`, `requirements.txt` — and of the
accepted kit-update captures (`scripts/setup_node.sh`, `scripts/smoke_one.sh`, `run_static_tests.sh`), the fmnist/cifar10
accepted result records, the accepted five-node/Breakout units and the R3/Breakout reviews; Python recomputation of the
`mlgym_houseprice` committed-file pin (`88d359f2…`, 16 entries) and the expected deployed pin (`4cbbc5d6…`, 17 entries),
with the method validated against the captured `mlgym_cifar10` (`2d7e533b…`/`817c9034…`) and `mlgym_fmnist`
(`eb60107e…`/`ef804338…`) pins; and a local `bash -n` parse check of the unit's launch command as a literal multi-line
copy (inner script: `syntax error near unexpected token '&&'`) and as the joined one-line form (rc 0), using scratch
files under `/tmp` only (no smoke executed). No live-host state is claimed beyond what the accepted records and the
published kit branch show.
