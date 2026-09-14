"""Verify campaign023 fixed-trait histories and preregistered source contrasts."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
if __package__:
    from .verify_v0_common_environment_metrics import initial_gate,metric_gate,read_metrics
    from .verify_v0_monomorphic_histories import reconstruct as base_reconstruct
else:
    from verify_v0_common_environment_metrics import initial_gate,metric_gate,read_metrics
    from verify_v0_monomorphic_histories import reconstruct as base_reconstruct


def reconstruct(initial,rows,events,lineage,result):
    trait=result['founder_trait'];initial_gate(initial,result['seed'],trait);metric_gate(rows,trait,len(rows)-1)
    if any(type(e['genome']) is not int or e['genome']!=trait for e in events if e['event']=='birth') or any(type(o['genome']) is not int or o['genome']!=trait for o in lineage):
        raise ValueError('Birth or lineage trait differs from assigned genotype')
    for tick,obs in result['observations'].items():
        row=rows[int(tick)]
        if obs['living_genome_histogram']!=({str(trait):row['population']} if row['population'] else {}) or obs['ever_born_genome_histogram']!={str(trait):80+row['births']}:
            raise ValueError('Assigned-trait histogram differs')
    # Check actual genotype first, then reuse only structural history arithmetic.
    ni=deepcopy(initial);nr=[dict(r,mean_genome=250 if r['population'] else None) for r in rows]
    for o in ni['founders']:o['genome']=250
    ne=[dict(e,genome=250) if e['event']=='birth' else dict(e) for e in events]
    nl=[dict(o,genome=250) for o in lineage];result_copy=deepcopy(result)
    for obs in result_copy['observations'].values():
        obs['mean_genome']=250 if obs['population'] else None
        obs['living_genome_histogram']={'250':obs['population']} if obs['population'] else {}
        obs['ever_born_genome_histogram']={'250':80+obs['births']}
    checked=base_reconstruct(ni,nr,ne,nl,result_copy)
    return dict(checked,**{k:result[k] for k in ('source_seed','replicate','arm','founder_trait')})


def source_contrasts(runs,sources):
    expected={(s,r,a) for s in sources for r in range(5) for a in ('sampled','ancestor')}
    if len(runs)!=len(expected) or {(r['source_seed'],r['replicate'],r['arm']) for r in runs}!=expected:raise ValueError('Incomplete source evaluation grid')
    index={(r['source_seed'],r['replicate'],r['arm']):r for r in runs};pairs=[];summaries=[]
    for source in sorted(sources):
        counts={k:0 for k in ('both_alive','sampled_only','ancestor_only','both_extinct')}
        for replicate in range(5):
            sampled,ancestor=(index[source,replicate,a]['population'] for a in ('sampled','ancestor'))
            status='both_alive' if sampled and ancestor else 'sampled_only' if sampled else 'ancestor_only' if ancestor else 'both_extinct'
            counts[status]+=1;pairs.append(dict(source_seed=source,replicate=replicate,status=status,sampled_population=sampled,ancestor_population=ancestor))
        contrast=Fraction(counts['sampled_only']-counts['ancestor_only'],5)
        summaries.append(dict(source_seed=source,counts=counts,contrast=str(contrast),contrast_float=float(contrast)))
    mean=sum((Fraction(s['contrast']) for s in summaries),Fraction())/len(summaries) if summaries else None
    return dict(pairs=pairs,sources=summaries,mean_source_contrast=str(mean) if mean is not None else None,mean_source_contrast_float=float(mean) if mean is not None else None,
                positive_sources=sum(Fraction(s['contrast'])>0 for s in summaries),negative_sources=sum(Fraction(s['contrast'])<0 for s in summaries),zero_sources=sum(Fraction(s['contrast'])==0 for s in summaries))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-023'))
    parser.add_argument('--metrics-verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    gate=json.loads(args.metrics_verification.read_text(encoding='utf-8'))
    mp=root/'docs/research/results/campaign-023-samples.json';vp=root/'docs/research/results/campaign-023-sample-verification.json'
    manifest=json.loads(mp.read_text(encoding='utf-8'));sources={s['source_seed'] for s in manifest['samples'] if s['available']}
    if gate['manifest_sha256']!=sha(mp) or gate['sample_verification_sha256']!=sha(vp) or gate['metadata_sha256']!=sha(args.input/'metadata.json') or gate['metric_rows_checked']!=len(sources)*10*10001:raise ValueError('Full metric gate linkage differs')
    comparisons=source_contrasts(gate['runs'],sources);results=[];hashes={}
    for r in gate['runs']:
        folder=args.input/f"source-{r['source_seed']}-replicate-{r['replicate']}-{r['arm']}"
        for name in ('initial.json','metrics.csv','result.json','events.jsonl','lineage.json'):
            p=folder/name;key=p.relative_to(args.input).as_posix();hashes[key]=sha(p)
            if hashes[key]!=gate['input_sha256'][key]:raise ValueError('Verified evaluation input changed')
        load=lambda name:json.loads((folder/name).read_text(encoding='utf-8'))
        result=load('result.json')
        if {k:v for k,v in result.items() if k!='observations'}!=r:raise ValueError('Summary changed')
        events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        results.append(reconstruct(load('initial.json'),read_metrics(folder/'metrics.csv'),events,load('lineage.json'),result))
    report=dict(scope='Complete fixed-trait life-history reconstruction and source-level paired contrasts. Repeated evaluation seeds within each source are not independent evolved traits. No source sample replacement or selection-mediation claim.',results=results,**comparisons,available_sources=len(sources),unavailable_source_seeds=[s['source_seed'] for s in manifest['samples'] if not s['available']],input_sha256=hashes,metric_verification_sha256=sha(args.metrics_verification),script_sha256=sha(Path(__file__)),fixed_trait_metric_helper_sha256=sha(Path(__file__).with_name('verify_v0_common_environment_metrics.py')),history_helper_sha256=sha(Path(__file__).with_name('verify_v0_monomorphic_histories.py')))
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({k:report[k] for k in ('available_sources','mean_source_contrast','positive_sources','negative_sources','zero_sources')},indent=2))


if __name__=='__main__':main()
