import copy
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts import analyze_v4_material_support as subject


def fixture():
    units = [None] * 256
    units[85] = {'energy': 32}
    raw = [0] * 256
    raw[86] = 1
    ids = [None] * 256
    ids[85] = 0
    initial = dict(units=units, raw=raw, site_ids=ids)
    rows = [dict(tick=t, site_ids=copy.deepcopy(ids), physical=dict(tick=t, units=copy.deepcopy(units), raw=list(raw))) for t in range(1, 33)]
    actor = dict(tick=1, site=85, identity=0, root=0, direction=3, target=69, raw_available=0, target_occupied=False, energy_interaction=32, reason='raw_material')
    actors = dict(genotype='homogeneous', mode='random-direction', exchange=False, seed=120000, steps=[[dict(actor, tick=t)] for t in range(1, 33)])
    case = dict(mode='random-direction', exchange=False, seed=120000, initial=initial, rows=rows, final=dict(copy.deepcopy(initial), parents=[None]))
    return case, actors


class MaterialSupportTests(unittest.TestCase):
    def test_inventory_and_north(self):
        case, actors = fixture()
        case['rows'][0]['physical']['raw'][86] = 0
        case['rows'][0]['physical']['raw'][87] = 1
        record = subject.analyze_case(case, actors)
        self.assertEqual(record['support'], [85, 86])
        self.assertEqual(record['checked_sites'], 8448)
        self.assertEqual(record['violations'], [dict(tick=1, site=86, expected=1, actual=0), dict(tick=1, site=87, expected=0, actual=1)])
        self.assertEqual(record['north_tickets'], dict(all=32, target=32))
        self.assertEqual(record['events'][0]['category'], 'no_initial_material')
        self.assertTrue(record['events'][0]['energy_ready'])

    def test_categories_dissolved_and_other_root(self):
        case, actors = fixture()
        # North target 69 is supplied initially, then classify the saved proposal state.
        case['initial']['raw'][69] = 1
        for t, (occupied, raw, reason) in enumerate([(True, 0, 'occupied'), (False, 1, 'formed'), (False, 2, 'energy')]):
            actors['steps'][t][0].update(target_occupied=occupied, raw_available=raw, reason=reason, energy_interaction=8 if t == 2 else 32)
        actors['steps'][3][0].update(reason='dissolved', energy_interaction=0)
        record = subject.analyze_case(case, actors)
        self.assertEqual([e['category'] for e in record['events'][:3]], ['occupied', 'available', 'other'])
        self.assertFalse(record['events'][2]['energy_ready'])
        self.assertEqual(record['north_dissolved'], dict(all=1, target=1))
        self.assertEqual(len(record['events']), 31)

    def test_reject_damaged_inputs(self):
        for mutation in [lambda c,a: a.update(seed=120001), lambda c,a: a['steps'].pop(), lambda c,a: c['initial']['raw'].pop(), lambda c,a: a['steps'][0][0].update(target_occupied=1), lambda c,a: a['steps'][0].clear(), lambda c,a: a['steps'][0][0].update(identity=True)]:
            with self.subTest(mutation=mutation):
                c,a = fixture(); mutation(c,a)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    subject.analyze_case(c,a)

    def records(self):
        c,a = fixture(); record = subject.analyze_case(c,a)
        return [dict(copy.deepcopy(record), genotype=g, mode=m, exchange=e, seed=s) for g in ('homogeneous','heterogeneous') for m in ('random-direction','random-feed','random-both') for e in (False,True) for s in range(120000,120020)]

    def test_summary_full_grid_and_zero_reasons(self):
        summary = subject.summarize(self.records())
        self.assertEqual(len(summary), 12)
        self.assertEqual(summary[0]['n'], 20)
        scope = summary[0]['scopes']['all']
        self.assertEqual(scope['north_proposals'], 640)
        self.assertEqual(scope['categories']['no_initial_material']['reasons'], dict(energy=0, occupied=0, raw_material=640, collision=0, formed=0))
        self.assertEqual(scope['categories']['available']['n'], 0)

    def test_summary_strict(self):
        for mutation in [lambda r:r.pop(), lambda r:r.reverse(), lambda r:r[0]['events'][0].update(energy_ready=1), lambda r:r[0]['events'][0].update(reason='dissolved'), lambda r:r[0]['events'][0].update(category='bad'), lambda r:r[0]['north_tickets'].update(all=True), lambda r:r[0].update(checked_sites=8447), lambda r:r[0]['events'][0].update(extra=1), lambda r:r[0]['north_tickets'].update(all=31)]:
            with self.subTest(mutation=mutation):
                records=self.records(); mutation(records)
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    subject.summarize(records)

    def test_zero_events_and_nontarget_root(self):
        case, actors = fixture()
        case['final']['parents'] = [None, None, None]
        for snapshot in [case['initial'], case['final'], *case['rows']]:
            snapshot['site_ids'][85] = 2
        for step in actors['steps']:
            step[0].update(identity=2, root=2)
        record = subject.analyze_case(case, actors)
        self.assertEqual(record['north_tickets'], dict(all=32, target=0))
        for step in actors['steps']:
            step[0].update(reason='dissolved', energy_interaction=0)
        record = subject.analyze_case(case, actors)
        self.assertEqual(record['events'], [])
        self.assertEqual(record['north_dissolved'], dict(all=32, target=0))

    def test_main_preserves_progress_on_bad_second_case(self):
        from scripts import material_support_inputs as inputs
        case, actor = fixture()
        ledger = [dict(copy.deepcopy(actor), genotype=g, mode=m, exchange=e, seed=s) for g,m,e,s in subject.GRID]
        sources = [(g, str(i)) for i,(g,m,e,s) in enumerate(subject.GRID)]
        bound = {str(i): 'frozen' for i in range(401)}
        def read(path):
            if str(path) == 'data/v4-study-026/records.json':
                return ledger
            return copy.deepcopy(case)  # Second identity deliberately mismatches.
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'audit'
            with patch.object(subject, 'OUTPUT', out), patch.object(subject.subprocess, 'check_output', side_effect=['', 'commit']), patch.object(inputs, 'input_paths', return_value=list(bound)), patch.object(inputs, 'bindings', return_value=bound), patch.object(inputs, 'digest', return_value='frozen'), patch.object(inputs, 'source_cases', return_value=iter(sources)), patch.object(inputs, 'read', side_effect=read):
                with self.assertRaisesRegex(ValueError, 'identity match'):
                    subject.main()
            metadata = json.loads((out/'metadata.json').read_text())
            self.assertEqual(metadata['status'], 'failed')
            self.assertEqual(metadata['completed_cases'], 1)
            self.assertEqual(metadata['checked_snapshots'], 33)
            self.assertEqual(metadata['checked_sites'], 8448)
            self.assertEqual(len(json.loads((out/'records.json').read_text())), 1)
            self.assertEqual(metadata['input_sha256_after'], bound)
