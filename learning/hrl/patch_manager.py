"""Wire an explicit per-run seed into native policy and critic initialization."""
from pathlib import Path
import base64,json,sys

def patch(source,destination,helpers):
    sys.path.insert(0,str(helpers))
    from graph_asset import pins
    from patch_graphs import Editor,prop
    ed=Editor(json.loads(Path(source).read_text(encoding='utf-8-sig')))
    calls=[]
    for i,e in enumerate(ed.a['Exports'],1):
        f=next((p for p in e.get('Data',[]) if p['Name']=='FunctionReference'),None)
        name=next((p['Value'] for p in f['Value'] if p['Name']=='MemberName'),'') if f else ''
        if name in ['MakePolicy','MakeCritic']:calls.append(i)
    assert len(calls)==2
    template=next(i for i,e in enumerate(ed.a['Exports'],1) if e['OuterIndex']==ed.e(calls[0])['OuterIndex'] and 'VariableGet' in e['ObjectName'])
    def getter(name,kind,default):
        existing=next((i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']=='K2Node_HRLLearning_'+name),None)
        if existing:return existing
        old=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[old[-1]['end']:]
        i=ed.node(template,'K2Node_HRLLearning_'+name,'',[
            (name,1,kind,0,default),('self',0,'object',0)],600,1400)
        ed.e(i)['Extras']=base64.b64encode(base64.b64decode(ed.e(i)['Extras'])+tail).decode()
        ref=prop(ed.e(i),'VariableReference');ref['Value']=[p for p in ref['Value'] if p['Name'] in ['MemberName','bSelfContext']]
        next(p for p in ref['Value'] if p['Name']=='MemberName')['Value']=name;ed.fname(name)
        return i
    i=getter('InitializationSeed','int','1234')
    for target in calls:
        if not ed.p(target,'Seed')['links']:ed.connect(i,'InitializationSeed',target,'Seed')
    update=getter('ResetWorldOnPolicyUpdate','bool','true')
    training=[]
    for j,e in enumerate(ed.a['Exports'],1):
        f=next((p for p in e.get('Data',[]) if p['Name']=='FunctionReference'),None)
        name=next((p['Value'] for p in f['Value'] if p['Name']=='MemberName'),'') if f else ''
        if name=='RunTraining':training.append(j)
    assert len(training)==1
    ed.disconnect(training[0],'bResetAgentsOnUpdate')
    ed.connect(update,'ResetWorldOnPolicyUpdate',training[0],'bResetAgentsOnUpdate')
    Path(destination).write_text(json.dumps(ed.a),encoding='utf-8')
