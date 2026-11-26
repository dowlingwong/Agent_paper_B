# Report — recurring resource samples and pool watch (27 Nov 2026, ~23:42Z)

**Task:** `experiment/20261126-02` (TASL-7 card and Ada) with `cluster/20261126-03` (pool watch). Read-only; no
reservation, no job submitted, no request changed.

**Result: PASS (samples).** TASL-7's card is free; Ada has two empty 48 GB cards; the ETP pool still advertises no
H200/H100/A100 and no NEMO2 GPU. P.4's H200 job `760065` remains Idle and unmatched.

## TASL-7 — third sample

| UTC | Free MiB | Util | Compute apps | `gpu0.lock` | Load (1/5/15) |
|---|---|---|---|---|---|
| 2026-11-26T23:42:09Z | 24,029 | 0 % | 0 | free | 0.10 / 3.10 / 4.13 |

The card has been empty at all three samples (22:39, 22:54, 23:42Z). This is a snapshot, not a reservation. No R1
job uses it.

## Ada — third sample

| UTC | Cards 0 / 2 free | Cards 1, 3, 4, 5 free | Cards 6 / 7 free | Compute apps | Load |
|---|---|---|---|---|---|
| 2026-11-26T23:42:26Z | 48,427 MiB (0 %) | 14,717 / 14,729 MiB (100 %) | 21,331 / 21,732 MiB (71 / 93 %) | 10 | 13.10 |

Two empty 48 GB cards again (cards 0 and 2). The shared cards carry other users' processes; only count and memory
were read. No reservation. Ada still has no torch environment for P.4 (survey, 26 Nov).

## ETP HTCondor pool — third snapshot

- Advertised GPU slots: 2× GTX TITAN X on deepthought, 1× L40S on deepthought2. **No H200, H100, A100, and no NEMO2
  GPU of any model.**
- Slot states: 454 Claimed, 20 Unclaimed, 1 Owner.
- `760065` (P.4 T1, H200): **Idle**, 1 idle / 0 running, still unmatched.
- Our other jobs: `759624`, `759625` (old idle probes); `760142`, `760143`, `760145`, `760146` Running (the
  non-Paper-B A100 project). No request was edited.

## What happens next

The next round takes the next samples. When a NEMO2 GPU of any model appears, report at once with model, machines
and free GPUs. When an H200 appears, let `760065` run and commit its output and `T1_versions/condor_history.txt` as
the P.4 units require. TASL-7's card and Ada's two empty cards stay unreserved; no run starts without a note/task.

**Decided alone:** to report the samples without opening any other user's process identity (count and memory only),
and to keep the pool watch read-only. No pin, request, lease or evidence file changed.
