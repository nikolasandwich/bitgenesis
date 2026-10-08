"""Study045 phase 1.1: immutable sources and identity census, no science audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.policy_component_timing_inputs import bindings, read, digest
from scripts.founder_removal_inputs import validate_manifest

OUT = Path('docs/research/results')
MIDDLE = (101, 102)


def canonical_hash(value: object) -> str:
    """Hash normalized record content; source file hash separately binds raw bytes."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def completed(study: str, expected: dict[str, str]) -> list[str]:
    base = f'data/v4-study-{study}'
    meta = read(f'{base}/metadata.json')
    proof = read(f'{base}/independent-verification.json')
    assert meta['status'] == 'complete' and proof['status'] == 'verified'
    assert meta['input_sha256'] == meta['input_sha256_after'] == expected
    assert proof['input_sha256'] == proof['input_sha256_after'] == expected
    validate_manifest({f'{base}/{name}': sha for name, sha in proof['files_sha256'].items()})
    review_path = f'docs/research/results/v4-study-{study}-review.json'
    review = read(review_path)
    assert review['verdict'] == 'APPROVED' and review['task'] == '2.1'
    validate_manifest(review['files_sha256'])
    preserve_path = f'docs/research/results/v4-study-{study}-preservation.json'
    preserve = read(preserve_path)
    assert preserve['byte_identical'] is True
    paths = [review_path, preserve_path]
    for name in ('metadata', 'records', 'summary', 'independent-verification') + (('index',) if study == '044' else ()):
        a = f'{base}/{name}.json'
        b = f'docs/research/results/v4-study-{study}-{name}.json'
        assert Path(a).read_bytes() == Path(b).read_bytes()
        paths += [a, b]
    return paths


