"""Compile staged copies only, retaining production defaults for installation."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
assert root.name=='TestProject' and root.parent.name=='TrialMetricsFix'
for name in ['/Game/Libraries/BFL_Common','/Game/Learning/BP_AgentTrainingEnv','/Game/Agent/BP_GameMode']:
    bp=unreal.load_asset(name);assert bp
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert unreal.EditorAssetLibrary.save_asset(name,False)
unreal.log('TRIAL_METRICS_COMPILED')
