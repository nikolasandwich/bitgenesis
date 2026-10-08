"""R1控制面缺POSIX能力模拟；不声称原生Windows或运行科学。"""
import signal
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
for name in ('SIGALRM','ITIMER_REAL','setitimer','getitimer'):
    if hasattr(signal,name):delattr(signal,name)
loader=unittest.TestLoader()
loader.testNamePatterns=['*PreflightBoundary*','*real_entry_rejects*','*FinalHygiene*']
result=unittest.TextTestRunner(verbosity=2).run(loader.discover('tests',pattern='test_v4_middle_withdrawal_verifier.py'))
raise SystemExit(0 if result.wasSuccessful() else 1)
