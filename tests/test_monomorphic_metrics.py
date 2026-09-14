from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_monomorphic_mutation import initialize,record_world
from scripts.verify_v0_monomorphic_metrics import initial_gate,read_metrics,metric_gate


class MonomorphicMetricTests(unittest.TestCase):
    def test_real_recording_and_corrupt_accounts(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for mutation in (0,100):
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'run';result=record_world(initialize(base,23,mutation),out,100)
                initial=json.loads((out/'initial.json').read_text());initial_gate(initial,23,mutation)
                bad=deepcopy(initial);bad['founders'][0]['genome']=251
                with self.assertRaises(ValueError):initial_gate(bad,23,mutation)
                rows=read_metrics(out/'metrics.csv')
                self.assertEqual(metric_gate(rows,mutation,100),result['extinction_tick'])
                for key,value in [('food_energy',24577),('dissipated_energy',0),('changed_births',99999),('mean_genome',float('nan')),('tick',2)]:
                    bad=deepcopy(rows);bad[1][key]=value
                    with self.assertRaises(ValueError,msg=key):metric_gate(bad,mutation,100)
                with self.assertRaises(ValueError):metric_gate(rows[:-1],mutation,100)


if __name__=='__main__':unittest.main()
