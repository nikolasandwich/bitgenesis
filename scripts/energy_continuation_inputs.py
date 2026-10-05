"""Study028 source inventory and byte bindings; no scientific computation."""
from pathlib import Path
from scripts.north_energy_inputs import bindings as prior, source_cases, read, digest, save

NAMES = ('metadata.json', 'records.json', 'summary.json', 'independent-verification.json')
NEW_FILES = ('experiments/v4/study-028.md', 'scripts/energy_continuation_inputs.py',
             'scripts/run_v4_energy_continuation.py', 'scripts/verify_v4_energy_continuation.py')


def input_paths(errors=None):
    if errors is None:
        errors = {}
    paths = set(NEW_FILES) | {str(p) for _, p in source_cases()}
    for name in NAMES:
        paths.update(('data/v4-study-027/' + name, 'docs/research/results/v4-study-027-' + name))
    for path in (Path('data/v4-study-027/metadata.json'), Path('docs/research/results/v4-study-027-metadata.json')):
        try:
            inventory = read(path)['input_sha256']
            if not isinstance(inventory, dict) or len(inventory) != 401 or not all(isinstance(k, str) for k in inventory):
                raise ValueError('prior401 inventory')
            paths.update(inventory)
            break
        except Exception as error:
            errors[str(path)] = repr(error)
    return sorted(paths)


def bindings():
    result = prior()
    assert len(result) == 401
    root = Path('data/v4-study-027')
    assert {p.name for p in root.iterdir()} == set(NAMES)
    meta = read(root/'metadata.json'); proof = read(root/'independent-verification.json')
    assert meta['status'] == 'complete' and meta['planned_probes'] == meta['completed_probes'] == 52
    assert meta['new_phase_transitions'] == 104 and meta['new_full_world_steps'] == 0
    assert meta['input_sha256'] == meta['input_sha256_after'] == result
    assert meta['output_sha256'] == {n: digest(root/n) for n in ('records.json', 'summary.json')}
    assert proof['status'] == 'verified' and proof['probes'] == 52 and proof['input_files'] == 401
    assert proof['new_phase_transitions'] == 104 and proof['replayed_saved_steps'] == 7680
    assert proof['input_sha256'] == proof['input_sha256_after'] == result
    assert proof['verifier_sha256'] == result['scripts/verify_v4_north_energy.py']
    assert proof['files_sha256'] == {n: digest(root/n) for n in NAMES[:-1]}
    for name in NAMES:
        p = root/name; archive = Path('docs/research/results/v4-study-027-' + name)
        assert p.read_bytes() == archive.read_bytes()
        for path in (p, archive):
            result[str(path)] = digest(path)
    for name in NEW_FILES:
        result[name] = digest(name)
    assert len(result) == 413 and set(result) == set(input_paths())
    return dict(sorted(result.items()))
