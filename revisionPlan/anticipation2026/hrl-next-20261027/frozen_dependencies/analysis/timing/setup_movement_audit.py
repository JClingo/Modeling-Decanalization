"""Configure inference only in the isolated MovementAudit/TestProject copy."""
import pathlib
import unreal

project = pathlib.Path(unreal.Paths.project_dir()).resolve()
assert project.name == 'TestProject' and project.parent.name == 'MovementAudit'
snapshots = project.parent / 'checkpoint'
bp = unreal.load_asset('/Game/Learning/BP_AgentManager')
cdo = unreal.get_default_object(bp.generated_class())
fields = [('encoder','EncoderSnapshot'),('policy','PolicySnapshot'),
          ('decoder','Decoder Snapshot'),('critic','Critic Snapshot')]
def configure(o):
    o.set_editor_property('Run Inference', True)
    for k,field in fields:
        o.set_editor_property(field, unreal.FilePath(file_path=str(snapshots/(k+'.bin'))))
configure(cdo)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentManager', False)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level('/Game/Level/Landscape')
unreal.SystemLibrary.execute_console_command(
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(), 'QUIT_EDITOR')
