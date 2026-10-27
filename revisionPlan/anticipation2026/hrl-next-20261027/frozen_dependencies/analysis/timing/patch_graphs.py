"""Stage narrowly scoped Blueprint graph edits; never patch compiled bytecode.

Unreal must compile and save the staged assets before runtime validation.
Input JSON comes from the hash-verified backups in Saved/TimingFix.
"""
import base64
import copy
import json
import struct
import uuid
from pathlib import Path
from graph_asset import load, pins

def i32(v): return struct.pack('<i', v)
def string(v):
    b = v.encode('utf-8') + b'\0' if v else b''
    return i32(len(b)) + b
def refs(items): return i32(len(items)) + b''.join(i32(0)+i32(j)+bytes.fromhex(g) for j,g in items)
def prop(e, name): return next(p for p in e['Data'] if p['Name']==name)

class Editor:
    def __init__(self, asset): self.a, self.changed = asset, set()
    def e(self, i): return self.a['Exports'][i-1]
    def p(self, i, name): return next(p for p in pins(self.a,self.e(i)) if p['name']==name)
    def replace(self, i, start, end, data):
        e=self.e(i); b=base64.b64decode(e['Extras'])
        e['Extras']=base64.b64encode(b[:start]+data+b[end:]).decode()
        self.changed.add(i)
    def links(self, i, name, links):
        p=self.p(i,name); self.replace(i,p['links_start'],p['links_end'],refs(links))
    def disconnect(self, i, name):
        p=self.p(i,name)
        for j,g in p['links']:
            peer=next(q for q in pins(self.a,self.e(j)) if q['guid']==g)
            self.links(j,peer['name'],[r for r in peer['links'] if r != (i,p['guid'])])
        self.links(i,name,[])
    def connect(self, i, name, j, other):
        p,q=self.p(i,name),self.p(j,other)
        assert p['direction'] != q['direction']
        self.links(i,name,p['links']+[(j,q['guid'])])
        self.links(j,other,q['links']+[(i,p['guid'])])
    def rewire(self, i, name, j, other):
        self.disconnect(i,name); self.connect(i,name,j,other)
    def fname(self, name):
        if name not in self.a['NameMap']: self.a['NameMap'].append(name)
        return i32(self.a['NameMap'].index(name))+i32(0)
    def import_class(self, name):
        self.fname(name)
        for i,x in enumerate(self.a['Imports'],1):
            if x['ObjectName']==name and x['ClassName']=='Class': return -i
        template=copy.deepcopy(next(x for x in self.a['Imports'] if x['ObjectName']=='Actor' and x['ClassName']=='Class'))
        template['ObjectName']=name
        self.a['Imports'].append(template)
        self.a['ImportBits'].append(True)
        return -len(self.a['Imports'])
    def pin(self, owner, name, direction, category, obj=0, default='', subcategory='None'):
        guid=uuid.uuid5(uuid.NAMESPACE_URL, f'timing/{owner}/{name}').bytes_le
        empty_text=i32(0)+b'\xff'+i32(0)
        b=i32(0)+i32(owner)+guid+i32(owner)+guid+self.fname(name)+empty_text+i32(-1)+string('')+bytes([direction])
        b+=self.fname(category)+self.fname(subcategory)+i32(obj)+b'\0'+i32(0)*3+self.fname('None')+b'\0'*16+i32(0)*3
        b+=string(default)+string(default)+i32(0)+empty_text+refs([])+refs([])+i32(1)*2+b'\0'*16+i32(0)
        return b
    def node(self, template, name, function, specs, x, y):
        self.fname(name)
        if function: self.fname(function)
        idx=len(self.a['Exports'])+1
        e=copy.deepcopy(self.e(template))
        e['ObjectName']=name
        for p in e['Data']:
            if p['Name']=='FunctionReference':
                for member in p['Value']:
                    if member['Name']=='MemberName': member['Value']=function
            elif p['Name']=='NodePosX': p['Value']=x
            elif p['Name']=='NodePosY': p['Value']=y
            elif p['Name']=='NodeGuid': p['Value'][0]['Value']='{'+str(uuid.uuid5(uuid.NAMESPACE_URL,name)).upper()+'}'
        e['Extras']=base64.b64encode(i32(len(specs))+b''.join(self.pin(idx,*spec) for spec in specs)).decode()
        self.a['Exports'].append(e)
        nodes=prop(self.e(e['OuterIndex']),'Nodes')['Value']
        entry=copy.deepcopy(nodes[0]); entry['Name']=str(len(nodes)); entry['Value']=idx; nodes.append(entry)
        self.changed.add(idx)
        return idx
    def save(self,name):
        # Every edited link must be reciprocal, including untouched peers.
        for i in self.changed:
            for p in pins(self.a,self.e(i)):
                for j,g in p['links']:
                    q=next(q for q in pins(self.a,self.e(j)) if q['guid']==g)
                    assert (i,p['guid']) in q['links'], (i,p['name'],j)
        Path('Saved/TimingFix',name+'.patched.json').write_text(json.dumps(self.a),encoding='utf-8')
        print(name,'edited node indices:',sorted(self.changed))

