# compute/20261128-24 — order: finish D.3a template checks, then launch G.5 from the clean bases; P.4 signing key

Author (28 Nov): "G.5 启动 A … 让 D.3a 这轮先完成". PLAN **R1-G5-LAUNCH-BASE** and **R1-P4-SIGNING-KEY** are on `main` (`11cfeb51`).
1. **First** finish `compute/20261128-23` (D.3a template per-chunk server checks, engineering, record + review).
2. **Then launch G.5**, each run from its own clean base (now ancestors of `origin/main`): main run `2178bc6e` (`c3_t1_labels_20261128`); addenda Titanic
   `88edb84f`, MetaMaze `4ee43037`, ETTh1 `e9441f03`, Forest Cover `f96069d0` (`…_addendum_1…4`). For each: fresh clean checkout of the base, fresh fetch, strict
   `check-note` with that run's note and spec, `verify_launch_tasl` PASS, then `validate --launch` and the run as the note says (TASL pair routing, S13 CPU
   sets, per-card lease, server foreign-process check: wait, never work around). Addenda start when their hosts/CPU sets are free; record each launch time
   and job ID. Report progress each round; any STOP with the scene sealed.
3. **P.4 signing key** (R1-P4-SIGNING-KEY): on the host where you make the commit, generate a **new** SSH signing key (ed25519) outside the repository
   (e.g. `~/.config/r1-signing/`, mode 600; never print or commit the private key; do not touch existing key files). Commit its public key and fingerprint
   to `docs/r1/keys/` with an `allowed_signers` line. Make the signed one-file commit: parent `0b46595418bb21dc0e8e5b234b30f2a84ac5082c`, exactly the spec bytes of
   `befb58c8` (sha256 `d9ab6269…`), `git -c gpg.format=ssh -c user.signingkey=<pub> commit -S`; push a branch; report the commit, `git verify-commit`
   (with the allowed_signers file) and the spec sha256. Local then fills P3. Do this alongside step 2 (no GPU).
