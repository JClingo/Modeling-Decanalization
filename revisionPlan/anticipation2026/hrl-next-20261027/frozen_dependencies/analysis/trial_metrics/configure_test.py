"""Configure isolated two-trial smoke tests, never production defaults."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve();assert root.parent.name=='TrialMetricsFix'
command=unreal.SystemLibrary.get_command_line();mode='NF' if '-MetricsNF' in command else 'HRL'
for asset,fields in [('Agent/BP_GameMode',['TotalTickCount','IsHRL','Setpoints','HasInitializedTrialRun']),('Learning/BP_AgentManager',['Run Inference']),('Learning/BP_AgentTrainingEnv',['Episode Steps','PreviousRewardState','HasPreviousRewardState','ShouldTerminate'])]:
    bp=unreal.load_asset('/Game/'+asset)
    for field in fields:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
    cdo=unreal.get_default_object(bp.generated_class())
    if asset.endswith('BP_GameMode'):
        cdo.set_editor_property('TrialSequenceOrder','ccc' if '-MetricsCCC' in command else 'cdr');cdo.set_editor_property('TrialsToRun',2);cdo.set_editor_property('IsHRL',mode=='HRL');cdo.set_editor_property('IsTrialMode',True)
    if asset.endswith('BP_AgentManager'):
        cdo.set_editor_property('Run Inference',True)
        for field,kind in [('EncoderSnapshot','encoder'),('PolicySnapshot','policy'),('Decoder Snapshot','decoder')]:
            iteration=10000 if mode=='HRL' else 5000
            original=root.parents[2]/'analysis/snapshots'/('Winning '+mode)/(f'{kind}_{iteration} - Copy.bin')
            cdo.set_editor_property(field,unreal.FilePath(file_path=str(original)))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);assert unreal.EditorAssetLibrary.save_asset('/Game/'+asset,False)
unreal.log('TRIAL_METRICS_TEST_CONFIGURED '+mode)
