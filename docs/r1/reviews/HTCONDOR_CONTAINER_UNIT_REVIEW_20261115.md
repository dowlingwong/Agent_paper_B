# Independent review — HTCondor adapter unit: container universe (branch `htcondor-container-20261115`, commit `e81fbe0d`)

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the unit, not the executing agent.
I ran only read-only checks: `git show`/`diff`, the repo's own test suite in a pre-existing Python 3.12 venv
(`/tmp/p2venv`, pytest 9.2.0), and the adapter's own `--dry-run` render on the Mac (no `condor_submit` on PATH,
so JDL rendering only). No cluster access, no submission, no image push, no git commit.

**Date/time of review:** 15 November 2026, 21:00–21:35 CET (Europe/Berlin).

**Reviewed unit:** branch `htcondor-container-20261115` at pinned commit **`e81fbe0d`** (one commit on the reviewed
`mac-htcondor-20261114` @ `68057612`), worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-container-20261115` (clean). Files below,
hashes verified against the Lead's message.

**Basis.** The author's ask (container universe, `runtime: container`, image by ghcr digest, a separate
image-transfer disk cap per S5, reviewed dry-run JDLs for both sites); the reviewed baseline
`HTCONDOR_ADAPTER_REVIEW_20261114.md` (rounds 1–3, accepted at paper `ee6567a0` / harness `e5830af3`); the S5
container-universe evidence (image pulled by Singularity on NEMO2; the OCI cache in the job sandbox; job dir
≈11 GB during the run for the 5,226,487,808 B image; the I3 NEMO2 run's final `Image size of job updated` =
28,107,500 kB); the S2 M1 measurement (`HasContainer`/`HasDockerURL` true on ETP/NEMO2/TOpAS); and the handoff
§9 (container-universe unit).

---

## 1. Files reviewed and pinned (SHA-256)

| File | SHA-256 |
|---|---|
| `r1/scripts/htcondor/htc_submit.py` | `351ec37c652c17f681f72a4a80c6960cc09eca0a6785605ffb1226159caee2c8` |
| `r1/scripts/htcondor/htc_config.json` | `b21a4c144ea88b9a0f3b022ff44b33fcddb625d90acbe6695e41727e0ed810eb` |
| `r1/tests/htcondor/test_htc_adapter.py` | `989e1b086be5ca6200d3eae8bb2d890f46e753309ff6139cb77c8df1d8531dbe` |
| `r1/scripts/htcondor/examples/container_probe_nemo2_l40s.json` | `29c2d3583793451648e156eeb3076c400ef53d718180a66d4ebb57445661a3e8` |
| `r1/scripts/htcondor/examples/container_probe_topas_v100s.json` | `798c5d9c22a891308d3db3a6641cab2b0f23a65e74496710091e329a5e5d435d` |
| `r1/scripts/htcondor/examples/container_probe.sh` | `7e10f6ba…` (byte-identical to the S2-reviewed probe) |
| `docs/r1/reports/htcondor_container_20261115/dryrun/cprobe_nemo2_l40s.jdl` | `6c1dd70c67c2e4f621cdea66c4fac16d1eae71c53be65ffb3fdc80c5f235abf8` |
| `docs/r1/reports/htcondor_container_20261115/dryrun/cprobe_nemo2_l40s.dryrun.txt` | `cf07c1613902f680a76df0f708dafcbdd5075b6b53f9ddb43ce82c14cbc8009e` |
| `docs/r1/reports/htcondor_container_20261115/dryrun/cprobe_topas_v100s.jdl` | `575c04fbacbc9abfd1cfd27b77c0165d78eab608be7b5cc0e346ea5695af5dfc` |
| `docs/r1/reports/htcondor_container_20261115/dryrun/cprobe_topas_v100s.dryrun.txt` | `f44ce5b59ebb0d981fb920ba8c7768c363b7ca39f22e637271e3f9720a2c26a7` |
| `docs/r1/reports/HTCONDOR_ADAPTER_HANDOFF_20261114.md` §9 | (committed at `e81fbe0d`) |

**Commit content note:** the commit also adds a **root `uv.lock`** (new file, 239 lines, paper project
`numpy`/`pyyaml` runtime extra) that is not in the Lead's file list and is unrelated to the adapter unit — see
MINOR 2.

---

## 2. What was checked, and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Docker path unchanged (no regression) | diff `68057612..e81fbe0d`; `test_docker_runtime_is_the_default_and_unchanged` | Renderer chooses `universe = docker`/`docker_image` unless `runtime == "container"`; the docker branch of the validator is the old `IMAGE` regex plus the new refusal of `image_disk_kb`; test passes. ✓ |
| 2 | Container manifest surface | diff + handoff §9 | Optional `runtime` (`"docker"` default / `"container"`), optional `image_disk_kb` (container only); the single `image` key carries the `docker://` URI; `universe = container` + `container_image` rendered. Reasonable minimal surface. ✓ |
| 3 | Digest-only images | `CONTAINER_IMAGE` regex; 3 negative tests (`tag`, `:latest`, no digest) | `docker://<repo>@sha256:<64 lowercase hex>` required; tags without a digest are refused; a tag *before* a digest is accepted (harmless: the digest wins); registry host:port forms are not matched (see NIT 1). ✓ with NIT |
| 4 | `image_disk_kb` required/refused and cap+margin rules | tests `test_container_requires_image_disk_kb`, `test_image_disk_kb_is_refused_for_docker_runtime`, `test_container_disk_must_cover_cap_plus_margin`, `test_container_image_cap_is_bounded` | Refused for docker; required for container; `disk_kb >= image_disk_kb + image_disk_margin_kb`; `image_disk_kb <= max_image_disk_kb`; clear error messages. Guards work as coded. **The basis of `image_disk_kb` is the issue — MAJOR 1.** |
| 5 | Config statuses | `htc_config.json` diff | `max_image_disk_kb` 40,000,000 and `image_disk_margin_kb` 2,000,000 both marked `proposed:` ✓ (author's fact policy respected). Status wording is partly muddled (MINOR 3). |
| 6 | Remote GPU semantics | `test_container_remote_gpu_job_renders_remote_semantics` + both dry ads | `+RemoteJob = True`, `request_GPUs = 1`, exact `TARGET.GPUs_DeviceName` in the config list, `TARGET.CloudSite` when given, **no** `ProvidesETPResources`; the synthesized ad adds `TARGET.HasContainer && TARGET.HasDockerURL`; device strings are the measured ones (`NVIDIA L40S`, `Tesla V100S-PCIE-32GB`). ✓ |
| 7 | Test suite | `/tmp/p2venv/bin/python -m pytest -p no:cacheprovider -q r1/tests/htcondor` in the worktree | **77 passed in 0.81 s** — matches the Lead's count (the diff adds 9 new test functions; 68 before at `68057612` per the earlier review record). ✓ |
| 8 | Dry-run raw JDLs are the adapter's output | re-rendered both example manifests locally with the adapter (`--dry-run --out /tmp/...`, no `condor_submit` on the Mac) and diffed against the committed `dryrun/*.jdl` | **Byte-identical for both sites** ✓ (the committed raw JDLs are genuine adapter renders; the `# manifest_sha256` comment equals the example file's sha). |
| 9 | Dry-run classads | read both `*.dryrun.txt` (produced on deepthought, no submission) | `JobUniverse=5`, `WantContainer=true`, `ContainerImage=docker://…@sha256:69b0…`, `ContainerImageSource="docker"`, `RequestCpus=2`/`RequestMemory=8000`/`RequestDisk=25000000`/`RequestGPUs=1`/`RequestWalltime=1800`, `RemoteJob=true`, `TransferInput="container_probe.sh"`, requirements with the device (and CloudSite for NEMO2) + `HasContainer && HasDockerURL`; `Cmd`/`Iwd` under the dry-run working dir. ✓ (I could not re-run `condor_submit -dry-run` from the Mac — no cluster access; the committed ads are the operator's evidence and are internally consistent with the JDLs.) |
| 10 | Submission disabled | `htc_submit.py` main (`--submit` refused while `real_submission_enabled` false); config unchanged | `real_submission_enabled` stays false; `--submit` raises; the dry-run mode only renders. ✓ |
| 11 | Examples' disk values | manifests | Both use `disk_kb = 25,000,000` and `image_disk_kb = 5,104,000` → 25,000,000 ≥ 5,104,000+2,000,000 ✓ (well above the S5-measured sandbox). ✓ |
| 12 | No other adapter files changed | diff stat | Only the files listed above (plus the root `uv.lock`); `htc_events.py`/`htc_units.py` blobs unchanged. ✓ |

---

## 3. Findings

### BLOCKING

None. The extension is dry-run-only (`real_submission_enabled` false), the docker path is unchanged, and the
committed dry-run JDLs are exactly the adapter's output for the two sites.

### MAJOR

**M1 — `image_disk_kb` is sized from the SIF file size, not the S5-measured EP-side footprint, so the
request-disk guard can accept an under-provisioned manifest.** S5 (same image, same container-universe route)
recorded the OCI cache inside the job sandbox (`APPTAINER_CACHEDIR=/srv`) and a job dir of **≈11 GB during the
run for the 5,226,487,808 B (5,104,000 kB) image** — the pull cache plus extraction is ≈2× the SIF size — and the
I3 NEMO2 run reached `Image size of job updated` **28,107,500 kB** (image + 4.35 GiB model). With
`image_disk_kb = 5,104,000` and the default margin 2,000,000, the guard accepts `disk_kb = 7,104,000 kB` (~6.9 GiB)
— below the observed image-only footprint. The two examples happen to use 25,000,000 kB (safe), but the reusable
rule under-covers. *Fix (before the adapter is used for real submissions):* define `image_disk_kb` as the
**measured EP-side image footprint** (≈11,000,000 kB for this image; cite S5) and let the margin cover the job's
own overhead, **or** require `disk_kb >= 2*image_disk_kb + image_disk_margin_kb` and document the S5 factor;
update the config status (which currently cites the SIF size and claims the margin covers "the image plus the
sandbox", which 2,000,000 kB does not) and the examples' `image_disk_kb` accordingly. This does not affect the
reviewed dry-run evidence (both examples pass with 25,000,000), but it must be fixed before real use.

### MINOR

**m2 — the pinned commit adds a root `uv.lock` (239 lines) that is not part of this unit.** It is a new file
(paper project `agent-paper-b` with the `runtime` extra), absent at `68057612`, not mentioned in the Lead's file
list or the commit message, and unrelated to the adapter extension (likely test-environment churn from a local
`uv lock`). *Fix:* drop it in a follow-up commit, or move it to the test tooling and record why it is needed; the
reviewed adapter unit should not carry unlisted files.
**m3 — documentation/status wording.** The docstring/handoff say `image_disk_kb` is "the image-transfer disk cap
in kB that request_disk must cover **in addition to the job's own disk**", but the validator only enforces the
*total* `disk_kb >= image_disk_kb + margin` (the manifest's `disk_kb` is the total request). Reword to "the
manifest's `disk_kb` must be at least `image_disk_kb + image_disk_margin_kb`" and state the S5 basis. The
`max_image_disk_kb` status text also mixes the cap with "room for the sandbox"; reword. The handoff §9 says
"ten container-runtime tests" and "77 passed (67 before)"; the commit adds **9** test functions and the baseline
was 68 at `68057612` (suite 68+9 = 77) — correct the count/wording (NIT-level).
**m4 — container-runtime coverage gaps for future use.** No tests for container + `placement: local`, container +
`executable_in_image`/`resume_dir`, or container + `etp_ceph` interactions. The current ghcr remote-probe use does
not need them, but if those combinations are allowed for real submissions, add tests/guards first (they change the
rendered transfer/requirements semantics).
**m5 — `image_disk_kb` naming/semantics.** It is called a "cap" but is used as a required coverage value; the
actual cap is `max_image_disk_kb`. Rename to e.g. `image_need_disk_kb` (or document the two clearly).

### NIT

**n1** — `CONTAINER_IMAGE` accepts a tag before the digest (harmless: digest wins) and does not accept a registry
host:port form; document or tighten.
**n2** — the examples' probe script is the S2-reviewed `container_probe.sh` (hash `7e10f6ba…`); its header still
refers to the 13/14 Nov runbook — fine for an example, but a one-line comment update would be cleaner.
**n3** — the dry-run raw JDLs are in `docs/.../html`-free plain files; record the exact `htc_submit.py --dry-run`
command next to them for reproducibility (the committed `.dryrun.txt` was produced on deepthought; my re-render
matches the JDLs byte-for-byte, which is strong evidence but the command should be written down).
**n4** — the adapter's `--dry-run` on a machine with `condor_submit` (deepthought) also writes the ad; record the
`condor_submit` rc/stdout in the same evidence file (the committed `.dryrun.txt` has the ad but not the rc line;
the handoff states rc 0).

---

## 4. Verdict and what is accepted

**What is accepted:** the container-universe extension as a **dry-run unit** — `runtime: "container"` with
`universe = container` + `container_image`, digest-only `docker://` images, the `image_disk_kb` guard family
(required/refused/cap/margin) as *mechanisms*, the unchanged docker path, the remote-GPU semantics, the two
reviewed dry-run JDLs (byte-identical to the adapter's render) and their classads (container universe,
`WantContainer`, `ContainerImageSource=docker`, `HasContainer && HasDockerURL`, measured device/CloudSite strings),
77 passing tests, and `real_submission_enabled` false (no submission path). The handoff §9 records the unit
correctly apart from the count/wording NITs.

**What must be added before the adapter may be used for real submissions:** fix M1 (image-disk basis: measured
EP-side footprint or the 2× rule; update config status/examples), remove or justify m2 (unlisted root `uv.lock`),
clear m3's wording, and decide m4/m5 (coverage/naming). The adapter may continue to be used for **dry-run only**
in the meantime.

**Residual risk carried:** the S5/I3 measurements are the only container-universe disk data (used for M1); the
dry-run ads were produced on deepthought and I could only re-render the JDLs (no cluster access to re-run
`condor_submit -dry-run`); the container path is only exercised for remote GPU sites so far (local/container and
SIF-path variants are out of scope by design); the `image_disk_kb` semantics is a cluster-side interpretation that
the author should confirm before real submissions.

VERDICT: ACCEPTED
