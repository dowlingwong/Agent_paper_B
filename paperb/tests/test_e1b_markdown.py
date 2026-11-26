"""The E1b tables Markdown must pass `git diff --check` (DT4 rerun STOP, 13 Oct 2026).

Loads `_f` and `markdown` from e1b_analyze via AST, so the harness is not needed.
"""
import ast
import math
from pathlib import Path
import subprocess

SOURCE = Path(__file__).parents[1] / 'headroom' / 'e1b_analyze.py'


def load_markdown():
    body = [n for n in ast.parse(SOURCE.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name in {'_f', 'markdown'}]
    ns = {'math': math}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(SOURCE), 'exec'), ns)
    return ns['markdown']


def result():
    node = {'n_points': 18, 'n_instances': 6, 'best_simple': 'rho',
            'headroom_leafsplit': 0.0001, 'headroom_naive': 0.0002,
            'contrast_ci': {'oracle_leafsplit - rho': (-0.0001, 0.0003), 'oracle_naive - rho': (0.0, 0.0004),
                            'kg - rho': (-0.001, 0.001)},
            'contrasts': {'kg - rho': 0.0}, 'estimates': {'rho': 0.008, 'kg': 0.008},
            'ci': {'rho': (0.006, 0.010), 'kg': (0.006, 0.010)}, 'verify_rate': {'rho': 0.0, 'kg': 0.0},
            'mean_verify_minus_continue': -0.0006, 'share_points_verify_changes_leaf': 0.6,
            'mean_cost': {'continue': 12.0, 'verify': 12.0}}
    return {'per_node': {'digits_mlp': node, 'ALL': node}}


def test_tables_file_ends_with_exactly_one_newline():
    text = load_markdown()(result()) + '\n'  # as main() writes it
    assert text.endswith('|\n') and not text.endswith('\n\n')


def test_tables_file_passes_git_whitespace_check(tmp_path):
    def git(*args):
        return subprocess.run(['git', *args], cwd=tmp_path, capture_output=True, text=True)
    git('init', '-q')
    (tmp_path / 'tables.md').write_text(load_markdown()(result()) + '\n')
    git('add', 'tables.md')
    check = git('diff', '--cached', '--check')
    assert check.returncode == 0, check.stdout + check.stderr


def test_dt4_saves_after_collection_offload_telemetry():
    source = (Path(__file__).parents[1] / 'scripts' / 'deepthought_batch1_resume.py').read_text()
    assert 'gpu_offload_after_collection.json' in source
