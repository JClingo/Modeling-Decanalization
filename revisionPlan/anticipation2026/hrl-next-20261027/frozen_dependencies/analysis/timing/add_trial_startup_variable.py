import unreal
bp=unreal.load_asset('/Game/Agent/BP_GameMode')
assert unreal.BlueprintEditorLibrary.add_member_variable(bp,'HasInitializedTrialRun',unreal.BlueprintEditorLibrary.get_basic_type_by_name('bool'))
unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'HasInitializedTrialRun',False)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset('/Game/Agent/BP_GameMode',False)
