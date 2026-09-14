"""Post hoc traces of the final individuals in the seven campaign-019 extinctions."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/local-resource-replay-019'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    vp=root/'docs/research/results/local-actions-019.json'
    verification=json.loads(vp.read_text(encoding='utf-8'))
    fields=('arm','birth_threshold','birth_cost','seed')
    if len(verification['results'])!=40 or {tuple(r[k] for k in fields) for r in verification['results']}!={('block',t,c,s) for t in (40,160) for c in (0,4) for s in range(1600,1610)}:raise ValueError('Incomplete source cohort')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    traces=[];hashes={};excluded=[]
    for r in verification['results']:
        key={k:r[k] for k in fields}
        if r['right_censored']:
            excluded.append(dict(**key,reason='No observed extinction or final survivor at horizon'));continue
        prefix=f"block-threshold-{r['birth_threshold']}-birth-cost-{r['birth_cost']}-seed-{r['seed']}"
        streams={}
        for kind in ('local','energy','feeding','terminal'):
            p=args.input/f'{prefix}-{kind}.jsonl';hashes[p.name]=sha(p)
            if hashes[p.name]!=verification['input_sha256'][p.name]:raise ValueError('Verified stream changed')
            streams[kind]=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
        final=[x for x in streams['terminal'] if x['tick']==r['endpoint']]
        if len(final)!=1:raise ValueError('Expected single final survivor; report multi-individual ending explicitly')
        identity=final[0]['id'];filtered={k:[x for x in rows if x['id']==identity] for k,rows in streams.items()}
        energy=filtered['energy'];local={x['tick']:x for x in filtered['local']};feeding={x['tick']:x for x in filtered['feeding']};terminal={x['tick']:x for x in filtered['terminal']}
        ticks=[x['tick'] for x in energy]
        if ticks!=list(range(r['endpoint']-19,r['endpoint']+1)):raise ValueError('Final individual lacks full twenty-action window')
        timeline=[]
        for e in energy:
            tick=e['tick'];loc=local[tick];f=feeding.get(tick);d=terminal.get(tick)
            attempted=f['movement_attempted'] if f else d['movement_attempted']
            outcome='basal_death' if d and d['phase']=='basal' else 'movement_death' if d else 'moved' if f['moved'] else 'blocked' if attempted else 'no_attempt'
            if e['energy_before_action']+e['eaten']!=e['energy_after_action']+e['basal_paid']+e['movement_paid']+e['birth_paid']+e['child_energy']:raise ValueError('Energy trace differs')
            if timeline and timeline[-1]['energy_after']!=e['energy_before_action']:raise ValueError('Energy trace discontinuity')
            timeline.append(dict(tick=tick,energy_before=e['energy_before_action'],energy_after=e['energy_after_action'],eaten=e['eaten'],
                basal_paid=e['basal_paid'],movement_paid=e['movement_paid'],birth_paid=e['birth_paid'],child_energy=e['child_energy'],
                movement_outcome=outcome,current_food=loc['sites'][0]['food'],
                free_neighbor_food=any(s['occupant_id'] is None and s['food']>0 for s in loc['sites'][1:])))
        outcomes={k:sum(t['movement_outcome']==k for t in timeline) for k in ('no_attempt','moved','blocked','basal_death','movement_death')}
        intakes=[t['tick'] for t in timeline if t['eaten']>0]
        traces.append(dict(**key,id=identity,endpoint=r['endpoint'],window_start=ticks[0],
            initial_energy=timeline[0]['energy_before'],total_eaten=sum(t['eaten'] for t in timeline),
            total_basal=sum(t['basal_paid'] for t in timeline),total_movement=sum(t['movement_paid'] for t in timeline),
            total_birth=sum(t['birth_paid'] for t in timeline),total_child_transfer=sum(t['child_energy'] for t in timeline),
            last_positive_intake_tick_in_window=intakes[-1] if intakes else None,
            action_outcomes=outcomes,timeline=timeline))
    result=dict(selection='Post hoc: final individual in every observed campaign-019 extinction; excludes right-censored worlds, not a random sample of individuals.',
        traces=traces,excluded_worlds=excluded,input_sha256=hashes,source_verification_sha256=sha(vp),script_sha256=sha(Path(__file__)),
        scope='Only final twenty actions of outcome-selected individuals. Null last intake means no positive intake in this window, not lifetime starvation. Observed action budgets do not establish a counterfactual sensory benefit or the cause of earlier population decline.')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(traces=len(traces),excluded_worlds=len(excluded),action_rows=sum(len(t['timeline']) for t in traces))))


if __name__=='__main__':main()
