"""Editor preparation in a marked disposable copy only."""
from pathlib import Path
import sys
import unreal
project=Path(unreal.Paths.project_dir()).resolve()
assert (project/'HRL_LEARNING_COPY').exists()
sys.path.insert(0,str(project/'analysis/hrl_learning'))
from metrics import COUNTERS
bp=unreal.load_asset('/Game/Learning/BP_AgentTrainingEnv')
for name,kind,value in [('UseAbsoluteErrorReward','bool',False),('RecordDecisionHomeostasis','bool',False)]+[(n,'real',0.) for n in COUNTERS]:
    pin=unreal.BlueprintEditorLibrary.get_basic_type_by_name(kind)
    try:unreal.get_default_object(bp.generated_class()).get_editor_property(name)
    except Exception:assert unreal.BlueprintEditorLibrary.add_member_variable(bp,name,pin),name
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.get_default_object(bp.generated_class()).set_editor_property(name,value)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentTrainingEnv',False)
unreal.log('HRL_LEARNING_VARIABLES_READY')
bp=unreal.load_asset('/Game/Learning/BP_AgentManager')
for name,kind,value in [('InitializationSeed','int',1234),('ResetWorldOnPolicyUpdate','bool',True)]:
    pin=unreal.BlueprintEditorLibrary.get_basic_type_by_name(kind)
    try:unreal.get_default_object(bp.generated_class()).get_editor_property(name)
    except Exception:assert unreal.BlueprintEditorLibrary.add_member_variable(bp,name,pin),name
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,name,True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.get_default_object(bp.generated_class()).set_editor_property(name,value)
assert unreal.EditorAssetLibrary.save_asset('/Game/Learning/BP_AgentManager',False)
unreal.log('HRL_LEARNING_INITIALIZATION_AND_RESET_CONTROLS_READY')
