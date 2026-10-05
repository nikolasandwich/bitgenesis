import json
import unittest
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
from scripts import verify_v4_material_support as v
from scripts import verify_v4_north_opportunities as old

GRID = tuple(product(('homogeneous', 'heterogeneous'), ('random-direction', 'random-feed', 'random-both'), (False, True), range(120000, 120020)))
CATEGORIES = ('no_initial_material', 'occupied', 'available', 'other')
REASONS = ('energy', 'occupied', 'raw_material', 'collision', 'formed')


def synthetic():
    units = [None] * 256
    raw = [0] * 256
    raw[1] = 1
    case = dict(mode='random-direction', exchange=False, seed=120000,
                initial=dict(tick=0, units=units, raw=raw),
                rows=[dict(tick=tick, physical=dict(tick=tick, units=deepcopy(units), raw=raw.copy())) for tick in range(1, 33)])
    actors = dict(genotype='homogeneous', mode=case['mode'], exchange=False, seed=120000, steps=[[] for _ in range(32)])
    for site, (target, occupied, stock, reason) in enumerate(((0, False, 0, 'energy'), (1, True, 0, 'occupied'), (1, False, 1, 'formed'), (1, False, 0, 'raw_material'), (0, False, 0, 'dissolved'))):
        actors['steps'][0].append(dict(tick=1, site=site, identity=site, root=site % 3, direction=3, target=target, target_occupied=occupied, raw_available=stock, reason=reason, energy_interaction=16 if site % 2 else 15))
    return case, actors


def summary_fixture():
    event = dict(tick=1, site=85, identity=0, root=0, target=69, initial_stock=0, raw_available=0,
                 target_occupied=False, category='no_initial_material', energy_ready=False, reason='energy')
    return [dict(genotype=g, mode=m, exchange=x, seed=s, support=[85, 86, 101, 102, 117, 118, 204], checked_snapshots=33, checked_sites=8448, violations=[], north_tickets=dict(all=1, target=1), north_dissolved=dict(all=0, target=0), events=[deepcopy(event)]) for g,m,x,s in GRID]


class MaterialVerifierTests(unittest.TestCase):
    def test_independent_inventory_classification_and_replay_gate(self):
        case, actors = synthetic()
        case['rows'][3]['physical']['raw'][2] = 2
        with patch.object(old, 'recount', return_value=actors) as replay:
            result = v.analyze_case(case, actors)
            replay.assert_called_once_with(case, 'homogeneous')
        self.assertEqual(result['support'], [1])
        self.assertEqual(result['checked_snapshots'], 33)
        self.assertEqual(result['checked_sites'], 8448)
        self.assertEqual(result['violations'], [dict(tick=4, site=2, expected=0, actual=2)])
        self.assertEqual([e['category'] for e in result['events']], list(CATEGORIES))
        self.assertEqual(result['north_tickets'], dict(all=5, target=4))
        self.assertEqual(result['north_dissolved'], dict(all=1, target=1))
        self.assertEqual([e['energy_ready'] for e in result['events']], [False, True, False, True])
        wrong = deepcopy(actors); wrong['steps'][0][0]['reason'] = 'formed'
        with patch.object(old, 'recount', return_value=wrong), self.assertRaises(ValueError):
            v.analyze_case(case, actors)
        with patch.object(old, 'recount', side_effect=ValueError('physics')), self.assertRaisesRegex(ValueError, 'physics'):
            v.analyze_case(case, actors)

    def test_input_shape_rejected(self):
        for change in ('identity', 'steps', 'initial', 'snapshot', 'bool_raw'):
            case, actors = synthetic()
            if change == 'identity': actors['seed'] = 120001
            if change == 'steps': actors['steps'].pop()
            if change == 'initial': case['initial']['units'].pop()
            if change == 'snapshot': case['rows'][0]['physical']['raw'].pop()
            if change == 'bool_raw': case['rows'][0]['physical']['raw'][0] = True
            with self.subTest(change=change), patch.object(old, 'recount', return_value=actors), self.assertRaises(ValueError):
                v.analyze_case(case, actors)

    def test_one_real_saved_case_and_actor_tamper(self):
        case = json.loads(Path('data/v4-study-019/cases/seed-120000-random-direction-exchange-false.json').read_text())
        actors = old.recount(case, 'homogeneous')
        result = v.analyze_case(case, actors)
        self.assertEqual(result['support'], [85, 86, 101, 102, 117, 118, 204])
        self.assertEqual(result['violations'], [])
        actors['steps'][0][0]['energy_interaction'] += 1
        with self.assertRaises(ValueError): v.analyze_case(case, actors)

    def test_twelve_strict_cells_with_zero_reason_counts(self):
        records = summary_fixture()
        cells = v.summarize(records)
        self.assertEqual(len(cells), 12)
        self.assertEqual(cells[0]['n'], 20)
        self.assertEqual(cells[0]['checked_snapshots'], 660)
        self.assertEqual(cells[0]['checked_sites'], 168960)
        self.assertEqual(cells[0]['violation_count'], 0)
        scope = cells[0]['scopes']['target']
        self.assertEqual(scope['north_proposals'], 20)
        self.assertEqual(scope['categories']['no_initial_material'], dict(n=20, energy_ready=0, reasons=dict(energy=20, occupied=0, raw_material=0, collision=0, formed=0)))
        self.assertEqual(scope['categories']['other']['reasons'], dict.fromkeys(REASONS, 0))

    def test_summary_rejects_corrupt_records(self):
        mutations = [lambda r: r.pop(), lambda r: r.reverse(),
            lambda r: r[0].update(extra=0), lambda r: r[0].update(checked_sites=True),
            lambda r: r[0]['north_tickets'].update(all=-1), lambda r: r[0]['north_tickets'].update(target=2),
            lambda r: r[0]['events'][0].update(energy_ready=1), lambda r: r[0]['events'][0].update(identity=True),
            lambda r: r[0]['events'][0].update(reason='dissolved'), lambda r: r[0]['events'][0].update(category='available'),
            lambda r: r[0]['events'].append(deepcopy(r[0]['events'][0])), lambda r: r[0].update(support=[2, 1]),
            lambda r: r[0]['violations'].append(dict(tick=0, site=0, expected=0, actual=0)),
            lambda r: r[0]['events'][0].update(extra=0), lambda r: r[0]['north_dissolved'].update(all=2)]
        for index, mutate in enumerate(mutations):
            records = summary_fixture(); mutate(records)
            with self.subTest(index=index), self.assertRaises(ValueError): v.summarize(records)


