import unreal
bp=unreal.load_asset('/Game/Agent/BP_GameMode')
assert unreal.BlueprintEditorLibrary.add_member_variable(bp,'TrialStartingHomeostaticState',unreal.BlueprintEditorLibrary.get_basic_type_by_name('real'))
unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'TrialStartingHomeostaticState',False)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset('/Game/Agent/BP_GameMode',False)
unreal.log('TRIAL_HOMEOSTASIS_VARIABLE_ADDED')
