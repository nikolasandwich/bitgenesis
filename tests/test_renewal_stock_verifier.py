import copy
from pathlib import Path
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_renewal_granularity import initialize,REGIMES
from scripts.observe_v0_renewal_stocks import capture,reconcile
from scripts.verify_v0_renewal_stocks import verify_record


class RenewalStockVerifierTests(unittest.TestCase):
    def fixture(self,renewal):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        w=initialize(base,'block',40,renewal,23)
        before=w.snapshot();row=capture(w);w.step();after=w.snapshot()
        return {**reconcile(row,before,after),'before_metrics':before,'after_metrics':after},before,after

    def test_registered_regimes_reconstruct(self):
        for renewal in REGIMES:
            row,before,after=self.fixture(renewal)
            verify_record(row,before,after,renewal)

    def test_histogram_fraction_and_discard_corruption_rejected(self):
        row,before,after=self.fixture('rare-large')
        for field in ('histogram','expected_cap_loss','discarded_energy','after_metrics'):
            bad=copy.deepcopy(row)
            if field=='histogram':bad[field][0]+=1
            elif field=='expected_cap_loss':bad[field]='999'
            elif field=='after_metrics':bad[field]['births']+=1
            else:bad[field]+=1
            with self.subTest(field=field),self.assertRaises(ValueError):
                verify_record(bad,before,after,'rare-large')
