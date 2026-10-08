"""Execute the registered recovery cohort without selecting successful prefixes."""
from hashlib import sha256
from itertools import product
from pathlib import Path
import subprocess
from bitgenesis.v4.growing_runner import run as prefix_run, save
from bitgenesis.v4.growing_audit import audit as prefix_audit
from bitgenesis.v4.branches import run as branch_run
from bitgenesis.v4.branch_audit import audit as branch_audit


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    root=Path('data/v4-study-003')
    root.mkdir(parents=True,exist_ok=False)
    meta=dict(status='running',planned_prefixes=5,planned_branches=20,completed_prefixes=0,completed_branches=0,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=sha256(Path('experiments/v4/study-003.md').read_bytes()).hexdigest())
    results=[]
    def room():
        if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=2*1024**3:
            meta['status']='storage_limit'
            return False
        return True
    save(root/'metadata.json',meta)
    try:
        for seed in range(93000,93005):
            if not room():
                return
            origin=root/f'seed-{seed}-prefix'
            summary=prefix_run(origin,seed,300,occupancy=250,max_site_records=77056)
            save(origin/'audit.json',prefix_audit(origin))
            results.append(dict(seed=seed,kind='prefix',directory=origin.name,summary=summary))
            meta['completed_prefixes']+=1
            save(root/'results.json',results)
            save(root/'metadata.json',meta)
            for removal,threshold in product((False,True),(16,65)):
                if not room():
                    return
                sites=[y*16+x for y in range(6,10) for x in range(6,10)] if removal else []
                output=root/f'seed-{seed}-removal-{int(removal)}-threshold-{threshold}'
                summary=branch_run(output,origin,200,sites,threshold,max_site_records=51456)
                save(output/'audit.json',branch_audit(output,origin))
                results.append(dict(seed=seed,kind='branch',removal=removal,threshold=threshold,
                                    directory=output.name,summary=summary))
                meta['completed_branches']+=1
                save(root/'results.json',results)
                save(root/'metadata.json',meta)
                print(f"{meta['completed_prefixes']}/5 prefixes, {meta['completed_branches']}/20 branches",flush=True)
        meta['status']='complete'
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',meta)


if __name__=='__main__':
    main()
