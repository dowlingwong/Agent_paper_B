# Paper C E-INT development census

Preparation under `local/20261127-20` and the next-phase runbook §5. The census measures
whether a batching edit changes the feasibility or held-out quality of a longer context.

## Workload check

The published `autoresearch_fixedtokens` harness pin is
`2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`. Its `prepare.py` reads natural documents
from Parquet and trains an 8,192-token tokenizer. Its current loader packs fixed rows,
crops a document where no whole document fits and shifts adjacent tokens into targets.
Its fixed BPB evaluation uses that loader. A context change would change the scored
token positions and packing would change which tokens survived cropping. Use a fresh
development adapter over the existing raw documents and tokenizer.

Use the publicly pinned ClimbMix revision `915333b4f8b8684f39aeaafea600fea6f43fb703`
and verify all files against manifest SHA-256
`ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`.
Train documents come from shards 00000–00009. Hold out shard 06542. Freeze a deterministic
per-seed order for train and the identical first 65,536 eligible validation targets
in canonical shard order for every cell. Tokenize each document once with the pinned
tokenizer, prepend its BOS and record ordered document and token digests. Keep BOS
as context and count only next-token predictions of real document tokens.

## Proposed smoke and census spec

| Cell | Batching | Training context |
|---|---|---:|
| baseline | one segment per padded row | 512 |
| A | consecutive segments packed in order | 512 |
| B | one segment per padded row | 2,048 |
| A+B | consecutive segments packed in order | 2,048 |

Use a shared model, optimizer, precision, initialization and document order for each seed.
Recommend three fresh development seeds `61005–61007` from the Paper C training reservation.
Keep 8,192 loss-bearing targets per optimizer update and 1,048,576 per complete attempt.
Treat numerical values as draft until the launch card binds them after reviewing a
separate smoke budget. Retain the first 1,048,576 ordered targets in all cells, including
at update/context boundaries. Separate segments keep local position IDs. Attending across
documents or separately cut segments is refused. Pad targets with `-100`, mask future and
cross-segment keys and divide the accumulated loss sum by the effective target count.

Use a single empty GPU and a fixed memory cap. Recommend an 18 GiB cap on an RTX 4090,
pending a free card, driver/backend identity, reproducible baseline and signed smoke limits.
Define the cap as maximum memory reserved by the process's PyTorch caching allocator.
Set the ceiling before creating the model. Pair all cells under that exact cap. An
operator sensor records host-side process memory including allocations outside PyTorch.
Report the sensor peak as sampled process memory. Charge every attempt even if OOM,
and record the first cap/refusal event. Never substitute a larger card or change precision
mid-comparison. Use the same reference evaluator for all cells with context 512 and exactly
the same validation tokens, masks and scoring denominator.

## Code and acceptance

`paperc.eint_batches` verifies the pinned source, streams documents, and provides the shared
loss-target stream and mask. `paperc.eint_census` binds a six-layer, width-256 decoder with
tied embeddings, four attention heads, math SDPA, BF16 autocast and AdamW (3e-4).
It divides accumulated loss by the effective target count and logs observed targets per update.
Before any
GPU run, independently verify the mask and per-document loss equality between packed and
unpacked layouts with deterministic weights, then verify backend, memory counters, lease
and signed cap in a smoke. Seal attempt identity, ordered token digests, metrics, per-update
tokens, peak memory, wall/GPU seconds, throughput, exits and checksums.

After a launch card and signed authorization, stage one empty visible GPU and invoke the
reviewed module once per authorized cell and seed, in a new output directory.

```sh
PYTHONPATH=paperC/src python -m paperc.eint_census --paper "$PAPER" --data "$DATA" \
  --spec "$SIGNED_SPEC" --cell "$CELL" --seed "$SEED" --out "$OUT"
```

The spec binds the phase, exact cell/seed pairs, GPU model, allocator cap bytes, number of
updates and number of fixed evaluation targets. The published note at
`docs/r1/authorizations/paperc_eint_census_20261127.md` binds `task`, `approved`,
`paper_commit`, `spec_sha256` and the independent review digest. The probe readiness
record must verify baseline repeatability and headroom before proposing further sequential
work. The common 512-token evaluator measures short-context quality after training.

Read feasibility first. If the four cells complete on matched seeds, report paired
`Y(A+B) - Y(A) - Y(B) + Y(base)` with (Y) equal to negative held-out cross-entropy.
Keep an infeasible comparison descriptive by cause and cost. Report inconclusive comparisons
as such. Speed is a systems result. A test of sequential search value would require a
new intervention design and authorization.
