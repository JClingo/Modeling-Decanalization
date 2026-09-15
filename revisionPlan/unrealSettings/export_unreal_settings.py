"""Read-only Unreal 5.5 asset/settings export; run with PythonScriptCommandlet.

Does not start PIE, train, compile explicitly, or save any Unreal assets.
Output is written beside this script under raw/current.
"""
import json
import os
from pathlib import Path
import traceback
import unreal

OUT = Path(__file__).resolve().parent / "raw" / os.environ.get("UE_SETTINGS_LABEL", "current")
OUT.mkdir(parents=True, exist_ok=True)
report = {"engine_version": unreal.SystemLibrary.get_engine_version(), "exports": [], "errors": []}

def export(obj, name):
    task = unreal.AssetExportTask()
    task.object = obj
    task.filename = str(OUT / (name + ".t3d"))
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    task.exporter = unreal.ObjectExporterT3D()
    ok = unreal.Exporter.run_asset_export_task(task)
    report["exports"].append({"object": obj.get_path_name(), "file": name + ".t3d", "success": ok, "errors": list(task.errors)})

paths = [
    "/Game/Agent/BP_Agent", "/Game/Agent/BP_GameMode",
    "/Game/Learning/BP_AgentManager", "/Game/Learning/BP_AgentInteractor",
    "/Game/Learning/BP_AgentTrainingEnv", "/Game/Level/BP_Tile",
    "/Game/Level/BP_TileSpawner",
    "/Game/Resource/BP_Resource", "/Game/Resource/BP_ResourceSpawner",
    "/Game/Libraries/BFL_Common", "/Game/Learning/DA_AgentPolicy",
    "/Game/Learning/DA_AgentCritic", "/Game/Learning/DA_AgentEncoder",
    "/Game/Learning/DA_AgentDecoder",
]
for path in paths:
    try:
        obj = unreal.load_asset(path)
        if obj is None:
            raise RuntimeError("Asset not found: " + path)
        export(obj, path.rsplit("/", 1)[1])
        if isinstance(obj, unreal.LearningAgentsNeuralNetwork):
            obj.save_network_to_snapshot(unreal.FilePath(str(OUT / (obj.get_name() + ".bin"))))
        if isinstance(obj, unreal.Blueprint):
            cls = unreal.load_class(None, path + "." + path.rsplit("/", 1)[1] + "_C")
            export(unreal.get_default_object(cls), path.rsplit("/", 1)[1] + "_defaults")
    except Exception:
        report["errors"].append({"asset": path, "traceback": traceback.format_exc()})

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Level/Landscape")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    export(world.get_world_settings(), "Landscape_WorldSettings")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    report["actors"] = [{"path": a.get_path_name(), "label": a.get_actor_label(), "class": a.get_class().get_path_name()} for a in actors]
    for i, actor in enumerate(actors):
        if "BP_" in actor.get_class().get_name() or actor.get_class().get_name() == "WorldSettings":
            export(actor, "Landscape_actor_%03d_%s" % (i, actor.get_class().get_name()))
except Exception:
    report["errors"].append({"map": "Landscape", "traceback": traceback.format_exc()})

(OUT / "export_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("SETTINGS_EXPORT_COMPLETE " + str(OUT))
