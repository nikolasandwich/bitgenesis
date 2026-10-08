"""Study036 immutable input inventory; no intervention or scientific calculation."""
from pathlib import Path
from scripts.copy_slots_inputs import bindings as prior, read, save, digest, source_cases

NAMES = ('metadata.json', 'records.json', 'summary.json', 'independent-verification.json')
SELECTION = Path('docs/research/results/v4-study-035-selection.json')
MANIFEST = Path('docs/research/results/v4-study-035-sources.json')
NEW_FILES = ('experiments/v4/study-036.md', 'scripts/founder_removal_inputs.py',
             'scripts/run_v4_founder_removal.py', 'scripts/verify_v4_founder_removal.py')
EVIDENCE = (str(SELECTION), str(MANIFEST), 'docs/research/results/v4-study-035-review.json',
            'docs/research/v4-study-035.zh-CN.md')


def input_paths(errors=None):
    if errors is None:
        errors = {}
    paths = set(NEW_FILES) | set(EVIDENCE)
    for name in NAMES:
        paths.update(('data/v4-study-034/' + name, 'docs/research/results/v4-study-034-' + name))
    try:
        manifest = read(MANIFEST)['files_sha256']
        assert isinstance(manifest, dict) and len(manifest) == 509
        paths.update(manifest)
    except Exception as error:
        errors[str(MANIFEST)] = repr(error)
    path = Path('docs/research/results/v4-study-034-metadata.json')
    try:
        old = read(path)['input_sha256']
        assert isinstance(old, dict) and len(old) == 413
        paths.update(old)
    except Exception as error:
        errors[str(path)] = repr(error)
    return sorted(paths)


def validate_manifest(expected):
    actual = {name: digest(name) for name in expected}
    assert actual == expected, 'source bytes changed'
    return actual


def bindings():
    old = prior()
    assert len(old) == 413
    root = Path('data/v4-study-034')
    assert {p.name for p in root.iterdir()} == set(NAMES)
    meta, proof = read(root/'metadata.json'), read(root/'independent-verification.json')
    assert meta['status'] == 'complete' and proof['status'] == 'verified'
    assert meta['input_sha256'] == meta['input_sha256_after'] == old
    assert proof['input_sha256'] == proof['input_sha256_after'] == old
    assert meta['output_sha256'] == {n: digest(root/n) for n in ('records.json', 'summary.json')}
    assert proof['files_sha256'] == {n: digest(root/n) for n in NAMES[:-1]}
    for name in NAMES:
        assert (root/name).read_bytes() == Path('docs/research/results/v4-study-034-' + name).read_bytes()
    manifest = read(MANIFEST)['files_sha256']
    assert len(manifest) == 509
    validate_manifest(manifest)
    review = read(Path(EVIDENCE[2]))
    assert all(r['verdict'] == 'APPROVED' for r in review['reviews']) and len(review['reviews']) == 2
    validate_manifest(review['files_sha256'])
    errors = {}
    paths = input_paths(errors)
    assert not errors
    assert set(old) <= set(paths)
    return {p: digest(p) for p in paths}
