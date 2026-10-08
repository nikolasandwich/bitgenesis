"""Study043 method-only source/selection/ticket census; no physics execution."""
import json
from pathlib import Path
from scripts.middle_energy_inputs import bindings, read, digest
from scripts.founder_removal_inputs import validate_manifest

def run():
    manifest=bindings()
    meta=read('data/v4-study-042/metadata.json'); proof=read('data/v4-study-042/independent-verification.json')
    assert meta['status']=='complete' and proof['status']=='verified'
    assert meta['input_sha256']==meta['input_sha256_after']==proof['input_sha256']==proof['input_sha256_after']==manifest
    validate_manifest({f'data/v4-study-042/{p}':h for p,h in proof['files_sha256'].items()})
    review=read('docs/research/results/v4-study-042-review.json')
    assert review['verdict']=='APPROVED';validate_manifest(review['files_sha256'])
    extra=['experiments/v4/study-043.md','docs/design/v4-middle-north-policy.zh-CN.md','scripts/audit_v4_middle_north_design.py','docs/design/v4-structure-copy-control.zh-CN.md','experiments/v4/study-019.md','data/v4-study-039/records.json','data/v4-study-036/records.json']
    extra += [f'{root}/{prefix}{name}.json' for root,prefix in [('data/v4-study-042',''),('docs/research/results','v4-study-042-')] for name in ('metadata','records','summary','independent-verification')]
    extra += ['docs/research/v4-study-042.zh-CN.md','docs/research/results/v4-study-042-review.json','docs/research/results/v4-study-042-preservation.json']
    observed={(r['encoding'],r['seed']):r for r in read('data/v4-study-038/records.json')}
    extra.append('data/v4-study-038/records.json')
    cases=read('data/v4-study-039/records.json');old=read('data/v4-study-036/records.json');result=[]
    assert len(cases)==100
    for enc in ('east','west','south','north','homogeneous'):
        assert sorted(c['seed'] for c in cases if c['encoding']==enc)==list(range(120000,120020))
    for c in cases:
        src=read(c['source']);extra.append(c['source'])
        series=observed[c['encoding'],c['seed']]['series']['new_genetic_copy_count']
        hits=[tick for tick,n in enumerate(series,1) if n>=1]
        assert bool(hits)==c['trigger'] and (hits[0] if hits else None)==c['t0']
        item={k:c[k] for k in ('encoding','seed','source','trigger','t0','remaining','short_window')}
        item.update(baseline=None,mask=[])
        if c['trigger']:
            if c['encoding'] in ('east','west'):
                path=f"data/v4-study-039/cases/{c['encoding']}-{c['seed']}.json"
            else:
                matches=[i for i,r in enumerate(old) if r['selection']==c['selection']];assert len(matches)==1
                path=f'data/v4-study-036/cases/branch-{matches[0]:03d}.json'
            b=read(path);extra.append(path)
            assert b['selection']==c['selection'] and b['ablation']['metrics']==c['ablation_future_metrics']
            assert len(b['ablation']['rows'])==c['remaining']==32-c['t0']
            assert b['ablation']['initial']['tick']==c['t0']
            assert b['ablation']['initial']['units'][85] is None and b['ablation']['initial']['units'][86] is None
            item['baseline']=path
            for r in src['rows'][c['t0']:]:
                oldrow=b['ablation']['rows'][r['tick']-c['t0']-1]
                assert r['physical']['directions']==oldrow['physical']['directions']
                for site in (101,102):
                    direction=r['physical']['directions'][site]
                    assert direction in range(4)
                    item['mask'].append(dict(tick=r['tick'],site=site,original_direction=direction,new_direction=3,changed=direction!=3))
        result.append(item)
    assert sum(c['trigger'] for c in result)==28 and sum(len(c['mask']) for c in result)==780
    groups=[]
    for enc in ('east','west','south','north','homogeneous'):
        cs=[c for c in result if c['encoding']==enc];mask=[m for c in cs for m in c['mask']]
        groups.append(dict(encoding=enc,n=len(cs),triggered=sum(c['trigger'] for c in cs),short_windows=sum(c['short_window'] for c in cs),future_steps=len(mask)//2,mask_slots=len(mask),changed_tickets=sum(m['changed'] for m in mask),original_directions={str(d):sum(m['original_direction']==d for m in mask) for d in range(4)}))
    manifest.update({p:digest(p) for p in extra});validate_manifest(manifest)
    out=Path('docs/research/results')
    for name,obj in [('sources',dict(files_sha256=manifest)),('census',dict(phase='1.1',physical_steps=0,policy_executed=False,cases=result,groups=groups))]:
        with (out/f'v4-study-043-design-{name}.json').open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(bindings=len(manifest),groups=groups)))
if __name__=='__main__':run()
