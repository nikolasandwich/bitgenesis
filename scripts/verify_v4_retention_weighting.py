"""Independent original-identity intersections and retention-weight arithmetic."""
import json
from pathlib import Path
from fractions import Fraction
from itertools import product
from hashlib import sha256

CLASSES=('world','singleton','local_multi','all')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def initial_records(initial,on,off):
    original={i for i in initial['site_ids'] if i is not None};groups=initial['observation']['components']['material']
    flat=[i for g in groups for i in g]
    assert len(flat)==len(set(flat))==len(original) and set(flat)==original
    assert all(groups)
    alive={side:{i for i in final['site_ids'] if i is not None} for side,final in (('on',on),('off',off))}
    assert all(len(alive[side])==sum(i is not None for i in final['site_ids']) for side,final in (('on',on),('off',off)))
    return [dict(component=c,category='world' if len(g)==len(original) else 'singleton' if len(g)==1 else 'local_multi',size=len(g),on=len(set(g)&alive['on']),off=len(set(g)&alive['off'])) for c,g in enumerate(groups)]


def measure(records,total):
    C=len(records);N=sum(r['size'] for r in records);A=sum(r['on'] for r in records);B=sum(r['off'] for r in records)
    result=dict(components=C,initial=N,on=A,off=B,count_difference=A-B)
    rates=('component_on','component_off','component_difference','individual_on','individual_off','individual_difference','covariance','mean_size','weighting_gap','covariance_term')
    if not C:
        return dict(**result,**dict.fromkeys(rates),world_contribution='0')
    assert total>=N>0 and all(r['size']>0 and 0<=r['on']<=r['size'] and 0<=r['off']<=r['size'] for r in records)
    ca=sum(Fraction(r['on'],r['size']) for r in records)/C;cb=sum(Fraction(r['off'],r['size']) for r in records)/C
    delta=ca-cb;ia=Fraction(A,N);ib=Fraction(B,N);mean_size=Fraction(N,C)
    covariance=sum((r['size']-mean_size)*(Fraction(r['on']-r['off'],r['size'])-delta) for r in records)/C
    gap=ia-ib-delta;term=covariance/mean_size
    assert gap==term
    return dict(**result,component_on=str(ca),component_off=str(cb),component_difference=str(delta),individual_on=str(ia),individual_off=str(ib),individual_difference=str(ia-ib),covariance=str(covariance),mean_size=str(mean_size),weighting_gap=str(gap),covariance_term=str(term),world_contribution=str(Fraction(A-B,total)))


def average(items):
    valid=[Fraction(i) for i in items if i is not None]
    return dict(mean=str(sum(valid)/len(valid)) if valid else None,available=len(valid),missing=len(items)-len(valid))


def summary_from_records(pairs):
    keys=[(p['seed'],p['mutation'],p['anchor']) for p in pairs]
    assert len(keys)==40 and set(keys)==set(product(range(96000,96005),(0,100),(100,200,300,400)))
    sizes=sorted({r['size'] for p in pairs for r in p['records']});anchors=[]
    for p in sorted(pairs,key=lambda p:(p['seed'],p['mutation'],p['anchor'])):
        total=sum(r['size'] for r in p['records']);cells={c:measure([r for r in p['records'] if c=='all' or r['category']==c],total) for c in CLASSES}
        assert sum(cells[c]['count_difference'] for c in CLASSES[:-1])==cells['all']['count_difference']
        assert sum(Fraction(cells[c]['world_contribution']) for c in CLASSES[:-1])==Fraction(cells['all']['individual_difference'])
        anchors.append(dict(seed=p['seed'],mutation=p['mutation'],anchor=p['anchor'],cells=cells,sizes={str(n):measure([r for r in p['records'] if r['size']==n],total) for n in sizes}))
    sources=[]
    for seed,mutation in product(range(96000,96005),(0,100)):
        selected=[a for a in anchors if a['seed']==seed and a['mutation']==mutation]
        result={section:{key:{metric:average([a[section][key][metric] for a in selected]) for metric in selected[0][section][key]} for key in selected[0][section]} for section in ('cells','sizes')}
        sources.append(dict(seed=seed,mutation=mutation,**result))
    groups=[]
    for mutation in (0,100):
        selected=[s for s in sources if s['mutation']==mutation]
        result={section:{key:{metric:average([s[section][key][metric]['mean'] for s in selected]) for metric in selected[0][section][key]} for key in selected[0][section]} for section in ('cells','sizes')}
        groups.append(dict(mutation=mutation,**result))
    return dict(anchors=anchors,sources=sources,groups=groups)


