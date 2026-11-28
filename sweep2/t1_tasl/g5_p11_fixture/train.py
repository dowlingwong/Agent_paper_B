"""Tiny deterministic CUDA computation with a single editable constant."""
import torch

OFFSET = 0


def checksum():
    values = torch.arange(4, device="cuda", dtype=torch.int64)
    result = int((values + OFFSET).sum())
    with open("synthetic.bin", "wb") as fh:
        fh.write(result.to_bytes(4, "little"))
    return result
