# Local round close — houseprice CPU-set check and Ada card lease

for: coordinator

Queue checked after both deliveries at published `main` `35c42b81880a444c55d25d604007366c7533ec82`, `coord/coordinator` `418214d2e27a16ba78eb86c037aa5e9d9561d85f`, `coord/compute` `75570153ed0469a058e31b3c9ac52f71f299540e` and `coord/local` `a1f925b2ffabafc683e616a25dc6f2bd00e73bc5`. Local is idle. Both units were based on `35c42b81880a444c55d25d604007366c7533ec82`. The assigned checkout is clean. Task checkouts used writable temporary Git metadata because the shared linked-worktree metadata is read-only in this session.

## Delivered

- **`local/20261127-27`** `mac-houseprice-cpuset-count-20261127` @ `b5626bf4aa5486395714e30186263ad6cd896af5`. Independent tier-E **ACCEPTED**. Full suite 5,016 passed versus 5,013 at base, with all 123 failure/error IDs identical. The former `tasl2-cpuset-mlgym_houseprice-20261127` STOP and its two seals are preserved. After publication and lease clearance, Compute `20261127-15` uses the exact `for: compute` command for three attempts at the next unused dated ID, earliest 28 Nov UTC. [Task report](20261127-27-houseprice-two-attempts.md)
- **`local/20261127-28`** `mac-trackp-per-card-lease-20261127` @ `801b2d49432c68f46b3658b1cb27a0d5e99ef9ad`. Independent tier-E **ACCEPTED**. Full suite 5,025 passed, identical 123 failure/error IDs, and 215 targeted P.4 tests passed. After publication, Compute `20261127-29` uses an empty Ada card for staged smoke and E0, with the same UUID and reviewed per-card lock directory. [Task report](20261127-28-trackp-per-card-lease.md)

Both full suites had zero new failures. The shared failure/error list SHA-256 is `bdb6d456d3898cc16ae2fcad76e8a7870e2ce20122fc0837bb3e0e8baf216ff4`. The coordinator owns publication to `main`.

## In flight and pending at the latest receipts

- **Screening evidence running elsewhere.** `compute/20261127-30`, run `SMEAS_EVIDENCE_20261127T1550Z`, deepthought tmux `smeas_reissue2`, strict preflight PASS at the second signed re-issue. Check its manifest, run count, then committed analysis. `R1-D3-STEP8-HOLD` keeps D.3 step (8) and campaigns pending on the screening result. `compute/20261127-31` owns the G6 smoke-audit correction.
- **Expansion G.1b running elsewhere.** `compute/20261126-10`, `g1b-x-tasl-20261126-a`. ETTh1, MetaMaze and Forest Cover are sealed. Titanic PID `106578` on CPUs 12–15 was 84/150 at 15:33Z in the latest receipt. Compute checks its exit, seals, assembles and publishes the per-node determinism records.
- **G.5 P11 ready for Compute.** `compute/20261127-32` follows the screening launch. No new job ID is recorded. The remaining engineering host checks and accepted joint P11 receipt precede `local/20261126-08`'s final `paper.commit`, render and review. Houseprice additionally needs its published S14 PASS. `local/20261126-12` awaits the shared switch/launch-code binding, published expansion determinism and the approved PRE-SPLIT v2 amendment. Shared-card repeat policy awaits its author disposition.
- **Ada P.4 P5 pending publication of the lease unit.** The prior pre-check stopped before smoke or E0, with no GPU job ID. The next receipt should carry the accepted smoke, E0 and timing disposition. Phase 1 also requires the reviewed project-signed spec commit, note publication and strict checks. `compute/20261127-28` E-INT waits for its exact staging and engineering smoke on a separate eligible Ada card under Paper B priority. No E-INT job ID is recorded. The Paper C CPU drafts await operator pins and author approvals.
- **Batch route idle.** D.3 HTCondor jobs `760148`, `760149` and `760152` were removed unmatched, as was P.4 H200 job `760065`. Compute continues watching for an eligible ETP L40S or TOpAS A100. No D.3 evidence campaign is recorded.

Job state comes from published coordination and Compute receipts. No host job was submitted by Local and no sealed partition was opened.
