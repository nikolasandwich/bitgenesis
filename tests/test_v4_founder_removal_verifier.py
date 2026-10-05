"""Independent route boundary tests, including historical dead identities."""
import unittest
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch
from scripts import verify_v4_founder_removal as audit


class FounderRemovalVerifierTests(unittest.TestCase):
    def test_strict_comparison_rejects_boolean_for_count(self):
        with self.assertRaises(ValueError):
            audit.same({'count': True}, {'count': 1}, 'typed count')

    def test_intervals_use_future_ticks_only(self):
        self.assertEqual(audit.intervals([2] * 9, 24), [[24, 32]])
        self.assertEqual(audit.intervals([], 33), [])
        self.assertEqual(audit.intervals([2, 0, 2, 2], 7), [[7, 7], [9, 10]])

    def test_ancestry_stops_at_selected_identity(self):
        parents = [None, None, None, 0, 1, 3, 4, 0]
        self.assertEqual(audit.chain_to(6, {3, 4}, parents), [6, 4])
        self.assertIsNone(audit.chain_to(7, {3, 4}, parents))
        with self.assertRaises(ValueError):
            audit.chain_to(3, {0}, [None, None, None, 3])

    def test_birth_after_dead_maximum_does_not_recycle(self):
        units = [dict(material=0, program=[0]*4, energy=20), None]
        ids, people = audit.initial_history(units)
        people.append(dict(people[0], id=1, parent=0, birth_tick=1, death_tick=2))
        physical = dict(tick=3, units=[units[0],dict(units[0],energy=1)], material=dict(dissolved=[],proposals=[dict(reason='formed',source=0,target=1,material=0,child_program=[0]*4,child_energy=1,mutated=False)]))
        births, deaths = audit.advance_history(ids, people, physical)
        self.assertEqual(ids, [0,2])
        self.assertEqual(births[0]['id'], 2)
        self.assertEqual(deaths, [])

    def test_diagnostic_copy_never_enters_metric_window(self):
        arm = dict(initial=dict(tick=32,copies=[dict(all_new=True)]*2),rows=[],
                   final=dict(individuals=[],units=[]))
        result = audit.summarize_arm(arm, [])
        self.assertEqual(result['metrics']['persistent10'], 0)
        self.assertEqual(result['metrics']['double_new_ever'], 0)

    def test_short_window_and_selected_ancestry_are_separate(self):
        people=[dict(parent=None,birth_tick=0,site=85),dict(parent=None,birth_tick=0,site=86),
                dict(parent=0,birth_tick=6,site=117),dict(parent=1,birth_tick=6,site=118),
                dict(parent=0,birth_tick=24,site=85),dict(parent=1,birth_tick=24,site=86)]
        copies=[dict(members=[2,3],sites=[117,118],all_new=True),dict(members=[4,5],sites=[85,86],all_new=True)]
        rows=[dict(tick=t,copies=copies,births=[],deaths=[],physical=dict(imported=0,spent=0)) for t in range(24,33)]
        arm=dict(initial=dict(tick=23),rows=rows,final=dict(individuals=people,units=[]))
        result=audit.summarize_arm(arm,[2,3])
        self.assertEqual(result['metrics']['formation_supported'],1)
        self.assertEqual(result['metrics']['upper_formed'],1)
        self.assertEqual(result['metrics']['selected_ancestry_supported'],0)
        self.assertEqual(result['metrics']['persistent10'],0)
        self.assertEqual(result['metrics']['formation_persistent10'],0)
        people[4]['parent']=2;people[5]['parent']=3
        self.assertEqual(audit.summarize_arm(arm,[2,3])['metrics']['selected_ancestry_supported'],1)
        arm['initial']['tick']=22
        rows.insert(0,dict(rows[0],tick=23))
        # Births must precede the observed copy: move both formed births to tick 23.
        people[4]['birth_tick']=23;people[5]['birth_tick']=23
        positive=audit.summarize_arm(arm,[2,3])
        for key in ('persistent10','formation_persistent10','upper_persistent10','selected_ancestry_persistent10'):
            self.assertEqual(positive['metrics'][key],1)
        self.assertEqual(positive['upper_witnesses'][0]['selected_ancestry'][0]['chain'],[4,2])

    def test_horizontal_direction_codes_and_structural_zero(self):
        selection=dict(genotype='homogeneous',source='unused',eligible=True,exchange=False,
                       t0=6,category='horizontal_structural_zero',energy_export_preview=0)
        source=dict(rows=[dict(physical=dict(directions=[0,1])) for _ in range(32)])
        arm=dict(initial=dict(energy_export=0),metrics={m:0 for m in audit.METRICS})
        with patch.object(audit,'choose_case',return_value=selection), patch.object(audit,'verify_arm',return_value=arm):
            audit.verify_branch(source,selection)
            source['rows'][6]['physical']['directions']=[2]
            with self.assertRaisesRegex(ValueError,'horizontal-only'):
                audit.verify_branch(source,selection)

    def test_first_selected_source_control_export_and_history(self):
        selection=next(s for s in json.loads(Path('docs/research/results/v4-study-035-selection.json').read_text())['cases'] if s['eligible'])
        source=json.loads(Path(selection['source']).read_text())
        result=audit.verify_branch(source,selection)
        control,treated=result['control'],result['ablation']
        self.assertEqual(control['initial']['individuals'],treated['initial']['individuals'])
        self.assertEqual(treated['initial']['energy_export'],123)
        self.assertEqual(treated['initial']['energy_after'],treated['initial']['energy_before']-123)
        self.assertNotIn(0,treated['initial']['site_ids'])
        self.assertIsNone(treated['initial']['individuals'][0]['death_tick'])
        self.assertEqual(treated['rows'][0]['tick'],selection['t0']+1)
        for row,old in zip(control['rows'],source['rows'][selection['t0']:]):
            self.assertEqual(row['physical'],old['physical'])
        altered=deepcopy(source)
        altered['rows'][selection['t0']]['physical']['units'][85]['energy']-=1
        with self.assertRaises(ValueError):audit.verify_branch(altered,selection)


if __name__ == '__main__': unittest.main()
