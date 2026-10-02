import unittest
from itertools import product
from scripts.verify_v4_study016_summary import aggregate_saved,checkpoint_recount


def grid():
    metrics=('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')
    return [dict(history=h,seed=s,mutation=m,exchange=e,status='complete',anchor=100,horizon=400,checkpoints={str(t):dict(occupied=s-112000+(t//100 if e else 0),components=dict(initial_components=0,eligible_components=0,fractions={k:None for k in metrics})) for t in (100,200,300,400)}) for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False))]


class HorizonVerifierTests(unittest.TestCase):
    def test_one_anchor_not_average_over_checkpoints(self):
        s=aggregate_saved(grid())
        self.assertEqual(len(s['pairs']),20);self.assertEqual(len(s['cells']),32);self.assertEqual(len(s['groups']),16)
        self.assertEqual(s['cells'][0]['metrics']['occupied'],dict(mean='3',available=5,missing=0))
        self.assertEqual(s['groups'][3]['metrics']['occupied'],dict(mean='4',available=5,missing=0))
        self.assertEqual(s['groups'][3]['metrics']['replacement'],dict(mean=None,available=0,missing=5))

    def test_missing_failed_or_wrong_horizon_rejected(self):
        rows=grid()
        for bad in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises((ValueError,AssertionError)):aggregate_saved(bad)
        for field,value in (('history',1),('status','failed'),('anchor',200),('horizon',100)):
            rows=grid();rows[0][field]=value
            with self.assertRaises((ValueError,AssertionError)):aggregate_saved(rows)

    def test_late_replacement_and_reclosure_distinguished(self):
        initial={'observation':{'components':{'material':[[0,1],[2]]}}}
        final={'parents':[None,None,None,0,3]}
        rows=[dict(tick=1,observation={'components':{'material':[[0,3],[2]]}}),dict(tick=2,observation={'components':{'material':[[3,4],[2]]}})]
        result=checkpoint_recount(initial,rows,final,(1,2))
        self.assertFalse(result['1'][0]['primary']);self.assertTrue(result['2'][0]['primary'])
        rows[0]['observation']['components']['material']=[[0],[1],[2]]
        final['parents']=[None,None,None,0,1]
        result=checkpoint_recount(initial,rows,final,(1,2))
        self.assertTrue(result['2'][0]['complete_replacement']);self.assertFalse(result['2'][0]['primary'])

    def test_checkpoint_boolean_integer_alias_is_rejected(self):
        from scripts.verify_v4_study016_summary import checkpoint_index
        rows=[dict(history=h,seed=s,mutation=m,exchange=e,records={}) for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False))]
        self.assertEqual(len(checkpoint_index(rows)),40)
        rows[0]['history']=1
        with self.assertRaises((ValueError,AssertionError)):checkpoint_index(rows)
        rows[0]['history']=True;rows[0]['exchange']=1
        with self.assertRaises((ValueError,AssertionError)):checkpoint_index(rows)
