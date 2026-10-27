"""Initialize forward velocity from BaseMaxSpeed at startup, reset and each phase."""
import base64
import copy
import json
from pathlib import Path
import struct
import uuid
from graph_asset import pins
from patch_graphs import Editor, prop, string

root = Path('Saved/PhaseVelocityFix')
def member(e, kind):
    return next((q['Value'] for p in e.get('Data', []) if p['Name'] == kind
                 for q in p['Value'] if q['Name'] == 'MemberName'), None)
def find(ed, kind, name, graph=None):
    return next(i for i, e in enumerate(ed.a['Exports'], 1)
                if member(e, kind) == name and
                (graph is None or ed.e(e['OuterIndex'])['ObjectName'] == graph))
def byname(ed, name):
    return next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']==name)
def clone(ed, template, label):
    idx = len(ed.a['Exports']) + 1
    e = copy.deepcopy(ed.e(template)); e['ObjectName'] = 'K2Node_PhaseVelocity_' + label
    ed.fname(e['ObjectName']); ed.a['Exports'].append(e)
    prop(e,'NodeGuid')['Value'][0]['Value'] = '{'+str(uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName'])).upper()+'}'
    data = bytearray(base64.b64decode(e['Extras']))
    for p in pins(ed.a,e):
        guid = uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName']+'/'+p['name']).bytes_le
        for offset in (4,24): struct.pack_into('<i',data,p['start']+offset,idx)
        for offset in (8,28): data[p['start']+offset:p['start']+offset+16]=guid
    e['Extras']=base64.b64encode(data).decode()
    for p in list(pins(ed.a,e)): ed.links(idx,p['name'],[])
    ns=prop(ed.e(e['OuterIndex']),'Nodes')['Value']; item=copy.deepcopy(ns[0])
    item.update(Name=str(len(ns)),Value=idx);ns.append(item);ed.changed.add(idx)
    return idx
def node(ed, template, label, function, specs, tail=None):
    if tail is None:
        ps=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[ps[-1]['end']:]
    i=ed.node(template,'K2Node_PhaseVelocity_'+label,function,specs,1600,800)
    ed.e(i)['Extras']=base64.b64encode(base64.b64decode(ed.e(i)['Extras'])+tail).decode()
    for p in list(pins(ed.a,ed.e(i)))[::-1]:
        if p['auto_default']:ed.replace(i,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
    return i
def ref(ed, i, function, parent=None):
    r=prop(ed.e(i),'FunctionReference')['Value']
    name=copy.deepcopy(next(q for q in r if q['Name']=='MemberName'));name['Value']=function;ed.fname(function)
    if parent is None:
        context=copy.deepcopy(next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']=='FunctionReference'
                                  for q in p['Value'] if q['Name']=='bSelfContext' and q['Value']))
        r[:]=[name,context]
    else:
        par=copy.deepcopy(next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']=='FunctionReference'
                              for q in p['Value'] if q['Name']=='MemberParent'))
        par['Value']=parent;r[:]=[par,name]
def connect_original_input(ed, original, new, pin):
    for source, guid in ed.p(original,pin)['links']:
        source_pin=next(p['name'] for p in pins(ed.a,ed.e(source)) if p['guid']==guid)
        ed.connect(source,source_pin,new,pin)
def save(ed, name):
    ed.save(name)
    (root/(name+'.patched.json')).write_text(json.dumps(ed.a))

