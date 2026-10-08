"""Read-only post-run evidence audit; never import research/science modules."""
from pathlib import Path
from collections import Counter
import datetime, hashlib, json, subprocess, time
ROOT=Path('/Users/todd/Documents/bitgenesis'); BASE=ROOT/'data/v4-study-047-engineering'
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def strict(a,b,label='object'):
 assert type(a) is type(b),(label,'type')
 if type(a) is dict:
  assert a.keys()==b.keys(),(label,'keys')
  for k in a: strict(a[k],b[k],label+'/'+k)
 elif type(a) is list:
  assert len(a)==len(b),(label,'length')
  for i,(x,y) in enumerate(zip(a,b)): strict(x,y,label+'/'+str(i))
 else: assert a==b,(label,'value')
def checked_hashes(mapping):
 for path,h in mapping.items(): assert sha(ROOT/path)==h,path
 return len(mapping)
def file_record(p): return dict(bytes=p.stat().st_size,sha256=sha(p))
started=time.monotonic()
pre=read(BASE/'preflight.json')
assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)==''
checked_hashes(pre['git_tracked_sha256'])
assert not (ROOT/'data/v4-study-047').exists()
roles={}
for role,status in [('producer','complete'),('verifier','verified')]:
 root=BASE/role; m=read(root/'metadata.json'); ex=read(BASE/'execution'/role/'result.json'); request=read(BASE/'execution'/role/'request.json')
 strict([m[k] for k in ['status','mode','physical_steps','future_generator_ticks','future_direction_values','reconstructed_past_generator_ticks','completed_pairs','fixed_future_ticks','synthetic_fixture_steps','time_limit_seconds','storage_limit_bytes','git_commit']], [status,'engineering',64,32,8192,640,1,[33,64],0,600,134217728,pre['git']['commit']])
 assert ex['exit_code']==0 and ex['wall_seconds']<600 and m['elapsed_seconds']<600
 assert ex['source_unchanged'] and ex['all_git_tracked_unchanged'] and ex['git_after']['status']==''
 strict(request['source_sha256_before'],ex['source_sha256_after']); checked_hashes(ex['source_sha256_after'])
 strict(m['input_sha256'],m['input_sha256_after']); checked_hashes(m['input_sha256'])
 for k in ['input_read_errors_before','input_read_errors_after','output_read_errors','finalization_errors']: strict(m[k],{})
 for name,h in m['output_sha256'].items(): assert sha(root/name)==h
 for name,h in ex['raw_output_sha256'].items(): assert sha(BASE/'execution'/role/name)==h
 assert list(sorted(p.name for p in (root/'cases').iterdir()))==['east-120005.json']
 assert list(sorted(p.name for p in (root/'environments').iterdir()))==['120005.json']
 files={str(p.relative_to(root)):file_record(p) for p in sorted(root.rglob('*')) if p.is_file()}
 total=sum(x['bytes'] for x in files.values()); assert total<134217728
 case=files['cases/east-120005.json']['bytes']; env=files['environments/120005.json']['bytes']; summaries=sum(files[n]['bytes'] for n in ['records.json','index.json','summary.json']); admin=total-case-env-summaries
 conservative=case*28+env*14+summaries*28+admin*4
 assert conservative<134217728 and m['projected_full_storage_bytes']<134217728
 roles[role]=dict(status=status,metadata_path=str((root/'metadata.json').relative_to(ROOT)),metadata_sha256=sha(root/'metadata.json'),input_bindings_verified=len(m['input_sha256']),output_files=files,physical_steps=m['physical_steps'],future_generator_ticks=m['future_generator_ticks'],past_generator_ticks=m['reconstructed_past_generator_ticks'],wall_seconds=ex['wall_seconds'],metadata_elapsed_seconds=m['elapsed_seconds'],actual_route_bytes=total,actual_route_MiB=total/1024**2,case_bytes=case,environment_bytes=env,index_records_summary_bytes=summaries,final_administrative_bytes=admin,recorded_projected_full_storage_bytes=m['projected_full_storage_bytes'],conservative_projected_full_storage_bytes=conservative,conservative_projected_MiB=conservative/1024**2,wall_times_28_seconds=ex['wall_seconds']*28,projection_limitation='仅首例外推，不是其他27例大小或用时保证；正式继续逐写128MiB及600秒硬限，不缩字段/队列。')
prod=BASE/'producer'; ver=BASE/'verifier'
artifact_equality=[]
for name in ['cases/east-120005.json','environments/120005.json','records.json','index.json','summary.json']:
 strict(read(prod/name),read(ver/name),name)
 artifact_equality.append(dict(path=name,strict_concrete_type_equality=True,original_bytes_identical=(prod/name).read_bytes()==(ver/name).read_bytes(),producer_sha256=sha(prod/name),verifier_sha256=sha(ver/name)))
