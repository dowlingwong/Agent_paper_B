#!/usr/bin/env bash
# Track P Phase 0 follow-up checks (review finding 5). Read-only; no weights, no secrets.
#   bash followup.sh > followup.txt 2>&1
set -u
run() { echo; echo "\$ $*"; bash -c "$*" 2>&1; echo "[exit $?]"; }
echo "# collected $(date -u +%FT%TZ)"

echo "## code repos: GitHub vs Hub"
for r in jaredpalmer/kev NandhaKishorM/laya StartLuxLabs/StartLux-Decision; do
  run "curl -sI --max-time 10 -o /dev/null -w 'github %{http_code}\n' https://github.com/$r; curl -s -o /dev/null -w 'hub-api %{http_code}\n' https://huggingface.co/api/models/$r"
done

echo "## Kev: v1.0 vs main bytes, base revision"
for r in jaredpalmer/kev-0.8b jaredpalmer/kev-4b; do
  for rev in main v1.0; do
    run "curl -s https://huggingface.co/api/models/$r/tree/$rev | python3 -c \"import sys,json; print('$r@$rev', {f['path']:(f.get('lfs') or {}).get('oid') for f in json.load(sys.stdin) if f['path'] in ('adapter_model.safetensors','head.pt')})\""
  done
  run "curl -sL https://huggingface.co/$r/resolve/v1.0/training_config.json | python3 -c \"import sys,json; print('base_revision', json.load(sys.stdin).get('base_revision'))\""
done
run "curl -sI --max-time 10 -o /dev/null -w '%{http_code}\n' https://github.com/jaredpalmer/kev/releases/tag/kev-1.0"

echo "## weight download redirect (HEAD only)"
run "curl -sIL --max-time 20 -o /dev/null -w '%{http_code} %{url_effective}\n' https://huggingface.co/jaredpalmer/kev-0.8b/resolve/bf75a6a8848ea6960ff2ed108d9ed44c2941174f/adapter_model.safetensors | sed 's/?.*//'"

echo "## Laya: duplicate typed-decisions checkpoint"
for p in "convaiinnovations/laya/tree/main/typed-decisions" "convaiinnovations/laya-typed-decisions/tree/main"; do
  run "curl -s https://huggingface.co/api/models/$p | python3 -c \"import sys,json; [print('$p', f['path'], (f.get('lfs') or {}).get('oid')) for f in json.load(sys.stdin) if f['path'].endswith('safetensors')]\""
done

echo "## StartLux Instant architecture"
run "curl -sL https://huggingface.co/startlux-models/StartLux-Decision-v1.1-0.8B-Instant/resolve/6496ae641cc71b149ce9dad69bd97f2a44e7bf11/config.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('architectures'), d.get('model_type'))\""
run "curl -s https://raw.githubusercontent.com/StartLuxLabs/StartLux-Decision/main/README.md | grep -n -i -E 'vllm 0\\.|cuda 1[23]'"

echo "## PyTorch wheel index (latest torch per CUDA tag)"
for cu in cu121 cu124 cu126 cu128 cu130; do
  run "curl -s https://download.pytorch.org/whl/$cu/torch/ | grep -o 'torch-[0-9.]*+$cu' | sort -uV | tail -1"
done

echo "## harness pin"
run "cat /home/dowling/r1_trackp/Agent_paper_B/r1/scripts/HARNESS_PIN_C3"
run "cd /home/dowling/r1_trackp/autoresearch_harness && git fetch -q --all && git branch -r && git cat-file -t \$(tr -d '[:space:]' < ../Agent_paper_B/r1/scripts/HARNESS_PIN_C3)"
run "gh api repos/dowlingwong/autoresearch_harness/commits/6afdb0e9b800933dfbb682618b8909441f0f6495 --jq .sha"

echo "## Track X STATUS on origin/main (first heading lines)"
run "cd /home/dowling/r1_trackp/Agent_paper_B && git fetch -q origin && git show origin/main:docs/r1/STATUS.md | grep '^## ' | head -5"

echo "## gh login, pre-session config changes (metadata only)"
run "gh auth status 2>&1 | grep -E 'Logged in|protocol'"
run "stat -c '%y %n' ~/.gitconfig ~/.config/gh/hosts.yml ~/.bashrc"
