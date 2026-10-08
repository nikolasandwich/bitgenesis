"""逐字节独立复核作者证据、冻结源码和旧生产审查，不运行任何科学计算。"""
import json,hashlib,re,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as inputs
base=Path('docs/research/results/v4-study-047-verifier-implementation');out=Path(__file__).parent
start=time.monotonic(); manifest=inputs.read(base/'final-validation.json')
def verify(mapping):
 for name,h in mapping.items():
  assert inputs.digest(name)==h,name
verify(manifest['evidence_files_sha256']);verify(manifest['files_sha256']);verify(manifest['own_files_sha256'])
inputs.same(manifest['files_sha256'],manifest['files_sha256_after'],'作者来源前后')
producer=inputs.approved_gate(inputs.BASE+'producer-review.json','2.1',inputs.NEW_CODE)
executions=[]
for declared in manifest['executions']:
 directory=base/declared['epoch']; execution=inputs.read(directory/'execution.json')
 for key in ('command','exit_code','files_sha256','raw_output_sha256','wall_seconds'):
  inputs.same(execution[key],declared[key],'执行清单/'+key)
 for name,h in execution['raw_output_sha256'].items():assert inputs.digest(directory/name)==h
 for name,h in execution['files_sha256'].items():assert inputs.digest(directory/Path(name).name)==h
 stderr=(directory/'stderr.bin').read_text(errors='replace');stdout=(directory/'stdout.bin').read_text(errors='replace')
 count=re.search(r'Ran (\d+) tests? in ([\d.]+)s',stderr)
 executions.append({'epoch':declared['epoch'],'exit_code':execution['exit_code'],'current_code':execution['files_sha256']==manifest['own_files_sha256'],'tests':int(count[1]) if count else None,'seconds':float(count[2]) if count else None,'summary':stderr[-600:],'raw_output_sha256':execution['raw_output_sha256']})
full=next(e for e in executions if e['epoch']=='final-full');assert full['current_code'] and full['exit_code']==0 and full['tests']==1058 and full['summary'].rstrip().endswith('OK')
assert all(e['exit_code']!=0 for e in executions if e['epoch'].startswith('red-'))
actual_evidence={str(p):inputs.digest(p) for p in base.rglob('*') if p.is_file()}
result={'status':'PASS','author_bound_evidence_count':len(manifest['evidence_files_sha256']),'author_total_files':len(actual_evidence),'author_current_source_count':len(manifest['files_sha256']),'producer_review_binding_count':len(producer['files_sha256']),'producer_review_sha256':inputs.digest(inputs.BASE+'producer-review.json'),'executions':executions,'all_author_evidence_sha256':actual_evidence,'elapsed_seconds':time.monotonic()-start}
(out/'author-evidence-check.json').write_text(inputs.canonical(result)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('executions','all_author_evidence_sha256')}))
for e in executions: print(e['epoch'],e['exit_code'],e['tests'],e['current_code'],e['summary'][-180:])
