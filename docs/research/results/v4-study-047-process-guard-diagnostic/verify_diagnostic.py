"""最终只读核对诊断证据和来源，不运行研究或修改其它目录。"""
from datetime import datetime, timezone
import hashlib, json, platform, re, subprocess, sys
from pathlib import Path
ROOT=Path('/Users/todd/Documents/bitgenesis')
OUT=Path(__file__).resolve().parent
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def write(name,obj):
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
latest=OUT/'epoch-3'
before=json.loads((latest/'tracked-source-hashes-before.json').read_text())
after=json.loads((latest/'tracked-source-hashes-after.json').read_text())
assert before==after
current={p:digest(ROOT/p) for p in before};assert current==before
snapshots=json.loads((latest/'input-snapshot-hashes.json').read_text())
assert snapshots==json.loads((latest/'input-source-hashes-after.json').read_text())
for p,h in snapshots.items():
 assert digest(ROOT/p)==digest(latest/'input-snapshots'/p)==h
result=json.loads((latest/'probe-output/results.json').read_text())
assert result['status']=='RED' and len(result['cases'])==74 and result['required_rejections_missed']==36
assert result['forbidden_calls']==[]
for key in ['actual_physics_steps','synthetic_physics_steps','future_generator_ticks','past_generator_ticks','route_cli_invocations','source_mutations']:assert result[key]==0
execution=json.loads((latest/'probe-execution.json').read_text())
assert execution['exit_code']==1 and execution['wrapper_error'] is None
for name,h in execution['raw_output_sha256'].items():assert digest(latest/name)==h
assert (latest/'probe.stderr.bin').read_bytes()==b''
source_hashes={p:before[p] for p in ['scripts/middle_withdrawal_inputs.py','scripts/run_v4_middle_withdrawal.py','scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']}
runtime=[]
for role in ['producer','verifier']:
 meta=json.loads((latest/'input-snapshots'/f'data/v4-study-047/{role}/metadata.json').read_text())
 rt=meta['runtime']
 actual={p:digest(Path(p)) for p in rt['files_sha256']}
 assert actual==rt['files_sha256'] and rt['python_version']==platform.python_version()
 runtime.append(dict(role=role,version=rt['python_version'],implementation=rt['implementation'],expected=rt['files_sha256'],current=actual))
write('runtime-current-equals-formal.json',runtime)
pattern=r'(?:python|pypy)(?:[0-9]+(?:\.[0-9]+)*)?(?:\.exe)?'
assert re.fullmatch(pattern,'python') and not re.fullmatch(pattern,'Python')
assert re.fullmatch(pattern,'Python',flags=re.IGNORECASE)
# 仅对新增诊断源码做内存语法检查，不创建pyc，不运行其内容。
for folder in [OUT,OUT/'epoch-2',OUT/'epoch-3']:
 for name in ['probe.py','record_probe.py']:compile((folder/name).read_bytes(),str(folder/name),'exec')
diff=subprocess.run(['git','diff','--exit-code','--','src','scripts','tests','.kiro','AGENTS.md','experiments/v4/study-047.md'],cwd=ROOT,capture_output=True)
assert diff.returncode==0 and diff.stdout==b'' and diff.stderr==b''
write('diagnostic-summary.json',dict(created_at_utc=datetime.now(timezone.utc).isoformat(),category='LOGIC_ERROR',next_action='RETRY_TASK',confidence='HIGH',effective_epoch='epoch-3',probe_is_red=True,probe_exit_code=1,guard_cases=74,missed_required_rejections=36,wrapper_cases=6,wrapper_misses=4,tracked_files_unchanged=len(before),input_snapshots_unchanged=len(snapshots),source_hashes=source_hashes,formal_commit='a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f',formal_evidence_automatically_invalid=False,complete_or_feature_go=False,independent_formal_review_performed=False,actual_physics_steps=0,synthetic_physics_steps=0,future_generator_ticks=0,past_generator_ticks=0,route_cli_invocations=0))
manifest={}
for p in sorted(OUT.rglob('*')):
 if p.is_file() and p.name not in {'artifact-manifest.json','final-verification.stdout.bin','final-verification.stderr.bin','final-verification.execution.json'}:
  manifest[str(p.relative_to(OUT))]=dict(bytes=p.stat().st_size,sha256=digest(p))
write('artifact-manifest.json',dict(files=manifest,excludes=['artifact-manifest.json','final-verification.stdout.bin','final-verification.stderr.bin','final-verification.execution.json']))
print(json.dumps(dict(status='VERIFIED_DIAGNOSTIC_EVIDENCE',tracked_files_unchanged=len(before),input_snapshots_unchanged=len(snapshots),manifest_files=len(manifest),source_hashes=source_hashes,scope='仅调试证据完整性；guard仍RED；不构成正式科学审查或FEATURE_GO'),ensure_ascii=False))