def rename(value, old, new):
    if isinstance(value,list): return [rename(x,old,new) for x in value]
    if isinstance(value,dict): return {k:rename(v,old,new) for k,v in value.items()}
    return new if value==old else value

if __name__ == '__main__':
    agent=Editor(load('BP_Agent'))
    # One assignment each frame, with CharacterMovement integrating speed in cm/s.
    agent.rewire(186,'then',405,'execute')
    agent.rewire(405,'then',404,'execute')
    agent.rewire(404,'MaxWalkSpeed',325,'BaseMaxSpeed')
    agent.rewire(406,'then',192,'execute')
    # Disconnect the obsolete train/infer/landscape speed formula subtree at its roots.
    agent.disconnect(196,'then_0')
    agent.disconnect(196,'then_1')
    for idx in [267,269,270,272]:
        for p in list(pins(agent.a,agent.e(idx))): agent.disconnect(idx,p['name'])
        graph_nodes=prop(agent.e(10),'Nodes')['Value']
        graph_nodes[:]=[p for p in graph_nodes if p['Value']!=idx]
    agent.save('BP_Agent')
    
    manager=Editor(load('BP_AgentManager'))
    actor=manager.import_class('Actor'); controller=manager.import_class('PlayerController')
    gameplay=next(i for i,x in enumerate(manager.a['Imports'],1) if x['ObjectName']=='GameplayStatics')
    get_pc=manager.node(29,'K2Node_CallFunction_TimingController','GetPlayerController',[
        ('self',0,'object',-gameplay), ('WorldContextObject',0,'object',manager.import_class('Object')),
        ('PlayerIndex',0,'int',0,'0'), ('ReturnValue',1,'object',controller)],-700,900)
    prereq_gm=manager.node(38,'K2Node_CallFunction_TimingGameMode','AddTickPrerequisiteActor',[
        ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',actor),('PrerequisiteActor',0,'object',actor)],-350,900)
    prereq_pc=manager.node(38,'K2Node_CallFunction_TimingControllerOrder','AddTickPrerequisiteActor',[
        ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',actor),('PrerequisiteActor',0,'object',actor)],0,900)
    manager.connect(105,'then',prereq_gm,'execute')
    manager.connect(105,'Output_Get',prereq_gm,'PrerequisiteActor')
    manager.connect(prereq_gm,'then',prereq_pc,'execute')
    manager.connect(get_pc,'ReturnValue',prereq_pc,'self')
    # Existing Self node's output is the manager actor.
    self_pin=next(p['name'] for p in pins(manager.a,manager.e(58)) if p['direction']==1)
    manager.connect(58,self_pin,prereq_pc,'PrerequisiteActor')
    # Inference does not need a trainer process or PPO communicator. The original
    # BeginPlay sequence tried to spawn both even when Run Inference was true.
    for output, label in [('then_6','Process'),('then_7','PPO')]:
        original=manager.p(44,output)['links']
        assert len(original)==1
        destination, guid=original[0]
        destination_pin=next(p['name'] for p in pins(manager.a,manager.e(destination)) if p['guid']==guid)
        branch=manager.node(47,'K2Node_IfThenElse_Timing'+label,'',[
            ('execute',0,'exec'),('Condition',0,'bool',0,'true'),('then',1,'exec'),('else',1,'exec')],350,1100 if label=='Process' else 1400)
        manager.rewire(44,output,branch,'execute')
        manager.connect(84,'Run Inference',branch,'Condition')
        manager.connect(branch,'else',destination,destination_pin)
    manager.save('BP_AgentManager')
    
    # Preserve duration/threshold behavior, but name its units honestly. This also
    # renames the local results-function parameter receiving the same period count.
    gm=rename(load('BP_GameMode'),'SecondsElapsed','HomeostaticPeriodsElapsed')
    Path('Saved/TimingFix/BP_GameMode.patched.json').write_text(json.dumps(gm),encoding='utf-8')
    print('BP_GameMode: renamed period counter and matching local parameter')
