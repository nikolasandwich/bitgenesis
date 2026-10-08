"""Read-only source/approval validation; writes only new author evidence files."""
from pathlib import Path
import ast
import hashlib
import json
import sys
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as inputs
base=Path('docs/research/results/v4-study-047-verifier-implementation')
joint=Path('docs/research/results/v4-study-047-preflight-joint-validation')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,value):
    with (base/name).open('x') as stream:json.dump(value,stream,sort_keys=True,ensure_ascii=False,indent=2);stream.write('\n')
before=inputs.bindings(include_verifier=True)
assert len(before)==1192
save('remediation-sources-before.json',before)
gate_path=inputs.BASE+'producer-review.json'
assert digest(gate_path)=='74ac9792ea57ae793665a610649adc790cf39f0a858c8908978b7d8d86828754'
gate=inputs.approved_gate(gate_path,'2.1',inputs.NEW_CODE)
assert len(gate['files_sha256'])==1985
old=json.loads((base/'final-validation.json').read_text())
for name,h in old['evidence_files_sha256'].items():assert digest(name)==h,name
preserved=json.loads((base/'rejected-epoch-1/preservation.json').read_text())
assert digest(preserved['review'])==preserved['review_sha256']
for item in preserved['sources'].values():assert digest(item['archive'])==item['sha256']
archive=Path('docs/research/results/v4-study-047-producer-preflight-preservation')
mapping=json.loads((archive/'preservation.json').read_text())['sources']
for item in mapping.values():assert digest(item['archive'])==item['sha256']
oldgate=json.loads((archive/'v4-study-047-producer-review.json').read_text())
assert oldgate['files_sha256']==oldgate['files_sha256_after']
for name,h in oldgate['files_sha256'].items():assert digest(mapping[name]['archive'] if name in mapping else name)==h,name
assert len(oldgate['files_sha256'])==1321
executions=[]
for root in [*sorted(base.glob('remediation-1-*/execution.json')),*sorted(joint.glob('*/execution.json'))]:
    value=json.loads(root.read_text())
    for name,h in value['raw_output_sha256'].items():assert digest(root.parent/name)==h,str(root.parent/name)
    for name,h in value['files_sha256'].items():assert digest(root.parent/Path(name).name)==h,str(root.parent/Path(name).name)
    if 'files_sha256_after' in value:assert value['files_sha256']==value['files_sha256_after']
    executions.append(str(root))
current=json.loads((joint/'full-revalidated/execution.json').read_text())
assert current['exit_code']==0
for name,h in current['files_sha256'].items():assert digest(name)==h,name
science={}
for name,archived in [('scripts/verify_v4_middle_withdrawal.py',base/'rejected-epoch-1/verify_v4_middle_withdrawal.py'),('scripts/run_v4_middle_withdrawal.py',archive/'run_v4_middle_withdrawal.py')]:
    def definitions(path):
        return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(Path(path).read_text()).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    olddef,newdef=definitions(archived),definitions(name)
    changed=sorted(k for k in olddef.keys()|newdef.keys() if olddef.get(k)!=newdef.get(k))
    assert changed==['Epoch','run'],changed
    science[name]={'changed_top_level_definitions':changed,'all_other_scientific_definitions_unchanged':True}
after=inputs.bindings(include_verifier=True)
assert before==after
assert not Path('data/v4-study-047').exists()
save('remediation-sources-after.json',after)
result=dict(task='2.2',status='author source closure checked, not independent approval',source_bindings_verified=len(before),producer_review_bindings_verified=len(gate['files_sha256']),producer_review_sha256=digest(gate_path),historical_producer_review_bindings_verified_with_archived_sources=len(oldgate['files_sha256']),historical_verifier_evidence_files_unchanged=len(old['evidence_files_sha256']),execution_receipts_verified=executions,current_full_source_sha256=current['files_sha256'],scientific_boundary=science,real_study047_future_ticks=0,real_study047_physical_steps=0,synthetic_future_ticks=0,synthetic_physical_steps=0)
save('remediation-closure.json',result)
print(json.dumps(result,ensure_ascii=False,sort_keys=True))
