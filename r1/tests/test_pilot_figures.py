"""The renderer is provisional; tests exercise only transformations, not evidence."""
import csv
import hashlib
import json

import pytest

from r1.analysis import pilot_figures as figures


def test_noise_reproduction_mismatch_is_not_silently_accepted():
    expected = {'n': {'sigma_train': 1.0, 'sigma_split': 2.0, 'sigma_joint': 3.0}}
    figures.validate_noise_reproduction(expected, expected)
    with pytest.raises(ValueError, match='noise summary mismatch'):
        figures.validate_noise_reproduction({'n': {'sigma_train': 1.1, 'sigma_split': 2.0, 'sigma_joint': 3.0}}, expected)
    with pytest.raises(ValueError, match='node set'):
        figures.validate_noise_reproduction({}, expected)


def test_c1_renderer_has_no_19_oct_pilot_inputs():
    assert all('20261019' not in path and 'c3_audit_pilot' not in path for path in figures.INPUT_REL)
    assert figures.OUT.name == 'c1_pilot'


def test_render_matches_committed_c1_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(figures, 'OUT', tmp_path)
    figures.main()
    assert figures.verify_outputs(tmp_path)
    recorded = json.loads((figures.ROOT / figures.INPUT_REL[0]).read_text())['summaries']['common_30']['nodes']
    with (tmp_path / 'noise_floor.csv').open() as handle:
        rows = list(csv.DictReader(handle))
    assert {row['node'] for row in rows} == set(recorded)
    for row in rows:
        assert row['provisional_status'] == 'PILOT; pending author acceptance'
        for column in ('sigma_train', 'sigma_split', 'sigma_joint'):
            assert float(row[column]) == recorded[row['node']][column]


def test_failed_render_marks_prior_outputs_unusable(tmp_path, monkeypatch):
    monkeypatch.setattr(figures, 'OUT', tmp_path)
    (tmp_path / 'old.csv').write_text('old content')
    def fail():
        raise ValueError('fixture failure')
    monkeypatch.setattr(figures, '_render', fail)
    with pytest.raises(ValueError, match='fixture failure'):
        figures.main()
    assert (tmp_path / 'old.csv').read_text() == 'old content'
    assert json.loads((tmp_path / 'render_status.json').read_text())['status'] == 'FAILED'
    with pytest.raises(ValueError, match='not successful'):
        figures.verify_outputs(tmp_path)


def test_verify_rejects_empty_or_redirected_manifest(tmp_path):
    (tmp_path / 'render_status.json').write_text('{"status":"SUCCESS"}')
    (tmp_path / 'provenance.json').write_text(json.dumps({'renderer': {'path': 'fake', 'sha256': 'x'}, 'inputs': {}, 'outputs': {}}))
    with pytest.raises(ValueError, match='file set'):
        figures.verify_outputs(tmp_path)


def test_verify_rejects_changed_input_or_output(tmp_path):
    root, out = tmp_path / 'root', tmp_path / 'out'
    root.mkdir()
    out.mkdir()
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    for name in (*figures.INPUT_REL, figures.RENDERER_REL):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
    for name in figures.OUTPUT_NAMES:
        (out / name).write_text(name)
    manifest = {'renderer': {'path': figures.RENDERER_REL, 'sha256': digest(root / figures.RENDERER_REL)},
                'inputs': {name: digest(root / name) for name in figures.INPUT_REL},
                'outputs': {name: digest(out / name) for name in figures.OUTPUT_NAMES}}
    (out / 'render_status.json').write_text('{"status":"SUCCESS"}')
    (out / 'provenance.json').write_text(json.dumps(manifest))
    assert figures.verify_outputs(out, root)
    (root / figures.INPUT_REL[0]).write_text('changed')
    with pytest.raises(ValueError, match='input differs'):
        figures.verify_outputs(out, root)
    (root / figures.INPUT_REL[0]).write_text(figures.INPUT_REL[0])
    (out / figures.OUTPUT_NAMES[0]).write_text('changed')
    with pytest.raises(ValueError, match='output differs'):
        figures.verify_outputs(out, root)
