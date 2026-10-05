import json
import unittest
from copy import deepcopy
from pathlib import Path
from scripts import verify_v4_north_energy as audit


def initial(collision=False):
    units = [None]*256; raw = [0]*256; directions = [0]*256
    units[32] = dict(material=0, energy=7, program=[0, 0, 0, 2])
    directions[32] = 3; raw[16] = 1
    units[100] = dict(material=3, energy=0, program=[3]*4)
    if collision:
        units[17] = dict(material=1, energy=20, program=[1]*4)
        directions[17] = 1
    return dict(units=units, raw=raw, directions=directions, mutation_tickets=[[0, 0, 1] for _ in units])


def probe(collision=False):
    state = initial(collision)
    selection = dict(genotype='heterogeneous', mode='random-both', seed=120000,
                     exchange=False, tick=1, site=32, identity=0, root=0, energy_before=7)
    control = audit.phase(state)
    physical = dict(control, interaction_units=state['units'], directions=state['directions'], mutation_tickets=state['mutation_tickets'])
    case = dict(mode='random-both', seed=120000, exchange=False, initial=dict(raw=state['raw'], site_ids=[0 if i == 32 else None for i in range(256)]), rows=[dict(tick=1, physical=physical)], final=dict(parents=[None]))
    return case, selection


