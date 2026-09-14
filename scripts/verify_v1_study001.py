"""Complete study001 cohort gate; rejects partial/altered registered assays."""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

from bitgenesis.v1.audit import audit
from scripts.summarize_v1_study001 import summarize

PROTOCOL='6cf119418994ddfe640fd9fdc01acdc7f33974b6de40b79c69bbc56e723322fb'


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    def require(value,message):
        if not value:
            raise ValueError(message)
    metadata=read(root/'metadata.json')
    require(metadata['status']=='complete','incomplete evaluation')
    source_path=Path('docs/research/results/v1-study-001-sources.json')
    sources=read(source_path)
    require(metadata['sources_sha256']==sha256(source_path.read_bytes()).hexdigest(),'source binding')
    require(metadata['protocol_sha256']==PROTOCOL==sha256(Path('experiments/v1/study-001.md').read_bytes()).hexdigest(),'protocol binding')
    available={s['training_seed']:s['sample'] for s in sources if s['sample']['status']=='available'}
    expected=set(product(available,('descendant','founder','randomized'),('blind','shuffled','intact'),range(73000,73005),(15,30),(0,1)))
    rows=read(root/'results.json')
    require(len(rows)==metadata['planned_runs']==metadata['completed_runs']==len(expected),'cohort size')
    seen={}
    verification=[]
    observations=[]
    for row in rows:
        key=tuple(row[k] for k in ('source','kind','control','seed','renewal','swap'))
        require(key in expected and key not in seen,'trial identity')
        source,kind,control,seed,renewal,swap=key
        name=f'source-{source}-{kind}-{control}-seed-{seed}-renewal-{renewal}-swap-{swap}'
        require(row['directory']==name,'directory identity')
        directory=root/name
        sample=available[source]
        selected=sample['samples'][0]
        weights={'descendant':selected['genome'],'founder':selected['founder_genome'],
                 'randomized':sample['randomized_genome']}[kind]['weights']
        run_meta=read(directory/'metadata.json')
        config={'width':16,'height':16,'capacity':24,'initial_food':12,'founders':32,
                'initial_energy':24,'renewal_per_thousand':renewal,'renewal_amount':4,
                'basal_cost':1,'decision_cost':1,'movement_cost':0,'feeding_limit':8,
                'birth_threshold':80,'birth_cost':0,'mutation_per_thousand':0}
        require(run_meta['config']==config and run_meta['seed']==seed and run_meta['steps']==1000,'registered physiology')
        groups={str(i):('intact' if (i<16)!=bool(swap) else 'control') for i in range(32)}
        assignments=[{'weights':weights,'mode':'intact' if groups[str(i)]=='intact' else control} for i in range(32)]
        require(run_meta['founder_assignments']==assignments and row['founder_groups']==groups,'registered assignments')
        local=read(directory/'competition.json')
        require(local=={k:v for k,v in row.items() if k not in ('source','kind','renewal','directory')},'global/local results mismatch')
        checked=audit(directory)
        require(checked==row['verification']==read(directory/'audit.json'),'saved audit mismatch')
        lineage=read(directory/'final.json')['lineage']
        by_id={o['id']:o for o in lineage}
        totals={}
        for group in ('intact','control'):
            members=[o for o in lineage if groups[str(o['founder'])]==group]
            living=[o for o in members if o['death_tick'] is None]
            totals[group]={'population':len(living),'births':sum(o['parent'] is not None for o in members),
                           'deaths':len(members)-len(living),'energy':sum(o['energy'] for o in living)}
        require(row['groups']==totals,'group totals')
        n,m=(totals[g]['population'] for g in ('intact','control'))
        require(row['contrast']==str(Fraction(n-m,16)) and row['initial_per_group']==16,'endpoint contrast')
        require(row['intact_fraction']==(str(Fraction(n,n+m)) if n+m else None),'terminal fraction')
        status='both_present' if n and m else 'intact_only' if n else 'control_only' if m else 'both_extinct'
        require(row['status']==status,'terminal status')
        observed={g:Counter() for g in ('intact','control')}
        with (directory/'steps.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                tick=json.loads(line)
                for actor in tick['actors']:
                    group=groups[str(by_id[actor['id']]['founder'])]
                    observed[group]['directional_attempts']+=int(bool(actor['action']))
                    observed[group]['blocked_attempts']+=int(actor['blocked'])
                    observed[group]['intake']+=actor['intake']
        with (directory/'events.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                event=json.loads(line)
                group=groups[str(by_id[event['id']]['founder'])]
                if event['event']=='death':
                    observed[group]['death_'+event['phase']]+=1
                if 501<=event['tick']<=1000:
                    observed[group]['late_'+event['event']]+=1
        observations.append({'identity':list(key),'groups':{g:dict(v) for g,v in observed.items()}})
        verification.append({'identity':list(key),'audit':checked,
                             'competition_sha256':sha256((directory/'competition.json').read_bytes()).hexdigest()})
        seen[key]=row
    require(set(seen)==expected,'missing trials')
    neutral=0
    for source,kind,seed,renewal in product(available,('descendant','founder','randomized'),range(73000,73005),(15,30)):
        first=seen[(source,kind,'intact',seed,renewal,0)]
        second=seen[(source,kind,'intact',seed,renewal,1)]
        require(first['verification']['input_sha256']==second['verification']['input_sha256'],'neutral physical mismatch')
        require(first['groups']['intact']==second['groups']['control'] and first['groups']['control']==second['groups']['intact'],'neutral group mismatch')
        neutral+=1
    return {'aggregation':summarize(rows,list(available)),'neutral_pairs':neutral,
            'observations':observations,'runs':verification,
            'metadata_sha256':sha256((root/'metadata.json').read_bytes()).hexdigest(),
            'results_sha256':sha256((root/'results.json').read_bytes()).hexdigest(),
            'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/v1-study-001/evaluation'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.input)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result['aggregation'],indent=2))
