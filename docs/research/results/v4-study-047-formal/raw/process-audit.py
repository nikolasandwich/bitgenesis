"""Supplemental read-only, case-insensitive snapshot of Study047 processes."""
from pathlib import Path
import datetime,json,re,shlex,subprocess,sys
root=Path('/Users/todd/Documents/bitgenesis');matches=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
 fields=line.strip().split(None,3)
 if len(fields)!=4: continue
 try: words=shlex.split(fields[3])
 except ValueError: continue
 if not words: continue
 names={'run_v4_middle_withdrawal.py','verify_v4_middle_withdrawal.py'}
 direct=Path(words[0]).name in names
 python=re.fullmatch(r'(?:python|pypy)(?:[0-9]+(?:\.[0-9]+)*)?(?:\.exe)?',Path(words[0]).name,re.I)
 if direct or (python and any(Path(w).name in names or w in {'scripts.run_v4_middle_withdrawal','scripts.verify_v4_middle_withdrawal'} for w in words[1:])):
  matches.append(dict(pid=int(fields[0]),ppid=int(fields[1]),elapsed=fields[2],command=words))
result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),case_insensitive=True,matches=matches,scope='当前只读进程快照；不能回溯证明启动时全部进程。',finding='外层wrapper与已批准两CLI的解释器匹配为小写，macOS实际ps显示Python大写；本快照补充当前状态，不改源码、不重跑。')
p=root/sys.argv[1]
with p.open('x') as out:json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps(result,ensure_ascii=False))
