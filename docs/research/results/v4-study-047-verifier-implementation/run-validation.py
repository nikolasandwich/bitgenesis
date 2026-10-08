"""仅任务执行证据：逐次独占保存命令、原始输出和源码。"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
base=Path(__file__).resolve().parent
label=sys.argv[1]; command=sys.argv[2:];out=base/label;out.mkdir(exist_ok=False)
files=['scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']
hashes={}
for name in files:
 p=Path(name)
 if p.exists():
  data=p.read_bytes();(out/p.name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
started=time.time();clock=time.monotonic()
with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
 result=subprocess.run(command,stdout=stdout,stderr=stderr,env=dict(os.environ,PYTHONPATH='src',STUDY047_VERIFIER_TEST_EVIDENCE=str(out/'runtime-epochs')))
meta=dict(command=command,environment={'PYTHONPATH':'src','STUDY047_VERIFIER_TEST_EVIDENCE':str(out/'runtime-epochs')},exit_code=result.returncode,started_unix=started,wall_seconds=time.monotonic()-clock,files_sha256=hashes)
meta['raw_output_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.bin')}
(out/'execution.json').write_text(json.dumps(meta,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps(meta));print((out/'stdout.bin').read_text(errors='replace'));print((out/'stderr.bin').read_text(errors='replace'))
sys.exit(result.returncode)
