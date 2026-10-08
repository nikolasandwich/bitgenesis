"""独立审查：仅标准库读取保存JSON/字节；不导入科学模块或调用RNG/物理。"""
import ast, collections, fractions, hashlib, json, pathlib, re, tarfile, time
ROOT=pathlib.Path('/Users/todd/Documents/bitgenesis'); B=ROOT/'docs/research/results/v4-study-047-formal'; O=ROOT/'docs/research/results/v4-study-047-formal-review-run'
A=('continue_north','withdraw_to_natural'); E=('east','west','south','north','homogeneous'); nodes=0; checks=collections.Counter(); result={}
def load(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def obj(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def eq(a,b,label=''):
 global nodes
 nodes+=1
 assert type(a) is type(b),(label,type(a),type(b))
 if isinstance(a,dict):
  assert a.keys()==b.keys(),(label,a.keys(),b.keys())
  for k in a:eq(a[k],b[k],label+'/'+str(k))
 elif isinstance(a,list):
  assert len(a)==len(b),(label,len(a),len(b))
  for i,(x,y) in enumerate(zip(a,b)):eq(x,y,label+'/'+str(i))
 else: assert a==b,(label,a,b)
def bindings(d,label):
 for p,h in d.items(): assert sha(p)==h,(label,p)
 checks[label]+=len(d)
def deref(r):
 assert sha(r['path'])==r['sha256']; d=load(r['path'])
 for k in r['pointer'].strip('/').split('/'):d=d[k]
 assert obj(d)==r['value_sha256']; return d
def energy(u):return sum(x['energy'] for x in u if x is not None)
def spans(ts):
 out=[]
 for t in sorted(set(ts)):
  if out and out[-1][1]==t-1:out[-1][1]=t
  else:out.append([t,t])
 return out
def chain(i,people,selected):
 out=[]; hit=None
 while i is not None:
  out.append(i)
  if i in selected:hit=i;break
  i=people[i]['parent']
 return {'identity':out[0],'chain':out,'selected_ancestor':hit}
def signature(sites,units,program=True):
 variants=[]
 for base in sites:
  parts=[[(s%16-base%16)%16,(s//16-base//16)%16,units[s]['material']]+([units[s]['program']] if program else []) for s in sites]
  variants.append(sorted(parts))
 return min(variants)
def observe(saved,units,ids,people,template,t0):
 # 从已保存的末态重算无动力学的几何连通、完整模板、祖系和出生见证。
 loc={i:s for s,i in enumerate(ids) if i is not None}; assert len(loc)==sum(x is not None for x in units)
 remaining=set(loc); groups=[]
 while remaining:
  group={min(remaining)}; stack=list(group)
  while stack:
   i=stack.pop();s=loc[i];x=s%16;y=s//16
   for t in [y*16+(x+1)%16,y*16+(x-1)%16,((y+1)%16)*16+x,((y-1)%16)*16+x]:
    j=ids[t]
    if j is not None and j not in group and units[t]['material']==units[s]['material']:group.add(j);stack.append(j)
  remaining-=group;groups.append(sorted(group))
 eq(saved['observation']['components']['material'],groups,'geometry')
 template_sites=[template['site_ids'].index(i) for i in [0,1]];target=signature(template_sites,template['units']);targetmat=signature(template_sites,template['units'],False)
 eq(saved['template_fingerprint'],target)
 rebuilt=[]
 for ix,g in enumerate(groups):
  sites=[loc[i] for i in g];sig=signature(sites,units);ancestral=all(people[i]['founder'] in [0,1] for i in g); excludes=not set(g)&{0,1}; genetic=len(g)==2 and sig==target and ancestral
  witnesses=[]
  for i in g:
   p=people[i];s=loc[i];assert units[s]['program']==p['program'] and units[s]['material']==p['material']
   witnesses.append(dict(identity=i,site=s,birth_site=p['site'],birth_tick=p['birth_tick'],parent=p['parent'],founder=p['founder'],generation=p['generation'],material=units[s]['material'],program=units[s]['program'],ancestor_chain=chain(i,people,{0,1})['chain'],born_after_original_t0=p['birth_tick']>t0,born_after_tick32=p['birth_tick']>32))
  rebuilt.append(dict(component=ix,members=g,sites=sites,fingerprint=sig,material_matches=signature(sites,units,False)==targetmat,full_program_matches=sig==target,original_ancestry=ancestral,excludes_original_members=excludes,member_witnesses=witnesses,genetic_copy=genetic,all_new=genetic and excludes))
 eq(saved['components'],rebuilt,'components')
 copies=[c for c in rebuilt if c['genetic_copy']]
 assert [c['members'] for c in saved['copies']]==[c['members'] for c in copies]
 for c in saved['copies']:
  rebuiltc=rebuilt[c['component']]
  for k in ['members','sites','member_witnesses','all_new']:eq(c[k],rebuiltc[k])
 q=sum(c['all_new'] for c in rebuilt);eq(saved['new_copy_count'],q);checks['passive_observations']+=1;return q
start=time.monotonic(); validation=load(B/'validation-summary.json'); eq(validation['files_sha256'],validation['files_sha256_after']);bindings(validation['files_sha256'],'author_seal')
for role,n in [('producer',1985),('verifier',3023),('engineering',3535)]:
 d=load(f'docs/research/results/v4-study-047-{role}-review.json'); assert d['verdict']=='APPROVED';assert len(d['files_sha256'])==n;eq(d['files_sha256'],d['files_sha256_after']);bindings(d['files_sha256'],role+'_approval')
manifest=load(B/'archive-manifest.json'); assert sha(manifest['archive_path'])==manifest['archive_sha256']; restore=O/'restored';restore.mkdir()
with tarfile.open(ROOT/manifest['archive_path'],'r:gz') as tar:
 members={x.name:x for x in tar.getmembers() if x.isfile()};assert len(members)==325
 for e in manifest['entries']:
  raw=tar.extractfile(members[e['member']]).read(); target=restore/e['member']; assert target.is_relative_to(restore) and '..' not in target.parts;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  assert raw==(ROOT/e['source']).read_bytes()==(ROOT/e['archive_copy']).read_bytes()==target.read_bytes();assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'];checks['restored_files']+=1
assert sum(e['bytes'] for e in manifest['entries'])==119528074
result['archive']={'files':325,'original_bytes':119528074,'tar_bytes':(ROOT/manifest['archive_path']).stat().st_size,'sha256':manifest['archive_sha256'],'restore_directory':str(restore.relative_to(ROOT))}
science=sorted([*pathlib.Path('cases').glob('none')])
prod=B/'raw/producer';ver=B/'raw/verifier'; science=[*sorted((prod/'cases').glob('*.json')),*sorted((prod/'environments').glob('*.json')),prod/'index.json',prod/'records.json',prod/'summary.json']; n0=nodes
for p in science:
 q=ver/p.relative_to(prod);eq(load(p),load(q),'science/'+p.name);assert p.read_bytes()==q.read_bytes()
assert len(science)==45;result['strict_science']={'files':45,'nodes':nodes-n0,'bytes_equal':True}
result['routes']={}
for route in ['producer','verifier']:
 d=load(B/f'raw/{route}/metadata.json');eq(d['input_sha256'],d['input_sha256_after']);bindings(d['input_sha256'],route+'_inputs')
 for p,h in d['output_sha256'].items(): assert sha(B/f'raw/{route}'/p)==h
 for k in ['input_read_errors_before','input_read_errors_after','output_read_errors','finalization_errors']:assert d[k]=={}
 assert d['physical_steps']==d['planned_physical_steps']==1792 and d['completed_pairs']==d['planned_pairs']==28;assert d['future_generator_ticks']==448 and d['reconstructed_past_generator_ticks']==640 and d['synthetic_fixture_steps']==0
 assert d['elapsed_seconds']<600 and d['time_limit_seconds']==600 and d['storage_limit_bytes']==134217728
 request=load(B/f'raw/execution/{route}/request.json');execution=load(B/f'raw/execution/{route}/result.json'); assert execution['exit_code']==0 and request['scientific_invocation_ordinal']==1
 assert request['git_before']==execution['git_after'];assert request['git_before']=={'commit':'a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f','origin_main':'a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f','status':''}
 eq(request['source_sha256_before'],execution['source_sha256_after']);bindings(request['source_sha256_before'],route+'_execution_source');bindings(execution['raw_output_sha256'],route+'_execution_raw')
 size=sum(p.stat().st_size for p in (prod if route=='producer' else ver).rglob('*') if p.is_file());assert size<134217728
 result['routes'][route]={'physical_steps':1792,'future_generator_ticks':448,'past_generator_ticks':640,'bytes':size,'wall_seconds':execution['wall_seconds'],'source_bindings':len(d['input_sha256']),'exit_code':0}
# 历史测试仅核原始日志/执行记录/当前版本，不再执行测试。
result['reused_validation']=[]
for entry in validation['reused_validation']:
 d=load(entry['path']);assert sha(entry['path'])==entry['sha256'] and d['exit_code']==0;bindings(entry['current_execution_source_bindings'],'reused_current_code')
 raw=d.get('raw_output_sha256',d.get('evidence_sha256'));bindings(raw,'reused_raw');result['reused_validation'].append({'label':entry['label'],'exit_code':0,'reexecuted':False,'raw_bindings':len(raw)})
full=load(validation['reused_validation'][0]['path']);text='\n'.join((ROOT/p).read_text(errors='replace') for p in full['raw_output_sha256']);assert 'Ran 1070 tests' in text and '\nOK' in text;assert sum('test_v4_middle_withdrawal' in line and line.rstrip().endswith('ok') for line in text.splitlines())==104
census=load('docs/research/results/v4-study-047-design-revalidated-census.json');index=load(prod/'index.json');records=load(prod/'records.json');summary=load(prod/'summary.json');assert len(index)==100 and len(records)==28
assert sum(not r['trigger'] for r in index)==72 and sum(r['short_window'] for r in index)==10;assert len({r['seed'] for r in records})==14
for saved,original in zip(index,census['cases']):
 for k in ['encoding','seed','source','trigger','t0','remaining','short_window','applicability','selection']:eq(saved[k],original[k])
 if not saved['trigger']:assert saved['future'] is None and saved['future_status']=='not_applicable_original_32_no_trigger'
 else:eq(saved['future'],next(r for r in records if (r['encoding'],r['seed'])==(saved['encoding'],saved['seed'])))
result['pairs']=[];counts=collections.Counter();failures={a:collections.Counter() for a in A};aggregate={a:collections.Counter() for a in A}
for record in records:
 c=load(prod/record['case']);original=deref(c['boundary']['final']);template=deref(c['boundary']['template']);removals=deref(c['boundary']['historical_removals']);eq(c['original_template'],template)
 environment=load(prod/f"environments/{c['seed']}.json");eq(c['natural_tape'],environment['natural_tape']);assert obj(c['natural_tape'])==c['natural_tape_sha256']==environment['sha256'];assert [x['tick'] for x in c['natural_tape']]==list(range(33,65))
 pair={'encoding':c['encoding'],'seed':c['seed'],'q32':None,'arms':{}}; source043=load(c['boundary']['final']['path'])
 for arm in A:
  a=c[arm];eq(a['initial'],original);eq(a['historical_removals'],removals);eq(a['historical_energy_export'],c['boundary']['original_export']); assert a['boundary_tick']==32 and a['ledger']['energy_export']==0
  people=a['final']['individuals'];assert a['final']['parents']==[p['parent'] for p in people];assert all(p['id']==i and (p['parent'] is None or p['parent']<i) for i,p in enumerate(people));assert 0 not in original['site_ids'] and 1 not in original['site_ids'];assert people[0]['death_tick'] is people[1]['death_tick'] is None
  q32=observe(a['tick32_diagnostic'],original['units'],original['site_ids'],people,template,a['original_t0']);pair['q32']=q32
  eq([r['tick'] for r in a['rows']],list(range(33,65)));prior=original;qs=[];m=collections.Counter();prior_ids=original['site_ids'];next_id=len(original['individuals'])
  for row,tape in zip(a['rows'],c['natural_tape']):
   p=row['physical'];assert row['status']=='complete';d=list(tape['directions'])
   if arm==A[0]:
    for s in [101,102]:counts['policy_sites']+=1;counts['changed_policy_sites']+=d[s]!=3;counts['empty_policy_sites']+=prior['units'][s] is None;d[s]=3
   eq(p['directions'],d);eq(p['mutation_tickets'],[[999,0,1]]*256);inputs=p['driven']['inputs'];eq([x['site'] for x in inputs],list(range(256)));eq([x['proposed'] for x in inputs],[8 if i in [85,86,117,118] else 0 for i in range(256)])
   assert sum(x['accepted'] for x in inputs)==p['imported'] and sum(x['rejected'] for x in inputs)==p['rejected_import'] and p['imported']+p['rejected_import']==32
   assert p['energy_before']==energy(prior['units']);assert energy(p['units'])==p['energy_after']==p['energy']==p['energy_before']+p['imported']-p['spent'];assert p['material_before']==p['material_after']==sum(p['raw'])+sum(x is not None for x in p['units'])==7
   assert p['spent']==p['driven']['leakage']+p['driven']['interaction']['spent']+p['material']['construction_spent']+p['material']['copy_spent']
   eq(row['deaths'],[prior_ids[s] for s in p['material']['dissolved']]);eq([x['id'] for x in row['births']],list(range(next_id,next_id+len(row['births']))));next_id+=len(row['births'])
   live_before={x for x in prior_ids if x is not None};live_after={x for x in row['site_ids'] if x is not None};assert live_after==(live_before-set(row['deaths']))|{x['id'] for x in row['births']};assert len(live_after)==len(live_before)+len(row['births'])-len(row['deaths'])
   for birth in row['births']:
    assert birth['birth_tick']==row['tick']; saved=people[birth['id']]
    for k in birth:
     if k not in ['death_tick','offspring']:eq(birth[k],saved[k])
   for death in row['deaths']:assert people[death]['death_tick']==row['tick']
   qs.append(observe(row,p['units'],row['site_ids'],people,template,a['original_t0']))
   props=p['material']['proposals'];reasons=['collision','energy','formed','occupied','raw_material'];eq(row['failure_counts'],{reason:sum(x['reason']==reason for x in props) for reason in reasons});failures[arm].update(row['failure_counts'])
   assert len(props)==len(row['proposal_gates']);stocks=list(p['raw'])
   for proposal in props:
    if proposal['reason']=='formed':stocks[proposal['target']]+=1
   interaction=p['interaction_units'];alive=[None if u is None or u['energy']==0 else u for u in interaction];candidates=collections.Counter(x['target'] for x in props if alive[x['source']]['energy']>=20 and alive[x['target']] is None and stocks[x['target']]>=1)
   for proposal,gate in zip(props,row['proposal_gates']):
    s,t=proposal['source'],proposal['target'];u=alive[s]
    eq(gate,dict(source=s,target=t,direction=proposal['direction'],reason=proposal['reason'],source_energy=u['energy'],energy_sufficient=u['energy']>=20,target_empty=alive[t] is None,raw_available=stocks[t]>=1,candidate_count=candidates[t],no_collision=candidates[t]==1,parent_program=u['program'],expressed_material=u['program'][proposal['direction']],mutation_ticket=p['mutation_tickets'][s],construction_cost=4,copy_cost=1))
   m.update({k:p[k] for k in ['imported','rejected_import','spent']});m.update(births=len(row['births']),deaths=len(row['deaths']),leakage=p['driven']['leakage'],bond_spent=p['driven']['interaction']['spent'],construction_spent=p['material']['construction_spent'],copy_spent=p['material']['copy_spent']);prior=p;prior_ids=row['site_ids'];checks['rows']+=1
  assert next_id==len(people);eq(a['final']['units'],prior['units']);eq(a['final']['raw'],prior['raw']);eq(a['final']['site_ids'],prior_ids);eq(a['new_copy_counts'],qs)
  runs=spans([33+i for i,q in enumerate(qs) if q>=2]);intervals=[dict(start=s,end=e,length=e-s+1,left_censored_at_boundary=s==33 and q32>=2,right_censored=e==64) for s,e in runs];eq(a['intervals'],intervals);longest=max((e-s+1 for s,e in runs),default=0);assert a['longest_double']==longest and a['future_persistent10']==(longest>=10)
  if q32>=2 and qs[0]>=2:
   prefix=spans([r['tick'] for r in source043['ablation']['rows'] if sum(x['all_new'] for x in r['copies'])>=2]);s=prefix[-1][0];e=runs[0][1];cross=dict(prefix_start=s,prefix_end=32,future_start=33,future_end=e,prefix_length=33-s,future_length=e-32,combined_observed_length=e-s+1,prefix_left_censored_at_original_intervention=s==a['original_t0']+1,right_censored=e==64,combined_persistent10=e-s+1>=10);eq(a['cross_boundary'],cross)
  else:assert a['cross_boundary'] is None
  m.update(living=sum(x is not None for x in prior_ids),final_energy=energy(prior['units']),new_copy_ever=int(any(qs)),double_new_ever=int(any(q>=2 for q in qs)),future_persistent10=int(longest>=10),persistent10=int(longest>=10),longest_double=longest)
  for prefix,threshold in [('',a['original_t0']),('after32_',32)]:
   forms=[];uppers=[]
   def witness(i):return dict(identity=i,birth_tick=people[i]['birth_tick'],parent=people[i]['parent'],site=people[i]['site'])
   for row in a['rows']:
    copies=[x for x in row['copies'] if x['all_new']]
    if len(copies)<2:continue
    born=[witness(i) for cp in copies for i in cp['members'] if people[i]['birth_tick']>threshold]
    if born:forms.append(dict(tick=row['tick'],copies=[cp['members'] for cp in copies],births=born))
    for cp in copies:
     if sorted(cp['sites'])==[85,86] and all(people[i]['birth_tick']>threshold for i in cp['members']):uppers.append(dict(tick=row['tick'],members=cp['members'],sites=cp['sites'],births=[witness(i) for i in cp['members']],selected_ancestry=[chain(i,people,set(c['selection']['offspring_ids'])) for i in cp['members']]))
   eq(a[prefix+'formation_witnesses'],forms);eq(a[prefix+'upper_witnesses'],uppers);selected=[u for u in uppers if all(x['selected_ancestor'] is not None for x in u['selected_ancestry'])]
   for supported,persistent,w in [('formation_supported','formation_persistent10',forms),('upper_formed','upper_persistent10',uppers),('selected_ancestry_supported','selected_ancestry_persistent10',selected)]:m[prefix+supported]=int(bool(w));m[prefix+persistent]=int(any(e-s+1>=10 for s,e in spans([x['tick'] for x in w])))
  eq(a['metrics'],dict(m));eq(record[arm+'_metrics'],dict(m));eq(record['intervals'][arm],intervals);eq(record['cross_boundary'][arm],a['cross_boundary']);aggregate[arm].update(m)
  eq(a['ledger'],dict(initial_energy=energy(original['units']),initial_living=sum(x is not None for x in original['site_ids']),initial_mass=7,final_mass=7,energy_export=0,future_births=m['births'],future_natural_deaths=m['deaths']))
  pair['arms'][arm]={'counts':qs,'intervals':intervals,'cross_boundary':a['cross_boundary'],'metrics':dict(m)}
 eq(c['delta'],{k:c[A[1]]['metrics'][k]-c[A[0]]['metrics'][k] for k in c[A[0]]['metrics']});eq(record['delta'],c['delta']);pair['delta']=c['delta'];result['pairs'].append(pair)
eq(summary['pairs'],records);keys=list(records[0]['delta']);binary=list(summary['overall']['binary_pairs'])
def group(saved,rows):
 n=len(rows);assert saved['n']==n
 for arm in A:eq(saved['arm_totals'][arm],{k:sum(r[arm+'_metrics'][k] for r in rows) for k in keys})
 totals={k:sum(r['delta'][k] for r in rows) for k in keys};eq(saved['delta_totals'],totals);eq(saved['mean_delta'],{k:str(fractions.Fraction(v,n)) if n else None for k,v in totals.items()})
 for label,fn in [('positive',lambda v:v>0),('negative',lambda v:v<0),('tie',lambda v:v==0)]:eq(saved[label],{k:sum(fn(r['delta'][k]) for r in rows) for k in keys})
 for k in binary:eq(saved['binary_pairs'][k],[dict(continue_north=a,withdraw_to_natural=b,n=sum(r[A[0]+'_metrics'][k]==a and r[A[1]+'_metrics'][k]==b for r in rows)) for a in [0,1] for b in [0,1]])
group(summary['overall'],records);assert [x['encoding'] for x in summary['cells']]==list(E)
for cell,n in zip(summary['cells'],[5,3,0,9,11]): assert cell['original_n']==20 and cell['selected_n']==n;group(cell,[r for r in records if r['encoding']==cell['encoding']])
assert len(summary['seed_groups'])==14
for g in summary['seed_groups']:
 rows=[r for r in records if r['seed']==g['seed']];group(g,rows);eq(g['pairs'],rows);eq(g['selected_encodings'],[r['encoding'] for r in rows])
result['aggregate']={a:dict(aggregate[a]) for a in A};result['failure_counts']={a:dict(failures[a]) for a in A};result['policy_counts']=dict(counts);result['checks']=dict(checks);result['elapsed_seconds']=time.monotonic()-start;result['status']='PASS';result['scope']={'scientific_module_imports':0,'physics_steps':0,'synthetic_physics_steps':0,'future_draws':0,'past_draws':0,'cli_calls':0,'basis':'现存JSON完整具体类型及字节、独立被动观察与账目/分母/汇总核算'}
(O/'audit_v1.result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['pairs']},ensure_ascii=False,indent=2))
