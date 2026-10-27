import json
from graph_asset import load, pins

def describe(asset, indices):
    for i in indices:
        e = asset['Exports'][i-1]
        parent = asset['Exports'][e['OuterIndex']-1]['ObjectName'] if e['OuterIndex'] > 0 else ''
        print(i, parent, e['ObjectName'])
        for p in e.get('Data', []):
            if p['Name'] in ['FunctionReference','VariableReference','EventReference','NodeComment']:
                v = p['Value']
                print(' ', p['Name'], [(x['Name'],x.get('Value')) for x in v] if isinstance(v,list) else v)
        try:
            for p in pins(asset,e):
                print(' ',p['name'],p['direction'],p['default'], '->',
                      [(j,asset['Exports'][j-1]['ObjectName'],guid) for j,guid in p['links'] if j>0])
        except Exception as ex: print(' ',ex)

if __name__ == '__main__':
    selections = {
        'BP_Agent': ['K2Node_PromotableOperator_16','K2Node_PromotableOperator_18','K2Node_PromotableOperator_22','K2Node_PromotableOperator_19','K2Node_VariableSet_13','K2Node_VariableSet_24'],
        'BP_AgentManager': ['K2Node_CallFunction_11','K2Node_VariableGet_44'],
        'BP_AgentInteractor': ['K2Node_CallFunction_4','K2Node_CallFunction_8427'],
    }
    for name, wanted in selections.items():
        a=load(name); print('\n'+name)
        describe(a,[i for i,e in enumerate(a['Exports'],1) if e['ObjectName'] in wanted])
    for name in ['BP_AgentManager','BP_GameMode']:
        a=load(name)
        print(name,'DEFAULTS')
        e=next(e for e in a['Exports'] if e['ObjectName']=='Default__'+name+'_C')
        for p in e['Data']:
            if any(s in p['Name'].lower() for s in ['training','inference','loss','time','tick','second','trial']):
                print(p['Name'],json.dumps(p.get('Value')))
