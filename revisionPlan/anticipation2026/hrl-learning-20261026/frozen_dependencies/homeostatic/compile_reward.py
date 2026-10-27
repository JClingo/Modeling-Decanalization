import unreal
bp=unreal.load_asset('/Game/Learning/BP_AgentTrainingEnv')
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentTrainingEnv',False)
unreal.log('HOMEOSTATIC_COMPILE_COMPLETE')
