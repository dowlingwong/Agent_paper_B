# G.4 on the TASL pair — authorization note (T1 pilot, real runs) — DRAFT for the author's signature

This file is the note in the key-block format that `sweep2/t1_tasl/g4_tasl.py check_note` parses. Every line of the
form `key: value` is a field, and no key may appear twice; the parser ignores all other lines. Prepared by the Mac-desk
agent (Claude), AI-assisted, 21 Nov 2026, on `mac-g4-auth-20261121` over published `main` `985dd45d`; to be
independently reviewed with the code unit (P4).

**On signature** the author copies this file to `docs/r1/authorizations/g4_t1_tasl_<YYYYMMDD>.md` with these edits:
- `approved: true`;
- `paper_commit` and `spec_sha256` filled;
- P3 completed per decision G4-ORDER, and P4 completed with the review path.

The author then publishes the note byte-identically on `main`, in the same commit as the spec's `paper.commit` (the
launch commit).

**How both hosts launch.** Both TASL-7 (`serve`) and TASL-2 (`run-node`) launch from a published checkout at or after
the commit that publishes this note and the spec, whose code equals `paper_commit` outside `docs/` and the spec file.
They use the TASL launch binding (`verify_launch_tasl`; decision G4-LB below). The code checks all of the following:
- this note on `origin/main`;
- `run_id` and `harness_commit` equal to the spec's;
- P1–P5 PASS with their citations, and no `<…>` placeholder left in any field;
- P1 citing TASL-2's host check record;
- P4's review files on `origin/main`;
- both keys;
- the imported modules are the reviewed source files.

**The G.1b checkout.** G.1b launches, including the TASL-7 nodes under the second G.1b note, must come from
**exactly `985dd45d`**. It is the only published commit that both holds the signed G.1b spec (`060aac91…`; earlier
commits hold the `-a` spec) and has code equal to the note's `paper_commit` `10fd3343`. `main` already differs from it
outside `docs/` from `7219a57a` on, and this unit's merge widens the difference. Any later G.1b note is copied from
`origin/main` into that checkout's `docs/r1/authorizations/` as an untracked docs file. G.4 uses its own, separate
checkout.

**Values.** The binding values below were copied from published `main` `985dd45d`.
- `spec_sha256` there is `fd5a14b51463d5658dc1833b1e6805f5b4241078ec3fa813a9a14df833ba1b6b`. It changes at the launch,
  because `paper.commit` changes.
- The label is ENGINEERING_ONLY because the parser requires it. The pilot reads no label, and its outputs (per-call
  time, the ratio, the dates) are engineering measurements.

## Author decisions (not part of the note)

**G4-LB. The launch binding for G.4.** R1-G1B-TASL-DECISIONS chose LB A (`verify_launch_tasl`) for G.1b only. The
binding G.4 shipped with (`g1b_lib.verify_launch`, S2-C5) can never pass for a note on main that names its launch
commit (READY 75).
- **A (recommended): apply LB A to G.4** `serve` and `run-node`. The checkout is published, and its code equals the
  note's `paper_commit` outside `docs/` and the G.4 spec. This unit implements A; the note line `launch:` names it.
- **B: a G.4-specific binding.** None is drafted, and none would be simpler.

**G4-ORDER. When the proposer server may hold TASL-7's GPU.** `sweep2/t1_tasl/T1_TASL_PLAN.md` planned the order
"G.1b on both hosts (TASL-7's G.1b nodes finish first) → the proposer server on TASL-7 → the G.4 pilot on TASL-2".
Under R1-G1B-TASL-DECISIONS, TASL-7's G.1b nodes now wait for the second G.1b note:
- the cross-host check job, reviewed and passed;
- autoresearch's spec entry and C1–C5, reviewed.

