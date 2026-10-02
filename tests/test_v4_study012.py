from itertools import product
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_v4_study012 as study


def record(size=2, world=False, continuous=True, primary=False, survivors=1, descendants=2, state='closed_multi'):
    return dict(anchor_size=size,whole_world_anchor=world,continuous_closed_multi=continuous,primary=primary,
                endpoint=dict(original_survivors=survivors,descendants=descendants,state=state))


def grid():
    return [dict(seed=s,drive=250,mutation=m,anchor=a,horizon=100,exchange=e,status='complete',summary=study.summarize([]))
            for s,m,a,e in product(range(96000,96005),(0,100),(100,200,300,400),(True,False))]


class Summaries(unittest.TestCase):
    def test_initial_eligibility_and_joint_replacement(self):
        got=study.summarize([record(),record(size=4,survivors=0,primary=True,descendants=10),record(size=1),record(world=True)])
        self.assertEqual(got['eligible_components'],2)
        self.assertEqual(got['initial_components'],4)
        self.assertEqual(got['fractions']['original_retention'],'1/4')
        self.assertEqual(got['fractions']['descendants'],'6')
        self.assertEqual(got['fractions']['replacement'],'1/2')
        self.assertEqual(got['counts']['continuous'],2)

    def test_empty_is_missing_failed_and_missing_are_errors(self):
        rows=grid();got=study.aggregate(rows)
        self.assertEqual(got['groups'][0]['metrics']['continuous'],dict(mean=None,available=0,missing=5))
        for bad in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError): study.aggregate(bad)
        rows[0]['status']='failed'
        with self.assertRaises(ValueError): study.aggregate(rows)

    def test_equal_anchor_then_source_weighting_and_negative_sources(self):
        rows=grid()
        for row in rows:
            if row['mutation']==0 and row['seed']==96000:
                if row['anchor']==100:
                    row['summary']=study.summarize([record(continuous=row['exchange'])])
                elif row['anchor']==200:
                    row['summary']=study.summarize([record(continuous=False)]*9)
            elif row['mutation']==0 and row['seed']==96001:
                row['summary']=study.summarize([record(continuous=not row['exchange'])])
        got=study.aggregate(rows)
        self.assertEqual(got['source_means'][0]['metrics']['continuous'],dict(mean='1/2',available=2,missing=2))
        self.assertEqual(got['groups'][0]['metrics']['continuous'],dict(mean='-1/4',available=2,missing=3))

    def test_pair_denominators_and_null_consistency(self):
        rows=grid();rows[0]['summary']=study.summarize([record()])
        with self.assertRaises(ValueError):study.aggregate(rows)
        rows=grid();rows[0]['summary']['fractions']['continuous']='0'
        with self.assertRaises(ValueError):study.aggregate(rows)


class Launch(unittest.TestCase):
    def test_preflight_failure_preserves_metadata(self):
        with tempfile.TemporaryDirectory() as d, patch.object(study,'OUTPUT',Path(d)/'out'), patch.object(study.subprocess,'check_output',return_value=''), patch.object(study,'binding_paths',return_value=[]), patch.object(study,'preflight',side_effect=ValueError('bad source')):
            with self.assertRaisesRegex(ValueError,'bad source'): study.main()
            meta=study.read(Path(d)/'out/metadata.json')
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_branches'],0)

    def test_budget_preserves_incomplete_grid(self):
        sources=[dict(seed=s,drive=250,mutation=m) for s,m in product(range(96000,96005),(0,100))]
        with tempfile.TemporaryDirectory() as d, patch.object(study,'OUTPUT',Path(d)/'out'), patch.object(study.subprocess,'check_output',return_value=''), patch.object(study,'binding_paths',return_value=[]), patch.object(study,'preflight',return_value=(sources,Path(d),{},{})), patch.object(study,'source_bindings',return_value={}), patch.object(study,'STORAGE_LIMIT',0), patch.object(study,'run') as branch:
            study.main();branch.assert_not_called()
            meta=study.read(Path(d)/'out/metadata.json')
            self.assertEqual(meta['status'],'storage_limit');self.assertEqual(meta['completed_branches'],0)
            self.assertFalse((Path(d)/'out/summary.json').exists())

    def test_dirty_and_existing_outputs_rejected(self):
        with patch.object(study.subprocess,'check_output',return_value=' M file'):
            with self.assertRaisesRegex(ValueError,'clean'): study.main()
        with tempfile.TemporaryDirectory() as d, patch.object(study,'OUTPUT',Path(d)), patch.object(study.subprocess,'check_output',return_value=''):
            with self.assertRaises(FileExistsError):study.main()

    def test_branch_failure_preserves_partial_and_budget_between_branches(self):
        sources=[dict(seed=s,drive=250,mutation=m) for s,m in product(range(96000,96005),(0,100))]
        for mode in ('failure','time'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as d:
                root=Path(d)/'out'
                calls=[]
                def branch(directory,source,anchor,horizon,exchange):
                    calls.append(exchange)
                    if len(calls)==2:
                        raise ValueError('audit failed')
                    directory.mkdir()
                    study.save(directory/'metadata.json',dict(status='complete',output_sha256={}))
                    study.save(directory/'audit.json',dict(ticks=100,output_sha256={}))
                    study.save(directory/'continuity.json',[])
                    return dict(records=[])
                def clock():
                    return 2000 if mode=='time' and calls else 0
                with patch.object(study,'OUTPUT',root), patch.object(study.subprocess,'check_output',return_value=''), patch.object(study,'binding_paths',return_value=[]), patch.object(study,'preflight',return_value=(sources,Path(d),{},{})), patch.object(study,'source_bindings',return_value={}), patch.object(study,'run',side_effect=branch), patch.object(study.time,'monotonic',side_effect=clock):
                    if mode=='failure':
                        with self.assertRaisesRegex(ValueError,'audit failed'):study.main()
                    else:study.main()
                meta=study.read(root/'metadata.json')
                self.assertEqual(meta['status'],'failed' if mode=='failure' else 'time_limit')
                self.assertEqual(meta['completed_branches'],1)
                self.assertEqual(len(study.read(root/'results.json')),1)
                self.assertFalse((root/'summary.json').exists())

    def test_binding_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_text('old')
            bound={str(p):study.digest(p)}
            p.write_text('new')
            with self.assertRaisesRegex(ValueError,'bytes changed'):study.check_bindings(bound)
