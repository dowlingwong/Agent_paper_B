# Independent review — Track G G.0 U2 isolated-node results, five nodes (19 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-iso-result-reviewer`), delegated by the coordinator after the five
isolated-node smokes were run; no involvement in the units, their R1/R2/R3 reviews, the port kits, the isolation fix,
the kit update, or the execution. Read-only: the **only file written is this review** (uncommitted). No new GPU/U2
run, no unit/code edit, no deletion, no commit/push, no HTCondor/deepthought, no other host. I did log in to Ada
(`ssh -o BatchMode=yes experiment_zhixu …`) **read-only** to compare the five result records and their captures
against the live evidence; I ran no smoke, no GPU query that could disturb a card, and no write on Ada.

**Objects under review.** Five untracked result directories under `docs/r1/reports/trackg_g0_20261117/` (result md +
captures + `SHA256SUMS`) and the live Ada evidence under
`/home/dowling/r1_engineering/u2_iso_20261119/`. The executed units are the accepted revision-3 files **as amended
with the R3 pre-execution MINOR conditions** (the R3 review's `mR1`/`mR7`, plus `mR8b`/`mR11` for the nodes named
there); current file shas are recorded by each result. The R3-reviewed bytes were never committed, so the amendment
scope is checked against the R3 conditions and the amended text, not by a byte diff (shared finding S10).

| node | result record (this worktree) | result md sha256 | `SHA256SUMS` sha256 |
|---|---|---|---|
| mlab_cifar10 | `u2_iso_mlab_cifar10_20261119T033747Z/` | `c8e0ab2eed55e1df536876551156eb244e0ac53824df50f785660249ed74575f` | `cbf6fe822cd6302275ba6d67d8c4be6bf74aab25661722c9da3efd2459a43492` |
| mlab_imdb | `u2_iso_mlab_imdb_20261119T034107Z/` | `77154ec2de57ef2eb2c0b39a9b70175ce5c85e9e1b54457f35f18deae074dd4f` | `f3ce6738281ff4c8c87093eb58c9eb7817156b3ba1797f3d19bc76e1b6082682` |
| mlab_ogbn_arxiv | `u2_iso_mlab_ogbn_arxiv_20261119T035109Z/` | `939475564c08aa15b399e9549365edc26db1552b6a1e4145bd836b4b45afb212` | `2f7731028e5a49fad2b97a1d9397057950cf0572c6311dbb51a5348f5ea75de0` |
| mlgym_cifar10 | `u2_iso_mlgym_cifar10_20261119T035326Z/` | `ba68f5e297ad71a5d220f4ed9930ec02d7dff8d863dcbac717b1c3d78b74cdc6` | `7699dc0337d60610e76f87cf9bfb39ea3e58abf7f8959406fe3d70b1d0d9e862` |
| mlgym_fmnist | `u2_iso_mlgym_fmnist_20261119T035842Z/` | `e8ef1fca116de170efa01d90c5f65851ddcaf727fc8f598a94c5111e340fa595` | `6aac3e22523aee70bbe18603615f68f96bdbfeb2a3ec37558280c178a3c836f4` |

Executed unit files (current, amended) and shas: `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md`
`7278932f1b8898a7690eb935e0dd46172445ddb4c3e41823d725c0b65ca57684`; `U2_ISO_MLAB_IMDB_UNIT_20261119.md`
`bbc02cc55390341ded0ea48d1aae320778b1ee56ea8ab66c42d15d6c78349d9d`; `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md`
`81a3a393731186b89742971a17fe2cb2b4814e543b55892714b867c847ec1bc4`; `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md`
`82e90b7ce9668031619689d3e5c10ff966c4ad0120180f8ba99a6ee4b437d7a3`; `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md`
`0f124d107424bc5f0c0c166211beced242d5c599519b91ecbc4623f41f329421`. These match the shas cited in the five
result records. The amended units contain exactly the R3 pre-execution corrections: mR1 (the `cd` inside the scope,
`PYTHONDONTWRITEBYTECODE=1`, the `scope_cgroup=` echo, the expected `8589934592`/`0` bytes and the STOP, and the
one-line `--memory-limit`), mR7 (metric wording, `outcome.value`/sealed, no `val_bpb`), and imdb mR11 + imdb/ogbn mR8b;
no unit claims a second node or a scope beyond its own.

**Worktree and authority state.** Worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`,
HEAD **`1cc54d81`** (`ops-tasl-20261116`); `origin/main` = **`de3de54fd22dcdd86215be0924307e36a64ed08b`** = the
authority `de3de54f`. The worktree's `docs/r1/PLAN.md` carries `R1-TRACKG-G0-GO:1258` and `R1-TRACKG-LICENCES:1269`
but **not** `R1-TRACKG-PORT-DECISIONS:1289` / `R1-HARNESS-ISOLATION:1290`; those rows, the port report
`docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` and its review resolve **only against published `main` `de3de54f`**
(verified with `git show origin/main:…`). The five results cite the port report/review; that citation is valid against
published main, and the branch must not be treated as carrying those rows in its own tree until it merges main. The
only working-tree changes are the ten untracked items (units, five result dirs, the moved-aside dir, R1/R2/R3 unit
reviews); no commit or push was made (`origin/main` unchanged).

**Authority read.**
- `R1-TRACKG-G0-GO` (`origin/main:docs/r1/PLAN.md:1258`): one node per unit, each unit independently reviewed,
  ENGINEERING_ONLY, re-check idle card/sharing/Paper A gate each time, no noise floor/D21/D28.
- `R1-HARNESS-ISOLATION` (`:1290`): separate process for editable code, append-only metric log, cgroup-wide kill,
  a run with more than one metric line refused.
- `R1-TRACKG-PORT-DECISIONS` (`:1289`): (3) imdb baseline written by the port — accepted provided frozen and
  independently reviewed before any label run, and the census funnel/appendix must note "baseline written by us";
  (4) node timeout = measured baseline × 3, a timeout is the proposal's failure and not an infrastructure rerun;
  census on Python 3.12.
- Port report §2/§3(3)/§7 and its round-4 ACCEPTED review; accepted kit update report
  (`TRACKG_ISO_KIT_UPDATE_20261119.md` sha256 `fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`)
  and its review (`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED, C-K1…C-K5);
  isolation-fix review (`c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`, conditions C1–C4);
  the R3 unit review (`TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` sha256
  `99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`); the accepted prior U2 pattern
  (`TRACKG_U2_AR_RESULT_20261117.md`, `TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md` §9 result-record standard).

