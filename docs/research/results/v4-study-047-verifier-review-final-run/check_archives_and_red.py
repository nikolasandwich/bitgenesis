"""逐成员校验独立fixture归档和作者R1原始执行证据。"""
import hashlib,json,re,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as i
root=Path(__file__).parent
archives=[]
for p in root.rglob('*.tar.gz'):
 manifest=i.read(p.with_name(p.name[:-7]+'-members.json'))
 with tarfile.open(p,'r:gz') as t:
  actual={m.name.removeprefix('repository/'):hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t.getmembers() if m.isfile()}
 i.same(actual,manifest,'独立Git fixture逐成员归档')
 archives.append({'path':str(p),'members':len(actual),'sha256':i.digest(p)})
a=i.read(i.BASE+'verifier-implementation/final-validation-remediated.json')
executions=[]
for declared in a['executions']:
 p=Path(declared['evidence']);e=i.read(p)
 for k in ('command','exit_code','files_sha256','raw_output_sha256'):
  i.same(e[k],declared[k],'R1原始执行/'+k)
 for name,h in e['raw_output_sha256'].items():assert i.digest(p.parent/name)==h
 for name,h in e['files_sha256'].items():assert i.digest(p.parent/Path(name).name)==h
 stderr=(p.parent/'stderr.bin').read_text(errors='replace')
 executions.append({'path':str(p),'exit_code':e['exit_code'],'summary':stderr[-240:]})
red=[e for e in executions if 'remediation-1-red/' in e['path']];assert len(red)==1 and red[0]['exit_code']==1
# Timing-only test adjustment: current implementation is byte-identical to
# the initial joint run; only synthetic timeout scales changed afterwards.
old=i.read(i.BASE+'preflight-joint-validation/full/execution.json')
new=i.read(i.BASE+'preflight-joint-validation/full-revalidated/execution.json')
assert old['files_sha256']['scripts/verify_v4_middle_withdrawal.py']==new['files_sha256']['scripts/verify_v4_middle_withdrawal.py']
assert old['files_sha256']['scripts/run_v4_middle_withdrawal.py']==new['files_sha256']['scripts/run_v4_middle_withdrawal.py']
result={'status':'PASS','archive_count':len(archives),'archive_members':sum(x['members'] for x in archives),'archives':archives,'executions':executions,'timer_scale_assessment':'真实600秒/30秒及两条路线实现不变；合成2秒/5秒使fork和失败I/O留出实际调度余量。原失败原字节保留，不冒称完整保全已删除的Producer临时目录。'}
(root/'archive-red-check.json').write_text(i.canonical(result)+'\n')
print(i.canonical({'status':result['status'],'archive_count':len(archives),'archive_members':result['archive_members'],'executions':len(executions),'red':red}))
