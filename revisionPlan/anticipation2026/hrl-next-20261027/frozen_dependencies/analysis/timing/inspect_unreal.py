"""Read-only load/defaults audit. Run with Unreal's PythonScript commandlet."""
import json
import pathlib
import unreal

out = pathlib.Path(unreal.Paths.project_saved_dir()) / "TimingFix"
report = {}
assets = {
    "Agent": ("/Game/Agent/BP_Agent", ["BaseMaxSpeed", "PrevDeltaSeconds"]),
    "GameMode": ("/Game/Agent/BP_GameMode", ["IsTraining", "PeriodTickLength", "BasePassiveLossRate", "PassiveLossRate", "HomeostaticPeriodsElapsed", "TotalTickCount"]),
    "Manager": ("/Game/Learning/BP_AgentManager", ["Training Game Settings", "Run Inference"]),
    "Interactor": ("/Game/Learning/BP_AgentInteractor", []),
    "TrainingEnv": ("/Game/Learning/BP_AgentTrainingEnv", []),
}
for name, (path, properties) in assets.items():
    bp = unreal.load_asset(path)
    if bp is None:
        raise RuntimeError("Cannot load " + path)
    cdo = unreal.get_default_object(bp.generated_class())
    item = {"path": path, "class": str(bp.generated_class()), "defaults": {}}
    for prop in properties:
        try:
            item["defaults"][prop] = str(cdo.get_editor_property(prop))
        except Exception as exc:
            item["defaults"][prop] = {"error": str(exc)}
    if name == "Agent":
        movement = cdo.get_editor_property("character_movement")
        for prop in ["max_walk_speed", "min_analog_walk_speed", "max_acceleration", "ground_friction", "braking_deceleration_walking"]:
            item["defaults"][prop] = movement.get_editor_property(prop)
    report[name] = item
    unreal.log("TIMING_AUDIT " + name + " " + json.dumps(item))
out.mkdir(parents=True, exist_ok=True)
(out / "unreal_defaults.json").write_text(json.dumps(report, indent=2))
for kind in ['Encoder', 'Policy', 'Decoder', 'Critic']:
    network = unreal.load_asset('/Game/Learning/DA_Agent' + kind)
    network.save_network_to_snapshot(unreal.FilePath(file_path=str(out / ('embedded_' + kind.lower() + '.bin'))))
