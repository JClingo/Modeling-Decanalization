"""Seed the shared environment stream before initial actors draw randomness."""
import base64
import copy
import json
import struct
import sys
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'timing'))
from patch_graphs import Editor,prop
from graph_asset import pins

root=Path('Saved/RngSeedFix')
ed=Editor(json.loads((root/'gamemode.variables.json').read_text(encoding='utf-8-sig')))
def outer(i):return ed.e(ed.e(i)['OuterIndex'])['ObjectName']
def named(name,graph='EventGraph'):
    return next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']==name and outer(i)==graph)
entry=named('K2Node_FunctionEntry_34','UserConstructionScript')
graph=ed.e(entry)['OuterIndex']

def clone(template,name):
    idx=len(ed.a['Exports'])+1
    e=copy.deepcopy(ed.e(template));e['ObjectName']='K2Node_EnvironmentSeed_'+name;e['OuterIndex']=graph
    ed.fname(e['ObjectName']);ed.a['Exports'].append(e)
    data=bytearray(base64.b64decode(e['Extras']))
    for p in pins(ed.a,e):
        guid=uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName']+'/'+p['name']).bytes_le
        struct.pack_into('<i',data,p['start']+4,idx)
        struct.pack_into('<i',data,p['start']+24,idx)
        data[p['start']+8:p['start']+24]=guid
        data[p['start']+28:p['start']+44]=guid
    e['Extras']=base64.b64encode(data).decode()
    for p in list(pins(ed.a,e)):ed.links(idx,p['name'],[])
    nodes=prop(ed.e(graph),'Nodes')['Value'];ref=copy.deepcopy(nodes[0]);ref['Name']=str(len(nodes));ref['Value']=idx;nodes.append(ref)
    ed.changed.add(idx)
    return idx

get_actor=named('K2Node_CallFunction_11')
get_manager=clone(get_actor,'GetManagerBeforeBeginPlay')
get_mode=clone(named('K2Node_VariableGet_25'),'RunInference')
# IsValid already checks the same manager at BeginPlay; retain its native flags.
valid_template=next(i for i,e in enumerate(ed.a['Exports'],1)
    if outer(i)=='EventGraph' and e['ObjectName'].startswith('K2Node_CallFunction')
    and any(p['Name']=='FunctionReference' and any(q['Name']=='MemberName' and q['Value']=='IsValid' for q in p['Value']) for p in e.get('Data',[])))
valid=clone(valid_template,'IsValidManager')
branch=clone(named('K2Node_IfThenElse_1'),'ManagerExists')
stream=clone(named('K2Node_VariableGet_2'),'EnvironmentStream')
seed_call=clone(named('K2Node_CallFunction_41'),'SeedStreamBeforeSpawning')

def own_get(name):
    idx=clone(named('K2Node_VariableGet_2'),'Get'+name)
    # Replace struct stream pins with a native integer variable getter.
    e=ed.e(idx);e['Extras']=base64.b64encode(struct.pack('<i',2)+
        ed.pin(idx,name,1,'int')+ed.pin(idx,'self',0,'object',0)).decode()
    r=prop(e,'VariableReference')['Value'];r[:]=[q for q in r if q['Name'] in ['MemberName','bSelfContext']]
    next(q for q in r if q['Name']=='MemberName')['Value']=name
    ed.fname(name)
    return idx
training=own_get('TrainingEnvironmentSeed');trial=own_get('TrialEnvironmentSeed');active=own_get('ActiveEnvironmentSeed')
def set_active(name):
    template=named('K2Node_VariableSet_6')
    old=ed.e(template)['OuterIndex'];ed.e(template)['OuterIndex']=graph
    idx=ed.node(template,'K2Node_EnvironmentSeed_'+name,'',[
        ('execute',0,'exec'),('then',1,'exec'),('ActiveEnvironmentSeed',0,'int'),('Output_Get',1,'int'),('self',0,'object',0)],400,300)
    ed.e(template)['OuterIndex']=old
    prop(ed.e(idx),'VariableReference')['Value']=copy.deepcopy(prop(ed.e(active),'VariableReference')['Value'])
    return idx
fallback=set_active('FallbackTrainingSeed');selected=set_active('SelectedModeSeed')
math_import=next(-i for i,x in enumerate(ed.a['Imports'],1) if x['ObjectName']=='KismetMathLibrary')
math_template=next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']=='K2Node_CallFunction_7' and outer(i)=='ResetValues')
old=ed.e(math_template)['OuterIndex'];ed.e(math_template)['OuterIndex']=graph
select=ed.node(math_template,'K2Node_EnvironmentSeed_SelectSeed','SelectInt',[
    ('self',0,'object',math_import),('A',0,'int'),('B',0,'int'),('bPickA',0,'bool'),('ReturnValue',1,'int')],200,300)
ed.e(math_template)['OuterIndex']=old

ed.connect(entry,'then',get_manager,'execute')
ed.connect(get_manager,'then',branch,'execute')
ed.connect(get_manager,'ReturnValue',get_mode,'self')
valid_input=next(p['name'] for p in pins(ed.a,ed.e(valid)) if p['direction']==0 and p['name']!='self')
ed.connect(get_manager,'ReturnValue',valid,valid_input)
ed.connect(valid,'ReturnValue',branch,'Condition')
ed.connect(branch,'then',selected,'execute');ed.connect(branch,'else',fallback,'execute')
ed.connect(trial,'TrialEnvironmentSeed',select,'A');ed.connect(training,'TrainingEnvironmentSeed',select,'B')
ed.connect(get_mode,'Run Inference',select,'bPickA')
ed.connect(select,'ReturnValue',selected,'ActiveEnvironmentSeed')
ed.connect(training,'TrainingEnvironmentSeed',fallback,'ActiveEnvironmentSeed')
ed.connect(selected,'then',seed_call,'execute');ed.connect(fallback,'then',seed_call,'execute')
ed.connect(stream,'RandomStream',seed_call,'Stream');ed.connect(active,'ActiveEnvironmentSeed',seed_call,'NewSeed')

# Do not rewind the stream after initial resources have already consumed it.
begin_seed=named('K2Node_CallFunction_41');sequence=named('K2Node_ExecutionSequence_0')
next_idx,next_guid=ed.p(begin_seed,'then')['links'][0]
next_pin=next(p['name'] for p in pins(ed.a,ed.e(next_idx)) if p['guid']==next_guid)
ed.disconnect(begin_seed,'then')
ed.rewire(sequence,'then_2',next_idx,next_pin)
ed.save('BP_GameMode')
(root/'gamemode.patched.json').write_text(json.dumps(ed.a))
