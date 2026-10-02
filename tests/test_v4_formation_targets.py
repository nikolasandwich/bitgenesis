import unittest
from scripts.analyze_v4_formation_targets import preformation, ledger, analyze_pair


class FormationTargetTests(unittest.TestCase):
    def test_rescued_target_and_death_birth_same_site(self):
        off=[dict(energy=16),dict(energy=0)]+[None]*7
        on=[dict(energy=16),dict(energy=1)]+[None]*7
        a=preformation(off,[0]*9,[0]*9,3,3,16)
        b=preformation(on,[0]*9,[0]*9,3,3,16)
        self.assertEqual(a['reason'][0],'formed')
        self.assertEqual(b['reason'][0],'occupied')
        self.assertEqual(a['raw'][1],1)
        self.assertEqual(a['dead'],[1])
        self.assertEqual(a['candidates'][1],[0])

    def test_threshold_and_collision_change(self):
        u=[dict(energy=16),None,dict(energy=15)]+[None]*6
        raw=[0,1]+[0]*7; directions=[0,0,1]+[0]*6
        self.assertEqual(preformation(u,raw,directions,3,3,16)['reason'][0],'formed')
        u[2]['energy']=16
        state=preformation(u,raw,directions,3,3,16)
        self.assertEqual(state['reason'][0],'collision')
        self.assertEqual(state['candidates'][1],[0,2])

    def test_gross_net_and_boundary(self):
        u=[dict(energy=8),dict(energy=8),dict(energy=8),dict(energy=1),dict(energy=7)]
        flows=ledger(u,[dict(donor=0,recipient=1,amount=1),dict(donor=1,recipient=2,amount=1)])
        self.assertEqual(flows[1],dict(gross_in=1,gross_out=1,net=0))
        self.assertEqual(flows[3],dict(gross_in=0,gross_out=0,net=0))
        for e in (1,7):
            with self.assertRaises(ValueError):
                ledger([dict(energy=e),dict(energy=8)],[dict(donor=0,recipient=1,amount=1)])

    def test_pair_full_coverage_and_saved_reason_tamper(self):
        origin=dict(units=[dict(energy=8),dict(energy=8)]+[None]*7,raw=[0]*9)
        arm=dict(interaction_units=origin['units'],directions=[0]*9,driven=dict(interaction=dict(transfers=[])),material=dict(dissolved=[],proposals=[dict(source=0,reason='energy'),dict(source=1,reason='energy')]))
        pair=dict(tick=101,on=arm,off=arm)
        answer=analyze_pair(origin,pair,dict(width=3,height=3,threshold=16))
        self.assertEqual(answer['counts']['actors'],2)
        self.assertEqual(answer['counts']['flow:gross_zero:actors'],2)
        self.assertEqual(len([k for k in answer['counts'] if k.startswith('reason:')]),36)
        arm['material']['proposals'][0]['reason']='formed'
        with self.assertRaises(ValueError): analyze_pair(origin,pair,dict(width=3,height=3,threshold=16))

    def test_saved_rescue_evidence_does_not_use_final_occupancy(self):
        origin=dict(units=[dict(energy=16),dict(energy=1),dict(energy=8)]+[None]*6,raw=[0]*9)
        def arm(energies,reasons,dead,transfers):
            units=[dict(energy=e) for e in energies]+[None]*6
            return dict(interaction_units=units,units=[dict(energy=4)]*9,directions=[0]*9,driven=dict(interaction=dict(transfers=transfers)),material=dict(dissolved=dead,proposals=[dict(source=i,reason=r) for i,r in enumerate(reasons) if r!='dissolved']))
        pair=dict(tick=101,off=arm([16,0,8],['formed','dissolved','energy'],[1],[]),on=arm([16,1,7],['occupied','energy','energy'],[],[dict(donor=2,recipient=1,amount=1)]))
        out=analyze_pair(origin,pair,dict(width=3,height=3,threshold=16))
        rec=out['records'][0]
        self.assertEqual(rec['off']['target_raw'],1)
        self.assertTrue(rec['off']['target_dissolved'])
        self.assertFalse(rec['off']['target_occupied'])
        self.assertEqual(out['counts']['occupied_rescue_match'],1)
        self.assertEqual(out['counts']['avoided_zero'],1)

    def test_candidate_change_saved_with_energy_and_flows(self):
        origin=dict(units=[dict(energy=16),None,dict(energy=15),None,None,dict(energy=8)]+[None]*3,raw=[0,1]+[0]*7)
        def arm(e2,e5,reasons,transfers):
            units=[dict(energy=16),None,dict(energy=e2),None,None,dict(energy=e5)]+[None]*3
            return dict(interaction_units=units,directions=[0,0,1]+[0]*6,driven=dict(interaction=dict(transfers=transfers)),material=dict(dissolved=[],proposals=[dict(source=i,reason=r) for i,r in zip((0,2,5),reasons)]))
        pair=dict(tick=101,off=arm(15,8,['formed','energy','energy'],[]),on=arm(16,7,['collision','collision','energy'],[dict(donor=5,recipient=2,amount=1)]))
        out=analyze_pair(origin,pair,dict(width=3,height=3,threshold=16))
        rec=out['records'][0]
        self.assertEqual(rec['extra_candidates'],dict(on=[2],off=[]))
        self.assertEqual(rec['candidate_evidence'][1],dict(actor=2,on_energy=16,off_energy=15,flow=dict(gross_in=1,gross_out=0,net=1)))

    def test_input_binding_omission_rejected_before_snapshot(self):
        from unittest.mock import patch
        from pathlib import Path
        from scripts.analyze_v4_formation_targets import input_bindings
        meta=dict(status='complete',completed_pairs=4000,completed_sources=10,bindings_sha256={},source_bindings_sha256={})
        with patch('scripts.analyze_v4_formation_targets.read',side_effect=[meta,[],{}]), patch('scripts.verify_v4_study012_summary.expected_bindings',return_value=({Path('required')},set())):
            with self.assertRaisesRegex(ValueError,'binding inventory'):input_bindings()

    def test_failure_metadata_and_exclusive_directory(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts import analyze_v4_formation_targets as analyzer
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'targets'
            with patch.object(analyzer,'OUTPUT',output), patch.object(analyzer.subprocess,'check_output',side_effect=['','test-commit']), patch.object(analyzer,'input_bindings',side_effect=ValueError('input changed')):
                with self.assertRaisesRegex(ValueError,'input changed'):analyzer.main()
            metadata=json.loads((output/'metadata.json').read_text())
            self.assertEqual(metadata['status'],'failed')
            self.assertIn('input changed',metadata['error'])
            before=(output/'metadata.json').read_bytes()
            with patch.object(analyzer,'OUTPUT',output),patch.object(analyzer.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):analyzer.main()
            self.assertEqual((output/'metadata.json').read_bytes(),before)