def run() -> None:
    targets = [OUT / f'v4-study-045-design-{name}.json' for name in ('sources', 'census')]
    assert not any(path.exists() for path in targets), 'Immutable outputs already exist'
    prior = bindings()
    assert len(prior) == 892
    paths = completed('044', prior)
    from scripts.middle_energy_inputs import bindings as energy_bindings
    old_inputs = energy_bindings()
    assert len(old_inputs) == 820
    paths += completed('042', old_inputs)
    paths += ['experiments/v4/study-045.md', 'docs/design/v4-middle-turnover.zh-CN.md',
              'scripts/audit_v4_middle_turnover_design.py']
    manifest = dict(prior)
    for path, sha in old_inputs.items():
        assert path not in manifest or manifest[path] == sha
        manifest[path] = sha
    manifest.update({path: digest(path) for path in paths})
    validate_manifest(manifest)

    index = read('data/v4-study-044/index.json')
    assert len(index) == 100 and len({(r['encoding'], r['seed']) for r in index}) == 100
    assert sum(not r['trigger'] for r in index) == 72
    assert sum(r['short_window'] for r in index) == 10
    observed = [r for r in index if r['trigger']]
    assert len(observed) == 28
    assert all(r['branch'] is None and r['applicability'] == 'not_applicable'
               for r in index if not r['trigger'])
    records044 = {(c['encoding'], c['selection']['seed']): c
                  for c in read('data/v4-study-044/records.json')}
    old_records = read('data/v4-study-042/records.json')
    assert len(old_records) == 8
    old_map = {(c['encoding'], c['selection']['seed']): (i, c)
               for i, c in enumerate(old_records)}
    arms = []
    reuse = []
    for item in observed:
        key = (item['encoding'], item['seed'])
        branch_path = item['branch']
        assert branch_path in manifest
        branch = read(branch_path)
        assert branch['selection'] == records044[key]['selection']
        assert branch['selection']['t0'] == item['t0']
        t0 = item['t0']
        for arm_name in ('control', 'ablation'):
            arm = branch[arm_name]
            assert arm['initial']['tick'] == t0
            assert [r['tick'] for r in arm['rows']] == list(range(t0 + 1, 33))
            assert len(arm['rows']) == item['remaining']
            observed044 = records044[key]['arms'][arm_name]
            assert observed044['diagnostic']['tick'] == t0
            assert [r['tick'] for r in observed044['rows']] == list(range(t0 + 1, 33))
            people = arm['final']['individuals']
            initial_ids = {arm['initial']['site_ids'][s] for s in MIDDLE
                           if arm['initial']['site_ids'][s] is not None}
            visible: dict[int, dict[str, object]] = {}
            # Enumerate actual saved occupancy first; do not infer membership from lineage labels.
            states = [(t0, arm['initial']['site_ids'], arm['initial']['units'])]
            states += [(r['tick'], r['site_ids'], r['physical']['units']) for r in arm['rows']]
            for tick, ids, units in states:
                for site in MIDDLE:
                    identity = ids[site]
                    assert (identity is None) == (units[site] is None)
                    if identity is None:
                        continue
                    person = people[identity]
                    assert person['id'] == identity and person['site'] == site
                    assert person['birth_tick'] <= tick
                    assert units[site]['material'] == person['material']
                    assert person['death_tick'] is None or person['death_tick'] > tick
                    if identity not in visible:
                        visible[identity] = dict(identity=identity, site=site,
                            parent=person['parent'], birth_tick=person['birth_tick'],
                            entry_kind='initial_left_censored' if identity in initial_ids else 'future_birth',
                            left_censored=identity in initial_ids, first_visible_tick=tick,
                            initial_visible_material=units[site]['material'],
                            birth_material=person['material'],
                            history_pointer=f'/{arm_name}/final/individuals/{identity}')
            expected = {p['id'] for p in people if p['site'] in MIDDLE and
                        (p['id'] in initial_ids or t0 < p['birth_tick'] <= 32)}
            assert set(visible) == expected
            assert initial_ids <= expected
            assert all(v['first_visible_tick'] == (t0 if v['left_censored'] else v['birth_tick'])
                       for v in visible.values())
            # 044 is the already completed scientific source; only compare structural identities.
            for diagnostic, (_, ids, _) in zip([observed044['diagnostic']] + observed044['rows'], states):
                assert diagnostic['slots'][1]['sites'] == list(MIDDLE)
                assert diagnostic['slots'][1]['identities'] == [ids[s] for s in MIDDLE]
                for slot in (diagnostic['slots'][0], diagnostic['slots'][2]):
                    assert all(isinstance(slot[n], bool) for n in
                               ('occupied', 'material_match', 'genetic_match', 'whole_component',
                                'root_descendant', 'all_new', 'post_birth', 'selected_ancestry', 'new_copy'))
            mode = 'reuse_042' if arm_name == 'control' and key in old_map else 'needed_event_projection'
            if mode == 'reuse_042':
                case_index, old = old_map[key]
                old_path = f'data/v4-study-039/cases/{key[0]}-{key[1]}.json'
                assert old_path in manifest
                old_branch = read(old_path)
                assert old_branch['selection'] == branch['selection'] == old['selection']
                assert old_branch['ablation'] == arm
                assert {p['identity'] for p in old['identities']} == expected
                for identity_index, old_person in enumerate(old['identities']):
                    ident = old_person['identity']
                    person = people[ident]
                    assert all(old_person[n] == person[n] for n in ('site', 'parent', 'birth_tick', 'birth_energy'))
                    assert old_person['left_censored'] == visible[ident]['left_censored']
                    reuse.append(dict(encoding=key[0], seed=key[1], arm=arm_name, identity=ident,
                        source_path='data/v4-study-042/records.json',
                        source_file_sha256=manifest['data/v4-study-042/records.json'],
                        json_pointer=f'/{case_index}/identities/{identity_index}',
                        normalized_record_sha256=canonical_hash(old_person),
                        old_branch_source=old_path, paired_branch_source=branch_path,
                        complete_old_arm_equal=True, ledger_recalculated=False))
            arms.append(dict(encoding=key[0], seed=key[1], arm=arm_name, source=branch_path,
                source_sha256=manifest[branch_path], t0=t0, saved_states=len(arm['rows']),
                diagnostic_states=1, short_window=item['short_window'], energy_plan=mode,
                identities=[visible[k] for k in sorted(visible)]))
    assert len(arms) == 56 and sum(a['saved_states'] for a in arms) == 780
    assert len(reuse) == 35 and sum(a['energy_plan'] == 'reuse_042' for a in arms) == 8
    assert sum(a['energy_plan'] == 'needed_event_projection' for a in arms) == 48
    validate_manifest(manifest)
    after = {p: digest(p) for p in manifest}
    assert manifest == after
    census = dict(phase='1.1', physical_steps=0, scientific_turnover_audit=False,
        gap_analysis=False, new_energy_projection=False, index=index, arms=arms,
        identities=sum(len(a['identities']) for a in arms),
        left_censored_identities=sum(p['left_censored'] for a in arms for p in a['identities']),
        reuse_042= reuse, reuse_042_identity_count=len(reuse),
        counts=dict(index=100, not_applicable=72, pairs=28, arms=56,
                    saved_states=780, diagnostic_states=56, short_window_pairs=10,
                    reuse_arms=8, event_projection_arms=48))
    sources = dict(phase='1.1', physical_steps=0, prior_044_input_count=892,
        files_sha256=manifest, files_sha256_after=after,
        archive_bytes_checked=True, outputs_exclusive=True)
    for target, value in zip(targets, (sources, census)):
        with target.open('x') as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write('\n')
    print(json.dumps(dict(source_files=len(manifest), identities=census['identities'],
                          left_censored=census['left_censored_identities'], reuse=35,
                          arms=56, saved_states=780, physical_steps=0)))


if __name__ == '__main__':
    run()
