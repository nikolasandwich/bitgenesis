"""Retrospective full paired-cohort failure-state and demographic accounting."""
import json
import subprocess
import time
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path

CATEGORIES=('both','on_only','off_only','neither')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def save(path,value):
    Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')


def roots(parents):
    result=[]
    for identity,parent in enumerate(parents):
        if parent is not None and (type(parent) is not int or not 0<=parent<identity):
            raise ValueError('invalid parent chain')
        result.append(identity if parent is None else result[parent])
    return result


def cohort_state(groups,parents,members):
    ancestry=roots(parents)
    descendants={i for g in groups for i in g if ancestry[i] in members}
    targets=[g for g in groups if descendants.intersection(g)]
    if not descendants:return 'extinct'
    if len(targets)>1:return 'fragmented'
    if set(targets[0])!=descendants:return 'mixed'
    return 'closed_multi' if len(descendants)>1 else 'closed_singleton'


def event_counts(initial_ids,rows,parents):
    previous=list(initial_ids);born=[];dead=[];seen={i for i in previous if i is not None}
    for row in rows:
        expected=list(previous)
        for site in row['physical']['material']['dissolved']:
            if expected[site] is None:raise ValueError('death at empty site')
            dead.append(expected[site]);expected[site]=None
        for p in row['physical']['material']['proposals']:
            if p['reason']=='formed':
                i=row['site_ids'][p['target']]
                if i is None or i in seen or parents[i] is None or parents[i] not in previous or expected[p['target']] is not None:
                    raise ValueError('invalid new identity')
                seen.add(i);born.append(i);expected[p['target']]=i
        if expected!=row['site_ids']:raise ValueError('event and identity mismatch')
        previous=list(expected)
    return born,dead


def analyze_branch(directory):
    directory=Path(directory);meta=read(directory/'metadata.json')
    if meta['status']!='complete' or meta['horizon']!=100:raise ValueError('complete100-step branch required')
    if set(meta['output_sha256'])!={'initial.json','steps.jsonl','final.json','continuity.json','summary.json'}:
        raise ValueError('branch output inventory')
    for name,value in meta['output_sha256'].items():
        if digest(directory/name)!=value:raise ValueError('branch payload binding')
    initial=read(directory/'initial.json');final=read(directory/'final.json');parents=final['parents'];ancestry=roots(parents)
    rows=[json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()]
    if len(rows)!=100 or [r['tick'] for r in rows]!=list(range(1,101)):raise ValueError('branch observation horizon')
    born,dead=event_counts(initial['site_ids'],rows,parents)
    result=[]
    for r in read(directory/'continuity.json'):
        members=set(r['anchor_members'])
        b=[i for i in born if ancestry[i] in members];d=[i for i in dead if ancestry[i] in members]
        original_deaths=len(members.intersection(d))
        if r['endpoint']['descendants']!=len(members)+len(b)-len(d) or r['endpoint']['original_survivors']!=len(members)-original_deaths:
            raise ValueError('cohort demographic balance')
        tick=r['first_break_tick']
        state=None if tick is None else cohort_state(rows[tick-1]['observation']['components']['material'],parents,members)
        if state=='closed_multi':raise ValueError('first failure is closed')
        result.append(dict(component=r['component'],anchor_members=r['anchor_members'],anchor_size=r['anchor_size'],
            whole_world_anchor=r['whole_world_anchor'],continuous=r['continuous_closed_multi'],
            first_break_tick=tick,first_break_state=state,endpoint=r['endpoint'],births=len(b),deaths=len(d),
            original_deaths=original_deaths,descendant_deaths=len(d)-original_deaths))
    if sum(r['births'] for r in result)!=len(born) or sum(r['deaths'] for r in result)!=len(dead):
        raise ValueError('component ownership coverage')
    return result


def average(values):
    valid=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(valid)/len(valid)) if valid else None,available=len(valid),missing=len(values)-len(valid))


