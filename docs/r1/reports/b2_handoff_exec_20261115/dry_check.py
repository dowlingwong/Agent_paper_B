"""Dry check of the B2 run-HEAD package on the Mac: the two PLAN rows pasted from the accepted drafts satisfy the
B2 author-row parser; the note draft (with approved set to true, as the author would) binds exactly the filled
config; the config loads and has no unresolved B2 placeholders.  Host-only checks (Stage A files on TASL-7, the
clean committed run HEAD, the harness checkout) are not run here."""
import json, re, sys, subprocess
from pathlib import Path
sys.path.insert(0, '.')
from r1.exam import runtime
from r1.exam.runtime import load_config, placeholders, _b2_author_rows, _x5_author_row
plan = Path('docs/r1/PLAN.md').read_text()
drafts = {k: subprocess.check_output(['git', '-C', '/tmp/pb/wt/b2plan', 'show', f'3533b545:docs/r1/proposals/{k}'], text=True)
          for k in ('PLAN_ROW_R1-EXAM-B2-POWER-PLAN_DRAFT_20261114.md', 'PLAN_ROW_R1-EXAM-B2-INVALID-TRIALS_DRAFT_20261114.md')}
def first_block(md):
    blocks = re.findall(r'```\n(### .*?)```', md, re.S)
    return blocks[0].replace('14 November 2026', '15 November 2026')
section10 = plan.index('\n## 10.')
nxt = plan.index('\n## ', section10 + 5)
pasted = plan[:nxt] + '\n\n' + '\n'.join(first_block(d) for d in drafts.values()) + plan[nxt:]
cfg = load_config('r1/scripts/configs/exam_b2_v2.json')
required = ['stage_a_table', 'stage_a_table_sha256', 'nodes', 'llm_call_cap', 'anchor_duplicate_reference',
            'b1_analysis', 'b1_analysis_sha256', 'b2_instances_per_node', 'stage_a_amendment_table',
            'stage_a_amendment_table_sha256', 'stage_a_amendment_acceptance', 'stage_a_amendment_acceptance_sha256']
note_md = Path('docs/r1/proposals/TRACKX_B2_AUTHORIZATION_NOTE_DRAFT_20261115.md').read_text()
note = json.loads(re.findall(r'```json\s*(.*?)```', note_md, re.S)[0]); note['approved'] = True
expect = {'author': 'Dowling Wong', 'phase': 'b2', 'approved': True, 'rule_sha256': cfg['rule_sha256'], 'nodes': cfg['nodes'],
          'stage_a_table_sha256': cfg['stage_a_table_sha256'], 'stage_a_amendment_table_sha256': cfg['stage_a_amendment_table_sha256'],
          'stage_a_amendment_acceptance_sha256': cfg['stage_a_amendment_acceptance_sha256'],
          'anchor_duplicate_reference_sha256': cfg['anchor_duplicate_reference']['sha256'], 'b1_analysis_sha256': cfg['b1_analysis_sha256'],
          'instances_per_node': cfg['b2_instances_per_node'], 'llm_call_cap': cfg['llm_call_cap'], 'host': cfg['host'],
          'gpu_uuid': cfg['gpu_uuid'], 'workers': cfg['workers']}
import hashlib
result = {
  'x5_row_present': _x5_author_row(plan, cfg['rule_sha256']),
  'b2_rows_absent_before_author': not _b2_author_rows(plan, 4),
  'b2_rows_after_paste': _b2_author_rows(pasted, cfg['b2_instances_per_node']),
  'b2_rows_wrong_n_refused': not _b2_author_rows(pasted, 5),
  'unresolved_b2_settings': placeholders({k: cfg[k] for k in required}),
  'b2_authorization_path_resolved': not placeholders(cfg['authorizations']['b2']),
  'note_binds_config': note == expect,
  'b1_analysis_sha_matches_file': hashlib.sha256(Path(cfg['b1_analysis']).read_bytes()).hexdigest() == cfg['b1_analysis_sha256'],
  'anchor_sha_matches_file': hashlib.sha256(Path(cfg['anchor_duplicate_reference']['source']).read_bytes()).hexdigest() == cfg['anchor_duplicate_reference']['sha256'],
  'count_within_author_cap': 1 <= cfg['b2_instances_per_node'] <= runtime.B2_AUTHOR_CAP,
  'protected_diff_empty': subprocess.check_output(['git', 'diff', '--name-only', cfg['paper_commit'], '--', 'r1/exam', 'r1/scripts/exam_runner.py',
      'r1/scripts/llama_server_instance.py', 'r1/scripts/llamacpp_probe.py', 'r1/headroom/e1b_collect.py'], text=True).strip() == '',
  'paper_commit_is_ancestor': subprocess.run(['git', 'merge-base', '--is-ancestor', cfg['paper_commit'], 'HEAD']).returncode == 0,
}
print(json.dumps(result, indent=1))
