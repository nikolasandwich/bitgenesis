"""只读核对生产来源闭包与旧证据；保存本轮源码，不包含开发中Verifier。"""
import json
from pathlib import Path
import shutil
import time
from scripts import middle_withdrawal_inputs as inputs

base = Path(__file__).resolve().parent
started = time.monotonic()
before = inputs.bindings(include_verifier=False)
snapshots = {}
for name, expected in before.items():
    source = Path(name)
    if source.suffix == '.py' and not source.is_absolute():
        target = base / 'source-closure' / source
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(source.read_bytes())
        assert inputs.digest(target) == expected
        snapshots[name] = dict(archive=str(target.relative_to(inputs.ROOT)), sha256=expected)
name = 'tests/test_v4_middle_withdrawal.py'
target = base / 'source-closure' / name
target.parent.mkdir(parents=True, exist_ok=True)
if not target.exists():
    with target.open('xb') as stream: stream.write(Path(name).read_bytes())
    snapshots[name] = dict(archive=str(target.relative_to(inputs.ROOT)), sha256=inputs.digest(target))
after = inputs.bindings(include_verifier=False)
assert before == after
preservation = inputs.read(inputs.ROOT / 'docs/research/results/v4-study-047-producer-preflight-preservation/preservation.json')
modified = {'scripts/run_v4_middle_withdrawal.py', 'tests/test_v4_middle_withdrawal.py'}
preserved = {}
for name, entry in preservation['sources'].items():
    assert inputs.digest(inputs.ROOT / entry['archive']) == entry['sha256']
    if name not in modified:
        assert inputs.digest(inputs.ROOT / name) == entry['sha256']
    preserved[name] = entry
previous = inputs.read(inputs.ROOT / 'docs/research/results/v4-study-047-producer-implementation/final-validation-remediated2.json')
old_evidence = previous['prior_evidence_sha256']
for name, expected in old_evidence.items():
    assert inputs.digest(inputs.ROOT / name) == expected, name
assert not (inputs.ROOT / 'data/v4-study-047').exists()
report = dict(status='VERIFIED', scope='生产来源闭包与历史字节；不是任务审批或真实工程/正式科学执行',
              include_verifier=False, bindings=len(before), files_sha256=before, files_sha256_after=after,
              source_snapshots=snapshots, previous_preservation=preserved,
              previous_evidence_sha256=old_evidence, previous_evidence_unchanged=True,
              runtime=inputs.runtime(), wall_seconds=time.monotonic()-started,
              real_study047_future_generator_ticks=0, real_study047_physical_steps=0,
              data_v4_study047_exists=False)
with (base / 'source-closure-check.json').open('x') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps(dict(status=report['status'], bindings=len(before), snapshots=len(snapshots),
                     previous_evidence=len(old_evidence), wall_seconds=report['wall_seconds'], include_verifier=False)))
