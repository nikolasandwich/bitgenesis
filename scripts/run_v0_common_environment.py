"""Campaign023 common-environment trait evaluation; use python -m scripts.run_v0_common_environment."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.runner import load_config,provenance
from scripts.run_v0_monomorphic_mutation import initialize as initialize_base,record_world


def initialize(base,seed,genome):
    if type(genome) is not int or not 0<=genome<=1000:raise ValueError('Invalid fixed trait')
    world=initialize_base(base,seed,0)
    for organism in world.living.values():organism.genome=genome
    for event in world.events:event['genome']=genome
    world.check_invariants()
    return world


def evaluate(world,output,steps,identity,after_record=None):
    initial_snapshot=world.snapshot()
    result=record_world(world,output,steps,after_record)
    initial=json.loads((output/'initial.json').read_text(encoding='utf-8'))
    initial.update(snapshot=initial_snapshot,**identity)
    write_json_atomic(output/'initial.json',initial)
    result.update(identity)
    final_state=dict(food=world.food,occupied=world.occupied,rng=world.rng.getstate(),snapshot=world.snapshot())
    result['final_state_sha256']=hashlib.sha256(json.dumps(final_state,sort_keys=True).encode()).hexdigest()
    write_json_atomic(output/'result.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    mp=root/'docs/research/results/campaign-023-samples.json'
    vp=root/'docs/research/results/campaign-023-sample-verification.json'
    manifest=json.loads(mp.read_text(encoding='utf-8'));verified=json.loads(vp.read_text(encoding='utf-8'))
    if verified['manifest_sha256']!=sha(mp) or manifest['protocol_sha256']!=sha(root/'experiments/v0/campaign-023.md'):raise ValueError('Sample/protocol changed')
    if len(manifest['samples'])!=20 or {s['source_seed'] for s in manifest['samples']}!=set(range(1900,1920)):raise ValueError('Incomplete source grid')
    if verified['available_sources']!=manifest['available_sources'] or verified['planned_evaluations']!=manifest['planned_evaluations']:raise ValueError('Verified source budget changed')
    base=load_config(root/'experiments/v0/darwin-baseline.toml')
    metadata=dict(protocol='campaign-023-common-environment-1',rules_version='v0-darwin-1',
        manifest_sha256=sha(mp),sample_verification_sha256=sha(vp),protocol_sha256=sha(root/'experiments/v0/campaign-023.md'),
        available_sources=manifest['available_sources'],planned_runs=manifest['planned_evaluations'],steps=10000,
        replicates=list(range(5)),arms=['sampled','ancestor'],status='running',completed_runs=0,**provenance())
    if metadata['git_dirty'] is not False:raise ValueError('Commit source before evaluation')
    args.output.mkdir(parents=True,exist_ok=False);write_json_atomic(args.output/'metadata.json',metadata)
    write_json_atomic(args.output/'samples.json',manifest);results=[]
    try:
        for sample in manifest['samples']:
            if not sample['available']:continue
            source=sample['source_seed'];selected=sample['selected']
            for replicate in range(5):
                seed=2000+5*(source-1900)+replicate;pair={}
                for arm,genome in [('sampled',selected['genome']),('ancestor',selected['founder_genome'])]:
                    folder=args.output/f'source-{source}-replicate-{replicate}-{arm}'
                    identity=dict(source_seed=source,replicate=replicate,arm=arm,founder_trait=genome,
                        sampled_individual_id=selected['id'],source_founder_id=selected['founder_id'])
                    world=initialize(base,seed,genome)
                    result=evaluate(world,folder,10000,identity)
                    results.append(result);pair[arm]=(folder,result)
                    write_json_atomic(args.output/'results.json',results)
                    metadata['completed_runs']=len(results);write_json_atomic(args.output/'metadata.json',metadata)
                    print(f"{folder.name}: trait={genome}, population={result['population']}, extinction={result['extinction_tick']}",flush=True)
                if selected['genome']==selected['founder_genome']:
                    for name in ('metrics.csv','events.jsonl','lineage.json'):
                        if (pair['sampled'][0]/name).read_bytes()!=(pair['ancestor'][0]/name).read_bytes():raise ValueError('Identical-trait dynamics differ')
                    if pair['sampled'][1]['final_state_sha256']!=pair['ancestor'][1]['final_state_sha256']:raise ValueError('Identical-trait final state differs')
        compact=[{k:v for k,v in r.items() if k!='observations'} for r in results]
        if compact:
            with (args.output/'results.csv').open('w',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(compact[0]));writer.writeheader();writer.writerows(compact)
        metadata['status']='complete'
    except (Exception,KeyboardInterrupt) as error:
        metadata['status']='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed'
        metadata['error']=f'{type(error).__name__}: {error}';raise
    finally:write_json_atomic(args.output/'metadata.json',metadata)


if __name__=='__main__':main()
