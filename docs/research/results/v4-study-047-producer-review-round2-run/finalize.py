"""保存只读复审结论与精确版本证据，不修改生产/规格/历史文件。"""
import json
from pathlib import Path
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as i
HERE=Path(__file__).resolve().parent
before=i.read(HERE/'initial-bindings.json');after,errors,first=i.capture(before)
assert first is None and not errors;i.same(before,after)
raw=Path('docs/research/results/v4-study-047-producer-implementation/remediation-full-suite.stderr.txt').read_text()
assert 'Ran 1011 tests in 63.535s' in raw and raw.rstrip().endswith('OK')
assert not Path('data/v4-study-047').exists()
evidence={str(p.relative_to(ROOT)):i.digest(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p)}
report=dict(verdict='REJECTED',task='2.1',independent_author_review=True,
 author='/root/withdrawal_producer',reviewer='/root/withdrawal_producer_review',review_round=2,
 created_at_utc=datetime.now(timezone.utc).isoformat(),language='zh-CN',
 files_sha256=before,files_sha256_after=after,review_evidence_sha256=evidence,
 binding_counts=dict(current_source_closure=1191,current_review_bindings=len(before),prior_review_bindings=1221,prior_review_evidence=22,archived_old_source_mapping=3),
 source_chain={p:i.digest(p) for p in (i.SOURCES,i.CENSUS,i.REVIEW)},
 preserved_history='旧初审1221绑定通过rejected-epoch-1的3项显式源码映射验证，其余旧路径字节不变；旧22审查证据亦不变。',
 mechanical_results=dict(
  regression='同版原始1011测试PASS63.535秒、exit0及当前3代码/1191输入hash核实；未再次运行完整suite。',
  targeted='作者同版45项PASS证据核实；独立缺少POSIXAPI模拟45项PASS/5个具体计时测试SKIP，exit0。不是原生Windows运行。',
  static='当前compileall与CLI help原始exit0证据核实；修复diff人工检查无占位符、凭据或科学规则漂移。',
  boundary='WITHIN：仅Producer3文件和审查/实现证据；不实现或执行Verifier，不跑真实工程/正式。',
  red_phase='VERIFIED：原始RED及初审/修复反例完整保留。',
  adversarial='FAIL：释放与恢复双重异常后，磁盘metadata仍complete；其他R1–R4具体反例通过。'),
 resolved_findings=[
  dict(id='R1',result='PASS',evidence='独立去除SIGALRM/ITIMER_REAL/setitimer/getitimer后，两个原错误测试通过；整个相关suite45项通过，5项POSIX真实计时用例按平台跳过。'),
  dict(id='R2',result='PASS',evidence='-m启动、-u -B脚本启动、-X/-W核验模块启动均拒绝；无关脚本携带同名参数不会误报。'),
  dict(id='R3-normal-closing',result='PASS',evidence='独立0.3秒预算中1秒blocked hash被中断，总耗时0.04976429196540266秒，首ValueError保持且磁盘failed。新异常见R5。'),
  dict(id='R4',result='PASS',evidence='32合成票后directions.getstate抛KeyboardInterrupt，checkpoint为failed，feeds状态仍保存，首异常原对象传播。')],
 findings=[dict(id='R5',severity='Important',file='scripts/run_v4_middle_withdrawal.py',lines=[685,709],
  focus_lines=[695,708],requirement_refs=['4.2','技术设计：失败、预算与测试策略','预注册：来源、执行和审查门槛'],
  problem='release恢复旧handler抛首SystemExit；随后的恢复安装抛KeyboardInterrupt；第二次release成功后直接退出，没有修复持久化状态。内存status=failed，但已写磁盘metadata.json保留status=complete且无failure.json。文件I/O健康且2秒预算仍充裕，因此这不是OS不可中断I/O/存储损坏的限制，而是ready=false分支遗漏失败证据。',
  reproduction='recheck.py::failed_release_and_recovery：signal handler调用1正常安装，2抛SystemExit，3抛KeyboardInterrupt，4正常；execute(lambda:None)传播首异常。观测disk_status=complete、in_memory_status=failed、failure_file_exists=false、retry_release_succeeded=true。',
  evidence=['docs/research/results/v4-study-047-producer-review-round2-run/release-recovery-disk-metadata.json','docs/research/results/v4-study-047-producer-review-round2-run/release-recovery-memory-metadata.json'],
  remediation='补齐释放/恢复异常的持久化状态协议，使任何失败退出不能留下可被当作成功的complete记录；至少覆盖恢复安装失败后retry release成功的当前反例，以及首异常优先。修复仍须使用原600秒总预算内的有界收尾，不能改为无保护写入。')],
 scope=dict(real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0,
  reviewer_synthetic_physical_steps=66,reviewer_synthetic_future_generator_ticks=131,synthetic_rng_seed=987654,
  full_suite_rerun=False,native_windows_execution=False,new_source_edits=False,task_or_spec_or_LOG_edits=False,committed=False),
 verification=dict(status='NOT_VERIFIED',claim_type='TASK',claim='任务2.1可通过生产实现独立审查',gap='R5失败epoch磁盘误记complete尚未修复。'),
 summary='原R1/R2/R4及通常的有界收尾修复有效；R5释放/恢复双重异常会留下假complete，须修复后复审。')
out=ROOT/'docs/research/results/v4-study-047-producer-review-round2.json'
with out.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(verdict=report['verdict'],task='2.1',findings=1,binding_count=len(before),real_future_physical_steps=0,real_future_generator_ticks=0,report=str(out.relative_to(ROOT))),ensure_ascii=False))
