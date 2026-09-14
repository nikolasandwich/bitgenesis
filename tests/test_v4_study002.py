import unittest
from scripts.verify_v4_study002 import spatial, windows


class Study002Tests(unittest.TestCase):
    def test_spatial_wrap_material_and_empty(self):
        units=[None]*16
        self.assertEqual(spatial(units,4,4),(0,0))
        for i in (0,3,12):
            units[i]=dict(material=0,energy=1)
        units[1]=dict(material=1,energy=1)
        units[10]=dict(material=0,energy=1)
        self.assertEqual(spatial(units,4,4),(3,3))

    def test_exact_windows_and_missing_ticks(self):
        rows=[]
        for tick in range(1,301):
            units=[None]*256
            if tick==101:
                units[0]=dict(material=1,energy=1)
            rows.append(dict(tick=tick,units=units,imported=0,rejected_import=0,
                material=dict(proposals=[],dissolved=[],spent=0),
                driven=dict(leakage=0,interaction=dict(spent=0))))
        a,b=windows(rows)
        self.assertEqual(a['occupied_fraction'],'0')
        self.assertEqual(b['occupied_fraction'],'1/51200')
        self.assertEqual(b['mean_largest_spatial_component'],'1/200')
        with self.assertRaises(ValueError):
            windows(rows[:-1])
        rows[-1]['tick']=299
        with self.assertRaises(ValueError):
            windows(rows)
