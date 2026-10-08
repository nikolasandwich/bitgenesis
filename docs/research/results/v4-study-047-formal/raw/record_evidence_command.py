"""Record one non-scientific audit/archive command without inherited secrets."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
ROOT=Path('/Users/todd/Documents/bitgenesis')
dest=ROOT/sys.argv[1];args=sys.argv[2:];dest.mkdir(parents=True,exist_ok=False)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,obj):
 with (dest/name).open('x') as out:json.dump(obj,out,ensure_ascii=False,indent=2);out.write('\n')
env={k:os.environ[k] for k in ('PATH','HOME','TMPDIR','LANG') if k in os.environ};env['PYTHONPATH']='src'
script=ROOT/args[1];script_before=sha(script)
write('request.json',dict(command=args,cwd=str(ROOT),environment=env,environment_is_complete=True,started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_sha256_before=script_before,scientific_steps=0))
start=time.monotonic()
with (dest/'stdout.bin').open('xb') as stdout,(dest/'stderr.bin').open('xb') as stderr:r=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
record=dict(command=args,exit_code=r.returncode,wall_seconds=time.monotonic()-start,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),script_sha256_after=sha(script),raw_output_sha256={n:sha(dest/n) for n in ['stdout.bin','stderr.bin']},scientific_steps=0)
write('execution.json',record)
assert script_before==record['script_sha256_after']
print(json.dumps(record));print((dest/'stdout.bin').read_text(errors='replace'));print((dest/'stderr.bin').read_text(errors='replace'))
raise SystemExit(r.returncode)
