"""Summarize the frozen study009 windows without treating boundaries as organisms."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def mean(values):
    present = [v for v in values if v is not None]
    return dict(mean=None if not present else str(sum(present, Fraction())/len(present)),
                available=len(present), missing=len(values)-len(present))


def disagreement(snapshot, first, second):
    def memberships(name):
        return {i: frozenset(group) for group in snapshot['components'][name] for i in group}
    a, b = memberships(first), memberships(second)
    if a.keys() != b.keys():
        raise ValueError('boundary member coverage')
    return None if not a else Fraction(sum(a[i] != b[i] for i in a), len(a))


def summarize(observed):
    rows = observed['observations']
    if [row['tick'] for row in rows] != list(range(1, 501)):
        raise ValueError('complete ordered 500-tick observations required')
    windows = []
    for start, end in ((1, 100), (101, 500)):
        selected = rows[start-1:end]
        output = dict(start=start, end=end, boundaries={}, continuity={})
        for phase, names in (('interaction', ('contact', 'material', 'bond')),
                             ('final', ('contact', 'material'))):
            for name in names:
                counts, largest, singleton = [], [], []
                splits = merges = no_overlap = transitions = 0
                for row in selected:
                    groups = row[phase]['components'][name]
                    sizes = [len(group) for group in groups]
                    occupied = sum(sizes)
                    counts.append(Fraction(len(sizes)))
                    largest.append(None if not occupied else Fraction(max(sizes), occupied))
                    singleton.append(None if not occupied else Fraction(sizes.count(1), occupied))
                    links = row[phase+'_continuity']
                    if links is None:
                        if phase != 'interaction' or row['tick'] != 1:
                            raise ValueError('missing same-phase continuity')
                        continue
                    transitions += 1
                    splits += len(links[name]['splits'])
                    merges += len(links[name]['merges'])
                    no_overlap += len(links[name]['current_without_overlap'])
                key = phase+'/'+name
                output['boundaries'][key] = dict(component_count=mean(counts),
                    largest_fraction=mean(largest), singleton_fraction=mean(singleton))
                output['continuity'][key] = dict(transitions=transitions, splits=splits,
                    merges=merges, current_without_overlap=no_overlap)
        for name, first, second in (('material_bond', 'material', 'bond'),
                                    ('contact_material', 'contact', 'material')):
            output[name] = mean([disagreement(row['interaction'], first, second) for row in selected])
        windows.append(output)
    return dict(primary=windows[1]['material_bond'], windows=windows)


def aggregate(sources):
    expected = set(product(range(96000, 96005), (250, 500), (0, 100)))
    keys = [(r['seed'], r['drive'], r['mutation']) for r in sources]
    if len(keys) != 20 or set(keys) != expected:
        raise ValueError('all twenty unique source cases required')
    groups = []
    for drive, mutation in product((250, 500), (0, 100)):
        selected = sorted((r for r in sources if (r['drive'], r['mutation']) == (drive, mutation)),
                          key=lambda r: r['seed'])
        values = [None if r['summary']['primary']['mean'] is None else
                  Fraction(r['summary']['primary']['mean']) for r in selected]
        windows = []
        for index in (0, 1):
            source_windows = [r['summary']['windows'][index] for r in selected]
            def source_mean(items):
                return mean([None if item['mean'] is None else Fraction(item['mean']) for item in items])
            window = dict(start=source_windows[0]['start'], end=source_windows[0]['end'],
                          boundaries={}, continuity_totals={})
            for key in source_windows[0]['boundaries']:
                window['boundaries'][key] = {
                    metric: source_mean([w['boundaries'][key][metric] for w in source_windows])
                    for metric in ('component_count', 'largest_fraction', 'singleton_fraction')}
                window['continuity_totals'][key] = {
                    metric: sum(w['continuity'][key][metric] for w in source_windows)
                    for metric in ('transitions', 'splits', 'merges', 'current_without_overlap')}
            for metric in ('material_bond', 'contact_material'):
                window[metric] = source_mean([w[metric] for w in source_windows])
            windows.append(window)
        groups.append(dict(drive=drive, mutation=mutation, primary=mean(values), windows=windows,
            seeds=[r['seed'] for r in selected],
            nonempty_ticks=[r['summary']['primary']['available'] for r in selected],
            empty_ticks=[r['summary']['primary']['missing'] for r in selected]))
    return groups


def main():
    root = Path('data/v4-study-009')
    meta, results = read(root/'metadata.json'), read(root/'results.json')
    if meta['status'] != 'complete' or meta['completed_sources'] != 20:
        raise ValueError('incomplete observation cohort')
    def digest(path):
        return sha256(path.read_bytes()).hexdigest()
    if meta['protocol_sha256'] != digest(Path('experiments/v4/study-009.md')):
        raise ValueError('protocol binding')
    sources = []
    for row in results:
        name = f"seed-{row['seed']}-drive-{row['drive']}-mutation-{row['mutation']}"
        source = Path('data/v4-study-005')/name
        path = root/row['observation']
        checked = read(root/row['audit'])
        observed = read(path)
        hashes = {p.name: digest(p) for p in source.iterdir() if p.is_file()}
        if (digest(path) != checked['observation_sha256'] or
                checked['observation_sha256'] != row['observation_sha256'] or
                hashes != checked['input_sha256'] or hashes != observed['input_sha256'] or
                hashes != row['input_sha256']):
            raise ValueError('audited observation/source binding')
        if (checked['ticks'], checked['partitions'], checked['transitions']) != (500, 2502, 2497):
            raise ValueError('audit coverage')
        if checked['auditor_sha256'] != digest(Path('src/bitgenesis/v4/structure_audit.py')):
            raise ValueError('auditor binding')
        for filename, value in observed['observer_sha256'].items():
            if digest(Path('src/bitgenesis/v4')/filename) != value:
                raise ValueError('observer binding')
        sources.append(dict(seed=row['seed'], drive=row['drive'], mutation=row['mutation'],
            observation_sha256=digest(path), audit_sha256=digest(root/row['audit']),
            summary=summarize(observed)))
    report = dict(scope='descriptive boundary dependence; reconstructed original trajectories, zero new samples',
        sources=sources, groups=aggregate(sources), protocol_sha256=meta['protocol_sha256'],
        reconstruction_sha256=digest(Path('data/v4-study-005/reconstruction.json')),
        script_sha256=digest(Path(__file__)))
    with (root/'summary.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report['groups'], indent=2))


if __name__ == '__main__':
    main()
