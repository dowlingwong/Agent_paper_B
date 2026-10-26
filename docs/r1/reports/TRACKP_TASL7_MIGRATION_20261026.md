# Track P — migration to TASL-7 (26 Oct 2026)

AI-assisted (Claude Code, Track P agent running on TASL-7, started by the author). ENGINEERING_ONLY / DRYRUN. Authority: PLAN §10 R1-TASL7-TRACKP and R1-ADA-OVERFLOW; `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, host-change header. Branch `trackp-20261026`.

## What was done

| Step | Result | Record |
|---|---|---|
| Branch | Checked out `trackp-20261026` (`471f93f`) and merged `origin/main` (`fc3e0da`) → `af158f1`. The STATUS conflict was resolved by keeping both entries with no text changed, newest first. There were no PLAN conflicts. The portal session later pushed its last commits (`52b527b`–`84fe7c1`: rule-v2 review fixes, the two-stage short DRYRUN and its hand-over); these were merged without conflicts. | merge commits |
| (1) Phase 0 host facts | Collected with the portal's inventory script. TASL-7: RTX 4090, cc 8.9, driver 580 / CUDA 13.0, 965 G free. Work dir `/home/dowling/r1_trackp` (same paths as the portal). GitHub push works; Hub metadata is identical to the portal's. | `PORTAL_TRACKP_HOST_FACTS_TASL7_20261026.md` |
| (2) Phase 2, same pins | The venv was rebuilt from the recorded freeze, and its freeze is **identical** (torch 2.6.0+cu124). The GPU smoke test passes and agrees with the portal to about 1e-6. All 8 repos are at the same revisions, and every file was re-hashed against the committed `registry.yaml`. The config is unchanged and `--check-config` is clean. | `TRACKP_PHASE2_ENV_PINS_TASL7_20261026.md` |
| (3) Host equivalence | The TASL-7 agent chose this configuration and pre-declared it in `f3567e9`. The portal session's later hand-over STATUS entry (`84fe7c1`, pushed 23:41 UTC) repeats it. Kev-0.8B, fresh head, soft labels, lr 1e-4, seed 0, 2,000-step cap, at the portal's code `8e13e77` with identical config, data and environment hashes. The tolerance was pre-declared and pushed first (`f3567e9`). Result: **equivalent**. Δ width slope −0.0095 (≤ 0.05), Δ mean slope +0.0077 (≤ 0.05), RPS −2.5 % (≤ 10 %). | `TRACKP_TASL7_EQUIVALENCE_20261026.md` |
| Code | Run manifests now record the host (hostname, GPU name, compute capability, driver, `CUDA_VISIBLE_DEVICES`), as R1-ADA-OVERFLOW requires ("each manifest records the host and GPU"). A test covers it. | `d3bed8b` |
| (4) Review | Independent reviewer; see `docs/r1/reviews/TRACKP_TASL7_MIGRATION_REVIEW_20261026.md`. | — |

GPU: 26.3 leased minutes on TASL-7 (smoke test 0.9 min, equivalence run 25.4 min). Before each job there was no Track X marker and no foreign compute process. The portal's work dir and models were not touched; this session has no access to the portal.

## Not done

- **No P.3a run.** P.3a needs `docs/r1/authorizations/trackp_p3a_<date>.md`, which does not exist. The R1-P3A-READY short two-stage DRYRUN ran on the portal (`TRACKP_E0V2_TWOSTAGE_DRYRUN_20261026.md`). The portal's hand-over lists repeating it on TASL-7 at `5538b79` as optional; it has not been run here.
- **No CPU test venv.** The Phase 1 CPU venv (`trackp-cpu`, torch 2.14.1+cpu) is not rebuilt here, and the full Track P suite was not re-run on TASL-7. Only the changed manifest tests were run, in `trackp-gpu`: 3 passed.
- **No secrets file.** `~/.config/r1/secrets.env` is absent; it is needed from Phase 7.
- **No reboot.** The reboot pending since 6 Oct has not been done.

## Questions for the author

1. **Track X STATUS fallback on TASL-7.** The GPU lease (`r1/c3/train/run.py`, `gpu_lease` → `track_x_running`) still refuses to start whenever `origin/main` STATUS has a newest Track X heading reading "B1/B2 running". On the portal that guard is correct. On TASL-7, R1-TASL7-TRACKP says Track P no longer shares the card and the header says the Track X marker "is not needed". So from about 2 Nov, while B1/B2 runs on the portal, the guard would also block every Track P GPU job on TASL-7. I propose one config key, e.g. `gpu.trackx_shared_card: false` on TASL-7, that skips both Track X checks (marker and STATUS) there, while keeping the flock and the foreign-process check. Your decision; not changed.
2. **Config label.** `trackp_portal.json` still says `"host": "TASL-2 (zhixu portal)"`. No code reads it, and each manifest now records the real host. Should I keep the file unchanged, which keeps the config digest equal to the portal's, or add `trackp_tasl7.json`? A new file changes the digest of every later run. The digest would change anyway if question 1 adds a key.
3. **Reboot.** When will you reboot TASL-7 (pending since 6 Oct)? Before the P.3a runs is safer.
4. **Other users.** `tianyu` and `jiachenl` have sessions on the "exclusive" node. If they ever start GPU work, the lease will refuse to start while it runs. Is that intended?
5. **P.3a.** The migration is complete. `trackp_p3a_<date>.md` is needed before any P.3a evidence run, and every P.3a and later table runs on TASL-7 only.
