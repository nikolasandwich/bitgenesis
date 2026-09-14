import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v2.development import DevelopmentGenome
from bitgenesis.v3.assay import run_assay,select_target
from bitgenesis.v3.genome import EcologyGenome
from bitgenesis.v3.world import Config


class AssayTests(unittest.TestCase):
    def test_prefix_selection_tie_and_no_partner(self):
        final=dict(lineage=[dict(id=i,founder=i,death_tick=None) for i in (0,1)])
        steps=[dict(actors=[dict(id=i,feeding=dict(released_b=2)) for i in (1,0)])]
        self.assertEqual(select_target(final,steps)['target'],0)
        final['lineage'][1]['death_tick']=3
        self.assertIsNone(select_target(final,steps)['target'])

    def test_full_engineering_assay_and_unavailable_case(self):
        genome=EcologyGenome(DevelopmentGenome((6,100,0,0,0,0,0,0,1,1)),16)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=Config(width=5,height=5,founders=2,initial_energy=400,birth_threshold=160)
            result=run_assay(root/'available',config,85700,3,10,founder_genomes=[genome]*2)
            self.assertEqual(result['selection']['status'],'available')
            for name in ('intact','removed','replayed'):
                self.assertTrue((root/'available'/(name+'-verification.json')).exists())
                self.assertEqual((root/'available'/name/'initial.json').read_bytes(),
                                 (root/'available/prefix/final.json').read_bytes())
            result=run_assay(root/'unavailable',Config(width=3,height=3,founders=1),85701,3,10,
                             founder_genomes=[genome])
            self.assertIsNone(result['outcomes'])
            meta=json.loads((root/'unavailable/metadata.json').read_text())
            self.assertEqual(meta['outcome'],'unavailable')
            self.assertFalse((root/'unavailable/intact').exists())


if __name__=='__main__':
    unittest.main()
