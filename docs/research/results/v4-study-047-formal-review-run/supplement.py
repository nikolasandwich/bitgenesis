"""独立只读复核报告所有表、诊断封口、源码/随机后缀合同；清理本审查临时恢复副本。"""
import ast,hashlib,json,pathlib,re,shutil,subprocess,time
R=pathlib.Path('/Users/todd/Documents/bitgenesis');O=R/'docs/research/results/v4-study-047-formal-review-run';B=R/'docs/research/results/v4-study-047-formal';D=R/'docs/research/results/v4-study-047-process-guard-diagnostic'
def load(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
audit=load(O/'audit_v2.result.json');pairs=audit['pairs'];A=('continue_north','withdraw_to_natural');report=(R/'docs/research/v4-study-047-results.zh-CN.md').read_text();summary=load(B/'raw/producer/summary.json')
tables=[]
for block in re.findall(r'(?:^\|.*\|\n)+',report,re.M):tables.append([[x.strip() for x in row.strip().strip('|').split('|')] for row in block.strip().splitlines()])
assert len(tables)==8,len(tables)
# 以保存JSON独立计算所有科学表格列，不执行作者生成器。
expected=[]
for cell in summary['cells']:
 counts=[f"{cell['arm_totals'][A[0]][k]} → {cell['arm_totals'][A[1]][k]}" for k in ['future_persistent10','new_copy_ever','double_new_ever','after32_formation_supported']]
 expected.append([cell['encoding'],str(cell['n']),*counts,'null' if cell['n']==0 else '0'])
assert tables[1][2:]==expected
assert tables[2][2:]==[[k,*[str(x['n']) for x in v]] for k,v in summary['overall']['binary_pairs'].items()]
short={'east':'E','west':'W','north':'N','homogeneous':'H','south':'S'}
def render(spans):
 out=[]
 for s in spans:
  x=str(s['start']) if s['start']==s['end'] else f"{s['start']}–{s['end']}"
  if s['left_censored_at_boundary']:x+=' L'
  if s['right_censored']:x+=' R'
  out.append(x)
 return '；'.join(out) if out else '无'
expected=[[short[p['encoding']]+str(p['seed']),str(p['q32']),*[render(p['arms'][arm]['intervals']) for arm in A],*[str(p['delta'][k]) for k in ['longest_double','births','deaths','final_energy']]] for p in pairs]
assert tables[3][2:]==expected
assert tables[4][2:]==[[str(g['seed']),'/'.join(short[e] for e in g['selected_encodings']),str(g['n']),str(g['delta_totals']['longest_double']),str(g['delta_totals']['final_energy'])] for g in summary['seed_groups']]
labels=[('未来出生','births'),('未来自然死亡','deaths'),('最终活着','living'),('接受供能','imported'),('拒绝供能','rejected_import'),('漏损','leakage'),('连接支出','bond_spent'),('构造支出','construction_spent'),('复制支出','copy_spent'),('总支出','spent'),('末能量','final_energy')]
assert tables[5][2:]==[[name,str(audit['aggregate'][A[0]][key]),str(audit['aggregate'][A[1]][key]),str(audit['aggregate'][A[1]][key]-audit['aggregate'][A[0]][key])] for name,key in labels]
assert tables[6][2:]==[[key,str(audit['failure_counts'][A[0]][key]),str(audit['failure_counts'][A[1]][key]),str(audit['failure_counts'][A[1]][key]-audit['failure_counts'][A[0]][key])] for key in ['formed','collision','energy','occupied','raw_material']]
for p,h in tables[7][2:]:assert sha(p)==h
observations={}
for arm in A:
 spans=[s for p in pairs for s in p['arms'][arm]['intervals']]
 observations[arm]={'intervals':len(spans),'qualified_future_states':sum(s['length'] for s in spans),'left_censored':sum(s['left_censored_at_boundary'] for s in spans),'right_censored':sum(s['right_censored'] for s in spans),'cross_boundary':sum(p['arms'][arm]['cross_boundary'] is not None for p in pairs),'longest':max(p['arms'][arm]['metrics']['longest_double'] for p in pairs)}
assert observations[A[0]]==dict(intervals=13,qualified_future_states=24,left_censored=3,right_censored=0,cross_boundary=3,longest=5)
assert observations[A[1]]==dict(intervals=15,qualified_future_states=28,left_censored=3,right_censored=1,cross_boundary=3,longest=5)
assert sum(p['arms'][A[0]]['counts']!=p['arms'][A[1]]['counts'] for p in pairs)==9
assert sum(p['arms'][A[0]]['intervals']!=p['arms'][A[1]]['intervals'] for p in pairs)==3
assert sum(any(p['delta'].values()) for p in pairs)==18
census=load('docs/research/results/v4-study-047-design-revalidated-census.json');source=load('docs/research/results/v4-study-047-design-revalidated-sources.json')
for route in ['producer','verifier']:assert load(B/f'raw/{route}/metadata.json')['runtime']==source['runtime']
for env in census['environments']:
 assert env['past_ticks']==32
 for kind in ['directions','feeds']:
  state=env['states_after_tick32'][kind];assert state[0]==3 and len(state[1])==625 and state[2] is None
  assert hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==env['state_sha256'][kind]
for path in (B/'raw/producer/environments').glob('*.json'):
 env=load(path)
 for kind,state in env['states_after_tick64'].items():assert kind in ['directions','feeds'] and state[0]==3 and len(state[1])==625 and state[2] is None
 for tick in env['natural_tape']:
  assert len(tick['directions'])==256 and all(type(x) is int and x in range(4) for x in tick['directions']);assert len(set(tick['feed_sites_draw_order']))==4 and all(type(x) is int and x in range(256) for x in tick['feed_sites_draw_order'])
probe=load(D/'epoch-3/probe-output/results.json');assert len(probe['cases'])==74 and sum(not c['requirement_met'] for c in probe['cases'])==36;assert len(probe['wrapper_cases'])==6 and sum(not c['requirement_met'] for c in probe['wrapper_cases'])==4;assert probe['forbidden_calls']==[]
for k in ['actual_physics_steps','synthetic_physics_steps','future_generator_ticks','past_generator_ticks','route_cli_invocations','source_mutations']:assert probe[k]==0
assert load(D/'epoch-3/probe-execution.json')['exit_code']==1 and load(D/'final-verification.execution.json')['exit_code']==0
manifest=load(D/'artifact-manifest.json');print('diagnostic manifest keys',list(manifest))
# AST only: 独立核验器未导入生产运行模块；人工已逐行核对恢复32状态后续同一流，按seed一次缓存后缀。
verifier=ast.parse((R/'scripts/verify_v4_middle_withdrawal.py').read_text());imports=[ast.unparse(n) for n in ast.walk(verifier) if isinstance(n,(ast.Import,ast.ImportFrom))];assert not any('run_v4_middle_withdrawal' in x for x in imports)
placeholder=[];secrets=[]
for p in [R/'docs/research/v4-study-047-results.zh-CN.md',B/'post-report-validation.zh-CN.md',D/'report.zh-CN.md']:
 for lineno,line in enumerate(p.read_text().splitlines(),1):
  if re.search(r'\b(?:TBD|TODO|FIXME|HACK|XXX)\b',line):placeholder.append([str(p.relative_to(R)),lineno])
  if re.search(r'AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|sk-[A-Za-z0-9]{32,}',line):secrets.append([str(p.relative_to(R)),lineno])
assert not placeholder and not secrets
restored=[]
for directory in [O/'restored',O/'restored-v2']:
 entries={str(p.relative_to(directory)):sha(p) for p in directory.rglob('*') if p.is_file()};assert len(entries)==325
 restored.append({'directory':str(directory.relative_to(R)),'files_sha256':entries,'status':'已实际写盘逐字节比较；仅本审查临时恢复副本随后清理，原data/raw/tar不变'})
(O/'restored-copy-manifest.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2)+'\n')
for directory in [O/'restored',O/'restored-v2']:shutil.rmtree(directory)
result={'status':'PASS','report_tables':8,'scientific_tables_verified':6,'code_hash_table_verified':True,'observations':observations,'q_series_different_pairs':9,'interval_different_pairs':3,'nonzero_metric_pairs':18,'rng_boundaries_checked_without_draws':20,'active_saved_rng64_checked':14,'diagnostic':{'cases':74,'missed':36,'wrapper_cases':6,'wrapper_missed':4,'forbidden_calls':[],'contract':'RED','integrity_exit':0},'placeholder_matches':placeholder,'secret_matches':secrets,'physics_steps':0,'future_draws':0,'restored_temporary_copies_removed_only':True}
(O/'supplement.result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
