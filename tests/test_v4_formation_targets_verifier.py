import unittest
from scripts.verify_v4_formation_targets import flow_ledger, before_formation


class TargetVerifierTests(unittest.TestCase):
    def test_gross_zero_and_throughflow_are_distinct(self):
        units=[dict(energy=8),dict(energy=8),dict(energy=8)]
        transfers=[dict(donor=0,recipient=1,amount=1),dict(donor=1,recipient=2,amount=1)]
        flow=flow_ledger(units,transfers)
        self.assertEqual(flow[1],dict(gross_in=1,gross_out=1,net=0))
        self.assertEqual(flow[0]['net'],-1)
        with self.assertRaises(ValueError):
            flow_ledger([dict(energy=7)], [dict(donor=0,recipient=0,amount=1)])

    def test_preformation_raw_and_collision(self):
        # Sites0 and2 both target1 after1 dissolves; final births are irrelevant.
        units=[None]*9
        units[0]=dict(energy=16);units[1]=dict(energy=0);units[2]=dict(energy=16)
        state=before_formation(units,[0]*9,[0,0,1,0,0,0,0,0,0],3,3,16)
        self.assertEqual(state['dead'],[1])
        self.assertEqual(state['raw'][1],1)
        self.assertEqual(state['candidates'][1],[0,2])
        self.assertEqual(state['reason'][0],'collision')
        self.assertEqual(state['reason'][2],'collision')

    def test_small_energy_cannot_be_drained_by_gross_flow(self):
        for energy in (1,7):
            with self.assertRaisesRegex(ValueError,'outflow bound'):
                flow_ledger([dict(energy=energy),dict(energy=0)],[dict(donor=0,recipient=1,amount=1)])
        flow=flow_ledger([dict(energy=8)]+[dict(energy=0)]*4,
                         [dict(donor=0,recipient=i,amount=1) for i in range(1,5)])
        self.assertEqual(flow[0]['gross_out'],4)
        self.assertGreater(8+flow[0]['net'],0)

    def test_invalid_direction_and_transfer_identity_rejected(self):
        with self.assertRaises(ValueError):
            before_formation([dict(energy=1)]+[None]*8,[0]*9,[-1]+[0]*8,3,3,16)
        with self.assertRaises(ValueError):
            flow_ledger([dict(energy=8),dict(energy=8)],[dict(donor=False,recipient=1,amount=1)])

    def test_unlisted_actor_rejected(self):
        from scripts.verify_v4_formation_targets import pair_evidence
        origin=dict(units=[None]*9,raw=[0]*9)
        arm=dict(interaction_units=[dict(energy=8)]+[None]*8,directions=[0]*9,
                 driven=dict(interaction=dict(transfers=[])),
                 material=dict(dissolved=[],proposals=[dict(source=0,target=1,reason='energy')]))
        with self.assertRaises(ValueError):
            pair_evidence(origin,dict(tick=101,on=arm,off=arm),dict(width=3,height=3,threshold=16))

    def test_input_inventory_omission_rejected(self):
        from unittest.mock import patch
        from pathlib import Path
        from scripts.verify_v4_formation_targets import checked_inputs
        meta=dict(status='complete',completed_pairs=4000,completed_sources=10,bindings_sha256={},source_bindings_sha256={})
        proof=dict(status='verified',pairs=4000,actors=973345,results_sha256='same',summary_sha256='same',verifier_sha256='same')
        with patch('scripts.verify_v4_formation_targets.read',side_effect=[meta,[],proof]),patch('scripts.verify_v4_formation_targets.digest',return_value='same'),patch('scripts.verify_v4_study012_summary.expected_bindings',return_value=({Path('required')},set())):
            with self.assertRaisesRegex(ValueError,'binding inventory'):checked_inputs()
