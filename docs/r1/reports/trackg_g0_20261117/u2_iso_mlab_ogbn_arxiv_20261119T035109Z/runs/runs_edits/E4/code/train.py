"""Editable baseline of node mlab_ogbn_arxiv (MLAgentBench ogbn-arxiv, Track G fixed-step port).

The model, optimizer and loss are those of MLAgentBench's
``benchmarks/ogbn-arxiv/env/train.py`` (MIT licence): a 2-layer MLP on the
node features (hidden size 16, batch norm, ReLU, dropout 0, log-softmax),
negative log-likelihood loss, Adam with learning rate 1, batches of 1,024
training nodes.  The suite's script builds a ReduceLROnPlateau scheduler but
never steps it, so the baseline has no schedule.  The suite's MLP has 172
outputs (ogbn-arxiv has 40 classes); the port uses 40, which the frozen
evaluation requires.  Two further differences come from the frozen loop:
(1) the suite trains the MLP on ``batch.x`` of a NeighborLoader subgraph (the
1,024 seed nodes plus their sampled 2-hop neighbours, 30 per hop) and computes
the loss on the seeds, so its batch-norm statistics include the sampled
neighbours; here a batch is the 1,024 training seeds alone, so batch norm sees
only them; (2) the suite's loader keeps each epoch's last partial batch (89
batches per epoch, the last of 829 nodes), while the frozen loop drops it (88
full batches per epoch; the 356-step budget is about 4.05 epochs).  The MLP
uses only node features; the graph is available in ``info`` for models that
use it.  The training loop, the step budget, the data and the metric are in
the frozen files.
"""
import torch
import torch.nn.functional as F

CONFIG = {
    "batch_size": 1024,
    "grad_clip": None,
    "amp_bf16": False,
}
# Model: the suite's MLP.
HIDDEN = 16
NUM_LAYERS = 2
DROPOUT = 0.0


class MLP(torch.nn.Module):
    def __init__(self, x, in_channels, hidden_channels, out_channels, num_layers, dropout):
        super().__init__()
        self.x = x
        self.lins = torch.nn.ModuleList([torch.nn.Linear(in_channels, hidden_channels)])
        self.bns = torch.nn.ModuleList([torch.nn.BatchNorm1d(hidden_channels)])
        for _ in range(num_layers - 2):
            self.lins.append(torch.nn.Linear(hidden_channels, hidden_channels))
            self.bns.append(torch.nn.BatchNorm1d(hidden_channels))
        self.lins.append(torch.nn.Linear(hidden_channels, out_channels))
        self.dropout = dropout

    def forward(self, idx):
        h = self.x[idx]
        for lin, bn in zip(self.lins[:-1], self.bns):
            h = F.dropout(F.relu(bn(lin(h))), p=self.dropout, training=self.training)
        return torch.log_softmax(self.lins[-1](h), dim=-1)


class SAGE(torch.nn.Module):
    """Two-layer GraphSAGE (mean aggregation over in- and out-neighbours), full-graph forward."""

    def __init__(self, x, edge_index, num_nodes, in_channels, hidden_channels, out_channels, dropout):
        super().__init__()
        self.x = x
        src, dst = edge_index
        self.src = torch.cat([src, dst])
        self.dst = torch.cat([dst, src])
        deg = torch.zeros(num_nodes, device=x.device).index_add_(0, self.dst, torch.ones_like(self.dst, dtype=x.dtype))
        self.inv_deg = 1.0 / deg.clamp(min=1).unsqueeze(1)
        self.self1 = torch.nn.Linear(in_channels, hidden_channels)
        self.neigh1 = torch.nn.Linear(in_channels, hidden_channels, bias=False)
        self.self2 = torch.nn.Linear(hidden_channels, out_channels)
        self.neigh2 = torch.nn.Linear(hidden_channels, out_channels, bias=False)
        self.bn = torch.nn.BatchNorm1d(hidden_channels)
        self.dropout = dropout

    def aggregate(self, h):
        out = torch.zeros_like(h).index_add_(0, self.dst, h[self.src])
        return out * self.inv_deg

    def forward(self, idx):
        h = self.self1(self.x) + self.neigh1(self.aggregate(self.x))
        h = F.dropout(F.relu(self.bn(h)), p=self.dropout, training=self.training)
        h = self.self2(h) + self.neigh2(self.aggregate(h))
        return torch.log_softmax(h[idx], dim=-1)


def build_model(info):
    model = SAGE(info["x"], info["edge_index"], info["num_nodes"], info["x"].shape[1], 128,
                 info["num_classes"], 0.5)
    return model.to(info["device"])


# Optimizer: the suite's Adam (its ReduceLROnPlateau scheduler is never stepped there, so none here).
LEARNING_RATE = 0.01


def build_optimizer(model, total_steps):
    return torch.optim.Adam(model.parameters(), lr=LEARNING_RATE), None


def training_step(model, batch, step):
    return F.nll_loss(model(batch["idx"]), batch["y"])


def predict_logits(model, batch):
    return model(batch["idx"])
