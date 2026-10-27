"""Compile staged changes in Unreal and save only the explicitly affected assets."""
import json
import pathlib
import unreal

results = {}
for path in ['/Game/Agent/BP_GameMode', '/Game/Agent/BP_Agent', '/Game/Learning/BP_AgentManager', '/Game/Learning/BP_AgentInteractor', '/Game/Learning/BP_AgentTrainingEnv']:
    bp = unreal.load_asset(path)
    if bp is None: raise RuntimeError('Cannot load ' + path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    # Status is protected in Python. Treat the commandlet's compiler errors and
    # exit code as authoritative, then inspect saved Blueprint status offline.
    results[path] = 'compile invoked'
    unreal.log('TIMING_COMPILE ' + path)
for path in ['/Game/Agent/BP_GameMode', '/Game/Agent/BP_Agent', '/Game/Learning/BP_AgentManager']:
    if not unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False):
        raise RuntimeError('Save failed: ' + path)
root = pathlib.Path(unreal.Paths.project_saved_dir()) / 'TimingFix'
(root / 'compile_results.json').write_text(json.dumps(results, indent=2))
