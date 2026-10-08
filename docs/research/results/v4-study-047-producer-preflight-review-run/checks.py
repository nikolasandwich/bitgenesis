"""Producer预检独立复审；仅控制面合成Git/I/O，全部科学入口禁止。"""
from contextlib import contextmanager,ExitStack
import hashlib,json,os,signal,subprocess,sys,tarfile,tempfile,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts import middle_withdrawal_inputs as i
from scripts import run_v4_middle_withdrawal as p
HERE=Path(__file__).resolve().parent
OBS=[]
def record(name,**data):
 row=dict(name=name,**data);OBS.append(row);print(json.dumps(row,ensure_ascii=False))
def sha(data):return hashlib.sha256(data).hexdigest()
def archive_check(path,expected):
 with tarfile.open(path,'r:gz') as t:
  actual={m.name:sha(t.extractfile(m).read()) for m in t.getmembers() if m.isfile()}
 i.same(actual,expected,'archive members '+str(path))
 return len(actual)
def verify_evidence():
 preservation=i.read('docs/research/results/v4-study-047-producer-preflight-preservation/preservation.json')
 for src,item in preservation['sources'].items():i.same(i.digest(item['archive']),item['sha256'],src)
 old=i.read(preservation['sources']['docs/research/results/v4-study-047-producer-review.json']['archive'])
 for src,h in old['files_sha256'].items():
  path=preservation['sources'].get(src,{}).get('archive',src);i.same(i.digest(path),h,src)
 current=i.bindings(include_verifier=False)
 localbase=Path('docs/research/results/v4-study-047-producer-preflight-implementation')
 ready=i.read(localbase/'review-ready.json');v=i.read(localbase/'final-validation-scaled.json')
 for src,h in ready['producer_code_sha256'].items():i.same(i.digest(src),h,src)
 i.same(v['code_sha256'],ready['producer_code_sha256'])
 joint=Path('docs/research/results/v4-study-047-preflight-joint-validation')
 full=i.read(joint/'full-revalidated/execution.json')
 i.same(full['files_sha256'],full['files_sha256_after'])
 for src,h in full['files_sha256'].items():
  i.same(i.digest(src),h,src)
  i.same(i.digest(joint/'full-revalidated'/Path(src).name),h,'frozen snapshot')
 for name,h in full['raw_output_sha256'].items():i.same(i.digest(joint/'full-revalidated'/name),h,name)
 assert full['exit_code']==0
 raw=(joint/'full-revalidated/stderr.bin').read_text();assert 'Ran 1070 tests in 77.334s' in raw and raw.rstrip().endswith('OK')
 archive_counts={}
 for name in ('archive-map.json','archive-map-scaled.json'):
  mapping=i.read(localbase/name);i.same(i.digest(mapping['archive']),mapping['archive_sha256'])
  archive_counts[name]=archive_check(mapping['archive'],mapping['archive_member_sha256'])
 mapping=i.read(joint/'full-revalidated/producer-runtime-preservation.json')
 i.same(i.digest(mapping['archive']),mapping['archive_sha256'])
 with tarfile.open(mapping['archive'],'r:gz') as t:
  members={m.name:sha(t.extractfile(m).read()) for m in t.getmembers() if m.isfile()}
 # 该归档以各合成test名称为根目录。
 i.same(members,mapping['files'],'joint preserved temporary git epochs')
 archive_counts['joint-producer-runtime']=len(members)
 paths=set(current)|set(ready['producer_code_sha256'])
 # 上轮完整绑定已验证，改绑旧源码档案；不再绑定将更新的canonical审批。
 for src in old['files_sha256']:
  paths.add(preservation['sources'].get(src,{}).get('archive',src))
 for dirname in ('docs/research/results/v4-study-047-producer-preflight-preservation','docs/research/results/v4-study-047-producer-preflight-audit','docs/research/results/v4-study-047-producer-preflight-implementation','docs/research/results/v4-study-047-preflight-joint-validation'):
  for q in Path(dirname).rglob('*'):
   if q.is_file() and '__pycache__' not in str(q) and '.git' not in q.parts:
    paths.add(str(q))
 paths.discard('docs/research/results/v4-study-047-producer-review.json')
 for forbidden in ('scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py'):
  assert forbidden not in paths
 hashes,errors,first=i.capture(paths);assert first is None and not errors
 (HERE/'initial-bindings.json').write_text(json.dumps(hashes,indent=2)+'\n')
 record('immutable_evidence',current_sources=len(current),old_approval_bindings=len(old['files_sha256']),review_bindings=len(hashes),archives=archive_counts,full_suite=1070,full_suite_seconds=77.334,live_verifier_not_bound=True)

