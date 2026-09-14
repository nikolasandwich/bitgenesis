import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v4.growing_runner import run as growing_run
from bitgenesis.v4.branches import run


class BranchTests(unittest.TestCase):
    def test_sham_equals_continuous_and_removal_preserves_tickets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90800,steps=10,width=4,height=4)
            growing_run(root/'continuous',90800,steps=20,width=4,height=4)
            original=(root/'prefix/final.json').read_bytes()
            for name,sites,threshold in (('sham',[],None),('removed',[0,1,4,5],None),('disabled',[0,1,4,5],65)):
                summary=run(root/name,root/'prefix',10,sites,threshold)
                self.assertEqual(summary['initial_energy']+summary['imported']-summary['spent'],summary['final_energy'])
                self.assertEqual(summary['initial_material'],summary['final_material'])
            self.assertEqual((root/'sham/final.json').read_bytes(),(root/'continuous/final.json').read_bytes())
            continuous=(root/'continuous/steps.jsonl').read_bytes().splitlines(keepends=True)[10:]
            self.assertEqual((root/'sham/steps.jsonl').read_bytes(),b''.join(continuous))
            reference=json.loads((root/'sham/final.json').read_text())
            for name in ('removed','disabled'):
                final=json.loads((root/name/'final.json').read_text())
                for key in ('drive_rng','direction_rng'):
                    self.assertEqual(final[key],reference[key])
            self.assertEqual((root/'prefix/final.json').read_bytes(),original)
            self.assertEqual(json.loads((root/'disabled/summary.json').read_text())['formations'],0)

    def test_zero_horizon_and_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            growing_run(root/'prefix',90801,steps=0,width=3,height=3)
            for kwargs in ({'sites':[0,0]},{'threshold':False},{'max_site_records':1}):
                with self.assertRaises(ValueError):
                    run(root/'bad',root/'prefix',0,**kwargs)
                self.assertFalse((root/'bad').exists())
            summary=run(root/'zero',root/'prefix',0,sites=[0,1])
            self.assertEqual(summary['formations'],0)
            self.assertEqual(summary['initial_energy'],summary['final_energy'])
            self.assertEqual((root/'zero/steps.jsonl').read_bytes(),b'')
            with self.assertRaises(FileExistsError):
                run(root/'zero',root/'prefix',0)
