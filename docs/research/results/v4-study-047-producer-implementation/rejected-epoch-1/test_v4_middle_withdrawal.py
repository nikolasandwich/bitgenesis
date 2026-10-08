"""Synthetic Study047 producer boundaries; no research future tape or physics."""
from copy import deepcopy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from scripts import middle_withdrawal_inputs as inputs
from scripts import run_v4_middle_withdrawal as producer
from bitgenesis.v4.lineage import Observer


_SYNTHETIC_FIXTURE_STEPS = 0
_KERNEL = None


def setUpModule():
    global _KERNEL, _SYNTHETIC_FIXTURE_STEPS
    _KERNEL = producer.step
    _SYNTHETIC_FIXTURE_STEPS = 0
    def counted(*args, **kwargs):
        global _SYNTHETIC_FIXTURE_STEPS
        value = _KERNEL(*args, **kwargs)
        _SYNTHETIC_FIXTURE_STEPS += 1
        return value
    producer.step = counted


def tearDownModule():
    producer.step = _KERNEL
    print(json.dumps(dict(study047_task='2.1', synthetic_fixture_steps=_SYNTHETIC_FIXTURE_STEPS,
                          real_study047_future_physical_steps=0, real_study047_future_generator_ticks=0,
                          synthetic_rng_seed=987654, full_case_expected_steps=64)))


def fixture():
    units = [None] * 256
    for site, material in ((85, 0), (86, 0), (204, 3)):
        units[site] = dict(material=material, energy=32, program=[material] * 4)
    observer = Observer(units)
    template = dict(tick=0, units=deepcopy(units), site_ids=list(observer.alive))
    for identity in (0, 1):
        units[85 + identity] = None
        observer.alive[85 + identity] = None
    for site, parent in ((117, 0), (118, 1)):
        units[site] = dict(material=0, energy=32, program=[0] * 4)
        observer._birth(site, 20, 0, [0] * 4, 32, parent, False)
    raw = [0] * 256
    for site in (85, 86, 101, 102):
        raw[site] = 1
    state = dict(tick=32, units=units, raw=raw, site_ids=list(observer.alive),
                 parents=[p['parent'] for p in observer.individuals], individuals=deepcopy(observer.individuals))
    item = dict(encoding='homogeneous', seed=987654, trigger=True, t0=10, short_window=False,
                selection=dict(offspring_ids=[3, 4], exchange=False), boundary={'synthetic': True})
    return dict(item=item, initial=state, template=template,
                prefix_initial=dict(tick=10, removals=[dict(identity=0, site=85, energy=32),
                                                     dict(identity=1, site=86, energy=32)], energy_export=64),
                prefix_rows=[dict(tick=t, copies=[]) for t in range(11, 33)])


def tape():
    return tuple(dict(tick=t, directions=tuple([0] * 256), feed_sites_draw_order=(1, 2, 3, 4))
                 for t in range(33, 65))


def environment_fixture(seed=987654):
    streams = {kind: inputs.new_stream(seed, kind) for kind in ('directions', 'feeds')}
    originals = {mode: dict(seed=seed, mode=mode, exchange=False, config=dict(inputs.CONFIG), rows=[])
                 for mode in ('random-direction', 'random-both')}
    past = []
    for tick in range(1, 33):
        directions = [streams['directions'].randrange(4) for _ in range(256)]
        feeds = streams['feeds'].sample(range(256), 4)
        past.append(dict(tick=tick, directions=directions, feed_sites_draw_order=feeds))
        for mode, case in originals.items():
            proposed = inputs.fixed_proposals() if mode == 'random-direction' else [8 if s in feeds else 0 for s in range(256)]
            case['rows'].append(dict(physical=dict(tick=tick, directions=directions[:],
                mutation_tickets=inputs.fixed_tickets(), driven=dict(inputs=[dict(site=s, proposed=v) for s, v in enumerate(proposed)]))))
    states = {kind: json.loads(json.dumps(r.getstate())) for kind, r in streams.items()}
    env = dict(seed=seed, states_after_tick32=states, state_sha256={k: inputs.object_hash(v) for k, v in states.items()},
               tape_sha256=inputs.object_hash(past), past_feed_sites_draw_order=[p['feed_sites_draw_order'] for p in past], past_ticks=32)
    return env, originals


