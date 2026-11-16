"""Agreement count of gate v3's (b2) pass decision with the simulation's code over synthetic tables (report §4)."""
import sys, importlib.util, json, numpy as np
sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location('t', 'r1/tests/test_d8_gate_synthetic.py'); t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
from r1.c3 import gate
gate.NUMPY_VERSION = np.__version__
n = agree = stops = 0; maxdiff = 0.0
for seed in range(1, 41):
    for dist in ('normal', 'left_skewed', 't3'):
        tab = t.sim_table(seed, dist, 1.0 + (seed % 3) * 0.5)
        nodes = gate._validate(tab)
        try:
            el, _, sm = gate._point(nodes)
        except gate.GateStop:
            stops += 1; continue
        boot, _ = gate._bootstrap(nodes, el, sm)
        for lv in gate.LEVELS:
            ref = t.reference_b2(tab, set(el), lv)
            for arm in gate.ARMS:
                got = gate._lower_iqm(boot[arm], lv); want = ref[arm][0]
                n += 1; agree += (got > 0) == (want > 0)
                maxdiff = max(maxdiff, abs(got - want) / max(1.0, abs(want)))
print(json.dumps({'comparisons': n, 'decision_agreement': agree, 'point_stops_skipped': stops, 'max_rel_diff': maxdiff,
                  'numpy': np.__version__}))
