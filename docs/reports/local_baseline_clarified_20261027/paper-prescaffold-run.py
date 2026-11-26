import os, subprocess, time, signal, json
from pathlib import Path
base=Path('/private/tmp/paper-b-prescaffold-20261027')
env=os.environ.copy()
env.update({'PATH':json.loads(Path('/private/tmp/paper-b-baseline-paper-20261027/run.json').read_text())['environment']['PATH'], 'AR_HARNESS_ROOT':'/private/tmp/paper-b-harness-local-20261027', 'CUDA_VISIBLE_DEVICES':'', 'HF_HUB_OFFLINE':'1', 'TRANSFORMERS_OFFLINE':'1', 'HF_HOME':str(base/'hf-empty'), 'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1', 'PYTHONDONTWRITEBYTECODE':'1', 'PYTORCH_ENABLE_MPS_FALLBACK':'0', 'PYTEST_ADDOPTS':'--ignore=r1/tests/test_c3_h8_amendment.py --ignore=r1/tests/test_c3_sidecar_prompt_fixture.py --ignore=r1/tests/test_trackp_model.py --ignore=r1/tests/test_trackp_sidecar_loader.py --ignore=r1/tests/test_c3_sweep_dryrun.py --ignore=r1/tests/test_c3_control_dryrun.py --ignore=r1/tests/test_exam_dryrun.py --deselect=r1/tests/test_trackp_trainer.py::test_kill_and_resume_matches_an_uninterrupted_run --deselect=r1/tests/test_rerun2_batch4c.py::test_real_runner_desktop_dryrun --junitxml=/private/tmp/paper-b-prescaffold-20261027/junit.xml --durations=30'})
cmd=['make','r1-test','R1_PY=/private/tmp/paper-b-local-20261026-venv/bin/python']
record={'command':cmd,'cwd':str(base/'clone'),'environment':{k:env[k] for k in ('PATH','AR_HARNESS_ROOT','CUDA_VISIBLE_DEVICES','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HOME','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','PYTHONDONTWRITEBYTECODE','PYTORCH_ENABLE_MPS_FALLBACK','PYTEST_ADDOPTS')},'timeout_seconds':590,'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(base/'run.json').write_text(json.dumps(record,indent=2)+'\n')
t=time.monotonic()
with (base/'run.log').open('w') as log:
 p=subprocess.Popen(cmd,cwd=base/'clone',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try: rc=p.wait(timeout=590); timed_out=False
 except subprocess.TimeoutExpired:
  timed_out=True; os.killpg(p.pid,signal.SIGTERM)
  try: rc=p.wait(timeout=5)
  except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
record.update(returncode=rc,timed_out=timed_out,elapsed_seconds=round(time.monotonic()-t,3),end_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
(base/'run.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
