"""保存独立初审结论及前后不可变绑定；不修改实现、任务、规格或旧数据。"""
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as inputs
HERE=Path(__file__).resolve().parent
before=inputs.read(HERE/'initial-bindings.json')
after, errors, failure=inputs.capture(before)
assert failure is None and not errors
inputs.same(before,after,'review unchanged source/test/evidence bytes')
assert not (ROOT/'data/v4-study-047').exists()
assert not (ROOT/'docs/research/results/v4-study-047-producer-review.json').exists()
evidence_files={str(p.relative_to(ROOT)):inputs.digest(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
report=dict(
    verdict='REJECTED',task='2.1',independent_author_review=True,
    author='/root/withdrawal_producer',reviewer='/root/withdrawal_producer_review',
    created_at_utc=datetime.now(timezone.utc).isoformat(),language='zh-CN',
    claim='任务2.1生产实现和边界测试可通过独立审查；不涉及2.2、2.3或FEATURE_GO。',
    verification=dict(status='NOT_VERIFIED',claim_type='TASK',reason='三个可复现的执行/回归门槛缺陷仍未解决。'),
    files_sha256=before,files_sha256_after=after,
    binding_counts=dict(source_closure=1191,approved_method_closure=1188,reviewed_source_code_implementation_evidence=len(before)),
    source_chain={p:inputs.digest(p) for p in (inputs.SOURCES,inputs.CENSUS,inputs.REVIEW)},
    review_evidence_sha256=evidence_files,
    mechanical_results=dict(
        canonical_regression=dict(status='PASS',evidence='同版实际原始输出：Ran 1000 tests in 61.368s / OK；exit0，wall61.70892458292656秒；3源码和1191前后输入当前仍相等，未重复完整suite。',
            command='PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v',
            stderr='docs/research/results/v4-study-047-producer-implementation/full-suite.stderr.txt',
            metadata='docs/research/results/v4-study-047-producer-implementation/final-validation.json'),
        independent_targeted=dict(status='PASS',tests=34,exit_code=0,elapsed_seconds=0.519),
        independent_adversarial=dict(status='FAIL',harness_exit_code=0,
            explanation='观测脚本成功完成，但其中真实unittest在无SIGALRM接口下2项ERROR；两种有效进程命令未拒绝，收尾deadline被撤销。原始stdout/stderr保留。'),
        static_checks='PASS：py_compile和真实CLI --help均exit0；无额外lint配置。',
        placeholders='CLEAN：rg exit1，无匹配。',secrets='CLEAN：定向模式扫描及人工检查未发现具体凭据。',
        boundary='WITHIN：仅Producer新文件和本次独立审查证据；旧文件无tracked diff。',
        boundary_audit='CLEAN：不把独立科学核验塞进共享输入契约；未来Verifier尚未实现或执行。',
        red_phase='VERIFIED：red.stderr.txt为实现模块不存在导致的导入失败，相关行为fixture随后实际运行通过。'),
    findings=[
        dict(id='R1',severity='Important',file='tests/test_v4_middle_withdrawal.py',lines=[455,526],
             related_file='scripts/run_v4_middle_withdrawal.py',related_lines=[600,603],
             requirement_refs=['回归安全（kiro-review）'],
             problem='仓库现有CI明确包含Windows的Python3.12/3.13/3.14，但两个新故障测试在进入注入的git/signal异常前无条件访问signal.SIGALRM。Windows没有此接口；仿真删除该属性后，两测试均收到AttributeError而非预期异常。',
             evidence='independent-adversarial.stderr.txt：Ran 2 tests / FAILED(errors=2)。这是缺失Unix接口的本机仿真，不冒称在Windows主机执行。',
             remediation='使合成故障测试在现有CI平台可运行，并为不支持的deadline后端提供明确、无科学执行的拒绝路径；无需扩展已冻结的真实研究运行时。'),
        dict(id='R2',severity='Important',file='scripts/run_v4_middle_withdrawal.py',lines=[574,580],
             requirement_refs=['4.2','技术设计：失败、预算与测试策略（运行前047进程检查）'],
             problem='进程检查只看前三个token且仅识别.py文件名，因此漏掉有效启动方式python -m scripts.run_v4_middle_withdrawal和python -u -B scripts/run_v4_middle_withdrawal.py。同一047路线已在运行时仍会通过检查，另一个独占输出目录并不能阻止重复科学执行。',
             evidence='independent-adversarial.stdout.txt记录两种命令rejected=false；直接python script.py为true。',
             remediation='按完整Python命令形式识别Producer/Verifier，包括模块启动和解释器参数，并增加上述否定检查；现有epoch目录保持只读。'),
        dict(id='R3',severity='Important',file='scripts/run_v4_middle_withdrawal.py',lines=[550,565],
             related_lines=[667,671],requirement_refs=['4.2','技术设计：失败、预算与测试策略','预注册：固定窗口与预算'],
             problem='run将disarm/restore_handler作为closing项，Epoch随后才执行input_hashes、output_hashes、最终metadata和失败证据写入。这些操作没有活动deadline；若单次hash或I/O阻塞，后面的elapsed预算检查无法中断它，也无法保证失败证据收尾及600秒硬上限。超时曾在work触发时，一次性alarm也已经消耗。',
             evidence='在第一次输入采集前合成中断后，output_hash观察到ITIMER_REAL=(0,0)；配置0.05秒alarm仍允许0.13秒收尾睡眠不中断。首RuntimeError正确传播，但deadline保护已丢失。',
             remediation='使独立收尾动作也有明确有界的执行策略，覆盖输入/输出hash与metadata/failure写入，并在超时后仍逐项尝试可用证据且保持首异常；用短合成deadline验证阻塞收尾。'),
        dict(id='R4',severity='Suggestion',file='scripts/run_v4_middle_withdrawal.py',lines=[140,150],
             requirement_refs=['4.2'],
             problem='完成32张票后若current_stream_states的getstate失败，嵌套partial-environment.status仍为complete且没有current_stream_states。外层epoch正确failed且保留原SystemExit，所以本条不单独作为拒绝门槛，但该标签容易误导失败证据读者。',
             evidence='合成seed987654：epoch_status=failed，checkpoint_status=complete，tickets=32，has_current_states=false。',
             remediation='建议区分tape完成与checkpoint完成，并在状态捕获异常时清楚标为失败；分别尝试两条流状态可保存更多已有证据。')],
    positive_checks=[
        '完整1191来源、1188批准方法闭包与当前源码字节匹配，3源码及测试证据无漂移。',
        '独立加载28真实过去tick32状态并恢复两份Observer；没有调用真实未来抽签、物理或未来观察。',
        '手工合成物理1步覆盖energy/occupied/raw_material/collision/formed五类提议门槛；死亡后同格原料重用与实际事件一致。',
        '32步双臂连续状态、原模板/完整组件/祖系、两种出生阈值、q>=2连续10及未来/跨界删失契约代码与测试相符。',
        '100索引、72N/A、工程27未跑、28对/五编码S零格/14seed分组及撤除减继续符合固定设计。',
        '多数失败路径正确保留首BaseException对象、失败epoch、进度、前后来源和输出hash；未发现旧材料/能量重复移除。'],
    scope=dict(real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0,
        reviewer_targeted_synthetic_physical_steps=66,reviewer_adversarial_synthetic_physical_steps=1,
        reviewer_adversarial_synthetic_generator_ticks=32,synthetic_rng_seed=987654,
        actual_past_boundary_loads=28,actual_past_environment_generator_ticks=0,
        verifier_implemented_or_executed=False,engineering_or_formal_executed=False,
        modified_source_tasks_specs_logs_old_data=False,committed=False),
    summary='科学实现主体和同版验证证据可信；先修复跨平台测试、进程识别与有界收尾，再复审任务2.1。')
out=ROOT/'docs/research/results/v4-study-047-producer-review-initial.json'
with out.open('x',encoding='utf-8') as f: json.dump(report,f,indent=2,ensure_ascii=False); f.write('\n')
print(json.dumps(dict(verdict=report['verdict'],task=report['task'],important_findings=3,suggestions=1,
    unchanged_review_bindings=len(before),real_study047_future_physical_steps=0,real_study047_future_generator_ticks=0,
    report=str(out.relative_to(ROOT))),ensure_ascii=False))
