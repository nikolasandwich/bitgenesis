"""Verify frozen actual ancestry, then run every registered matched assay."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
from bitgenesis.v4.lineage import trace
from bitgenesis.v4.program_assay import run, save
from bitgenesis.v4.program_assay_audit import audit
from scripts.trace_v4_study005 import select


def verify_selection():
    path=Path('data/v4-study-005-lineage/selection.json')
    selection=json.loads(path.read_text(encoding='utf-8'))
    if path.read_bytes()!=Path('docs/research/results/v4-study-005-ancestor-selection.json').read_bytes():
        raise ValueError('archived selection mismatch')
    if selection['selection_protocol_sha256']!=sha256(Path('experiments/v4/ancestral-assay-selection.md').read_bytes()).hexdigest():
        raise ValueError('selection protocol mismatch')
    sources=selection['sources']
    if len(sources)!=20 or {(s['seed'],s['drive'],s['mutation']) for s in sources}!=set(product(range(96000,96005),(250,500),(0,100))):
        raise ValueError('selection source grid')
    if selection['source_results_sha256']!=sha256(Path('data/v4-study-005/results.json').read_bytes()).hexdigest():
        raise ValueError('source results mismatch')
    for s in sources:
        name=f"seed-{s['seed']}-drive-{s['drive']}-mutation-{s['mutation']}"
        stored=Path('data/v4-study-005-lineage')/(name+'.json')
        if sha256(stored.read_bytes()).hexdigest()!=s['lineage_sha256']:
            raise ValueError('lineage file mismatch')
        lineage=trace(Path('data/v4-study-005')/name)
        if lineage!=json.loads(stored.read_text(encoding='utf-8')):
            raise ValueError('reconstructed lineage mismatch')
        if lineage['dynamics_audit']['output_sha256']!=s['source_output_sha256']:
            raise ValueError('source trajectory mismatch')
        sampled=select(lineage,s['seed'],s['drive'],s['mutation'])
        if any(s[k]!=v for k,v in sampled.items()):
            raise ValueError('frozen sampling mismatch')
        print(f'Validated ancestry {name}',flush=True)
    pairs=[(s,p) for s in sources for p in s['pairs']]
    if len(pairs)!=60 or sum(p['equal_program'] for _,p in pairs)!=55:
        raise ValueError('registered pair count mismatch')
    return pairs,sha256(path.read_bytes()).hexdigest()


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    pairs,selection_hash=verify_selection()
    root=Path('data/v4-study-006')
    root.mkdir(parents=True,exist_ok=False)
    metadata=dict(status='running',planned_runs=480,completed_runs=0,selection_sha256=selection_hash,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        protocol_sha256=sha256(Path('experiments/v4/study-006.md').read_bytes()).hexdigest())
    save(root/'metadata.json',metadata)
    results=[]
    try:
        for source,pair in pairs:
            for environment,drive,role in product((98000,98001),(250,500),('descendant','founder')):
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=2*1024**3:
                    metadata['status']='storage_limit'
                    return
                name=f"source-{source['seed']}-{source['drive']}-{source['mutation']}-unit-{pair['descendant']['id']}-env-{environment}-drive-{drive}-{role}"
                output=root/name
                summary=run(output,environment,tuple(pair[role]['program']),200,width=8,height=8,
                            initial_site=36,drive_per_thousand=drive,max_site_records=12864)
                checked=audit(output)
                save(output/'audit.json',checked)
                results.append(dict(source_seed=source['seed'],training_drive=source['drive'],
                    training_mutation=source['mutation'],descendant_id=pair['descendant']['id'],
                    environment=environment,drive=drive,role=role,directory=name,summary=summary))
                metadata['completed_runs']=len(results)
                save(root/'results.json',results)
                save(root/'metadata.json',metadata)
                if len(results)%8==0:
                    print(f'{len(results)}/480 audited assays',flush=True)
        metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',metadata)


if __name__=='__main__':
    main()