class IndependentEnergyTest(unittest.TestCase):
    def test_phase_expression_dissolution_and_immutability(self):
        state = initial(); state['units'][32]['energy'] = 16; before = deepcopy(state)
        result = audit.phase(state)
        self.assertEqual(result['units'][16], dict(material=2, energy=5, program=[0, 0, 0, 2]))
        self.assertEqual(result['units'][32]['energy'], 6)
        self.assertEqual(result['raw'][100], 1)
        p = result['material']['proposals'][0]
        self.assertFalse(p['mutated']); self.assertEqual(p['mutation_ticket'], [0, 0, 1])
        self.assertEqual(result['material']['spent'], 5)
        self.assertEqual(state, before)

    def test_complete_control_treated_and_negative_collision(self):
        for collision in (False, True):
            case, selected = probe(collision); before = deepcopy(case)
            record = audit.verify_probe(case, selected)
            self.assertEqual(record['added_energy'], 9)
            reasons = {p['source']: p['reason'] for p in record['treated']['material']['proposals']}
            self.assertEqual(reasons[32], 'collision' if collision else 'formed')
            if collision:
                self.assertEqual(reasons[17], 'collision')
                self.assertEqual(record['control']['material']['proposals'][0]['reason'], 'formed')
            self.assertEqual(case, before)

    def test_bad_control_energy_and_source_keys_rejected(self):
        for change in ('control', 'energy', 'seed', 'identity', 'root'):
            case, selected = probe()
            if change == 'control': case['rows'][0]['physical']['raw'][16] += 1
            elif change == 'energy': selected['energy_before'] += 1
            else: selected[change] += 1
            with self.subTest(change=change), self.assertRaises(ValueError): audit.verify_probe(case, selected)

    def test_selection_exact_saved_order_and_predicates(self):
        records = json.loads(Path('docs/research/results/v4-study-026-records.json').read_text())
        result = audit.select(records)
        self.assertEqual(len(result), 52)
        self.assertEqual([sum(s['genotype'] == g and s['exchange'] == e for s in result)
                          for g in ('homogeneous', 'heterogeneous') for e in (False, True)], [21, 5, 21, 5])
        first = result[0]
        record = next(r for r in records if all(r[k] == first[k] for k in ('genotype', 'mode', 'seed', 'exchange')))
        actor = next(a for a in record['steps'][first['tick']-1] if a['site'] == first['site'])
        actor['target_occupied'] = True
        with self.assertRaises(ValueError): audit.select(records)

    def test_statistics_all_proposals_including_adverse_effect(self):
        selections = audit.select(json.loads(Path('docs/research/results/v4-study-026-records.json').read_text()))
        case, selection = probe(True); record = audit.verify_probe(case, selection)
        rows = [dict(deepcopy(record), **dict(s, energy_before=7)) for s in selections]
        for r in rows:
            for state in (r['initial'], r['control'], r['treated']):
                state['units'][32], state['units'][r['site']] = state['units'][r['site']], state['units'][32]
            for arm in ('control', 'treated'):
                for p in r[arm]['material']['proposals']:
                    p['source'] = r['site'] if p['source'] == 32 else (r['site']+1) % 256
        cells = audit.aggregate(rows)
        self.assertEqual(len(cells), 4)
        c = cells[0]
        self.assertEqual((c['probes'], c['control_formed'], c['treated_formed']), (21, 0, 0))
        self.assertEqual((c['total_formed_delta'], c['spent_delta'], c['other_reason_changes']), (-21, -105, 21))
        self.assertEqual(c['treated_reasons']['collision'], 21)
        with self.assertRaises(ValueError): audit.aggregate(rows[::-1])
        rows[0]['added_energy'] += 1
        with self.assertRaises(ValueError): audit.aggregate(rows)

    def test_invalid_phase_inputs_rejected(self):
        for key, value in (('mutation_tickets', [1000, 0, 1]), ('directions', 4), ('raw', -1)):
            state = initial(); state[key][0] = value
            with self.subTest(key=key), self.assertRaises(ValueError): audit.phase(state)

    def test_main_initial_failure_preserves_readable_inventory(self):
        import tempfile, types, sys, hashlib
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); present = root/'present'; missing = root/'missing'; present.write_text('original')
            def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
            helper = types.SimpleNamespace(input_paths=lambda errors: [str(present), str(missing)],
                bindings=lambda: (_ for _ in ()).throw(ValueError('bad binding')), digest=digest,
                source_cases=lambda: iter([]), read=lambda p: json.loads(p.read_text()))
            with patch.object(audit, 'OUTPUT', root), patch.dict(sys.modules, {'scripts.north_energy_inputs': helper}):
                with self.assertRaisesRegex(ValueError, 'bad binding'): audit.main()
            failure = json.loads((root/'verification-failure.json').read_text())
            self.assertEqual(failure['input_sha256'], {str(present): digest(present)})
            self.assertEqual(failure['input_sha256_after'], failure['input_sha256'])
            self.assertIn(str(missing), failure['read_errors_before'])
            self.assertEqual(failure['completed_probes'], 0)
            self.assertFalse((root/'independent-verification.json').exists())

    def test_main_existing_proof_never_overwrites(self):
        import tempfile, types, sys
        from unittest.mock import patch
        helper = types.SimpleNamespace(**dict.fromkeys(('bindings', 'read', 'digest', 'input_paths', 'source_cases')))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); proof = root/'independent-verification.json'; proof.write_text('keep')
            with patch.object(audit, 'OUTPUT', root), patch.dict(sys.modules, {'scripts.north_energy_inputs': helper}):
                with self.assertRaisesRegex(ValueError, 'proof already exists'): audit.main()
            self.assertEqual(proof.read_text(), 'keep')

    def test_main_recounts_all_sources_before_probes_and_binds_proof(self):
        import tempfile, types, sys, hashlib
        from unittest.mock import patch, Mock
        selections = audit.select(json.loads(Path('docs/research/results/v4-study-026-records.json').read_text()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bound = {f'input-{i}': 'h' for i in range(400)}
            bound['scripts/verify_v4_north_energy.py'] = 'self'
            paths = sorted(bound)
            saved = [dict(s) for s in selections]
            for name, obj in (('records.json', saved), ('summary.json', [])):
                (root/name).write_text(json.dumps(obj))
            def digest(path):
                path = Path(path)
                if path == Path(audit.__file__) or str(path) == 'scripts/verify_v4_north_energy.py': return 'self'
                if str(path) in bound: return bound[str(path)]
                return hashlib.sha256(path.read_bytes()).hexdigest()
            meta = dict(status='complete', planned_probes=52, completed_probes=52, new_phase_transitions=104,
                new_full_world_steps=0, new_environment_sources=0, reused_environment_sources=20,
                new_independent_initial_worlds=0, time_limit_seconds=300, storage_limit_bytes=33554432,
                git_commit='a'*40, elapsed_seconds=1, input_paths=paths, input_sha256=bound, input_sha256_after=bound,
                output_sha256={n: digest(root/n) for n in ('records.json', 'summary.json')})
            (root/'metadata.json').write_text(json.dumps(meta))
            source = [(g, Path(f'case-{i}')) for i, (g, m, e, s) in enumerate(audit.prior.GRID)]
            cases = {p: dict(mode=m, exchange=e, seed=s) for (_, p), (_, m, e, s) in zip(source, audit.prior.GRID)}
            def read(path):
                if path in cases: return cases[path]
                if path == Path('data/v4-study-026/records.json'): return list(range(240))
                return json.loads(path.read_text())
            helper = types.SimpleNamespace(input_paths=lambda errors: paths, bindings=lambda: bound, digest=digest,
                                           source_cases=lambda: iter(source), read=read)
            recount = Mock(side_effect=list(range(240)))
            def verify(case, selection):
                self.assertEqual(recount.call_count, 240)
                return dict(selection)
            with patch.object(audit, 'OUTPUT', root), patch.dict(sys.modules, {'scripts.north_energy_inputs': helper}), \
                    patch.object(audit.prior, 'recount', recount), patch.object(audit, 'select', return_value=selections) as selected, \
                    patch.object(audit, 'verify_probe', side_effect=verify) as verified, patch.object(audit, 'aggregate', return_value=[]):
                audit.main()
            selected.assert_called_once_with(list(range(240)))
            self.assertEqual(verified.call_count, 52)
            proof = json.loads((root/'independent-verification.json').read_text())
            self.assertEqual(proof['replayed_saved_steps'], 7680)
            self.assertEqual(proof['new_phase_transitions'], 104)
            self.assertEqual(proof['input_sha256'], proof['input_sha256_after'])
            self.assertEqual(proof['files_sha256'], {n: digest(root/n) for n in ('metadata.json', 'records.json', 'summary.json')})
