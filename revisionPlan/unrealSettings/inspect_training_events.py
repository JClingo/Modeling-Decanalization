"""Read retained TensorBoard records for the two checkpoint-matched runs."""
import json
from pathlib import Path
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

PROJECT = Path(r"C:\Users\jingo\Documents\Unreal Projects\decanalization")
ROOT = Path(__file__).resolve().parent
results = []
for run, folder in (("Training_ppo_sharedmemory_2025-05-25_19-45-04", "Training_ppo_sharedmemory_2025-05-25_19-45-04"),
                    ("Training_ppo_sharedmemory_2025-05-25_20-27-19", "NF-Final")):
    directory = PROJECT / "Intermediate/LearningAgents/Tensorboard/runs" / folder
    if not directory.exists():
        results.append({"run": run, "present": False})
        continue
    ea = EventAccumulator(str(directory), size_guidance={"scalars": 0})
    ea.Reload()
    scalars = {}
    for tag in ea.Tags().get("scalars", []):
        events = ea.Scalars(tag)
        scalars[tag] = {"count": len(events), "first_step": min(e.step for e in events),
                        "last_step": max(e.step for e in events), "first_wall_time": events[0].wall_time,
                        "last_wall_time": events[-1].wall_time, "last_value": events[-1].value}
    results.append({"run": run, "folder": folder, "present": True,
                    "folder_match_basis": "Exact run name" if run == folder else "NF-Final folder; event file creation epoch is 3 seconds after the matching trainer timestamp (local PDT)",
                    "files": [str(p) for p in directory.iterdir()], "scalars": scalars})
(ROOT / "training_event_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
for row in results:
    print(row["run"], {k: v for k, v in row.get("scalars", {}).items() if k in ("experience/avg_reward", "loss/policy")})
