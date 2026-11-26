# B1 final-head gate + TASL-7 host preflight (`_d`): result review

- Date: 2026-11-13
- Reviewer: independent (did not author, stage or run the unit). TASL-7 checks were read-only; only `/tmp` scratch and this review file were written locally.
- Run HEAD: `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` (`_d` restart).
- Reviewed unit: transport `/tmp/paper-b-final-host-preflight-d-20261113-7912/transport.sh` SHA-256 `e1c7234a2f7f1383b93ed12b3b27df913b106b7b4d960a867cccbcb063388960`; remote body `/tmp/paper-b-final-host-preflight-d-20261113-7912/remote.sh` SHA-256 `03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e` (both re-hashed locally; equal to the reviewed values).
- Local capture: `/private/tmp/paper-b-final-host-preflight-capture-d-20261113.LUCIeK0Z/` (the only `…capture-d-20261113.*` directory).
- Remote CAP: `/home/dowling/r1_b1_engineering/b1_final_gate_preflight_7912_20261113_a`; OUT: `/home/dowling/exam-x/work/b1_host_preflight_7912_20261113_a`.
- PASS criteria source: `docs/r1/proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` (in the staged checkout at this HEAD).

## 1. Exits, hashes and capture consistency — PASS

| Artifact | Size | SHA-256 | Content |
|---|---|---|---|
| local `ssh.exit` | 2 B | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | `0\n` |
| local `ssh.log` | 765 B | `203281d4505867de64c88bf6f4f90744e89ae7bd72126002bbb40719e10a1171` | 6 lines, no stderr noise |
| CAP `gate.log` | 611 B | `79eac86c81d0fd167f1108c8d23bd3ad22ea45fae001261152685a9f648c1acb` | 4 lines |
| CAP `gate.exit` | 2 B | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | `0\n` |
| CAP `preflight.log` | 1509 B | `6b1a8b6d60beca4704afb32915a0d120833a434fd4e2a51c96f6bf535097ddd9` | 4 lines |
| CAP `preflight.exit` | 2 B | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | `0\n` |

`ssh.log` contains exactly `PRIVATE_CAPTURE=…_7912_20261113_a`, `PREFLIGHT_OUTPUT=…/b1_host_preflight_7912_20261113_a` and the four `sha256sum` lines for the CAP files. Every digest listed there was re-derived independently over SSH and is identical (gate.log, gate.exit, preflight.log, preflight.exit, in that order). Both CAP exit records are `0\n`; local SSH exit is `0`. Single invocation, no retry: one capture directory and one CAP/OUT pair exist.

## 2. `gate.log` — PASS

Exactly four lines: three `node_source` lines (`digits_mlp` `train.py 4c0692ba…`, `openml_credit_approval` `config.yaml 60e31d30…`, `openml_ionosphere` `config.yaml 60e31d30…`) and exactly one:

```
GATE_PASS 7912b7fffb4c1adeb39688bdb3852a919bdc71c8 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad python /home/dowling/exam-x/work/venv/bin/python prefix /home/dowling/exam-x/work/venv worker_python /home/dowling/exam-x/work/venv/bin/python3 threads 1 1 1
```

HEAD and rule hash are exact; python/prefix/worker_python are the venv; threads are `1 1 1`. `grep -c GATE_PASS` = 1; no `STOP`, `error`, `traceback` or `fail` line.

## 3. `preflight.log` — PASS

Four lines: environment JSON (venv python, numpy 2.4.4, sklearn 1.8.0, worker python3, threads `1 1 1`), 16-model list, state JSON, and `PREFLIGHT_PASS: owned server exited and own lease descriptor closed`.

- 16 validated models, including anchor `qwen25_coder_7b`; count and list match the criterion.
- `gpu_before`: device 0, free 23812 MiB, used 236 MiB, 0 %; `gpu_loaded`: free 18075 MiB, used 5973 MiB, 77 %.
- `lock.contender_refused: true`, `dev: 66306`, `ino: 56251186` — exactly `stat` of `/home/dowling/r1_locks/gpu0.lock`.
- `model: qwen25_coder_7b`; `offload.full: true`, `offloaded_layers: 29`, `total_layers: 29`, `cpu_fallback_lines: []`, `reasons: []`, `line: "full"`, `route: "log_line"`.
- Pinned GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, `footprint_mib: 5734`, `used_mib: 5732`, single `rows_of_pid` row for pid 4165964; model buffers CUDA0 4168.09 MiB, KV 952.0 MiB. The same 5734 MiB anchor footprint appears in the accepted `_b` (6835) and `_c` (4b31) preflight logs.
- `head: 7912b7ff…` equals the run HEAD exactly; no `STOP`, `error`, `traceback` or `fail`. `grep -c PREFLIGHT_PASS` = 1.

