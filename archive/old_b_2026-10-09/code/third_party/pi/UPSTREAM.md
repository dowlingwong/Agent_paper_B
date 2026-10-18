# Vendored Pi — upstream record

This directory contains a pinned, vendored copy of the Pi coding-agent
repository. It is the exact source that the Round 8 scientific adapter invokes;
project-specific modifications are recorded in `LOCAL_CHANGES.md` and appear in
the same reviewable diff.

## Acquisition

| Field | Value |
| --- | --- |
| Requested repository URL | `https://github.com/badlogic/pi-mono` |
| Resolved repository URL | `https://github.com/earendil-works/pi` (redirected) |
| Canonical repository URL | `https://github.com/earendil-works/pi` |
| Upstream commit | `086c32e74530564922d011ade23ff582c9d63116` |
| Upstream commit date | `2026-08-15T05:33:05Z` |
| Default branch | `main` |
| Acquisition method | GitHub codeload tarball for the immutable commit SHA |
| Acquisition timestamp (UTC) | `2026-08-16T02:14:00Z` |
| License | MIT (preserved at `LICENSE`) |
| License digest (SHA-256) | `0457f5bcec3b3b211605dfb5d1a49042fd638f3686a410fe099c24a25af13c48` |

## Pristine source manifest

- Manifest path: `scripts/pi_pristine_manifest.txt` (1373 files)
- Manifest digest (SHA-256): `d4228eae4bf89ea3d1319d96f3245f390938a0b39794faf86f634d4fe5946c2c`

The manifest records the SHA-256 of every vendored source file (excluding
`node_modules`, `dist`, `.git`, and other generated/cache products). It is the
baseline against which `scripts/verify_vendored_pi.py` compares the current tree
and enumerates local modifications.

## Toolchain requirements

| Field | Value |
| --- | --- |
| Node | `>=22.19.0` (declared in `package.json` engines) |
| Package manager | npm (lockfile `package-lock.json` present; `npm-shrinkwrap.json` under `packages/coding-agent/`) |
| Package name | `pi-monorepo` (workspaces: `packages/*`) |

## Excluded artifacts

The vendored tree contains **no** `.git` directory, `node_modules`, compiled
`dist` output, caches, user sessions, authentication files, or model artifacts.
Build products are produced locally and must not be committed.
