import unreal
for path in ['/Game/Agent/BP_Agent', '/Game/Agent/BP_GameMode']:
    bp=unreal.load_asset(path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert unreal.EditorAssetLibrary.save_asset(path,False)
unreal.log('PHASE_VELOCITY_COMPILED')
