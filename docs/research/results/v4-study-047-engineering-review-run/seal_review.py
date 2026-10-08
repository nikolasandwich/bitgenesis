"""Seal the independent engineering review without importing research modules."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, subprocess
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
CANONICAL=ROOT/'docs/research/results/v4-study-047-engineering-review.json'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=read(OUT/'review-inputs-before.json'); audit=read(OUT/'audit-results.json'); extra=read(OUT/'supplemental-checks.json')
assert audit['status']==extra['status']=='PASS'
assert read(OUT/'audit-execution-v2/execution.json')['exit_code']==0
assert read(OUT/'supplemental-execution/execution.json')['exit_code']==0
for p,h in before['files_sha256'].items():assert sha(ROOT/p)==h,p
status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
allowed=('?? docs/research/results/v4-study-047-engineering/', '?? docs/research/v4-study-047-engineering.zh-CN.md', '?? docs/research/results/v4-study-047-engineering-review-run/', '?? docs/research/results/v4-study-047-engineering-parent-verification/')
assert all(line.startswith(allowed) for line in status.splitlines()),status
assert subprocess.run(['git','diff','--exit-code'],cwd=ROOT,capture_output=True).returncode==0
assert not (ROOT/'data/v4-study-047').exists()
for p in OUT.rglob('*.py'): ast.parse(p.read_text(),filename=str(p))
for p in OUT.rglob('*.json'): read(p)
(OUT/'git-status-before-review-seal.txt').write_text(status)
paths=set(before['files_sha256'])
paths.update(str(p.relative_to(ROOT)) for p in OUT.rglob('*') if p.is_file())
mutable={'.kiro/specs/middle-policy-withdrawal/spec.json','.kiro/specs/middle-policy-withdrawal/tasks.md','LOG.md'}
assert not paths & mutable
assert not any('v4-study-047-engineering-parent-verification/' in p or p.endswith('v4-study-047-engineering-validation.json') or p.endswith('v4-study-047-engineering-review.json') for p in paths)
files={p:sha(ROOT/p) for p in sorted(paths)}
after={p:sha(ROOT/p) for p in sorted(paths)}
assert files==after
code=['scripts/middle_withdrawal_inputs.py','scripts/run_v4_middle_withdrawal.py','scripts/verify_v4_middle_withdrawal.py']
engineering={role:f'docs/research/results/v4-study-047-engineering/raw/{role}/metadata.json' for role in ['producer','verifier']}
assert set(code+list(engineering.values()))<=files.keys()
for role,status in [('producer','complete'),('verifier','verified')]:
    meta=read(ROOT/engineering[role]);assert [meta['status'],meta['mode'],meta['physical_steps']]==[status,'engineering',64]
findings=[
 {'severity':'FYI','text':'无未解决阻断。审批仅覆盖任务2.3工程证据及独立作者审查；父层仍须完成核验、更新状态并形成干净提交，之后才可按任务3.1另启完整正式队列。'},
 {'severity':'FYI','text':'两臂只有44–48五步双副本，future_persistent10均false且全部指标差为0；occupied为65/59、raw_material为86/92，不能解释为全过程相同、正式队列无效应或生命标准达成。'},
 {'severity':'FYI','text':'完整1070测试、104专项及编译/help均复用历史真实执行；五份当前源码/测试=运行前=运行后=冻结副本，原始日志hash相符。本审查未重跑真实或合成物理，未重新抽取环境票。'},
 {'severity':'FYI','text':'作者只读审计v1误读boundary引用的exit1与纠正v2 exit0完整保存。独立审查器v1因历史help哈希字段名不同而exit1，v2仅适配schema并exit0；两版审查源码/原始日志均绑定。补充交互读取旧RED临时fixture路径失败也明确记录，不冒称旧fixture在本轮恢复；均非真实科学运行失败。'},
 {'severity':'FYI','text':'新文本空白检查仅命中source-snapshots/src/bitgenesis/v4/competition.py:117既有尾部空行，已核原源码逐字节相同；保持历史证据。'},
 {'severity':'FYI','text':'首例保守容量外推64,642,426/64,974,382字节均低于128MiB，但时间与容量外推不保证余27例；正式仍须原600秒/128MiB硬限。原生Windows未执行；早期联合回归失败目录保全缺口维持原披露。'}]
record=dict(
 verdict='APPROVED',task='2.3',independent_author_review=True,reviewer='/root/withdrawal_engineering_review',
 language='zh-CN',boundary='EngineeringIntegration',created_at_utc=datetime.now(timezone.utc).isoformat(),
 approved_implementation_commit='931dd9e70f6b89813635f7d25e74cdc8cf42e0bf',
 protocol='.agents/skills/kiro-review/SKILL.md',reviewer_prompt='.agents/skills/kiro-impl/templates/reviewer-prompt.md',
 requirements=['2.3','3.1','3.2','3.3','4.1','4.2','4.3'],
 design_sections=['架构及流程','组件、接口与需求追踪','数据和连续状态合同','指标和完整账','失败、预算与测试策略'],
 engineering_evidence=engineering,files_sha256=files,files_sha256_after=after,
 binding_count=len(files),binding_policy='包含全部当前输入、1985/3023依赖审批闭包、当前审批、当前源码/测试、作者报告、完整工程归档和原始输入/输出、历史回归/RED、独立审查脚本与原始执行证据；排除可变spec.json/tasks.md/LOG、未来父验证和本JSON，避免自引用。报告保持原封不动。',
 code_sha256={p:files[p] for p in code},report_sha256=files['docs/research/v4-study-047-engineering.zh-CN.md'],
 mechanical_results=dict(
  tests=audit['regression'],saved_evidence_audit=dict(status='PASS',exit_code=0,evidence=str((OUT/'audit-execution-v2/execution.json').relative_to(ROOT)),strict_comparison_nodes=audit['strict_comparison_nodes'],new_scientific_calls=0),
  full_objects=audit['complete_scientific_comparison'],archive_restore=audit['archive_restore'],
  approvals=audit['current_approvals'],source_closure_counts=dict(producer=1194,verifier=1200),
  original_tracked_files_currently_equal=audit['original_tracked_files_currently_equal'],source_snapshots_current_byte_identical=201,
  placeholder_scan='CLEAN：7份新作者文本无新增占位标记。',secrets_scan='CLEAN：未发现具体凭据模式。',
  static_checks='PASS：当前同版编译证据已核实；新增归档脚本AST可解析；实际入口及独立字典物理依赖已阅读。无源码改动。',
  whitespace=extra['historical_eof_blank_line'],boundary='WITHIN',boundary_audit='CLEAN：作者仅新增工程报告及工程归档，未改源码/测试/旧数据/规格/审批，未预跑其余27对。',
  red_phase='N/A（本任务无新行为实现）；已有批准真实RED原始exit1/hash已核实，当前1070回归GREEN为同码复用。'),
 requirement_assessment={
  '2.3':'PASS：运行前固定任务说明、干净提交和实际argv证明唯一E120005、33–64；两路线各64步，工程目录独占且正式目录不存在。',
  '3.1':'PASS：五份科学文件递归具体类型/值及原字节相同；原模板、整个组件、全程序、身份祖系、q序列及撤除减继续差保存核对。',
  '3.2':'PASS：q32=0；44–48 inclusive5步、持续10false、左右删失false、cross_boundary=null；原t0=19和32后出生双阈值见证核对。',
  '3.3':'PASS：逐tick完整256方向/feed/mutation，全部事件/失败/零项、被动身份账重建、E32基线能量/人口/质量7、export0和原移除旁账核对；100索引1完成/27未跑/72N/A及全部五编码/14seed/二元四格重核。',
  '4.1':'PASS：依赖方法/生产/独立核验审批当前绑定有效，实际两路线从同一干净931dd9e提交运行；各600秒/128MiB内完成，未来正式仍等待父层干净工程提交。',
  '4.2':'PASS：当前来源前后/现值一致、metadata/proof/输出闭合；严格具体类型比较，既有失败与异常边界测试由同码1070回归覆盖；作者和审查只读失败版本保持独立账。',
  '4.3':'PASS：236原文件8,251,010字节从tar实际恢复并与直接副本/原字节比较，执行命令/环境/退出码/源快照齐全，当前独立工程审查通过；父层完成核验/提交不由本记录冒称已完成。'},
 routes=audit['routes'],scientific_observations=audit['arms'],index_summary=audit['index_summary'],
 findings=findings,remediation='无必须修复项。父层按既定顺序完成核验、状态更新及干净提交；本审查不提交或运行正式研究。',
 reviewer_failures=extra['reviewer_audit_correction'],historical_red_evidence=extra['historical_red'],
 scope=dict(real_engineering_physical_steps=128,real_engineering_future_generator_ticks=64,past_generator_ticks_per_route=640,reviewer_new_real_or_synthetic_physical_steps=0,reviewer_new_future_draws=0,real_route_reruns=0,formal_directory_exists=False,other_27_pairs_executed=False,task_completion_by_parent_pending=True,clean_engineering_commit_pending=True,feature_go=False,source_or_author_report_modified=False,committed_by_reviewer=False),
 summary='独立工程审查APPROVED：唯一首E120005两路线、完整对象、来源、实际归档恢复及当前同版回归证据满足任务2.3；无阻断，正式完整队列仍须父层完成核验与干净提交后另启。')
assert record['report_sha256']=='123419f692b1a97b9ae2010b13b51755d819c1e6916aefffa3893ace41d30582'
with CANONICAL.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
# Replicate only the data contract of approved_gate; never import or invoke the
# production CLI or execution_gates, and never bypass its clean-Git condition.
saved=read(CANONICAL);assert saved['files_sha256']==saved['files_sha256_after']
for p,h in saved['files_sha256'].items():assert sha(ROOT/p)==h,p
print(json.dumps(dict(verdict=saved['verdict'],task=saved['task'],bindings=len(files),path=str(CANONICAL.relative_to(ROOT)),sha256=sha(CANONICAL),compatible_with_formal_review_schema=True,clean_git_gate_not_bypassed=True,new_scientific_calls=0),ensure_ascii=False))
