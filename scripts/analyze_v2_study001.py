"""Independent behavior check and complete descriptive sensitivity tables."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import csv
import json
from pathlib import Path
from scripts.verify_v2_study001 import verify


def probabilities(weights,food,energy):
    vector=[f*1000//24 for f in food]+[energy*1000//160,1000]
    scores=[sum(a*b for a,b in zip(weights[offset:offset+7],vector)) for offset in range(0,35,7)]
    winners=[i for i in range(5) if scores[i]==max(scores)]
    counts=Counter(winners[ticket%len(winners)] for ticket in range(60))
    return [Fraction(counts[i],60) for i in range(5)]


def behavioral_difference(first,second):
    foods=[[0]*5,[12]*5,[24,0,0,0,0]]
    foods += [[24 if i==direction else 0 for i in range(5)] for direction in range(1,5)]
    foods += [[6,24,12,6,0]]
    values=[]
    for food in foods:
        for energy in (1,24,80,160):
            a,b=probabilities(first,food,energy),probabilities(second,food,energy)
            values.append(sum((abs(x-y) for x,y in zip(a,b)),Fraction(0))/2)
    return sum(values,Fraction(0))/32


def main():
    root=Path('data/v2-study-001')
    structure=verify(root)
    rows=json.loads((root/'results.json').read_text())
    output=root/'analysis'
    output.mkdir(exist_ok=False)
    variants=[]
    parents=[]
    for row in rows:
        parent=row['parent']; p=parent['development']
        parent_counts=Counter()
        parent_tvs=[]
        for v in row['variants']:
            child=v['construction']; c=child['development']
            expected={'weights_changed':p['weights']!=c['weights'],
                      'active_sites_changed':p['active_sites']!=c['active_sites'],
                      'cost_change':c['cost']-p['cost']}
            if any(v[k]!=value for k,value in expected.items()):
                raise ValueError('structural difference mismatch')
            tv=behavioral_difference(p['weights'],c['weights']) if parent['valid'] and child['valid'] else None
            if v['behavior_mean_tv']!=(str(tv) if tv is not None else None):
                raise ValueError('behavior mismatch')
            parent_counts[v['validity_transition']]+=1
            parent_counts['weight_changes']+=int(expected['weights_changed'])
            parent_counts['active_changes']+=int(expected['active_sites_changed'])
            parent_counts['behavior_comparable']+=int(tv is not None)
            parent_counts['behavior_changes']+=int(tv is not None and tv>0)
            if tv is not None:
                parent_tvs.append(tv)
            variants.append({'source':row['source_seed'],'parent_index':row['parent_index'],
                'coordinate':v['coordinate'],'delta':v['delta'],
                'parent_valid':parent['valid'],'variant_valid':child['valid'],
                'variant_reason':c['reason'],'transition':v['validity_transition'],
                'silent_genotype':v['silent_genotype'],**expected,'behavior_tv':str(tv) if tv is not None else None})
        parents.append({'source':row['source_seed'],'parent_index':row['parent_index'],
            'valid':parent['valid'],'reason':p['reason'],**dict(parent_counts),
            'conditional_mean_tv':str(sum(parent_tvs,Fraction(0))/len(parent_tvs)) if parent_tvs else None})
    sources=[]
    for seed in range(83000,83020):
        group=[p for p in parents if p['source']==seed]
        totals=Counter()
        for p in group:
            totals.update({k:v for k,v in p.items() if k not in ('source','parent_index','valid','reason','conditional_mean_tv')})
        means=[Fraction(p['conditional_mean_tv']) for p in group if p['conditional_mean_tv'] is not None]
        sources.append({'source':seed,'parents':5,'valid_parents':sum(p['valid'] for p in group),
            **dict(totals),'conditional_parent_equal_mean_tv':str(sum(means,Fraction(0))/len(means)) if means else None})
    summary={'scope':'complete structural and fixed-probe sensitivity; no population evolution or fitness measurement',
        'structure_verification':structure,'sources':sources,
        'behavior_comparable':sum(v['behavior_tv'] is not None for v in variants),
        'behavior_changes':sum(v['behavior_tv'] is not None and Fraction(v['behavior_tv'])>0 for v in variants),
        'weights_changed':sum(v['weights_changed'] for v in variants),
        'active_sites_changed':sum(v['active_sites_changed'] for v in variants),
        'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
    for name,data in [('variants.csv',variants),('parents.csv',parents),('sources.csv',sources)]:
        fields=list(dict.fromkeys(k for row in data for k in row))
        with (output/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields)
            writer.writeheader();writer.writerows(data)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('structure_verification','sources')},indent=2))


if __name__=='__main__':
    main()
