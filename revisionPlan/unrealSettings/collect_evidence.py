"""Inventory source provenance, historical trainer configurations and checkpoint headers.

Run with ordinary Python; reads the Unreal project and writes only this directory.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parent
PROJECT = Path(r"C:\Users\jingo\Documents\Unreal Projects\decanalization")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(["git", "-C", str(PROJECT), *args], text=True).strip()

def write(name, data):
    (ROOT / name).write_text(json.dumps(data, indent=2), encoding="utf-8")

def main():
    provenance = {"project": str(PROJECT), "commit": git("rev-parse", "HEAD"),
                  "status": git("status", "--short"), "assets": []}
    for path in sorted(PROJECT.joinpath("Content").rglob("*")):
        if path.is_file() and path.suffix in (".uasset", ".umap"):
            provenance["assets"].append({"file": path.relative_to(PROJECT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write("source_manifest.json", provenance)

    configs, profiles = [], {}
    for path in sorted(PROJECT.joinpath("Intermediate/LearningAgents/Configs").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        effective = {k: data[k] for k in ("PPOSettings", "Schemas", "ReplayBuffers", "Networks") if k in data}
        sig = hashlib.sha256(json.dumps(effective, sort_keys=True).encode()).hexdigest()
        if sig not in profiles:
            profiles[sig] = {"settings": effective, "files": []}
        relative = path.relative_to(PROJECT).as_posix()
        profiles[sig]["files"].append(relative)
        configs.append({"file": relative, "sha256": sha(path), "timestamp": data.get("TimeStamp"), "profile": sig})
    write("training_configs.json", {"runs": configs, "profiles": profiles})

    checkpoints = []
    for path in sorted(PROJECT.joinpath("Intermediate/LearningAgents/Snapshots").rglob("*.bin")):
        data = path.read_bytes()
        header = struct.unpack("<6I", data[:24])
        assert header[0:2] == (0x1e9b0c80, 1) and header[5] + 24 == len(data), path
        checkpoints.append({"file": path.relative_to(PROJECT).as_posix(), "sha256": sha(path),
                            "bytes": len(data), "input_size": header[2], "output_size": header[3],
                            "compatibility_hash": header[4]})
    write("checkpoint_inventory.json", checkpoints)

    matches = []
    trials = list(PROJECT.joinpath("logs/trials").glob("*.yml"))
    for path in sorted(PROJECT.joinpath("analysis/data").glob("*.yml")):
        digest = sha(path)
        matches.append({"analysis_file": path.relative_to(PROJECT).as_posix(), "sha256": digest,
                        "byte_identical_logs": [p.relative_to(PROJECT).as_posix() for p in trials if sha(p) == digest],
                        "trial_count": len(re.findall(r"^- id:", path.read_text(), re.M)),
                        "durations": sorted(set(re.findall(r"^    duration: (.+)$", path.read_text(), re.M)))})
    write("evaluation_data_provenance.json", matches)
    print(json.dumps({"config_count": len(configs), "distinct_profiles": len(profiles), "checkpoints": len(checkpoints), "evaluation_matches": matches}, indent=2))

if __name__ == "__main__":
    main()