**Method.** Paper review plus independent capture/live cross-check. For every node I recomputed, from the
**live Ada** kit worktrees, `pins/*.json`, data root and node specs, the committed and deployed pins
(`sha256(json.dumps(files, sort_keys=True))`), the canonical node-spec sha
(`sha256(json.dumps(yaml_payload, sort_keys=True, separators=(",",":")))`), the run budgets and the live data
manifests; I hashed every file named by the five `SHA256SUMS` and mapped it to the live evidence
(`./static|scripts/X` → the campaign-level `static/`, `scripts/X`) to find any live/local divergence; and I parsed
the 45 `run_record.json`-equivalent files (9 per node), the verifier JSON, the sampler CSVs and the run logs. Every
number quoted in the result tables was re-derived from the records. This review does not re-run the smoke; it
verifies the record against the preserved evidence.

---

## Verdict summary

| node | verdict | BLOCKING | MAJOR | MINOR (node-specific + shared) | census row supported | STOP/blocker for the node |
|---|---|---|---|---|---|---|
| `mlab_cifar10` | **ACCEPTED** | 0 | 0 | 5 + 10 | yes | no (initial runner STOP was the disclosed verifier false-negative, corrected on the same records) |
| `mlab_imdb` | **ACCEPTED** | 0 | 0 | 2 + 10 | yes | no |
| `mlab_ogbn_arxiv` | **ACCEPTED** | 0 | 0 | 2 + 10 | yes | no |
| `mlgym_cifar10` | **ACCEPTED** | 0 | 0 | 2 + 10 | yes | no |
| `mlgym_fmnist` | **ACCEPTED** | 0 | 0 | 2 + 10 | yes | no |

All five verdicts are **ACCEPTED**, each conditional on the MINOR record-text corrections listed per node and in §9
being applied **before the census row is written/committed**. The substantive requirements — one accepted unit, one
smoke, no retry, kit tip clean, data manifest, committed-vs-deployed pin convention, effective isolation on all eight
executed records, refused `s001`, cgroup enforcement, gate, GPU co-tenancy, sampler label, B1/B2 and 3×B1, whole-smoke
CPU/RAM, no synthetic marker, no timeout/OOM, `CHECKLIST_E_PASSED`, live-capture integrity — **pass on every node**.
The MINORs are record-text/citation/housekeeping items; none changes a measurement, the isolation result, the pins,
the scope or the STOP set.

---

## 1. Shared verification (all five nodes)

### 1.1 One accepted unit, one smoke, no retry

- Each node executed its own accepted unit (the amended revision 3 whose sha its result cites) and no other node's
  unit. Each evidence root contains **exactly one non-dryrun U2 directory**; the Ada campaign root also contains two
  launcher **dry-runs** for `mlab_cifar10` (`dryrun_u2_iso_mlab_cifar10_20261119T033214Z`,
  `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z`) whose inner command is `taskset -c 0-7 /usr/bin/time -v -o … true -m
  tests.trackg.port_smoke_gpu …` (i.e. `true` swallows the smoke arguments) and which correctly STOP on missing
  `CHECKLIST_E_PASSED`; they executed no U2 run and are not retries (findings S1). The only other "re-run" is the
  `mlab_cifar10` verifier re-run on the same records (no smoke re-run).
- Each node's nine `run_record.json`-equivalent directories are present; each executed eight records + the refused
  frozen-diff `s001`. `s001` is `executed:false`, `outcome:null`, `diff.status: refused`, `diff.refusal:
  scope_violation` (with `frozen_paths` match), and carries no isolation fields — by design.
- `CHECKLIST_E_PASSED <node>`, `SMOKE_EXIT=0`, `systemd_run_rc=0` are in the smoke logs/stdout extracts of all five.
- No result claims a second smoke, a retry, a T1 run, a U3 run, or cross-node pooling.

### 1.2 Kit, data and pins

Live Ada, read-only:

| node | kit branch @ tip (`git rev-parse HEAD`) | tracked status | data manifest (live = recorded) |
|---|---|---|---|
| mlab_cifar10 | `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` | clean, only the three expected untracked `nodes/*/data` links | `43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3` |
| mlab_imdb | same @ `fb6e7d73…` | same | `a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c` |
| mlab_ogbn_arxiv | same @ `fb6e7d73…` | same | `9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c` |
| mlgym_cifar10 | `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf` | clean, only the two expected untracked `third_party/mlgym/nodes/*/data` links | `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` |
| mlgym_fmnist | same @ `f07875de…` | same | `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` |

The data dirs are `dr-xr-xr-x`, the worker sandbox ro-binds each node data dir (checked in every baseline record's
`isolation.worker_sandbox.ro`), and no `synthetic` marker exists in any manifest or run log.

**Pins (convention verified by re-derivation, not by trusting the record).** For every node I recomputed the pin as
`sha256(json.dumps(files, sort_keys=True))` from the live `pins/new_*.json` / `pins/deployed_*.json` file dicts and
re-hashed every committed file against the live kit: **all 10 pins recompute exactly**, the committed-file pins are
the 16-entry (no data link) values and the deployed pins are the 17-entry values that also hash `data: link:<abs
target>`; each executed record carries the deployed pin; the committed pin is **not** present in any run record and is
directed to the census. The result md values are the full 64-hex values:

