"""复审：核实当前来源、旧版保全、同版原始执行及科学AST不变。"""
import ast,json,re,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as i
root=Path(__file__).parent;start=time.monotonic()
author_path=Path(i.BASE+'verifier-implementation/final-validation-remediated.json')
a=i.read(author_path)
assert i.digest(author_path)=='c5abaf81192473cc34199af27d5ae8983ba3cc79deeefe36097db42c8fc491aa'
def verify(mapping):
 for p,h in mapping.items():assert i.digest(p)==h,p
verify(a['files_sha256']);verify(a['evidence_files_sha256']);verify(a['own_files_sha256']);i.same(a['files_sha256'],a['files_sha256_after'],'当前作者来源前后')
gate=i.approved_gate(i.BASE+'producer-review.json','2.1',i.NEW_CODE)
assert i.digest(i.BASE+'producer-review.json')=='74ac9792ea57ae793665a610649adc790cf39f0a858c8908978b7d8d86828754'
old_author=i.read(i.BASE+'verifier-implementation/final-validation.json');verify(old_author['evidence_files_sha256'])
original=i.read(i.BASE+'verifier-review-initial.json')
assert i.digest(i.BASE+'verifier-review-initial.json')=='94e47c7e92adf8f79f6926ec6644ea02f50c71c70c7f4adbdd3d516099518316'
preservation=i.read(i.BASE+'producer-preflight-preservation/preservation.json')['sources']
mapping={p:v['archive'] for p,v in preservation.items()}
mapping.update({'scripts/verify_v4_middle_withdrawal.py':i.BASE+'verifier-implementation/rejected-epoch-1/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py':i.BASE+'verifier-implementation/rejected-epoch-1/test_v4_middle_withdrawal_verifier.py'})
for p,h in original['files_sha256'].items():assert i.digest(mapping.get(p,p))==h,p
old_producer=i.read(mapping[i.BASE+'producer-review.json'])
for p,h in old_producer['files_sha256'].items():assert i.digest(mapping.get(p,p))==h,p
ast_results={}
for name in ('scripts/run_v4_middle_withdrawal.py','scripts/verify_v4_middle_withdrawal.py'):
 def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(p).read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
 before=nodes(mapping[name]);after=nodes(name);assert before.keys()==after.keys()
 changes=[k for k in before if before[k]!=after[k]];assert changes==['Epoch','run'],changes
 ast_results[name]={'changed_definitions':changes,'all_scientific_definitions_unchanged':True}
executions=[]
for dirname in ('full-revalidated','compile-revalidated','full'):
 p=Path(i.BASE+'preflight-joint-validation')/dirname;e=i.read(p/'execution.json')
 for n,h in e['raw_output_sha256'].items():assert i.digest(p/n)==h
 for n,h in e['files_sha256'].items():assert i.digest(p/Path(n).name)==h
 i.same(e['files_sha256'],e['files_sha256_after'],'完整回归源码前后')
 current=all(i.digest(n)==h for n,h in e['files_sha256'].items())
 stderr=(p/'stderr.bin').read_text();m=re.search(r'Ran (\d+) tests in ([\d.]+)s',stderr)
 executions.append({'name':dirname,'exit_code':e['exit_code'],'current_five_source_files':current,'tests':int(m[1]) if m else None,'seconds':float(m[2]) if m else None,'wall_seconds':e['wall_seconds'],'raw_output_sha256':e['raw_output_sha256'],'summary':stderr[-150:]})
full=executions[0];assert full['current_five_source_files'] and full['exit_code']==0 and full['tests']==1070 and full['summary'].rstrip().endswith('OK')
assert executions[1]['exit_code']==0 and executions[1]['current_five_source_files']
assert executions[2]['exit_code']==1 and executions[2]['tests']==1070
source=Path('scripts/verify_v4_middle_withdrawal.py').read_text();test=Path('tests/test_v4_middle_withdrawal_verifier.py').read_text()
for s in (source,test):
 assert not re.search(r'\b(?:TBD|TODO|FIXME|HACK|XXX)\b',s)
 assert not re.search(r'(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,})',s)
 assert all(x.rstrip()==x for x in s.splitlines()) and s.endswith('\n')
result={'status':'PASS','current_source_bindings':len(a['files_sha256']),'current_author_evidence':len(a['evidence_files_sha256']),'current_producer_approval_bindings':len(gate['files_sha256']),'old_author_evidence':len(old_author['evidence_files_sha256']),'initial_rejection_bindings_preserved':len(original['files_sha256']),'old_producer_bindings_preserved':len(old_producer['files_sha256']),'archive_source_mapping':mapping,'science_ast':ast_results,'executions':executions,'static_check':'PASS','elapsed_seconds':time.monotonic()-start,'real_future_ticks':0,'real_physical_steps':0}
(root/'evidence-check.json').write_text(i.canonical(result)+'\n')
print(i.canonical(result))
