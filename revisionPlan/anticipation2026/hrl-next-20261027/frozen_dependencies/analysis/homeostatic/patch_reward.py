"""Stage a continuous homeostatic objective while retaining legacy reward mode.

Input: Saved/HomeostaticFix/env.variables.json, exported after adding controls.
Compile the staged Blueprint with Unreal before using it.
"""
import copy
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'timing'))
from patch_graphs import Editor, prop, string
from graph_asset import pins

root=Path('Saved/HomeostaticFix')
ed=Editor(json.loads((root/'env.variables.json').read_text(encoding='utf-8-sig')))
graph=ed.e(155)['OuterIndex']
assert ed.e(graph)['ObjectName']=='GatherAgentReward'

def node(template,name,function,specs):
    old_pins=pins(ed.a,ed.e(template))
    suffix=base64.b64decode(ed.e(template)['Extras'])[old_pins[-1]['end']:]
    old=ed.e(template)['OuterIndex']; ed.e(template)['OuterIndex']=graph
    idx=ed.node(template,'K2Node_Homeostatic_'+name,function,specs,2200,200+len(ed.changed)*90)
    ed.e(template)['OuterIndex']=old
    ed.e(idx)['Extras']=base64.b64encode(base64.b64decode(ed.e(idx)['Extras'])+suffix).decode()
    # Keep explicit constants through Unreal's pin reconstruction. They are
    # authored overrides, not defaults inherited from the new native function.
    for p in list(pins(ed.a,ed.e(idx)))[::-1]:
        if p['default']:
            start=p['default_end']
            length=4+(len(p['auto_default'].encode())+1 if p['auto_default'] else 0)
            ed.replace(idx,start,start+length,string(''))
    return idx

def real(name,direction=0,default=''):
    return (name,direction,'real',0,default,'double')

def get(name,category='real'):
    idx=node(364,'Get'+name,'',[
        (name,1,category,0,'','double' if category=='real' else 'None'),
        ('self',0,'object',0)])
    r=prop(ed.e(idx),'VariableReference')
    r['Value']=[x for x in r['Value'] if x['Name'] in ['MemberName','bSelfContext']]
    next(x for x in r['Value'] if x['Name']=='MemberName')['Value']=name
    ed.fname(name)
    return idx

def math(name,function,inputs):
    return node(52,name,function,[('self',0,'object',-28)]+inputs+[real('ReturnValue',1)])

def branch(name):
    return node(204,name,'',[('execute',0,'exec'),('Condition',0,'bool',0,'true'),
                            ('then',1,'exec'),('else',1,'exec')])

def set_reward(name):
    return node(414,name,'',[('execute',0,'exec'),('then',1,'exec'),
                           real('CurrentReward'),real('Output_Get',1)])

enabled=get('UseHomeostaticReward','bool')
scale=get('RewardDistanceScale')
rate=get('HomeostaticRewardRate')
failure=get('HomeostaticFailureReward')
choose=branch('SelectObjective'); active=branch('AlreadyTerminated'); bound=branch('FailureBoundary')
ed.rewire(155,'then',choose,'execute')
ed.connect(enabled,'UseHomeostaticReward',choose,'Condition')
ed.connect(choose,'else',204,'execute')
ed.connect(choose,'then',active,'execute')
ed.connect(387,'ShouldTerminate',active,'Condition')
zero=node(167,'AlreadyDone','GatherAgentReward',[('execute',0,'exec'),('OutReward',0,'real',0,'0','float')])
ed.connect(active,'then',zero,'execute')
ed.connect(active,'else',bound,'execute')
ed.connect(284,'ReturnValue',bound,'Condition')

# Smooth positive quality: dt*rate/(1+(h/scale)^2). No flat regions or sign bias.
safe_scale=math('SafeScale','FMax',[real('A'),real('B',default='0.001')])
safe_rate=math('SafeRate','FMax',[real('A'),real('B',default='0')])
normal=math('NormalizedDistance','Divide_DoubleDouble',[real('A'),real('B')])
square=math('SquaredDistance','Multiply_DoubleDouble',[real('A'),real('B')])
denom=math('QualityDenominator','Add_DoubleDouble',[real('A',default='1'),real('B')])
quality=math('Quality','Divide_DoubleDouble',[real('A'),real('B')])
reward=math('TimeIntegratedQuality','Multiply_DoubleDouble',[real('A'),real('B')])
delta=node(52,'DeltaSeconds','GetWorldDeltaSeconds',[
    ('self',0,'object',0),('WorldContextObject',0,'object',0),real('ReturnValue',1)])
