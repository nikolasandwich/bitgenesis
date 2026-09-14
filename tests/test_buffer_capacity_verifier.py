import unittest
from scripts.summarize_v0_buffer_capacity import INITIAL,verify_rows,window_observations


class BufferCapacityVerifierTests(unittest.TestCase):
    def test_capacity_specific_food_bound(self):
        # Aggregate accounting fixture, not a claim of spatial realizability.
        rows=[dict(INITIAL)]
        for tick in (1,2):
            rows.append({**INITIAL,'tick':tick,'food_energy':5120+12288*tick,
                'supplied_energy':7040+12288*tick,'organism_energy':1920-80*tick,
                'dissipated_energy':80*tick})
        verify_rows(rows,12,96,steps=2)
        with self.assertRaisesRegex(ValueError,'Energy accounting'):
            verify_rows(rows,12,24,steps=2)
        with self.assertRaises(ValueError):verify_rows(rows,12,True,steps=2)

    def test_extinction_window_includes_extinction_tick(self):
        rows=[dict(INITIAL),{**INITIAL,'tick':1,'population':0,'supplied_energy':7100,'food_energy':5180},
              {**INITIAL,'tick':2,'population':0,'supplied_energy':7140,'food_energy':5220}]
        result=window_observations(rows)
        self.assertEqual(result['active_start_ticks'],1)
        self.assertEqual(result['empty_start_ticks'],1)
        self.assertEqual(result['resources_added_during_active_start_ticks'],60)
        self.assertEqual(result['resources_added_after_extinction'],40)
        rows[-1]['population']=1;rows[1]['population']=1
        result=window_observations(rows)
        self.assertEqual(result['active_start_ticks'],2)
        self.assertEqual(result['resources_added_after_extinction'],0)
