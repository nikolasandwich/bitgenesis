"""Run the registered hereditary-variation cohort with independent per-run audits."""
from hashlib import sha256
from itertools import product
from pathlib import Path
import subprocess

from bitgenesis.v4.hereditary_runner import run,save
from bitgenesis.v4.hereditary_audit import audit


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    root=Path('data/v4-study-005')
    root.mkdir(parents=True,exist_ok=False)
    metadata=dict(status='running',planned_runs=20,completed_runs=0,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=sha256(Path('experiments/v4/study-005.md').read_bytes()).hexdigest())
    save(root/'metadata.json',metadata)
    results=[]
    try:
        for seed,drive,mutation in product(range(96000,96005),(250,500),(0,100)):
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=2*1024**3:
                metadata['status']='storage_limit'
                return
            output=root/f'seed-{seed}-drive-{drive}-mutation-{mutation}'
            summary=run(output,seed,500,drive_per_thousand=drive,mutation_per_thousand=mutation,occupancy=250,max_site_records=128256)
            checked=audit(output)
            save(output/'audit.json',checked)
            results.append(dict(seed=seed,drive=drive,mutation=mutation,summary=summary))
            save(root/'results.json',results)
            metadata['completed_runs']=len(results)
            save(root/'metadata.json',metadata)
            print(f'{len(results)}/20 {output.name}',flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