a=Editor(json.loads((root/'agent.json').read_text(encoding='utf-8-sig')))
vector=next(-i for i,e in enumerate(a.a['Imports'],1) if e['ObjectName']=='Vector')
math=next(-i for i,e in enumerate(a.a['Imports'],1) if e['ObjectName']=='KismetMathLibrary')
movement=next(-i for i,e in enumerate(a.a['Imports'],1) if e['ObjectName']=='CharacterMovementComponent')
event_template=next(i for i,e in enumerate(a.a['Exports'],1) if any(p['Name']=='CustomFunctionName' and p['Value']=='ResetEvent' for p in e.get('Data',[])))
event=node(a,event_template,'InitializeEvent','', [('OutputDelegate',1,'delegate'),('then',1,'exec')],struct.pack('<i',0))
prop(a.e(event),'CustomFunctionName')['Value']='InitializePhaseVelocity';a.fname('InitializePhaseVelocity')
walk_original=byname(a,'K2Node_VariableSet_13')
max_original=byname(a,'K2Node_VariableSet_16')
velocity_original=next(i for i,e in enumerate(a.a['Exports'],1) if member(e,'VariableReference')=='Velocity' and e['ObjectName'].startswith('K2Node_VariableSet'))
walk=clone(a,walk_original,'SetSpeedCap');cached=clone(a,max_original,'SetCachedSpeed')
connect_original_input(a,walk_original,walk,'self');connect_original_input(a,walk_original,walk,'MaxWalkSpeed')
a.connect(walk,'Output_Get',cached,'MaxSpeed')
forward=clone(a,find(a,'FunctionReference','GetActorForwardVector','EventGraph'),'ForwardDirection')
multiply=node(a,find(a,'FunctionReference','GetActorForwardVector','EventGraph'),'ForwardSpeed','Multiply_VectorFloat',[
    ('self',0,'object',math),('A',0,'struct',vector),('B',0,'real',0,'','double'),('ReturnValue',1,'struct',vector)])
ref(a,multiply,'Multiply_VectorFloat',math)
a.connect(forward,'ReturnValue',multiply,'A');a.connect(cached,'Output_Get',multiply,'B')
velocity=node(a,velocity_original,'SetForwardVelocity','',[
    ('execute',0,'exec'),('then',1,'exec'),('Velocity',0,'struct',vector),
    ('Output_Get',1,'struct',vector),('self',0,'object',movement)])
connect_original_input(a,velocity_original,velocity,'self')
a.connect(multiply,'ReturnValue',velocity,'Velocity')
a.connect(event,'then',walk,'execute');a.connect(walk,'then',cached,'execute');a.connect(cached,'then',velocity,'execute')
move_template=find(a,'FunctionReference','AddMovementInput','EventGraph')
move=node(a,move_template,'FreshForwardInput','AddMovementInput',[
    ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',0),
    ('WorldDirection',0,'struct',vector),('ScaleValue',0,'real',0,'1.0','float'),('bForce',0,'bool',0,'true')])
