# P.4 phase-1 signing key (28 Nov 2026)

New ed25519 key generated on TASL-2 under R1-P4-SIGNING-KEY. The private key is
`~/.config/r1-signing/p4_ed25519_20261128` (mode 600); it is never committed, copied or printed.

| Item | Value |
|---|---|
| public key | `docs/r1/keys/p4_ed25519_20261128.pub` |
| fingerprint | `SHA256:4Pw8bY6TGiiEhO0dik670Cj8p0JRCSAgqmiACRKbiA8` |
| allowed signer | `r1-p4-phase1-20261128` in `docs/r1/keys/allowed_signers` |
| signed spec | `r1/scripts/htcondor/trackp_p4/p4_spec_ada_phase1_20261127.json`, sha256 `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6` |
| signed commit parent | `0b46595418bb21dc0e8e5b234b30f2a84ac5082c` |
| signed branch | `p4-phase1-signed-20261128` |

The key was created for the author's P3 signature on the reviewed phase-1 spec bytes; it is
separate from every existing key file. Verification:

```
git -c gpg.ssh.allowedSignersFile=docs/r1/keys/allowed_signers verify-commit <signed-commit>
```
