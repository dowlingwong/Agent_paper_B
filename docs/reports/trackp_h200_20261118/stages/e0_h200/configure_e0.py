"""Port only paths and GPU identity in the exact TASL-7 E0 recipe."""
import hashlib
import json
from pathlib import Path

root = Path.cwd()
source = root / "paper/r1/scripts/configs/trackp_portal.json"
config = json.loads(source.read_text())
source_digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
reference = json.loads(Path("reference_manifest.json").read_text())
if source_digest != reference["config_sha256"]:
    raise SystemExit(f"STOP: historical config differs from the TASL-7 reference ({source_digest})")
config["host"] = "ETP HTCondor / NEMO2 H200"
config["gpu"].update(name="NVIDIA H200", compute_capability="9.0",
                     lock_path=str(root / "h200_probe.lock"))
config["work_dir"] = str(root)
config["runs_dir"] = str(root / "logs")
config["models_dir"] = str(root / "models")
config["hf_home"] = str(root / "hf_cache")
config["venv"]["path"] = "/opt/r1/envs/trackp"
config["bases"]["kev-0.8b"]["local_path"] = str(root / "models/qwen3.5-0.8b-base")
config["bases"]["kev-0.8b"]["adapter_local_path"] = str(root / "models/kev-0.8b")
Path("handback/e0_config.json").write_text(json.dumps(config, indent=2) + "\n")