def main():
    from scripts.retention_weighting_inputs import bindings,TRADEOFF,POPULATION,ROOT
    target=Path('data/v4-study-012-retention-weighting');meta=read(target/'metadata.json')
    assert meta['status']=='complete' and meta['completed_pairs']==meta['planned_pairs']==40 and meta['independent_new_samples']==0
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={f:digest(target/f) for f in ('results.json','summary.json')}
    expected=[];count=0
    for p in read(TRADEOFF/'results.json'):
        base=f"seed-{p['seed']}-drive-250-mutation-{p['mutation']}-anchor-{p['anchor']}-exchange-"
        a,b=ROOT/(base+'true'),ROOT/(base+'false')
        initial=read(a/'initial.json');assert initial==read(b/'initial.json')
        records=initial_records(initial,read(a/'final.json'),read(b/'final.json'))
        assert len(records)==len(p['records'])==p['initial_components']
        for row,old in zip(records,p['records']):
            assert row['component']==old['component']
            assert row['category']==('world' if old['on']['whole_world_anchor'] else 'singleton' if old['on']['anchor_size']==1 else 'local_multi')
            for arm in ('on','off'):
                assert row['size']==old[arm]['anchor_size']
                assert row[arm]==old[arm]['endpoint']['original_survivors']==row['size']-old[arm]['original_deaths']
        expected.append(dict(seed=p['seed'],mutation=p['mutation'],anchor=p['anchor'],records=records));count+=len(records)
    assert count==6212 and read(target/'results.json')==expected
    summary=summary_from_records(expected);assert read(target/'summary.json')==summary
    study=read(ROOT/'summary.json');population=read(POPULATION/'summary.json')
    for a in summary['anchors']:
        key=lambda p:(p['seed'],p['mutation'],p['anchor'])
        old=next(p for p in study['pairs'] if key(p)==key(a))['metrics']['original_retention']
        for side in ('on','off','difference'):assert a['cells']['local_multi']['component_'+side]==old[side]
        pop=next(p for p in population['pairs'] if key(p)==key(a))['path']
        assert a['cells']['all']['initial']==pop[0]['on']['occupied']==pop[0]['off']['occupied']
        for side in ('on','off'):assert a['cells']['all'][side]==pop[100][side]['original_survivors']
        assert a['cells']['all']['count_difference']==pop[100]['differences']['original_survivors']
    for level,oldlevel,poplevel in (('sources','source_means','sources'),('groups','groups','groups')):
        for row in summary[level]:
            match=lambda s:s['mutation']==row['mutation'] and ('seed' not in row or s['seed']==row['seed'])
            old=next(s for s in study[oldlevel] if match(s))
            assert row['cells']['local_multi']['component_difference']==old['metrics']['original_retention']
            pop=next(s for s in population[poplevel] if match(s))['path'][100]
            value=pop['differences']['original_survivors'] if level=='sources' else pop['metrics']['original_survivors']['difference']
            assert row['cells']['all']['count_difference']['mean']==value
            for section in ('cells','sizes'):
                for cell in row[section].values():
                    assert cell['weighting_gap']==cell['covariance_term']
                    if cell['weighting_gap']['mean'] is not None:assert Fraction(cell['individual_difference']['mean'])-Fraction(cell['component_difference']['mean'])==Fraction(cell['weighting_gap']['mean'])
    assert meta['input_sha256']==bindings()
    assert meta['output_sha256']=={f:digest(target/f) for f in ('results.json','summary.json')}
    proof=dict(status='verified',pairs=40,components=6212,component_branch_records=12424,independent_new_samples=0,
        metadata_sha256=digest(target/'metadata.json'),results_sha256=digest(target/'results.json'),summary_sha256=digest(target/'summary.json'),verifier_sha256=digest(Path(__file__)),
        scope='initial/final original-identity intersections independent of death-ledger counts; all cells/sizes, exact covariance and hierarchy; both prior estimands restored; provenance-only helper shared')
    with (target/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        p=Path('data/v4-study-012-retention-weighting/verification-failure.json')
        if p.parent.exists() and not p.exists():
            with p.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
