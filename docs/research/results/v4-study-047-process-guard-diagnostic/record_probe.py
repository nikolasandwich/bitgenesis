"""独占保存诊断输入、完整受跟踪来源hash、原始stdout/stderr和退出值。"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path('/Users/todd/Documents/bitgenesis')
OUT = Path(__file__).resolve().parent


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def command(name, args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True)
    for suffix, data in [('stdout.bin', result.stdout), ('stderr.bin', result.stderr)]:
        with (OUT / f'{name}.{suffix}').open('xb') as stream:
            stream.write(data)
    write(name + '.execution.json', dict(argv=args, exit_code=result.returncode))
    if result.returncode:
        raise RuntimeError(f'{name} exit {result.returncode}')
    return result.stdout


started = time.monotonic()
git_before = command('git-status-before', ['git', 'status', '--porcelain=v1']).decode()
commit = command('git-head', ['git', 'rev-parse', 'HEAD']).decode().strip()
tracked = command('git-ls-files', ['git', 'ls-files', '-z']).decode().split('\0')
paths = sorted(p for p in tracked if p and (ROOT / p).is_file())
before = {p: digest(ROOT / p) for p in paths}
write('tracked-source-hashes-before.json', before)
snapshots = [
    'AGENTS.md', 'pyproject.toml', '.agents/skills/kiro-debug/SKILL.md',
    '.agents/skills/kiro-discovery/SKILL.md',
    '.kiro/specs/middle-policy-withdrawal/requirements.md',
    '.kiro/specs/middle-policy-withdrawal/design.md',
    '.kiro/specs/middle-policy-withdrawal/tasks.md',
    '.kiro/specs/middle-policy-withdrawal/spec.json',
    'experiments/v4/study-047.md', 'scripts/middle_withdrawal_inputs.py',
    'scripts/run_v4_middle_withdrawal.py', 'scripts/verify_v4_middle_withdrawal.py',
    'tests/test_v4_middle_withdrawal.py', 'tests/test_v4_middle_withdrawal_verifier.py',
    'docs/research/results/v4-study-047-producer-review.json',
    'docs/research/results/v4-study-047-verifier-review.json',
    'docs/research/results/v4-study-047-engineering-review.json',
    'docs/research/results/v4-study-047-design-review.json',
    'docs/research/results/v4-study-047-engineering/raw/execution_runner.py',
    'data/v4-study-047/execution_runner.py',
    'data/v4-study-047-parent-preflight-observation.json',
    'data/v4-study-047/process-supplement-during-verifier.json',
    'data/v4-study-047/producer/metadata.json', 'data/v4-study-047/verifier/metadata.json',
    'data/v4-study-047/execution/producer/request.json', 'data/v4-study-047/execution/producer/result.json',
    'data/v4-study-047/execution/verifier/request.json', 'data/v4-study-047/execution/verifier/result.json',
]
snapshot_hashes = {}
for name in snapshots:
    path = OUT / 'input-snapshots' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((ROOT / name).read_bytes())
    snapshot_hashes[name] = digest(path)
write('input-snapshot-hashes.json', snapshot_hashes)
argv = [str(ROOT / '.venv/bin/python'), '-B', str(OUT / 'probe.py')]
environment = {key: os.environ[key] for key in ('PATH', 'HOME', 'TMPDIR', 'LANG') if key in os.environ}
environment.update(PYTHONPATH=str(ROOT / 'src'), PYTHONDONTWRITEBYTECODE='1')
write('probe-request.json', dict(argv=argv, cwd=str(ROOT), environment=environment,
                               environment_is_complete=True, commit=commit,
                               git_status_before=git_before,
                               started_at_utc=datetime.now(timezone.utc).isoformat(),
                               scripts_sha256={name:digest(OUT / name) for name in ('probe.py','record_probe.py')}))
error = None
try:
    with (OUT / 'probe.stdout.bin').open('xb') as stdout, (OUT / 'probe.stderr.bin').open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr)
    exit_code = result.returncode
except BaseException:
    error = traceback.format_exc()
    exit_code = None
finally:
    after = {p: digest(ROOT / p) if (ROOT / p).is_file() else None for p in paths}
    write('tracked-source-hashes-after.json', after)
    snapshots_after = {p:digest(ROOT / p) for p in snapshots}
    write('input-source-hashes-after.json', snapshots_after)
    git_after = command('git-status-after', ['git', 'status', '--porcelain=v1']).decode()
    summary = dict(exit_code=exit_code, wrapper_error=error, wall_seconds=time.monotonic()-started,
                   finished_at_utc=datetime.now(timezone.utc).isoformat(),
                   tracked_file_count=len(before), tracked_sources_unchanged=before==after,
                   input_snapshots_unchanged=snapshot_hashes==snapshots_after,
                   changed_tracked_paths=[p for p in paths if before[p]!=after[p]],
                   git_status_after=git_after,
                   raw_output_sha256={name:digest(OUT / name) for name in ('probe.stdout.bin','probe.stderr.bin')})
    write('probe-execution.json', summary)
    print(json.dumps(summary, ensure_ascii=False))
    print((OUT / 'probe.stdout.bin').read_text())
    if error:
        print(error, file=sys.stderr)
    print((OUT / 'probe.stderr.bin').read_text(), file=sys.stderr)