class SourceTests(unittest.TestCase):
    def test_concrete_types_recursive(self):
        for a, b in ((0, False), (8, 8.0), ([1], (1,)), ({'x': [False]}, {'x': [0]})):
            with self.assertRaises(ValueError): inputs.same(a, b, 'strict')
        inputs.same({'x': [True, None, 8]}, {'x': [True, None, 8]}, 'strict')

    def test_restore_uses_full_history_and_alive_not_death_field(self):
        f = fixture(); state = deepcopy(f['initial'])
        a = producer.restore_observer(state); b = producer.restore_observer(state)
        self.assertEqual((a.tick, a.founders, len(a.individuals)), (32, 3, 5))
        self.assertNotIn(0, a.alive); self.assertIsNone(a.individuals[0]['death_tick'])
        a._birth(100, 33, 0, [0] * 4, 10, 3, False)
        self.assertEqual(a.alive[100], 5); self.assertEqual(len(b.individuals), 5)
        self.assertEqual(state, f['initial'])

    def test_boundary_rejects_bad_identity_parent_program_mass_and_types(self):
        for mutate in (lambda s: s['site_ids'].__setitem__(117, 0),
                       lambda s: s['parents'].__setitem__(3, 3),
                       lambda s: s['units'][117]['program'].__setitem__(0, 1),
                       lambda s: s['raw'].__setitem__(0, 1),
                       lambda s: s.__setitem__('tick', 32.0),
                       lambda s: s['raw'].__setitem__(85, True)):
            s = fixture()['initial']; mutate(s)
            with self.assertRaises(ValueError): inputs.validate_state(s)

    def test_past_reconstruction_state_roundtrip_and_common_future(self):
        env, originals = environment_fixture()
        streams = producer.restore_environment(env, originals, inputs.runtime())
        for k, r in streams.items():
            self.assertEqual(json.loads(json.dumps(r.getstate())), env['states_after_tick32'][k])
        future = producer.future_tape(streams)
        self.assertEqual([t['tick'] for t in future], list(range(33, 65)))
        self.assertIsInstance(future, tuple)
        self.assertIsInstance(future[0]['directions'], tuple)
        self.assertEqual(len(future[0]['directions']), 256)
        again = producer.future_tape(producer.restore_environment(env, originals, inputs.runtime()))
        self.assertEqual(future, again)

    def test_past_state_runtime_and_seed_drift_rejected_before_future(self):
        env, originals = environment_fixture()
        for kind in ('past', 'state', 'runtime', 'seed', 'feed', 'mutation'):
            e, o, rt = deepcopy(env), deepcopy(originals), inputs.runtime()
            if kind == 'past': o['random-direction']['rows'][0]['physical']['directions'][0] ^= 1
            if kind == 'state': e['states_after_tick32']['directions'][1][0] ^= 1
            if kind == 'runtime': rt['python_version'] = 'different'
            if kind == 'seed': e['seed'] += 1
            if kind == 'feed': o['random-direction']['rows'][0]['physical']['driven']['inputs'][85]['proposed'] = 8.0
            if kind == 'mutation': o['random-both']['rows'][0]['physical']['mutation_tickets'][0][0] = 998
            with self.subTest(kind=kind), self.assertRaises(ValueError): producer.restore_environment(e, o, rt)

    def test_mask_only_two_sites_including_empty_without_mutating_common_tape(self):
        original = tuple(i % 4 for i in range(256))
        a = producer.arm_directions(original, 'continue_north')
        b = producer.arm_directions(original, 'withdraw_to_natural')
        self.assertEqual(b, list(original)); self.assertEqual(a[101:103], [3, 3])
        self.assertEqual([i for i in range(256) if a[i] != b[i]], [101, 102])
        self.assertEqual(original[101:103], (1, 2))
        with self.assertRaises(ValueError): producer.arm_directions([False] * 256, 'continue_north')


