"""Execute study001's complete held-out grid without dropping failed sources."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess

from bitgenesis.v1.competition import compete
from bitgenesis.v1.controller import Genome
from bitgenesis.v1.runner import save
from bitgenesis.v1.world import Config

PROTOCOL_SHA = '6cf119418994ddfe640fd9fdc01acdc7f33974b6de40b79c69bbc56e723322fb'


def grid(sources):
    if [s['training_seed'] for s in sources] != list(range(72000,72010)):
        raise ValueError('complete ten-source manifest required')
    for source in sources:
        sample = source['sample']
        if sample['status'] == 'extinct':
            if sample['samples'] or sample['sample_count'] or sample['survivors']:
                raise ValueError('extinct source has samples')
            continue
        if sample['status'] != 'available' or sample['sample_count'] != 1 or len(sample['samples']) != 1:
            raise ValueError('one sample per available source required')
        selected = sample['samples'][0]
        genomes = {'descendant':selected['genome'], 'founder':selected['founder_genome'],
                   'randomized':sample['randomized_genome']}
        for kind, control, seed, renewal, swap in product(
                genomes, ('blind','shuffled','intact'), range(73000,73005), (15,30), (0,1)):
            yield {'source':source['training_seed'], 'kind':kind, 'control':control,
                   'seed':seed, 'renewal':renewal, 'swap':swap,
                   'weights':genomes[kind]['weights']}


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean source required')
    root=Path('data/v1-study-001')
    protocol=Path('experiments/v1/study-001.md')
    if sha256(protocol.read_bytes()).hexdigest() != PROTOCOL_SHA:
        raise ValueError('registered protocol changed')
    training=json.loads((root/'training-metadata.json').read_text())
    if training['status'] != 'complete' or training['completed_runs'] != 10 or training['protocol_sha256'] != PROTOCOL_SHA:
        raise ValueError('incomplete training')
    source_bytes=(root/'sources.json').read_bytes()
    if source_bytes != Path('docs/research/results/v1-study-001-sources.json').read_bytes():
        raise ValueError('source manifest differs from archived training')
    sources=json.loads(source_bytes)
    trials=list(grid(sources))
    output=root/'evaluation'
    output.mkdir(exist_ok=False)
    metadata={'status':'running','planned_runs':len(trials),'completed_runs':0,
              'protocol_sha256':PROTOCOL_SHA,'sources_sha256':sha256(source_bytes).hexdigest(),
              'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    save(output/'metadata.json',metadata)
    results=[]
    try:
        for trial in trials:
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) >= 16*1024**3:
                metadata['status']='storage_limit'
                return
            name=f"source-{trial['source']}-{trial['kind']}-{trial['control']}-seed-{trial['seed']}-renewal-{trial['renewal']}-swap-{trial['swap']}"
            config=Config(width=16,height=16,founders=32,birth_threshold=80,
                          renewal_per_thousand=trial['renewal'],mutation_per_thousand=0)
            result=compete(output/name,config,trial['seed'],1000,Genome(tuple(trial['weights'])),
                           trial['control'],trial['swap'],max_actor_records=256000)
            result.update(source=trial['source'],kind=trial['kind'],renewal=trial['renewal'],directory=name)
            results.append(result)
            save(output/'results.json',results)
            metadata['completed_runs']=len(results)
            save(output/'metadata.json',metadata)
            print(f"{len(results)}/{len(trials)} {name}",flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(output/'metadata.json',metadata)


if __name__=='__main__':
    main()
