"""Frozen study001 training and source sampling; no held-out evaluation here."""
from hashlib import sha256
from pathlib import Path
from random import Random
import subprocess

from bitgenesis.v1.controller import Genome
from bitgenesis.v1.audit import audit
from bitgenesis.v1.evaluation import sample_endpoint
from bitgenesis.v1.runner import run, save
from bitgenesis.v1.world import Config


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean source required')
    root=Path('data/v1-study-001')
    protocol=Path('experiments/v1/study-001.md')
    root.mkdir(parents=True,exist_ok=False)
    metadata={'status':'running','phase':'training','planned_runs':10,'completed_runs':0,
              'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              'protocol_sha256':sha256(protocol.read_bytes()).hexdigest()}
    save(root/'training-metadata.json',metadata)
    sources=[]
    try:
        for index in range(10):
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) >= 16*1024**3:
                metadata['status']='storage_limit'
                return
            seed=72000+index
            output=root/f'train-{seed}'
            config=Config(width=16,height=16,founders=32,birth_threshold=80)
            summary=run(output,config,seed,5000,max_actor_records=1280000)
            save(output/'audit.json',audit(output))
            sample=sample_endpoint(output,1,74000+index)
            sample['randomized_genome']={'weights':list(Genome.random(Random(75000+index)).weights)}
            sample['randomized_seed']=75000+index
            save(output/'sample.json',sample)
            sources.append({'training_seed':seed,'summary':summary,'sample':sample})
            save(root/'sources.json',sources)
            metadata['completed_runs']=len(sources)
            save(root/'training-metadata.json',metadata)
            print(f'{seed}: {sample["status"]}, population={summary["population"]}',flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'training-metadata.json',metadata)


if __name__=='__main__':
    main()
