"""Independent fixed-trait initialization and aggregate metrics for campaign023."""
import argparse
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_monomorphic_metrics import initial_gate as base_initial,metric_gate as base_metrics,read_metrics,INITIAL
else:
    from verify_v0_monomorphic_metrics import initial_gate as base_initial,metric_gate as base_metrics,read_metrics,INITIAL


def initial_gate(initial,seed,trait):
    if type(trait) is not int or not 0<=trait<=1000 or initial['founder_trait']!=trait:
        raise ValueError('Invalid fixed founder trait')
    if initial['snapshot']!={**INITIAL,'mean_genome':trait}:
        raise ValueError('Initial snapshot differs')
    if any(type(o['genome']) is not int or o['genome']!=trait for o in initial['founders']):
        raise ValueError('Founders differ from assigned trait')
    normalized=deepcopy(initial)
    for o in normalized['founders']:o['genome']=250
    base_initial(normalized,seed,0)


def metric_gate(rows,trait,steps=10000):
    if type(trait) is not int or not 0<=trait<=1000:raise ValueError('Invalid fixed trait')
    for r in rows:
        if r['mean_genome']!=(trait if r['population'] else None) or r['genome_variants']!=int(r['population']>0) or r['ever_genome_values']!=1 or r['changed_births']!=0:
            raise ValueError('Fixed-trait closure differs')
    # Actual assigned trait is checked first; remaining accounts share the frozen
    # no-mutation arithmetic independently verified in the earlier campaign.
    normalized=[dict(r,mean_genome=250 if r['population'] else None) for r in rows]
    return base_metrics(normalized,0,steps)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-023'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    mp=root/'docs/research/results/campaign-023-samples.json';vp=root/'docs/research/results/campaign-023-sample-verification.json'
    manifest=json.loads(mp.read_text(encoding='utf-8'));sample_gate=json.loads(vp.read_text(encoding='utf-8'));meta=json.loads((args.input/'metadata.json').read_text(encoding='utf-8'))
    if meta['status']!='complete' or meta['git_dirty'] is not False or meta['steps']!=10000 or meta['arms']!=['sampled','ancestor'] or meta['replicates']!=list(range(5)):
        raise ValueError('Incomplete experiment or metadata')
    if meta['manifest_sha256']!=sha(mp) or meta['sample_verification_sha256']!=sha(vp) or sample_gate['manifest_sha256']!=sha(mp) or meta['protocol_sha256']!=sha(root/'experiments/v0/campaign-023.md'):
        raise ValueError('Sample/protocol provenance changed')
    if json.loads((args.input/'samples.json').read_text(encoding='utf-8'))!=manifest:raise ValueError('Archived sample manifest differs')
    samples={s['source_seed']:s for s in manifest['samples'] if s['available']}
    expected={(s,r,a) for s in samples for r in range(5) for a in ('sampled','ancestor')}
    results=json.loads((args.input/'results.json').read_text(encoding='utf-8'))
    if len(results)!=len(expected) or {(r['source_seed'],r['replicate'],r['arm']) for r in results}!=expected or meta['completed_runs']!=len(expected) or meta['planned_runs']!=len(expected) or meta['available_sources']!=len(samples) or sample_gate['planned_evaluations']!=len(expected):
        raise ValueError('Evaluation grid differs')
    verified=[];hashes={};paired={};identical=0
    for r in results:
        source,replicate,arm=r['source_seed'],r['replicate'],r['arm'];selected=samples[source]['selected']
        trait=selected['genome'] if arm=='sampled' else selected['founder_genome'];seed=2000+5*(source-1900)+replicate
        identity=dict(source_seed=source,replicate=replicate,arm=arm,founder_trait=trait,sampled_individual_id=selected['id'],source_founder_id=selected['founder_id'])
        if any(r[k]!=v for k,v in identity.items()) or r['seed']!=seed or r['mutation_probability']!=0:raise ValueError('Evaluation identity differs')
        folder=args.input/f'source-{source}-replicate-{replicate}-{arm}'
        initial=json.loads((folder/'initial.json').read_text(encoding='utf-8'))
        if any(initial[k]!=v for k,v in identity.items()):raise ValueError('Initial identity differs')
        initial_gate(initial,seed,trait);rows=read_metrics(folder/'metrics.csv');extinction=metric_gate(rows,trait)
        if any(r[k]!=v for k,v in rows[-1].items()) or r['extinction_tick']!=extinction or r['right_censored']!=(extinction is None):raise ValueError('Terminal result differs')
        if set(r['observations'])!={'0','100','500','1000','5000','10000'}:raise ValueError('Checkpoint grid differs')
        for tick,obs in r['observations'].items():
            row=rows[int(tick)]
            if any(obs[k]!=v for k,v in row.items()) or obs['living_genome_histogram']!=({str(trait):row['population']} if row['population'] else {}) or obs['ever_born_genome_histogram']!={str(trait):80+row['births']}:
                raise ValueError('Checkpoint metrics or fixed histograms differ')
        if json.loads((folder/'result.json').read_text(encoding='utf-8'))!=r:raise ValueError('Per-world result differs')
        comparable=dict(config=initial['config'],food=initial['food'],rng_state=initial['rng_state'],founders=[{k:v for k,v in o.items() if k!='genome'} for o in initial['founders']],supplied_energy=initial['supplied_energy'])
        key=(source,replicate)
        if key in paired:
            earlier,earlier_result,earlier_folder=paired[key]
            if comparable!=earlier:raise ValueError('Paired initial states differ')
            if selected['genome']==selected['founder_genome']:
                for name in ('metrics.csv','events.jsonl','lineage.json'):
                    if (folder/name).read_bytes()!=(earlier_folder/name).read_bytes():raise ValueError('Identical-trait records differ')
                if r['final_state_sha256']!=earlier_result['final_state_sha256']:raise ValueError('Identical final-state digest differs')
                identical+=1
        else:paired[key]=(comparable,r,folder)
        for name in ('initial.json','metrics.csv','result.json','events.jsonl','lineage.json'):
            p=folder/name;hashes[p.relative_to(args.input).as_posix()]=sha(p)
        verified.append({k:v for k,v in r.items() if k!='observations'})
    with (args.input/'results.csv').open(encoding='utf-8',newline='') as stream:compact=list(csv.DictReader(stream))
    if compact!=[{k:'' if v is None else str(v) for k,v in r.items()} for r in verified]:raise ValueError('Summary CSV differs')
    report=dict(scope='Fixed-trait initial conditions, complete aggregate accounts, checkpoints and identical-trait record equality. Individual histories and source-level outcome synthesis remain separate required gates.',runs=verified,metric_rows_checked=len(results)*10001,initial_states_checked=len(results),paired_initial_groups=len(paired),identical_trait_pairs_checked=identical,input_sha256=hashes,metadata_sha256=sha(args.input/'metadata.json'),manifest_sha256=sha(mp),sample_verification_sha256=sha(vp),script_sha256=sha(Path(__file__)),metric_helper_sha256=sha(Path(__file__).with_name('verify_v0_monomorphic_metrics.py')),geometry_helper_sha256=sha(Path(__file__).with_name('summarize_v0_food_geometry.py')))
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(f'Checked {len(results)} worlds and {identical} identical-trait pairs; individual history gate remains')


if __name__=='__main__':main()
