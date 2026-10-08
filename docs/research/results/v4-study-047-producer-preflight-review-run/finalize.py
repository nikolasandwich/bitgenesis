"""替换已保全的旧Producer审批；仅批准重新打开的任务2.1。"""
from datetime import datetime,timezone
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as i
HERE=Path(__file__).resolve().parent
oldpath='docs/research/results/v4-study-047-producer-preflight-preservation/v4-study-047-producer-review.json'
old=i.read(oldpath);canonical='docs/research/results/v4-study-047-producer-review.json'
i.same(i.digest(canonical),i.digest(oldpath),'old canonical already preserved')
initial=i.read(HERE/'initial-bindings.json');current,errors,first=i.capture(initial)
assert first is None and not errors;i.same(initial,current,'unchanged reviewed inputs')
# 父层摘要仅已读取参考，不成为后续生产门槛依赖。实际命令/源码快照/原始输出保留。
excluded={'docs/research/results/v4-study-047-preflight-joint-validation/validation-summary.json',canonical,
          'scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py',
          'docs/research/results/v4-study-047-verifier-review.json',
          '.kiro/specs/middle-policy-withdrawal/tasks.md','.kiro/specs/middle-policy-withdrawal/spec.json',
          'LOG.md','docs/research/results/v4-study-047-producer-validation.json','docs/research/v4-study-047-producer.zh-CN.md'}
