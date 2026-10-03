import unittest
from copy import deepcopy
from scripts import verify_v4_program_direction as verifier

KEYS=('genetic_persistent10','genetic_ever','material_persistent10','material_ever','longest_genetic','births','deaths','living','imported','spent','final_energy','nonzero_births','north_births')


def records():
    result=[]
    for seed in range(120000,120020):
        for exchange in (False,True):
            old=dict.fromkeys(KEYS,0);new=dict(old)
            old.update(living=3,final_energy=192)
            new.update(old)
            old['imported']=10
            old['final_energy']=202
            change=(1,-1,0,0)[seed%4]
            new['imported']=10+change;new['final_energy']=202+change
            result.append(dict(seed=seed,exchange=exchange,homogeneous=old,heterogeneous=new,
                               delta={k:new[k]-old[k] for k in KEYS}))
    return result


class PairedTests(unittest.TestCase):
    def test_positive_negative_zero_and_fraction(self):
        result=verifier.aggregate(records())
        self.assertEqual(len(result['cells']),4)
        for row in result['contrasts']:
            self.assertEqual(row['positive']['imported'],5)
            self.assertEqual(row['negative']['imported'],5)
            self.assertEqual(row['tie']['imported'],10)
            self.assertEqual(row['mean_delta']['imported'],'0')
        self.assertEqual(result['cells'][0]['means']['imported'],'10')
        self.assertTrue(all(type(v) is int for v in result['cells'][0]['totals'].values()))
        changed=records()
        changed[0]['heterogeneous']['imported']+=1
        changed[0]['heterogeneous']['final_energy']+=1
        changed[0]['delta']['imported']+=1
        changed[0]['delta']['final_energy']+=1
        self.assertEqual(verifier.aggregate(changed)['contrasts'][0]['mean_delta']['imported'],'1/20')

    def test_incomplete_duplicate_identity_and_delta_rejected(self):
        for mutate in (lambda r:r.pop(), lambda r:r.__setitem__(0,r[1]),
                       lambda r:r[0].__setitem__('exchange',0),
                       lambda r:r[0]['delta'].__setitem__('imported',3),
                       lambda r:r[0]['homogeneous'].__setitem__('genetic_ever',False)):
            bad=records();mutate(bad)
            with self.assertRaises(ValueError):verifier.aggregate(bad)


class PhysicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.run_v4_copy_ablation import run_case as baseline
        from scripts.run_v4_program_direction import run_case
        cls.pairs=[(source,run_case(source)) for source in
                   (baseline(120000,'random-direction',False),baseline(120000,'random-direction',True))]

    def test_independent_replay_and_metrics(self):
        for source,case in self.pairs:
            untouched=deepcopy((source,case))
            self.assertEqual(verifier.verify_case(case,source),case['summary'])
            self.assertEqual((source,case),untouched)
            for row in case['rows']:
                physical=row['physical']
                self.assertEqual(physical['material_before'],7)
                self.assertEqual(physical['material_after'],7)
                self.assertEqual(physical['energy_before']+physical['imported']-physical['spent'],physical['energy_after'])
            record=verifier.pair_record(case,source)
            self.assertEqual(set(record['heterogeneous']),set(KEYS))
            self.assertEqual(record['homogeneous'],verifier.metrics(source))
            for key in KEYS:
                self.assertEqual(record['delta'][key],record['heterogeneous'][key]-record['homogeneous'][key])
                self.assertIs(type(record['heterogeneous'][key]),int)

    def test_all_input_and_observation_tampering_rejected(self):
        source,case=self.pairs[0]
        def change_direction(c):c['rows'][0]['physical']['directions'][0]=(c['rows'][0]['physical']['directions'][0]+1)%4
        def change_ticket(c):c['rows'][0]['physical']['mutation_tickets'][0][0]-=1
        def change_feed(c):c['rows'][0]['physical']['driven']['inputs'][0]['proposed']+=1
        def change_program(c):c['initial']['units'][85]['program'][3]=0
        def change_identity(c):c['rows'][0]['site_ids'][85]=999
        def change_summary(c):c['summary']['longest']+=1
        def change_copies(c):c['copy_parents'][0]['series']['unrelated_genetic'][0]+=1
        for mutate in (change_direction,change_ticket,change_feed,change_program,change_identity,change_summary,change_copies):
            bad=deepcopy(case);mutate(bad)
            with self.assertRaises(ValueError):verifier.verify_case(bad,source)
        self.assertEqual(verifier.metrics(case)['north_births'],1)
        self.assertEqual(verifier.metrics(case)['nonzero_births'],1)
        for mutate in (change_direction,change_ticket,change_feed):
            bad=deepcopy(source);mutate(bad)
            with self.assertRaises(ValueError):verifier.verify_case(case,bad)
        wrong=deepcopy(source);wrong['exchange']=True
        with self.assertRaises(ValueError):verifier.verify_case(case,wrong)


