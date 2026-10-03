import copy
import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import verify_v4_program_boundaries as verifier


def fixture(seed=120000, exchange=False):
    ids = [None] * 32
    units = [None] * 32
    for identity, site in ((0, 0), (1, 1)):
        ids[site] = identity
        units[site] = dict(material=0, program=[0, 0, 0, identity+1], energy=20)
    initial = dict(site_ids=ids.copy(), units=copy.deepcopy(units))
    for identity, site, material in ((2, 4, 0), (3, 5, 0), (4, 18, 2)):
        ids[site] = identity
        units[site] = dict(material=material, program=units[identity % 2]['program'].copy(), energy=20)
    rows = [dict(tick=tick, site_ids=ids.copy(), physical=dict(units=copy.deepcopy(units),
        material=dict(dissolved=[], proposals=[dict(reason='formed', source=source, target=site)
            for source, site in ((0, 4), (1, 5), (0, 18))] if tick == 1 else []))) for tick in range(1,33)]
    return dict(seed=seed, mode='random-direction', exchange=exchange, config=dict(width=8, height=4),
        initial=initial, rows=rows, final=dict(site_ids=ids, units=units, parents=[None,None,0,1,0]),
        summary=dict(genetic_counts=[2]*32, episodes=[[1,32]]))


class BoundaryVerifierTests(unittest.TestCase):
    def test_recounts_identity_births_all_materials_and_full_steps(self):
        record = verifier.recount(fixture(), 'heterogeneous')
        self.assertEqual(record['formations'][0], [dict(child=2,parent=0,site=4,material=0),
            dict(child=3,parent=1,site=5,material=0),dict(child=4,parent=0,site=18,material=2)])
        self.assertEqual(record['formations'][1:], [[] for _ in range(31)])
        self.assertEqual(record['members']['label'], 'seed-120000-random-direction-exchange-false')
        self.assertEqual(record['phases']['episodes'][0]['length'],32)

    def test_complete_grid_and_summary(self):
        records = [verifier.recount(fixture(seed, exchange), genotype) for genotype,exchange,seed in verifier.GRID]
        cells = verifier.aggregate(records)
        self.assertEqual(len(cells),4)
        for cell in cells:
            self.assertEqual(cell['episodes'],20)
            self.assertEqual(cell['double_steps'],640)
            self.assertEqual(cell['nonzero_births'],20)
            self.assertEqual(cell['stable_pair_episodes'],20)
            self.assertEqual(cell['max_same_pair_run'],32)
            self.assertEqual(cell['formation_up'],20)
            self.assertEqual(cell['all_new_double_steps'],0)
        for bad in (records[:-1], records[::-1], records[:-1]+records[:1]):
            with self.assertRaises(ValueError): verifier.aggregate(bad)

    def test_tampered_source_ancestry_and_program_rejected(self):
        for field in ('ancestry','program','ticks','birth'):
            case=fixture()
            if field=='ancestry': case['final']['parents'][2]=1
            elif field=='program': case['rows'][1]['physical']['units'][4]['program'][0]=3
            elif field=='ticks': case['rows'][3]['tick']=3
            else: case['rows'][0]['physical']['material']['proposals'].pop()
            with self.subTest(field=field), self.assertRaises(ValueError): verifier.recount(case,'heterogeneous')

    def test_unknown_genotype_and_incomplete_steps_rejected(self):
        with self.assertRaises(ValueError): verifier.recount(fixture(),'other')
        case=fixture();case['rows'].pop()
        with self.assertRaises(ValueError): verifier.recount(case,'homogeneous')

    def setup_run(self,root):
        def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        def read(path): return json.loads(Path(path).read_text())
        cases=[];records=[]
        for genotype,exchange,seed in verifier.GRID:
            case=fixture(seed,exchange);path=root/f'{genotype}-{exchange}-{seed}.json'
            path.write_text(json.dumps(case));cases.append((genotype,path));records.append(verifier.recount(case,genotype))
        values={'records.json':records,'summary.json':verifier.aggregate(records)}
        for name,value in values.items(): (root/name).write_text(json.dumps(value))
        bound={'scripts/verify_v4_program_boundaries.py':digest(verifier.__file__)}
        metadata=dict(status='complete',planned_cases=80,completed_cases=80,saved_steps=2560,
            new_simulation_steps=0,new_environment_sources=0,reused_environment_sources=20,
            new_independent_initial_worlds=0,time_limit_seconds=300,storage_limit_bytes=33554432,
            elapsed_seconds=1,git_commit='a'*40,input_sha256=bound,input_sha256_after=bound,
            output_sha256={n:digest(root/n) for n in values})
        (root/'metadata.json').write_text(json.dumps(metadata))
        helper=types.SimpleNamespace(read=read,digest=digest,bindings=lambda:bound,source_cases=lambda:cases)
        return helper

    def test_main_proof_exclusive_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);helper=self.setup_run(root)
            before={p:p.read_bytes() for p in root.iterdir()}
            with patch.object(verifier,'OUTPUT',root),patch.dict(sys.modules,{'scripts.program_boundary_inputs':helper}):
                verifier.main()
                proof=(root/'independent-verification.json').read_bytes()
                with self.assertRaises(FileExistsError): verifier.main()
            self.assertEqual(json.loads(proof)['cases'],80)
            self.assertEqual(json.loads(proof)['saved_steps'],2560)
            self.assertFalse((root/'verification-failure.json').exists())
            for path,payload in before.items(): self.assertEqual(path.read_bytes(),payload)

    def test_tamper_rehashed_records_metadata_summary_and_bindings(self):
        for target in ('formation','members','summary','metadata','binding','source_order','input_changed','output_changed'):
            with self.subTest(target=target),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);helper=self.setup_run(root)
                meta=helper.read(root/'metadata.json')
                if target in ('formation','members'):
                    records=helper.read(root/'records.json')
                    if target=='formation': records[0]['formations'][0][0]['material']=7
                    else: records[0]['members']['steps'][0]['copies'][0]['depths']=[1,1]
                    (root/'records.json').write_text(json.dumps(records))
                elif target=='summary':
                    summary=helper.read(root/'summary.json');summary[0]['nonzero_births']+=1
                    (root/'summary.json').write_text(json.dumps(summary))
                elif target=='metadata': meta['completed_cases']=True
                elif target=='binding': helper.bindings()['scripts/verify_v4_program_boundaries.py']='0'*64
                elif target=='source_order':
                    sources=helper.source_cases();helper.source_cases=lambda:sources[::-1]
                elif target=='input_changed':
                    bound=helper.bindings();helper.bindings=unittest.mock.Mock(side_effect=[bound,dict(bound,extra='changed')])
                else:
                    original=helper.bindings;calls=[]
                    def changed():
                        calls.append(1)
                        if len(calls)==2:
                            with (root/'summary.json').open('a') as stream: stream.write(' ')
                        return original()
                    helper.bindings=changed
                meta['output_sha256']={n:helper.digest(root/n) for n in ('records.json','summary.json')}
                (root/'metadata.json').write_text(json.dumps(meta))
                with patch.object(verifier,'OUTPUT',root),patch.dict(sys.modules,{'scripts.program_boundary_inputs':helper}):
                    with self.assertRaises(ValueError): verifier.main()
                failure=helper.read(root/'verification-failure.json')
                self.assertEqual(failure['status'],'failed')
                self.assertEqual(set(failure['files_sha256_after']),{'metadata.json','records.json','summary.json'})
                self.assertIn('scripts/verify_v4_program_boundaries.py',failure['input_sha256_after'])
                self.assertFalse((root/'independent-verification.json').exists())

    def test_timeout_retains_failure_and_rerun_does_not_overwrite_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);helper=self.setup_run(root)
            with patch.object(verifier,'OUTPUT',root),patch.dict(sys.modules,{'scripts.program_boundary_inputs':helper}), \
                 patch.object(verifier,'monotonic',side_effect=[0,301,0,301]):
                with self.assertRaisesRegex(ValueError,'verification time budget'): verifier.main()
                failure=(root/'verification-failure.json').read_bytes()
                with self.assertRaisesRegex(ValueError,'verification time budget'): verifier.main()
            self.assertEqual((root/'verification-failure.json').read_bytes(),failure)
            self.assertFalse((root/'independent-verification.json').exists())

    def test_binding_exception_still_records_actual_input_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);helper=self.setup_run(root)
            helper.bindings=unittest.mock.Mock(side_effect=ValueError('source digest changed'))
            with patch.object(verifier,'OUTPUT',root),patch.dict(sys.modules,{'scripts.program_boundary_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'source digest changed'): verifier.main()
            failure=helper.read(root/'verification-failure.json')
            self.assertEqual(failure['input_sha256_after']['scripts/verify_v4_program_boundaries.py'],
                             helper.digest(verifier.__file__))
