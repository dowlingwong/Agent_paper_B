Reviewed base: harness `c025f89aeafc2199bf3487b4bcaa16678273c702` (the signed G.1b pin); accepted at harness `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`

# Independent review record — the autoresearch harness pin 2d09f9a9 (mac-trackg-t1-ar-20261121) for the third G.1b note

**Unit.** Harness branch `mac-trackg-t1-ar-20261121` (dowlingwong/autoresearch_harness): `eb14ed61` (the option-A kit `0e0b820` of R1-TRACKG-AR-COND7 cherry-picked onto
`c025f89a`), `fb3ad64f` and `2d09f9a9` (the port check's declared earlier node_lib master, keyed to the seven named T1 nodes). Authority:
R1-G1B-NOTE2-DECISIONS (NOTE2-AR A: the third note is signed once "its harness pin (harness `2d09f9a9`, `mac-trackg-t1-ar-20261121`) is
independently reviewed"); the queue of 22 Nov 2026 (01:22), item 2. The branch was delivered in READY 78 (harness bundle).

**Process.** One independent reviewer, read-only on a clone at the pin, with git-archive copies of base and head and the port tests run in
full (82 passed); scratch under `/tmp/rev_t1ar/` moved to its `_to_delete/`. One round: accepted with four minors, all citations or
documentation; none needs a new pin.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `2d09f9a9` | ACCEPTED (minors 1–4) |

**Open items.** Minor 1 and 3 are carried into the third note draft (`harness_report:`: cite the code unit report reviewed at `7330338`, blob `ee7a0c53`; the copy inside the pin is version 1; the earlier edit manifest `02e05d06…` is in git history, not under `superseded/`). Minor 2: the AR spec's `node_spec_sha256` is the canonical raw `5c1bdf3d…` the engine checks; `5bdce00a…` is labelled the spec file's sha256 in the draft and the procedure. Minor 4 (a port_support docstring) waits for the next change of that file. Not exercised here: the GPU device-to-host write of option A (no GPU on the review host); the TASL-2 host check at the pin covers the GPU smoke (C6).

## Round 1 (`2d09f9a9`)

> **ACCEPTED**
>
> Harness 2d09f9a9 (branch mac-trackg-t1-ar-20261121) is a correct, clean basis for running autoresearch_fixedtokens under option A. It changes nothing for the seven T1 nodes. I found no blocking or major issues. There are four minor findings, all in documentation or citations. None of them requires re-cutting the pin.
>
> **BLOCKING**
> None.
>
> **MAJOR**
> None.
>
> **MINOR**
>
> 1. **The report on the branch is the pre-review version.**
>    - Where: docs/r1/reports/trackg_g0_20261117/TRACKG_AR_COND7A_CODE_UNIT_20261120.md:175 (also :14, :58-61, :161).
>    - What is wrong: eb14ed61 carries version 1 of the report (blob 79aeecf0, 221 lines), from 0e0b820. The reviewed revision at 7330338 is blob ee7a0c53 (336 lines). Version 1 still has the slowdown estimate that review M1 corrected: it says "≈1.2–2 s per run", against the corrected ≈97–161 s per run for 644 requests. It also has the stale authority commit `de3de54f`, the claim "no node uses them (verified …)" without the evidence the review added, and §7/§27 describe the old branch and base (448f682).
>    - Why it matters: the third note will cite this pin. A reader of the report inside the pin gets a figure that review found wrong. There is no runtime effect.
>    - Fix: do not re-cut the pin. The third note and its spec should cite the reviewed report at 7330338 (blob ee7a0c53) and its captures, and say that the copy in the pin is version 1. Port the fixed report only if the pin is ever re-cut for another reason.
>
> 2. **There are two different "node spec sha" values, and the chunk must use the canonical one.**
>    - Where: src/autoresearch/trackg/noise_floor.py:232 (the `load_node` check `spec.raw_sha256 != data["node_spec_sha256"]`).
>    - What is wrong: the spec file's own sha256 is `5bdce00ac51718de…`, the value the U2 review and the G1B cross-check (row "Node spec at eb14ed61") cite. The harness checks a different value: the canonical hash `spec.raw_sha256` = `5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`. That canonical value is also what the manifest records (manifest.json:53) and what the U2 result report lists as "spec raw". The signed G.1b note uses canonical hashes for the seven nodes (for example mlab_cifar10 `90c8364f…`).
>    - Why it matters: if the third note's chunk sets `node_spec_sha256 = 5bdce00a…`, `load_node` stops at the first chunk.
>    - Fix: the third note must set `node_spec_sha256 5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`, and label `5bdce00a…` as "spec file sha" wherever it is cited.
>
> 3. **The previous edits manifest was not kept.**
>    - Where: nodes/autoresearch_fixedtokens/representative_edits/manifest.json:53.
>    - What is wrong: option A re-declares the manifest (node_spec_sha256 changes from `5f48b86f…` to `5c1bdf3d…`; the old manifest's sha256 is `02e05d06…`). The previous manifest was not saved under representative_edits/superseded/. Earlier re-declarations did save one (for example c162f36 saved manifest_pre_shared_dev_shm.json).
>    - Why it matters: it is only provenance (the old manifest is still in git history), and only a convention.
>    - Fix: none needed for this pin. Mention it in the third note, or add the copy if the pin is ever re-cut. Adding it now would change neither the committed pin nor the manifest sha, but it would change the harness commit.
>
> 4. **A docstring in the port checks is stale.**
>    - Where: tests/trackg/port_support.py:7.
>    - What is wrong: the module docstring still says the shared helpers are identical "(``ar_isolated.py`` also with the harness master)". After fb3ad64/2d09f9a9, a declared earlier master copy is allowed.
>    - Why it matters: it is test documentation only.
>    - Fix: reword it the next time the file is touched.
>
> **Verified sound**
>
> - **(a) Code equals the reviewed kit.** 7330338 and 0e0b820 are both reachable in this clone. 7330338 is 0e0b820 plus three docs-only commits (6f235c4, 13786d1, 7330338). At 0e0b820, 7330338 and 2d09f9a9 the code is identical:
>   - nodes/autoresearch_fixedtokens tree `689ae6c01917e16b1fca83ae973ffb4f261d2fd9`
>   - node_lib/ar_isolated.py blob `b95a9cb2633504e53bd6f1ad1d6febeaaf18f652`
>   - spec yaml blob `8ee12985cc2dd093671dcbc3fee63e5de5fc0cc3`
>   - tests/trackg/test_port_autoresearch.py is also identical.
>   - The only difference is the report text (finding 1).
>   - The other src/ differences between 7330338 and 2d09f9a9 (campaign_v2_diff, gpu_identity, manager_v2_diff, noise_floor, pilot_g4) come from the base. 448f682 and c025f89a differ by those same files, so they are not changes made by this branch.
> - **(b) Scope of the change.** `git diff --name-status c025f89a 2d09f9a9` touches exactly 10 files: the AR spec, the report, 4 files of the AR node (ar_isolated, ar_worker, manifest, run_fixed_budget), node_lib/ar_isolated.py, port_support.py, test_port_autoresearch.py and the new test_port_node_lib.py. The tree ids of the seven T1 nodes are the same at c025f89a and 2d09f9a9, and their working trees are clean:
>   - mlab_cifar10 `cd1874f2`, mlab_imdb `74767a05`, mlab_ogbn_arxiv `169ffa82`
>   - mlgym_cifar10 `b54cd059`, mlgym_fmnist `06f4690e`, mlgym_breakout_minatar `b7822e2b`, mlgym_houseprice `923ca51f`
>   - third_party/mlgym `98924b46`; the three mlab spec yamls are also unchanged.
> - **Pins recomputed** with noise_floor.frozen_pin_sha256(committed_view(frozen_file_hashes)), spec.raw_sha256 and the manifest file sha, from git-archive copies of both commits. Values are identical at base and head for all seven nodes and match the signed G.1b note where it cites them:
>
>   | node | spec (raw) | pin | manifest |
>   |---|---|---|---|
>   | mlab_cifar10 | 90c8364f | 1f047ad7 | bef79111 |
>   | mlab_imdb | 0123a8a7 | 4b1019a6 | 09edee58 |
>   | mlab_ogbn_arxiv | e952df6a | bd71fdf4 | b2cf5ae6 |
>   | mlgym_cifar10 | f1360bcd | 2d7e533b | d0ad0e64 |
>   | mlgym_fmnist | 65f229af | eb60107e | de6782b3 |
>   | mlgym_breakout_minatar | db57b202 | cec562e6 | a7fe205a |
>   | mlgym_houseprice | 2f150cde | 88d359f2 | f26332ff |
>
> - **(d) AR pins at head.** spec file sha256 `5bdce00ac51718de…`, spec raw `5c1bdf3d84c07218…`, committed pin `147f0d35d40df54b…`, edits manifest `55f2666a3d09aaed…`. All four match the U2 record. At base they were raw `5f48b86f…`, pin `b5f0ec2f…`, manifest `02e05d06…`.
> - **(d) Option A.** `git grep` finds no call to cuda_share, cuda_open, bind_cuda or _new_shared_cuda outside the ar_isolated.py definitions, in any node. Parent and worker use only `iso.SharedBuffer` + `bind_cpu` + SCM_RIGHTS + `snapshot()`. The worker writes `out.copy_(result.float())` into the CPU mapping; a device-to-pageable-host copy is synchronous. The spec sets `shared_dev_shm: false`, so runner.py:522 records `exceptions: []`.
> - **(c) The master change.** The node_lib master diff is a docstring plus `torch.cuda.init()` inside `cuda_open`, which imports torch locally and is never called. The node copy equals the master (sha256 `3ba34c67…`). The sandbox probe (isolation.py:351-369, run per isolated run from runner.py:477) loads the master but only uses Worker/serve/worker_connect/ping, which are unchanged, so it is safe. The seven nodes run their own frozen copies (`37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`, which equals the c025f89a master). If they were ever run at 2d09f9a9, only the probe would load the new master, and that path behaves the same. Under the signed spec they stay at c025f89a.
> - **(e) The port-check allowance is narrow.** It is keyed to sha `37d99ab0…` and the seven named nodes, and autoresearch_fixedtokens must carry the current master. I tested this on a scratch copy:
>   - All 8 nodes pass check_isolated.
>   - A one-byte undeclared edit to mlab_imdb's copy fails.
>   - autoresearch_fixedtokens carrying the earlier copy fails.
>   - An unnamed node carrying the earlier copy fails.
>   - A T1 node carrying the current master is accepted. That would change its pin, which the note's pin check catches.
> - **(f) Tests:** 82 passed, 0 skipped, 0 failed, in 19 min 20 s (node_lib 1, autoresearch 29, mlgym 30, mlagentbench 22). There is no GPU on this host (torch 2.6.0+cu124, CUDA unavailable), so the AR smoke ran on the CPU memfd path; the GPU device-to-host write was not exercised here. My first attempt was killed by my own 900 s timeout and is not counted.
> - **(g) Branch and commits.** The worktree is clean at 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe; the only untracked files are ignored __pycache__ directories. The three commits are linear on c025f89a. eb14ed61 carries the "(cherry picked from 0e0b820…)" trailer and is content-identical to 0e0b820's change. The commit messages are accurate. fb3ad64's interim test ran `git show c025f89a:…`; 2d09f9a replaces that with a read of the frozen copy, as its message says.
>
> **Scratch:** everything is in /tmp/rev_t1ar/_to_delete/ (base/ and head/ are git-archive copies, plus neg/, scripts/, t/, t2/ and pytest_run2.txt with the full test log). Nothing under /tmp/pb was modified.

---

Code-Commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe
Verdict: ACCEPTED

Accepted: harness `2d09f9a9` as the autoresearch_fixedtokens pin of the third G.1b note; the seven T1 nodes unchanged from `c025f89a`.
