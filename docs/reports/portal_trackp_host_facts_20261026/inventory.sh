#!/usr/bin/env bash
# Track P Phase 0 host-facts inventory (read-only). Run on zhixu portal:
#   bash inventory.sh > inventory.txt 2>&1
# Installs nothing, writes nothing outside stdout, never reads secret contents.
set -u
run() { echo; echo "\$ $*"; bash -c "$*" 2>&1; echo "[exit $?]"; }

echo "# collected $(date -u +%FT%TZ) (local: $(date))"
echo "## 0.1 host, user, OS, disk"
run 'hostname; id -un; id'
run 'head -4 /etc/os-release; uname -r'
run 'df -h / /home/dowling; df -B1 /home/dowling'
run 'nproc; free -g'
run 'ls -ld /home/dowling/r1_trackp /home/dowling/r1_trackp/* 2>&1'

echo "## 0.2 GPU"
run 'nvidia-smi'
run 'nvidia-smi --query-gpu=name,driver_version,compute_cap,memory.total,memory.used --format=csv'
run 'nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv'

echo "## 0.3 toolchain"
for c in python3 python3.11 python3.12 uv pip3 git git-lfs gh tmux flock nvcc huggingface-cli hf conda; do
  run "command -v $c && $c --version 2>&1 | head -1"
done
run 'ls -d /usr/local/cuda*; /usr/local/cuda/bin/nvcc --version | tail -2'
run "python3 -c \"import importlib.util as u; print({m: bool(u.find_spec(m)) for m in ['torch','transformers','huggingface_hub','peft','venv','ensurepip']})\""
for u in https://download.pytorch.org/whl/ https://pypi.org/simple/ https://astral.sh/uv/install.sh https://github.com/astral-sh/python-build-standalone/releases; do
  run "curl -sIL --max-time 10 -o /dev/null -w '%{http_code}\n' $u"
done

echo "## 0.4 network (HTTP status only, no keys)"
for u in https://github.com https://huggingface.co https://api.typesafe.ai https://docs.typesafe.ai/api https://api.deepseek.com https://api.anthropic.com; do
  run "curl -sI --max-time 10 -o /dev/null -w '%{http_code}\n' $u"
done
run 'GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/dowlingwong/Agent_paper_B | head -5'
run 'GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/dowlingwong/autoresearch_harness | grep -E "HEAD|refs/heads/r1$"'
run "gh api repos/dowlingwong/Agent_paper_B --jq '{private:.private, push:.permissions.push}'"
run 'cd /home/dowling/r1_trackp/Agent_paper_B && GIT_TERMINAL_PROMPT=0 git push --dry-run origin HEAD:refs/heads/trackp-20261026 2>&1 | tail -1'

echo "## 0.5 Hugging Face"
run 'curl -s -o /dev/null -w "%{http_code}\n" https://huggingface.co/api/whoami-v2'
run 'test -f ~/.cache/huggingface/token && echo token-file-present || echo no-token-file; env | grep -c -E "^HF_TOKEN=|^HUGGING_FACE_HUB_TOKEN=" || true'
python3 "$(dirname "$0")/hf_repos.py"

echo "## 0.6 lock"
run 'command -v flock; ls -ld ~/r1_locks; test -w ~ && echo home-writable'

echo "## 0.7 secrets file (metadata only)"
run 'stat -c "%a %U" ~/.config/r1/secrets.env'

echo "## 0.8 clones"
run 'cd /home/dowling/r1_trackp/Agent_paper_B && git branch --show-current && git rev-parse HEAD origin/main'
run 'cd /home/dowling/r1_trackp/autoresearch_harness && git branch --show-current && git rev-parse HEAD origin/r1'
