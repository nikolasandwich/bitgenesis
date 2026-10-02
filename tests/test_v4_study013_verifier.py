import unittest
from scripts.verify_v4_study013_summary import recount, total, canonical_source


class ImmediateVerifierTests(unittest.TestCase):
    def test_net_zero_preserves_opposite_actor_changes(self):
        units=[{'energy':16},{'energy':5},None]
        def arm(formed,energies):
            return dict(material=dict(dissolved=[],proposals=[dict(source=i,reason='formed' if i==formed else 'energy') for i in range(2)]),
                interaction_units=[{'energy':x} for x in energies]+[None],units=[{}, {}, {}])
        r=recount(units,arm(0,[16,5]),arm(1,[5,16]),16)
        self.assertEqual(r['differences']['births'],0)
        self.assertEqual((r['birth_gains'],r['birth_losses']),(1,1))
        self.assertEqual(sum(map(sum,r['actor_matrix'])),2)
        self.assertEqual(r['counts']['on']['energy_eligible'],1)
        s=total([r,r]);self.assertEqual(s['steps'],2)
        self.assertEqual(s['means']['births'],'0')
        self.assertEqual(s['step_signs']['births'],dict(positive=0,zero=2,negative=0))

    def test_missing_actor_and_threshold_disagreement_rejected(self):
        units=[{'energy':20}]
        arm=dict(material=dict(dissolved=[],proposals=[]),interaction_units=[{'energy':20}],units=[{}])
        with self.assertRaises(ValueError):recount(units,arm,arm,16)
        arm['material']['proposals']=[dict(source=0,reason='energy')]
        with self.assertRaisesRegex(ValueError,'eligibility'):recount(units,arm,arm,16)

    def test_alternate_source_path_rejected(self):
        from pathlib import Path
        row=dict(seed=96000,drive=250,mutation=0)
        expected=Path('data/v4-study-005/seed-96000-drive-250-mutation-0')
        self.assertEqual(canonical_source(str(expected.resolve()),row),expected.resolve())
        with self.assertRaisesRegex(ValueError,'canonical historical source'):
            canonical_source('/tmp/alternate-valid-source',row)
