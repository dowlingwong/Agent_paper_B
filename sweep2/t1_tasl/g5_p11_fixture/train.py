"""Tiny deterministic CUDA computation with a single editable constant."""
import os

import torch

OFFSET = 0


def checksum():
    values = torch.arange(4, device="cuda", dtype=torch.int64)
    train_seed = int(os.environ["AR_TRAIN_SEED"])
    split_seed = int(os.environ["AR_SPLIT_SEED"])
    result = int((values + OFFSET).sum()) + (train_seed + split_seed) % 4
    with open("synthetic.bin", "wb") as fh:
        fh.write(result.to_bytes(4, "little"))
    return result
