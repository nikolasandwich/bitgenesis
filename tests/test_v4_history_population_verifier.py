import copy
from itertools import product
import unittest
from scripts import verify_v4_history_population as verifier


class HistoryPopulationVerifierTests(unittest.TestCase):
    def grid(self):
        rows=[]
        for history,seed,mutation,anchor,exchange in product((True,False),range(112000,112005),(0,100),(100,200,300,400),(True,False)):
            initial=10 if history else 20
            path=[]
            for tick in range(101):
                births=tick*((1 if history else 2) if exchange else 0)
                path.append(dict(tick=tick,occupied=initial+births,births=births,deaths=0,original_survivors=initial,new_survivors=births))
            rows.append(dict(history=history,seed=seed,mutation=mutation,anchor=anchor,exchange=exchange,directory='unused',path=path))
        return rows

    def test_history_interaction_uses_effects_not_different_initial_counts(self):
        summary=verifier.independent_summary(self.grid())
        self.assertEqual(summary['histories']['on']['groups'][0]['path'][100]['metrics']['occupied']['difference'],'100')
        self.assertEqual(summary['histories']['off']['groups'][0]['path'][100]['metrics']['occupied']['difference'],'200')
        metric=summary['interaction']['groups'][0]['path'][100]['metrics']['occupied']
        self.assertEqual(metric,dict(on_history='100',off_history='200',difference='100',positive=20,zero=0,negative=0))
        self.assertEqual(summary['interaction']['pairs'][0]['path'][0]['differences']['occupied'],0)
        self.assertEqual(summary['interaction']['sources'][0]['path'][100]['differences']['occupied'],'100')

    def test_missing_repeated_nonboolean_and_invalid_paths_rejected(self):
        rows=self.grid()
        cases=[rows[:-1],rows[:-1]+[rows[0]]]
        for key in ('history','exchange'):
            bad=copy.deepcopy(rows);bad[0][key]=1;cases.append(bad)
        for change in ('length','tick','balance','survivors','initial'):
            bad=copy.deepcopy(rows)
            if change=='length':bad[0]['path'].pop()
            elif change=='tick':bad[0]['path'][5]['tick']=6
            elif change=='balance':bad[0]['path'][5]['occupied']+=1
            elif change=='survivors':bad[0]['path'][5]['original_survivors']+=1
            else:
                for node in bad[0]['path']:
                    node['births']+=1;node['deaths']+=1
            cases.append(bad)
        for bad in cases:
            with self.assertRaises((AssertionError,ValueError)):
                verifier.independent_summary(bad)

    def fixture(self):
        initial=dict(site_ids=[0,1],units=[{},{}])
        rows=[dict(tick=1,site_ids=[0,2],physical=dict(units=[{},{}],material=dict(dissolved=[1],proposals=[dict(reason='formed',source=0,target=1)]))),
              dict(tick=2,site_ids=[0,3],physical=dict(units=[{},{}],material=dict(dissolved=[1],proposals=[dict(reason='formed',source=0,target=1)])))]
        final=dict(site_ids=[0,3],parents=[None,None,0,0])
        return initial,rows,final

    def test_same_site_replacement_identity_ledger_and_resurrection(self):
        initial,rows,final=self.fixture()
        path=verifier.recount(initial,rows,final)
        self.assertEqual(path[-1],dict(tick=2,occupied=2,births=2,deaths=2,original_survivors=1,new_survivors=1))
        rows[1]['site_ids'][1]=1;final['site_ids'][1]=1
        with self.assertRaises(AssertionError):verifier.recount(initial,rows,final)

    def test_tampered_parent_and_events_rejected(self):
        for target in ('parent','deaths','births'):
            initial,rows,final=self.fixture()
            if target=='parent':final['parents'][2]=1
            if target=='deaths':rows[0]['physical']['material']['dissolved']=[]
            if target=='births':rows[0]['physical']['material']['proposals']=[]
            with self.assertRaises(AssertionError):verifier.recount(initial,rows,final)

    def test_frozen_endpoints_include_absolute_current_switch_values(self):
        summary=verifier.independent_summary(self.grid())
        endpoint=dict(histories={},interaction={})
        for name,effect,initial in (('on',100,10),('off',200,20)):
            pairs=[dict(seed=s,mutation=m,anchor=a,metrics=dict(occupied=dict(on=str(initial+effect),off=str(initial),difference=str(effect)))) for s,m,a in product(range(112000,112005),(0,100),(100,200,300,400))]
            sources=[dict(seed=s,mutation=m,metrics=dict(occupied=dict(mean=str(effect)))) for s,m in product(range(112000,112005),(0,100))]
            groups=[dict(mutation=m,metrics=dict(occupied=dict(mean=str(effect)))) for m in (0,100)]
            endpoint['histories'][name]=dict(pairs=pairs,sources=sources,groups=groups)
        endpoint['interaction']['pairs']=[dict(seed=s,mutation=m,anchor=a,metrics=dict(occupied=dict(on_history='100',off_history='200',difference='100'))) for s,m,a in product(range(112000,112005),(0,100),(100,200,300,400))]
        endpoint['interaction']['sources']=[dict(seed=s,mutation=m,metrics=dict(occupied=dict(mean='100'))) for s,m in product(range(112000,112005),(0,100))]
        endpoint['interaction']['groups']=[dict(mutation=m,metrics=dict(occupied=dict(mean='100'))) for m in (0,100)]
        verifier.verify_endpoints(summary,endpoint)
        for kind in ('absolute','interaction'):
            bad=copy.deepcopy(endpoint)
            if kind=='absolute':bad['histories']['on']['pairs'][0]['metrics']['occupied']['off']='11'
            else:bad['interaction']['groups'][0]['metrics']['occupied']['mean']='201'
            with self.assertRaises(AssertionError):verifier.verify_endpoints(summary,bad)
