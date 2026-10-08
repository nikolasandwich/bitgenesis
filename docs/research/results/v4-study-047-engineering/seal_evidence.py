"""Seal engineering evidence without performing any science or changing raw data."""
from pathlib import Path
import datetime, hashlib, json, subprocess, tarfile, time
ROOT=Path('/Users/todd/Documents/bitgenesis');DEST=ROOT/'docs/research/results/v4-study-047-engineering';BASE=ROOT/'data/v4-study-047-engineering';REPORT=ROOT/'docs/research/v4-study-047-engineering.zh-CN.md'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
started=time.monotonic();archive=read(DEST/'archive-manifest.json');audit=read(DEST/'raw/audit.json');pre=read(BASE/'preflight.json')
assert archive['status']==audit['status']=='PASS'
assert archive['original_file_count']==archive['restored_file_count']==236
assert sha(ROOT/archive['archive_path'])==archive['archive_sha256']
assert len(archive['entries'])==len([p for p in BASE.rglob('*') if p.is_file()])
with tarfile.open(ROOT/archive['archive_path'],'r:gz') as tar:
 for e in archive['entries']:
  s=ROOT/e['source'];d=ROOT/e['archive_copy'];data=tar.extractfile(e['member']).read()
  assert s.read_bytes()==d.read_bytes()==data and len(data)==e['bytes'] and sha(s)==sha(d)==e['sha256'] and e['restored_bytes_equal']
for path,h in pre['git_tracked_sha256'].items():assert sha(ROOT/path)==h,path
for role,x in audit['routes'].items():
 m=read(BASE/role/'metadata.json');assert m['input_sha256']==m['input_sha256_after']
 for path,h in m['input_sha256'].items():assert sha(ROOT/path)==h,path
for role,entry in pre['reviews'].items():
 assert sha(ROOT/entry['path'])==entry['sha256'];review=read(ROOT/entry['path'])
 assert review['files_sha256']==review['files_sha256_after']
 for path,h in review['files_sha256'].items():assert sha(ROOT/path)==h,path
# Verify the mask against saved inputs, including cases where a target is empty.
case=read(BASE/'producer/cases/east-120005.json');counts={}
for arm in ('continue_north','withdraw_to_natural'):
 previous=case[arm]['initial']['units'];empty=0;changed=0
 for row,tape in zip(case[arm]['rows'],case['natural_tape']):
  directions=row['physical']['directions'];expected=tape['directions'][:]
  if arm=='continue_north':expected[101]=expected[102]=3
  assert type(directions) is list and directions==expected
  for site in (101,102):
   if previous[site] is None:empty+=1
   if directions[site]!=tape['directions'][site]:changed+=1
  previous=row['physical']['units']
 counts[arm]=dict(all_32_by_256_directions_verified=True,mask_applied_without_occupancy_condition=(arm=='continue_north'),target_positions_empty_at_start_of_step=empty,target_direction_values_changed_from_natural=changed)
assert counts['withdraw_to_natural']['target_direction_values_changed_from_natural']==0
assert counts['continue_north']['target_direction_values_changed_from_natural']>0
checks={}
for label,cmd in [('tracked_diff',['git','diff','--exit-code']),('tracked_whitespace',['git','diff','--check'])]:
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True);assert p.returncode==0
 checks[label]=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode(),scope='原Git跟踪文件；另对本轮新写文本做显式检查。')
new_text=[REPORT,DEST/'seal_evidence.py']+[DEST/'raw'/name for name in ['task-brief.zh-CN.md','execution_runner.py','evidence_audit.py','evidence_audit_v2.py','archive_evidence.py']]
for p in new_text:
 for line in p.read_bytes().splitlines():assert line.rstrip(b' \t')==line,(str(p),'trailing whitespace')
 assert all(marker not in p.read_text() for marker in ('TO'+'DO','FIX'+'ME','T'+'BD'))
status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
assert all(line.startswith('?? docs/research/results/v4-study-047-engineering/') or line=='?? docs/research/v4-study-047-engineering.zh-CN.md' for line in status.splitlines()),status
assert not (ROOT/'data/v4-study-047').exists()
with (DEST/'git-status-before-seal.txt').open('x') as out:out.write(status)
files=[p for p in sorted(DEST.rglob('*')) if p.is_file()]+[REPORT]
summary=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='READY_FOR_REVIEW',task='2.3',boundary='EngineeringIntegration',requirements=['2.3','3.1','3.2','3.3','4.1','4.2','4.3'],design_sections=['架构及流程','组件、接口与需求追踪','数据和连续状态合同','指标和完整账','失败、预算与测试策略'],independent_engineering_review_completed=False,parent_completion_verification_completed=False,task_complete=False,formal_authorized_by_this_record=False,commit=pre['git']['commit'],original_tracked_files_unchanged=True,raw_evidence_frozen=True,raw_member_count=236,raw_original_bytes=archive['original_bytes'],archive_bytes=archive['archive_bytes'],archive_sha256=archive['archive_sha256'],archive_manifest_sha256=sha(DEST/'archive-manifest.json'),raw_audit_sha256=sha(DEST/'raw/audit.json'),report_sha256=sha(REPORT),engineering_evidence={r:str((DEST/'raw'/r/'metadata.json').relative_to(ROOT)) for r in ('producer','verifier')},source_current_approval_bindings_verified={r:x['verified_bindings'] for r,x in pre['reviews'].items()},complete_scientific_artifacts=audit['complete_scientific_artifacts'],actual_execution_counts=audit['current_task_counts'],real_total_physical_steps=128,real_total_future_generator_ticks=64,past_generator_ticks_per_route=640,reused_regression_tests=1070,reused_regression_exit_code=0,reused_regression_internal_seconds=77.334,new_tests_or_synthetic_science_executed=False,reused_validation=audit['reused_validation'],source_snapshot_count=len(pre['source_snapshots']),saved_input_policy_checks=counts,storage=audit['routes'],real_cli_failures=0,real_cli_reruns=0,supplemental_audit_failure=dict(count=1,path=str((DEST/'raw/post-check/execution.json').relative_to(ROOT)),script_preserved=True,raw_exit1_preserved=True,cause='证据检查器把boundary.final来源引用误当状态对象；只修正检查器，未改科学源码或数据。',corrected_execution=str((DEST/'raw/post-check-v2/execution.json').relative_to(ROOT)),corrected_exit_code=0,new_scientific_steps=0),checks=checks,new_authored_text_whitespace_checked=[str(p.relative_to(ROOT)) for p in new_text],historical_source_snapshots_kept_verbatim=True,formal_directory_exists=False,remaining_gate='新上下文独立工程审查、父层kiro-verify-completion及干净提交；之后才可任务3.1。',files_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},files_sha256_scope='本清单封口前存在的全部工程归档文件及报告；本清单自身和封口命令随后生成的输出由后续独立审查绑定，避免自引用。',elapsed_seconds=time.monotonic()-started)
with (DEST/'validation-summary.json').open('x',encoding='utf-8') as out:json.dump(summary,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps({k:summary[k] for k in ['status','raw_member_count','real_total_physical_steps','real_total_future_generator_ticks','source_snapshot_count','saved_input_policy_checks','elapsed_seconds']},ensure_ascii=False))
