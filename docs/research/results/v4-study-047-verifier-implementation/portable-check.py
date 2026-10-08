"""模拟缺POSIX接口；不声称原生Windows验证。"""
import signal
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
import unittest
for name in ('SIGALRM','ITIMER_REAL','setitimer','getitimer'):
    if hasattr(signal,name): delattr(signal,name)
suite=unittest.defaultTestLoader.discover('tests',pattern='test_v4_middle_withdrawal_verifier.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