## 4. Post-run read-only state — PASS

- No `llama-server`, `exam_runner` or `b1_host_preflight` process; `pgrep -a llama-server` empty; pid 4165964 gone; `nvidia-smi --query-compute-apps` returns no rows; port 35479 has no listener.
- Lease free: `flock -n /home/dowling/r1_locks/gpu0.lock` acquired, no `/proc/locks` entry on device 66306; the lock file itself is unchanged (0 B, mode 664, mtime 2026-10-26 15:50:48).
- OUT contains only `llama_server_35479.json`, `llama_server_35479.log` and `_to_delete/`; the record has `stopped_utc` 2026-11-13T13:34:34Z, `returncode: 0`, `health: ok`; the two retained `_to_delete/server_record.*.json` files (2379 B and 2300 B) are the pre-/post-health versions of the same pid/port/start_ticks and were not deleted.
- CAP mode 700, files 600; OUT mode 700, files 600, `_to_delete` 700; all owned `dowling:dowling`.
- `CACHE=/home/dowling/r1_b1_engineering/b1_final_gate_pycache_7912_20261113_a` absent (as intended with `-B`/`PYTHONDONTWRITEBYTECODE=1`).
- Staged checkout `…/b1_paper_final_7912b7ff…/paper` at exactly `7912b7ff…`, 0 status lines; harness at `a3fedbbd…`, 0 status lines.
- `68357d3d…`, `fffa45a1…` and `4b312844…` checkouts each at their own pin with 0 status lines.
- `_c` scene (`b1_4b31_20261112_c`, handover dir), `_b`/6835 scene and their CAP/OUT are unchanged (all mtimes before the run); the Track S scene `/home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113` still has the empty `STOP` (mtime 05:00:52) and `"status": "paused"`; only the idle `trks_watch` tmux session exists.
- Track X marker `/home/dowling/r1_locks/trackx_evidence.active` absent; the earlier retirement STOP receipt `marker-retirement_stop.json` is intact (`retired: trackx_evidence.active.040ffbe1…`, `sha256 f8c8624f…`, `.rc` 0, `.err` 0 B).
- Files modified in the run window (05:31–05:34 remote) are only the four CAP files, the CAP directory, and the OUT files/`_to_delete`; a `find -newermt "2026-11-13 05:30"` over `r1_b1_engineering`, `exam-x/work`, `r1_locks`, `r1_tracks` and `~/.cache` shows nothing else.

## 5. Usability — PASS

This is a genuine gate + native-preflight PASS for exactly `7912b7fffb4c1adeb39688bdb3852a919bdc71c8`, on the reviewed body and transport, against a fresh and now-clean host state. It is usable as a **precondition** (not launch authority) for the `_d` handover and eventual authorized B1 launch.

Residual limits (unchanged, non-blocking): the result is point-in-time, so a fresh census/no-preemption and idle-GPU check remain prerequisites for launch; the transport has no SSH keepalive/command timeout beyond `ConnectTimeout=12`; the Track X marker is absent by design and must be created by the `_d` handover; the `_c` CAP/OUT evidence must not be deleted or renamed; an observed 29/29 offload and 5734 MiB footprint are not scientific readiness.

## Reviewer-side notes (not findings against the run)

- My `flock` probe on the wrong path created a zero-byte `/home/dowling/exam-x/work/gpu0.lock` at 05:37; it did not exist before, and I removed it immediately (it is absent now). The real lease is `/home/dowling/r1_locks/gpu0.lock`. This changed only the `exam-x/work` directory mtime (05:37).
- My read-only `git status` queries transiently created/removed a lock file inside each `.git`, leaving only `.git` directory mtimes at 05:38 on the four checkouts and the harness. `.git/index` mtimes (2026-11-07/11/12/13, pre-run), objects and HEADs are unchanged, no lock residue remains, and all working trees are clean at their pins.
- These effects are confined to directory mtimes on TASL-7 after the run window (05:31–05:34) and do not touch CAP, OUT, staged inputs or evidence.

VERDICT: accepted
