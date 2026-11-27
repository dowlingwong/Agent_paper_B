"""Matched target accounting and boundary-safe E-INT batching."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Iterator, Sequence

import torch

IGNORE = -100


@dataclass(frozen=True)
class Segment:
    inputs: tuple[int, ...]
    targets: tuple[int, ...]


def updates(documents: Iterable[Sequence[int]], *, context: int, tokens_per_update: int,
            steps: int) -> Iterator[list[Segment]]:
    """Yield an exact ordered block of targets per optimizer update."""
    if min(context, tokens_per_update, steps) <= 0:
        raise ValueError("positive context, tokens per update and steps are required")
    remaining = tokens_per_update
    batch = []
    for doc in documents:
        position = 0
        while position < len(doc) - 1:
            n = min(context, remaining, len(doc) - 1 - position)
            end = position + n
            batch.append(Segment(tuple(doc[position:end]), tuple(doc[position + 1:end + 1])))
            position = end
            remaining -= n
            if remaining == 0:
                yield batch
                steps -= 1
                if steps == 0:
                    return
                batch = []
                remaining = tokens_per_update
    raise ValueError("document stream ended before the exact target budget")


def rows(segments: Iterable[Segment], *, context: int, packed: bool, max_rows: int) -> Iterator[dict]:
    """Use sequential next-fit packing and materialize only one microbatch at a time."""
    if min(context, max_rows) <= 0:
        raise ValueError("positive context and microbatch row count are required")
    pending, row, size = [], [], 0
    for segment in segments:
        n = len(segment.inputs)
        if not 0 < n <= context or len(segment.targets) != n:
            raise ValueError("invalid segment length")
        if row and (not packed or size + n > context):
            pending.append(row)
            row, size = [], 0
            if len(pending) == max_rows:
                yield _tensors(pending, context)
                pending = []
        row.append(segment)
        size += n
    if row:
        pending.append(row)
    if pending:
        yield _tensors(pending, context)


def _tensors(group: list[list[Segment]], context: int) -> dict:
    shape = (len(group), context)
    input_ids = torch.zeros(shape, dtype=torch.long)
    positions = torch.zeros_like(input_ids)
    targets = torch.full_like(input_ids, IGNORE)
    segment_ids = torch.full_like(input_ids, -1)
    for i, row in enumerate(group):
        offset = 0
        for j, segment in enumerate(row):
            n = len(segment.inputs)
            slot = slice(offset, offset + n)
            input_ids[i, slot] = torch.tensor(segment.inputs)
            targets[i, slot] = torch.tensor(segment.targets)
            positions[i, slot] = torch.arange(n)
            segment_ids[i, slot] = j
            offset += n
    same = segment_ids[:, :, None] == segment_ids[:, None, :]
    valid = segment_ids >= 0
    attention = same & valid[:, :, None] & torch.ones((context, context), dtype=torch.bool).tril()
    # Give padding queries a harmless self-edge. Their targets are ignored by the loss.
    attention |= (~valid[:, :, None]) & torch.eye(context, dtype=torch.bool)
    return {"input_ids": input_ids, "targets": targets, "positions": positions, "attention_mask": attention,
            "loss_tokens": int((targets != IGNORE).sum())}
