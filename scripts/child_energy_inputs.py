"""Study029 immutable input inventory and archive checks, without computation."""
from pathlib import Path
import tarfile
from scripts.energy_continuation_inputs import bindings as prior, read, save, digest

NAMES=('metadata.json','records.json','summary.json','independent-verification.json')
NEW_FILES=('experiments/v4/study-029.md','scripts/child_energy_inputs.py',
           'scripts/analyze_v4_child_energy.py','scripts/verify_v4_child_energy.py')
ARCHIVES=('docs/research/results/v4-study-028-cases.tar.gz',
          'docs/research/results/v4-study-028-archive-verification.json')


def source_cases():
    return [Path(f'data/v4-study-028/cases/branch-{i:03d}.json') for i in range(52)]


def input_paths(errors=None):
    if errors is None: errors={}
    paths=set(NEW_FILES)|set(ARCHIVES)|{str(p) for p in source_cases()}
    for name in NAMES:
        paths.update(('data/v4-study-028/'+name,'docs/research/results/v4-study-028-'+name))
    for path in (Path('data/v4-study-028/metadata.json'),Path('docs/research/results/v4-study-028-metadata.json')):
        try:
            inventory=read(path)['input_sha256']
            if not isinstance(inventory,dict) or len(inventory)!=413 or not all(isinstance(k,str) for k in inventory):
                raise ValueError('prior413 inventory')
            paths.update(inventory);break
        except Exception as error:
            errors[str(path)]=repr(error)
    return sorted(paths)


def bindings():
    result=prior();assert len(result)==413
    root=Path('data/v4-study-028');assert {p.name for p in root.iterdir()}==set(NAMES)|{'cases'}
    meta=read(root/'metadata.json');proof=read(root/'independent-verification.json')
    assert meta['status']=='complete' and meta['planned_branches']==meta['completed_branches']==52
    assert meta['new_full_world_steps']==996 and meta['new_phase_transitions']==0
    assert meta['input_sha256']==meta['input_sha256_after']==result
    assert proof['status']=='verified' and proof['branches']==52 and proof['new_full_world_steps']==996 and proof['input_files']==413
    assert proof['input_sha256']==proof['input_sha256_after']==result
    assert proof['verifier_sha256']==result['scripts/verify_v4_energy_continuation.py']
    cases=source_cases();assert sorted((root/'cases').iterdir())==cases
    hashes={str(p.relative_to(root)):digest(p) for p in cases}
    hashes.update({n:digest(root/n) for n in ('records.json','summary.json')})
    assert meta['output_sha256']==hashes
    assert proof['files_sha256']==dict(hashes,**{'metadata.json':digest(root/'metadata.json')})
    for name in NAMES:
        p=root/name;archive=Path('docs/research/results/v4-study-028-'+name)
        assert p.read_bytes()==archive.read_bytes()
        for path in (p,archive):result[str(path)]=digest(path)
    manifest=read(Path(ARCHIVES[1]));archive=Path(ARCHIVES[0])
    assert manifest['status']=='restored-and-verified' and manifest['cases']==52
    assert manifest['archive_bytes']==archive.stat().st_size and manifest['archive_sha256']==digest(archive)
    names=[str(p.relative_to(root)) for p in cases]
    assert set(manifest['files'])==set(names)
    assert manifest['raw_bytes']==sum(p.stat().st_size for p in cases)
    with tarfile.open(archive) as tar:
        assert tar.getnames()==names
        for p,name in zip(cases,names):
            assert manifest['files'][name]==dict(bytes=p.stat().st_size,sha256=hashes[name])
            assert tar.extractfile(name).read()==p.read_bytes()
            result[str(p)]=hashes[name]
    for name in ARCHIVES+NEW_FILES:result[name]=digest(name)
    assert len(result)==479 and set(result)==set(input_paths())
    return dict(sorted(result.items()))
