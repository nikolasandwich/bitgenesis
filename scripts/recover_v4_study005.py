"""Import historical replay after matching all archived trajectory hashes.

Run run_v4_study005.py in a clean worktree at the archived revision first.
Replay Python/source provenance is retained; reconstruction is explicitly recorded.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
from bitgenesis.v4.hereditary_audit import audit


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def historical_bytes(raw, digest):
    if sha256(raw).hexdigest() == digest:
        return raw, False
    converted = raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    if sha256(converted).hexdigest() != digest:
        raise ValueError('historical trajectory hash mismatch')
    return converted, True


def recover(replay, destination):
    replay, destination = Path(replay), Path(destination)
    archive = Path('docs/research/results')
    expected_meta = read(archive/'v4-study-005-metadata.json')
    expected_rows = read(archive/'v4-study-005-results.json')
    checks = read(archive/'v4-study-005-verification.json')['checks']
    replay_meta = read(replay/'metadata.json')
    protocol = Path('experiments/v4/study-005.md').read_bytes()
    if sha256(protocol).hexdigest() != replay_meta['protocol_sha256']:
        raise ValueError('replay protocol binding')
    historical_bytes(protocol, expected_meta['protocol_sha256'])
    if ({k: v for k, v in replay_meta.items() if k != 'protocol_sha256'} !=
            {k: v for k, v in expected_meta.items() if k != 'protocol_sha256'} or
            read(replay/'results.json') != expected_rows):
        raise ValueError('replay cohort differs from archive')
    names = {row['directory'] for row in checks}
    if len(checks) != 20 or len(names) != 20 or {p.name for p in replay.iterdir() if p.is_dir()} != names:
        raise ValueError('replay source coverage')
    destination.mkdir(parents=True, exist_ok=False)
    report = dict(status='running', reconstructed_at=datetime.now(timezone.utc).isoformat(),
        historical_revision=expected_meta['git_commit'], independent_new_samples=0,
        scope='deterministic replay; trajectory bytes match archived hashes; metadata regenerated',
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        archive_sha256={p.name: sha256(p.read_bytes()).hexdigest() for p in
            (archive/'v4-study-005-metadata.json', archive/'v4-study-005-results.json',
             archive/'v4-study-005-verification.json')}, checks=[])
    try:
        for row in checks:
            source = replay/row['directory']
            meta = read(source/'metadata.json')
            if meta['git_commit'] != expected_meta['git_commit'] or meta['git_dirty'] is not False:
                raise ValueError('historical replay revision')
            for name, digest in meta['source_sha256'].items():
                if sha256((Path('src/bitgenesis/v4')/name).read_bytes()).hexdigest() != digest:
                    raise ValueError('historical runtime source mismatch')
            target = destination/row['directory']
            target.mkdir()
            conversions = []
            for name, digest in row['audit']['output_sha256'].items():
                raw = (source/name).read_bytes()
                if sha256(raw).hexdigest() != meta['output_sha256'][name]:
                    raise ValueError('replay output hash mismatch')
                raw, converted = historical_bytes(raw, digest)
                if converted:
                    conversions.append(name)
                (target/name).write_bytes(raw)
            meta['output_sha256'] = row['audit']['output_sha256']
            (target/'metadata.json').write_text(json.dumps(meta, sort_keys=True)+'\n', encoding='utf-8')
            checked = audit(target)
            archived_audit = row['audit']
            code_hash_fields = {'audit_sha256', 'dependencies_sha256'}
            if ({k: v for k, v in checked.items() if k not in code_hash_fields} !=
                    {k: v for k, v in archived_audit.items() if k not in code_hash_fields}):
                raise ValueError('independent replay audit differs from archive')
            # Fresh audits must agree on every scientific field. Preserve both
            # code identities: historical working-copy encoding may differ from
            # the Git blob, so do not claim historical auditor byte identity.
            auditor_provenance = {key: dict(current=checked[key], archived=archived_audit[key])
                                  for key in sorted(code_hash_fields)}
            (target/'audit.json').write_text(json.dumps(checked, sort_keys=True)+'\n', encoding='utf-8')
            report['checks'].append(dict(directory=source.name, python=meta['python'],
                output_sha256=checked['output_sha256'], lf_to_crlf=conversions,
                independent_audit_scientific_fields_match_archive=True,
                auditor_provenance=auditor_provenance))
            print(f"{len(report['checks'])}/20 replay hashes and independent audit match", flush=True)
        # Exact archived cohort manifests are copied only after semantic equality
        # and every trajectory/audit gate passes. Per-run metadata stays truthful.
        for name in ('metadata', 'results'):
            shutil.copyfile(archive/f'v4-study-005-{name}.json', destination/f'{name}.json')
        report['status'] = 'complete'
    except BaseException as error:
        report.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        (destination/'reconstruction.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replay', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/v4-study-005'))
    args = parser.parse_args()
    recover(args.replay, args.output)