class MainProofTests(unittest.TestCase):
    def fixture(self,root):
        import json
        pairs=records()
        cases=root/'cases';cases.mkdir()
        for record in pairs:
            name=f"seed-{record['seed']}-random-direction-exchange-{str(record['exchange']).lower()}.json"
            (cases/name).write_text(json.dumps(dict(seed=record['seed'],exchange=record['exchange'],mode='random-direction')))
        (root/'results.json').write_text(json.dumps(pairs))
        (root/'summary.json').write_text(json.dumps(verifier.aggregate(pairs)))
        bound={f'fixture-{n}':str(n) for n in range(228)}
        bound['scripts/verify_v4_program_direction.py']=verifier.digest(verifier.Path(verifier.__file__))
        outputs={str(p.relative_to(root)):verifier.digest(p) for p in root.rglob('*.json')}
        meta=dict(status='complete',planned_cases=40,completed_cases=40,new_simulation_steps=1280,
                  new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,
                  artificial_initial_state=True,time_limit_seconds=600,storage_limit_bytes=134217728,
                  git_commit='a'*40,elapsed_seconds=1,input_sha256=bound,input_sha256_after=bound,output_sha256=outputs)
        (root/'metadata.json').write_text(json.dumps(meta))
        return pairs,bound

    def run_fixture(self,root,pairs,bound):
        from unittest.mock import patch
        original_read=verifier.read
        indexed={(r['seed'],r['exchange']):r for r in pairs}
        def read(path):
            if str(path).startswith('data/v4-study-019/'):
                # The source provenance helper is mocked; no ignored files are read.
                return {'fixture_source':str(path)}
            return original_read(path)
        with patch.object(verifier,'OUTPUT',root),patch.object(verifier,'bindings',return_value=bound), \
             patch.object(verifier,'read',side_effect=read),patch.object(verifier,'verify_case') as replay, \
             patch.object(verifier,'pair_record',side_effect=lambda case,source:indexed[case['seed'],case['exchange']]):
            verifier.main()
        self.assertEqual(replay.call_count,40)

    def test_full_main_inventory_statistics_and_proof(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as temporary:
            root=Path(temporary);pairs,bound=self.fixture(root)
            self.run_fixture(root,pairs,bound)
            proof=verifier.read(root/'independent-verification.json')
            self.assertEqual(proof['status'],'verified')
            for key,value in dict(cases=40,saved_steps=1280,new_simulation_steps=1280,input_files=229,
                                  new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0).items():
                self.assertEqual(proof[key],value)
            self.assertEqual(proof['verifier_sha256'],bound['scripts/verify_v4_program_direction.py'])
            self.assertEqual(proof['files_sha256'],{str(p.relative_to(root)):verifier.digest(p) for p in root.rglob('*.json') if p.name!='independent-verification.json'})

    def test_current_verifier_binding_tamper_rejected_before_replay(self):
        import json
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        with TemporaryDirectory() as temporary:
            root=Path(temporary);pairs,bound=self.fixture(root)
            bound['scripts/verify_v4_program_direction.py']='0'*64
            meta=verifier.read(root/'metadata.json');meta.update(input_sha256=bound,input_sha256_after=bound)
            (root/'metadata.json').write_text(json.dumps(meta))
            read=verifier.read
            def bounded_read(path):
                self.assertTrue(Path(path).is_relative_to(root),'no source may be read before verifier identity is accepted')
                return read(path)
            with patch.object(verifier,'OUTPUT',root),patch.object(verifier,'bindings',return_value=bound), \
                 patch.object(verifier,'read',side_effect=bounded_read), \
                 patch.object(verifier,'verify_case') as replay,patch.object(verifier,'pair_record',return_value=pairs[0]):
                with self.assertRaisesRegex(ValueError,'running verifier'):
                    verifier.main()
                replay.assert_not_called()
            self.assertFalse((root/'independent-verification.json').exists())

    def test_existing_proof_rejected_before_any_replay(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import patch
        with TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root)
            proof=root/'independent-verification.json';proof.write_text('existing evidence')
            with patch.object(verifier,'OUTPUT',root),patch.object(verifier,'bindings') as binding, \
                 patch.object(verifier,'verify_case') as replay:
                with self.assertRaisesRegex(ValueError,'proof already exists'):
                    verifier.main()
                replay.assert_not_called();binding.assert_not_called()
            self.assertEqual(proof.read_text(),'existing evidence')

    def test_rehashed_statistics_tamper_cannot_produce_proof(self):
        import json
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as temporary:
            root=Path(temporary);pairs,bound=self.fixture(root)
            summary=verifier.read(root/'summary.json')
            summary['contrasts'][0]['positive']['imported']+=1
            (root/'summary.json').write_text(json.dumps(summary))
            meta=verifier.read(root/'metadata.json')
            meta['output_sha256']['summary.json']=verifier.digest(root/'summary.json')
            (root/'metadata.json').write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError,'all paired statistics'):
                self.run_fixture(root,pairs,bound)
            self.assertFalse((root/'independent-verification.json').exists())
