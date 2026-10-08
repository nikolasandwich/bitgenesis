"""Archive immutable formal evidence; restore every original byte."""
from pathlib import Path
import datetime, gzip, hashlib, json, tarfile, tempfile, time
ROOT=Path('/Users/todd/Documents/bitgenesis')
SOURCE=ROOT/'data/v4-study-047'
DEST=ROOT/'docs/research/results/v4-study-047-formal'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
started=time.monotonic()
assert json.loads((SOURCE/'audit.json').read_bytes())['status']=='PASS'
for role,status in [('producer','complete'),('verifier','verified')]:
 assert json.loads((SOURCE/role/'metadata.json').read_bytes())['status']==status
 assert json.loads((SOURCE/'execution'/role/'result.json').read_bytes())['exit_code']==0
assert DEST.is_dir() and not (DEST/'raw').exists()
files=[p for p in sorted(SOURCE.rglob('*')) if p.is_file()]
assert all(not p.is_symlink() for p in files)
entries=[]
for p in files:
 rel=p.relative_to(SOURCE);q=DEST/'raw'/rel;q.parent.mkdir(parents=True,exist_ok=True)
 payload=p.read_bytes()
 with q.open('xb') as out: assert out.write(payload)==len(payload)
 assert q.read_bytes()==payload
 entries.append(dict(source=str(p.relative_to(ROOT)),archive_copy=str(q.relative_to(ROOT)),member=str(rel),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
archive=DEST/'formal-evidence.tar.gz'
with archive.open('xb') as binary:
 with gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as compressed:
  with tarfile.open(fileobj=compressed,mode='w') as tar:
   for entry in entries:
    p=ROOT/entry['source'];info=tar.gettarinfo(str(p),arcname=entry['member']);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
    with p.open('rb') as stream: tar.addfile(info,stream)
restored=0
with tempfile.TemporaryDirectory(prefix='study047-formal-restore-') as temp:
 target=Path(temp)
 with tarfile.open(archive,'r:gz') as tar:
  members=tar.getmembers();assert [m.name for m in members]==[e['member'] for e in entries]
  for member,entry in zip(members,entries):
   assert member.isfile() and member.size==entry['bytes'];out=target/member.name;assert out.resolve().is_relative_to(target.resolve())
   out.parent.mkdir(parents=True,exist_ok=True)
   with tar.extractfile(member) as stream: payload=stream.read()
   with out.open('xb') as stream: assert stream.write(payload)==len(payload)
   assert len(payload)==entry['bytes'] and sha(out)==entry['sha256']
   assert out.read_bytes()==(ROOT/entry['source']).read_bytes()==(ROOT/entry['archive_copy']).read_bytes()
   entry['restored_bytes_equal']=True;restored+=1
assert [str(p.relative_to(SOURCE)) for p in sorted(SOURCE.rglob('*')) if p.is_file()]==[e['member'] for e in entries]
for entry in entries: assert sha(ROOT/entry['source'])==sha(ROOT/entry['archive_copy'])==entry['sha256']
manifest=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',original_root=str(SOURCE.relative_to(ROOT)),original_files_untouched=True,archive_path=str(archive.relative_to(ROOT)),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),original_file_count=len(entries),original_bytes=sum(e['bytes'] for e in entries),restored_file_count=restored,restore_method='逐文件从gzip tar读取，在新临时目录写出后比较原文件、直接归档副本和恢复文件的完整bytes/sha256/size；临时恢复副本删除，原数据未移动或覆盖。',entries=entries,elapsed_seconds=time.monotonic()-started,new_scientific_steps=0)
with (DEST/'archive-manifest.json').open('x',encoding='utf-8') as out: json.dump(manifest,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps({k:manifest[k] for k in ['status','archive_bytes','archive_sha256','original_file_count','original_bytes','restored_file_count','elapsed_seconds']},ensure_ascii=False))