| node | committed-file pin (census value) | deployed run-record pin |
|---|---|---|
| mlab_cifar10 | `1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2` | `a459b3d823075953d05422594cc97fa743723f22e79e1f8368480007dd041388` |
| mlab_imdb | `4b1019a60b1ac96028944d1dcc02be582f84e1fab0dbfd11d00011f460fb97fb` | `c169a6b875733cdb03d223659d06cc9a6839dd6255a924c420f10982bbefbbb0` |
| mlab_ogbn_arxiv | `bd71fdf4c6b3a66715cb602a41a7a1f5bdeeaa6e23439c558a96c2bda061c9d7` | `5ff5824ac22783f05f84b84d6d3222e8f1f4ddbc118e6bb1f657041bfb3285ad` |
| mlgym_cifar10 | `2d7e533b2a1075000d15a21445f98b94d7df2cf527baff0264f3ae306f93022e` | `817c90340e7ae004b7cd7161f899cb159a91ae482febc9a7f9ea2d9969f76e62` |
| mlgym_fmnist | `eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3` | `ef8043389dbd55a9a01d192227f0483daf2a406043b0a1feaf74eba4d858ddee` |

The committed pins equal the accepted kit update report §3 table; the deployed pins equal the accepted kit-update
engineering-smoke records' pins; the run records' `frozen_files_checked` is 17 and the pin is constant across all
nine records of a node (including `s001`). `pins/new_mlab.json`/`deployed_mlab.json` sha256 are
`731b713d…`/`388c09f5…` and `new_mlgym.json`/`deployed_mlgym.json` are `8974359b…`/`dcfcb080…` on live Ada, matching
the results. The node-spec canonical shas (`sha256(json.dumps(yaml_payload, sort_keys=True, separators=(",",":")))`)
recompute from the live kit specs and equal every record's `node_spec_sha256`
(`90c8364f…`/`0123a8a7…`/`e952df6a…`/`f1360bcd…`/`65f229af…`), and the run budgets
(`--steps 1950/1000/356/7820/9380`) match the live node specs' `run_budget`.

### 1.3 Isolation on every executed record

Parsed all 40 executed records (8 per node): every one has `isolation.effective: true`, `isolation.waivers == {}`,
`isolation.exceptions == []`, `isolation.log_intact: true`, `isolation.result_channel_overflow: false`, a non-null
`isolation.result_channel_sha256`, and `isolation.cgroup.kill {method: "cgroup.kill", empty_after: true}`,
`isolation.cgroup.removed: true`; `isolation.frozen_files_checked == 17`; `isolation.euid == 1030`;
`determinism.not_forced == ["dataloader_workers"]`; `process.returncode == 0`,
`process.timed_out == false`. The three verifier outputs (`verify_u2_records.py`, kit `verify_records.py`,
`collect_smoke_summary.py`) are all clean on all five: `ok: true` / `records: 9` / `executed: 8` /
`refused_s001: true`, `issues: []`, `gate_ok: true`, and the verifier checks include exactly the isolation fields above
(plus the one-line `external_limit`, GPU UUID, CPU list, external memory method, provisional 1800 s, factor 3.0,
synthetic-in-log/manifest, one JSON line per run when `--smoke-log` is given). `s001` is refused
(`executed:false`, `outcome:null`, `scope_violation`) and is not counted as a failure. The `mlab_cifar10` v1
false-negative is preserved as `verify_full.v1_verifier_bug.json`/`.summary.v1_verifier_bug.txt`; the fix
(`scripts/_patch2_verifier_s002_fix.py`) and the corrected verifier are the ones that produced the final `ok: true`
outputs. No synthetic marker appeared in any run log or manifest (`synthetic_in_log`/`synthetic_in_data_manifest`
false on every row; `data_manifest.txt` `synthetic_marker=absent`). No timeout and no OOM occurred; no retry.

### 1.4 Command and cgroup

