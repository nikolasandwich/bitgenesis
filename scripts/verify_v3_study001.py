"""Complete protocol, target and reference-schedule verification for study001."""
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from bitgenesis.v3.audit import audit
from bitgenesis.v3.branch_replay import verify as replay
from bitgenesis.v3.runner import encoded,state
from bitgenesis.v3.world import Config,World


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read(root/'metadata.json')
    require((meta['status'],meta['completed_sources'],meta['planned_sources'])==('complete',5,5),'incomplete cohort')
    require(meta['protocol_sha256']==sha256(Path('experiments/v3/study-001.md').read_bytes()).hexdigest(),'protocol mismatch')
    rows=read(root/'results.json')
    require(len(rows)==5 and {r['seed'] for r in rows}==set(range(88000,88005)),'source grid mismatch')
    config=Config(width=16,height=16,founders=32,feeding_limit=16,renewal_per_thousand=60)
    checks=[]
    for row in rows:
        seed=row['seed']
        directory=root/f'seed-{seed}'
        pm=read(directory/'prefix/metadata.json')
        am=read(directory/'metadata.json')
        require(pm['config']==asdict(config) and pm['seed']==seed and pm['steps']==300
                and pm['mode']=='intact' and pm['encoding']=='ecological'
                and pm['git_commit']==meta['git_commit'] and pm['git_dirty'] is False
                and 'founder_genomes' not in pm,'prefix protocol/source mismatch')
        require(am['status']=='complete' and am['prefix_steps']==300 and am['branch_steps']==500
                and am['seed']==seed and am['schema']=='v3-assay-1','assay metadata mismatch')
        prefix=audit(directory/'prefix')
        require(prefix==read(directory/'prefix-audit.json'),'prefix audit mismatch')
        final=read(directory/'prefix/final.json')
        require(am['prefix_final_sha256']==sha256((directory/'prefix/final.json').read_bytes()).hexdigest(),'prefix binding')
        founders={o['id']:o['founder'] for o in final['lineage']}
        living={o['founder'] for o in final['lineage'] if o['death_tick'] is None}
        releases=Counter()
        with (directory/'prefix/steps.jsonl').open() as stream:
            for line in stream:
                for actor in json.loads(line)['actors']:
                    if actor['feeding'] is not None:
                        releases[founders[actor['id']]]+=actor['feeding']['released_b']
        candidates=sorted((f for f in living if releases[f]>0),key=lambda f:(-releases[f],f)) if len(living)>=2 else []
        target=candidates[0] if candidates else None
        selection=dict(target=target,living_founders=sorted(living),status='available' if candidates else 'unavailable',
                       retained_release={str(f):releases[f] for f in sorted(set(founders.values()))})
        require(selection==row['selection']==read(directory/'selection.json'),'prefix target selection mismatch')
        if target is None:
            require(row['outcomes'] is None and am['outcome']=='unavailable','unavailable outcome mismatch')
            require(all(not (directory/name).exists() for name in ('intact','removed','replayed')),'unexpected unavailable branches')
            require(read(directory/'result.json')==dict(selection=selection,outcomes=None),'unavailable result mismatch')
            checks.append(dict(seed=seed,status='unavailable',contrasts=None))
            continue
        origin=World(config,seed)
        for _ in range(300):
            origin.step()
            origin.events.clear()
        require(encoded(state(origin))==encoded(final),'origin mismatch')
        reference_final=read(directory/'intact/final.json')
        donor_ids={o['id'] for o in reference_final['lineage'] if o['founder']==target}
        schedule={}
        with (directory/'intact/steps.jsonl').open() as stream:
            for line in stream:
                step=json.loads(line)['step']
                additions=[[a['feeding']['site'],a['feeding']['released_b']] for a in step['actors']
                           if a['id'] in donor_ids and a['feeding'] is not None and a['feeding']['released_b']>0]
                if step['tick']<800 and additions:
                    schedule[str(step['tick'])]=additions
        require(read(directory/'schedule.json')==dict(target=target,boundary_deposits=schedule,
            reference_steps_sha256=sha256((directory/'intact/steps.jsonl').read_bytes()).hexdigest()),'reference schedule mismatch')
        outcomes={}
        reports={}
        for name in ('intact','removed','replayed'):
            bm=read(directory/name/'metadata.json')
            require(bm['steps']==500 and bm['start_tick']==300 and bm['max_actor_records']==128000
                    and bm['remove_founder']==(None if name=='intact' else target)
                    and bm['deposits']==(schedule if name=='replayed' else {}),'branch intervention protocol mismatch')
            reports[name]=replay(directory/name,origin)
            require(reports[name]==read(directory/(name+'-verification.json')),'branch verification mismatch')
            endpoint=read(directory/name/'final.json')
            other=[o for o in endpoint['lineage'] if o['founder']!=target]
            outcomes[name]=dict(other_population=sum(o['death_tick'] is None for o in other),
                other_new_births=sum(o['birth_tick']>300 for o in other),summary=reports[name]['summary'])
        require(outcomes==row['outcomes'] and read(directory/'result.json')==dict(selection=selection,outcomes=outcomes),'source result mismatch')
        contrasts={metric:{'removed_minus_intact':outcomes['removed'][metric]-outcomes['intact'][metric],
                          'replayed_minus_removed':outcomes['replayed'][metric]-outcomes['removed'][metric]}
                   for metric in ('other_population','other_new_births')}
        checks.append(dict(seed=seed,status='available',target=target,contrasts=contrasts,
                           outcomes=outcomes,branch_checks=reports))
        print(f'verified {seed}',flush=True)
    return dict(scope='complete registered cohort; independent prefix/target/schedule/boundaries, same-engine branch replay',
                sources=checks,protocol_sha256=meta['protocol_sha256'],
                results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
                verifier_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    root=Path('data/v3-study-001')
    result=verify(root)
    with (root/'verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
