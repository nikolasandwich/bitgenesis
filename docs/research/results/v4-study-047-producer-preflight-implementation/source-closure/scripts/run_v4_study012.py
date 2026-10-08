"""Frozen 80-branch exchange intervention; python -m scripts.run_v4_study012."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.exchange_branch import run
from scripts.run_v4_study011 import preflight
from scripts.run_v4_study010 import read, save, digest, hashes, average

OUTPUT = Path('data/v4-study-012')
STORAGE_LIMIT = 2 * 1024**3
TIME_LIMIT = 1800
SEEDS = tuple(range(96000,96005))
ANCHORS = (100,200,300,400)
METRICS = ('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
COUNTS = METRICS[:4]


def summarize(records):
    eligible = [r for r in records if r['anchor_size'] >= 2 and not r['whole_world_anchor']]
    n = len(eligible)
    counts = dict(continuous=sum(r['continuous_closed_multi'] for r in eligible),
                  replacement=sum(r['primary'] for r in eligible),
                  endpoint_closed=sum(r['endpoint']['state']=='closed_multi' for r in eligible),
                  lineage_survival=sum(r['endpoint']['descendants']>0 for r in eligible))
    sums = dict(original_retention=str(sum((Fraction(r['endpoint']['original_survivors'],r['anchor_size']) for r in eligible),Fraction(0))),
                descendants=sum(r['endpoint']['descendants'] for r in eligible))
    numerators = dict(counts,**sums)
    return dict(initial_components=len(records),eligible_components=n,counts=counts,sums=sums,
                fractions={k:str(Fraction(numerators[k])/n) if n else None for k in METRICS})


def validate_summary(summary):
    n = summary['eligible_components']
    if type(n) is not int or n < 0 or type(summary['initial_components']) is not int or summary['initial_components'] < n:
        raise ValueError('invalid initial denominator')
    counts = summary['counts']; sums = summary['sums']
    if set(counts)!=set(COUNTS) or any(type(v) is not int or not 0 <= v <= n for v in counts.values()):
        raise ValueError('invalid integer counts')
    if not 0 <= Fraction(sums['original_retention']) <= n or type(sums['descendants']) is not int or sums['descendants']<0:
        raise ValueError('invalid endpoint sums')
    numerators = dict(counts,**sums)
    expected = {k:str(Fraction(numerators[k])/n) if n else None for k in METRICS}
    if summary['fractions'] != expected or (not n and any(Fraction(v) for v in numerators.values())):
        raise ValueError('fraction denominator mismatch')


def aggregate(results):
    expected = set(product(SEEDS,(250,),(0,100),ANCHORS,(True,False)))
    keys = [(r['seed'],r['drive'],r['mutation'],r['anchor'],r['exchange']) for r in results]
    if len(results)!=80 or set(keys)!=expected:
        raise ValueError('complete unique eighty-branch grid required')
    for row in results:
        if row.get('status')!='complete' or row.get('horizon')!=100 or type(row['exchange']) is not bool:
            raise ValueError('incomplete branch cannot become statistical missingness')
        validate_summary(row['summary'])
    by_key = dict(zip(keys,results)); pairs=[]
    for seed,mutation,anchor in product(SEEDS,(0,100),ANCHORS):
        on = by_key[seed,250,mutation,anchor,True]['summary']
        off = by_key[seed,250,mutation,anchor,False]['summary']
        if (on['initial_components'],on['eligible_components']) != (off['initial_components'],off['eligible_components']):
            raise ValueError('paired initial denominator mismatch')
        metrics={}
        for k in METRICS:
            a,b=on['fractions'][k],off['fractions'][k]
            metrics[k]=dict(on=a,off=b,difference=str(Fraction(a)-Fraction(b)) if a is not None else None)
        pairs.append(dict(seed=seed,drive=250,mutation=mutation,anchor=anchor,metrics=metrics))
    sources=[]
    for seed,mutation in product(SEEDS,(0,100)):
        selected=[p for p in pairs if (p['seed'],p['mutation'])==(seed,mutation)]
        sources.append(dict(seed=seed,drive=250,mutation=mutation,
            metrics={k:average([p['metrics'][k]['difference'] for p in selected]) for k in METRICS}))
    groups=[]
    for mutation in (0,100):
        selected=[p for p in sources if p['mutation']==mutation]
        groups.append(dict(drive=250,mutation=mutation,
            metrics={k:average([p['metrics'][k]['mean'] for p in selected]) for k in METRICS}))
    return dict(pairs=pairs,source_means=sources,groups=groups)


def binding_paths():
    paths = list(Path('src/bitgenesis/v4').glob('*.py'))
    paths += [Path('scripts')/f'{name}.py' for name in ('run_v4_study009','run_v4_study010','run_v4_study011','run_v4_study012','verify_v4_study012_summary')]
    paths.append(Path('experiments/v4/study-012.md'))
    for study in ('009','010'):
        paths += [Path(f'data/v4-study-{study}/{name}.json') for name in ('metadata','results')]
        paths += [Path(f'docs/research/results/v4-study-{study}-{name}.json') for name in ('metadata','results','summary')]
    return sorted(paths)


def source_bindings(rows,observations,by_observation,by_continuity):
    bound={}
    for row in rows:
        key=row['seed'],row['drive'],row['mutation']
        source=Path('data/v4-study-005')/f'seed-{key[0]}-drive-{key[1]}-mutation-{key[2]}'
        obs=by_observation[key]; old=by_continuity[key]
        if hashes(source)!=obs['input_sha256']:
            raise ValueError('historical source byte binding mismatch')
        paths=list(source.iterdir())+[observations/obs['observation'],observations/obs['audit'],Path('data/v4-study-010')/old['file']]
        for p in paths:
            if p.is_file():bound[str(p)]=digest(p)
    return bound


def check_source_bindings(expected, rows, observations, by_observation, by_continuity):
    if source_bindings(rows,observations,by_observation,by_continuity) != expected:
        raise ValueError('source file inventory or bytes changed')


def check_bindings(bound):
    if any(digest(Path(path))!=value for path,value in bound.items()):
        raise ValueError('bound source, protocol or code bytes changed')


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    root=OUTPUT;root.mkdir(exist_ok=False)
    metadata=dict(status='preflight',planned_branches=80,completed_branches=0,independent_new_samples=0,
                  storage_limit_bytes=STORAGE_LIMIT,time_limit_seconds=TIME_LIMIT)
    started=time.monotonic();results=[]
    save(root/'metadata.json',metadata)
    save(root/'results.json',results)
    try:
        metadata['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bound={str(p):digest(p) for p in binding_paths()}
        metadata['bindings_sha256']=bound
        save(root/'metadata.json',metadata)
        rows,observations,by_observation,by_continuity=preflight()
        sources=source_bindings(rows,observations,by_observation,by_continuity)
        metadata['source_bindings_sha256']=sources
        low=[r for r in rows if r['drive']==250]
        if len(low)!=10 or {(r['seed'],r['mutation']) for r in low}!=set(product(SEEDS,(0,100))):
            raise ValueError('all ten low-drive sources required')
        metadata['status']='running';save(root/'metadata.json',metadata)
        for row in sorted(low,key=lambda r:(r['seed'],r['mutation'])):
            seed,mutation=row['seed'],row['mutation']
            source=Path('data/v4-study-005')/f'seed-{seed}-drive-250-mutation-{mutation}'
            for anchor,exchange in product(ANCHORS,(True,False)):
                check_bindings(bound);check_source_bindings(sources,rows,observations,by_observation,by_continuity)
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=STORAGE_LIMIT:
                    metadata['status']='storage_limit';return
                if time.monotonic()-started>=TIME_LIMIT:
                    metadata['status']='time_limit';return
                name=f'seed-{seed}-drive-250-mutation-{mutation}-anchor-{anchor}-exchange-{str(exchange).lower()}'
                directory=root/name
                outcome=run(directory,source,anchor,horizon=100,exchange=exchange)
                branch_meta=read(directory/'metadata.json')
                if branch_meta['status']!='complete':raise ValueError('branch did not complete')
                checked=read(directory/'audit.json')
                if checked['ticks']!=100 or checked['output_sha256']!=branch_meta['output_sha256']:
                    raise ValueError('branch audit coverage mismatch')
                records=read(directory/'continuity.json')
                if records!=outcome['records']:raise ValueError('returned continuity mismatch')
                check_bindings(bound);check_source_bindings(sources,rows,observations,by_observation,by_continuity)
                results.append(dict(seed=seed,drive=250,mutation=mutation,anchor=anchor,horizon=100,exchange=exchange,
                    status='complete',directory=name,summary=summarize(records),audit=checked,
                    metadata_sha256=digest(directory/'metadata.json'),audit_sha256=digest(directory/'audit.json'),
                    continuity_sha256=digest(directory/'continuity.json')))
                metadata['completed_branches']=len(results)
                save(root/'results.json',results);save(root/'metadata.json',metadata)
                print(f'{len(results)}/80 audited branches: {name}',flush=True)
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=STORAGE_LIMIT:
                    metadata['status']='storage_limit';return
                if time.monotonic()-started>=TIME_LIMIT:
                    metadata['status']='time_limit';return
        check_bindings(bound);check_source_bindings(sources,rows,observations,by_observation,by_continuity)
        save(root/'summary.json',aggregate(results))
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        metadata['elapsed_seconds']=time.monotonic()-started
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
