"""保存本轮全部临时测试输出，再执行生产专项或缺POSIX接口模拟。"""
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import types
import unittest

base = Path(os.environ['STUDY047_PREFLIGHT_EVIDENCE']).parent / 'all-test-temporary-epochs'
original = tempfile.TemporaryDirectory
count = 0
class RetainedTemporaryDirectory(original):
    def cleanup(self):
        global count
        if not getattr(self, '_retained', False) and Path(self.name).exists():
            self._retained = True
            count += 1
            target = base / ('epoch-%03d' % count)
            shutil.copytree(self.name, target)
        super().cleanup()
tempfile.TemporaryDirectory = RetainedTemporaryDirectory
if '--portable' in sys.argv:
    portable = types.ModuleType('signal')
    for name, value in vars(signal).items():
        if name not in ('SIGALRM', 'ITIMER_REAL', 'setitimer', 'getitimer'):
            setattr(portable, name, value)
    sys.modules['signal'] = portable
suite = unittest.defaultTestLoader.discover('tests', pattern='test_v4_middle_withdrawal.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps(dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                      skipped=len(result.skipped), preserved_temporary_epochs=count,
                      native_windows_execution=False, missing_posix_simulation='--portable' in sys.argv)))
sys.exit(not result.wasSuccessful())
