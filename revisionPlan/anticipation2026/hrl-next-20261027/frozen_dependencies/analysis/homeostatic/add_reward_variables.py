import unreal
bp=unreal.load_asset('/Game/Learning/BP_AgentTrainingEnv')
for name,category,sub,value in [
 ('UseHomeostaticReward','bool','',True),
 ('RewardDistanceScale','real','double',25.0),
 ('HomeostaticRewardRate','real','double',1.0),
 ('HomeostaticFailureReward','real','double',-1.0)]:
 pin=unreal.BlueprintEditorLibrary.get_basic_type_by_name(category)
 assert unreal.BlueprintEditorLibrary.add_member_variable(bp,name,pin),name
 unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,False)
 unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 unreal.get_default_object(bp.generated_class()).set_editor_property(name,value)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentTrainingEnv',False)
unreal.log('HOMEOSTATIC_VARIABLES_READY')
