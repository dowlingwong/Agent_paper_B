# Branches of `dowlingwong/Agent_paper_B` (16 Nov 2026)

**Written 16 Nov 2026 by the coordinating chat (Claude) during the repo cleanup the author asked for; AI-assisted.** Supersedes `BRANCHES_20261104.md` (kept as history).

## Rules

- `main` is the published authority. Evidence code checks its authority files against GitHub `main` (`r1/c3/dataset.py` `_verify_published`), and the D8 guard reads PLAN at the committed HEAD. Author rows are committed on an `author-*` branch and reach `main` by merge (no squash, rebase or cherry-pick).
- Agents push only their own branches: one operator per branch and per host. Nobody force-pushes. Only the author decides pushes to `main`. `exam-x-*` is never pushed or deleted by an agent.
- Finished work is merged into `main`; the branch is then removed. Nothing is lost: every removed branch is listed below with its tip SHA, and the tips that are not in `main` are in the backup bundle.

## Kept branches

| Branch | Why it is kept |
|---|---|
| `main` | published authority; all merged work; author rows reach it by merge |
| `exam-x-20261026` | protected exam branch (agents never push or delete exam-x-*) |
| `author-decisions-20261116` | author rows of 16 Nov; merged into main; agents read authority from it until told to use main |
| `docs/runbooks-16nov` | sweep-2 work plan; merged into main |
| `mac-b1-20261107` | STATUS publication branch of the experiment agent; merged into main |
| `ops-b2-exec-20261115` | B2 execution record (experiment agent); merged into main |
| `mac-m3-dryrun-path-20261114` | named as a deploy branch in authorizations/c3_env_replay_20261116.md; merged into main; keep until e1 is done |
| `sweep2-cluster-20261116` | cluster agent, active (S2-C2 wrapper) |
| `sweep2-main-20261116` | cluster agent, active |
| `s2c3-deploy-20261116` | cluster agent, active (S2-C3) |
| `s2c3b-live-20261116` | cluster agent, active (S2-C3b liveness) |
| `g1b-noise-20261116` | cluster agent, active (G.1b) |
| `htc-image-v2-20261115` | cluster agent, image v2 (not yet approved) |
| `htcondor-container-20261115` | cluster agent, HTCondor adapter (container universe) |
| `ops-e1-replay-20261116` | cluster agent, e1 environment replay |
| `w2-3-rebuild-unit-20261115` | cluster agent, c3_features/v3 rebuild record; changes r1/c3 code, integration pending |
| `ops-tasl-20261116` | experiment agent, TASL work |
| `paperc-build-20261115` | Paper C work (paperC/); separate |
| `paperc-scaffold-20261115` | Paper C scaffold; separate |
| `mac-int-trial-20261114` | pending integration of reviewed code units (W2 budget/stop rule, Track P RL, M4, Track G docs); author decides |
| `trackp-20261026` | Track P P.3a code (watchdog, guarded tests); Track P resumes on TASL-7 |
| `mac-tracks-stop4-end-20261115` | Track S home: separate history (unrelated to main), code and full record; its docs and results were imported into main |
| `repo-cleanup-20261116` | the cleanup branch itself; equals main after the cleanup |

Any branch an agent created after this file was written is also active.

## Scheduled for removal (16 Nov 2026)

The cleanup session could not push tags or delete branches (HTTP 403 from its git proxy). The removal is therefore run from the author's side with `archive_and_delete.sh` (same folder as the bundle): it first pushes a tag `archive/20261116/<branch>` at each tip SHA below, verifies the tags, then deletes each branch only if its tip still equals the listed SHA. A second, independent archive is the git bundle:
- `agent_paper_b_branches_20261116.bundle` (6.1 MB; sha256 in `SHA256SUMS`) and `MANIFEST.txt`, in the author's `Claude outputs/archive_branches_20261116/`. The bundle holds every removed tip that is not in `main`; tips marked `main=yes` are commits in `main` already.
- Restore one branch: from its tag (`git push origin archive/20261116/<branch>:refs/heads/<branch>`), or `git fetch <bundle> refs/remotes/origin/<branch>:refs/heads/<branch>` (or, for a `main=yes` row, `git branch <branch> <sha>`), then push it.

Reasons:
- `merged`: merged into `main` today or earlier (finished deliverables);
- `obsolete`: superseded troubleshooting, candidate, probe and review branches (B1, 7–8 Nov), `codex/*`, old runbook lines, and branches whose tips are contained in a kept branch.

