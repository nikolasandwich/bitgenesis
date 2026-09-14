"""Reconstruct the complete registered V2 sensitivity grid and counts."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from bitgenesis.v2.construction_audit import reconstruct


def verify(root):
    root=Path(root)
    meta=json.loads((root/'metadata.json').read_text())
    if meta['status']!='complete' or meta['completed_parents']!=100:
        raise ValueError('incomplete study')
    if meta['protocol_sha256']!=sha256(Path('experiments/v2/study-001.md').read_bytes()).hexdigest():
        raise ValueError('protocol mismatch')
    rows=json.loads((root/'results.json').read_text())
    if [(r['source_seed'],r['parent_index']) for r in rows]!=[(s,i) for s in range(83000,83020) for i in range(5)]:
        raise ValueError('parent grid')
    bounds=((0,34),(-100,100),(0,34),(-100,100),(0,34),(-100,100),(0,4),(0,10),(0,100),(1,16))
    def check(record,genes):
        if record['genes']!=genes:
            raise ValueError('genotype mismatch')
        expected=reconstruct({'genes':genes},'developmental',640)
        if record['development']!=expected or record['valid']!=(expected['valid'] and expected['cost']<640):
            raise ValueError('construction mismatch')
        direct=reconstruct({'weights':expected['weights']},'direct',640,35*(genes[9]-1)) if record['valid'] else None
        if record['direct_control']!=direct:
            raise ValueError('direct control mismatch')
    clusters=[]
    for source in range(83000,83020):
        rng=Random(source)
        counts=Counter()
        for row in rows[(source-83000)*5:(source-83000+1)*5]:
            genes=[rng.randint(low,high) for low,high in bounds]
            check(row['parent'],genes)
            counts['valid_parents']+=int(row['parent']['valid'])
            if [(v['coordinate'],v['delta']) for v in row['variants']]!=[(i,d) for i in range(10) for d in (-1,1)]:
                raise ValueError('variant grid')
            for variant in row['variants']:
                i,d=variant['coordinate'],variant['delta']
                changed=genes[:]
                changed[i]=min(bounds[i][1],max(bounds[i][0],changed[i]+d))
                check(variant['construction'],changed)
                parent,child=row['parent'],variant['construction']
                status=('valid' if parent['valid'] else 'invalid')+'_to_'+('valid' if child['valid'] else 'invalid')
                if variant['validity_transition']!=status or variant['silent_genotype']!=(genes==changed):
                    raise ValueError('transition mismatch')
                counts[status]+=1
                counts['silent_genotypes']+=int(genes==changed)
        clusters.append({'source':source,**dict(counts)})
    totals=sum((Counter({k:v for k,v in c.items() if k!='source'}) for c in clusters),Counter())
    return {'scope':'complete genotype grid, independent constructions and validity transitions; behavioral probabilities pending separate validation',
            'parents':100,'variants':2000,'sources':clusters,'totals':dict(totals),
            'results_sha256':sha256((root/'results.json').read_bytes()).hexdigest(),
            'metadata_sha256':sha256((root/'metadata.json').read_bytes()).hexdigest(),
            'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    result=verify('data/v2-study-001')
    with Path('data/v2-study-001/structure-verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result['totals'],indent=2))
