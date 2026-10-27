"""Authored graph variants in marked copies; compile before evaluating."""
from pathlib import Path
import json,sys

def patch_variants(project,settings,asset,helpers):
    assert (project/'HRL_LEARNING_COPY').exists()
    sys.path.insert(0,str(helpers))
    from patch_graphs import Editor,string
    def edit(relative,callback):
        target=project/'Content'/relative
        source=project.parent/(Path(relative).stem+'.audit-source.json')
        destination=source.with_name(source.stem+'.patched.json')
        asset(project.parent,'export',target,source)
        ed=Editor(json.loads(source.read_text(encoding='utf-8-sig')))
        callback(ed)
        destination.write_text(json.dumps(ed.a))
        asset(project.parent,'import',destination,target)
    def literal(ed,index,pin,value):
        ed.disconnect(index,pin)
        p=ed.p(index,pin);ed.replace(index,p['default_start'],p['default_end'],string(str(value)))
    if 'inference_action_noise' in settings:
        value=float(settings['inference_action_noise']);assert value in (0.,1.)
        def noise(ed):
            found=[]
            for i,e in enumerate(ed.a['Exports'],1):
                ref=next((p for p in e.get('Data',[]) if p['Name']=='FunctionReference'),None)
                if ref and any(x['Name']=='MemberName' and x.get('Value')=='RunInference' for x in ref['Value']):found.append(i)
            assert len(found)==1
            assert not ed.p(found[0],'ActionNoiseScale')['links']
            literal(ed,found[0],'ActionNoiseScale',value)
        edit('Learning/BP_AgentManager.uasset',noise)
    if settings.get('static_tile_costs'):
        def tile(ed):
            # All three ordinary-contact/decanalization cost branches.
            found=[]
            for i,e in enumerate(ed.a['Exports'],1):
                ref=next((p for p in e.get('Data',[]) if p['Name']=='FunctionReference'),None)
                if not ref or not any(x['Name']=='MemberName' and x.get('Value')=='Divide_DoubleDouble' for x in ref['Value']):continue
                a=ed.p(i,'A')
                if not a['links']:continue
                source=ed.e(a['links'][0][0])
                r=next((p for p in source.get('Data',[]) if p['Name']=='VariableReference'),None)
                if r and any(x['Name']=='MemberName' and x.get('Value')=='BaseHomeostaticImpact' for x in r['Value']):found.append(i)
            assert len(found)==3,found
            for i in found:literal(ed,i,'B',2.)
        def agent(ed):
            i=next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']=='K2Node_Anticipation_TileLossPerSecond')
            literal(ed,i,'B',2.)
        edit('Level/BP_Tile.uasset',tile)
        edit('Agent/BP_Agent.uasset',agent)
