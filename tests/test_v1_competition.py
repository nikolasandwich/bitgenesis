import json
from pathlib import Path
import tempfile
import unittest
from random import Random

from bitgenesis.v1.competition import compete
from bitgenesis.v1.controller import Genome
from bitgenesis.v1.world import Config


class CompetitionTests(unittest.TestCase):
    def test_neutral_swaps_reproduce_physics_and_complement_groups(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            config=Config(width=5,height=5,founders=8,mutation_per_thousand=0)
            results=[compete(root/str(s),config,70400,40,Genome((0,)*35),'intact',s) for s in (0,1)]
            for name in ('initial.json','steps.jsonl','events.jsonl','final.json','summary.json'):
                self.assertEqual((root/'0'/name).read_bytes(),(root/'1'/name).read_bytes())
            self.assertEqual(results[0]['groups']['intact'],results[1]['groups']['control'])
            self.assertEqual(results[0]['groups']['control'],results[1]['groups']['intact'])

    def test_mixed_modes_and_both_extinct_fraction(self):
        with tempfile.TemporaryDirectory() as directory:
            for i,control in enumerate(('blind','shuffled')):
                root=Path(directory)/str(i)
                config=Config(width=5,height=5,founders=8,initial_energy=1,mutation_per_thousand=0)
                result=compete(root,config,70401,3,Genome((0,)*35),control)
                self.assertEqual(result['status'],'both_extinct')
                self.assertIsNone(result['intact_fraction'])
                self.assertEqual(result['contrast'],'0')
                initial=json.loads((root/'initial.json').read_text())
                self.assertEqual([o['mode'] for o in initial['lineage']],['intact']*4+[control]*4)

    def test_mixed_surviving_decisions_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Config(width=5,height=5,founders=8,initial_energy=80,mutation_per_thousand=0)
            result=compete(Path(directory)/'run',config,70402,30,Genome.random(Random(1)),'shuffled')
            self.assertGreater(result['verification']['decisions'],0)
            self.assertEqual(sum(g['population']+g['deaths']-g['births'] for g in result['groups'].values()),8)
