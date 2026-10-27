"""Compile/save only the world reset assets without starting simulation."""
import unreal
for path in ['/Game/Level/BP_Tile','/Game/Resource/BP_Resource']:
 bp=unreal.load_asset(path);assert bp,path
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 assert unreal.EditorAssetLibrary.save_asset(path,False),path
unreal.log('TRIAL_WORLD_RESET_COMPILED')
