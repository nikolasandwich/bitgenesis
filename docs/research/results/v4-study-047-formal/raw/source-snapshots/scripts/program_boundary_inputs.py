"""Source integrity and IO only for the frozen 80-case read-only audit."""
from pathlib import Path
from scripts.program_direction_inputs import bindings as prior,read,digest,save

def source_cases():
    for genotype,study in (('homogeneous','019'),('heterogeneous','023')):
        for exchange in (False,True):
            for seed in range(120000,120020):
                yield genotype,Path(f'data/v4-study-{study}/cases/seed-{seed}-random-direction-exchange-{str(exchange).lower()}.json')

def bindings():
    result=prior();root=Path('data/v4-study-023')
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['completed_cases']==40
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert proof['status']=='verified' and proof['cases']==40
    assert proof['verifier_sha256']==result['scripts/verify_v4_program_direction.py']
    for n,h in meta['output_sha256'].items():assert digest(root/n)==h
    for n,h in proof['files_sha256'].items():assert digest(root/n)==h
    cases=[p for g,p in source_cases() if g=='heterogeneous']
    assert set(root.glob('cases/*.json'))==set(cases)
    for p in cases:result[str(p)]=digest(p)
    for n in ('metadata','results','summary','independent-verification'):
        p=root/(n+'.json');a=Path(f'docs/research/results/v4-study-023-{n}.json')
        assert p.read_bytes()==a.read_bytes()
        for f in (p,a):result[str(f)]=digest(f)
    for p in ('docs/research/results/v4-study-023-cases.tar.gz','docs/research/results/v4-study-023-archive-verification.json','experiments/v4/study-024.md','scripts/program_boundary_inputs.py','scripts/analyze_v4_program_boundaries.py','scripts/verify_v4_program_boundaries.py','scripts/analyze_v4_copy_episodes.py','scripts/verify_v4_copy_episodes.py','scripts/analyze_v4_copy_members.py','scripts/verify_v4_copy_members.py'):
        if p in result:assert result[p]==digest(p)
        result[p]=digest(p)
    return dict(sorted(result.items()))
