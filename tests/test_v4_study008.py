import unittest
from fractions import Fraction
from itertools import product
from scripts.verify_v4_study008 import aggregate, LAYOUTS


class Study008Tests(unittest.TestCase):
    def test_source_paired_layout_differences_and_missing_observation(self):
        rows=[]
        offsets={'adjacent':Fraction(1,4),'intermediate':Fraction(-1,8),'separated':Fraction()}
        for seed,td,mutation,drive,layout,desc,env in product(range(96000,96005),(250,500),(0,100),(250,500),LAYOUTS,range(3),(101000,101001)):
            value=Fraction(seed-96000,10)+offsets[layout]
            rows.append(dict(source_seed=seed,training_drive=td,training_mutation=mutation,drive=drive,
                layout=layout,descendant_id=desc,environment=env,difference=str(value)))
        sources,groups,paired,contrasts=aggregate(rows)
        self.assertEqual((len(sources),len(groups),len(paired),len(contrasts)),(120,24,80,16))
        for row in groups:
            self.assertEqual(Fraction(row['mean']),Fraction(1,5)+offsets[row['layout']])
        for row in contrasts:
            self.assertEqual(Fraction(row['mean']),offsets[row['layout']])
        with self.assertRaises(ValueError):
            aggregate(rows[:-1])
        with self.assertRaises(ValueError):
            aggregate(rows+[dict(rows[0],layout='unknown')])
        with self.assertRaises(ValueError):
            aggregate(rows[:-1]+[rows[0]])
