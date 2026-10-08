"""封口当前不可变审查闭包。仅hash/语法/保存证据核查，无科学调用。"""
import ast,datetime,hashlib,json,pathlib,subprocess,time
R=pathlib.Path('/Users/todd/Documents/bitgenesis');O=R/'docs/research/results/v4-study-047-formal-review-run';B=R/'docs/research/results/v4-study-047-formal';D=R/'docs/research/results/v4-study-047-process-guard-diagnostic'; C=R/'docs/research/results/v4-study-047-formal-review.json'
def read(p):return json.loads((R/p).read_text())
def hash(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def pathkey(p):
 p=pathlib.Path(p)
 return str(p.relative_to(R)) if p.is_absolute() and p.is_relative_to(R) else str(p)
def excluded(p):
 return p==str(C.relative_to(R)) or p.startswith('docs/research/results/v4-study-047-formal-parent-verification/') or (p.startswith('.kiro/') and pathlib.Path(p).name in ['spec.json','tasks.md']) or p in ['LOG.md','LOG'] or p.endswith('/LOG.md')
expected={}
def add(p,h=None):
 p=pathkey(p)
 if excluded(p):return
 h=h or hash(p)
 assert p not in expected or expected[p]==h,('conflicting binding',p)
 expected[p]=h
for role in ['producer','verifier','engineering']:
 p=f'docs/research/results/v4-study-047-{role}-review.json';d=read(p);assert d['files_sha256']==d['files_sha256_after']
 for f,h in d['files_sha256'].items():add(f,h)
 add(p)
d=read(B/'validation-summary.json');assert d['files_sha256']==d['files_sha256_after']
for p,h in d['files_sha256'].items():add(p,h)
for route in ['producer','verifier']:
 d=read(B/f'raw/{route}/metadata.json')
 for p,h in d['input_sha256'].items():add(p,h)
# 最终诊断manifest原始字节及最终完整性日志独立核对，不重复运行诊断。
manifest=read(D/'artifact-manifest.json')
for p,v in manifest['files'].items():assert hash(D/p)==v['sha256'] and (D/p).stat().st_size==v['bytes']
for fname in ['final-verification.execution.json','epoch-3/probe-execution.json']:
 p=D/fname;d=read(p)
 for f,h in d['raw_output_sha256'].items():
  q=pathlib.Path(f);q=R/q if (R/q).exists() else p.parent/q
  assert hash(q)==h
before=read(D/'tracked-source-hashes-before.json');after=read(D/'tracked-source-hashes-after.json');assert before==after
checked=0
for p,h in before.items():
 if not excluded(p):assert hash(p)==h;checked+=1
assert read(D/'epoch-3/probe-output/results.json')['forbidden_calls']==[]
for directory in [B,D,O]:
 for p in directory.rglob('*'):
  if p.is_file():add(p)
# 全部现行代码与测试也绑定；父层状态及未来验收不纳入。
for base in ['src','scripts','tests']:
 for p in (R/base).rglob('*.py'):
  if '__pycache__' not in p.parts:add(p)
for p in ['AGENTS.md','pyproject.toml','.agents/skills/kiro-review/SKILL.md','.agents/skills/kiro-impl/templates/reviewer-prompt.md','.kiro/specs/middle-policy-withdrawal/requirements.md','.kiro/specs/middle-policy-withdrawal/design.md','experiments/v4/study-047.md','docs/design/v4-middle-policy-withdrawal.zh-CN.md','docs/research/v4-study-047-results.zh-CN.md']:add(p)
# 确保审查脚本语法与叙述无空白残留；不compile/import任何科学程序。
for p in O.glob('*.py'):ast.parse(p.read_text())
for p in O.glob('*.md'):
 for n,line in enumerate(p.read_text().splitlines(),1):assert line.rstrip()==line,(p,n)
assert subprocess.check_output(['git','diff','--stat'],cwd=R,text=True)==''
finalcheck={'status':'PASS','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'diagnostic_manifest_verified':len(manifest['files']),'tracked_immutable_current_checked':checked,'diagnostic_tracked_before_after_equal':len(before),'author_seal_sha256':hash(B/'validation-summary.json'),'report_sha256':hash('docs/research/v4-study-047-results.zh-CN.md'),'reviewer_script_syntax':'PASS','tracked_diff':'empty','scope':'只读封口，不重新运行科学/测试/guard；临时恢复已保存清单后清理','reviewer_failure_epochs':[{'script':'audit_v1.py','exit_code':1,'classification':'审查器相对日志路径错误；原脚本/trace保留，不是科学失败'}]}
fp=O/'final-checks.json';fp.write_text(json.dumps(finalcheck,ensure_ascii=False,indent=2)+'\n');add(fp)
first={p:hash(p) for p in sorted(expected)};assert first==dict(sorted(expected.items()))
second={p:hash(p) for p in sorted(expected)};assert first==second
assert not any(excluded(p) for p in first)
audit=read(O/'audit_v2.result.json');supp=read(O/'supplement.result.json')
findings=[{'id':'F1','severity':'Important','blocking':True,'category':'LOGIC_ERROR','title':'macOS大写Python使两路线及wrapper互斥预检漏检','locations':['scripts/run_v4_middle_withdrawal.py:740','scripts/verify_v4_middle_withdrawal.py:841','docs/research/results/v4-study-047-formal/raw/execution_runner.py:process_state'],'requirements':['4.1','4.3'],'task_acceptance':'任务3.1第一条最新指示/进程/独占目录检查及最终完整验收门槛','evidence':'最终独立diagnostic真实guard74用例36漏检、原wrapper6用例4漏检；epoch3 exit1，完整性exit0，forbidden_calls=[]。父层预启动脚本路径空观察有辅助价值但缺全ps/准确时钟及-m完备覆盖，事后空快照不能反推历史。','impact':'不能无条件沿用旧2.1/2.2与相关工程互斥完备性；阻断任务3.1完整完成、规格最终通过与FEATURE_GO。未证明实际并发或科学字节损坏。','ownership':['Producer任务2.1','Verifier任务2.2','父控制器/集成外层检查及状态验收']}]
requirements={k:{'verdict':'PASS','basis':v} for k,v in {'1.2':'100索引、72N/A、10旧短窗、28配对及五格14seed完整','2.3':'冻结33–64窗口和分路线600秒/128MiB，无缩队列选窗，工程与正式分开','3.1':'完整材料组件/四项程序/祖系的被动重算、全部28指标/见证/配对差一致','3.2':'tick32诊断、未来左右删失、跨界及双出生阈值均独立核查，未借过去满足未来10','3.3':'1792行全部事件/失败门槛/能量材料人口账和零项保存；旧移除不重计','3.4':'完整政策撤除条件描述，明确人工初态/外供能/同seed相关性，无自主生命或等效性升级','4.2':'本正式epoch源前后当前及全部收尾错误表完整；作者格式检查与审查器失败保留，旧full临时失败目录缺口仍披露'}.items()}
requirements['4.1']={'verdict':'FAIL','passed':'阶段顺序、干净提交、全部实际执行与预算通过','blocked':'进程互斥预检存在当前运行时真实漏检，相关工程门槛不能无条件沿用','finding':'F1'}
requirements['4.3']={'verdict':'FAIL','passed':'实际CLI、来源及完整字节恢复、科学结果和本独立审查产物通过','blocked':'独立审查REJECTED，整体完成声明及最终规格验收尚未通过','finding':'F1'}
canonical={'verdict':'REJECTED','task':'3.1','independent_author_review':True,'reviewer':'/root/withdrawal_formal_review','language':'zh-CN','boundary':'FormalIntegration','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scientific_evidence_verdict':'PASS','archive_verdict':'PASS','interpretation_verdict':'PASS','execution_guard_verdict':'FAIL','task_complete':False,'feature_go':False,'execution_commit':'a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f','requirements':list(requirements),'requirement_assessment':requirements,'design_assessment':{'boundary':'WITHIN','scientific_contract':'PASS','continuous_state_and_rng_contract':'PASS_WITHOUT_REDRAW','full_metrics_ledger':'PASS','failure_budget':'PASS_FOR_FORMAL_EPOCH_WITH_PROCESS_GUARD_BLOCKER','architecture':'既有控制面缺陷回2.1/2.2，不把修复推入科学协议或篡改正式报告'},'mechanical_results':{'tests':'PASS_REUSED_ORIGINAL_1070_INCLUDING_104; NO_NEW_TEST_RUN','test_command':['.venv/bin/python','-m','unittest','discover','-s','tests','-v'],'test_exit_code':0,'compile_and_help':'PASS_REUSED_CURRENT_SOURCE_BOUND','placeholder_scan':'CLEAN','secret_scan':'CLEAN','static_checks':'PASS_AST_REVIEWER_AND_SOURCE_SPOT_CHECK','boundary':'WITHIN','boundary_audit':'CLEAN_OWNERSHIP_ROUTED','red_phase':'N/A_FOR_NEW_SCIENCE; VERIFIED_RED_FOR_PROCESS_GUARD','independent_audit':{'path':str((O/'audit_v2.execution.result.json').relative_to(R)),'exit_code':0,'wall_seconds':read(O/'audit_v2.execution.result.json')['wall_seconds']},'supplement':{'path':str((O/'supplement.execution.result.json').relative_to(R)),'exit_code':0}},'scientific_evidence':{'strict_comparison':audit['strict_science'],'routes':audit['routes'],'archive':audit['archive'],'observations':supp['observations'],'denominators':{'original_index':100,'not_applicable':72,'pairs':28,'shared_environment_seeds':14,'five_encoding_counts':[5,3,0,9,11],'south_zero_denominator_mean':None},'metrics_per_pair':28,'binary_endpoints':16,'q_series_different_pairs':9,'interval_different_pairs':3,'nonzero_metric_pairs':18,'scientific_report_tables_verified':6,'formal_physical_steps':3584,'prior_engineering_physical_steps':128,'combined_actual_physical_steps':3712,'assessment_scope':'既有两路线实际物理证据及全部保存JSON的独立被动审计；不是重新运行物理或随机后缀'},'reviewer_scope':audit['scope'],'findings':findings,'remediation':[{'owner':'Producer 2.1 / Verifier 2.2','action':'仅对解释器basename规范化大小写；保留脚本/模块精确匹配、自身PID及阴性排除。固定mock ps补script/-m/附着-m/参数/--/实际框架路径及阴性，保存新鲜RED/GREEN并独立再审。','forbidden':'不得执行额外真实或合成物理、环境抽票或科学CLI，不为控制修复重跑已有研究。'},{'owner':'父控制器及集成外层检查','action':'修正未来使用的外层谓词；冻结旧wrapper、源码、审批和a9efac4正式epoch。更新受影响状态但不改历史执行来源。'},{'owner':'新鲜独立审查及父层最终验收','action':'新代码用新审批/显式历史归档映射；证明科学路径未变，明确处置既有互斥证据剩余局限后再评3.1。不能篡改旧审批hash、关闭来源门禁或声称新代码产生了旧数据。'}],'ownership':{'science_and_archives':'当前正式epoch保留，PASS不要求重跑','process_guards':['2.1','2.2'],'future_wrapper':'父控制器/集成拥有者','spec_tasks_LOG':'父层','review_artifacts':'/root/withdrawal_formal_review'},'historical_limits':['父层预检缺完整ps和准确观察时间，未覆盖全部-m；事后快照不能倒推独占','旧full首次2 errors生产临时失败目录已清理，仅trace/日志/源码存在；不冒称恢复','缺POSIX模拟不代表原生Windows通过','作者报告冻结后的格式v1 exit1/v2 exit0和本审查audit_v1 exit1/audit_v2 exit0均保留'],'files_sha256':first,'files_sha256_after':second,'binding_count':len(first),'binding_policy':'当前代码、全部必需输入/三审批闭包、正式raw/tar/作者封口/报告、全部本审查证据及最终diagnostic文件；排除canonical自身、可变当前.kiro/**/{spec.json,tasks.md}/LOG、父层formal-parent-verification和未来父验收产物。诊断清单及历史快照绑定，但不递归引入其可变当前路径。','report_path':str((O/'review.zh-CN.md').relative_to(R)),'summary':'保存科学对象、完整归档与限定解释PASS；大小写进程漏检使4.1/4.3及任务3.1完整验收REJECTED，回2.1/2.2最小控制修复，旧科学epoch不重跑。'}
with C.open('x') as f:f.write(json.dumps(canonical,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verdict':canonical['verdict'],'scientific_evidence_verdict':'PASS','binding_count':len(first),'canonical_sha256':hash(C),'review_report_sha256':hash(O/'review.zh-CN.md'),'diagnostic_manifest_verified':len(manifest['files']),'current_tracked_immutable_checked':checked},ensure_ascii=False,indent=2))
