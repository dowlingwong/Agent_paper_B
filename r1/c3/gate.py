"""R1-BX-D8 aggregate C3 gate (M11), version 3.1: statistic on already computed utilities.

Synthetic-tested implementation; AI-assisted. It is not an author decision and it opens nothing before the D8
confirmation check passes.

Version 3.1 (PRE-WDBC option B of the sweep-2 analysis preregistration; R1-S2C3B-WDBC) differs from version 3
(``r1/c3/gate.py`` @ ``6aa9985c``, sha256 ``ffb70d7a…``) only in the T0 layout check: the input declares the T0 node set
it carries (``"t0_nodes"``, a subset of ``T0_NODES``, possibly empty, e.g. for a leave-one-suite-out fold), the gate
STOPs unless the T0 nodes supplied are exactly that set, and it records the set in its output
(``protocol.declared_t0_nodes``). With all eight T0 nodes declared its output is version 3's, except the gate version,
the gate sha256, the schema strings and that field. Everything below is version 3's text, read with "the declared T0
set" for "the eight T0 nodes" in the node layout.

Version 3 implements the author rows R1-BX-D8-V3-A (items 1-3) and R1-BX-D8-V3-B (items 4-5), on top of R1-BX-D8 and
R1-BX-PROPOSED-CONFIRM (D8). What it computes:

* per node, gap closed G = mean(a) / mean(d) on the node's test instances, with a = U_arm - U_A2 and
  d = U_oracle - U_A2 per test instance, where U_oracle is the noisy-oracle ceiling. This is the ratio of means
  (mean U_arm - mean U_A2) / (mean U_oracle - mean U_A2) of gate v2;
* IQM-eligibility (V3-A item 2, V3-B item 5). A node is IQM-eligible only if all of:
  - the paired z of oracle - A2 over its train + dev instances is at least ``ELIG_Z_MIN`` = 3 (replacing v2's
    dev z >= 6, not adopted on 14 Nov);
  - its dev denominator mean U_oracle - mean U_A2 on the dev split is at least ``delta_n`` (R1-BX-D8);
  - it has at least ``TEST_FLOOR[tier]`` test instances (T0 >= 9, T1 >= 3; V3-B item 5).
  An ineligible node is excluded from the IQM, listed with every reason that applies, and kept in the probability
  of improvement (PoI);
* IQM of gap closed across the eligible nodes: the 25%-75% empirical trimmed mean with fractional boundary weights
  (``_node_iqm``, inlined so that the gate SHA binds it; identical to the accepted
  ``d8_point_statistics.node_iqm``);
* PoI: per node the share of test instances with U_arm > U_A2, ties (exact floating-point equality) one half, then
  the plain mean over all nodes, eligible or not;
* node-stratified bootstrap: 2,000 resamples of test instances within each node, one shared index draw per node and
  resample for A2, oracle, A3 and A5; nodes are fixed, so the bounds cover instance noise for these nodes only;
* test side (V3-A item 1, "V1n"): a nonpositive point test denominator mean(d) on an IQM-eligible node is a STOP. A
  resample in which an eligible node's denominator is nonpositive sets that node's gap closed to -inf before the
  IQM; it is counted and reported, never dropped;
* pass rule (V3-B item 4, "(b2)"): the studentized node-stratified bootstrap lower bound of the IQM, as declared in
  ``M11_D8_SKEW_DECLARATION_20261115.md`` section 2 (b2) and implemented in ``r1/scripts/d8_skew_sim.py`` @
  ``dc899aad``:
  - per node, the delta-method se of the ratio,
    se_j^2 = [var(a) + G_j^2 var(d) - 2 G_j cov(a, d)]^+ / (n_j mean(d)^2), with ddof 1;
  - se(IQM) = sqrt(sum_i w_i^2 se_(i)^2), the IQM weights applied in the sorted order of G;
  - t* = (IQM* - IQM_hat) / se*(IQM), with se* computed the same way inside each resample; a resample with a
    nonpositive eligible-node denominator, se* = 0 or a non-finite t* counts as t* = +inf (so item 1's -inf has no
    further effect on the bound);
  - lower bound at level L = IQM_hat - q_L(t*) se_hat(IQM), with q_L the linear quantile of t*; if
    se_hat(IQM) = 0 the bound is IQM_hat;
  an arm passes at level L if this bound is > 0 **and** the percentile lower bound of the PoI is > 0.5 (both
  strict);
* decision: Holm over A3 and A5 at family-wise one-sided alpha = 0.05; the first-ranked arm is tested at L = 97.5%,
  the second (only if the first passes) at L = 95%. The gate passes if the first-ranked arm passes. The point IQM is
  reported against 0.1.

Node layout (pinned here, so the gate SHA binds it):

* tier T0 is drawn from the eight CPU nodes of ``T0_NODES``: the authorized sweep-1 node set (R1-DT-PIN-SWEEP1;
  docs/r1/authorizations/c3_sweep1_20261027.md), in which openml_climate substitutes for openml_blood_transfusion,
  which failed D21 (R1-D28-REPAIR). The input declares which of them it carries (``"t0_nodes"``, v3.1); the supplied
  T0 nodes must be exactly the declared set. T0 nodes belong to no suite (``"suite": null``). A declared node outside
  ``T0_NODES``, and a missing, extra or renamed T0 node against the declared set, is a STOP;
* tier T1 nodes carry a suite from ``SUITES`` (R1-BX-D2 as amended by R1-1GC-FALLBACK). A T1 node without a suite or
  with another suite is a STOP. The T1 node list itself cannot be pinned (partial T1, R1-B7-PARTIAL-T1);
* partial T1 (R1-B7-PARTIAL-T1): the condition "each suite in ``SUITES`` has at least one labelled T1 node" is a
  precondition of each leave-one-suite-out fold and is applied where leave-one-suite-out is computed (not in this
  module). The aggregate gate does **not** STOP on it; it reports ``t1_by_suite`` and the suites without a labelled
  T1 node.

Split (V3-A item 3): the caller supplies each node's train, dev and test instances under the split P3 = 1/3 : 1/6 :
1/2 per tier, fixed in the analysis preregistration. The input must declare ``"split"`` exactly as ``SPLIT``, and a
node's three instance-id lists must be pairwise disjoint. The gate reports each node's counts and its total against
the design size (T0 18, T1 12 instances per node; R1-BX-D8-V3-B fixes T1 at 12), and lists under ``off_split`` every
node at the design size whose train : dev : test counts are not exactly P3 (T0 6 : 3 : 9, T1 4 : 2 : 6). It does not
STOP on counts: a short node is handled by the test floor.

Implementation conventions that the PLAN rows do not fix (preregistration candidates; see
docs/r1/reports/M11_D8_GATE_V3_20261116.md):

* environment: the harness ``uv.lock`` environment at ``a3fedbb`` (Python 3.13, NumPy 2.4.4). Only the NumPy version
  is checked;
* seed 20261108, ``numpy.random.Generator(PCG64)``; NumPy must be exactly ``NUMPY_VERSION`` (STOP otherwise); nodes in
  sorted node-id order, test instances in sorted instance-id order; for each node in that order one
  ``integers(0, n, size=(2000, n))`` draw (unchanged from v2);
* PoI lower bound at level L = ``numpy.quantile(poi*, 1 - L, method='linear')`` (unchanged from v2); the t* quantile
  q_L = ``numpy.quantile(t*, L, method='linear')`` over the 2,000 resamples. As in the simulation, t* = +inf is held
  as ``TSTAR_INF`` = 1e12, so the bound equals the simulation's bound. With a nonnegligible se_hat(IQM), more than
  (1 - L) of screened resamples drives the bound far below 0, as +inf would; only when se_hat(IQM) is of order 1e-12
  of the bound (e.g. rounding noise on constant data) does the sentinel differ from a literal +inf;
* ties in G: nodes are put in ascending G order with a stable sort over sorted node ids, so tied nodes keep node-id
  order when the weights are paired with their se. The simulation used NumPy's default ``np.argsort``, which is not
  stable on every platform, so with exactly tied G its se can differ from the gate's; without ties the two agree;
* arm ranking for Holm: an arm that passes at the first level (97.5%) ranks before one that does not; then ascending
  composite tail share max(P*(t* >= IQM_hat / se_hat), P*(PoI* <= 0.5)) (for se_hat = 0 the first term is 0 if
  IQM_hat > 0 and 1 otherwise); then the fixed order A3, A5. The first key is the pass test itself, so the verdict
  does not depend on arm labels;
* train + dev z: d = oracle - A2 paired per instance over the train and dev instances together,
  z = mean(d) / (sd(d, ddof=1) / sqrt(n)); train and dev are each nonempty, so n >= 2. If sd(d) = 0, z is +inf when mean(d) > 0 (eligible on this criterion) and the node is ineligible
  otherwise; z is then reported as null with ``z_sd_zero`` true. A z of exactly 3 is eligible. The reasons
  ``delta_n``, ``z`` and ``test_floor`` are listed for every ineligible node (several may apply);
* no IQM-eligible node is a STOP (the IQM is undefined);
* T0 and T1 are pooled with tier as a stratum: every node lies in one tier and resampling is within node; per-tier
  node counts and descriptive point statistics are reported.

Inputs are the caller's responsibility: U is the one-step utility scaled to a 20-run campaign (20 proposals,
R1-T4-PROOF-CHECK R4); ``delta_n`` is the node's D18 delta_n in the same units as U; the oracle utility comes from the
label-seed block only, test utilities from the evaluation block, and the train and dev arrays from their splits.
This module does not compute or verify those provenance properties or units. The gate's power is not computed here;
R1-BX-D8-V3-B asks that it be reported in the paper (D8-PASS: mean two-arm power 0.36 at g = 0.3 on T1 x 12).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

from r1.c3 import analysis_guard

CONFIRM_ID = 'R1-BX-D8-CONFIRM'
GATE_VERSION = '3.1'           # v3 (6aa9985c) plus a declared T0 node set (PRE-WDBC B)
INPUT_SCHEMA = 'r1_d8_gate_input/v3.1'
OUTPUT_SCHEMA = 'r1_d8_gate_result/v3.1'
NUMPY_VERSION = '2.4.4'         # harness uv.lock pin; STOP on any other version
ENVIRONMENT = 'harness uv.lock environment at a3fedbb (Python 3.13, NumPy 2.4.4)'   # recorded, not checked
ELIG_Z_MIN = 3.0                # V3-A item 2: paired z of oracle - A2 on train + dev, with delta_n on dev
TEST_FLOOR = {'T0': 9, 'T1': 3}         # V3-B item 5: test instances per node, per tier
SPLIT = {'name': 'P3', 'train': '1/3', 'dev': '1/6', 'test': '1/2'}   # V3-A item 3 (caller supplies it)
DESIGN_INSTANCES = {'T0': 18, 'T1': 12}  # reported only; V3-B fixes T1 at 12 per node
# P3 counts at the design size (exact: 18 and 12 are divisible by 6); reported only, as ``off_split``.
DESIGN_SPLIT = {t: tuple(n * num // den for num, den in ((1, 3), (1, 6), (1, 2))) for t, n in DESIGN_INSTANCES.items()}
INTERVAL = 'studentized node-stratified bootstrap (b2), delta-method se'   # V3-B item 4
TSTAR_INF = 1e12                # the value standing for t* = +inf, as in d8_skew_sim.py (BIG)
N_RESAMPLES = 2000
SEED = 20261108
RNG = 'numpy.random.Generator(PCG64)'
QUANTILE_METHOD = 'linear'
FAMILY_ALPHA = 0.05
LEVELS = (0.975, 0.95)          # Holm: first-ranked arm, second-ranked arm
PRACTICAL_SIZE = 0.1
POI_NULL = 0.5
ARMS = ('A3', 'A5')             # fixed order; also the tie-break for ranking
TIERS = ('T0', 'T1')
SERIES = ('A2', 'oracle', 'A3', 'A5')
SPLITS = ('train', 'dev', 'test')
# Tier T0: the 8 CPU nodes of the authorized sweep 1 (R1-DT-PIN-SWEEP1, 27 Oct;
# docs/r1/authorizations/c3_sweep1_20261027.md; R1-BX-D2 "the 8 CPU nodes stay as
# tier T0"). openml_climate substitutes for openml_blood_transfusion (failed D21;
# R1-D28-REPAIR). Same set as the evidence classifier and the deepthought config.
T0_NODES = ('digits_mlp', 'openml_breast_w', 'openml_climate', 'openml_credit_approval',
            'openml_ionosphere', 'openml_sonar', 'openml_wdbc', 'tabular_mlp')
# T1 suites: R1-BX-D2 as amended by R1-1GC-FALLBACK (MLAgentBench replaces 1GC-7RC).
SUITES = ('autoresearch', 'MLAgentBench', 'MLGym')


class GateStop(RuntimeError):
    """A predeclared STOP: the gate is not read and nothing is dropped."""


def gate_file_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _require_pins():
    """STOP unless this file is the gate the D8 check bound and NumPy is pinned."""
    bound = Path(analysis_guard.REPO) / 'r1/c3/gate.py'
    here = Path(__file__)
    try:
        same = here.resolve() == bound.resolve() and here.read_bytes() == bound.read_bytes()
    except OSError:
        same = False
    if not same:
        raise GateStop('STOP: the executing gate file is not r1/c3/gate.py of the checked repository')
    if np.__version__ != NUMPY_VERSION:
        raise GateStop(f'STOP: NumPy {np.__version__} is not the pinned NumPy {NUMPY_VERSION}')


# ------------------------------------------- point statistics (inlined, bound)

def _node_iqm(gap_closed):
    """25%-trimmed mean with fractional weights at empirical quantile edges.

    Same arithmetic as the accepted ``d8_point_statistics.node_iqm``; inlined
    so that the confirmed gate SHA covers it.
    """
    values = sorted(_finite_list(gap_closed, 'node gap closed'))
    n = len(values)
    # Work in quarter-observation units to avoid floating cut-point rounding.
    lower, upper = n, 3 * n
    total = 0.0
    for i, value in enumerate(values):
        weight = max(0, min(4 * (i + 1), upper) - max(4 * i, lower))
        total += value * weight
    result = total / (2 * n)
    if not math.isfinite(result):
        raise ValueError('IQM overflow')
    return result


def _node_poi(nodes):
    """Average node-level win rates; ties count one half, nodes equally.

    Same arithmetic as the accepted
    ``d8_point_statistics.node_equal_probability_of_improvement``; inlined.
    """
    if not isinstance(nodes, (list, tuple)) or not nodes:
        raise ValueError('nodes must be a nonempty sequence')
    node_rates = []
    for pair in nodes:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError('each node needs arm and baseline values')
        arm = _finite_list(pair[0], 'arm utility')
        baseline = _finite_list(pair[1], 'baseline utility')
        if len(arm) != len(baseline):
            raise ValueError('paired node observations differ in length')
        score = sum(1.0 if a > b else 0.5 if a == b else 0.0
                    for a, b in zip(arm, baseline))
        node_rates.append(score / len(arm))
    return sum(node_rates) / len(node_rates)


# ----------------------------------------------------------------- validation

def _finite_list(values, label):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f'{label} must be a nonempty list')
    for v in values:
        if type(v) not in (int, float):
            raise ValueError(f'{label} contains a non-numeric value')
        try:
            ok = math.isfinite(v)
        except OverflowError:
            ok = False
        if not ok:
            raise ValueError(f'{label} contains a non-finite value')
    return list(values)


def _finite_vector(values, label):
    array = np.asarray(_finite_list(values, label), dtype=float)
    # Bound every resampled sum and every difference of two means: 4 n max|v|
    # finite means no mean, resampled mean or mean difference can overflow.
    if not math.isfinite(4.0 * len(array) * float(np.max(np.abs(array)))):
        raise ValueError(f'{label} is too large in magnitude for finite means')
    return array


def _text(value, label):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f'{label} must be a nonempty string without outer spaces')
    return value


def _ids(raw, label):
    if not isinstance(raw, list) or not raw:
        raise ValueError(f'{label} instance_ids must be a nonempty list')
    ids = [_text(i, f'{label} instance id') for i in raw]
    if len(set(ids)) != len(ids):
        raise ValueError(f'{label} has duplicate instance ids')
    return ids


def _paired_block(raw, keys, label):
    """Validate one split block: instance_ids plus the paired series in ``keys``."""
    if not isinstance(raw, dict) or set(raw) != {'instance_ids', *keys}:
        raise ValueError(f'{label} must have exactly instance_ids, {", ".join(keys)}')
    ids = _ids(raw['instance_ids'], label)
    series = {k: _finite_vector(raw[k], f'{label} {k}') for k in keys}
    if any(len(v) != len(ids) for v in series.values()):
        raise ValueError(f'{label} vectors are not paired with instance_ids')
    order = sorted(range(len(ids)), key=ids.__getitem__)
    return [ids[i] for i in order], {k: v[order] for k, v in series.items()}


def _validate(gate_input):
    if not isinstance(gate_input, dict) or gate_input.get('schema') != INPUT_SCHEMA:
        raise ValueError(f'gate input must be a dict with schema {INPUT_SCHEMA}')
    extra = set(gate_input) - {'schema', 'split', 't0_nodes', 'nodes'}
    if extra:
        raise ValueError(f'unknown gate input fields: {sorted(extra)}')
    declared = _declared_t0(gate_input.get('t0_nodes'))
    if gate_input.get('split') != SPLIT:
        raise GateStop(f'STOP: the declared split must be exactly {SPLIT} (R1-BX-D8-V3-A item 3); '
                       f'got {gate_input.get("split")!r}')
    raw_nodes = gate_input.get('nodes')
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError('nodes must be a nonempty list')
    nodes = {}
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            raise ValueError('each node must be a dict')
        if set(raw) != {'node', 'suite', 'tier', 'delta_n', 'train', 'dev', 'test'}:
            raise ValueError(f'node fields must be exactly node, suite, tier, delta_n, train, dev, test; '
                             f'got {sorted(raw)}')
        name = _text(raw.get('node'), 'node id')
        if name in nodes:
            raise ValueError(f'duplicate node id {name}')
        suite = raw.get('suite')
        if suite is not None:
            suite = _text(suite, 'suite')
        tier = raw.get('tier')
        if tier not in TIERS:
            raise ValueError(f'node {name} tier must be one of {TIERS}')
        delta = raw.get('delta_n')
        if type(delta) not in (int, float) or not math.isfinite(delta) or delta <= 0:
            raise ValueError(f'node {name} delta_n must be a positive finite number')
        train_ids, train = _paired_block(raw.get('train'), ('A2', 'oracle'), f'node {name} train')
        dev_ids, dev = _paired_block(raw.get('dev'), ('A2', 'oracle'), f'node {name} dev')
        test_ids, test = _paired_block(raw.get('test'), SERIES, f'node {name} test')
        overlap = sorted((set(train_ids) & set(dev_ids)) | (set(train_ids) & set(test_ids))
                         | (set(dev_ids) & set(test_ids)))
        if overlap:
            raise ValueError(f'node {name}: train, dev and test instance ids must be disjoint; shared {overlap}')
        dev_denominator = float(dev['oracle'].mean() - dev['A2'].mean())
        if not math.isfinite(dev_denominator):
            raise ValueError(f'node {name} dev denominator is not finite')
        z, z_sd_zero, z_ok = _train_dev_z(np.concatenate([train['A2'], dev['A2']]),
                                               np.concatenate([train['oracle'], dev['oracle']]))
        n_test = len(test_ids)
        reasons = (([] if dev_denominator >= float(delta) else ['delta_n'])
                   + ([] if z_ok else ['z'])
                   + ([] if n_test >= TEST_FLOOR[tier] else ['test_floor']))
        n_total = len(train_ids) + len(dev_ids) + n_test
        nodes[name] = {
            'suite': suite, 'tier': tier, 'delta_n': float(delta),
            'dev_denominator': dev_denominator,
            'train_dev_z': z, 'z_sd_zero': z_sd_zero,
            'ineligible_reasons': reasons,
            'n_train': len(train_ids), 'n_dev': len(dev_ids), 'n_test': n_test, 'n_total': n_total,
            'test': test,
        }
    _check_layout(nodes, declared)
    return dict(sorted(nodes.items()))


def _declared_t0(raw):
    """The declared T0 node set (v3.1): a list of distinct T0_NODES members, possibly empty; returned sorted."""
    if not isinstance(raw, list) or any(not isinstance(k, str) for k in raw):
        raise ValueError('t0_nodes must be a list of node ids (the declared T0 node set)')
    if len(set(raw)) != len(raw):
        raise ValueError('t0_nodes has duplicate node ids')
    outside = sorted(set(raw) - set(T0_NODES))
    if outside:
        raise GateStop(f'STOP: the declared T0 node set must be a subset of {sorted(T0_NODES)}; outside it {outside}')
    return sorted(raw)


def _check_layout(nodes, declared):
    """STOP unless the node set matches the declared T0 set and the pinned layout (nothing dropped silently)."""
    t0 = sorted(k for k, n in nodes.items() if n['tier'] == 'T0')
    if t0 != declared:
        raise GateStop(f'STOP: T0 nodes must be exactly the declared set {declared}; missing '
                       f'{sorted(set(declared) - set(t0))}, unexpected {sorted(set(t0) - set(declared))}')
    relabelled = sorted(k for k in nodes if k in T0_NODES and k not in declared)
    if relabelled:
        raise GateStop(f'STOP: {relabelled} are T0 nodes (T0_NODES) supplied in another tier but not declared; '
                       'a T0 node is never relabelled (R1-S2C3B-WDBC)')
    t0_with_suite = sorted(k for k in t0 if nodes[k]['suite'] is not None)
    if t0_with_suite:
        raise GateStop(f'STOP: T0 nodes belong to no suite; suite given for {t0_with_suite}')
    t1 = [k for k, n in nodes.items() if n['tier'] == 'T1']
    bad = sorted(k for k in t1 if nodes[k]['suite'] not in SUITES)
    if bad:
        raise GateStop(f'STOP: T1 nodes without a suite in {list(SUITES)}: {bad}')
    # A suite without a labelled T1 node is reported, not a STOP: the per-suite rule of
    # R1-B7-PARTIAL-T1 belongs to leave-one-suite-out (Q1 option (b)).


def _train_dev_z(a2, oracle):
    """Paired z of oracle - A2 over train + dev; returns (z or None, sd_zero, eligible_on_z).

    Train and dev are each nonempty (validated), so n >= 2.
    """
    d = oracle - a2
    n = len(d)
    mean = float(d.mean())
    sd = float(d.std(ddof=1))
    if not math.isfinite(mean) or not math.isfinite(sd):
        raise ValueError('train + dev z is not finite')
    if sd == 0.0:
        return None, True, mean > 0.0
    z = mean / (sd / math.sqrt(n))
    if not math.isfinite(z):
        raise ValueError('train + dev z is not finite')
    return z, False, z >= ELIG_Z_MIN


# ---------------------------------------------------------------- statistics

def _wins(arm, a2):
    return (arm > a2).astype(float) + 0.5 * (arm == a2)


def _iqm_weights(k):
    """The IQM weights of ``_node_iqm`` on the sorted order, as an array (sum 1)."""
    return np.array([max(0, min(4 * (i + 1), 3 * k) - max(4 * i, k)) for i in range(k)], dtype=float) / (2 * k)


def _node_se(a, d, g):
    """Delta-method se of the ratio mean(a)/mean(d) along the last axis (d8_skew_sim ``node_se``, ddof 1)."""
    n = a.shape[-1]
    va = a.var(axis=-1, ddof=1)
    vd = d.var(axis=-1, ddof=1)
    cv = ((a - a.mean(axis=-1, keepdims=True)) * (d - d.mean(axis=-1, keepdims=True))).sum(axis=-1) / (n - 1)
    num = np.maximum(va + g ** 2 * vd - 2 * g * cv, 0.0)
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.sqrt(num / (n * d.mean(axis=-1) ** 2))


def _point(nodes):
    eligible = [k for k, n in nodes.items() if not n['ineligible_reasons']]
    if not eligible:
        reasons = {k: n['ineligible_reasons'] for k, n in nodes.items()}
        raise GateStop(f'STOP: no node is IQM-eligible (train + dev z >= {ELIG_Z_MIN}, dev denominator >= delta_n, '
                       f'test floor {TEST_FLOOR}); the IQM is undefined; reasons {reasons}')
    table = {}
    nonpositive = []
    for name, n in nodes.items():
        t = n['test']
        d = t['oracle'] - t['A2']
        denom = float(d.mean())
        row = {'suite': n['suite'], 'tier': n['tier'], 'delta_n': n['delta_n'],
               'n_train': n['n_train'], 'n_dev': n['n_dev'], 'n_test': n['n_test'], 'n_total': n['n_total'],
               'design_instances': DESIGN_INSTANCES[n['tier']], 'test_floor': TEST_FLOOR[n['tier']],
               'dev_denominator': n['dev_denominator'],
               'train_dev_z': n['train_dev_z'], 'z_sd_zero': n['z_sd_zero'],
               'ineligible_reasons': list(n['ineligible_reasons']),
               'included_in_iqm': name in eligible, 'test_denominator': denom}
        if name in eligible and not denom > 0:
            nonpositive.append(name)
            continue
        for arm in ARMS:
            if name in eligible:
                a = t[arm] - t['A2']
                g = float(a.mean()) / denom
                row[f'gap_closed_{arm}'] = g
                row[f'se_gap_closed_{arm}'] = float(_node_se(a, d, g))
            else:
                row[f'gap_closed_{arm}'] = None
                row[f'se_gap_closed_{arm}'] = None
            row[f'poi_{arm}'] = float(_wins(t[arm], t['A2']).mean())
        table[name] = row
    if nonpositive:
        raise GateStop(f'STOP: nonpositive test oracle-A2 denominator on IQM nodes {nonpositive}')
    summary = {}
    w = _iqm_weights(len(eligible))
    for arm in ARMS:
        g = np.array([table[k][f'gap_closed_{arm}'] for k in eligible])
        se = np.array([table[k][f'se_gap_closed_{arm}'] for k in eligible])
        order = np.argsort(g, kind='stable')
        summary[arm] = {
            'iqm_gap_closed': _node_iqm(g.tolist()),
            'se_iqm_gap_closed': float(np.sqrt(np.sum((w * se[order]) ** 2))),
            'probability_of_improvement': _node_poi(
                [(nodes[k]['test'][arm].tolist(), nodes[k]['test']['A2'].tolist()) for k in nodes]),
        }
    return eligible, table, summary


def _bootstrap(nodes, eligible, summary):
    """Per arm: t* (with +inf for screened resamples) and the PoI resamples, from shared within-node draws.

    Also returns, per eligible node, the number of resamples with a nonpositive denominator (V1n: gap closed -inf).
    """
    rng = np.random.Generator(np.random.PCG64(SEED))
    k = len(eligible)
    col = {name: j for j, name in enumerate(eligible)}
    g_b = {arm: np.empty((N_RESAMPLES, k)) for arm in ARMS}
    se_b = {arm: np.empty((N_RESAMPLES, k)) for arm in ARMS}
    bad = np.zeros((N_RESAMPLES, k), dtype=bool)
    poi = {arm: np.zeros(N_RESAMPLES) for arm in ARMS}
    for name, n in nodes.items():          # sorted node-id order
        t = n['test']; size = n['n_test']
        idx = rng.integers(0, size, size=(N_RESAMPLES, size))
        for arm in ARMS:
            poi[arm] += _wins(t[arm], t['A2'])[idx].mean(axis=1)
        if name in col:
            j = col[name]
            db = (t['oracle'] - t['A2'])[idx]
            dm = db.mean(axis=1)
            bad[:, j] = ~(dm > 0)
            for arm in ARMS:
                ab = (t[arm] - t['A2'])[idx]
                with np.errstate(divide='ignore', invalid='ignore'):
                    gb = np.where(dm > 0, ab.mean(axis=1) / dm, 0.0)
                g_b[arm][:, j] = np.where(dm > 0, gb, -np.inf)
                se_b[arm][:, j] = _node_se(ab, db, gb)
    w = _iqm_weights(k)
    out = {}
    for arm in ARMS:
        theta = summary[arm]['iqm_gap_closed']
        gm = g_b[arm]
        ordb = np.argsort(gm, axis=1, kind='stable')
        g_sorted = np.take_along_axis(gm, ordb, axis=1)
        se_sorted = np.take_along_axis(se_b[arm], ordb, axis=1)
        ok = ~bad.any(axis=1)
        iqm = np.full(N_RESAMPLES, -np.inf)
        iqm[ok] = g_sorted[ok] @ w
        se_iqm = np.full(N_RESAMPLES, np.nan)
        se_iqm[ok] = np.sqrt(np.sum((w * se_sorted[ok]) ** 2, axis=1))
        with np.errstate(divide='ignore', invalid='ignore'):
            tstar = (iqm - theta) / se_iqm
        screened = ~ok | ~(se_iqm > 0) | ~np.isfinite(tstar)
        tstar = np.where(screened, TSTAR_INF, tstar)
        out[arm] = {'theta': theta, 'se_hat': summary[arm]['se_iqm_gap_closed'], 'tstar': tstar,
                    'poi': poi[arm] / len(nodes), 'infinite_tstar': int(np.count_nonzero(screened))}
    nonpositive = {name: int(np.count_nonzero(bad[:, col[name]])) for name in eligible}
    return out, nonpositive


def _upper_quantile(t, level):
    """numpy's linear quantile of t* at ``level`` (screened resamples hold ``TSTAR_INF``)."""
    return float(np.quantile(t, level, method=QUANTILE_METHOD))


