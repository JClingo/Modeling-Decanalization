"""Give trial 1 the same full reset as later trials; clear stale observation caches."""
import base64
import copy
import json
from pathlib import Path
import struct
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parent))
from patch_graphs import Editor,prop,string
from graph_asset import pins
root=Path('Saved/TrialStartupAudit')

def node(ed,template,label,function,specs):
 old=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[old[-1]['end']:]
 idx=ed.node(template,'K2Node_TrialStart_'+label,function,specs,1200,500+len(ed.changed)*120)
 ed.e(idx)['Extras']=base64.b64encode(base64.b64decode(ed.e(idx)['Extras'])+tail).decode()
 for p in list(pins(ed.a,ed.e(idx)))[::-1]:
  if p['auto_default']:ed.replace(idx,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
 return idx

def ref(ed,i,kind,name,parent=None):
 r=prop(ed.e(i),kind)['Value'];n=copy.deepcopy(next(q for q in r if q['Name']=='MemberName'));n['Value']=name;ed.fname(name)
 if parent is None:
  context=copy.deepcopy(next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']==kind for q in p['Value'] if q['Name']=='bSelfContext' and q['Value']))
  r[:]=[n,context]
 else:
  source=next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']=='FunctionReference' for q in p['Value'] if q['Name']=='MemberParent')
  p=copy.deepcopy(source);p['Value']=parent;r[:]=[p,n]

def clone(ed,template,label):
 idx=len(ed.a['Exports'])+1;e=copy.deepcopy(ed.e(template));e['ObjectName']='K2Node_TrialStart_'+label;ed.fname(e['ObjectName']);ed.a['Exports'].append(e)
 prop(e,'NodeGuid')['Value'][0]['Value']='{'+str(uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName'])).upper()+'}'
 data=bytearray(base64.b64decode(e['Extras']))
 for p in pins(ed.a,e):
  g=uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName']+'/'+p['name']).bytes_le
  for o in (4,24):struct.pack_into('<i',data,p['start']+o,idx)
  for o in (8,28):data[p['start']+o:p['start']+o+16]=g
 e['Extras']=base64.b64encode(data).decode()
 for p in list(pins(ed.a,e)):ed.links(idx,p['name'],[])
 ns=prop(ed.e(e['OuterIndex']),'Nodes')['Value'];v=copy.deepcopy(ns[0]);v.update(Name=str(len(ns)),Value=idx);ns.append(v);ed.changed.add(idx);return idx

m=Editor(json.loads((root/'gm.variables.json').read_text(encoding='utf-8-sig')))
def scope(ed,e):return ed.e(e['OuterIndex'])['ObjectName'] if e['OuterIndex']>0 else ''
def member(e,kind):return next((q['Value'] for p in e.get('Data',[]) if p['Name']==kind for q in p['Value'] if q['Name']=='MemberName'),None)
def find_var(name):return next(i for i,e in enumerate(m.a['Exports'],1) if e['ObjectName'].startswith('K2Node_VariableGet') and member(e,'VariableReference')==name)
def find_call(name):return next(i for i,e in enumerate(m.a['Exports'],1) if e['ObjectName'].startswith('K2Node_CallFunction') and member(e,'FunctionReference')==name)
entry=next(i for i,e in enumerate(m.a['Exports'],1) if scope(m,e)=='RunTrial' and e['ObjectName'].startswith('K2Node_FunctionEntry'))
graph=m.e(entry)['OuterIndex']
original,guid=m.p(entry,'then')['links'][0]
original_pin=next(p['name'] for p in pins(m.a,m.e(original)) if p['guid']==guid)
def move(i):
 old=prop(m.e(m.e(i)['OuterIndex']),'Nodes')['Value'];v=next(v for v in old if v['Value']==i);old.remove(v)
 m.e(i)['OuterIndex']=graph;new=prop(m.e(graph),'Nodes')['Value'];v['Name']=str(len(new));new.append(v);return i
trial_mode=move(clone(m,find_var('IsTrialMode'),'IsTrialMode'))
manager=move(clone(m,find_var('AgentManager'),'Manager'))
inference=move(clone(m,find_var('Run Inference'),'RunInference'))
m.connect(manager,'AgentManager',inference,'self')
math=next(-i for i,e in enumerate(m.a['Imports'],1) if e['ObjectName']=='KismetMathLibrary')
both=move(node(m,find_call('Not_PreBool'),'TrialInferenceOnly','BooleanAND', [('self',0,'object',math),('A',0,'bool'),('B',0,'bool'),('ReturnValue',1,'bool')]))
m.connect(trial_mode,'IsTrialMode',both,'A');m.connect(inference,'Run Inference',both,'B')
gate=clone(m,original,'TrialModeOnly');once=clone(m,original,'OncePerWorld')
initialized=move(node(m,find_var('IsTrialMode'),'HasInitialized','', [('HasInitializedTrialRun',1,'bool'),('self',0,'object',0)]))
ref(m,initialized,'VariableReference','HasInitializedTrialRun')
m.connect(both,'ReturnValue',gate,'Condition');m.connect(initialized,'HasInitializedTrialRun',once,'Condition')
m.rewire(entry,'then',gate,'execute');m.connect(gate,'else',original,original_pin);m.connect(gate,'then',once,'execute');m.connect(once,'then',original,original_pin)
header_template=next(i for i,e in enumerate(m.a['Exports'],1) if e['ObjectName'].startswith('K2Node_VariableSet') and scope(m,e)=='EventGraph' and member(e,'VariableReference')=='TrialYML')
mark=move(node(m,header_template,'MarkInitialized','', [('execute',0,'exec'),('then',1,'exec'),('HasInitializedTrialRun',0,'bool',0,'true'),('Output_Get',1,'bool'),('self',0,'object',0)]))
ref(m,mark,'VariableReference','HasInitializedTrialRun')
header=move(clone(m,header_template,'InitializeYamlBuffer'))
reset=next(i for i,e in enumerate(m.a['Exports'],1) if scope(m,e)=='RunTrial' and member(e,'FunctionReference')=='ResetAllAgents')
m.connect(once,'else',mark,'execute');m.connect(mark,'then',header,'execute');m.connect(header,'then',reset,'execute')
m.save('BP_GameMode');(root/'gm.patched.json').write_text(json.dumps(m.a))

a=Editor(json.loads((root/'BP_Agent.json').read_text(encoding='utf-8-sig')))
# Erase perception from the previous location before teleporting. Each new
# decision may repopulate these arrays normally; phase transitions do not reset.
gain=clone(a,416,'ClearAnticipatedGain');loss=clone(a,401,'ClearAnticipatedLoss')
clear1=clone(a,67,'ClearResourceHits');clear2=clone(a,68,'ClearTileHits')
for idx in [clear1,clear2]:
 old=prop(a.e(a.e(idx)['OuterIndex']),'Nodes')['Value'];item=next(v for v in old if v['Value']==idx);old.remove(item)
 a.e(idx)['OuterIndex']=a.e(422)['OuterIndex'];new=prop(a.e(a.e(idx)['OuterIndex']),'Nodes')['Value'];item['Name']=str(len(new));new.append(item)
for name,idx in [('CollidingDriveReducers',clear1),('CollidingDriveIncreasers',clear2)]:
 getter=next(i for i,e in enumerate(a.a['Exports'],1) if e['ObjectName'].startswith('K2Node_VariableGet') and any(p['Name']=='VariableReference' and any(q.get('Value')==name for q in p['Value']) for p in e.get('Data',[])))
 a.connect(getter,name,idx,'TargetArray')
a.rewire(422,'then',gain,'execute')
for left,right in [(gain,loss),(loss,clear1),(clear1,clear2),(clear2,230)]:a.connect(left,'then',right,'execute')
a.save('BP_Agent');(root/'agent.patched.json').write_text(json.dumps(a.a))
