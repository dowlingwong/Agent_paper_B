# Batch-4c independent review — 14 October 2026

AI-assisted fresh-context review by Codex. Initial evidence: only the newest STATUS entry, BUILD_BATCH4C_PROMPT.md, the paper/harness diffs, the supplied test logs, and the before/after desktop fixture evidence. Current sources referenced by those diffs were inspected. No memory, other chats, historical producer explanations, real model calls, GPU runs or Ada runs were used. Only this review file was edited. The harness diff is empty.

**Verdict before the correction round: observed X1–X3 launch defects are repaired and the real-runner desktop path succeeds; one MAJOR defensive boundary gap and two MINOR gaps remain.** The successful fixture is engineering evidence, not scientific eligibility or authorization for an experiment. The implementation-agent Resolution follows below.

## Findings

### C1 — MAJOR: validate the effective push destinations, not only the fetch URL

`r1/scripts/dryrun_guard.py:30–35` checks `git remote get-url dryrun`, then checks that its target is a temporary local bare repository. That command checks the fetch URL. `r1/scripts/deepthought_batch1_resume.py:73–74` and `r1/scripts/ada_e1b_rerun2_launch.sh:45` push by remote name; Git can use separately configured `remote.dryrun.pushurl` destinations. A valid temporary fetch URL with a nonlocal push URL therefore passes the current guard. Multiple push URLs also need inspection. This violates the hard local-only push boundary, although the saved fresh-clone fixture uses only local destinations and provides no evidence of an external push.

Correction: validate every effective URL from `git remote get-url --push --all dryrun` using the same absolute-path, root-containment and bare-repository checks before any push, including the launcher's push dry run. Add a regression with a valid local fetch URL and an invalid push URL; it must refuse without contacting that URL.

### C2 — MINOR: the compiled guard misses module-level undefined names

`r1/tests/test_rerun2_batch4c.py:21–39` scans only `LOAD_GLOBAL`, so it detects missing function globals but misses module/class `LOAD_NAME` references. Independently compiling the current merged source with `PROBE = OTHER_MISSING_GLOBAL` appended returned an empty undefined set; appending `def probe(): return OTHER_MISSING_GLOBAL` returned `{'OTHER_MISSING_GLOBAL'}`. The current test at lines 42–49 covers only the latter. Thus the original MODELS defect and similar function-global defects are covered, but the prompt's broader “every global name referenced” requirement is incomplete. Extend the scope-aware check and add a module-level missing-name regression. This is a guard-coverage finding, not an observed missing name in current production code.

### C3 — MINOR: the newly dry-run-aware liveness CLI does not constrain its output/work arguments

`r1/liveness/__main__.py:35–48` validates environment paths, then accepts arbitrary `args.out` and `args.work` and creates those directories. `dryrun_guard.py:18–22` does not inspect these CLI arguments. The integrated runner supplies temporary paths (`ada_e1b_rerun2.py:223–228`), so the saved fixture is contained; a direct DRYRUN liveness invocation can write outside the marked root. Validate both resolved argument paths before either mkdir when DRYRUN is enabled. The explicitly exported engineering summary/log directory of `rerun2_dryrun.py:43–45,181–189` is an intentional artifact-export exception and should be described separately from temporary execution repositories.

## Required five-point checklist

### 1. X1–X3 observed failures and the static guard

X1 reads `R1_OLLAMA_MODELS`, refuses an unset variable or missing directory, and uses the validated local value in the server command before inference (`ada_e1b_rerun2.py:141–146,170–173`). The guard compiles the runner and exec-loaded helper, detects MODELS in the original `69b2bbd` source, and detects an injected function-global name (`test_rerun2_batch4c.py:42–49`); C2 bounds its coverage.

X2 requires both identity variables, sets repository-local identity in both clones, checks the local values and `GIT_COMMITTER_IDENT`, and checks both branch pushes (`ada_e1b_rerun2_launch.sh:39–46,132,154–159`). X3 installs `uv sync --extra dev` and records the pytest version (`:160–169`). `--start` requires saved setup checks, rechecks both identities/push permissions, and prints heads, identity, accepted failures, pytest and models (`:222–229`). The saved `rerun2_dryrun_20261014T133616Z/prepare.json:40–55` records DRYRUN, both successful identity/push checks and pytest 9.0.3.

