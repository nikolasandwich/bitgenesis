"""独立批准仅限任务2.1；绑定当前代码/来源/全部不可变执行和审查证据。"""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as i
HERE=Path(__file__).resolve().parent
initial=i.read(HERE/'initial-bindings.json')
current,errors,first=i.capture(initial)
assert first is None and not errors;i.same(initial,current,'unchanged review inputs')
reviewfiles=[str(p.relative_to(ROOT)) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
review_before,errors,first=i.capture(reviewfiles)
assert first is None and not errors
before=dict(initial,**review_before)
after,errors,first=i.capture(before)
assert first is None and not errors;i.same(before,after,'final complete current approval bindings')
assert set((*i.NEW_CODE,'tests/test_v4_middle_withdrawal.py'))<=set(before)
assert not any(Path(p).name in ('tasks.md','spec.json','LOG.md') for p in before)
assert not Path('data/v4-study-047').exists()
assert not Path('scripts/verify_v4_middle_withdrawal.py').exists()
validation=i.read('docs/research/results/v4-study-047-producer-implementation/final-validation-remediated2.json')
report=dict(
 verdict='APPROVED',task='2.1',independent_author_review=True,
 author='/root/withdrawal_producer',reviewer='/root/withdrawal_producer_review',review_round=3,
 created_at_utc=datetime.now(timezone.utc).isoformat(),language='zh-CN',
 claim='任务2.1：完整两臂连续生产实现、来源契约和合成边界测试通过独立审查；不批准任务2.2/2.3/3.1，不表示FEATURE_GO。',
 files_sha256=before,files_sha256_after=after,
 files_sha256_policy='全部为当前可读取字节；旧被拒源码经各epoch归档路径保存并逐项映射验证。排除可变tasks/spec/LOG、未来父层报告及本报告自身。',
 binding_counts=dict(source_closure=1191,approved_method_closure=1188,source_code_history_execution_evidence=len(initial),final_review_evidence=len(review_before),approval_total=len(before)),
 code_sha256=validation['code_sha256'],
 source_chain={p:i.digest(p) for p in (i.SOURCES,i.CENSUS,i.REVIEW)},
 history=[
  dict(review='docs/research/results/v4-study-047-producer-review-initial.json',verdict='REJECTED',bound_inputs=1221,review_evidence=22,
       source_mapping='docs/research/results/v4-study-047-producer-implementation/rejected-epoch-1/preservation.json',current_verification='PASS'),
  dict(review='docs/research/results/v4-study-047-producer-review-round2.json',verdict='REJECTED',bound_inputs=1268,review_evidence=12,
       source_mapping='docs/research/results/v4-study-047-producer-implementation/rejected-epoch-2/preservation.json',current_verification='PASS')],
 mechanical_results=dict(
  tests=dict(status='PASS',canonical_command='PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v',
    canonical_tests=1013,canonical_exit_code=0,canonical_seconds=62.356,canonical_wall_seconds=62.69541275000665,
    canonical_evidence='docs/research/results/v4-study-047-producer-implementation/remediation2-full-suite.stderr.txt',
    same_version_validation='docs/research/results/v4-study-047-producer-implementation/final-validation-remediated2.json',
    independently_rerun_full_suite=False,
    rationale='同版当前3代码与1191来源前后绑定及原始完整输出核实；按当前验证规则不重复已通过的完整suite。',
    targeted_tests=47,targeted_seconds=1.169,targeted_exit_code=0,
    portable_simulation=dict(tests=47,skipped_posix_timer_tests=6,exit_code=0,native_windows_execution=False)),
  independent_adversarial=dict(status='PASS',command='PYTHONPATH=src .venv/bin/python docs/research/results/v4-study-047-producer-review-final-run/checks.py',exit_code=0,
    evidence='docs/research/results/v4-study-047-producer-review-final-run/observations.json'),
  static=dict(status='PASS',compileall_exit_code=0,cli_help_exit_code=0,placeholder_scan='CLEAN',secret_scan='CLEAN',new_file_whitespace='CLEAN'),
  boundary='WITHIN',boundary_audit='CLEAN：共享模块只管来源与类型合同；生产科学与未来独立核验仍分开。',
  red_phase='VERIFIED：原实现RED及两次修复RED均保留；最新47项RED实际2fail/1error，随后相同反例和最终验证通过。'),
 resolved_findings=[
  dict(id='R1',status='RESOLVED',evidence='可移植git/signal故障测试使用适配器；缺少POSIXAPI显式拒绝且无科学调用；当前模拟47项PASS/6具体计时SKIP。'),
  dict(id='R2',status='RESOLVED',evidence='完整Python启动形式解析覆盖-m、额外解释器flags、直接Producer/Verifier脚本；旧独立反例已通过且该实现本轮无变化。'),
  dict(id='R3',status='RESOLVED',evidence='总600秒保留，work最多570秒并预留30秒收尾；独立动作按原绝对deadline的剩余份额重新计时，hash超时标不可用并保留已有hash，所有操作仍受总限。'),
  dict(id='R4',status='RESOLVED',evidence='RNG状态各流独立捕获，失败标checkpoint.failed并保留其他流状态；首异常不被替换。'),
  dict(id='R5',status='RESOLVED',evidence='精确旧反例（无/有先前work异常）均保存metadata.failed及failure.failed；最多2次恢复安装，6次handler调用，首异常和次级恢复异常均保存。真实计时器下所有恢复写入timer有效且原end未延长。')],
 findings=[dict(severity='FYI',text='本审查没有原生Windows执行；实际研究仍限定方法冻结的CPython运行时。跨平台结论仅为明确列出的缺POSIX接口模拟。'),
           dict(severity='FYI',text='有界清理不保证OS不可中断操作或失效存储仍能写出证据。本轮故意阻塞failure.json写入：0.4秒总预算内0.203802秒被中断，首异常仍传播、磁盘metadata已failed，未增加恢复预算。')],
 requirement_assessment={
  '1.1':'PASS：固定043.ablation.final、原模板和完整身份/祖系/移除旁账；独立旧轮只读加载28边界成功，相关实现未改变。',
  '1.2':'PASS：100原索引/72原N/A/10短窗标签、28条件配对、工程27未跑独立状态、五编码和14seed。',
  '2.1':'PASS：两份tick32完整深拷贝、仅101/102北向掩码差异、同seed不可变自然票复用、固定供能与突变。',
  '2.2':'PASS：原命名空间与消费序重建过去32票，完整state往返、运行时和来源严格绑定；不改seed。',
  '2.3':'PASS：固定33–64窗口与独立阶段门槛；实现阶段未执行真实后缀。',
  '3.1':'PASS：原编码全程序/整个材料组件/原0或1祖系且非原成员、实际q>=2连续10未来末态，完整见证与撤除减继续差。',
  '3.2':'PASS：tick32仅诊断、未来左右删失、跨界辅助长度和t0/32双出生阈值。',
  '3.3':'PASS：完整事件和五类门槛、身份账、E32未来收支基线、质量7、人口账、export0且无二次移除。',
  '3.4':'PASS：条件固定队列、人工初态/外部供能、方向同时影响材料表达和同seed相关性的解释限制明确。',
  '4.2':'PASS：具体类型、源漂移、首BaseException、失败进度/输入/输出hash和有界收尾得到代码及合成反例支持。'},
 design_assessment=dict(file_structure='PASS',continuous_state='PASS',metrics_and_ledgers='PASS',failure_and_budget='PASS',science_contract_changed=False),
 scope=dict(real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0,
    third_round_reviewer_synthetic_physical_steps=0,third_round_reviewer_synthetic_future_generator_ticks=0,
    earlier_round_reviewer_synthetic_physical_steps=133,earlier_round_reviewer_synthetic_future_generator_ticks='各轮原始记录分别保留；本轮不重复科学fixture。',
    author_current_targeted_or_full_synthetic_physical_steps=66,author_current_targeted_or_full_synthetic_generator_ticks=99,synthetic_rng_seed=987654,
    verifier_implemented_or_executed=False,engineering_or_formal_executed=False,feature_go=False,
    source_task_spec_LOG_or_old_data_modified_by_reviewer=False,committed_by_reviewer=False),
 verification=dict(status='VERIFIED',claim_type='TASK',task='2.1',claim='完整两臂连续生产实现与边界测试通过独立任务审查',unresolved_blocking_findings=0,
    limitation='不覆盖尚未实现的独立核验器、真实工程集成或正式研究执行。'),
 summary='任务2.1通过：冻结科学合同、完整来源/连续状态/指标账和当前验证证据相符，所有已报告阻塞反例已修复；真实未来执行仍为0。')
out=ROOT/'docs/research/results/v4-study-047-producer-review.json'
with out.open('x',encoding='utf-8') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
i.approved_gate(str(out.relative_to(ROOT)),'2.1',(*i.NEW_CODE,'tests/test_v4_middle_withdrawal.py'))
print(json.dumps(dict(verdict='APPROVED',task='2.1',approval_total=len(before),gate_validation='PASS',real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0,report=str(out.relative_to(ROOT))),ensure_ascii=False))
