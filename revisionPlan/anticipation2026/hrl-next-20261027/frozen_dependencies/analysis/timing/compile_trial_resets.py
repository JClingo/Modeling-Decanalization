import unreal

for path in ['/Game/Agent/BP_GameMode', '/Game/Agent/BP_Agent',
             '/Game/Learning/BP_AgentManager', '/Game/Learning/BP_AgentTrainingEnv']:
    bp = unreal.load_asset(path)
    if bp is None: raise RuntimeError('Cannot load ' + path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.log('TRIAL_RESET_COMPILE ' + path)
    if path == '/Game/Agent/BP_GameMode':
        if not unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False):
            raise RuntimeError('Cannot save ' + path)
