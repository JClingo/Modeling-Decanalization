"""Stage graph-only count-transform variants; Unreal must compile each asset."""
from pathlib import Path
import argparse, json, sys

parser=argparse.ArgumentParser()
parser.add_argument('original',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--retain',type=float,required=True)
parser.add_argument('--exact',action='store_true')
parser.add_argument('--helpers',type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.helpers))
from patch_graphs import Editor,prop,string

ed=Editor(json.loads(args.original.read_text()))
assert ed.e(60)['ObjectName']=='K2Node_PromotableOperator_5'
assert ed.e(98)['ObjectName']=='K2Node_VariableSet_2'
ref=prop(ed.e(60),'FunctionReference')['Value']
member=next(p for p in ref if p['Name']=='MemberName')
assert member['Value']=='Divide_DoubleDouble'
assert ed.p(60,'B')['default']=='2.000000'
member['Value']='Multiply_DoubleDouble'
ed.fname(member['Value'])
p=ed.p(60,'B')
ed.replace(60,p['default_start'],p['default_end'],string(str(args.retain)))
if args.exact:
    ed.rewire(98,'OverlapCount',60,'ReturnValue')
for idx in ed.changed:
    for p in __import__('graph_asset').pins(ed.a,ed.e(idx)):
        for j,g in p['links']:
            q=next(q for q in __import__('graph_asset').pins(ed.a,ed.e(j)) if q['guid']==g)
            assert (idx,p['guid']) in q['links']
args.output.write_text(json.dumps(ed.a))
print('Graph staged: retain',args.retain,'floor',not args.exact)
