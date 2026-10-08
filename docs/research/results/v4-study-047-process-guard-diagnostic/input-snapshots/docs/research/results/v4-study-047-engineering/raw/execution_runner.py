"""Engineering evidence wrapper; no scientific imports or extra simulation."""
from pathlib import Path
import datetime, hashlib, json, os, shlex, subprocess, sys, time
ROOT = Path('/Users/todd/Documents/bitgenesis')
BASE = ROOT / 'data/v4-study-047-engineering'
COMMIT = '931dd9e70f6b89813635f7d25e74cdc8cf42e0bf'
REVIEWS = {
 'producer': ('74ac9792ea57ae793665a610649adc790cf39f0a858c8908978b7d8d86828754', 1985),
 'verifier': ('bf7180e688208e5af27274d01e4ff900966a965e9688fa9b9d05ee7e46e7057e', 3023),
}
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, obj):
 with Path(path).open('x', encoding='utf-8') as out: json.dump(obj, out, ensure_ascii=False, indent=2); out.write('\n')
def command(args): return subprocess.check_output(args, cwd=ROOT, text=True)
def git_state(): return dict(commit=command(['git','rev-parse','HEAD']).strip(), origin_main=command(['git','rev-parse','origin/main']).strip(), status=command(['git','status','--porcelain']))
def files_state():
 return {name:digest(ROOT/name) for name in command(['git','ls-files']).splitlines() if (ROOT/name).is_file()}
def process_state():
 matching=[]
 for line in command(['ps','-axo','pid=,ppid=,command=']).splitlines():
  fields=line.strip().split(None,2)
  if len(fields)!=3: continue
  try: words=shlex.split(fields[2])
  except ValueError: continue
  if words and (Path(words[0]).name in {'run_v4_middle_withdrawal.py','verify_v4_middle_withdrawal.py'} or (Path(words[0]).name.startswith(('python','pypy')) and len(words)>1 and (Path(words[1]).name in {'run_v4_middle_withdrawal.py','verify_v4_middle_withdrawal.py'} or any(x in {'scripts.run_v4_middle_withdrawal','scripts.verify_v4_middle_withdrawal'} for x in words[1:])))):
   matching.append(dict(pid=int(fields[0]),ppid=int(fields[1]),command=fields[2]))
 return matching

def initialize():
 state=git_state(); assert state==dict(commit=COMMIT,origin_main=COMMIT,status=''),state
 assert not (ROOT/'data/v4-study-047').exists()
 assert not (BASE/'producer').exists() and not (BASE/'verifier').exists()
 processes=process_state(); assert not processes,processes
 reviews={}; source_paths=set()
 for role,(expected,count) in REVIEWS.items():
  path=ROOT/f'docs/research/results/v4-study-047-{role}-review.json'; assert digest(path)==expected
  obj=json.loads(path.read_bytes()); assert obj['verdict']=='APPROVED' and obj['independent_author_review'] is True
  assert obj['files_sha256']==obj['files_sha256_after'] and len(obj['files_sha256'])==count
  for name,h in obj['files_sha256'].items():
   assert digest(ROOT/name)==h,name
   if name.endswith('.py') and name.startswith(('scripts/','src/','tests/')): source_paths.add(name)
  reviews[role]=dict(path=str(path.relative_to(ROOT)),sha256=expected,verified_bindings=count)
 full=ROOT/'docs/research/results/v4-study-047-preflight-joint-validation/full-revalidated'
 ex=json.loads((full/'execution.json').read_bytes()); assert ex['exit_code']==0
 assert ex['files_sha256']==ex['files_sha256_after']
 for name,h in ex['files_sha256'].items():
  assert digest(ROOT/name)==h and digest(full/Path(name).name)==h,name
 for name,h in ex['raw_output_sha256'].items(): assert digest(full/name)==h,name
 reuse=dict(execution=str((full/'execution.json').relative_to(ROOT)),execution_sha256=digest(full/'execution.json'),current_source_bindings=ex['files_sha256'],raw_output_sha256=ex['raw_output_sha256'],exit_code=0,wall_seconds=ex['wall_seconds'],tests=1070,test_seconds=77.334,reexecuted=False)
 for name in ['AGENTS.md','pyproject.toml','experiments/v4/study-047.md','.kiro/specs/middle-policy-withdrawal/spec.json','.kiro/specs/middle-policy-withdrawal/tasks.md','.kiro/specs/middle-policy-withdrawal/requirements.md','.kiro/specs/middle-policy-withdrawal/design.md']: source_paths.add(name)
 snapshots={}
 for name in sorted(source_paths):
  target=BASE/'source-snapshots'/name; target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as out: out.write((ROOT/name).read_bytes())
  snapshots[name]=dict(snapshot=str(target.relative_to(BASE)),sha256=digest(target),bytes=target.stat().st_size)
 write(BASE/'preflight.json',dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),git=state,active_route_processes=processes,reviews=reviews,reused_full_regression=reuse,source_snapshots=snapshots,git_tracked_sha256=files_state(),formal_directory_exists=False,task_brief_sha256=digest(BASE/'task-brief.zh-CN.md'),runner_sha256=digest(__file__)))
 with (BASE/'git-show.txt').open('xb') as out: out.write(subprocess.check_output(['git','show','--no-patch','--format=fuller',COMMIT],cwd=ROOT))
 print(json.dumps(dict(status='preflight_passed',source_snapshots=len(snapshots),reviews=reviews)))

