# B1 final host preflight (`_d`): independent review of the filled invocation and local transport

- Date: 2026-11-13
- Reviewer: independent (did not author the unit). Review was read-only on TASL-7; only this file and `/tmp` scratch were written.
- Run HEAD: `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` (`_d` restart; reviewed base `999759b7…`; PLAN `R1-EXAM-B1-MODEL-OUTPUT-INVALID`; `paper_commit` `02a914944cc546fc33a6428b1eb92a8993542bef`).
- Verdict: **changes required** (one blocking transport binding defect; the remote body itself is accepted-substance).

## 1. Inputs reviewed

| Item | Path / value | SHA-256 |
|---|---|---|
| Filled remote body | `/tmp/paper-b-final-host-preflight-d-20261113-7912/remote.sh` (3139 B) | `03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e` (recomputed, twice) |
| Local transport as submitted | `/tmp/paper-b-final-host-preflight-d-20261113-7912/transport.sh` (635 B) | `67afcc9732fa5be878418210f0dc4cbda39de27a51b963dc35f5afef7035a033` (recomputed) |
| Accepted template at run HEAD | `docs/r1/proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` in the staged checkout, byte-identical to the local worktree copy | `edc99db6c56d01be7504b1328d05d061683e1018ff127b3285d85d03722b3e11` |
| Accepted `_c` remote body (diff reference) | `/tmp/paper-b-final-host-preflight-c-20261112-4b31/remote.sh` | `e53f6d72a2bcad4440efba25b34e4d291a41ff5c5626e87a63cde86901ad0c71` |

The template digest is unchanged between `_c` and `_d` HEADs, so the `_c` body is a valid diff reference. The staged checkout payload `paper.tar` hashes to `c719fad563902cec9c7f0afc57cc1db465227c5dc12104044ef13e5328dc7b2a` (transfer receipt value) and `git fsck --connectivity-only` returns 0.

## 2. Remote body — fidelity, bindings and site state (all PASS)

**Fidelity.** `diff -u` of the filled body against the accepted `_c` body shows exactly four differing lines: the `HEAD` literal (`7912b7ff…`) and the `CAP`/`OUT`/`CACHE` literals (`…_7912_20261113_a`). All other 53 lines are byte-identical: `set -eu`, `umask 077`, every `unset`/`export`, the `HOME`/absence/non-symlink/executable guards, `mkdir -m 700 "$CAP"`, `set -C`, `AR_HARNESS_ROOT` before the `r1.exam.runtime` import, the quoted gate heredoc, `gate.exit`, the `b1_host_preflight` call, `preflight.exit`, the `PRIVATE_CAPTURE`/`PREFLIGHT_OUTPUT` print, the four-file `sha256sum`, and `exit "$probe_rc"`. `bash -n` passes; the heredoc compiles; no placeholders, no CR, no secrets.

**Bindings (TASL-7).** HEAD is 40 lowercase hex. `PAPER=/home/dowling/r1_b1_engineering/b1_paper_final_7912b7ff…/paper` exists, is not a symlink, is at exactly `7912b7ff…`, `git status --porcelain --untracked-files=all` = 0, no remotes. `HARNESS=…/b1_harness_offline_stage_20261107_a/harness` is at pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, clean. `PY` is the venv link (CPython 3.13.4); `sys.executable`/`sys.prefix` = the venv, sibling `python3` identical. `CAP`, `OUT`, `CACHE` are absent and non-symlinks at review time; `OUT`'s parent is exactly `work_dir=/home/dowling/exam-x/work`, and `b1_host_preflight.check_inputs`'s direct-child rule holds. The `_d` batch child `/home/dowling/exam-x/work/b1_7912_20261113_d` is absent and is not referenced or created. `paper_commit 02a91494…` is an ancestor of HEAD, and `git diff --name-only 02a91494..7912b7ff -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty (0 lines); the working-tree check is also empty. `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`; `GIT_*` hygiene and `GIT_OPTIONAL_LOCKS=0` are exported; `set -C` precedes the first capture write.

**Gate dry run (read-only, stdout only, no remote writes).** Running the exact heredoc at `7912b7ff…` with the script's environment returns rc 0 and prints `node_source` lines for the three nodes and
`GATE_PASS 7912b7fffb4c1adeb39688bdb3852a919bdc71c8 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad python /home/dowling/exam-x/work/venv/bin/python prefix /home/dowling/exam-x/work/venv worker_python /home/dowling/exam-x/work/venv/bin/python3 threads 1 1 1`.
The checkout is still clean and `CACHE` was not created.

**Staged inputs.** Config `af57a42334198b2a0885c086d831ecee8c00ace274eea5705914793ac6288669` (tracked, clean; `paper_commit 02a91494…`, `work_dir`/`models_dir`/`host`/`gpu_uuid`/`harness_commit` as bound). `r1/scripts/b1_host_preflight.py` = `7cc2c560bfd7be6a05eac958e88041371124d8ecc6fe1828e6187abd07c83f00` (equals `git show HEAD:…`). Pins recomputed equal: rule `53018aa7…`, registry `2c6ef6b3…`, prompts `70872a77…`, server binary `b70f4882…`, Stage A t7h8 `00ab143d…`, t7j10 amendment `71525124…`, acceptance record `0cda82fa…`, anchor reference `84200770…`. The three template-repair files exist and match both registry and config digests.

**Models.** 18 eligible rows; the preflight's 16-model validated set is present under `/home/dowling/exam-x/models`, every file size equals the registry pin, every full SHA-256 equals the registry `quant_source.sha256`, every `.verified` pin matches, and the anchor is a single `qwen25_coder_7b` eligible with `509287f7…`; `bad = []`.

**Site.** Free space `565,979,258,880` B (≈527 GiB, above the 100 GB floor). GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` present, 23,812 MiB free, 236 MiB used, 0 %, `--query-compute-apps` empty. `gpu0.lock` is a regular one-link owner file; a non-blocking `flock` probe acquired and released it; no `gpu0` entry in `/proc/locks`. Track X marker absent; the preflight path contains no reference to it (only `b1_o2_marker.py` does). Older checkouts `68357d3d…`, `fffa45a1…`, `4b312844…` are each at their own pin and clean. Track S `s05_t7_20261113` scene unchanged (`STOP` present, manifest `"status": "paused"`, exit rc 0); only the idle `trks_watch` tmux session; no `llama-server`/`exam_runner` process.

