import copy
import unittest
from itertools import product
from scripts import analyze_v4_copy_bottlenecks as tool


def unit(material=0,program=(0,0,0,0)):
    return dict(material=material,program=list(program))


def fixture(groups,types=None,copy_counts=None,ancestry=None):
    initial=dict(site_ids=[0,1,2],units=[unit(),unit(),unit(1)],observation=dict(components=dict(material=[[0,1],[2]])))
    ids=[i for g in groups for i in g]
    types=types or {i:unit() for i in ids}
    row=dict(tick=1,site_ids=ids,physical=dict(units=[types[i] for i in ids]),observation=dict(components=dict(material=groups)))
    last=max([2]+ids)
    parents=[None,None,None]+[0]*(last-2) if ancestry is None else ancestry
    cp=[dict(component=0,anchor_members=[0,1],anchor_size=2,series=dict(descendant_genetic=copy_counts or [0]))]
    return initial,[row],dict(parents=parents,site_ids=ids),cp


def cohort(flags):
    series={g:[bool(flags[i])]*400 for i,g in enumerate(tool.GATES)}
    spans={g:[[1,400]] if flags[i] else [] for i,g in enumerate(tool.GATES)}
    state=next((i for i,v in enumerate(flags) if not v),4)
    return dict(component=0,anchor_members=[0,1],anchor_size=2,series=series,episodes=spans,
                longest={g:400 if flags[i] else 0 for i,g in enumerate(tool.GATES)},state_steps={s:400 if i==state else 0 for i,s in enumerate(tool.STATES)})


class Bottlenecks(unittest.TestCase):
    def test_mixed_inventory_and_extra_type(self):
        args=fixture([[0,1,3,4,2]],{0:unit(),1:unit(),3:unit(),4:unit(),2:unit(1)})
        got=tool.analyze(*args)[0]
        self.assertEqual({k:v[0] for k,v in got['series'].items()},dict(population=True,inventory=True,partition=False,copy=False))
        args=fixture([[0,1],[3,4],[5]],{0:unit(),1:unit(),3:unit(),4:unit(),5:unit(2)})
        self.assertTrue(tool.analyze(*args)[0]['series']['partition'][0])

    def test_repeated_types_and_complete_components(self):
        args=fixture([[0,1],[3,4]],{0:unit(),1:unit(),3:unit(1),4:unit(1)})
        got=tool.analyze(*args)[0]
        self.assertTrue(got['series']['population'][0]);self.assertFalse(got['series']['inventory'][0])
        got=tool.analyze(*fixture([[0,1,3,4]]))[0]
        self.assertTrue(got['series']['inventory'][0]);self.assertFalse(got['series']['partition'][0])

    def test_copy_nesting_and_parent_binding(self):
        got=tool.analyze(*fixture([[0,1],[3,4]],copy_counts=[2]))[0]
        self.assertEqual(got['state_steps']['copy_pass'],1)
        with self.assertRaises(ValueError):tool.analyze(*fixture([[0,1,3,4]],copy_counts=[2]))
        args=fixture([[0,1],[3,4]]);args[3][0]['anchor_members']=[0,2]
        with self.assertRaises(ValueError):tool.analyze(*args)

    def test_future_births_excluded_and_unrooted_live_rejected(self):
        args=fixture([[0,1],[2]]);args[2]['parents'] += [0]*20
        self.assertFalse(tool.analyze(*args)[0]['series']['population'][0])
        with self.assertRaises(ValueError):tool.analyze(*fixture([[0,1],[3,4]],ancestry=[None,None,None,None,0]))

    def test_nine_ten_and_all_state_steps(self):
        p=cohort((True,True,True,False))
        for g in tool.GATES:
            p['series'][g]=[False]*400
        p['series']['population'][0:10]=[True]*10
        p['series']['inventory'][0:9]=[True]*9
        p['episodes']={g:tool.episodes(v) for g,v in p['series'].items()}
        p['longest']={g:max((b-a+1 for a,b in spans),default=0) for g,spans in p['episodes'].items()}
        p['state_steps']=dict(population_fail=390,inventory_fail=1,partition_fail=9,copy_fail=0,copy_pass=0)
        result=tool.branch_result(dict(history=True,seed=112000,mutation=0,exchange=True,parents=[p]))
        self.assertEqual(result['counts']['population_persistent'],1)
        self.assertEqual(result['counts']['inventory_persistent'],0)
        self.assertEqual(sum(result['state_steps'].values()),400)
        self.assertEqual(result['state_fractions']['population_fail'],'39/40')
        p['state_steps']['copy_pass']=1
        with self.assertRaises(ValueError):tool.branch_result(dict(history=True,seed=112000,mutation=0,exchange=True,parents=[p]))

    def test_equal_sources_null_and_complete_grid(self):
        records=[]
        for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False)):
            parents=[]
            if s in (112000,112001):
                parents=[cohort((True,True,s==112000 and e,False))]
                if s==112001:
                    second=copy.deepcopy(parents[0]);second.update(component=1,anchor_members=[2,3]);parents.append(second)
            records.append(dict(history=h,seed=s,mutation=m,exchange=e,parents=parents))
        results,summary=tool.summarize_records(records)
        self.assertEqual(summary['cells'][0]['metrics']['partition_ever'],dict(mean='1/2',available=2,missing=3))
        self.assertEqual(summary['groups'][0]['metrics']['partition_ever']['mean'],'1/2')
        self.assertEqual(len(summary['cells'][0]['metrics']),13)
        for bad in (results[:-1],results[:-1]+[results[0]]):
            with self.assertRaises(ValueError):tool.aggregate(bad)
        results[0]['status']='failed'
        with self.assertRaises(ValueError):tool.aggregate(results)

    def test_complete_program_frequency_and_strict_boolean_series(self):
        args=fixture([[0,1],[3,4]],{0:unit(),1:unit(),3:unit(program=(0,0,0,1)),4:unit()})
        self.assertFalse(tool.analyze(*args)[0]['series']['inventory'][0])
        with self.assertRaises(ValueError):tool.episodes([1])
        args=fixture([[0,1],[3,4]]);args[3][0]['series']['descendant_genetic']=[True]
        with self.assertRaises(ValueError):tool.analyze(*args)

    def test_all_empty_are_null_and_state_corruption_rejected(self):
        records=[dict(zip(tool.IDENTITY,k),parents=[]) for k in tool.GRID]
        results,summary=tool.summarize_records(records)
        self.assertEqual(summary['groups'][0]['metrics']['partition_ever'],dict(mean=None,available=0,missing=5))
        self.assertEqual(results[0]['state_fractions']['copy_pass'],None)
        results[0]['state_steps']['copy_pass']=1
        with self.assertRaises(ValueError):tool.aggregate(results)

    def test_preflight_failure_preserves_metadata_and_exclusive_output(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts import copy_bottleneck_inputs as inputs
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'out'
            with patch.object(tool,'OUTPUT',output), patch.object(tool.subprocess,'check_output',return_value=''), patch.object(inputs,'bindings',side_effect=ValueError('bad upstream')):
                with self.assertRaisesRegex(ValueError,'bad upstream'):tool.main()
                meta=json.loads((output/'metadata.json').read_text())
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['completed_branches'],0)
                self.assertEqual(json.loads((output/'records.json').read_text()),[])
                with self.assertRaises(FileExistsError):tool.main()
