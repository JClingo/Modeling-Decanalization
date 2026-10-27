"""Configure an isolated copy for frozen-checkpoint reset comparisons."""
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir()).resolve()
assert project.parent.name == 'ResetPerformanceAudit'
for asset, fields in [
    ('/Game/Agent/BP_GameMode', ['Setpoints', 'RandomStream', 'TotalTickCount', 'HasInitializedTrialRun']),
    ('/Game/Agent/BP_Agent', ['AnticipatedResourceGain', 'AnticipatedResourceLoss', 'MaxSpeed']),
    ('/Game/Resource/BP_Resource', ['BaseHomeostaticImpact', 'HomeostaticImpact', 'OverlapCount']),
    ('/Game/Level/BP_Tile', ['HomeostaticImpact', 'OverlapCount']),
]:
    bp = unreal.load_asset(asset)
    for field in fields:
        # The pre-startup GameMode has no one-time flag.
        if field == 'HasInitializedTrialRun':
            try: unreal.get_default_object(bp.generated_class()).get_editor_property(field)
            except Exception: continue
        unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp, field, True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if asset.endswith('BP_GameMode'):
        cdo = unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property('TrialsToRun', 1)
        cdo.set_editor_property('IsTrialMode', True)
    assert unreal.EditorAssetLibrary.save_asset(asset, False)
bp = unreal.load_asset('/Game/Learning/BP_AgentManager')
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property('Run Inference', True)
snapshot = Path('D:/Dev/decanalization/Intermediate/LearningAgents/Snapshots')
for kind, field in [('encoder', 'EncoderSnapshot'), ('policy', 'PolicySnapshot'), ('decoder', 'Decoder Snapshot')]:
    path = snapshot / ('Training_ppo_sharedmemory_2026-10-14_16-11-38_' + kind + '_6000.bin')
    assert path.exists(), path
    cdo.set_editor_property(field, unreal.FilePath(file_path=str(path)))
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentManager', False)
print('RESET_COMPARISON_CONFIGURED')
