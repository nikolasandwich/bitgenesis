"""Complete preregistered V2 local developmental sensitivity assay."""
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from random import Random
import subprocess

from bitgenesis.v2.development import DevelopmentGenome,GENE_BOUNDS,develop
from bitgenesis.v2.direct_control import construct_direct
from bitgenesis.v2.construction_audit import reconstruct
from bitgenesis.v1.evaluation import action_distribution,total_variation
from scripts.probe_v1_study001 import probe_states


def variants(genome):
    for coordinate,(low,high) in enumerate(GENE_BOUNDS):
        for delta in (-1,1):
            genes=list(genome.genes)
            genes[coordinate]=max(low,min(high,genes[coordinate]+delta))
            yield coordinate,delta,DevelopmentGenome(tuple(genes))


def build(genome):
    result=develop(genome,640)
    record=json.loads(json.dumps(asdict(result)))
    if reconstruct({'genes':list(genome.genes)},'developmental',640)!=record:
        raise ValueError('development reconstruction mismatch')
    valid=result.valid and result.cost<640
    direct_record=None
    if valid:
        padding=35*(genome.genes[9]-1)
        direct=construct_direct(result.weights,640,padding)
        direct_record=json.loads(json.dumps(asdict(direct)))
        if reconstruct({'weights':list(result.weights)},'direct',640,padding)!=direct_record:
            raise ValueError('direct reconstruction mismatch')
        if not direct.valid or direct.weights!=result.weights or direct.cost!=result.cost:
            raise ValueError('matched direct mismatch')
    return {'genes':list(genome.genes),'valid':valid,'development':record,'direct_control':direct_record}


def compare(parent,child):
    p,c=parent['development'],child['development']
    status=('valid' if parent['valid'] else 'invalid')+'_to_'+('valid' if child['valid'] else 'invalid')
    behavior=None
    if parent['valid'] and child['valid']:
        behavior=str(sum((total_variation(action_distribution(p['weights'],s['normalized']),
                            action_distribution(c['weights'],s['normalized'])) for s in probe_states()),Fraction(0))/32)
    return {'validity_transition':status,'silent_genotype':parent['genes']==child['genes'],
            'weights_changed':p['weights']!=c['weights'],
            'active_sites_changed':p['active_sites']!=c['active_sites'],
            'cost_change':c['cost']-p['cost'],'behavior_mean_tv':behavior}


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean source required')
    root=Path('data/v2-study-001')
    root.mkdir(parents=True,exist_ok=False)
    meta={'status':'running','planned_parents':100,'completed_parents':0,
          'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'protocol_sha256':sha256(Path('experiments/v2/study-001.md').read_bytes()).hexdigest()}
    def save(name,value):
        (root/name).write_text(json.dumps(value,separators=(',',':'))+'\n',encoding='utf-8')
    save('metadata.json',meta)
    rows=[]
    try:
        for seed in range(83000,83020):
            rng=Random(seed)
            for index in range(5):
                if sum(p.stat().st_size for p in root.iterdir() if p.is_file())>=1024**3:
                    meta['status']='storage_limit'
                    return
                genome=DevelopmentGenome.random(rng)
                parent=build(genome)
                children=[]
                for coordinate,delta,child in variants(genome):
                    built=build(child)
                    children.append({'coordinate':coordinate,'delta':delta,'construction':built,**compare(parent,built)})
                rows.append({'source_seed':seed,'parent_index':index,'parent':parent,'variants':children})
                save('results.json',rows)
                meta['completed_parents']=len(rows)
                save('metadata.json',meta)
            print(f'{seed}: preserved five parents and 100 variants',flush=True)
        meta['status']='complete'
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save('metadata.json',meta)


if __name__=='__main__':
    main()
