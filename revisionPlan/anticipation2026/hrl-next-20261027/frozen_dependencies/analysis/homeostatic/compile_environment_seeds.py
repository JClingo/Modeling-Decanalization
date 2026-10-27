"""Compile and save the two environment RNG Blueprints without starting play."""
import unreal

for path in ('/Game/Agent/BP_GameMode', '/Game/Resource/BP_ResourceSpawner'):
    bp = unreal.load_asset(path)
    assert bp, path
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert unreal.EditorAssetLibrary.save_asset(path, False), path
unreal.log('ENVIRONMENT_RNG_BLUEPRINTS_COMPILED')