class ScienceTests(unittest.TestCase):
    def test_two_arms_full_rows_accounting_and_no_second_removal(self):
        f = fixture(); saved = deepcopy(f); progress = {'physical_steps': 0}
        case = producer.run_pair(f, tape(), progress=progress)
        self.assertEqual(f, saved); self.assertEqual(progress['physical_steps'], 64)
        for name in inputs.ARMS:
            arm = case[name]; self.assertEqual(arm['initial'], f['initial'])
            self.assertEqual(len(arm['rows']), 32); self.assertEqual(arm['final']['tick'], 64)
            self.assertEqual(arm['ledger']['energy_export'], 0)
            self.assertEqual(arm['ledger']['initial_energy'] + arm['metrics']['imported'] - arm['metrics']['spent'], arm['metrics']['final_energy'])
            self.assertEqual(arm['ledger']['initial_living'] + arm['metrics']['births'] - arm['metrics']['deaths'], arm['metrics']['living'])
            self.assertTrue(all(r['physical']['material_before'] == r['physical']['material_after'] == 7 for r in arm['rows']))
            self.assertEqual(arm['final']['individuals'][0]['death_tick'], None)
            self.assertIn('proposal_gates', arm['rows'][0]); self.assertIn('components', arm['rows'][0])
            self.assertEqual(set(arm['rows'][0]['failure_counts']), set(producer.REASONS))
        self.assertEqual(case['delta'], {k: case['withdraw_to_natural']['metrics'][k] - case['continue_north']['metrics'][k] for k in producer.METRICS})
        case['continue_north']['initial']['raw'][0] = 9
        self.assertEqual(case['withdraw_to_natural']['initial']['raw'][0], 0)

    def test_component_full_program_whole_shape_ancestry_and_original_exclusion(self):
        f = fixture(); s = f['initial']
        diagnostic = producer.observe_components(f['template'], s['units'], s['site_ids'], s['individuals'], 10)
        self.assertEqual(diagnostic['new_copy_count'], 1)
        member = diagnostic['copies'][0]['member_witnesses'][0]
        self.assertTrue(member['born_after_original_t0']); self.assertFalse(member['born_after_tick32'])
        bad = deepcopy(s); bad['units'][117]['program'][0] = 1
        self.assertEqual(producer.observe_components(f['template'], bad['units'], bad['site_ids'], bad['individuals'], 10)['new_copy_count'], 0)
        bad = deepcopy(s); bad['units'][116] = deepcopy(bad['units'][117]); bad['site_ids'][116] = 5
        bad['individuals'].append(dict(bad['individuals'][3], id=5, site=116))
        self.assertEqual(producer.observe_components(f['template'], bad['units'], bad['site_ids'], bad['individuals'], 10)['new_copy_count'], 0)
        bad = deepcopy(s); bad['individuals'][3]['founder'] = 2
        self.assertEqual(producer.observe_components(f['template'], bad['units'], bad['site_ids'], bad['individuals'], 10)['new_copy_count'], 0)
        bad = deepcopy(s); bad['individuals'][4]['founder'] = 0
        self.assertEqual(producer.observe_components(f['template'], bad['units'], bad['site_ids'], bad['individuals'], 10)['new_copy_count'], 1)

    def test_future_intervals_cross_boundary_nine_plus_one_not_ten(self):
        future = [2] + [0] * 31
        r = producer.interval_metrics(future, 2, [dict(tick=t, copies=[{'all_new': True}] * 2) for t in range(24, 33)], 23)
        self.assertFalse(r['future_persistent10']); self.assertEqual(r['longest_double'], 1)
        self.assertEqual(r['intervals'], [dict(start=33, end=33, length=1, left_censored_at_boundary=True, right_censored=False)])
        cross = r['cross_boundary']; self.assertEqual((cross['prefix_length'], cross['future_length'], cross['combined_observed_length']), (9, 1, 10))
        self.assertTrue(cross['combined_persistent10']); self.assertTrue(cross['prefix_left_censored_at_original_intervention'])
        self.assertIsNone(producer.interval_metrics(future, 0, [], 10)['cross_boundary'])
        r = producer.interval_metrics([0] * 22 + [2] * 10, 2, [], 10)
        self.assertTrue(r['future_persistent10']); self.assertTrue(r['intervals'][0]['right_censored'])
        self.assertFalse(r['intervals'][0]['left_censored_at_boundary'])
        self.assertIsNone(r['cross_boundary'])

    def test_original_birth_support_survives_tick32_threshold(self):
        f = fixture(); state = f['initial']
        copies = producer.observe_components(f['template'], state['units'], state['site_ids'], state['individuals'], 10)['copies']
        copies = [deepcopy(copies[0]), deepcopy(copies[0])]
        support = producer.birth_support([dict(tick=t, copies=deepcopy(copies)) for t in range(33, 65)], state['individuals'], 10, [3, 4])
        self.assertEqual(support['metrics']['formation_supported'], 1)
        self.assertEqual(support['metrics']['formation_persistent10'], 1)
        self.assertEqual(support['metrics']['after32_formation_supported'], 0)
        self.assertEqual(support['after32_formation_witnesses'], [])

    def test_completed_step_and_partial_rows_retained_when_observation_fails(self):
        f = fixture(); partial = {}; progress = {'physical_steps': 0}; sentinel = KeyboardInterrupt('observe')
        real = producer.observe_components; calls = 0
        def fail(*a, **k):
            nonlocal calls
            calls += 1
            if calls == 3: raise sentinel
            return real(*a, **k)
        with patch.object(producer, 'observe_components', side_effect=fail):
            with self.assertRaises(KeyboardInterrupt) as caught:
                producer.run_arm(f, tape(), 'continue_north', progress=progress, partial=partial)
        self.assertIs(caught.exception, sentinel)
        self.assertEqual(progress['physical_steps'], 2)
        self.assertEqual(len(partial['rows']), 2)
        self.assertIn('physical', partial['rows'][-1]); self.assertNotEqual(partial['status'], 'complete')


