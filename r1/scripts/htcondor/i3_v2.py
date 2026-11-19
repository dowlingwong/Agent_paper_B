#!/usr/bin/env python3
"""I3 (image v2) on NEMO2 H200: torch CUDA device check, 60 s matmul, llama-server --version, optional qwen25 GGUF
load + one short completion (cache_prompt false), then stop the server. Runbook HTCONDOR_PREP §4 I3 + R1-TRACKP-I3-H200.
"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path

OUT = Path("i3.json")
MODEL_CANDIDATES = [
    "/ceph/srv/dwong/paperb/models/qwen25_coder_7b/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    "/ceph/srv/dwong/paperb/models/qwen25_coder_7b.gguf",
]

def torch_check():
    py = "/opt/r1/envs/trackp/bin/python"
    if not Path(py).is_file():
        py = sys.executable
    code = """import json, torch, time
ok = torch.cuda.is_available()
out = {"cuda": ok}
if ok:
    p = torch.cuda.get_device_properties(0)
    out.update(name=str(p.name), uuid=str(getattr(p, "uuid", None)), total_memory=int(p.total_memory),
               major=int(p.major), minor=int(p.minor), torch=torch.__version__, cuda=torch.version.cuda)
    t = time.time()
    a = torch.randn(4096, 4096, device="cuda"); b = torch.randn(4096, 4096, device="cuda")
    while time.time() - t < 60:
        c = a @ b
    out["matmul_seconds"] = round(time.time() - t, 1)
print(json.dumps(out))
"""
    res = subprocess.run([py, "-B", "-c", code], capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        return {"error": res.stderr[-2000:]}
    return json.loads(res.stdout.strip().splitlines()[-1])

def server_version():
    for binary in ("/opt/r1/llama/bin/llama-server", "llama-server"):
        try:
            res = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                return {"binary": binary, "line": (res.stdout + res.stderr).strip().splitlines()[-1]}
        except OSError:
            continue
    return {"error": "llama-server missing"}

def model_part():
    model = next((Path(p) for p in MODEL_CANDIDATES if Path(p).is_file()), None)
    if model is None:
        return {"skipped": True, "reason": "/ceph/srv dwong model not available inside the NEMO2 job"}
    import socket
    port = None
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    log = Path("llama-server-i3.log").open("wb")
    proc = subprocess.Popen(["/opt/r1/llama/bin/llama-server", "-m", str(model), "--host", "127.0.0.1",
                             "--port", str(port), "-c", "4096", "-ngl", "999", "--jinja"], stdout=log,
                            stderr=subprocess.STDOUT, start_new_session=True)
    try:
        t0 = time.time(); base = f"http://127.0.0.1:{port}"
        while time.time() - t0 < 300:
            try:
                with urllib.request.urlopen(base + "/health", timeout=5) as r:
                    if r.status == 200: break
            except Exception:
                time.sleep(2)
        load_s = round(time.time() - t0, 1)
        body = json.dumps({"model": model.name, "messages": [{"role": "user", "content": "Say hi."}],
                           "max_tokens": 16, "cache_prompt": False, "temperature": 0}).encode()
        req = urllib.request.Request(base + "/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        t1 = time.time()
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.loads(r.read())
        return {"skipped": False, "model": str(model), "load_seconds": load_s,
                "completion_seconds": round(time.time() - t1, 1),
                "completion": (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")}
    finally:
        try: os.killpg(proc.pid, 15)
        except Exception: pass
        log.close()

def main():
    result = {"runbook": "HTCONDOR_PREP_20261114 §4 I3 + R1-TRACKP-I3-H200", "host": os.uname().nodename,
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    result["torch"] = torch_check()
    result["server"] = server_version()
    result["model"] = model_part()
    result["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))

if __name__ == "__main__":
    main()
