"""Does the incumbent's error screen off other configurations' errors? A check on the 22 Oct E1 runs. ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 22 Nov 2026). AI analysis, unreviewed. Input: the PILOT 30-seed noise-floor runs
`results/r1/pilot/E1_20261022T214606Z/runs.jsonl` (not yet accepted by the author; not evidence).

T4 Proposition 9 and T2 Proposition 4(a) assume that a candidate's error, given the history, depends only on the
incumbent's error e: eps | e ~ N(rho e, sigma_c^2). In a Gaussian model this is a screening (Markov) property:
the correlation between two configurations' errors, given the configuration between them, is zero.

Proxy tested here: the five E1 edits of each node are siblings of the default configuration c0. If c0's error
screens off the edits from each other, the partial correlation corr(a, b | c0) is zero. A shared component that
all configurations of a campaign carry, beyond what c0 carries, makes it positive. Joint-seed condition (training
and split seed vary together), which matches the CRN regime of a campaign. 30 seeds per configuration; bootstrap
over seeds (2,000 resamples). Pairs with |corr(., c0)| >= 0.999 are dropped (partial correlation undefined).
Run: python3 check_kernel_e1.py <runs.jsonl>
"""
import collections
import itertools
import json
import sys

import numpy as np


def stats(M):
    C = np.corrcoef(M)
    pairs = list(itertools.combinations(range(1, M.shape[0]), 2))
    part = [
        (C[a, b] - C[0, a] * C[0, b]) / np.sqrt((1 - C[0, a] ** 2) * (1 - C[0, b] ** 2))
        for a, b in pairs if abs(C[0, a]) < 0.999 and abs(C[0, b]) < 0.999
    ]
    cab = np.mean([C[a, b] for a, b in pairs])
    prod = np.mean([C[0, a] * C[0, b] for a, b in pairs])
    return C[0, 1:], cab, prod, (np.mean(part) if part else np.nan), len(part)


def main(path):
    data = collections.defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        if r["condition"] == "joint" and r["success"]:
            data[r["node"]][(r["config"], r["train_seed"], r["split_seed"])] = r["metric"]
    rng = np.random.default_rng(20261122)
    print("node | sd(c0) | corr(edit, c0) | mean corr(a,b) | mean product | partial corr(a,b|c0) [95% bootstrap] | pairs")
    for node in sorted(data):
        d = data[node]
        seeds = sorted({k[1:] for k in d})
        M = np.array([[d[(c,) + s] for s in seeds] for c in ("c0", "c1", "c2", "c3", "c4", "c5")])
        r0, cab, prod, part, n = stats(M)
        boots = []
        for _ in range(2000):
            Mb = M[:, rng.integers(0, M.shape[1], M.shape[1])]
            if Mb.std(axis=1).min() > 0:
                boots.append(stats(Mb)[3])
        lo, hi = np.nanpercentile(boots, [2.5, 97.5])
        print(f"{node} | {M[0].std(ddof=1):.4f} | {np.round(r0, 2).tolist()} | {cab:.2f} | {prod:.2f} | "
              f"{part:+.2f} [{lo:+.2f}, {hi:+.2f}] | {n}")


if __name__ == "__main__":
    main(sys.argv[1])
