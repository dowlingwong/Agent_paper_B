"""Gate v3.1 (PRE-WDBC option B): a declared T0 node set; v3's output on all eight nodes otherwise.

Synthetic only. The eight-node reproduction runs the frozen v3 file (``r1/tests/fixtures/gate_v3_6aa9985c.py``,
byte-identical to ``r1/c3/gate.py`` @ ``6aa9985c``, sha256 ``ffb70d7a…``) and v3.1 on the same random fixtures and
requires identical output except the gate version, the gate sha256, the schema strings and the declared node-set
field. No real label, audit value or table is read.
"""
import copy
import hashlib
import importlib.util
import math

import numpy as np
import pytest

from r1.c3 import gate
from r1.harness import REPO

V3_PATH = REPO / 'r1/tests/fixtures/gate_v3_6aa9985c.py'
V3_SHA = 'ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee'
T0 = sorted(gate.T0_NODES)


def load_v3():
    assert hashlib.sha256(V3_PATH.read_bytes()).hexdigest() == V3_SHA
    spec = importlib.util.spec_from_file_location('gate_v3_frozen', V3_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def pins(monkeypatch):
    v3 = load_v3()
    for mod in (gate, v3):
        monkeypatch.setattr(mod, '_require_pins', lambda: None)
        monkeypatch.setattr(mod, 'NUMPY_VERSION', np.__version__)
    monkeypatch.setattr(gate.analysis_guard, 'require_d8_confirmation', lambda: None)
    return v3


def block(name, split, rng, n, mu_d, arms=False):
    a2 = rng.normal(0.0, 1.0, n)
    oracle = a2 + mu_d + rng.normal(0.0, 0.5, n)
    out = {'instance_ids': [f'{name}-{split}{i:03d}' for i in range(n)], 'A2': a2.tolist(), 'oracle': oracle.tolist()}
    if arms:
        out['A3'] = (a2 + 0.3 * (oracle - a2) + rng.normal(0.0, 0.4, n)).tolist()
        out['A5'] = (a2 + 0.1 * (oracle - a2) + rng.normal(0.0, 0.4, n)).tolist()
    return out


def node(name, tier, suite, rng, n_test, mu_d=1.5):
    n_train, n_dev = (6, 3) if tier == 'T0' else (4, 2)
    return {'node': name, 'suite': suite, 'tier': tier, 'delta_n': 0.05,
            'train': block(name, 'r', rng, n_train, mu_d), 'dev': block(name, 'd', rng, n_dev, mu_d),
            'test': block(name, 't', rng, n_test, mu_d, arms=True)}


def fixture(seed, t0=T0, t1=(('ar1', 'autoresearch'), ('mlab1', 'MLAgentBench'), ('mlgym1', 'MLGym'))):
    rng = np.random.default_rng(seed)
    nodes = [node(k, 'T0', None, rng, 9) for k in t0] + [node(k, 'T1', s, rng, 6) for k, s in t1]
    return nodes


def v3_input(nodes):
    return {'schema': 'r1_d8_gate_input/v3', 'split': dict(gate.SPLIT), 'nodes': copy.deepcopy(nodes)}


def v31_input(nodes, declared=None):
    t0 = [n['node'] for n in nodes if n['tier'] == 'T0'] if declared is None else declared
    return {'schema': gate.INPUT_SCHEMA, 'split': dict(gate.SPLIT), 't0_nodes': list(t0), 'nodes': copy.deepcopy(nodes)}


def strip(result, fields):
    r = copy.deepcopy(result)
    for key in ('schema', 'gate_version'):
        r.pop(key)
    for key in ('gate_version', 'gate_sha256', *fields):
        r['protocol'].pop(key, None)
    return r


def same(a, b):
    """Exact equality, NaN equal to NaN (nested)."""
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return a == b and type(a) is type(b)


@pytest.mark.parametrize('seed', [1, 2, 3, 20261121])
def test_eight_nodes_reproduce_v3_exactly(pins, seed):
    v3 = pins
    nodes = fixture(seed)
    old = v3._evaluate(v3_input(nodes))
    new = gate._evaluate(v31_input(nodes))
    assert old['schema'] == 'r1_d8_gate_result/v3' and new['schema'] == 'r1_d8_gate_result/v3.1'
    assert old['gate_version'] == 3 and new['gate_version'] == '3.1'
    assert new['protocol']['declared_t0_nodes'] == T0
    assert old['protocol']['gate_sha256'] != new['protocol']['gate_sha256']
    assert same(strip(old, ()), strip(new, ('declared_t0_nodes',)))
    assert set(new['protocol']) - set(old['protocol']) == {'declared_t0_nodes'}


def test_eight_nodes_reproduce_v3_including_stops(pins):
    v3 = pins
    nodes = fixture(5)
    for n in nodes:      # no eligible node: both STOP with the same message
        n['dev']['oracle'] = list(n['dev']['A2'])
    with pytest.raises(v3.GateStop) as e3:
        v3._evaluate(v3_input(nodes))
    with pytest.raises(gate.GateStop) as e31:
        gate._evaluate(v31_input(nodes))
    assert str(e3.value) == str(e31.value)


def test_seven_node_primary_without_wdbc(pins):
    t0 = [k for k in T0 if k != 'openml_wdbc']
    nodes = fixture(7, t0=t0)
    r = gate._evaluate(v31_input(nodes))
    assert r['protocol']['declared_t0_nodes'] == t0 and r['node_counts']['by_tier']['T0'] == 7
    assert 'openml_wdbc' not in r['nodes'] and r['protocol']['t0_nodes'] == list(gate.T0_NODES)
    # the same seven nodes without the declaration in v3 STOP (the reason for v3.1)
    with pytest.raises(pins.GateStop, match='T0 nodes must be exactly'):
        pins._evaluate(v3_input(nodes))


def test_empty_declared_t0_set_for_a_fold(pins):
    nodes = fixture(9, t0=())
    r = gate._evaluate(v31_input(nodes, declared=[]))
    assert r['protocol']['declared_t0_nodes'] == [] and r['node_counts']['by_tier'] == {'T0': 0, 'T1': 3}
    assert r['tier_descriptive']['T0']['n_nodes'] == 0


@pytest.mark.parametrize('declared, match', [
    (T0[:7], r"unexpected \['tabular_mlp'\]"),                       # a supplied T0 node not declared
    (T0 + ['openml_blood_transfusion'], 'subset of'),               # outside the eight
])
def test_declared_set_must_match_the_supplied_t0_nodes(pins, declared, match):
    with pytest.raises(gate.GateStop, match=match):
        gate._evaluate(v31_input(fixture(11), declared=declared))


def test_declared_but_missing_t0_node_stops(pins):
    nodes = [n for n in fixture(12) if n['node'] != 'openml_sonar']
    with pytest.raises(gate.GateStop, match=r"missing \['openml_sonar'\]"):
        gate._evaluate(v31_input(nodes, declared=T0))


@pytest.mark.parametrize('bad', [None, 'digits_mlp', [T0[0], T0[0]], [1], {'digits_mlp': 1}])
def test_malformed_declared_set_refused(pins, bad):
    t = v31_input(fixture(13))
    if bad is None:
        del t['t0_nodes']
    else:
        t['t0_nodes'] = bad
    with pytest.raises(ValueError, match='t0_nodes'):
        gate._evaluate(t)


def test_v3_input_refused(pins):
    with pytest.raises(ValueError, match='r1_d8_gate_input/v3.1'):
        gate._evaluate(v3_input(fixture(14)))


def test_only_the_declared_field_and_the_version_strings_differ_in_the_source():
    """Guard against unintended changes: every changed line of gate.py is in the T0 layout path, the version
    strings, the declared field in the output, or the docstring."""
    import difflib
    old = V3_PATH.read_text().splitlines()
    new = (REPO / 'r1/c3/gate.py').read_text().splitlines()
    body_old = old[[i for i, l in enumerate(old) if l.startswith('from __future__')][0]:]
    body_new = new[[i for i, l in enumerate(new) if l.startswith('from __future__')][0]:]
    changed = [l[1:].strip() for l in difflib.unified_diff(body_old, body_new, lineterm='', n=0)
               if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    allowed = ('GATE_VERSION', 'INPUT_SCHEMA', 'OUTPUT_SCHEMA', "extra = set(gate_input)", 'declared',
               '_check_layout', 'def _declared_t0', 'The declared T0', 'if not isinstance(raw', 'raise ValueError(',
               'if len(set(raw))', 'outside', 'raise GateStop(', 'return sorted(raw)', 'STOP unless the node set',
               "t0 = sorted(k for k", 'if t0 != ', "f'{sorted(set(", "'t0_nodes': list(T0_NODES)", '')
    assert all(any(c.startswith(a) for a in allowed) for c in changed), [c for c in changed
                                                                          if not any(c.startswith(a) for a in allowed)]
