"""Synthetic Study045 boundaries; saved-source science runs are separate."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from scripts import analyze_v4_middle_turnover as audit


def observation(tick, material=None, identity=None, genetic=True, whole=True):
    units=[None]*256; ids=[None]*256
    if identity is not None:
        units[101]=dict(material=material,energy=10,program=[0]*4);ids[101]=identity
    slot={k:True for k in audit.FLAGS}
    slot.update(occupied=genetic,material_match=genetic,genetic_match=genetic,whole_component=whole,
                sites=[85,86],identities=[3,4],components=[dict(sites=[85,86]),dict(sites=[85,86])])
    prior=dict(tick=tick,slots=[slot,dict(sites=[101,102],identities=ids[101:103]),deepcopy(slot)],new_copy_count=2 if whole and genetic else 0)
    return audit.snapshot(tick,ids,units,prior)


class TurnoverTests(unittest.TestCase):
    def test_nonzero_occupancy_is_not_empty_or_target_bridge(self):
        row=observation(31,material=3,identity=7)
        self.assertTrue(row['G']);self.assertFalse(row['physically_empty_both'])
        self.assertFalse(row['B101']);self.assertTrue(row['component_equivalence'])
        mismatch=observation(31,material=3,identity=7,genetic=False,whole=False)
        self.assertIsNone(mismatch['component_equivalence'])

    def test_diagnostic_immediate_exit_is_zero_length_left_censored(self):
        diagnostic=dict(tick=30,overlaps={'G':True})
        rows=[dict(tick=31,overlaps={'G':False}),dict(tick=32,overlaps={'G':True})]
        self.assertEqual(audit.intervals(diagnostic,rows,'G'),[
            dict(start=None,end=None,length=0,left_censored=True,right_censored=False,entry_tick=None,exit_tick=31),
            dict(start=32,end=32,length=1,left_censored=False,right_censored=True,entry_tick=32,exit_tick=None)])

    def test_all_gap_censoring_and_same_tick_replacement(self):
        people=[dict(identity=1,site=101,birth_tick=20,left_censored=True,birth_material=3,exit=dict(kind='death',tick=30)),
                dict(identity=2,site=101,birth_tick=30,left_censored=False,birth_material=0,exit=dict(kind='death',tick=31))]
        gaps=audit.gap_records(29,people)
        self.assertEqual(gaps[0]['empty_ticks'],[])
        self.assertTrue(gaps[0]['same_tick_replacement']);self.assertTrue(gaps[0]['material_changed'])
        self.assertEqual(gaps[1]['empty_ticks'],[31,32]);self.assertTrue(gaps[1]['right_censored'])
        self.assertEqual(gaps[1]['distance_ticks'],1)
        self.assertEqual(gaps[2]['empty_ticks'],[30,31,32]);self.assertTrue(gaps[2]['left_censored'])
        self.assertTrue(gaps[2]['right_censored'])
        births=[dict(identity=3,site=101,birth_tick=32,left_censored=False,birth_material=0,exit=dict(kind='endpoint',tick=32))]
        first=audit.gap_records(29,births)[0]
        self.assertEqual(first['empty_ticks'],[30,31]);self.assertEqual(first['distance_ticks'],3)

    def test_reuse_projects_existing_values_without_energy_recalculation(self):
        ledger=dict(rows=[dict(phase='birth',tick=30,end_energy=29),dict(phase='action',tick=31,reason='formed',preformation_energy=24,end_energy=10,child_transfer=9,proposal=dict(source=101,target=85,identity=8,child_id=9)),dict(phase='action',tick=32,reason='dissolved',end_energy=0)],window=dict(death_tick=32,right_censored=False))
        entry,successes,exit_event=audit.reuse_events(ledger)
        self.assertEqual(entry,dict(kind='birth',tick=30,energy=29))
        self.assertEqual(successes[0]['preformation_energy'],24)
        self.assertEqual(successes[0]['child_energy'],9)
        self.assertEqual(exit_event,dict(kind='death',tick=32,energy=0,right_censored=False))

    def test_full_zero_cells_and_numeric_paired_deltas(self):
        summary=audit.summarize([],[])
        self.assertEqual(len(summary['cells']),20)
        self.assertTrue(all(c['identities']==c['n']==c['ticks']['G']==0 for c in summary['cells']))
        self.assertEqual(audit.difference({'x':2,'y':{'z':0}},{'x':3,'y':{'z':1}}),{'x':-1,'y':{'z':-1}})

    def test_terminal_birth_same_tick_death_and_left_entry_energy(self):
        units=[None]*256;ids=[None]*256
        units[101]=dict(material=3,energy=64);units[117]=dict(material=0,energy=64)
        ids[101]=0;ids[117]=1
        old=dict(id=0,site=101,birth_tick=0,birth_energy=64,material=3,parent=None,death_tick=32)
        newborn=dict(id=2,site=101,birth_tick=32,birth_energy=29,material=0,parent=1,death_tick=None)
        end=deepcopy(units);end[101]=dict(material=0,energy=29);end[117]['energy']=30
        after=list(ids);after[101]=2
        interaction=deepcopy(units);interaction[101]['energy']=0
        proposal=dict(source=117,target=101,reason='formed',child_energy=29,parent_energy=30,material=0)
        arm=dict(initial=dict(tick=31,units=units,site_ids=ids),rows=[dict(tick=32,site_ids=after,births=[newborn],deaths=[0],physical=dict(units=end,interaction_units=interaction,directions=[3]*256,material=dict(proposals=[proposal],dissolved=[101])))])
        entry,success,exit_event=audit.project_events(arm,old,True)
        self.assertEqual(entry['energy'],64)  # Historical entry is not limited by a newborn bound.
        self.assertEqual(success,[]);self.assertEqual(exit_event['energy'],0)
        entry,success,exit_event=audit.project_events(arm,newborn,False)
        self.assertEqual(entry,dict(kind='birth',tick=32,energy=29))
        self.assertEqual(success,[])  # Its site's prior identity acted/died; the child did not.
        self.assertEqual(exit_event,dict(kind='endpoint',tick=32,energy=29,right_censored=True))
        arm['rows'][0]['physical']['material']['proposals'].append(dict(source=101,target=85,reason='energy'))
        with self.assertRaisesRegex(ValueError,'death phase is not proposal'):
            audit.project_events(arm,old,True)

    def test_success_reads_saved_pre_parent_and_child_energy(self):
        units=[None]*256;ids=[None]*256
        units[101]=dict(material=0,energy=28);ids[101]=0
        person=dict(id=0,site=101,birth_tick=30,birth_energy=28,material=0,parent=None,death_tick=None)
        newborn=dict(id=1,site=85,birth_tick=32,birth_energy=10,material=0,parent=0,death_tick=None)
        end=deepcopy(units);end[101]['energy']=11;end[85]=dict(material=0,energy=10)
        after=list(ids);after[85]=1
        interaction=deepcopy(units);interaction[101]['energy']=26
        proposal=dict(source=101,target=85,reason='formed',child_energy=10,parent_energy=11,material=0)
        arm=dict(initial=dict(tick=31,units=units,site_ids=ids),rows=[dict(tick=32,site_ids=after,births=[newborn],deaths=[],physical=dict(units=end,interaction_units=interaction,material=dict(proposals=[proposal],dissolved=[])))])
        _,success,exit_event=audit.project_events(arm,person,True)
        self.assertEqual(success,[dict(tick=32,source=101,target=85,parent_identity=0,child_identity=1,preformation_energy=26,parent_energy=11,child_energy=10)])
        self.assertEqual(exit_event['energy'],11)

    def test_material_anomaly_and_arm_identity_isolation_are_retained(self):
        units=[None]*256;ids=[None]*256
        units[101]=dict(material=3,energy=10);ids[101]=0
        person=dict(id=0,site=101,birth_tick=0,birth_energy=64,material=3,parent=None,death_tick=None)
        after=deepcopy(units);after[101]=dict(material=1,energy=9)
        selection=dict(seed=120000,t0=31,offspring_ids=[],category='short_window')
        row=dict(tick=32,site_ids=ids,births=[],deaths=[],physical=dict(units=after,interaction_units=after,material=dict(proposals=[],dissolved=[])))
        arm=dict(initial=dict(tick=31,units=units,site_ids=ids),rows=[row],final=dict(individuals=[person]),new_copy_counts=[0],episodes=[],metrics=dict(longest_double=0,double_new_ever=0,persistent10=0))
        branch=dict(selection=selection,control=arm,ablation=deepcopy(arm))
        slot={k:False for k in audit.FLAGS}
        def oldrow(t):return dict(tick=t,slots=[slot,dict(sites=[101,102],identities=[0,None]),slot],new_copy_count=0)
        old=dict(diagnostic=oldrow(31),rows=[oldrow(32)],prior043=dict(new_copy_counts=[0],episodes=[],matched=True))
        prior=dict(encoding='east',selection=selection,arms={a:deepcopy(old) for a in audit.ARMS})
        census=[dict(encoding='east',seed=120000,arm=a,t0=31,saved_states=1,energy_plan='needed_event_projection',identities=[dict(identity=0,site=101,parent=None,birth_tick=0,left_censored=True)]) for a in audit.ARMS]
        result=audit.analyze_pair('east',branch,prior,census,[],[])
        left,right=(result['arms'][a] for a in audit.ARMS)
        self.assertNotEqual(left['identities'][0]['key'],right['identities'][0]['key'])
        self.assertEqual(left['identities'][0]['birth_material'],3)
        self.assertEqual(left['material_anomalies'],[dict(tick=32,site=101,identity=0,birth_material=3,observed_material=1)])
        self.assertFalse(left['transitions'][0]['identity_changed'])
        self.assertTrue(left['transitions'][0]['material_changed'])
        self.assertTrue(left['rows'][0]['G']);self.assertFalse(left['rows'][0]['physically_empty_both'])

    def test_budget_failure_is_retained(self):
        from scripts import middle_turnover_inputs as inputs
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'audit'
            with patch.object(audit,'OUTPUT',output),patch.object(audit.subprocess,'check_output',side_effect=['','commit']),patch.object(inputs,'input_paths',return_value=[]),patch.object(inputs,'capture',return_value=({},{})),patch.object(inputs,'bindings',return_value={}),patch.object(audit.time,'monotonic',side_effect=[0,601,602]):
                with self.assertRaisesRegex(ValueError,'bounded execution'):audit.main()
            metadata=inputs.read(output/'metadata.json')
            self.assertEqual(metadata['status'],'failed')
            self.assertEqual(metadata['input_sha256_after'],{})
            self.assertIn('bounded execution',metadata['error'])

    def test_run_failure_retains_inputs_after_and_exclusive_output(self):
        from scripts import middle_turnover_inputs as inputs
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'audit'
            with patch.object(audit,'OUTPUT',output),patch.object(audit.subprocess,'check_output',side_effect=['','commit']),patch.object(inputs,'input_paths',return_value=[]),patch.object(inputs,'capture',return_value=({},{})),patch.object(inputs,'bindings',side_effect=ValueError('source binding')):
                with self.assertRaisesRegex(ValueError,'source binding'):audit.main()
            metadata=inputs.read(output/'metadata.json')
            self.assertEqual(metadata['status'],'failed');self.assertEqual(metadata['input_sha256_after'],{})
            with patch.object(audit,'OUTPUT',output),patch.object(audit.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):audit.main()


if __name__=='__main__':unittest.main()
