"""Execute the five registered common-prefix mechanism sources."""
from hashlib import sha256
from pathlib import Path
import subprocess

from bitgenesis.v3.assay import run_assay
from bitgenesis.v3.runner import save
from bitgenesis.v3.world import Config


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch source required')
    root=Path('data/v3-study-001')
    root.mkdir(parents=True,exist_ok=False)
    metadata=dict(status='running',planned_sources=5,completed_sources=0,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=sha256(Path('experiments/v3/study-001.md').read_bytes()).hexdigest())
    save(root/'metadata.json',metadata)
    sources=[]
    try:
        for seed in range(88000,88005):
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=8*1024**3:
                metadata['status']='storage_limit'
                return
            config=Config(width=16,height=16,founders=32,feeding_limit=16,renewal_per_thousand=60)
            result=run_assay(root/f'seed-{seed}',config,seed,300,500,max_actor_records=128000)
            sources.append(dict(seed=seed,**result))
            save(root/'results.json',sources)
            metadata['completed_sources']=len(sources)
            save(root/'metadata.json',metadata)
            print(f'{len(sources)}/5 seed={seed} {result["selection"]["status"]}',flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
