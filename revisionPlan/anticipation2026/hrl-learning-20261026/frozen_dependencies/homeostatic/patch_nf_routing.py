"""Route only NF training through nf_ppo before spawning its trainer process."""
import base64
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'timing'))
from patch_graphs import Editor,prop,string
from graph_asset import pins
root=Path('Saved/NFStabilityFix')
ed=Editor(json.loads((root/'manager.json').read_text(encoding='utf-8-sig')))
def member(e,kind):
    return next((q['Value'] for p in e.get('Data',[]) if p['Name']==kind for q in p['Value'] if q['Name']=='MemberName'),None)
def find(kind,name):return next(i for i,e in enumerate(ed.a['Exports'],1) if member(e,kind)==name)
def native_class(name,package):
    for i,e in enumerate(ed.a['Imports'],1):
        if e['ObjectName']==name and e['ClassName']=='Class':return -i
    pkg=next((-i for i,e in enumerate(ed.a['Imports'],1) if e['ObjectName']==package),None)
    if pkg is None:
        item=copy.deepcopy(next(e for e in ed.a['Imports'] if e['ObjectName']=='/Script/Engine'))
        item['ObjectName']=package;ed.fname(package);ed.a['Imports'].append(item);ed.a['ImportBits'].append(True);pkg=-len(ed.a['Imports'])
    item=copy.deepcopy(next(e for e in ed.a['Imports'] if e['ObjectName']=='Actor' and e['ClassName']=='Class'))
    item.update(ObjectName=name,OuterIndex=pkg);ed.fname(name);ed.a['Imports'].append(item);ed.a['ImportBits'].append(True)
    return -len(ed.a['Imports'])
def node(template,label,function,specs):
    old=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[old[-1]['end']:]
    i=ed.node(template,'K2Node_NFTraining_'+label,function,specs,1000,1500)
    ed.e(i)['Extras']=base64.b64encode(base64.b64decode(ed.e(i)['Extras'])+tail).decode()
    for p in list(pins(ed.a,ed.e(i)))[::-1]:
        if p['auto_default']:ed.replace(i,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
    return i
def reference(i,kind,name,parent=None):
    r=prop(ed.e(i),kind)['Value'];n=copy.deepcopy(next(q for q in r if q['Name']=='MemberName'));n['Value']=name;ed.fname(name)
    if parent is None:
        ctx=copy.deepcopy(next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']==kind for q in p['Value'] if q['Name']=='bSelfContext' and q['Value']))
        r[:]=[n,ctx]
    else:
        par=copy.deepcopy(next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']=='FunctionReference' for q in p['Value'] if q['Name']=='MemberParent'))
        par['Value']=parent;r[:]=[n,par]
spawn=find('FunctionReference','SpawnSharedMemoryTrainingProcess')
source,guid=ed.p(spawn,'execute')['links'][0]
source_pin=next(p['name'] for p in pins(ed.a,ed.e(source)) if p['guid']==guid)
branch_template=next(i for i,e in enumerate(ed.a['Exports'],1) if e['ClassIndex']<0 and ed.a['Imports'][-e['ClassIndex']-1]['ObjectName']=='K2Node_IfThenElse')
gm_type=next(-i for i,e in enumerate(ed.a['Imports'],1) if e['ObjectName']=='BP_GameMode_C')
gm=node(find('VariableReference','Agent Actors'),'GameMode','',[('BP Game Mode',1,'object',gm_type),('self',0,'object')])
reference(gm,'VariableReference','BP Game Mode')
mode=node(find('VariableReference','Run Inference'),'IsHRL','',[('IsHRL',1,'bool'),('self',0,'object',gm_type)])
reference(mode,'VariableReference','IsHRL',gm_type);ed.connect(gm,'BP Game Mode',mode,'self')
gate=node(branch_template,'ModeGuard','',[('execute',0,'exec'),('Condition',0,'bool'),('then',1,'exec'),('else',1,'exec')])
ed.connect(mode,'IsHRL',gate,'Condition');ed.rewire(source,source_pin,gate,'execute');ed.connect(gate,'then',spawn,'execute')
python=native_class('PythonScriptLibrary','/Script/PythonScriptPlugin')
configure=node(spawn,'ConfigureNF','ExecutePythonCommand',[
    ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',python),
    ('PythonCommand',0,'string',0,'import nf_training; nf_training.configure_nf_training()'),('ReturnValue',1,'bool')])
reference(configure,'FunctionReference','ExecutePythonCommand',python)
success=node(branch_template,'Configured','',[('execute',0,'exec'),('Condition',0,'bool'),('then',1,'exec'),('else',1,'exec')])
ed.connect(gate,'else',configure,'execute');ed.connect(configure,'then',success,'execute')
ed.connect(configure,'ReturnValue',success,'Condition');ed.connect(success,'then',spawn,'execute')
system=native_class('KismetSystemLibrary','/Script/Engine');obj=native_class('Object','/Script/CoreUObject')
error=node(find('FunctionReference','PrintString'),'ConfigurationFailed','PrintString',[
    ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',system),('WorldContextObject',0,'object',obj),
    ('InString',0,'string',0,'NF trainer configuration failed; stopping rather than starting the HRL trainer.'),
    ('bPrintToScreen',0,'bool',0,'true'),('bPrintToLog',0,'bool',0,'true')])
reference(error,'FunctionReference','PrintString',system)
quit_node=node(spawn,'Abort','ExecuteConsoleCommand',[
    ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',system),('WorldContextObject',0,'object',obj),
    ('Command',0,'string',0,'QUIT'),('SpecificPlayer',0,'object',native_class('PlayerController','/Script/Engine'))])
reference(quit_node,'FunctionReference','ExecuteConsoleCommand',system)
ed.connect(success,'else',error,'execute');ed.connect(error,'then',quit_node,'execute')
self_node=next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName'].startswith('K2Node_Self'))
self_pin=next(p['name'] for p in pins(ed.a,ed.e(self_node)) if p['direction']==1)
for i in [error,quit_node]:ed.connect(self_node,self_pin,i,'WorldContextObject')
ed.save('BP_AgentManager');(root/'manager.patched.json').write_text(json.dumps(ed.a))
