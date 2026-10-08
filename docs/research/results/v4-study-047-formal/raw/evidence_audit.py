"""Read-only formal evidence audit, adapted from approved engineering audit."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import datetime, hashlib, json, subprocess, time
ROOT=Path('/Users/todd/Documents/bitgenesis'); BASE=ROOT/'data/v4-study-047'
ARMS=('continue_north','withdraw_to_natural'); ENCODINGS=('east','west','south','north','homogeneous')
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(o): return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
nodes=0
def strict(a,b,label='object'):
 global nodes
 nodes+=1
 assert type(a) is type(b),(label,'type',type(a),type(b))
 if type(a) is dict:
  assert a.keys()==b.keys(),(label,'keys')
  for k in a: strict(a[k],b[k],label+'/'+k)
 elif type(a) is list:
  assert len(a)==len(b),(label,'length')
  for i,(x,y) in enumerate(zip(a,b)): strict(x,y,label+'/'+str(i))
 else: assert a==b,(label,'value',a,b)
def checked_hashes(mapping):
 for path,h in mapping.items(): assert sha(ROOT/path)==h,path
 return len(mapping)
def file_record(p): return dict(bytes=p.stat().st_size,sha256=sha(p))
def deref(ref):
 p=ROOT/ref['path']; assert sha(p)==ref['sha256'],ref['path']; o=read(p)
 for key in ref['pointer'].split('/')[1:]: o=o[int(key)] if type(o) is list else o[key]
 assert canonical(o)==ref['value_sha256']; return o
started=time.monotonic(); pre=read(BASE/'preflight.json')
assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)==''
checked_hashes(pre['git_tracked_sha256'])
roles={}
for role,status in [('producer','complete'),('verifier','verified')]:
 root=BASE/role; m=read(root/'metadata.json'); ex=read(BASE/'execution'/role/'result.json'); request=read(BASE/'execution'/role/'request.json')
 strict([m[k] for k in ['status','mode','physical_steps','future_generator_ticks','future_direction_values','reconstructed_past_generator_ticks','completed_pairs','fixed_future_ticks','synthetic_fixture_steps','time_limit_seconds','storage_limit_bytes','git_commit']], [status,'formal',1792,448,114688,640,28,[33,64],0,600,134217728,pre['git']['commit']])
 assert ex['exit_code']==0 and ex['wall_seconds']<600 and m['elapsed_seconds']<600
 assert ex['source_unchanged'] and ex['all_git_tracked_unchanged'] and ex['git_after']['status']==''
 strict(request['source_sha256_before'],ex['source_sha256_after']); checked_hashes(ex['source_sha256_after'])
 strict(m['input_sha256'],m['input_sha256_after']); checked_hashes(m['input_sha256'])
 for k in ['input_read_errors_before','input_read_errors_after','output_read_errors','finalization_errors']: strict(m[k],{})
 for name,h in m['output_sha256'].items(): assert sha(root/name)==h
 for name,h in ex['raw_output_sha256'].items(): assert sha(BASE/'execution'/role/name)==h
 assert len(list((root/'cases').iterdir()))==28 and len(list((root/'environments').iterdir()))==14
 files={str(p.relative_to(root)):file_record(p) for p in sorted(root.rglob('*')) if p.is_file()}
 total=sum(x['bytes'] for x in files.values()); assert total<134217728
 roles[role]=dict(status=status,metadata_path=str((root/'metadata.json').relative_to(ROOT)),metadata_sha256=sha(root/'metadata.json'),input_bindings_verified=len(m['input_sha256']),output_files=files,physical_steps=m['physical_steps'],future_generator_ticks=m['future_generator_ticks'],past_generator_ticks=m['reconstructed_past_generator_ticks'],wall_seconds=ex['wall_seconds'],metadata_elapsed_seconds=m['elapsed_seconds'],actual_route_bytes=total,actual_route_MiB=total/1024**2)
prod=BASE/'producer'; ver=BASE/'verifier'; artifact_equality=[]
scientific=sorted([str(p.relative_to(prod)) for d in ['cases','environments'] for p in (prod/d).iterdir()]+['records.json','index.json','summary.json'])
assert len(scientific)==45
for name in scientific:
 before=nodes; strict(read(prod/name),read(ver/name),name)
 artifact_equality.append(dict(path=name,strict_concrete_type_equality=True,compared_nodes=nodes-before,original_bytes_identical=(prod/name).read_bytes()==(ver/name).read_bytes(),producer_sha256=sha(prod/name),verifier_sha256=sha(ver/name)))
proof=read(ver/'proof.json');strict(proof['input_sha256'],proof['input_sha256_after']);strict(proof['input_sha256'],read(ver/'metadata.json')['input_sha256']);assert proof['status']=='verified'
records=read(prod/'records.json'); assert len(records)==28
pair_results=[]; masked=empty_masked=0
for record in records:
 case=read(prod/record['case']); enc=case['encoding']; seed=case['seed']; arms={}
 strict([record['encoding'],record['seed']],[enc,seed]); strict(case['fixed_future_ticks'],[33,64]);assert case['full_case_expected_steps']==64
 ref=case['boundary']['final']; assert ref['path']==f'data/v4-study-043/cases/{enc}-{seed}.json' and ref['pointer']=='/ablation/final'
 original=deref(ref); template=deref(case['boundary']['template']); removals=deref(case['boundary']['historical_removals'])
 strict(case['original_template'],template)
 env=read(prod/f'environments/{seed}.json'); strict(case['natural_tape'],env['natural_tape']); assert case['natural_tape_sha256']==env['sha256']
 assert [t['tick'] for t in case['natural_tape']]==list(range(33,65))
 for arm in ARMS:
  a=case[arm]; strict(a['initial'],original);strict(a['historical_removals'],removals)
  assert [r['tick'] for r in a['rows']]==list(range(33,65))
  assert a['initial']['tick']==32 and a['final']['tick']==64
  assert 0 not in a['initial']['site_ids'] and 1 not in a['initial']['site_ids']
  assert a['initial']['individuals'][0]['death_tick'] is None and a['initial']['individuals'][1]['death_tick'] is None
  alive={i for i in a['initial']['site_ids'] if i is not None}; next_id=len(a['initial']['individuals']); failures=Counter({k:0 for k in a['failure_counts']});totals=Counter()
  for row,tape in zip(a['rows'],case['natural_tape']):
   expected=tape['directions'][:]
   if arm=='continue_north':
    for pos in (101,102):
     masked+=int(expected[pos]!=3);empty_masked+=int(a['initial']['site_ids'][pos] is None) if row['tick']==33 else int(previous['site_ids'][pos] is None)
     expected[pos]=3
   strict(row['physical']['directions'],expected); assert row['status']=='complete'
   p=row['physical'];assert [x['proposed'] for x in p['driven']['inputs']]==[8 if i in (85,86,117,118) else 0 for i in range(256)]
   strict(p['mutation_tickets'],[[999,0,1] for _ in range(256)])
   assert p['material_before']==p['material_after']==7
   assert p['energy_after']==p['energy_before']+p['imported']-p['spent']
   assert p['energy_before']==(case['boundary']['energy'] if row['tick']==33 else previous['physical']['energy_after'])
   for k in ('imported','rejected_import','spent'): totals[k]+=p[k]
   totals['births']+=len(row['births']);totals['deaths']+=len(row['deaths'])
   strict([b['id'] for b in row['births']],list(range(next_id,next_id+len(row['births']))));next_id+=len(row['births'])
   for b in row['births']: assert b['birth_tick']==row['tick'] and b['parent']<b['id'] and b['parent'] in alive
   assert set(row['deaths'])<=alive
   alive.difference_update(row['deaths']);alive.update(b['id'] for b in row['births']);assert alive=={i for i in row['site_ids'] if i is not None}
   failures.update(row['failure_counts']); actual=Counter(g['reason'] for g in row['proposal_gates'])
   strict(row['failure_counts'],{k:actual[k] for k in row['failure_counts']})
   assert row['new_copy_count']==len([c for c in row['copies'] if c['all_new']])
   for comp in row['components']:
    for witness in comp['member_witnesses']:
     identity=a['final']['individuals'][witness['identity']]
     strict([witness['birth_tick'],witness['parent'],witness['program'],witness['material']],[identity['birth_tick'],identity['parent'],identity['program'],identity['material']])
     strict(witness['born_after_original_t0'],witness['birth_tick']>a['original_t0']);strict(witness['born_after_tick32'],witness['birth_tick']>32)
    if comp['all_new']: assert all(comp[k] for k in ('genetic_copy','full_program_matches','material_matches','original_ancestry','excludes_original_members'))
   previous=row
  strict(dict(failures),a['failure_counts']); assert next_id==len(a['final']['individuals'])
  ledger=a['ledger']; metrics=a['metrics'];assert ledger['energy_export']==0 and ledger['initial_mass']==ledger['final_mass']==7
  strict({k:metrics[k] for k in totals},dict(totals))
  assert ledger['initial_energy']+metrics['imported']-metrics['spent']==metrics['final_energy']
  assert ledger['initial_living']+ledger['future_births']-ledger['future_natural_deaths']==metrics['living']==len(alive)
  strict(a['new_copy_counts'],[row['new_copy_count'] for row in a['rows']]);q=a['new_copy_counts'];q32=a['tick32_diagnostic']['new_copy_count']
  runs=[];start=None
  for t,n in list(zip(range(33,65),q))+[(65,0)]:
   if n>=2 and start is None: start=t
   if n<2 and start is not None:
    runs.append(dict(start=start,end=t-1,length=t-start,left_censored_at_boundary=start==33 and q32>=2,right_censored=t==65));start=None
  strict(a['intervals'],runs);longest=max([r['length'] for r in runs],default=0)
  strict(a['longest_double'],longest);strict(a['future_persistent10'],longest>=10)
  assert metrics['future_persistent10']==metrics['persistent10']==int(longest>=10)
  source_arm=read(ROOT/ref['path'])['ablation'];prefix=source_arm['new_copy_counts']
  assert q32==prefix[-1]
  if q32>=2 and q[0]>=2:
   length=0
   for count in reversed(prefix):
    if count<2: break
    length+=1
   first=runs[0];start=33-length
   expected_cross=dict(prefix_start=start,prefix_end=32,future_start=33,future_end=first['end'],prefix_length=length,future_length=first['length'],combined_observed_length=length+first['length'],combined_persistent10=length+first['length']>=10,prefix_left_censored_at_original_intervention=start==a['original_t0']+1,right_censored=first['right_censored'])
   strict(a['cross_boundary'],expected_cross)
  else: assert a['cross_boundary'] is None
  for field,boundary in [('formation_witnesses',a['original_t0']),('after32_formation_witnesses',32)]:
   for witness in a[field]:
    assert witness['births'] and 33<=witness['tick']<=64
    for b in witness['births']: assert b['birth_tick']>boundary and b['birth_tick']<=witness['tick']
  strict(record[arm+'_metrics'],metrics);strict(record['intervals'][arm],a['intervals']);strict(record['cross_boundary'][arm],a['cross_boundary'])
  arms[arm]=dict(q32=q32,new_copy_counts=q,future_persistent10=a['future_persistent10'],longest_double=longest,intervals=runs,cross_boundary=a['cross_boundary'],original_t0=a['original_t0'],ledger=ledger,metrics=metrics,failure_counts=a['failure_counts'],formation_witnesses=a['formation_witnesses'],after32_formation_witnesses=a['after32_formation_witnesses'])
 delta={k:case[ARMS[1]]['metrics'][k]-case[ARMS[0]]['metrics'][k] for k in case[ARMS[0]]['metrics']};strict(record['delta'],delta);strict(case['delta'],delta)
 pair_results.append(dict(encoding=enc,seed=seed,case=record['case'],arms=arms,delta=delta))
index=read(prod/'index.json');statuses=dict(Counter(row['future_status'] for row in index));strict(statuses,{'not_applicable_original_32_no_trigger':72,'complete':28});assert len(index)==100
assert sum(x['short_window'] for x in index)==10
for row in index:
 if not row['trigger']: assert row['future'] is None and row['future_status']=='not_applicable_original_32_no_trigger'
 else: strict(row['future'],next(r for r in records if (r['encoding'],r['seed'])==(row['encoding'],row['seed'])))
summary=read(prod/'summary.json');strict(summary['pairs'],records)
strict([(c['encoding'],c['selected_n'],c['n']) for c in summary['cells']],[('east',5,5),('west',3,3),('south',0,0),('north',9,9),('homogeneous',11,11)])
assert summary['selected_pairs']==summary['completed_pairs']==28 and len(summary['seed_groups'])==14
for group,subset in [(summary['overall'],records)]+[(c,[r for r in records if r['encoding']==c['encoding']]) for c in summary['cells']]+[(g,[r for r in records if r['seed']==g['seed']]) for g in summary['seed_groups']]:
 assert group['n']==len(subset)
 for arm in ARMS:
  strict(group['arm_totals'][arm],{k:sum(r[arm+'_metrics'][k] for r in subset) for k in group['arm_totals'][arm]})
 for k in group['delta_totals']:
  values=[r['delta'][k] for r in subset]; total=sum(values)
  strict(group['delta_totals'][k],total);strict(group['mean_delta'][k],str(Fraction(total,len(values))) if values else None)
  for name,predicate in [('positive',lambda x:x>0),('negative',lambda x:x<0),('tie',lambda x:x==0)]: strict(group[name][k],sum(predicate(x) for x in values))
 for k,cells in group['binary_pairs'].items():
  strict(cells,[dict(continue_north=a,withdraw_to_natural=b,n=sum(r[ARMS[0]+'_metrics'][k]==a and r[ARMS[1]+'_metrics'][k]==b for r in subset)) for a in (0,1) for b in (0,1)])
 if 'seed' in group:
  strict(group['selected_encodings'],[e for e in ENCODINGS if any(r['encoding']==e for r in subset)]);strict(group['pairs'],subset)
reused=[]
for label,path in [('full','docs/research/results/v4-study-047-preflight-joint-validation/full-revalidated/execution.json'),('compile','docs/research/results/v4-study-047-preflight-joint-validation/compile-revalidated/execution.json'),('producer_help','docs/research/results/v4-study-047-producer-preflight-implementation/final-help/execution.json'),('verifier_help','docs/research/results/v4-study-047-verifier-implementation/remediation-1-help/execution.json')]:
 p=ROOT/path; obj=read(p); assert obj['exit_code']==0
 hashes=obj.get('files_sha256',obj.get('source_before',{})); needed=hashes if label in ('full','compile') else {n:h for n,h in hashes.items() if n.startswith('scripts/')}
 checked_hashes(needed)
 raw=obj.get('raw_output_sha256',obj.get('evidence_sha256',{}))
 for n,h in raw.items(): assert sha(p.parent/n)==h
 if label in ('full','compile'): strict(hashes,obj['files_sha256_after'])
 if label=='full':
  for n,h in hashes.items(): assert sha(p.parent/Path(n).name)==h
 reused.append(dict(label=label,path=path,sha256=sha(p),exit_code=0,command=obj['command'],current_execution_source_bindings=needed,raw_hashes_verified=len(raw),reexecuted=False,qualification='帮助证据绑定当前CLI；所附测试快照早于仅测试时标调整，不冒称其测试文件为当前。' if 'help' in label else '五份当前源码/测试前后绑定一致；完整回归1070通过含104项047测试。'))
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',scope='全部28正式配对只读证据自审；待新鲜独立审查与父层最终验收。',git_commit=pre['git']['commit'],pre_archive_git_clean=True,all_tracked_files_unchanged=True,routes=roles,complete_scientific_artifacts=artifact_equality,strict_comparison_nodes=nodes,pairs=pair_results,index_status_counts=statuses,full_selected_by_encoding=[5,3,0,9,11],preserved_seed_groups=14,zero_denominator_means_null=True,binary_four_cells_preserved=True,summary=summary,reused_validation=reused,policy_overrides_different_from_natural=masked,policy_target_ticks_empty_at_start=empty_masked,current_task_counts=dict(real_producer_physical_steps=1792,real_independent_physical_steps=1792,real_future_generator_ticks_per_route=448,past_generator_ticks_per_route=640,new_synthetic_physical_steps=0,new_synthetic_future_generator_ticks=0,formal_physical_steps=3584,engineering_physical_steps_prior=128,combined_actual_physical_steps=3712),real_failed_runs=0,real_reruns=0,scientific_modules_imported_by_audit=False,elapsed_seconds=time.monotonic()-started)
with (BASE/'audit.json').open('x',encoding='utf-8') as out: json.dump(report,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps(dict(status=report['status'],strict_comparison_nodes=nodes,routes={r:{k:v for k,v in o.items() if k!='output_files'} for r,o in roles.items()},main_binary_pairs=summary['overall']['binary_pairs']['future_persistent10'],counts=report['current_task_counts']),ensure_ascii=False))
