"""只追加原始执行证据，不修改旧文件。"""
import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path(__file__).parent
files=['scripts/run_v4_middle_withdrawal.py','scripts/middle_withdrawal_inputs.py','tests/test_v4_middle_withdrawal.py','docs/research/results/v4-study-047-producer-review.json']
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={p:digest(p) for p in files}
for p in files:(root/Path(p).name).write_bytes(Path(p).read_bytes())
command=['.venv/bin/python',str(root/'counterexample.py')]
start=time.monotonic()
with (root/'stdout.bin').open('xb') as stdout,(root/'stderr.bin').open('xb') as stderr:
    p=subprocess.run(command,env=dict(os.environ,PYTHONPATH='src'),stdout=stdout,stderr=stderr)
elapsed=time.monotonic()-start
record={'command':command,'environment':{'PYTHONPATH':'src'},'exit_code':p.returncode,'wall_seconds':elapsed,'files_sha256':before,'files_sha256_after':{p:digest(p) for p in files},'raw_output_sha256':{name:digest(root/name) for name in ('stdout.bin','stderr.bin')}}
with (root/'execution.json').open('x') as f:json.dump(record,f,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps(record));print((root/'stdout.bin').read_text());print((root/'stderr.bin').read_text())
