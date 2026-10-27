"""Author reward selection and native decision counters, then compile with UE."""
from pathlib import Path
import argparse,base64,json,sys

def patch(source,destination,helpers):
    sys.path.insert(0,str(helpers))
    from graph_asset import pins
    from patch_graphs import Editor,prop,string
    ed=Editor(json.loads(Path(source).read_text(encoding='utf-8-sig')))
    def named(name):return next(i for i,e in enumerate(ed.a['Exports'],1) if e['ObjectName']==name)
    quality=named('K2Node_Homeostatic_Quality');graph=ed.e(quality)['OuterIndex']
    def node(template,name,function,specs):
        old=pins(ed.a,ed.e(template));tail=base64.b64decode(ed.e(template)['Extras'])[old[-1]['end']:]
        parent=ed.e(template)['OuterIndex'];ed.e(template)['OuterIndex']=graph
        i=ed.node(template,'K2Node_HRLLearning_'+name,function,specs,3200,200+len(ed.changed)*80)
        ed.e(template)['OuterIndex']=parent
        ed.e(i)['Extras']=base64.b64encode(base64.b64decode(ed.e(i)['Extras'])+tail).decode()
        for p in list(pins(ed.a,ed.e(i)))[::-1]:
            if p['default']:
                length=4+(len(p['auto_default'].encode())+1 if p['auto_default'] else 0)
                ed.replace(i,p['default_end'],p['default_end']+length,string(''))
        return i
    real=lambda name,d=0,value='':(name,d,'real',0,value,'double')
    boolean=lambda name,d=0,value='':(name,d,'bool',0,value)
    def get(name,kind='real'):
        template=named('K2Node_Homeostatic_GetRewardDistanceScale')
        spec=boolean(name,1) if kind=='bool' else real(name,1)
        i=node(template,'Get'+name,'',[spec,('self',0,'object',0)])
        r=prop(ed.e(i),'VariableReference');r['Value']=[p for p in r['Value'] if p['Name'] in ['MemberName','bSelfContext']]
        next(p for p in r['Value'] if p['Name']=='MemberName')['Value']=name;ed.fname(name)
        return i,name
    def math_node(name,function,inputs,output=None):
        specs=[('self',0,'object',0)]+inputs+[output or real('ReturnValue',1)]
        i=node(quality,name,function,specs)
        return i,'ReturnValue'
    def link(source,target,pin):ed.connect(source[0],source[1],target[0],pin)
    def binary(name,function,a,b,output=None):
        target=math_node(name,function,[real('A'),real('B')],output)
        link(a,target,'A');link(b,target,'B');return target
    # Add_DoubleDouble inherits B=1 during Blueprint pin reconstruction.
    # FMax(v,v) has zero defaults and preserves every authored constant.
    def constant(name,value):return math_node(name,'FMax',[real('A',value=str(value)),real('B',value=str(value))])
    def select(name,a,b,condition):
        target=math_node(name,'SelectFloat',[real('A'),real('B'),boolean('bPickA')])
        link(a,target,'A');link(b,target,'B');link(condition,target,'bPickA');return target
    def source_pin(index,pin):
        j,g=ed.p(index,pin)['links'][0]
        return j,next(p['name'] for p in pins(ed.a,ed.e(j)) if p['guid']==g)
    normalized=named('K2Node_Homeostatic_NormalizedDistance')
    absolute_h=source_pin(normalized,'A');signed_h=source_pin(absolute_h[0],'A')
    delta=(named('K2Node_Homeostatic_DeltaSeconds'),'ReturnValue')
    normal=(normalized,'ReturnValue')
    minus=constant('MinusOne',-1)
    negative=binary('NegativeAbsoluteDistance','Multiply_DoubleDouble',normal,minus)
    negative=binary('NegativeDistanceRate','Multiply_DoubleDouble',negative,(named('K2Node_Homeostatic_SafeRate'),'ReturnValue'))
    reward_rate=select('RewardRate',negative,(quality,'ReturnValue'),get('UseAbsoluteErrorReward','bool'))
    integrated=(named('K2Node_Homeostatic_TimeIntegratedQuality'),'ReturnValue')
    ed.disconnect(integrated[0],'A');link(reward_rate,integrated,'A')

    # Sampling occurs before reward/failure branches, including all out-of-bounds
    # decisions during fixed-horizon inference. No per-decision Python callback.
    entry=next(i for i,e in enumerate(ed.a['Exports'],1) if e['OuterIndex']==graph and 'FunctionEntry' in e['ObjectName'])
    old_target=source_pin(entry,'then')
    branch=node(named('K2Node_Homeostatic_SelectObjective'),'RecordDecision','',[
        ('execute',0,'exec'),boolean('Condition'),('then',1,'exec'),('else',1,'exec')])
    ed.rewire(entry,'then',branch,'execute')
    ed.connect(branch,'else',old_target[0],old_target[1]);link(get('RecordDecisionHomeostasis','bool'),(branch,''),'Condition')
    one=constant('One',1);zero=constant('Zero',0);five=constant('Five',5);hundred=constant('Hundred',100)
    inside=binary('WithinFive','LessEqual_DoubleDouble',absolute_h,five,boolean('ReturnValue',1))
    outside=binary('OutsideFive','Greater_DoubleDouble',absolute_h,five,boolean('ReturnValue',1))
    extreme=binary('ExtremeError','Greater_DoubleDouble',absolute_h,hundred,boolean('ReturnValue',1))
    previous_out=get('DecisionOutOfBandTime')
    had_out=binary('HadExcursion','Greater_DoubleDouble',previous_out,zero,boolean('ReturnValue',1))
    recovery=math_node('CompletedRecovery','BooleanAND',[boolean('A'),boolean('B')],boolean('ReturnValue',1))
    link(had_out,recovery,'A');link(inside,recovery,'B')
    square=binary('SquareH','Multiply_DoubleDouble',signed_h,signed_h)
    measurements=[
        ('DecisionSampleCount',one),('DecisionDuration',delta),
        ('DecisionAbsoluteIntegral',binary('AbsoluteTime','Multiply_DoubleDouble',absolute_h,delta)),
        ('DecisionSquaredIntegral',binary('SquaredTime','Multiply_DoubleDouble',square,delta)),
        ('DecisionSignedIntegral',binary('SignedTime','Multiply_DoubleDouble',signed_h,delta)),
        ('DecisionWithin5Time',select('WithinTime',delta,zero,inside)),
        ('DecisionExtremeTime',select('ExtremeTime',delta,zero,extreme)),
        ('DecisionRecoveryCount',select('RecoveryIncrement',one,zero,recovery)),
        ('DecisionRecoveryTimeSum',select('RecoveryDuration',previous_out,zero,recovery)),
    ]
    previous=(branch,'then')
    def assign(name,value):
        nonlocal previous
        i=node(named('K2Node_Homeostatic_CountDecision'),'Set'+name,'',[
            ('execute',0,'exec'),('then',1,'exec'),real(name),real('Output_Get',1),('self',0,'object',0)])
        ref=prop(ed.e(i),'VariableReference');ref['Value']=[p for p in ref['Value'] if p['Name'] in ['MemberName','bSelfContext']]
        next(p for p in ref['Value'] if p['Name']=='MemberName')['Value']=name;ed.fname(name)
        ed.connect(previous[0],previous[1],i,'execute');link(value,(i,''),name);previous=(i,'then')
    for name,increment in measurements:
        assign(name,binary('Accumulate'+name,'Add_DoubleDouble',get(name),increment))
    assign('DecisionMaximumAbsoluteH',binary('MaximumAbsoluteH','FMax',get('DecisionMaximumAbsoluteH'),absolute_h))
    # Update the streak last: recovery calculations must see its previous value.
    assign('DecisionOutOfBandTime',select('ExcursionTime',binary('ExtendExcursion','Add_DoubleDouble',previous_out,delta),zero,outside))
    ed.connect(previous[0],previous[1],old_target[0],old_target[1])
    for i in ed.changed:
        for p in pins(ed.a,ed.e(i)):
            for j,g in p['links']:
                peer=next(q for q in pins(ed.a,ed.e(j)) if q['guid']==g)
                assert (i,p['guid']) in peer['links']
    Path(destination).write_text(json.dumps(ed.a),encoding='utf-8')
    return len(ed.changed)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path);p.add_argument('--helpers',type=Path,required=True)
    a=p.parse_args();print('Authored nodes:',patch(a.source,a.destination,a.helpers))
