"""B2 ranking arithmetic and grid: synthetic fixtures, no execution or authority."""
import copy
import math
import pytest
from r1.exam.b2_ranking import synthetic_b2_rank
from r1.exam.analyze import RULE, RULE_V2, b2_summary
from r1.exam.guards import digest_file

SHA = digest_file(RULE_V2)
NODES = ['digits_mlp', 'openml_credit_approval', 'openml_ionosphere']


def manifest(candidate, y, gpu):
    audits = [{'node': n, 'instance_id': f'{n}__s{s}', 'seeds': list(range(9201, 9211)),
               'metrics': [y] * 10, 'final_y': y} for n in NODES for s in (9011, 9012)]
    return {'label': 'EXAM', 'execution_label': 'DRYRUN', 'phase': 'b2', 'status': 'COMPLETE',
            'candidate': candidate, 'source_label': 'fixture', 'rule_sha256': SHA, 'purpose': 'primary', 'mode': 'off',
            'final_audits': audits, 'gpu_hours': gpu}


def rank(rows, **kw):
    values = {'finalists': ['a', 'b'], 'nodes': NODES, 'instances_per_node': 2, 'rule_sha256': SHA}
    return synthetic_b2_rank(rows, **{**values, **kw})


def test_complete_grid_ranks_y_then_gpu_hours_without_sensitivity():
    rows = [manifest('a', .6, 4), manifest('b', .7, 3)]
    rows.append({**manifest('a', .99, 1), 'purpose': 'thinking_on_descriptive', 'mode': 'on'})
    result = rank(rows)
    assert [r['candidate'] for r in result['rows']] == ['b', 'a']
    assert result['rule_top'] == 'b' and result['label'] == 'DRYRUN'
    tied = rank([manifest('a', .7, 4), manifest('b', .7, 3)])
    assert tied['rule_top'] == 'b'
    exact = rank([manifest('a', .7, 3), manifest('b', .7, 3)])
    assert exact['rule_top'] is None and exact['unresolved_exact_tie']


def test_public_api_synthetic_plan_only_and_production_still_stops():
    rows = [manifest('a', .6, 4), manifest('b', .7, 3)]
    plan = {'finalists': ['a', 'b'], 'nodes': NODES, 'instances_per_node': 2}
    result = b2_summary(rows, rule_path=RULE_V2, synthetic_plan=plan)
    assert result['rule_top'] == 'b' and result['provenance'].startswith('synthetic_')
    with pytest.raises(ValueError, match='B2 node/instance grid'):
        b2_summary(rows, rule_path=RULE_V2)
    with pytest.raises(ValueError, match='DRYRUN'):
        b2_summary([{**rows[0], 'execution_label': 'EVIDENCE'}, rows[1]], rule_path=RULE_V2, synthetic_plan=plan)
    with pytest.raises(ValueError, match='needs the frozen v2 rule'):
        b2_summary(rows, synthetic_plan=plan)
    with pytest.raises(ValueError):
        b2_summary(rows, rule_path=RULE, synthetic_plan=plan)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'extra', 'wrong_node', 'wrong_seed', 'duplicate_finalist',
                                      'missing_finalist', 'extra_finalist', 'wrong_mode', 'wrong_sha', 'evidence'])
def test_grid_and_authority_containment_fails_closed(mutation):
    rows = [manifest('a', .6, 4), manifest('b', .7, 3)]
    if mutation == 'missing': rows[0]['final_audits'].pop()
    if mutation == 'duplicate': rows[0]['final_audits'][-1] = copy.deepcopy(rows[0]['final_audits'][0])
    if mutation == 'extra': rows[0]['final_audits'].append(copy.deepcopy(rows[0]['final_audits'][0]))
    if mutation == 'wrong_node': rows[0]['final_audits'][0]['node'] = 'openml_ionosphere'
    if mutation == 'wrong_seed': rows[0]['final_audits'][0]['instance_id'] = 'digits_mlp__s9001'
    if mutation == 'duplicate_finalist': rows.append(copy.deepcopy(rows[0]))
    if mutation == 'missing_finalist': rows.pop()
    if mutation == 'extra_finalist': rows.append(manifest('c', .8, 1))
    if mutation == 'wrong_mode': rows[0]['mode'] = 'on'
    if mutation == 'wrong_sha': rows[0]['rule_sha256'] = 'b' * 64
    if mutation == 'evidence': rows[0]['execution_label'] = 'EVIDENCE'
    with pytest.raises(ValueError): rank(rows)


@pytest.mark.parametrize('value', [None, True, '1', math.nan, math.inf, -1])
def test_cost_must_be_finite_nonnegative_number(value):
    with pytest.raises(ValueError): rank([manifest('a', .6, value), manifest('b', .7, 3)])


@pytest.mark.parametrize('value', [True, '0.6', math.nan, math.inf])
def test_metrics_and_reported_y_must_be_finite_numbers(value):
    rows = [manifest('a', .6, 4), manifest('b', .7, 3)]
    rows[0]['final_audits'][0]['metrics'][0] = value
    with pytest.raises(ValueError): rank(rows)
    rows = [manifest('a', .6, 4), manifest('b', .7, 3)]
    rows[0]['final_audits'][0]['final_y'] = value
    with pytest.raises(ValueError): rank(rows)


def test_exact_ordered_integer_audit_seeds_and_absolute_tolerance():
    rows = [manifest('a', .6, 4), manifest('b', .7, 3)]
    rows[0]['final_audits'][0]['seeds'][0] = True
    with pytest.raises(ValueError): rank(rows)
    rows[0]['final_audits'][0]['seeds'] = list(reversed(range(9201, 9211)))
    with pytest.raises(ValueError): rank(rows)
    rows[0]['final_audits'][0]['seeds'] = list(range(9201, 9211))
    rows[0]['final_audits'][0]['final_y'] += 1e-9
    with pytest.raises(ValueError): rank(rows)


@pytest.mark.parametrize('count', [True, 0, 90, '2'])
def test_grid_count_must_be_an_explicit_integer(count):
    with pytest.raises(ValueError): rank([manifest('a', .6, 4), manifest('b', .7, 3)], instances_per_node=count)