paths=set(initial)-excluded
paths.update(str(q.relative_to(ROOT)) for q in HERE.rglob('*') if q.is_file() and '__pycache__' not in str(q))
before,errors,first=i.capture(paths);assert first is None and not errors
after,errors,first=i.capture(paths);assert first is None and not errors;i.same(before,after)
assert not set(before)&excluded
assert not any(Path(p).name in ('tasks.md','spec.json','LOG.md') for p in before)
assert set((*i.NEW_CODE,'tests/test_v4_middle_withdrawal.py'))<=set(before)
assert not (ROOT/'data/v4-study-047').exists()
ready=i.read('docs/research/results/v4-study-047-producer-preflight-implementation/review-ready.json')
report=dict(
 verdict='APPROVED',task='2.1',independent_author_review=True,
 author='/root/withdrawal_producer_preflight',original_author='/root/withdrawal_producer',reviewer='/root/withdrawal_producer_review',
 review_scope='重新打开的Producer2.1预检修复及相关回归；不审批独立核验器或真实研究阶段。',
 created_at_utc=datetime.now(timezone.utc).isoformat(),language='zh-CN',
 files_sha256=before,files_sha256_after=after,code_sha256=ready['producer_code_sha256'],
 binding_counts=dict(current_source_closure=1191,method_closure=1188,previous_approval=1321,initial_reviewed_evidence=1964,approval_total=len(before)),
 binding_policy='绑定当前Producer/input/test及不可变执行/归档/历史证据；Verifier仅绑定实际回归时冻结副本，不绑定live源码或未来审批。排除tasks/spec/LOG、当前父完成报告与canonical自身。已移动临时Git通过tar及逐成员manifest绑定。',
 previous_approval=dict(path=oldpath,sha256=i.digest(oldpath),status='preserved_superseded_after_preflight_reopen',
   source_mapping='docs/research/results/v4-study-047-producer-preflight-preservation/preservation.json',all_1321_bindings_verified=True),
 source_chain={p:i.digest(p) for p in (i.SOURCES,i.CENSUS,i.REVIEW)},
 reviewed_change='只修改Epoch/run的预检生命周期及其合成测试。独占空目录后安装原deadline；预检在Epoch.execute.work内执行；干净Git门槛前仅内存保存输入hash，门槛通过后才写metadata。科学内核/环境/窗口/指标/600秒总限均未改变。',
 mechanical_results=dict(
  canonical_tests=dict(status='PASS',count=1070,exit_code=0,internal_seconds=77.334,wall_seconds=77.7735480000265,
   command='PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v',
   evidence='docs/research/results/v4-study-047-preflight-joint-validation/full-revalidated/execution.json',
   raw='docs/research/results/v4-study-047-preflight-joint-validation/full-revalidated/stderr.bin',
   exact_five_source_before_after_and_frozen_copies_verified=True,full_suite_rerun_by_reviewer=False),
  producer_targeted=dict(status='PASS',count=56,exit_code=0,source_hash_match=True),
  portable=dict(status='PASS',count=56,skipped=10,exit_code=0,native_windows_execution=False),
  independent_checks=dict(status='PASS',exit_code=0,
   evidence='docs/research/results/v4-study-047-producer-preflight-review-run/observations.json',
   command='PYTHONPATH=src .venv/bin/python docs/research/results/v4-study-047-producer-preflight-review-run/checks2.py'),
  red_phase='VERIFIED：预检5项RED为2fail/3error，flag ON后5PASS，最终删除开关并无条件启用修复。',
  compile_and_help='PASS：当前版本原始退出码0及源码快照核实。',placeholders='CLEAN',secrets='CLEAN',diff_check='PASS',
  boundary='WITHIN：父层任务状态与并行Verifier改动识别为其他责任域，本审查未改动或批准它们。',boundary_audit='CLEAN'),
 independent_counterexamples=[
  dict(case='5秒普通进程预检阻塞',budget_seconds=2.0,elapsed_seconds=1.8145676660351455,result='DeadlineExpired，metadata与failure均failed，8项来源before/after相同。'),
  dict(case='5秒普通审批读取阻塞',budget_seconds=2.0,elapsed_seconds=1.8408989170566201,result='DeadlineExpired，metadata与failure均failed，8项来源before/after相同。'),
  dict(case='5秒最早Git revision阻塞',budget_seconds=2.0,elapsed_seconds=1.8167606659699231,result='DeadlineExpired，metadata与failure均failed；尚未读取来源因此来源数0，不伪造hash。'),
  dict(case='真实clean Git门槛',result='空独占目录没有把运行自身变脏；审批通过后在source closure之前主动停止，正确保存失败，无科学调用。'),
  dict(case='审批首KeyboardInterrupt与晚SystemExit',result='原首异常对象传播，metadata/failure保留首异常，晚output hash异常单列。')],
 scaled_test_assessment=dict(result='ACCEPTED',production_total_seconds=600,production_work_seconds=570,production_closing_seconds=30,
  synthetic_before_seconds=0.3,synthetic_after_seconds=2.0,blocking_before_seconds=0.75,blocking_after_seconds=5.0,
  rationale='只同比放大4项计时测试的总限/阻塞，保留原异常、两个失败文件、真实Git、同一绝对deadline及0科学断言。受控每写6ms试验显示原30ms总收尾余量不足，200ms收尾可保存完整失败证据；生产预算与源不因校准改变。',
  qualification='原联合失败的临时Producer目录已经清理，无法逐字节还原其精确调度；6ms实验是同症状受控解释而非恢复原事故。原trace、stdout/stderr和源快照保留，不能称原失败epoch完整保全。'),
 archive_integrity=dict(local_first_members=2193,local_scaled_members=1595,joint_producer_epoch_members=342,
  actual_member_sha256_checked=True,reviewer_fixture_archives=5,reviewer_fixture_archive_members=190,
  moved_raw_directories_required_by_approval=False),
 findings=[dict(severity='FYI',text='原联合失败含2errors，原始日志未替换；其Producer临时epoch未保全是明确历史证据限制。当前同版1070项通过及新失败epoch归档单独构成完成证据。'),
           dict(severity='FYI',text='可移植性检查模拟缺POSIXAPI，未执行原生Windows；OS不可中断I/O或持久存储故障仍可能阻止最佳努力证据写入，不能据此宣称成功。'),
           dict(severity='FYI',text='独立复审脚本首次误把joint tar的根前缀/manifest值类型视为直接映射，停于只读归档校验；原exit1日志保留。修正审查脚本映射后全检查exit0，未修改被审实现。')],
 requirement_assessment=dict(old['requirement_assessment'],**{'4.2':'PASS：本次新增普通预检阻塞、早期Git、审批异常和后续收尾反例均在同一绝对deadline下保留失败epoch与首异常；科学字段和固定窗口不变。'}),
 design_assessment=dict(file_structure='PASS',continuous_state='UNCHANGED_PASS',metrics_and_ledgers='UNCHANGED_PASS',failure_and_budget='PASS：预检纳入原Epoch有界工作与失败收尾。'),
 scope=dict(real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0,
  reviewer_synthetic_physical_steps=0,reviewer_synthetic_future_generator_ticks=0,
  scientific_entries_called_by_reviewer=0,verifier_approved=False,engineering_or_formal_run=False,feature_go=False,
  source_task_spec_LOG_or_old_data_modified_by_reviewer=False,committed_by_reviewer=False),
 verification=dict(status='VERIFIED',claim_type='TASK',task='2.1',claim='重新打开的Producer预检缺口已修复，完整生产实现和相关边界测试可接受',unresolved_blocking_findings=0),
 summary='任务2.1重新批准：预检已进入原计时与失败epoch生命周期，真实Git门槛保持；当前同版回归和独立反例通过，真实未来仍为0。')
# 原canonical与1321绑定已保全并已在本轮验证；按父授权替换唯一当前gate。
with (ROOT/canonical).open('w',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
i.approved_gate(canonical,'2.1',(*i.NEW_CODE,'tests/test_v4_middle_withdrawal.py'))
print(json.dumps(dict(verdict='APPROVED',task='2.1',approval_bindings=len(before),gate_self_check='PASS',real_future_physical_steps=0,real_future_ticks=0,canonical_sha256=i.digest(canonical)),ensure_ascii=False))
