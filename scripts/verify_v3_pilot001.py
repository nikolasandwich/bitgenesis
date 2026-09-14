"""Verify full V3 pilot001 coverage and apply its fixed viability rule."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v3.audit import audit


def summarize(rows):
    expected=set(product((15,30),(1,0),range(86000,86005)))
    seen={}
    for row in rows:
        key=tuple(row[k] for k in ('renewal','recycling','seed'))
        if key not in expected or key in seen:
            raise ValueError('unexpected or duplicate trial')
        seen[key]=row
    if set(seen)!=expected:
        raise ValueError('incomplete pilot grid')
    cells=[]
    for renewal,recycling in product((15,30),(1,0)):
        group=[seen[(renewal,recycling,seed)] for seed in range(86000,86005)]
        survivors=[r for r in group if r['population']>0]
        cells.append(dict(renewal=renewal,recycling=recycling,
            populations=[r['population'] for r in group],births=[r['births'] for r in group],
            surviving_worlds=len(survivors),
            usable=len(survivors)>=4 and all(r['births']>0 for r in survivors)))
    selected=next((c['renewal'] for c in cells if c['recycling']==1 and c['usable']),None)
    return {'runs':20,'cells':cells,'selected_renewal':selected,
            'scope':'viability calibration; recycling changes retained environmental energy'}


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    meta=read(root/'metadata.json')
    if meta['status']!='complete' or meta['completed_runs']!=20 or meta['planned_runs']!=20:
        raise ValueError('incomplete pilot')
    if meta['protocol_sha256']!=sha256(Path('experiments/v3/pilot-001.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows=read(root/'results.json')
    result=summarize(rows)
    checks=[]
    paired={}
    for row in rows:
        directory=root/f"renewal-{row['renewal']}-seed-{row['seed']}-recycling-{row['recycling']}"
        checked=audit(directory)
        if checked!=read(directory/'audit.json'):
            raise ValueError('audit differs from saved report')
        if any(row[k]!=v for k,v in checked['summary'].items()):
            raise ValueError('summary differs from raw run')
        metadata=read(directory/'metadata.json')
        c=metadata['config']
        expected={'width':16,'height':16,'capacity':24,'initial_food':12,'founders':32,
                  'initial_energy':640,'renewal_per_thousand':row['renewal'],
                  'renewal_amount':4,'basal_cost':1,'decision_cost':1,'movement_cost':0,
                  'feeding_limit':8,'birth_threshold':1280,'birth_cost':0,
                  'mutation_per_thousand':100,'initial_b':0,'recycling':row['recycling']}
        if c!=expected or metadata['seed']!=row['seed'] or metadata['encoding']!='ecological' or metadata['mode']!='intact' or metadata['git_dirty'] or metadata['git_commit']!=meta['git_commit'] or 'founder_genomes' in metadata or metadata['steps']!=1000:
            raise ValueError('registered configuration mismatch')
        initial=read(directory/'initial.json')
        pair=(row['renewal'],row['seed'])
        if pair in paired:
            if paired[pair]!=initial:
                raise ValueError('paired initial states differ')
        else:
            paired[pair]=initial
        final=read(directory/'final.json')
        reasons={kind:dict(Counter(a['reason'] for a in final['attempts'] if not a['valid'] and
                    (a['parent'] is None)==(kind=='founder'))) for kind in ('founder','offspring')}
        if reasons!=row['failed_reasons']:
            raise ValueError('failure reason mismatch')
        extinction=0 if not read(directory/'initial.json')['lineage'] else None
        with (directory/'steps.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                tick=json.loads(line)
                if not tick['population'] and extinction is None:
                    extinction=tick['tick']
        if row['extinction_tick']!=extinction or row['max_generation']!=max((o['generation'] for o in final['lineage']),default=None):
            raise ValueError('extinction or generation mismatch')
        checks.append({'directory':directory.name,'audit':checked})
    return {**result,'checks':checks,'metadata_sha256':sha256((root/'metadata.json').read_bytes()).hexdigest(),
            'results_sha256':sha256((root/'results.json').read_bytes()).hexdigest(),
            'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('data/v3-pilot-001'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.input)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