class EvidenceTests(unittest.TestCase):
    def test_exclusive_epoch_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'run'; p.mkdir(); (p / 'marker').write_text('foreign')
            with self.assertRaises(FileExistsError): producer.Epoch(p)
            self.assertEqual((p / 'marker').read_text(), 'foreign')

    def test_work_or_closing_interrupt_preserves_first_object_and_hashes(self):
        for failure in (KeyboardInterrupt('first'), SystemExit(9), ValueError('first')):
            with self.subTest(kind=type(failure)), tempfile.TemporaryDirectory() as d:
                e = producer.Epoch(Path(d) / 'run'); source = Path(d) / 'input'; source.write_text('source')
                def work():
                    e.capture([str(source)]); e.write('partial.json', {'rows': [1]}); e.meta['physical_steps'] = 1
                    raise failure
                with self.assertRaises(type(failure)) as caught: e.execute(work)
                self.assertIs(caught.exception, failure)
                meta = inputs.read(e.root / 'metadata.json')
                self.assertEqual(meta['status'], 'failed'); self.assertEqual(meta['physical_steps'], 1)
                self.assertEqual(meta['input_sha256'], meta['input_sha256_after'])
                self.assertIn('partial.json', meta['output_sha256'])

    def test_source_capture_error_persists_successes_and_first_exception(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); source = Path(d) / 'a'; source.write_text('a')
            missing = Path(d) / 'z'
            with self.assertRaises(FileNotFoundError): e.execute(lambda: e.capture([str(source), str(missing)]))
            meta = inputs.read(e.root / 'metadata.json')
            self.assertIn(str(source), meta['input_sha256']); self.assertIn(str(missing), meta['input_read_errors_before'])
            self.assertEqual(meta['status'], 'failed')

    def test_source_drift_and_late_failure_cannot_be_complete(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); source = Path(d) / 'a'; source.write_text('a')
            def work(): e.capture([str(source)]); source.write_text('b')
            with self.assertRaises(ValueError): e.execute(work)
            self.assertEqual(inputs.read(e.root / 'metadata.json')['status'], 'failed')
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); fail = SystemExit('closing')
            with self.assertRaises(SystemExit) as caught: e.execute(lambda: None, closing=lambda: (_ for _ in ()).throw(fail))
            self.assertIs(caught.exception, fail)
            self.assertEqual(inputs.read(e.root / 'metadata.json')['status'], 'failed')

    def test_budget_rejects_before_oversize_write(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run', storage=12000)
            with self.assertRaises(ValueError): e.execute(lambda: e.write('huge.json', {'blob': 'x' * 20000}))
            self.assertFalse((e.root / 'huge.json').exists())
            self.assertEqual(inputs.read(e.root / 'metadata.json')['status'], 'failed')
            self.assertLess(sum(p.stat().st_size for p in e.root.rglob('*') if p.is_file()), 12000)


def cohort_fixture():
    # Same frozen dimensions, synthetic metric values only; no source reads.
    selected_seeds = {'east': (120005, 120001, 120003, 120004, 120006),
                      'west': (120007, 120009, 120010), 'south': (),
                      'north': (120001, 120003, 120004, 120005, 120006, 120011, 120013, 120015, 120017),
                      'homogeneous': (120001, 120003, 120004, 120005, 120006, 120007, 120009, 120010, 120011, 120018, 120019)}
    cases = []; records = []; short = 0
    for enc in inputs.ENCODINGS:
        for seed in inputs.SEEDS:
            trigger = seed in selected_seeds[enc]
            short_window = trigger and short < 10
            if short_window: short += 1
            cases.append(dict(encoding=enc, seed=seed, source='synthetic', trigger=trigger, t0=23 if trigger else None,
                              remaining=9 if trigger else 0, short_window=short_window, applicability={}, selection={}))
            if trigger:
                a = dict.fromkeys(producer.METRICS, 0); b = dict(a)
                b['persistent10'] = b['future_persistent10'] = 1 if enc == 'east' else 0
                records.append(dict(encoding=enc, seed=seed, case=f'cases/{enc}-{seed}.json',
                                    continue_north_metrics=a, withdraw_to_natural_metrics=b,
                                    delta={k: b[k] - a[k] for k in a}, intervals={}, cross_boundary={}))
    return dict(cases=cases), records


class ContractAndSummaryTests(unittest.TestCase):
    def test_complete_grid_all_pairs_seed_correlation_and_na(self):
        census, records = cohort_fixture()
        index = producer.make_index(census, records, 'formal')
        summary = producer.summarize(records, index, 'formal')
        self.assertEqual(len(index), 100)
        self.assertEqual(sum(r['future'] is None for r in index), 72)
        self.assertEqual([c['n'] for c in summary['cells']], [5, 3, 0, 9, 11])
        self.assertIsNone(summary['cells'][2]['mean_delta']['persistent10'])
        self.assertEqual(summary['cells'][2]['delta_totals']['persistent10'], 0)
        self.assertEqual(len(summary['seed_groups']), 14)
        self.assertEqual(len(summary['pairs']), 28)
        self.assertEqual(summary['overall']['binary_pairs']['persistent10'], [
            dict(continue_north=0, withdraw_to_natural=0, n=23), dict(continue_north=0, withdraw_to_natural=1, n=5),
            dict(continue_north=1, withdraw_to_natural=0, n=0), dict(continue_north=1, withdraw_to_natural=1, n=0)])
        self.assertNotIn('rows', json.dumps(summary))
        with self.assertRaises(ValueError): producer.make_index(census, records[:-1], 'formal')
        with self.assertRaises(ValueError): producer.make_index(census, records + [records[0]], 'formal')

    def test_engineering_unrun_is_not_original_na_and_cannot_choose_other_seed(self):
        census, records = cohort_fixture()
        first = [r for r in records if (r['encoding'], r['seed']) == ('east', 120005)]
        index = producer.make_index(census, first, 'engineering')
        self.assertEqual(sum(r['future_status'] == 'not_run_engineering' for r in index), 27)
        self.assertEqual(sum(r['future_status'] == 'not_applicable_original_32_no_trigger' for r in index), 72)
        with self.assertRaises(ValueError): producer.make_index(census, records[:1], 'engineering')
        with self.assertRaises(ValueError): producer.make_index(census, records, 'other')
        with self.assertRaises(ValueError): producer.run('other', Path('unused'))

    def test_original_members_match_but_not_all_new(self):
        f = fixture(); t = f['template']; o = Observer(t['units'])
        r = producer.observe_components(t, t['units'], t['site_ids'], o.individuals, 10)
        self.assertEqual(len(r['copies']), 1); self.assertFalse(r['copies'][0]['all_new'])
        self.assertEqual(r['new_copy_count'], 0)

    def test_refs_reject_path_byte_object_and_pointer_drift(self):
        with tempfile.TemporaryDirectory() as d, patch.object(inputs, 'ROOT', Path(d)):
            p = Path(d) / 'saved.json'; p.write_text('{"ablation":{"final":{"tick":32}}}')
            value = {'tick': 32}; ref = dict(path='saved.json', sha256=inputs.digest(p), pointer='/ablation/final', value_sha256=inputs.object_hash(value))
            self.assertEqual(inputs.resolve_ref(ref), value)
            for key, changed in (('path', '../saved.json'), ('sha256', '0' * 64), ('value_sha256', '0' * 64)):
                bad = dict(ref); bad[key] = changed
                with self.assertRaises(ValueError): inputs.resolve_ref(bad)
            bad = dict(ref, pointer='/ablation')
            with self.assertRaises(ValueError): inputs.resolve_ref(bad)

    def test_review_must_bind_current_code_and_be_independent(self):
        with tempfile.TemporaryDirectory() as d, patch.object(inputs, 'ROOT', Path(d)):
            p = Path(d); (p / 'code.py').write_text('code')
            hashes = {'code.py': inputs.digest(p / 'code.py')}
            gate = dict(verdict='APPROVED', task='2.1', independent_author_review=True, files_sha256=hashes, files_sha256_after=hashes)
            (p / 'review.json').write_text(json.dumps(gate))
            inputs.approved_gate('review.json', '2.1', ['code.py'])
            with self.assertRaises(ValueError): inputs.approved_gate('review.json', '2.2', ['code.py'])
            with self.assertRaises(ValueError): inputs.approved_gate('review.json', '2.1', ['other.py'])
            (p / 'code.py').write_text('drift')
            with self.assertRaises(ValueError): inputs.approved_gate('review.json', '2.1', ['code.py'])


class ClosingFaultTests(unittest.TestCase):
    def test_output_hash_failure_retains_first_and_attempts_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); first = KeyboardInterrupt('hash'); real = inputs.capture
            def capture(paths):
                if any(str(p).endswith('partial.json') for p in paths): return {}, {'partial.json': repr(first)}, first
                return real(paths)
            with patch.object(inputs, 'capture', side_effect=capture):
                with self.assertRaises(KeyboardInterrupt) as caught:
                    e.execute(lambda: e.write('partial.json', {'actual': 1}))
            self.assertIs(caught.exception, first)
            meta = inputs.read(e.root / 'metadata.json')
            self.assertEqual(meta['status'], 'failed'); self.assertIn('partial.json', meta['output_read_errors'])

    def test_final_metadata_write_failure_repaired_and_propagated(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); first = SystemExit('write'); real = e.persist; count = 0
            def persist():
                nonlocal count
                count += 1
                if count == 1: raise first
                return real()
            with patch.object(e, 'persist', side_effect=persist):
                with self.assertRaises(SystemExit) as caught: e.execute(lambda: None)
            self.assertIs(caught.exception, first)
            self.assertEqual(inputs.read(e.root / 'metadata.json')['status'], 'failed')
            self.assertEqual(inputs.read(e.root / 'failure.json')['error'], repr(first))

    def test_first_exception_wins_over_closing_write_and_hash_faults(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); first = ValueError('work'); late = KeyboardInterrupt('later')
            with patch.object(e, 'output_hashes', side_effect=late):
                with self.assertRaises(ValueError) as caught: e.execute(lambda: (_ for _ in ()).throw(first))
            self.assertIs(caught.exception, first)
            meta = inputs.read(e.root / 'metadata.json'); self.assertEqual(meta['error'], repr(first))
            self.assertIn('output_hashes', meta['finalization_errors'])

    def test_epoch_partial_arm_survives_and_success_complete_is_last(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); first = RuntimeError('partial')
            def work():
                e.active_case = {'continue_north': {'rows': [{'tick': 33, 'physical': {'actual': True}}]}}
                e.meta['physical_steps'] = 1
                raise first
            with self.assertRaises(RuntimeError): e.execute(work)
            self.assertEqual(inputs.read(e.root / 'partial-case.json'), e.active_case)
            self.assertIn('partial-case.json', inputs.read(e.root / 'metadata.json')['output_sha256'])
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run')
            result = e.execute(lambda: e.write('complete.json', {'done': True}))
            self.assertEqual(result['status'], 'complete'); self.assertFalse((e.root / 'failure.json').exists())

    def test_early_inventory_error_keeps_minimal_captured_sources(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); p = Path(d) / 'manifest.json'; p.write_text('not json')
            def work():
                e.capture([str(p)])
                inputs.read(p)
            with self.assertRaises(json.JSONDecodeError): e.execute(work)
            meta = inputs.read(e.root / 'metadata.json')
            self.assertEqual(meta['input_sha256'][str(p)], inputs.digest(p))
            self.assertEqual(meta['input_sha256'], meta['input_sha256_after']); self.assertEqual(meta['status'], 'failed')

    def test_time_limit_and_late_budget_failure_are_not_complete(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); e.started -= 601
            with self.assertRaisesRegex(ValueError, 'time budget'): e.execute(lambda: self.fail('must not work'))
            self.assertEqual(inputs.read(e.root / 'metadata.json')['status'], 'failed')
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); real = e.budget; checks = 0
            def budget():
                nonlocal checks
                checks += 1
                if checks == 3: raise KeyboardInterrupt('after complete write')
                real()
            with patch.object(e, 'budget', side_effect=budget):
                with self.assertRaises(KeyboardInterrupt): e.execute(lambda: None)
            self.assertEqual(inputs.read(e.root / 'metadata.json')['status'], 'failed')


