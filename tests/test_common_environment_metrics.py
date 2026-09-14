from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_common_environment import initialize,evaluate
from scripts.verify_v0_common_environment_metrics import initial_gate,metric_gate,read_metrics


class CommonMetricTests(unittest.TestCase):
    def test_assigned_trait_is_checked_before_account_normalization(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for trait in (0,250,1000):
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'world'
                result=evaluate(initialize(base,23,trait),out,100,dict(founder_trait=trait))
                initial=json.loads((out/'initial.json').read_text());rows=read_metrics(out/'metrics.csv')
                initial_gate(initial,23,trait);self.assertEqual(metric_gate(rows,trait,100),result['extinction_tick'])
                other=250 if trait!=250 else 256
                with self.assertRaises(ValueError):initial_gate(initial,23,other)
                with self.assertRaises(ValueError):metric_gate(rows,other,100)
                bad=deepcopy(initial);bad['founders'][0]['genome']=other
                with self.assertRaises(ValueError):initial_gate(bad,23,trait)
                bad=deepcopy(rows);bad[1]['changed_births']=1
                with self.assertRaises(ValueError):metric_gate(bad,trait,100)
                bad=deepcopy(rows);bad[1]['supplied_energy']+=1
                with self.assertRaises(ValueError):metric_gate(bad,trait,100)


if __name__=='__main__':unittest.main()
