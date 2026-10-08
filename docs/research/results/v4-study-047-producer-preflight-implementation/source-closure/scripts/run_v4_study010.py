"""Run frozen sampled-continuity observations; invoke with python -m scripts.run_v4_study010."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
import time

from bitgenesis.v4.lineage import trace as trace_lineage
from bitgenesis.v4.structure_continuity import analyze
from bitgenesis.v4.continuity_audit import event_parents, check_panels
from scripts.run_v4_study009 import sources


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def hashes(directory):
    return {p.name:digest(p) for p in directory.iterdir() if p.is_file()}


def save(path, value):
    path.write_text(json.dumps(value, separators=(',', ':'))+'\n', encoding='utf-8')


def average(values):
    present = [Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(present)/len(present)) if present else None,
                available=len(present), missing=len(values)-len(present))


METRICS = ('primary', 'continuous_closed_multi', 'complete_replacement', 'endpoint_closed_after_break',
           'endpoint_closed_multi', 'endpoint_extinct', 'whole_world_anchor')


def panel_summary(panels):
    summaries = []
    for panel in panels:
        for stratum in ('singleton','multi'):
            rows = [r for r in panel['records'] if (r['anchor_size']==1)==(stratum=='singleton')]
            counts = {k:sum((r['endpoint']['state']==k.removeprefix('endpoint_')) if
                      k in ('endpoint_closed_multi','endpoint_extinct') else r[k] for r in rows) for k in METRICS}
            summaries.append(dict(**{k:panel[k] for k in ('phase','boundary','anchor','horizon')}, stratum=stratum,
                components=len(rows), counts=counts,
                fractions={k:str(Fraction(v,len(rows))) if rows else None for k,v in counts.items()},
                anchor_members=sum(r['anchor_size'] for r in rows),
                original_survivors=sum(r['endpoint']['original_survivors'] for r in rows),
                represented_anchor_members=sum(r['endpoint']['represented_anchor_members'] for r in rows),
                descendants=sum(r['endpoint']['descendants'] for r in rows),
                all_anchor_members_represented=sum(r['endpoint']['represented_anchor_members']==r['anchor_size'] for r in rows),
                non_world_primary=sum(r['primary'] and not r['whole_world_anchor'] for r in rows)))
    return summaries


def aggregate(results):
    grid = set(product(range(96000,96005),(250,500),(0,100)))
    keys = [(r['seed'],r['drive'],r['mutation']) for r in results]
    if len(keys)!=20 or set(keys)!=grid:
        raise ValueError('all twenty unique sources required')
    definitions = (('interaction','contact'),('interaction','material'),('interaction','bond'),
                   ('final','contact'),('final','material'))
    expected = {(p,b,a,h,s) for p,b in definitions for a in (100,200,300,400)
                for h in (10,50,100) for s in ('singleton','multi')}
    source_means = []
    for row in results:
        rows = row['summary']
        keys = [(r['phase'],r['boundary'],r['anchor'],r['horizon'],r['stratum']) for r in rows]
        if len(keys)!=len(expected) or set(keys)!=expected:
            raise ValueError('complete unique anchor panels required')
        for phase,boundary in definitions:
            for horizon,stratum in product((10,50,100),('singleton','multi')):
                selected = [r for r in rows if (r['phase'],r['boundary'],r['horizon'],r['stratum'])==
                            (phase,boundary,horizon,stratum)]
                source_means.append(dict(seed=row['seed'],drive=row['drive'],mutation=row['mutation'],
                    phase=phase,boundary=boundary,horizon=horizon,stratum=stratum,
                    metrics={k:average([r['fractions'][k] for r in selected]) for k in METRICS}))
    groups = []
    for phase,boundary in definitions:
        for drive,mutation,horizon,stratum in product((250,500),(0,100),(10,50,100),('singleton','multi')):
            selected = [r for r in source_means if (r['phase'],r['boundary'],r['drive'],r['mutation'],r['horizon'],r['stratum'])==
                        (phase,boundary,drive,mutation,horizon,stratum)]
            groups.append(dict(phase=phase,boundary=boundary,drive=drive,mutation=mutation,horizon=horizon,stratum=stratum,
                metrics={k:average([r['metrics'][k]['mean'] for r in selected]) for k in METRICS}))
    return dict(source_means=source_means,groups=groups)


def preflight():
    source_rows = sources()
    previous = Path('data/v4-study-009')
    for name in ('metadata','results'):
        if (previous/f'{name}.json').read_bytes() != Path(f'docs/research/results/v4-study-009-{name}.json').read_bytes():
            raise ValueError('archived study009 cohort binding')
    old_rows = read(previous/'results.json')
    by_source = {(r['seed'],r['drive'],r['mutation']):r for r in old_rows}
    if len(by_source)!=20 or len(old_rows)!=20 or set(by_source)!={(r['seed'],r['drive'],r['mutation']) for r in source_rows}:
        raise ValueError('observation source grid')
    summary_rows = read(Path('docs/research/results/v4-study-009-summary.json'))['sources']
    summary_by_key = {(r['seed'],r['drive'],r['mutation']):r for r in summary_rows}
    # Gate every source before examining any new continuity measurement.
    for row in source_rows:
        key = row['seed'],row['drive'],row['mutation']
        old = by_source[key]
        directory = Path('data/v4-study-005')/f"seed-{key[0]}-drive-{key[1]}-mutation-{key[2]}"
        if hashes(directory)!=old['input_sha256'] or digest(previous/old['observation'])!=old['observation_sha256']:
            raise ValueError('archived source/observation hash binding')
        if digest(previous/old['audit'])!=summary_by_key[key]['audit_sha256']:
            raise ValueError('archived structural audit binding')
        checked = read(previous/old['audit'])
        if (checked['ticks'],checked['partitions'],checked['transitions'])!=(500,2502,2497):
            raise ValueError('prior structural audit coverage')
    return source_rows, previous, by_source


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    root = Path('data/v4-study-010')
    root.mkdir(exist_ok=False)
    code = [Path('src/bitgenesis/v4')/n for n in ('structure_continuity.py','continuity_audit.py','lineage.py')]+[Path(__file__)]
    metadata = dict(status='preflight',planned_sources=20,completed_sources=0,independent_new_samples=0,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=digest(Path('experiments/v4/study-010.md')),
        source_index_sha256=None,code_sha256={p.name:digest(p) for p in code},
        storage_limit_bytes=1024**3,time_limit_seconds=1800)
    save(root/'metadata.json',metadata)
    started = time.monotonic()
    results = []
    try:
        source_rows, previous, by_source = preflight()
        metadata.update(status='running', source_index_sha256=digest(previous/'results.json'))
        save(root/'metadata.json', metadata)
        for row in source_rows:
            if sum(p.stat().st_size for p in root.iterdir() if p.is_file())>=1024**3:
                metadata['status']='storage_limit'
                return
            if time.monotonic()-started>=1800:
                metadata['status']='time_limit'
                return
            key = row['seed'],row['drive'],row['mutation']
            name = f'seed-{key[0]}-drive-{key[1]}-mutation-{key[2]}'
            source = Path('data/v4-study-005')/name
            old = by_source[key]
            observation_path = previous/old['observation']
            before = hashes(source)
            observed = read(observation_path)
            if observed['input_sha256']!=before or before!=old['input_sha256']:
                raise ValueError('input changed before continuity observation')
            lineage = trace_lineage(source)
            parents = [individual['parent'] for individual in lineage['individuals']]
            independent_parents = event_parents(source,observed)
            if independent_parents!=parents:
                raise ValueError('independent ancestry mismatch')
            panels = analyze(observed,parents)
            checked = check_panels(observed,independent_parents,panels)
            if before!=hashes(source) or digest(observation_path)!=old['observation_sha256']:
                raise ValueError('input bytes changed during continuity observation')
            path = root/(name+'.json')
            save(path,dict(panels=panels,audit=checked,input_sha256=before,
                           observation_sha256=old['observation_sha256']))
            results.append(dict(seed=key[0],drive=key[1],mutation=key[2],file=path.name,
                sha256=digest(path),audit=checked,summary=panel_summary(panels)))
            metadata['completed_sources']=len(results)
            save(root/'results.json',results)
            save(root/'metadata.json',metadata)
            print(f'{len(results)}/20 independently verified: {name}; {checked["component_windows"]} component windows',flush=True)
        if any(digest(p)!=metadata['code_sha256'][p.name] for p in code):
            raise ValueError('analysis source changed during execution')
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
