"""Final read-only artifact checks; no research imports or simulation."""
from pathlib import Path
import ast,hashlib,json,re,subprocess
R=Path('/Users/todd/Documents/bitgenesis');B=R/'data/v4-study-047';D=R/'docs/research/results/v4-study-047-formal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
m=read(D/'archive-manifest.json');pre=read(B/'preflight.json');a=read(B/'audit.json')
assert sha(R/m['archive_path'])==m['archive_sha256']
assert sorted(str(p.relative_to(B)) for p in B.rglob('*') if p.is_file())==sorted(e['member'] for e in m['entries'])
for e in m['entries']:
 assert sha(R/e['source'])==sha(R/e['archive_copy'])==e['sha256'];assert (R/e['source']).read_bytes()==(R/e['archive_copy']).read_bytes();assert e['restored_bytes_equal']
for name,h in pre['git_tracked_sha256'].items():assert sha(R/name)==h,name
for role in ('producer','verifier'):
 meta=read(B/role/'metadata.json')
 for name,h in meta['input_sha256'].items():assert sha(R/name)==h,name
 for name,h in meta['output_sha256'].items():assert sha(B/role/name)==h,name
report=R/'docs/research/v4-study-047-results.zh-CN.md';assert sha(report)=='151ed1ed9ba760585dd3d63262f6e25d87bfddf9fcfcb91c669a177d537b2d4d'
parsed=0;authored=[];snapshot_waivers=[]
for p in D.rglob('*'):
 if not p.is_file():continue
 if p.suffix=='.json':read(p);parsed+=1
 if p.suffix=='.py':ast.parse(p.read_bytes(),filename=str(p))
 if p.suffix in ('.py','.md'):
  if 'source-snapshots' in p.parts:snapshot_waivers.append(str(p.relative_to(R)));continue
  authored.append(p)
authored.append(report)
for p in authored:
 text=p.read_text();assert text.endswith('\n'),str(p)
 assert not any(line.rstrip()!=line for line in text.splitlines()),str(p)
 assert not re.search(r'\b(?:TODO|TBD|FIXME)\b',text),str(p)
missing=[]
for link in re.findall(r'\]\(([^)]+)\)',report.read_text()):
 if '://' not in link and not (report.parent/link.split('#')[0]).exists():missing.append(link)
assert missing==['results/v4-study-047-formal/validation-summary.json'],missing
assert sha(B/'parent-preflight-observation.json')==sha(R/'data/v4-study-047-parent-preflight-observation.json')
assert [p.name for p in sorted((B/'execution').iterdir())]==['producer','verifier']
assert subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
print(json.dumps(dict(status='PASS',archive_original_raw_pairs_verified=len(m['entries']),archive_bytes=m['archive_bytes'],original_tracked_files_verified=len(pre['git_tracked_sha256']),json_files_parsed=parsed,authored_text_files_checked=len(authored),source_snapshot_files_kept_original_bytes=len(snapshot_waivers),report_sha256=sha(report),pending_seal_link=missing,scientific_steps=0,other_agent_expected_output='docs/research/results/v4-study-047-process-guard-diagnostic/',scope='不修改原件；只验证作者边界，诊断agent目录不纳入作者封口。'),ensure_ascii=False))
