"""Verify full V2 pilot001 coverage and apply its fixed viability rule."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v2.audit import audit


def summarize(rows):
    expected=set(product((640,1280),(15,30),('developmental','direct'),range(82000,82005)))
    seen={}
    for row in rows:
        key=tuple(row[k] for k in ('energy','renewal','encoding','seed'))
        if key not in expected or key in seen:
            raise ValueError('unexpected or duplicate pilot trial')
        seen[key]=row
    if set(seen)!=expected:
        raise ValueError('incomplete pilot grid')
    cells=[]
    for energy,renewal,encoding in product((640,1280),(15,30),('developmental','direct')):
        group=[seen[(energy,renewal,encoding,seed)] for seed in range(82000,82005)]
        survivors=[r for r in group if r['population']>0]
        reasons={kind:dict(sum((Counter(r['failed_reasons'][kind]) for r in group),Counter())) for kind in ('founder','offspring')}
        cells.append(dict(energy=energy,renewal=renewal,encoding=encoding,
            populations=[r['population'] for r in group],surviving_worlds=len(survivors),
            usable=len(survivors)>=4 and all(r['births']>0 for r in survivors),
            attempted_founders=sum(r['founder_attempts'] for r in group),
            successful_founders=sum(r['successful_founders'] for r in group),
            successful_births=sum(r['births'] for r in group),failed_reasons=reasons))
    selected=None
    for energy,renewal in ((640,15),(1280,15),(640,30),(1280,30)):
        if next(c for c in cells if (c['energy'],c['renewal'],c['encoding'])==(energy,renewal,'developmental'))['usable']:
            selected={'energy':energy,'renewal':renewal}
            break
    return {'runs':40,'cells':cells,'selected_developmental_cell':selected,
            'scope':'viability calibration; encoding costs and phenotype distributions are not matched'}


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    meta=read(root/'metadata.json')
    if meta['status']!='complete' or meta['completed_runs']!=40:
        raise ValueError('incomplete pilot')
    if meta['protocol_sha256']!=sha256(Path('experiments/v2/pilot-001.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows=read(root/'results.json')
    result=summarize(rows)
    checks=[]
    for row in rows:
        directory=root/f"energy-{row['energy']}-renewal-{row['renewal']}-{row['encoding']}-seed-{row['seed']}"
        checked=audit(directory)
        if checked!=read(directory/'audit.json'):
            raise ValueError('audit differs from saved report')
        if any(row[k]!=v for k,v in checked['summary'].items()):
            raise ValueError('summary differs from raw run')
        metadata=read(directory/'metadata.json')
        c=metadata['config']
        expected={'width':16,'height':16,'capacity':24,'initial_food':12,'founders':32,
                  'initial_energy':row['energy'],'renewal_per_thousand':row['renewal'],
                  'renewal_amount':4,'basal_cost':1,'decision_cost':1,'movement_cost':0,
                  'feeding_limit':8,'birth_threshold':2*row['energy'],'birth_cost':0,
                  'mutation_per_thousand':100,'direct_padding_cost':0}
        if c!=expected or metadata['seed']!=row['seed'] or metadata['encoding']!=row['encoding'] or metadata['steps']!=1000:
            raise ValueError('registered configuration mismatch')
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
    parser.add_argument('--input',type=Path,default=Path('data/v2-pilot-001'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.input)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
