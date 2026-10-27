"""Compile/save only the production GameMode trial YAML graph (no play/training)."""
import unreal

path='/Game/Agent/BP_GameMode'
bp=unreal.load_asset(path)
assert bp, path
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset(path,False)
unreal.log('TRIAL_YAML_COMPILED')
