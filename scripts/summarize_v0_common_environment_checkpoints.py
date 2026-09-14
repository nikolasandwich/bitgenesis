"""Summarize campaign023 checkpoints within source and arm after both full gates."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

CHECKPOINTS = (0, 100, 500, 1000, 5000, 10000)
ARMS = ('sampled', 'ancestor')
FIELDS = ('population', 'births', 'deaths', 'genome_variants',
          'ever_genome_values', 'changed_births', 'founder_lineages',
          'food_energy', 'organism_energy', 'supplied_energy', 'dissipated_energy')


def group_observations(observations, sources):
    expected = {(s, r, a, t) for s in sources for r in range(5)
                for a in ARMS for t in CHECKPOINTS}
    actual = {(r['source_seed'], r['replicate'], r['arm'], r['tick'])
              for r in observations}
    if len(observations) != len(expected) or actual != expected:
        raise ValueError('Incomplete or duplicated checkpoint grid')
    groups = []
    for source in sorted(sources):
        for arm in ARMS:
            for tick in CHECKPOINTS:
                rows = [r for r in observations if
                        (r['source_seed'], r['arm'], r['tick']) == (source, arm, tick)]
                groups.append(dict(source_seed=source, arm=arm, tick=tick,
                    worlds=len(rows), alive=sum(r['population'] > 0 for r in rows),
                    ranges={k: [min(r[k] for r in rows), max(r[k] for r in rows)]
                            for k in FIELDS},
                    null_mean_worlds=sum(r['mean_genome'] is None for r in rows),
                    null_generation_worlds=sum(r['max_generation'] is None for r in rows)))
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/campaign-023'))
    parser.add_argument('--metrics-verification', type=Path, required=True)
    parser.add_argument('--histories-verification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    root = Path(__file__).resolve().parents[1]
    mp = root/'docs/research/results/campaign-023-samples.json'
    vp = root/'docs/research/results/campaign-023-sample-verification.json'
    manifest = load(mp)
    sources = {s['source_seed'] for s in manifest['samples'] if s['available']}
    metrics = load(args.metrics_verification)
    histories = load(args.histories_verification)
    if (histories['metric_verification_sha256'] != sha(args.metrics_verification)
            or metrics['metadata_sha256'] != sha(args.input/'metadata.json')
            or metrics['manifest_sha256'] != sha(mp)
            or metrics['sample_verification_sha256'] != sha(vp)
            or metrics['metric_rows_checked'] != len(sources)*10*10001):
        raise ValueError('Full gate linkage differs')
    grid = {(s, r, a) for s in sources for r in range(5) for a in ARMS}
    for rows in (metrics['runs'], histories['results']):
        if len(rows) != len(grid) or {(r['source_seed'], r['replicate'], r['arm'])
                                     for r in rows} != grid:
            raise ValueError('Incomplete verification gate')
    observations, hashes = [], {}
    identity = ('source_seed', 'replicate', 'arm', 'seed', 'founder_trait',
                'sampled_individual_id', 'source_founder_id')
    for run in sorted(metrics['runs'], key=lambda r: (r['source_seed'], r['replicate'], r['arm'])):
        relative = f"source-{run['source_seed']}-replicate-{run['replicate']}-{run['arm']}/result.json"
        path = args.input/relative
        digest = sha(path)
        if any(gate['input_sha256'][relative] != digest for gate in (metrics, histories)):
            raise ValueError('Verified checkpoint data changed')
        hashes[relative] = digest
        result = load(path)
        if {k: v for k, v in result.items() if k != 'observations'} != run:
            raise ValueError('Terminal summary changed')
        for tick, obs in sorted(result['observations'].items(), key=lambda item: int(item[0])):
            if int(tick) != obs['tick']:
                raise ValueError('Checkpoint key differs from observation')
            observations.append(dict(**{k: run[k] for k in identity}, **obs))
    groups = group_observations(observations, sources)
    report = dict(scope='All registered checkpoints including extinct worlds. Each group contains five evaluation repeats of one source and arm; ranges are descriptive, not confidence intervals or independent evolved samples. Full histograms and null values remain in observation rows.',
        available_sources=len(sources),
        unavailable_source_seeds=[s['source_seed'] for s in manifest['samples'] if not s['available']],
        observations=observations, groups=groups, input_sha256=hashes,
        metric_report_sha256=sha(args.metrics_verification),
        history_report_sha256=sha(args.histories_verification), script_sha256=sha(Path(__file__)))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    compact = [{k: v for k, v in r.items() if not k.endswith('_histogram')} for r in observations]
    if compact:
        with (args.output/'checkpoints.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(compact[0]))
            writer.writeheader()
            writer.writerows(compact)
    print(f'Summarized {len(observations)} checkpoints in {len(groups)} source/arm/time groups')


if __name__ == '__main__':
    main()
