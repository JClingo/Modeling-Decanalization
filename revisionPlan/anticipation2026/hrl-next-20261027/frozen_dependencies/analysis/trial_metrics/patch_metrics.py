"""Patch exported Blueprint copies. Import/compile only in the isolated test project."""
import base64,copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'timing'))
from patch_graphs import Editor,prop,string
from graph_asset import pins
ROOT=Path('Saved/TrialMetricsFix')
class Graph(Editor):
    def scope(self,i):return self.e(self.e(i)['OuterIndex'])['ObjectName']
    def member(self,i,key='FunctionReference'):
        return next((q['Value'] for p in self.e(i).get('Data',[]) if p['Name']==key for q in p['Value'] if q['Name']=='MemberName'),None)
    def find(self,scope,member,key='FunctionReference'):
        return next(i for i,e in enumerate(self.a['Exports'],1) if e['ObjectName'].startswith('K2Node') and self.scope(i)==scope and self.member(i,key)==member)
    def named(self,name):return next(i for i,e in enumerate(self.a['Exports'],1) if e['ObjectName']==name)
    def make(self,template,label,fn,specs,scope=None,parent=None):
        old=self.e(template)['OuterIndex'];ps=pins(self.a,self.e(template));tail=base64.b64decode(self.e(template)['Extras'])[ps[-1]['end']:]
        if scope:self.e(template)['OuterIndex']=scope
        i=self.node(template,'K2Node_TrialMetrics_'+label,fn,specs,2600,100+70*len(self.changed));self.e(template)['OuterIndex']=old
        self.e(i)['Extras']=base64.b64encode(base64.b64decode(self.e(i)['Extras'])+tail).decode()
        if parent is not None:
            ref=prop(self.e(i),'FunctionReference')['Value'];member=copy.deepcopy(next(q for q in ref if q['Name']=='MemberName'))
            par=copy.deepcopy(next(q for e in self.a['Exports'] for p in e.get('Data',[]) if p['Name']=='FunctionReference' for q in p['Value'] if q['Name']=='MemberParent'))
            par['Value']=parent;ref[:]=[par,member]
        for p in list(pins(self.a,self.e(i)))[::-1]:
            if p['auto_default']:self.replace(i,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
        return i
    def cls(self,package,name,generated=False):
        for i,e in enumerate(self.a['Imports'],1):
            if e['ObjectName']==name:return -i
        pkg=copy.deepcopy(next(e for e in self.a['Imports'] if e['ClassName']=='Package'));pkg.update(ObjectName=package,OuterIndex=0)
        self.fname(package);self.a['Imports'].append(pkg);self.a['ImportBits'].append(True);pi=-len(self.a['Imports'])
        c=copy.deepcopy(next(e for e in self.a['Imports'] if e['ClassName']==('BlueprintGeneratedClass' if generated else 'Class')))
        c.update(ObjectName=name,OuterIndex=pi);self.fname(name);self.a['Imports'].append(c);self.a['ImportBits'].append(True);return -len(self.a['Imports'])
    def getter(self,template,label,name,category='real',obj=0,parent=None,scope=None):
        i=self.make(template,label,'',[(name,1,category,obj,'','double' if category=='real' else 'None'),('self',0,'object',parent or 0)],scope)
        ref=prop(self.e(i),'VariableReference')['Value'];m=copy.deepcopy(next(q for q in ref if q['Name']=='MemberName'));m['Value']=name;self.fname(name)
        if parent:
            p=copy.deepcopy(next(q for e in self.a['Exports'] for p in e.get('Data',[]) if p['Name']=='FunctionReference' for q in p['Value'] if q['Name']=='MemberParent'));p['Value']=parent;ref[:]=[p,m]
        else:
            s=copy.deepcopy(next(q for e in self.a['Exports'] for p in e.get('Data',[]) if p['Name']=='VariableReference' for q in p['Value'] if q['Name']=='bSelfContext' and q['Value']));ref[:]=[m,s]
        return i
    def write(self,name):
        for i in self.changed:
            for p in pins(self.a,self.e(i)):
                for j,g in p['links']:
                    q=next(q for q in pins(self.a,self.e(j)) if q['guid']==g);assert (i,p['guid']) in q['links']
        (ROOT/(name+'.patched.json')).write_text(json.dumps(self.a),encoding='utf-8')
def real(n,d=0,v=''):return(n,d,'real',0,v,'double')
def fix_sd(g,scope):
    sqrt=g.find(scope,'Sqrt');length=g.find(scope,'Array_Length');div=g.find(scope,'Divide_DoubleDouble');conv=g.find(scope,'Conv_IntToDouble')
    # The existing converter is the sample-count input to the mean calculation.
    assert g.member(g.p(conv,'InInt')['links'][0][0])=='Array_Length'
    source,guid=g.p(sqrt,'A')['links'][0];sp=next(p['name'] for p in pins(g.a,g.e(source)) if p['guid']==guid)
    n=g.make(div,'PopulationVariance'+scope,'Divide_DoubleDouble',[('self',0,'object',0),real('A'),real('B'),real('ReturnValue',1)])
    g.connect(source,sp,n,'A');g.connect(conv,'ReturnValue',n,'B');g.rewire(sqrt,'A',n,'ReturnValue')
lib=Graph(json.loads((ROOT/'BFL_Common.json').read_text(encoding='utf-8-sig')))
fix_sd(lib,'GetStandardDev');lib.write('BFL_Common')

env=Graph(json.loads((ROOT/'BP_AgentTrainingEnv.json').read_text(encoding='utf-8-sig')))
fix_sd(env,'GetStandardDeviation')
scope=env.e(env.named('K2Node_Homeostatic_SelectObjective'))['OuterIndex']
managercls=env.cls('/Game/Learning/BP_AgentManager','BP_AgentManager_C',True)
gmcls=next(-i for i,x in enumerate(env.a['Imports'],1) if x['ObjectName']=='BP_GameMode_C')
gm=env.find('GatherAgentReward','GameMode','VariableReference');vt=env.find('GatherAgentReward','CurrentReward','VariableReference')
manager=env.getter(vt,'Manager','AgentManager','object',managercls,gmcls,scope)
infer=env.getter(vt,'Inference','Run Inference','bool',parent=managercls,scope=scope)
env.connect(gm,'GameMode',manager,'self');env.connect(manager,'AgentManager',infer,'self')
branch=env.named('K2Node_Homeostatic_AlreadyTerminated')
gate=env.make(branch,'EvaluationMode','',[('execute',0,'exec'),('Condition',0,'bool'),('then',1,'exec'),('else',1,'exec')])
choose=env.named('K2Node_Homeostatic_SelectObjective');normal=env.named('K2Node_NF_SelectHRLOrNF')
env.rewire(choose,'then',gate,'execute');env.connect(infer,'Run Inference',gate,'Condition');env.connect(gate,'else',branch,'execute')
# Each fixed-length evaluation phase starts a fresh reward transition history.
math=env.find('GatherAgentReward','Abs');mathparent=next(q['Value'] for q in prop(env.e(math),'FunctionReference')['Value'] if q['Name']=='MemberParent')
mod=env.make(math,'PhaseStep','Percent_IntInt',[('self',0,'object',mathparent),('A',0,'int'),('B',0,'int',0,'2000'),('ReturnValue',1,'int')],parent=mathparent)
zero=env.make(math,'PhaseFirstDecision','EqualEqual_IntInt',[('self',0,'object',mathparent),('A',0,'int'),('B',0,'int',0,'0'),('ReturnValue',1,'bool')],parent=mathparent)
steps=env.find('GatherAgentReward','Episode Steps','VariableReference');env.connect(steps,'Episode Steps',mod,'A');env.connect(mod,'ReturnValue',zero,'A')
first=env.make(branch,'SeedPhase','',[('execute',0,'exec'),('Condition',0,'bool'),('then',1,'exec'),('else',1,'exec')]);env.connect(gate,'then',first,'execute');env.connect(zero,'ReturnValue',first,'Condition');env.connect(first,'else',normal,'execute')
prev=env.find('GatherAgentReward','PreviousRewardState','VariableReference');valid=env.find('GatherAgentReward','HasPreviousRewardState','VariableReference')
setter=env.named('K2Node_Homeostatic_MarkFailure')
def setvar(name,getter,category):
    i=env.make(setter,'Seed'+name,'',[('execute',0,'exec'),('then',1,'exec'),(name,0,category,0,'true' if category=='bool' else '','double' if category=='real' else 'None'),('Output_Get',1,category,0,'','double' if category=='real' else 'None'),('self',0,'object',0)])
    prop(env.e(i),'VariableReference')['Value']=copy.deepcopy(prop(env.e(getter),'VariableReference')['Value']);return i
sp=setvar('PreviousRewardState',prev,'real');sv=setvar('HasPreviousRewardState',valid,'bool');current=env.find('GatherAgentReward','GetCurrentSetpoint')
env.connect(first,'then',sp,'execute');env.connect(current,'setpoint',sp,'PreviousRewardState');env.connect(sp,'then',sv,'execute');env.connect(sv,'then',normal,'execute');env.write('BP_AgentTrainingEnv')

gm=Graph(json.loads((ROOT/'BP_GameMode.json').read_text(encoding='utf-8-sig')))
event=gm.e(gm.find('EventGraph','EstimateReward'))['OuterIndex'];mt=gm.find('EventGraph','EstimateReward')
old_acc=gm.p(mt,'then')['links'][0][0];delegate=gm.p(old_acc,'then')['links'][0][0]
source,guid=gm.p(mt,'execute')['links'][0];pin=next(p['name'] for p in pins(gm.a,gm.e(source)) if p['guid']==guid)
gm.rewire(source,pin,delegate,'execute') # no legacy score accumulation
# HandlePerception also added its legacy net score to TotalRewards through a
# separate event path. Preserve perception history but disconnect that accumulator.
for i,e in enumerate(gm.a['Exports'],1):
    if e['ObjectName'].startswith('K2Node_VariableSet') and gm.scope(i)=='EventGraph' and gm.member(i,'VariableReference')=='TotalRewards' and i!=old_acc:
        gm.disconnect(i,'execute')
managercls=gm.cls('/Game/Learning/BP_AgentManager','BP_AgentManager_C',True)
envcls=gm.cls('/Game/Learning/BP_AgentTrainingEnv','BP_AgentTrainingEnv_C',True)
vt=gm.find('EventGraph','TotalRewards','VariableReference')
mg=gm.getter(vt,'ManagerRef','AgentManager','object',managercls,scope=event)
eg=gm.getter(vt,'EnvironmentRef','TrainingEnv','object',envcls,managercls,event);gm.connect(mg,'AgentManager',eg,'self')
inf=gm.getter(vt,'InferenceRef','Run Inference','bool',parent=managercls,scope=event);gm.connect(mg,'AgentManager',inf,'self')
trial=gm.getter(vt,'TrialMode','IsTrialMode','bool',scope=event)
branch=next(i for i,e in enumerate(gm.a['Exports'],1) if e['ObjectName'].startswith('K2Node_IfThenElse') and gm.scope(i)=='EventGraph')
def gate(label,condition,output):
    b=gm.make(branch,label,'',[('execute',0,'exec'),('Condition',0,'bool'),('then',1,'exec'),('else',1,'exec')],event);gm.connect(condition,output,b,'Condition');return b
b1=gate('OnlyTrials',trial,'IsTrialMode');b2=gate('OnlyInference',inf,'Run Inference');gm.connect(b1,'then',b2,'execute')
tickseq=gm.named('K2Node_ExecutionSequence_4');assert not gm.p(tickseq,'then_3')['links'];gm.connect(tickseq,'then_3',b1,'execute')
math=gm.find('EstimateReward','Abs');mp=next(q['Value'] for q in prop(gm.e(math),'FunctionReference')['Value'] if q['Name']=='MemberParent')
tick=gm.getter(vt,'DecisionTick','TotalTickCount','int',scope=event)
limit=gm.make(math,'ScoredHorizon','LessEqual_IntInt',[('self',0,'object',mp),('A',0,'int'),('B',0,'int',0,'6000'),('ReturnValue',1,'bool')],event,mp);gm.connect(tick,'TotalTickCount',limit,'A');b3=gate('InsideTrial',limit,'ReturnValue');gm.connect(b2,'then',b3,'execute')
steps=gm.getter(vt,'RewardSteps','Episode Steps','int',parent=envcls,scope=event);gm.connect(eg,'TrainingEnv',steps,'self')
mod=gm.make(math,'FirstStepModulo','Percent_IntInt',[('self',0,'object',mp),('A',0,'int'),('B',0,'int',0,'2000'),('ReturnValue',1,'int')],event,mp)
eq=gm.make(math,'FirstStep','EqualEqual_IntInt',[('self',0,'object',mp),('A',0,'int'),('B',0,'int',0,'0'),('ReturnValue',1,'bool')],event,mp)
gm.connect(steps,'Episode Steps',mod,'A');gm.connect(mod,'ReturnValue',eq,'A');b4=gate('CapturePhaseStart',eq,'ReturnValue');gm.connect(b3,'then',b4,'execute')
pytemplate=gm.find('RunTrial','ExecutePythonCommand');pyparent=next(q['Value'] for q in prop(gm.e(pytemplate),'FunctionReference')['Value'] if q['Name']=='MemberParent')
def py(label,command,outer):
    return gm.make(pytemplate,label,'ExecutePythonCommand',[('execute',0,'exec'),('then',1,'exec'),('self',0,'object',pyparent),('PythonCommand',0,'string',0,'import trial_metrics; trial_metrics.'+command+'()'),('ReturnValue',1,'bool')],outer,pyparent)
start=py('BeginPhase','begin_phase',event);gm.connect(b4,'then',start,'execute')
reward=gm.make(mt,'GatherActualReward','GatherRewards',[('execute',0,'exec'),('then',1,'exec'),('self',0,'object',envcls)],event,envcls)
rewardvalue=gm.make(math,'ReadActualReward','GetReward',[('self',0,'object',envcls),('AgentId',0,'int',0,'0'),('ReturnValue',1,'real',0,'','float')],event,envcls)
agentzero=gm.make(math,'AgentZero','Conv_BoolToInt',[('self',0,'object',mp),('InBool',0,'bool',0,'false'),('ReturnValue',1,'int')],event,mp)
gm.connect(agentzero,'ReturnValue',rewardvalue,'AgentId') # native metadata otherwise reconstructs default -1
gm.connect(eg,'TrainingEnv',rewardvalue,'self')
gm.connect(eg,'TrainingEnv',reward,'self');gm.connect(start,'then',reward,'execute');gm.connect(b4,'else',reward,'execute');gm.connect(reward,'then',old_acc,'execute')
add=gm.p(old_acc,'TotalRewards')['links'][0][0];gm.rewire(add,'A',rewardvalue,'ReturnValue')
# Record the completed phase before existing serialization clears its histories.
store=gm.find('StoreTrial','StoreTrial');dest=gm.p(store,'then')['links'][0][0]
capture=py('CaptureCompletedPhase','capture_phase',gm.e(store)['OuterIndex']);gm.rewire(store,'then',capture,'execute');gm.connect(capture,'then',dest,'execute')
writeok=gm.named('K2Node_TrialYaml_WriteSucceeded');checkpoint=py('LinkProvenance','checkpoint',gm.e(writeok)['OuterIndex']);assert not gm.p(writeok,'then')['links'];gm.connect(writeok,'then',checkpoint,'execute')
# Logged duration is now explicit simulation seconds, consistent with 2000 * .05.
duration=gm.find('RunTrial','SequenceDuration','VariableReference')
duration=next(i for i,e in enumerate(gm.a['Exports'],1) if gm.scope(i)=='RunTrial' and e['ObjectName'].startswith('K2Node_VariableSet') and gm.member(i,'VariableReference')=='SequenceDuration')
p=gm.p(duration,'SequenceDuration');gm.replace(duration,p['default_start'],p['default_end'],string('100'))
gm.write('BP_GameMode')
print('Staged population SD, shared actual reward callbacks, and provenance hooks.')
