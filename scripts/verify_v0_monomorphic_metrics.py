"""Independent campaign-022 initial-state and aggregate-metric verification.

This gate does not replace complete event/lineage reconstruction.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
if __package__:
    from .summarize_v0_food_geometry import BASE, INITIAL, verify_initial as verify_geometry
else:
    from summarize_v0_food_geometry import BASE, INITIAL, verify_initial as verify_geometry


def initial_gate(initial, seed, mutation):
    expected={**BASE,'seed':seed,'initial_food':0,'regrowth_probability':15,
        'mutation_probability':mutation,'movement_cost':0,'birth_cost':0}
    if mutation not in (0,100) or initial['config']!=expected or initial['supplied_energy']!=7040:
        raise ValueError('Initial configuration or energy differs')
    normalized=dict(initial,arm='block',seed=seed,snapshot=INITIAL,
        config={**expected,'mutation_probability':0,'movement_cost':1,'birth_cost':4},
        rng_sha256=hashlib.sha256(json.dumps(initial['rng_state']).encode()).hexdigest())
    return verify_geometry(normalized,'block',seed)


def read_metrics(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return [{k:(None if v=='' else float(v) if k=='mean_genome' else int(v)) for k,v in r.items()} for r in csv.DictReader(stream)]


def metric_gate(rows, mutation, steps=10000):
    if mutation not in (0,100) or len(rows)!=steps+1:
        raise ValueError('Invalid treatment or metric length')
    expected_initial=dict(INITIAL,ever_genome_values=1,changed_births=0)
    extinction=None
    for tick,r in enumerate(rows):
        if set(r)!=set(expected_initial) or r['tick']!=tick:
            raise ValueError('Metric schema or tick order differs')
        if any(type(v) is not int or v<0 for k,v in r.items() if k not in ('mean_genome','max_generation')):
            raise ValueError('Invalid integer metric')
        n=r['population']
        if n!=80+r['births']-r['deaths'] or not 0<=n<=1024:
            raise ValueError('Population accounting differs')
        if r['food_energy']>24576 or r['organism_energy']<n or r['organism_energy']+r['food_energy']+r['dissipated_energy']!=r['supplied_energy']:
            raise ValueError('Energy accounting differs')
        if not 1<=r['ever_genome_values']<=min(1001,80+r['births']) or not 0<=r['changed_births']<=r['births']:
            raise ValueError('Cumulative trait bounds differ')
        if not int(n>0)<=r['genome_variants']<=min(n,r['ever_genome_values']) or not int(n>0)<=r['founder_lineages']<=min(n,80):
            raise ValueError('Living diversity bounds differ')
        if n:
            if not isinstance(r['mean_genome'],(int,float)) or not math.isfinite(r['mean_genome']) or not 0<=r['mean_genome']<=1000 or type(r['max_generation']) is not int or not 0<=r['max_generation']<=tick:
                raise ValueError('Invalid living trait or generation')
        elif r['mean_genome'] is not None or r['max_generation'] is not None or r['organism_energy']:
            raise ValueError('Invalid empty-world state')
        if mutation==0 and (r['mean_genome']!=(250 if n else None) or r['ever_genome_values']!=1 or r['changed_births']):
            raise ValueError('No-mutation closure failed')
        if tick==0:
            if r!=expected_initial:raise ValueError('Initial metrics differ')
        else:
            p=rows[tick-1];births=r['births']-p['births'];deaths=r['deaths']-p['deaths']
            supply=r['supplied_energy']-p['supplied_energy'];diss=r['dissipated_energy']-p['dissipated_energy']
            uptake=supply+p['food_energy']-r['food_energy']
            if not 0<=births<=p['population'] or not 0<=deaths<=p['population'] or not 0<=supply<=4096 or diss!=p['population'] or not 0<=uptake<=8*p['population']:
                raise ValueError('Per-step account differs')
            if not 0<=r['changed_births']-p['changed_births']<=births or not 0<=r['ever_genome_values']-p['ever_genome_values']<=r['changed_births']-p['changed_births']:
                raise ValueError('Trait increments differ')
        if n==0 and extinction is None:extinction=tick
    return extinction


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-022'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    mp=args.input/'metadata.json';metadata=json.loads(mp.read_text(encoding='utf-8'))
    if metadata['status']!='complete' or metadata['completed_runs']!=40 or metadata['steps']!=10000 or metadata['seeds']!=list(range(1900,1920)) or metadata['mutation_probabilities']!=[0,100] or metadata['git_dirty'] is not False:
        raise ValueError('Incomplete cohort or provenance')
    if metadata['protocol_sha256']!=hashlib.sha256((root/'experiments/v0/campaign-022.md').read_bytes()).hexdigest():
        raise ValueError('Protocol changed')
    results=json.loads((args.input/'results.json').read_text(encoding='utf-8'))
    grid={(s,m) for s in range(1900,1920) for m in (0,100)}
    if len(results)!=40 or {(r['seed'],r['mutation_probability']) for r in results}!=grid:raise ValueError('Result grid differs')
    hashes={};initials={};verified=[]
    for result in results:
        seed,mutation=result['seed'],result['mutation_probability'];folder=args.input/f'mutation-{mutation}-seed-{seed}'
        initial=json.loads((folder/'initial.json').read_text(encoding='utf-8'));initial_gate(initial,seed,mutation)
        comparable={k:v for k,v in initial.items() if k!='config'}
        if seed in initials and comparable!=initials[seed]:raise ValueError('Initial paired states differ')
        initials[seed]=comparable
        rows=read_metrics(folder/'metrics.csv');extinction=metric_gate(rows,mutation)
        if result['extinction_tick']!=extinction or result['right_censored']!=(extinction is None) or any(result[k]!=v for k,v in rows[-1].items()):raise ValueError('Terminal summary differs')
        if set(result['observations'])!={'0','100','500','1000','5000','10000'}:raise ValueError('Checkpoint grid differs')
        for tick,obs in result['observations'].items():
            if any(obs[k]!=v for k,v in rows[int(tick)].items()):raise ValueError('Checkpoint metric differs')
        if json.loads((folder/'result.json').read_text(encoding='utf-8'))!=result:raise ValueError('Per-world summary differs')
        verified.append({k:v for k,v in result.items() if k!='observations'})
        for filename in ('initial.json','metrics.csv','result.json'):
            p=folder/filename;hashes[p.relative_to(args.input).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    with (args.input/'results.csv').open(encoding='utf-8',newline='') as stream:compact=list(csv.DictReader(stream))
    if compact!=[{k:'' if v is None else str(v) for k,v in r.items()} for r in verified]:raise ValueError('CSV summaries differ')
    report=dict(scope='Initial state and aggregate metrics only; event/lineage and histogram reconstruction remain separate required gates.',runs=verified,metric_rows_checked=400040,initial_states_checked=40,paired_initial_groups=20,input_sha256=hashes,metadata_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),geometry_helper_sha256=hashlib.sha256((root/'scripts/summarize_v0_food_geometry.py').read_bytes()).hexdigest())
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print('Verified 40 initial states and 400040 metric rows; event/lineage gate remains')


if __name__=='__main__':main()
