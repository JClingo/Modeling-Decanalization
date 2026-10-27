from pathlib import Path
import unreal
assert Path(unreal.Paths.project_dir()).resolve().parent.name=='PhaseVelocityFix'
for path, fields in [('/Game/Agent/BP_GameMode',['TotalTickCount','HasInitializedTrialRun','IsHRL','Setpoints']),
                     ('/Game/Agent/BP_Agent',['BaseMaxSpeed']),
                     ('/Game/Learning/BP_AgentManager',['Run Inference'])]:
    bp=unreal.load_asset(path)
    for field in fields: unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if path.endswith('BP_GameMode'):
        cdo=unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property('TrialsToRun',10)
    assert unreal.EditorAssetLibrary.save_asset(path,False)
unreal.log('PHASE_VELOCITY_TEST_CONFIGURED')
