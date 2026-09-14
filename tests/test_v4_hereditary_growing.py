import random
import unittest
from bitgenesis.v4.local import Unit
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.growing import step as baseline


class HereditaryGrowingTests(unittest.TestCase):
    def test_multistep_baseline_projection(self):
        rng=random.Random(95000)
        physical=[Unit(rng.randrange(4),rng.randrange(65)) if rng.randrange(2) else None for _ in range(25)]
        units=[None if u is None else HeritableUnit(u.material,u.energy,(u.material,)*4) for u in physical]
        raw=stock=[1]*25
        for _ in range(50):
            proposals=[rng.randrange(9) for _ in units]
            directions=[rng.randrange(4) for _ in units]
            tickets=[(rng.randrange(1000),rng.randrange(4),rng.randrange(1,4)) for _ in units]
            physical,raw,old=baseline(physical,raw,5,5,proposals,directions)
            units,stock,row=step(units,stock,5,5,proposals,directions,tickets,copy_cost=0,mutation_per_thousand=0)
            self.assertEqual([None if u is None else Unit(u.material,u.energy) for u in units],physical)
            self.assertEqual(raw,stock)
            self.assertEqual(row['spent'],old['spent'])
            self.assertEqual(row['interaction_components'],old['interaction_components'])

    def test_program_survives_interaction_and_mutation_is_local(self):
        units=[HeritableUnit(0,32,(1,2,3,0))]+[None]*8
        result,stock,row=step(units,[1]*9,3,3,[8]*9,[0]*9,[(0,2,1)]*9,mutation_per_thousand=1000)
        self.assertEqual(row['interaction_units'][0]['program'],(1,2,3,0))
        self.assertEqual(result[0].program,(1,2,3,0))
        self.assertEqual(result[1].material,1)
        self.assertEqual(result[1].program,(1,2,0,0))
        self.assertEqual(row['spent'],6)
        self.assertEqual(row['material']['copy_spent'],1)
        self.assertEqual(row['energy_before']+row['imported']-row['spent'],row['energy_after'])

    def test_random_programs_keep_per_site_material_and_energy(self):
        rng=random.Random(95001)
        units=[HeritableUnit(rng.randrange(4),rng.randrange(65),tuple(rng.randrange(4) for _ in range(4)))
               if rng.randrange(2) else None for _ in range(16)]
        raw=[1]*16
        mass=[1+(u is not None) for u in units]
        energy=sum(u.energy for u in units if u is not None)
        for _ in range(100):
            units,raw,row=step(units,raw,4,4,[rng.randrange(17) for _ in units],
                [rng.randrange(4) for _ in units],[(rng.randrange(1000),rng.randrange(4),rng.randrange(1,4)) for _ in units],
                mutation_per_thousand=500)
            energy+=row['imported']-row['spent']
            self.assertEqual([r+(u is not None) for r,u in zip(raw,units)],mass)
            self.assertEqual(sum(u.energy for u in units if u is not None),energy)
            self.assertTrue(all(u is None or 0<u.energy<=64 for u in units))
