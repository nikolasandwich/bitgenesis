"""写入task2.2独立最终审批，绑定当前实现与不可变审查/执行证据。"""
from datetime import datetime,timezone
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as i
root=Path(__file__).parent
check=i.read(root/'evidence-check.json');controls=i.read(root/'independent-fixtures-v2/preflight-check.json');archives=i.read(root/'archive-red-check.json')
author_path=i.BASE+'verifier-implementation/final-validation-remediated.json';author=i.read(author_path)
producer_path=i.BASE+'producer-review.json';producer=i.approved_gate(producer_path,'2.1',i.NEW_CODE)
initial_path=i.BASE+'verifier-review-initial.json';initial=i.read(initial_path)
files={}
def add(mapping):
 for p,h in mapping.items():
  assert not p.endswith('/tasks.md') and not p.endswith('/spec.json') and Path(p).name!='LOG.md',p
  if p in files:assert files[p]==h,p
  assert i.digest(p)==h,p
  files[p]=h
add(author['files_sha256']);add(producer['files_sha256']);add(author['evidence_files_sha256']);add(author['own_files_sha256'])
add({check['archive_source_mapping'].get(p,p):h for p,h in initial['files_sha256'].items()})
add({p:i.digest(p) for p in [producer_path,author_path,initial_path,'tests/test_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py','tests/test_provenance.py',i.BASE+'producer-preflight-preservation/preservation.json']})
add({str(p):i.digest(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
after={p:i.digest(p) for p in files};i.same(files,after,'当前完整复审绑定前后')
report={
 'verdict':'APPROVED','task':'2.2','independent_author_review':True,'reviewer':'/root/withdrawal_verifier_review','author':'/root/withdrawal_verifier','created_at_utc':datetime.now(timezone.utc).isoformat(),'language':'zh-CN',
 'scope':'TASK2.2独立核验实现与合成边界测试，含R1预检生命周期修复；不表示FEATURE_GO或真实工程/正式研究完成。','boundary':'Verifier',
 'code_sha256':{p:i.digest(p) for p in [*i.NEW_CODE,i.VERIFIER,'tests/test_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']},
 'binding_policy':'当前1192来源、Producer再审1985绑定及当前审批、核验器与两路线测试、作者执行证据及独立新旧审查证据均绑定。旧已替换源依据显式归档映射核对；不绑定tasks.md/spec.json/LOG、未来父报告/完成验证或审批自身。临时Git归档逐成员核实，不依赖已清理临时目录。',
 'binding_counts':{'current_source_closure':1192,'producer_current_approval':1985,'author_current_evidence':1171,'initial_rejection':1856,'old_producer_approval':1321,'old_author_evidence':398,'final_approval_total':len(files)},
 'requirements':['1.1','2.1','2.2','3.1','3.2','3.3','4.2','4.3'],
 'design_sections':['边界承诺','架构及流程','文件结构计划','组件、接口与需求追踪','数据和连续状态合同','指标和完整账','失败、预算与测试策略'],
 'previous_verdict':{'path':initial_path,'verdict':'REJECTED','sha256':i.digest(initial_path),'finding':'R1','all_1856_bindings_preserved_via_mapping':True,'mapping':check['archive_source_mapping']},
 'producer_dependency':{'path':producer_path,'verdict':'APPROVED','task':'2.1','sha256':i.digest(producer_path),'all_1985_bindings_current':True,'ownership':'生产侧同源预检缺口由Producer作者与原Producer独立审查者修复/再审，Verifier未代偿生产职责。'},
 'remediation_assessment':{'finding':'R1','status':'RESOLVED','implementation':'Epoch.execute安装Guard后，在原工作租期中执行preflight；run中的process和execution_gates进入同一首异常/失败保全边界。独占空目录维持clean-git门槛，审批未过无科学读取/计算；保留真实失败类型、message和filename。','changed_top_level_definitions':['Epoch','run'],'all_other_scientific_definitions_unchanged':True,'actual_total_seconds':600,'actual_work_seconds':570,'actual_closing_reserve_seconds':30,'no_budget_reset':True},
 'mechanical_results':{
  'canonical_suite':{'status':'PASS','tests':1070,'seconds':77.334,'wall_seconds':77.7735480000265,'exit_code':0,'command':'PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v','evidence':i.BASE+'preflight-joint-validation/full-revalidated/execution.json','verification':'五份当前源码=运行前=运行后=冻结副本；原始stdout/stderr逐字节核实。按用户指示不重复完整suite。'},
  'current_compile':{'status':'PASS','exit_code':0,'evidence':i.BASE+'preflight-joint-validation/compile-revalidated/execution.json'},
  'help':{'status':'PASS','exit_code':0,'evidence':i.BASE+'verifier-implementation/remediation-1-help/execution.json'},
  'author_special_related':{'status':'PASS','special_tests':48,'related_tests':104,'qualification':'实现同版；后续仅合成预检时标调整，当前1070项完整回归覆盖最终48/104测试。'},
  'independent_R1_controls':{'status':'PASS','checks':5,'exit_code':0,'evidence':str(root/'independent-preflight-v2/execution.json'),'real_or_synthetic_science_calls':0},
  'red_phase':'VERIFIED：remediation-1-red原始exit1，3测试1failure/4errors；GREEN与当前final-full原字节逐项绑定。',
  'static_checks':'PASS：运行时导入、当前新增代码无占位标记/具体秘密模式/行尾空白；无生产科学函数导入。',
  'boundary':'WITHIN','boundary_audit':'CLEAN：只有Verifier生命周期变化；独立字典核/union-find及不可变读取合同依赖保持。'
 },
 'independent_counterexamples':controls['checks'],
 'archive_integrity':{'independent_fixture_archives':archives['archive_count'],'independent_fixture_members':archives['archive_members'],'sha256_per_member_verified':True,'author_executions_verified':len(archives['executions'])},
 'scaled_test_assessment':{'status':'ACCEPTED','implementation_unchanged_between_initial_joint_failure_and_final_full':True,'old_verifier_synthetic_seconds':.2,'new_synthetic_seconds':2.,'old_block_seconds':.5,'new_block_seconds':5.,'rationale':'仅合成调度时标放大，使真实fork与失败I/O不受十几毫秒收尾份额左右；仍断言有界中断、相同绝对起点、失败metadata/failure、首异常与0科学调用。真实600/30秒与固定未来窗口不变。','historical_limitation':'首次联合full1070项2errors未抹去；核验失败metadata为0B但failure/proof及源码/原日志保留。Producer当时临时epoch因父执行器缺少保全环境配置已删除，只能保留trace/raw/源码，不能声称精确恢复该失败目录。'},
 'requirement_assessment':{
  '1.1':'PASS：28真实043.ablation.final只读恢复，原history/parents/移除旁账/template保留；初审实际被动390prefix tick通过，相关科学AST未变。',
  '2.1':'PASS：独立两臂深拷贝同一tick32；同seed唯一不可变自然票缓存；continue仅101/102为3，withdraw全部自然票；固定feed/mutation/exchange false。',
  '2.2':'PASS：独立SHA256 namespace与两Random流恢复20seed×32过去票及完整checkpoint；初审真实640past tick通过，当前环境科学实现字节/AST不变，错误seed/消费序/runtime合成拒绝测试由当前full覆盖。',
  '3.1':'PASS：原encoding模板、全四项程序、整个材料组件、原0/1祖系且排除原成员，允许同创始祖系；实际q>=2连续10未来末态、全见证与撤除减继续配对差。',
  '3.2':'PASS：q32仅诊断；跨界两端均≥2，过去长度不满足future10；原t0和32出生阈值、inclusive区间/左右删失独立保留。',
  '3.3':'PASS：完整事件/提议门槛与失败零项、祖系程序组件见证、E32基线、质量7、人口账、export0无二次移除；100index/72N/A/工程27未跑、五编码零格/14seed/二元四格均重建比较。',
  '4.2':'PASS：严格递归具体类型与完整对象比较；来源/输出漂移、短写、阶段和收尾异常、首BaseException、部分数据及错误epoch保留；R1预检纳入同deadline且独立反例通过。',
  '4.3':'PASS：当前源码/原始执行、RED/失败epoch/旧审批按映射保留；依赖Producer正式再审通过，本轮独立核验TASK审批不外推真实研究。'
 },
 'findings':[
  {'severity':'FYI','text':'初始R1已修复，无未解决阻断。初审640真实过去环境tick及390保存prefix为只读检查，未产生真实未来/物理；本次复审无新增科学调用。'},
  {'severity':'FYI','text':'原生Windows未测试；缺POSIX能力模拟不等于原生平台验证。永久坏存储/OS不可中断调用可能妨碍证据保全，不能因此声明成功。'},
  {'severity':'FYI','text':'复审自写fixture首跑未将macOS /var临时路径resolve，触发启动目录守卫并错误读取不存在metadata；原exit1/归档保留。只修正审查fixture路径，v2五项通过，未改实现。'}
 ],
 'reviewer_counts':{'initial_review_synthetic_physical_steps':129,'initial_review_synthetic_future_ticks':97,'initial_real_past_generator_ticks':640,'initial_real_passive_prefix_ticks':390,'this_final_review_synthetic_physical_steps':0,'this_final_review_synthetic_future_ticks':0,'real_study047_future_ticks':0,'real_new_or_replayed_physical_steps':0},
 'verification':{'status':'VERIFIED','claim_type':'TASK','task':'2.2','claim':'独立核验器实现、边界异常测试及独立审查完成；R1修复可接受。','unresolved_blocking_findings':0,'feature_go':False,'engineering_or_formal_executed':False},
 'data_v4_study047_exists':Path('data/v4-study-047').exists(),'files_sha256':files,'files_sha256_after':after,
 'summary':'任务2.2批准：独立科学重建和严格完整对象核验符合冻结合同，预检已处于同一绝对截止与失败epoch边界，当前证据及依赖审查有效；真实未来仍为0。'
}
assert not report['data_v4_study047_exists']
p=Path(i.BASE+'verifier-review.json')
with p.open('x') as f:f.write(i.canonical(report)+'\n')
# Check the actual gate interface against every final binding.
i.approved_gate(str(p),'2.2',(*i.NEW_CODE,i.VERIFIER))
print(i.canonical({'verdict':'APPROVED','task':'2.2','path':str(p),'sha256':i.digest(p),'bindings':len(files),'approved_gate':'PASS'}))