def run_route(role):
 assert role in REVIEWS
 p=json.loads((BASE/'preflight.json').read_bytes()); assert files_state()==p['git_tracked_sha256']
 state=git_state(); assert state==dict(commit=COMMIT,origin_main=COMMIT,status=''),state
 processes=process_state(); assert not processes,processes
 assert not (ROOT/'data/v4-study-047').exists()
 assert not (BASE/role).exists()
 if role=='verifier':
  previous=json.loads((BASE/'execution/producer/result.json').read_bytes()); assert previous['exit_code']==0
  meta=json.loads((BASE/'producer/metadata.json').read_bytes()); assert (meta['status'],meta['physical_steps'],meta['future_generator_ticks'],meta['completed_pairs'])==('complete',64,32,1)
 exdir=BASE/'execution'/role; exdir.mkdir(parents=True,exist_ok=False)
 script='scripts/run_v4_middle_withdrawal.py' if role=='producer' else 'scripts/verify_v4_middle_withdrawal.py'
 args=['.venv/bin/python',script,'--mode','engineering']
 if role=='verifier': args+=['--producer','data/v4-study-047-engineering/producer']
 args+=['--output',f'data/v4-study-047-engineering/{role}']
 env={k:os.environ[k] for k in ('PATH','HOME','TMPDIR','LANG') if k in os.environ}; env['PYTHONPATH']='src'
 before={name:digest(ROOT/name) for name in p['source_snapshots']}
 request=dict(command=args,display_command='PYTHONPATH=src '+shlex.join(args),cwd=str(ROOT),environment=env,environment_is_complete=True,git_before=state,active_route_processes=processes,source_sha256_before=before,runner_sha256=digest(__file__),task_brief_sha256=digest(BASE/'task-brief.zh-CN.md'),started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scientific_invocation_ordinal=1)
 write(exdir/'request.json',request)
 started=time.monotonic()
 with (exdir/'stdout.bin').open('xb') as stdout, (exdir/'stderr.bin').open('xb') as stderr:
  result=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
 elapsed=time.monotonic()-started
 after={name:digest(ROOT/name) for name in before}
 record=dict(exit_code=result.returncode,wall_seconds=elapsed,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),git_after=git_state(),source_sha256_after=after,source_unchanged=before==after,all_git_tracked_unchanged=files_state()==p['git_tracked_sha256'],raw_output_sha256={name:digest(exdir/name) for name in ('stdout.bin','stderr.bin')},active_route_processes_after=process_state(),formal_directory_exists=(ROOT/'data/v4-study-047').exists())
 write(exdir/'result.json',record)
 print(json.dumps(dict(role=role,**{k:record[k] for k in ('exit_code','wall_seconds','source_unchanged','all_git_tracked_unchanged')})))
 print((exdir/'stdout.bin').read_text(errors='replace'))
 if result.returncode: print((exdir/'stderr.bin').read_text(errors='replace')); raise SystemExit(result.returncode)
 assert before==after and record['all_git_tracked_unchanged'] and record['git_after']['status']==''

if __name__=='__main__':
 action=sys.argv[1]
 if action=='initialize': initialize()
 else: run_route(action)
