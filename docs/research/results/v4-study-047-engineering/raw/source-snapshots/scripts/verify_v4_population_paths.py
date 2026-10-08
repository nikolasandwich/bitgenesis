"""Set-difference population accounting, separate from the event-led analyzer."""
import json
from fractions import Fraction
from itertools import product
from pathlib import Path
from scripts.population_path_inputs import bindings,read,digest,ROOT,reset_firsts

FIELDS=('occupied','births','deaths','original_survivors','new_survivors')


def recount(initial,rows,final):
    starting={i for i in initial['site_ids'] if i is not None};previous=set(starting);seen=set(starting);old_ids=list(initial['site_ids'])
    assert len(starting)==sum(i is not None for i in old_ids)
    births=deaths=0;result=[dict(tick=0,occupied=len(starting),births=0,deaths=0,original_survivors=len(starting),new_survivors=0)]
    for tick,r in enumerate(rows,1):
        assert r['tick']==tick
        ids=r['site_ids'];alive={i for i in ids if i is not None}
        assert len(alive)==sum(i is not None for i in ids)
        assert [i is not None for i in ids]==[u is not None for u in r['physical']['units']]
        added,removed=alive-previous,previous-alive
        assert not added&seen
        assert all(i<len(final['parents']) and final['parents'][i] in previous&alive for i in added)
        death_sites=r['physical']['material']['dissolved']
        assert len(death_sites)==len(set(death_sites))==len(removed) and {old_ids[s] for s in death_sites}==removed
        formed=[p for p in r['physical']['material']['proposals'] if p['reason']=='formed']
        assert len(formed)==len(added) and {ids[p['target']] for p in formed}==added
        assert all(final['parents'][ids[p['target']]]==old_ids[p['source']] for p in formed)
        for site,identity in enumerate(old_ids):
            if identity in alive:assert ids[site]==identity
        births+=len(added);deaths+=len(removed);seen|=added
        originals=len(alive&starting);new=len(alive-starting)
        assert len(alive)==len(starting)+births-deaths==originals+new
        result.append(dict(tick=tick,occupied=len(alive),births=births,deaths=deaths,original_survivors=originals,new_survivors=new))
        previous=alive;old_ids=list(ids)
    assert old_ids==final['site_ids']
    return result


def independent_summary(branches):
    keys=[(b['seed'],b['mutation'],b['anchor'],b['exchange']) for b in branches]
    assert len(keys)==80 and set(keys)==set(product(range(96000,96005),(0,100),(100,200,300,400),(True,False)))
    lookup=dict(zip(keys,branches));pairs=[];sources=[];groups=[]
    for seed,mutation in product(range(96000,96005),(0,100)):
        source_pairs=[]
        for anchor in (100,200,300,400):
            a=lookup[seed,mutation,anchor,True]['path'];b=lookup[seed,mutation,anchor,False]['path']
            assert len(a)==len(b)==101 and a[0]==b[0]
            path=[]
            for t in range(101):
                assert a[t]['tick']==b[t]['tick']==t
                values={s:{k:p[t][k] for k in FIELDS} for s,p in (('on',a),('off',b))}
                values['differences']={k:values['on'][k]-values['off'][k] for k in FIELDS}
                path.append(dict(tick=t,**values))
            pair=dict(seed=seed,mutation=mutation,anchor=anchor,path=path);pairs.append(pair);source_pairs.append(pair)
        path=[]
        for t in range(101):
            values={side:{k:str(sum((Fraction(p['path'][t][side][k],4) for p in source_pairs),Fraction())) for k in FIELDS} for side in ('on','off','differences')}
            path.append(dict(tick=t,**values))
        sources.append(dict(seed=seed,mutation=mutation,path=path))
    for m in (0,100):
        selected=[s for s in sources if s['mutation']==m];pair_rows=[p for p in pairs if p['mutation']==m];path=[]
        for t in range(101):
            metrics={}
            for k in FIELDS:
                on=sum(Fraction(s['path'][t]['on'][k]) for s in selected)/5;off=sum(Fraction(s['path'][t]['off'][k]) for s in selected)/5
                differences=[p['path'][t]['differences'][k] for p in pair_rows]
                metrics[k]=dict(on=str(on),off=str(off),difference=str(on-off),positive=sum(v>0 for v in differences),zero=sum(v==0 for v in differences),negative=sum(v<0 for v in differences))
            path.append(dict(tick=t,metrics=metrics))
        groups.append(dict(mutation=m,source_count=5,pair_count=20,path=path))
    return dict(pairs=pairs,sources=sources,groups=groups)


def main():
    root=Path('data/v4-study-012-population-paths');meta=read(root/'metadata.json')
    assert meta['status']=='complete' and meta['completed_branches']==80 and meta['independent_new_samples']==0
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={p:digest(root/p) for p in ('branches.json','summary.json')}
    firsts=reset_firsts();expected=[];histories={}
    for r in read(ROOT/'results.json'):
        p=ROOT/r['directory'];initial=read(p/'initial.json');rows=[json.loads(line) for line in (p/'steps.jsonl').open()];final=read(p/'final.json')
        assert len(rows)==100
        key=r['seed'],r['mutation']
        if key not in histories:
            fp=Path('data/v4-study-005')/f'seed-{key[0]}-drive-250-mutation-{key[1]}'/'steps.jsonl';histories[key]=[json.loads(line) for line in fp.open()]
        origin=histories[key][r['anchor']-1]
        assert initial['units']==origin['units'] and initial['raw']==origin['raw']
        path=recount(initial,rows,final);arm='on' if r['exchange'] else 'off';other=firsts[r['seed'],r['mutation'],r['anchor']]
        assert rows[0]['physical']==other[arm]
        counts=other['metrics']['counts'][arm]
        assert path[1]['occupied']==counts['occupied'] and path[1]['births']==counts['births'] and path[1]['deaths']==counts['deaths']
        expected.append(dict(seed=r['seed'],mutation=r['mutation'],anchor=r['anchor'],exchange=r['exchange'],directory=r['directory'],path=path))
    assert read(root/'branches.json')==expected
    assert read(root/'summary.json')==independent_summary(expected)
    assert meta['input_sha256']==bindings()
    assert meta['output_sha256']=={p:digest(root/p) for p in ('branches.json','summary.json')}
    proof=dict(status='verified',branches=80,branch_steps=8000,paired_paths=40,first_step_pairs_reused=40,independent_new_samples=0,
        metadata_sha256=digest(root/'metadata.json'),branches_sha256=digest(root/'branches.json'),summary_sha256=digest(root/'summary.json'),verifier_sha256=digest(Path(__file__)),
        scope='identity-set differences independently reconstruct event-led paths and all exact paired means; shared provenance helper contains no classification')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    try:main()
    except BaseException as e:
        p=Path('data/v4-study-012-population-paths/verification-failure.json')
        if p.parent.exists() and not p.exists():
            with p.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(e).__name__}: {e}'))+'\n')
        raise
