"""Verify frozen actual ancestry, then run every registered matched assay."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
from scripts.run_v4_study006 import verify_selection
from bitgenesis.v4.competition import run, save
from bitgenesis.v4.competition_lineage import trace


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    pairs,selection_hash=verify_selection()
    root=Path('data/v4-study-007')
    root.mkdir(parents=True,exist_ok=False)
    metadata=dict(status='running',planned_runs=480,completed_runs=0,selection_sha256=selection_hash,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=sha256(Path('experiments/v4/study-007.md').read_bytes()).hexdigest())
    save(root/'metadata.json',metadata)
    results=[]
    try:
        for source,pair in pairs:
            for environment,drive,swapped in product((100000,100001),(250,500),(False,True)):
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=2*1024**3:
                    metadata['status']='storage_limit'
                    return
                name=f"source-{source['seed']}-{source['drive']}-{source['mutation']}-unit-{pair['descendant']['id']}-env-{environment}-drive-{drive}-swap-{int(swapped)}"
                output=root/name
                summary=run(output,environment,(tuple(pair['descendant']['program']),tuple(pair['founder']['program'])),200,width=8,height=8,
                            initial_sites=(38,34) if swapped else (34,38),drive_per_thousand=drive,max_site_records=12864)
                lineage=trace(output)
                checked=lineage['dynamics_audit']
                save(output/'lineage.json',lineage)
                save(output/'audit.json',checked)
                results.append(dict(source_seed=source['seed'],training_drive=source['drive'],
                    training_mutation=source['mutation'],descendant_id=pair['descendant']['id'],
                    environment=environment,drive=drive,swapped=swapped,directory=name,summary=summary))
                metadata['completed_runs']=len(results)
                save(root/'results.json',results)
                save(root/'metadata.json',metadata)
                if len(results)%8==0:
                    print(f'{len(results)}/480 audited competitions',flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