| Branch | Tip | Reason | In main |
|---|---|---|---|
| `author-ack-w23-20261115` | `b0c8a48d1c1b` | merged | yes |
| `author-qtorch-20261115` | `d4ea56c101e2` | merged | yes |
| `author-stop4-20261115` | `1f5f24e340f5` | merged | yes |
| `author-sweephost-20261116` | `4651469a7292` | merged | yes |
| `author-x7-20261116` | `e35c6727f342` | merged | yes |
| `b1-d-report-20261114` | `5ec0aeafbd07` | merged | yes |
| `codex/b2-repair-20261031` | `f98e315e9227` | merged | yes |
| `codex/coordinator-20261031` | `10742f85f345` | obsolete | no |
| `codex/trackx-seed-20261031` | `1be426fd653e` | obsolete | no |
| `codex/trackx-stagea-cooperative-20261031` | `74a0790739b7` | obsolete | no |
| `docs/b1-stop-diagnosis-08nov` | `1d517b79a16c` | obsolete | no |
| `docs/main-proposer-03nov` | `14dc0fea2847` | obsolete | no |
| `docs/repo-tidy-20261104` | `d413dc81294b` | obsolete | no |
| `docs/runbooks-04nov` | `78000a6f765d` | obsolete | no |
| `docs/runbooks-09nov` | `421a93d215a7` | merged | yes |
| `docs/runbooks-11nov` | `7cfbe7c9bd2f` | merged | yes |
| `docs/runbooks-14nov` | `69b3576bb077` | merged | yes |
| `docs/seq-revision-04nov` | `4af310ec6301` | obsolete | no |
| `docs/trackS-decisions-30oct` | `13badb0d1627` | obsolete | no |
| `dt-sweep1-20261025` | `75c8f5ce1b99` | obsolete | no |
| `dt-sweep1-20261026` | `38923543be46` | merged | yes |
| `htc-image-20261114` | `74820315f56e` | obsolete | no |
| `htcondor-chain-20261114` | `13050d14f23c` | merged | yes |
| `htcondor-prep-20261114` | `36cc113c88f8` | merged | yes |
| `int-main-sweep2-20261116` | `9ae6d87783f5` | merged | yes |
| `local-20261026` | `7c8449b0f62a` | merged | yes |
| `local-h8-20261027` | `f666a38d6448` | merged | yes |
| `mac-answers-20261114` | `e7f890964af5` | merged | yes |
| `mac-appendix-20261114` | `4a5811d1ace6` | merged | yes |
| `mac-auth-p3a-20261104` | `bf203b0d066d` | obsolete | no |
| `mac-b1-6835-b2-ranking-review-20261108` | `f03069557f84` | obsolete | no |
| `mac-b1-6835-capacity-review-20261108` | `7d0193f02f76` | obsolete | no |
| `mac-b1-6835-monitor-review-20261108` | `e15f02704881` | obsolete | no |
| `mac-b1-6835-native-preflight-review-20261108` | `09a011e4def6` | obsolete | no |
| `mac-b1-6835-observation-review-20261108` | `b26dca354c47` | obsolete | no |
| `mac-b1-6835-operator-review-20261108` | `a951d047d588` | obsolete | no |
| `mac-b1-6835-restoration-review-20261108` | `1e23814a9e54` | obsolete | no |
| `mac-b1-6835-status-review-20261108` | `f63904d57a53` | obsolete | no |
| `mac-b1-audit-stop-candidate-20261107` | `7eec8ab2acf2` | obsolete | no |
| `mac-b1-combined-20261107` | `c35617aab6ab` | obsolete | no |
| `mac-b1-containment-20261107` | `9f4690fd00da` | obsolete | no |
| `mac-b1-diag-20261109-c` | `7b08c2ad548e` | obsolete | no |
| `mac-b1-diag-report-20261111` | `3e4d7cc9fabe` | obsolete | no |
| `mac-b1-direct-worker-20261107` | `9c354de30eef` | obsolete | no |
| `mac-b1-exact-6835-review-20261108` | `da32d9511eac` | obsolete | no |
| `mac-b1-exact-review-20261108` | `0c16a2f3ac67` | obsolete | no |
| `mac-b1-finalization-candidate-20261107` | `d7633ac4de76` | obsolete | no |
| `mac-b1-fixture-next-20261107` | `2c3c2ddeb438` | obsolete | no |
| `mac-b1-handshake-20261107` | `f80895a3cac4` | obsolete | no |
| `mac-b1-m15-standby-20261114` | `8eae3e02f6a4` | obsolete | no |
| `mac-b1-mac-fixture-probe-20261107` | `620d755ccbb9` | obsolete | no |
| `mac-b1-mac-publisher-probe-20261107` | `1570aeca72ba` | obsolete | no |
| `mac-b1-mac-rename-probe-20261107` | `04146eef1539` | obsolete | no |
| `mac-b1-obs180-20261113` | `8eae3e02f6a4` | obsolete | no |
| `mac-b1-observer-20261105` | `726ba867a8f1` | obsolete | no |
| `mac-b1-other-state-20261107` | `e16b9a08a802` | obsolete | no |
| `mac-b1-overnight-20261105` | `4019756e276d` | obsolete | no |
| `mac-b1-preserved-pytest-candidate-20261107` | `0d6d9ad84cdb` | obsolete | no |
| `mac-b1-pytest-session-candidate-20261107` | `1ddd82bfdc82` | obsolete | no |
| `mac-b1-r4-20261109` | `3c0fa0b7e6e0` | obsolete | no |
| `mac-b1-receive-audit-6835-20261108` | `dd5877458dc0` | obsolete | no |
| `mac-b1-stagea-synthetic-20261107` | `573f518511b5` | obsolete | no |
| `mac-b1-state-preservation-20261107` | `908302290ae6` | obsolete | no |
| `mac-b1-stop-census-review-20261108` | `c3f028f8ffca` | obsolete | no |
| `mac-b1-stop-descriptive-review-20261108` | `c014bb2e0e62` | obsolete | no |
| `mac-b1-tests-20261105` | `97bb9a7ebdc6` | obsolete | no |
| `mac-b2-20261104` | `14686a29dd50` | merged | yes |
| `mac-b2-code-20261114` | `a2cd540c6259` | merged | yes |
| `mac-b2-handoff-20261114` | `2120956c3fde` | merged | yes |
| `mac-b2-handoff-exec-20261115` | `aeeab991e883` | merged | yes |
| `mac-b2-plan-20261114` | `3533b5457399` | merged | yes |
| `mac-b2-ranking-20261107` | `cfb0779eea4a` | obsolete | no |
| `mac-b2-stop6-report-20261115` | `5c63ebfd4e17` | merged | yes |
| `mac-gate-20261104` | `9bdbcc27eea8` | obsolete | no |
| `mac-htcondor-20261114` | `f2a46da11b4b` | merged | yes |
| `mac-htcondor-container-20261114` | `7a6e96127614` | merged | yes |
| `mac-int-20261104` | `e9641c1dd0ba` | merged | yes |
| `mac-int-20261107` | `a15300ca80cd` | merged | yes |
| `mac-int-pre-10742f85` | `73e63c5d419b` | obsolete | no |
| `mac-m10-hk6-20261107` | `eb8766079a91` | obsolete | no |
| `mac-m10-hk6-cut-review-20261108` | `c21c4485aebc` | obsolete | no |
| `mac-m10-hk6-shard-review-20261108` | `8a98824742e8` | obsolete | no |
| `mac-m10-hk6-synthetic-cli-review-20261108` | `ef435334be30` | obsolete | no |
| `mac-m10-hk6-usr1-review-20261108` | `dd97e2a60c05` | obsolete | no |
| `mac-m11-b2-questions-review-20261108` | `c58590f6db65` | merged | yes |
| `mac-m11-binding-20261107` | `3af4090a16ae` | merged | yes |
| `mac-m11-constructors-sealed-review-20261108` | `ea3ac2927086` | merged | yes |
| `mac-m11-d8-20261107` | `33f0a278365f` | merged | yes |
| `mac-m11-d8-20261109` | `83a12b446cfd` | merged | yes |
| `mac-m11-d8-alt-20261114` | `6cbb6ef5f6f0` | merged | yes |
| `mac-m11-d8-git-tests-review-20261108` | `850f4fc7656a` | merged | yes |
| `mac-m11-d8-skew-20261115` | `cb36a30fbe50` | merged | yes |
| `mac-m11-d8-test-20261115` | `0a6293d22725` | merged | yes |
| `mac-m11-d8-v2-20261114` | `e3c0921ee59e` | merged | yes |
| `mac-m11-inference-primitives-review-20261108` | `b856e9667d4c` | merged | yes |
| `mac-m11-manifest-sealed-review-20261108` | `c53f13034ee1` | merged | yes |
| `mac-m11-model-base-sealed-review-20261108` | `9e7abaaf211a` | merged | yes |
| `mac-m11-model-hash-sealed-review-20261108` | `18132a97a3bd` | obsolete | no |
| `mac-m11-point-stat-review-20261108` | `14d4571b7705` | merged | yes |
| `mac-m11-reader-inventory-review-20261108` | `a5339ea4a709` | merged | yes |
| `mac-m11-readers-integration-review-20261108` | `0446487fbee5` | merged | yes |
| `mac-m11-registry-sealed-review-20261108` | `32b8d78b55fd` | obsolete | no |
| `mac-m11-spike-metrics-sealed-review-20261108` | `a7907716a417` | obsolete | no |
| `mac-m3-16case-path-review-20261108` | `dad7fffdcd7b` | merged | yes |
| `mac-m3-20261109` | `ec6e30a98811` | merged | yes |
| `mac-m3-blocker-review-20261108` | `928b9678a68b` | merged | yes |
| `mac-m3-cache-copy-20261105` | `ecf1ce3cc1e2` | merged | yes |
| `mac-m3-case-binding-20261105` | `9ce6b3b88637` | merged | yes |
| `mac-m3-hup-source-20261107` | `4b52ae9233ef` | merged | yes |
| `mac-m3-listener-20261107` | `30868a23e3a8` | merged | yes |
| `mac-m3-pidfd-wait-20261107` | `4ad0b6e946b5` | merged | yes |
| `mac-m3-sigchld-20261107` | `78cf72206a03` | merged | yes |
| `mac-m3-supervisor-20261105` | `e3c1473b8cbf` | merged | yes |
| `mac-m3-withdrawn-recheck-review-20261108` | `1dcf23c8eb3d` | merged | yes |
| `mac-m4-20261109` | `5cd32efcae65` | obsolete | no |
| `mac-m4-dtq-20261114` | `1da4cd60a853` | obsolete | no |
| `mac-m4-order-review-20261108` | `5097b6a36ce8` | obsolete | no |
| `mac-m5-fix-20261104` | `d5f7b75e07fd` | obsolete | no |
| `mac-overnight-report-20261109` | `e7c525b6787c` | obsolete | no |
| `mac-overnight-report-20261114` | `9492032c6298` | merged | yes |
| `mac-s2-m1-auth-20261116` | `56b5b76e5ceb` | merged | yes |
| `mac-s2-m4-d8confirm-20261116` | `e9f003710b96` | merged | yes |
| `mac-s2-m5-x7c-20261116` | `31ed1c19f72f` | merged | yes |
| `mac-trackg-20261104` | `eba5f03681dd` | obsolete | no |
| `mac-trackg-20261109` | `f56f7f359d2a` | merged | yes |
| `mac-trackg-v2-20261114` | `52a40d573a24` | merged | yes |
| `mac-trackp-rl-20261114` | `c9d29ba96b07` | obsolete | no |
| `mac-tracks-a2u-stale-20261111` | `c8b13b5d63d3` | obsolete | no |
| `mac-tracks-s05-summary-20261114` | `3e0fa203793d` | obsolete | no |
| `mac-tracks-s05-summary-both-20261115` | `1417807b2120` | obsolete | no |
| `mac-w2-budget-20261109` | `0b62fb03df54` | obsolete | no |
| `mac-w2-stoprule-20261114` | `87f674679adc` | obsolete | no |
| `mac-w2-v3-prompt-20261114` | `90d17fde06b0` | obsolete | no |
| `mac-w2-v3-rebuild-20261115` | `d8aa956193ba` | obsolete | no |
| `mac-x5v2-20261104` | `cd47229f7618` | obsolete | no |
| `ops-20261104` | `ad1535872580` | obsolete | no |
| `ops-b1-20261109` | `d1d3068733ca` | obsolete | no |
| `ops-b1-restart-20261111` | `fffa45a12b5b` | merged | yes |
| `ops-b1-restart-c-20261112` | `4b312844962e` | merged | yes |
| `ops-b1-restart-d-20261113` | `7912b7fffb4c` | merged | yes |
| `ops-b2-20261115` | `8709dce792d4` | merged | yes |
| `ops/c3-sweep1-classify-20261028` | `007a8d1cdf57` | merged | yes |
| `trackS-20261029` | `9bb64ba67126` | obsolete | no |
| `trackS-ops-20261030` | `fab88fced839` | obsolete | no |
| `w2-3-check-20261115` | `03d742cf8f91` | obsolete | no |
