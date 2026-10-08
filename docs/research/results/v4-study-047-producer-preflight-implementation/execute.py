"""独占保存本轮执行命令、源码快照和完整失败epoch；禁止真实047科学运行。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
CODE = ('scripts/middle_withdrawal_inputs.py', 'scripts/run_v4_middle_withdrawal.py', 'tests/test_v4_middle_withdrawal.py')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    label = sys.argv[1]; command = sys.argv[2:]
    target = BASE / label; target.mkdir(exist_ok=False)
    before = {}
    for name in CODE:
        destination = target / 'source-before' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
        before[name] = digest(destination)
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'src') + os.pathsep + str(ROOT),
               STUDY047_PREFLIGHT_EVIDENCE=str(target / 'failure-epochs'))
    started = time.monotonic()
    with (target / 'stdout.bin').open('xb') as stdout, (target / 'stderr.bin').open('xb') as stderr:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
    after = {}
    for name in CODE:
        destination = target / 'source-after' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
        after[name] = digest(destination)
    report = dict(command=command, exit_code=result.returncode, wall_seconds=time.monotonic()-started,
                  source_before=before, source_after=after, source_unchanged=before == after,
                  evidence_sha256={str(p.relative_to(target)):digest(p) for p in target.rglob('*') if p.is_file()},
                  data_v4_study047_exists=(ROOT / 'data/v4-study-047').exists())
    (target / 'execution.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'evidence_sha256'},ensure_ascii=False))
    print((target / 'stderr.bin').read_text()[-5000:])
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
