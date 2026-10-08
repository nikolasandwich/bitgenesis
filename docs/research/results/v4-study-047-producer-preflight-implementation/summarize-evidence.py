"""汇总已执行证据；只声明生产预检修复待独立审核。"""
import ast
import hashlib
import json
from pathlib import Path
from scripts import middle_withdrawal_inputs as inputs

base = Path(__file__).resolve().parent
root = inputs.ROOT
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
records = {p.parent.name: read(p) for p in base.glob('*/execution.json')}
for label in ('final-targeted', 'final-portable', 'final-compile', 'final-help', 'final-closure'):
    assert records[label]['exit_code'] == 0 and records[label]['source_unchanged']
assert records['red-off']['exit_code'] == 1
current = {p: sha(root / p) for p in records['final-targeted']['source_after']}
assert current == records['final-targeted']['source_after']
old = root / 'docs/research/results/v4-study-047-producer-preflight-preservation/run_v4_middle_withdrawal.py'
def definitions(path):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name not in ('run', 'Epoch')}
assert definitions(old) == definitions(root / 'scripts/run_v4_middle_withdrawal.py')
closure = read(base / 'source-closure-check.json')
archive = read(base / 'archive-map.json')
assert sha(root / archive['archive']) == archive['archive_sha256']
observed = {}
for name in ('test_ordinary_blocking_process_preflight_is_bounded_and_retained',
             'test_ordinary_blocking_approval_read_is_bounded_and_retained',
             'test_git_status_block_is_bounded_and_failed_epoch_is_retained',
             'test_process_gate_and_closing_share_one_absolute_deadline'):
    path = root / 'data/v4-study-047-implementation-evidence/producer-preflight/final-targeted/failure-epochs' / name / 'repository/run/metadata.json'
    meta = read(path)
    observed[name] = {k:meta[k] for k in ('status','stage','error','elapsed_seconds','time_limit_seconds',
                                       'physical_steps','future_generator_ticks')}
    assert meta['elapsed_seconds'] < .3
assert not (root / 'data/v4-study-047').exists()
report = dict(status='READY_FOR_REVIEW', task='2.1',
    scope='仅Producer启动预检控制边界；独立审查与父层统一验证待进行，不是工程/正式或FEATURE_GO',
    root_cause='process/gates先于Epoch创建和RouteDeadline安装，普通阻塞耗尽同一预算后无失败epoch收尾时间。',
    fix='先独占空目录并安装原deadline；预检置于Epoch.execute的work截止内，预检capture先仅存内存，原始clean Git与审批门槛通过后才写metadata。',
    requirements_checked=['4.1','4.2','4.3'], design_checked=['失败、预算与测试策略','边界承诺','文件结构计划'],
    code_sha256=current, scientific_and_deadline_definitions_unchanged=True,
    feature_flag_protocol=dict(red_off='red-off', green_on='green-on', removed='green-unconditional'),
    red=dict(tests=5, failures=2, errors=3, blocking_process_seconds=.7955614170059562,
             blocking_approval_seconds=.7790421249810606, total_budget_seconds=.3,
             source='red-off/stderr.bin'),
    final_targeted=dict(tests=56, failures=0, errors=0, skipped=0, preserved_temporary_epochs=43),
    final_portable=dict(tests=56, failures=0, errors=0, skipped=10, preserved_temporary_epochs=33,
                        native_windows_execution=False),
    preflight_timeout_observations=observed,
    executions={name:{key:value for key,value in record.items() if key != 'evidence_sha256'}
                for name,record in records.items()},
    source_closure=dict(bindings=closure['bindings'], include_verifier=False,
                        snapshots=len(closure['source_snapshots']), evidence='source-closure-check.json'),
    previous_evidence_unchanged=True, archive=archive['archive'], archive_sha256=archive['archive_sha256'],
    archive_member_map='archive-map.json', restored_files=archive['extracted_files_verified'],
    synthetic_counts=dict(seed=987654, per_producer_suite_physical_steps=66,
                          per_producer_suite_future_ticks=99, physical_steps_all_local_runs=198,
                          future_ticks_all_local_runs=297),
    real_study047_future_generator_ticks=0, real_study047_physical_steps=0,
    data_v4_study047_exists=False, full_suite_executed_locally=False,
    local_validation_scope='完整suite与关联suite由父协调器统一执行；本地仅生产专项、portable、compile/help及只读来源。',
    evidence_files_sha256={str(p.relative_to(root)):sha(p) for p in base.rglob('*') if p.is_file()})
with (base / 'final-validation.json').open('x') as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status=report['status'], current_code=current, source_bindings=closure['bindings'],
                     source_snapshots=len(closure['source_snapshots']), observations=observed),ensure_ascii=False))
