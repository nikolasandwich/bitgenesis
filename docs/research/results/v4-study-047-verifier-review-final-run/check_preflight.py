"""独立复审控制面：真实临时Git/审批、同一绝对截止、0科学入口。"""
from contextlib import ExitStack
import hashlib,json,os,signal,subprocess,sys,tarfile,tempfile,time,traceback
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as i
from scripts import verify_v4_middle_withdrawal as v
out=Path(__file__).parent.resolve();observations=[];limit=2.;real_epoch=v.Epoch;actual_read=i.read
for mode in ('process_block','approval_block','shared_deadline','missing_approval_read','clean_gate'):
 with tempfile.TemporaryDirectory() as temporary, ExitStack() as patches:
  root=Path(temporary);previous=Path.cwd();observed=[];epochs=[];first=None;raised=None
  for name in ('inputs.py','producer.py','verifier.py','sources.json','census.json','method.json'):(root/name).write_text('{}\n')
  source_hashes={n:i.digest(root/n) for n in ('inputs.py','producer.py','verifier.py')}
  for name,task in (('producer-review.json','2.1'),('verifier-review.json','2.2')):
   (root/name).write_text(i.canonical(dict(verdict='APPROVED',task=task,independent_author_review=True,files_sha256=source_hashes,files_sha256_after=source_hashes)))
  for args in (('init','-q'),('add','.'),('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','-qm','synthetic review')):
   subprocess.run(['git',*args],cwd=root,capture_output=True,check=True)
  for k,value in dict(ROOT=root,BASE='',SOURCES='sources.json',CENSUS='census.json',REVIEW='method.json',NEW_CODE=('inputs.py','producer.py'),VERIFIER='verifier.py',SECONDS=limit).items():patches.enter_context(patch.object(i,k,value))
  patches.enter_context(patch.object(i,'runtime_paths',return_value=[]))
  forbidden={name:patches.enter_context(patch.object(v,name,side_effect=AssertionError('scientific entry forbidden'))) for name in ('draw_future','physical_step','restore_environment','reconstruct_pair','validate_producer')}
  def epoch_factory(*args,**kwargs):
   assert kwargs['seconds']==limit
   e=real_epoch(*args,**kwargs);epochs.append(e);return e
  patches.enter_context(patch.object(v,'Epoch',side_effect=epoch_factory))
  def process():
   observed.append(('process',list((root/'epoch').iterdir())))
   if mode=='process_block':time.sleep(5.)
   if mode=='shared_deadline':time.sleep(.7)
  patches.enter_context(patch.object(v,'check_no_other_process',side_effect=process))
  def read(p):
   nonlocal_placeholder=None
   if Path(p).name=='producer-review.json':
    if mode=='approval_block':time.sleep(5.)
    if mode=='shared_deadline':time.sleep(.95)
    if mode=='missing_approval_read':return actual_read(root/'unreadable-approval.json')
   return actual_read(p)
  patches.enter_context(patch.object(i,'read',side_effect=read))
  stop=SystemExit('approved clean preflight reached source closure')
  patches.enter_context(patch.object(i,'input_paths',side_effect=stop))
  os.chdir(root)
  start=time.monotonic()
  try:
   try:v.run('engineering',root/'producer-source',root/'epoch')
   except BaseException as error:raised=error
   elapsed=time.monotonic()-start
   assert raised is not None
   meta=actual_read(root/'epoch/metadata.json');failure=actual_read(root/'epoch/failure.json')
   assert meta['status']==failure['status']=='failed'
   assert meta['error']==failure['error']==repr(raised)
   assert meta['physical_steps']==meta['future_generator_ticks']==0
   assert len(epochs)==1 and epochs[0].guard.end==epochs[0].started+limit
   assert abs(epochs[0].guard.work_end-epochs[0].started-1.6)<1e-6
   assert not epochs[0].guard.installed and signal.getitimer(signal.ITIMER_REAL)==(0.,0.)
   assert observed[0][1]==[]
   assert all(mock.call_count==0 for mock in forbidden.values())
   if mode in ('process_block','approval_block','shared_deadline'):
    assert isinstance(raised,i.DeadlineExpired)
    assert elapsed<limit+.3
    assert meta['preflight_error']['type']=='DeadlineExpired'
   if mode=='clean_gate':
    assert raised is stop and meta['stage']=='source_capture'
    assert len(meta['input_sha256'])==8
   if mode=='missing_approval_read':
    assert isinstance(raised,FileNotFoundError)
    assert meta['preflight_error']['filename']==str(root/'unreadable-approval.json')
   observations.append({'case':mode,'result':'PASS','elapsed_seconds':elapsed,'stage':meta['stage'],'error_type':type(raised).__name__,'failed_metadata_and_failure':True,'total_limit_seconds':limit,'same_absolute_deadline':True,'empty_owned_directory_during_preflight':True,'science_call_counts':{n:m.call_count for n,m in forbidden.items()},'source_hashes_before':len(meta['input_sha256']),'source_hashes_after':len(meta['input_sha256_after'])})
  finally:
   os.chdir(previous)
   members={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
   (out/(mode+'-members.json')).write_text(json.dumps(members,sort_keys=True,separators=(',',':'))+'\n')
   with tarfile.open(out/(mode+'.tar.gz'),'x:gz') as archive:archive.add(root,arcname='repository')
result={'status':'PASS','checks':observations,'synthetic_future_ticks':0,'synthetic_physical_steps':0,'real_future_ticks':0,'real_physical_steps':0}
(out/'preflight-check.json').write_text(i.canonical(result)+'\n')
print(i.canonical(result))
