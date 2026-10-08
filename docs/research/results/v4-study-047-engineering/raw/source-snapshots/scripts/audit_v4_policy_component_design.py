"""Study044 method-only source/schema census. No scientific observer or physics."""
import json
from pathlib import Path
from scripts.middle_north_policy_inputs import bindings,read,digest
from scripts.founder_removal_inputs import validate_manifest

def run():
    manifest=bindings();root=Path('data/v4-study-043')
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert manifest==meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']
    validate_manifest({str(root/p):h for p,h in proof['files_sha256'].items()})
    review=read('docs/research/results/v4-study-043-review.json');assert review['verdict']=='APPROVED';validate_manifest(review['files_sha256'])
    extra=['experiments/v4/study-044.md','docs/design/v4-policy-component-timing.zh-CN.md','scripts/audit_v4_policy_component_design.py','docs/research/results/v4-study-043-review.json']
    extra+=list(review['files_sha256'])+list(str(root/p) for p in proof['files_sha256'])+[str(root/'independent-verification.json')]
    records=read(root/'records.json');census=[]
    for encoding in ('east','west','south','north','homogeneous'):
        assert sorted(r['seed'] for r in records if r['encoding']==encoding)==list(range(120000,120020))
    assert len(records)==100
    for r in records:
        c={k:r[k] for k in ('encoding','seed','trigger','t0','remaining','short_window','source')}
        c.update(branch=None,arms=[],template=None)
        if r['trigger']:
            path=root/'cases'/f"{r['encoding']}-{r['seed']}.json";b=read(path);source=read(r['source']);extra.append(str(path))
            assert b['selection']==r['selection'] and b['control']['initial']==b['ablation']['initial']
            c['branch']=str(path);c['template']=[source['initial']['units'][s] for s in (85,86)]
            assert source['initial']['site_ids'][85:87]==[0,1]
            for name in ('control','ablation'):
                a=b[name];assert a['metrics']==r[name+'_future_metrics'] and a['episodes']==r[name+'_episodes']
                assert a['initial']['tick']==r['t0'] and a['final']['tick']==32
                ticks=[row['tick'] for row in a['rows']];assert ticks==list(range(r['t0']+1,33)) and len(ticks)==r['remaining']
                people=a['final']['individuals'];assert [p['id'] for p in people]==list(range(len(people)))
                assert a['final']['parents']==[p['parent'] for p in people]
                for p in people:
                    assert set(('id','parent','site','birth_tick','death_tick','program','material'))<=p.keys()
                    assert p['parent'] is None or 0<=p['parent']<p['id']
                for row in [a['initial']]+a['rows']:
                    state=row.get('physical',row);ids=row['site_ids'];units=state['units']
                    assert len(ids)==len(units)==len(state['raw'])==256
                    assert all((i is None)==(u is None) for i,u in zip(ids,units))
                    assert all(i is None or 0<=i<len(people) for i in ids)
                    assert set(('observation','copies'))<=row.keys()
                    if 'physical' in row:assert set(('births','deaths','selected_lineage'))<=row.keys()
                c['arms'].append(dict(arm=name,future_steps=len(ticks),slot_steps=3*len(ticks),diagnostic_states=1,first_tick=ticks[0],last_tick=ticks[-1],historical_individuals=len(people)))
        else:
            assert r['remaining']==0 and not any(r['applicability'].values())
            assert r['control_metrics']==r['ablation_metrics']
        census.append(c)
    arms=[a for c in census for a in c['arms']]
    assert len(arms)==56 and sum(a['future_steps'] for a in arms)==780 and sum(a['slot_steps'] for a in arms)==2340
    groups=[dict(encoding=e,n=20,triggers=sum(c['trigger'] for c in census if c['encoding']==e),short_windows=sum(c['short_window'] for c in census if c['encoding']==e),paired_arm_steps=sum(a['future_steps'] for c in census if c['encoding']==e for a in c['arms'])) for e in ('east','west','south','north','homogeneous')]
    manifest.update({p:digest(p) for p in extra});validate_manifest(manifest)
    out=Path('docs/research/results')
    for name,obj in [('sources',dict(files_sha256=manifest)),('census',dict(phase='1.1',physical_steps=0,full_scientific_audit=False,cases=census,groups=groups,diagnostic_states=56,saved_arm_steps=780,slot_steps=2340))]:
        with (out/f'v4-study-044-design-{name}.json').open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print('bindings',len(manifest),'cases',len(census),'arms',len(arms),'saved_arm_steps',780)
if __name__=='__main__':run()
