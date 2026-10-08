"""父层统一同版验证：独占原始日志和源码快照，不运行研究入口。"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
base=Path(__file__).resolve().parent
label=sys.argv[1];command=sys.argv[2:];out=base/label;out.mkdir(exist_ok=False)
files=['scripts/middle_withdrawal_inputs.py','scripts/run_v4_middle_withdrawal.py','scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']
def hashes():return {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in files}
before=hashes()
for n in files:(out/Path(n).name).write_bytes(Path(n).read_bytes())
env=dict(os.environ,PYTHONPATH='src',STUDY047_VERIFIER_TEST_EVIDENCE=str(out/'runtime-epochs'))
start=time.monotonic()
with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
 result=subprocess.run(command,env=env,stdout=stdout,stderr=stderr)
after=hashes()
record=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,files_sha256=before,files_sha256_after=after,environment={'PYTHONPATH':'src','STUDY047_VERIFIER_TEST_EVIDENCE':str(out/'runtime-epochs')},raw_output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.bin')})
(out/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False));print((out/'stdout.bin').read_text(errors='replace'));print('\n'.join((out/'stderr.bin').read_text(errors='replace').splitlines()[-10:]))
assert before==after,'source changed during verification'
sys.exit(result.returncode)
