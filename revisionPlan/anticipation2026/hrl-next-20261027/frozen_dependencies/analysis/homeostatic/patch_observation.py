"""Read the policy's signed homeostatic observation from live GameMode history."""
import base64
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'timing'))
from patch_graphs import Editor,prop
from graph_asset import pins

root=Path('Saved/HomeostaticFix')
ed=Editor(json.loads((root/'interactor.json').read_text(encoding='utf-8-sig')))
template=copy.deepcopy(ed.a['Imports'][1])
package=copy.deepcopy(ed.a['Imports'][90]);package['ObjectName']='/Game/Agent/BP_GameMode'
ed.fname(package['ObjectName']);ed.a['Imports'].append(package);ed.a['ImportBits'].append(True)
template['ObjectName']='BP_GameMode_C';template['OuterIndex']=-len(ed.a['Imports'])
ed.fname(template['ObjectName']);ed.a['Imports'].append(template);ed.a['ImportBits'].append(True)
gm_class=-len(ed.a['Imports'])
def node(template,name,function,specs):
    idx=ed.node(template,'K2Node_Homeostatic_'+name,function,specs,1600,200+len(ed.changed)*120)
    return idx
def variable(name,owner,type_index,category='object'):
    idx=node(144,'Live'+name,'',[(name,1,category,type_index,'','double' if category=='real' else 'None'),('self',0,'object',owner)])
    r=prop(ed.e(idx),'VariableReference')['Value']
    r[:]=[x for x in r if x['Name'] in ['MemberParent','MemberName']]
    next(x for x in r if x['Name']=='MemberParent')['Value']=owner
    next(x for x in r if x['Name']=='MemberName')['Value']=name
    ed.fname(name)
    return idx
def array_pin(idx,name):
    p=next(p for p in pins(ed.a,ed.e(idx)) if p['name']==name)
    data=bytearray(base64.b64decode(ed.e(idx)['Extras']))
    assert data[p['start']+90]==0
    data[p['start']+90]=1
    ed.e(idx)['Extras']=base64.b64encode(data).decode()
def array_call(name,function,specs):
    idx=node(19,name,function,[('self',0,'object',-31)]+specs)
    r=prop(ed.e(idx),'FunctionReference')['Value']
    parent=copy.deepcopy(next(x for x in prop(ed.e(24),'FunctionReference')['Value'] if x['Name']=='MemberParent'))
    parent['Value']=-31
    r[:]=[parent,next(x for x in r if x['Name']=='MemberName')]
    return idx
gm=variable('BP Game Mode',-2,gm_class)
history=variable('Setpoints',gm_class,0,'real')
last=array_call('LastSetpointIndex','Array_LastIndex',[
    ('TargetArray',0,'real',0,'','double'),('ReturnValue',1,'int')])
item=array_call('CurrentSetpoint','Array_Get',[
    ('TargetArray',0,'real',0,'','double'),('Index',0,'int',0,'0'),('Item',1,'real',0,'','double')])
for idx,name in [(history,'Setpoints'),(last,'TargetArray'),(item,'TargetArray')]:array_pin(idx,name)
ed.connect(114,'ObsActor',gm,'self')
ed.connect(gm,'BP Game Mode',history,'self')
ed.connect(history,'Setpoints',last,'TargetArray')
ed.connect(history,'Setpoints',item,'TargetArray')
ed.connect(last,'ReturnValue',item,'Index')
ed.rewire(23,'Value',item,'Item')
ed.save('BP_AgentInteractor')
(root/'interactor.patched.json').write_text(json.dumps(ed.a))
