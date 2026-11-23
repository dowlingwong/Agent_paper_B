# I2 759982 still idle — clause diagnosis and options (23 November 2026)

**Read-only diagnosis; the request was not changed.** Job 759982 is the I2 v2.1 CPU image check, resubmitted with
`request_disk=2,000,000 kB` (R1-TRACKP-I2-DISK) after 759919 was removed. It has been idle ≈3.5 h.

## `condor_q -better-analyze` (sample 2026-11-23 ~13:35Z; latest failure 14:40:52Z)

The job's requirements are `(TARGET.ProvidesETPResources) && Arch==""X86_64"" && HasContainer && HasDockerURL &&
Disk>=RequestDisk && Memory>=RequestMemory && Cpus>=RequestCpus && HasFileTransfer` (the container/HasDockerURL/
file-transfer terms are added by `universe=container`). Step table:

| Step | Slots matched | If drained | Clause |
|---|---|---|---|
| [0] | 14 | 1 | `TARGET.ProvidesETPResources` |
| [3] | 87 | 7 | `TARGET.HasContainer` |
| [4] | 13 | 1 | [0] && [3] |
| [9] | 39 | 7 | `TARGET.Memory >= 8000` |
| [10] | 12 | 1 | [4] && [9] |

At the sample: **0 slots match and are willing, 5 would match if drained**; 75 slots rejected by the job's
requirements, 8 reject because of their own requirements (owner slots: bms1/2/3, deepthought, deepthought2, portal1/2,
sg02). A later resample after `condor_reschedule` showed 4 match / 1 drained, but the job remained idle (no successful
match recorded), i.e. capacity appears/disappears between negotiation cycles.

## Clause counts on the full advertisement set (sample; 2,342 slots)

| Clause alone | Slots |
|---|---|
| `ProvidesETPResources` | 383 |
| `Arch == X86_64` / `OpSys == LINUX` | 2,342 / 2,342 |
| `HasContainer` / `HasDockerURL` / `HasFileTransfer` | 2,341 / 2,341 / 2,342 |
| `Disk >= 2,000,000 kB` | 2,251 |
| `Memory >= 8,000 MB` | 2,195 |
| `Cpus >= 2` | 2,120 |
| **All clauses together** | **222** |

Restricted to ETP+container+arch/OS+file-transfer+CPUs≥2+Disk≥2 GB: **241** slots; applying the memory request:

| `request_memory` | Slots | Unclaimed |
|---|---|---|
| ≥500 / ≥1,000 MB | 241 | **4 / 4** |
| ≥2,000 MB | 239 | **2** |
| ≥4,000 MB | 239 | 2 |
| ≥6,000 MB | 230 | 1 |
| **≥8,000 MB (current)** | **222** | **0** |

So `ProvidesETPResources ∩ HasContainer` is the first hard filter (14→13 of the negotiator's 88), but the **8 GB
`request_memory` is the binding constraint for currently unclaimed slots**: at 8 GB there are **0 unclaimed**
candidates, while 2 GB exposes 2 and 1 GB exposes 4.

## What I2 actually used

Prior I2 v2 job **759693** (same script/request; completed): `MemoryUsage=48` MB, `ResidentSetSize=75,000` kB
(≈73 MB), `ImageSize=50` MB, `DiskUsage=30` kB, wall 243 s. The current 8,000 MB request is ≈**166×** the measured
memory (48 MB) and the observed RSS (~73 MB); the I2 design/run does no memory-heavy training.

## Options and recommendation

1. **Recommended: a reviewed `request_memory` reduction to 2,000 MB** (author row; only this field, with a short
   independent JDL-diff review), leaving `request_disk=2,000,000 kB`, CPU/image/pool unchanged. This is ≈27× the
   measured RSS, and exposes 2 unclaimed ETP container slots immediately (4 at 1,000 MB). It mirrors the
   R1-TRACKP-I2-DISK pattern and keeps the measured-need margin.
2. **A different CPU class** without `ProvidesETPResources` (if the author allows the route change): would match
   easily, but changes the pool provenance; not recommended while option 1 is sufficient.
3. **Keep waiting with 8 GB**: possible but currently 0 unclaimed slots at this memory; the historical I2 wait was
   243 s only when capacity existed, so the expected wait is unbounded/unknown. Not recommended unless the author
   prefers not to change another request field.

The watcher continues waiting on 759982; no smoke/E0/P.4 will start until I2 passes.
