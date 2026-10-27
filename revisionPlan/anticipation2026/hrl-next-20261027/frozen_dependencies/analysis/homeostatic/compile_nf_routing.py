import unreal
bp=unreal.load_asset('/Game/Learning/BP_AgentManager')
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentManager',False)
unreal.log('NF_ROUTING_COMPILED')
