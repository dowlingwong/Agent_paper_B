# Unit A execution — P.3a attempt-1 inventory export for M13/order determination (16 November 2026)

**Status: Unit A inventory step executed (read-only on TASL-7); M13 order/version determination is
delegated to an independent reviewer; Unit B remains blocked.** Authority: `author-decisions-20261116` @
`4da73306` (+ `04ce814c` T4 row, not Track P); PLAN `R1-TASL7-TRACKP`, `R1-P3A-OOM-OPTION3`,
`R1-P3A-BUDGET-CLOCK`, `R1-C3-POOL`, `R1-C3-POOL-EXAM`; authorizations `trackp_p3a_20261027.md` +
`trackp_p3a_amend_20261104.md`; M13 inventory `reports/MAC_M13_TEMPLATE_INVENTORY_20261105.md`.
Unit A acceptance: `reviews/TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md` (sha `94d4c1de…`, 444 lines,
accepted for Unit A only; Unit B not authorized). No host write (only reads); nothing executed on the GPU.

## 1. Preflight capture (TASL-7, 2026-11-16T10:13:36Z; capture in the inventory dir, `preflight.txt`, rc 0)

- host `TASL-7`, user `dowling`, **boot id `2c9bb104-cc3c-4c60-be67-c1c8f0287fe4`**, uptime since
  2026-10-01 13:07 (no reboot).
- paper `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` on branch `trackp-20261026`, clean; harness
  `897d83c8efa364ec2fdd37288241cc42e01d7274`, clean.
- GPU RTX 4090, driver `580.178.04`, 236 MiB used, 0 %, **no compute app**; disk 524 G free (71 %).
- `~/r1_locks/gpu0.lock` present (0 B, 26 Oct), **lease FREE**; `_to_delete/` mode 700; no `*.active`
  marker; default tmux socket has no server; **other users' tmux exists** (`tianyu` pid 934891, three
  panes) and the preserved `dowling` `b1_6835_20261108_a` session (pid 1570627, own socket) — untouched.
- `~/r1_locks/bin/trackp-evidence` sha `f457a04e…`, mode 755, 3,949 B (matches the committed helper).
- Attempt-1 root 12 G; journal last line is the STOP at `2026-10-29T01:25:17Z` with
  `gpu_seconds_total = 130745.3789889291`.

## 2. Inventory exported (read-only; committed under `reports/trackp_p3a_attempt1_inventory_20261116/`)

243 files / 2.9 MB, `SHA256SUMS` sha `5c35ef2b9bf148ca4d73b28aa195ec2e439fd5f877559a7c85a3d3e6a291f950`
(242 entries), covering:
- **Attempt-1 run artifacts:** all **129 `manifest.json`** and **39 `report.json`** under
  `runs/p3a_operator_20261027` (including the three completed probes reports and the DRYRUN), the five
  `probes.stdout.log` files (including the 4b OOM traceback), `journal.jsonl` (81 lines),
  `gpu_lease_log.jsonl` (111 lines), the launch log and `p3a_operator_20261027.sh`;
- **Pinned source at `b9ad6f8f`:** `r1/c3/train/{types.py,serialize.py,model.py,exam_run.py,
  exam_synthetic.py,registry.yaml}`, `r1/c3/train/data/e0_v1.jsonl.gz` (sha `4f4db29b…`),
  `r1/scripts/{trackp.py,trackp_p3a_guarded.py,trackp_p3a_watchdog.py}`,
  `r1/scripts/configs/trackp_portal.json`;
- **Pinned Kev encoder for M13 (P-M1):** the installed `kev` package tree (0.1.0) and its
  `kev-0.1.0.dist-info` (`direct_url.json`: `https://github.com/jaredpalmer/kev` @
  `2074cc44256200bb37540103fa4572901faa10f3`);
- Attempt-1 manifests themselves record paper `b9ad6f8f` clean, harness `897d83c8` clean, the same
  **boot id `2c9bb104…`**, driver `580.178.04`, and env package commits (`kev 2074cc44`, `laya
  a478221b`, `startlux a99977d9`).