## 3. Finding F1 — BLOCKING: the transport still runs the `_c` body

- **Severity:** blocking. Acceptance requires running exactly this filled remote script through exactly this transport; the transport does not bind it.
- **Location:** `/tmp/paper-b-final-host-preflight-d-20261113-7912/transport.sh` lines 3–4.
- **Issue:** `REMOTE_SCRIPT=/tmp/paper-b-final-host-preflight-c-20261112-4b31/remote.sh` and `EXPECTED_SCRIPT_SHA=e53f6d72a2bcad4440efba25b34e4d291a41ff5c5626e87a63cde86901ad0c71` still name the accepted `_c` body (HEAD `4b312844…`). The local hash guard therefore validates the `_c` file successfully (`e53f6d72…` matches), and `ssh … 'bash -s' < "$REMOTE_SCRIPT"` pipes the `_c` body — not the reviewed `_d` body (`03313660…`, HEAD `7912b7ff…`). On the current site the `_c` body's own absence guard sees its retained `CAP=/home/dowling/r1_b1_engineering/b1_final_gate_preflight_4b31_20261112_a` (and `OUT=…/b1_host_preflight_4b31_20261112_a`) already present and exits 1 before `mkdir`, so no `_d` gate/preflight log, no `_d` exit record and no preflight output are produced; the wrapper fails closed at the wrong target. If an operator "unblocked" it by deleting or renaming the `_c` CAP, it would instead run the old `_c` HEAD and record wrong-HEAD evidence, which is worse. Either way one run yields no evidence for this HEAD and consumes the single-run budget.
- **Minimal fix:** in `transport.sh`, set line 3 to `/tmp/paper-b-final-host-preflight-d-20261113-7912/remote.sh` and line 4 to `03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e`; keep the capture prefix. That exact two-line edit yields a transport of SHA-256 `e1c7234a2f7f1383b93ed12b3b27df913b106b7b4d960a867cccbcb063388960` (computed on a `/tmp` copy, `bash -n` OK). The remote body needs no change and remains `03313660…`. The corrected transport must be re-reviewed at its new hash (or at minimum re-hashed and diffed to prove only these two lines moved) before the one-shot run.

The transport otherwise matches the accepted template exactly: `set -u`, `umask 077`, hash guard, `mktemp -d` exclusive capture, `set -C`, one `ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s'`, single `ssh.exit` write, final hashes, no retry. The capture prefix `…capture-d-20261113` differs from the template only by run tag.

## 4. Marker and safety notes

- The Track X marker is absent and **not required** by this preflight or gate: neither `b1_host_preflight.py` nor `r1/exam/runtime.py`/`b1_lease.py` reads `trackx_evidence.active`; the `_d` gate/preflight neither creates nor retires a marker. Retirement receipts are intact (`marker-retirement_stop.json` `2bfc6542…`, `.rc` 0, `.err` empty; creation receipt `e0da112f…`; archived marker `040ffbe1…` / `f8c8624f…`). The `_d` handover must create the new marker after the gate/preflight, as planned; nothing in the reviewed unit depends on it.
- Writes are confined to `CAP` (gate/preflight logs and `.exit` records), `OUT` (created by the preflight; server record/log and `_to_delete` versions), and the bytecode prefix `CACHE` (never created because `-B`/`PYTHONDONTWRITEBYTECODE=1`); source checkouts, models, Stage A tables, the `_c`/`_b`/6835 scenes and the paused Track S scene are read-only. The unit sends no signals itself; the native preflight signals only its own `start_new_session` child after group-identity checks. A failed/interrupted run preserves `CAP`/`OUT` and is STOP, never retry.

## 5. Residual notes (not findings)

1. The transport has no command timeout / `ServerAliveInterval`; a hung remote command leaves `ssh` waiting. Operator STOP and scene preservation remain the control (template-inherited).
2. Local hash-then-read of `remote.sh` leaves a small TOCTOU window on owner-only `/tmp` (template-inherited).
3. On gate failure the remote body exits before printing `PRIVATE_CAPTURE`/hashes; `CAP` is a fixed reviewed literal and `gate.log`/`gate.exit` are still written, so evidence is retained.
4. The `_c` CAP/OUT directories now hold the accepted `_c` evidence and must not be deleted, moved or "cleaned" to make the stale transport pass.

## 6. Conclusion

The filled remote body is substantively the accepted template with only the permitted HEAD and run-specific path substitutions, and all bindings, site preconditions, fresh-path exclusions, model/gate pins and safety properties hold on the current TASL-7 state; a read-only gate dry run at this HEAD passes. The submitted local transport, however, still validates and pipes the `_c` body, so the reviewed `_d` invocation would not be executed and no `_d` gate/preflight evidence would be produced. Running exactly the submitted unit once is therefore not acceptable; the two-line transport fix above (resulting SHA-256 `e1c7234a2f7f1383b93ed12b3b27df913b106b7b4d960a867cccbcb063388960`) must be made and re-reviewed.

VERDICT: changes required