gameplay_import=copy.deepcopy(ed.a['Imports'][27])
assert gameplay_import['ObjectName']=='KismetMathLibrary'
gameplay_import['ObjectName']='GameplayStatics'
ed.fname('GameplayStatics')
ed.a['Imports'].append(gameplay_import); ed.a['ImportBits'].append(True)
gameplay=-len(ed.a['Imports'])
r=prop(ed.e(delta),'FunctionReference')
parent=copy.deepcopy(next(x for x in r['Value'] if x['Name']=='MemberParent'))
parent['Value']=gameplay
r['Value']=[parent,next(x for x in r['Value'] if x['Name']=='MemberName')]
ed.connect(scale,'RewardDistanceScale',safe_scale,'A')
ed.connect(rate,'HomeostaticRewardRate',safe_rate,'A')
ed.connect(80,'ReturnValue',normal,'A')
ed.connect(safe_scale,'ReturnValue',normal,'B')
ed.connect(normal,'ReturnValue',square,'A'); ed.connect(normal,'ReturnValue',square,'B')
ed.connect(square,'ReturnValue',denom,'B')
ed.connect(safe_rate,'ReturnValue',quality,'A'); ed.connect(denom,'ReturnValue',quality,'B')
ed.connect(quality,'ReturnValue',reward,'A'); ed.connect(delta,'ReturnValue',reward,'B')
ed.connect(339,'GameMode',delta,'WorldContextObject')
set_normal=set_reward('SetQualityReward')
ed.connect(bound,'else',set_normal,'execute'); ed.connect(reward,'ReturnValue',set_normal,'CurrentReward')

terminal=node(413,'MarkFailure','',[('execute',0,'exec'),('then',1,'exec'),
    ('ShouldTerminate',0,'bool',0,'true'),('Output_Get',1,'bool'),('self',0,'object',0)])
safe_failure=math('SafeFailureReward','FMin',[real('A'),real('B',default='0')])
set_failure=set_reward('SetFailureReward')
ed.connect(failure,'HomeostaticFailureReward',safe_failure,'A')
ed.connect(bound,'then',terminal,'execute'); ed.connect(terminal,'then',set_failure,'execute')
ed.connect(safe_failure,'ReturnValue',set_failure,'CurrentReward')

total=math('AccumulateReward','Add_DoubleDouble',[real('A'),real('B')])
ed.connect(314,'TotalReward',total,'A'); ed.connect(346,'CurrentReward',total,'B')
set_total=node(433,'SetTotalReward','',[('execute',0,'exec'),('then',1,'exec'),
    real('TotalReward'),real('Output_Get',1),('self',0,'object',0)])
ed.connect(set_normal,'then',set_total,'execute'); ed.connect(set_failure,'then',set_total,'execute')
ed.connect(total,'ReturnValue',set_total,'TotalReward')
plus=node(52,'NextEpisodeStep','Add_IntInt',[
    ('self',0,'object',-28),('A',0,'int'),('B',0,'int',0,'1'),('ReturnValue',1,'int')])
increment=node(413,'CountDecision','',[('execute',0,'exec'),('then',1,'exec'),
    ('Episode Steps',0,'int'),('Output_Get',1,'int'),('self',0,'object',0)])
prop(ed.e(increment),'VariableReference')['Value']=copy.deepcopy(prop(ed.e(388),'VariableReference')['Value'])
ed.connect(388,'Episode Steps',plus,'A')
ed.connect(plus,'ReturnValue',increment,'Episode Steps')
ed.connect(set_total,'then',increment,'execute')
result=node(166,'ReturnReward','GatherAgentReward',[('execute',0,'exec'),('OutReward',0,'real',0,'0','float')])
ed.connect(increment,'then',result,'execute')
ed.connect(346,'CurrentReward',result,'OutReward')
ed.save('BP_AgentTrainingEnv')
(root/'env.patched.json').write_text(json.dumps(ed.a),encoding='utf-8')