The post-snapshot refinements are appropriate on source inspection: start validates the selected batch/root before any identity-start log redirection (`launch.sh:204–206,226–227`); an invalid git var explicitly returns failure even when the function is invoked in an `||` context (`:44,158–159`); fixture postchecks assert phase commits exist in the bare remote, analysis hashes agree, final local/remote heads agree, integer chat seeds arrive and an inactive-key rejection occurs (`rerun2_dryrun.py:153–169`). Targeted tests for the first two refinements are now present at `test_rerun2_batch4c.py:143–163`. Their completion must be recorded by the correction round; the saved 153-pass suite predates those additions.

### 2. Does the fixture execute the production runner path?

Yes. Fresh clones and local bare remotes are created, the real launcher performs `--prepare` and `--start`, and tmux invokes `ada_e1b_rerun2.py` directly (`rerun2_dryrun.py:50–66,116–129`; `launch.sh:228–229`). The actual collector, workers, gates, analysis, regeneration, comparison and finish execute; fake binaries replace the external GPU/model service. The fake HTTP server implements the chat protocol and logs seeds (`rerun2_fake_ollama.py:27–58`); fake GPU/ps data exercises co-tenancy (`rerun2_dryrun.py:74–82`). No tracked harness change is supplied.

The guarded fixture uses two instances/node and W=6 at E2=2, with one repetition/audit seed (`ada_e1b_rerun2.py:62–64`). Those deviations respect unchanged analysis requiring at least two instances and paired verification costing 2*r=4. Liveness alone uses one instance and four runs. Production remains four prescribed nodes, 18 instances, W=20, E2=4/8/12, two repetitions and six audit seeds (`:54–64,223–228`). The ephemeral loopback port isolates the occupied Mac port; production remains 11434 (`deepthought_batch1_resume.py:32–34`).

The saved passing summary records every checkpoint, including STATUS, six generated commits, matching per-arm regeneration hashes, completion, restart refusal, 100 seeded chats and three inactive-key rejections in 319.61 seconds (`results/r1/engineering/rerun2_dryrun_20261014T133616Z/summary.json:1–207`, especially 149–152 and 183–206). I additionally checked all six recorded commits with full `git show --check`; all returned zero, including result artifacts otherwise excluded by the runner's own whitespace check (`deepthought_batch1_resume.py:67–70`).

### 3. Can DRYRUN leak into production?

The integrated fixture requires explicit `R1_DRYRUN=1`, a marked directory beneath the system temp root, and contained execution paths; Ada host `ucrtasl` is refused (`dryrun_guard.py:9–25`; runner `:43–45`; launcher `:15–24`; fake server `:60–65`). DRYRUN clones rename origin to dryrun, and DRYRUN commits/outputs are labeled (`launch.sh:149–152`; helper `:32–38,64–74,286–290`). Normal production uses origin, fixed production design and port. C1 and C3 identify the remaining defensive gaps; the saved fixture itself does not exhibit leakage. Raw old-runner reproduction necessarily retains its original ENGINEERING_ONLY/PILOT text and origin remote name, but origin points to a local temporary bare repository; its exported summary labels DRYRUN (`rerun2_dryrun.py:97–114`; before-fixes runner.log:1–9).

### 4. Residual unexercised paths

- Real Ollama/model-file validation beyond the fake digest; GPU offload, actual OOM, shrinking free memory, disappeared GPU, card wait/reselection, multi-card competition and server-load/timeouts (`runner:106–118,176–204`; helper:123–149).
- `tabular_mlp` and `openml_ionosphere`, the full production instance/budget/E2/repetition/audit scale and concurrency. One repetition cannot exercise independent leaf-split headroom; results can contain null intervals (`runner:54–64`; comparison log in the supplied passing fixture).
- Liveness excluding one node or STOPping below two, malformed chat/parse failures, repeated inactive revisions reaching their cap, model-digest mismatch, partial offload and real provider failures. The fake server deterministically returns successful chat responses and one revisable inactive-key pattern (`rerun2_fake_ollama.py:36–58`; runner:229–239).
- Real GitHub authentication/transport, rejected/non-fast-forward pushes, interrupted commit/finish, recovery after process death, and author-directed intervention after an interrupted phase (`helper:64–80,270–308`; runner:78–103,341–354). Completed-batch refusal is exercised; interrupted-phase recovery is not exercised by this fixture.
- Long-running monitoring/telemetry behavior. The fake co-tenant is a static owner/process census, not a real competing job.

