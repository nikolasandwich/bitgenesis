"""Replay registered campaign-020 early stock observations without changing V0."""
import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.runner import load_config,provenance
from scripts.run_v0_renewal_granularity import initialize
from scripts.summarize_v0_renewal_granularity import verify_initial
from scripts.observe_v0_renewal_stocks import capture,reconcile,check_engine


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-020'))
    parser.add_argument('--verification',type=Path,default=Path('docs/research/results/campaign-020-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    verification=json.loads(args.verification.read_text(encoding='utf-8'))
    runs=verification['runs'];fields=('arm','birth_threshold','renewal','seed')
    grid={('block',t,n,s) for t in (40,160) for n in ('frequent-small','reference','rare-large') for s in range(1700,1710)}
    if len(runs)!=60 or {tuple(r[k] for k in fields) for r in runs}!=grid:raise ValueError('Incomplete original cohort')
    if digest(args.input/'metadata.json')!=verification['metadata_sha256']:raise ValueError('Original metadata changed')
    originals=[];hashes={}
    for run in runs:
        prefix=f"block-threshold-{run['birth_threshold']}-renewal-{run['renewal']}-seed-{run['seed']}"
        ip=args.input/(prefix+'-initial.json');mp=args.input/(prefix+'.csv')
        for p in (ip,mp):
            if digest(p)!=verification['input_sha256'][p.name]:raise ValueError('Original input changed')
            hashes[p.name]=digest(p)
        initial=json.loads(ip.read_text(encoding='utf-8'))
        verify_initial(initial,*(run[k] for k in fields))
        with mp.open(encoding='utf-8',newline='') as f:
            metrics=[{k:None if v=='' else float(v) if k=='mean_genome' else int(v) for k,v in row.items()} for row in csv.DictReader(f)][:101]
        if len(metrics)!=101:raise ValueError('Incomplete original early metrics')
        originals.append((run,prefix,initial,metrics))
    metadata=dict(protocol='observation-020-renewal-stocks-1',engine_sha256=check_engine(),
        protocol_sha256=digest(root/'experiments/v0/observation-020-renewal-stocks.md'),
        original_verification_sha256=digest(args.verification),original_metadata_sha256=digest(args.input/'metadata.json'),
        original_input_sha256=hashes,window=[1,100],planned_worlds=60,planned_replay_ticks=6000,
        completed_runs=0,status='running',**provenance())
    if metadata['git_dirty'] is not False:raise ValueError('Commit source before replay')
    args.output.mkdir(parents=True,exist_ok=False)
    write_json_atomic(args.output/'metadata.json',metadata);results=[]
    base=load_config(root/'experiments/v0/darwin-baseline.toml')
    try:
        for run,prefix,initial,metrics in originals:
            world=initialize(base,*(run[k] for k in fields))
            if (asdict(world.config)!=initial['config'] or list(world.food)!=initial['food'] or
                [asdict(o) for o in world.living.values()]!=initial['founders'] or world.snapshot()!=metrics[0] or
                hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest()!=initial['rng_sha256']):
                raise ValueError('Replay initialization differs')
            path=args.output/(prefix+'-stocks.jsonl')
            with path.open('x',encoding='utf-8') as f:
                for tick in range(1,101):
                    before=world.snapshot();observation=capture(world)
                    world.step();world.check_invariants();after=world.snapshot()
                    if after!=metrics[tick]:raise ValueError('Historical metric prefix differs')
                    row=reconcile(observation,before,after)
                    f.write(json.dumps(row,separators=(',',':'))+'\n')
                    world.drain_feeding();world.drain_pre_feeding_deaths();world.drain_energy();world.events.clear()
            results.append(dict(**{k:run[k] for k in fields},replay_ticks=100,metric_rows_matched=101,
                observations=100,output_file=path.name,output_sha256=digest(path)))
            write_json_atomic(args.output/'results.json',results)
            metadata['completed_runs']=len(results);write_json_atomic(args.output/'metadata.json',metadata)
            print(f'{prefix}: 101 historical metrics match',flush=True)
        metadata['status']='complete'
    except (Exception,KeyboardInterrupt) as error:
        metadata['status']='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed'
        metadata['error']=f'{type(error).__name__}: {error}'
        raise
    finally:write_json_atomic(args.output/'metadata.json',metadata)


if __name__=='__main__':main()
