"""Verify frozen actual ancestry, then run every registered spatial competition."""
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
    root=Path('data/v4-study-008')
    root.mkdir(parents=True,exist_ok=False)
    metadata=dict(status='running',planned_runs=1440,completed_runs=0,selection_sha256=selection_hash,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=sha256(Path('experiments/v4/study-008.md').read_bytes()).hexdigest())
    save(root/'metadata.json',metadata)
    results=[]
    try:
        for source,pair in pairs:
            for environment,drive,layout,swapped in product((101000,101001),(250,500),('adjacent','intermediate','separated'),(False,True)):
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=6*1024**3:
                    metadata['status']='storage_limit'
                    return
                name=f"source-{source['seed']}-{source['drive']}-{source['mutation']}-unit-{pair['descendant']['id']}-env-{environment}-drive-{drive}-layout-{layout}-swap-{int(swapped)}"
                output=root/name
                sites={'adjacent':(34,35),'intermediate':(34,36),'separated':(34,38)}[layout]
                summary=run(output,environment,(tuple(pair['descendant']['program']),tuple(pair['founder']['program'])),200,width=8,height=8,
                            initial_sites=sites[::-1] if swapped else sites,initial_energy=64,initial_material=0,
                            initial_raw=1,capacity=64,drive_amount=8,leak=1,bond_cost=1,exchange=True,
                            threshold=16,construction_cost=4,copy_cost=1,
                            drive_per_thousand=drive,max_site_records=12864)
                lineage=trace(output)
                checked=lineage['dynamics_audit']
                save(output/'lineage.json',lineage)
                save(output/'audit.json',checked)
                results.append(dict(source_seed=source['seed'],training_drive=source['drive'],
                    training_mutation=source['mutation'],descendant_id=pair['descendant']['id'],
                    environment=environment,drive=drive,layout=layout,swapped=swapped,directory=name,summary=summary))
                metadata['completed_runs']=len(results)
                save(root/'results.json',results)
                save(root/'metadata.json',metadata)
                if len(results)%24==0:
                    print(f'{len(results)}/1440 audited spatial competitions',flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
