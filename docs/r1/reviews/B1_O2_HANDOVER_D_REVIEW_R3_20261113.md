# Independent review, round 3 — B1 `_d` O2 handover blocker fix (run `7912_20261113_d`, 13 Nov 2026)

**Reviewer.** Fresh, independent; I did not write the unit and did not take part in rounds 1–2. Narrow confirmation of the round-2 blocker only. Read-only on TASL-7 (`ls`, `stat`, `cat`, `find -printf`, `sha256sum`, `git rev-parse/status`, `tmux`, `ps`, `nvidia-smi`, `flock -n` probe); no writes, signals, marker/STOP touch, server start, or deletion. I wrote only under `/Users/wongdowling/Documents/agent_sys_paper/` and `/private/tmp`; nothing under `/Users/wongdowling/Documents/agent_paper_B`. `handover_pre` was not executed. Review window: Mac `2026-11-13T14:42–14:48+01:00`; `tasl7` UTC `13:42–13:47Z`.

**Unit reviewed (sha256 recomputed; all match the operator list).** Under `/tmp/b1_handover_d_7912_20261113_d/`:

| file | sha256 |
|---|---|
| `handover_pre.sh` | `7ec04c72722805418f08a16305d41e9866e43514730556fb361f6b70ca815994` |
| `launch_precheck.sh` | `3f828051433e4b799cc8dc74a098184bd86c765836748d3433fef86221e0e108` |
| `PLAN.md` | `72f3ec714770d277b6a97e61e9ca9958066502a16f3643af3447919a0c56c48e` |
| `handover_run.sh` | `6d1da9443ccc42a3c6a90d06d33278d4a24541a26c1b1bc0865dab00174dc89b` |
| `status_publish.sh` | `582adb3ae585e7d2910ff906a317014012a99a64569e7e978af59411af5e8949` |
| `launch.sh` | `1ade789ddc3e727c3974a21fb657756702d67f3c95dd9d174e20d30bfa6c24ce` |
| `launch_start.sh` | `10f9be100aa57f27b7f3a4b19a00f5acb0f8979b75c48dfba724121caa3236c9` |
| `start.sh` | `4a545a756820df3d73c03aaf3557df18e14cfdba6bccefb96274ff087bb9eb5f` |
| `receipt.sh` | `2e6ad2abce0027699c61f0461a37122742a521b08370d2993921c16c0130c94a` |

## 1. Fix verification
- `handover_pre.sh:79` and `:146` now both run `find "$HOME/r1_tracks/out" -name STOP -print0 | sort -z | xargs -0 sha256sum`; no `cd` and no `find .` in either generator. On the live host the generated keys are exactly the absolute inventory paths (`/home/dowling/r1_tracks/out/{smoke,digits_mlp/s05_t7_20261113}/STOP`), i.e. identical key space to `inv_stop_before/after.txt`.
- `handover_pre.sh:160` normalises a leading `./` in `load_sha` to `/home/dowling/r1_tracks/out/` as defence (`HOME` is asserted at `:11`). With deliberately relative `./smoke/STOP` key files the comparison also passes.

## 2. Comparison reproduction (live listings and live sha values, copied into `/private/tmp/r3_live`)
Extracted the exact `PYJ` block (`handover_pre.sh:148–175`) and ran it against the live two-STOP inventory (both 0 B, sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, inos `57048195`/`57048847`) and live manifest inventory:

| case | result |
|---|---|
| identical before/after | rc 0, `INVENTORY_DIRECTED_ONLY` |
| mtime-only change on both STOPs (simulated watcher touch) | rc 0, `INVENTORY_DIRECTED_ONLY` |
| relative `./` sha keys | rc 0, `INVENTORY_DIRECTED_ONLY` |
| STOP content sha changed | rc 1, `STOP content changed: …/smoke/STOP` |
| new STOP path added | rc 1, `STOP path set changed` |
| STOP path deleted | rc 1, `STOP path set changed` |
| STOP identity (ino) changed | rc 1, `STOP identity changed` |
| manifest mtime changed | rc 1, `manifest changed` |

The round-2 `KeyError` no longer reproduces; the directed-only rule is enforced, not merely documented.

## 3. PLAN
`PLAN.md:38–39` now reads "its data/content is untouched, but the watcher may mtime-touch pre-existing STOP files beside its manifests (allowed by the inventory rule above)", matching `:40–43` and the code. No contradiction remains.

## 4. `launch_precheck.sh`
Validates the predecessor record (`:32–43`: run id, head, marker/creation/retirement/note/archive SHAs, rc), then re-hashes the on-disk `marker-retirement.note` to `4b86ba34efba72537ea946ddacd250a139c479bf3e734ebfe65fcbff6d54dcf8` at `:44–47` (live note sha confirmed identical). `bash -n` passes for all nine scripts; no `rm`/`mv`/`truncate`/`shred`/`find -delete`/`git clean|reset`/`--force` anywhere.

## 5. Diff scope and live state
- Versus round 2 (`c8bb9c37…` PLAN, `a038ee57…` handover_pre, `a45059e1…` launch_precheck), the other six files are byte-identical and exactly three hashes changed. The round-2 bytes are not retained anywhere under `/private/tmp`, `agent_sys_paper` or `agent_paper_B`, so no byte diff was possible; reconstruction from the round-2 hash table plus its quoted line anchors shows only the three intended regions (absolute generators + defensive `load_sha`; PLAN `:38–39` wording; note re-hash), with all other cited lines unchanged. No unrelated change observed.
- Live state unchanged: `~/r1_locks/trackx_evidence.active` absent, `trackp`/drill markers absent, lease free, tmux exactly `trks_watch`, no `_d` session, `RUN_DIR`/`BATCH` absent, no compute apps or owned processes, staged checkout `7912b7ff…` clean, `_c` handover files untouched (12 Nov mtimes, no `_d` name), Track S paused with only the two manifests/two STOPs.

## Residual notes (non-blocking)
- `PLAN.md:42` says type is required, but `b[:6]` compares path/dev/ino/size/user/group only; any type change also changes inode and the pre-inventory grep enforces regular files, so there is no practical gap — wording only.
- `launch_precheck.sh:45` hardcodes `/home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d/marker-retirement.note` instead of passing `$RUN_DIR`; equal today.
- `pgrep` self-matches the review's own `bash -c` line; filtering it out shows `NO-OWNED-PROCS`.

VERDICT: accepted