@contextmanager
def fixture(label):
 with tempfile.TemporaryDirectory() as d,ExitStack() as stack:
  root=Path(d).resolve();old=Path.cwd()
  for name in ('inputs.py','producer.py','verifier.py','sources.json','census.json','method.json'):(root/name).write_text('{}')
  hashes={name:i.digest(root/name) for name in ('inputs.py','producer.py','verifier.py')}
  for name,task in (('producer-review.json','2.1'),('verifier-review.json','2.2')):
   (root/name).write_text(json.dumps(dict(verdict='APPROVED',task=task,independent_author_review=True,files_sha256=hashes,files_sha256_after=hashes)))
  for args in (('init','-q'),('add','.'),('-c','user.name=ReviewFixture','-c','user.email=review@example.invalid','-c','commit.gpgsign=false','commit','-qm','synthetic evidence')):
   subprocess.run(['git',*args],cwd=root,check=True,capture_output=True)
  for key,val in dict(ROOT=root,BASE='',SOURCES='sources.json',CENSUS='census.json',REVIEW='method.json',NEW_CODE=('inputs.py','producer.py'),VERIFIER='verifier.py').items():stack.enter_context(patch.object(i,key,val))
  stack.enter_context(patch.object(i,'runtime_paths',return_value=[]))
  stack.enter_context(patch.object(p,'check_no_other_process'))
  forbidden=[stack.enter_context(patch.object(p,name,side_effect=AssertionError('science forbidden'))) for name in ('step','future_tape','run_pair','restore_environment')]
  os.chdir(root)
  try:yield root
  finally:
   os.chdir(old)
   with tarfile.open(HERE/(label+'.tar.gz'),'w:gz') as t:t.add(root,arcname=label)
   for fn in forbidden:fn.assert_not_called()

def check_timeout(label,which):
 original_read=i.read;actual_check=subprocess.check_output
 with fixture(label) as root,patch.object(i,'SECONDS',2.0),ExitStack() as stack:
  if which=='process':stack.enter_context(patch.object(p,'check_no_other_process',side_effect=lambda:time.sleep(5)))
  elif which=='approval':
   def slow_read(path):
    if Path(path).name=='producer-review.json':time.sleep(5)
    return original_read(path)
   stack.enter_context(patch.object(i,'read',side_effect=slow_read))
  elif which=='git':
   def slow_check(command,*a,**k):
    if command==['git','rev-parse','HEAD']:time.sleep(5)
    return actual_check(command,*a,**k)
   stack.enter_context(patch.object(subprocess,'check_output',side_effect=slow_check))
  started=time.monotonic();error=None
  try:p.run('engineering',root/'run')
  except i.DeadlineExpired as caught:error=caught
  elapsed=time.monotonic()-started
  assert error is not None and elapsed<2.1
  meta=original_read(root/'run/metadata.json');proof=original_read(root/'run/failure.json')
  assert meta['status']==proof['status']=='failed' and meta['error']==proof['error']==repr(error)
  assert meta['physical_steps']==meta['future_generator_ticks']==0
  assert signal.getitimer(signal.ITIMER_REAL)==(0.,0.)
  if which!='git':assert meta['input_sha256']==meta['input_sha256_after'] and len(meta['input_sha256'])==8
  record(label,elapsed=elapsed,budget=2.0,stage=meta['stage'],disk_status=meta['status'],proof_status=proof['status'],sources=len(meta['input_sha256']),science_calls=0)

def check_clean_and_first():
 stop=SystemExit('after clean preflight before science')
 with fixture('clean-gate') as root,patch.object(i,'input_paths',side_effect=stop):
  try:p.run('engineering',root/'run')
  except SystemExit as caught:assert caught is stop
  else:raise AssertionError('source closure must stop')
  meta=i.read(root/'run/metadata.json');assert meta['preflight_status']=='passed' and meta['status']=='failed'
  record('actual_clean_gate',passed=True,status=meta['status'],source_bindings=len(meta['input_sha256']),science_calls=0)
 first=KeyboardInterrupt('approval first');late=SystemExit('later hash');original=i.read
 with fixture('first-exception') as root:
  def fail(path):
   if Path(path).name=='producer-review.json':raise first
   return original(path)
  with patch.object(i,'read',side_effect=fail),patch.object(p.Epoch,'output_hashes',side_effect=late):
   try:p.run('engineering',root/'run')
   except KeyboardInterrupt as caught:assert caught is first
   else:raise AssertionError('first exception missing')
  meta=original(root/'run/metadata.json');proof=original(root/'run/failure.json')
  assert meta['error']==proof['error']==repr(first) and meta['finalization_errors']['output_hashes']==repr(late)
  record('first_exception_with_later_closing_failure',first_preserved=True,secondary_preserved=True,status=meta['status'],science_calls=0)

verify_evidence()
check_timeout('process-timeout','process')
check_timeout('approval-timeout','approval')
check_timeout('git-revision-timeout','git')
check_clean_and_first()
assert i.SECONDS==600
assert not (ROOT/'data/v4-study-047').exists()
(HERE/'observations.json').write_text(json.dumps(dict(observations=OBS,synthetic_physics=0,synthetic_future_ticks=0,real_study047_future_physics=0,real_study047_future_ticks=0),indent=2,ensure_ascii=False)+'\n')
