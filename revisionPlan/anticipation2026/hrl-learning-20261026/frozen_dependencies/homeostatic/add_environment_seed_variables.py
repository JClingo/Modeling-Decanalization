import unreal
bp=unreal.load_asset('/Game/Agent/BP_GameMode')
for name,value in [('TrainingEnvironmentSeed',1),('TrialEnvironmentSeed',10001),('ActiveEnvironmentSeed',1)]:
 assert unreal.BlueprintEditorLibrary.add_member_variable(bp,name,unreal.BlueprintEditorLibrary.get_basic_type_by_name('int'))
 unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,False)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 unreal.get_default_object(bp.generated_class()).set_editor_property(name,value)
assert unreal.EditorAssetLibrary.save_asset('/Game/Agent/BP_GameMode',False)