The pilot reads no G.1b output: its timeout basis is the census (R1-G1B-TIMEOUT), not the noise floor. The two jobs
on each card cannot overlap: the lease is an exclusive non-blocking `flock`, so a busy lease is a STOP, not a wait.
- **A: the plan's order.** The server starts only after TASL-7's G.1b jobs are sealed. P3 then cites the second G.1b
  note and the sealed TASL-7 attempts. G.4 waits for the whole second-note path, so the pre-pilot B.7 slack of about
  one day (plan §4) is likely spent before the pilot.
- **B (recommended): lease order only.** G.4 runs whenever both cards are free:
  - TASL-2: between its G.1b node jobs, or after them;
  - TASL-7: before or between its cross-check and G.1b jobs;
  - the server is stopped after the pilot (plan §5 step 5), which frees TASL-7 again.

  P3 cites the signed G.1b note and states that no G.1b job runs on either card during the pilot.
  - Benefit: it measures the per-call LLM time, the schedule's main unknown, a few days earlier. R1-TRACKG-G3-EARLY
    ("G.1b and G.4 start on these six now") supports starting G.4 without waiting.
  - Cost: a gap in the G.1b schedule of about the pilot's span, 5.5 h of TASL-2 and TASL-7 time (projection below).
  - Order of results: two of the three pilot nodes, `mlab_cifar10` and `mlgym_breakout_minatar`, are TASL-7 G.1b
    nodes, so their noise floors come after the pilot. The pilot does not use them: `pilot_g4.py` imports only
    noise_floor functions, and `g4_lib` reads no G.1b output.
  - Risk: a busy lease or a foreign process on TASL-7 STOPs `serve`. Since this unit's revision, `serve` writes only
    a refusal in that case and can be started again.

  Under A, the delay is the whole second-note path:
  - the cross-check jobs (about 2.1 GPU-h);
  - two reviews;
  - the three TASL-7 G.1b nodes (TASL-7's 14.2 GPU wall-hours).

  That path is at least a day, against the pre-pilot B.7 slack of about one day (plan §4).

**G4-NODE3. The third pilot node.** R1-TRACKG-G3-EARLY names `autoresearch_fixedtokens`, or
`mlgym_breakout_minatar` "if autoresearch is not ready".
- **A (recommended): `mlgym_breakout_minatar`** (the spec as it stands). Autoresearch is not ready on the G.4 harness:
  - its cond7a kit (`7330338`) is not an ancestor of `c025f89a`;
  - its U2 conditions C1–C5 are only partly applied (the G.1b cross-check unit's report, on
    `mac-g1b-xc-20261121`, not yet on main);
  - its spec entry is under review.

  Cost: the pilot measures no autoresearch-suite node. Autoresearch's per-call time and run cost enter the G.5 dates
  only from its census row.
- **B: wait for autoresearch.** This needs a G.4 spec at a new harness pin (the cond7a cherry-pick), a second harness
  checkout on TASL-2, and the reviewed U2 text. Not recommended for the pilot.

---

approved: false
label: ENGINEERING_ONLY
labels_read: none
run_id: g4-tasl-20261121-a
paper_commit: <FILL at the launch: the main commit that carries this unit's launch binding (verify_launch_tasl in g4_tasl.launch and serve); it must equal spec.paper.commit>
spec_sha256: <FILL at the launch: sha256 of sweep2/t1_tasl/g4_tasl_spec.json as committed on the launch main>
spec: sweep2/t1_tasl/g4_tasl_spec.json; on main 985dd45d with sha256 fd5a14b51463d5658dc1833b1e6805f5b4241078ec3fa813a9a14df833ba1b6b and paper.commit d47d1008 (the stale pre-unit commit); at the launch only paper.commit changes; no run has used run_id g4-tasl-20261121-a
harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702
harness: dowlingwong/autoresearch_harness at harness_commit (branch mac-trackg-t1-tasl-20261121), clean on TASL-2 (checked by every worker job; check_note requires harness_commit to equal the spec's); the same harness checkout as the G.1b TASL-2 nodes
launch: decision G4-LB (R1-G1B-TASL-DECISIONS LB A applied to G.4): TASL-7 (serve) and TASL-2 (run-node) each from a published checkout (an ancestor of the freshly fetched origin/main) at or after the commit that publishes this note and the spec, holding the signed spec, whose code equals paper_commit outside docs/ and the spec file (verify_launch_tasl, rows R1-T1-HOST-TASL, R1-TRACKG-G3-EARLY, R1-G1B-TIMEOUT, R1-T1-TASL-ENV; the imported modules checked against their reviewed sources); main may move on after the signature; a checkout separate from the G.1b launch checkout (G.1b launches from exactly 985dd45d)
gpu_model: NVIDIA GeForce RTX 4090 on both hosts (one GPU model for the whole T1 table, R1-T1-HOST-TASL)
worker: TASL-2; GPU GPU-4d623e76-7587-ee15-a633-46f60d220d94; driver 535.309.01; cpus 0-7; lease ~/r1_locks/gpu0.lock; envs torch312, jax312 (jax312 for mlgym_breakout_minatar, installed on TASL-2 from its freeze); runs under runs_root/g4-tasl-20261121-a/NODE/attempt-N/ through sweep2/t1_tasl/t1_tasl_node.sh g4 (the delegated scope, MemoryMax 8G, MemorySwapMax 0, the CPU affinity, a fresh log)
proposer: TASL-7; GPU GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1; driver 580.178.04; lease ~/r1_locks/gpu0.lock held for the server's whole life; nothing is written for the run before the lease is held and the checks pass (a refusal goes to run_dir/g4-tasl-20261121-a/_refusals/; each started server has its own run_dir/g4-tasl-20261121-a/server-N/ with server_record.json, llama-server.log and, on exit, server_end.json); the Track X exam llama-server used in place (/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server, sha256 b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b, version: 0.7.0-dev (build 1, commit 620d222), build-directory manifest sha256 a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170, llama.cpp libraries resolved inside it, started without LD_LIBRARY_PATH/LD_PRELOAD); model gemma4_31b GGUF sha256 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75; settings -c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs {"enable_thinking":false} --cache-type-k q8_0 --cache-type-v q8_0 --no-webui; URL http://tasl-7.tail119748.ts.net:8095 (Tailscale)
pilot: nodes mlab_cifar10, mlgym_fmnist, mlgym_breakout_minatar (decision G4-NODE3); 3 instances each (train/split/manager seeds 4001, 4002, 4003) x W = 20 manager calls; manager_proposal/v2-diff; max_tokens 4096; temperature 0.2; cache_prompt false on every call (else STOP); memory mode history; 180 proposals in all
nodes: mlab_cifar10 (torch312, node_spec_sha256 90c8364f3c35b276ad97c73ea66b9e31d9f8e128aa9be7db5a013b5eb7b4093f, committed_pin_sha256 1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2, data_manifest_sha256 43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3); mlgym_fmnist (torch312, node_spec_sha256 65f229affedca7abcc0a78792053cf5fa3c8a1237bf683298faa03e674a152e9, committed_pin_sha256 eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3, data_manifest_sha256 8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c); mlgym_breakout_minatar (jax312, node_spec_sha256 db57b202301e323d4471cf23ef6ad3b822d5f5e0d471f1896ffda3041af2a10a, committed_pin_sha256 cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4, no data setup)
envs: torch312 (freeze env/torch312.freeze.txt, sha256 d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42) and jax312 (freeze env/jax312.freeze.txt, sha256 80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1), Python 3.12.16; each job compares uv pip freeze to the freeze at its start (STOP on a difference)
timing: the pilot's per-run timeout is 3 x the G.1b timeout basis census_slowest_x3 (R1-G1B-TIMEOUT); a pilot run median on the 4090 above the basis is a STOP (stop_class timing); an edited proposal's timeout is its failure; a baseline timeout STOPs the campaign
projection: 11.077 GPU-h (worker GPU on TASL-2 plus proposer GPU on TASL-7 over each node's span: mlab_cifar10 2.864, mlgym_fmnist 3.636, mlgym_breakout_minatar 4.577; about 5.5 h of span), from g4_tasl.py validate at 985dd45d
cap: 20 GPU-h for the pilot (spec caps.max_total_gpu_hours); a projection or consumption beyond it is an author STOP
order: decision G4-ORDER; the GPU leases enforce that no G.1b or cross-check job and the pilot overlap on a card (a busy lease is a STOP)
seal: on TASL-2 g4_tasl.py seal NODE/attempt-N with --server-end and --server-log after the server is stopped; dates (R1-BX-D14 recompute) from one sealed attempt per node with one concurrent worker slot
keys: real runs need --enable and G4_TASL_ENABLE_REAL=1, on TASL-7 for serve and on TASL-2 for run-node, after this note is on main
P1: PASS — R1-T1-HOST-TASL: worker TASL-2, proposer TASL-7 (no worker on TASL-7, so only TASL-2's host check is required); TASL-2 harness-isolation host check docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md sha256 681011b2114f6ff7db679d3265535d1cc2e8a9bdbc231371230f4de42d7b6b6d (review docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md); its item 7 (CUDA IPC) is untested on TASL-2 (review condition C1). In G.4 the model writes train.py freely, and an edit could import the frozen ar_isolated.py and call cuda_share or cuda_open in the worker; no frozen parent of the three pilot nodes ever exports a tensor with cuda_share (the sharing side; cuda_open is the worker side), so a worker has no parent handle to open. The residual risk (an edit using CUDA IPC within its own worker process, with no parent handle) is accepted by the author with this line
P2: PASS — R1-TRACKG-G3-EARLY: pilot nodes mlab_cifar10, mlgym_fmnist and mlgym_breakout_minatar (autoresearch_fixedtokens not ready on the G.4 harness; decision G4-NODE3)
P3: PASS — <FILL per G4-ORDER. B: the signed G.1b note docs/r1/authorizations/g1b_t1_tasl_20261121.md; the pilot reads no G.1b output (timeout basis = census, R1-G1B-TIMEOUT); no G.1b or cross-check job runs on TASL-2 or TASL-7 while the server and the pilot run (the leases). A: the second G.1b note docs/r1/authorizations/g1b_t1_tasl_<date>.md, and TASL-7's G.1b attempts sealed (<paths>)>
P4: PASS — independent reviews: the code unit docs/r1/reviews/T1_TASL_REVIEW_20261121.md (accepted at 021dbc26 with harness c025f89a); the launch binding of g4_tasl.launch and serve and this note, docs/r1/reviews/<the G.4 launch-binding review>.md
P5: PASS — R1-T1-TASL-ENV: proposer binary, build-directory manifest and GGUF as in the spec and above; node environments from the census freezes; harness at harness_commit

STOPs (each returns to the author; outputs are kept; nothing is deleted or silently retried):
- a host name, GPU UUID or GPU model other than above (checked by the code); a driver other than above (recorded by
  the code, compared by the operator before each job); a root uid; Yama ptrace_scope below 1 on TASL-2; a scope
  without MemoryMax 8G and MemorySwapMax 0; a CPU affinity other than 0-7;
- a busy GPU lease, or a compute process of another owner on either leased GPU;
- the llama-server binary, build-directory manifest, ldd resolution, build line or GGUF other than above; /health or
  /props (context 32,768, one slot, the build, the GGUF name) differing from the spec, or changing between before and
  after the pilot;
- a call without cache_prompt false;
- the harness not at c025f89a or not clean; an environment freeze, node data manifest or kit pin other than above;
- a pilot run median above the timeout basis (stop_class timing), or a baseline timeout;
- the projection passing 20 GPU-h (checked by the code), or the GPU-hours consumed passing it (summed by the operator
  from the job and server records; no meter in the code);
- any label, evaluation or sweep-2 file opened (none is needed).