class MaterialVerifierMainTests(unittest.TestCase):
    def test_early_failures_preserve_input_and_output_evidence(self):
        import sys
        import types
        from tempfile import TemporaryDirectory
        for defect in ('binding', 'metadata', 'paths'):
            with self.subTest(defect=defect), TemporaryDirectory() as directory:
                root = Path(directory)
                for name in ('metadata.json', 'records.json', 'summary.json'):
                    (root/name).write_text('{}')
                bound = {f'input-{i}': 'a' * 64 for i in range(400)}
                bound['scripts/verify_v4_material_support.py'] = 'a' * 64
                def paths(errors):
                    if defect == 'paths': raise ValueError('broken inventory')
                    return sorted(bound)
                helper = types.SimpleNamespace(input_paths=paths,
                    digest=lambda path: 'a' * 64,
                    bindings=lambda: {} if defect == 'binding' else bound,
                    read=lambda path: dict(status='failed'), source_cases=lambda: ())
                with patch.dict(sys.modules, {'scripts.material_support_inputs': helper}), patch.object(v, 'OUTPUT', root), patch.object(v, 'analyze_case') as analyze:
                    with self.assertRaises(ValueError): v.main()
                    analyze.assert_not_called()
                evidence = json.loads((root/'verification-failure.json').read_text())
                self.assertEqual(evidence['status'], 'failed')
                self.assertEqual(len(evidence['files_sha256_before']), 3)
                self.assertEqual(len(evidence['files_sha256_after']), 3)
                self.assertEqual(len(evidence['input_sha256']), 0 if defect == 'paths' else 401)
                self.assertFalse((root/'independent-verification.json').exists())

    def test_existing_proof_never_overwritten(self):
        import sys
        import types
        from tempfile import TemporaryDirectory
        helper = types.SimpleNamespace(bindings=None, read=None, digest=None, input_paths=None, source_cases=None)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            proof = root/'independent-verification.json'; proof.write_text('existing evidence')
            with patch.dict(sys.modules, {'scripts.material_support_inputs': helper}), patch.object(v, 'OUTPUT', root), self.assertRaisesRegex(ValueError, 'proof already exists'):
                v.main()
            self.assertEqual(proof.read_text(), 'existing evidence')
            self.assertFalse((root/'verification-failure.json').exists())

    def test_postwrite_budget_failure_withdraws_verified_proof(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            proof = Path(directory)/'independent-verification.json'
            calls = []
            def budget(extra=0):
                calls.append(extra)
                if len(calls) == 2:
                    self.assertTrue(proof.exists())
                    raise ValueError('postwrite budget')
            with self.assertRaisesRegex(ValueError, 'postwrite budget'):
                v.write_proof(proof, dict(status='verified'), budget)
            self.assertFalse(proof.exists())
            self.assertGreater(calls[0], 0)
            self.assertEqual(calls[1], 0)
