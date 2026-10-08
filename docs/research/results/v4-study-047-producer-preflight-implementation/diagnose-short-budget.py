"""同一源码受控诊断：毫秒收尾窗口与等比例放大的合成预算。"""
import json
import os
from pathlib import Path
import time
from unittest.mock import patch
from tests.test_v4_middle_withdrawal import PreflightLifecycleTests
from scripts import middle_withdrawal_inputs as inputs
from scripts import run_v4_middle_withdrawal as producer

base = Path(os.environ['STUDY047_PREFLIGHT_EVIDENCE'])
read = inputs.read; write = producer.Epoch._write
results = []
for label, seconds in (('short', .3), ('scaled', 2.0)):
    os.environ['STUDY047_PREFLIGHT_EVIDENCE'] = str(base / label)
    fixture = PreflightLifecycleTests('test_ordinary_blocking_approval_read_is_bounded_and_retained')
    def slow_approval(path):
        if Path(path).name == 'producer-review.json': time.sleep(5)
        return read(path)
    writes = []
    def delayed_write(epoch, name, value, **kwargs):
        if epoch.deadline.phase == 'closing':
            writes.append(dict(name=name, remaining=epoch.deadline.cutoff-time.monotonic()))
            time.sleep(.006)
        return write(epoch, name, value, **kwargs)
    with fixture.repository() as root, patch.object(inputs, 'SECONDS', seconds), \
         patch.object(inputs, 'read', side_effect=slow_approval), patch.object(producer.Epoch, '_write', delayed_write):
        started = time.monotonic(); first = None
        try: producer.run('engineering', root / 'run')
        except BaseException as error: first = error
        elapsed = time.monotonic() - started
        disk = {}
        for name in ('metadata.json', 'failure.json'):
            try: disk[name] = read(root / 'run' / name)
            except BaseException as error: disk[name] = dict(read_error=repr(error))
        assert isinstance(first, inputs.DeadlineExpired)
        results.append(dict(label=label,total_seconds=seconds, elapsed_seconds=elapsed,
                            closing_write_delay_seconds=.006, writes=writes,
                            files=disk, propagated_error=repr(first)))
assert any('read_error' in result for result in results[0]['files'].values())
assert all(result['status'] == 'failed' for result in results[1]['files'].values())
with (base.parent / 'diagnosis.json').open('x') as stream:
    json.dump(dict(source_unchanged=True, experiment='每次收尾写入添加6ms等待；预算与阻塞按比例检验，不修改生产600秒',results=results), stream, ensure_ascii=False,indent=2)
print(json.dumps(results, ensure_ascii=False))
