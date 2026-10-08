"""父层统一同版验证：独占原始日志和源码快照，不运行研究入口。"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,tarfile,tempfile
base=Path(__file__).resolve().parent
label=sys.argv[1];command=sys.argv[2:];out=base/label;out.mkdir(exist_ok=False)
files=['scripts/middle_withdrawal_inputs.py','scripts/run_v4_middle_withdrawal.py','scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']
def hashes():return {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in files}
before=hashes()
for n in files:(out/Path(n).name).write_bytes(Path(n).read_bytes())
env=dict(os.environ,PYTHONPATH='src',STUDY047_VERIFIER_TEST_EVIDENCE=str(out/'runtime-epochs'),STUDY047_PREFLIGHT_EVIDENCE=str(out/'producer-runtime-epochs'))
start=time.monotonic()
with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
 result=subprocess.run(command,env=env,stdout=stdout,stderr=stderr)
after=hashes()
record=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,files_sha256=before,files_sha256_after=after,environment={'PYTHONPATH':'src','STUDY047_VERIFIER_TEST_EVIDENCE':str(out/'runtime-epochs'),'STUDY047_PREFLIGHT_EVIDENCE':str(out/'producer-runtime-epochs')},raw_output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.bin')})
raw=out/'producer-runtime-epochs'
if raw.exists():
    def inventory(root):return {str(p.relative_to(root)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in root.rglob('*') if p.is_file()}
    originals=inventory(raw); archive=out/'producer-runtime-epochs.tar.gz'
    with tarfile.open(archive,'x:gz') as bundle:bundle.add(raw,arcname='producer-runtime-epochs')
    with tempfile.TemporaryDirectory() as temporary:
        with tarfile.open(archive) as bundle:bundle.extractall(temporary,filter='data')
        assert inventory(Path(temporary)/'producer-runtime-epochs')==originals
    destination=Path('data/v4-study-047-implementation-evidence/joint-validation')/label
    assert subprocess.run(['git','check-ignore','-q',str(destination)]).returncode==0
    destination.parent.mkdir(parents=True,exist_ok=True);assert not destination.exists()
    raw.rename(destination)
    preservation={'archive':str(archive.relative_to(Path.cwd())),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'former_root':str(raw.relative_to(Path.cwd())),'preserved_local_root':str(destination),'files':originals,'byte_restore_verified':True,'scope':'仅合成临时Git与错误epoch；不是Study047真实未来轨迹。'}
    (out/'producer-runtime-preservation.json').write_text(json.dumps(preservation,ensure_ascii=False,indent=2)+'\n')
(out/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False));print((out/'stdout.bin').read_text(errors='replace'));print('\n'.join((out/'stderr.bin').read_text(errors='replace').splitlines()[-10:]))
assert before==after,'source changed during verification'
sys.exit(result.returncode)
