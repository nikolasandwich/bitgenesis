"""Study042 phase1.1 only: bounded arithmetic proof and saved birth census."""
from pathlib import Path
import json
from scripts.lineage_route_inputs import bindings as prior,read,digest
from scripts.founder_removal_inputs import validate_manifest
OUT=Path('docs/research/results')

def region(site):return 'upper' if site in (85,86) else 'middle' if site in (101,102) else 'lower' if site in (117,118) else 'other'

def run():
    manifest=prior();meta=read('data/v4-study-041/metadata.json');proof=read('data/v4-study-041/independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']==manifest
    validate_manifest({f'data/v4-study-041/{n}':h for n,h in proof['files_sha256'].items()})
    review=read('docs/research/results/v4-study-041-review.json');assert review['verdict']=='APPROVED';validate_manifest(review['files_sha256'])
    paths=[f'{root}/{prefix}{name}.json' for root,prefix in [('data/v4-study-041',''),('docs/research/results','v4-study-041-')] for name in ('metadata','records','summary','independent-verification')]
    paths+=['docs/research/v4-study-041.zh-CN.md','docs/research/results/v4-study-041-review.json','docs/research/results/v4-study-041-preservation.json','experiments/v4/study-042.md','scripts/audit_v4_middle_energy_design.py']
    manifest.update({p:digest(p) for p in paths})
    census=[];preconditions=[]
    cases=read('data/v4-study-041/records.json');assert len(cases)==8
    for c in cases:
        enc=c['encoding'];seed=c['selection']['seed'];branchpath=f'data/v4-study-039/cases/{enc}-{seed}.json';b=read(branchpath);arm=b['ablation'];source=read(b['selection']['source'])
        assert source['config']==dict(width=16,height=16,capacity=64,leak=1,bond_cost=1,threshold=16,construction_cost=4,copy_cost=1,mutation_per_thousand=0)
        assert b['selection']['exchange'] is False and all(arm['initial']['units'][s] is None for s in (101,102))
        checks=0
        for old,row in zip(c['rows'],arm['rows']):
            p=row['physical'];assert old['tick']==row['tick'];assert p['driven']['interaction']['transfers']==[]
            for site in (101,102):
                inp=p['driven']['inputs'][site];assert inp['site']==site and inp['proposed']==inp['accepted']==0;checks+=1
            for q in p['material']['proposals']:
                if q['reason']!='formed' or q['target'] not in (101,102):continue
                ev=next(e for e in old['events'] if e['source']==q['source']);child=row['site_ids'][q['target']];person=arm['final']['individuals'][child]
                assert ev['child_id']==child and person['birth_tick']==row['tick'] and person['birth_energy']==q['child_energy']
                e=p['interaction_units'][q['source']]['energy'];assert 16<=e<=64 and q['child_energy']==(e-5)//2<=29
                if region(q['source'])=='middle':assert e<=28 and q['parent_energy']<=12 and q['child_energy']<=11
                census.append(dict(encoding=enc,seed=seed,tick=row['tick'],identity=child,site=q['target'],parent=person['parent'],source=q['source'],source_region=region(q['source']),lineage=ev['lineage'],parent_preformation_energy=e,parent_after=q['parent_energy'],birth_energy=q['child_energy'],maximum_eligible_steps=max(0,q['child_energy']-16),source_path=branchpath))
        preconditions.append(dict(encoding=enc,seed=seed,future_steps=len(arm['rows']),middle_input_checks=checks,initial_middle_empty=True,exchange=False,transfers=0))
    assert len(census)==35 and sum(c['future_steps'] for c in preconditions)==116
    births=[dict(parent_pre=e,child=(e-5)//2) for e in range(16,65)]
    splits=[dict(pre=e,parent=e-5-(e-5)//2,child=(e-5)//2) for e in range(16,29)]
    windows=[dict(birth_energy=b,eligible_age_upper_bound=[a for a in range(1,30) if b-a>=16],maximum_eligible_steps=max(0,b-16)) for b in range(1,30)]
    assert max(v['child'] for v in births)==29
    assert max(v['parent'] for v in splits)==12 and max(v['child'] for v in splits)==11
    assert all(len(w['eligible_age_upper_bound'])==w['maximum_eligible_steps']<=13 for w in windows)
    validate_manifest(manifest)
    outputs=dict(sources=dict(files_sha256=manifest),census=dict(phase='1.1',physical_steps=0,full_lifecycle_audit=False,cases=preconditions,births=census),proof=dict(phase='1.1',birth_bounds=births,middle_success_bounds=splits,eligibility_bounds=windows,physical_steps=0))
    for name,obj in outputs.items():
        with (OUT/f'v4-study-042-design-{name}.json').open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print('bindings',len(manifest),'births',len(census),'input_checks',sum(x['middle_input_checks'] for x in preconditions))
if __name__=='__main__':run()
