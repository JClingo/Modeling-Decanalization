"""Add NF progress reward to the existing continuous HRL objective."""
import base64
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'timing'))
from patch_graphs import Editor,prop,string
from graph_asset import pins

root=Path('Saved/NFRewardFix')
ed=Editor(json.loads((root/'env.variables.json').read_text(encoding='utf-8-sig')))
def graph_name(e):return ed.e(e['OuterIndex'])['ObjectName'] if e['OuterIndex']>0 else ''
def find(name,graph='GatherAgentReward'):
    return next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']==name and graph_name(e)==graph)
def reference(i,key='VariableReference'):
    return next(x['Value'] for x in prop(ed.e(i),key)['Value'] if x['Name']=='MemberName')
def variable(name):
    return next(i for i,e in enumerate(ed.a['Exports'],1) if graph_name(e)=='GatherAgentReward'
                and e['ObjectName'].startswith('K2Node_VariableGet')
                and reference(i)==name)
def function(name):
    return next(i for i,e in enumerate(ed.a['Exports'],1) if graph_name(e)=='GatherAgentReward'
                and e['ObjectName'].startswith('K2Node_CallFunction')
                and reference(i,'FunctionReference')==name)

graph=ed.e(find('K2Node_Homeostatic_SelectObjective'))['OuterIndex']
get_template=variable('Max Setpoint Distance')
set_template=find('K2Node_Homeostatic_MarkFailure')
math_template=function('Abs')
branch_template=find('K2Node_Homeostatic_SelectObjective')
def node(template,name,function,specs,outer=None):
    oldpins=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[oldpins[-1]['end']:]
    old=ed.e(template)['OuterIndex'];ed.e(template)['OuterIndex']=outer or graph
    idx=ed.node(template,'K2Node_NF_'+name,function,specs,3000,200+len(ed.changed)*100)
    ed.e(template)['OuterIndex']=old
    ed.e(idx)['Extras']=base64.b64encode(base64.b64decode(ed.e(idx)['Extras'])+tail).decode()
    for p in list(pins(ed.a,ed.e(idx)))[::-1]:
        if p['default']:
            n=4+(len(p['auto_default'].encode())+1 if p['auto_default'] else 0)
            ed.replace(idx,p['default_end'],p['default_end']+n,string(''))
    return idx
def real(name,direction=0,default=''):return(name,direction,'real',0,default,'double')
def get(name,category='real'):
    idx=node(get_template,'Get'+name,'',[(name,1,category,0,'','double' if category=='real' else 'None'),('self',0,'object',0)])
    r=prop(ed.e(idx),'VariableReference')['Value']
    r[:]=[x for x in r if x['Name'] in ['MemberName','bSelfContext']]
    next(x for x in r if x['Name']=='MemberName')['Value']=name;ed.fname(name)
    return idx
def set_own(name,getter,category='real',default='',outer=None):
    idx=node(set_template,'Set'+name+str(len(ed.a['Exports'])),'',[
        ('execute',0,'exec'),('then',1,'exec'),(name,0,category,0,default,'double' if category=='real' else 'None'),
        ('Output_Get',1,category,0,'','double' if category=='real' else 'None'),('self',0,'object',0)],outer)
    prop(ed.e(idx),'VariableReference')['Value']=copy.deepcopy(prop(ed.e(getter),'VariableReference')['Value'])
    return idx
def math(name,fn,inputs,output=None):
    return node(math_template,name,fn,[('self',0,'object',-28)]+inputs+[output or real('ReturnValue',1)])
def branch(name):return node(branch_template,name,'',[('execute',0,'exec'),('Condition',0,'bool'),('then',1,'exec'),('else',1,'exec')])

cached=get('PreviousRewardState');valid=get('HasPreviousRewardState','bool')
previous=function('GetPreviousSetpoint');current=function('GetCurrentSetpoint')
mode=variable('IsHRL')
choose=branch('SelectHRLOrNF')
bound=find('K2Node_Homeostatic_FailureBoundary')
quality_set=find('K2Node_Homeostatic_SetQualityReward')
ed.rewire(bound,'else',choose,'execute')
ed.connect(mode,'IsHRL',choose,'Condition')
ed.connect(choose,'then',quality_set,'execute')

