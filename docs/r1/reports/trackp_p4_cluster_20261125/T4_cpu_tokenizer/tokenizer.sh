#!/bin/bash
set -uo pipefail
cd /work/dwong/paperb/work/trackp-p4-cluster-20261125/paper || exit 2
export PYTHONPATH=$PWD HF_HOME=/work/dwong/paperb/work/trackp-p4-cluster-20261125/T4_hf HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$HF_HOME"
/opt/r1/envs/trackp/bin/python -B -c "from r1.c3.train import serialize as S; [S.load_tokenizer(n) for n in S.POOL]; print(len(S.POOL))"
echo "tokenizer_rc=$?"
