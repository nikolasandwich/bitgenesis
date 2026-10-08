"""Synthetic phase boundaries and bounded read-only Study046 execution."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import analyze_v4_middle_refill as audit
from scripts import middle_refill_inputs as inputs


def unit(energy=20, material=0):
    return dict(energy=energy, material=material, program=[0, 1, 2, 3])


class Fixture:
    """Saved observations, authored explicitly rather than using a physics step."""
    def __init__(self, directory, actors=None, raw=None, end=None, births=None, proposals=None):
        actors = actors or {}
        self.directory = Path(directory)
        ids, units, phase, directions = [None]*256, [None]*256, [None]*256, [0]*256
        people = []
        for site, (energy, direction) in sorted(actors.items()):
            identity = len(people)
            ids[site] = identity
            units[site] = unit(max(energy, 1))
            phase[site] = unit(energy)
            directions[site] = direction
            people.append(dict(id=identity, site=site, parent=None, birth_tick=0, material=0))
        before_raw = [0]*256
        for site, value in (raw or {}).items():
            before_raw[site] = value
        final_ids, final_units, final_raw = ids[:], deepcopy(phase), before_raw[:]
        dead = [s for s in actors if phase[s]['energy'] == 0]
        for site in dead:
            final_ids[site] = final_units[site] = None
            final_raw[site] += 1
        born = []
        for site, parent_site in births or []:
            identity = len(people)
            person = dict(id=identity, site=site, parent=ids[parent_site], birth_tick=32, material=0,
                          birth_energy=7)
            people.append(person)
            born.append(deepcopy(person))
            final_ids[site], final_units[site] = identity, unit(7)
            final_raw[site] -= 1
        for site, value in (end or {}).items():
            final_raw[site] = value
        initial = dict(tick=31, site_ids=ids, units=units, raw=before_raw)
        physical = dict(tick=32, interaction_units=phase, units=final_units, raw=final_raw,
                        directions=directions, material=dict(dissolved=sorted(dead), proposals=proposals or []))
        row = dict(tick=32, site_ids=final_ids, physical=physical, births=born,
                   deaths=[ids[s] for s in dead])
        arm = dict(initial=initial, rows=[row], final=dict(individuals=people))
        self.branch = dict(selection=dict(seed=120005, t0=31, remaining_steps=1,
            category='short_window', offspring_ids=[], offspring_sites=[]), control=arm, ablation=deepcopy(arm))
        self.gaps = []
        self.reuse = []
        self.plans = []
        self.refresh()

    def write(self, name, value):
        path = self.directory/name
        path.write_text(json.dumps(value))
        return str(path)

    def ref(self, path, pointer):
        return inputs.make_ref(path, pointer)

    def refresh(self):
        branch_path = self.write('branch.json', self.branch)
        turnover = []
        for arm in audit.ARMS:
            row = self.branch[arm]['rows'][0]
            turnover.append(dict(diagnostic=dict(tick=31), rows=[dict(tick=32,
                middle=[dict(site=s, identity=row['site_ids'][s]) for s in (101, 102)],
                B101=False, B102=False, G=True, actual_double_new=False)]))
        old_path = self.write('turnover.json', turnover)
        self.plans = []
        for i, arm in enumerate(audit.ARMS):
            self.plans.append(dict(key=['east', 120005, arm], encoding='east', seed=120005,
                arm=arm, t0=31, saved_states=1, diagnostic_states=1, target_ticks=2, source_slots=8,
                short_window=True, category='short_window', source=self.ref(branch_path, '/'+arm),
                diagnostic=self.ref(branch_path, '/'+arm+'/initial'),
                turnover_diagnostic=self.ref(old_path, f'/{i}/diagnostic'),
                proposal_plan='needed_projection', reuse_041=None, gap_keys=[], gap_target_ticks=0,
                gap_source_slots=0, rows=[dict(tick=32, target_ticks=2, source_slots=8,
                    source=self.ref(branch_path, '/'+arm+'/rows/0'),
                    before=self.ref(branch_path, '/'+arm+'/initial'),
                    turnover=self.ref(old_path, f'/{i}/rows/0'), reuse_041=None)]))

    def add_gap(self, arm='control', site=101, predecessor=None, successor=None):
        original = dict(site=site, predecessor=predecessor, successor=successor,
            start_boundary=31 if predecessor is None else 32, end_boundary=32,
            distance_ticks=1 if predecessor is None else 0,
            empty_ticks=[32] if successor is None else [], empty_saved_states=int(successor is None),
            left_censored=predecessor is None, right_censored=successor is None,
            same_tick_replacement=predecessor is not None and successor is not None,
            material_changed=False if predecessor is not None and successor is not None else None)
        path = self.write(f'gap{len(self.gaps)}.json', original)
        key = ['east', 120005, arm, path]
        gap = dict(key=key, encoding='east', seed=120005, arm=arm, reference=self.ref(path, ''),
            original=original, decision_ticks=[32], decision_target_ticks=1,
            decision_source_slots=4, intervals_recalculated=False)
        self.gaps.append(gap)
        plan = next(p for p in self.plans if p['arm'] == arm)
        plan['gap_keys'].append(key)
        plan['gap_target_ticks'] += 1
        plan['gap_source_slots'] += 4
        return gap

    def project(self):
        return audit.project_pair('east', self.branch, self.plans, self.gaps, self.reuse)

    def reuse_control(self, event):
        existing = dict(encoding='east', selection=deepcopy(self.branch['selection']),
                        rows=[dict(tick=32, events=[event], deaths=[])])
        self.reuse = [existing]
        path = self.write('041.json', self.reuse)
        old_path = self.write('039.json', dict(selection=self.branch['selection'], ablation=self.branch['control']))
        plan = self.plans[0]
        plan['proposal_plan'] = 'reuse_041'
        plan['reuse_041'] = dict(reference=self.ref(path, '/0'), old_branch=self.ref(old_path, '/ablation'),
            complete_old_arm_equal=True, proposals_reclassified=False,
            historical_verifier_mode='parent inline fallback independent algorithm')
        plan['rows'][0]['reuse_041'] = self.ref(path, '/0/rows/0')


def q(source, target, direction, reason):
    return dict(source=source, target=target, direction=direction, reason=reason)


def slot(pair, source, target, arm='control'):
    return next(s for s in pair['arms'][arm]['rows'][0]['slots'] if s['source'] == source and s['target'] == target)


class RefillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def fixture(self, **kwargs):
        return Fixture(self.tmp.name, **kwargs)

    def test_all_slots_empty_tickets_are_not_proposals_and_diagnostic_is_separate(self):
        fixture = self.fixture()
        record = fixture.project()
        arm = record['arms']['control']
        self.assertEqual(len(arm['rows']), 1)
        self.assertEqual(len(arm['rows'][0]['slots']), 8)
        self.assertEqual(len(arm['rows'][0]['targets']), 2)
        self.assertNotIn('slots', arm['diagnostic'])
        s = slot(record, 100, 101)
        self.assertEqual((s['state'], s['ticket_target'], s['proposal_target']), ('empty_source', 101, None))
        self.assertIsNone(s['proposal'])
        self.assertEqual(s['source_region'], 'other')
        self.assertNotEqual(s['key'], slot(record, 100, 101, 'ablation')['key'])

    def test_empty_source_newborn_cannot_act_in_birth_tick(self):
        fixture = self.fixture(actors={100: (20, 0)}, raw={101: 1}, births=[(101, 100)],
                               proposals=[q(100, 101, 0, 'formed')])
        record = fixture.project()
        incoming, outgoing = slot(record, 100, 101), slot(record, 101, 102)
        self.assertEqual(incoming['proposal']['child_id'], 1)
        self.assertEqual(outgoing['end_identity'], 1)
        self.assertEqual(outgoing['state'], 'empty_source')
        self.assertIsNone(outgoing['proposal_target'])
        self.assertEqual(record['arms']['control']['rows'][0]['targets'][0]['birth']['parent'], 0)

    def test_dissolved_ticket_is_not_proposal_and_same_tick_replacement_uses_raw_release(self):
        fixture = self.fixture(actors={101: (0, 0), 117: (20, 3)}, births=[(101, 117)],
                               proposals=[q(117, 101, 3, 'formed')])
        fixture.add_gap(predecessor=0, successor=2)
        record = fixture.project()
        dead, made = slot(record, 101, 102), slot(record, 117, 101)
        self.assertEqual((dead['state'], dead['ticket_target'], dead['proposal_target']), ('dissolved', 102, None))
        self.assertEqual(dead['identity'], 0)
        self.assertEqual(dead['end_identity'], 2)
        self.assertEqual(made['proposal']['target_raw'], 1)
        self.assertTrue(made['proposal']['target_empty'])
        target = record['arms']['control']['rows'][0]['targets'][0]
        self.assertEqual(target['before'], dict(identity=0, material=0, raw=0))
        self.assertEqual(target['preformation'], dict(identity=None, material=None, raw=1))
        self.assertEqual(target['after'], dict(identity=2, material=0, raw=0))
        gap = record['arms']['control']['gaps'][0]
        self.assertEqual(gap['original']['empty_ticks'], [])
        self.assertEqual(len(gap['target_keys']), 1)
        self.assertEqual(gap['counts']['births'], 1)

    def test_surviving_other_direction_is_not_a_failed_or_counterfactual_proposal(self):
        fixture = self.fixture(actors={100: (5, 1)}, proposals=[q(100, 99, 1, 'energy')])
        s = slot(fixture.project(), 100, 101)
        self.assertEqual(s['state'], 'not_pointing')
        self.assertEqual(s['proposal_target'], 99)
        self.assertIsNone(s['proposal'])

    def test_independent_gates_and_collision_preserve_low_energy_first_reason(self):
        fixture = self.fixture(actors={100: (3, 0), 85: (20, 2), 117: (20, 3)}, raw={101: 1},
            proposals=[q(85, 101, 2, 'collision'), q(100, 101, 0, 'energy'), q(117, 101, 3, 'collision')])
        record = fixture.project()
        low = slot(record, 100, 101)['proposal']
        self.assertEqual((low['reason'], low['candidate_count'], low['candidate']), ('energy', 2, False))
        self.assertTrue(low['target_empty'] and low['raw_ok'])
        target = record['arms']['control']['rows'][0]['targets'][0]
        self.assertEqual(len(target['proposal_keys']), 3)
        self.assertEqual(len(target['candidate_keys']), 2)
        self.assertEqual(slot(record, 85, 101)['state'], 'collision')

    def test_occupied_precedes_raw_and_all_gates_remain_visible(self):
        fixture = self.fixture(actors={100: (20, 0), 101: (1, 1)},
            proposals=[q(100, 101, 0, 'occupied'), q(101, 100, 1, 'energy')])
        proposal = slot(fixture.project(), 100, 101)['proposal']
        self.assertEqual(proposal['reason'], 'occupied')
        self.assertFalse(proposal['target_empty'])
        self.assertFalse(proposal['raw_ok'])
        self.assertTrue(proposal['energy_ok'])

    def test_raw_failure_and_saved_reason_mismatch_rejected(self):
        fixture = self.fixture(actors={100: (20, 0)}, proposals=[q(100, 101, 0, 'raw_material')])
        self.assertEqual(slot(fixture.project(), 100, 101)['state'], 'raw_material')
        fixture.branch['control']['rows'][0]['physical']['material']['proposals'][0]['reason'] = 'formed'
        fixture.refresh()
        with self.assertRaisesRegex(ValueError, 'saved proposal reason'):
            fixture.project()

    def test_birth_parent_site_and_identity_must_match_saved_object(self):
        for field, bad in [('parent', 99), ('site', 102), ('id', 99)]:
            with self.subTest(field=field):
                fixture = self.fixture(actors={100: (20, 0)}, raw={101: 1}, births=[(101, 100)],
                                       proposals=[q(100, 101, 0, 'formed')])
                fixture.branch['control']['rows'][0]['births'][0][field] = bad
                fixture.refresh()
                with self.assertRaisesRegex(ValueError, 'birth'):
                    fixture.project()

    def test_dissolved_and_empty_sources_cannot_have_saved_proposals(self):
        for actors in ({}, {100: (0, 0)}):
            fixture = self.fixture(actors=actors, proposals=[q(100, 101, 0, 'energy')])
            with self.assertRaisesRegex(ValueError, 'nonacting source'):
                fixture.project()

    def test_gap_endpoint_censoring_and_outside_rows_retained(self):
        fixture = self.fixture()
        original = deepcopy(fixture.add_gap()['original'])
        record = fixture.project()
        arm = record['arms']['control']
        self.assertEqual(arm['gaps'][0]['original'], original)
        self.assertTrue(original['left_censored'] and original['right_censored'])
        self.assertEqual(len(arm['gaps'][0]['slot_keys']), 4)
        self.assertEqual(sum(s['gap_key'] is None for s in arm['rows'][0]['slots']), 4)
        self.assertEqual(len(arm['rows'][0]['targets']), 2)

    def test_successful_gap_endpoint_is_included_without_empty_saved_state(self):
        fixture = self.fixture(actors={100: (20, 0)}, raw={101: 1}, births=[(101, 100)],
                               proposals=[q(100, 101, 0, 'formed')])
        fixture.add_gap(successor=1)
        gap = fixture.project()['arms']['control']['gaps'][0]
        self.assertEqual(gap['decision_ticks'], [32])
        self.assertEqual(gap['original']['empty_saved_states'], 0)
        self.assertEqual(gap['sequence'][0]['birth_id'], 1)
        fixture.gaps[0]['decision_ticks'] = []
        with self.assertRaisesRegex(ValueError, 'gap decision'):
            fixture.project()

    def test_duplicate_target_gap_is_rejected(self):
        fixture = self.fixture()
        fixture.add_gap()
        fixture.add_gap()
        with self.assertRaisesRegex(ValueError, 'overlapping gap'):
            fixture.project()

    def test_reuse_exact_object_without_reclassifying_old_gates(self):
        fixture = self.fixture(actors={100: (3, 0)}, proposals=[q(100, 101, 0, 'energy')])
        event = dict(tick=32, source=100, target=101, direction=0, identity=0, program=[0, 1, 2, 3],
            energy=3, target_region='middle', target_raw=0, target_occupied=False, target_dissolved=False,
            energy_ok=False, target_empty=True, raw_ok=False, candidate=False, candidate_count=7,
            reason='energy', child_id=None, lineage='other', ancestor=None, chain=[0])
        fixture.reuse_control(event)
        with patch.object(audit, 'project_proposals', side_effect=AssertionError('must not classify reuse')):
            result = audit.project_arm('east', fixture.branch, fixture.plans[0], [], fixture.reuse)
        s = next(s for s in result['rows'][0]['slots'] if s['source'] == 100 and s['target'] == 101)
        self.assertEqual(s['proposal'], event)
        self.assertEqual(s['source_mode'], 'reuse_041')
        self.assertEqual(s['proposal_reference']['json_pointer'], '/0/rows/0/events/0')
        self.assertEqual(result['reuse_041']['historical_verifier_mode'], 'parent inline fallback independent algorithm')

    def test_reuse_wrong_arm_pointer_selection_and_hash_are_rejected(self):
        fixture = self.fixture(actors={100: (3, 0)}, proposals=[q(100, 101, 0, 'energy')])
        event = dict(tick=32, source=100, target=101, direction=0, identity=0, reason='energy',
            child_id=None, candidate=False, candidate_count=0)
        fixture.reuse_control(event)
        for field, bad in [('arm', 'ablation'), ('encoding', 'west')]:
            plan = deepcopy(fixture.plans[0]);plan[field] = bad
            with self.assertRaises(ValueError):
                audit.project_arm('east', fixture.branch, plan, [], fixture.reuse)
        plan = deepcopy(fixture.plans[0]);plan['rows'][0]['reuse_041']['json_pointer'] = '/0/rows/1'
        with self.assertRaises(ValueError):
            audit.project_arm('east', fixture.branch, plan, [], fixture.reuse)
        fixture.reuse[0]['selection']['seed'] = 9
        with self.assertRaises(ValueError):
            fixture.project()

    def test_all_20_cells_full_index_and_zero_denominators(self):
        index = [dict(encoding=e, seed=120000+i, trigger=False) for e in audit.ENCODINGS for i in range(20)]
        summary = audit.summarize([], index)
        self.assertEqual(summary['index'], index)
        self.assertEqual((summary['index_cases'], summary['no_trigger']), (100, 100))
        self.assertEqual(len(summary['cells']), 20)
        for cell in summary['cells']:
            self.assertEqual(cell['policy_denominator'], 20)
            self.assertEqual(cell['source_slots'], 0)
            self.assertEqual(set(cell['states']), set(audit.STATES))
            self.assertEqual(set(cell['cross_counts']), set(audit.REGIONS))
            self.assertTrue(all(value == 0 for value in cell['states'].values()))
        record = self.fixture().project()
        summary = audit.summarize([record], index)
        self.assertEqual(len(summary['paired']), 1)
        self.assertEqual(summary['paired'][0]['delta']['source_slots'], 0)

    def test_gap_wait_includes_empty_state_and_later_successful_endpoint(self):
        fixture = self.fixture(actors={100: (20, 0)}, raw={101: 1}, births=[(101, 100)],
                               proposals=[q(100, 101, 0, 'formed')])
        fixture.branch['selection'].update(t0=30, remaining_steps=2)
        for name in audit.ARMS:
            arm = fixture.branch[name]
            arm['initial']['tick'] = 30
            first = deepcopy(arm['rows'][0])
            first['tick'] = first['physical']['tick'] = 31
            first['births'] = []
            first['site_ids'] = arm['initial']['site_ids'][:]
            first['physical']['units'] = deepcopy(arm['initial']['units'])
            first['physical']['interaction_units'][100]['energy'] = 3
            first['physical']['units'][100]['energy'] = 3
            first['physical']['raw'] = arm['initial']['raw'][:]
            first['physical']['material']['proposals'][0]['reason'] = 'energy'
            arm['rows'].insert(0, first)
        branch_path = fixture.write('branch.json', fixture.branch)
        turnover = [dict(tick=t, middle=[dict(site=101, identity=None if t == 31 else 1),
            dict(site=102, identity=None)], B101=False, B102=False, G=True, actual_double_new=False) for t in (31, 32)]
        prior_path = fixture.write('two-turnover.json', dict(diagnostic=dict(tick=30), rows=turnover))
        for plan in fixture.plans:
            name = plan['arm']
            plan.update(t0=30, saved_states=2, target_ticks=4, source_slots=16,
                source=fixture.ref(branch_path, '/'+name), diagnostic=fixture.ref(branch_path, '/'+name+'/initial'),
                turnover_diagnostic=fixture.ref(prior_path, '/diagnostic'))
            plan['rows'] = [dict(tick=31+i, source_slots=8, target_ticks=2,
                source=fixture.ref(branch_path, f'/{name}/rows/{i}'),
                before=fixture.ref(branch_path, f'/{name}/initial' if i == 0 else f'/{name}/rows/0'),
                turnover=fixture.ref(prior_path, f'/rows/{i}'), reuse_041=None) for i in range(2)]
        gap = fixture.add_gap(successor=1)
        gap['original'].update(start_boundary=30, distance_ticks=2, empty_ticks=[31], empty_saved_states=1)
        fixture.write('gap0.json', gap['original'])
        gap.update(reference=fixture.ref(str(fixture.directory/'gap0.json'), ''), decision_ticks=[31, 32],
                   decision_target_ticks=2, decision_source_slots=8)
        fixture.plans[0].update(gap_target_ticks=2, gap_source_slots=8)
        result = fixture.project()['arms']['control']['gaps'][0]
        self.assertEqual(result['decision_ticks'], [31, 32])
        self.assertEqual(result['original']['empty_ticks'], [31])
        self.assertEqual([item['birth_id'] for item in result['sequence']], [None, 1])
        self.assertEqual(result['counts']['target_ticks'], 2)
        self.assertEqual(result['counts']['source_slots'], 8)
        self.assertEqual(result['counts']['real_proposals'], 2)

    def test_all_28_pairs_are_preserved_in_synthetic_summary(self):
        index = [dict(encoding=e, seed=120000+i, trigger=False) for e in audit.ENCODINGS for i in range(20)]
        template = self.fixture().project()
        records = []
        for item in [i for i in index if i['encoding'] != 'south'][:28]:
            item['trigger'] = True
            record = deepcopy(template)
            record['encoding'] = item['encoding']
            record['selection']['seed'] = item['seed']
            records.append(record)
        result = audit.summarize(records, index)
        self.assertEqual((result['index_cases'], result['triggered'], result['no_trigger']), (100, 28, 72))
        self.assertEqual(len(result['paired']), 28)
        self.assertTrue(all(cell['source_slots'] == 0 for cell in result['cells'] if cell['encoding'] == 'south'))

    def test_method_source_hash_mismatch_is_rejected(self):
        original = inputs.read(inputs.BASE)
        changed = deepcopy(original)
        changed['files_sha256']['experiments/v4/study-046.md'] = 'tampered'
        changed['files_sha256_after'] = deepcopy(changed['files_sha256'])
        real_read = inputs.read
        def reading(path):
            return changed if str(path) == inputs.BASE else real_read(path)
        with patch.object(inputs, 'read', side_effect=reading):
            with self.assertRaisesRegex(ValueError, 'frozen method source hashes'):
                inputs.bindings(include_verifier=False)

    def test_later_failure_preserves_completed_pair_checkpoint(self):
        output = Path(self.tmp.name)/'partial'
        record = self.fixture().project()
        index = [dict(encoding=e, seed=120000+i, trigger=False, short_window=False,
                      branch=None, applicability='not_applicable') for e in audit.ENCODINGS for i in range(20)]
        for pos, item in enumerate(index[:28]):
            item.update(trigger=True, short_window=pos < 10, branch='branch', source='original')
        branch = dict(selection=dict(seed=120000, source='original'))
        census = dict(index=index, arms=[], gaps=[])
        def reading(path):
            if path == inputs.CENSUS:
                return census
            if path == 'branch':
                branch['selection']['seed'] += 1
                return deepcopy(branch)
            return []
        branch['selection']['seed'] = 119999
        with patch.object(audit.subprocess, 'check_output', side_effect=['', 'commit']), \
             patch.object(inputs, 'input_paths', return_value=[]), \
             patch.object(inputs, 'capture', return_value=({}, {})), \
             patch.object(inputs, 'bindings', return_value={}), \
             patch.object(inputs, 'read', side_effect=reading), \
             patch.object(audit, 'project_pair', side_effect=[record, ValueError('second pair failed')]):
            with self.assertRaisesRegex(ValueError, 'second pair failed'):
                audit.run(output=output)
        meta = inputs.read(output/'metadata.json')
        self.assertEqual((meta['completed_cases'], meta['completed_arms'], meta['saved_steps']), (1, 2, 2))
        self.assertTrue((output/'pair-01.json').exists())
        self.assertIn('pair-01.json', meta['output_sha256'])
        self.assertFalse((output/'records.json').exists())
        self.assertEqual(meta['input_sha256'], meta['input_sha256_after'])

    def test_source_references_reject_tampered_bytes_pointer_and_value(self):
        path = Path(self.tmp.name)/'input.json'
        path.write_text('{"a":[1]}')
        ref = inputs.make_ref(str(path), '/a/0')
        self.assertEqual(inputs.SourceReader().resolve(ref), 1)
        for key, bad in [('json_pointer', '/a/2'), ('normalized_sha256', 'bad')]:
            changed = dict(ref, **{key: bad})
            with self.assertRaises(ValueError):inputs.SourceReader().resolve(changed)
        path.write_text('{"a":[2]}')
        with self.assertRaisesRegex(ValueError, 'file hash'):inputs.SourceReader().resolve(ref)

    def test_failure_retains_before_after_hashes_partial_progress_and_exclusive_output(self):
        output = Path(self.tmp.name)/'failed'
        with patch.object(audit.subprocess, 'check_output', side_effect=['', 'commit']), \
             patch.object(inputs, 'input_paths', return_value=['missing']), \
             patch.object(inputs, 'capture', side_effect=[({'source':'before'}, {}), ({'source':'after'}, {'missing':'gone'})]), \
             patch.object(inputs, 'bindings', side_effect=ValueError('source binding')):
            with self.assertRaisesRegex(ValueError, 'source binding'):audit.run(output=output)
        meta = inputs.read(output/'metadata.json')
        self.assertEqual(meta['status'], 'failed')
        self.assertEqual(meta['input_sha256'], {'source':'before'})
        self.assertEqual(meta['input_sha256_after'], {'source':'after'})
        self.assertEqual(meta['input_read_errors_after'], {'missing':'gone'})
        self.assertEqual(meta['completed_arms'], 0)
        self.assertEqual(meta['new_simulation_steps'], 0)
        saved = (output/'metadata.json').read_bytes()
        with patch.object(audit.subprocess, 'check_output', return_value=''):
            with self.assertRaises(FileExistsError):audit.run(output=output)
        self.assertEqual(saved, (output/'metadata.json').read_bytes())

    def test_clean_launch_and_engineering_cannot_use_formal_directory(self):
        output = Path(self.tmp.name)/'clean'
        with patch.object(audit.subprocess, 'check_output', return_value='dirty'):
            with self.assertRaisesRegex(ValueError, 'clean launch'):audit.run(output=output)
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, 'engineering.*formal'):
            audit.run(output=audit.OUTPUT, engineering=True)

    def test_time_and_storage_budget_failures_are_saved(self):
        for limits in ({'time_limit':-1}, {'storage_limit':1}):
            output = Path(self.tmp.name)/str(len(list(Path(self.tmp.name).iterdir())))
            with patch.object(audit.subprocess, 'check_output', side_effect=['', 'commit']), \
                 patch.object(inputs, 'input_paths', return_value=[]), \
                 patch.object(inputs, 'capture', return_value=({}, {})), \
                 patch.object(inputs, 'bindings', return_value={}):
                with self.assertRaisesRegex(ValueError, 'bounded execution'):
                    audit.run(output=output, **limits)
            meta = inputs.read(output/'metadata.json')
            self.assertEqual(meta['status'], 'failed')
            self.assertEqual(meta['input_sha256_after'], {})

    def test_formal_entry_cannot_omit_verifier(self):
        with self.assertRaisesRegex(ValueError, 'formal.*verifier'):
            audit.run(output=Path(self.tmp.name)/'bad', include_verifier=False)

    def test_engineering_default_still_binds_verifier(self):
        output = Path(self.tmp.name)/'engineering'
        with patch.object(audit.subprocess, 'check_output', return_value='commit'), \
             patch.object(inputs, 'input_paths', return_value=[]) as inventory, \
             patch.object(inputs, 'capture', return_value=({}, {})), \
             patch.object(inputs, 'bindings', side_effect=ValueError('stop input')) as binding:
            with self.assertRaisesRegex(ValueError, 'stop input'):
                audit.run(output=output, engineering=True)
        self.assertTrue(inventory.call_args.kwargs['include_verifier'])
        self.assertTrue(binding.call_args.kwargs['include_verifier'])

    def test_engineering_inventory_omits_only_missing_verifier(self):
        self.assertIn('scripts/verify_v4_middle_refill.py', inputs.input_paths())
        self.assertNotIn('scripts/verify_v4_middle_refill.py', inputs.input_paths(include_verifier=False))


if __name__ == '__main__':
    unittest.main()
