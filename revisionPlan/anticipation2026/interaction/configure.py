"""Configure only an explicitly marked disposable recanalization project."""
import json,pathlib,unreal
p=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert (p/'INTERACTION_EVALUATION_COPY').exists()
s=json.loads((p/'evaluation_settings.json').read_text())
def default(path):
    bp=unreal.load_asset(path)
    return bp,unreal.get_default_object(bp.generated_class())
bp,c=default('/Game/Agent/BP_GameMode')
for name,value in [('IsTrialMode',True),('IsTraining',False),('IsHRL',True),
                   ('TrialsToRun',s['trials']),('TrialSequenceOrder','cdr'),('TrialEnvironmentSeed',10001)]:
    c.set_editor_property(name,value)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
bp,c=default('/Game/Level/BP_Tile')
c.set_editor_property('DecanalizationRateFactor',float(s['factor']))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
bp,c=default('/Game/Learning/BP_AgentManager')
c.set_editor_property('Run Inference',True)
props={'EncoderSnapshot':'encoder','PolicySnapshot':'policy','Decoder Snapshot':'decoder','Critic Snapshot':'critic'}
for prop,kind in props.items():c.set_editor_property(prop,unreal.FilePath(file_path=s['snapshots'][kind]['path']))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Level/Landscape')
cls=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
for actor in unreal.GameplayStatics.get_all_actors_of_class(world,cls):
    actor.set_editor_property('Run Inference',True)
    for prop in props:actor.set_editor_property(prop,c.get_editor_property(prop))
assert unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/Level/Landscape')
(p/'configured.json').write_text(json.dumps(s,indent=2))
unreal.log('RECANALIZATION_CONFIGURED '+s['condition'])