### 5. Fail-before/pass-after for X1, X2 and X3

The before-fixes real entrypoint log records exactly `NameError: name 'MODELS' is not defined`, with preconditions incomplete and no model started (`results/r1/engineering/rerun2_dryrun_20261014T131354Z/runner.log:7`; its summary.json). Five targeted tests fail at the prior source: compiled-global guard, unset/missing models, model-command construction, identity/dev setup and dev-extra installation (`batch4c_test_logs_20261014/x_fail_before_final.log:210–215`). The dev regression explicitly observes old `sync` without `--extra dev` (`:203–205`). The saved pass-after targeted log reports 31 passed/1 skipped (`x_pass_after_final.log:1–2`); the full saved suite reports 153 passed in 351.20 seconds (`full_r1_after_final.log:1–5`). Nested-clone prepare reports 152 passed/1 skipped, with only recursive integration skipped (`passing prepare.json:22–25`; `test_rerun2_batch4c.py:166–172`). These establish the requested observed regressions; C1–C3 and the post-snapshot tests require the single correction round's fresh verification.


## Resolution (implementation agent, 14 October 2026)

One correction round; AI-assisted by Codex. Code/tests/evidence commit **`bb7a12c02717566ebe8338287f9f9b55afe97beb`**, pushed to paper `origin/main`. The harness and production design are unchanged. This records implementation verification, not a second independent review.

| Finding | Severity | Resolution |
|---|---|---|
| C1 — fetch-only remote validation | MAJOR | **Fixed.** `dryrun_guard.py:30–39` validates the fetch URL and every effective push URL from `remote get-url --push --all`; all must resolve to absolute local bare repositories under the marked root. A real local-config regression adds both a valid local push URL and a hostile HTTPS push URL and refuses before network use. |
| C2 — missing module/class global-name coverage | MINOR | **Fixed.** The compiled scan includes scope-aware `LOAD_NAME` as well as `LOAD_GLOBAL`; function, module and class injected missing-name probes are all detected, alongside original MODELS. |
| C3 — direct liveness CLI paths escape root | MINOR | **Fixed.** `liveness/__main__.py:48–53` checks resolved output/work arguments before either mkdir in DRYRUN. Parameterized no-worker/no-model tests cover both escapes and assert no directories are created. |

All three findings are closed on the stated tests; no open MAJOR remains. The invalid-committer and external-batch-start regressions also pass. Targeted correction suite: **45 passed, 1 skipped** (recursive integration excluded); a nested-hostile-pushurl fixture isolation correction was then checked under inherited outer-batch variables, **1 passed**. The final complete `make r1-test` is **158 passed in 399.89 seconds**, including a fresh actual launcher/runner DRYRUN after every correction. Its nested-clone unit suite is **157 passed, 1 skipped**.

Final end-to-end summary: `results/r1/engineering/rerun2_dryrun_20261014T135521Z/summary.json` (**DRYRUN**, **348.14 seconds**). Every phase and STATUS completed, six commits exist in the local bare remote, all three regeneration hashes match, 100 fake chat calls carry seeds, three inactive-key rejections occur, and a finished-batch restart refuses. The final fixture includes the postflight refinements described in the review. Raw failing preparation logs from the intermediate nested fixture are preserved in `results/r1/engineering/rerun2_dryrun_correction_prepare_failed_20261014/`; the earlier successful fixture and all other failed attempts remain intact.

The tiny-fixture instance/budget/port deviations and residual unexercised production paths listed above remain explicit. This closes the batch-4c engineering launch gate only. Ada liveness, collection, scientific decisions and any future evidence authorization remain separate; the author has explicitly authorized a fresh PILOT runner attempt after these checks.


**Ada test-host portability check before fresh preparation.** The desktop integration test is explicitly skipped on physical `ucrtasl`, where DRYRUN is forbidden; pure path/push-URL guard fixtures explicitly mock a desktop host. The external-batch refusal regression accepts Ada's earlier host refusal as well as desktop path refusal and still asserts no logs are written. Runtime code/design are unchanged. With `platform.node()` set to `ucrtasl`, the new module is **13 passed, 1 skipped**; the complete nonrecursive unit suite is **157 passed, 1 skipped** after this test-only adaptation. The actual fresh Ada `--prepare` will provide the final host-specific suite evidence. Both logs are preserved in the batch-4c test-log directory.
