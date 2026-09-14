import unittest
from bitgenesis.v4.local import Unit
from bitgenesis.v4.material import convert


class MaterialTests(unittest.TestCase):
    def test_local_formation_cost_and_no_newborn_cascade(self):
        units=[Unit(2,24)]+[None]*8
        raw=[1]*9
        after,remaining,row=convert(units,raw,3,3,[0]*9)
        self.assertEqual(after[:3],[Unit(2,10),Unit(2,10),None])
        self.assertEqual(remaining[1],0)
        self.assertEqual(len(row['proposals']),1)
        self.assertEqual(row['spent'],4)
        self.assertEqual(units[0].energy,24)
        self.assertEqual(raw,[1]*9)

    def test_collision_rejects_both_without_cost(self):
        units=[Unit(0,24),None,Unit(1,24)]+[None]*6
        directions=[0]*9
        directions[2]=1
        after,raw,row=convert(units,[1]*9,3,3,directions)
        self.assertEqual(after,units)
        self.assertEqual(row['spent'],0)
        self.assertEqual([p['reason'] for p in row['proposals']],['collision','collision'])

    def test_dissolution_returns_material_before_proposals(self):
        units=[Unit(2,24),Unit(3,0)]+[None]*7
        after,raw,row=convert(units,[0]*9,3,3,[0]*9)
        self.assertEqual(row['dissolved'],[1])
        self.assertEqual(after[1],Unit(2,10))
        self.assertEqual(sum(raw),0)
        self.assertEqual(row['material_before'],row['material_after'])

    def test_unavailable_resources_and_energy_stay_explicit(self):
        units=[Unit(2,24)]+[None]*8
        self.assertEqual(convert(units,[0]*9,3,3,[0]*9)[2]['proposals'][0]['reason'],'raw_material')
        units[0]=Unit(2,3)
        self.assertEqual(convert(units,[1]*9,3,3,[0]*9)[2]['proposals'][0]['reason'],'energy')
        with self.assertRaises(ValueError):
            convert(units,[1]*9,3,3,[0]*9,threshold=4)


if __name__=='__main__':
    unittest.main()
