"""Full campaign024 cohort verification from saved records, without simulation."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_direct_competition_metrics import read_metrics,read_groups
    from .verify_v0_direct_competition_histories import reconstruct,source_contrasts
else:
    from verify_v0_direct_competition_metrics import read_metrics,read_groups
    from verify_v0_direct_competition_histories import reconstruct,source_contrasts


def paired_initial(initial):
    return dict(config=initial['config'],food=initial['food'],rng_state=initial['rng_state'],
                supplied_energy=initial['supplied_energy'],
                founders=[{k:v for k,v in o.items() if k!='genome'} for o in initial['founders']])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-024'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    load=lambda p:json.loads(p.read_text(encoding='utf-8'))
    mp=root/'docs/research/results/campaign-023-samples.json'
    vp=root/'docs/research/results/campaign-023-sample-verification.json'
    if sha(mp)!='58fe9c9c7484da17db5d095fbeb93289903ffe5b801b7d3709a297f52a19c741' or sha(vp)!='9aee4ba43d99b541da878fa26231cc78e484f2dcb51e103d45ea7705a63c0a68':
        raise ValueError('Frozen sample evidence changed')
    manifest=load(mp);meta=load(args.input/'metadata.json')
    samples={s['source_seed']:s['selected'] for s in manifest['samples'] if s['available']}
    expected=dict(status='complete',rules_version='v0-darwin-1',protocol='campaign-024-direct-competition-1',
        git_dirty=False,steps=10000,replicates=list(range(5)),swaps=[0,1],available_sources=len(samples),
        completed_runs=10*len(samples),planned_runs=10*len(samples),manifest_sha256=sha(mp),sample_verification_sha256=sha(vp),
        protocol_sha256=sha(root/'experiments/v0/campaign-024.md'))
    if any(meta[k]!=v for k,v in expected.items()) or load(args.input/'samples.json')!=manifest:
        raise ValueError('Incomplete cohort or changed provenance')
    results=load(args.input/'results.json')
    contrasts=source_contrasts(results,set(samples))
    index={(r['source_seed'],r['replicate'],r['swap']):r for r in results}
    histories=[];hashes={};neutral=0
    for source in sorted(samples):
        selected=samples[source]
        for replicate in range(5):
            pair=[]
            for swap in (0,1):
                r=index[source,replicate,swap]
                identity=dict(source_seed=source,replicate=replicate,swap=swap,
                    sampled_trait=selected['genome'],ancestor_trait=selected['founder_genome'],
                    sampled_individual_id=selected['id'],source_founder_id=selected['founder_id'])
                if any(r[k]!=v for k,v in identity.items()) or r['seed']!=2100+5*(source-1900)+replicate or r['mutation_probability']!=0:
                    raise ValueError('Evaluation identity differs')
                folder=args.input/f'source-{source}-replicate-{replicate}-swap-{swap}'
                initial=load(folder/'initial.json')
                if any(initial[k]!=v for k,v in identity.items()) or load(folder/'result.json')!=r:
                    raise ValueError('Initial or per-world identity differs')
                metrics=read_metrics(folder/'metrics.csv');groups=read_groups(folder/'groups.csv')
                if len(metrics)!=10001 or len(groups)!=10001 or r['tick']!=10000:
                    raise ValueError('Incomplete registered horizon')
                events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
                checked=reconstruct(initial,metrics,groups,events,load(folder/'lineage.json'),r)
                histories.append(dict(**checked,source_seed=source,replicate=replicate,swap=swap))
                for name in ('initial.json','metrics.csv','groups.csv','events.jsonl','lineage.json','result.json'):
                    path=folder/name;hashes[path.relative_to(args.input).as_posix()]=sha(path)
                pair.append((paired_initial(initial),folder,groups,r))
            if pair[0][0]!=pair[1][0]:raise ValueError('Paired physical initial states differ')
            if selected['genome']==selected['founder_genome']:
                for name in ('metrics.csv','events.jsonl','lineage.json'):
                    if (pair[0][1]/name).read_bytes()!=(pair[1][1]/name).read_bytes():raise ValueError('Neutral physical records differ')
                if pair[0][3]['final_state_sha256']!=pair[1][3]['final_state_sha256']:raise ValueError('Neutral final state differs')
                for left,right in zip(pair[0][2],pair[1][2],strict=True):
                    expected={'tick':left['tick']}
                    for k,v in left.items():
                        if k!='tick':
                            group,field=k.split('_',1)
                            expected[('ancestor' if group=='sampled' else 'sampled')+'_'+field]=v
                    if expected!=right:raise ValueError('Neutral groups are not complementary')
                neutral+=1
    compact=[]
    for r in results:
        row={k:v for k,v in r.items() if k not in ('observations','groups','group_extinction_ticks')}
        for g in ('sampled','ancestor'):
            row.update({g+'_'+k:v for k,v in r['groups'][g].items() if k!='living_genome_histogram'})
            row[g+'_extinction_tick']=r['group_extinction_ticks'][g]
        compact.append(row)
    if compact:
        with (args.input/'results.csv').open(encoding='utf-8',newline='') as stream:actual=list(csv.DictReader(stream))
        if actual!=[{k:'' if v is None else str(v) for k,v in r.items()} for r in compact]:raise ValueError('Compact CSV differs')
    for name in ('metadata.json','samples.json','results.json'):
        hashes[name]=sha(args.input/name)
    if compact:hashes['results.csv']=sha(args.input/'results.csv')
    report=dict(scope='Complete initial, group/world metric and event/lineage verification; exact source abundance contrasts. No full movement or individual intake histories, selection mediation or V1 claim.',
        histories=histories,**contrasts,available_sources=len(samples),
        unavailable_source_seeds=[s['source_seed'] for s in manifest['samples'] if not s['available']],
        metric_rows_checked=sum(r['metric_rows'] for r in histories),neutral_pairs_checked=neutral,
        input_sha256=hashes,manifest_sha256=sha(mp),sample_verification_sha256=sha(vp),
        script_sha256=sha(Path(__file__)),helper_sha256={name:sha(root/'scripts'/name) for name in
        ('verify_v0_direct_competition_metrics.py','verify_v0_direct_competition_histories.py','verify_v0_monomorphic_metrics.py','summarize_v0_food_geometry.py')})
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:report[k] for k in ('available_sources','metric_rows_checked','neutral_pairs_checked','mean_source_contrast')},indent=2))


if __name__=='__main__':main()
