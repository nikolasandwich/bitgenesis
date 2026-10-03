import unittest
from scripts.verify_v4_copy_ablation import aggregate,verify_case


def summaries():
    rows=[]
    for seed in range(120000,120020):
        for mode in ('random-direction','random-feed','random-both'):
            for exchange in (False,True):
                success=seed%4==0 or seed%4==1 and exchange or seed%4==2 and not exchange
                rows.append(dict(seed=seed,mode=mode,exchange=exchange,steps=32,births=4,deaths=2,living=5,initial_energy=192,final_energy=180,imported=100,rejected_import=924,spent=112,proposed=1024,initial_mass=7,final_mass=7,genetic_counts=[2 if success else 0]*32,episodes=[[1,32]] if success else [],longest=32 if success else 0,persistent10=success,ever=success))
    return rows

class AggregationTests(unittest.TestCase):
    def test_paired_four_outcomes(self):
        s=aggregate(summaries())
        for g in s['groups']:
            self.assertEqual({k:g[k] for k in ('on_only','off_only','both','neither')},dict(on_only=5,off_only=5,both=5,neither=5))
            self.assertEqual(g['mean_difference'],'0')
        for c in s['cells']:self.assertEqual(c['success_fraction'],'1/2')
    def test_missing_duplicate_bad_bool_and_accounting(self):
        for mutate in (lambda r:r.pop(),lambda r:r.__setitem__(0,r[1]),lambda r:r[0].__setitem__('exchange',0),lambda r:r[0].__setitem__('imported',101)):
            rows=summaries();mutate(rows)
            with self.assertRaises((AssertionError,ValueError)):aggregate(rows)

class PhysicalReplayTests(unittest.TestCase):
    def test_all_modes_and_input_tampering(self):
        from scripts.run_v4_copy_ablation import run_case
        from copy import deepcopy
        for mode in ('random-direction','random-feed','random-both'):
            for exchange in (False,True):
                c=run_case(120000,mode,exchange)
                self.assertEqual(verify_case(c),c['summary'])
                for field in ('direction','feed','identity','summary'):
                    bad=deepcopy(c)
                    if field=='direction':bad['rows'][0]['physical']['directions'][0]=(bad['rows'][0]['physical']['directions'][0]+1)%4
                    elif field=='feed':bad['rows'][0]['physical']['driven']['inputs'][0]['proposed']+=8
                    elif field=='identity':bad['rows'][0]['site_ids'][85]=999
                    else:bad['summary']['longest']+=1
                    with self.assertRaises((AssertionError,ValueError)):verify_case(bad)
