"""Read-only Study039 method census and finite proof checks; no dynamics."""
import json
from pathlib import Path
from scripts.program_position_inputs import bindings, source_path, digest

OUT=Path('docs/research/results')
def run():
    manifest=bindings()
    records=json.loads(Path('data/v4-study-038/records.json').read_text())
    old=json.loads(Path('data/v4-study-036/records.json').read_text())
    census=[]
    for r in records:
        enc,seed=r['encoding'],r['seed']
        path=Path(f'data/v4-study-038/cases/{enc}-{seed}.json') if enc in ('east','west','south') else source_path(seed,enc)
        manifest[str(path)]=digest(path)
        case=json.loads(path.read_text())
        t=next((i for i,n in enumerate(r['series']['new_genetic_copy_count'],1) if n>=1),None)
        assert t==r['first_new_genetic_copy_tick']
        stock=[n+int(u is not None) for n,u in zip(case['initial']['raw'],case['initial']['units'])]
        assert [i for i,n in enumerate(stock) if n]==[85,86,101,102,117,118,204]
        assert all(n in (0,1) for n in stock)
        for row in case['rows']:
            p=row['physical']
            assert row['site_ids'][85:87]==[0,1]
            assert all(p['units'][i]['energy']>0 for i in (85,86))
            assert [n+int(u is not None) for n,u in zip(p['raw'],p['units'])]==stock
        match=None
        if enc in ('north','homogeneous') and t is not None:
            matches=[(i,o) for i,o in enumerate(old) if o['selection']['mode']=='random-direction' and not o['selection']['exchange'] and o['selection']['seed']==seed and o['selection']['genotype']==('heterogeneous' if enc=='north' else enc)]
            assert len(matches)==1
            match,o=matches[0];assert o['selection']['t0']==t and o['selection']['remaining_steps']==32-t
        census.append(dict(encoding=enc,seed=seed,source=str(path),trigger=t is not None,t0=t,remaining=32-t if t else 0,short_window=t is not None and 32-t<10,reuse_branch=match))
    assert len(census)==100 and sum(x['trigger'] for x in census)==28
    totals={e:dict(n=20,triggers=sum(x['trigger'] for x in census if x['encoding']==e),remaining=sum(x['remaining'] for x in census if x['encoding']==e),short=sum(x['short_window'] for x in census if x['encoding']==e)) for e in ('east','west','south','north','homogeneous')}
    pre=[dict(energy=e,cost=c,lower=min(64,e+8)-1-c) for e in range(1,65) for c in range(5)]
    parents=[dict(pre=e,parent=(e-5)-(e-5)//2) for e in range(16,65)]
    support={85,86,101,102,117,118,204}
    slots=[[s,(s//16)*16+(s%16+1)%16] for s in range(256) if {s,(s//16)*16+(s%16+1)%16}<=support]
    assert slots==[[85,86],[101,102],[117,118]] and min(x['lower'] for x in pre)==4 and min(x['parent'] for x in parents)==6
    for p in ['data/v4-study-038/records.json','data/v4-study-036/records.json','experiments/v4/study-039.md',__file__]+[str(p) for p in Path('src/bitgenesis/v4').glob('*.py')]:
        p=str(Path(p).relative_to(Path.cwd())) if Path(p).is_absolute() else p
        manifest[p]=digest(p)
    for p,h in manifest.items():assert digest(p)==h
    outputs={'census':dict(cases=census,totals=totals,source_states_checked=3200,physical_steps=0,reuse_status='time/key matched; full state and metrics matching required in task2.1'), 'proof':dict(preformation_checks=pre,successful_parent_checks=parents,horizontal_slots=slots,physical_steps=0), 'sources':dict(files_sha256=manifest)}
    for name,data in outputs.items():
        path=OUT/f'v4-study-039-design-{name}.json'
        with path.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(totals));print('bound sources',len(manifest),'states checked',3200,'physics',0)
if __name__=='__main__':run()
