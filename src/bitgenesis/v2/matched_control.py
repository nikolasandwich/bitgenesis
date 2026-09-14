"""Fixed-genome, fixed-cost developmental/direct neutral comparison."""
from dataclasses import replace
import json
from pathlib import Path

from bitgenesis.v1.controller import Genome
from .development import develop
from .runner import run,save
from .audit import audit


def physical_state(state):
    return {'tick':state['tick'],'food':state['food'],
            'organisms':[{k:v for k,v in o.items() if k!='genome'} for o in state['lineage']],
            'rng':{k:v for k,v in state['rng'].items() if k!='initial'}}


def paired_control(root, config, seed, steps, genome):
    if config.mutation_per_thousand!=0:
        raise ValueError('fixed-genome control requires mutation disabled')
    built=develop(genome,config.initial_energy)
    if not built.valid or built.cost>=config.initial_energy:
        raise ValueError('reference must yield a living founder; record failures separately')
    root=Path(root)
    root.mkdir(parents=True,exist_ok=False)
    direct_config=replace(config,direct_padding_cost=35*(genome.genes[9]-1))
    for encoding,settings,genes in (
            ('developmental',config,genome),('direct',direct_config,Genome(built.weights))):
        output=root/encoding
        run(output,settings,seed,steps,encoding=encoding,
            founder_genomes=[genes]*config.founders)
        save(output/'audit.json',audit(output))
    def read(encoding,name):
        return json.loads((root/encoding/name).read_text(encoding='utf-8'))
    for name in ('initial.json','final.json'):
        if physical_state(read('developmental',name))!=physical_state(read('direct',name)):
            raise ValueError('matched physical state diverged')
    count=0
    with (root/'developmental/steps.jsonl').open() as first, (root/'direct/steps.jsonl').open() as second:
        from itertools import zip_longest
        for a,b in zip_longest(first,second):
            if a is None or b is None:
                raise ValueError('unequal tick coverage')
            rows=[json.loads(a),json.loads(b)]
            for row in rows:
                for actor in row['actors']:
                    actor['construction_total']=actor.pop('development_cost')+actor.pop('failure_loss')
            if rows[0]!=rows[1]:
                raise ValueError('matched actor trajectory diverged')
            count+=1
    result={'scope':'fixed genotype/phenotype neutral baseline; no mutation or encoding-benefit claim',
            'ticks_compared':count,'direct_padding_cost':direct_config.direct_padding_cost,
            'development_genes':list(genome.genes),'matched_weights':list(built.weights),
            'initial_construction_cost':built.cost,
            'note':'Failure construction work and dissipated remainder may differ; total lost allocation is compared. Initial genotype-draw RNG is encoding-specific.'}
    save(root/'comparison.json',result)
    return result
