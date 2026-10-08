"""Study046 task 1: immutable references and structural census, no classification.

Only existing Study041 events and Study045 gaps are indexed. No physical step,
proposal-gate reconstruction, energy ledger, component or interval algorithm is
called. The eight geometric slots are a plan, not observed proposal outcomes.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from time import monotonic

OUT = Path('docs/research/results')
PREFIX = 'v4-study-046-design-'
TIME_LIMIT = 600
STORAGE_LIMIT = 134217728
ARMS = ('control', 'ablation')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
METHOD_FILES = (
    'experiments/v4/study-046.md',
    'docs/design/v4-middle-refill-opportunities.zh-CN.md',
    '.kiro/specs/middle-refill-opportunities/requirements.md',
    '.kiro/specs/middle-refill-opportunities/design.md',
    '.kiro/specs/middle-refill-opportunities/research.md',
    'scripts/audit_v4_middle_refill_design.py',
)
EDGES = (
    (100, 101, 0, 'other'), (102, 101, 1, 'middle'),
    (85, 101, 2, 'upper'), (117, 101, 3, 'lower'),
    (101, 102, 0, 'middle'), (103, 102, 1, 'other'),
    (86, 102, 2, 'upper'), (118, 102, 3, 'lower'),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def capture(paths):
    hashes, errors = {}, {}
    for path in sorted(paths):
        try:
            hashes[path] = digest(path)
        except Exception as error:
            errors[path] = repr(error)
    return hashes, errors


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def exclusive_write(path, value):
    with path.open('xb') as output:
        output.write(encode(value))


def discover_paths(errors):
    """Discover before validation, so damaged sources still yield failure evidence."""
    paths = set(METHOD_FILES)
    for study in ('041', '045'):
        root = f'data/v4-study-{study}'
        names = ('metadata', 'records', 'summary', 'independent-verification')
        if study == '045':
            names += ('index',)
        for name in names:
            paths.update((f'{root}/{name}.json', f'{OUT}/v4-study-{study}-{name}.json'))
        for name in ('review', 'preservation'):
            paths.add(f'{OUT}/v4-study-{study}-{name}.json')
        for name in ('metadata', 'independent-verification'):
            path = f'{root}/{name}.json'
            try:
                paths.update(read(path)['input_sha256'])
            except Exception as error:
                errors[path] = repr(error)
        review_path = f'{OUT}/v4-study-{study}-review.json'
        try:
            paths.update(read(review_path)['files_sha256'])
        except Exception as error:
            errors[review_path] = repr(error)
    engineering = f'{OUT}/v4-study-045-engineering-review.json'
    preserve = f'{OUT}/v4-study-045-engineering/preservation.json'
    paths.update((engineering, preserve))
    try:
        review = read(engineering)
        paths.update(review['files_sha256'])
        paths.update(review['evidence_sha256'])
    except Exception as error:
        errors[engineering] = repr(error)
    try:
        # Historical temporary source paths are not persistent dependencies.
        paths.update(item['archive'] for item in read(preserve)['files'])
    except Exception as error:
        errors[preserve] = repr(error)
    return sorted(paths)


def check_manifest(expected, captured, label):
    require(isinstance(expected, dict) and expected, label + ' nonempty manifest')
    require(all(captured.get(path) == sha for path, sha in expected.items()), label + ' hashes')


def validate_completed(study, expected, captured):
    root = f'data/v4-study-{study}'
    meta = read(f'{root}/metadata.json')
    proof = read(f'{root}/independent-verification.json')
    require(meta['status'] == 'complete' and proof['status'] == 'verified', study + ' complete')
    require(meta['input_sha256'] == meta['input_sha256_after'] == expected,
            study + ' producer input epochs')
    require(proof['input_sha256'] == proof['input_sha256_after'] == expected,
            study + ' verifier input epochs')
    check_manifest(expected, captured, study + ' complete inputs')
    for obj in (meta, proof):
        require(obj['new_simulation_steps'] == 0 and obj['elapsed_seconds'] < TIME_LIMIT,
                study + ' zero physics and completed time budget')
        for name in ('input_read_errors_before', 'input_read_errors_after'):
            require(not obj.get(name, {}), study + ' source read errors')
    check_manifest({f'{root}/{name}': sha for name, sha in proof['files_sha256'].items()},
                   captured, study + ' proof outputs')
    check_manifest({f'{root}/{name}': sha for name, sha in meta['output_sha256'].items()},
                   captured, study + ' producer outputs')
    review_path = f'{OUT}/v4-study-{study}-review.json'
    review = read(review_path)
    require(review['verdict'] == 'APPROVED' and review['task'] == ('1.1' if study == '041' else '2.1'),
            study + ' completed review')
    check_manifest(review['files_sha256'], captured, study + ' review')
    preserve = read(f'{OUT}/v4-study-{study}-preservation.json')
    require(preserve['byte_identical'] is True, study + ' preservation claim')
    check_manifest(preserve['files_sha256'], captured, study + ' preserved originals')
    names = ('metadata', 'records', 'summary', 'independent-verification')
    if study == '045':
        names += ('index',)
        require(proof['files_sha256_before'] == proof['files_sha256_after'] == proof['files_sha256'],
                '045 verifier output epochs')
        require(len(review['files_sha256']) == 18, '045 full final review evidence')
    archive_bytes = 0
    for name in names:
        a = Path(f'{root}/{name}.json')
        b = Path(f'{OUT}/v4-study-{study}-{name}.json')
        require(a.read_bytes() == b.read_bytes(), study + ' archive byte identity ' + name)
        archive_bytes += a.stat().st_size
    require(preserve['files'] == len(names), study + ' archive file count')
    require(archive_bytes == preserve['bytes' if study == '041' else 'root_json_bytes'],
            study + ' archive byte count')
    return dict(input_files=len(expected), root_files=len(names), root_bytes=archive_bytes,
                review_files=len(review['files_sha256']), archive_bytes_checked=True,
                producer_status=meta['status'], verifier_status=proof['status'],
                historical_review_mode=review['review_mode'])


def validate_engineering(captured, current045):
    root = f'{OUT}/v4-study-045-engineering'
    review = read(f'{OUT}/v4-study-045-engineering-review.json')
    require(review['verdict'] == 'APPROVED', '045 engineering review')
    check_manifest(review['files_sha256'], captured, '045 engineering code')
    check_manifest(review['evidence_sha256'], captured, '045 engineering evidence')
    preserve = read(f'{root}/preservation.json')
    require(preserve['byte_identical'] is True and len(preserve['files']) == 8,
            '045 engineering preservation scope')
    total = 0
    for item in preserve['files']:
        require(captured.get(item['archive']) == item['sha256'], 'engineering archived hash')
        require(Path(item['archive']).stat().st_size == item['bytes'], 'engineering archived size')
        total += item['bytes']
    producer = read(f'{root}/producer/engineering.json')
    verifier = read(f'{root}/verifier/engineering-verification.json')
    failure = read(f'{root}/verifier-failure-2/engineering-verification.json')
    for obj in (producer, verifier, failure):
        require(len(obj['input_sha256']) == 916 and obj['input_sha256'] == obj['input_sha256_after'],
                'engineering source epochs internally equal')
    require(producer['physical_steps'] == 0 and verifier['new_simulation_steps'] == 0
            and failure['new_simulation_steps'] == 0, 'engineering zero physics')
    require(verifier['status'] == 'verified' and failure['status'] == 'failed',
            'engineering success and failure preserved')
    require(verifier['input_sha256'] == current045, 'final engineering source epoch')
    changes = sorted(path for path, sha in producer['input_sha256'].items()
                     if current045.get(path) != sha)
    require(changes == sorted(review['engineering']['producer_to_final_script_hash_changes']),
            'documented earlier producer source epoch')
    for obj in (verifier, failure):
        require(obj['files_sha256'] == obj['files_sha256_after'], 'engineering output epochs')
        for name, sha in obj['files_sha256'].items():
            require(captured.get(f'{root}/producer/{name}') == sha, 'engineering producer output')
    for name in ('records', 'summary'):
        require(Path(f'{root}/producer/{name}.json').read_bytes()
                == Path(f'{root}/verifier/{name}.json').read_bytes(), 'engineering output equality')
    require(read(f'{root}/verifier-failure-1/failure.json')['status'] == 'failed',
            'first engineering diagnostic retained')
    return dict(archive_files=8, archive_bytes=total, review_code_files=len(review['files_sha256']),
                review_evidence_files=len(review['evidence_sha256']),
                temporary_sources_required=False, historical_source_changes=changes)


def census(captured, budget, progress):
    index_path = 'data/v4-study-045/index.json'
    record_path = 'data/v4-study-045/records.json'
    route_path = 'data/v4-study-041/records.json'
    index, prior, routes = read(index_path), read(record_path), read(route_path)

    def ref(path, pointer, value):
        require(path in captured, 'referenced source belongs to manifest')
        return dict(path=path, file_sha256=captured[path], json_pointer=pointer,
                    normalized_sha256=normalized_hash(value))

    require(len(index) == len({(r['encoding'], r['seed']) for r in index}) == 100,
            'complete unique policy index')
    require(all(sum(r['encoding'] == e for r in index) == 20 for e in ENCODINGS), 'five full denominators')
    require(sum(not r['trigger'] for r in index) == 72 and sum(r['short_window'] for r in index) == 10,
            'untriggered and short-window index')
    require(all(r['branch'] is None and r['applicability'] == 'not_applicable'
                for r in index if not r['trigger']), 'untriggered applicability')
    observed = [r for r in index if r['trigger']]
    prior_map = {(r['encoding'], r['selection']['seed']): (i, r) for i, r in enumerate(prior)}
    route_map = {(r['encoding'], r['selection']['seed']): (i, r) for i, r in enumerate(routes)}
    require(len(prior_map) == len(prior) == len(observed) == 28, 'full 045 cohort')
    require(set(prior_map) == {(r['encoding'], r['seed']) for r in observed}, '045 index mapping')
    require(len(route_map) == len(routes) == 8 and set(route_map) == {
        (r['encoding'], r['seed']) for r in observed if r['encoding'] in ('east', 'west')}, '041 reuse cohort')
    geometry = []
    for source, target, direction, source_region in EDGES:
        x, y = source % 16, source // 16
        target_by_direction = (y * 16 + (x + 1) % 16, y * 16 + (x - 1) % 16,
                               ((y + 1) % 16) * 16 + x, ((y - 1) % 16) * 16 + x)
        require(target_by_direction[direction] == target, 'fixed incoming neighbor geometry')
        geometry.append(dict(source=source, target=target, required_direction=direction,
                             source_region=source_region))
    require(len({(e['source'], e['target']) for e in geometry}) == 8, 'eight unique incoming slots')

    arms, reused_rows, gaps = [], [], []
    for item in observed:
        budget()
        key = (item['encoding'], item['seed'])
        pair_index, saved045 = prior_map[key]
        branch_path = item['branch']
        require(branch_path in captured, '043 branch bound')
        branch = read(branch_path)
        selection = branch['selection']
        require(selection == saved045['selection'] and selection['t0'] == item['t0'], 'exact 043/045 selection')
        require(selection['seed'] == item['seed'] and selection['source'] == item['source'], 'indexed source')
        require(branch['control']['initial'] == branch['ablation']['initial'], 'paired diagnostic equality')
        t0, remaining = item['t0'], item['remaining']
        require(remaining == selection['remaining_steps'] == 32 - t0, 'fixed future horizon')
        for arm_name in ARMS:
            arm, old = branch[arm_name], saved045['arms'][arm_name]
            ticks = list(range(t0 + 1, 33))
            require([r['tick'] for r in arm['rows']] == [r['tick'] for r in old['rows']] == ticks,
                    'continuous 043/045 future sequence')
            require(arm['initial']['tick'] == old['diagnostic']['tick'] == t0, 'diagnostic alignment')
            arm_key = [*key, arm_name]
            pointer045 = f'/{pair_index}/arms/{arm_name}'
            plan = dict(key=arm_key, encoding=key[0], seed=key[1], arm=arm_name,
                t0=t0, saved_states=remaining, diagnostic_states=1, short_window=item['short_window'],
                category=selection['category'], target_ticks=remaining * 2, source_slots=remaining * 8,
                source=ref(branch_path, f'/{arm_name}', arm),
                diagnostic=ref(branch_path, f'/{arm_name}/initial', arm['initial']),
                turnover_diagnostic=ref(record_path, pointer045 + '/diagnostic', old['diagnostic']),
                proposal_plan='reuse_041' if arm_name == 'control' and key in route_map else 'needed_projection',
                rows=[], gap_keys=[])
            people045 = {p['identity']: p for p in old['identities']}
            coverage = set()
            for gap_index, gap in enumerate(old['gaps']):
                require(gap['site'] in (101, 102), 'gap middle target')
                predecessor, successor = gap['predecessor'], gap['successor']
                require(gap['left_censored'] == (predecessor is None)
                        and gap['right_censored'] == (successor is None), 'gap endpoint censoring')
                if predecessor is not None:
                    predecessor_record = people045[predecessor]
                    require(predecessor_record['site'] == gap['site']
                            and predecessor_record['exit']['kind'] == 'death'
                            and predecessor_record['exit']['tick'] == gap['start_boundary'], 'gap death reference')
                else:
                    require(gap['start_boundary'] == t0, 'gap entry boundary')
                if successor is not None:
                    successor_record = people045[successor]
                    require(successor_record['site'] == gap['site'] and not successor_record['left_censored']
                            and successor_record['birth_tick'] == gap['end_boundary'], 'gap successor reference')
                else:
                    require(gap['end_boundary'] == 32, 'gap endpoint horizon')
                first = t0 + 1 if predecessor is None else gap['start_boundary']
                decision_ticks = list(range(first, gap['end_boundary'] + 1))
                # Link saved gaps; do not regenerate their empty-state intervals.
                require(decision_ticks == gap['empty_ticks'] + ([] if successor is None else [gap['end_boundary']]),
                        'saved gap plus successful endpoint')
                require(len(gap['empty_ticks']) == gap['empty_saved_states'], 'saved gap length')
                require(all(t in ticks for t in decision_ticks), 'gap only future ticks')
                require(gap['same_tick_replacement'] == (predecessor is not None and successor is not None
                        and gap['start_boundary'] == gap['end_boundary']), 'same-tick gap marker')
                keys = {(gap['site'], t) for t in decision_ticks}
                require(not coverage.intersection(keys), 'disjoint per-arm target gap windows')
                coverage.update(keys)
                gap_pointer = pointer045 + f'/gaps/{gap_index}'
                reference = ref(record_path, gap_pointer, gap)
                gap_key = [*arm_key, gap_pointer]
                plan['gap_keys'].append(gap_key)
                gaps.append(dict(key=gap_key, encoding=key[0], seed=key[1], arm=arm_name,
                    reference=reference, original=deepcopy(gap), decision_ticks=decision_ticks,
                    decision_target_ticks=len(decision_ticks), decision_source_slots=len(decision_ticks) * 4,
                    intervals_recalculated=False))
            plan['gap_target_ticks'] = len(coverage)
            plan['gap_source_slots'] = len(coverage) * 4
            old_route = None
            if plan['proposal_plan'] == 'reuse_041':
                route_index, old_route = route_map[key]
                old_path = f'data/v4-study-039/cases/{key[0]}-{key[1]}.json'
                require(old_path in captured, '039 exact old branch bound')
                old_branch = read(old_path)
                require(old_route['selection'] == old_branch['selection'] == selection, '041/039/043 exact selection')
                require(old_branch['ablation'] == arm, 'entire 039 ablation equals 043 control')
                require([r['tick'] for r in old_route['rows']] == ticks, '041 exact row chronology')
                plan['reuse_041'] = dict(reference=ref(route_path, f'/{route_index}', old_route),
                    old_branch=ref(old_path, '/ablation', old_branch['ablation']),
                    complete_old_arm_equal=True, proposals_reclassified=False,
                    historical_verifier_mode='parent inline fallback independent algorithm')
            else:
                plan['reuse_041'] = None
            for row_index, (row043, row045) in enumerate(zip(arm['rows'], old['rows'])):
                before = arm['initial'] if row_index == 0 else arm['rows'][row_index - 1]
                physical = row043['physical']
                require(row043['tick'] == physical['tick'], 'physical tick')
                require(all(len(value) == 256 for value in (
                    before['site_ids'], row043['site_ids'], physical['interaction_units'],
                    physical['units'], physical['raw'], physical['directions'])), 'source array coverage')
                require(all(type(d) is int and 0 <= d < 4 for d in physical['directions']), 'all saved direction tickets')
                require(all(isinstance(p, dict) and {'id', 'parent', 'site'} <= p.keys()
                            for p in row043['births']), 'saved births object schema')
                require([v['site'] for v in row045['middle']] == [101, 102]
                        and [v['identity'] for v in row045['middle']]
                        == [row043['site_ids'][s] for s in (101, 102)], '045 saved target identity mapping')
                row_plan = dict(tick=row043['tick'], target_ticks=2, source_slots=8,
                    source=ref(branch_path, f'/{arm_name}/rows/{row_index}', row043),
                    before=ref(branch_path, f'/{arm_name}/initial' if row_index == 0
                               else f'/{arm_name}/rows/{row_index - 1}', before),
                    turnover=ref(record_path, pointer045 + f'/rows/{row_index}', row045))
                if old_route is not None:
                    existing = old_route['rows'][row_index]
                    events = existing['events']
                    saved_proposals = physical['material']['proposals']
                    require(len(events) == len(saved_proposals)
                            and [e['source'] for e in events] == [q['source'] for q in saved_proposals],
                            '041 full actual proposal coverage')
                    for event, proposal in zip(events, saved_proposals):
                        require(all(event[k] == proposal[k] for k in ('source', 'target', 'direction', 'reason')),
                                '041 exact saved proposal, no reclassification')
                        require(event['identity'] == before['site_ids'][event['source']], '041 actual source identity')
                    require(sorted(d['identity'] for d in existing['deaths']) == sorted(row043['deaths']),
                            '041 exact saved death identity coverage')
                    reuse = dict(key=[*arm_key, row043['tick']],
                        reference=ref(route_path, f'/{route_index}/rows/{row_index}', existing),
                        source043=row_plan['source'], existing_events=len(events), existing_deaths=len(existing['deaths']),
                        proposals_reclassified=False, includes_all_actual_directions=True)
                    reused_rows.append(reuse)
                    row_plan['reuse_041'] = reuse['reference']
                else:
                    row_plan['reuse_041'] = None
                plan['rows'].append(row_plan)
            arms.append(plan)
            progress.update(completed_arms=len(arms), saved_states=sum(a['saved_states'] for a in arms),
                            gap_references=len(gaps), reused_rows=len(reused_rows))
        progress['completed_pairs'] = len(arms) // 2

    counts = dict(index=len(index), not_applicable=sum(not r['trigger'] for r in index),
        pairs=len(observed), arms=len(arms), saved_states=sum(a['saved_states'] for a in arms),
        diagnostic_states=len(arms), short_window_pairs=sum(r['short_window'] for r in index),
        target_ticks=sum(a['target_ticks'] for a in arms), source_slots=sum(a['source_slots'] for a in arms),
        reuse_arms=sum(a['proposal_plan'] == 'reuse_041' for a in arms), reuse_rows=len(reused_rows),
        existing_041_events=sum(r['existing_events'] for r in reused_rows),
        existing_041_deaths=sum(r['existing_deaths'] for r in reused_rows),
        projection_arms=sum(a['proposal_plan'] == 'needed_projection' for a in arms),
        projection_rows=sum(a['saved_states'] for a in arms if a['proposal_plan'] == 'needed_projection'),
        gap_references=len(gaps), left_boundary_gaps=sum(g['original']['predecessor'] is None for g in gaps),
        death_boundary_gaps=sum(g['original']['predecessor'] is not None for g in gaps),
        successor_birth_endpoints=sum(g['original']['successor'] is not None for g in gaps),
        empty_saved_states=sum(g['original']['empty_saved_states'] for g in gaps),
        gap_target_ticks=sum(g['decision_target_ticks'] for g in gaps),
        gap_source_slots=sum(g['decision_source_slots'] for g in gaps))
    expected = dict(index=100, not_applicable=72, pairs=28, arms=56, saved_states=780,
        diagnostic_states=56, short_window_pairs=10, target_ticks=1560, source_slots=6240,
        reuse_arms=8, reuse_rows=116, existing_041_events=596, existing_041_deaths=22,
        projection_arms=48, projection_rows=664, gap_references=226, left_boundary_gaps=100,
        death_boundary_gaps=126, successor_birth_endpoints=190, empty_saved_states=411,
        gap_target_ticks=601, gap_source_slots=2404)
    require(counts == expected, 'complete frozen structural census')
    per_arm = {name: dict(gap_references=sum(g['arm'] == name for g in gaps),
        gap_target_ticks=sum(g['decision_target_ticks'] for g in gaps if g['arm'] == name)) for name in ARMS}
    require(per_arm == {'control': {'gap_references': 112, 'gap_target_ticks': 278},
                        'ablation': {'gap_references': 114, 'gap_target_ticks': 323}}, 'policy gap structure')
    return dict(phase='method', task='1', physical_steps=0, scientific_slot_classification=False,
        proposal_gates_recalculated=False, gap_intervals_recalculated=False, energy_ledgers_recalculated=False,
        index=index, index_reference=ref(index_path, '', index), incoming_geometry=geometry,
        counts=counts, gap_structure_by_arm=per_arm, arms=arms, reuse_041_rows=reused_rows, gaps=gaps)


def run():
    outputs = {name: OUT / f'{PREFIX}{name}.json' for name in ('sources', 'census', 'failure')}
    require(not any(path.exists() for path in outputs.values()), 'exclusive method outputs already exist')
    require(not Path('data/v4-study-046').exists(), 'formal Study046 output must not exist')
    start = monotonic()
    paths, before, read_errors, discovery_errors = [], {}, {}, {}
    progress = dict(completed_pairs=0, completed_arms=0, saved_states=0, gap_references=0, reused_rows=0)

    def budget(extra=0):
        used = sum(p.stat().st_size for p in outputs.values() if p.exists())
        require(monotonic() - start < TIME_LIMIT and used + extra < STORAGE_LIMIT, 'bounded method audit')

    try:
        paths = discover_paths(discovery_errors)
        before, read_errors = capture(paths)
        require(not discovery_errors and not read_errors, 'complete initial source capture')
        # These input helpers validate earlier immutable evidence; no science functions are imported.
        from scripts.middle_turnover_inputs import bindings as turnover_bindings
        from scripts.lineage_route_inputs import bindings as route_bindings
        prior045, prior041 = turnover_bindings(), route_bindings()
        require(len(prior045) == 916 and len(prior041) == 799, 'frozen prior input inventories')
        completed = {study: validate_completed(study, previous, before)
                     for study, previous in (('045', prior045), ('041', prior041))}
        engineering = validate_engineering(before, prior045)
        budget()
        result = census(before, budget, progress)
        after, after_errors = capture(paths)
        require(before == after and not after_errors, 'unchanged complete method sources')
        census_bytes = encode(result)
        sources = dict(status='complete', phase='method', task='1', physical_steps=0,
            scientific_slot_classification=False, time_limit_seconds=TIME_LIMIT, storage_limit_bytes=STORAGE_LIMIT,
            input_paths=paths, input_inventory_errors=discovery_errors,
            input_read_errors_before=read_errors, input_read_errors_after=after_errors,
            files_sha256=before, files_sha256_after=after, completed_sources=completed,
            engineering_045=engineering, source_files=len(before), outputs_exclusive=True,
            formal_output_created=False, census_sha256=hashlib.sha256(census_bytes).hexdigest(),
            elapsed_seconds=monotonic() - start)
        budget(len(census_bytes) + len(encode(sources)))
        exclusive_write(outputs['census'], result)
        exclusive_write(outputs['sources'], sources)
        budget()
        print(json.dumps(dict(status='complete', source_files=len(before), counts=result['counts'],
            elapsed_seconds=monotonic() - start, physical_steps=0, scientific_slot_classification=False)))
    except BaseException as error:
        after, after_errors = capture(paths)
        failure = dict(status='failed', phase='method', task='1', error=repr(error), physical_steps=0,
            scientific_slot_classification=False, time_limit_seconds=TIME_LIMIT, storage_limit_bytes=STORAGE_LIMIT,
            progress=progress, input_paths=paths, input_inventory_errors=discovery_errors,
            files_sha256=before, files_sha256_after=after, input_read_errors_before=read_errors,
            input_read_errors_after=after_errors, elapsed_seconds=monotonic() - start,
            partial_outputs_sha256={str(p): digest(p) for n, p in outputs.items() if n != 'failure' and p.exists()})
        exclusive_write(outputs['failure'], failure)
        raise


if __name__ == '__main__':
    run()
