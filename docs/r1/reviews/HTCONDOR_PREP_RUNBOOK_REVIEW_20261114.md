# Independent pre-execution review — ETP HTCondor preparation runbook (night of 13/14 Nov 2026)

**Reviewer role:** fresh, independent, read-only reviewer. Not the author, not the executing agent.

**Date/time of review:** 13 November 2026, 23:20–23:55 CET (Europe/Berlin).

**Reviewed document:** `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` (240 lines), branch
`htcondor-prep-20261114` from `origin/docs/runbooks-14nov` @ **`69b3576bb0779b50650ae0abb356627458910a03`**.
Worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-prep-20261114`, clean
before and after this review (only this review file was added).

**Scope.** Pre-execution review, as the document's own opening step requires (L3): the §0.3 ETP-wiki
facts, internal consistency and night-window executability, existence/consistency of every referenced
artifact, and the safety/scope rules (no deletion, own jobs only, no Paper B data, no secrets, VPN
window, disk/quota and GPU-hour limits). Line W2 (§8, L239) is in the start message and therefore in
scope.

**Hard limits of this review (deliberate).** No SSH, no deepthought/HoreKa/ETP access, no execution of
the runbook, no cluster commands. Nothing on the pool was run or inspected. No file other than this
review was written, no commit or push was made. Every statement below about cluster state (drivers,
GPUs, quotas, accounting groups, `/ceph/srv`, registry login state) is therefore **not verified here**
and is marked as such.

---

## 1. What was checked, and how

| # | Item | Method | Result |
|---|---|---|---|
| 1 | The runbook itself, all 240 lines | `read`, line-numbered | Read in full; every line reference below is to commit `69b3576b`. |
| 2 | Official ETP wiki (`wiki.etp.kit.edu`) | `web_fetch` of wiki root and `/books/htcondor` | **Not reachable without login**: both redirect to the BookStack login page (`https://wiki.etp.kit.edu/login`). No wiki page content could be read. |
| 3 | ETP HTCondor tutorial / GPU tutorial on Indico | `web_search`, `web_fetch` of Indico events and PDFs | The 2022 tutorial is public: [ETP Batch System Tutorial, M. Schnepf, 11 Aug 2022](https://indico.kit.edu/event/2951/attachments/5343/8200/presentation.pdf) (also [event 2963](https://indico.kit.edu/event/2963/)) — downloaded and text-extracted. A newer tutorial page [event 4627](https://indico.kit.edu/event/4627/) is **access-key protected**. |
| 4 | ETP tutorial Git repo (`gitlab.etp.kit.edu/EKPCondor/HTCondor_Tutorial`) | `web_fetch` | **Login-gated** (`/users/sign_in`), no content. |
| 5 | A recent public ETP/TOpAS/NEMO2 description | `web_fetch` of [HEPiX 2024, M. Schnepf, KIT](https://indico.cern.ch/event/1377701/contributions/5896917/attachments/2838161/4960202/HEPiX_2024_Matthias_Schnepf_KIT.pdf) | Downloaded and text-extracted; used as cross-evidence for TOpAS/NEMO2/containers/JDL fields. |
| 6 | `r1/scripts/w2_execute_all_identity_check.py` on `origin/mac-w2-budget-20261109` | `git ls-tree`, `git show` | Exists (99 lines). Read in full: CLI, imports, exit codes (§5 findings). |
| 7 | `docs/r1/reviews/B1_TASL7_REAL_WORKER_RESULT_REVIEW_20261107.md`, `B1_TASL7_WORKER_ONCE_60EC_REVIEW_20261107.md` on `origin/mac-b1-20261107` | `git show`, `git grep` | Both exist; both contain `e5dc8c67…`, `1be4ae33…`, `0.922225`, Python 3.13.4, NumPy 2.4.4, scikit-learn 1.8.0. |
| 8 | The reviewed one-shot command's SHA-256 (`1be4ae33…`) | `shasum -a 256` on `docs/r1/proposals/B1_TASL7_WORKER_ONCE_60EC_20261107.sh` at `origin/mac-b1-20261107` | Matches `1be4ae335cd8e22d123b3253617aa1612fcb0f7ea7076900addc5d0cacf1a5b3`. The script itself asserts PAPER `60ecf1dae299…` and HARNESS `a3fedbbd4430…`. |
| 9 | Cited "paper commit `e5dc8c67…`" | `git cat-file` (full SHA), `git branch --contains`, all 111 `origin` refs; GitHub API for the paper and harness repos | **Not reachable from any fetched ref in the shared clone** (full clone, `is-shallow-repository: false`, no partial-clone promisor); GitHub API for `dowlingwong/Agent_paper_B` returns 404 (private repo, so not checkable there); harness repo returns 422 for that SHA. |
| 10 | `a3fedbb…` (harness) | GitHub API + repo docs | **Exists** in the public repo `dowlingwong/autoresearch_harness`; `uv.lock` at that commit **exists** (blob `98d6e6556f6a…`, 536 392 B); `requires-python = ">=3.11"`. |
| 11 | llama.cpp `620d2225…` | GitHub API (`ggml-org/llama.cpp`) | **Exists**, commit dated 2026-10-15; matches the repo's R1-DT-PIN record (`0.7.0-dev (build 1, commit 620d222)`). |
| 12 | Base image tag `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` | Docker Hub registry API | **Exists (HTTP 200)**. CUDA 12.4 minimum driver 550.54.14+ — confirmed ([GPU Compat Tracker](https://gpucompat.com/cuda/12-4/)). The runbook's "take 12.2" fallback tag as written (`12.2.2-cudnn-devel-rockylinux9`) **does not exist (404)**; `12.2.2-cudnn8-devel-rockylinux9` and `12.2.2-devel-rockylinux9` do. |
| 13 | Official probe images `mschnepf/slc7-condocker`, `cverstege/alma9-gridjob`, `mschnepf/cs8-base` | Docker Hub API | Repositories exist (200); existence only — image contents not checked. |
| 14 | `TRACKS_HOST_FACTS_20261030.md` §0.5 freeze pin `f1c818e5…` | `git show` on `origin/docs/runbooks-14nov` | **Matches**: `pip_freeze.txt`, 65 packages, sha256 `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687`, Python 3.11.17/3.11.18. |
| 15 | `docs/r1/overnight/trackp_code_20261026/pip_freeze_trackp-cpu.txt` | `git show` | Exists on the reviewed branch (101 lines); pins `torch==2.14.1+cpu`, `numpy==2.4.4`, `scikit-learn==1.8.0`. Note: `docs/r1/PLAN.md` R1-ENV-PIN separately pins `torch 2.6.0+cu124` — two torch pins coexist (finding F19). |
| 16 | §1.2 pinned-path branches | `git ls-tree` on `origin/mac-int-20261107`, `origin/trackS-ops-20261030`, `origin/mac-b1-20261107` | All three exist and contain `/ceph/dwong` references (PLAN, STATUS, handoffs, sweep-1 runbook). |
| 17 | `R1-DT-PIN-SWEEP1` | `git grep` on `origin/docs/runbooks-14nov` `docs/r1/PLAN.md` | Exists (row at PLAN L596) but **names no file paths** — it names paper/harness pins, config SHA, GGUF SHA. §5's "files named by R1-DT-PIN-SWEEP1" is therefore not a usable file list by itself (F1). |
| 18 | Delivery path `~/Documents/agent_paper_B/Claude outputs/` | `ls` on the Mac | Exists. |
| 19 | Cross-document timing constraints | `git show` of `docs/r1/prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md` | B1 `_d` is expected 06:00–11:00 CET; the cluster agent's 05:30 CET disconnect is consistent with that. |
| 20 | Cluster state: drivers, GPU device names, quotas, accounting groups, `/ceph/srv/dwong`, docker login, sweep-1 output paths | — | **Not checked** (no SSH allowed). All such claims are marked UNVERIFIED. |

---

## 2. Findings

Severity: **BLOCKING** = executing as written would certainly fail or be unsafe; **MAJOR** = a stated
goal or standing rule is at real risk as written; **MINOR** = robustness/clarity that can cost the
night; **NIT** = wording.

| ID | Sev | Where | Finding and evidence | Exact required fix / author question |
|---|---|---|---|---|
| F1 | **BLOCKING** | §5 (L209) | The W2 command is not executable as written. The script's own docstring: `python -m r1.scripts.w2_execute_all_identity_check <root_trials.jsonl[.gz]> [...] --runs-total W`; `--runs-total` is a **required** argument (argparse `required=True`), and the script imports `r1.c3.features.row_worker_runs` and `r1.c3.analysis_guard.refuse_sealed` at call time. Running it as a plain script path (as §5 says) puts `r1/scripts` on `sys.path`, not the repo root, so the import fails (`ModuleNotFoundError`, uncaught → exit 1); omitting `--runs-total` → argparse exit 2. §5 also gives no Python environment for the r1 dependencies and no file list (F17: `R1-DT-PIN-SWEEP1` names no paths). Because W2 is in the start message, this in-scope step fails as written. | Replace §5's line with the exact invocation: `python -m r1.scripts.w2_execute_all_identity_check <files…> --runs-total <W>`, run from the repository root of the `origin/mac-w2-budget-20261109` checkout; state W's source (sweep-1 authorization/config, **not** any label table); state the interpreter (an environment that has the r1 deps, e.g. the harness/Track-S venv on deepthought, recorded); list the files ("the `root_trials.jsonl[.gz]` under the sweep-1 output directory recorded in the sweep manifests / `docs/r1/authorizations/c3_sweep1_20261027.md`"). Also align §5's "a difference is reported" with the start-message "如有差异 STOP" — the runbook must say the difference is STOPPED and handed to the author. |
| F2 | **BLOCKING** | §4.4 I2 (L201) | I2 tells the agent to archive "the exact paper and harness commits" and earlier calls the source "the reviewed one-shot command at paper commit `e5dc8c67…`". `e5dc8c67…` is **not reachable** from any of the 111 `origin` refs in the (full) shared clone, and not from the public harness repo. The command actually binds (and asserts) PAPER `60ecf1dae299ee424aa1bdfe078eab02a881b87e` and HARNESS `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (script lines 24–26). If the agent archives `e5dc8c67`, the script's `rev-parse HEAD == 60ecf1da` assertion fails and I2 exits non-zero — a certain failure of the determinism probe. | Cite the commits the command itself binds: paper **`60ecf1da…`** + harness **`a3fedbb…`**; add "confirm both commits are present in the deepthought/Mac clone (or fetch) before writing the I2 job"; drop `e5dc8c67` or define exactly what it is. Also say where the harness clone comes from (it is a separate public repo; I2 needs a `git archive` of `a3fedbb` too). |
| F3 | **MAJOR** | §0.4 B (L61–62) + §4.4 (L196) | The image-delivery path is undefined and probably not executable tonight. `docker info` / `docker system info` do **not** report registry logins (only daemon config, mirrors, insecure registries); the only place a login is recorded is `~/.docker/config.json`, which contains registry auth tokens — a credential file that §0.4 B itself forbids reading. The stated fallback — a `docker save` tar under `/work` — is **not a pullable image reference** for HTCondor's docker universe, and §4.4's "(or loadable)" has no mechanism defined. So I1–I4 (the "pinned image on the batch system" part of the goal) likely cannot run tonight, and the agent will discover this late. (Independently: the repo records a 12 Oct precheck "Deepthought: Docker daemon cannot be reached" — `docs/r1/PLAN.md` DT5_FEASIBILITY_PRECHECK — while the 4 Nov author row says the author is in deepthought's `docker` group; a `docker info` gate is needed either way.) | Define the outcome explicitly: (a) if a registry is usable, name it and the exact non-secret login check (or a harmless push probe) — never `docker login`; (b) otherwise record I1–I4 as **not executed tonight (no pullable image)** in the report and question list, and test the image only on deepthought with `docker build` + `docker run` inside the image; (c) add a `docker info` pre-check with the apptainer/`docker save` fallback from `PLAN.md` R1-BX-REVISIONS (g). Do not leave "(or loadable)" undefined. |
| F4 | **MAJOR** | §0.2 cadence, §1, §3, §4.3 (L194), §6 (L229) | No night schedule or priority, and the plan does not fit the window. The first step (§1) is unbounded: a full `find -xdev` inventory of `/ceph/dwong`, then per entry an rsync plus **two full SHA-256 manifests of every file**, three git checks and a review. §3 then builds three `uv` environments plus a CUDA torch plus a CUDA `llama.cpp` build inside one image, with its own review. §4.3's "about 6 hours after the first wave" cannot happen before 05:30 (first wave earliest ≈00:30 → +6 h ≈06:30), and §6's "report … at 06:00 CET" is after the mandated 05:30 disconnect (L229). As written, goals 3–4 (probes/queue times) can be starved by §1/§3. | Add an explicit timetable with hard cut-offs (e.g. §2 facts first; §3 build started early/in the background; stop starting new moves at 03:30; all probes submitted by 04:30; report written 04:45–05:15; disconnect ≤05:30) and a priority order (queue-time probes > image build > moves). Drop the +6 h resubmission or label it "cannot happen before 05:30". |
| F5 | **MAJOR** | §1.4 (L120–130) vs §0.5 (L74) | The move loop has no pre-copy free-space gate for the 15 % STOP. §1.1 records quotas, but §1.4 rsyncs without computing whether the entry still leaves ≥15 % free on `/work`; a failed verification must leave **both** copies in place (L130) and the no-deletion rule forbids removing the failed copy, so repeated failures consume `/work` with no recovery described. | Before each rsync: compute the entry's bytes and require `(free_after_copy / quota) ≥ 15 %` and `free_after_copy ≥ size + margin`; record it in `MOVE_LOG.tsv`; if it would breach the floor, stop the move programme and report. State how a failed copy is retired under the no-deletion rule (move to a `_to_delete` under `/work`, or ask the author; do not `rm`). Add `mkdir -p /ceph/dwong/_to_delete` and a collision guard before the `mv`. |
| F6 | **MAJOR** | §0.4 C (L67), §4.1/§4.3 (L173–177, L194), §4.4 I3/I4 | The GPU-hour cap is planned to be consumed exactly. Wave 1 GPU jobs P4–P7 = 4 × 1800 s = 2 GPU-h; resubmissions of P4 and P6 at +3 h and +6 h = 4 × 0.5 h = 2 GPU-h; I3 + I4 = 2 × 1 h = 2 GPU-h → **exactly 6.0 GPU-h**, the author's cap, with zero margin. TOpAS preempts/backfills ETP jobs (HEPiX 2024: "backfilling with jobs from GridKa via COBalD/TARDIS and preemption"), so any eviction/restart adds GPU time and breaks the cap. §4.2 records evictions but there is no GPU-hour counter. | Add a running GPU-hour register (from event-log run times / `condor_history` `RemoteWallClockTime`), stop at a margin (e.g. ≤5 GPU-h), and drop one GPU resubmission (or I4) unless the register allows it. State that restarts count. |
| F7 | **MINOR** | §4.4 I3 (L202) | The `xrootd` endpoint and transfer-size facts are unverified or contradicted by the only public tutorial: the 2022 deck gives `root://ceph-node-a.etp.kit.edu://<user>` for `/ceph/srv`, while the runbook says `root://ceph-node-j.etp.kit.edu`; the 2022 deck's size guidance is ">2 GB input per 30 min runtime = data-intensive, add `TARGET.ProvidesIO =?= True`", not a 100 MB transfer limit. If the endpoint is wrong, I3's model copy fails (it has a skip fallback, so not unsafe, but the goal of testing the model path is lost silently). | Author question: confirm the current `/ceph/srv` XRootD endpoint and the transfer limit from the wiki. In I3, verify the GGUF sha256 (`509287f78cb4…`, R1-DT-PIN-SWEEP1) before loading, and record which endpoint was used. |
| F8 | **MAJOR** | §4.2 (L186–188), §4.3 (L194), §0.4 C (L64) | The resubmission plan can exceed the author's 10-job cap: 7 wave-1 jobs + 4 resubmissions = 11 if the wave-1 probes are still queued (they are explicitly allowed to idle for 4 h, L190). The runbook says to remove an idle probe only "unless it blocks your 10-job limit" but not which one or how to record it. | State the ordering: before a resubmission, ensure ≤6 of the author's own jobs are active; remove the author's own idle duplicates (allowed: own jobs) and record them as `>4h (removed)` in `queue_times.tsv`. Add the GPU-hour register to the same check. |
| F9 | **MINOR** | §1.4 (L126) | `mv /ceph/dwong/X /ceph/dwong/_to_delete/X.moved_20261114` assumes `_to_delete` exists; if the destination name already exists, `mv` nests the tree inside it rather than failing. `ln -s` also has no guard against an existing target. | `mkdir -p /ceph/dwong/_to_delete`; `test -e` before mv/ln and use a unique suffix (`…moved_20261114_<n>`) on collision; abort the entry otherwise. |
| F10 | **MINOR** | §1.1 (L94) | The in-use check is host-local (`pgrep`, `/proc`) but the runbook does not say on which ETP login hosts it must run. A process on `portal1`/`bms*` using `/ceph/dwong/X` is invisible to a check on deepthought. (The rename+symlink keeps the path working, but writers on the moved inode would diverge from the `/work` copy.) | Run the process check on every login host where `/ceph/dwong` is mounted (deepthought, portal1, bms1–3), or record in `MOVE_LOG.tsv` that only deepthought was checked; note `condor_q` is pool-wide. |
| F11 | **MINOR** | §1.2 (L100) | The pinned-path grep covers only three Mac branches. It misses the sweep-1 outputs themselves (the authoritative paths are in the deepthought sweep manifests / `docs/r1/authorizations/c3_sweep1_20261027.md`) and `origin/dt-sweep1-20261026`. A missed pin does not break the symlink protocol, but it silently disables the §0.5 STOP "a pinned path names it". | Add the sweep-1 authorization/manifests and `origin/dt-sweep1-20261026` to the grep, and state that the deepthought sweep manifests are the authoritative pinned-path list (read-only). |
| F12 | **MINOR** | §4.1 P3 (L173) | "remote CPU" probes set only `+RemoteJob = True`; such a job can still match a local ETP slot, so the "remote CPU" queue-time class may not be measured at all. | Either add a requirement excluding local ETP slots (e.g. `TARGET.ProvidesETPResources =?= False`) and review it, or mark P3 as "best effort" and record the actual site; report the class only if a remote execution is observed. |
| F13 | **MINOR** | §4.2 (L188) | `exit` is a column of `queue_times.tsv` but the runbook never says where it comes from (`condor_history -af ExitCode` or `ExitStatus`); `condor_history` only sees finished jobs, so held/idle/removed probes need `condor_q -af`. | Name the exact attributes and the tool for queued/held vs finished rows. |
| F14 | **MINOR** | §3 (L152) | Torch pin ambiguity: `pip_freeze_trackp-cpu.txt` pins `torch==2.14.1+cpu`, while `docs/r1/PLAN.md` R1-ENV-PIN pins `torch 2.6.0+cu124` (driver 535, TASL-7). The runbook says "plus the matching CUDA torch build … if a CUDA wheel version is not pinned anywhere, record the choice as `proposed:`" — but a CUDA version *is* pinned in the repo, and it does **not** match the CPU freeze. The agent could build a mismatched environment and call it pinned. | Say which source wins: match the freeze version (2.14.1+cuXXX if that wheel exists) and record `proposed:` for the exact build, or use the R1-ENV-PIN torch and say why; record `python -VV` + `pip freeze` for each environment in the README. |
| F15 | **MINOR** | §3 (L153, L147) | (a) "Use the same build flags as `build-exam`" — no `build-exam` reference exists on `docs/runbooks-14nov`; the repo's documented flags are in `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md` §2.1 (`-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89 -DCMAKE_BUILD_TYPE=Release`) and `TRACKS_HOST_FACTS_20261030` §2. The TASL-7 `CMakeCache.txt` is unavailable by design tonight (Tailscale off), so the conditional is always the fallback. (b) The CUDA 12.2 fallback tag as written does not exist on Docker Hub (`12.2.2-cudnn-devel-rockylinux9` → 404; use `12.2.2-cudnn8-devel-rockylinux9` or `12.2.2-devel-rockylinux9`). | Cite the repo flags explicitly, and fix the fallback tag name; keep `CMAKE_CUDA_ARCHITECTURES="70;80;89;90"` as the declared list. |
| F16 | **MINOR** | §0.3 (L55), §0.4 A (L59) | "The tutorial uses `cms.higgs`" is **contradicted** by the only reachable public tutorial and by the 2024 HEPiX JDL, both of which use `accounting_group = belle`. The fallback "use the tutorial's `cms.higgs` for the CPU probes only" therefore rests on a misattribution; a non-existent group could hold the jobs. | Change the fallback to `belle` (documented example) or to no group; keep the author question in §7. |
| F17 | **MINOR** | §5 (L209) + §1.2 | `R1-DT-PIN-SWEEP1` (PLAN L596) names paper/harness/config/GGUF pins, not `root_trials.jsonl` paths, so "files named by R1-DT-PIN-SWEEP1" is not a file list; the agent cannot locate the W2 inputs from the runbook alone. | Name the sweep-1 output directory source (sweep manifests / authorization on deepthought) and the exact glob, read-only; do not open label tables. |
| F18 | **MINOR** | §4.4 I3 (L202) | The model path is conditional on a directory existence that is never checked ("if the author has a `/ceph/srv/dwong` directory with it"), and no read-only discovery step is scheduled. | Add a §2/§4.4 read-only check (`ls -l /ceph/srv/dwong`, `xrdcp` endpoint from §2) and record the result; verify the GGUF sha256 before loading. |
| F19 | **MINOR** | §0.1 (L21), §6 (L229) | The runbook runs the night with Tailscale off while B1 `_d` (TASL-7, expected 06:00–11:00) and the experiment agent are active. Nothing checks that no Mac→TASL-7 session is in use before the KIT VPN displaces Tailscale, and no coordination with the experiment agent is stated. | Add a pre-flight `tailscale status` check and a "record VPN-up/VPN-down times" step; never kill Tailscale processes; the start message should confirm the handover. The 05:30 disconnect order itself is correct for B1's end. |
| F20 | **MINOR** | §0.2 (L36) vs §5 (L209) | §0.2 says "No Paper B data on the cluster tonight: no sweep tables…", while §5 reads sweep-1 `root_trials.jsonl` (field-limited, read-only) — a frontal contradiction unless the exception is stated. | Carve out the W2 read explicitly as the authorized exception (read-only, fields limited to `budget_index`, `decision`, `worker_mode`, `extra.control`; no labels), exactly as the W2 line says. |
| F21 | **MINOR** | §3 (L156) | The image build assumes `docker build` works on deepthought (`the author is in its docker group`), but the repo's own 12 Oct precheck records "Deepthought: Docker daemon cannot be reached" (`PLAN.md` DT5_FEASIBILITY_PRECHECK), and the 4 Nov check found apptainer/singularity but no podman. Discovering this at build time costs the night. | Add a `docker info` gate at the start of §3; if the daemon is unreachable, use the rootless apptainer route from `PLAN.md` R1-BX-REVISIONS (g) and record it; note that HTCondor docker universe still needs a pullable image (F3). |
| F22 | **MINOR** | §2 (L140) | `condor_userprio -all` — the public tutorial documents `-allusers` (and `-long`); `-all` may not be accepted on the pool's HTCondor version. | Use `-allusers` (or record if `-all` is rejected); keep "only the author's own line and the group lines". |
| F23 | **MINOR** | §6 (L217–227) | The report deadline and the commit list are incomplete: the report is to be written "or at 06:00 CET, whichever comes first" but the VPN-dependent work must end 05:30 (F4); and "Commit the TSV files" omits `inventory.tsv` (is it committed?), `MOVE_PLAN.md`, `POOL_FACTS.md`, the report and the questions document. | Write the report before 05:30 and send the Chinese message after/at the deadline; list every file to commit under `docs/r1/reports/htcondor_prep_20261114/` plus the two report documents. |
| F24 | **NIT** | §0.3 (L42) | "bms1/2/3" vs the 2022 deck's "bms[1,3] portal1 deepthought" — bms2 is unverified. | Author question only; submission works from one host. |
| F25 | **NIT** | §4.4 (L201) | The reviews are referenced as `reviews/B1_…` but live at `docs/r1/reviews/B1_…` (finding is only a path ambiguity; both files exist and match). | Prefix with `docs/r1/`. |
| F26 | **NIT** | §0.1 (L22) | `grep -i '^Host ' ~/.ssh/config` may not reveal the alias if the config uses `Match` blocks or a separate include; the runbook forbids reading anything else, including non-secret `HostName`/`User`/`Port` lines. | Allow reading non-secret `Host`/`HostName`/`User`/`Port` lines only; still forbid keys and `secrets.env`. |

**No finding contradicts the no-deletion guarantee itself.** The protocol as written never deletes: the
original is renamed into `_to_delete/` and a symlink is left behind. The risks found (F5, F9) are about
space accounting and collision safety, not about deletion.

---

## 3. §0.3 ETP-wiki claims — verification ledger

The official wiki (`wiki.etp.kit.edu`) is **login-gated** from this machine (BookStack login page), the
tutorial Git repo is login-gated, and the newer Indico tutorial page is access-key protected. The
reachable public evidence is the **2022 ETP Batch System Tutorial**
([Indico 2951 deck](https://indico.kit.edu/event/2951/attachments/5343/8200/presentation.pdf)) and the
**2024 HEPiX KIT slides**
([HEPiX 2024, M. Schnepf](https://indico.cern.ch/event/1377701/contributions/5896917/attachments/2838161/4960202/HEPiX_2024_Matthias_Schnepf_KIT.pdf)).
Claims below are marked **VERIFIED** only where a reachable public source states them; the wiki itself
could not be read.

| Claim in §0.3 | Status | Evidence |
|---|---|---|
| Submission with `condor_submit`; monitor with `condor_q`, `-analyze`, `-better-analyze`, `condor_history`, event log | **VERIFIED** (tools); host list partly | 2022 tutorial slides 4, 8, 13; `-better-analyse` spelling in the deck. |
| Submission from `bms1/2/3`, `portal1`, `deepthought` | **PARTLY VERIFIED** | 2022 deck: portal machines "bms[1,3] portal1, deepthought(GPUs)". `bms2` not confirmed. |
| `Universe = docker`, `docker_image = …`; official images `mschnepf/slc7-condocker`, `cverstege/alma9-gridjob`, `mschnepf/cs8-base` | **PARTLY VERIFIED** | `Universe=docker` + `mschnepf/slc7-condocker`: 2022 deck and HEPiX 2024. All three image repositories exist on Docker Hub (200); the two non-slc7 names are not in the reachable public ETP docs. "Any image the pool can pull may be used": HEPiX 2024 ("usable any image from docker hub"). |
| `RequestCPUs`, `RequestMemory` (MB), `request_disk` (kB), `+RequestWalltime` (s) | **VERIFIED** | HEPiX 2024 JDL: `RequestCPUs = 1`, `RequestMemory = 8000`, `request_disk = 5000000`, `+RequestWalltime = 3600`. |
| Multi-core jobs optimised for 1 and 8 cores | **UNVERIFIED** | No reachable public source. |
| `requirements = TARGET.ProvidesETPResources` gives `/work`, `/home`, `/ceph` | **UNVERIFIED** | Exact ClassAd not in public docs. Semantics consistent with 2022 "external resources have not mounted /home, /work, /ceph". |
| `+RemoteJob = True` allows remote sites; remote jobs must not require `ProvidesETPResources` | **VERIFIED** | 2022 deck: external resources via `+RemoteJob=True`, no ETP mounts; HEPiX 2024: "+RemoteJob = True required to run jobs outside of ETP WNs". `ProvidesETPResources` caveat follows from the same slide but the attribute name itself is unverified. |
| `request_GPUs = N` (up to 8) needs `+RemoteJob = True` | **PARTLY VERIFIED** | `request_GPUs = 1` + `+RemoteJob = True` in HEPiX 2024 JDL; "up to 8" unverified. |
| Select type with `TARGET.GPUs_DeviceName =?= "…"` | **UNVERIFIED** | Not in public docs. |
| TOpAS: V100 32 GB (8), V100S (16), A100-PCIE-40GB (24) | **PARTLY / POSSIBLE MISMATCH** | HEPiX 2024: "7 GPU nodes (8x V100, 24x V100s, 24x A100)". Counts for V100 (8) and A100 (24) match; **V100S is 24 in HEPiX 2024 vs 16 in the runbook**. Exact `GPUs_DeviceName` strings unverified. |
| TOpAS has `/ceph/srv` (`TARGET.ProvidesEtpCeph =?= True`) | **PARTLY VERIFIED** | 2022 deck: `/ceph/srv` "only readable from ETP and TOpAS"; the ClassAd name `ProvidesEtpCeph` is unverified. |
| NEMO2: L40S (36), H200 (16), `TARGET.CloudSite =?= "BwForCluster-Nemo2"`, no `/ceph/srv` | **UNVERIFIED** | NEMO at Freiburg and the `CloudSite` machine ClassAd are in public docs; the L40S/H200 counts, the exact CloudSite string and the no-`/ceph/srv` statement are not. |
| `NVIDIA_VISIBLE_DEVICES` set by HTCondor in short UUID format; do not overwrite | **UNVERIFIED** | No reachable public source (the sibling Mac runbook repeats it, which is not independent evidence). |
| `+RequestGPUMemoryMB` shares a physical GPU; never use it | **UNVERIFIED** (fact) / reasonable design rule | Not in public docs; the "whole GPU only" policy is a legitimate choice but should be recorded as such. |
| Files via HTCondor transfer only if under 100 MB; larger via `/ceph` or XRootD | **UNVERIFIED / POSSIBLE MISMATCH** | Public 2022 deck's only rule is ">2 GB input per 30 min runtime = data-intensive → `TARGET.ProvidesIO =?= True`"; no 100 MB limit found. |
| XRootD endpoint `root://ceph-node-j.etp.kit.edu//…` | **CONTRADICTED by the reachable public source** | 2022 deck: `root://ceph-node-a.etp.kit.edu://<user>`. The current wiki may name another node — author question (F7). |
| Fair-share priority; a job that started 6 times is held | **UNVERIFIED** | Not found in reachable public docs. |
| Accounting groups: belle, cms.top, cms.higgs, cms.jet, cms.production, beamdump, ams; "the tutorial uses cms.higgs" | **PARTLY / CONTRADICTED** | `accounting_group = belle` is the documented example in both the 2022 deck and the 2024 HEPiX JDL; the other group names are unverified, and "the tutorial uses cms.higgs" is not supported (F16). |

---

## 4. Executability against the night window (until 05:30 CET)

- Now: 23:55 CET; window ≈5 h 35 min to 05:30. The plan's own sequence is §1 (unbounded moves)
  → §2 → §3 (image build) → §4 (probes) with a fresh independent review for each unit (§0.2). The
  review cadence alone (move plan, Dockerfile+build log, seven JDLs, four I-JDLs, report ≈5 fresh
  reviewers) is a real share of the night; the runbook gives it no time bound.
- §4.3's second and third waves are at +3 h and +6 h after the first wave; the +6 h wave cannot
  complete before 05:30 (F4). The queue-time goal is still met by wave 1 for every resource class, so
  this is a plan-text fix, not a blocker — but the runbook should say so.
- The only hard deadline (05:30, L229) and the only report deadline (06:00, L229) conflict; the
  report must be written before the disconnect.
- The GPU-hour plan exactly equals the 6 GPU-h cap (F6); the 10-job cap can be exceeded by
  resubmissions (F8). Both are standing rules, so they need explicit accounting, not judgement calls
  at 03:00.
- The move protocol is safe by construction (no deletion), but its cost is unbounded and its
  failed-copy handling can consume `/work` (F5). The disk rule (15 %) is stated as a STOP but not
  wired into the loop.

---

## 5. Safety and scope review

- **No deletion:** preserved. `mv` into `_to_delete/` + symlink; no `rm` anywhere in §1. Fix
  `_to_delete` creation/collision (F9) and failed-copy retirement (F5).
- **Own jobs only:** §0.2 (L29) and §4.2 (L190) are consistent (`condor_rm`/`condor_hold` only on
  tonight's own job IDs); the 10-job cap and resubmission ordering need the explicit rule in F8.
- **No Paper B data:** §0.2 forbids sweep tables/labels/exam outputs; the only reads are the W2
  field-limited read (§5) and the one allowed GGUF (§4.4 I3). The §0.2/§5 contradiction needs the
  carve-out in F20. W2 reads only `budget_index`, `decision`, `worker_mode`, `extra.control` and
  refuses sealed paths — good.
- **No secrets:** §0.1 forbids key files and `secrets.env`; §0.4 B's "check `docker info` for a
  registry login" is not a secret-safe check because it cannot work without the credential file
  (F3) — fix it rather than let an agent improvise.
- **Others' processes/jobs:** the in-use check is host-local (F10); the Tailscale/VPN interaction
  needs the pre-flight in F19.
- **Quota/disk 15 %:** stated, not wired into the procedure (F5).
- **GPU-hour cap 6:** planned to exactly 6 with no accounting (F6).
- **VPN window:** 05:30 disconnect is correct for B1's end; report deadline conflict (F4/F23).

---

## 6. What this review could not check

- Any cluster fact: drivers, CUDA versions, GPU device names, slot attributes, quotas, `/ceph/srv`
  contents, sweep-1 output paths, the author's past accounting groups, docker/registry state on
  deepthought. No SSH/HoreKa/deepthought access was used, by rule.
- The private ETP wiki, the GitLab tutorial repo, and the newer Indico tutorial (login/access key).
- The paper commit `e5dc8c67…` (not reachable in the shared clone; the paper GitHub repo is private
  from here) and the deepthought clone's contents (whether `60ecf1da`, `a3fedbb`, `e5dc8c67` are
  present there).
- Whether `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` and the official images actually run on the
  ETP worker nodes (only tag existence was checked).
- The contents of the deepthought sweep-1 manifests and `R1-DT-PIN-SWEEP1`'s file paths (the repo row
  does not name files).

---

## 7. Verdict

VERDICT: NOT ACCEPTED

**Minimal fixes required before execution can begin** (all BLOCKING/MAJOR; the MINOR/NIT items can be
folded in while fixing):

1. **F1 — make W2 executable:** exact `python -m r1.scripts.w2_execute_all_identity_check <files…>
   --runs-total <W>` invocation, with the interpreter/environment, the W source, the file list source,
   and the start-message STOP semantics for a difference.
2. **F2 — fix I2's commits:** cite paper `60ecf1da…` + harness `a3fedbb…` (the commits the command
   asserts); confirm both are present in the deepthought/Mac clone or fetched before writing the I2
   job; remove or define `e5dc8c67`.
3. **F3 — define the image delivery:** a concrete, non-secret registry path, or an explicit
   "I1–I4 not executable tonight" fallback with the deepthought-only image test and a question;
   add the `docker info` gate (F21).
4. **F4 — add the night timetable, priority and hard cut-offs** (including dropping the +6 h wave and
   writing the report before the 05:30 disconnect).
5. **F5 — wire the 15 % disk STOP into §1.4** (pre-copy size check, `_to_delete` creation/collision
   guard, failed-copy retirement under the no-deletion rule).
6. **F6 + F8 — add GPU-hour and 10-job accounting** with a margin and restart counting; drop one GPU
   resubmission or I4 unless the register allows it; state the resubmission ordering.
7. **F7/F16 + §3 ledger — turn the §0.3 UNVERIFIED/CONTRADICTED claims into explicit author
   questions** (XRootD endpoint, 100 MB limit, `cms.higgs` vs `belle`, V100S count, `bms2`,
   `ProvidesETPResources`/`ProvidesEtpCeph`/device-name strings, the 6-start rule) and record in the
   report that the wiki was not reachable from the Mac. These do not block execution, because §0.3
   already says a mismatch is a question — but they must not be silently treated as fact.

Execution of the runbook (including the W2 read-only run) may begin only after the lead/author accepts
this review and the BLOCKING/MAJOR fixes above are applied or explicitly waived in the start message.
