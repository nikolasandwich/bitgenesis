"""记录合成预算缩放诊断、当前测试及不可恢复的旧联合失败证据限制。"""
import hashlib
import json
from pathlib import Path
from scripts import middle_withdrawal_inputs as inputs

base=Path(__file__).resolve().parent
root=inputs.ROOT
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
previous=read(base/'final-validation.json')
report=dict(previous)
report['supersedes_local_validation']='final-validation.json'
report['scope']='生产2.1预检控制修复及等比例合成测试校准；待父层统一回归与独立审查，不是工程/正式或FEATURE_GO'
for label in ('scaled-targeted','scaled-portable','scaled-compile','budget-diagnosis'):
    record=read(base/label/'execution.json')
    assert record['exit_code']==0 and record['source_unchanged']
    report['executions'][label]={k:v for k,v in record.items() if k!='evidence_sha256'}
report['code_sha256']={name:sha(root/name) for name in previous['code_sha256']}
assert report['code_sha256']==report['executions']['scaled-targeted']['source_after']
assert report['code_sha256']['scripts/run_v4_middle_withdrawal.py']==previous['code_sha256']['scripts/run_v4_middle_withdrawal.py']
closure=inputs.bindings(include_verifier=False)
assert closure==read(base/'source-closure-check.json')['files_sha256']
report['source_closure']['current_test_snapshot']='scaled-targeted/source-after/tests/test_v4_middle_withdrawal.py'
report['source_closure']['current_bindings_rechecked']=True
report['test_budget_calibration']=dict(
    production_total_seconds=600, production_work_seconds=570, production_closing_seconds=30,
    previous_test_total_seconds=.3, previous_test_closing_seconds=.03,
    calibrated_test_total_seconds=2.0, calibrated_test_closing_seconds=.2,
    original_blocking_sleep_seconds=.75, calibrated_blocking_sleep_seconds=5.0,
    calibration_changes='仅4项新增POSIX测试同比放大总限、阻塞与时间断言；首异常、完整metadata/failure、Git门槛、绝对deadline和0科学要求保持。',
    diagnosis='budget-diagnosis/diagnosis.json',
    observed='原.3s给写入约3.50–4.71ms，添加6ms每写等待时metadata failed但failure缺失；同源码2s给32–72ms，1.866s内两证据均failed。')
full=root/'docs/research/results/v4-study-047-preflight-joint-validation/full'
report['prior_joint_failure']=dict(tests=1070, errors=2,
    producer_failure='test_ordinary_blocking_approval_read_is_bounded_and_retained: failure.json缺失；metadata可读且failed。',
    evidence_sha256={str(p.relative_to(root)):sha(p) for p in (full/'execution.json',full/'stdout.bin',full/'stderr.bin')},
    producer_temporary_epoch_preserved=False,
    limitation='父执行器未设置STUDY047_PREFLIGHT_EVIDENCE，该失败Producer临时目录已cleanup，只有原trace、stdout/stderr、源码快照；不可声称该失败epoch已保全。',
    inference='原联合失败缺少临时metadata，无法还原其精确调度；受控6ms延迟实验复现同症状并定位毫秒级合成时间片的敏感性。')
observed={}
for name in previous['preflight_timeout_observations']:
    p=root/'data/v4-study-047-implementation-evidence/producer-preflight/scaled-targeted/failure-epochs'/name/'repository/run/metadata.json'
    meta=read(p)
    observed[name]={key:meta[key] for key in ('status','stage','error','elapsed_seconds','time_limit_seconds','physical_steps','future_generator_ticks')}
    assert meta['status']=='failed' and meta['elapsed_seconds']<2
report['preflight_timeout_observations']=observed
report['synthetic_counts'].update(physical_steps_all_local_runs=330,future_ticks_all_local_runs=495)
archive=read(base/'archive-map-scaled.json')
assert sha(root/archive['archive'])==archive['archive_sha256']
report.update(archive=archive['archive'],archive_sha256=archive['archive_sha256'],
              archive_member_map='archive-map-scaled.json',restored_files=archive['extracted_files_verified'],
              previous_archive_map='archive-map.json',
              raw_directory_current_dependency=False, docs_nested_git_directories=len(list(base.rglob('.git'))))
assert report['docs_nested_git_directories']==0
assert not (root/'data/v4-study-047').exists()
report['evidence_files_sha256']={str(p.relative_to(root)):sha(p) for p in base.rglob('*') if p.is_file()}
with (base/'final-validation-scaled.json').open('x') as stream:
    json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status=report['status'],code_sha256=report['code_sha256'],
                     include_verifier=False, bindings=len(closure), observations=observed),ensure_ascii=False))
