"""审查执行器：追加独占证据，保留原始stdout/stderr与当前源码哈希。"""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
base=Path(__file__).parent
name=sys.argv[1]; command=sys.argv[2:]; out=base/name; out.mkdir()
files=['scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={p:digest(p) for p in files}
for p in files: shutil.copyfile(p,out/Path(p).name)
env=dict(os.environ,PYTHONPATH='src',STUDY047_VERIFIER_TEST_EVIDENCE=str((out/'runtime-epochs').resolve()))
start=time.monotonic();started=time.time()
with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
    p=subprocess.run(command,env=env,stdout=stdout,stderr=stderr)
elapsed=time.monotonic()-start
after={p:digest(p) for p in files}
record={'command':command,'exit_code':p.returncode,'started_unix':started,'wall_seconds':elapsed,'environment':{'PYTHONPATH':'src','STUDY047_VERIFIER_TEST_EVIDENCE':env['STUDY047_VERIFIER_TEST_EVIDENCE']},'files_sha256':before,'files_sha256_after':after,'raw_output_sha256':{p:digest(out/p) for p in ('stdout.bin','stderr.bin')}}
(out/'execution.json').write_text(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(record,sort_keys=True))
print((out/'stdout.bin').read_text(errors='replace')[-1200:]);print((out/'stderr.bin').read_text(errors='replace')[-1500:])
sys.exit(p.returncode)
