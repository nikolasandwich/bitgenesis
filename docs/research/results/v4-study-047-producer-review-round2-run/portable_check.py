import signal,sys,types,unittest
portable=types.ModuleType("signal")
for name,value in vars(signal).items():
    if name not in ("SIGALRM","ITIMER_REAL","setitimer","getitimer"):
        setattr(portable,name,value)
sys.modules["signal"]=portable
suite=unittest.defaultTestLoader.discover("tests",pattern="test_v4_middle_withdrawal.py")
result=unittest.TextTestRunner(verbosity=2).run(suite)
print("Independent missing-POSIX-API simulation; not native Windows execution.")
sys.exit(not result.wasSuccessful())