selected=math('PreviousDecisionState','SelectFloat',[real('A'),real('B'),('bPickA',0,'bool')])
ed.connect(cached,'PreviousRewardState',selected,'A')
ed.connect(previous,'Value',selected,'B')
ed.connect(valid,'HasPreviousRewardState',selected,'bPickA')
absolute_previous=math('PreviousDistance','Abs',[real('A')])
absolute_current=math('CurrentDistance','Abs',[real('A')])
progress=math('ProgressTowardZero','Subtract_DoubleDouble',[real('A'),real('B')])
positive=math('OnlyImprovement','FMax',[real('A'),real('B',default='0')])
normalized=math('NormalizedProgress','Divide_DoubleDouble',[real('A'),real('B')])
reward=math('ScaleProgressReward','Multiply_DoubleDouble',[real('A'),real('B')])
ed.connect(selected,'ReturnValue',absolute_previous,'A')
ed.connect(current,'setpoint',absolute_current,'A')
ed.connect(absolute_previous,'ReturnValue',progress,'A');ed.connect(absolute_current,'ReturnValue',progress,'B')
ed.connect(progress,'ReturnValue',positive,'A')
ed.connect(positive,'ReturnValue',normalized,'A')
ed.connect(find('K2Node_Homeostatic_SafeScale'),'ReturnValue',normalized,'B')
ed.connect(normalized,'ReturnValue',reward,'A')
ed.connect(find('K2Node_Homeostatic_SafeRate'),'ReturnValue',reward,'B')
negative=math('BelowZero','Less_DoubleDouble',[real('A'),real('B',default='0')],('ReturnValue',1,'bool'))
ed.connect(current,'setpoint',negative,'A')
gate=branch('OnlyNegativeState');ed.connect(choose,'else',gate,'execute');ed.connect(negative,'ReturnValue',gate,'Condition')
reward_template=quality_set
def set_reward(name):
    return node(reward_template,name,'',[('execute',0,'exec'),('then',1,'exec'),real('CurrentReward',default='0'),real('Output_Get',1)])
set_nf=set_reward('RewardProgress');set_zero=set_reward('ZeroReward')
ed.connect(gate,'then',set_nf,'execute');ed.connect(gate,'else',set_zero,'execute')
ed.connect(reward,'ReturnValue',set_nf,'CurrentReward')
total=find('K2Node_Homeostatic_SetTotalReward')
ed.connect(set_nf,'then',total,'execute');ed.connect(set_zero,'then',total,'execute')

# NF is reward-only: even failure at/above zero receives zero, not an HRL penalty.
failure_choice=branch('FailureRewardMode')
terminal=find('K2Node_Homeostatic_MarkFailure');failure_set=find('K2Node_Homeostatic_SetFailureReward')
ed.rewire(terminal,'then',failure_choice,'execute')
ed.connect(mode,'IsHRL',failure_choice,'Condition')
ed.connect(failure_choice,'then',failure_set,'execute');ed.connect(failure_choice,'else',set_zero,'execute')

# Cache once per reward decision, including HRL phases, so phase continuity holds.
save_state=set_own('PreviousRewardState',cached)
save_valid=set_own('HasPreviousRewardState',valid,'bool','true')
increment=find('K2Node_Homeostatic_CountDecision')
ed.rewire(total,'then',save_state,'execute')
ed.connect(current,'setpoint',save_state,'PreviousRewardState')
ed.connect(save_state,'then',save_valid,'execute');ed.connect(save_valid,'then',increment,'execute')

# Episode/trial resets must invalidate the cache before the new world state is seeded.
result=next(i for i,e in enumerate(ed.a['Exports'],1) if graph_name(e)=='Initialize' and e['ObjectName'].startswith('K2Node_FunctionResult'))
outer=ed.e(result)['OuterIndex']
reset_valid=set_own('HasPreviousRewardState',valid,'bool','false',outer)
reset_state=set_own('PreviousRewardState',cached,'real','0',outer)
old_links=list(ed.p(result,'execute')['links'])
ed.disconnect(result,'execute')
for idx,guid in old_links:
    name=next(p['name'] for p in pins(ed.a,ed.e(idx)) if p['guid']==guid)
    ed.connect(idx,name,reset_valid,'execute')
ed.connect(reset_valid,'then',reset_state,'execute');ed.connect(reset_state,'then',result,'execute')
ed.save('BP_AgentTrainingEnv')
(root/'env.patched.json').write_text(json.dumps(ed.a))
