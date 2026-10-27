"""Cache each trial's initial homeostatic state and reuse it at phase boundaries."""
import base64
import copy
import json
from pathlib import Path
from graph_asset import pins
from patch_graphs import Editor,prop,string
root=Path('Saved/PhaseVelocityFix')
ed=Editor(json.loads((root/'gm.variables.json').read_text(encoding='utf-8-sig')))
name='TrialStartingHomeostaticState'
def member(e,kind):
    return next((q['Value'] for p in e.get('Data',[]) if p['Name']==kind for q in p['Value'] if q['Name']=='MemberName'),None)
def scope(e):return ed.e(e['OuterIndex'])['ObjectName'] if e['OuterIndex']>0 else ''
def find(kind,value,graph):
    return next(i for i,e in enumerate(ed.a['Exports'],1) if member(e,kind)==value and scope(e)==graph)
def variable(template,label,setter,default=''):
    old=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[old[-1]['end']:]
    specs=([('execute',0,'exec'),('then',1,'exec'),(name,0,'real',0,default,'double'),('Output_Get',1,'real',0,'','double')]
           if setter else [(name,1,'real',0,'','double')])+[('self',0,'object',0)]
    i=ed.node(template,'K2Node_PhaseHomeostasis_'+label,'',specs,2100,900)
    ed.e(i)['Extras']=base64.b64encode(base64.b64decode(ed.e(i)['Extras'])+tail).decode()
    for p in list(pins(ed.a,ed.e(i)))[::-1]:
        if p['auto_default']:ed.replace(i,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
    r=prop(ed.e(i),'VariableReference')['Value']
    n=copy.deepcopy(next(q for q in r if q['Name']=='MemberName'));n['Value']=name;ed.fname(name)
    c=copy.deepcopy(next(q for e in ed.a['Exports'] for p in e.get('Data',[]) if p['Name']=='VariableReference' for q in p['Value'] if q['Name']=='bSelfContext' and q['Value']))
    r[:]=[n,c]
    return i
template=find('VariableReference','TotalLoss','ResetValues')
adds=[i for i,e in enumerate(ed.a['Exports'],1) if scope(e)=='ResetValues' and member(e,'FunctionReference')=='Array_Add'
      and any(p['name']=='NewItem' and (p['default']=='-15.000000' or p['links'] and member(ed.e(p['links'][0][0]),'FunctionReference')=='RandomFloatInRangeFromStream') for p in pins(ed.a,e))]
assert len(adds)==2
for add in adds:
    source,guid=ed.p(add,'execute')['links'][0]
    source_pin=next(p['name'] for p in pins(ed.a,ed.e(source)) if p['guid']==guid)
    item=ed.p(add,'NewItem');random=bool(item['links'])
    setter=variable(template,'CaptureRandomStart' if random else 'CaptureTrainingStart',True,'' if random else item['default'])
    if random:
        r,g=item['links'][0];rpin=next(p['name'] for p in pins(ed.a,ed.e(r)) if p['guid']==g)
        ed.connect(r,rpin,setter,name)
    ed.rewire(source,source_pin,setter,'execute');ed.connect(setter,'then',add,'execute')
    ed.disconnect(add,'NewItem');ed.connect(setter,'Output_Get',add,'NewItem')
phase_add=next(i for i,e in enumerate(ed.a['Exports'],1) if scope(e)=='RunTrial' and member(e,'FunctionReference')=='Array_Add'
               and any(p['name']=='NewItem' and p['links'] and member(ed.e(p['links'][0][0]),'FunctionReference')=='RandomFloatInRangeFromStream' for p in pins(ed.a,e)))
getter=variable(find('VariableReference','TotalTickCount','RunTrial'),'RestoreTrialStart',False)
ed.rewire(phase_add,'NewItem',getter,name)
ed.save('BP_GameMode')
(root/'gm.homeostasis.patched.json').write_text(json.dumps(ed.a))
