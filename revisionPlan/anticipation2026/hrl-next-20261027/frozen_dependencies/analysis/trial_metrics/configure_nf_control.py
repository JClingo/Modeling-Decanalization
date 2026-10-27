"""Set CCC on an isolated copy of the saved NF project; preserve source assets."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
assert root.parent.name in ('NFControl20261017','NFRecovery20261017')
original=root.parents[2]
for name in ['Agent/BP_GameMode','Learning/BP_AgentManager']:
    bp=unreal.load_asset('/Game/'+name);cdo=unreal.get_default_object(bp.generated_class())
    if name.endswith('BP_GameMode'):
        assert not cdo.get_editor_property('IsHRL') and cdo.get_editor_property('IsTrialMode')
        assert cdo.get_editor_property('TrialsToRun') in (1,250)
        cdo.set_editor_property('TrialsToRun',250)
        cdo.set_editor_property('TrialSequenceOrder','cdr' if '-NFRecoveryCDR' in unreal.SystemLibrary.get_command_line() else 'ccc')
        if '-NFControlSmoke' in unreal.SystemLibrary.get_command_line():cdo.set_editor_property('TrialsToRun',1)
    else:
        assert cdo.get_editor_property('Run Inference')
        for field,kind in [('EncoderSnapshot','encoder'),('PolicySnapshot','policy'),('Decoder Snapshot','decoder')]:
            path=original/'analysis/snapshots/Winning NF'/(kind+'_5000 - Copy.bin');assert path.is_file()
            cdo.set_editor_property(field,unreal.FilePath(file_path=str(path)))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp);assert unreal.EditorAssetLibrary.save_asset('/Game/'+name,False)
unreal.log('NF_CONTROL_COPY_CONFIGURED')
