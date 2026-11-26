# B1 `_d` Preflight Transport — Narrow Fix Re-Review (2026-11-13)

Scope: confirmation only. Prior blocking finding: the transport still bound the `_c` body
(`REMOTE_SCRIPT=/tmp/paper-b-final-host-preflight-c-20261112-4b31/remote.sh` and
`EXPECTED_SCRIPT_SHA=e53f6d72…`). Reviewer is independent; no files outside the review
directory were modified, and no preflight was executed.

## Unit under review

| Item | Path | SHA-256 |
|---|---|---|
| Transport | `/tmp/paper-b-final-host-preflight-d-20261113-7912/transport.sh` | `e1c7234a2f7f1383b93ed12b3b27df913b106b7b4d960a867cccbcb063388960` |
| Remote body | `/tmp/paper-b-final-host-preflight-d-20261113-7912/remote.sh` | `03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e` |
| Baseline `_c` transport | `/tmp/paper-b-final-host-preflight-c-20261112-4b31/transport.sh` | `84207fa422e8e0318b44a5430ca018424890e0e0408a0bb77dcca06f5e1d041a` |

Recomputed transport hash equals the requested `e1c7234a2f7f1383b93ed12b3b27df913b106b7b4d960a867cccbcb063388960`.
Recomputed remote hash equals the requested `03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e`.

## 1. Binding lines correct

```
3: REMOTE_SCRIPT=/tmp/paper-b-final-host-preflight-d-20261113-7912/remote.sh
4: EXPECTED_SCRIPT_SHA=03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e
```

Line 3 is the `_d` path; line 4 is the `_d` remote SHA. Local simulation of the guard on
lines 5 (`shasum -a 256 "$REMOTE_SCRIPT"` vs `EXPECTED_SCRIPT_SHA`) passes for the `_d`
remote and would exit 1 for any other body. The blocking finding is resolved.

## 2. Diff vs `_c` transport — exactly three lines

`diff -u` of `84207fa4…` → `e1c7234a…` reports exactly two hunks / three changed lines and
no added or deleted lines:

- line 3: `…-c-20261112-4b31/remote.sh` → `…-d-20261113-7912/remote.sh`
- line 4: `e53f6d72a2bcad4440efba25b34e4d291a41ff5c5626e87a63cde86901ad0c71` → `03313660c1bb951a278e5678a9b771ec6b553dfcbfde45fd2a0534281879a72e`
- line 6: capture prefix `…-capture-c-20261112` → `…-capture-d-20261113` (local `mktemp -d` directory only)

All other lines (1–2, 5, 7–12: `set -u`, `umask 077`, sha guard, `set -C`, the `ssh … 'bash -s' < "$REMOTE_SCRIPT"` invocation, `rc` capture, hash listing, final printf) are byte-identical to `_c`. Nothing else changed.

## 3. Syntax, `_c` residues, execution target, evidence state

- `bash -n transport.sh` → passes (12 lines, ASCII only).
- No `_c` reference remains: grep for `preflight-c-`, `e53f6d72`, `20261112` over the transport returns no match.
- Execution target: line 8 pipes the sha-gated `$REMOTE_SCRIPT` (the `_d` body) into `bash -s` on `tasl7`; `remote.sh` carries the `7912b7ff…` HEAD marker (single occurrence, not re-reviewed here). So a run would execute the `_d` body, not `_c`.
- TASL-7 read-only checks (no preflight run): `_d` CAP `/home/dowling/r1_b1_engineering/b1_final_gate_preflight_7912_20261113_a`, OUT `/home/dowling/exam-x/work/b1_host_preflight_7912_20261113_a`, and CACHE `/home/dowling/r1_b1_engineering/b1_final_gate_pycache_7912_20261113_a` are all **ABSENT** (clean slate for `_d`).
- `_c` evidence untouched: CAP `…_preflight_4b31_20261112_a` and OUT `…/b1_host_preflight_4b31_20261112_a` are present on TASL-7 with mtime `Nov 12 12:28`, earlier than this session; no file under them is newer than 2026-11-12 21:30. (`_c` CACHE `…pycache_4b31_20261112_a` is absent — pre-existing remote state, unrelated to this diff.)

## 4. No other change, no secrets

No files outside the review directory were written; `_c` and `_d` artifacts were only read. Transport has no credential material (no password/token/key/private-key/cloud-key patterns; local `ssh` relies on `BatchMode`). Local host reachability to TASL-7 confirmed, and the only `ssh` use here was read-only `ls`/`find`.

## Residual notes (non-blocking)

- The capture prefix is `paper-b-final-host-preflight-capture-d-20261113`, i.e. it omits the `-7912` label used by the unit dir; this is a local `mktemp -d` name only and does not affect binding.
- The transport intentionally has `set -u` and `set -C` but no `set -e`; exit status is captured explicitly on line 9 and recorded on line 10, as in `_c`.
- Verdict is limited to this transport fix; the `_d` remote body's own content (HEAD `7912b7ff…`) was accepted previously and was not re-reviewed.

VERDICT: accepted