proof=read(ver/'proof.json');strict(proof['input_sha256'],proof['input_sha256_after']);strict(proof['input_sha256'],read(ver/'metadata.json')['input_sha256']);assert proof['status']=='verified'
case=read(prod/'cases/east-120005.json'); src=read(ROOT/'data/v4-study-043/cases/east-120005.json')
strict(case['boundary']['final'],src['ablation']['final'])
strict(case['continue_north']['initial'],src['ablation']['final']);strict(case['withdraw_to_natural']['initial'],src['ablation']['final'])
strict([case[k] for k in ['encoding','seed','fixed_future_ticks','full_case_expected_steps']],['east',120005,[33,64],64])
arm_results={}
for arm in ['continue_north','withdraw_to_natural']:
 a=case[arm];assert [r['tick'] for r in a['rows']]==list(range(33,65))
 assert [t['tick'] for t in case['natural_tape']]==list(range(33,65))
 assert a['initial']['tick']==32 and a['final']['tick']==64
 assert 0 not in a['initial']['site_ids'] and 1 not in a['initial']['site_ids']
 assert a['initial']['individuals'][0]['death_tick'] is None and a['initial']['individuals'][1]['death_tick'] is None
 for row,tape in zip(a['rows'],case['natural_tape']):
  expected=tape['directions'][:]
  if arm=='continue_north': expected[101]=expected[102]=3
  strict(row['physical']['directions'],expected)
  assert row['status']=='complete'
  assert [x['proposed'] for x in row['physical']['driven']['inputs']]==[8 if i in (85,86,117,118) else 0 for i in range(256)]
  strict(row['physical']['mutation_tickets'],[[999,0,1] for _ in range(256)])
  assert row['physical']['material_before']==row['physical']['material_after']==7
  assert row['physical']['energy_after']==row['physical']['energy_before']+row['physical']['imported']-row['physical']['spent']
 ledger=a['ledger']; metrics=a['metrics']; assert ledger['energy_export']==0
 assert ledger['initial_energy']+metrics['imported']-metrics['spent']==metrics['final_energy']
 assert ledger['initial_living']+ledger['future_births']-ledger['future_natural_deaths']==metrics['living']
 strict(a['new_copy_counts'],[row['new_copy_count'] for row in a['rows']])
 arm_results[arm]=dict(new_copy_counts=a['new_copy_counts'],q32=a['tick32_diagnostic']['new_copy_count'],future_persistent10=a['future_persistent10'],longest_double=a['longest_double'],intervals=a['intervals'],cross_boundary=a['cross_boundary'],original_t0=a['original_t0'],formation_witness_count=len(a['formation_witnesses']),after32_formation_witness_count=len(a['after32_formation_witnesses']),ledger=ledger,metrics=metrics,failure_counts=a['failure_counts'],boundary_identity_history_preserved=True,full_32_rows=True,policy_direction_and_fixed_feed_mutation_checked=True,each_step_energy_and_mass_checked=True)
index=read(prod/'index.json'); statuses=dict(Counter(row['future_status'] for row in index)); strict(statuses,{'not_applicable_original_32_no_trigger':72,'complete':1,'not_run_engineering':27})
assert len(index)==100
for row in index:
 if row['future_status']!='complete': assert row['future'] is None
summary=read(prod/'summary.json'); strict([(c['encoding'],c['selected_n'],c['n']) for c in summary['cells']],[('east',5,1),('west',3,0),('south',0,0),('north',9,0),('homogeneous',11,0)])
for c in summary['cells']:
 if c['n']==0: assert all(v is None for v in c['mean_delta'].values())
 assert all(len(v)==4 for v in c['binary_pairs'].values())
assert summary['selected_pairs']==28 and summary['completed_pairs']==1 and len(summary['seed_groups'])==14
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
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',scope='仅首E120005工程、对象及证据读取核查；待独立工程审查与父层验收提交。',git_commit=pre['git']['commit'],pre_archive_git_clean=True,all_tracked_files_unchanged=True,source_closure_size=1192,producer_closure_with_gates=1194,verifier_with_producer_files=1200,routes=roles,complete_scientific_artifacts=artifact_equality,source_final_and_both_initials_strictly_equal=True,arm_results=arm_results,delta=case['delta'],index_status_counts=statuses,full_selected_by_encoding=[5,3,0,9,11],completed_by_encoding=[1,0,0,0,0],preserved_seed_groups=14,zero_denominator_means_null=True,binary_four_cells_preserved=True,reused_validation=reused,current_task_counts=dict(real_producer_physical_steps=64,real_independent_physical_steps=64,real_future_generator_ticks_per_route=32,past_generator_ticks_per_route=640,new_synthetic_physical_steps=0,new_synthetic_future_generator_ticks=0,formal_physical_steps=0,other_27_future_physical_steps=0),real_failed_runs=0,real_reruns=0,formal_directory_exists=False,scientific_modules_imported_by_audit=False,elapsed_seconds=time.monotonic()-started)
with (BASE/'audit.json').open('x',encoding='utf-8') as out: json.dump(report,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps({k:report[k] for k in ['status','current_task_counts','index_status_counts','real_failed_runs']},ensure_ascii=False))
print(json.dumps({r:{k:v for k,v in x.items() if k in ['actual_route_bytes','recorded_projected_full_storage_bytes','conservative_projected_full_storage_bytes','wall_times_28_seconds']} for r,x in roles.items()},ensure_ascii=False))