a.connect(forward,'ReturnValue',move,'WorldDirection');a.connect(velocity,'then',move,'execute')
def call(label):
    i=node(a,find(a,'FunctionReference','Jump','EventGraph'),label,'InitializePhaseVelocity',[
        ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',0)])
    ref(a,i,'InitializePhaseVelocity');return i
startup=call('Startup');reset=call('AfterReset')
actor_type=a.import_class('Actor')
rotator_type=next(-i for i,e in enumerate(a.a['Imports'],1) if e['ObjectName']=='Rotator')
enum=copy.deepcopy(next(e for e in a.a['Imports'] if e['ClassName']=='Enum' and e['ObjectName']=='ETraceTypeQuery'))
enum['ObjectName']='EMovementMode';a.fname('EMovementMode');a.a['Imports'].append(enum);a.a['ImportBits'].append(True)
movement_mode=-len(a.a['Imports'])
def settle_spawn(label, initialize):
    # SetActorTransform's teleport flag skips collision placement checks. Use
    # Unreal's tested teleport placement before setting velocity, so floor
    # depenetration does not cancel the newly initialized first-frame motion.
    t=find(a,'FunctionReference','GetActorForwardVector','EventGraph')
    location=node(a,t,label+'Location','K2_GetActorLocation',[
        ('self',0,'object',actor_type),('ReturnValue',1,'struct',vector)])
    ref(a,location,'K2_GetActorLocation',actor_type)
    rotation=node(a,t,label+'Rotation','K2_GetActorRotation',[
        ('self',0,'object',actor_type),('ReturnValue',1,'struct',rotator_type)])
    ref(a,rotation,'K2_GetActorRotation',actor_type)
    teleport=node(a,find(a,'FunctionReference','Jump','EventGraph'),label+'ResolveSpawn','K2_TeleportTo',[
        ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',actor_type),
        ('DestLocation',0,'struct',vector),('DestRotation',0,'struct',rotator_type),('ReturnValue',1,'bool')])
    ref(a,teleport,'K2_TeleportTo',actor_type)
    a.connect(location,'ReturnValue',teleport,'DestLocation');a.connect(rotation,'ReturnValue',teleport,'DestRotation')
    walking=node(a,find(a,'FunctionReference','Jump','EventGraph'),label+'Walking','SetMovementMode',[
        ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',movement),
        ('NewMovementMode',0,'byte',movement_mode,'MOVE_Walking'),('NewCustomMode',0,'byte',0,'0')])
    ref(a,walking,'SetMovementMode',movement)
    connect_original_input(a,velocity_original,walking,'self')
    a.connect(teleport,'then',walking,'execute');a.connect(walking,'then',initialize,'execute')
    return teleport
startup_spawn=settle_spawn('Startup',startup);reset_spawn=settle_spawn('Reset',reset)
source,guid=a.p(velocity_original,'execute')['links'][0]
source_pin=next(p['name'] for p in pins(a.a,a.e(source)) if p['guid']==guid)
a.rewire(source,source_pin,startup_spawn,'execute')
rotation=byname(a,'K2Node_CallFunction_ResetK2_SetActorRotation446')
assert not a.p(rotation,'then')['links']
a.connect(rotation,'then',reset_spawn,'execute')
save(a,'BP_Agent')

m=Editor(json.loads((root/'gm.json').read_text(encoding='utf-8-sig')))
template=find(m,'FunctionReference','CanalizationToggled_Event','RunTrial')
agent_type=next(-i for i,e in enumerate(m.a['Imports'],1) if e['ObjectName']=='BP_Agent_C')
phase=node(m,template,'PhaseStart','InitializePhaseVelocity',[
    ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',agent_type)])
ref(m,phase,'InitializePhaseVelocity',agent_type)
agent_get=find(m,'VariableReference','Agent')
target=clone(m,agent_get,'Agent')
# Move the getter from its original function into RunTrial.
old=prop(m.e(m.e(target)['OuterIndex']),'Nodes')['Value'];item=next(v for v in old if v['Value']==target);old.remove(item)
m.e(target)['OuterIndex']=m.e(template)['OuterIndex'];ns=prop(m.e(m.e(target)['OuterIndex']),'Nodes')['Value'];item['Name']=str(len(ns));ns.append(item)
m.connect(target,'Agent',phase,'self')
boundary=next(i for i,e in enumerate(m.a['Exports'],1) if m.e(e['OuterIndex'])['ObjectName']=='RunTrial'
              and member(e,'DelegateReference')=='SetpointsChanged')
destination,guid=m.p(boundary,'then')['links'][0]
dest_pin=next(p['name'] for p in pins(m.a,m.e(destination)) if p['guid']==guid)
gate=clone(m,destination,'HasNextPhase')
math=next(-i for i,e in enumerate(m.a['Imports'],1) if e['ObjectName']=='KismetMathLibrary')
less=node(m,find(m,'FunctionReference','RandomFloatInRangeFromStream','RunTrial'),'BeforeFinalBoundary','Less_IntInt',[
    ('self',0,'object',math),('A',0,'int'),('B',0,'int',0,'18000'),('ReturnValue',1,'bool')])
ref(m,less,'Less_IntInt',math)
tick_get=find(m,'VariableReference','TotalTickCount','RunTrial')
m.connect(tick_get,'TotalTickCount',less,'A');m.connect(less,'ReturnValue',gate,'Condition')
m.rewire(boundary,'then',gate,'execute');m.connect(gate,'then',phase,'execute')
m.connect(gate,'else',destination,dest_pin);m.connect(phase,'then',destination,dest_pin)
save(m,'BP_GameMode')