For all five, the resolved `invocation_inner.sh` runs inside
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'` and contains, in order:
`cd <kit worktree root>`, `CG=$(cut -d: -f3 /proc/self/cgroup)` **inside** the scope,
`export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `echo scope_cgroup=…`, `PYTHONPATH=src
PYTHONDONTWRITEBYTECODE=1`, the torch env `bin` first on `PATH`, `VIRTUAL_ENV`, `CUDA_VISIBLE_DEVICES=""`,
`AR_TRACKG_DATA_ROOT=…/data`, then
`taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node <node> --gpu-uuid <uuid> --cpus <cpus> --memory-limit
"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root
<outside-repo>/runs --provisional-timeout 1800`, with the expected-bytes STOP
(`memory.max != 8589934592` → exit 90; `memory.swap.max != 0` → exit 91). The live `cgroup_probe.txt` scope equals the
run records' `limits.cgroup_parent` on every node (one parent path per node), `memory.max=8589934592`,
`memory.swap.max=0`, `which_python` before `PATH` empty and after `PATH/VIRTUAL_ENV` the
`envs/torch312/bin/python` (Python 3.12.16), `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=` empty. Every executed record's
`limits.external_limit` is exactly the one-line unit string, `memory_method: external`,
`provisional_timeout_seconds: 1800.0`, `timeout_factor: 3.0`, `cpu_list` 0–7 (mlab) or 8–15 (mlgym), `gpu_uuids`
`[<the selected UUID>]`. The runs-root is outside the repository on every node
(`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_<node>_<UTC>/runs`).

### 1.5 Gate, GPU and sampler

- **Paper A gate** (captured immediately before each launch; the five gate JSON files hash-match the live captures):
  `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`,
  `unidentified_apps: 0`, newest v4 `live_*` == configured run dir (`newest_live_equals_configured=yes`), self-excluded
  `pgrep port_smoke_gpu` empty, `pgrep agent-checkpoint-intervention` empty, gate script rc 0. Gate JSON shas:
  `f30799b1…` (cifar), `75a26675…` (imdb), `1d9e8062…` (ogbn), `2d0aad26…` (mlgym cifar), `1fc11b9f…` (fmnist).
- **GPU co-tenancy**: each node selected an idle card with no other user's compute app
  (cifar card 1 `GPU-aa340032…`; imdb card 2 `GPU-f439cca8…`; ogbn card 6 `GPU-3b36edea…`; mlgym cifar card 7
  `GPU-3719bd35…`; fmnist card 2 `GPU-f439cca8…`), 48,427 MiB free of 49,140 MiB, 0 % utilisation; before and after
  full snapshots captured on all five, and the card is back to 5 MiB / 0 % after. **Direct full mid-run snapshots**
  exist for ogbn/mlgym_cifar10/mlgym_fmnist; for **cifar10 and imdb** the mid-run snapshot is derived from the 1 s
  sampler and clearly labelled (cifar `gpu/gpu_mid.txt` "derived … threshold 1000 MiB while the measured sampler
  maximum was 836 MiB"; imdb "derived … watcher subshell exited on its first iteration (bash resets the special `_`
  loop variable)"), with mid-run utilisation `NOT_CAPTURED_MID_RUN` stated and before/after utilisation recorded.
  No card switch happened (the same selected UUID is in qualify/before/mid/after and in every run record).
- **Sampler**: the exact command `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1`
  (interval 1 s), started before the scope and stopped after it. I independently recomputed the maxima from the
  required and timestamped CSVs restricted to the used card: maxima, sample counts, distinct pids and row counts
  reproduce **exactly** (see §1.6 table). The reported value is a **whole-smoke upper bound over the used GPU,
  including co-tenants by construction, NOT a per-run peak and NOT attributed to the baseline process tree**; the
  CSV header is excluded; the max single row equals the max per-sample sum because only this smoke's processes were
  on the card. Each node's sampler has exactly eight distinct pids on the used card (consistent with the eight
  executed runs; the same card was idle with no compute app before/after), and no other user's app appears on the used
  card in any sampler row.
- **Whole-smoke CPU/RAM** (`/usr/bin/time -v`, labelled aggregate, not a per-run peak) matches `time_v.txt`
  exactly on all five.

### 1.6 Numbers

| node | B1 s | B1 `outcome.value` | B1 sealed | B2 s | B2 value / sealed | node timeout 3×B1 s | whole-smoke user/sys/wall/maxRSS | sampler bound / duration / samples / pids / rows |
|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | **12.297** | 0.5152 | 0.5015 | **11.846** | 0.5152 / 0.5015 | **36.891** | 94.21 s / 13.77 s / 1:41.53 / 1,402,612 kB | 836 MiB / 100.7 s / 73 / 8 / 780 |
| mlab_imdb | **64.142** | 0.9048 | 0.89924 | **64.133** | 0.9048 / 0.89924 | **192.426** | 498.14 s / 18.97 s / 8:28.85 / 1,659,008 kB | 11292 MiB / 508.8 s / 472 / 8 / 4007 |
| mlab_ogbn_arxiv | **5.651** | 0.275982 | 0.238442 | **5.665** | 0.275982 / 0.238442 | **16.953** | 56.76 s / 11.86 s / 1:03.92 / 1,256,776 kB | 4544 MiB / 63.4 s / 36 / 8 / 484 |
| mlgym_cifar10 | **31.731** | 0.491 | 0.4926 | **31.244** | 0.491 / 0.4926 | **95.193** | 251.05 s / 15.32 s / 4:18.83 / 1,493,864 kB | 982 MiB / 258.5 s / 227 / 8 / 2026 |
| mlgym_fmnist | **34.376** | 0.861667 | 0.8515 | **28.868** | 0.861667 / 0.8515 | **103.128** | 280.78 s / 14.86 s / 4:49.02 / 1,213,024 kB | 912 MiB / 288.9 s / 261 / 8 / 2270 |

Every value above was re-derived from `runs/runs_smoke/s000_baseline/run_record.json`, `runs/runs_edits/B2/…`, the
baseline `result_channel.txt` (`AR_METRIC val_accuracy=…`, `AR_TEST test_accuracy=…`) and the CSVs; the result tables
match the records exactly for B1/B2 and every edit outcome (`s002` divergent/non-finite with sealed 0.0, `s003`/
`E1–E4` values and sealed values). The derived node timeout is exactly 3×B1. The pre-run reference values in each
result (12.859/61.399/5.702/24.07/26.702 s, same metrics) match the accepted kit-update attempt-2
`s000_baseline` records. The whole-smoke wall is coherent with the sum of the eight executed run times plus overhead.
Record hashes: each result's `record_hashes.txt` (25 entries: 9 records + 8 logs + 8 result channels) verifies
against the local and live files; the baseline record / run.log / result-channel shas cited in each result md are
correct (e.g. cifar `c4d532a7…` / `77f18a64…` / `ebb17269…`; imdb `b18796e0…` / `e7313f95…` / `c3231319…`; ogbn
`41c542d0…` / `47f0eb8e…` / `679cb595…`; mlgym cifar `645795ca…` / `8f210cd6…` / `a3d987ed…`; fmnist
`9838015e…` / `7aaf4f69…` / `94cb9926…`). The five `SHA256SUMS` self-verify (`shasum -a 256 -c`, rc 0; 427/425/425/
425/425 entries OK) and each covers every captured file. Every other 64-hex cited in the result mds resolves either
to a `SHA256SUMS` entry, to the unit file, to the live data manifest, or to a live accepted-kit-update setup log
(`setup_mlab_imdb.log` `7d704550…`, `setup_mlab_ogbn_arxiv.log` `e76ecf0b…`, `setup_mlgym_cifar10.log` `2f2e4bcf…`,
`setup_mlgym_fmnist.log` `7c0b284e…` — all verified live).

### 1.7 Live-Ada cross-check of the captures

I hashed every file named by the five `SHA256SUMS` on live Ada and compared it with the local capture. Result:
**every captured evidence file is byte-identical to live Ada except one**: the `mlab_imdb`
`RESULT_STATUS.txt` (local sha256 `7bd2f2ff…`; live sha256 `1752f80c…`; the difference is only the wording of the
03:54Z mid-snapshot note — "the launcher's … fixed for the later nodes" locally vs "the launcher … fixed for later
nodes" live). This is a capture-fidelity defect, not a measurement difference (finding I1). The three Mac-authored
`scripts/` files that are not on Ada are `scripts/README.txt`, `scripts/_patch2_verifier_s002_fix.py`,
`scripts/_patch3_mid_watcher_fix.py` (the result md and `SHA256SUMS` are also Mac-authored); they are covered by the
local `SHA256SUMS` and are documented as fix patches. The five live evidence dirs exist, are the same evidence trees, and
contain no file not present in the local capture. The result md/SHA256SUMS are Mac-authored and are not expected on
Ada.

### 1.8 Deviations — accuracy and materiality

- **cifar10/imdb missing direct mid snapshot → sampler-derived, labelled.** Accurately disclosed in both node
  results (cifar in the GPU section and the "Deviation" block, imdb in the derived `gpu_mid.txt` and "Deviations");
  the derived census is labelled and mid-run utilisation is explicitly `NOT_CAPTURED_MID_RUN`; the whole-run 1 s
  sampler (stronger for co-tenancy) is intact and complete. **Non-material.** The launcher defects are documented
  (`scripts/_patch2_verifier_s002_fix.py` and `scripts/_patch3_mid_watcher_fix.py`); for cifar/imdb the
  *launch-time* runner bytes are not preserved (only the final runner + patches) — see S10.
- **Verifier false-negative fixed with originals preserved.** Accurately disclosed (cifar result "Deviation
  (verifier bug…)", `RESULT_STATUS.txt` correction block, `DONE_PASS_CORRECTED`); the v1 output is preserved as
  `verify_full.v1_verifier_bug.json` / `verify_full.summary.v1_verifier_bug.txt` (live+local; `ok:false`, the two
  `s002` check errors) and the fix is preserved as a patch; the final verifier is clean on the same records. The
  smoke was not re-run. **Non-material.**
- **Dry-run `true -m` preserved.** Preserved on Ada (two dryrun dirs + `dryrun_launcher.log`/`dryrun2_launcher.log`);
  the dry-runs executed `true -m …` (no U2, no GPU work) and correctly went STOP. **Not disclosed in any of the five
  result records** (shared finding S1). Non-material: they are not smokes and do not affect the one-smoke claim.
- **Wrong-timestamp directory moved aside.** Exists only locally as
  `docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS_MOVED_ASIDE/`;
  it contains only copies of `static/` and `scripts/` that are byte-identical to the fmnist result dir (all eight
  files hash-equal) and no evidence. **Not disclosed** in the results (shared finding S2). Non-material to the
  result, but it sits in the reports tree and its name would be committed unless it is moved/excluded.

---

## 2. Shared MINOR findings

**S1 (dry-runs undisclosed).** The two Ada launcher dry-runs are preserved and clearly not U2 runs, but no result
record or evidence index mentions them; a reader of the campaign evidence root sees two extra `dryrun*` dirs.
*Condition:* add one line to each result's Deviations or to a short campaign note recording them as non-evidence
launcher dry-runs (`true -m`) and their STOP status.

**S2 (wrong-timestamp dir).** `u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS_MOVED_ASIDE/` (untracked, local only)
has no result/README mention; it duplicates `static/`/`scripts/` and contains no run evidence. *Condition:* relocate
it out of the reports tree or document it as a non-evidence duplicate before the branch is committed.

**S3 (R3 result-record residuals: mR6).** The result rows do not print their own result-file name/path/sha, the
node-spec sha and representative-edit-manifest sha (they are captured in `kit.txt`/the run records),
`killed_with` (null on the normal exits) or an explicit "one JSON line per run" statement. All are present in the
captures; this is a recording-completeness residual of R3 mR6. *Condition:* add the missing fields/shas to the
result rows (or cite them from `kit.txt`/`record_hashes.txt` explicitly).

**S4 (mR8: abbreviated shas).** The result mds cite the accepted kit-update report as `fe232e2b…` (prefix only) and
the kit-update review by path without a sha; `fe232e2b…` is the true report sha (`fe232e2bbf23…`), the review is
`d8c68f9f…`. *Condition:* cite the full 64-hex report sha and the review sha.

**S5 (mR9: floor basis / mid-run rule).** The result mds state the 8 GiB floor and the before/mid/after census but do
not state the floor's basis (the kit's measured ~2.85 GB torch peak; prior accepted run-1 floor 24 GiB), the
mid-run contamination rule (free VRAM below baseline peak + 2 GiB or a new co-tenant → STOP/record), nor "no switch
from the launch card" (they say "no unrecorded card switch", which was not exercised because no switch occurred).
*Condition:* add the basis and the rule.

**S6 (mR10: no-resume).** The results state "one smoke only; no retry" but not the R3 no-resume statement (an
interrupted unit re-runs whole from a new `<runs-root>`); and the disk footprint is reported without the exact
filesystems in the four non-cifar results (cifar uses `df -B1 / /home /tmp`, the others only `/`). *Condition:* add
the no-resume line and name the filesystems.

**S7 ("data root not writable" label).** Each result's data bullet says "data root not writable"; the capture
(`data_manifest.txt`) actually tests `[ -w "$BASE/data/<node>" ]` (the **node data dir**, which is `dr-xr-xr-x` and
ro-bound in the worker sandbox), while the top-level `data/` root is `drwxrwxr-x` (operator-writable). The statement
overstates the top-level root; the integrity claim that matters (node data read-only to the worker) is evidenced by
the sandbox `ro` bind and the manifest hashes. *Condition:* reword to "node data dir read-only; data ro-bound in the
worker sandbox".

**S8 ("preserved read-only on Ada" wording).** The live evidence dirs are `drwxrwxr-x` and files `-rw-rw-r--`, i.e.
not filesystem-read-only (they are unaltered and hash-matching). *Condition:* say "preserved unaltered" or make them
read-only.

**S9 (`data_link=` capture line).** `data_manifest.txt` line 4 prints
`data_link=<readlink -f result> -> target=<readlink>`; both sides show the absolute target, so the in-kit symlink
path (`nodes/<node>/data`) is implicit (it is evidenced by `kit.txt` `?? nodes/<node>/data` and the deployed pin's
`data: link:` entry). Cosmetic, no measurement impact. *Condition:* record the actual symlink path (`$NODE_DIR/data`).

**S10 (amended-unit and launch-runner bytes not preserved).** The R3-reviewed unit bytes were never committed (only
their sha is recorded), so the amendment scope is inferred from the R3 conditions and the amended text (verified
present), not by diff; and for cifar10/imdb the launch-time runner bytes are not preserved (only the final runner +
the two fix patches). *Condition:* commit the executed unit bytes and (if cheap) the launch-time runner snapshot with
the result records so the derivation is reproducible.

---

## 3. Node verdict — `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md` / `u2_iso_mlab_cifar10_20261119T033747Z/`

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 5 node-specific + 10 shared MINOR.**

**Node-specific verification.** Unit sha `7278932f…` (amended rev 3, R3 ACCEPTED); kit
`mac-trackg-iso-mlab-20261117` @ `fb6e7d73…`, tracked-clean; manifest `43fdf860…`; committed pin `1f047ad7…`,
deployed `a459b3d8…` (both re-derived live); 9 records = 8 executed + refused `s001`; B1 12.297 s / 0.5152 /
sealed 0.5015, B2 11.846 s same value, node timeout 36.891 s; isolation/verifiers clean; cgroup scope
`run-r5cd39bf10ace44cd8950d39b9809554a.scope`, `memory.max=8589934592`, swap 0; gate `f30799b1…` three-check PASS;
GPU card 1 `GPU-aa340032…` idle; sampler 836 MiB upper bound (100.7 s, 73 samples, 8 pids, 780 rows) recomputed;
`time -v` matches; `CHECKLIST_E_PASSED`; disk before/after 69.5 GiB free. Live Ada: all this node's capture bytes
match; kit/pins/manifests/node-spec recompute exactly.

**Node-specific findings.**
- **C1 (MINOR, disk-number citation).** `U2_ISO_MLAB_CIFAR10_RESULT_20261119.md:167-169` reports before
  `74,632,830,976` / after `74,630,221,824` B and cites `disk_before.txt`/`disk_after.txt`; those captures say
  `74,632,835,072` / `74,630,283,264` (a second `df` sample; the values quoted are `RESULT_STATUS.txt`'s
  `disk_avail_before/after_bytes`). Both are >69 GiB, so the 50 GiB STOP is unaffected. Use one consistent source.
- **C2 (MINOR, gate time).** `:58-60` says the gate JSON was "captured UTC `2026-11-19T03:37:47Z`"; the gate JSON's
  own `utc` is `2026-11-19T03:37:51Z` and `gate/gate_check.txt` was captured at `03:37:51Z` (03:37:47Z is the
  runner/evidence-dir timestamp in the JSON's filename). Report the gate JSON `utc` (03:37:51Z) or explain the
  filename.
- **C3 (MINOR, mR4).** `:32-35` gives the accepted setup log path but not its sha256; the live
  `…/iso_kit_update_20261119/data/setup_mlab_cifar10.log` is `6747f821af7e6b89db3667a2fbd9115b3031b9a6f5446c4d072806fa01c1eb95`.
  The other four results cite their setup-log shas.
- **C4 (MINOR, licence line).** The cifar result has no licence/provenance line, while the other four carry the unit's
  `R1-TRACKG-LICENCES` line (CIFAR-10 generic citation/disclosure). Add it for record consistency with
  `R1-TRACKG-LICENCES`'s appendix duty.
- **C5 (MINOR, status-file reconciliation).** `RESULT_STATUS.txt` still starts `status=STOP` (then appends
  `status_corrected=PASS`, `verify_full_rc_corrected=0`) and `DONE` contains `DONE_STOP` then
  `DONE_PASS_CORRECTED`; the result says "Final status: PASS". The correction is transparent and the final verifier
  is rc 0 on the same records, but a machine reader of `RESULT_STATUS.txt` sees STOP first. Normalise the status
  (`status=PASS`, keep the STOP as history) before the census cites it.

**Conditions.** Apply C1–C5 and S1–S10 before the census row/commit. The smoke itself needs nothing: the initial
STOP was the verifier false-negative, disclosed and corrected on the same records; no re-run is authorised. This
node's single smoke is complete and its eight executed records are effective. **Census row: supported** (one node,
ENGINEERING_ONLY, no evidence/no noise/D21/D28; committed pin directed as the census value). **No STOP/blocker for
the node.**

---

## 4. Node verdict — `U2_ISO_MLAB_IMDB_UNIT_20261119.md` / `u2_iso_mlab_imdb_20261119T034107Z/`

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 2 node-specific + 10 shared MINOR.**

**Node-specific verification.** Unit sha `bbc02cc5…` (amended rev 3 with mR1/mR7/mR8b/mR11); kit
`mac-trackg-iso-mlab-20261117` @ `fb6e7d73…`, tracked-clean; manifest `a87254e1…`; committed pin `4b1019a6…`,
deployed `c169a6b8…`; 9 records = 8 executed + refused `s001`; B1 64.142 s / 0.9048 / sealed 0.89924, B2 64.133 s
same value, node timeout 192.426 s; isolation/verifiers clean; cgroup scope
`run-r4cf689a2c4344e66a9de2ab8b12686ba.scope`, 8 GiB / swap 0; gate `75a26675…` PASS; GPU card 2
`GPU-f439cca8…` idle; sampler 11292 MiB upper bound (508.8 s, 472 samples, 8 pids, 4007 rows) recomputed; `time -v`
matches; `CHECKLIST_E_PASSED`; port-decision (3) DistilBERT/"written by us"/census funnel+appendix disclosure is
carried; disk before/after 69.5 GiB. Live Ada: all capture bytes match **except** I1.

**Node-specific findings.**
- **I1 (MINOR, capture fidelity).** The captured `RESULT_STATUS.txt` is not byte-identical to the live Ada record:
  local sha256 `7bd2f2ff3cb73478950755b4499da6b8d52235320c52f24f14bb29d14bef981d`, live sha256
  `1752f80ca232129d88940a4060f17bb6e541e036c27d35ec9c528b979d25e8fe`; only the wording of the 03:54Z mid-snapshot
  note differs. The local `SHA256SUMS` verifies the local bytes, so the capture package is self-consistent but not a
  byte-faithful copy of the live record. The result md's substance is unaffected (it states the same deviation in its
  own words). *Fix:* re-copy the live file and regenerate `SHA256SUMS`, or record the edit.
- **I2 (MINOR, footprint numbers).** The Disk bullet (`:152-157`) and the run line (`:112`) report the **pre-run**
  sizes `evidence 60K, runs 4.0K` / "run root 4.0K", while the cited `runs_du.txt` is `3.8M` and
  `disk_after.txt` says `evidence_du=4.5M`, `runs_du=3.8M`. The disk-free STOP numbers are correct. Report the
  post-run footprint.

**Conditions.** Apply I1, I2 and S1–S10 before the census row/commit. **Census row: supported** (one node,
ENGINEERING_ONLY, no evidence/no noise/D21/D28; committed pin directed as the census value; port-decision (3)
disclosure carried). **No STOP/blocker for the node.**

---

## 5. Node verdict — `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` / `u2_iso_mlab_ogbn_arxiv_20261119T035109Z/`

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 2 node-specific + 10 shared MINOR.**

**Node-specific verification.** Unit sha `81a3a393…` (amended rev 3 with mR1/mR7/mR8b); kit
`mac-trackg-iso-mlab-20261117` @ `fb6e7d73…`, tracked-clean; manifest `91312162…`; committed pin `bd71fdf4…`,
deployed `5ff5824a…`; 9 records = 8 executed + refused `s001`; B1 5.651 s / 0.275982 / sealed 0.238442, B2 5.665 s
same value, node timeout 16.953 s; isolation/verifiers clean; cgroup scope
`run-rc4b68d2b57e34b30b6beeffa132feae8.scope`, 8 GiB / swap 0; gate `1d9e8062…` PASS; GPU card 6
`GPU-3b36edea…` idle; **direct** full mid snapshot present (used 763 MiB, util 6 %, own pid); sampler 4544 MiB
upper bound (63.4 s, 36 samples, 8 pids, 484 rows) recomputed; `time -v` matches; `CHECKLIST_E_PASSED`; disk
before/after 69.5 GiB. Live Ada: all capture bytes match.

**Node-specific findings.**
- **O1 (MINOR, footprint numbers).** Same as I2: `:112` "run root 4.0K" and `:152-157` "evidence 60K, runs 4.0K"
  are the pre-run values; `runs_du.txt` is `3.8M` and `disk_after.txt` gives `evidence_du=4.0M`, `runs_du=3.8M`.
- **O2 (MINOR, derived-timeout relation not disclosed).** The derived node timeout is 16.953 s (3×B1 5.651 s), but
  one executed representative edit, `E4` (the GraphSAGE full-graph edit; result table row `E4`, `:126`), has
  `elapsed_seconds_info_only = 21.8 s` — i.e. **above** the derived node timeout (`:110-111`). This is not a timeout in the
  measuring smoke (the smoke ran at the provisional 1800 s, and the accepted pattern makes 3×B1 a derived value for
  later units/runs, not a mid-smoke kill), and the result correctly says no 1800 s timeout occurred. But the result
  should say explicitly that one edit's measured elapsed exceeds the derived node timeout (so under a future label
  run that edit would be classified as a timeout/failed proposal), for the census/funnel reader. Non-material to the
  raw-cost measurement.

**Conditions.** Apply O1, O2 and S1–S10 before the census row/commit. **Census row: supported** (one node,
ENGINEERING_ONLY, no evidence/no noise/D21/D28; committed pin directed as the census value). **No STOP/blocker for
the node.**

---

## 6. Node verdict — `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` / `u2_iso_mlgym_cifar10_20261119T035326Z/`

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 2 node-specific + 10 shared MINOR.**

**Node-specific verification.** Unit sha `82e90b7c…` (amended rev 3 with mR1/mR7); kit
`mac-trackg-iso-mlgym-20261117` @ `f07875de…`, tracked-clean; manifest `c0ef1168…`; committed pin `2d7e533b…`,
deployed `817c9034…`; 9 records = 8 executed + refused `s001`; B1 31.731 s / 0.491 / sealed 0.4926, B2 31.244 s
same value, node timeout 95.193 s; isolation/verifiers clean; cgroup scope
`run-rf8361516bc6f4889b4d949bbff23446e.scope`, 8 GiB / swap 0; gate `2d0aad26…` PASS; GPU card 7
`GPU-3719bd35…` idle; **direct** full mid snapshot (used 867 MiB, util 11 %, own pid); sampler 982 MiB upper bound
(258.5 s, 227 samples, 8 pids, 2026 rows) recomputed; `time -v` matches; `CHECKLIST_E_PASSED`; licence/provenance
line (CC BY-NC 4.0 with notice, gymnax Apache-2.0 parts not used) present; disk before/after 69.5 GiB. Live Ada: all
capture bytes match.

**Node-specific findings.**
- **M1 (MINOR, footprint numbers).** Same as I2/O1: `:112` "run root 4.0K" and `:152-157` "evidence 60K, runs 4.0K"
  are the pre-run values; `runs_du.txt` is `3.9M` and `disk_after.txt` gives `evidence_du=4.3M`, `runs_du=3.9M`.
- **M2 (MINOR, metric label — correct before the census row).** `:114-115` says "`outcome.value` is the node's
  **test** accuracy, as the kit reports it". The live run's `result_channel.txt` for the baseline is
  `AR_METRIC val_accuracy=0.491000` / `AR_TEST test_accuracy=0.492600`; the node spec's `metric_name` is
  `val_accuracy` with `selection_split: validation` and `sealed.test_accuracy` = `test_accuracy`. So `outcome.value`
  is the **validation** accuracy (`val_accuracy`); only the sealed column is test accuracy. The numbers are right;
  only the label is wrong. The census row must use `val_accuracy` (and keep `test_accuracy` separate).

**Conditions.** Apply M1, M2 and S1–S10 before the census row/commit. **Census row: supported** (one node,
ENGINEERING_ONLY, no evidence/no noise/D21/D28; committed pin directed as the census value). **No STOP/blocker for
the node.**

---

## 7. Node verdict — `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` / `u2_iso_mlgym_fmnist_20261119T035842Z/`

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 2 node-specific + 10 shared MINOR.**

**Node-specific verification.** Unit sha `0f124d10…` (amended rev 3 with mR1/mR7); kit
`mac-trackg-iso-mlgym-20261117` @ `f07875de…`, tracked-clean; manifest `8d28287b…`; committed pin `eb60107e…`,
deployed `ef804338…`; 9 records = 8 executed + refused `s001`; B1 34.376 s / 0.861667 / sealed 0.8515, B2 28.868 s
same value, node timeout 103.128 s; isolation/verifiers clean; cgroup scope
`run-r2e20932cd4a8477495f6a98186d4a77a.scope`, 8 GiB / swap 0; gate `1fc11b9f…` PASS; GPU card 2
`GPU-f439cca8…` idle; **direct** full mid snapshot (used 729 MiB, util 10 %, own pid); sampler 912 MiB upper bound
(288.9 s, 261 samples, 8 pids, 2270 rows) recomputed; `time -v` matches; `CHECKLIST_E_PASSED`; licence/provenance
line present; disk before/after 69.4–69.5 GiB. Live Ada: all capture bytes match.

**Node-specific findings.**
- **F1 (MINOR, footprint numbers).** Same as I2/O1/M1: `:112` "run root 4.0K" and `:152-157` "evidence 60K, runs
  4.0K" are the pre-run values; `runs_du.txt` is `3.9M` and `disk_after.txt` gives `evidence_du=4.4M`, `runs_du=3.9M`.
- **F2 (MINOR, metric label — correct before the census row).** Same as M2: `:114-115` says "test accuracy" for
  `outcome.value`, but the baseline `result_channel.txt` is `AR_METRIC val_accuracy=0.861667` /
  `AR_TEST test_accuracy=0.851500` and the node spec's `metric_name` is `val_accuracy` (validation split). The
  numbers are right; the label must be `val_accuracy` for the census row.
- Observation (not a finding): B2's elapsed `28.868 s` is 16 % below B1's `34.376 s`; the timeout correctly uses B1
  (conservative) and B2's metric is identical. Fine for a U2 raw-cost run, but the census reader should see the two
  numbers (the result table has both).

**Conditions.** Apply F1, F2 and S1–S10 before the census row/commit; also apply S2 (the wrong-timestamp local dir is
this node's). **Census row: supported** (one node, ENGINEERING_ONLY, no evidence/no noise/D21/D28; committed pin
directed as the census value). **No STOP/blocker for the node.**

---

## 8. Census-row support and STOP status

All five results supply, per node, exactly what `R1-TRACKG-G0-GO`/U4 and the kit-update review C-K5 require: one node,
ENGINEERING_ONLY, "not evidence / no noise floor / no D21 / no D28 / no T1 label", the kit branch@tip and clean
status, the data manifest, the **committed-file pin as the census value** and the **deployed run-record pin
separately**, B1/B2 elapsed and `outcome.value`/sealed metric, the derived node timeout (3×B1), the whole-smoke
CPU/RAM aggregate, the labelled whole-GPU sampler upper bound, disk free before/after, the gate capture, and the
isolation fields. The values needed for the U4 row are present and internally consistent (except the MINOR record-text
items above). **No result contains a STOP/blocker for its node.** The only runner-level STOP is the `mlab_cifar10`
verifier false-negative, preserved and corrected on the same records (C5).

---

## 9. Required conditions before the census row / commit

Per node, apply before the census row is written and before the branch is committed:
- **All five:** S1–S10 (disclose the dry-runs; relocate/document the wrong-timestamp dir; add mR6/mR8/mR9/mR10
  record fields and full shas; reword the data-root and read-only claims; record the symlink path; commit the
  executed-unit bytes and, if cheap, the launch-time runner snapshot). Where the results report the disk footprint,
  use the post-run values from `runs_du.txt`/`disk_after.txt` (footprint items I2, O1, M1, F1).
- **mlab_cifar10:** C1 (disk source), C2 (gate UTC 03:37:51Z), C3 (setup-log sha `6747f821…`), C4 (licence line),
  C5 (normalise the status file to PASS while preserving the STOP history).
- **mlab_imdb:** I1 (reconcile `RESULT_STATUS.txt` with live; regenerate the capture hash) and I2 (post-run
  footprint).
- **mlab_ogbn_arxiv:** O1 (post-run footprint) and O2 (disclose that E4 = 21.8 s > derived node timeout 16.953 s;
  confirm the 1800 s provisional timeout governed the measuring run).
- **mlgym_cifar10:** M1 (post-run footprint) and M2 (label `outcome.value` as `val_accuracy`, validation; keep
  `test_accuracy` as the sealed value).
- **mlgym_fmnist:** F1 (post-run footprint), F2 (metric label), and S2 (wrong-timestamp dir is this node's).

These are literal recording/citation corrections; none requires re-running a smoke. **No retry, no second smoke, no
T1/U3, no cross-node pooling is authorised by this review.** Any future change to a measurement, the isolation
records, the pins, the kit tip, the data manifest, or the scope would require a fresh review.

---

## 10. Attestation and command record

This review is the only file written (uncommitted). I did not run the smoke or any GPU/U2/census job, did not edit a
unit or code, did not commit/push/delete anything, did not touch HTCondor/deepthought/TASL-7/TASL-2, and made no
write on Ada. Read-only operations (19 November 2026, Europe/Berlin):
`pwd`/`git rev-parse HEAD` (`1cc54d81`)/`git rev-parse origin/main` (`de3de54f`)/`git status`;
`git show origin/main:docs/r1/PLAN.md` rows `R1-TRACKG-G0-GO:1258`, `R1-TRACKG-LICENCES:1269`,
`R1-TRACKG-PORT-DECISIONS:1289`, `R1-HARNESS-ISOLATION:1290`; the accepted kit report/review and fix review (shas
above); `shasum -a 256 -c SHA256SUMS` in all five result dirs (**rc 0**, 427/425/425/425/425 entries OK); reads of
the five units, the five result mds and their captures; Python reads of the 45 `run_record.json`-equivalents, the
verifier/summary JSON, the sampler CSVs and the run logs; recomputation of the sampler maxima, the pins, the canonical
node-spec shas and the budgets; live Ada (`ssh -o BatchMode=yes experiment_zhixu`, host `ucrtasl`, user `dowling`):
`git rev-parse/status` of the two kit worktrees, `sha256sum` of every file named by the five `SHA256SUMS` (mapped to
the live evidence), `cat/ls/stat/find/readlink`, `sha256sum` of `pins/*.json` and the data manifests/setup logs, and
read-only Python recomputation of the pins and node-spec shas (no writes; no GPU command run). The only local files
outside this review are transient `/tmp` hash dumps used for the comparison. No live-host state is claimed beyond
what these read-only commands returned.
