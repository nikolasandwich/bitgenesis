"""Read-only, phase-aligned structure observations on audited hereditary runs."""
from hashlib import sha256
import json
from pathlib import Path
from .lineage import Observer
from .structure import snapshot, continuity


def trace(directory):
    root = Path(directory)
    def hashes():
        return {p.name: sha256(p.read_bytes()).hexdigest()
                for p in sorted(root.iterdir()) if p.is_file()}
    before = hashes()
    def read(name):
        return json.loads((root / name).read_text(encoding='utf-8'))
    meta = read('metadata.json')
    schema = meta['schema']
    if schema == 'v4-hereditary-run-1':
        from .hereditary_audit import audit
    elif schema == 'v4-competition-1':
        from .competition_audit import audit
    elif schema == 'v4-program-assay-1':
        from .program_assay_audit import audit
    else:
        raise ValueError('unsupported audited hereditary schema')
    checked = audit(root)
    initial = read('initial.json')
    observer = Observer(initial['units'])
    width, height = meta['width'], meta['height']
    previous_units = initial['units']
    initial_snapshot = snapshot(previous_units, observer.alive, width, height, phase='final')
    previous_final = initial_snapshot
    previous_interaction = None
    observations = []
    with (root / 'steps.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            intermediate = row['interaction_units']
            if len(intermediate) != len(previous_units):
                raise ValueError('interaction geometry mismatch')
            for old, current in zip(previous_units, intermediate):
                if (old is None) != (current is None):
                    raise ValueError('interaction changed occupation before conversion')
                if old is not None and (old['program'], old['material']) != (current['program'], current['material']):
                    raise ValueError('interaction changed inherited identity')
            pre_ids = list(observer.alive)
            interaction = snapshot(intermediate, pre_ids, width, height, phase='interaction',
                                   bonds=row['driven']['interaction']['bonds'])
            observer.accept(row)
            final = snapshot(row['units'], observer.alive, width, height, phase='final')
            final_links = {name: continuity(previous_final['components'][name], groups)
                           for name, groups in final['components'].items()}
            interaction_links = None if previous_interaction is None else {
                name: continuity(previous_interaction['components'][name], groups)
                for name, groups in interaction['components'].items()}
            observations.append(dict(tick=row['tick'], interaction=interaction, final=final,
                interaction_site_ids=pre_ids, final_site_ids=list(observer.alive),
                interaction_continuity=interaction_links, final_continuity=final_links))
            previous_final, previous_interaction = final, interaction
            previous_units = row['units']
    if observer.tick != meta['steps'] or previous_units != read('final.json')['units']:
        raise ValueError('structure final state/horizon mismatch')
    if hashes() != before:
        raise ValueError('input bytes changed during observation')
    return dict(scope='passive phase-aligned boundaries and surviving-member overlap; not structural replication',
                input_sha256=before, dynamics_audit=checked,
                observer_sha256={name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                 for name in ('structure_trace.py', 'structure.py', 'lineage.py')},
                initial=initial_snapshot, observations=observations, lineage_summary=observer.result()['summary'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.directory.resolve()):
        parser.error('observation output must be outside the input directory')
    result = trace(args.directory)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