def main():
    source=Path('data/v4-study-012');root=Path('data/v4-study-012-tradeoff');root.mkdir(exist_ok=False)
    metadata=dict(status='running',completed_pairs=0,planned_pairs=40,independent_new_samples=0,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        script_sha256=digest(Path(__file__)),design_sha256=digest(Path('docs/design/v4-exchange-tradeoff-supplement.md')),
        storage_limit_bytes=128*1024**2,time_limit_seconds=1800)
    start=time.monotonic();pairs=[];save(root/'metadata.json',metadata)
    try:
        for name in ('metadata','results','summary','aggregation-verification'):
            if (source/f'{name}.json').read_bytes()!=Path(f'docs/research/results/v4-study-012-{name}.json').read_bytes():
                raise ValueError('study012 archive mismatch')
        metadata['study012_results_sha256']=digest(source/'results.json')
        results=read(source/'results.json');index={(r['seed'],r['drive'],r['mutation'],r['anchor'],r['exchange']):r for r in results}
        expected=set(product(range(96000,96005),(250,),(0,100),(100,200,300,400),(True,False)))
        if len(results)!=80 or set(index)!=expected:raise ValueError('full branch grid required')
        for seed,mutation,anchor in product(range(96000,96005),(0,100),(100,200,300,400)):
            if time.monotonic()-start>1800 or sum(p.stat().st_size for p in root.iterdir() if p.is_file())>128*1024**2:
                raise ValueError('supplement budget exceeded')
            sides={};bindings={}
            for flag,name in ((True,'on'),(False,'off')):
                row=index[seed,250,mutation,anchor,flag];directory=source/row['directory']
                for f in ('metadata','continuity','audit'):
                    if digest(directory/f'{f}.json')!=row[f+'_sha256']:raise ValueError('branch index binding')
                sides[name]=analyze_branch(directory)
                bindings[name]=dict(directory=row['directory'],metadata_sha256=row['metadata_sha256'],
                    continuity_sha256=row['continuity_sha256'],audit_sha256=row['audit_sha256'])
            if len(sides['on'])!=len(sides['off']):raise ValueError('initial cohort coverage')
            records=[];counts={kind:dict.fromkeys(CATEGORIES,0) for kind in ('continuous','survival')}
            n=0
            for on,off in zip(sides['on'],sides['off']):
                for key in ('component','anchor_members','anchor_size','whole_world_anchor'):
                    if on[key]!=off[key]:raise ValueError('paired baseline mismatch')
                eligible=on['anchor_size']>=2 and not on['whole_world_anchor'];n+=eligible
                categories={}
                for kind,a,b in [('continuous',on['continuous'],off['continuous']),
                                  ('survival',on['endpoint']['descendants']>0,off['endpoint']['descendants']>0)]:
                    category='both' if a and b else 'on_only' if a else 'off_only' if b else 'neither'
                    categories[kind]=category
                    if eligible:counts[kind][category]+=1
                records.append(dict(component=on['component'],eligible=eligible,categories=categories,on=on,off=off))
            pairs.append(dict(seed=seed,drive=250,mutation=mutation,anchor=anchor,initial_components=len(records),
                eligible_components=n,counts=counts,fractions={f'{k}_{c}':str(Fraction(counts[k][c],n)) if n else None
                    for k in counts for c in CATEGORIES},records=records,bindings=bindings))
            metadata['completed_pairs']=len(pairs);save(root/'results.json',pairs);save(root/'metadata.json',metadata)
        sources=[]
        metrics=list(pairs[0]['fractions'])
        for seed,mutation in product(range(96000,96005),(0,100)):
            selected=[p for p in pairs if (p['seed'],p['mutation'])==(seed,mutation)]
            sources.append(dict(seed=seed,drive=250,mutation=mutation,
                metrics={k:average([p['fractions'][k] for p in selected]) for k in metrics}))
        groups=[dict(drive=250,mutation=m,metrics={k:average([s['metrics'][k]['mean'] for s in sources if s['mutation']==m])
                    for k in metrics}) for m in (0,100)]
        save(root/'summary.json',dict(source_means=sources,groups=groups))
        if digest(Path(__file__))!=metadata['script_sha256'] or digest(source/'results.json')!=metadata['study012_results_sha256']:
            raise ValueError('analysis input changed')
        metadata.update(status='complete',results_sha256=digest(root/'results.json'),summary_sha256=digest(root/'summary.json'))
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}');raise
    finally:
        metadata['elapsed_seconds']=time.monotonic()-start;save(root/'metadata.json',metadata)


if __name__=='__main__':main()
