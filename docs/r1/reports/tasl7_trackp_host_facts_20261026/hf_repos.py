"""Phase 0.5: anonymous Hugging Face metadata for every Track P repo (stdlib only, no weights)."""
import json
import urllib.error
import urllib.request

REPOS = [
    "jaredpalmer/kev-0.8b",
    "jaredpalmer/kev-4b",
    "Qwen/Qwen3.5-0.8B-Base",
    "Qwen/Qwen3.5-4B-Base",
    "NandhaKishorM/laya",  # name given in RUNBOOK Track P; expected to be the GitHub repo, not a Hub repo
    "convaiinnovations/laya-typed-decisions",
    "convaiinnovations/laya",
    "startlux-models/StartLux-Decision-v1.1-0.8B-Instant",
    "startlux-models/StartLux-Decision-v1.1-2B-Instant",
    "startlux-models/StartLux-Decision-v1.1-4B-Instant",
]


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None


for repo in REPOS:
    code, d = get(f"https://huggingface.co/api/models/{repo}?blobs=true")
    row = {"repo": repo, "api_status": code}
    if d:
        tags = d.get("tags", [])
        sib = d.get("siblings", [])
        row.update(
            sha=d.get("sha"),
            gated=d.get("gated"),
            private=d.get("private"),
            license=[t[8:] for t in tags if t.startswith("license:")],
            base_model=[t for t in tags if t.startswith("base_model:")],
            n_files=len(sib),
            total_bytes=sum(s.get("size", 0) for s in sib),
            weights=[s["rfilename"] for s in sib if s["rfilename"].endswith((".safetensors", ".pt"))],
            last_modified=d.get("lastModified"),
        )
        rc, refs = get(f"https://huggingface.co/api/models/{repo}/refs")
        if refs:
            row["tags"] = {t["name"]: t["targetCommit"] for t in refs.get("tags", [])}
        try:
            req = urllib.request.Request(
                f"https://huggingface.co/{repo}/resolve/{d['sha']}/config.json", method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                row["config_head"] = r.status
        except urllib.error.HTTPError as e:
            row["config_head"] = e.code
    print(json.dumps(row))