class EarlyAndEnvironmentFaultTests(unittest.TestCase):
    def test_initial_metadata_write_failure_has_failed_owned_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'run'; first = KeyboardInterrupt('initial write'); real = producer.Epoch.write; calls = 0
            def write(obj, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1: raise first
                return real(obj, *args, **kwargs)
            with patch.object(producer.Epoch, 'write', write):
                with self.assertRaises(KeyboardInterrupt) as caught: producer.Epoch(root)
            self.assertIs(caught.exception, first)
            self.assertEqual(inputs.read(root / 'failure.json')['status'], 'failed')
            self.assertFalse((root / 'metadata.json').exists())

    def test_post_ownership_git_failure_has_failed_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            first = SystemExit('git revision')
            with patch.object(producer, 'check_no_other_process'), patch.object(inputs, 'execution_gates', return_value=['p', 'v']), \
                 patch.object(inputs, 'approved_gate'), patch.object(producer.subprocess, 'check_output', side_effect=first):
                with self.assertRaises(SystemExit) as caught: producer.run('engineering', Path(d) / 'run')
            self.assertIs(caught.exception, first)
            self.assertEqual(inputs.read(Path(d) / 'run' / 'metadata.json')['status'], 'failed')

    def test_future_interrupt_retains_completed_tickets_and_current_stream_states(self):
        with tempfile.TemporaryDirectory() as d:
            e = producer.Epoch(Path(d) / 'run'); streams = {k: inputs.new_stream(987654, k) for k in ('directions', 'feeds')}
            # Only synthetic seed987654; these are not a study continuation.
            first = KeyboardInterrupt('future'); calls = 0
            e.active_environment = dict(seed=987654, natural_tape=[])
            def budget():
                nonlocal calls
                calls += 1
                if calls == 4: raise first
            def work():
                producer.future_tape(streams, budget, e.meta, e.active_environment['natural_tape'], e.active_environment)
            with self.assertRaises(KeyboardInterrupt) as caught: e.execute(work)
            self.assertIs(caught.exception, first)
            partial = inputs.read(e.root / 'partial-environment.json')
            self.assertEqual([t['tick'] for t in partial['natural_tape']], [33, 34, 35])
            self.assertEqual(partial['current_stream_states'], {k: producer.normalized(v.getstate()) for k, v in streams.items()})
            self.assertEqual(partial['status'], 'failed')
            self.assertEqual(inputs.read(e.root / 'metadata.json')['future_generator_ticks'], 3)
            self.assertEqual(inputs.read(e.root / 'metadata.json')['physical_steps'], 0)

    def test_future_ticket_is_deeply_immutable(self):
        ticket = producer.NaturalTicket(33, tuple([0] * 256), (1, 2, 3, 4))
        with self.assertRaises(AttributeError): ticket.tick = 34
        with self.assertRaises(TypeError): ticket.directions[0] = 1


class AdditionalFailureTests(unittest.TestCase):
    def test_hash_capture_attempts_every_path_and_keeps_first_interrupt(self):
        for first in (KeyboardInterrupt('input'), SystemExit(12)):
            with self.subTest(kind=type(first)):
                def digest(path):
                    if path == 'a': raise first
                    if path == 'c': raise ValueError('later')
                    return 'hash-b'
                with patch.object(inputs, 'digest', side_effect=digest):
                    values, errors, failure = inputs.capture(['a', 'b', 'c'])
                self.assertIs(failure, first); self.assertEqual(values, {'b': 'hash-b'})
                self.assertEqual(set(errors), {'a', 'c'})

    def test_partial_initial_write_is_repaired_without_overwriting_foreign_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'run'; real = Path.open; first = SystemExit('partial initial write'); calls = 0
            class Broken:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): return self
                def __exit__(self, *args): return self.stream.__exit__(*args)
                def write(self, payload):
                    self.stream.write(payload[:10]); raise first
            def opened(path, *args, **kwargs):
                nonlocal calls
                stream = real(path, *args, **kwargs)
                if path == root / 'metadata.json':
                    calls += 1
                    if calls == 1: return Broken(stream)
                return stream
            with patch.object(Path, 'open', opened):
                with self.assertRaises(SystemExit) as caught: producer.Epoch(root)
            self.assertIs(caught.exception, first)
            self.assertEqual(inputs.read(root / 'metadata.json')['status'], 'failed')
            self.assertEqual(inputs.read(root / 'failure.json')['error'], repr(first))

    def test_signal_setup_failure_after_ownership_is_retained(self):
        with tempfile.TemporaryDirectory() as d:
            first = KeyboardInterrupt('signal setup')
            with patch.object(producer, 'check_no_other_process'), patch.object(inputs, 'execution_gates', return_value=['p', 'v']), \
                 patch.object(inputs, 'approved_gate'), patch.object(producer.signal, 'signal', side_effect=first):
                with self.assertRaises(KeyboardInterrupt) as caught: producer.run('engineering', Path(d) / 'run')
            self.assertIs(caught.exception, first)
            self.assertEqual(inputs.read(Path(d) / 'run' / 'metadata.json')['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
