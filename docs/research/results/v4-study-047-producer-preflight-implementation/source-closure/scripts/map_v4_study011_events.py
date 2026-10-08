"""Retrospective, exhaustive local-event mapping on frozen study011 records."""
import subprocess
import time
from pathlib import Path
from bitgenesis.v4.demography_audit import event_ledger
from scripts.run_v4_study011 import preflight, read, save, digest, hashes


def transition(before, after, kind, identity, parent):
    """All post-event components touching the reference group or newborn.

    Concurrent events and, for bonds, the next drive/interaction are included.
    This set correspondence is not an isolated causal effect of this event.
    """
    focus = parent if kind == 'birth' else identity
    matches = [g for g in before if focus in g]
    if len(matches) != 1:
        raise ValueError('unique event reference component required')
    if after is None:
        return None
    old = set(matches[0])
    probe = old | ({identity} if kind == 'birth' else set())
    groups = [g for g in after if probe.intersection(g)]
    new = set().union(*map(set, groups)) if groups else set()
    return dict(before_members=sorted(old), after_components=groups,
                gained=sorted(new-old), lost=sorted(old-new))


def selected_events(panels, births, deaths):
    times = {kind: dict((i,t) for t,i in rows)
             for kind, rows in [('birth',births),('death',deaths)]}
    selected = {}
    for p in panels:
        for r in p['records']:
            if r['whole_world_anchor']:
                continue
            for kind in ('birth','death'):
                for i in r[kind+'_ids']:
                    if i not in times[kind]:
                        raise ValueError('selected event absent from raw ledger')
                    tick = times[kind][i]
                    start = p['anchor'] - (p['phase']=='interaction')
                    if not start < tick <= start+p['horizon']:
                        raise ValueError('selected event outside window')
                    key = tick,kind,i
                    ref = {k:p[k] for k in ('phase','boundary','anchor','horizon')}
                    ref['component'] = r['component']
                    refs = selected.setdefault(key,[])
                    if ref in refs:
                        raise ValueError('duplicate event reference')
                    refs.append(ref)
    return [dict(tick=t,kind=k,identity=i,references=refs)
            for (t,k,i),refs in sorted(selected.items())]


def main():
    root=Path('data/v4-study-011-event-boundaries');root.mkdir(exist_ok=False)
    started=time.monotonic()
    metadata=dict(status='running',completed_sources=0,planned_sources=20,
                  scope='retrospective selected local-event correspondence; no new simulation',
                  git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  script_sha256=digest(Path(__file__)),
                  design_sha256=digest(Path('docs/design/v4-event-boundary-supplement.md')),
                  storage_limit_bytes=128*1024**2,time_limit_seconds=1800)
    save(root/'metadata.json',metadata)
    try:
        sources,observations,by_observation,_=preflight()
        previous=Path('data/v4-study-011')
        for name in ('metadata','results','summary','aggregation-verification'):
            if (previous/f'{name}.json').read_bytes()!=Path(f'docs/research/results/v4-study-011-{name}.json').read_bytes():
                raise ValueError('study011 archive binding')
        old=read(previous/'results.json')
        index={(r['seed'],r['drive'],r['mutation']):r for r in old}
        if len(old)!=20 or set(index)!={(s['seed'],s['drive'],s['mutation']) for s in sources}:
            raise ValueError('study011 source coverage')
        metadata['study011_results_sha256']=digest(previous/'results.json')
        results=[]
        for source in sources:
            if time.monotonic()-started>1800 or sum(p.stat().st_size for p in root.iterdir())>128*1024**2:
                raise ValueError('supplement budget exceeded')
            key=source['seed'],source['drive'],source['mutation'];row=index[key]
            payload=previous/row['file'];obsrow=by_observation[key];obspath=observations/obsrow['observation']
            directory=Path('data/v4-study-005')/payload.stem
            before=hashes(directory)
            if digest(payload)!=row['sha256'] or digest(obspath)!=obsrow['observation_sha256'] or before!=obsrow['input_sha256']:
                raise ValueError('supplement input binding')
            panels=read(payload)['panels'];observed=read(obspath)
            _,parents,births,deaths=event_ledger(directory,observed)
            events=selected_events(panels,births,deaths)
            snapshots={r['tick']:r for r in observed['observations']}
            for e in events:
                tick=e['tick'];snap=snapshots[tick];next_snap=snapshots.get(tick+1)
                e['parent']=parents[e['identity']]
                e['boundaries']={b:transition(snap['interaction']['components'][b],
                    (next_snap['interaction']['components']['bond'] if next_snap else None) if b=='bond'
                    else snap['final']['components'][b], e['kind'],e['identity'],e['parent'])
                    for b in ('contact','material','bond')}
            if hashes(directory)!=before or digest(payload)!=row['sha256'] or digest(obspath)!=obsrow['observation_sha256']:
                raise ValueError('input changed')
            results.append(dict(seed=key[0],drive=key[1],mutation=key[2],events=events,
                denominators=row['summary'],demography_sha256=row['sha256'],
                observation_sha256=obsrow['observation_sha256'],input_sha256=before))
            save(root/'results.json',results)
            metadata['completed_sources']=len(results)
            print(f'{len(results)}/20 sources; {len(events)} unique local events',flush=True)
        if digest(Path(__file__))!=metadata['script_sha256']:
            raise ValueError('script changed')
        metadata.update(status='complete',results_sha256=digest(root/'results.json'),
                        unique_events=sum(len(r['events']) for r in results))
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        metadata['elapsed_seconds']=time.monotonic()-started
        save(root/'metadata.json',metadata)


if __name__=='__main__': main()
