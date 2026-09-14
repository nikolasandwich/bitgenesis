"""Replay the registered final twenty action ticks of every campaign-019 world."""
import argparse
from contextlib import ExitStack
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from bitgenesis.v0.engine import Config
from bitgenesis.v0.runner import provenance
from bitgenesis.v0.artifacts import write_json_atomic
from scripts.observe_v0_local_resources import LocalResourceWorld
from scripts.summarize_v0_joint_zero_charge import verify_initial


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize(initial):
    verify_initial(initial,initial['arm'],initial['birth_threshold'],initial['birth_cost'],initial['seed'])
    world=LocalResourceWorld(Config(**initial['config']))
    for organism in world.living.values():organism.genome=250
    world.food[:]=initial['food'];world.supplied_energy+=sum(world.food)
    world.events.clear();world.check_invariants()
    if ([asdict(o) for o in world.living.values()]!=initial['founders'] or
        world.snapshot()!=initial['snapshot'] or
        hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest()!=initial['rng_sha256']):
        raise ValueError('Original initialization differs')
    return world


def boundary(world):
    world.check_invariants()
    return dict(tick=world.tick,metrics=world.snapshot(),food=list(world.food),
        occupied=[[p,i] for p,i in sorted(world.occupied.items())],
        living=[asdict(o) for o in world.living.values()],rng_state=world.rng.getstate())


def check_window(world,actors,before,streams):
    local,energy,feeding,terminal=(streams[k] for k in ('local','energy','feeding','terminal'))
    local_ids={r['id'] for r in local};energy_ids={r['id'] for r in energy}
    feeds={r['id']:r for r in feeding};deaths={r['id']:r for r in terminal}
    if len(local)!=len(actors) or local_ids!=actors or len(energy)!=len(actors) or energy_ids!=actors or len(feeds)!=len(feeding) or len(deaths)!=len(terminal) or set(feeds)&set(deaths) or set(feeds)|set(deaths)!=actors:
        raise ValueError('Window actor partition differs')
    energies={r['id']:r for r in energy}
    for row in local:
        observation=feeds.get(row['id'],deaths.get(row['id']))
        if row['position']!=observation['position_before_action'] or row['founder_id']!=observation['founder_id'] or row['energy_before_action']!=energies[row['id']]['energy_before_action']:
            raise ValueError('Local identity or position differs')
    now=world.snapshot()
    if sum(r[k] for r in energy for k in ('basal_paid','movement_paid','birth_paid'))!=now['dissipated_energy']-before['dissipated_energy'] or sum(r['energy_after_action']+r['child_energy'] for r in energy)!=now['organism_energy'] or sum(r['eaten'] for r in energy)!=sum(r['eaten'] for r in feeding):
        raise ValueError('Window energy differs')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-019'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    verification_path=root/'docs/research/results/campaign-019-verification.json'
    verification=json.loads(verification_path.read_text(encoding='utf-8'));records=verification['runs']
    fields=('arm','birth_threshold','birth_cost','seed')
    grid={('block',t,c,s) for t in (40,160) for c in (0,4) for s in range(1600,1610)}
    if len(records)!=40 or {tuple(r[k] for k in fields) for r in records}!=grid:
        raise ValueError('Expected all forty registered worlds')
    hashes={}
    for record in records:
        prefix=f"block-threshold-{record['birth_threshold']}-birth-cost-{record['birth_cost']}-seed-{record['seed']}"
        for suffix in ('-initial.json','.csv'):
            path=args.input/(prefix+suffix);hashes[path.name]=digest(path)
            if hashes[path.name]!=verification['input_sha256'][path.name]:raise ValueError('Original input changed')
    metadata=dict(protocol='observation-019-local-resources-1',status='running',completed_runs=0,
        input_sha256=hashes,verification_sha256=digest(verification_path),
        protocol_sha256=digest(root/'experiments/v0/observation-019-local-resources.md'),
        window_action_ticks=20,boundary_states_per_world=21,**provenance())
    if metadata['git_dirty'] is not False:raise ValueError('Commit replay source before execution')
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):write_json_atomic(args.output/name,value)
    save('metadata.json',metadata);results=[]
    try:
        for record in records:
            prefix=f"block-threshold-{record['birth_threshold']}-birth-cost-{record['birth_cost']}-seed-{record['seed']}"
            endpoint=record['extinction_tick'] if record['extinction_tick'] is not None else 10000
            if endpoint<20:raise ValueError('Registered terminal window unavailable')
            initial_path=args.input/(prefix+'-initial.json');metric_path=args.input/(prefix+'.csv')
            if digest(initial_path)!=hashes[initial_path.name] or digest(metric_path)!=hashes[metric_path.name]:raise ValueError('Input changed after preflight')
            initial=json.loads(initial_path.read_text(encoding='utf-8'));world=initialize(initial)
            counts={k:0 for k in ('local','energy','feeding','terminal','boundaries')}
            with ExitStack() as stack:
                source=stack.enter_context(metric_path.open(encoding='utf-8',newline=''));reader=csv.DictReader(source)
                targets={k:stack.enter_context((args.output/f'{prefix}-{k}.jsonl').open('x',encoding='utf-8')) for k in counts}
                for tick in range(endpoint+1):
                    world.local_capture_enabled=tick>endpoint-20
                    actors=set(world.living) if world.local_capture_enabled else None
                    before=world.snapshot() if world.local_capture_enabled else None
                    if tick:world.step()
                    expected={k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in next(reader).items()}
                    if world.snapshot()!=expected:raise ValueError(f'Metric replay differs: {prefix} tick {tick}')
                    streams=dict(local=world.drain_local_resources(),energy=world.drain_energy(),feeding=world.drain_feeding(),terminal=world.drain_pre_feeding_deaths())
                    if world.local_capture_enabled:
                        check_window(world,actors,before,streams)
                        for kind,rows in streams.items():
                            for row in rows:targets[kind].write(json.dumps(row,separators=(',',':'))+'\n')
                            counts[kind]+=len(rows)
                    if tick>=endpoint-20:
                        targets['boundaries'].write(json.dumps(boundary(world),separators=(',',':'))+'\n');counts['boundaries']+=1
                    world.events.clear()
            if counts['boundaries']!=21:raise ValueError('Incomplete boundary window')
            results.append(dict(**{k:record[k] for k in fields},endpoint=endpoint,right_censored=record['right_censored'],
                matched_metric_rows=endpoint+1,replayed_ticks=endpoint,counts=counts,
                output_sha256={k:digest(args.output/f'{prefix}-{k}.jsonl') for k in counts}))
            save('results.json',results);metadata['completed_runs']=len(results);save('metadata.json',metadata)
            print(f'{prefix}: endpoint={endpoint}, local_records={counts["local"]}',flush=True)
        metadata['status']='complete'
    except (Exception,KeyboardInterrupt) as error:
        metadata['status']='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed'
        metadata['error']=f'{type(error).__name__}: {error}';raise
    finally:save('metadata.json',metadata)


if __name__=='__main__':main()
