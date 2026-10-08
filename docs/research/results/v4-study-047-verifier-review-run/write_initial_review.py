"""保存本轮独立拒绝记录；不更新规格/任务/实现或canonical批准。"""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as i
run=Path(__file__).parent
saved=i.read(run/'saved-input-check.json');author=i.read(run/'author-evidence-check.json');fault=i.read(run/'preflight-deadline-counterexample-v2.json')
files={}
def add(mapping):
 for p,h in mapping.items():
  if p in files:assert files[p]==h,p
  assert i.digest(p)==h,p
  files[p]=h
add(saved['files_sha256']);add(i.read(i.BASE+'producer-review.json')['files_sha256']);add(author['all_author_evidence_sha256'])
add({p:i.digest(p) for p in [i.BASE+'producer-review.json','tests/test_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py','tests/test_provenance.py']})
add({str(p):i.digest(p) for p in run.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
after={p:i.digest(p) for p in files};i.same(files,after,'独立审查前后完整绑定')
report={
 'verdict':'REJECTED','task':'2.2','independent_author_review':True,'reviewer':'/root/withdrawal_verifier_review','baseline_commit':'a69ca8b7fc7a12193f9a6e486be7c1dbce442fa4',
 'scope':'仅核验器实现、合成测试及真实只读过去检查；不是TASK完成/FEATURE_GO，也不授权2.3或3.1。',
 'task_text':'独立恢复过去环境后继续同一流，独立重建身份/组件/程序匹配、未来及跨界指标和完整汇总，不用生产科学输出作为答案；对源漂移、完整对象具体类型、阶段异常和收尾失败建立拒绝证据，保留错误epoch。',
 'boundary':'Verifier','requirements':['1.1','2.1','2.2','3.1','3.2','3.3','4.2','4.3'],
 'design_sections':['边界承诺','架构及流程','文件结构计划','组件、接口与需求追踪','数据和连续状态合同','指标和完整账','失败、预算与测试策略'],
 'mechanical_results':{
   'fresh_special':{'status':'PASS','tests':45,'seconds':2.447,'exit_code':0,'execution':str(run/'fresh-special/execution.json')},
   'reviewer_additional_faults':{'status':'PASS','tests':6,'seconds':.145,'exit_code':0,'execution':str(run/'independent-faults/execution.json')},
   'preflight_absolute_deadline':{'status':'FAIL','exit_code':1,'execution':str(run/'preflight-deadline-v2/execution.json'),'observed':fault},
   'canonical_regression':{'status':'PASS','tests':1058,'seconds':64.690,'wall_seconds':65.04632695799228,'exit_code':0,'evidence':'docs/research/results/v4-study-047-verifier-implementation/final-full/execution.json','basis':'独立逐字节复核当前源码快照及原始stdout/stderr，同版证据未无故重复完整suite；用户明确允许。'},
   'related':{'status':'PASS','tests':92,'seconds':3.518,'exit_code':0,'basis':'同版原始证据独立复核'},
   'portable_simulation':{'status':'PASS','tests':45,'skipped':12,'native_windows_tested':False},
   'compileall':{'status':'PASS','exit_code':0,'execution':str(run/'fresh-compile/execution.json')},
   'cli_help':{'status':'PASS','exit_code':0,'execution':str(run/'fresh-help/execution.json')},
   'placeholders':'CLEAN','concrete_secret_patterns':'CLEAN','static_checks':'PASS：标准库和既有独立字典物理/union-find，无生产科学函数导入','boundary':'WITHIN','boundary_audit':'CLEAN：无实现越界；预算控制缺陷单列','red_phase':'VERIFIED：原始red-01..06及源码快照/原输出hash匹配，关联实质行为反例。'
 },
 'findings':[{'id':'R1','severity':'Important','title':'将阶段预检纳入已声明的绝对预算和失败epoch',
   'file':'scripts/verify_v4_middle_withdrawal.py','lines':[857,858,859,860,861,862,863],
   'requirements':['4.2','4.3'],'design_section':'失败、预算与测试策略','protocol_section':'固定窗口与预算；来源、执行和审查门槛',
   'description':'run在857行构造Guard但未安装/持有；858的进程检查、859的阶段审批和全部来源hash检查、860的路径解析先执行，直到944进入Epoch.execute才在716安装计时器。start时间传递虽然避免重新获得600秒，却不能中断这些可阻塞预检。当它们耗尽总预算后才创建输出，随后的所有收尾都已无预算，留下空epoch。',
   'reproduction':'PYTHONPATH=src .venv/bin/python docs/research/results/v4-study-047-verifier-review-run/preflight_deadline_counterexample_v2.py（已有输出目录，复现副本须使用全新输出名，不覆盖本证据）',
   'observed':{'configured_total_seconds':.2,'interruptible_gate_delay_seconds':.5,'actual_seconds':fault['elapsed_seconds'],'exception':fault['error']['type'],'output_files':fault['output_files'],'future_calls':0,'physical_calls':0},
   'remediation':'在同一run起点的绝对截止内安装并保持预检计时保护，将适用的进程检查、阶段审批/来源读取纳入有界工作及统一首异常/失败保全；仍须先拒绝未授权科学执行。保留预检失败或超时的非完成证据，并为可中断预检超时、审批来源读取异常和干净成功路径添加真实RED→GREEN反例；不得重置总预算或因修复缩短科学窗口。'}],
 'read_only_real_validation':{k:saved[k] for k in ('environment_count','past_generator_ticks','saved_prefix_count','saved_prefix_ticks','forbidden_calls','new_or_replayed_physical_steps','real_study047_future_ticks','elapsed_seconds','data_v4_study047_exists')},
 'evidence_preservation':{'author_bound_evidence':398,'author_total_files':399,'author_source_bindings':1192,'producer_review_bindings':1321,'producer_review_sha256':author['producer_review_sha256'],'notes':'原raw stderr与刻意截断JSON不修复；所有旧证据字节不变。preflight反例v1未显式缩放定义绑定的Epoch默认600s，其结论不采用，原字节保留；R1依据已纠正v2。'},
 'reviewer_incremental_counts':{'synthetic_dictionary_physical_steps':65,'synthetic_producer_physical_steps':64,'synthetic_verifier_future_ticks':65,'synthetic_reference_future_ticks':32,'synthetic_physical_total':129,'synthetic_future_total':97,'real_past_generator_ticks':640,'real_saved_prefix_passive_ticks':390,'real_study047_future_ticks':0,'real_new_or_replayed_physical_steps':0},
 'verification_result':{'status':'NOT_VERIFIED','claim_type':'TASK','claim':'TASK2.2核验实现与任务独立审查完成','gap':'R1：可中断预检超出统一总预算，并失去错误epoch保全；暂不批准。'},
 'files_sha256':files,'files_sha256_after':after,'summary':'独立科学重建及已有证据通过检查，但阶段预检位于计时/错误epoch边界之外，须修复后再审。'
}
path=Path(i.BASE+'verifier-review-initial.json')
with path.open('x') as f:json.dump(report,f,ensure_ascii=False,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps({'verdict':report['verdict'],'task':report['task'],'bindings':len(files),'path':str(path),'sha256':i.digest(path),'finding':'R1','real_future':0,'real_physics':0}))
