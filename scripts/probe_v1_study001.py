"""Frozen study001 synthetic probes; no trajectory outcomes are read."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from bitgenesis.v1.evaluation import action_distribution, total_variation


def probe_states():
    food_patterns=[(0,0,0,0,0),(12,12,12,12,12),(24,0,0,0,0)]
    food_patterns += [tuple(24 if i==direction else 0 for i in range(5)) for direction in range(1,5)]
    food_patterns += [(6,24,12,6,0)]
    for pattern,food in enumerate(food_patterns):
        for energy in (1,24,80,160):
            yield {'pattern':pattern,'food':list(food),'post_charge_energy':energy,
                   'normalized':[1000*f//24 for f in food]+[1000*energy//160,1000]}


def probe_genome(weights):
    rows=[]
    for state in probe_states():
        probabilities={mode:action_distribution(weights,state['normalized'],mode)
                       for mode in ('intact','blind','shuffled')}
        distances={mode:total_variation(probabilities['intact'],probabilities[mode]) for mode in ('blind','shuffled')}
        for occupied in (False,True):
            rows.append({**state,'occupied_east':occupied,
                'probabilities':{k:[str(v) for v in values] for k,values in probabilities.items()},
                'total_variation':{k:str(v) for k,v in distances.items()}})
    mean={mode:str(sum((Fraction(row['total_variation'][mode]) for row in rows if not row['occupied_east']),Fraction(0))/32)
          for mode in ('blind','shuffled')}
    return {'states':rows,'mean_total_variation':mean}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    protocol=Path('experiments/v1/study-001.md')
    if sha256(protocol.read_bytes()).hexdigest()!='6cf119418994ddfe640fd9fdc01acdc7f33974b6de40b79c69bbc56e723322fb':
        raise ValueError('protocol mismatch')
    source_path=Path('docs/research/results/v1-study-001-sources.json')
    sources=json.loads(source_path.read_bytes())
    if [s['training_seed'] for s in sources]!=list(range(72000,72010)):
        raise ValueError('incomplete source manifest')
    records=[]
    for source in sources:
        sample=source['sample']
        if sample['status']=='extinct':
            records.append({'source':source['training_seed'],'status':'extinct','genomes':None})
            continue
        selected=sample['samples'][0]
        genomes={'descendant':selected['genome'],'founder':selected['founder_genome'],
                 'randomized':sample['randomized_genome']}
        records.append({'source':source['training_seed'],'status':'available',
                        'sample_id':selected['id'],'founder_id':selected['founder_id'],
                        'genomes':{k:{'weights':g['weights'],**probe_genome(g['weights'])} for k,g in genomes.items()}})
    result={'scope':'32 fixed physical states plus occupied-east duplicates; synthetic intended actions, not reproduction',
            'sources_sha256':sha256(source_path.read_bytes()).hexdigest(),
            'protocol_sha256':sha256(protocol.read_bytes()).hexdigest(),
            'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'evaluation_sha256':sha256(Path('src/bitgenesis/v1/evaluation.py').read_bytes()).hexdigest(),
            'sources':records}
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('Saved all ten sources, nine genomes, and 576 probe rows.')


if __name__=='__main__':
    main()
