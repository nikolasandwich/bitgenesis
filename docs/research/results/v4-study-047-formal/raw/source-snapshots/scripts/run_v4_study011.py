"""Registered demographic observation; invoke with python -m scripts.run_v4_study011."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import subprocess
import time
from bitgenesis.v4.lineage import trace as lineage
from bitgenesis.v4.structure_demography import observe
from bitgenesis.v4.demography_audit import check
from scripts.run_v4_study010 import preflight as base_preflight, read, save, digest, hashes, average

CATEGORIES=('stasis','births_only','with_deaths')
METRICS=CATEGORIES+('with_original_deaths','with_descendant_deaths','eligible_rate')
DEFINITIONS=(('interaction','contact'),('interaction','material'),('interaction','bond'),('final','contact'),('final','material'))


def summarize(panels):
    rows=[]
    for p in panels:
        records=p['records'];n=len(records);denom=p['initial_multi_components']
        if n!=p['eligible_components'] or n>denom or any(r['category'] not in CATEGORIES for r in records):
            raise ValueError('demographic denominator/category mismatch')
        counts={k:sum(r['category']==k for r in records) for k in CATEGORIES}
        counts.update(with_original_deaths=sum(r['original_deaths']>0 for r in records),
                      with_descendant_deaths=sum(r['descendant_deaths']>0 for r in records))
        fractions={k:str(Fraction(v,n)) if n else None for k,v in counts.items()}
        fractions['eligible_rate']=str(Fraction(n,denom)) if denom else None
        rows.append(dict(**{k:p[k] for k in ('phase','boundary','anchor','horizon')},
            initial_multi_components=denom,eligible_components=n,counts=counts,fractions=fractions,
            event_totals={k:sum(r[k] for r in records) for k in ('births','deaths','original_deaths','descendant_deaths')},
            whole_world_cohorts=sum(r['whole_world_anchor'] for r in records),
            non_world_with_events=sum(not r['whole_world_anchor'] and r['category']!='stasis' for r in records)))
    return rows


def aggregate(results):
    grid=set(product(range(96000,96005),(250,500),(0,100)))
    if len(results)!=20 or {(r['seed'],r['drive'],r['mutation']) for r in results}!=grid:
        raise ValueError('complete twenty-source grid required')
    expected={(p,b,a,100) for p,b in DEFINITIONS for a in (100,200,300,400)}
    sources=[]
    for r in results:
        rows=r['summary']
        if len(rows)!=20 or {(p['phase'],p['boundary'],p['anchor'],p['horizon']) for p in rows}!=expected:
            raise ValueError('complete unique panels required')
        for phase,boundary in DEFINITIONS:
            selected=[p for p in rows if (p['phase'],p['boundary'])==(phase,boundary)]
            sources.append(dict(seed=r['seed'],drive=r['drive'],mutation=r['mutation'],phase=phase,boundary=boundary,
                metrics={k:average([p['fractions'][k] for p in selected]) for k in METRICS}))
    groups=[]
    for (phase,boundary),drive,mutation in product(DEFINITIONS,(250,500),(0,100)):
        selected=[r for r in sources if (r['phase'],r['boundary'],r['drive'],r['mutation'])==(phase,boundary,drive,mutation)]
        groups.append(dict(phase=phase,boundary=boundary,drive=drive,mutation=mutation,
            metrics={k:average([r['metrics'][k]['mean'] for r in selected]) for k in METRICS}))
    return dict(source_means=sources,groups=groups)


def preflight():
    source_rows,observations,by_observation=base_preflight()
    root=Path('data/v4-study-010')
    for name in ('metadata','results'):
        if (root/f'{name}.json').read_bytes()!=Path(f'docs/research/results/v4-study-010-{name}.json').read_bytes():
            raise ValueError('archived continuity index binding')
    meta=read(root/'metadata.json')
    if meta['status']!='complete' or meta['completed_sources']!=20:
        raise ValueError('incomplete continuity cohort')
    rows=read(root/'results.json')
    index={(r['seed'],r['drive'],r['mutation']):r for r in rows}
    expected={(r['seed'],r['drive'],r['mutation']) for r in source_rows}
    if len(rows)!=20 or set(index)!=expected:
        raise ValueError('continuity source coverage')
    for key,r in index.items():
        if digest(root/r['file'])!=r['sha256']:
            raise ValueError('continuity record binding')
        if r['audit']['panels']!=60:
            raise ValueError('continuity audit coverage')
    return source_rows,observations,by_observation,index


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    root=Path('data/v4-study-011');root.mkdir(exist_ok=False)
    metadata=dict(status='preflight',planned_sources=20,completed_sources=0,independent_new_samples=0)
    started=time.monotonic();results=[]
    save(root/'metadata.json',metadata)
    try:
        code=[Path('src/bitgenesis/v4')/n for n in ('structure_demography.py','demography_audit.py','lineage.py')]
        code += [Path(__file__),Path('scripts/run_v4_study010.py'),Path('scripts/run_v4_study009.py')]
        metadata.update(git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            protocol_sha256=digest(Path('experiments/v4/study-011.md')),
            code_sha256={p.name:digest(p) for p in code},storage_limit_bytes=1024**3,time_limit_seconds=1800)
        source_rows,observations,by_observation,by_continuity=preflight()
        metadata.update(status='running',source_index_sha256=digest(Path('data/v4-study-010/results.json')))
        save(root/'metadata.json',metadata)
        for row in source_rows:
            if sum(p.stat().st_size for p in root.iterdir() if p.is_file())>=1024**3:
                metadata['status']='storage_limit';return
            if time.monotonic()-started>=1800:
                metadata['status']='time_limit';return
            key=row['seed'],row['drive'],row['mutation']
            name=f'seed-{key[0]}-drive-{key[1]}-mutation-{key[2]}'
            source=Path('data/v4-study-005')/name
            old=by_continuity[key];obs=by_observation[key]
            old_path=Path('data/v4-study-010')/old['file']
            obs_path=observations/obs['observation']
            before=hashes(source)
            if before!=obs['input_sha256'] or digest(old_path)!=old['sha256'] or digest(obs_path)!=obs['observation_sha256']:
                raise ValueError('source changed before demographic measurement')
            observed=read(obs_path);continuity=read(old_path)
            if continuity['input_sha256']!=before or continuity['observation_sha256']!=obs['observation_sha256']:
                raise ValueError('continuity input binding')
            lives=lineage(source)['individuals']
            panels=observe(lives,observed,continuity['panels'])
            checked=check(source,observed,continuity['panels'],panels)
            if before!=hashes(source) or digest(old_path)!=old['sha256'] or digest(obs_path)!=obs['observation_sha256']:
                raise ValueError('demographic input bytes changed')
            path=root/(name+'.json')
            save(path,dict(panels=panels,audit=checked,input_sha256=before,
                continuity_sha256=old['sha256'],observation_sha256=obs['observation_sha256']))
            results.append(dict(seed=key[0],drive=key[1],mutation=key[2],file=path.name,
                sha256=digest(path),audit=checked,summary=summarize(panels)))
            metadata['completed_sources']=len(results)
            save(root/'results.json',results);save(root/'metadata.json',metadata)
            print(f'{len(results)}/20 event/lifecycle audits agree: {name}; {checked["cohort_windows"]} selected windows',flush=True)
        if any(digest(p)!=metadata['code_sha256'][p.name] for p in code):
            raise ValueError('analysis code changed during execution')
        save(root/'summary.json',aggregate(results));metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        metadata['elapsed_seconds']=time.monotonic()-started
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