## 3. M13 facts found in the exported bytes (to be interpreted by the independent reviewer)

- **No attempt-1 manifest or report records a prompt or template version**: 0 hits for
  `prompt_version`/`template_version`/`template` across the 129 manifests + 39 reports; the per-run
  probes manifests record `model_files_sha256: {}` (the round-2 review's MINOR P-M1).
- The per-run manifests do record the paper commit (`b9ad6f8f`) and the host boot id, so the attempt-1
  launch provenance is fixed; the **template order/version** must be derived from the pinned source (now
  exported) by the independent reviewer, and a recording mechanism for attempt 2 defined (a manifest
  field + attempt-1 provenance tagging; attempt-1 results are not re-labelled).
- **Amendment record:** `main:docs/r1/authorizations/trackp_p3a_amend_20261104.md` sha256
  `cd867e95ddab0525827a48d68ea570743977bbf1b6ea819fefb98b3cf460f32d` (to be recorded in the attempt-2
  journal; the host checkout is unchanged and clean at `b9ad6f8f`).
- **A6:** resolved by the author's `R1-TRACKP-A6-DEFER` (16 Nov 2026, `author-decisions-20261116c` @
  `65d8d5bb`): A6 is **deferred for P.3a attempt 2 and disclosed in the report**; a separate independently
  reviewed A6 unit comes before any P.3b serialisation-order change. No A6 work is started here.

## 3b. M13 order/version record — COMPLETE (accepted)

The independent M13 record is committed as `reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md` (573 lines,
sha256 `351611c55516ca2aa2134b1efa0ca9d43bbec9b880a047ad1485baf16c94bce1`, verdict accepted). It
confirms: the exported pinned source is byte-identical to `b9ad6f8f` (11/11 blobs); all 39 run manifests
record paper `b9ad6f8f`, harness `897d83c8`, one config sha, boot `2c9bb104…`, Kev `2074cc44`; the only
two wrapper families that ran are PointerWrapper (Kev) and BinTokenWrapper (Qwen), both render
**history-before-proposal** (state → proposal → question → options/bins; Qwen has no `<decide>` token);
attempt 1 recorded **no** prompt/template version (0 of 168 JSON artifacts, 0 journal/lease lines) and its
probes manifests have `model_files_sha256 {}`; `PROMPT_VERSION = "trackp_prompt/v1"` is not read by the
wrappers. Attempt-2 mechanism specified: a per-unit `runner_manifest.json` (`trackp_p3a_unit_manifest/v1`)
with a `template` block (version/order/readout/encoder/wrapper + composite `template_id`) and an
`attempt1_provenance` block (root, journal/lease hashes, paper commit, loaded `final/saved` file hashes,
derived order/version, `label: derived`), plus journal fields at campaign/start/complete/STOP; attempt-1
results are retro-tagged by provenance, never re-labelled. A6 remains unimplemented; the record recommends
recorded deferral + disclosure for attempt 2 and a separate reviewed A6 unit before any P.3b order change
(author/coordinator decision, not decided here).

## 4. What remains for Unit A

- An **independent reviewer** inspects this inventory (pinned source + Kev encoder + manifests) and writes
  the M13 order/version record: which order attempt 1 used per family, the exact template-version strings,
  and the attempt-2 recording mechanism. Until that record exists, Unit A is not complete and Unit B is
  blocked.
- The A6 disposition request is with the author/coordinator.
- The two code units (A3-short delta; probes-only runner/preflight/journal/budget) remain to be written
  and independently reviewed before Unit B; this report does not authorize them or any GPU run.

## 5. Limits

- Read-only; attempt 1 untouched (journal still 81 lines, no new root); no host write beyond read-only
  SSH logins (which may touch the host's own systemd user/wireplumber state outside `~/r1_trackp`,
  as disclosed in earlier reviews); nothing deleted.
