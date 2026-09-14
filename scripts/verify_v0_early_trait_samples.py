"""Verify fixed campaign-023 samples by reconstructing source events independently."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def reconstruct(events,seed):
    born={};alive=set();previous=-1;processed=0
    for event in events:
        tick=event['tick']
        if type(tick) is not int or tick<previous:raise ValueError('Invalid event order')
        previous=tick
        if tick>100:break
        identity=event['id'];processed+=1
        if event['event']=='birth':
            if type(identity) is not int or identity!=len(born) or event['birth_tick']!=tick:raise ValueError('Invalid birth identity')
            parent=event['parent_id']
            if parent is None:
                if tick!=0 or identity>=80 or event['genome']!=250:raise ValueError('Invalid founder')
            elif parent not in alive or born[parent]['tick']>=tick:raise ValueError('Invalid parent')
            born[identity]=event;alive.add(identity)
        elif event['event']=='death':
            if identity not in alive or born[identity]['tick']>=tick:raise ValueError('Invalid death')
            alive.remove(identity)
        else:raise ValueError('Unexpected source event')
    if sum(b['parent_id'] is None for b in born.values())!=80:raise ValueError('Missing founders')
    priorities=[]
    for identity in sorted(alive):
        payload='bitgenesis-c023-sample-v1:'+str(seed)+':'+str(identity)
        priorities.append(dict(id=identity,sha256=hashlib.sha256(payload.encode('utf-8')).hexdigest()))
    selected=None
    if priorities:
        ranked=sorted(priorities,key=lambda p:(int(p['sha256'],16),p['id']))
        chosen=ranked[0];b=born[chosen['id']];chain=[b['id']]
        while born[chain[-1]]['parent_id'] is not None:chain.append(born[chain[-1]]['parent_id'])
        founder=born[chain[-1]]
        selected=dict(id=b['id'],genome=b['genome'],birth_tick=b['tick'],founder_id=founder['id'],founder_genome=founder['genome'],ancestor_chain=chain,priority_sha256=chosen['sha256'])
    return dict(source_seed=seed,sampling_tick=100,candidates=priorities,available=bool(alive),selected=selected),dict(events_processed=processed,eligible=len(alive),histogram={str(k):v for k,v in sorted(Counter(born[i]['genome'] for i in alive).items())})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/campaign-022'))
    parser.add_argument('--manifest',type=Path,default=Path('docs/research/results/campaign-023-samples.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    if manifest['git_dirty'] is not False or manifest['protocol_sha256']!=sha(root/'experiments/v0/campaign-023.md'):raise ValueError('Manifest provenance differs')
    if len(manifest['samples'])!=20 or {r['source_seed'] for r in manifest['samples']}!=set(range(1900,1920)):raise ValueError('Source grid differs')
    reports={}
    for key,name in [('metrics','verification'),('histories','histories'),('checkpoints','checkpoints')]:
        p=root/f'docs/research/results/campaign-022-{name}.json'
        if sha(p)!=manifest['source_report_sha256'][key]:raise ValueError('Verified source report changed')
        reports[key]=json.loads(p.read_text(encoding='utf-8'))
    results=[];hashes={}
    for sample in manifest['samples']:
        seed=sample['source_seed'];prefix=f'mutation-100-seed-{seed}'
        for filename in ('events.jsonl','lineage.json'):
            key=prefix+'/'+filename;p=args.input/key;digest=sha(p)
            if digest!=reports['histories']['input_sha256'][key]:raise ValueError('Source input changed')
            if filename=='lineage.json' and digest!=manifest['input_sha256'][key]:raise ValueError('Manifest lineage differs')
            hashes[key]=digest
        with (args.input/prefix/'events.jsonl').open(encoding='utf-8') as stream:
            actual,counts=reconstruct((json.loads(line) for line in stream),seed)
        if actual!=sample:raise ValueError('Event-derived sample differs from fixed manifest')
        checkpoint=next(r for r in reports['checkpoints']['observations'] if (r['seed'],r['mutation_probability'],r['tick'])==(seed,100,100))
        if counts['eligible']!=checkpoint['population'] or counts['histogram']!=checkpoint['living_genome_histogram']:raise ValueError('Event-derived checkpoint differs')
        results.append(dict(source_seed=seed,**counts,selected=actual['selected']))
    available=sum(r['eligible']>0 for r in results)
    if manifest['available_sources']!=available or manifest['planned_evaluations']!=10*available:raise ValueError('Evaluation budget differs')
    report=dict(scope='Independent event-based reconstruction of all preregistered early candidates, hash rankings and actual founder chains. No evaluation outcomes.',results=results,available_sources=available,planned_evaluations=10*available,input_sha256=hashes,manifest_sha256=sha(args.manifest),script_sha256=sha(Path(__file__)))
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(available_sources=available,planned_evaluations=10*available,candidates=sum(r['eligible'] for r in results),events_processed=sum(r['events_processed'] for r in results)),indent=2))


if __name__=='__main__':main()
