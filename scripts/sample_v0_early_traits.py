"""Extract preregistered early samples; no evaluation outcomes are simulated."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


def choose_sample(lineage,seed):
    index={r['id']:r for r in lineage}
    if len(index)!=len(lineage) or set(index)!=set(range(len(lineage))):raise ValueError('Invalid lineage IDs')
    eligible=[r for r in lineage if r['birth_tick']<=100 and (r['death_tick'] is None or r['death_tick']>100)]
    candidates=sorted([dict(id=r['id'],sha256=hashlib.sha256(f"bitgenesis-c023-sample-v1:{seed}:{r['id']}".encode('ascii')).hexdigest()) for r in eligible],key=lambda r:r['id'])
    base=dict(source_seed=seed,sampling_tick=100,candidates=candidates,available=bool(candidates))
    if not candidates:return dict(**base,selected=None)
    selected=min(candidates,key=lambda r:(r['sha256'],r['id']))
    organism=index[selected['id']];chain=[organism['id']];cursor=organism
    while cursor['parent_id'] is not None:
        parent=cursor['parent_id']
        if parent not in index or parent>=cursor['id'] or index[parent]['birth_tick']>=cursor['birth_tick']:raise ValueError('Broken ancestor chain')
        chain.append(parent);cursor=index[parent]
    if cursor['genome']!=250 or cursor['birth_tick']!=0 or cursor['id']!=organism['founder_id']:raise ValueError('Invalid actual founder')
    return dict(**base,selected=dict(id=organism['id'],genome=organism['genome'],birth_tick=organism['birth_tick'],founder_id=cursor['id'],founder_genome=cursor['genome'],ancestor_chain=chain,priority_sha256=selected['sha256']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-022'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    git=lambda *a:subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
    if git('status','--porcelain'):raise ValueError('Commit sampler before extraction')
    paths={k:root/f'docs/research/results/campaign-022-{name}.json' for k,name in [('metrics','verification'),('histories','histories'),('checkpoints','checkpoints')]}
    reports={k:json.loads(p.read_text(encoding='utf-8')) for k,p in paths.items()}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if reports['histories']['metric_verification_sha256']!=sha(paths['metrics']) or reports['checkpoints']['metric_report_sha256']!=sha(paths['metrics']) or reports['checkpoints']['history_report_sha256']!=sha(paths['histories']):raise ValueError('Source reports disagree')
    samples=[];hashes={}
    for seed in range(1900,1920):
        rel=f'mutation-100-seed-{seed}/lineage.json';p=args.input/rel
        if sha(p)!=reports['histories']['input_sha256'][rel]:raise ValueError('Verified source lineage changed')
        hashes[rel]=sha(p);lineage=json.loads(p.read_text(encoding='utf-8'));sample=choose_sample(lineage,seed)
        checkpoint=next(r for r in reports['checkpoints']['observations'] if (r['seed'],r['mutation_probability'],r['tick'])==(seed,100,100))
        candidate_ids={r['id'] for r in sample['candidates']}
        histogram={str(k):v for k,v in sorted(Counter(r['genome'] for r in lineage if r['id'] in candidate_ids).items())}
        if checkpoint['population']!=len(candidate_ids) or checkpoint['living_genome_histogram']!=histogram:raise ValueError('Source candidate population differs from verified checkpoint')
        samples.append(sample)
    report=dict(protocol='campaign-023-early-sampled-trait-1',git_commit=git('rev-parse','HEAD'),git_dirty=False,protocol_sha256=sha(root/'experiments/v0/campaign-023.md'),script_sha256=sha(Path(__file__)),source_report_sha256={k:sha(p) for k,p in paths.items()},input_sha256=hashes,samples=samples,available_sources=sum(r['available'] for r in samples),planned_evaluations=10*sum(r['available'] for r in samples),scope='Fixed early sampling only. Source outcomes were known at registration; independent event-based sampling verification and evaluation engineering remain required before outcome execution.')
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(available_sources=report['available_sources'],planned_evaluations=report['planned_evaluations'],selected=[dict(source_seed=r['source_seed'],selected=r['selected']) for r in samples]),indent=2))


if __name__=='__main__':main()
