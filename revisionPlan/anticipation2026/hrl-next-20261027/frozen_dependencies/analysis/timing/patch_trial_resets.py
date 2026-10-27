"""Replace only the completed-trial reset with Learning Agents ResetAllAgents."""
import copy
import json
from pathlib import Path
from patch_graphs import Editor, prop

root = Path('Saved/TrialResetFix')
ed = Editor(json.loads((root / 'BP_GameMode.json').read_text(encoding='utf-8')))
run_trial = ed.e(118)['OuterIndex']
# LearningAgentsManager belongs to its plugin module, not /Script/Engine.
package = copy.deepcopy(next(x for x in ed.a['Imports'] if x['ClassName']=='Package'))
package['ObjectName'] = '/Script/LearningAgents'
ed.fname(package['ObjectName'])
ed.a['Imports'].append(package)
ed.a['ImportBits'].append(True)
package_index = -len(ed.a['Imports'])
cls = copy.deepcopy(next(x for x in ed.a['Imports'] if x['ObjectName']=='LearningAgentsTrainingEnvironment'))
cls['ObjectName'] = 'LearningAgentsManager'
cls['OuterIndex'] = package_index
ed.fname(cls['ObjectName'])
ed.a['Imports'].append(cls)
ed.a['ImportBits'].append(True)
la_class = -len(ed.a['Imports'])
manager_class = next(-i for i,x in enumerate(ed.a['Imports'],1) if x['ObjectName']=='BP_AgentManager_C')

def node(template, name, function, specs, x, y):
    old_outer = ed.e(template)['OuterIndex']
    ed.e(template)['OuterIndex'] = run_trial
    idx = ed.node(template, name, function, specs, x, y)
    ed.e(template)['OuterIndex'] = old_outer
    return idx

get_manager = node(633, 'K2Node_VariableGet_TrialAgentManager', '', [
    ('AgentManager',1,'object',manager_class), ('self',0,'object',0)], 1900, 1700)
get_la = node(635, 'K2Node_VariableGet_TrialLearningManager', '', [
    ('LearningAgentsManager',1,'object',la_class), ('self',0,'object',manager_class)], 2150, 1700)
ref = prop(ed.e(get_la), 'VariableReference')
ref['Value'] = [q for q in ref['Value'] if q['Name'] in ['MemberParent','MemberName']]
next(q for q in ref['Value'] if q['Name']=='MemberName')['Value'] = 'LearningAgentsManager'
ed.fname('LearningAgentsManager')
reset = node(232, 'K2Node_CallFunction_ResetBetweenTrials', 'ResetAllAgents', [
    ('execute',0,'exec'), ('then',1,'exec'), ('self',0,'object',la_class)], 2400, 1500)
ref = prop(ed.e(reset), 'FunctionReference')
parent = copy.deepcopy(next(q for q in prop(ed.e(227),'FunctionReference')['Value'] if q['Name']=='MemberParent'))
parent['Value'] = la_class
ref['Value'] = [parent, next(q for q in ref['Value'] if q['Name']=='MemberName')]
ed.connect(get_manager,'AgentManager',get_la,'self')
ed.connect(get_la,'LearningAgentsManager',reset,'self')
ed.rewire(408,'else',reset,'execute')
# The phase transition branch and trial logging/increment/quit paths are intact.
ed.save('BP_GameMode')
(root / 'BP_GameMode.patched.json').write_text(json.dumps(ed.a),encoding='utf-8')