def _lower_poi(poi, level):
    return float(np.quantile(poi, 1.0 - level, method=QUANTILE_METHOD))


def _lower_iqm(b, level):
    """Studentized lower bound IQM_hat - q_L(t*) se_hat; IQM_hat itself when se_hat = 0 (as in the simulation)."""
    if not b['se_hat'] > 0:
        return b['theta']
    return b['theta'] - _upper_quantile(b['tstar'], level) * b['se_hat']


def _passes(b, level):
    """The pass test for one arm at one level (both bounds, strict)."""
    return _lower_iqm(b, level) > 0.0 and _lower_poi(b['poi'], level) > POI_NULL


def _tail_iqm(b):
    """Share of resamples at which the studentized bound would reach 0 (ranking only)."""
    if not b['se_hat'] > 0:
        return 0.0 if b['theta'] > 0 else 1.0
    return float(np.mean(b['tstar'] >= b['theta'] / b['se_hat']))


def _holm_decision(boot):
    """Holm step-down over the two arms with the studentized IQM bound and the PoI bound.

    ``boot`` maps each arm to its bootstrap summary (theta, se_hat, t*, PoI*). The ranking key starts with the
    first-level pass test itself, so an arm that passes at 97.5% always ranks first: the verdict is "some arm passes
    at 97.5%" and cannot depend on arm labels. The composite tail share and the fixed order only order arms that
    agree on that test.
    """
    ranking = []
    for arm in ARMS:
        b = boot[arm]
        p_iqm = _tail_iqm(b); p_poi = float(np.mean(b['poi'] <= POI_NULL))
        first_level_pass = _passes(b, LEVELS[0])
        ranking.append((not first_level_pass, max(p_iqm, p_poi), ARMS.index(arm), arm, p_iqm, p_poi))
    ranking.sort()
    arms = {}
    still_testing = True
    for rank, (_, p_comp, _, arm, p_iqm, p_poi) in enumerate(ranking):
        level = LEVELS[rank]
        b = boot[arm]
        lb_iqm, lb_poi = _lower_iqm(b, level), _lower_poi(b['poi'], level)
        if still_testing:
            passed = lb_iqm > 0.0 and lb_poi > POI_NULL
            tested = True
        else:
            passed, tested = False, False
        arms[arm] = {'rank': rank + 1, 'level': level, 'tested': tested, 'passed': passed,
                     'lower_iqm_gap_closed': lb_iqm, 'lower_probability_of_improvement': lb_poi,
                     'tstar_quantile': (_upper_quantile(b['tstar'], level) if b['se_hat'] > 0 else None),
                     'resamples_with_infinite_tstar': b['infinite_tstar'],
                     'ranking_p_iqm': p_iqm, 'ranking_p_poi': p_poi, 'ranking_p_composite': p_comp}
        still_testing = still_testing and passed
    first = ranking[0][3]
    return arms, first, arms[first]['passed']


