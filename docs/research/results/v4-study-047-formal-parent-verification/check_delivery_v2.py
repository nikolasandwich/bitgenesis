"""Read-only delivery verification; no scientific imports or execution."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


review_path = Path('docs/research/results/v4-study-047-formal-review.json')
assert digest(review_path) == '6a11a3a4f71c5ae725ca27c7f640d719a9ec49dfd7dd3867bb1a348da9543171'
review = json.loads(review_path.read_text())
assert review['verdict'] == 'REJECTED'
assert review['files_sha256'] == review['files_sha256_after']
assert len(review['files_sha256']) == 4718
for name, expected in review['files_sha256'].items():
    assert digest(name) == expected, name

snapshot = 'docs/research/results/v4-study-047-formal/raw/source-snapshots/src/bitgenesis/v4/competition.py'
original = 'data/v4-study-047/source-snapshots/src/bitgenesis/v4/competition.py'
head_bytes = subprocess.check_output(['git', 'show', 'a9efac4:src/bitgenesis/v4/competition.py'])
assert Path(snapshot).read_bytes() == Path(original).read_bytes() == head_bytes
stderr = 'docs/research/results/v4-study-047-process-guard-diagnostic/epoch-2/probe.stderr.bin'
execution = json.loads(Path(stderr).with_name('probe-execution.json').read_text())
assert digest(stderr) == execution['raw_output_sha256']['probe.stderr.bin']
assert digest(stderr) == review['files_sha256'][stderr]

# These two parent raw logs quote the original whitespace findings verbatim.
# Exclude only these exact log paths after checking their original recording hashes.
for meta_name, field, raw_name in [
    ('staged-whitespace.execution.json', 'stdout_sha256', 'staged-whitespace.stdout.bin'),
    ('delivery-check.execution.json', None, 'delivery-check.stderr.bin'),
]:
    parent_dir = Path(__file__).parent
    record = json.loads((parent_dir / meta_name).read_text())
    expected_log_hash = record[field] if field else record['raw_output_sha256'][raw_name]
    assert digest(parent_dir / raw_name) == expected_log_hash
parent_raw_exclusions = [
    'docs/research/results/v4-study-047-formal-parent-verification/staged-whitespace.stdout.bin',
    'docs/research/results/v4-study-047-formal-parent-verification/delivery-check.stderr.bin',
]
p = subprocess.run(['git', 'diff', '--cached', '--check', '--', '.',
                    *[':(exclude)' + x for x in parent_raw_exclusions]], capture_output=True)
assert p.returncode == 2 and p.stderr == b''
expected = (snapshot + ':117: new blank line at EOF.\n' + stderr + ':23: trailing whitespace.\n+    \n').encode()
assert p.stdout == expected, p.stdout.decode()
paths = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z']).decode().split('\0')[:-1]
json_paths = [name for name in paths if name.endswith('.json')]
for name in json_paths:
    json.loads(Path(name).read_text())
# If working bytes equal the index, validation above is also validation of staged JSON.
assert subprocess.run(['git', 'diff', '--quiet', '--', *paths]).returncode == 0
assert subprocess.check_output(['git', 'diff', 'HEAD', '--name-only', '--', 'src', 'scripts', 'tests']) == b''
spec = json.loads(Path('.kiro/specs/middle-policy-withdrawal/spec.json').read_text())
validation = json.loads(Path('docs/research/results/v4-study-047-formal-validation.json').read_text())
assert spec['feature_validation']['decision'] == validation['decision'] == 'NO_GO'
assert validation['status'] == 'NOT_VERIFIED'
assert validation['scientific_evidence_status'] == 'VERIFIED'
assert not validation['user_intervention_required']
assert digest('docs/research/v4-study-047-results.zh-CN.md') == '151ed1ed9ba760585dd3d63262f6e25d87bfddf9fcfcb91c669a177d537b2d4d'
print(json.dumps({
    'status': 'PASS_WITH_ORIGINAL_EVIDENCE_WHITESPACE_EXCEPTIONS',
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'review_bindings': 4718,
    'independent_review_verdict': 'REJECTED',
    'scientific_source_tests_unchanged': True,
    'staged_files': len(paths), 'staged_json_parsed': len(json_paths),
    'raw_whitespace_exit_code': p.returncode,
    'exceptions': [
        {'path': snapshot, 'line': 117, 'reason': 'Exact original data snapshot and a9efac4 Git bytes; preserve historical source.', 'sha256': digest(snapshot)},
        {'path': stderr, 'line': 23, 'reason': 'Exact native diagnostic failure stderr, bound by original execution and independent review; preserve raw traceback.', 'sha256': digest(stderr)}
    ],
    'unexpected_whitespace_findings': 0,
    'original_hash_verified_parent_raw_log_exclusions': parent_raw_exclusions,
    'feature_go': False, 'new_physical_steps': 0, 'new_generator_ticks': 0
}, ensure_ascii=False, indent=2))
