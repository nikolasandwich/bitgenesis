"""IO and frozen input provenance for study025; no scientific algorithms."""
from pathlib import Path
from scripts.program_boundary_inputs import bindings as prior,read,digest,save


def source_cases():
    for mode in ('random-feed','random-both'):
        for seed in range(120000,120020):
            for exchange in (False,True):
                yield Path('data/v4-study-019/cases')/f'seed-{seed}-{mode}-exchange-{str(exchange).lower()}.json'


def input_paths(errors=None):
    """Recover the inventory before validation, retaining readable-path evidence."""
    if errors is None:errors={}
    root=Path('data/v4-study-024')
    paths=set()
    for name in ('metadata.json','records.json','summary.json','independent-verification.json'):
        paths.update((str(root/name),str(Path('docs/research/results')/('v4-study-024-'+name))))
    paths.update(('experiments/v4/study-025.md','scripts/program_feed_inputs.py','scripts/run_v4_program_feed.py','scripts/verify_v4_program_feed.py'))
    for metadata in (root/'metadata.json',Path('docs/research/results/v4-study-024-metadata.json')):
        try:
            old=read(metadata)['input_sha256']
            if not isinstance(old,dict) or len(old)!=283 or not all(isinstance(p,str) for p in old):
                raise ValueError('invalid prior inventory')
            paths.update(old)
            break
        except Exception as exc:errors[str(metadata)]=repr(exc)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==283
    root=Path('data/v4-study-024')
    names=('metadata.json','records.json','summary.json','independent-verification.json')
    assert {p.name for p in root.iterdir()}==set(names)
    meta=read(root/names[0]);proof=read(root/names[-1])
    assert meta['status']=='complete' and meta['completed_cases']==80 and meta['saved_steps']==2560
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert meta['output_sha256']=={n:digest(root/n) for n in names[1:-1]}
    assert proof['status']=='verified' and proof['cases']==80 and proof['saved_steps']==2560 and proof['input_files']==283
    assert proof['files_sha256']=={n:digest(root/n) for n in names[:-1]}
    assert proof['verifier_sha256']==result['scripts/verify_v4_program_boundaries.py']
    for n in names:
        archive=Path('docs/research/results')/('v4-study-024-'+n)
        assert archive.read_bytes()==(root/n).read_bytes()
        for p in (archive,root/n):result[str(p)]=digest(p)
    for p in ('experiments/v4/study-025.md','scripts/program_feed_inputs.py','scripts/run_v4_program_feed.py','scripts/verify_v4_program_feed.py'):
        result[p]=digest(p)
    assert len(result)==295
    return dict(sorted(result.items()))