def _tier_descriptive(nodes, table, eligible):
    out = {}
    for tier in TIERS:
        names = [k for k in nodes if nodes[k]['tier'] == tier]
        elig = [k for k in names if k in eligible]
        row = {'n_nodes': len(names), 'n_iqm_nodes': len(elig)}
        for arm in ARMS:
            row[f'iqm_gap_closed_{arm}'] = (_node_iqm([table[k][f'gap_closed_{arm}'] for k in elig])
                                            if elig else None)
            row[f'poi_{arm}'] = (float(np.mean([table[k][f'poi_{arm}'] for k in names]))
                                 if names else None)
        out[tier] = row
    return out


def _evaluate(gate_input):
    _require_pins()
    nodes = _validate(gate_input)
    declared = _declared_t0(gate_input['t0_nodes'])      # validated in _validate
    eligible, table, summary = _point(nodes)
    boot, nonpositive = _bootstrap(nodes, eligible, summary)
    arms, first, passed = _holm_decision(boot)
    for arm in ARMS:
        arms[arm].update(summary[arm])
        arms[arm]['meets_practical_size'] = summary[arm]['iqm_gap_closed'] >= PRACTICAL_SIZE
    for name in eligible:
        table[name]['resamples_nonpositive_denominator'] = nonpositive[name]
    return {
        'schema': OUTPUT_SCHEMA,
        'gate_version': GATE_VERSION,
        'verdict': 'PASS' if passed else 'FAIL',
        'first_ranked_arm': first,
        'arms': arms,
        'nodes': table,
        'excluded_from_iqm': [k for k in nodes if k not in eligible],
        'ineligible_nodes': {k: list(nodes[k]['ineligible_reasons']) for k in nodes if k not in eligible},
        'below_test_floor': [k for k in nodes if 'test_floor' in nodes[k]['ineligible_reasons']],
        'off_design_size': {k: {'n_total': nodes[k]['n_total'], 'design': DESIGN_INSTANCES[nodes[k]['tier']]}
                            for k in nodes if nodes[k]['n_total'] != DESIGN_INSTANCES[nodes[k]['tier']]},
        'off_split': {k: {'counts': [nodes[k]['n_train'], nodes[k]['n_dev'], nodes[k]['n_test']],
                          'p3': list(DESIGN_SPLIT[nodes[k]['tier']])}
                      for k in nodes if nodes[k]['n_total'] == DESIGN_INSTANCES[nodes[k]['tier']]
                      and (nodes[k]['n_train'], nodes[k]['n_dev'], nodes[k]['n_test']) != DESIGN_SPLIT[nodes[k]['tier']]},
        't1_suites_without_labelled_node': [s for s in SUITES if not any(
            n['tier'] == 'T1' and n['suite'] == s for n in nodes.values())],
        'node_counts': {'total': len(nodes),
                        'by_tier': {t: sum(n['tier'] == t for n in nodes.values()) for t in TIERS},
                        't1_by_suite': {s: sum(n['tier'] == 'T1' and n['suite'] == s
                                               for n in nodes.values()) for s in SUITES}},
        'tier_descriptive': _tier_descriptive(nodes, table, eligible),
        'protocol': {'gate_version': GATE_VERSION, 'interval': INTERVAL,
                     'resamples': N_RESAMPLES, 'seed': SEED, 'rng': RNG,
                     'numpy_version': np.__version__, 'numpy_pin': NUMPY_VERSION,
                     'environment': ENVIRONMENT, 'elig_z_min': ELIG_Z_MIN,
                     'test_floor': dict(TEST_FLOOR), 'split': dict(SPLIT),
                     'design_instances': dict(DESIGN_INSTANCES),
                     'design_split': {t: list(v) for t, v in DESIGN_SPLIT.items()},
                     'quantile_method': QUANTILE_METHOD, 'tstar_inf': TSTAR_INF,
                     't0_nodes': list(T0_NODES), 'declared_t0_nodes': declared, 'suites': list(SUITES),
                     'family_alpha': FAMILY_ALPHA, 'levels': list(LEVELS),
                     'practical_size': PRACTICAL_SIZE, 'arms': list(ARMS),
                     'gate_sha256': gate_file_sha256()},
    }


# --------------------------------------------------------------- entry points

def evaluate(gate_input):
    """Run the gate on an in-memory input after the D8 confirmation check."""
    analysis_guard.require_d8_confirmation()
    _require_pins()
    return _evaluate(gate_input)


def _no_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f'duplicate JSON key {key!r} in gate input')
        out[key] = value
    return out


def _no_constant(name):
    raise ValueError(f'non-finite JSON constant {name} in gate input')


def load_and_evaluate(path):
    """Check D8 confirmation, pins and sealed paths before opening the input file."""
    analysis_guard.require_d8_confirmation()
    _require_pins()
    analysis_guard.refuse_sealed(path)
    with open(path, encoding='utf-8') as handle:
        gate_input = json.load(handle, object_pairs_hook=_no_duplicate_keys, parse_constant=_no_constant)
    return _evaluate(gate_input)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print('usage: python -m r1.c3.gate GATE_INPUT.json', file=sys.stderr)
        return 2
    print(json.dumps(load_and_evaluate(argv[0]), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
