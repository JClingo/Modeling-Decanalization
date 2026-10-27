import unreal

for path in ['/Game/Agent/BP_Agent', '/Game/Learning/BP_AgentTrainingEnv',
             '/Game/Learning/BP_AgentManager', '/Game/Learning/BP_AgentInteractor', '/Game/Agent/BP_GameMode']:
    bp = unreal.load_asset(path)
    if bp is None:
        raise RuntimeError('Missing ' + path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.log('RESET_COMPILE ' + path)
    if path in ['/Game/Agent/BP_Agent', '/Game/Learning/BP_AgentTrainingEnv']:
        if not unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False):
            raise RuntimeError('Cannot save ' + path)
