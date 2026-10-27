"""Configure the project-local trainer and conservative PPO safeguards."""
import pathlib
import unreal

project=pathlib.Path(unreal.Paths.project_dir()).resolve()
bp=unreal.load_asset('/Game/Learning/BP_AgentManager')
cdo=unreal.get_default_object(bp.generated_class())
settings=cdo.get_editor_property('Trainer Training Settings')
for name,value in [('minimum_advantage',-10.0),('action_entropy_weight',0.001),
                   ('use_grad_norm_max_clipping',True),('grad_norm_max',0.5),
                   ('number_of_steps_to_trim_at_start_of_episode',0)]:
    settings.set_editor_property(name,value)
cdo.set_editor_property('Trainer Training Settings',settings)
process=cdo.get_editor_property('Trainer Process Settings')
process.set_editor_property('custom_trainer_module_path',unreal.DirectoryPath(path=str(project/'analysis/homeostatic')))
process.set_editor_property('trainer_file_name','homeostatic_ppo')
cdo.set_editor_property('Trainer Process Settings',process)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentManager',False)
unreal.log('HOMEOSTATIC_TRAINER_CONFIGURED')
