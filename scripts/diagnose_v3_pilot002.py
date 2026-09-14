"""Post-hoc energy accounting on the complete pilot; no causal outcome claims."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from verify_v3_pilot002 import verify


def main():
    root=Path('data/v3-pilot-002')
    gate=verify(root)
    original=json.loads((root/'verification.json').read_text())
    if gate!=original:
        raise ValueError('complete verification changed')
    results=[]
    for checked in gate['checks']:
        directory=root/checked['directory']
        meta=json.loads((directory/'metadata.json').read_text())
        final=json.loads((directory/'final.json').read_text())
        organisms={o['id']:o for o in final['lineage']}
        totals={identifier:Counter() for identifier in organisms}
        for line in (directory/'steps.jsonl').read_text().splitlines():
            row=json.loads(line)
            for actor in row['actors']:
                t=totals[actor['id']]
                t['actor_ticks']+=1
                if actor['action'] is not None:
                    t['action_'+str(actor['action'])]+=1
                    t['blocked_moves']+=bool(actor['blocked'])
                for key in ('basal','decision','movement','intake','birth_cost','child_energy',
                            'development_cost','failure_loss'):
                    t[key]+=actor[key]
                if actor['feeding'] is not None:
                    feeding=actor['feeding']
                    t['feeding_ticks']+=1
                    for key in ('consumed_a','consumed_b','released_b','dissipated'):
                        t[key]+=feeding[key]
                    qa=meta['config']['feeding_limit']*feeding['allocation_a']//16
                    qb=meta['config']['feeding_limit']-qa
                    t['a_quota_unfilled']+=qa-feeding['consumed_a']
                    t['b_quota_unfilled']+=qb-feeding['consumed_b']
                    t['a_empty_visits']+=feeding['a_before']==0
                    t['b_empty_visits']+=feeding['b_before']==0
                    t['nonpositive_feeding_surplus']+=actor['intake']<=actor['basal']+actor['decision']+actor['movement']
                    energy=actor['energy_before']-actor['basal']-actor['decision']-actor['movement']+actor['intake']
                    t['max_prebirth_energy']=max(t['max_prebirth_energy'],energy)
        individual_rows=[]
        for identifier,o in organisms.items():
            t=totals[identifier]
            attempt=final['attempts'][identifier]
            costs=sum(t[k] for k in ('basal','decision','movement','birth_cost','child_energy',
                                     'development_cost','failure_loss'))
            if attempt['living_energy']+t['intake']-costs!=o['energy']:
                raise ValueError('lifetime energy mismatch')
            qa=meta['config']['feeding_limit']*o['genome']['allocation_a']//16
            qb=meta['config']['feeding_limit']-qa
            saturated_gain=min(qa,meta['config']['capacity'])//2+min(qb,meta['config']['capacity'])//2
            individual_rows.append(dict(saturated_feeding_gain=saturated_gain,
                id=identifier,parent=o['parent'],allocation_a=o['genome']['allocation_a'],
                initial_living_energy=attempt['living_energy'],final_energy=o['energy'],
                death_tick=o['death_tick'],offspring=o['offspring'],**dict(t)))
        summed=Counter()
        for row in individual_rows:
            for key in ('actor_ticks','feeding_ticks','basal','decision','movement','intake',
                        'a_quota_unfilled','b_quota_unfilled'):
                summed[key]+=row.get(key,0)
        results.append(dict(directory=directory.name,config=meta['config'],summary=checked['audit']['summary'],
                            lifetime_totals=dict(summed),individuals=individual_rows))
    result=dict(scope='post-hoc lifetime energy and processing-quota accounting; no intervention',
                worlds=results,verification_sha256=sha256((root/'verification.json').read_bytes()).hexdigest(),
                script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    with (root/'diagnosis.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    for row in results:
        print(row['directory'], 'individuals='+str(len(row['individuals'])),flush=True)


if __name__=='__main__':
    main()
