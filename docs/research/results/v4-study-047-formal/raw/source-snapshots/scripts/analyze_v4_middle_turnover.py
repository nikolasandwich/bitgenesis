"""Study045 read-only identity turnover and saved energy-event projection.

No physics, phase reconstruction, or Study042 ledger recomputation is performed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import time

OUTPUT = Path('data/v4-study-045')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
ARMS = ('control', 'ablation')
CATEGORIES = ('short_window', 'remaining_conditional')
MIDDLE = (101, 102)
FLAGS = ('occupied', 'material_match', 'genetic_match', 'whole_component',
         'root_descendant', 'all_new', 'post_birth', 'selected_ancestry', 'copy', 'new_copy')
OVERLAPS = ('G', 'physically_empty_both', 'G_genetic_match', 'G_whole_component',
            'G_root_descendant', 'G_all_new', 'G_post_birth', 'G_selected_ancestry',
            'G_other_copy_gates', 'double_new')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def region(site):
    return 'upper' if site in (85, 86) else 'middle' if site in MIDDLE else 'lower' if site in (117, 118) else 'other'


def snapshot(tick, ids, units, old):
    require(old['tick'] == tick, '044 tick alignment')
    require(old['slots'][1]['sites'] == list(MIDDLE) and old['slots'][1]['identities'] == [ids[s] for s in MIDDLE], '044 middle identities')
    middle = []
    for site in MIDDLE:
        require((ids[site] is None) == (units[site] is None), 'occupancy identity agreement')
        middle.append(dict(site=site, identity=ids[site], material=None if units[site] is None else units[site]['material']))
    upper, lower = (deepcopy(old['slots'][s]) for s in (0, 2))
    require(all(isinstance(slot[k], bool) for slot in (upper, lower) for k in FLAGS), '044 boolean gate vector')
    both = {k: upper[k] and lower[k] for k in FLAGS}
    bridges = [p['identity'] is not None and p['material'] == 0 for p in middle]
    absent = not any(bridges)
    empty = all(p['identity'] is None for p in middle)
    genetic = all(both[k] for k in ('occupied', 'material_match', 'genetic_match'))
    double = old['new_copy_count'] >= 2
    overlaps = dict(G=absent, physically_empty_both=empty, G_genetic_match=absent and genetic,
                    G_whole_component=absent and both['whole_component'],
                    G_root_descendant=absent and both['root_descendant'],
                    G_all_new=absent and both['all_new'], G_post_birth=absent and both['post_birth'],
                    G_selected_ancestry=absent and both['selected_ancestry'],
                    G_other_copy_gates=absent and genetic and both['root_descendant'] and both['all_new'],
                    double_new=double)
    return dict(tick=tick, middle=middle, B101=bridges[0], B102=bridges[1], G=absent,
                physically_empty_both=empty, upper=upper, lower=lower, both_gates=both,
                genetic_context=genetic, actual_whole_components=both['whole_component'],
                component_equivalence=(absent == both['whole_component']) if genetic else None,
                actual_double_new=double, overlaps=overlaps)


def intervals(diagnostic, rows, key):
    """Future saved-state runs, retaining diagnostic-only left-censored exits."""
    answer = []
    active = bool(diagnostic['overlaps'][key])
    current = dict(start=None, end=None, length=0, left_censored=True,
                   right_censored=False, entry_tick=None, exit_tick=None) if active else None
    for row in rows:
        present = row['overlaps'][key]
        if present:
            if current is None:
                current = dict(start=None, end=None, length=0, left_censored=False,
                               right_censored=False, entry_tick=row['tick'], exit_tick=None)
            if current['start'] is None:
                current['start'] = row['tick']
            current['end'] = row['tick']
            current['length'] += 1
        elif current is not None:
            current['exit_tick'] = row['tick']
            answer.append(current)
            current = None
    if current is not None:
        current['right_censored'] = True
        answer.append(current)
    return answer


def gap_records(t0, identities):
    answer = []
    for site in MIDDLE:
        members = sorted((p for p in identities if p['site'] == site), key=lambda p: (p['birth_tick'], p['identity']))
        def append(previous, following):
            left, right = previous is None, following is None
            start = t0 if left else previous['exit']['tick']
            end = 32 if right else following['birth_tick']
            require(end >= start, 'nonnegative turnover interval')
            ticks = list(range(start + int(left), end + int(right)))
            answer.append(dict(site=site, predecessor=None if left else previous['identity'],
                successor=None if right else following['identity'], start_boundary=start, end_boundary=end,
                distance_ticks=end-start, empty_ticks=ticks, empty_saved_states=len(ticks),
                left_censored=left, right_censored=right, same_tick_replacement=not left and not right and start == end,
                material_changed=(previous['birth_material'] != following['birth_material']) if not left and not right else None))
        if not members or not members[0]['left_censored']:
            append(None, members[0] if members else None)
        for pos, member in enumerate(members):
            if member['exit']['kind'] == 'death':
                append(member, members[pos + 1] if pos + 1 < len(members) else None)
            else:
                require(pos == len(members)-1, 'living identity cannot have successor')
    return answer


def reuse_events(ledger):
    """Select values from the existing complete ledger; never recompute them."""
    first, last = ledger['rows'][0], ledger['rows'][-1]
    entry = dict(kind=first['phase'], tick=first['tick'], energy=first['end_energy'])
    successes = []
    for row in ledger['rows']:
        if row.get('reason') == 'formed':
            proposal = row['proposal']
            successes.append(dict(tick=row['tick'], source=proposal['source'], target=proposal['target'],
                parent_identity=proposal['identity'], child_identity=proposal['child_id'],
                preformation_energy=row['preformation_energy'], parent_energy=row['end_energy'], child_energy=row['child_transfer']))
    died = ledger['window']['death_tick'] is not None
    exit_event = dict(kind='death' if died else 'endpoint', tick=last['tick'],
                      energy=last['end_energy'], right_censored=ledger['window']['right_censored'])
    return entry, successes, exit_event


def project_events(arm, person, left_censored):
    """Read only birth/entry, successful formation, and death/endpoint stages."""
    identity, site = person['id'], person['site']
    initial = arm['initial']
    entry = dict(kind='initial', tick=initial['tick'], energy=initial['units'][site]['energy']) if left_censored else None
    successes, exit_event = [], None
    before = initial
    for saved in arm['rows']:
        tick, physical = saved['tick'], saved['physical']
        proposals = physical['material']['proposals']
        if not left_censored and person['birth_tick'] == tick:
            require(saved['site_ids'][site] == identity and identity in [b['id'] for b in saved['births']], 'saved birth identity')
            matches = [q for q in proposals if q['target'] == site and q['reason'] == 'formed']
            require(len(matches) == 1, 'unique birth formation')
            q = matches[0]
            require(before['site_ids'][q['source']] == person['parent'], 'birth parent identity')
            require(physical['units'][site]['energy'] == q['child_energy'] == person['birth_energy'], 'birth saved energy')
            require(q['material'] == person['material'], 'birth material provenance')
            entry = dict(kind='birth', tick=tick, energy=q['child_energy'])
        if before['site_ids'][site] == identity:
            require(tick > person['birth_tick'], 'birth identity cannot act')
            phase = physical['interaction_units'][site]
            require(phase is not None, 'preformation phase identity present')
            choices = [q for q in proposals if q['source'] == site]
            require(len(choices) <= 1, 'unique source proposal')
            if identity in saved['deaths']:
                require(phase['energy'] == 0 and not choices and site in physical['material']['dissolved'], 'death phase is not proposal')
                require(person['death_tick'] == tick and saved['site_ids'][site] != identity, 'death chronology')
                exit_event = dict(kind='death', tick=tick, energy=phase['energy'], right_censored=False)
            elif choices and choices[0]['reason'] == 'formed':
                q = choices[0]
                child = saved['site_ids'][q['target']]
                births = [b for b in saved['births'] if b['id'] == child]
                require(len(births) == 1 and births[0]['parent'] == identity and births[0]['birth_tick'] == tick, 'formation child identity')
                require(saved['site_ids'][site] == identity and physical['units'][site]['energy'] == q['parent_energy'], 'formation parent saved energy')
                require(physical['units'][q['target']]['energy'] == q['child_energy'] == births[0]['birth_energy'], 'formation child saved energy')
                successes.append(dict(tick=tick, source=site, target=q['target'], parent_identity=identity,
                    child_identity=child, preformation_energy=phase['energy'], parent_energy=q['parent_energy'], child_energy=q['child_energy']))
        before = dict(site_ids=saved['site_ids'], units=physical['units'])
    require(entry is not None, 'identity entry witnessed')
    if exit_event is None:
        require(person['death_tick'] is None and before['site_ids'][site] == identity, 'right-censored identity remains present')
        exit_event = dict(kind='endpoint', tick=32, energy=before['units'][site]['energy'], right_censored=True)
    return entry, successes, exit_event


def analyze_arm(encoding, branch, old, census, reuse, old_records, arm_name):
    from scripts.middle_turnover_inputs import read, digest
    arm, selection = branch[arm_name], branch['selection']
    seed, t0 = selection['seed'], selection['t0']
    people = arm['final']['individuals']
    require([r['tick'] for r in arm['rows']] == list(range(t0+1, 33)), 'continuous future saved states')
    require(arm['initial']['tick'] == t0 and old['diagnostic']['tick'] == t0, 'diagnostic origin')
    require([r['tick'] for r in old['rows']] == list(range(t0+1, 33)), '044 future chronology')
    expected = [c for c in census if (c['encoding'],c['seed'],c['arm']) == (encoding,seed,arm_name)]
    require(len(expected) == 1, 'unique census arm')
    expected = expected[0]
    require(expected['t0'] == t0 and expected['saved_states'] == len(arm['rows']), 'census chronology')
    refs = {r['identity']:r for r in reuse if (r['encoding'],r['seed'],r['arm']) == (encoding,seed,arm_name)}
    if refs:
        require(arm_name == 'control' and expected['energy_plan'] == 'reuse_042', 'reuse old policy only')
        old_branch = read(next(iter(refs.values()))['old_branch_source'])
        require(old_branch['selection'] == selection and old_branch['ablation'] == arm, 'complete old arm equality before reuse')
    identities = []
    for item in expected['identities']:
        identity = item['identity']
        person = people[identity]
        require(person['id'] == identity and all(person[k] == item[k] for k in ('site','parent','birth_tick')), 'census identity provenance')
        chain, cursor = [], identity
        while cursor is not None:
            require(cursor not in chain and 0 <= cursor < len(people), 'acyclic complete ancestry')
            chain.append(cursor)
            cursor = people[cursor]['parent']
        parent = person['parent']
        source = None if parent is None else people[parent]['site']
        reference = deepcopy(refs.get(identity))
        if reference is not None:
            parts = reference['json_pointer'].strip('/').split('/')
            require(len(parts) == 3 and parts[1] == 'identities', '042 ledger pointer')
            original = old_records[int(parts[0])]
            ledger = original['identities'][int(parts[2])]
            require(original['encoding'] == encoding and original['selection'] == selection, '042 exact case')
            require(digest(reference['source_path']) == reference['source_file_sha256'] and canonical_hash(ledger) == reference['normalized_record_sha256'], '042 exact record hash')
            require(ledger['identity'] == identity and all(ledger[k] == person[k] for k in ('site','parent','birth_tick','birth_energy')), '042 birth provenance')
            require(ledger['left_censored'] == item['left_censored'], '042 entry censoring')
            entry, successes, exit_event = reuse_events(ledger)
        else:
            require(expected['energy_plan'] == 'needed_event_projection', 'all reused identities require exact ledger')
            entry, successes, exit_event = project_events(arm, person, item['left_censored'])
        identities.append(dict(key=[encoding,seed,arm_name,identity], identity=identity, site=person['site'], parent=parent,
            source_site=source, source_region=region(source), ancestry_chain=chain,
            selected_ancestors=[i for i in chain if i in selection['offspring_ids']],
            birth_tick=person['birth_tick'], birth_energy=person['birth_energy'], birth_material=person['material'],
            left_censored=item['left_censored'], entry=entry, successful_formations=successes, exit=exit_event,
            energy_source=dict(mode='reuse_042' if reference is not None else 'event_projection', reference=reference)))
    identities.sort(key=lambda p:p['identity'])
    states = [(t0, arm['initial']['site_ids'], arm['initial']['units'])]
    states += [(r['tick'],r['site_ids'],r['physical']['units']) for r in arm['rows']]
    observed, anomalies, transitions = [], [], []
    visible = set()
    for (tick,ids,units), previous in zip(states,[old['diagnostic']]+old['rows']):
        row = snapshot(tick,ids,units,previous)
        for member in row['middle']:
            identity, site = member['identity'], member['site']
            if identity is not None:
                visible.add(identity)
                person = people[identity]
                require(person['id'] == identity and person['site'] == site and person['birth_tick'] <= tick, 'saved identity provenance')
                require(person['death_tick'] is None or person['death_tick'] > tick, 'saved identity survival')
                if member['material'] != person['material']:
                    anomalies.append(dict(tick=tick,site=site,identity=identity,birth_material=person['material'],observed_material=member['material']))
            if observed:
                before = observed[-1]['middle'][MIDDLE.index(site)]
                if before['identity'] != identity or before['material'] != member['material']:
                    transitions.append(dict(tick=tick,site=site,before_identity=before['identity'],after_identity=identity,
                        before_material=before['material'],after_material=member['material'],
                        identity_changed=before['identity'] != identity,material_changed=before['material'] != member['material']))
        observed.append(row)
    require(visible == {p['identity'] for p in identities}, 'complete visible census')
    diagnostic, rows = observed[0], observed[1:]
    spans = {k:intervals(diagnostic,rows,k) for k in OVERLAPS}
    prior = deepcopy(old['prior043'])
    require(prior['matched'] and prior['new_copy_counts'] == [r['new_copy_count'] for r in old['rows']] == arm['new_copy_counts'], 'original per-tick count agreement')
    double = [[v['start'],v['end']] for v in spans['double_new'] if v['length']]
    require(double == prior['episodes'] == arm['episodes'], 'original double episode agreement')
    longest = max((v['length'] for v in spans['double_new']),default=0)
    require(arm['metrics']['longest_double'] == longest and arm['metrics']['double_new_ever'] == int(longest>0) and arm['metrics']['persistent10'] == int(longest>=10), 'original double metric agreement')
    gaps = gap_records(t0,identities)
    by_tick = {row['tick']:row for row in rows}
    for gap in gaps:
        require(all(by_tick[t]['middle'][MIDDLE.index(gap['site'])]['identity'] is None for t in gap['empty_ticks']), 'gap states physically empty')
    return dict(arm=arm_name,t0=t0,saved_steps=len(rows),identities=identities,diagnostic=diagnostic,rows=rows,
                gaps=gaps,intervals=spans,transitions=transitions,material_anomalies=anomalies,
                component_counterexamples=[deepcopy(r) for r in observed if r['component_equivalence'] is False],prior044=prior)


def analyze_pair(encoding, branch, prior044, census_arms, reuse, old_records):
    require(encoding in ENCODINGS and prior044['encoding'] == encoding and prior044['selection'] == branch['selection'], 'paired044 selection')
    require(branch['control']['initial'] == branch['ablation']['initial'], 'identical paired diagnostic states')
    return dict(encoding=encoding,selection=deepcopy(branch['selection']),arms={
        arm:analyze_arm(encoding,branch,prior044['arms'][arm],census_arms,reuse,old_records,arm) for arm in ARMS})


def group(arms):
    identities = [p for arm in arms for p in arm['identities']]
    gaps = [g for arm in arms for g in arm['gaps']]
    rows = [r for arm in arms for r in arm['rows']]
    return dict(n=len(arms),saved_steps=len(rows),diagnostic_states=len(arms),identities=len(identities),
        births=sum(not p['left_censored'] for p in identities),left_censored=sum(p['left_censored'] for p in identities),
        right_censored=sum(p['exit']['right_censored'] for p in identities),natural_deaths=sum(p['exit']['kind']=='death' for p in identities),
        successes=sum(len(p['successful_formations']) for p in identities),
        reused_identities=sum(p['energy_source']['mode']=='reuse_042' for p in identities),
        projected_identities=sum(p['energy_source']['mode']=='event_projection' for p in identities),gaps=len(gaps),
        same_tick_replacements=sum(g['same_tick_replacement'] for g in gaps),
        identity_replacements=sum(g['predecessor'] is not None and g['successor'] is not None for g in gaps),
        material_replacements=sum(g['material_changed'] is True for g in gaps),
        left_censored_gaps=sum(g['left_censored'] for g in gaps),right_censored_gaps=sum(g['right_censored'] for g in gaps),
        empty_saved_states=sum(g['empty_saved_states'] for g in gaps),
        material_anomalies=sum(len(a['material_anomalies']) for a in arms),component_counterexamples=sum(len(a['component_counterexamples']) for a in arms),
        transitions=sum(len(a['transitions']) for a in arms),ticks={k:sum(r['overlaps'][k] for r in rows) for k in OVERLAPS},
        intervals={k:sum(len(a['intervals'][k]) for a in arms) for k in OVERLAPS},
        longest={k:max((v['length'] for a in arms for v in a['intervals'][k]),default=0) for k in OVERLAPS})


def difference(new, old):
    if isinstance(new,dict):
        require(new.keys() == old.keys(), 'matching numeric aggregate fields')
        return {k:difference(new[k],old[k]) for k in new}
    return new-old


def summarize(records, index):
    cells=[]
    for encoding in ENCODINGS:
        for category in CATEGORIES:
            for arm in ARMS:
                chosen=[r['arms'][arm] for r in records if r['encoding']==encoding and r['selection']['category']==category]
                cells.append(dict(encoding=encoding,category=category,arm=arm,policy_denominator=20,
                    triggered_encoding_count=sum(i['trigger'] for i in index if i['encoding']==encoding),**group(chosen)))
    return dict(index_cases=len(index),triggered=sum(i['trigger'] for i in index),no_trigger=sum(not i['trigger'] for i in index),
        cells=cells,overall={a:group([r['arms'][a] for r in records]) for a in ARMS},
        paired=[dict(encoding=r['encoding'],seed=r['selection']['seed'],delta=difference(group([r['arms']['ablation']]),group([r['arms']['control']]))) for r in records])


def main():
    from scripts.middle_turnover_inputs import bindings,input_paths,read,save,digest,capture
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started=time.monotonic();records=[];inventory=[]
    meta=dict(status='running',planned_cases=28,planned_arms=56,completed_cases=0,completed_arms=0,saved_steps=0,diagnostic_states=0,
              index_cases=100,no_trigger_cases=72,new_simulation_steps=0,new_environment_sources=0,new_independent_initial_worlds=0,
              time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():
        require(time.monotonic()-started<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728, 'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)):digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name!='metadata.json'}
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_inventory_errors']={};inventory=input_paths(meta['input_inventory_errors']);meta['input_paths']=inventory
        meta['input_sha256'],meta['input_read_errors_before']=capture(inventory)
        save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        require(bindings()==meta['input_sha256'] and not meta['input_inventory_errors'] and not meta['input_read_errors_before'], 'validated initial inputs');budget()
        census=read('docs/research/results/v4-study-045-design-census.json');index=deepcopy(census['index'])
        require(len(index)==100 and sum(i['trigger'] for i in index)==28 and sum(i['short_window'] for i in index)==10, 'full frozen index')
        require(all(sorted(i['seed'] for i in index if i['encoding']==e)==list(range(120000,120020)) for e in ENCODINGS), 'five complete encoding cohorts')
        require(all(i['branch'] is None and i['applicability']=='not_applicable' for i in index if not i['trigger']), 'retain non-applicable cases')
        save(OUTPUT/'index.json',index)
        previous={(r['encoding'],r['selection']['seed']):r for r in read('data/v4-study-044/records.json')}
        ledgers=read('data/v4-study-042/records.json')
        for item in index:
            if not item['trigger']:continue
            budget();branch=read(item['branch'])
            require(branch['selection']['seed']==item['seed'] and branch['selection']['source']==item['source'], 'indexed branch identity')
            records.append(analyze_pair(item['encoding'],branch,previous[(item['encoding'],item['seed'])],census['arms'],census['reuse_042'],ledgers))
            meta.update(completed_cases=len(records),completed_arms=2*len(records),saved_steps=sum(r['arms'][a]['saved_steps'] for r in records for a in ARMS),diagnostic_states=2*len(records))
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta);budget()
        summary=summarize(records,index)
        require((meta['completed_cases'],meta['completed_arms'],meta['saved_steps'],meta['diagnostic_states'])==(28,56,780,56), 'complete frozen denominator')
        require(sum(summary['overall'][a]['identities'] for a in ARMS)==202 and sum(summary['overall'][a]['reused_identities'] for a in ARMS)==35 and sum(summary['overall'][a]['projected_identities'] for a in ARMS)==167, 'complete identity projection')
        meta.update(identities=sum(summary['overall'][a]['identities'] for a in ARMS),
                    left_censored_identities=sum(summary['overall'][a]['left_censored'] for a in ARMS),
                    reused_identities=sum(summary['overall'][a]['reused_identities'] for a in ARMS),
                    projected_identities=sum(summary['overall'][a]['projected_identities'] for a in ARMS),
                    reuse_arms=sum(a['energy_plan']=='reuse_042' for a in census['arms']),
                    event_projection_arms=sum(a['energy_plan']=='needed_event_projection' for a in census['arms']))
        require((meta['left_censored_identities'],meta['reuse_arms'],meta['event_projection_arms'])==(12,8,48), 'frozen censoring and energy provenance')
        save(OUTPUT/'summary.json',summary)
        require(bindings()==meta['input_sha256'], 'unchanged validated inputs');budget()
        meta['status']='complete'
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc));raise
    finally:
        try:
            meta['input_sha256_after'],meta['input_read_errors_after']=capture(inventory)
            meta['output_sha256']=hashes();meta['elapsed_seconds']=time.monotonic()-started
            if meta['status']=='complete':
                require(meta['input_sha256_after']==meta['input_sha256'] and not meta['input_read_errors_after'], 'final input binding');budget()
            save(OUTPUT/'metadata.json',meta)
            if meta['status']=='complete':budget()
        except BaseException as exc:
            meta.update(status='failed',finalization_error=repr(exc),elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'metadata.json',meta);raise


if __name__ == '__main__':
    main()
