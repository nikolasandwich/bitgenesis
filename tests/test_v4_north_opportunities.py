import json
import unittest
from copy import deepcopy
from pathlib import Path
from scripts import analyze_v4_north_opportunities as analysis


def fixture():
    return json.loads(Path('data/v4-study-025/cases/seed-120000-random-both-exchange-true.json').read_text())


class OpportunitiesTest(unittest.TestCase):
    def test_saved_actors_and_roots(self):
        case = fixture()
        result = analysis.analyze_case(case, 'heterogeneous')
        self.assertEqual(len(result['steps']), 32)
        self.assertEqual([a['identity'] for a in result['steps'][0]], [0, 1, 2])
        self.assertEqual([a['root'] for a in result['steps'][0]], [0, 1, 2])
        a = result['steps'][0][1]
        self.assertEqual((a['direction'], a['target'], a['reason'], a['encoded_material'], a['formed_material']), (3, 70, 'raw_material', 2, None))
        self.assertEqual(a['energy_before'], 64)
        for old, step in zip([case['initial']]+case['rows'][:-1], result['steps']):
            self.assertEqual([a['identity'] for a in step], [i for i in old['site_ids'] if i is not None])

    def test_saved_tampering_rejected(self):
        for change in ('accepted', 'root', 'actor', 'reason', 'raw', 'energy', 'parent'):
            case = fixture(); p = case['rows'][0]['physical']
            if change == 'accepted': p['driven']['inputs'][85]['accepted'] += 1
            if change == 'root': case['final']['parents'][2] = 0
            if change == 'actor': p['material']['proposals'].pop()
            if change == 'reason': p['material']['proposals'][1]['reason'] = 'energy'
            if change == 'raw': p['raw'][70] += 1
            if change == 'energy': p['interaction_units'][85]['energy'] += 1
            if change == 'parent': case['final']['parents'][3] = 2
            with self.subTest(change=change), self.assertRaises(ValueError):
                analysis.analyze_case(case, 'heterogeneous')

    def records(self):
        return [dict(genotype=g, mode=m, exchange=e, seed=s, steps=[[] for _ in range(32)]) for g, m, e, s in analysis.GRID]

    def test_joint_masks_dissolved_sentinel_and_nonzero(self):
        records = self.records()
        base = dict(tick=1, site=0, identity=0, root=0, direction=3, proposed=2, accepted=1,
                    energy_before=4, energy_interaction=4, target=16, target_occupied=True,
                    raw_available=0, reason='energy', encoded_material=2, formed_material=None)
        records[0]['steps'][0] = [base, dict(base, site=1, identity=1, root=1, reason='dissolved', energy_interaction=0),
                                    dict(base, site=2, identity=2, root=2, reason='formed', energy_interaction=20, target_occupied=False, raw_available=1, formed_material=2),
                                    dict(base, site=3, identity=3, root=0, reason='collision', energy_interaction=20, target_occupied=False, raw_available=1)]
        cells = analysis.summarize(records)
        self.assertEqual(len(cells), 12)
        a, t = cells[0]['all'], cells[0]['target']
        self.assertEqual((a['actor_steps'], a['north_tickets'], a['north_proposals'], a['north_nonzero_formed']), (4, 4, 3, 1))
        self.assertEqual((t['actor_steps'], t['north_nonzero_formed'], t['proposed'], t['accepted']), (3, 0, 6, 3))
        self.assertEqual(a['north_predicates'], {'0': 2, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 1})
        self.assertEqual(t['north_reasons']['dissolved'], 1)
        self.assertEqual(list(a['reasons']), list(analysis.REASONS))
        self.assertEqual(cells[-1]['all']['actor_steps'], 0)

    def test_exact_grid_rejects_missing_reordered_duplicate_and_boolean_seed(self):
        for change in ('missing', 'reordered', 'duplicate', 'bool', 'exchange'):
            records = self.records()
            if change == 'missing': records.pop()
            if change == 'reordered': records.reverse()
            if change == 'duplicate': records[-1] = records[0]
            if change == 'bool': records[0]['seed'] = True
            if change == 'exchange': records[0]['exchange'] = 0
            with self.subTest(change=change), self.assertRaises(ValueError): analysis.summarize(records)

    def test_initial_failure_preserves_inventory_and_hash_errors(self):
        import tempfile, types, sys, hashlib
        from unittest.mock import patch
        def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root/'run'; present = root/'present'; missing = root/'missing'
            present.write_text('unchanged')
            helper = types.SimpleNamespace(input_paths=lambda errors: [str(present), str(missing)],
                bindings=lambda: (_ for _ in ()).throw(ValueError('bad binding')), digest=digest,
                source_cases=lambda: iter([]), read=lambda p: json.loads(p.read_text()), save=lambda p, v: p.write_text(json.dumps(v)))
            def git(command, **kwargs): return '' if command[1] == 'status' else 'a'*40
            with patch.object(analysis, 'OUTPUT', out), patch.object(analysis.subprocess, 'check_output', git), patch.dict(sys.modules, {'scripts.north_opportunity_inputs': helper}):
                with self.assertRaisesRegex(ValueError, 'bad binding'): analysis.main()
                with self.assertRaises(FileExistsError): analysis.main()
            meta = json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'], 'failed')
            self.assertEqual(meta['input_paths'], [str(present), str(missing)])
            self.assertEqual(meta['input_sha256'], {str(present): digest(present)})
            self.assertEqual(meta['input_sha256_after'], meta['input_sha256'])
            self.assertIn(str(missing), meta['input_read_errors_before'])
            self.assertIn(str(missing), meta['input_read_errors'])
            self.assertEqual(meta['output_sha256'], {'records.json': digest(out/'records.json')})
            self.assertEqual(meta['new_simulation_steps'], 0)

    def test_final_write_budget(self):
        import tempfile, types, sys, hashlib
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)/'run'; expired = False
            def save(path, value):
                nonlocal expired
                path.write_text(json.dumps(value))
                if path.name == 'metadata.json' and value['status'] == 'complete': expired = True
            helper = types.SimpleNamespace(input_paths=lambda errors: [], bindings=lambda: {},
                digest=lambda p: hashlib.sha256(p.read_bytes()).hexdigest(), source_cases=lambda: iter([]), read=lambda p: {}, save=save)
            def git(command, **kwargs): return '' if command[1] == 'status' else 'a'*40
            with patch.object(analysis, 'OUTPUT', out), patch.object(analysis.subprocess, 'check_output', git), patch.object(analysis.time, 'monotonic', side_effect=lambda: 301 if expired else 0), patch.object(analysis, 'summarize', return_value=[]), patch.dict(sys.modules, {'scripts.north_opportunity_inputs': helper}):
                with self.assertRaisesRegex(ValueError, 'bounded execution'): analysis.main()
            self.assertEqual(json.loads((out/'metadata.json').read_text())['status'], 'failed')

    def test_saved_dissolution_releases_target_before_proposals(self):
        case = json.loads(Path('data/v4-study-019/cases/seed-120000-random-direction-exchange-false.json').read_text())
        result = analysis.analyze_case(case, 'homogeneous')
        actor = next(a for a in result['steps'][7] if a['site'] == 102)
        self.assertIsNotNone(case['rows'][6]['physical']['units'][101])
        self.assertEqual(case['rows'][6]['physical']['raw'][101], 0)
        self.assertIn(101, case['rows'][7]['physical']['material']['dissolved'])
        self.assertEqual((actor['target'], actor['target_occupied'], actor['raw_available']), (101, False, 1))
        bad = deepcopy(case)
        with self.assertRaisesRegex(ValueError, 'initial genotype'):
            analysis.analyze_case(bad, 'heterogeneous')
