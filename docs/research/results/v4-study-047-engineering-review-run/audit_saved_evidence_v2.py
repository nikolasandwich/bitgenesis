"""Independent saved-evidence audit. No research imports, RNG, or physics."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import ast, hashlib, json, re, subprocess, tarfile, tempfile, time
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
E = ROOT / 'docs/research/results/v4-study-047-engineering'
R = E / 'raw'
BASE = ROOT / 'data/v4-study-047-engineering'
COMMIT = '931dd9e70f6b89813635f7d25e74cdc8cf42e0bf'
ARMS = ('continue_north', 'withdraw_to_natural')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
started = time.monotonic()
results = dict(reviewer='/root/withdrawal_engineering_review', task='2.3', created_at_utc=datetime.now(timezone.utc).isoformat(), new_physical_steps=0, new_future_draws=0, scientific_modules_imported=False)
nodes = 0

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vh(v): return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
def hashes(mapping, base=ROOT):
    for p, h in mapping.items(): assert sha(base / p) == h, ('hash', str(base / p))
    return len(mapping)
def strict(a, b, label):
    global nodes
    nodes += 1
    assert type(a) is type(b), (label, type(a).__name__, type(b).__name__)
    if type(a) is dict:
        assert a.keys() == b.keys(), (label, 'keys')
        for k in a: strict(a[k], b[k], label + '/' + k)
    elif type(a) is list:
        assert len(a) == len(b), (label, 'length')
        for i, (x, y) in enumerate(zip(a, b)): strict(x, y, label + '/' + str(i))
    else: assert a == b, (label, a, b)
def write(name, obj):
    with (OUT / name).open('x', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')

before = read(OUT / 'review-inputs-before.json')
hashes(before['files_sha256'])
pre = read(R / 'preflight.json')
strict(pre['git'], dict(commit=COMMIT, origin_main=COMMIT, status=''), 'clean original preflight')
assert pre['active_route_processes'] == [] and pre['formal_directory_exists'] is False
results['original_tracked_files_currently_equal'] = hashes(pre['git_tracked_sha256'])
assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == COMMIT
results['current_approvals'] = {}
for role, task, count in [('producer','2.1',1985),('verifier','2.2',3023)]:
    p = ROOT / f'docs/research/results/v4-study-047-{role}-review.json'; gate = read(p)
    assert gate['verdict'] == 'APPROVED' and gate['task'] == task and gate['independent_author_review'] is True
    strict(gate['files_sha256'], gate['files_sha256_after'], role + ' approval before/after')
    assert hashes(gate['files_sha256']) == count and sha(p) == pre['reviews'][role]['sha256']
    results['current_approvals'][role] = dict(bindings_verified=count, sha256=sha(p))
for source, item in pre['source_snapshots'].items():
    p = R / item['snapshot']
    assert p.read_bytes() == (ROOT/source).read_bytes() and sha(p) == item['sha256'] and p.stat().st_size == item['bytes']
assert len(pre['source_snapshots']) == 201
results['source_snapshots_current_byte_identical'] = 201

manifest = read(E/'archive-manifest.json'); archive = ROOT/manifest['archive_path']; restored=[]
assert sha(archive) == manifest['archive_sha256'] == '57c0ab9830a8a06725fcc6aa6c9a8290ab62cbde3515df63d927ab9094bf4f0e'
assert archive.stat().st_size == manifest['archive_bytes'] == 1101788
with tarfile.open(archive,'r:gz') as tar, tempfile.TemporaryDirectory(prefix='restore-', dir=OUT) as temp:
    members = tar.getmembers()
    assert all(m.isfile() for m in members) and len(members) == len({m.name for m in members}) == 236
    assert {m.name for m in members} == {e['member'] for e in manifest['entries']}
    assert {str(p.relative_to(ROOT)) for p in BASE.rglob('*') if p.is_file()} == {e['source'] for e in manifest['entries']}
    for e in manifest['entries']:
        name=Path(e['member']); assert not name.is_absolute() and '..' not in name.parts
        p=Path(temp)/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(tar.extractfile(e['member']).read())
        assert p.read_bytes() == (ROOT/e['source']).read_bytes() == (ROOT/e['archive_copy']).read_bytes()
        assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes']
        restored.append(dict(member=e['member'],sha256=sha(p),bytes=p.stat().st_size,original_direct_tar_restored_bytes_equal=True))
assert sum(e['bytes'] for e in restored)==manifest['original_bytes']==8251010
results['archive_restore']=dict(files=236,bytes=8251010,status='PASS',physically_restored=True,temporary_restore_removed=True)

science=['cases/east-120005.json','environments/120005.json','records.json','index.json','summary.json']
results['routes']={}
for role,status,count in [('producer','complete',1194),('verifier','verified',1200)]:
    route=R/role; m=read(route/'metadata.json'); req=read(R/'execution'/role/'request.json'); ex=read(R/'execution'/role/'result.json')
    keys=['status','mode','physical_steps','future_generator_ticks','reconstructed_past_generator_ticks','completed_pairs','planned_pairs','fixed_future_ticks','synthetic_fixture_steps','time_limit_seconds','storage_limit_bytes']
    strict([m[k] for k in keys],[status,'engineering',64,32,640,1,1,[33,64],0,600,134217728],role+' exact limits')
    assert m['git_commit']==COMMIT and m['work_done'] is True
    for key in ('input_read_errors_before','input_read_errors_after','output_read_errors','finalization_errors'): assert m[key]=={},(role,key)
    strict(m['input_sha256'],m['input_sha256_after'],role+' input before/after'); assert hashes(m['input_sha256'])==count
    assert sorted(m['output_sha256'])==sorted(science); hashes(m['output_sha256'],route)
    strict(req['source_sha256_before'],ex['source_sha256_after'],role+' execution source before/after'); assert hashes(req['source_sha256_before'])==201
    strict(req['git_before'],pre['git'],role+' clean start'); strict(ex['git_after'],pre['git'],role+' clean finish')
    assert req['environment_is_complete'] is True and req['environment']['PYTHONPATH']=='src'
    assert set(req['environment']) <= {'PATH','HOME','TMPDIR','LANG','PYTHONPATH'}
    assert req['cwd']==str(ROOT) and req['scientific_invocation_ordinal']==1
    argv=['.venv/bin/python','scripts/run_v4_middle_withdrawal.py' if role=='producer' else 'scripts/verify_v4_middle_withdrawal.py','--mode','engineering']
    if role=='verifier': argv+=['--producer','data/v4-study-047-engineering/producer']
    argv+=['--output','data/v4-study-047-engineering/'+role]; strict(req['command'],argv,role+' argv')
    assert ex['exit_code']==0 and ex['wall_seconds']<600 and m['elapsed_seconds']<600
    assert ex['active_route_processes_after']==[] and ex['formal_directory_exists'] is False
    hashes(ex['raw_output_sha256'],R/'execution'/role); assert (R/'execution'/role/'stderr.bin').read_bytes()==b''
    files=[p for p in route.rglob('*') if p.is_file()]; assert len(files)==(6 if role=='producer' else 7)
    size=sum(p.stat().st_size for p in files); case_size=(route/science[0]).stat().st_size; env_size=(route/science[1]).stat().st_size
    aggregate_size=sum((route/f).stat().st_size for f in science[2:]); admin_size=size-case_size-env_size-aggregate_size
    projection=28*case_size+14*env_size+28*aggregate_size+4*admin_size
    assert size<134217728 and projection<134217728
    results['routes'][role]=dict(status=status,exit_code=0,physical_steps=64,future_generator_ticks=32,past_generator_ticks=640,input_bindings_verified=count,wall_seconds=ex['wall_seconds'],size_bytes=size,conservative_projection_bytes=projection,projection_is_guarantee=False)
proof=read(R/'verifier/proof.json'); vm=read(R/'verifier/metadata.json')
for k in ('input_sha256','input_sha256_after','output_sha256'): strict(proof[k],vm[k],'proof/'+k)
assert proof['status']=='verified'
assert read(R/'execution/producer/result.json')['finished_at_utc']<read(R/'execution/verifier/request.json')['started_at_utc']
results['complete_scientific_comparison']=[]
for name in science:
    p,v=R/'producer'/name,R/'verifier'/name; strict(read(p),read(v),name); assert p.read_bytes()==v.read_bytes()
    results['complete_scientific_comparison'].append(dict(path=name,strict_type_and_value_equal=True,bytes_equal=True,sha256=sha(p)))

case=read(R/'producer/cases/east-120005.json'); env=read(R/'producer/environments/120005.json')
assert (case['encoding'],case['seed'],case['status'])==('east',120005,'complete')
strict(env['natural_tape'],case['natural_tape'],'case natural tape')
assert vh(case['natural_tape'])==case['natural_tape_sha256']==env['sha256']
assert len(case['natural_tape'])==32 and set(env['states_after_tick64'])=={'directions','feeds'}
for state in env['states_after_tick64'].values():
    assert type(state) is list and len(state)==3 and state[0]==3 and len(state[1])==625 and all(type(x) is int for x in state[1])
for key in ('final','historical_removals','template'):
    ref=case['boundary'][key]; assert sha(ROOT/ref['path'])==ref['sha256']; value=read(ROOT/ref['path'])
    for part in ref['pointer'].strip('/').split('/'): value=value[part]
    assert vh(value)==ref['value_sha256']
    if key=='final':
        assert ref['path']=='data/v4-study-043/cases/east-120005.json' and ref['pointer']=='/ablation/final'
        for name in ARMS: strict(case[name]['initial'],value,name+' original043 full state')
    elif key=='template': strict(case['original_template'],value,'original038 full template')
    else:
        for name in ARMS: strict(case[name]['historical_removals'],value,name+' historical removals')

results['arms']={}
for name in ARMS:
    a=case[name]; initial,final=a['initial'],a['final']
    strict([initial['tick'],final['tick'],a['original_t0'],a['boundary_tick']],[32,64,19,32],name+' boundaries')
    assert len(a['rows'])==32 and len(initial['individuals'])==15
    assert final['parents']==[p['parent'] for p in final['individuals']]
    for i,person in enumerate(final['individuals']): assert person['id']==i and (person['parent'] is None or type(person['parent']) is int and person['parent']<i)
    assert all(i not in initial['site_ids'] and i not in final['site_ids'] for i in (0,1))
    strict(final['individuals'][:2],initial['individuals'][:2],name+' removed founders unchanged')
    previous_units,previous_ids=initial['units'],initial['site_ids']; previous_energy=sum(u['energy'] for u in previous_units if u)
    total_births=total_deaths=empty=changed=0; failures=Counter(); energies=Counter(); people=deepcopy(initial['individuals'])
    for tick,row,natural in zip(range(33,65),a['rows'],case['natural_tape']):
        p=row['physical']; strict([row['tick'],p['tick'],natural['tick']],[tick]*3,name+' ticks'); assert row['status']=='complete'
        assert len(natural['directions'])==256 and all(type(x) is int and x in range(4) for x in natural['directions'])
        assert len(natural['feed_sites_draw_order'])==len(set(natural['feed_sites_draw_order']))==4 and all(type(x) is int and 0<=x<256 for x in natural['feed_sites_draw_order'])
        expected=natural['directions'][:]
        if name=='continue_north': expected[101]=expected[102]=3
        strict(p['directions'],expected,name+' directions')
        for site in (101,102): empty+=int(previous_units[site] is None); changed+=int(p['directions'][site]!=natural['directions'][site])
        strict(p['mutation_tickets'],[[999,0,1] for _ in range(256)],name+' mutation tickets')
        feed=p['driven']['inputs']; strict([x['site'] for x in feed],list(range(256)),name+' all feed sites')
        strict([x['proposed'] for x in feed],[8 if i in (85,86,117,118) else 0 for i in range(256)],name+' feed proposals')
        assert all(x['accepted']+x['rejected']==x['proposed'] for x in feed)
        assert sum(x['accepted'] for x in feed)==p['imported'] and sum(x['rejected'] for x in feed)==p['rejected_import']
        assert p['energy_before']==previous_energy and p['energy_after']==previous_energy+p['imported']-p['spent']==sum(u['energy'] for u in p['units'] if u)
        assert len(p['units'])==len(p['raw'])==len(row['site_ids'])==256
        assert sum(u is not None for u in p['units'])+sum(p['raw'])==p['material_before']==p['material_after']==7
        assert p['spent']==p['driven']['spent']+p['material']['spent']
        assert p['driven']['spent']==p['driven']['leakage']+p['driven']['interaction']['spent']
        assert p['material']['spent']==p['material']['construction_spent']+p['material']['copy_spent']
        for k in ('imported','rejected_import','spent'): energies[k]+=p[k]
        energies['leakage']+=p['driven']['leakage']; energies['bond_spent']+=p['driven']['interaction']['spent']
        for k in ('construction_spent','copy_spent'): energies[k]+=p['material'][k]
        reasons=Counter(x['reason'] for x in p['material']['proposals'])
        assert set(row['failure_counts'])=={'energy','occupied','raw_material','collision','formed'}
        strict(row['failure_counts'],{k:reasons[k] for k in row['failure_counts']},name+' failure reasons')
        assert len(row['proposal_gates'])==len(p['material']['proposals'])
        for gate,proposal in zip(row['proposal_gates'],p['material']['proposals']):
            for k in ('source','target','direction','reason'): strict(gate[k],proposal[k],name+' proposal gate')
            assert gate['expressed_material']==gate['parent_program'][gate['direction']]
            strict(gate['mutation_ticket'],[999,0,1],name+' gate mutation')
        failures.update(row['failure_counts']); births,deaths=row['births'],row['deaths']
        assert len(births)==reasons['formed'] and len(deaths)==len(p['material']['dissolved'])
        live_before={i for i in previous_ids if i is not None}; live_after={i for i in row['site_ids'] if i is not None}
        assert set(deaths)<=live_before and live_after==(live_before-set(deaths))|{b['id'] for b in births}
        for dead in deaths: people[dead]['death_tick']=tick
        for birth in births:
            assert birth['id']==len(people) and birth['birth_tick']==tick and birth['parent'] in live_before
            people[birth['parent']]['offspring']+=1; people.append(deepcopy(birth))
        for site,(unit,identity) in enumerate(zip(p['units'],row['site_ids'])):
            assert (unit is None)==(identity is None)
            if unit: strict([unit['material'],unit['program']],[people[identity]['material'],people[identity]['program']],name+' living identity')
        assert row['new_copy_count']==sum(x['all_new'] for x in row['components'])==sum(x['all_new'] for x in row['copies'])
        for comp in row['components']:
            assert comp['members']==row['observation']['components']['material'][comp['component']]
            assert comp['sites']==[row['site_ids'].index(i) for i in comp['members']]
            assert comp['genetic_copy'] is (len(comp['members'])==2 and comp['full_program_matches'] and comp['original_ancestry'])
            assert comp['all_new'] is (comp['genetic_copy'] and not set(comp['members'])&{0,1})
            assert comp['full_program_matches'] is (comp['fingerprint']==row['template_fingerprint'])
            for w in comp['member_witnesses']:
                person=people[w['identity']]; assert w['birth_tick']==person['birth_tick']
                assert w['born_after_original_t0'] is (person['birth_tick']>19) and w['born_after_tick32'] is (person['birth_tick']>32)
                chain=w['ancestor_chain']; assert chain[0]==person['id']
                for child,parent in zip(chain,chain[1:]): assert people[child]['parent']==parent
        total_births+=len(births); total_deaths+=len(deaths); previous_units,previous_ids,previous_energy=p['units'],row['site_ids'],p['energy_after']
    strict(people,final['individuals'],name+' passive event identity ledger')
    strict(previous_units,final['units'],name+' final units'); strict(previous_ids,final['site_ids'],name+' final alive')
    strict(a['rows'][-1]['physical']['raw'],final['raw'],name+' final raw'); strict(dict(failures),a['failure_counts'],name+' all failures')
    for k,v in energies.items(): assert a['metrics'][k]==v
    assert total_births==a['metrics']['births']==5 and total_deaths==a['metrics']['deaths']==6
    assert sum(i is not None for i in final['site_ids'])==6+total_births-total_deaths==5
    assert a['metrics']['final_energy']==217+energies['imported']-energies['spent']==252
    assert a['ledger']['energy_export']==0 and a['historical_energy_export']==124
    strict(a['new_copy_counts'],[2 if 44<=t<=48 else 0 for t in range(33,65)],name+' q sequence')
    strict(a['new_copy_counts'],[r['new_copy_count'] for r in a['rows']],name+' row q')
    strict(a['intervals'],[dict(start=44,end=48,length=5,left_censored_at_boundary=False,right_censored=False)],name+' intervals')
    assert a['tick32_diagnostic']['new_copy_count']==0 and a['cross_boundary'] is None and a['future_persistent10'] is False and a['longest_double']==5
    assert a['after32_formation_witnesses']==[] and a['after32_upper_witnesses']==[]
    assert a['metrics']['formation_supported']==1 and a['metrics']['after32_formation_supported']==0
    for w in a['formation_witnesses']: assert w['tick'] in range(44,49) and {(b['identity'],b['birth_tick']) for b in w['births']}=={(12,25),(14,30)}
    results['arms'][name]=dict(ticks=32,q2_interval=[44,48],future_persistent10=False,failures=dict(failures),energy_ledger=dict(energies),births=total_births,deaths=total_deaths,empty_mask_target_instances=empty,directions_changed_from_natural=changed,passive_identity_events_checked=True)
assert results['arms'][ARMS[0]]['directions_changed_from_natural']==48 and results['arms'][ARMS[1]]['directions_changed_from_natural']==0
assert all(x['empty_mask_target_instances']==21 for x in results['arms'].values())
strict(case['delta'],{k:case[ARMS[1]]['metrics'][k]-v for k,v in case[ARMS[0]]['metrics'].items()},'delta sign')
assert all(v==0 for v in case['delta'].values()) and case[ARMS[0]]['failure_counts']!=case[ARMS[1]]['failure_counts']

records,index,summary=(read(R/'producer'/f) for f in ('records.json','index.json','summary.json'))
assert len(records)==1 and len(index)==100
assert Counter(x['future_status'] for x in index)==Counter(complete=1,not_run_engineering=27,not_applicable_original_32_no_trigger=72)
assert [(x['encoding'],x['seed']) for x in index if x['future_status']=='complete']==[('east',120005)]
assert all(x['future'] is None for x in index if x['future_status']!='complete') and sum(x['short_window'] for x in index)==10
assert [sum(x['trigger'] for x in index if x['encoding']==e) for e in ENCODINGS]==[5,3,0,9,11]
assert [(x['encoding'],x['seed']) for x in index]==[(e,s) for e in ENCODINGS for s in range(120000,120020)]
strict(summary['pairs'],records,'summary records'); strict(records[0]['delta'],case['delta'],'record delta')
for name in ARMS: strict(records[0][name+'_metrics'],case[name]['metrics'],'record metrics '+name)
assert len(summary['cells'])==5 and len(summary['seed_groups'])==14
for group in [summary['overall'],*summary['cells'],*summary['seed_groups']]:
    relevant=records
    if 'encoding' in group: relevant=[r for r in records if r['encoding']==group['encoding']]
    if 'seed' in group: relevant=[r for r in records if r['seed']==group['seed']]
    assert group['n']==len(relevant)
    for metric in case['delta']:
        vals=[r['delta'][metric] for r in relevant]
        assert group['delta_totals'][metric]==sum(vals)
        assert group['mean_delta'][metric]==(str(Fraction(sum(vals),len(vals))) if vals else None)
        assert group['positive'][metric]==sum(v>0 for v in vals) and group['negative'][metric]==sum(v<0 for v in vals) and group['tie'][metric]==sum(v==0 for v in vals)
        for name in ARMS: assert group['arm_totals'][name][metric]==sum(r[name+'_metrics'][metric] for r in relevant)
    for metric,cells in group['binary_pairs'].items():
        assert [(x[ARMS[0]],x[ARMS[1]]) for x in cells]==[(0,0),(0,1),(1,0),(1,1)]
        for cell in cells: assert cell['n']==sum(all(r[name+'_metrics'][metric]==cell[name] for name in ARMS) for r in relevant)
results['index_summary']=dict(original=100,complete=1,unrun_engineering=27,original_na=72,selected_by_encoding=[5,3,0,9,11],seed_groups=14,all_aggregate_values_checked=True)

full=ROOT/'docs/research/results/v4-study-047-preflight-joint-validation/full-revalidated'; ex=read(full/'execution.json')
assert ex['exit_code']==0; strict(ex['files_sha256'],ex['files_sha256_after'],'historical full before/after'); assert hashes(ex['files_sha256'])==5
for filename,h in ex['files_sha256'].items(): assert sha(full/Path(filename).name)==h
hashes(ex['raw_output_sha256'],full); log=(full/'stderr.bin').read_text()
assert re.search(r'Ran 1070 tests in 77\.334s\s+OK\s*$',log)
related=[line for line in log.splitlines() if 'test_v4_middle_withdrawal' in line and line.endswith(' ... ok')]; assert len(related)==104
results['regression']=dict(status='PASS_REUSED_CURRENT_BYTES',tests=1070,related_tests=104,exit_code=0,seconds=77.334,reexecuted=False,path=str((full/'execution.json').relative_to(ROOT)),raw_output_and_five_current_source_snapshots_verified=True)
for label,suffix in [('compile','preflight-joint-validation/compile-revalidated'),('producer_help','producer-preflight-implementation/final-help'),('verifier_help','verifier-implementation/remediation-1-help')]:
    folder=ROOT/('docs/research/results/v4-study-047-'+suffix); ex=read(folder/'execution.json'); assert ex['exit_code']==0; hashes(ex.get('raw_output_sha256', ex.get('evidence_sha256')),folder)
    results[label]=dict(status='PASS_REUSED',exit_code=0,reexecuted=False)
seal=read(E/'validation-summary.json'); hashes(seal['files_sha256'])
assert sha(ROOT/'docs/research/v4-study-047-engineering.zh-CN.md')==seal['report_sha256']=='123419f692b1a97b9ae2010b13b51755d819c1e6916aefffa3893ace41d30582'
for label,expected in [('post-check',1),('post-check-v2',0)]:
    folder=R/label; ex=read(folder/'execution.json'); assert ex['exit_code']==expected; hashes(ex['raw_output_sha256'],folder)
    script=R/('evidence_audit.py' if label=='post-check' else 'evidence_audit_v2.py'); assert sha(script)==ex['source_sha256']
results['preserved_author_readonly_audit_failure']=dict(original_exit=1,corrected_exit=0,source_and_outputs_bound=True,scientific_reruns=0)
authored=[ROOT/'docs/research/v4-study-047-engineering.zh-CN.md',E/'seal_evidence.py']+[R/name for name in ('execution_runner.py','evidence_audit.py','evidence_audit_v2.py','archive_evidence.py','task-brief.zh-CN.md')]
markers=re.compile(r'\b(?:T'+r'BD|TO'+r'DO|FIX'+r'ME|HA'+r'CK|X'+r'XX)\b')
secrets=re.compile(r'(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|sk-[A-Za-z0-9]{32,})')
for p in authored:
    text=p.read_text(); assert not markers.search(text),('placeholder',str(p)); assert not secrets.search(text),('secret',str(p))
    assert all(line.rstrip(' \t')==line for line in text.splitlines()),('whitespace',str(p))
    if p.suffix=='.py': ast.parse(text,filename=str(p))
historical_whitespace=[]
for source,item in pre['source_snapshots'].items():
    p=R/item['snapshot']
    for number,line in enumerate(p.read_bytes().splitlines(),1):
        if line.rstrip(b' \t')!=line: historical_whitespace.append(dict(source=source,snapshot=str(p.relative_to(ROOT)),line=number))
results['static_checks']=dict(new_authored_files=len(authored),placeholders='CLEAN',concrete_secret_patterns='CLEAN',python_ast='PASS',new_authored_whitespace='CLEAN',verbatim_historical_whitespace=historical_whitespace)
assert subprocess.run(['git','diff','--exit-code'],cwd=ROOT,capture_output=True).returncode==0
assert subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0
assert not (ROOT/'data/v4-study-047').exists()
results['current_source_before_after']=hashes(before['files_sha256']); results['strict_comparison_nodes']=nodes
results['status']='PASS'; results['elapsed_seconds']=time.monotonic()-started
write('archive-restore-check.json',dict(status='PASS',member_count=236,total_bytes=8251010,archive_sha256=sha(archive),physically_restored=True,temporary_restore_removed=True,entries=restored))
write('audit-results.json',results)
print(json.dumps({k:results[k] for k in ('status','current_source_before_after','strict_comparison_nodes','elapsed_seconds','archive_restore','regression','new_physical_steps','new_future_draws')},ensure_ascii=False))
