"""Independent identity-set ledger for both saved histories.

The pure recount and within-history estimator are copied from the independently
implemented population-path verifier; no old provenance module is imported.
"""
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

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


def within_history(branches):
    keys=[(b['seed'],b['mutation'],b['anchor'],b['exchange']) for b in branches]
    assert len(keys)==80 and set(keys)==set(product(range(112000,112005),(0,100),(100,200,300,400),(True,False)))
    lookup=dict(zip(keys,branches));pairs=[];sources=[];groups=[]
    for seed,mutation in product(range(112000,112005),(0,100)):
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


def independent_summary(branches):
    keys=[]
    for b in branches:
        assert type(b['history']) is bool and type(b['exchange']) is bool
        keys.append((b['history'],b['seed'],b['mutation'],b['anchor'],b['exchange']))
        path=b['path'];assert len(path)==101
        for tick,node in enumerate(path):
            assert node['tick']==tick and all(type(node[k]) is int and node[k]>=0 for k in FIELDS)
            assert node['occupied']==path[0]['occupied']+node['births']-node['deaths']
            assert node['occupied']==node['original_survivors']+node['new_survivors']
    assert len(keys)==160 and set(keys)==set(product((True,False),range(112000,112005),(0,100),(100,200,300,400),(True,False)))
    histories={name:within_history([b for b in branches if b['history'] is flag]) for name,flag in (('on',True),('off',False))}
    indexes={name:{(p['seed'],p['mutation'],p['anchor']):p for p in summary['pairs']} for name,summary in histories.items()}
    pairs=[];sources=[];groups=[]
    for seed,mutation in product(range(112000,112005),(0,100)):
        selected=[]
        for anchor in (100,200,300,400):
            a=indexes['on'][seed,mutation,anchor]['path'];b=indexes['off'][seed,mutation,anchor]['path'];path=[]
            for tick in range(101):
                on=a[tick]['differences'];off=b[tick]['differences']
                path.append(dict(tick=tick,on_history=dict(on),off_history=dict(off),differences={k:off[k]-on[k] for k in FIELDS}))
            pair=dict(seed=seed,mutation=mutation,anchor=anchor,path=path);pairs.append(pair);selected.append(pair)
        path=[]
        for tick in range(101):
            values={side:{k:str(sum((Fraction(p['path'][tick][side][k],4) for p in selected),Fraction())) for k in FIELDS} for side in ('on_history','off_history','differences')}
            path.append(dict(tick=tick,**values))
        sources.append(dict(seed=seed,mutation=mutation,path=path))
    for mutation in (0,100):
        chosen=[s for s in sources if s['mutation']==mutation];selected=[p for p in pairs if p['mutation']==mutation];path=[]
        for tick in range(101):
            metrics={}
            for k in FIELDS:
                a=sum(Fraction(s['path'][tick]['on_history'][k]) for s in chosen)/5
                b=sum(Fraction(s['path'][tick]['off_history'][k]) for s in chosen)/5
                differences=[p['path'][tick]['differences'][k] for p in selected]
                metrics[k]=dict(on_history=str(a),off_history=str(b),difference=str(b-a),positive=sum(v>0 for v in differences),zero=sum(v==0 for v in differences),negative=sum(v<0 for v in differences))
            path.append(dict(tick=tick,metrics=metrics))
        groups.append(dict(mutation=mutation,source_count=5,pair_count=20,path=path))
    return dict(histories=histories,interaction=dict(pairs=pairs,sources=sources,groups=groups))


def verify_endpoints(summary,endpoint):
    for name in ('on','off'):
        actual=summary['histories'][name];expected=endpoint['histories'][name]
        pairs={(p['seed'],p['mutation'],p['anchor']):p for p in expected['pairs']}
        for p in actual['pairs']:
            metric=pairs[p['seed'],p['mutation'],p['anchor']]['metrics']['occupied']
            for side in ('on','off'):
                assert Fraction(metric[side])==p['path'][100][side]['occupied']
            assert Fraction(metric['difference'])==p['path'][100]['differences']['occupied']
        for level,fields in (('sources',('seed','mutation')),('groups',('mutation',))):
            lookup={tuple(p[k] for k in fields):p for p in expected[level]}
            for p in actual[level]:
                observed=p['path'][100]['differences']['occupied'] if level=='sources' else p['path'][100]['metrics']['occupied']['difference']
                assert Fraction(observed)==Fraction(lookup[tuple(p[k] for k in fields)]['metrics']['occupied']['mean'])
    expected=endpoint['interaction']
    for level,fields in (('pairs',('seed','mutation','anchor')),('sources',('seed','mutation')),('groups',('mutation',))):
        lookup={tuple(p[k] for k in fields):p for p in expected[level]}
        for p in summary['interaction'][level]:
            metric=lookup[tuple(p[k] for k in fields)]['metrics']['occupied']
            node=p['path'][100]
            if level=='pairs':
                assert all(Fraction(metric[k])==node[k]['occupied'] for k in ('on_history','off_history'))
                observed=node['differences']['occupied'];reference=metric['difference']
            elif level=='sources':observed=node['differences']['occupied'];reference=metric['mean']
            else:observed=node['metrics']['occupied']['difference'];reference=metric['mean']
            assert Fraction(observed)==Fraction(reference)


def main():
    from scripts.history_population_inputs import bindings,read,digest,grid
    root=Path('data/v4-study-015-population-paths')
    before={p:digest(root/p) for p in ('metadata.json','branches.json','summary.json')}
    meta=read(root/'metadata.json')
    assert meta['status']=='complete' and meta['completed_branches']==160 and meta['independent_new_samples']==meta['new_simulation_steps']==0
    assert meta['time_limit_seconds']==1200 and meta['storage_limit_bytes']==200*1024**2 and meta['elapsed_seconds']<1200
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())<200*1024**2
    assert meta['input_sha256']==meta['input_sha256_after']==bindings()
    assert meta['output_sha256']=={p:digest(root/p) for p in ('branches.json','summary.json')}
    expected=[]
    for r in grid():
        directory=Path(r['directory']);initial=read(directory/'initial.json');final=read(directory/'final.json')
        rows=[json.loads(line) for line in (directory/'steps.jsonl').open()]
        assert len(rows)==100
        expected.append(dict(r,path=recount(initial,rows,final)))
    assert read(root/'branches.json')==expected
    summary=independent_summary(expected)
    assert read(root/'summary.json')==summary
    verify_endpoints(summary,read(Path('data/v4-study-015/summary.json')))
    assert meta['input_sha256']==bindings()
    assert before=={p:digest(root/p) for p in before}
    proof=dict(status='verified',branches=160,branch_steps=16000,pairs_per_history=40,sources=5,independent_new_samples=0,
        metadata_sha256=digest(root/'metadata.json'),branches_sha256=digest(root/'branches.json'),summary_sha256=digest(root/'summary.json'),verifier_sha256=digest(Path(__file__)),input_files=len(meta['input_sha256']),
        scope='identity-set differences independently recount all saved paths, event/ancestry consistency, exact within-history means and history interaction; all study015 population endpoints reproduced')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        p=Path('data/v4-study-015-population-paths/verification-failure.json')
        if p.parent.is_dir() and not p.exists():
            with p.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}'))+'\n')
        raise
