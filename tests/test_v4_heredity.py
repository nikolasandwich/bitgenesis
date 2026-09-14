import unittest
from bitgenesis.v4.local import Unit
from bitgenesis.v4.material import convert as baseline
from bitgenesis.v4.heredity import HeritableUnit, convert


class HeredityTests(unittest.TestCase):
    def test_all_directional_expression_and_copy_cost(self):
        for direction,target in enumerate((1,2,3,6)):
            units=[HeritableUnit(3,24,(0,1,2,3))]+[None]*8
            after,raw,row=convert(units,[1]*9,3,3,[direction]*9,[(999,0,1)]*9)
            self.assertEqual(after[target].material,direction)
            self.assertEqual(after[target].program,units[0].program)
            self.assertEqual(after[0].energy,10)
            self.assertEqual(after[target].energy,9)
            self.assertEqual(row['spent'],5)
            self.assertEqual((row['construction_spent'],row['copy_spent']),(4,1))
            self.assertEqual(units[0].energy,24)

    def test_expression_precedes_mutation_and_parent_unchanged(self):
        units=[HeritableUnit(3,40,(0,1,2,3))]+[None]*8
        after,raw,row=convert(units,[1]*9,3,3,[0]*9,[(0,0,2)]*9,mutation_per_thousand=1000)
        self.assertEqual(after[1].material,0)
        self.assertEqual(after[1].program,(2,1,2,3))
        self.assertEqual(after[0].program,(0,1,2,3))
        # The inherited change is expressed when that child forms its own child.
        isolated=[None]*9
        isolated[1]=HeritableUnit(after[1].material,24,after[1].program)
        future,_,_=convert(isolated,raw,3,3,[0]*9,[(999,0,1)]*9,mutation_per_thousand=0)
        self.assertEqual(future[2].material,2)

    def test_constant_program_projection_matches_old_conversion(self):
        physical=[Unit(2,24),None,Unit(1,0)]+[None]*6
        units=[None if u is None else HeritableUnit(u.material,u.energy,(u.material,)*4) for u in physical]
        expected,raw,old=baseline(physical,[1]*9,3,3,[0]*9)
        actual,stock,row=convert(units,[1]*9,3,3,[0]*9,[(0,0,1)]*9,copy_cost=0,mutation_per_thousand=0)
        self.assertEqual([None if u is None else Unit(u.material,u.energy) for u in actual],expected)
        self.assertEqual(stock,raw)
        self.assertEqual(row['spent'],old['spent'])

    def test_failed_proposals_do_not_charge_copy_or_mutate(self):
        units=[HeritableUnit(0,24,(0,0,0,0)),None,HeritableUnit(1,24,(1,1,1,1))]+[None]*6
        directions=[0]*9
        directions[2]=1
        after,_,row=convert(units,[1]*9,3,3,directions,[(0,0,1)]*9,mutation_per_thousand=1000)
        self.assertEqual(after,units)
        self.assertEqual(row['copy_spent'],0)
        self.assertTrue(all(p['reason']=='collision' for p in row['proposals']))
        with self.assertRaises(ValueError):
            HeritableUnit(0,10,[0,0,0,0])
        with self.assertRaises(ValueError):
            convert(units,[1]*9,3,3,directions,[(0,0,0)]*9)
        with self.assertRaises(ValueError):
            convert(units,[1]*9,3,3,directions,[(0,0,1)]*9,threshold=6)
