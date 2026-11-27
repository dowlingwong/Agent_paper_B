import pytest
import torch
from torch.nn import functional as F

from paperc import eint_batches as E
from paperc import eint_census as census


def test_update_targets_are_identical_at_both_contexts():
    docs = [[0, 1, 2, 3, 4], [0, 5, 6], [0, 7, 8, 9]]
    for context in [2, 8]:
        updates = E.updates(docs, context=context, tokens_per_update=3, steps=3)
        assert [[token for s in step for token in s.targets] for step in updates] == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    with pytest.raises(ValueError, match="ended"):
        list(E.updates(docs, context=2, tokens_per_update=3, steps=4))


def test_packing_preserves_positions_masks_and_reference_attention():
    docs = [[0, 1, 2], [0, 3], [0, 4, 5]]
    step, = E.updates(docs, context=4, tokens_per_update=5, steps=1)
    packed, = E.rows(step, context=4, packed=True, max_rows=4)
    plain, = E.rows(step, context=4, packed=False, max_rows=4)
    assert packed["targets"].shape == (2, 4) and plain["targets"].shape == (3, 4)
    assert packed["positions"][0].tolist() == [0, 1, 0, 0]
    assert not packed["attention_mask"][0, 2, :2].any()
    assert not packed["attention_mask"][0, 0, 1]
    assert packed["attention_mask"][0, 3, 3]
    assert packed["loss_tokens"] == plain["loss_tokens"] == 5

    def loss(batch):
        hot = F.one_hot(batch["input_ids"], num_classes=6).to(torch.float64)
        scores = F.scaled_dot_product_attention(hot, hot, hot, attn_mask=batch["attention_mask"])
        return F.cross_entropy(scores.flatten(0, 1), batch["targets"].flatten(), ignore_index=E.IGNORE,
                               reduction="sum")

    torch.testing.assert_close(loss(packed), loss(plain))


def test_complete_cell_receipts_require_matched_inputs():
    common = {"seed": 61005, "status": "complete", "target_sha256": "targets", "trained_tokens": 16,
              "validation_tokens": 4, "allocator_cap_bytes": 100, "paper_commit": "commit",
              "gpu_model": "GPU", "data_manifest_sha256": "data"}
    rows = [{**common, "cell": cell, "validation_loss": loss}
            for cell, loss in zip(census.CELLS, (4, 3.5, 3, 2))]
    assert census.interaction(rows)[61005]["quality_interaction"] == .5
    rows[-1]["status"] = "out_of_memory"
    assert census.interaction(rows)[61005]["quality_interaction"] is None
    rows[-1].update(status="complete", target_sha256="another")
    with pytest.raises(ValueError, match="unmatched"):
        census.interaction(rows)


def test_modified_manifest_is_refused_before_opening_tokenizer(tmp_path):
    (tmp_path / "data_manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="manifest differs"):
        next(E.documents(tmp_path, split="validation", seed=61005))
