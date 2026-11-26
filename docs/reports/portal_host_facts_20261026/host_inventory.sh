export LC_ALL=C
run() { printf '\nCOMMAND: %s\n' "$*"; "$@"; result=$?; printf 'EXIT: %s\n' "$result"; }
run date -u +%Y-%m-%dT%H:%M:%SZ
run hostname
run id
run printenv HOME
run printenv PATH
run cat /etc/os-release
run df -h
run df -B1 /home/dowling
run df -i /home/dowling
run stat -c '%A %U %G %n' /home/dowling /tmp /data /mnt /scratch
run ls -ld /home/dowling /home/dowling/models /home/dowling/work /home/dowling/agent_paper_B /home/dowling/autoresearch_harness /home/dowling/.cache/huggingface
run nvidia-smi
run nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,driver_version,compute_cap --format=csv
run nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv
run nproc
run free -g
run free -b
run uptime
run who
run ps -eo user,pid,pcpu,pmem,comm --sort=-pcpu
for tool in python3 python3.11 python3.12 uv git cmake gcc g++ nvcc llama-server huggingface-cli hf; do
  run command -v "$tool"
  case "$tool" in huggingface-cli|hf) ;; *) if command -v "$tool" >/dev/null 2>&1; then run timeout 15 "$tool" --version; fi ;; esac
done
run ls -ld /usr/local/cuda /usr/local/cuda-* /opt/cuda /home/dowling/.local/bin/uv /home/dowling/.local/bin/hf /home/dowling/.local/bin/huggingface-cli
run find /home/dowling -maxdepth 5 \( -name .cache -o -name .git -o -name node_modules \) -prune -o \( -name llama-server -o -name llama.cpp -o -name huggingface-cli -o -name hf -o -name nvcc -o -name uv \) -print
if command -v huggingface-cli >/dev/null 2>&1; then run timeout 20 huggingface-cli whoami; fi
if command -v hf >/dev/null 2>&1; then run timeout 20 hf auth whoami; fi
run timeout 25 env GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/ggml-org/llama.cpp.git HEAD
run timeout 25 env GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/dowlingwong/Agent_paper_B.git HEAD
run curl --connect-timeout 8 --max-time 20 -sSI https://huggingface.co
run curl --connect-timeout 8 --max-time 20 -sSI https://www.openml.org
run date -u +%Y-%m-%dT%H:%M:%SZ
