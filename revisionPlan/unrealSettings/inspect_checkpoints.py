"""Decode checkpoint topology with the installed Unreal serializer; never train."""
import io
import json
from pathlib import Path
import struct
import sys

ENGINE = Path(r"C:\Program Files\Epic Games\UE_5.5\Engine")
PROJECT = Path(r"C:\Users\jingo\Documents\Unreal Projects\decanalization")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE / "Plugins/Experimental/NNERuntimeBasicCpu/Content/Python"))
import nne_runtime_basic_cpu as nne
import numpy as np

def simplify(value):
    if isinstance(value, np.ndarray):
        result = {"shape": list(value.shape), "elements": value.size, "dtype": str(value.dtype)}
        if value.size <= 16:
            result["values"] = value.tolist()
        return result
    if isinstance(value, dict):
        return {k: simplify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [simplify(v) for v in value]
    return value

def linear_parameters(layer):
    if isinstance(layer, dict):
        own = sum(layer[k].size for k in ("Weights", "Biases") if k in layer and isinstance(layer[k], np.ndarray)) if layer.get("Type") in ("Linear", "MultiLinear") else 0
        return own + sum(linear_parameters(v) for v in layer.values() if isinstance(v, (dict, list)))
    if isinstance(layer, list):
        return sum(linear_parameters(x) for x in layer)
    return 0

def parameter_count(layer):
    if isinstance(layer, dict):
        keys = {"Linear": ("Weights", "Biases"), "MultiLinear": ("Weights", "Biases"),
                "Normalize": ("Mean", "Std"), "Denormalize": ("Mean", "Std")}.get(layer.get("Type"), ())
        own = sum(layer[k].size for k in keys)
        return own + sum(parameter_count(v) for v in layer.values() if isinstance(v, (dict, list)))
    if isinstance(layer, list):
        return sum(parameter_count(x) for x in layer)
    return 0

paths = list(PROJECT.joinpath("Intermediate/LearningAgents/Snapshots").rglob("*.bin"))
paths += list(ROOT.joinpath("raw").rglob("*.bin"))
results = []
for path in sorted(paths):
    data = path.read_bytes()
    header = struct.unpack("<6I", data[:24])
    assert header[:2] == (0x1e9b0c80, 1) and len(data) == header[5] + 24
    payload = np.frombuffer(data[24:], dtype=np.uint8)
    offset, layer = nne.serialization_load_model(0, payload)
    assert offset == len(payload)
    results.append({"file": str(path), "input_size": header[2], "output_size": header[3],
                    "linear_weight_and_bias_count": linear_parameters(layer),
                    "trainable_parameter_count": parameter_count(layer), "topology": simplify(layer)})
(ROOT / "checkpoint_architectures.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
for row in results:
    if "policy_1000" in row["file"] or "policy_4000" in row["file"]:
        print(row["file"], row["input_size"], row["output_size"], row["linear_weight_and_bias_count"])
